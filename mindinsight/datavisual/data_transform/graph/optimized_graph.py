# Copyright 2021 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""This file is used to define the MindSpore graph."""
from collections import defaultdict

from mindinsight.datavisual.common.log import logger
from mindinsight.datavisual.data_transform.graph.msgraph import MSGraph
from mindinsight.domain.graph.base import NodeTypeEnum


class OptimizedGraph(MSGraph):
    """The object describes the MindSpore graph, and it is defined in the anf_ir proto file."""

    MIN_GROUP_NODE_COUNT = 10

    def __init__(self):
        super().__init__()
        self._load_node_temp_cache = {}

    def _inherit_input_output_from_subnode(self, parent_node, subnode_list, filtered_type=None):
        """
        Adds the input and output of all direct child nodes to the current node.

        Args:
            parent_node (Node): The nodes that inherit the input and output of the child nodes.
            subnode_list (list[Node]): A list of child nodes that are inherited from the input and output.
            filtered_type (set(str)): Filter some input and output that do not require inheritance
                                      based on the node type. Default is filter const node.

        Note:
            - Only the inputs and outputs of the external scope are inherited.
            - Before add_const_node method, if the input is a const,
              the scope of the const node is not startswith the name of parent node.
              So in this scenario, we need to filter the const nodes.
        """
        filtered_type = {NodeTypeEnum.CONST.value} if filtered_type is None else filtered_type
        for method in ['inputs', 'outputs', 'proxy_inputs', 'proxy_outputs']:
            for node in subnode_list:
                for item_name, item_attr in getattr(node, method).items():
                    target_node = self._get_normal_node(node_name=item_name)
                    if target_node is None:
                        logger.warning("inherit %s from subnode, target node (%s) is None", method, item_name)
                        continue

                    if item_name.startswith(f'{parent_node.name}/'):
                        continue

                    if target_node.type in filtered_type:
                        continue

                    getattr(parent_node, f'add_{method}')(item_name, item_attr)

    def _cache_node(self, node):
        """Store the node in the cache."""
        # Notice:
        # The additional caching is used to handle the Const, Parameter and LOAD nodes separately later.
        super()._cache_node(node)
        if node.type == NodeTypeEnum.LOAD.value:
            self._load_node_temp_cache.update({node.name: node})

    def _delete_nodes_of_cache(self, node_names):
        """Delete node from cache."""
        logger.debug("These nodes will be removed from the cache, node names: %s.", node_names)
        for name in node_names:

            if self._parameter_node_temp_cache.get(name):
                self._parameter_node_temp_cache.pop(name)
            if self._const_node_temp_cache.get(name):
                self._const_node_temp_cache.pop(name)
            if self._load_node_temp_cache.get(name):
                self._load_node_temp_cache.pop(name)

            node = self._get_normal_node(node_name=name)
            self._normal_node_map.pop(name)
            self._node_id_map_name.pop(node.node_id)

    def _parse_data(self, proto_data):
        """
        The proto data is parsed and all nodes are stored in the specified structure.

        Args:
            proto_data (anf_ir_pb2.GraphProto): Refer to anf_ir_pb2.GraphProto object.
        """
        logger.info("Start to parse graph proto data.")

        self._parse_op_nodes(proto_data.node)
        self._parse_parameters(proto_data.parameters)
        self._parse_consts(proto_data.const_vals)

        self._update_input_after_create_node()
        self._update_output_after_create_node()

        self._delete_non_computational_ops()
        self._clean_no_input_output_node()

        self._extract_node_by_single_node_in_scope()
        logger.info("Parse proto data end, normal node count(only contain op node, "
                    "parameter, const): %s.", self.normal_node_count)

    def _parse_op_nodes(self, node_protos):
        """
        Parse `anf_ir_pb2.NodeProto` object, and create a normal node.

        Args:
            node_protos (list[anf_ir_pb2.NodeProto]): Refer to anf_ir_pb2.NodeProto.
        """
        logger.debug("Start to parse op nodes from proto.")
        for topological_index, node_proto in enumerate(node_protos):
            if not node_proto.name:
                logger.warning("Finding a node with an empty name will not save it.")
                continue

            if node_proto.full_name.startswith("Gradients") or "optimizer" in node_proto.full_name \
                    or "opt" in node_proto.instance_name:
                continue

            self._parse_op_node(topological_index, node_proto)

    def _update_input_after_create_node(self):
        """Update the input of node after create node."""
        for node in self._normal_node_map.values():
            for src_node_id, input_attr in dict(node.inputs).items():
                node.delete_inputs(src_node_id)
                if not self._is_node_exist(node_id=src_node_id):
                    continue

                src_node = self._get_normal_node(node_id=src_node_id)
                input_attr['shape'] = src_node.output_shape
                input_attr['data_type'] = src_node.output_data_type
                node.add_inputs(src_name=src_node.name, input_attr=input_attr)

        nodes = self._list_nodes_without_parameter_const()
        for node in nodes:
            for src_node_name, _ in dict(node.inputs).items():
                if not self._is_node_exist(node_name=src_node_name):
                    logger.warning("Source node (%s) is None.", src_node_name)
                    continue

                src_node = self._get_normal_node(node_name=src_node_name)
                if src_node.type in (NodeTypeEnum.LOAD.value,
                                     NodeTypeEnum.TUPLE_GET_ITEM.value,
                                     NodeTypeEnum.MAKETUPLE.value,
                                     NodeTypeEnum.UPDATE_STATE.value):
                    node.delete_inputs(src_node_name)
                    for source_node_name, source_attr in dict(src_node.inputs).items():
                        source_node = self._get_normal_node(node_name=source_node_name)
                        if source_node is None:
                            logger.warning("Source node (%s) is None.", source_node_name)
                            continue
                        source_attr['shape'] = source_node.output_shape
                        source_attr['data_type'] = source_node.output_data_type
                        node.add_inputs(src_name=source_node.name, input_attr=source_attr)

    def _update_output_after_create_node(self):
        """Update the output of node after create node."""
        super()._update_output_after_create_node()

        nodes = self._list_nodes_without_parameter_const()
        for node in nodes:
            for src_node_name, _ in dict(node.outputs).items():
                if not self._is_node_exist(node_name=src_node_name):
                    logger.warning("Source node (%s}) is None.", src_node_name)
                    continue

                src_node = self._get_normal_node(node_name=src_node_name)
                if src_node.type in (NodeTypeEnum.LOAD.value,
                                     NodeTypeEnum.TUPLE_GET_ITEM.value,
                                     NodeTypeEnum.MAKETUPLE.value,
                                     NodeTypeEnum.UPDATE_STATE.value):
                    node.delete_outputs(src_node_name)
                    for source_node_name, source_attr in dict(src_node.outputs).items():
                        source_node = self._get_normal_node(node_name=source_node_name)
                        if source_node is None:
                            logger.warning("Source node (%s) is None.", source_node_name)
                            continue
                        source_attr['shape'] = source_node.output_shape
                        source_attr['data_type'] = source_node.output_data_type
                        node.add_outputs(src_name=source_node.name, output_attr=source_attr)

    def _delete_non_computational_ops(self):
        """Deleted non-computational operators."""
        delete_names = []
        for node in self._normal_node_map.values():
            if node.type in (NodeTypeEnum.LOAD.value,
                             NodeTypeEnum.TUPLE_GET_ITEM.value,
                             NodeTypeEnum.MAKETUPLE.value,
                             NodeTypeEnum.UPDATE_STATE.value):
                delete_names.append(node.name)

        self._delete_nodes_of_cache(delete_names)

    def _list_nodes_without_parameter_const(self):
        """List nodes without parameter and const node."""
        nodes = self._normal_node_map.values()
        not_expect_type = (NodeTypeEnum.CONST.value, NodeTypeEnum.PARAMETER.value)
        nodes = filter(lambda node: node.type not in not_expect_type, nodes)
        nodes = sorted(nodes, key=lambda node: node.topological_index)
        return nodes

    def _extract_node_by_single_node_in_scope(self):
        """Extract node from the scope which has only one node."""
        nodes = self._list_nodes_without_parameter_const()
        scope_map_types = defaultdict(set)
        scope_map_node_cnt = defaultdict(int)
        for node in nodes:
            if not node.scope or '/' not in node.scope:
                continue
            scope_map_types[node.scope].add(node.type)
            scope_map_node_cnt[node.scope] += 1

        filter_scopes = set()
        for scope, types in scope_map_types.items():
            if len(types) == 1 and scope_map_node_cnt[scope] > 1 and types.pop() in scope:
                filter_scopes.add(scope)

        for filter_scope in list(filter_scopes):
            for scope in scope_map_types:
                if scope.startswith(f'{filter_scope}/'):
                    filter_scopes.remove(filter_scope)
                    break

        if not filter_scopes:
            return

        for node in nodes:
            if node.scope in filter_scopes and '/' in node.scope:
                name = node.name.rsplit('/', 1)[1]
                new_scope = node.scope.rsplit('/', 1)[0]
                new_name = f'{new_scope}/{name}'
                self._update_node_name_of_cache(node, new_name)

        return

    def _clean_no_input_output_node(self):
        """Clean nodes which has no input and output."""
        nodes = self._list_nodes_without_parameter_const()
        deleted_names = []
        for node in nodes:
            if not node.inputs and not node.outputs:
                deleted_names.append(node.name)
        self._delete_nodes_of_cache(deleted_names)

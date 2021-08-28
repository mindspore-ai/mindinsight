# Copyright 2020-2021 Huawei Technologies Co., Ltd
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
"""Define the graph stream handler."""
from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError, \
    DebuggerNodeNotInGraphError, DebuggerGraphNotExistError
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.common.utils import is_scope_type
from mindinsight.debugger.conditionmgr.common.utils import NodeBasicInfo
from mindinsight.debugger.conditionmgr.condition import TargetTypeEnum as CategoryTypeEnum
from mindinsight.debugger.stream_cache.debugger_graph import DebuggerGraph
from mindinsight.debugger.stream_cache.debugger_multigraph import DebuggerMultiGraph
from mindinsight.debugger.stream_handler.base_handler import StreamHandlerBase
from mindinsight.debugger.stream_handler.source_handler import validate_stack_pattern, SourceHandler
from mindinsight.domain.graph.query import StackQuery


class MultiCardGraphHandler(StreamHandlerBase):
    """Multi-card Graph Handler."""

    def __init__(self):
        self._graph_handlers = {}
        self._source_handler = SourceHandler()

    @property
    def graph_handlers(self):
        """The property of whole_graph."""
        return self._graph_handlers

    @property
    def source_handler(self):
        """The property of source handler."""
        return self._source_handler

    def get_graph_handler_by_rank_id(self, rank_id=0):
        """Get handler by rank id."""
        if rank_id in self._graph_handlers:
            return self._graph_handlers.get(rank_id)
        if rank_id == 0:
            # ms side still using device id instead of rank id, so the first rank_id is not 0
            for graph_handler in self._graph_handlers.values():
                return graph_handler
        log.error("There is no rank id %d.", rank_id)
        raise ValueError

    def put(self, value):
        """Put graphs into graph_handlers."""
        for rank_id, graph in value.items():
            if rank_id not in self._graph_handlers:
                self._graph_handlers[rank_id] = GraphHandler()
            self._graph_handlers[rank_id].put(graph)

    def parse_stack_infos(self):
        """Add stack infos into cache."""
        source_handler = self._source_handler
        for graph_stream in self._graph_handlers.values():
            for leaf_node in graph_stream.leaf_nodes.values():
                source_handler.put(leaf_node.stack)
        self._source_handler.sort()

    def get(self, filter_condition=None):
        """Get the graph of specific node for specific device."""
        if not self._graph_handlers:
            log.warning('There is no graph received yet.')
            return {'graph': {}}

        def _get_first_rank_id():
            rank_ids = list(self._graph_handlers.keys())
            rank_ids.sort()
            return rank_ids[0]
        if not filter_condition or not filter_condition.get('rank_id'):
            rank_id = _get_first_rank_id()
        else:
            rank_id = filter_condition.get('rank_id')
        if rank_id in self._graph_handlers:
            return self._graph_handlers.get(rank_id).get(filter_condition)
        log.error("There is no rank id %d.", rank_id)
        raise ValueError

    def has_graph(self):
        """check if has graph"""
        res = False
        for graph_handler in self._graph_handlers:
            res = res or graph_handler.graph
        return res

    def register_graph_handler(self, rank_id, graph_handler):
        """Register graph handler."""
        self._graph_handlers[rank_id] = graph_handler

    def clean(self):
        """Clean cache."""
        self.__init__()

    def validate_rank_id(self, rank_id):
        """Judge if the rank_id is valid"""
        return rank_id in self._graph_handlers


class GraphHandler(StreamHandlerBase):
    """Metadata Handler."""

    def __init__(self):
        # dict of <graph_name, GraphProto object>
        self._graph_proto = {}
        # dict of <graph_name, DebuggerGraph object>
        self._graph = {}
        self._searched_node_list = {}
        # dict of <node full name, graph_name>
        self.graph_node_map = {}
        # dict of <node ui name, Node object> for all graphs
        self._all_leaf_nodes = {}
        # the whole graph
        self._whole_graph = None

    @property
    def whole_graph(self):
        """The property of whole_graph."""
        return self._whole_graph

    @property
    def graph(self):
        """The property of graph."""
        return self._graph_proto

    @property
    def graph_names(self):
        """The property of graph names."""
        return list(self._graph)

    @property
    def debugger_graph_obj(self):
        """The property of graph object."""
        return self._graph

    @property
    def leaf_nodes(self):
        """The property of leaf nodes among all graphs."""
        return self._all_leaf_nodes

    def put(self, value):
        """
        Put value into graph cache. Called by grpc server.

        Args:
            value (dict): The Graph proto message. Each item is format like (<graph_name>, GraphProto).
        """
        log.info("Put graph into cache.")
        sorted_value_list = self._sort_graph(value)
        for graph_name, graph_value in sorted_value_list:
            self._graph_proto[graph_name] = graph_value
            # build sub graph
            graph = DebuggerGraph()
            graph.build_graph(graph_value)
            self._graph[graph_name] = graph
            leaf_nodes = graph.leaf_nodes
            self._all_leaf_nodes.update(leaf_nodes)
            for _, node in leaf_nodes.items():
                self.graph_node_map[node.full_name] = graph_name

        # build whole graph
        graph = DebuggerMultiGraph()
        graph.add_graph(self._graph)
        self._whole_graph = graph

    def get(self, filter_condition=None):
        """
        Get the graph of specific node.

        Args:
            filter_condition (dict):

                - name (str): The full debug node name.
                - graph_name (str): The relative graph_name of the node.
                - single_node (bool): If True, return the graph from root
                    to the specific node; else, return the sublayer of the
                    graph. Default: False.

        Returns:
            dict, the metadata.
        """
        try:
            self._graph_exists()
        except DebuggerGraphNotExistError:
            log.warning('The graph is empty. To view a graph, '
                        'please start the training script first.')
            return {'graph': {}}

        graph = {}
        if filter_condition is None:
            filter_condition = {}
            graph = {'graph_names': self.graph_names}

        single_node = filter_condition.get('single_node', False)
        name = filter_condition.get('name')
        graph_name = filter_condition.get('graph_name')
        if single_node is True:
            nodes = self._get_single_node(name, graph_name)
        else:
            nodes = self._list_nodes(name, graph_name)
        graph.update(nodes)

        return {'graph': graph}

    def _get_single_node(self, name, graph_name=None):
        """
        Search node, and return every layer nodes until this node.

        Args:
            graph_name(str): The graph_name.
            name (str): The name of node.

        Returns:
            dict, every layer nodes until this node.
        """
        graph = self._get_graph(graph_name=graph_name)
        searched_graph = graph.search_single_node(name)

        return searched_graph

    def _list_nodes(self, scope, graph_name):
        """
        Get the nodes of every layer in graph.

        Args:
            scope (str): The name of a scope.
            graph_name(str): The graph name.

        Returns:
            TypedDict{'nodes': ['Node_1', ...], 'graph_names': ['graph_name_1', ...]},
            format is {'nodes': [<NodeObject>], 'graph_names': [<str>]}.
                example:
                    {
                      "nodes" : [
                        {
                          "attr" :
                          {
                            "index" : "i: 0\n"
                          },
                          "input" : {},
                          "name" : "input_tensor",
                          "output" :
                          {
                            "Default/TensorAdd-op17" :
                            {
                              "edge_type" : "data",
                              "scope" : "name_scope",
                              "shape" : [1, 16, 128, 128]
                            }
                          },
                          "output_i" : -1,
                          "proxy_input" : {},
                          "proxy_output" : {},
                          "independent_layout" : False,
                          "subnode_count" : 0,
                          "type" : "Data"
                        }
                      ]
                    }
        """
        graph = self._get_graph(graph_name, scope)
        nodes = graph.list_node_by_scope(scope=scope)
        res = {'nodes': nodes}

        return res

    def get_tensor_history(self, node_name, graph_name=None, depth=0):
        """
        Get the tensor history of a specified node.

        Args:
            node_name (str): The debug name of the node.
            graph_name (str): The graph_name. Default: None.
            depth (int): The number of layers the user
                wants to trace. Default is 0.

        Returns:
            dict, basic tensor history, only including tensor name and tensor type and node type.
        """
        graph_name, node_name = self._parse_node_name(node_name, graph_name)
        graph = self._get_graph(graph_name=graph_name, node_name=node_name)
        # validate node type, scope node has no tensor history
        node_type = graph.get_node_type(node_name)
        if is_scope_type(node_type):
            log.error("Scope type node has no tensor history.")
            raise DebuggerParamValueError("Invalid leaf node name.")
        # get tensor history
        tensor_history, cur_outputs_nums = graph.get_tensor_history(node_name, depth)
        # add the tensor type for tensor history
        self._update_tensor_history(tensor_history[0:cur_outputs_nums], 'output', graph_name)
        self._update_tensor_history(tensor_history[cur_outputs_nums:], 'input', graph_name)
        log.debug("Get %d tensors in tensor history for node <%s>.", len(tensor_history), node_name)
        return {'tensor_history': tensor_history}

    @staticmethod
    def _update_tensor_history(tensor_history, tensor_type, graph_name):
        """
        Add tensor source type for tensor history.

        Args:
            tensor_history (list[dict]): Tensor history from Graph stream. Each element has two
                keys: `node_type` and `name`. `node_type` refers to the type of the node which
                the tensor come from. `name` refers to the tensor name.
            tensor_type (str): The source type of the tensor. `input` or `output`.
            graph_name (str): The graph name.
        """
        for single_tensor_info in tensor_history:
            single_tensor_info['type'] = tensor_type
            single_tensor_info['graph_name'] = graph_name

    def search_nodes(self, pattern):
        """
        Search nodes by given pattern.

        Args:
            pattern (dict): Filter condition.

                - name (str): The name pattern.
                - graph_name (str): The graph name.
                - node_category (str): The node_category.
                - condition (dict): The additional filter condition.
                - stack_pattern (str): The pattern of stack info.

        Returns:
            dict, the searched node.
        """
        graph_name = pattern.pop('graph_name', None)
        search_nodes = self.search_in_graph(pattern, graph_name)
        # construct to search tree
        graph = self._get_graph(graph_name=graph_name)
        format_nodes = graph.get_nodes(search_nodes)
        return {'nodes': format_nodes}

    def search_in_graph(self, pattern, graph_name=None):
        """
        Search nodes by given pattern.

        Args:
            pattern (dict): Filter condition.

                - name (str): The name pattern.
                - node_category (str): The node_category. Default: None.
                - condition (dict): The additional filter condition.
                - stack_pattern (str): The pattern of stack info.
            graph_name (str): The graph name. Default: None.

        Returns:
            list, the searched node list.
        """
        temp_node_list = []
        node_category = pattern.get('node_category')
        graph = self._get_graph(graph_name=graph_name)
        stack_pattern = pattern.get('stack_pattern')
        validate_stack_pattern(stack_pattern)
        # filter nodes by name
        if pattern.get('name'):
            if node_category or stack_pattern:
                # get leaf nodes for forward filter
                temp_node_list = graph.search_leaf_nodes_by_pattern(pattern.get('name'))
            else:
                # optimize search nodes
                temp_node_list = graph.search_nodes_by_pattern(pattern.get('name'))
            if not temp_node_list:
                log.debug("No node named %s", pattern.get('name'))
                return []
        # filter nodes by category
        if node_category:
            node_category = self._get_inner_node_category(node_category)
            condition = pattern['condition'].copy() if pattern.get('condition') else {}
            condition['search_range'] = temp_node_list
            temp_node_list = graph.search_nodes_by_category(node_category, condition=condition)
            if not temp_node_list:
                log.debug("No node with category %s", node_category)
                return []
        # filter nodes by stack_pattern
        if stack_pattern:
            if not temp_node_list:
                temp_node_list = graph.leaf_nodes.values()
            log.info("Begin to filter nodes by `stack_pattern`.")
            query = StackQuery(temp_node_list)
            temp_node_list = query.filter(stack_pattern).all()
        return temp_node_list

    @staticmethod
    def _get_inner_node_category(node_category):
        """
        Get inner node category.

        Args:
            node_category (str): The node category supported in
                mindinsight.conditionmgr.condition.TargetTypeEnum.

        Returns:
            CategoryTypeEnum, the translated value.
        """
        try:
            res = CategoryTypeEnum(node_category)
        except ValueError as err:
            log.error("Invalid node category. %s", err)
            raise DebuggerParamValueError("Invalid node_category.")
        return res

    def get_graph_id_by_name(self, node_name):
        """
        Get graph id by full name.

        Args:
            node_name (str): The name of the node.

        Returns:
            str, the graph name of the node.

        Raises:
            DebuggerNodeNotInGraphError: If can not find the node in all graphs.
        """
        if node_name:
            for graph_name, sub_graph in self._graph.items():
                if sub_graph.exist_node(name=node_name):
                    return graph_name
        log.error('Failed to find node %s in graph. Please make sure the graph has been sent and '
                  'the node name is correct, and try again.', node_name)
        raise DebuggerGraphNotExistError

    def get_graph_id_by_full_name(self, node_name):
        """
        Get graph id by full name.

        Args:
            node_name (str): The full name of the node.

        Returns:
            str, the graph name of the node.

        Raises:
            DebuggerNodeNotInGraphError: If can not find the node in all graphs.
        """
        graph_id = self.graph_node_map.get(node_name) if node_name else None
        if not graph_id:
            log.warning("Failed to get graph id by full name: %s", node_name)
        return graph_id

    def get_node_type(self, node_name, graph_name=None):
        """
        Get the type of the specified node.

        Args:
            node_name (str): The debug name of the node.
            graph_name (str): The relative graph_name of the node. Default: None.

        Returns:
            A string of the node type, name_scope or leaf.
        """
        if graph_name:
            graph = self._get_graph(node_name=node_name, graph_name=graph_name)
        else:
            graph = self._whole_graph
        node_type = graph.get_node_type(node_name)

        return node_type

    def get_full_name(self, node_name, graph_name=None):
        """Get full name according to ui node name."""
        full_name = ''
        if node_name:
            graph = self._get_graph(node_name=node_name, graph_name=graph_name)
            full_name = graph.get_full_name_by_node_name(node_name)

        return full_name

    def get_node_basic_info(self, node_name, graph_name):
        """Get node basic info with graph scope."""
        graph_name, node_name = self._parse_node_name(node_name=node_name, graph_name=graph_name)
        graph = self._get_graph(graph_name, node_name)
        full_name = graph.get_full_name_by_node_name(node_name)
        node_type = graph.get_node_type(node_name)
        return self.construct_node_basic_info(full_name, graph_name, node_name, node_type)

    def get_tensor_graph(self, tensor_name, graph_name):
        """
        Get tensor graph according to node name.

        Args:
            tensor_name (str): Tensor name from UI, format is "node_name:slot".
            graph_name (str): The relative graph_name of the node. Default: None.

        Returns:
            dict, relative node.
        """
        node_name, _ = tensor_name.rsplit(':', 1)
        graph = self._get_graph(graph_name=graph_name, node_name=node_name)
        tensor_graph = graph.get_tensor_graph(node_name)
        return {'graph': tensor_graph}

    @staticmethod
    def construct_node_basic_info(full_name, graph_name, node_name, node_type):
        """Construct node basic info."""
        node_name_with_graph_scope = '/'.join([graph_name, node_name]) if node_name else graph_name
        return NodeBasicInfo(name=node_name_with_graph_scope, full_name=full_name, type=node_type)

    def get_node_basic_info_by_scope(self, scope_name, graph_name):
        """
        Get node by a given scope name.

        Args:
            scope_name (str): The name of scope.
            graph_name (str): The relative graph_name of the watched node. Default: None.

        Returns:
            list[NodeBasicInfo], a list of node.
        """
        graph_name, node_name = self._parse_node_name(scope_name, graph_name)
        graph = self._get_graph(graph_name)
        # to make sure fully match the scope name
        node_name = node_name + '/' if node_name and not node_name.endswith('/') else node_name
        nodes = graph.search_leaf_nodes_by_pattern(node_name, True)
        res = [self.construct_node_basic_info(full_name=node.full_name,
                                              graph_name=graph_name,
                                              node_name=node.name,
                                              node_type=node.type) for node in nodes]
        return res

    def get_node_name_by_full_name(self, full_name, graph_name):
        """Get UI node name by full name and graph name."""
        if graph_name and full_name:
            graph = self._get_graph(graph_name)
            node_name = graph.get_node_name_by_full_name(full_name)
        else:
            node_name = ''
            log.debug("Get empty full name.")
        return node_name

    def _graph_exists(self):
        """
        Check if the graph has been loaded in the debugger cache.

        Raises:
            DebuggerGraphNotExistError: If the graph does not exist.
        """
        if not self._graph:
            log.error('The graph does not exist. Please start the '
                      'training script and try again.')
            raise DebuggerGraphNotExistError

    def _get_graph(self, graph_name=None, node_name=None):
        """
        Get the graph object according to graph name and node name.

        Args:
            graph_name (str): The graph name.
            node_name (str): The node name.

        Returns:
            DebuggerGraph, the graph object.

        Raises:
            DebuggerGraphNotExistError: If the graph does not exist.
        """
        graph = self._graph.get(graph_name) if graph_name else self._whole_graph
        # get graph according to graph name and check the node
        if graph and (not node_name or graph.exist_node(name=node_name)):
            return graph
        log.error('The graph %s does not exist node %s.', graph_name, node_name)
        raise DebuggerGraphNotExistError

    def _has_graph_scope(self, graph_name):
        """Check if query with graph_scope."""
        return bool(graph_name is None and len(self._graph) > 1)

    def validate_graph_name(self, graph_name):
        """Validate graph_name."""
        if graph_name and self._graph.get(graph_name) is None:
            log.error("No graph named %s in debugger cache.", graph_name)
            raise DebuggerGraphNotExistError
        if not graph_name and len(self._graph) == 1:
            graph_name = self.graph_names[0]
        return graph_name

    def _add_graph_scope_for_nodes(self, nodes, graph_name):
        """
        Add graph scope for nodes.

        Args:
            nodes (list[Node]): List of nodes object.
            graph_name (str): The graph name.
        """

        def _get_updated_node_info(cur_node, node_type):
            """Add graph scope in key."""
            old_node = cur_node.get(node_type)
            if not old_node:
                return
            new_values = {}
            for old_name, node_info in old_node.items():
                new_name = '/'.join([graph_name, old_name]) if old_name else graph_name
                new_values[new_name] = node_info
            cur_node[node_type] = new_values

        for node in nodes:
            node['name'] = '/'.join([graph_name, node['name']]) if node['name'] else graph_name
            _get_updated_node_info(node, 'input')
            _get_updated_node_info(node, 'output')
            if node.get('nodes'):
                self._add_graph_scope_for_nodes(node.get('nodes'), graph_name)

    def _parse_node_name(self, node_name, graph_name):
        """
        Parse node_name according to graph_name.

        Args:
            node_name (str): The ui node name.
            graph_name (str): The graph name.

        Returns:
            str, parsed graph name.
            str, parsed node name.
        """
        node_name = '' if node_name is None else node_name
        if self._has_graph_scope(graph_name):
            names = node_name.split("/", 1)
            graph_name = names[0]
            node_name = names[1] if len(names) == 2 else ''
        if graph_name is None and len(self._graph) == 1:
            graph_name = self.graph_names[0]
        return graph_name, node_name

    def validate_node_name(self, node_name, graph_name):
        """
        Validate the graph exist the specified node.

        Args:
            node_name (str): The ui node name.
            graph_name (str): The graph name.

        Raises:
            DebuggerNodeNotInGraphError: If can not find the node in all graphs.
        """
        graph = self._get_graph(graph_name=graph_name)
        if not graph.exist_node(name=node_name):
            log.error("graph %s doesn't find node: %s.", graph_name, node_name)
            raise DebuggerNodeNotInGraphError(node_name)

    @staticmethod
    def _sort_graph(graphs):
        """
        Sort graph by graph_name.

        Args:
            graphs(dict): <graph_name, GraphProto object>.
        """
        if len(graphs) == 1:
            return graphs.items()
        sorted_graphs = sorted(graphs.items(), key=lambda x: get_graph_number(x[0]))
        return sorted_graphs

    def get_root_graph_id(self, graph_name, node_name=None):
        """Get the root_graph_id of a graph."""
        graph_name, node_name = self._parse_node_name(node_name=node_name, graph_name=graph_name)
        graph = self._get_graph(graph_name=graph_name)
        return graph.root_graph_id


def get_graph_number(graph_name):
    """Get the number of graph."""
    number = graph_name.split("_")[-1]
    return int(number)

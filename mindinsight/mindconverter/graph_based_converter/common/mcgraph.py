# Copyright 2021 Huawei Technologies Co., Ltd.All Rights Reserved.
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
# ==============================================================================
"""The definition of ConverterGraph class."""
from mindinsight.datavisual.common.log import logger
from mindinsight.datavisual.data_transform.graph.node import Node
from mindinsight.datavisual.data_transform.graph.graph import check_invalid_character
from mindinsight.datavisual.data_transform.graph.msgraph import MSGraph
from mindinsight.debugger.stream_cache.source import DebuggerSource


class ConverterGraph(MSGraph):
    """The object describes the MindConverter graph, and it is defined in the anf_ir proto file."""
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

            node_name = node_proto.name

            # The Graphviz plug-in that the UI USES can't handle these special characters.
            check_invalid_character(node_name)

            node = Node(name=node_name, node_id=node_proto.name, topological_index=topological_index)
            node.full_name = node_proto.full_name
            node.type = node_proto.op_type
            if getattr(node_proto, 'source_address', None):
                node.stack = DebuggerSource.build_stack_from_source_address(node_proto.source_address)
            self._parse_attributes(node_proto.attribute, node)
            self._parse_inputs(node_proto.input, node)

            node.output_i = node_proto.output_i
            node.scope = node_proto.scope
            node.output_shape = self._get_shape_by_parse_type_proto(node_proto.output_type)
            node.output_nums = len(node.output_shape)
            node.output_data_type = self._get_data_type_by_parse_type_proto(node_proto.output_type, node)

            self._cache_node(node)

    def _build_aggregation_scope_nodes(self):
        """
        Under the same scope, the number of nodes of the same type will be aggregated.
        """

    def _process_independent_layout(self):
        """Handle separate layout nodes."""

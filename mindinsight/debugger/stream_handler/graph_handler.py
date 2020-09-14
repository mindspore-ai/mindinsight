# Copyright 2020 Huawei Technologies Co., Ltd
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
from mindinsight.debugger.common.log import logger as log
from mindinsight.debugger.stream_cache.debugger_graph import DebuggerGraph
from mindinsight.debugger.stream_handler.base_handler import StreamHandlerBase


class GraphHandler(StreamHandlerBase):
    """Metadata Handler."""

    def __init__(self):
        self._graph_proto = None
        self._graph = None
        self._searched_node_list = []
        self.bfs_order = []

    @property
    def graph(self):
        """The property of graph."""
        return self._graph_proto

    def put(self, value):
        """
        Put value into graph cache. Called by grpc server.

        Args:
            value (GraphProto): The Graph proto message.
        """
        self._graph_proto = value
        log.info("Put graph into cache.")

        # build graph
        graph = DebuggerGraph()
        graph.build_graph(value)
        self._graph = graph
        self.bfs_order = self._graph.get_bfs_order()

    def get(self, filter_condition=None):
        """
        Get the graph of specific node.

        Args:
            filter_condition (dict):

                - name (str): The full debug node name.

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

        if filter_condition is None:
            filter_condition = {}
        single_node = filter_condition.get('single_node', False)
        name = filter_condition.get('name')

        graph = {}
        if single_node is True:
            nodes = self.get_single_node(name)
        else:
            nodes = self.list_nodes(name)
        graph.update(nodes)

        return {'graph': graph}

    def get_tensor_history(self, node_name, depth=0):
        """
        Get the tensor history of a specified node.

        Args:
            node_name (str): The debug name of the node.
            depth (int): The number of layers the user
                wants to trace. Default is 0.

        Returns:
            dict, basic tensor history, only including tensor name and tensor type and node type.
        """
        self._graph_exists()
        if not self._graph.exist_node(node_name):
            raise DebuggerNodeNotInGraphError(node_name)

        tensor_history, cur_outputs_nums = self._graph.get_tensor_history(
            node_name, depth
        )
        # add the tensor type for tensor history
        self._update_tensor_history(tensor_history[0:cur_outputs_nums], 'output')
        self._update_tensor_history(tensor_history[cur_outputs_nums:], 'input')
        log.debug("Get %d tensors in tensor history for node <%s>.", len(tensor_history), node_name)
        return {'tensor_history': tensor_history}

    @staticmethod
    def _update_tensor_history(tensor_history, tensor_type):
        """
        Add tensor source type for tensor history.

        Args:
            tensor_history (list[dict]): Tensor history from Graph stream. Each element has two
                keys: `node_type` and `name`. `node_type` refers to the type of the node which
                the tensor come from. `name` refers to the tensor name.
            tensor_type (str): The source type of the tensor. `input` or `output`.
        """
        for single_tensor_info in tensor_history:
            single_tensor_info['type'] = tensor_type

    def search_nodes(self, pattern):
        """
        Search nodes by given pattern.

        Args:
            pattern (Union[str, None]): The pattern of the node to search,
                if None, return all node names.

        Returns:
            dict, the searched node.
        """
        self._graph_exists()
        self._searched_node_list = self._graph.search_nodes_by_pattern(pattern)
        nodes = self._graph.get_nodes(self._searched_node_list)

        return {'nodes': nodes}

    def get_node_names(self, pattern=None):
        """Get graph nodes according to pattern."""
        return self._graph.search_nodes_by_pattern(pattern)

    def get_searched_node_list(self):
        """Get searched node list."""
        return self._searched_node_list

    def get_node_type(self, node_name):
        """
        Get the type of the specified node.

        Args:
            node_name (str): The debug name of the node.

        Returns:
            A string of the node type, name_scope or leaf.
        """
        self._graph_exists()
        node_type = self._graph.get_node_type(node_name)

        return node_type

    def get_full_name(self, node_name):
        """Get full name according to ui node name."""
        full_name = self._graph.get_full_name_by_node_name(node_name) if node_name else ''
        return full_name

    def get_node_name_by_full_name(self, full_name):
        """Get UI node name by full name."""
        if self._graph:
            node_name = self._graph.get_node_name_by_full_name(full_name)
        else:
            node_name = ''
            log.info("No graph received yet.")
        return node_name

    def list_nodes(self, scope):
        """
        Get the nodes of every layer in graph.

        Args:
            scope (str): The name of a scope.

        Returns:
            TypedDict('Nodes', {'nodes': list[Node]}), format is {'nodes': [<Node object>]}.
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
        if scope and not self._graph.exist_node(scope):
            raise DebuggerNodeNotInGraphError(node_name=scope)

        nodes = self._graph.list_node_by_scope(scope=scope)
        return {'nodes': nodes}

    def get_node_by_bfs_order(self, node_name=None, ascend=True):
        """
        Traverse the graph in order of breath-first search by given node.

        Args:
            node_name (str): The name of current chosen leaf node.
            ascend (bool): If True, traverse the input nodes;
                If False, traverse the output nodes. Default is True.

        Returns:
            Union[None, dict], the next node object in dict type or None.
        """
        self._graph_exists()
        bfs_order = self.bfs_order
        length = len(bfs_order)

        if not bfs_order:
            log.error('Cannot get the BFS order of the graph!')
            msg = 'Cannot get the BFS order of the graph!'
            raise DebuggerParamValueError(msg)

        if node_name is None:
            if ascend is False:
                next_node = None
            else:
                next_node = bfs_order[0]
        else:
            try:
                index = bfs_order.index(node_name)
                log.debug("The index of the node in BFS list is: %d", index)
            except ValueError as err:
                log.error('Cannot find the node: %s. Please check '
                          'the node name: %s', node_name, err)
                msg = f'Cannot find the node: {node_name}. ' \
                      f'Please check the node name {err}.'
                raise DebuggerParamValueError(msg)

            next_node = self.get_next_node_in_bfs(index, length, ascend)

        return next_node

    def get_next_node_in_bfs(self, index, length, ascend):
        """
        Get the next node in bfs order.

        Args:
            index (int): The current index.
            length (int): The number of all leaf nodes.
            ascend (bool): Whether get the node in ascend order or not.

        Returns:
            Union[None, dict], the next node object in dict type or None.
        """
        next_node = None
        if 0 <= index < length:
            if ascend is True and index < length - 1:
                next_node = self.bfs_order[index + 1]
            elif ascend is False and index > 0:
                next_node = self.bfs_order[index - 1]

        return next_node

    def get_single_node(self, name):
        """
        Search node, and return every layer nodes until this node.

        Args:
            name (str): The name of node.

        Returns:
            dict, every layer nodes until this node.
        """
        nodes = self._graph.search_single_node(name)

        return nodes

    def _graph_exists(self):
        """
        Check if the graph has been loaded in the debugger cache.

        Raises:
            DebuggerGraphNotExistError: If the graph does not exist.
        """
        if self._graph is None:
            log.error('The graph does not exist. Please start the '
                      'training script and try again.')
            raise DebuggerGraphNotExistError

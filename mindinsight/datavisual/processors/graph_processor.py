# Copyright 2019 Huawei Technologies Co., Ltd
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
"""
This file is to process `data_transform.data_manager` to handle graph,
and the status of graph will be checked before calling `Graph` object.
"""

from mindinsight.datavisual.common import exceptions
from mindinsight.datavisual.common.enums import PluginNameEnum
from mindinsight.datavisual.common.validation import Validation
from mindinsight.datavisual.data_transform.graph import NodeTypeEnum
from mindinsight.datavisual.processors.base_processor import BaseProcessor
from mindinsight.utils.exceptions import ParamValueError


class GraphProcessor(BaseProcessor):
    """
    This object is to handle `DataManager` object, and process graph object.

    Args:
        train_id (str): To get train job data by this given id.
        data_manager (DataManager): A `DataManager` object.
        tag (str): The tag of graph, if tag is None, will load the first graph.
    """
    def __init__(self, train_id, data_manager, tag=None):
        Validation.check_param_empty(train_id=train_id)
        super(GraphProcessor, self).__init__(data_manager)

        train_job = self._data_manager.get_train_job_by_plugin(train_id, PluginNameEnum.GRAPH.value)
        if train_job is None:
            raise exceptions.TrainJobNotExistError()
        if not train_job['tags']:
            raise exceptions.GraphNotExistError()

        if tag is None:
            tag = train_job['tags'][0]

        tensors = self._data_manager.list_tensors(train_id, tag=tag)
        self._graph = tensors[0].value

    def get_nodes(self, name, node_type):
        """
        Get the nodes of every layer in graph.

        Args:
            name (str): The name of a node.
            node_type (Any): The type of node, either 'name_scope' or 'polymeric'.

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
                          "polymeric_input" : {},
                          "polymeric_output" : {},
                          "polymeric_scope_name" : "",
                          "subnode_count" : 0,
                          "type" : "Data"
                        }
                      ]
                    }
        """
        if node_type not in [NodeTypeEnum.NAME_SCOPE.value, NodeTypeEnum.POLYMERIC_SCOPE.value]:
            raise ParamValueError(
                'The node type is not support, only either %s or %s.'
                '' % (NodeTypeEnum.NAME_SCOPE.value, NodeTypeEnum.POLYMERIC_SCOPE.value))

        if name and not self._graph.exist_node(name):
            raise ParamValueError("The node name is not in graph.")
        nodes = []
        if node_type == NodeTypeEnum.NAME_SCOPE.value:
            nodes = self._graph.get_normal_nodes(name)

        if node_type == NodeTypeEnum.POLYMERIC_SCOPE.value:
            if not name:
                raise ParamValueError('The node name "%s" not in graph, node type is %s.' %
                                      (name, node_type))
            polymeric_scope_name = name
            nodes = self._graph.get_polymeric_nodes(polymeric_scope_name)

        return {'nodes': nodes}

    def search_node_names(self, search_content, offset, limit):
        """
        Search node names by search content.

        Args:
            search_content (Any): This content can be the key content of the node to search.
            offset (int): An offset for page. Ex, offset is 0, mean current page is 1.
            limit (int): The max data items for per page.

        Returns:
            TypedDict('Names', {'names': list[str]}), {"names": ["node_names"]}.
        """
        offset = Validation.check_offset(offset=offset)
        limit = Validation.check_limit(limit, min_value=1, max_value=1000)
        names = self._graph.search_node_names(search_content, offset, limit)
        return {"names": names}

    def search_single_node(self, name):
        """
        Search node by node name.

        Args:
            name (str): The name of node.

        Returns:
            dict, format is:
                item_object = {'nodes': [<Node object>],
                       'scope_name': '',
                       'children': {<item_object>}}
        """
        Validation.check_param_empty(name=name)

        nodes = self._graph.search_single_node(name)
        return nodes

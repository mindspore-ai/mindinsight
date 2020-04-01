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
This file is used to define the basic graph.
"""
import copy
import time

from enum import Enum

from mindinsight.datavisual.common.log import logger
from mindinsight.datavisual.common import exceptions
from .node import NodeTypeEnum
from .node import Node


class EdgeTypeEnum(Enum):
    """Node edge type enum."""
    CONTROL = 'control'
    DATA = 'data'


class DataTypeEnum(Enum):
    """Data type enum."""
    DT_TENSOR = 13


class Graph:
    """The `Graph` object is used to describe a graph file."""
    MIN_POLYMERIC_NODE_COUNT = 5

    def __init__(self):
        # Store nodes contain leaf nodes, name scope node, except polymeric nodes
        self._normal_nodes = {}

        # Store polymeric nodes.
        self._polymeric_nodes = {}

        # Store all nodes resolved from the file.
        self._leaf_nodes = {}

        # The format of node groups is {'group_name': {'node_name': <Node>}}
        self._node_groups = {}

    def exist_node(self, name):
        """
        Check node exist in graph.

        Args:
            name (str): The node name.

        Returns:
            bool, if node is exist will return True.

        """
        if self._normal_nodes.get(name) is None:
            return False
        return True

    def get_normal_nodes(self, namescope=None):
        """
        Get nodes by namescope.

        Args:
            namescope (str): A namescope of nodes.

        Returns:
            list[dict], a list object contain `Node` object.

        """
        nodes = []
        if namescope is None:
            for name, node in self._normal_nodes.items():
                if '/' not in name:
                    # Get first layer nodes
                    nodes.append(node.to_dict())
            return nodes

        namescope = namescope + '/'
        for name, node in self._normal_nodes.items():
            if name.startswith(namescope) and '/' not in name.split(namescope)[1]:
                nodes.append(node.to_dict())

        return nodes

    def get_polymeric_nodes(self, polymeric_scope):
        """
        Get polymeric nodes by polymeric scope.

        Args:
            polymeric_scope (str): The polymeric scope name of nodes.

        Returns:
            list[dict], a list object contain `Node` object.
        """
        nodes = []
        for node in self._polymeric_nodes.values():
            if node.polymeric_scope_name == polymeric_scope:
                nodes.append(node.to_dict())
        return nodes

    def search_node_names(self, content, offset, limit):
        """
        Search node names by content.

        Args:
            content (Union[str, None]): This content can be the key content of the node to search,
                if None, will get all node names.
            offset (int): An offset for page. Ex, offset is 0, mean current page is 1.
            limit (int): An offset for page. Ex, offset is 0, mean current page is 1.

        Returns:
            list[str], a list of node names.
        """
        all_names = []
        all_names.extend(list(self._normal_nodes.keys()))
        all_names.extend(list(self._polymeric_nodes.keys()))
        if content is not None:
            content = content.lower()
            catch_names = [name for name in all_names if content in name.lower()]
        else:
            catch_names = all_names
        catch_names = sorted(catch_names)
        real_offset = offset * limit
        return catch_names[real_offset:real_offset+limit]

    def search_single_node(self, node_name):
        """
        Search node, and return every layer nodes until this node.

        Args:
            node_name (str): The name of node.

        Returns:
            dict, a dict object, format is :
                item_object = {'nodes': [<Node object>],
                               'scope_name': '<Node scope>',
                               'children': {<item_object>}}
        """
        if node_name and self._polymeric_nodes.get(node_name) is None \
                and self._normal_nodes.get(node_name) is None:
            raise exceptions.NodeNotInGraphError()

        response = {}
        nodes = self.get_normal_nodes()
        response.update({
            'nodes': nodes,
            'scope_name': '',
            'children': {}
        })

        names = node_name.split('/')
        children = response['children']
        for i in range(1, len(names)+1):
            if i == len(names):
                polymeric_node = self._polymeric_nodes.get(node_name)
                if polymeric_node:
                    polymeric_scope = polymeric_node.polymeric_scope_name
                    nodes = self.get_polymeric_nodes(polymeric_scope)
                    children.update({'nodes': nodes,
                                     'scope_name': polymeric_scope,
                                     'children': {}})
                break

            name_scope = '/'.join(names[:i])
            nodes = self.get_normal_nodes(name_scope)
            children.update({
                'nodes': nodes,
                'scope_name': name_scope,
                'children': {}
            })
            children = children['children']

        return response

    def _build_polymeric_nodes(self):
        """Build polymeric node."""
        logger.debug("Start to build polymeric nodes")

        self._find_polymeric_nodes()

        group_count_map = {}
        for group_name, group in self._node_groups.items():
            name = group_name.split('/')[-1]
            count = group_count_map.get(name, 0)
            count += 1
            group_count_map[name] = count
            polymeric_node_name = group_name + '_{}_[{}]'.format(count, len(group))
            polymeric_node = Node(polymeric_node_name, node_id=polymeric_node_name)
            polymeric_node.node_type = NodeTypeEnum.POLYMERIC_SCOPE.value
            polymeric_node.name_scope = '/'.join(group_name.split('/')[:-1])
            polymeric_node.subnode_count = len(group)

            for name_tmp, node_tmp in group.items():
                node_tmp.polymeric_scope_name = polymeric_node_name
                self._polymeric_nodes.update({name_tmp: node_tmp})
                polymeric_node.update_input(node_tmp.input)
                polymeric_node.update_output(node_tmp.output)

            self._normal_nodes.update({polymeric_node_name: polymeric_node})

        self._update_input_output()

    def _find_polymeric_nodes(self):
        """Find polymeric nodes from node groups."""
        node_groups = copy.deepcopy(self._node_groups)
        for group_name, group in node_groups.items():
            if len(group) < self.MIN_POLYMERIC_NODE_COUNT:
                self._normal_nodes.update(group)
                self._node_groups.pop(group_name)
                continue

            move_node_names = []
            is_move_group = False
            for node_name, group_node in group.items():
                node_list = []
                is_in_group = False
                for dst_name in group_node.output:
                    node_tmp = self._leaf_nodes[dst_name]
                    node_list.append(node_tmp)

                start = time.time()
                run_count = 0
                visit_nodes = {}
                while node_list:
                    # Iterate to find if the output of the node in the group causes a loop
                    # example: there is a group A, and node_a is a Node in group.
                    # if there is a loop in node_a, like A/node_a -> B/node_b -> A/node_b
                    # we will remove the node_a from group A.
                    node_tmp = node_list[0]
                    node_list = node_list[1:]
                    visit_nodes.update({node_tmp.name: True})
                    if node_tmp in group.values():
                        is_in_group = True
                        break
                    for dst_name_tmp in node_tmp.output:
                        run_count += 1
                        node_tmp = self._leaf_nodes[dst_name_tmp]
                        if visit_nodes.get(dst_name_tmp):
                            continue
                        node_list.append(node_tmp)
                logger.debug("Find group %s node end, is_in_group: %s, use time: %s, "
                             "run count: %s.", group_name, is_in_group,
                             time.time() - start, run_count)

                if is_in_group:
                    move_node_names.append(node_name)

                if (len(group) - len(move_node_names)) < self.MIN_POLYMERIC_NODE_COUNT:
                    is_move_group = True
                    break

            if is_move_group:
                self._normal_nodes.update(group)
                self._node_groups.pop(group_name)
            else:
                for name_tmp in move_node_names:
                    node_tmp = self._node_groups[group_name].pop(name_tmp)
                    self._normal_nodes.update({name_tmp: node_tmp})

    def _update_input_output(self):
        """We need to update input and output attribute after build polymeric node."""
        for node in self._normal_nodes.values():
            for src_name, input_attr in node.input.items():
                if self._polymeric_nodes.get(src_name):
                    input_attr['scope'] = NodeTypeEnum.POLYMERIC_SCOPE.value
                    node.update_input({src_name: input_attr})

            for dst_name, output_attr in node.output.items():
                if self._polymeric_nodes.get(dst_name):
                    output_attr['scope'] = NodeTypeEnum.POLYMERIC_SCOPE.value
                    node.update_output({dst_name: output_attr})

        for node in self._polymeric_nodes.values():
            for src_name, input_attr in node.input.items():
                if self._polymeric_nodes.get(src_name):
                    input_attr['scope'] = NodeTypeEnum.POLYMERIC_SCOPE.value
                    node.update_input({src_name: input_attr})

            for dst_name, output_attr in node.output.items():
                if self._polymeric_nodes.get(dst_name):
                    output_attr['scope'] = NodeTypeEnum.POLYMERIC_SCOPE.value
                    node.update_output({dst_name: output_attr})

    def _update_polymeric_input_output(self):
        """Calc polymeric input and output after build polymeric node."""
        for node in self._normal_nodes.values():
            polymeric_input = self._calc_polymeric_attr(node, 'input')
            node.update_polymeric_input(polymeric_input)

            polymeric_output = self._calc_polymeric_attr(node, 'output')
            node.update_polymeric_output(polymeric_output)

        for name, node in self._polymeric_nodes.items():
            polymeric_input = {}
            for src_name in node.input:
                output_name = self._calc_dummy_node_name(name, src_name)
                polymeric_input.update({output_name: {'edge_type': EdgeTypeEnum.DATA.value}})
            node.update_polymeric_input(polymeric_input)

            polymeric_output = {}
            for dst_name in node.output:
                polymeric_output = {}
                output_name = self._calc_dummy_node_name(name, dst_name)
                polymeric_output.update({output_name: {'edge_type': EdgeTypeEnum.DATA.value}})
            node.update_polymeric_output(polymeric_output)

    def _calc_polymeric_attr(self, node, attr):
        """
        Calc polymeric input or polymeric output after build polymeric node.

        Args:
            node (Node): Computes the polymeric input for a given node.
            attr (str): The polymeric attr, optional value is `input` or `output`.

        Returns:
            dict, return polymeric input or polymeric output of the given node.
        """
        polymeric_attr = {}
        for node_name in getattr(node, attr):
            polymeric_node = self._polymeric_nodes.get(node_name)
            if node.node_type == NodeTypeEnum.POLYMERIC_SCOPE.value:
                node_name = node_name if not polymeric_node else polymeric_node.polymeric_scope_name
                dummy_node_name = self._calc_dummy_node_name(node.name, node_name)
                polymeric_attr.update({dummy_node_name: {'edge_type': EdgeTypeEnum.DATA.value}})
                continue

            if not polymeric_node:
                continue

            if not node.name_scope and polymeric_node.name_scope:
                # If current node is in top-level layer, and the polymeric_node node is not in
                # the top-level layer, the polymeric node will not be the polymeric input
                # or polymeric output of current node.
                continue

            if node.name_scope == polymeric_node.name_scope \
                    or node.name_scope.startswith(polymeric_node.name_scope + '/'):
                polymeric_attr.update(
                    {polymeric_node.polymeric_scope_name: {'edge_type': EdgeTypeEnum.DATA.value}})

        return polymeric_attr

    def _calc_dummy_node_name(self, current_node_name, other_node_name):
        """
        Calc dummy node name.

        Args:
            current_node_name (str): The name of current node.
            other_node_name (str): The target dummy node name.

        Returns:
            str, the dummy node name.
        """
        name_tmp = other_node_name
        if self._polymeric_nodes.get(other_node_name):
            name_tmp = self._polymeric_nodes[other_node_name].polymeric_scope_name
        name_tmp_list = name_tmp.split('/')
        current_name_list = current_node_name.split('/')
        index = 0
        min_len = min(len(name_tmp_list), len(current_name_list))
        for i in range(min_len):
            index = i
            if name_tmp_list[index] != current_name_list[index]:
                break
        dummy_node_name = '/'.join(name_tmp_list[:index+1])
        return dummy_node_name

    def _build_name_scope_nodes(self):
        """Build name scope node by every node name."""
        normal_nodes = dict(self._normal_nodes)

        rename_node_names = {}
        for name, node in normal_nodes.items():
            name_list = name.split('/')
            for i in range(1, len(name_list)):
                name_scope = '/'.join(name_list[:i])
                name_scope_node = self._normal_nodes.get(name_scope)
                if name_scope_node is None:
                    name_scope_node = Node(name_scope, node_id=name_scope)
                    name_scope_node.node_type = NodeTypeEnum.NAME_SCOPE.value
                    name_scope_node.name_scope = '/'.join(name_list[:i-1])
                elif name_scope_node.node_type != NodeTypeEnum.NAME_SCOPE.value:
                    # The name of this node conflicts with namescope, so rename this node
                    old_name = name_scope_node.name
                    old_names = name_scope_node.name.split('/')
                    old_names[-1] = f'({old_names[-1]})'
                    new_name = '/'.join(old_names)
                    name_scope_node.name = new_name
                    self._normal_nodes.pop(old_name)
                    self._normal_nodes.update({new_name: name_scope_node})
                    rename_node_names.update({old_name: new_name})

                    # create new namescope
                    name_scope_node = Node(name_scope, node_id=name_scope)
                    name_scope_node.node_type = NodeTypeEnum.NAME_SCOPE.value
                    name_scope_node.name_scope = '/'.join(name_list[:i-1])

                # update the input and output of this to namescope node
                name_scope_with_slash = name_scope + '/'
                for src_name, input_attr in node.input.items():
                    if src_name.startswith(name_scope_with_slash):
                        continue
                    name_scope_node.update_input({src_name: input_attr})

                for dst_name, output_attr in node.output.items():
                    if dst_name.startswith(name_scope_with_slash):
                        continue
                    name_scope_node.update_output({dst_name: output_attr})

                self._normal_nodes.update({name_scope: name_scope_node})

        if rename_node_names:
            # If existing nodes are renamed, the inputs and outputs of all nodes need to be refreshed
            nodes = []
            nodes.extend(self._normal_nodes.values())
            nodes.extend(self._polymeric_nodes.values())
            for node in nodes:
                attrs = ['input', 'output', 'polymeric_input', 'polymeric_output']
                for item in attrs:
                    tmp_dict = dict(getattr(node, item))
                    for name, value in tmp_dict.items():
                        new_name = rename_node_names.get(name, False)
                        if new_name:
                            getattr(node, item).pop(name)
                            getattr(node, f'update_{item}')({new_name: value})

        self._calc_subnode_count()

    def _calc_subnode_count(self):
        """Calc the sub node count of scope node."""
        name_scope_mapping = {}
        for node in self._normal_nodes.values():
            if node.name_scope:
                count = name_scope_mapping.get(node.name_scope, 0)
                name_scope_mapping[node.name_scope] = count + 1

        for name_scope, count in name_scope_mapping.items():
            node = self._normal_nodes[name_scope]
            node.subnode_count = count

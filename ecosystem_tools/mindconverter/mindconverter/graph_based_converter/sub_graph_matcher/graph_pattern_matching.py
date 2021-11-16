# Copyright 2021 Huawei Technologies Co., Ltd.All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Match the struct of patterns and that of the whole model."""
import itertools
from collections import OrderedDict

import networkx as nx
import networkx.algorithms.isomorphism as iso
from mindconverter.graph_based_converter.constant import FrameworkType


class GraphMatcher:
    """Find all sub-graphs in model which have the same structure with the pattern."""

    def __init__(self, model_or_nodes, framework=None, known_blocks=None):
        self._nodes_dict = self._extract_node_info(model_or_nodes, framework or FrameworkType.ONNX)
        self._known_blocks = known_blocks or dict()

    def _extract_node_info(self, model_or_nodes, framework):
        """Extract node info."""
        if framework == FrameworkType.ONNX:
            return self._extract_onnx_node_info(model_or_nodes)
        if framework == FrameworkType.PYTORCH:
            return self._extract_pytorch_node_info(model_or_nodes)
        raise ValueError("Unsupported framework type found.")

    @staticmethod
    def _extract_onnx_node_info(model):
        """Extract onnx node info from model."""
        nodes = model.graph.node
        initializer_list = [i.name for i in list(model.graph.initializer)]

        nodes_dict = dict()
        for node in nodes:
            inputs = [i for i in node.input if i not in initializer_list]
            nodes_dict[node.name] = {"op_type": node.op_type, "input": inputs, "output": node.output}
        return nodes_dict

    @staticmethod
    def _extract_pytorch_node_info(nodes):
        """Extract pytorch node info from nodes."""
        nodes_dict = dict()
        for node_name, node_inst in nodes.items():
            nodes_dict[node_name] = {"op_type": node_inst.op_type, "input": node_inst.input_name_list,
                                     "output": node_inst.output_name_list}
        return nodes_dict

    def _extract_name(self, output_name):
        """Extract node name based on output name."""
        for node_name, node_inst in self._nodes_dict.items():
            node_outputs = node_inst["output"]
            if output_name in node_outputs:
                return node_name
        return None

    def _extract_edges(self, pattern_nodes=None):
        """Extract edges based on input and output of nodes in pattern_nodes."""
        if pattern_nodes:
            input_output_list = [(self._nodes_dict[node]["input"], self._nodes_dict[node]["output"]) for node in
                                 pattern_nodes]
        else:
            input_output_list = [(v["input"], v["output"]) for v in self._nodes_dict.values()]

        edge_map_list = list()
        for in_out in input_output_list:
            full_combination_in_out = list(itertools.product(in_out[0], in_out[1]))
            if pattern_nodes:
                edge_map = [(self._extract_name(v[0]), self._extract_name(v[1])) for v in full_combination_in_out if
                            self._extract_name(v[0]) in pattern_nodes and self._extract_name(v[1]) in pattern_nodes]
            else:
                edge_map = [(self._extract_name(v[0]), self._extract_name(v[1])) for v in full_combination_in_out if
                            self._extract_name(v[0]) and self._extract_name(v[1])]
            edge_map_list.extend(edge_map)
        return edge_map_list

    def _build_graph(self, pattern_node=None):
        """Build graph."""
        edge_map_list = self._extract_edges(pattern_node)

        graph = nx.Graph()
        if edge_map_list:
            graph.add_edges_from(edge_map_list)
        else:
            graph.add_nodes_from(pattern_node)
        for node_name in graph.nodes:
            if node_name:
                graph.nodes[node_name]["op_type"] = self._nodes_dict[node_name]["op_type"]
        return graph

    @staticmethod
    def _check_repeat_node(nodes_list):
        """
        Check whether repeated node exists in sub-graph.

        Args:
            nodes_list (list): List including matched pattern nodes.
        """
        all_node_list = list()
        for nodes in nodes_list:
            all_node_list += nodes
            all_node_set = set(all_node_list)
            if len(all_node_set) != len(all_node_list):
                return True
        return False

    def _matcher(self, pattern_nodes):
        """Get one matched nodes list in model."""
        graph_model = self._build_graph()
        graph_patten = self._build_graph(pattern_nodes)

        if len(list(nx.connected_components(graph_patten))) > 1:
            return [pattern_nodes]

        graph_match = iso.GraphMatcher(graph_model, graph_patten,
                                       node_match=iso.categorical_node_match("op_type", None))
        if not graph_match.subgraph_is_isomorphic():
            return [pattern_nodes]

        matched_sub_graphs = list()
        for sub_graph in graph_match.subgraph_isomorphisms_iter():
            matched_sub_graphs.append(list(sub_graph.keys()))
        return matched_sub_graphs if not self._check_repeat_node(matched_sub_graphs) else [pattern_nodes]

    def _extract_full_pattern_nodes(self, pattern_nodes):
        """Extract full pattern nodes from multi-layers construct module."""
        full_pattern_nodes = list()
        for node in pattern_nodes:
            if node in self._known_blocks:
                full_pattern_nodes.extend(self._extract_full_pattern_nodes(self._known_blocks.get(node)))
            else:
                full_pattern_nodes.append(node)
        return full_pattern_nodes

    def _zip_matched_pattern_all_nodes(self, matched_pattern_all_nodes):
        """Zip matched pattern with all nodes to that with known blocks."""
        zipped_matched_pattern = dict()
        for module_name, matched_pattern_nodes in matched_pattern_all_nodes.items():
            zipped_matched_pattern_nodes = list()
            for nodes in matched_pattern_nodes:
                zipped_nodes = set(nodes)
                for known_name, known_nodes in self._known_blocks.items():
                    length_before_zipped_nodes = len(zipped_nodes)
                    zipped_nodes = set(zipped_nodes).difference(known_nodes)
                    if len(zipped_nodes) < length_before_zipped_nodes:
                        zipped_nodes.add(known_name)
                zipped_matched_pattern_nodes.append(list(zipped_nodes))
            zipped_matched_pattern[module_name] = zipped_matched_pattern_nodes
        return zipped_matched_pattern

    def full_matcher(self, patterns):
        """
        Get full match nodes list in model.

        Args:
            patterns (dict): self-defined patterns.
            For example,
                {
                    "module_0": ["conv_0", "bn_0", "relu_0"]
                }
        """
        matched_patterns_all_nodes = dict()
        for module_name, pattern_nodes in patterns.items():
            full_pattern_nodes = self._extract_full_pattern_nodes(pattern_nodes)
            matched_patterns_all_nodes[module_name] = self._matcher(full_pattern_nodes)
        matched_patterns = self._zip_matched_pattern_all_nodes(matched_patterns_all_nodes)
        return matched_patterns

    def is_matched(self, pattern_nodes0, pattern_nodes1, known_blocks):
        """Check whether two patterns are same or not."""
        self._known_blocks = {f"{idx}": list(pattern.values())[0] for idx, pattern in enumerate(known_blocks)}
        full_pattern_nodes0 = self._extract_full_pattern_nodes(pattern_nodes0)
        full_pattern_nodes1 = self._extract_full_pattern_nodes(pattern_nodes1)

        graph_0 = self._build_graph(full_pattern_nodes0)
        graph_1 = self._build_graph(full_pattern_nodes1)
        graph_match = iso.GraphMatcher(graph_0, graph_1, node_match=iso.categorical_node_match("op_type", None))
        return graph_match.is_isomorphic()

    @staticmethod
    def _extract_edges_from_self_pattern(self_pattern):
        """
        Extract edges from self_pattern.

        Args:
            self_pattern (dict): self-defined op_type pattern.
            {
                "op1": {
                    "op_type": "size",
                    "input": None,
                    "output": ["op1"]
                },
                "op2": {
                    "op_type": "view",
                    "input": ["op1"],
                    "output": ["op2"]
                },
                "op3": {
                    "op_type": "permute",
                    "input": ["op2"],
                    "output": ["op3"]
                },
                "op4": {
                    "op_type": "contiguous",
                    "input": ["op3"],
                    "output": ["op4"]
                }
            }
        """
        input_output_list = [(self_pattern[name]["input"], self_pattern[name]["output"]) for name in self_pattern]
        edge_map_list = list()
        for in_out in input_output_list:
            if not all(in_out):
                continue
            full_combination_in_out = list(itertools.product(in_out[0], in_out[1]))
            edge_map_list.extend(full_combination_in_out)
        return edge_map_list

    def _build_graphs_from_self_patterns(self, self_patterns):
        """Build graphs from every pattern."""
        graphs_dict = dict()
        for pattern_name, pattern in self_patterns.items():
            edge_map_list = self._extract_edges_from_self_pattern(pattern)
            graph = nx.Graph()
            graph.add_edges_from(edge_map_list)
            for node_name in pattern:
                graph.nodes[node_name]["op_type"] = pattern[node_name]["op_type"]
            graphs_dict[pattern_name] = graph
        return graphs_dict

    def matcher_from_self_patterns(self, self_patterns):
        """Match sub-graph according to self-defined op_type patterns."""
        ordered_patterns = sorted(self_patterns, key=lambda x: len(self_patterns[x]), reverse=True)
        self_patterns_ordered = OrderedDict({name: self_patterns[name] for name in ordered_patterns})
        self_graphs = self._build_graphs_from_self_patterns(self_patterns_ordered)

        model_graph = self._build_graph()
        matched_sub_graphs_dict = dict()
        for pattern_name, graph in self_graphs.items():
            graph_matcher = iso.GraphMatcher(model_graph, graph, node_match=iso.categorical_node_match("op_type", None))

            matched_sub_graphs = list()
            for sub_graph in graph_matcher.subgraph_isomorphisms_iter():
                sub_graph_nodes = set(list(sub_graph.keys()))
                is_repeated = False
                for matched_sub_graph in matched_sub_graphs:
                    if sub_graph_nodes.issubset(set(matched_sub_graph)) or sub_graph_nodes == set(matched_sub_graph):
                        is_repeated = True
                        break
                if not is_repeated:
                    matched_sub_graphs.append(list(sub_graph.keys()))
            if matched_sub_graphs:
                matched_sub_graphs_dict[f"{pattern_name}"] = matched_sub_graphs
        return matched_sub_graphs_dict

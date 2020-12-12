# Copyright 2020 Huawei Technologies Co., Ltd.All Rights Reserved.
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
"""Define PyTorch graph."""
import re
from copy import deepcopy
from typing import Dict, NoReturn

from mindinsight.mindconverter.common.log import logger as log
from .base import Graph
from .input_node import InputNode
from .pytorch_graph_node import PyTorchGraphNode
from .pytorch_graph_parser import PyTorchGraphParser

from ..constant import SEPARATOR_IN_SCOPE, LINK_IN_SCOPE, SEPARATOR_BTW_NAME_AND_ID, SCALAR_WITHOUT_SHAPE, \
    MIN_SCOPE_LENGTH, SEPARATOR_TITLE_AND_CONTENT_IN_CONSTRUCT
from ..constant import LEFT_BUCKET, RIGHT_BUCKET

NONE_SCOPE_OP = {
    "onnx::Add": "Add",
    "onnx::Flatten": "Flatten",
    "onnx::Concat": "Concat",
    "onnx::Squeeze": "Squeeze",
    "onnx::Unsqueeze": "Unsqueeze",
    "onnx::Split": "Split",
    "onnx::Reshape": "Reshape",
    "onnx::Transpose": "Transpose",
    "onnx::Constant": "Constant",
    "onnx::ReduceMean": "ReduceMean"
}


def normalize_scope_name(node, scope_name_dict):
    """
    Rename scope name into uniform.

    Args:
        node (Node): PyTorch node.
        scope_name_dict (dict): Dictionary of scope names with the key node_id.

    Returns:
        str, normalized scope name.
    """
    global NONE_SCOPE_OP

    scope_name = node.scopeName()
    if not scope_name:
        name = [retrieve_scope_name(node, scope_name_dict)]
    else:
        name = scope_name.replace(SEPARATOR_BTW_NAME_AND_ID, '').split(SEPARATOR_IN_SCOPE)
    scopes = []
    for segment in name:
        segment = segment.split(LINK_IN_SCOPE)[0]
        left = segment.find(LEFT_BUCKET)
        right = segment.find(RIGHT_BUCKET)
        if left != -1:
            if segment[left + 1: right].isdigit():
                scopes.append(f"{segment[:left]}_{segment[left + 1: right]}")
            else:
                scopes.append(segment[left + 1: right])
        else:
            scopes.append(segment)
    if node.kind() in NONE_SCOPE_OP.keys():
        scopes.append(NONE_SCOPE_OP[node.kind()])
    scopes = [s for s in scopes if s]
    node_id = PyTorchGraph.get_node_id(node)
    return f"{SEPARATOR_IN_SCOPE.join(scopes)}_{'&'.join(node_id)}"


def retrieve_scope_name(node, scope_name_dict):
    """
    Retrieve scope name from input nodes.

    Args:
        node (Node): PyTorch node.
        scope_name_dict (dict): Dictionary of scope names with the key node_id.

    Return:
        str: Scope name.
    """
    node_content = \
        SEPARATOR_TITLE_AND_CONTENT_IN_CONSTRUCT.join(str(node).split(SEPARATOR_TITLE_AND_CONTENT_IN_CONSTRUCT)[1:])
    node_inputs = re.findall(r"[(](.*?)[)]", node_content)[0]
    node_inputs = re.sub(r"[\s%]", '', node_inputs).split(",")

    scope_name_ipt_nodes = list()
    for node_input in node_inputs:
        if not scope_name_dict.get(node_input, None):
            continue
        scope_name_ipt_nodes.append(scope_name_dict[node_input])

    scope_name_split = list()
    for idx, _ in enumerate(scope_name_ipt_nodes):
        if not scope_name_split:
            scope_name_split = scope_name_ipt_nodes[idx]
        else:
            scope_name_split = [
                sub_scope_name
                for sub_scope_name in scope_name_split if sub_scope_name in scope_name_ipt_nodes[idx]
            ]
    scope_name = SEPARATOR_IN_SCOPE.join(scope_name_split)
    return scope_name


class PyTorchGraph(Graph):
    """
    Define PyTorch graph.

    Args:
        model (Module): PyTorch model.
        sample_shape (tuple): Input shape of the model.

    """

    def __init__(self, model, sample_shape: tuple):
        super(PyTorchGraph, self).__init__(model=model)

        from .torch_utils import unique_state_dict

        self._params_dict = unique_state_dict(model)
        self.build(sample_shape)

    @staticmethod
    def _check_input_shape(input_shape):
        """
        Check input shape.

        Args:
            input_shape (tuple): Input tensor shape.

        """
        if not input_shape:
            err_msg = "`input_shape` can not be None."
            log.error(err_msg)
            raise ValueError(err_msg)

        for item in input_shape:
            if not isinstance(item, int):
                err_msg = "Only support model with one input now, " \
                          "and each shape value in `input_shape` should be int."
                log.error(err_msg)
                raise ValueError(err_msg)

    @staticmethod
    def _extract_shape(shape):
        """
        Extract shape from string-type shape.

        Args:
            shape (str): Shape value in string-type.

        Returns:
            list, shape.
        """
        if "," not in shape:
            return []

        shape_arr = []
        for s in shape.split(","):
            s = s.strip()
            if not s:
                return []
            if ":" in s:
                s = s.split(":")[0]
            s = s.replace("!", "")
            if not s.isdigit():
                return []
            shape_arr.append(int(s))
        return shape_arr

    def _trace_torch_graph(self, input_shape):
        """
        Trace torch computational graph.

        Args:
            input_shape (tuple): Shape.

        Returns:
            object, pytorch graph.
        """
        import torch
        from torch.onnx import OperatorExportTypes
        from .torch_utils import OverloadTorchModuleTemporarily
        from .torch_utils import create_autograd_variable
        from .torch_utils import onnx_tracer

        batched_sample = create_autograd_variable(torch.rand(*input_shape))

        try:
            # Assign execution mode to eval.
            self.model.eval()

            with OverloadTorchModuleTemporarily() as _:
                # In pytorch higher version, trace function has a known.
                graph = onnx_tracer(self.model, batched_sample,
                                    OperatorExportTypes.ONNX)
            return graph
        except RuntimeError as error:
            log.error(str(error))
            log.exception(error)
            raise error

    def build(self, input_shape):
        """
        Build graph tree.

        Args:
            input_shape (tuple): Input shape of model.

        """
        self._check_input_shape(input_shape)

        feed_forward_ipt_shape = tuple(input_shape)
        graph = self._trace_torch_graph(feed_forward_ipt_shape)
        nodes = list(graph.nodes())

        scope_name_dict = dict()

        for node in nodes:
            node_name = normalize_scope_name(node, scope_name_dict)
            scope_name_dict[node_name.split(SEPARATOR_BTW_NAME_AND_ID)[-1]] \
                = list(node_name.split(SEPARATOR_BTW_NAME_AND_ID)[0].split(SEPARATOR_IN_SCOPE))
            output_shape_str_list = re.findall(r'[^()!]+', str(node))
            output_shape_str = output_shape_str_list[1]
            output_shape = self._extract_shape(output_shape_str)
            weight_scope = '.'.join(
                re.findall(r'\[([\w\d.]+)]', node.scopeName())
            )
            node_weight = {}
            for scope, weight in self._params_dict.items():
                split_scope = scope.split('.')
                if '.'.join(split_scope[:-1]) == weight_scope:
                    node_weight[split_scope[-1]] = weight
            self._shape_dict[node_name] = output_shape
            self._nodes_collection[node_name] = PyTorchGraphNode(node, node_weight)
            self._nodes_record[node_name] = node_name

            for node_input in list(node.inputs()):
                # Connect input node and src node.
                nd_id = PyTorchGraph.get_node_id(node_input.node())
                nd_scope_name = node_input.node().kind() in NONE_SCOPE_OP or \
                                node_input.node().scopeName()

                if nd_id and nd_scope_name:
                    node_input_name = normalize_scope_name(
                        node_input.node(), scope_name_dict
                    )
                    self.build_connection(node_input_name, node_name)

        self._unmerge_multi_ipt_opt_script()

        super(PyTorchGraph, self).build(input_shape=input_shape)
        self._collect_ipt_shape_of_each_node(feed_forward_ipt_shape)

    def _collect_ipt_shape_of_each_node(self, input_shape):
        """
        Collect input tensor shape of each node.

        Args:
            input_shape (tuple): Input shape.

        """
        input_node = InputNode(input_shape)
        input_node_name = "{}InputNode"
        for node_name, node in self._nodes_collection.items():
            if node_name in self._input_nodes:
                ipt_nd_name = input_node_name.format(input_node.scope_name)
                input_node.set_scope_name(node.scope_name)
                node.precursor_nodes.insert(0, ipt_nd_name)
                input_node.set_successor_nodes(node_name)
                self._shape_dict[ipt_nd_name] = input_node.output_shape

            if not self._shape_dict[node_name]:
                self._shape_dict[node_name] = SCALAR_WITHOUT_SHAPE

            ipt_shape = []
            for p_nd in node.precursor_nodes:
                shp = self._shape_dict.get(p_nd)
                ipt_shape.append(tuple(shp) if isinstance(shp, list) else shp)

            self._input_shape[node_name] = ipt_shape[0] if len(ipt_shape) == 1 else ipt_shape

    def _generate_module(self):
        """Generate modules."""
        module_dict = dict()
        for node_key, _ in self._nodes_collection.items():
            node_key_in_scope = node_key.split(SEPARATOR_IN_SCOPE)
            if len(node_key_in_scope) < MIN_SCOPE_LENGTH:
                continue

            for idx in range(1, len(node_key_in_scope)):
                node_key_module = SEPARATOR_IN_SCOPE.join(node_key_in_scope[:idx])
                node_name = SEPARATOR_IN_SCOPE.join(node_key_in_scope[:idx+1])
                if not module_dict.get(node_key_module, None):
                    module_dict[node_key_module] = {node_name}
                else:
                    module_dict[node_key_module].add(node_name)

        return module_dict

    def _check_multi_ipt_opt(self):
        """Check whether multi-input exists."""
        module_dict = self._generate_module()
        for _, nodes_per_module in module_dict.items():
            prcs_nodes_out_from_module = set()
            for node_name in nodes_per_module:
                if re.search(r"[\d]+[&][\d]+", node_name):
                    self._is_multi_opt_graph = True
                    return True

                node = self._nodes_collection.get(node_name, None)
                if node:
                    prcs_nodes = node.precursor_nodes
                else:
                    continue

                for prcs_node in prcs_nodes:
                    if prcs_node not in nodes_per_module:
                        prcs_node_module = SEPARATOR_IN_SCOPE.join(prcs_node.split(SEPARATOR_IN_SCOPE)[:-1])
                        if prcs_node_module not in nodes_per_module:
                            prcs_nodes_out_from_module.add(prcs_node)

                        if len(prcs_nodes_out_from_module) > 1:
                            return True

        return False

    def _unmerge_multi_ipt_opt_script(self):
        """Unmerge all submodule."""
        if self._check_multi_ipt_opt():
            for node_key, node_inst in deepcopy(self._nodes_collection).items():
                prsc_nodes = node_inst.precursor_nodes
                scsr_nodes = node_inst.successor_nodes

                node_inst.is_in_multi_opt_graph = self._is_multi_opt_graph

                node_inst.precursor_nodes = [SEPARATOR_IN_SCOPE.join((prsc_node.split(SEPARATOR_IN_SCOPE)[0],
                                                                      prsc_node.split(SEPARATOR_IN_SCOPE)[-1]))
                                             for prsc_node in deepcopy(prsc_nodes)]
                node_inst.successor_nodes = [SEPARATOR_IN_SCOPE.join((scsr_node.split(SEPARATOR_IN_SCOPE)[0],
                                                                      scsr_node.split(SEPARATOR_IN_SCOPE)[-1]))
                                             for scsr_node in deepcopy(scsr_nodes)]

                reduce_node_key = SEPARATOR_IN_SCOPE.join((node_key.split(SEPARATOR_IN_SCOPE)[0],
                                                           node_key.split(SEPARATOR_IN_SCOPE)[-1]))

                del self._nodes_collection[node_key]
                self._nodes_collection[reduce_node_key] = node_inst

            for node_key, shape in deepcopy(self._shape_dict).items():
                reduce_node_key = SEPARATOR_IN_SCOPE.join((node_key.split(SEPARATOR_IN_SCOPE)[0],
                                                           node_key.split(SEPARATOR_IN_SCOPE)[-1]))

                del self._shape_dict[node_key]
                self._shape_dict[reduce_node_key] = shape

    def sub_graph_merging(self):
        """
        Merge split operation into one.
        """
        raise NotImplementedError()

    def build_connection(self, src, tgt) -> NoReturn:
        """
        Build connection between source node and target node.

        Args:
            src (str): Source node name.
            tgt (str): Target node name.

        """
        # If src and tgt are the same node, src not in node_collection or
        # tgt not in node_collection, then skip this edge.
        if src == tgt or src not in self._nodes_collection or tgt not in self._nodes_collection:
            if src.split(':')[0] not in self._nodes_collection:
                log.warning("Graph construct a self-loop node %s. Ignored.", src)
                return
        if tgt not in self._nodes_collection[src.split(':')[0]].successor_nodes:
            self._nodes_collection[src.split(':')[0]].successor_nodes.append(tgt)
        if src not in self._nodes_collection[tgt].precursor_nodes:
            self._nodes_collection[tgt.split(':')[0]].precursor_nodes.append(src)

    @staticmethod
    def load_checkpoint(ckpt_path: str) -> Dict:
        """
        Load checkpoint.

        Args:
            ckpt_path (str):  Checkpoint file path.

        Returns:
            dict, weights in model.
        """

    @staticmethod
    def load_metadata(**kwargs):
        """
        Load graph metadata.
        """
        err_msg = "class `PyTorchGraph` has not implemented " \
                  "`load_metadata()`."
        log.error(err_msg)
        raise NotImplementedError(err_msg)

    @staticmethod
    def load_graph(graph_path: str, **kwargs):
        """
        Load graph.

        Args:
            graph_path (str): Graph path.

        Returns:
            object, pytorch model.
        """
        torch_model = PyTorchGraphParser.parse(graph_path)
        return torch_model

    @staticmethod
    def get_node_id(node):
        """
        Get node id using regular expr.

        Args:
            node (Node): PyTorch node.

        Returns:
            str, node id.
        """
        node_title = str(node).split(SEPARATOR_TITLE_AND_CONTENT_IN_CONSTRUCT)[0]
        node_id = re.findall(r"[%](.*?) [:]", node_title)
        return node_id

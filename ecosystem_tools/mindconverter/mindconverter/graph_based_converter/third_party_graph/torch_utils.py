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
"""Define torch tracer context manager"""
import json
import os
import re
from copy import copy, deepcopy
from importlib import import_module
from collections import OrderedDict

import numpy as np
import torch
from torch.jit import TracingCheckError

from mindconverter.common.exceptions import ModelLoadingError
from mindconverter.common.log import MindConverterLogger
from mindconverter.graph_based_converter.common.global_context import GlobalContext

from mindconverter.graph_based_converter.constant import NO_CONVERTED_OPERATORS, DYNAMIC_SHAPE, FrameworkType, \
    UNCONVERTED_ATEN_OPERATORS
from mindconverter.graph_based_converter.sub_graph_matcher.graph_pattern_matching import GraphMatcher
from mindconverter.graph_based_converter.third_party_graph.base import BaseNode, NodeOutputShape

TENSORTYPE = getattr(import_module("torch._C"), "TensorType")


@ModelLoadingError.check_except("Failed to trace pytorch model to graph.", added_except=TracingCheckError)
def model_to_graph(model, args):
    """Trace model to generate graph and param_dict."""
    if isinstance(args, (int, float, bool, torch.Tensor)):
        args = (args,)

    unique_state_dict = getattr(import_module("torch.onnx.utils"), "_unique_state_dict")
    param_dict = deepcopy(unique_state_dict(model))

    graph = torch.jit.trace(model, args, strict=False)
    return graph, param_dict


class PrimTranslation:
    """Define prim op parsing rules."""

    def __init__(self, constants, model_name):
        self._constants = constants
        self._model_name = model_name
        self._switch_mapper = {
            "prim::Constant": self._constant,
            "prim::GetAttr": self._get_attr,
            "prim::NumToTensor": self._num_to_tensor,
            "prim::ListConstruct": self._list_construct,
            "prim::ListUnpack": self._list_unpack,
            "prim::TupleConstruct": self._tuple_construct,
            "prim::TupleUnpack": self._tuple_unpack,
            "prim::DictConstruct": self._dict_construct,
            **{unconverted_aten_op: self._unconverted_aten_operators for unconverted_aten_op in
               UNCONVERTED_ATEN_OPERATORS}
        }

    def prim_translation(self, op, scope=None):
        """Parse prim op to be linked with aten op."""
        value = self._constants.get(op)
        if value:
            prim_func = self._switch_mapper.get(value.kind())
            if not prim_func:
                raise TypeError(f"Unsupported constant kind {value.kind()} found.")
            return prim_func(op=op, value=value, scope=scope)
        return op

    @staticmethod
    def _constant(**kwargs):
        """Parse prim::Constant."""
        value = kwargs.get("value")
        return value['value'] if value.attributeNames() else None

    def _get_attr(self, **kwargs):
        """Parse prim::GetAttr."""
        value = kwargs.get("value")
        scope = kwargs.get("scope")
        scope_name = '.'.join((value['name'], scope)) if scope else value['name']
        inputs = value.input().debugName()
        if inputs == "self.1":
            return '.'.join((self._model_name, scope_name))
        return self.prim_translation(inputs, scope=scope_name)

    def _num_to_tensor(self, **kwargs):
        """Parse prim::NumToTensor."""
        value = kwargs.get("value")
        return self.prim_translation(value.input().debugName())

    def _list_construct(self, **kwargs):
        """Parse prim::ListConstruct."""
        value = kwargs.get("value")
        return [self.prim_translation(ipt.debugName()) for ipt in value.inputs()]

    def _list_unpack(self, **kwargs):
        """Parse prim::ListUnpack."""
        value = kwargs.get("value")
        op = kwargs.get("op")
        outputs = [opt.debugName() for opt in value.outputs()]
        op_index = outputs.index(op)
        ret = self.prim_translation(value.input().debugName())
        return op if isinstance(ret, str) else ret[op_index]

    def _tuple_construct(self, **kwargs):
        """Parse prim::TupleConstruct."""
        value = kwargs.get("value")
        return tuple([self.prim_translation(ipt.debugName()) for ipt in value.inputs()])

    def _tuple_unpack(self, **kwargs):
        """Parse prim::TupleUnpack."""
        value = kwargs.get("value")
        op = kwargs.get("op")
        outputs = [opt.debugName() for opt in value.outputs()]
        op_index = outputs.index(op)
        ret = self.prim_translation(value.input().debugName())
        return op if isinstance(ret, str) else ret[op_index]

    def _dict_construct(self, **kwargs):
        """Parse prim::DictConstruct."""
        value = kwargs.get("value")
        values = [ipt.debugName() for idx, ipt in enumerate(value.inputs()) if idx % 2 == 1]
        return tuple([self.prim_translation(value) for value in values])

    def _unconverted_aten_operators(self, **kwargs):
        """Parse unconverted aten operators."""
        value = kwargs.get("value")
        return self.prim_translation([ipt for ipt in value.inputs()][0].debugName())


class Pattern:
    """Pattern class to generate model construction."""

    def __init__(self, nodes):
        self._nodes = nodes
        self._graph = dict()
        self._pattern = dict()
        self._node_inst = dict()
        self._scope_names = self._extract_scope_name()
        self._patterns = list()
        self._extract_patterns()
        self._existing_modules = dict()
        self._graph_matcher = GraphMatcher(nodes, FrameworkType.PYTORCH)

    @property
    def patterns(self):
        """Patterns."""
        patterns_info = dict()
        for idx, pattern in enumerate(self._patterns):
            name_info = re.findall(r"(.*)\[([\w\d.]+)]", list(pattern.keys())[0])
            if name_info:
                module_name = name_info[0][0]
            else:
                module_name = list(pattern.keys())[0]

            nodes = list(pattern.values())[0]
            real_module_name = self._check_different_modules_with_same_name(module_name, nodes)
            patterns_info[f"{idx}"] = {
                "module_name": real_module_name,
                "id": f"{idx}",
                "nodes": nodes
            }
        return patterns_info

    def _check_different_modules_with_same_name(self, module_name, module_nodes):
        """
        If the name of one module is the same with existing module,
        but operators in them are not, create a new name to this module.
        """
        existing_module = self._existing_modules.get(module_name)
        real_module_name = module_name

        if existing_module:
            if not self._graph_matcher.is_matched(module_nodes, existing_module["nodes"], self._patterns):
                existing_sub_module_num = existing_module["sub_module_num"]
                is_new_sub_module = True
                for existing_sub_module_idx in range(existing_sub_module_num):
                    sub_module_name = "".join((module_name, f"{existing_sub_module_idx}"))

                    existing_sub_module = self._existing_modules.get(sub_module_name)
                    if existing_sub_module:
                        if self._graph_matcher.is_matched(module_nodes, existing_sub_module["nodes"], self._patterns):
                            real_module_name = sub_module_name
                            is_new_sub_module = False
                            break

                if is_new_sub_module:
                    self._existing_modules[module_name]["sub_module_num"] += 1
                    new_module_name = "".join((module_name, f"{existing_sub_module_num}"))
                    self._existing_modules[new_module_name] = {
                        "nodes": module_nodes,
                        "sub_module_num": 0
                    }
                    real_module_name = new_module_name
        else:
            self._existing_modules.update({module_name: {"nodes": module_nodes, "sub_module_num": 0}})
        return real_module_name

    def _gen_scope_name(self, node):
        """Generate scope name for no-scope-name node."""
        matched_scopes = list()
        for _, inst in self._node_inst.items():
            node_inputs = node.input_name_list
            if [ipt for ipt in node_inputs if ipt in inst["outputs"]]:
                scope_name_trace = inst["scope_name"].split(".")[:-1]
                scope_name_trace.append(node.op_type)
                node_scope_name = ".".join(scope_name_trace)
                matched_scopes.append(node_scope_name)
        matched_scopes = sorted(matched_scopes, reverse=True)
        matched_scope = matched_scopes[0] if matched_scopes else ""
        return matched_scope

    def _retrieve_scope_name(self, node):
        """Retrieve scope name if node has full scope name."""
        scope_name = ".".join(node.scope_name.split(".")[1:]) or self._gen_scope_name(node)
        return scope_name

    def _extract_scope_name(self):
        for node_name, node_inst in self._nodes.items():
            scope_name = self._retrieve_scope_name(node_inst)
            self._node_inst[node_name] = {
                "scope_name": scope_name,
                "inputs": node_inst.input_name_list,
                "outputs": node_inst.output_name_list
            }
        return {n: v["scope_name"] for n, v in self._node_inst.items()}

    def _extract_pattern(self, all_scope_name):
        """Extract single pattern."""
        all_scope_trace = [scope.split('.') for scope in all_scope_name]
        sorted_scope_trace = sorted(all_scope_trace, reverse=True)

        full_name_pattern = dict()
        for scope_trace in sorted_scope_trace:
            for scope_idx, _ in enumerate(scope_trace[:-1]):
                pattern_name = ".".join(scope_trace[:scope_idx + 1])
                node_name = scope_trace[scope_idx + 1]
                if not full_name_pattern.get(pattern_name):
                    full_name_pattern[pattern_name] = {node_name}
                else:
                    full_name_pattern[pattern_name].add(node_name)

        for module_idx, module_name in enumerate(
                sorted(full_name_pattern, key=lambda x: len(x.split('.')), reverse=True)):
            module_nodes = full_name_pattern[module_name]
            full_module_nodes = list(module_nodes)

            for node_idx, node in enumerate(full_module_nodes):
                if self._pattern.get(".".join((module_name, node))):
                    full_module_nodes.remove(node)
                    full_module_nodes.insert(node_idx, self._pattern.get(".".join((module_name, node)))["module_idx"])

            self._pattern[module_name] = {"full_module_nodes": full_module_nodes, "module_idx": f"{module_idx}"}

        for module_name, module_nodes in self._pattern.items():
            self._patterns.append({module_name.split('.')[-1]: module_nodes["full_module_nodes"]})

    def _extract_patterns(self):
        """Extract patterns in model."""
        all_scope_name = [".".join((".".join(scope.split(".")[:-1]), name)) if ".".join(scope.split(".")[:-1]) else name
                          for name, scope in self._scope_names.items()]
        self._extract_pattern(all_scope_name)


class PytorchDataLoader:
    """
    Load and parse the pytorch model.

    Provide interfaces and encapsulate methods of loading values.

    Args:
        traced_model (torch._C.TraceModule): Original Pytorch defined graph.
        param_dict (dict): weights of Pytorch graph.
    """

    def __init__(self, traced_model, param_dict):
        self._traced_model = traced_model
        self._param_dict = param_dict
        self._model_name = self._traced_model.original_name
        self.graph = self._traced_model.inlined_graph
        self.patterns = dict()
        self.nodes = [node for node in self.graph.nodes() if
                      node.kind().startswith("aten::") and node.kind() not in UNCONVERTED_ATEN_OPERATORS]
        self._constant_values = dict()
        self._extract_constant_values()
        self._fake_output_nodes = [opt.debugName() for opt in self.graph.outputs()]
        self.input_nodes = [ipt.debugName() for ipt in self.graph.inputs() if isinstance(ipt.type(), TENSORTYPE)]
        self._prim_translation = PrimTranslation(self._constant_values, self._model_name)
        self.output_nodes = self._extract_graph_outputs()
        # args for init
        self._global_context = GlobalContext()

        self._nodes_dict = OrderedDict()
        self.tensors_dict = dict()

        # Record the weight names used many times.
        self.repeated_weight = dict()

        self.node_output_shape_dict = OrderedDict()

        # Key is edge of ir graph, value is the corresponding precursor node.
        self.output_name_to_node_name = dict()

        # Record dynamic shape nodes.
        self._dynamic_shape_nodes = list()

        # Record constant nodes.
        self.constant_nodes = list()

        # Record passes.
        self._pass_list = list()
        self._extract_pass_list()

        # Record nodes deleted.
        self._nodes_deleted = set()

        self.initialize()

    def _extract_constant_values(self):
        """Extract constant values from self._graph."""
        for node in self.graph.nodes():
            if node not in self.nodes:
                for output in node.outputs():
                    self._constant_values[output.debugName()] = node

    def _extract_graph_outputs(self):
        """Extract graph outputs to aten operator."""
        graph_outputs = list()

        def flatten_tuple(data):
            """Flatten multi-layer tuples to one tuple."""
            flattened_data = list()
            if isinstance(data, (tuple, list)):
                for s_data in data:
                    flattened_data.extend(flatten_tuple(s_data))
            else:
                flattened_data.append(data)
            return flattened_data

        for fake_opt_name in self._fake_output_nodes:
            ret = self._prim_translation.prim_translation(fake_opt_name)
            graph_outputs = flatten_tuple(ret)
        return graph_outputs

    def _extract_pass_list(self):
        """Extract pass list."""
        config_json = "self_patterns.json"
        passes_config = os.path.join(os.path.abspath(os.path.dirname(__file__)), "self_patterns", config_json)

        if os.path.exists(passes_config):
            with open(passes_config) as f:
                pass_modules = json.load(f)
                for pass_module in pass_modules:
                    pos = pass_module.rfind(".")
                    pass_obj = getattr(import_module(pass_module[:pos]), pass_module[pos + 1:])
                    self._pass_list.append(pass_obj)

    @property
    def nodes_dict(self):
        return self._nodes_dict

    def initialize(self):
        """Initialize the PytorchDataLoader."""

        # Parse Pytorch Graph level info
        self._parse_graph()

        # 1. parse  nodes, note that parse tensors must be done as nodes require tensor info
        # to process the node weight sharing.
        self._parse_nodes()

        # 1.5. generate the sub-graph according to self-define patterns
        self._generate_sub_graph()

        # 2. parse value info (node output shape)
        self._parse_node_output_shape()

        # 3. parse all tensors
        self._parse_tensors()

        # 4. build nodes connections
        self.build_nodes_connection()

    def _parse_graph(self):
        self._global_context.onnx_graph_info['graph_inputs'] = self.input_nodes
        self._global_context.onnx_graph_info['graph_outputs'] = self.output_nodes

    def _parse_nodes(self):
        """Parse each pytorch nodes in the model."""
        nodes_topo_idx = list()
        record_tensors = dict()
        for idx, node in enumerate(self.nodes):
            node_name = "_".join((node.kind().replace("aten::", ""), f"{idx}"))
            n = PytorchNode(node_name, node, self._constant_values, self._traced_model, self._param_dict)
            self._nodes_dict[node_name] = n
            nodes_topo_idx.append((idx, node_name))
            for output_name in n.output_name_list:
                self.output_name_to_node_name[output_name] = node_name

            for ipt_nd in node.inputs():
                if ipt_nd.debugName() not in self.output_name_to_node_name:
                    self._global_context.onnx_node_inputs.setdefault(node_name, [ipt_nd.debugName()]).append(
                        ipt_nd.debugName())
                if ipt_nd.debugName() in self.tensors_dict:
                    if ipt_nd.debugName() not in record_tensors:
                        record_tensors[ipt_nd.debugName()] = [node_name]
                        continue
                    record_tensors[ipt_nd.debugName()].append(node_name)
                    self.repeated_weight.setdefault(ipt_nd.debugName(), [])

            self._global_context.onnx_node_name_to_topo_idx[node_name] = idx

        for k in self.repeated_weight:
            if not self.tensors_dict.get(k).to_array().shape:
                continue
            self.repeated_weight[k] = record_tensors[k][:]

        self._global_context.onnx_nodes_collection = self._nodes_dict
        self._global_context.onnx_nodes_topo_index = nodes_topo_idx
        # now only process shared weights for multi-inputs models
        if len(self.input_nodes) > 1:
            self._global_context.repeated_weights = self.repeated_weight

    def _generate_sub_graph(self):
        """generate sub-graph according to self-defined patterns."""
        MindConverterLogger.info("Self-defined patterns generating begins.")
        self_defined_patterns = dict()
        for self_pass in self._pass_list:
            self_defined_patterns[self_pass.__name__] = self_pass.SELF_DEFINED_PATTERN
        graph_matcher = GraphMatcher(self.nodes_dict, FrameworkType.PYTORCH)
        matched_sub_graphs_dict = graph_matcher.matcher_from_self_patterns(self_defined_patterns)

        self._update_merged_graph(matched_sub_graphs_dict)
        MindConverterLogger.info("Self-defined patterns generating is finished.")

    def _update_merged_graph(self, matched_sub_graphs_dict):
        """Update merged graph based on matched sub-graphs."""
        for pattern_name, pattern_nodes_list in matched_sub_graphs_dict.items():
            pattern_id = int(re.findall(r".*(\d)", pattern_name)[0])
            for pattern_nodes in pattern_nodes_list:
                sorted_pattern_nodes = sorted(pattern_nodes, key=lambda x: int(x.split("_")[-1]))

                expected_order = [val["op_type"] for val in self._pass_list[pattern_id].SELF_DEFINED_PATTERN.values()]
                current_order = [val.split("_")[0] for val in sorted_pattern_nodes]
                if expected_order != current_order:
                    continue

                if {*sorted_pattern_nodes}.intersection(self._nodes_deleted):
                    continue

                input_name_list, has_multi_input_nodes = self._update_merged_inputs(sorted_pattern_nodes)
                if has_multi_input_nodes:
                    continue

                self_defined_node = copy(self.get_node(sorted_pattern_nodes[-1]))
                op_type = "self_defined_pattern"
                op_name = pattern_name.lower()

                op_index = self_defined_node.name.split("_")[-1]
                self_defined_node.name = f"{op_name}_{op_index}"
                self_defined_node.op_type = op_type

                for opt in self_defined_node.output_name_list:
                    self.output_name_to_node_name[opt] = self_defined_node.name

                self_defined_node.input_name_list = input_name_list

                scope_class_name = ".".join(self_defined_node.scope_name.split(".")[0:-1])
                self_defined_node.scope_name = f"{scope_class_name}.{op_name.capitalize()}[{op_name}]"

                self_defined_node.raw_node = FakedTorchCNode(kind=f"{op_type}::{op_name}")

                self_defined_node.params = ParamsAttribute(self_defined_node.name)
                self_defined_node.weights = dict()
                for node_name in sorted_pattern_nodes:
                    node = self.get_node(node_name)
                    self_defined_node.params.add_attribute(node_name, {"inputs": node.fake_input_name_list,
                                                                       "outputs": node.output_name_list},
                                                           is_self_pattern=True)
                    self_defined_node.weights.update(node.weights)
                    self._nodes_deleted.add(node_name)
                    del self._nodes_dict[node_name]

                self._nodes_dict[self_defined_node.name] = self_defined_node
                keys = sorted(self._nodes_dict.keys(), key=lambda x: int(x.split("_")[-1]))
                sorted_nodes_dict = OrderedDict()
                for key in keys:
                    sorted_nodes_dict[key] = self._nodes_dict[key]
                self._nodes_dict = sorted_nodes_dict

                # Update GlobalContext
                self._global_context.onnx_node_name_to_topo_idx[self_defined_node.name] = int(op_index)
                self._global_context.onnx_nodes_topo_index[int(op_index)] = self_defined_node.name
                self._global_context.onnx_nodes_collection = self._nodes_dict

    def _update_merged_inputs(self, pattern_nodes):
        """Update merged inputs."""
        output_name_all_nodes = list()
        constant_inputs_all_nodes = list()
        for pattern_node in pattern_nodes:
            node = self.get_node(pattern_node)
            output_name_all_nodes.extend(node.output_name_list)
            constant_inputs_all_nodes.extend(node.weights.keys())

        input_name_pattern = list()
        for pattern_node in pattern_nodes:
            input_name_list = self.get_node(pattern_node).input_name_list
            input_name_pattern.extend(
                [ipt for ipt in input_name_list if ipt not in output_name_all_nodes and ipt not in input_name_pattern])
        has_multi_input_nodes = len(set(input_name_pattern) - set(constant_inputs_all_nodes)) > 1
        return input_name_pattern, has_multi_input_nodes

    def _parse_node_output_shape(self):
        """Parse the output shape of each node."""
        for node_name, node_inst in self.nodes_dict.items():
            for node_opt_name in node_inst.output_name_list:
                raw_node = self._constant_values.get(node_opt_name, node_inst.raw_node)
                pattern = re.compile(r"\((.*?), strides=.*?, requires_grad=.*?, device=.*?\)")
                ret = re.findall(pattern, str(raw_node))
                if not ret:
                    shape = DYNAMIC_SHAPE
                else:
                    shape_str = ret[0]
                    shape = tuple([int(val) for val in shape_str.split(",")])
                node_name = self.output_name_to_node_name[node_opt_name]
                node_output_shape = NodeOutputShape(node_opt_name, node_name, shape)
                self.node_output_shape_dict.setdefault(node_name, []).append(node_output_shape)

    def _parse_tensors(self):
        """Parse each pytorch tensors in the model."""
        for _, node_inst in self._nodes_dict.items():
            for weight_name, weight_val in node_inst.weights.items():
                t = PytorchTensor(weight_val, weight_name)
                self.tensors_dict[t.name] = t
        self._global_context.onnx_tensors_collection = self.tensors_dict

    def build_nodes_connection(self):
        """Find the previous and next nodes of each node."""
        self._raw_node_dict = copy(self._nodes_dict)
        for node_name, node in self._raw_node_dict.items():
            if node.op_type in NO_CONVERTED_OPERATORS:
                self.constant_nodes.append(node_name)
                name = node.output_name_list[0]
                value = list(node.params.attribute_dict.values())[0]
                self.tensors_dict.update({name: PytorchTensor(value, name)})
                del self._nodes_dict[node_name]
                continue

            for input_name in node.input_name_list:
                if input_name not in self.tensors_dict:
                    input_node_name = self.output_name_to_node_name.get(input_name, input_name)
                    input_node = self.get_node(input_node_name)
                    if input_node:
                        node.precursor_onnx_node_dict[input_node_name] = input_node
                        input_node.successor_onnx_node_dict[node_name] = node

                    if self._global_context.onnx_node_inputs.get(node.name):
                        self._global_context.onnx_node_inputs[node.name].append(input_node_name)
                    else:
                        self._global_context.onnx_node_inputs[node.name] = [input_node_name]

    def get_node(self, node_name):
        """Get the PytorchNode instance by node name."""
        return self._nodes_dict.get(node_name)


class PytorchNode(BaseNode):
    """
    Define the parsed and readable Pytorch Node structure.

    Args:
        node_name (str): Node name.
        raw_node (torch._C.Node): Original Pytorch defined node.
    """

    def __init__(self, node_name, raw_node, constants, traced_model, param_dict):
        super(PytorchNode, self).__init__(node_name=node_name, op_type=raw_node.kind().split("::")[1])
        self.raw_node = raw_node
        self._constants = constants
        self._traced_model = traced_model
        self._model_name = self._traced_model.original_name
        self._param_dict = param_dict
        self._scope_var_name = self._get_scope_var_name()
        self.scope_name = self._get_scope_class_name()
        self._prim_translation = PrimTranslation(self._constants, self._model_name)
        self._fake_input_name_list = [
            self._prim_translation.prim_translation(ipt.debugName()) for ipt in raw_node.inputs()]
        self.output_name_list = list()
        self.params = ParamsAttribute(node_name)
        self.input_name_list = list()
        self.weights = dict()
        self._special_str_list = ["cpu", "gpu", "(.*),(.*)->(.*)", "(.*)->(.*)"]
        self._get_inputs_params()
        self._get_output_name_list()
        self._get_weights()

    @property
    def fake_input_name_list(self):
        return self._fake_input_name_list

    def _get_scope_var_name(self):
        """
        Get scope var name.

        The format of `self.raw_node.scopeName()` is like `__module/__module.a/__module.a.b`.
        The scopeName is divided into `scope_step_list`, which is
        [
            [`__module`],
            [`__module`, `a`],
            [`__module`, `a`, `b`]
        ]
        As a result, the valid scope name is `__module.a.b`.

        However, if `self.raw_node.scopeName() is `__module/__module.c/__module.a.b`,
        the right valid scope name is expected to be `__module.c.b`.

        This function is to get such a right valid scope name for node.
        """
        scope_var_list = self.raw_node.scopeName().split("/")
        # If `self.raw_node.scopeName()` is `__module`, return.
        if len(scope_var_list) < 2:
            return scope_var_list[0].replace("__module", self._model_name)

        scope_step_list = [s.split(".") for s in scope_var_list]
        max_length = max([len(lst) for lst in scope_step_list])
        scope_step_list = [s + [""] * (max_length - len(s)) for s in scope_step_list]

        scope_var_name = ""
        for scp in zip(*scope_step_list):
            scp_list = [value for value in scp if value != ""]
            scope_var_name = ".".join((scope_var_name, scp_list[0])) if scope_var_name else scp_list[0]
        return scope_var_name.replace("__module", self._model_name)

    def _get_scope_class_name(self):
        """Get scope class name."""
        scope_trace = self._scope_var_name.split(".")
        scope_class_name = scope_trace[0]
        scope_obj = self._traced_model
        class_name = ""
        for scope_step in scope_trace[1:]:
            scope_obj = getattr(scope_obj, "_modules")[f"{scope_step}"]
            class_name = scope_obj.original_name
            if class_name in ["ModuleList", "Sequential"]:
                class_name = scope_step.capitalize() if not scope_step.isdigit() \
                    else f"ModuleListInterLayer{scope_step}"
            scope_class_name += "." + class_name + f"[{scope_step}]"

        if class_name not in dir(torch.nn):
            self_name = self.op_type.replace("_", "")
            scope_class_name += f".{self_name.capitalize()}[{self.name}]"
        return scope_class_name

    def _get_inputs_params(self):
        """Get real inputs and params."""
        extend_num = 0
        for fake_ipt_idx, fake_ipt in enumerate(self._fake_input_name_list):
            filtered_ipt = self._filter_inputs(fake_ipt)
            if filtered_ipt:
                for idx, filtered_ipt_in in enumerate(filtered_ipt):
                    extend_num = idx
                    if isinstance(filtered_ipt_in, str):
                        self.input_name_list.append(filtered_ipt_in)
                        self.params.add_attribute(f"{fake_ipt_idx}[{idx}]", "from_input")
                    elif isinstance(filtered_ipt_in, torch.Tensor):
                        scope_trace = self.scope_name.split(".")
                        prefix = scope_trace[0]
                        for scope_step in scope_trace[1:]:
                            prefix = ".".join((prefix, re.findall(r".*\[(.*)]", scope_step)[0]))
                        prefix = ".".join([scope_trace[0]] + [re.findall(r".*\[(.*)]", scope_step)[0] for scope_step in
                                                              scope_trace[1:]])

                        self.input_name_list.append(f"{prefix}.constant_{fake_ipt_idx}_{idx}")
                        self.weights[f"{prefix}.constant_{fake_ipt_idx}_{idx}"] = filtered_ipt_in
                        self._fake_input_name_list[fake_ipt_idx] = f"{prefix}.constant_{fake_ipt_idx}_{idx}"
                        self.params.add_attribute(f"{fake_ipt_idx}[{idx}]", "from_input")
                    else:
                        self.params.add_attribute(f"{fake_ipt_idx}[{idx}]", filtered_ipt_in)
            else:
                self.params.add_attribute(f"{fake_ipt_idx}[{extend_num}]", fake_ipt)
        self.params.parse_attribute(self.fake_input_name_list)

    def _filter_inputs(self, ipt):
        """Filter inputs in node."""
        if isinstance(ipt, torch.Tensor):
            return [ipt]
        if isinstance(ipt, str) and not np.any([re.match(special_str, ipt) for special_str in self._special_str_list]):
            return [ipt]

        if isinstance(ipt, list):
            is_inputs = False
            for ipt_in in ipt:
                ret = self._filter_inputs(ipt_in)
                if ret != list():
                    is_inputs = True
                    break
            if is_inputs:
                return ipt

        return list()

    def _get_output_name_list(self):
        """Get output name list."""
        output = self.raw_node.output()
        if str(output.type()) == "List[Tensor]":
            multi_opt_nodes = output.uses()
            if len(multi_opt_nodes) > 1:
                raise ValueError("Output nodes is more than one.")
            self.output_name_list = [opt.debugName() for opt in multi_opt_nodes[0].user.outputs()]
        else:
            self.output_name_list = [output.debugName()]

    def _get_weights_from_model(self, param_name):
        """Get weights from traced_model, if param_name is not in in self._param_dict."""
        traced_obj = self._traced_model
        for name_step in param_name.split("."):
            if not hasattr(traced_obj, name_step):
                return None
            obj = getattr(traced_obj, name_step)
            if isinstance(obj, torch.Tensor):
                return obj
            traced_obj = obj
        return None

    def _get_weights(self):
        """Get weights from graph."""
        for ipt in self.input_name_list:
            if isinstance(ipt, str) and ipt.startswith(f"{self._model_name}"):
                param_name = ipt.replace(f"{self._model_name}.", "")
                if param_name in self._param_dict:
                    self.weights[ipt] = self._param_dict[param_name]
                else:
                    weights_from_model = self._get_weights_from_model(param_name)
                    if isinstance(weights_from_model, torch.Tensor):
                        self.weights[ipt] = weights_from_model


class PytorchTensor:
    """
    Define Pytorch Tensor structure for convenience.

    Args:
        raw_tensor (torch.Tensor): torch tensor instance.
        name (str): tensor name.
    """

    def __init__(self, raw_tensor, name):
        self.raw_tensor = raw_tensor
        self.name = name
        self.type = raw_tensor.dtype
        self.dim = raw_tensor.shape
        self.from_nodes = list()
        self.to_nodes = list()

    def to_array(self):
        """Convert the tensor value from binary to np array."""
        requires_grad = self.raw_tensor.requires_grad
        if requires_grad:
            return self.raw_tensor.detach().numpy()
        return self.raw_tensor.numpy()


class ParamsAttribute:
    """
    Define attribute structure.

    Args:
        node_name (str): Node name.
    """

    def __init__(self, node_name):
        self.node_name = node_name
        self.attribute_dict = dict()
        self.attribute_name_list = list()

        self._packed_params_recoder = dict()

    def get_attr(self, name):
        """
        Get the attribute value by attribute name.

        Note:
            The return object has various type because of
            the definition of the attribute itself.

        Args:
            name (str): Attribute name.
        """
        ret = self.attribute_dict.get(name)
        return ret

    def add_attribute(self, idx, ipt, is_self_pattern=False):
        """Add attribute ot ParamAttribute."""
        if is_self_pattern:
            self.attribute_dict.update({f"{idx}": ipt})
            self.attribute_name_list.append(f"{idx}")
        else:
            pack_id, param_idx = re.findall(r"(.*)\[(.*)]", idx)[0]
            self._packed_params_recoder.setdefault(pack_id, []).append(param_idx)
            self.attribute_dict.update({f"constant_{idx}": ipt})
            self.attribute_name_list.append(f"constant_{idx}")

    def parse_attribute(self, fake_input_name_list):
        """Parse attribute name."""
        for name in self.attribute_name_list:
            pack_id, param_idx = re.findall(r"constant_(.*)\[(.*)]", name)[0]
            pack_inst = fake_input_name_list[int(pack_id)]
            pack_id = int(pack_id)
            param_idx = int(param_idx)
            if isinstance(pack_inst, (tuple, list)) and not isinstance(self.attribute_dict[name], (tuple, list)):
                pattern = ["*" if idx == param_idx else "_" for idx, _ in enumerate(pack_inst)]
                self.attribute_dict[
                    f"constant_{pack_id + param_idx}[{pack_id}({','.join(pattern)})]"] = self.attribute_dict.pop(name)
                self.attribute_name_list[self.attribute_name_list.index(
                    name)] = f"constant_{pack_id + param_idx}[{pack_id}({','.join(pattern)})]"
            else:
                self.attribute_dict[f"constant_{pack_id + param_idx}"] = self.attribute_dict.pop(name)
                self.attribute_name_list[self.attribute_name_list.index(name)] = f"constant_{pack_id + param_idx}"


class FakedTorchCNode:
    """Faked torch._C.Node struct."""

    def __init__(self, kind):
        self._kind = kind

    def kind(self):
        return self._kind

# Copyright 2020-2021 Huawei Technologies Co., Ltd.All Rights Reserved.
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
"""Define ONNX related operations."""
import os
import itertools
import re
from importlib import import_module
from collections import OrderedDict

import numpy as np

from mindconverter.common.log import MindConverterLogger
from mindconverter.graph_based_converter.common.utils import fetch_output_from_onnx_model, build_feed_dict
from mindconverter.graph_based_converter.common.global_context import GlobalContext
from mindconverter.graph_based_converter.third_party_graph.base import BaseNode, NodeOutputShape
from mindconverter.graph_based_converter.third_party_graph.optimizer import OnnxSimplify

from mindconverter.graph_based_converter.constant import ONNX_TYPE_INT, ONNX_TYPE_INTS, ONNX_TYPE_STRING, \
    ONNX_TYPE_FLOATS, ONNX_TYPE_FLOAT, SCALAR_WITHOUT_SHAPE, DYNAMIC_SHAPE, UNKNOWN_DIM_VAL
from mindconverter.common.exceptions import GraphInitError, ModelLoadingError


def convert_tf_graph_to_onnx(model_path, model_inputs, model_outputs, opset=12):
    """
    Convert Tensorflow model to ONNX model.

    Note: shape override is supported by tf2onnx but we
          have not supported yet.

    Args:
        model_path (str): Path to the tensorflow model.
        model_inputs (str): Input nodes of the tf model.
        model_outputs (str): Output nodes of the tf model.
        opset (int): Op set version of onnx.

    Returns:
        onnx.ModelProto, onnx defined model proto.
    """
    tf = import_module('tensorflow')
    tf2onnx = import_module("tf2onnx")
    tfonnx = getattr(tf2onnx, "tfonnx")
    process_tf_graph = getattr(tfonnx, "process_tf_graph")
    constants = getattr(tf2onnx, "constants")
    utils = getattr(tf2onnx, "utils")
    optimizer = getattr(tf2onnx, "optimizer")
    tf_loader = getattr(tf2onnx, "tf_loader")

    target = ",".join(constants.DEFAULT_TARGET)
    shape_override = None

    if 'input' in model_outputs:
        error_msg = "The given output node is an input node."
        error = ValueError(error_msg)
        MindConverterLogger.error(str(error))
        raise error

    if model_inputs:
        model_inputs, shape_override = utils.split_nodename_and_shape(model_inputs)
    if model_outputs:
        model_outputs = model_outputs.split(',')
    graph_def, inputs, outputs = tf_loader.from_graphdef(model_path,
                                                         model_inputs,
                                                         model_outputs)

    with tf.Graph().as_default() as tf_graph:
        tf.import_graph_def(graph_def, name='')

    with tf_loader.tf_session(graph=tf_graph):
        g = process_tf_graph(tf_graph,
                             target=target,
                             opset=opset,
                             custom_op_handlers=None,
                             extra_opset=None,
                             shape_override=shape_override,
                             input_names=inputs,
                             output_names=outputs,
                             inputs_as_nchw=None)
    opt_map = getattr(optimizer.back_to_back_optimizer, '_func_map')
    if ('Conv', 'BatchNormalization') in opt_map:
        opt_map.pop(('Conv', 'BatchNormalization'))
    onnx_graph = optimizer.optimize_graph(g)
    model_proto = onnx_graph.make_model("converted from {}".format(model_path))

    return model_proto


class OnnxTensor:
    """
    Define Onnx Tensor structure for convenience.

    Args:
        raw_tensor (onnx.TensorProto): onnx.TensorProto instance.
    """

    def __init__(self, raw_tensor, name=None):
        self.raw_tensor = raw_tensor
        self.name = raw_tensor.name if not isinstance(raw_tensor, np.ndarray) else name
        self.type = raw_tensor.data_type if not isinstance(raw_tensor, np.ndarray) else raw_tensor.dtype
        self.dim = raw_tensor.dims if not isinstance(raw_tensor, np.ndarray) else raw_tensor.shape
        self.from_nodes = []
        self.to_nodes = []

    def to_array(self):
        """Convert the tensor value from binary to np array."""
        numpy_helper = import_module("onnx.numpy_helper")
        # Convert binary data to np.array
        if not isinstance(self.raw_tensor, (np.ndarray, list, tuple, int, float)):
            return numpy_helper.to_array(self.raw_tensor)
        return self.raw_tensor


class ParamsAttribute:
    """
    Define attribute structure.

    Args:
        raw_attribute (onnx.AttributeProto): onnx.AttributeProto instance.
        node (onnx.NodeProto): Must pass the onnx.NodeProto instance
                                containing the same AttributeProto.
    """

    def __init__(self, raw_attribute, node):
        self.raw_attribute = raw_attribute
        self.node_name = node.name
        self.attribute_dict = {}
        self.attribute_name_list = []
        self._parse_attribute(raw_attribute)

    def _parse_attribute(self, attrs):
        """
        Parse attribute value from protobuf to dict.

        Note:
            Not all types of attribute have been implemented.
            Different types have their own methods to parse value.

        Args:
            attrs (onnx.AttributeProto): onnx.AttributeProto instance.
        """
        if not attrs:
            return
        for attribute in attrs:
            self.attribute_name_list.append(attribute.name)
            type_num = attribute.type
            # get attribute value by determining its type
            # Can Convert to np.array if needed
            if type_num == ONNX_TYPE_INTS:
                self.attribute_dict[attribute.name] = attribute.ints
            elif type_num == ONNX_TYPE_FLOATS:
                self.attribute_dict[attribute.name] = attribute.floats
            elif type_num == ONNX_TYPE_STRING:
                self.attribute_dict[attribute.name] = str(attribute.s, 'utf-8')
            elif type_num == ONNX_TYPE_INT:
                self.attribute_dict[attribute.name] = attribute.i
            elif type_num == ONNX_TYPE_FLOAT:
                self.attribute_dict[attribute.name] = attribute.f
            else:
                MindConverterLogger.warning(f"WARNING: Attribute {attribute.name} in Node {self.node_name} not parsed.")

    def get_attr(self, name):
        """
        Get the attribute value by attribute name.

        Note:
            The return object has various type because of
            the definition of the attribute itself.

        Args:
            name (str): Attribute name.

        Returns:
            Object, various types of return depends on the attribute.
        """
        ret = self.attribute_dict.get(name)
        return ret


class OnnxNode(BaseNode):
    """
    Define the parsed and readable Onnx Node structure.

    Args:
        raw_node (onnx.NodeProto): Original Onnx defined node.

    """

    def __init__(self, raw_node):
        super(OnnxNode, self).__init__(node_name=raw_node.name, op_type=raw_node.op_type)
        self.raw_node = raw_node
        self.params = ParamsAttribute(raw_node.attribute, raw_node)
        self.scope_name = None
        self.input_name_list = getattr(raw_node, 'input')
        self.output_name_list = getattr(raw_node, 'output')


class OnnxDataLoader:
    """
    Load and parse the onnx model.

    Provide interfaces and encapsulate methods of loading values.

    Note:
        Shape inference could encounter error for some ops.

    Args:
        onnx_model (onnx.ModelProto): Original Onnx defined model.
        model_path (str): Onnx model path.
        input_nodes (Union[str, list]): Input nodes of ONNX model.
        output_nodes (Union[str, list]): Output nodes of ONNX model.
        infer_shape (bool): Enable the shape inference after conversion.
            Default: True
    """

    def __init__(self, onnx_model, model_path: str, input_nodes: dict,
                 output_nodes: list, infer_shape=True):
        MindConverterLogger.info("Onnx simplifying begins.")
        onnx_sim = OnnxSimplify()
        onnx_model_sim = onnx_sim.run_onnx_simplify(onnx_model, model_path, input_nodes)
        MindConverterLogger.info("Onnx simplifying is finished.")
        self.model = onnx_model_sim
        self.model_path = model_path
        self.graph = onnx_model_sim.graph
        self.nodes = onnx_model_sim.graph.node
        self.input_nodes = input_nodes
        self.output_nodes = output_nodes
        # args for init
        self._is_infer_shape = infer_shape
        self._global_context = GlobalContext()
        # params parsed in init
        self.inferred_model = None

        self._nodes_dict = OrderedDict()  # {node_name: OnnxNode} NO INPUT NODE
        self.tensors_dict = {}  # {tensor_name: OnnxTensor}
        self.value_info_dict = {}  # Not contains input and output nodes

        # Record the weight names used many times.
        self.repeated_weight = dict()

        self.node_output_shape_dict = OrderedDict()  # {node_name: [int]}

        # Key is edge of ONNX ir graph, value is the corresponding precursor node.
        self.output_name_to_node_name = dict()

        # Define dynamic nodes to be evaluated with onnxruntime
        self.dynamic_resize_node = list()
        self.dynamic_reshape_node = list()
        self.eliminated_nodes = list()

        # Validate init params
        self._check_user_provided_info()

        self.initialize()

    @property
    def nodes_dict(self):
        """Return a filtered nodes_dict."""
        filtered_dict = dict()
        for k, v in self._nodes_dict.items():
            if k in self.eliminated_nodes:
                continue
            filtered_dict[k] = v
        return filtered_dict

    def _infer_model(self):
        """
        Call onnx provided shape inference method.

        Note:
            The method will be replaced by self-implemented
            in future development.
        """
        onnx = import_module("onnx")
        self.inferred_model = onnx.shape_inference.infer_shapes(self.model)

    @staticmethod
    def _parse_value_info_manually(value_info):
        """Parse value info from onnx ir edge manually."""
        tensor_proto = getattr(import_module("onnx"), "TensorProto")
        node_name = value_info.name
        node_dim = []
        node_type = tensor_proto.DataType.Name(value_info.type.tensor_type.elem_type)
        if not value_info.type.tensor_type.shape.dim:
            return node_name, node_type, "".join(node_dim)

        for dim in value_info.type.tensor_type.shape.dim:
            v = dim.dim_value if dim.dim_value != 0 else UNKNOWN_DIM_VAL
            node_dim.append(f"{v}")

        return node_name, node_type, "x".join(node_dim)

    def _parse_value_info(self):
        """Parse onnx defined value_info class attributes."""
        onnx = import_module("onnx")

        def _parse_value_info_re(i):
            """
            Parse the value_info by regular expression

            Args:
                i (str): Line of each printable onnx value_info

            Returns:
                tuple(str, str, str), name, type, and dimensions of value_info.
            """
            regex = r'%(?P<name>.+)\[(?P<type>.+), (?P<dim_str>.+)\]'
            group_match = re.match(regex, i)
            i_name = group_match.group('name')
            i_type = group_match.group('type')
            i_dim_str = group_match.group('dim_str')

            for dim in i_dim_str.split('x'):
                if not dim.isdigit():
                    raise ValueError("Unknown output shape.")

            return i_name, i_type, i_dim_str

        if not self.inferred_model:
            return

        value_info = self.inferred_model.graph.value_info
        node_without_output_shape = dict()

        for v in itertools.chain(value_info, self.inferred_model.graph.output):
            try:
                readable_info = onnx.helper.printable_value_info(v)
                (node_name, node_type, node_dim) = _parse_value_info_re(readable_info)
            except (AssertionError, ValueError, AttributeError) as _:
                node_name, node_type, node_dim = self._parse_value_info_manually(v)
                node_without_output_shape[node_name] = {'node_type': node_type, 'output_name': v.name}
            self.value_info_dict[node_name] = (node_type, node_dim)

        inferred_outputs_name = [node_inst['output_name'] for node_inst in list(node_without_output_shape.values())]

        inferred_outputs = dict()
        if inferred_outputs_name:
            inferred_outputs = self._get_outputs_using_onnxruntime(inferred_outputs_name)

        for node_name, node_inst in node_without_output_shape.items():
            node_type = node_inst['node_type']
            output_name = node_inst['output_name']
            node_dim = 'x'.join(str(shape_axis) for shape_axis in inferred_outputs[output_name].shape)
            self.value_info_dict[node_name] = (node_type, node_dim)

    def _get_outputs_using_onnxruntime(self, output_nodes_name):
        """Get outputs using onnxruntime."""

        feed_dict = build_feed_dict(self.inferred_model, self.input_nodes)

        outputs_infer = fetch_output_from_onnx_model(self.model,
                                                     self.model_path,
                                                     feed_dict,
                                                     output_nodes_name)
        return outputs_infer

    def _parse_nodes(self):
        """Parse each onnx nodes in the model."""
        nodes_topo_idx = []
        record_tensors = dict()
        for idx, node in enumerate(self.nodes):
            if not node.name:
                node.name = "_".join(node.output)
            n = OnnxNode(node)
            self._nodes_dict[n.name] = n
            nodes_topo_idx.append((idx, n.name))
            for out in node.output:
                self.output_name_to_node_name[out] = node.name

            for ipt_nd in node.input:
                if ipt_nd not in self.output_name_to_node_name:
                    if self._global_context.onnx_node_inputs.get(n.name):
                        self._global_context.onnx_node_inputs[n.name].append(ipt_nd)
                    else:
                        self._global_context.onnx_node_inputs[n.name] = [ipt_nd]
                if ipt_nd in self.tensors_dict:
                    if ipt_nd not in record_tensors:
                        record_tensors[ipt_nd] = [node.name]
                        continue
                    record_tensors[ipt_nd].append(node.name)
                    self.repeated_weight.setdefault(ipt_nd, [])

            self._global_context.onnx_node_name_to_topo_idx[n.name] = idx

        for k in self.repeated_weight:
            if not self.tensors_dict.get(k).to_array().shape:
                # scalar does not have shape info
                continue
            self.repeated_weight[k] = record_tensors[k][:]

        self._global_context.onnx_nodes_collection = self._nodes_dict
        self._global_context.onnx_nodes_topo_index = nodes_topo_idx
        # now only process shared weights for multi-inputs models
        if len(self.input_nodes) > 1:
            self._global_context.repeated_weights = self.repeated_weight

    def _parse_tensors(self):
        """Parse each onnx tensors in the model."""
        tensors = self.graph.initializer
        for tensor in tensors:
            t = OnnxTensor(tensor)
            self.tensors_dict[t.name] = t

        self._global_context.onnx_tensors_collection = self.tensors_dict

    def _remove_extra_graph_output(self):
        idx = 0
        while idx < len(self.model.graph.output):
            cur_opt = self.model.graph.output[idx]
            if cur_opt.name not in self.output_nodes:
                self.model.graph.output.remove(cur_opt)
                continue
            idx += 1

    def _parse_node_output_shape(self):
        """
        Parse the inferred output shape of each node.

        Note:
            This function has a prerequisite of the shape inference.
        """
        for (node_opt_name, (_, shape_str)) in self.value_info_dict.items():
            # split shape by 'x'
            shape = shape_str.split('x')
            # replace unknown shape by '-1'
            for i, s in enumerate(shape):
                if 'unk' in s:
                    # Have to adapt user-define axis name, e.g. 'sequence', 'batch'.
                    raise ValueError(f"cannot get shape of {node_opt_name}.")
                if s == "scalar":
                    shape = SCALAR_WITHOUT_SHAPE
                    continue
                if s == "":
                    shape = DYNAMIC_SHAPE
                    continue
                shape[i] = int(shape[i])
            node_name = self.output_name_to_node_name[node_opt_name]
            if not node_name:
                raise GraphInitError(msg=f"Cannot find where edge {node_opt_name} comes from.")
            node_output_shape = NodeOutputShape(node_opt_name, node_name, shape)
            self.node_output_shape_dict.setdefault(node_name, []).append(node_output_shape)

    def get_node(self, node_name):
        """Get the OnnxNode instance by node name."""
        return self._nodes_dict[node_name]

    def get_tensor(self, tensor_name):
        """Get the OnnxTensor instance by tensor name."""
        return self.tensors_dict[tensor_name]

    def build_nodes_connection(self):
        """Find the previous and next nodes of each node."""
        for node_name, node in self._nodes_dict.items():
            if node_name in self.eliminated_nodes:
                continue
            for input_name in node.input_name_list:
                if self.output_name_to_node_name.get(input_name):
                    input_node_name = self.output_name_to_node_name.get(input_name)
                    input_node = self.get_node(input_node_name)
                    node.precursor_onnx_node_dict[input_node_name] = input_node
                    input_node.successor_onnx_node_dict[node_name] = node

                    if self._global_context.onnx_node_inputs.get(node.name):
                        self._global_context.onnx_node_inputs[node.name].append(input_node_name)
                    else:
                        self._global_context.onnx_node_inputs[node.name] = [input_node_name]

    def _parse_graph(self):
        """Parse ONNX Graph Info For usage in generator."""
        graph_outputs = [out.name for out in self.graph.output]
        self._global_context.onnx_graph_info['graph_inputs'] = self.input_nodes.keys()
        self._global_context.onnx_graph_info['graph_outputs'] = graph_outputs

    def _check_user_provided_info(self):
        """Validate user input and output node."""
        graph_inputs = [inp.name for inp in self.graph.input]
        graph_outputs = [out.name for out in self.graph.output]
        for output_node in self.output_nodes:
            if output_node not in graph_outputs:
                raise ModelLoadingError(f"Unexpected Node {output_node} detected which should not be a graph output.")
        for graph_inp in graph_inputs:
            if graph_inp not in self.input_nodes:
                raise ModelLoadingError(f"{graph_inp} is one of the graph inputs but user does not provide it.")

    def initialize(self):
        """Initialize the OnnxDataLoader."""

        # Parse ONNX Graph level info
        self._parse_graph()

        # 1. parse all nodes, note that parse tensors must be done as nodes require tensor info
        # to process the node weight sharing.
        self._parse_nodes()

        # 2. remove extra output from onnx model graph
        self._remove_extra_graph_output()

        # 3. parse value info (incl. node output shape)
        if self._is_infer_shape:
            try:
                self._infer_model()
                self._parse_value_info()
                self._parse_node_output_shape()
            except Exception as e:
                MindConverterLogger.error(str(e))
                MindConverterLogger.exception(e, console=False)
                raise e

        # 4. load external_data for initializer
        self.load_external_data()

        # 5. parse all tensors
        self._parse_tensors()

        # 6. Optimize graph to eliminate some nodes.
        self._find_nodes_to_be_eliminated()

        # 7. build nodes connections
        self.build_nodes_connection()

        # 8. Run onnx model to fetch actual value of eliminated nodes.
        self._fetch_eliminated_nodes_value()

    def load_external_data(self):
        load_external_data_for_model = getattr(import_module("onnx.external_data_helper"),
                                               "load_external_data_for_model")
        model_filepath = os.path.realpath(self.model_path)
        if model_filepath:
            base_dir = os.path.dirname(model_filepath)
            load_external_data_for_model(self.model, base_dir)

    def _fetch_eliminated_nodes_value(self):
        """Fetch eliminated nodes values by running onnx inference."""

        def _for_reshape():
            """Do reshape nodes."""
            nonlocal self
            output_tensors = []
            if not self.dynamic_reshape_node:
                return
            for node in self.dynamic_reshape_node:
                shape_ref = self._nodes_dict[node].input_name_list[1]
                output_tensors.append(shape_ref)
            feed_dict = build_feed_dict(self.model, self.input_nodes)
            fetch_dict = fetch_output_from_onnx_model(self.model,
                                                      self.model_path,
                                                      feed_dict=feed_dict,
                                                      output_nodes=output_tensors)
            for opt_tensor_name, value in fetch_dict.items():
                self.tensors_dict[opt_tensor_name] = OnnxTensor(value, opt_tensor_name)

        def _for_resize():
            """Do resize nodes."""
            nonlocal self
            output_tensors = []
            if not self.dynamic_resize_node:
                return
            for node in self.dynamic_resize_node:
                shape_ref = self._nodes_dict[node].input_name_list[3]
                output_tensors.append(shape_ref)
            feed_dict = build_feed_dict(self.model, self.input_nodes)
            fetch_dict = fetch_output_from_onnx_model(self.model,
                                                      self.model_path,
                                                      feed_dict=feed_dict,
                                                      output_nodes=output_tensors)
            for opt_tensor_name, value in fetch_dict.items():
                self.tensors_dict[opt_tensor_name] = OnnxTensor(value, opt_tensor_name)

        _for_reshape()
        _for_resize()

    def _find_nodes_to_be_eliminated(self):
        """Call all PASS to optimize graph."""
        for nd_name, nd_inst in self._nodes_dict.items():
            self._pass_of_shape(nd_name, nd_inst)
            self._pass_of_resize(nd_name, nd_inst)

    def _pass_of_shape(self, nd_name, nd_inst):
        """Create a PASS to optimize shape and reshape operations in ONNX ir graph."""
        to_be_eliminated_op = {"Cast", "Concat", "Squeeze", "Unsqueeze", "Slice",
                               "Gather", "Shape"}
        def _is_origin_inputs(node):
            for ipt in node.input_name_list:
                if ipt not in self.input_nodes:
                    return False
            return True
        def _traceback_precursor_nodes_until_shape_op(node_ref):
            nonlocal self
            e_nodes = []
            node = self._nodes_dict[self.output_name_to_node_name[node_ref]]
            if node.op_type not in to_be_eliminated_op or _is_origin_inputs(node):
                return e_nodes
            e_nodes.append(node.name)
            for ipt in node.input_name_list:
                if ipt not in self.tensors_dict:
                    e_nodes += _traceback_precursor_nodes_until_shape_op(ipt)
            return e_nodes

        if nd_inst.op_type == "Reshape":
            # Find its shape input.
            to_shape = nd_inst.input_name_list[1]
            if to_shape in self.tensors_dict:
                # Then its shape input is constant.
                return

            eliminated_nodes = _traceback_precursor_nodes_until_shape_op(to_shape)
            self.dynamic_reshape_node.append(nd_name)
            self.eliminated_nodes += eliminated_nodes

    def _pass_of_resize(self, nd_name, nd_inst):
        """Create a PASS to optimize resize operations in ONNX ir graph."""
        to_be_eliminated_op = {"Concat", "Cast", "Mul", "Slice", "Cast", "Gather", "Shape"}

        def _traceback_precursor_nodes_until_shape_op(node_ref):
            nonlocal self
            e_nodes = []
            node = self._nodes_dict[self.output_name_to_node_name[node_ref]]
            if node.op_type not in to_be_eliminated_op:
                return e_nodes
            e_nodes.append(node.name)
            for ipt in node.input_name_list:
                if ipt not in self.tensors_dict:
                    e_nodes += _traceback_precursor_nodes_until_shape_op(ipt)
            return e_nodes

        if nd_inst.op_type == "Resize":
            # Find the size params
            to_shape = nd_inst.input_name_list[-1]
            if to_shape in self.tensors_dict:
                return

            eliminated_nodes = _traceback_precursor_nodes_until_shape_op(to_shape)
            self.dynamic_resize_node.append(nd_name)
            self.eliminated_nodes += eliminated_nodes

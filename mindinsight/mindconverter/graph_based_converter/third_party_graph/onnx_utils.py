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
"""Define ONNX related operations."""
import re
import abc
from importlib import import_module
from collections import OrderedDict
from typing import Union

import numpy as np

from mindinsight.mindconverter.common.log import logger as log
from ..common.utils import fetch_output_from_onnx_model
from ..common.global_context import GlobalContext

from ..constant import ONNX_TYPE_INT, ONNX_TYPE_INTS, ONNX_TYPE_STRING, \
    ONNX_TYPE_FLOATS, ONNX_TYPE_FLOAT, SCALAR_WITHOUT_SHAPE, DYNAMIC_SHAPE, UNKNOWN_DIM_VAL
from ...common.exceptions import GraphInitError, ModelNotSupportError, ModelLoadingError


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
        log.error(str(error))
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
        onnx = import_module("onnx")
        # Convert binary data to np.array
        if not isinstance(self.raw_tensor, (np.ndarray, list, tuple, int, float)):
            return onnx.numpy_helper.to_array(self.raw_tensor)
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
                log.warning("WARNING: Attribute %s in Node %s not parsed.",
                            attribute.name, self.node_name)

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


class BaseNode(abc.ABC):
    """Define the basic parameters required for node.

    Args:
        node_name (str): The name of the node.
        op_type (str): The onnx ops.

    """

    def __init__(self, **kwargs):
        self.name = kwargs.get('node_name')
        self.op_type = kwargs.get('op_type')

        self.precursor_onnx_node_dict = OrderedDict()
        self.successor_onnx_node_dict = OrderedDict()

    def get_name(self):
        """Get node name."""
        return self.name

    def get_op(self):
        """Get node op type."""
        return self.op_type

    def get_precursor_dict(self):
        """Get node's precursor dict."""
        return self.precursor_onnx_node_dict

    def get_successor_dict(self):
        """Get node's successor dict."""
        return self.successor_onnx_node_dict


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
        input_nodes (Union[str, list]): Input nodes of ONNX model.
        output_nodes (Union[str, list]): Output nodes of ONNX model.
        infer_shape (bool): Enable the shape inference after conversion.
            Default: True
    """

    def __init__(self, onnx_model, graph_input_shape: Union[tuple, list],
                 input_nodes: list, output_nodes: list, infer_shape=True):
        self.model = onnx_model
        self.graph = onnx_model.graph
        self.nodes = onnx_model.graph.node
        self.graph_input_shape = graph_input_shape
        self.input_nodes = input_nodes if isinstance(input_nodes, list) else [input_nodes]
        self.output_nodes = output_nodes if isinstance(output_nodes, list) else [output_nodes]
        # args for init
        self._is_infer_shape = infer_shape
        self._global_context = GlobalContext()
        # params parsed in init
        self.inferred_model = None

        self._nodes_dict = OrderedDict()  # {node_name: OnnxNode} NO INPUT NODE
        self.tensors_dict = {}  # {tensor_name: OnnxTensor}
        self.value_info_dict = {}  # Not contains input and output nodes

        self.node_output_shape_dict = OrderedDict()  # {node_name: [int]}

        # Key is edge of ONNX ir graph, value is the corresponding precursor node.
        self.output_name_to_node_name = dict()

        # Define dynamic nodes to be evaluated with onnxruntime
        self.dynamic_resize_node = list()
        self.dynamic_reshape_node = list()
        self.eliminated_nodes = list()

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

    def _check_initialization(self):
        """Define conditions checked before init."""
        if all([self.model, self.graph, self.nodes]):
            if self.graph_input_shape is None:  # do not check
                return True
            onnx = import_module("onnx")
            # check input shape eligible
            input_node = getattr(self.graph, 'input')[0]
            type_str = onnx.helper.printable_type(input_node.type)
            regex = r"(.+\ )?(?P<full>(unk.+x|\d+x)*\d+)"
            match = re.match(regex, type_str)
            dims = match.group('full').split('x')
            h = int(dims[1])
            w = int(dims[2])
            c = int(dims[3])
            if [h, w, c] != list(self.graph_input_shape)[1:]:
                raise ModelLoadingError(f"Shape given should be (N, {h}, {w}, {c}) but got {self.graph_input_shape}")
            return True
        return False

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

            return i_name, i_type, i_dim_str

        if not self.inferred_model:
            return

        value_info = self.inferred_model.graph.value_info

        for v in value_info:
            try:
                readable_info = onnx.helper.printable_value_info(v)
                (node_name, node_type, node_dim) = _parse_value_info_re(readable_info)
            except (AssertionError, ValueError, AttributeError) as _:
                node_name, node_type, node_dim = self._parse_value_info_manually(v)
            # `node_dim` could be "" or "scalar".
            self.value_info_dict[node_name] = (node_type, node_dim)

    def _parse_nodes(self):
        """Parse each onnx nodes in the model."""
        nodes_topo_idx = []
        for idx, node in enumerate(self.nodes):
            n = OnnxNode(node)
            self._nodes_dict[n.name] = n
            nodes_topo_idx.append((idx, n.name))
            if len(node.output) > 1:
                raise ModelNotSupportError(msg=f"{node.name} has multi-outputs which is not supported now.")
            self.output_name_to_node_name[node.output[0]] = node.name
            self._global_context.onnx_node_name_to_topo_idx[n.name] = idx
            node_inputs = [i.replace(":0", "") for i in node.input]
            self._global_context.onnx_node_inputs[n.name] = node_inputs
        self._global_context.onnx_nodes_collection = self._nodes_dict
        self._global_context.onnx_nodes_topo_index = nodes_topo_idx

    def _parse_tensors(self):
        """Parse each onnx tensors in the model."""
        tensors = self.graph.initializer
        for tensor in tensors:
            t = OnnxTensor(tensor)
            self.tensors_dict[t.name] = t
        self._global_context.onnx_tensors_collection = self.tensors_dict

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
                    shape[i] = int(self.graph_input_shape[0]) if self.graph_input_shape is not None else 1
                    continue
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
            self.node_output_shape_dict[node_name] = shape

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
                    continue

    def initialize(self):
        """Initialize the OnnxDataLoader."""

        # check init conditions met
        if not self._check_initialization():
            err = ModuleNotFoundError("Unable to Find ONNX Model")
            log.error(str(err))
            log.exception(err)

        # 1. parse all nodes
        self._parse_nodes()

        # 2. parse value info (incl. node output shape)
        if self._is_infer_shape:
            try:
                self._infer_model()
                self._parse_value_info()
                self._parse_node_output_shape()
            except Exception as e:
                log.error(str(e))
                log.exception(e)
                raise e

        # 3. parse all tensors
        self._parse_tensors()

        # 4. Optimize graph to eliminate some nodes.
        self._find_nodes_to_be_eliminated()

        # 5. build nodes connections
        self.build_nodes_connection()

        # 6. Run onnx model to fetch actual value of eliminated nodes.
        self._fetch_eliminated_nodes_value()

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
            feed_dict = {self.input_nodes[0]: np.random.rand(*self.graph_input_shape).astype(np.float32)}
            fetch_dict = fetch_output_from_onnx_model(self.model, feed_dict=feed_dict, output_nodes=output_tensors)
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
            feed_dict = {self.input_nodes[0]: np.random.rand(*self.graph_input_shape).astype(np.float32)}
            fetch_dict = fetch_output_from_onnx_model(self.model, feed_dict=feed_dict, output_nodes=output_tensors)
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
            to_shape = nd_inst.input_name_list[3]
            if to_shape in self.tensors_dict:
                return

            eliminated_nodes = _traceback_precursor_nodes_until_shape_op(to_shape)
            self.dynamic_resize_node.append(nd_name)
            self.eliminated_nodes += eliminated_nodes

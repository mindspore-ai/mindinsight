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
"""Define ONNX related opertions."""
import re
import abc
from collections import OrderedDict

from mindinsight.mindconverter.common.log import logger as log

from ..constant import ONNX_TYPE_INT, ONNX_TYPE_INTS, ONNX_TYPE_STRING,\
    ONNX_TYPE_FLOATS, ONNX_TYPE_FLOAT


def convert_tf_graph_to_onnx(model_path, model_inputs, model_outputs, opset=None):
    """
    Convert Tensorflow model to ONNX model.

    Note: shape overide is supported by tf2onnx but we
          have not supported yet.

    Args:
        model_path (str): Path to the tensorflow model.
        model_inputs (str): Input nodes of the tf model.
        model_outputs (str): Output nodes of the tf model.
        opset (int): Op set version of onnx.

    Returns:
        onnx.ModelProto, onnx defined model proto.
    """
    import tensorflow as tf
    from tf2onnx.tfonnx import process_tf_graph
    from tf2onnx import constants, utils, optimizer
    from tf2onnx import tf_loader
    target = ",".join(constants.DEFAULT_TARGET)
    shape_override = None

    if model_inputs:
        model_inputs, shape_override = utils.split_nodename_and_shape(
            model_inputs)
    if model_outputs:
        model_outputs = model_outputs.split(',')
    graph_def, inputs, outputs = tf_loader.from_graphdef(
        model_path, model_inputs, model_outputs)

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
                             inputs_as_nchw=None
                             )
    opt_map = getattr(optimizer.back_to_back_optimizer, '_func_map')
    opt_map.pop(('Conv', 'BatchNormalization'))
    onnx_graph = optimizer.optimize_graph(g)
    model_proto = onnx_graph.make_model("converted from {}".format(model_path))

    return model_proto


class OnnxTensor:
    """
    Define Onnx Tensor structure for convenience.

    Note:
        parameter from_nodes and to_nodes.

    Args:
        raw_tensor (onnx.TensorProto): onnx.TensorProto instance.
    """
    import onnx
    def __init__(self, raw_tensor):
        self.raw_tensor = raw_tensor
        self.name = raw_tensor.name
        self.type = raw_tensor.data_type
        self.dim = raw_tensor.dims
        self.from_nodes = []
        self.to_nodes = []

    def to_array(self):
        """Convert binary data to np.array"""
        return onnx.numpy_helper.to_array(self.raw_tensor)


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
        super(OnnxNode, self).__init__(
            node_name=raw_node.name, op_type=raw_node.op_type)
        self.raw_node = raw_node
        self.params = ParamsAttribute(raw_node.attribute, raw_node)
        self.scope_name = None
        self.input_name_list = raw_node.input
        self.output_name_list = raw_node.output


class OnnxDataLoader:
    """
    Load and parse the onnx model.

    Provide interfaces and encapsulate methods of loading values.

    Note:
        Shape inference could encounter error for some ops.

    Args:
        onnx_model (onnx.ModelProto): Original Onnx defined model.
        infer_shape (bool): Enable the shape inference after conversion.
            Default: True
    """

    def __init__(self, onnx_model, infer_shape=True):
        self.model = onnx_model
        self.graph = onnx_model.graph
        self.nodes = onnx_model.graph.node

        # args for init
        self._is_infer_shape = infer_shape

        # params parsed in init
        self.inferred_model = None

        self.nodes_dict = OrderedDict()  # {node_name: OnnxNode} NO INPUT NODE
        self.tensors_dict = {}  # {tensor_name: OnnxTensor}
        self.weight_dict = {}  # {tensor_name: OnnxTensor} NOT USED
        self.bias_dict = {}  # {tensor_name: OnnxTensor}  NOT USED
        # {node_name : (type, dim)} NO INPUT & OUTPUT NODE!
        self.value_info_dict = {}

        self.tensor_name_set = set()  # [str]
        self.node_name_set = set()  # [str]
        self.node_output_shape_dict = OrderedDict()  # {node_name: [int]}

        self.initialize()

    def _check_initialization(self):
        """Define conditions checked before init."""
        if all([self.model, self.graph, self.nodes]):
            return True
        return False

    def _infer_model(self):
        """
        Call onnx provided shape inference method.

        Note:
            The method will be replaced by self-implemented
            in future development.
        """
        import onnx
        self.inferred_model = onnx.shape_inference.infer_shapes(self.model)

    def _parse_value_info(self):  # no input node & output node
        """Parse onnx defined value_info class attribtues"""
        import onnx
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

            return (i_name, i_type, i_dim_str)

        if not self.inferred_model:
            return

        value_info = self.inferred_model.graph.value_info

        for v in value_info:
            readable_info = onnx.helper.printable_value_info(v)
            (node_name, node_type, node_dim) = _parse_value_info_re(
                readable_info)
            self.value_info_dict[node_name] = (node_type, node_dim)

    def _parse_nodes(self):
        """Parse each onnx nodes in the model."""
        for node in self.nodes:
            n = OnnxNode(node)
            self.nodes_dict[n.name] = n
            self.node_name_set.add(n.name)

    def _parse_tensors(self):
        """Parse each onnx tensors in the model."""
        tensors = self.graph.initializer
        for tensor in tensors:
            t = OnnxTensor(tensor)
            self.tensors_dict[t.name] = t
            self.tensor_name_set.add(t.name)

    def _parse_node_output_shape(self):
        """
        Parse the inferred output shape of each node.

        Note:
            This function has a prerequisite of the shape inference.
        """
        for (node_name, (_, shape_str)) in self.value_info_dict.items():
            l = []
            # split shape by 'x'
            shape_list = shape_str.split('x')
            # replace unknown shape by '-1'
            for s in shape_list:
                if 'unk' in s:
                    s = '-1'

                # convert str to int
                s = int(s)
                l.append(s)
            self.node_output_shape_dict[node_name] = l

    def get_node(self, node_name):
        """Get the OnnxNode instance by node name."""
        return self.nodes_dict[node_name]

    def get_tensor(self, tensor_name):
        """Get the OnnxTensor instance by tensor name."""
        return self.tensors_dict[tensor_name]

    def build_tensor_dataflow(self):
        """Find the data from/to nodes of each tensor."""
        for node_name, node in self.nodes_dict.items():
            # for each input of a node
            for input_name in node.input_name_list:
                # if the input is a tensor
                if input_name in self.tensor_name_set:
                    t = self.get_tensor(input_name)
                    t.to_nodes.append(node_name)

            for output_name in node.output_name_list:
                # if the output is a tensor
                if output_name in self.tensor_name_set:
                    t = self.get_tensor(output_name)
                    t.from_nodes.append(node_name)

    def build_nodes_connection(self):
        """Find the previous and next nodes of each node."""
        for node_name, node in self.nodes_dict.items():
            # for each input of a node
            for input_name in node.input_name_list:
                # input_name = input_node:0, remove :0 here
                input_name = input_name.split(':')[0]
                if input_name in self.node_name_set:
                    # input is a node
                    # build connection
                    node.precursor_onnx_node_dict[input_name] = self.get_node(
                        input_name)

                    # backtracing successor nodes
                    back_tracked_node = self.get_node(input_name)
                    back_tracked_node.successor_onnx_node_dict[node_name] = self.get_node(
                        node_name)
                    continue

                # check if nodes connected by a tensor
                if input_name in self.tensor_name_set:
                    # regex to remove the ':0' in the name
                    regex = r'(?P<node>.+)/(?P<op>.+:0)'
                    match = re.match(regex, input_name)
                    if not match:
                        continue

                    n_name = match.group('node')
                    if n_name in self.node_name_set:
                        # current node has a pre node via tensor
                        node.precursor_onnx_node_dict[n_name] = self.get_node(
                            n_name)

                        # backtracing successor nodes
                        back_tracked_node = self.get_node(n_name)
                        back_tracked_node.successor_onnx_node_dict[n_name] = self.get_node(
                            n_name)
                    continue

                # input_name not a node /tensor but intermediate
                for nm, n in self.nodes_dict.items():
                    for out_name in n.output_name_list:
                        out_name = out_name.split(':')[0]
                        if out_name == input_name:
                            node.precursor_onnx_node_dict[nm] = n

                            # backtracing
                            n.successor_onnx_node_dict[node_name] = node

    @staticmethod
    def normalize_dict_key(d):
        """
        Normalize dictionary key.

        Note:
            The normalization is removing :0 in each node or output name.

        Args:
            d (dict): Dictionary where keys are node/output names.

        Returns:
            dict, normalized dictionary.
        """
        if not isinstance(d, (dict, OrderedDict)):
            error_msg = "Error occurs in normalizing dictionary key.\
                        Object passed in is not a dictionary."
            error = TypeError(error_msg)
            log.error(error_msg)
            log.exception(error)
            raise error

        new_d = None
        if isinstance(d, dict):
            new_d = {}
            for key_old in d.keys():
                key_new = key_old.split(':')[0]
                new_d[key_new] = d.get(key_old)

        if isinstance(d, OrderedDict):
            new_d = OrderedDict()
            for key_old in d.keys():
                key_new = key_old.split(':')[0]
                new_d[key_new] = d.get(key_old)

        if not new_d:
            error_msg = "Error occurs in normalizing dictionary key."
            error = ValueError(error_msg)
            log.error(error_msg)
            log.exception(error)
            raise error
        return new_d

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
            except Exception as e:
                log.error(str(e))
                log.exception(e)
                raise e

        if self.inferred_model:
            try:
                self._parse_value_info()
            except Exception as e:
                log.error(str(e))
                log.exception(e)
                raise e

            try:
                self._parse_node_output_shape()
            except Exception as e:
                log.error(str(e))
                log.exception(e)
                raise e

        # 3. parse all tensors
        self._parse_tensors()

        # 4. build nodes connections
        self.build_nodes_connection()

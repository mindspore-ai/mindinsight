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
"""OnnxProto to GraphProto."""
from mindinsight.domain.graph.proto import ms_graph_pb2
from mindinsight.mindconverter.common.log import logger as log
from mindinsight.mindconverter.graph_based_converter.constant import MS_DATA_EDGE, OUTPUT_PROTO_TYPE, \
    ONNXAttributeType, ONNXTensorType, MSDataType

# CONVERT_TENSOR_TYPE means the conversion of TensorProto type value from ONNX to msGraph.
CONVERT_TENSOR_TYPE = {
    ONNXTensorType.UNDEFINED.value: MSDataType.DT_UNDEFINED.value,
    ONNXTensorType.FLOAT.value: MSDataType.DT_FLOAT64.value,
    ONNXTensorType.UINT8.value: MSDataType.DT_UINT8.value,
    ONNXTensorType.INT8.value: MSDataType.DT_INT8.value,
    ONNXTensorType.UINT16.value: MSDataType.DT_UINT16.value,
    ONNXTensorType.INT16.value: MSDataType.DT_INT16.value,
    ONNXTensorType.INT32.value: MSDataType.DT_INT32.value,
    ONNXTensorType.INT64.value: MSDataType.DT_INT64.value,
    ONNXTensorType.STRING.value: MSDataType.DT_STRING.value,
    ONNXTensorType.BOOL.value: MSDataType.DT_BOOL.value,
    ONNXTensorType.FLOAT16.value: MSDataType.DT_FLOAT16.value,
    ONNXTensorType.UINT32.value: MSDataType.DT_UINT32.value,
    ONNXTensorType.UINT64.value: MSDataType.DT_UINT64.value
}
# CONVERT_ATTRIBUTE_TYPE means the conversion of AttributeProto type value from ONNX to msGraph.
CONVERT_ATTRIBUTE_TYPE = {
    ONNXAttributeType.UNDEFINED.value: MSDataType.DT_UNDEFINED.value,
    ONNXAttributeType.FLOAT.value: MSDataType.DT_FLOAT64.value,
    ONNXAttributeType.INT.value: MSDataType.DT_INT64.value,
    ONNXAttributeType.STRING.value: MSDataType.DT_STRING.value,
    ONNXAttributeType.TENSOR.value: MSDataType.DT_TENSOR.value,
    ONNXAttributeType.GRAPH.value: MSDataType.DT_GRAPH.value,
    ONNXAttributeType.FLOATS.value: MSDataType.DT_FLOATS64.value,
    ONNXAttributeType.INTS.value: MSDataType.DT_INTS64.value,
    ONNXAttributeType.STRINGS.value: MSDataType.DT_STRINGS.value,
    ONNXAttributeType.TENSORS.value: MSDataType.DT_TENSORS.value,
    ONNXAttributeType.GRAPHS.value: MSDataType.DT_GRAPHS.value
}


def convert_graph_output(onnx_graph):
    """This func generates a dict that the key is the output of node, and the value is the node."""
    convert_output = {}
    for n in onnx_graph.node:
        for out in n.output:
            convert_output[out] = n.name
    return convert_output


class AttributeProto:
    """The attribute proto class of MS."""

    def __init__(self):
        self.ms_attribute_proto = ms_graph_pb2.AttributeProto()

    def decode(self, onnx_attribute_proto):
        """This func converts the onnx attribute proto into ms attribute proto."""
        self.ms_attribute_proto.name = onnx_attribute_proto.name
        ms_type = CONVERT_ATTRIBUTE_TYPE[onnx_attribute_proto.type]
        self.ms_attribute_proto.value.dtype = ms_type
        if ms_type == MSDataType.DT_INT64.value:
            self.ms_attribute_proto.value.int_val = onnx_attribute_proto.i
        elif ms_type == MSDataType.DT_FLOAT64.value:
            self.ms_attribute_proto.value.float_val = onnx_attribute_proto.f
        elif ms_type == MSDataType.DT_TENSOR.value:
            tp = TensorProto()
            tp.decode(onnx_attribute_proto.t)
            self.ms_attribute_proto.value.tensor_val.node_name = tp.ms_tensor_proto.node.name
            self.ms_attribute_proto.value.tensor_val.tensor_content = tp.ms_tensor_proto.node.tensor_content
            self.ms_attribute_proto.value.tensor_val.data_type = tp.ms_tensor_proto.node.data_type
            for d in tp.ms_tensor_proto.dims:
                self.ms_attribute_proto.value.tensor_val.dims.append(d)
        elif ms_type == MSDataType.DT_INTS64.value:
            for i in onnx_attribute_proto.ints:
                self.ms_attribute_proto.value.int_vals.append(i)
        else:
            log.warning("MSGraph can not supply this data type when DataType equals to %s.", ms_type)


class TensorProto:
    """The Tensor proto class of MS."""

    def __init__(self):
        self.ms_tensor_proto = ms_graph_pb2.TensorProto()

    def decode(self, onnx_tensor_proto):
        """This func converts the onnx tensor proto into ms tensor proto."""
        self.ms_tensor_proto.node_name = onnx_tensor_proto.name
        self.ms_tensor_proto.tensor_content = onnx_tensor_proto.raw_data
        self.ms_tensor_proto.data_type = CONVERT_TENSOR_TYPE[onnx_tensor_proto.data_type]
        for dim in onnx_tensor_proto.dims:
            self.ms_tensor_proto.dims.append(dim)


class NodeProto:
    """The Node proto class of MS."""

    def __init__(self):
        self.ms_node_proto = ms_graph_pb2.NodeProto()

    def decode(self, onnx_node_proto, convert_output):
        """This func converts the node attribute proto into ms node proto."""
        self.ms_node_proto.name = onnx_node_proto.name
        self.ms_node_proto.op_type = onnx_node_proto.op_type
        self.ms_node_proto.scope = onnx_node_proto.domain
        for input_name in onnx_node_proto.input:
            input_node = ms_graph_pb2.InputProto()
            if input_name in convert_output:
                input_node.name = convert_output[input_name]
            else:
                input_node.name = input_name
            input_node.type = MS_DATA_EDGE
            self.ms_node_proto.input.append(input_node)
        for attr in onnx_node_proto.attribute:
            onnx_attr = AttributeProto()
            onnx_attr.decode(attr)
            ms_attr = onnx_attr.ms_attribute_proto
            self.ms_node_proto.attribute.append(ms_attr)


class GraphProto:
    """The graph proto class of MS."""

    def __init__(self):
        self.ms_graph_proto = ms_graph_pb2.GraphProto()

    def decode(self, onnx_graph_proto, convert_output):
        """
        This func converts the onnx graph proto into ms graph proto.

        Args:
            onnx_graph_proto (str): The node name.
            convert_output (dict): The dict of onnx model's output and node name.
        """
        self.ms_graph_proto.name = onnx_graph_proto.name
        for out in onnx_graph_proto.output:
            ms_output = ms_graph_pb2.NodeProto()
            ms_output.name = out.name
            ms_output.op_type = OUTPUT_PROTO_TYPE
            input_node = ms_graph_pb2.InputProto()
            input_node.type = MS_DATA_EDGE
            input_node.name = convert_output[out.name] if out.name in convert_output else out.name
            ms_output.input.append(input_node)
            self.ms_graph_proto.node.append(ms_output)
        for input_node in onnx_graph_proto.input:
            ms_input = ms_graph_pb2.ParameterProto()
            ms_input.name = input_node.name
            self.ms_graph_proto.parameters.append(ms_input)
        for n in onnx_graph_proto.node:
            onnx_node = NodeProto()
            onnx_node.decode(n, convert_output)
            ms_node = onnx_node.ms_node_proto
            self.ms_graph_proto.node.append(ms_node)
        for t in onnx_graph_proto.initializer:
            ms_value = ms_graph_pb2.NamedValueProto()
            onnx_tensor = TensorProto()
            onnx_tensor.decode(t)
            ms_value.key = onnx_tensor.ms_tensor_proto.node_name
            self.ms_graph_proto.const_vals.append(ms_value)


def convert_msgraph(onnx_model):
    """This func converts the onnx model proto into ms model proto."""
    convert_output = convert_graph_output(onnx_model.graph)
    graph_proto = GraphProto()
    graph_proto.decode(onnx_model.graph, convert_output)
    ms_model = ms_graph_pb2.ModelProto()
    ms_model.graph.name = graph_proto.ms_graph_proto.name
    for i in graph_proto.ms_graph_proto.parameters:
        ms_model.graph.parameters.append(i)
    for n in graph_proto.ms_graph_proto.node:
        ms_model.graph.node.append(n)
    return ms_model

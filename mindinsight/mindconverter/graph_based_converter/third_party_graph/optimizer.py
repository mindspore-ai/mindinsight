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
"""Define ONNX optimizer operations."""
import copy
from importlib import import_module

from mindinsight.mindconverter.common.exceptions import ModelLoadingError
from mindinsight.mindconverter.graph_based_converter.common.utils import fetch_output_from_onnx_model, build_feed_dict


class OnnxSimplify:
    """To simplify onnx model."""

    def __init__(self):
        self._onnx_model = None
        self._constant_nodes = list()
        self._outputs_infer = dict()

    def run_onnx_simplify(self, onnx_model, input_nodes):
        """
        Run to simplify onnx model.

        Args:
            onnx_model (onnx.ModelProto): Onnx Model.
            input_nodes (dict): Input nodes and corresponding sample shape.
        """
        self._onnx_model = onnx_model
        self._optimizer()
        self._get_constant_nodes()
        self._onnx_infer(input_nodes)
        self._replace_constant_nodes()
        self._optimizer()

        return self._onnx_model

    def _optimizer(self):
        """Run optimizer from onnx to eliminate constant nodes."""

        onnxoptimizer = import_module('onnxoptimizer')
        optimizers_list = [
            'eliminate_deadend',
            'eliminate_nop_dropout',
            'eliminate_nop_cast',
            'eliminate_nop_monotone_argmax',
            'eliminate_nop_pad',
            'extract_constant_to_initializer',
            'eliminate_unused_initializer',
            'eliminate_nop_transpose',
            'eliminate_identity',
            'fuse_add_bias_into_conv',
            'fuse_consecutive_concats',
            'fuse_consecutive_log_softmax',
            'fuse_consecutive_reduce_unsqueeze',
            'fuse_consecutive_squeezes',
            'fuse_consecutive_transposes',
            'fuse_matmul_add_bias_into_gemm',
            'fuse_pad_into_conv',
            'fuse_transpose_into_gemm'
        ]

        input_num = len(self._onnx_model.graph.input)
        onnx_model_optimized = onnxoptimizer.optimize(self._onnx_model, optimizers_list, fixed_point=True)

        if self._onnx_model.ir_version > 3:
            del onnx_model_optimized.graph.input[input_num:]
        self._onnx_model = onnx_model_optimized

    def _get_constant_nodes(self):
        """Get constant nodes."""

        const_nodes = list()
        const_tensors = [tensor_init.name for tensor_init in self._onnx_model.graph.initializer]
        const_tensors.append([node.output[0]
                              for node in self._onnx_model.graph.node if node.op_type == 'Constant'])

        for node in self._onnx_model.graph.node:
            if node.op_type == 'Shape' or all([input_node in const_tensors for input_node in node.input]):
                const_nodes.append(node)
                const_tensors.extend(node.output)

        self._constant_nodes = copy.deepcopy(const_nodes)

    @ModelLoadingError.check_except(
        "Error occurs when loading model with given params, please check `--shape`, "
        "`--input_nodes`, `--output_nodes`, `--model_file` or runtime environment integrity."
    )
    def _onnx_infer(self, infer_inputs_shape):
        """
        Run onnx inference to get outputs of constant nodes.

        Args:
            infer_inputs_shape (dict): Input shape for running inference.
        """
        feed_dict = build_feed_dict(self._onnx_model, infer_inputs_shape)
        output_nodes_name = list()
        for node in self._constant_nodes:
            output_nodes_name.extend(node.output)
        original_outputs = [nd.name for nd in self._onnx_model.graph.output]
        self._outputs_infer = fetch_output_from_onnx_model(self._onnx_model,
                                                           feed_dict, output_nodes_name)
        idx = 0
        while idx < len(self._onnx_model.graph.output):
            cur_opt = self._onnx_model.graph.output[idx]
            if cur_opt.name not in original_outputs:
                self._onnx_model.graph.output.remove(cur_opt)
                continue
            idx += 1

    def _replace_constant_nodes(self):
        """Replace constant nodes to nodes with op_type 'Constant'."""

        onnx = import_module('onnx')
        np_helper = import_module('onnx.numpy_helper')

        for i, node in enumerate(self._onnx_model.graph.node):
            if node in self._constant_nodes:
                for output in node.output:
                    new_attr = onnx.helper.make_attribute(
                        'value',
                        np_helper.from_array(self._outputs_infer[output], name=output)
                    )

                    new_node = onnx.helper.make_node(
                        op_type='Constant',
                        inputs=list(),
                        outputs=[output],
                        name='_'.join(('node', output))
                    )
                    new_node.attribute.extend([new_attr])
                    self._insert_node(self._onnx_model.graph.node, i + 1, new_node)
                del self._onnx_model.graph.node[i]

    @staticmethod
    def _insert_node(repeated_container, index, node):
        """Insert node into onnx model."""

        repeated_container.extend([repeated_container[-1]])
        for i in reversed(range(index + 1, len(repeated_container) - 1)):
            repeated_container[i].CopyFrom(repeated_container[i - 1])
        repeated_container[index].CopyFrom(node)

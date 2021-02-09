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
"""Third party graph parser."""
import multiprocessing as mp
import os
from importlib import import_module

from mindinsight.mindconverter.common.log import logger as log
from mindinsight.mindconverter.graph_based_converter.third_party_graph.base import GraphParser
from mindinsight.mindconverter.common.exceptions import ModelNotSupportError


class PyTorchGraphParser(GraphParser):
    """Define pytorch graph parser."""

    @classmethod
    @ModelNotSupportError.check_except(
        "Error occurs in loading model, please check your model or runtime environment integrity."
    )
    def parse(cls, model_path: str, **kwargs):
        """
        Parser pytorch graph.

        Args:
            model_path (str): Model file path.

        Returns:
            object, torch model.
        """

        if not os.path.exists(model_path):
            error = FileNotFoundError("`model_path` must be assigned with "
                                      "an existed file path.")
            log.error(str(error))
            raise error

        try:
            onnx_model_sim = cls._convert_pytorch_graph_to_onnx(
                model_path, kwargs['sample_shape'], opset_version=11)
            return onnx_model_sim

        except ModuleNotFoundError:
            error_msg = "Cannot find model scripts in system path, " \
                        "set `--project_path` to the path of model scripts folder correctly."
            error = ModuleNotFoundError(error_msg)
            raise error

    @staticmethod
    def _convert_pytorch_graph_to_onnx(model_path, sample_shape, opset_version=None):
        """
        Convert Pytorch model to ONNX model.

        Args:
            model_path (str): Path to the Pytorch model.
            sample_shape (tuple): Input shape to generate onnx model.
            opset_version (int): Op set version of onnx.
        """

        output_queue = mp.Queue()
        process = mp.Process(target=PyTorchGraphParser._pytorch_graph_to_proto,
                             args=(output_queue, model_path, sample_shape, opset_version))
        process.start()
        proto = output_queue.get()
        process.join()

        onnx = import_module('onnx')
        onnx_model = onnx.load_model_from_string(proto)

        return onnx_model

    @staticmethod
    def _pytorch_graph_to_proto(output_queue, model_path, sample_shape, opset_version):
        """
        Convert pytorch graph to pytorch proto.

        Args:
            output_queue (Queue): Output queue from multi-processing.
            model_path (str): Path to the Pytorch model.
            sample_shape (tuple): Input shape to generate onnx model.
            opset_version (int): Op set version of onnx.
        """

        torch = import_module('torch')
        has_cuda = torch.cuda.is_available()
        if has_cuda:
            model = torch.load(f=model_path).cuda()
            dump_input = torch.randn(*sample_shape, device='cuda')
        else:
            model = torch.load(f=model_path, map_location="cpu")
            dump_input = torch.randn(*sample_shape, device='cpu')

        if isinstance(model, torch.nn.DataParallel):
            raise ValueError('torch.nn.DataParallel is not supported by ONNX exporter.')

        torch_onnx = import_module('torch.onnx')
        operator_export_types = getattr(torch_onnx, 'OperatorExportTypes')
        utils = import_module('torch.onnx.utils')
        model_to_graph = getattr(utils, '_model_to_graph')

        symbolic_helper = import_module('torch.onnx.symbolic_helper')
        default_onnx_opset_version = getattr(symbolic_helper, '_default_onnx_opset_version')
        set_opset_version = getattr(symbolic_helper, '_set_opset_version')
        set_operator_export_type = getattr(symbolic_helper, '_set_operator_export_type')
        if not opset_version:
            opset_version = default_onnx_opset_version

        operator_export_type = operator_export_types.ONNX
        set_opset_version(opset_version)
        set_operator_export_type(operator_export_type)

        graph, params_dict, _ = model_to_graph(model, dump_input, _retain_param_name=True)
        export_onnx = getattr(graph, '_export_onnx')
        proto, _ = export_onnx(
            params_dict, opset_version, dict(), False,
            operator_export_type, True, False, dict(),
            True, False)

        output_queue.put(proto)

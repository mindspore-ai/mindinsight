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
"""Third party graph parser."""
import os
from importlib import import_module

from mindinsight.mindconverter.common.log import logger as log
from .base import GraphParser
from ...common.exceptions import ModelNotSupport


class TFGraphParser(GraphParser):
    """Define TF graph parser."""

    @classmethod
    @ModelNotSupport.check_except_tf("Error occurs in loading model, make sure model.pb correct.")
    def parse(cls, model_path: str, **kwargs):
        """
        Parse TF Computational Graph File (.pb)

        Args:
            model_path (str): Model file path.

        Returns:
            object, ONNX model.
        """

        onnx_utils = import_module(
            "mindinsight.mindconverter.graph_based_converter.third_party_graph.onnx_utils")
        convert_tf_graph_to_onnx = getattr(onnx_utils, "convert_tf_graph_to_onnx")
        tf_input_nodes = kwargs.get('input_nodes')
        tf_output_nodes = kwargs.get('output_nodes')
        if not os.path.exists(model_path):
            error = FileNotFoundError("`model_path` must be assigned with "
                                      "an existed file path.")
            log.error(str(error))
            raise error

        model = convert_tf_graph_to_onnx(model_path,
                                         model_inputs=tf_input_nodes,
                                         model_outputs=tf_output_nodes,
                                         )
        return model

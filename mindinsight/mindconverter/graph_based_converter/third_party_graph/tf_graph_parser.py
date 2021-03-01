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
import os
import re
from importlib import import_module

from mindinsight.mindconverter.common.log import logger as log
from mindinsight.mindconverter.graph_based_converter.third_party_graph.base import GraphParser
from mindinsight.mindconverter.common.exceptions import ModelLoadingError


class TFGraphParser(GraphParser):
    """Define TF graph parser."""

    @classmethod
    @ModelLoadingError.check_except(
        "Error occurs when loading model with given params, please check `--shape`, "
        "`--input_nodes`, `--output_nodes`, `--model_file` or runtime environment integrity."
    )
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

        input_nodes = ",".join(tf_input_nodes.keys())
        output_nodes = ",".join(tf_output_nodes)
        invalid_inputs = TFGraphParser.invalid_nodes_name(input_nodes)
        invalid_outputs = TFGraphParser.invalid_nodes_name(output_nodes)
        if invalid_inputs:
            raise ModelLoadingError(f"Invalid Input Node Name Found: {', '.join(invalid_inputs)}")
        if invalid_outputs:
            raise ModelLoadingError(f"Invalid Output Node Name Found: {', '.join(invalid_outputs)}")

        model = convert_tf_graph_to_onnx(model_path,
                                         model_inputs=input_nodes,
                                         model_outputs=output_nodes)
        return model

    @staticmethod
    def invalid_nodes_name(input_str):
        """
        Check model_inputs and model_outputs are correctly formatted.

        Args:
            input_str (str): The string of model inputs and model outputs the CLI passed in.

        Returns:
            list, a list of invalid node name the user inputs.
        """
        splited = input_str.replace(' ', '').split(',')
        name_format_re = r"(?P<name>[\w\/]+):(?P<postfix>\d+)"
        invalid_node_name_list = list()
        for name in splited:
            if re.match(name_format_re, name):
                continue
            invalid_node_name_list.append(name)
        return invalid_node_name_list

# Copyright 2020 Huawei Technologies Co., Ltd
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
# ============================================================================
"""Define common utils."""
from importlib import import_module
from typing import List

from mindinsight.mindconverter.graph_based_converter.constant import SEPARATOR_IN_ONNX_OP


def is_converted(operation: str):
    """
    Whether convert successful.

    Args:
        operation (str): Operation name.

    Returns:
        bool, true or false.
    """
    return operation and SEPARATOR_IN_ONNX_OP not in operation


def fetch_output_from_onnx_model(model, feed_dict: dict, output_nodes: List[str]):
    """
    Fetch specific nodes output from onnx model.

    Notes:
        Only support to get output without batch dimension.

    Args:
        model (ModelProto): ONNX model.
        feed_dict (dict): Feed forward inputs.
        output_nodes (list[str]): Output nodes list.

    Returns:
        dict, nodes' output value.
    """
    if not isinstance(feed_dict, dict) or not isinstance(output_nodes, list):
        raise TypeError("`feed_dict` should be type of dict, and `output_nodes` "
                        "should be type of List[str].")

    ort = import_module("onnxruntime")

    input_nodes = list(feed_dict.keys())

    extractor = getattr(import_module("onnx.utils"), "Extractor")(model)
    extracted_model = extractor.extract_model(input_nodes, output_nodes)
    sess = ort.InferenceSession(path_or_bytes=bytes(extracted_model.SerializeToString()))
    fetched_res = sess.run(output_names=output_nodes, input_feed=feed_dict)
    run_result = dict()
    for idx, opt in enumerate(output_nodes):
        run_result[opt] = fetched_res[idx]
    return run_result

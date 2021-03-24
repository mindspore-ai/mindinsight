# Copyright 2020-2021 Huawei Technologies Co., Ltd
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
import json
import os
import stat
from importlib import import_module
from importlib.util import find_spec
from typing import List, Tuple, Mapping

import numpy as np

from mindinsight.mindconverter.common.exceptions import ScriptGenerationError, ReportGenerationError, \
    CheckPointGenerationError, WeightMapGenerationError
from mindinsight.mindconverter.graph_based_converter.constant import SEPARATOR_IN_ONNX_OP, FrameworkType, \
    TENSORFLOW_MODEL_SUFFIX, THIRD_PART_VERSION, ONNX_MODEL_SUFFIX, DTYPE_MAP


def is_converted(operation: str):
    """
    Whether convert successful.

    Args:
        operation (str): Operation name.

    Returns:
        bool, true or false.
    """
    return operation and SEPARATOR_IN_ONNX_OP not in operation


def _add_outputs_of_onnx_model(model, output_nodes: List[str]):
    """
    Add output nodes of onnx model.

    Args:
        model (ModelProto): ONNX model.
        output_nodes (list[str]): Output nodes list.

    Returns:
        ModelProto, edited ONNX model.
    """
    onnx = import_module("onnx")
    for opt_name in output_nodes:
        intermediate_layer_value_info = onnx.helper.ValueInfoProto()
        intermediate_layer_value_info.name = opt_name
        model.graph.output.append(intermediate_layer_value_info)
    return model


def check_dependency_integrity(*packages):
    """Check dependency package integrity."""
    try:
        for pkg in packages:
            import_module(pkg)
        return True
    except ImportError:
        return False


def build_feed_dict(onnx_model, input_nodes: dict):
    """Build feed dict for onnxruntime."""
    dtype_mapping = DTYPE_MAP
    input_nodes_types = {
        node.name: dtype_mapping[node.type.tensor_type.elem_type]
        for node in onnx_model.graph.input
    }
    feed_dict = {
        name: np.random.rand(*shape).astype(input_nodes_types[name])
        for name, shape in input_nodes.items()
    }
    return feed_dict


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

    edit_model = _add_outputs_of_onnx_model(model, output_nodes)

    ort = import_module("onnxruntime")
    sess = ort.InferenceSession(path_or_bytes=bytes(edit_model.SerializeToString()))
    fetched_res = sess.run(output_names=output_nodes, input_feed=feed_dict)
    run_result = dict()
    for idx, opt in enumerate(output_nodes):
        run_result[opt] = fetched_res[idx]
    return run_result


def save_code_file_and_report(model_name: str, code_lines: Mapping[str, Tuple],
                              out_folder: str, report_folder: str):
    """
    Save code file and report.

    Args:
        model_name (str): Model name.
        code_lines (dict): Code lines.
        out_folder (str): Output folder.
        report_folder (str): Report output folder.
    """
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    modes = stat.S_IRUSR | stat.S_IWUSR
    modes_usr = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR

    out_folder = os.path.realpath(out_folder)
    if not report_folder:
        report_folder = out_folder
    else:
        report_folder = os.path.realpath(report_folder)

    if not os.path.exists(out_folder):
        os.makedirs(out_folder, modes_usr)
    if not os.path.exists(report_folder):
        os.makedirs(report_folder, modes_usr)

    for file_name in code_lines:
        code, report, trainable_weights, weight_map = code_lines[file_name]
        code_file_path = os.path.realpath(os.path.join(out_folder, f"{model_name}.py"))
        report_file_path = os.path.realpath(os.path.join(report_folder, f"report_of_{model_name}.txt"))
        try:
            if os.path.exists(code_file_path):
                raise ScriptGenerationError("Code file with the same name already exists.")
            with os.fdopen(os.open(code_file_path, flags, modes), 'w') as file:
                file.write(code)
        except (IOError, FileExistsError) as error:
            raise ScriptGenerationError(str(error))

        try:
            if os.path.exists(report_file_path):
                raise ReportGenerationError("Report file with the same name already exists.")
            with os.fdopen(os.open(report_file_path, flags, stat.S_IRUSR), "w") as rpt_f:
                rpt_f.write(report)
        except (IOError, FileExistsError) as error:
            raise ReportGenerationError(str(error))

        save_checkpoint = getattr(import_module("mindspore.train.serialization"), "save_checkpoint")
        ckpt_file_path = os.path.realpath(os.path.join(out_folder, f"{model_name}.ckpt"))
        try:
            if os.path.exists(ckpt_file_path):
                raise CheckPointGenerationError("Checkpoint file with the same name already exists.")
            save_checkpoint(trainable_weights, ckpt_file_path)
        except TypeError as error:
            raise CheckPointGenerationError(str(error))

        weight_map_path = os.path.realpath(os.path.join(report_folder, f"weight_map_of_{model_name}.json"))
        try:
            if os.path.exists(weight_map_path):
                raise WeightMapGenerationError("Weight map file with the same name already exists.")
            with os.fdopen(os.open(weight_map_path, flags, stat.S_IRUSR), 'w') as map_f:
                weight_map_json = {f"{model_name}": weight_map}
                json.dump(weight_map_json, map_f)
        except (IOError, FileExistsError) as error:
            raise WeightMapGenerationError(str(error))


def onnx_satisfied():
    """Validate ONNX , ONNXRUNTIME, ONNXOPTIMIZER installation."""
    if not find_spec("onnx") or not find_spec("onnxruntime") or not find_spec("onnxoptimizer"):
        return False
    return True


def lib_version_satisfied(current_ver: str, mini_ver_limited: str,
                          newest_ver_limited: str = ""):
    """
    Check python lib version whether is satisfied.

    Notes:
        Version number must be format of x.x.x, e.g. 1.1.0.

    Args:
        current_ver (str): Current lib version.
        mini_ver_limited (str): Mini lib version.
        newest_ver_limited (str): Newest lib version.

    Returns:
        bool, true or false.
    """
    required_version_number_len = 3
    if len(list(current_ver.split("."))) != required_version_number_len or \
            len(list(mini_ver_limited.split("."))) != required_version_number_len or \
            (newest_ver_limited and len(newest_ver_limited.split(".")) != required_version_number_len):
        raise ValueError("Version number must be format of x.x.x.")
    if current_ver < mini_ver_limited or (newest_ver_limited and current_ver > newest_ver_limited):
        return False
    return True


def get_dict_key_by_value(val, dic):
    """
    Return the first appeared key of a dictionary by given value.

    Args:
        val (Any): Value of the key.
        dic (dict): Dictionary to be checked.

    Returns:
        Any, key of the given value.
    """
    for d_key, d_val in dic.items():
        if d_val == val:
            return d_key
    return None


def convert_bytes_string_to_string(bytes_str):
    """
    Convert a byte string to string by utf-8.

    Args:
        bytes_str (bytes): A bytes string.

    Returns:
        str, a str with utf-8 encoding.
    """
    if isinstance(bytes_str, bytes):
        return bytes_str.decode('utf-8')
    return bytes_str


def get_framework_type(model_path):
    """Get framework type."""

    model_suffix = os.path.basename(model_path).split(".")[-1].lower()
    if model_suffix == ONNX_MODEL_SUFFIX:
        framework_type = FrameworkType.ONNX.value
    elif model_suffix == TENSORFLOW_MODEL_SUFFIX:
        framework_type = FrameworkType.TENSORFLOW.value
    else:
        framework_type = FrameworkType.UNKNOWN.value

    return framework_type


def reset_init_or_construct(template, variable_slot, new_data, scope):
    """Reset init statement."""
    template[variable_slot][scope].clear()
    template[variable_slot][scope] += new_data
    return template


def replace_string_in_list(str_list: list, original_str: str, target_str: str):
    """
    Replace a string in a list by provided string.

    Args:
        str_list (list): A list contains the string to be replaced.
        original_str (str): The string to be replaced.
        target_str (str): The replacement of string.

    Returns,
        list, the original list with replaced string.
    """
    return [s.replace(original_str, target_str) for s in str_list]


def get_third_part_lib_validation_error_info(lib_list):
    """Get error info when not satisfying third part lib validation."""
    error_info = None
    link_str = ', '
    for idx, lib in enumerate(lib_list):
        if idx == len(lib_list) - 1:
            link_str = ' and '

        lib_version_required = THIRD_PART_VERSION[lib]
        if len(lib_version_required) == 2:
            lib_version_required_min = lib_version_required[0]
            lib_version_required_max = lib_version_required[1]
            if lib_version_required_min == lib_version_required_max:
                info = f"{lib}(=={lib_version_required_min})"
            else:
                info = f"{lib}(>={lib_version_required_min} and <{lib_version_required_max})"
        else:
            info = f"{lib}(>={lib_version_required[0]})"

        if not error_info:
            error_info = info
        else:
            error_info = link_str.join((error_info, info))
    return error_info

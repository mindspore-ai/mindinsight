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
import os
import re
import stat
import json
import uuid
from importlib import import_module
from importlib.util import find_spec
from typing import List, Tuple, Mapping

import numpy as np

from mindinsight.mindconverter.common.log import logger as log, logger_console as log_console
from mindinsight.mindconverter.common.exceptions import ScriptGenerationError, ReportGenerationError, \
    CheckPointGenerationError, WeightMapGenerationError, ModelLoadingError, OnnxModelSaveError, \
    ParamMissingError, BadParamError
from mindinsight.mindconverter.graph_based_converter.constant import AUTO_DETECT_NODES, SEPARATOR_IN_ONNX_OP, FrameworkType, \
    TENSORFLOW_MODEL_SUFFIX, THIRD_PART_VERSION, ONNX_MODEL_SUFFIX, DTYPE_MAP, WRITE_FLAGS, RW_MODE_FOR_OWNER, \
    RWX_MODE_FOR_OWNER


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
    except ImportError as e:
        log.exception(e)
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


def fetch_output_from_onnx_model(model, model_path: str, feed_dict: dict, output_nodes: List[str]):
    """
    Fetch specific nodes output from onnx model.

    Notes:
        Only support to get output without batch dimension.

    Args:
        model (ModelProto): ONNX model.
        model_path (str): ONNX model path.
        feed_dict (dict): Feed forward inputs.
        output_nodes (list[str]): Output nodes list.

    Returns:
        dict, nodes' output value.
    """
    if not isinstance(feed_dict, dict) or not isinstance(output_nodes, list):
        raise TypeError("`feed_dict` should be type of dict, and `output_nodes` "
                        "should be type of List[str].")

    edit_model = _add_outputs_of_onnx_model(model, output_nodes)

    onnx = import_module("onnx")
    ort = import_module("onnxruntime")
    try:
        dir_path = os.path.dirname(model_path)
        stem_name = os.path.splitext(os.path.basename(model_path))[0]
        filename = ".~{0}_{1}".format(stem_name, str(uuid.uuid4()))
        tmp_file = os.path.join(dir_path, filename)
        onnx.save_tensor(edit_model, tmp_file)
    except (TypeError, IOError) as error:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
        raise OnnxModelSaveError("Onnx model save failed, {}".format(str(error)))

    try:
        sess = ort.InferenceSession(path_or_bytes=tmp_file)
        fetched_res = sess.run(output_names=output_nodes, input_feed=feed_dict)
    except ModelLoadingError.raise_from() as error:
        raise ModelLoadingError("OnnxRuntimeError, {}".format(str(error)))
    finally:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)

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
    out_folder = os.path.realpath(out_folder)
    if not report_folder:
        report_folder = out_folder
    else:
        report_folder = os.path.realpath(report_folder)

    if not os.path.exists(out_folder):
        os.makedirs(out_folder, RWX_MODE_FOR_OWNER)
    if not os.path.exists(report_folder):
        os.makedirs(report_folder, RWX_MODE_FOR_OWNER)

    for file_name in code_lines:
        code, report, trainable_weights, weight_map = code_lines[file_name]
        code_file_path = os.path.realpath(os.path.join(out_folder, f"{model_name}.py"))
        report_file_path = os.path.realpath(os.path.join(report_folder, f"report_of_{model_name}.txt"))
        try:
            if os.path.exists(code_file_path):
                raise ScriptGenerationError("Code file with the same name already exists.")
            with os.fdopen(os.open(code_file_path, WRITE_FLAGS, RW_MODE_FOR_OWNER), 'w') as file:
                file.write(code)
        except (IOError, FileExistsError) as error:
            raise ScriptGenerationError(str(error))

        try:
            if os.path.exists(report_file_path):
                raise ReportGenerationError("Report file with the same name already exists.")
            with os.fdopen(os.open(report_file_path, WRITE_FLAGS, stat.S_IRUSR), "w") as rpt_f:
                rpt_f.write(report)
        except (IOError, FileExistsError) as error:
            raise ReportGenerationError(str(error))

        save_checkpoint = getattr(import_module("mindspore.train.serialization"), "save_checkpoint")
        for idx, trainable_weight in enumerate(trainable_weights):
            if len(trainable_weights) > 1:
                ckpt_file_path = os.path.realpath(os.path.join(out_folder, f"{model_name}_{idx}.ckpt"))
            else:
                ckpt_file_path = os.path.realpath(os.path.join(out_folder, f"{model_name}.ckpt"))
            if os.path.exists(ckpt_file_path):
                raise CheckPointGenerationError("Checkpoint file with the same name already exists.")
            try:
                save_checkpoint(trainable_weight, ckpt_file_path)
            except TypeError as error:
                raise CheckPointGenerationError(str(error))

        weight_map_path = os.path.realpath(os.path.join(report_folder, f"weight_map_of_{model_name}.json"))
        try:
            if os.path.exists(weight_map_path):
                raise WeightMapGenerationError("Weight map file with the same name already exists.")
            with os.fdopen(os.open(weight_map_path, WRITE_FLAGS, stat.S_IRUSR), 'w') as map_f:
                weight_map_json = {f"{model_name}": weight_map}
                json.dump(weight_map_json, map_f)
        except (IOError, FileExistsError) as error:
            raise WeightMapGenerationError(str(error))


def onnx_satisfied():
    """Validate ONNX, ONNXRUNTIME, ONNXOPTIMIZER installation."""
    if not find_spec("onnx") or not find_spec("onnxruntime") or not find_spec("onnxoptimizer"):
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


def get_third_part_lib_error_info(lib_list, required_lib_versions=None):
    """Get error info when not satisfying third part lib validation."""
    required_lib_versions = required_lib_versions or THIRD_PART_VERSION
    error_info = None
    link_str = ', '
    for idx, lib in enumerate(lib_list):
        if idx == len(lib_list) - 1:
            link_str = ' and '

        lib_version_required = required_lib_versions.get(lib)
        if lib_version_required:
            if len(lib_version_required) == 2:
                lib_version_required_min = lib_version_required[0]
                lib_version_required_max = lib_version_required[1]
                if lib_version_required_min == lib_version_required_max:
                    info = f"{lib}(=={lib_version_required_min})"
                else:
                    info = f"{lib}(>={lib_version_required_min} and <{lib_version_required_max})"
            else:
                link_mark = '' if lib_version_required[0] == 'NotFound' else '>='
                info = f"{lib}({link_mark}{lib_version_required[0]})"
        else:
            info = f"{lib}"

        if not error_info:
            error_info = info
        else:
            error_info = link_str.join((error_info, info))
    return error_info


def save_intermediate_graph(dataloader, output_folder):
    """
    Save intermediate graph and topological order into output_folder.

    Args:
        dataloader (OnnxDataLoader): Dataloader inst.
        output_folder (str): Output folder path.
    """
    node_topo_order = []
    placeholder_width = 30
    for node_name, node in dataloader.nodes_dict.items():
        row = f"{node.op_type.ljust(placeholder_width)} {node_name}\n"
        node_topo_order.append(row)

    # Import onnx lib.
    onnx = import_module("onnx")

    out_folder = os.path.realpath(output_folder)
    if not os.path.exists(out_folder):
        os.makedirs(out_folder, RWX_MODE_FOR_OWNER)

    graph_file = os.path.join(out_folder, "graph.onnx")
    topological_order_file = os.path.join(out_folder, "topological_order.txt")

    if os.path.exists(topological_order_file):
        err_msg = f"{os.path.basename(topological_order_file)} already exists."
        log.error(err_msg)
        raise FileExistsError(err_msg)
    if os.path.exists(graph_file):
        err_msg = f"{os.path.basename(graph_file)} already exists."
        log.error(err_msg)
        raise FileExistsError(err_msg)

    # Write topological order to disk.
    with os.fdopen(os.open(topological_order_file, WRITE_FLAGS, stat.S_IRUSR), "w") as topo_file:
        topo_file.writelines(node_topo_order)

    try:
        # Save graph to disk.
        onnx.save_model(dataloader.inferred_model, graph_file)
        os.chmod(graph_file, RW_MODE_FOR_OWNER)
    except (IOError, OSError, FileExistsError) as e:
        if os.path.exists(topological_order_file):
            os.remove(topological_order_file)
        if os.path.exists(graph_file):
            os.remove(graph_file)
        raise e


def get_current_lib_versions(lib_list):
    """Get current lib versions."""
    current_lib_versions = dict()
    for lib in lib_list:
        try:
            if lib == 'onnxoptimizer':
                ver = getattr(import_module("onnxoptimizer.version"), 'version')
            else:
                ver = getattr(import_module(lib), '__version__')
        except ImportError:
            ver = 'NotFound'
        current_lib_versions[lib] = (ver, ver)
    return current_lib_versions


def get_lib_notice_info():
    """Get current lib information and required lib information."""
    common_lib_list = ['mindspore', 'onnx', 'onnxruntime', 'onnxoptimizer']
    tf_lib_list = ['tensorflow', 'tf2onnx']
    current_lib_versions = get_current_lib_versions(common_lib_list + tf_lib_list)
    info = f"Libraries {get_third_part_lib_error_info(common_lib_list)} are required by converter, " \
           f"{get_third_part_lib_error_info(tf_lib_list)} are required when converted from TF(.pb). " \
           f"Current versions are: " \
           f"{get_third_part_lib_error_info(common_lib_list + tf_lib_list, current_lib_versions)}."
    return info


def check_params_exist(params: list, config):
    """Check params exist."""
    miss_param_list = ''
    for param in params:
        if not config.get(param):
            miss_param_list = ', '.join((miss_param_list, param)) if miss_param_list else param

    if miss_param_list:
        raise ParamMissingError(
            f"Param(s) missing, {miss_param_list} is(are) required when using graph mode.", only_console=True)


def extract_from_cli(file_config, check_params):
    """Get params from CLI."""
    check_params_exist(check_params, file_config)

    if len(file_config['shape']) != len(file_config.get("input_nodes", [])):
        raise BadParamError("`--shape` and `--input_nodes` must have the same length, "
                            "and no redundant node in `--input_nodes`.", only_console=True)

    input_nodes = dict()
    for shape, node in zip(file_config['shape'], file_config['input_nodes']):
        input_nodes[node] = shape
    return input_nodes


def extract_from_model(input_instances, file_config):
    """Get params from model."""
    node_with_dynamic_shape = list()
    input_nodes = dict()

    onnx = import_module("onnx")
    pattern = re.compile(r"%(.+?)\[(.+?), (.+?)]")
    for input_inst in input_instances:
        value_info = onnx.helper.printable_value_info(input_inst)
        output = re.findall(pattern, value_info)[0]

        name, _, shape_str = output
        shape_org = shape_str.split("x")
        shape = [int(dim) for dim in shape_org if dim.isdigit()]
        if len(shape) == len(shape_org):
            input_nodes[name] = shape
        else:
            if not file_config.get("shape") or not file_config.get("input_nodes"):
                log_console.warning(f"Static shape is required, but input `{name}` with shape {shape_org} is gotten. "
                                    f"Use `--input_nodes` and `--shape` to set static shape.")
            node_with_dynamic_shape.append(name)

    if node_with_dynamic_shape:
        input_nodes_cli = extract_from_cli(file_config, check_params=("shape", "input_nodes"))
        for dynamic_name in node_with_dynamic_shape:
            shape_from_cli = input_nodes_cli.get(dynamic_name)
            if not shape_from_cli:
                raise BadParamError(f"Input `{dynamic_name}` is not found in param `--input_nodes`.")
            input_nodes[dynamic_name] = shape_from_cli
    return input_nodes


def extract_in_out_nodes(file_config, frame_type):
    """Extract input_nodes and output_nodes."""
    if frame_type == FrameworkType.ONNX.value and AUTO_DETECT_NODES:
        onnx = import_module("onnx")
        model = onnx.load(file_config["model_file"])
        input_nodes = extract_from_model(model.graph.input, file_config)
        output_nodes = [out.name for out in model.graph.output]
    else:
        check_params = ("shape", "input_nodes", "output_nodes")
        input_nodes = extract_from_cli(file_config, check_params)
        output_nodes = file_config["output_nodes"]
    return input_nodes, output_nodes

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
"""Graph based scripts converter workflow."""
import os
import sys
from typing import List
from importlib import import_module
from importlib.util import find_spec
from functools import partial
from google.protobuf.internal import api_implementation
from mindinsight.mindconverter.graph_based_converter.common.global_context import GlobalContext
from mindinsight.mindconverter.graph_based_converter.common.utils import lib_version_satisfied, onnx_satisfied, \
    save_code_file_and_report, get_framework_type, check_dependency_integrity, get_third_part_lib_validation_error_info
from mindinsight.mindconverter.graph_based_converter.constant import FrameworkType, \
    ONNX_MIN_VER, TF2ONNX_MIN_VER, ONNXRUNTIME_MIN_VER, ONNXOPTIMIZER_MIN_VER
from mindinsight.mindconverter.graph_based_converter.generator import batch_add_nodes
from mindinsight.mindconverter.graph_based_converter.mapper import ONNXToMindSporeMapper
from mindinsight.mindconverter.common.log import logger as log, logger_console as log_console
from mindinsight.mindconverter.common.exceptions import GraphInitError, TreeCreationError, SourceFilesSaveError, \
    BaseConverterError, UnknownModelError, GeneratorError, TfRuntimeError, RuntimeIntegrityError, ParamMissingError, \
    BadParamError
from mindinsight.mindconverter.graph_based_converter.third_party_graph import GraphFactory

check_common_dependency_integrity = partial(check_dependency_integrity,
                                            "onnx", "onnxruntime", "onnxoptimizer")


def onnx_lib_version_satisfied():
    """Check onnx libs version whether is satisfied."""
    onnx = import_module("onnx")
    ort = import_module("onnxruntime")
    optimizer = import_module("onnxoptimizer.version")
    if not lib_version_satisfied(getattr(ort, "__version__"), ONNXRUNTIME_MIN_VER):
        log_console.warning(f"onnxruntime's version should be greater than {ONNXRUNTIME_MIN_VER}, "
                            f"however current version is {ort.__version__}.")

    if not lib_version_satisfied(getattr(onnx, "__version__"), ONNX_MIN_VER) \
            or not lib_version_satisfied(getattr(optimizer, "version"), ONNXOPTIMIZER_MIN_VER):
        return False
    return True


def _print_error(err):
    """Print error to stdout and record it."""
    log.error(err)
    log_console.error(str(err))


def onnx_installation_validation(func):
    """
    Validate args of func.

    Args:
        func (type): Function.

    Returns:
        type, inner function.
    """

    def _f(graph_path: str, input_nodes: dict, output_nodes: List[str],
           output_folder: str, report_folder: str = None):
        # Check whether onnx is installed.
        error_info = f"{get_third_part_lib_validation_error_info(['onnx', 'onnxruntime', 'onnxoptimizer'])} " \
                     f"are required when using graph based scripts converter or ONNX conversion."

        if not onnx_satisfied() or not check_common_dependency_integrity():
            _print_error(RuntimeIntegrityError(error_info))
            sys.exit(0)

        if not onnx_lib_version_satisfied():
            _print_error(RuntimeIntegrityError(error_info))
            sys.exit(0)

        func(graph_path=graph_path,
             input_nodes=input_nodes, output_nodes=output_nodes,
             output_folder=output_folder, report_folder=report_folder)

    return _f


def _check_tf_installation():
    """
    Check whether TensorFlow was installed.

    Returns:
        bool, true or false.
    """
    return find_spec("tensorflow") or find_spec("tensorflow-gpu")


def tf_installation_validation(func):
    """
    Validate args of func.

    Args:
        func (type): Function.

    Returns:
        type, inner function.
    """

    def _f(graph_path: str, input_nodes: dict, output_nodes: List[str],
           output_folder: str, report_folder: str):
        not_integral_error = RuntimeIntegrityError(
            f"TensorFlow, "
            f"{get_third_part_lib_validation_error_info(['tf2onnx', 'onnx', 'onnxruntime', 'onnxoptimizer'])} "
            f"are required when using graph based scripts converter for TensorFlow conversion."
        )
        # Check whether tensorflow is installed.
        if not _check_tf_installation() or not onnx_satisfied():
            _print_error(not_integral_error)
            sys.exit(0)

        if not any([check_common_dependency_integrity("tensorflow"),
                    check_common_dependency_integrity("tensorflow-gpu")]):
            _print_error(not_integral_error)
            sys.exit(0)

        tf2onnx = import_module("tf2onnx")

        if not lib_version_satisfied(getattr(tf2onnx, "__version__"), TF2ONNX_MIN_VER) \
                or not onnx_lib_version_satisfied():
            _print_error(not_integral_error)
            sys.exit(0)

        func(graph_path=graph_path,
             input_nodes=input_nodes, output_nodes=output_nodes,
             output_folder=output_folder, report_folder=report_folder)

    return _f


def _extract_model_name(model_path):
    """
    Extract model name from model path.

    Args:
        model_path (str): Path of Converted model.

    Returns:
        str, name of Converted model.
    """

    base_path = os.path.basename(model_path)
    model_name = '.'.join(base_path.split('.')[:-1])
    return model_name


@onnx_installation_validation
@GraphInitError.uniform_catcher()
@TreeCreationError.uniform_catcher()
@SourceFilesSaveError.uniform_catcher()
@GeneratorError.uniform_catcher()
def graph_based_converter_onnx_to_ms(graph_path: str,
                                     input_nodes: dict, output_nodes: List[str],
                                     output_folder: str, report_folder: str = None):
    """
    ONNX to MindSpore based on Graph.

    Args:
        graph_path (str): Graph file path.
        input_nodes (dict): Input node(s) of the model.
        output_nodes (list[str]): Output node(s) of the model.
        output_folder (str): Output folder.
        report_folder (str): Report output folder path.
    """
    graph_obj = GraphFactory.init(graph_path, input_nodes=input_nodes, output_nodes=output_nodes)
    generator_inst = batch_add_nodes(graph_obj, ONNXToMindSporeMapper)
    model_name = _extract_model_name(graph_path)
    code_fragments = generator_inst.generate()
    save_code_file_and_report(model_name, code_fragments, output_folder, report_folder)
    # Release global context.
    GlobalContext.release()


@tf_installation_validation
@GraphInitError.uniform_catcher()
@TfRuntimeError.uniform_catcher()
@TreeCreationError.uniform_catcher()
@SourceFilesSaveError.uniform_catcher()
@GeneratorError.uniform_catcher()
def graph_based_converter_tf_to_ms(graph_path: str,
                                   input_nodes: dict, output_nodes: List[str],
                                   output_folder: str, report_folder: str = None):
    """
    Tensorflow to MindSpore based on Graph.

    Args:
        graph_path (str): Graph file path.
        input_nodes (dict): Input node(s) of the model.
        output_nodes (list[str]): Output node(s) of the model.
        output_folder (str): Output folder.
        report_folder (str): Report output folder path.
    """
    # Close unnecessary log.
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

    graph_obj = GraphFactory.init(graph_path, input_nodes=input_nodes, output_nodes=output_nodes)
    generator_inst = batch_add_nodes(graph_obj, ONNXToMindSporeMapper)
    model_name = _extract_model_name(graph_path)
    code_fragments = generator_inst.generate()
    save_code_file_and_report(model_name, code_fragments, output_folder, report_folder)
    # Release global context.
    GlobalContext.release()


@BaseConverterError.uniform_catcher()
def main_graph_base_converter(file_config):
    """
    The entrance for converter, script files will be converted.

    Args:
        file_config (dict): The config of file which to convert.
    """

    if api_implementation.Type() != 'cpp' or os.getenv('PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION') != 'cpp':
        log_console.warning("Protobuf is currently implemented in \"Python\". "
                            "The conversion process may take a long time. "
                            "Please use `export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=cpp` to enable cpp backend.")

    graph_path = file_config['model_file']
    frame_type = get_framework_type(graph_path)
    if not file_config.get("shape"):
        raise ParamMissingError("Param missing, `--shape` is required when using graph mode.")

    check_params = ['input_nodes', 'output_nodes']
    check_params_exist(check_params, file_config)

    if len(file_config['shape']) != len(file_config.get("input_nodes", [])):
        raise BadParamError("`--shape` and `--input_nodes` must have the same length, "
                            "and no redundant node in `--input_nodes`.")

    input_nodes = dict()
    for shape, node in zip(file_config['shape'], file_config['input_nodes']):
        input_nodes[node] = shape

    if frame_type == FrameworkType.ONNX.value:
        graph_based_converter_onnx_to_ms(graph_path=graph_path,
                                         input_nodes=input_nodes,
                                         output_nodes=file_config['output_nodes'],
                                         output_folder=file_config['outfile_dir'],
                                         report_folder=file_config['report_dir'])

    elif frame_type == FrameworkType.TENSORFLOW.value:
        graph_based_converter_tf_to_ms(graph_path=graph_path,
                                       input_nodes=input_nodes,
                                       output_nodes=file_config['output_nodes'],
                                       output_folder=file_config['outfile_dir'],
                                       report_folder=file_config['report_dir'])
    else:
        error_msg = "Get UNSUPPORTED model."
        error = UnknownModelError(error_msg)
        raise error


def check_params_exist(params: list, config):
    """Check params exist."""
    miss_param_list = ''
    for param in params:
        if not config.get(param) or not config[param]:
            miss_param_list = ', '.join((miss_param_list, param)) if miss_param_list else param

    if miss_param_list:
        raise ParamMissingError(f"Param(s) missing, {miss_param_list} is(are) required when using graph mode.")

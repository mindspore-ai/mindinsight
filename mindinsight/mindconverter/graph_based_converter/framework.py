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
from typing import List, Mapping, Dict
from importlib.util import find_spec
from functools import partial
from google.protobuf.internal import api_implementation
from mindinsight.mindconverter.graph_based_converter.common.convert_graph import convert_msgraph
from mindinsight.mindconverter.graph_based_converter.common.global_context import GlobalContext
from mindinsight.mindconverter.graph_based_converter.common.mcgraph import ConverterGraph
from mindinsight.mindconverter.graph_based_converter.common.utils import onnx_satisfied, \
    save_code_file_and_report, get_framework_type, check_dependency_integrity, \
    get_third_part_lib_error_info, save_intermediate_graph, extract_in_out_nodes
from mindinsight.mindconverter.graph_based_converter.constant import FrameworkType
from mindinsight.mindconverter.graph_based_converter.generator import batch_add_nodes
from mindinsight.mindconverter.graph_based_converter.mapper import ONNXToMindSporeMapper
from mindinsight.mindconverter.common.log import logger as log, logger_console as log_console
from mindinsight.mindconverter.common.exceptions import GraphInitError, FileSaveError, \
    BaseConverterError, UnknownModelError, GeneratorError, TfRuntimeError, RuntimeIntegrityError, \
    SubGraphSearchingError
from mindinsight.mindconverter.graph_based_converter.third_party_graph import GraphFactory

check_common_dependency_integrity = partial(check_dependency_integrity,
                                            "onnx", "onnxruntime", "onnxoptimizer", "mindspore")


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

    def _f(*args, **kwargs):
        error_info = \
            f"{get_third_part_lib_error_info(['mindspore', 'onnx', 'onnxruntime', 'onnxoptimizer'])} " \
            f"are required when using graph based scripts converter or ONNX conversion."

        # Check whether common dependency integrity is installed.
        if not onnx_satisfied() or not check_common_dependency_integrity():
            _print_error(RuntimeIntegrityError(error_info))
            sys.exit(-1)

        func(*args, **kwargs)

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

    def _f(*args, **kwargs):
        not_integral_error = RuntimeIntegrityError(
            f"TensorFlow, "
            f"{get_third_part_lib_error_info(['mindspore', 'tf2onnx', 'onnx', 'onnxruntime', 'onnxoptimizer'])} "
            f"are required when using graph based scripts converter for TensorFlow conversion."
        )
        # Check whether tensorflow and common dependency integrity are installed.
        if not _check_tf_installation() or not onnx_satisfied():
            _print_error(not_integral_error)
            sys.exit(-1)

        if not check_common_dependency_integrity("tensorflow"):
            _print_error(not_integral_error)
            sys.exit(-1)

        func(*args, **kwargs)

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
@FileSaveError.uniform_catcher()
@GeneratorError.uniform_catcher()
def graph_based_converter_onnx_to_ms(graph_path: str,
                                     input_nodes: dict, output_nodes: List[str],
                                     output_folder: str, report_folder: str = None,
                                     query_result_folder: str = None):
    """
    ONNX to MindSpore based on Graph.

    Args:
        graph_path (str): Graph file path.
        input_nodes (dict): Input node(s) of the model.
        output_nodes (list[str]): Output node(s) of the model.
        output_folder (str): Output folder.
        report_folder (str): Report output folder path.
        query_result_folder (str): Save the optimized graph and its topological order to disk.
    """
    graph_obj = GraphFactory.init(graph_path, input_nodes=input_nodes, output_nodes=output_nodes)
    if query_result_folder:
        save_intermediate_graph(graph_obj.dataloader, query_result_folder)
        GlobalContext.release()
        return
    graph_obj.build()
    generator_inst = batch_add_nodes(graph_obj, ONNXToMindSporeMapper)
    model_name = _extract_model_name(graph_path)
    log_console.info("Code saving begins.")
    code_fragments = generator_inst.generate()
    save_code_file_and_report(model_name, code_fragments, output_folder, report_folder)
    log_console.info("Code saving is finished.")
    # Release global context.
    GlobalContext.release()


@tf_installation_validation
@GraphInitError.uniform_catcher()
@TfRuntimeError.uniform_catcher()
@FileSaveError.uniform_catcher()
@GeneratorError.uniform_catcher()
def graph_based_converter_tf_to_ms(graph_path: str,
                                   input_nodes: dict, output_nodes: List[str],
                                   output_folder: str, report_folder: str = None,
                                   query_result_folder: str = None):
    """
    Tensorflow to MindSpore based on Graph.

    Args:
        graph_path (str): Graph file path.
        input_nodes (dict): Input node(s) of the model.
        output_nodes (list[str]): Output node(s) of the model.
        output_folder (str): Output folder.
        report_folder (str): Report output folder path.
        query_result_folder (str): Save the optimized graph and its topological order to disk.
    """
    # Close unnecessary log.
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

    graph_obj = GraphFactory.init(graph_path, input_nodes=input_nodes, output_nodes=output_nodes)
    if query_result_folder:
        save_intermediate_graph(graph_obj.dataloader, query_result_folder)
        GlobalContext.release()
        return
    graph_obj.build()
    generator_inst = batch_add_nodes(graph_obj, ONNXToMindSporeMapper)
    model_name = _extract_model_name(graph_path)
    log_console.info("Code saving begins.")
    code_fragments = generator_inst.generate()
    save_code_file_and_report(model_name, code_fragments, output_folder, report_folder)
    log_console.info("Code saving is finished.")
    # Release global context.
    GlobalContext.release()


@FileSaveError.uniform_catcher()
@GeneratorError.uniform_catcher()
@SubGraphSearchingError.uniform_catcher()
def convert_according_to_user_selections(graph_obj, output_folder: str, report_folder: str = None,
                                         user_operations: Mapping[str, Dict] = None):
    """
    ONNX to MindSpore based on Graph.

    Args:
        graph_obj (OnnxGraph): Onnx graph object.
        output_folder (str): Output folder.
        report_folder (str): Report output folder path.
        user_operations (dict): Record user's operations.
    """
    graph_obj.generate_scope_name(user_operations)
    graph_obj.build()
    generator_inst = batch_add_nodes(graph_obj, ONNXToMindSporeMapper)
    model_name = _extract_model_name(graph_obj.model_path)
    log_console.info("Code saving begins.")
    code_fragments = generator_inst.generate()
    save_code_file_and_report(model_name, code_fragments, output_folder, report_folder)
    log_console.info("Code saving is finished.")
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
    input_nodes, output_nodes = extract_in_out_nodes(file_config, frame_type)

    if frame_type == FrameworkType.ONNX.value:
        graph_based_converter_onnx_to_ms(graph_path=graph_path,
                                         input_nodes=input_nodes,
                                         output_nodes=output_nodes,
                                         output_folder=file_config['outfile_dir'],
                                         report_folder=file_config['report_dir'],
                                         query_result_folder=file_config.get("query_result_folder"))

    elif frame_type == FrameworkType.TENSORFLOW.value:
        graph_based_converter_tf_to_ms(graph_path=graph_path,
                                       input_nodes=input_nodes,
                                       output_nodes=output_nodes,
                                       output_folder=file_config['outfile_dir'],
                                       report_folder=file_config['report_dir'],
                                       query_result_folder=file_config.get("query_result_folder"))

    else:
        error_msg = "Get UNSUPPORTED model."
        error = UnknownModelError(error_msg)
        raise error


def get_ms_graph_from_onnx(graph_path: str, input_nodes: dict, output_nodes: List[str]):
    """
    Get ConverterGraph data structure from onnx model.

    Args:
        graph_path (str): Graph file path.
        input_nodes (dict): Input node(s) of the model.
        output_nodes (list[str]): Output node(s) of the model.
    """
    graph_obj = GraphFactory.init(graph_path, input_nodes=input_nodes, output_nodes=output_nodes)
    ms_graph = convert_msgraph(graph_obj.dataloader.inferred_model)
    mcgraph = ConverterGraph()
    mcgraph.build_graph(ms_graph.graph)
    nodes = mcgraph.list_node_by_scope()
    return {'nodes': nodes}


def convert_from_ui(graph_path: str, scope: dict, input_nodes: dict, output_nodes: List[str], output_folder: str):
    """
    Convert the graph according to user selections.

    Args:
        graph_path (str): Graph file path.
        scope (dict): Dict of User operations.
        input_nodes (dict): Input node(s) of the model.
        output_nodes (list[str]): Output node(s) of the model.
        output_folder (str): Output folder of the code.

    Returns:
        str, reply message.
    """
    graph_obj = GraphFactory.init(graph_path, input_nodes=input_nodes, output_nodes=output_nodes)
    convert_according_to_user_selections(graph_obj, output_folder=output_folder,
                                         user_operations=scope["user_operations"])
    return {'msg': "Convert successfully."}

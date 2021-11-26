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
from typing import List, Mapping, Dict
from google.protobuf.internal import api_implementation
from mindconverter.graph_based_converter.common.global_context import GlobalContext
from mindconverter.graph_based_converter.common.utils import save_code_file_and_report, get_framework_type, \
    save_intermediate_graph, extract_in_out_nodes, generate_operator_scanning_report, \
    onnx_installation_validation, extract_model_name, tf_installation_validation, torch_installation_validation
from mindconverter.graph_based_converter.constant import FrameworkType
from mindconverter.graph_based_converter.generator import batch_add_nodes
from mindconverter.graph_based_converter.mapper import ONNXToMindSporeMapper, PytorchToMindSporeMapper, get_table
from mindconverter.common.log import MindConverterLogger
from mindconverter.common.exceptions import GraphInitError, FileSaveError, \
    BaseConverterError, UnknownModelError, GeneratorError, TfRuntimeError, SubGraphSearchingError
from mindconverter.graph_based_converter.third_party_graph import GraphFactory
from mindconverter.graph_based_converter.third_party_graph.pytorch_graph import PytorchGraph


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
    generate_operator_scanning_report(graph_obj, get_table("onnx"), "onnx", report_folder)
    generator_inst = batch_add_nodes(graph_obj, ONNXToMindSporeMapper)
    model_name = extract_model_name(graph_path)
    MindConverterLogger.info("Code saving begins.")
    code_fragments = generator_inst.generate()
    save_code_file_and_report(model_name, code_fragments, output_folder, report_folder)
    MindConverterLogger.info("Code saving is finished.")
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
    model_name = extract_model_name(graph_path)
    MindConverterLogger.info("Code saving begins.")
    code_fragments = generator_inst.generate()
    save_code_file_and_report(model_name, code_fragments, output_folder, report_folder)
    MindConverterLogger.info("Code saving is finished.")
    # Release global context.
    GlobalContext.release()


def convert_according_to_user_selections(graph_obj, output_folder: str, report_folder: str = None,
                                         user_operations: Mapping[str, Dict] = None):
    """
    X to MindSpore based on Graph.

    Args:
        graph_obj (Graph): Graph object.
        output_folder (str): Output folder.
        report_folder (str): Report output folder path.
        user_operations (dict): Record user's operations.
    """
    graph_obj.generate_scope_name(user_operations)
    graph_obj.build()
    generator_inst = batch_add_nodes(graph_obj, PytorchToMindSporeMapper)
    model_name = extract_model_name(graph_obj.model_path)
    MindConverterLogger.info("Code saving begins.")
    code_fragments = generator_inst.generate()
    save_code_file_and_report(model_name, code_fragments, output_folder, report_folder)
    MindConverterLogger.info("Code saving is finished.")
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
        MindConverterLogger.warning("Protobuf is currently implemented in \"Python\". The conversion process may take "
                                    "a long time. Please use `export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=cpp` "
                                    "to enable cpp backend.")

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


@torch_installation_validation
@FileSaveError.uniform_catcher()
@GeneratorError.uniform_catcher()
@SubGraphSearchingError.uniform_catcher()
@GraphInitError.uniform_catcher()
def convert_api(model, dummy_inputs, output_dir=None):
    """
    Api to convert the model.
    Call the api in model script to run conversion.
    """
    if not isinstance(dummy_inputs, tuple):
        dummy_inputs = (dummy_inputs,)

    graph_obj = PytorchGraph(model, input_tensors=dummy_inputs)
    default_output_dir = os.path.realpath(os.path.join(os.getcwd(), "output"))
    output_dir = output_dir or default_output_dir
    convert_according_to_user_selections(graph_obj, output_folder=output_dir, user_operations=graph_obj.patterns)

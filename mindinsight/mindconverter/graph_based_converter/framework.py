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
"""Graph based scripts converter workflow."""
import os
import re
import argparse
from importlib import import_module
from importlib.util import find_spec

import mindinsight
from mindinsight.mindconverter.graph_based_converter.constant import BINARY_HEADER_PYTORCH_FILE, FrameworkType, \
    BINARY_HEADER_PYTORCH_BITS
from mindinsight.mindconverter.graph_based_converter.mapper import ONNXToMindSporeMapper
from mindinsight.mindconverter.common.log import logger as log
from mindinsight.mindconverter.common.exceptions import GraphInitFail, TreeCreateFail, SourceFilesSaveFail, \
    BaseConverterFail, UnknownModel
from mindinsight.utils.exceptions import ParamMissError

permissions = os.R_OK | os.W_OK | os.X_OK
os.umask(permissions << 3 | permissions)

parser = argparse.ArgumentParser(
    prog="MindConverter",
    description="Graph based MindConverter CLI entry point (version: {})".format(
        mindinsight.__version__)
)

parser.add_argument("--graph", type=str, required=True,
                    help="Third party framework's graph path.")
parser.add_argument("--sample_shape", nargs='+', type=int, required=True,
                    help="Input shape of the model.")
parser.add_argument("--ckpt", type=str, required=False,
                    help="Third party framework's checkpoint path.")
parser.add_argument("--output", type=str, required=True,
                    help="Generated scripts output folder path.")
parser.add_argument("--report", type=str, required=False,
                    help="Generated reports output folder path.")


def torch_installation_validation(func):
    """
    Validate args of func.

    Args:
        func (type): Function.

    Returns:
        type, inner function.
    """

    def _f(graph_path: str, sample_shape: tuple,
           output_folder: str, report_folder: str = None):
        # Check whether pytorch is installed.
        if not find_spec("torch"):
            error = ModuleNotFoundError("PyTorch is required when using graph based "
                                        "scripts converter, and PyTorch vision must "
                                        "be consisted with model generation runtime.")
            log.error(str(error))
            log.exception(error)
            raise error

        func(graph_path=graph_path, sample_shape=sample_shape,
             output_folder=output_folder, report_folder=report_folder)

    return _f


def tf_installation_validation(func):
    """
    Validate args of func.

    Args:
        func(type): Function.

    Returns:
        type, inner function.
    """

    def _f(graph_path: str, sample_shape: tuple,
           output_folder: str, report_folder: str = None,
           input_nodes: str = None, output_nodes: str = None):
        # Check whether tensorflow is installed.
        if not find_spec("tensorflow") or not find_spec("tf2onnx"):
            error = ModuleNotFoundError("Tensorflow and tf2onnx are required when using "
                                        "graph based scripts converter.")
            log.error(str(error))
            raise error
        func(graph_path=graph_path, sample_shape=sample_shape,
             output_folder=output_folder, report_folder=report_folder,
             input_nodes=input_nodes, output_nodes=output_nodes)

    return _f


def _extract_model_name(model_path):
    """
    Extract model name from model path.

    Args:
        model_path(str): Path of Converted model.

    Returns:
        str: Name of Converted model.
    """

    model_name = re.findall(r".*[/](.*)(?:\.pth|\.pb)", model_path)[-1]
    return model_name


@GraphInitFail.check_except_pytorch("Error occurred when init graph object.")
@TreeCreateFail.check_except_pytorch("Error occurred when create hierarchical tree.")
@SourceFilesSaveFail.check_except_pytorch("Error occurred when save source files.")
@torch_installation_validation
def graph_based_converter_pytorch_to_ms(graph_path: str, sample_shape: tuple,
                                        output_folder: str, report_folder: str = None):
    """
    Pytoch to MindSpore based on Graph.

    Args:
        graph_path (str): Graph file path.
        sample_shape (tuple): Input shape of the model.
        output_folder (str): Output folder.
        report_folder (str): Report output folder path.

    """
    third_party_graph_module = import_module(
        'mindinsight.mindconverter.graph_based_converter.third_party_graph')
    hierarchical_tree_module = import_module(
        'mindinsight.mindconverter.graph_based_converter.hierarchical_tree')
    cls_graph_factory = getattr(third_party_graph_module, 'GraphFactory')
    cls_hierarchical_tree_factory = getattr(hierarchical_tree_module, 'HierarchicalTreeFactory')

    graph_obj = cls_graph_factory.init(graph_path, sample_shape=sample_shape)

    hierarchical_tree = cls_hierarchical_tree_factory.create(graph_obj)

    model_name = _extract_model_name(graph_path)

    hierarchical_tree.save_source_files(output_folder, mapper=ONNXToMindSporeMapper,
                                        model_name=model_name,
                                        report_folder=report_folder)


@GraphInitFail.check_except_tf("Error occurred when init graph object.")
@TreeCreateFail.check_except_tf("Error occurred when create hierarchical tree.")
@SourceFilesSaveFail.check_except_tf("Error occurred when save source files.")
@tf_installation_validation
def graph_based_converter_tf_to_ms(graph_path: str, sample_shape: tuple,
                                   input_nodes: str, output_nodes: str,
                                   output_folder: str, report_folder: str = None):
    """
    Tensorflow to MindSpore based on Graph.

    Args:
        graph_path(str): Graph file path.
        sample_shape(tuple): Input shape of the model.
        input_nodes(str): Input node(s) of the model.
        output_nodes(str): Output node(s) of the model.
        output_folder(str): Output folder.
        report_folder(str): Report output folder path.

    """
    third_party_graph_module = import_module(
        'mindinsight.mindconverter.graph_based_converter.third_party_graph')
    hierarchical_tree_module = import_module(
        'mindinsight.mindconverter.graph_based_converter.hierarchical_tree')
    cls_graph_factory = getattr(third_party_graph_module, 'GraphFactory')
    cls_hierarchical_tree_factory = getattr(hierarchical_tree_module, 'HierarchicalTreeFactory')
    # Close unnecessary log.
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

    graph_obj = cls_graph_factory.init(graph_path, sample_shape=sample_shape,
                                       input_nodes=input_nodes, output_nodes=output_nodes)

    hierarchical_tree, scope_name_map = cls_hierarchical_tree_factory.create(graph_obj)

    model_name = _extract_model_name(graph_path)
    hierarchical_tree.save_source_files(output_folder, mapper=ONNXToMindSporeMapper,
                                        model_name=model_name,
                                        report_folder=report_folder,
                                        scope_name_map=scope_name_map)


@BaseConverterFail.check_except("Failed to start base converter.")
def main_graph_base_converter(file_config):
    """
    The entrance for converter, script files will be converted.

    Args:
        file_config (dict): The config of file which to convert.

    """
    graph_path = file_config['model_file']
    frame_type = get_framework_type(graph_path)
    if frame_type == FrameworkType.PYTORCH.value:
        graph_based_converter_pytorch_to_ms(graph_path=graph_path,
                                            sample_shape=file_config['shape'],
                                            output_folder=file_config['outfile_dir'],
                                            report_folder=file_config['report_dir'])
    elif frame_type == FrameworkType.TENSORFLOW.value:
        check_params = ['input_nodes', 'output_nodes']
        check_params_exist(check_params, file_config)
        graph_based_converter_tf_to_ms(graph_path=graph_path,
                                       sample_shape=file_config['shape'],
                                       input_nodes=file_config['input_nodes'],
                                       output_nodes=file_config['output_nodes'],
                                       output_folder=file_config['outfile_dir'],
                                       report_folder=file_config['report_dir'])
    else:
        error_msg = "Get UNSUPPORTED model."
        error = UnknownModel(error_msg)
        log.error(str(error))
        raise error


def get_framework_type(model_path):
    """Get framework type."""
    try:
        with open(model_path, 'rb') as f:
            if f.read(BINARY_HEADER_PYTORCH_BITS) == BINARY_HEADER_PYTORCH_FILE:
                framework_type = FrameworkType.PYTORCH.value
            else:
                framework_type = FrameworkType.TENSORFLOW.value
    except IOError:
        error_msg = "Get UNSUPPORTED model."
        error = UnknownModel(error_msg)
        log.error(str(error))
        raise error

    return framework_type


def check_params_exist(params: list, config):
    """Check params exist."""
    miss_param_list = ''
    for param in params:
        if not config.get(param) or not config[param]:
            miss_param_list = ', '.join((miss_param_list, param)) if miss_param_list else param

    if miss_param_list:
        error = ParamMissError(miss_param_list)
        log.error(str(error))
        raise error

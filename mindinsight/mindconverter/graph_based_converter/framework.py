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
import argparse
from importlib.util import find_spec

import mindinsight
from mindinsight.mindconverter.common.log import logger as log
from .mapper import ONNXToMindSporeMapper
from ..common.exceptions import NodeTypeNotSupport

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
           output_folder: str, report_folder: str = None,
           checkpoint_path: str = None):
        # Check whether pytorch is installed.
        if not find_spec("torch"):
            error = ModuleNotFoundError("PyTorch is required when using graph based "
                                        "scripts converter, and PyTorch vision must "
                                        "be consisted with model generation runtime.")
            log.error(str(error))
            log.exception(error)
            raise error

        func(graph_path=graph_path, sample_shape=sample_shape,
             output_folder=output_folder, report_folder=report_folder,
             checkpoint_path=checkpoint_path)

    return _f


@torch_installation_validation
def graph_based_converter(graph_path: str, sample_shape: tuple,
                          output_folder: str, report_folder: str = None,
                          checkpoint_path: str = None):
    """
    Graph based scripts converter.

    Args:
        graph_path (str): Graph file path.
        sample_shape (tuple): Input shape of the model.
        output_folder (str): Output folder.
        report_folder (str): Report output folder path.
        checkpoint_path (str): Checkpoint file path.

    """
    from .third_party_graph import GraphFactory
    from .hierarchical_tree import HierarchicalTreeFactory

    graph_obj = GraphFactory.init(graph_path, sample_shape=sample_shape,
                                  checkpoint=checkpoint_path)
    try:
        hierarchical_tree = HierarchicalTreeFactory.create(graph_obj)
    except Exception as e:
        log.exception(e)
        log.error("Error occur when create hierarchical tree.")
        raise NodeTypeNotSupport("This model is not supported now.")

    hierarchical_tree.save_source_files(output_folder, mapper=ONNXToMindSporeMapper,
                                        report_folder=report_folder)


def main_graph_base_converter(file_config):
    """
        The entrance for converter, script files will be converted.

        Args:
            file_config (dict): The config of file which to convert.
        """
    graph_based_converter(graph_path=file_config['model_file'],
                          sample_shape=file_config['shape'],
                          output_folder=file_config['outfile_dir'],
                          report_folder=file_config['report_dir'])

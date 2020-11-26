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
from mindinsight.mindconverter.common.log import logger as log
from .base import GraphParser


class PyTorchGraphParser(GraphParser):
    """Define pytorch graph parser."""

    @classmethod
    def parse(cls, model_path: str, **kwargs):
        """
        Parser pytorch graph.

        Args:
            model_path (str): Model file path.

        Returns:
            object, torch model.
        """
        import torch

        if not os.path.exists(model_path):
            error = FileNotFoundError("`model_path` must be assigned with "
                                      "an existed file path.")
            log.error(str(error))
            raise error

        try:
            if torch.cuda.is_available():
                model = torch.load(f=model_path)
            else:
                model = torch.load(f=model_path, map_location="cpu")
        except ModuleNotFoundError:
            error_msg = \
                "Cannot find model scripts in system path, " \
                "set `--project_path` to the path of model scripts folder correctly."
            error = ModuleNotFoundError(error_msg)
            log.error(str(error))
            log.exception(error)
            raise error
        except Exception as e:
            error_msg = "Error occurs in loading model, make sure model.pth correct."
            log.error(error_msg)
            log.exception(e)
            raise Exception(error_msg)

        return model


class TFGraphParser(GraphParser):
    """Define TF graph parser."""

    @classmethod
    def parse(cls, model_path: str, **kwargs):
        """
        Parse TF Computational Graph File (.pb)

        Args:
            model_path (str): Model file path.

        Returns:
            object, ONNX model.
        """

        from .onnx_utils import convert_tf_graph_to_onnx

        tf_input_nodes = kwargs.get('input_nodes')
        tf_output_nodes = kwargs.get('output_nodes')
        if not os.path.exists(model_path):
            error = FileNotFoundError("`model_path` must be assigned with "
                                      "an existed file path.")
            log.error(str(error))
            log.exception(error)
            raise error

        try:
            model = convert_tf_graph_to_onnx(model_path,
                                             model_inputs=tf_input_nodes,
                                             model_outputs=tf_output_nodes,
                                             )  # need pass more args

        except ModuleNotFoundError:
            error_msg = \
                "Cannot find model scripts in system path, " \
                "set `--project_path` to the path of model scripts folder correctly."
            error = ModuleNotFoundError(error_msg)
            log.error(error_msg)
            log.exception(error)
            raise error
        except Exception as e:
            error_msg = "Error occurs in loading model, make sure model.pb correct."
            log.error(error_msg)
            log.exception(e)
            raise Exception(error_msg)

        return model

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
from importlib import import_module

from mindinsight.mindconverter.common.log import logger as log
from .base import GraphParser
from ...common.exceptions import ModelNotSupportError


class PyTorchGraphParser(GraphParser):
    """Define pytorch graph parser."""

    @classmethod
    @ModelNotSupportError.check_except(
        "Error occurs in loading model, please check your model or runtime environment integrity."
    )
    def parse(cls, model_path: str, **kwargs):
        """
        Parser pytorch graph.

        Args:
            model_path (str): Model file path.

        Returns:
            object, torch model.
        """
        torch = import_module("torch")

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
            error_msg = "Cannot find model scripts in system path, " \
                        "set `--project_path` to the path of model scripts folder correctly."
            error = ModuleNotFoundError(error_msg)
            raise error

        return model

# Copyright 2019 Huawei Technologies Co., Ltd
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
"""
Description: This file is used for some common util.
"""
from unittest.mock import Mock

import pytest
from flask import Response

from mindinsight.backend import datavisual
from mindinsight.datavisual import utils


@pytest.fixture
def client():
    """This fixture is flask client."""
    mock_data_manager = Mock()
    mock_data_manager.start_load_data = Mock()
    datavisual.DATA_MANAGER = mock_data_manager

    packages = ["mindinsight.backend.raw_dataset",
                "mindinsight.backend.train_dataset",
                "mindinsight.backend.data_visual"]

    mock_obj = Mock(return_value=packages)
    utils.find_app_package = mock_obj

    from mindinsight.backend.application import APP
    APP.response_class = Response
    app_client = APP.test_client()

    yield app_client

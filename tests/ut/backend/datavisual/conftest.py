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
from mindinsight.datavisual.utils import tools


@pytest.fixture
def client():
    """This fixture is flask client."""
    mock_data_manager = Mock()
    mock_data_manager.start_load_data = Mock()
    datavisual.DATA_MANAGER = mock_data_manager

    packages = ["mindinsight.backend.data_visual"]

    mock_obj = Mock(return_value=packages)
    tools.find_app_package = mock_obj

    from mindinsight.backend.application import APP
    APP.response_class = Response
    app_client = APP.test_client()

    yield app_client


TRAIN_ROUTES = dict(
    train_jobs='/v1/mindinsight/datavisual/train-jobs',
    single_job='/v1/mindinsight/datavisual/single-job',
    plugins='/v1/mindinsight/datavisual/plugins',
    graph_nodes='/v1/mindinsight/datavisual/graphs/nodes',
    graph_nodes_names='/v1/mindinsight/datavisual/graphs/nodes/names',
    graph_single_node='/v1/mindinsight/datavisual/graphs/single-node',
    image_metadata='/v1/mindinsight/datavisual/image/metadata',
    image_single_image='/v1/mindinsight/datavisual/image/single-image',
    scalar_metadata='/v1/mindinsight/datavisual/scalar/metadata',
    histograms='/v1/mindinsight/datavisual/histograms'
)

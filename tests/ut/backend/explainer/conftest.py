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
Description: This file is used for constants and fixtures.
"""
import pytest
from flask import Response

from mindinsight.backend.application import APP


@pytest.fixture
def client():
    """This fixture is flask client."""
    APP.response_class = Response
    app_client = APP.test_client()

    yield app_client


EXPLAINER_URL_BASE = '/v1/mindinsight/explainer'

EXPLAINER_ROUTES = dict(
    explain_jobs=f'{EXPLAINER_URL_BASE}/explain-jobs',
    job_metadata=f'{EXPLAINER_URL_BASE}/explain-job',
    saliency=f'{EXPLAINER_URL_BASE}/saliency',
    evaluation=f'{EXPLAINER_URL_BASE}/evaluation',
    image=f'{EXPLAINER_URL_BASE}/image'
)

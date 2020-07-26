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
Function:
    Test error handler.
Usage:
    pytest tests/ut/datavisual
"""
from unittest.mock import patch

from werkzeug.exceptions import MethodNotAllowed, NotFound

from mindinsight.datavisual.processors.scalars_processor import ScalarsProcessor

from ....utils.tools import get_url
from ...backend.datavisual.conftest import TRAIN_ROUTES


class TestErrorHandler:
    """Test train visual api."""

    @patch.object(ScalarsProcessor, 'get_metadata_list')
    def test_handle_http_exception_error_not_found(self, mock_scalar_processor, client):
        """Test handle http exception error not found."""
        text = 'Test Message'

        # NotFound
        def get_metadata_list(train_ids, tag):
            raise NotFound("%s" % text)

        mock_scalar_processor.side_effect = get_metadata_list

        test_train_ids = "aa"
        test_tag = "bb"
        params = dict(train_ids=test_train_ids, tag=test_tag)
        url = get_url(TRAIN_ROUTES['scalar_metadata'], params)
        response = client.get(url)

        assert response.status_code == 404
        response = response.get_json()
        assert response['error_code'] == '50545001'
        assert response['error_msg'] == '404 Not Found.'

    @patch.object(ScalarsProcessor, 'get_metadata_list')
    def test_handle_http_exception_error_method_not_allowed(self, mock_scalar_processor, client):
        """Test handling http exception error method not allowed."""
        text = 'Test Message'

        # MethodNotAllowed
        def get_metadata_list(train_ids, tag):
            raise MethodNotAllowed("%s" % text)

        mock_scalar_processor.side_effect = get_metadata_list

        test_train_ids = "aa"
        test_tag = "bb"
        params = dict(train_ids=test_train_ids, tag=test_tag)
        url = get_url(TRAIN_ROUTES['scalar_metadata'], params)
        response = client.get(url)

        assert response.status_code == 405
        response = response.get_json()
        assert response['error_code'] == '50545002'
        assert response['error_msg'] == '405 Method Not Allowed.'

    @patch.object(ScalarsProcessor, 'get_metadata_list')
    def test_handle_http_exception_error_method_other_errors(self, mock_scalar_processor, client):
        """Test handling http exception error method other errors."""
        text = 'Test Message'

        # Other errors
        def get_metadata_list(train_ids, tag):
            raise KeyError("%s" % text)

        mock_scalar_processor.side_effect = get_metadata_list

        test_train_ids = "aa"
        test_tag = "bb"
        params = dict(train_ids=test_train_ids, tag=test_tag)
        url = get_url(TRAIN_ROUTES['scalar_metadata'], params)
        response = client.get(url)

        assert response.status_code == 500
        response = response.get_json()
        assert response['error_code'] == '50540000'
        assert response['error_msg'] == 'System error.'

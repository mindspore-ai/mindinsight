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
    Test train visual api.
Usage:
    pytest tests/ut/datavisual
"""
from unittest.mock import Mock, patch

import pytest

from mindinsight.datavisual.data_transform.graph import NodeTypeEnum
from mindinsight.datavisual.processors.graph_processor import GraphProcessor
from mindinsight.datavisual.processors.images_processor import ImageProcessor
from mindinsight.datavisual.processors.scalars_processor import ScalarsProcessor

from ....utils.tools import get_url
from .conftest import TRAIN_ROUTES


class TestTrainVisual:
    """Test Train Visual APIs."""

    def test_image_metadata_with_params_miss(self, client):
        """Test missing params when getting image metadata."""

        params = dict()
        url = get_url(TRAIN_ROUTES['image_metadata'], params)

        response = client.get(url)

        assert response.status_code == 400

        response = response.get_json()
        assert response['error_code'] == '50540003'
        assert response['error_msg'] == "Param missing. 'train_id' is required."

        train_id = "aa"

        params = dict(train_id=train_id)
        url = get_url(TRAIN_ROUTES['image_metadata'], params)

        response = client.get(url)

        assert response.status_code == 400

        response = response.get_json()
        assert response['error_code'] == '50540003'
        assert response['error_msg'] == "Param missing. 'tag' is required."

    @patch.object(ImageProcessor, 'get_metadata_list')
    def test_image_metadata_with_params_success(self, mock_processor, client):
        """
        Parsing available params to get image metadata.

        Test Params:
        request route: GET('/v1/mindinsight/datavisual/image/metadata').
        request params: train_id.
        request params: tag.

        Expect:
        response status code: 400.
        response json: {
            'error_code': '50545006',
            'error_message': "Invalid parameter value. 'plugin_name' only can
                             be one of ['graph', 'image', 'scalar']"
        }.
        """
        mock_get_metadata_list = Mock()
        mock_get_metadata_list.return_value = {
            "metadatas": [{
                "height": 224,
                "step": 1,
                "wall_time": 1572058058.1175,
                "width": 448
            }]
        }
        params = dict(train_id='123', tag='123')
        url = get_url(TRAIN_ROUTES['image_metadata'], params)

        mock_processor.side_effect = mock_get_metadata_list
        response = client.get(url)

        assert response.status_code == 200
        response = response.get_json()
        expected_response = {"metadatas": [{"height": 224, "step": 1, "wall_time": 1572058058.1175, "width": 448}]}
        assert expected_response == response

    def test_single_image_with_params_miss(self, client):
        """
        Test missing params when getting single image.

        Test Params:
        request route: GET('/v1/mindinsight/datavisual/image/single-image').
        request params: train_id.
        request params: tag.
        request params: step.

        Expect:
        response status code: 400.
        response json: {
            'error_code': '50540003',
            'error_message': "Param missing. 'train_id' is required."
        }.
        """
        params = dict()
        url = get_url(TRAIN_ROUTES['image_single_image'], params)
        response = client.get(url)
        assert response.status_code == 400
        response = response.get_json()
        assert response['error_code'] == '50540003'
        assert response['error_msg'] == "Param missing. 'train_id' is required."

        params = dict(train_id='123')
        url = get_url(TRAIN_ROUTES['image_single_image'], params)
        response = client.get(url)
        assert response.status_code == 400
        response = response.get_json()
        assert response['error_code'] == '50540003'
        assert response['error_msg'] == "Param missing. 'tag' is required."

        params = dict(train_id='123', tag='456')
        url = get_url(TRAIN_ROUTES['image_single_image'], params)
        response = client.get(url)
        assert response.status_code == 400
        response = response.get_json()
        assert response['error_code'] == '50540003'
        assert response['error_msg'] == "Param missing. 'step' is required."

    def test_single_image_with_step_not_int(self, client):
        """
        Test the `tag` param is not int when getting single image.

        Test Params:
        request route: GET('/v1/mindinsight/datavisual/image/single-image').
        request params: train_id.
        request params: tag.
        request params: step.

        Expect:
        response status code: 400.
        response json: {
            'error_code': '50540001',
            'error_message': "Invalid parameter type. 'step' expect Integer type."
        }.
        """
        params = dict(train_id='123', tag='456', step='abc')
        url = get_url(TRAIN_ROUTES['image_single_image'], params)
        response = client.get(url)
        assert response.status_code == 400
        response = response.get_json()
        assert response['error_code'] == '50540001'
        assert response['error_msg'] == "Invalid parameter type. 'step' expect Integer type."

    @patch.object(ImageProcessor, 'get_single_image')
    def test_single_image_with_params_success(self, mock_processor, client):
        """Test getting single image with params successfully."""
        mock_get_single_image = Mock(return_value=b'123')
        params = dict(train_id='123', tag='123', step=1)
        url = get_url(TRAIN_ROUTES['image_single_image'], params)

        mock_processor.side_effect = mock_get_single_image
        response = client.get(url)

        assert response.status_code == 200
        assert response.data == b'123'

    def test_scalar_metadata_with_params_is_none(self, client):
        """Parsing unavailable params to get scalar metadata."""
        params = dict()
        url = get_url(TRAIN_ROUTES['scalar_metadata'], params)

        response = client.get(url)
        results = response.get_json()
        assert response.status_code == 400
        assert results['error_code'] == '50540003'
        assert results['error_msg'] == "Param missing. 'train_id' is required."

        train_id = "aa"
        params = dict(train_id=train_id)
        url = get_url(TRAIN_ROUTES['scalar_metadata'], params)
        response = client.get(url)
        results = response.get_json()

        assert response.status_code == 400
        assert results['error_code'] == '50540003'
        assert results['error_msg'] == "Param missing. 'tag' is required."

    @patch.object(ScalarsProcessor, 'get_metadata_list')
    def test_scalar_metadata_success(self, mock_scalar_processor, client):
        """Parsing available params to get scalar metadata."""
        get_metadata_list = Mock(return_value={'metadatas': [{'value': 1}]})
        mock_scalar_processor.side_effect = get_metadata_list

        test_train_id = "aa"
        test_tag = "bb"
        params = dict(train_id=test_train_id, tag=test_tag)
        url = get_url(TRAIN_ROUTES['scalar_metadata'], params)
        response = client.get(url)
        assert response.status_code == 200
        results = response.get_json()
        assert results == dict(metadatas=[dict(value=1)])

    def test_graph_nodes_with_train_id_is_none(self, client):
        """Test getting graph nodes when train_id is none."""
        params = dict()
        url = get_url(TRAIN_ROUTES['graph_nodes'], params)

        response = client.get(url)
        results = response.get_json()
        assert response.status_code == 400
        assert results['error_code'] == '50540003'
        assert results['error_msg'] == "Param missing. 'train_id' is required."

    @patch.object(GraphProcessor, '__init__')
    def test_graph_nodes_with_type_is_invalid(self, mock_graph_processor, client):
        """Test getting graph nodes with invalid type."""
        mock_init = Mock(return_value=None)
        mock_graph_processor.side_effect = mock_init

        node_type = "invalid_node_type"
        params = dict(train_id='aaa', type=node_type)
        url = get_url(TRAIN_ROUTES['graph_nodes'], params)

        response = client.get(url)
        results = response.get_json()
        assert response.status_code == 400
        assert results['error_code'] == '50540002'
        assert results['error_msg'] == "Invalid parameter value. The node type " \
                                       "is not support, only either %s or %s." \
                                       "" % (NodeTypeEnum.NAME_SCOPE.value,
                                             NodeTypeEnum.POLYMERIC_SCOPE.value)

    @patch.object(GraphProcessor, '__init__')
    @patch.object(GraphProcessor, 'get_nodes')
    def test_graph_nodes_success(self, mock_graph_processor, mock_graph_processor_1, client):
        """Test getting graph nodes successfully."""

        def mock_get_nodes(name, node_type):
            return dict(name=name, node_type=node_type)

        mock_graph_processor.side_effect = mock_get_nodes

        mock_init = Mock(return_value=None)
        mock_graph_processor_1.side_effect = mock_init

        test_train_id = 'aaa'
        test_node_name = 'bbb'
        test_node_type = NodeTypeEnum.NAME_SCOPE.value
        params = dict(train_id=test_train_id, name=test_node_name, type=test_node_type)
        url = get_url(TRAIN_ROUTES['graph_nodes'], params)

        response = client.get(url)
        assert response.status_code == 200
        results = response.get_json()
        assert results == dict(name=test_node_name, node_type=test_node_type)

    def test_graph_node_names_with_train_id_is_none(self, client):
        """Test getting graph node names with train id is none."""
        params = dict()
        url = get_url(TRAIN_ROUTES['graph_nodes_names'], params)

        response = client.get(url)
        results = response.get_json()
        assert response.status_code == 400
        assert results['error_code'] == '50540003'
        assert results['error_msg'] == "Param missing. 'train_id' is required."

    @patch.object(GraphProcessor, '__init__')
    def test_graph_node_names_with_param_type(self, mock_graph_processor, client):
        """Test getting graph node names with param type."""
        mock_init = Mock(return_value=None)
        mock_graph_processor.side_effect = mock_init

        test_train_id = 'aaa'
        params = dict(train_id=test_train_id, offset='a', limit='b')
        url = get_url(TRAIN_ROUTES['graph_nodes_names'], params)

        response = client.get(url)
        results = response.get_json()
        assert response.status_code == 400
        assert results['error_code'] == '50540001'
        assert results['error_msg'] == "Invalid parameter type. 'offset' expect Integer type."

        params = dict(train_id=test_train_id, offset=1, limit='c')
        url = get_url(TRAIN_ROUTES['graph_nodes_names'], params)

        response = client.get(url)
        results = response.get_json()
        assert response.status_code == 400
        assert results['error_code'] == '50540001'
        assert results['error_msg'] == "Invalid parameter type. 'limit' expect Integer type."

    @patch.object(GraphProcessor, '__init__')
    def test_graph_node_names_with_invalid_offset(self, mock_graph_processor, client):
        """Test getting graph node names with invalid offset."""
        mock_init = Mock(return_value=None)
        mock_graph_processor.side_effect = mock_init

        test_train_id = 'aaa'
        test_offset = -1
        test_limit = 100
        params = dict(train_id=test_train_id, offset=test_offset, limit=test_limit)
        url = get_url(TRAIN_ROUTES['graph_nodes_names'], params)

        response = client.get(url)
        results = response.get_json()
        assert response.status_code == 400
        assert results['error_code'] == '50540002'
        assert results['error_msg'] == "Invalid parameter value. 'offset' should " \
                                       "be greater than or equal to 0."

    @pytest.mark.parametrize("limit", [-1, 0, 1001])
    @patch.object(GraphProcessor, '__init__')
    def test_graph_node_names_with_invalid_limit(self, mock_graph_processor, client, limit):
        """Test getting graph node names with invalid limit."""
        mock_init = Mock(return_value=None)
        mock_graph_processor.side_effect = mock_init

        test_train_id = 'aaa'
        params = dict(train_id=test_train_id, limit=limit)
        url = get_url(TRAIN_ROUTES['graph_nodes_names'], params)

        response = client.get(url)
        results = response.get_json()
        assert response.status_code == 400
        assert results['error_code'] == '50540002'
        assert results['error_msg'] == "Invalid parameter value. " \
                                       "'limit' should in [1, 1000]."

    @pytest.mark.parametrize(" offset, limit", [(0, 100), (1, 1), (0, 1000)])
    @patch.object(GraphProcessor, '__init__')
    @patch.object(GraphProcessor, 'search_node_names')
    def test_graph_node_names_success(self, mock_graph_processor, mock_graph_processor_1, client, offset, limit):
        """
        Parsing unavailable params to get image metadata.

        Test Params:
        request route: GET('/v1/mindinsight/datavisual/graph/nodes/names').
        request params: plugin_name.

        Expect:
        response status code: 200.
        response json: dict, contains search_content, offset, and limit.
        """

        def mock_search_node_names(search_content, offset, limit):
            return dict(search_content=search_content, offset=int(offset), limit=int(limit))

        mock_graph_processor.side_effect = mock_search_node_names

        mock_init = Mock(return_value=None)
        mock_graph_processor_1.side_effect = mock_init

        test_train_id = "aaa"
        test_search_content = "bbb"
        params = dict(train_id=test_train_id, search=test_search_content, offset=offset, limit=limit)
        url = get_url(TRAIN_ROUTES['graph_nodes_names'], params)
        response = client.get(url)
        assert response.status_code == 200
        results = response.get_json()
        assert results == dict(search_content=test_search_content, offset=int(offset), limit=int(limit))

    def test_graph_search_single_node_with_params_is_wrong(self, client):
        """Test searching graph single node with params is wrong."""
        test_name = 'aaa'
        params = dict(name=test_name)
        url = get_url(TRAIN_ROUTES['graph_single_node'], params)

        response = client.get(url)
        results = response.get_json()
        assert response.status_code == 400
        assert results['error_code'] == '50540003'
        assert results['error_msg'] == "Param missing. 'train_id' is required."

    @patch.object(GraphProcessor, '__init__')
    def test_graph_search_single_node_with_params_is_none(self, mock_graph_processor, client):
        """Test searching graph single node with node_name is none."""
        mock_init = Mock(return_value=None)

        mock_graph_processor.side_effect = mock_init
        params = dict()
        url = get_url(TRAIN_ROUTES['graph_single_node'], params)
        response = client.get(url)
        results = response.get_json()

        assert response.status_code == 400
        assert results['error_code'] == '50540003'
        assert results['error_msg'] == "Param missing. 'name' is required."

    @patch.object(GraphProcessor, '__init__')
    @patch.object(GraphProcessor, 'search_single_node')
    def test_graph_search_single_node_success(self, mock_graph_processor, mock_graph_processor_1, client):
        """
        Test searching graph single node successfully.

        Test Params:
        request route: GET('/v1/mindinsight/datavisual//').
        request params: plugin_name.

        Expect:
        response status code: 200.
        response json: name.
        """

        def mock_search_single_node(name):
            return name

        mock_graph_processor.side_effect = mock_search_single_node

        mock_init = Mock(return_value=None)
        mock_graph_processor_1.side_effect = mock_init

        test_train_id = "aaa"
        test_name = 'bbb'
        params = dict(train_id=test_train_id, name=test_name)
        url = get_url(TRAIN_ROUTES['graph_single_node'], params)
        response = client.get(url)
        assert response.status_code == 200
        results = response.get_json()
        assert results == test_name

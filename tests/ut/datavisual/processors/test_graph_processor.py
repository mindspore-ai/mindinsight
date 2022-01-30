# Copyright 2019-2021 Huawei Technologies Co., Ltd
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
    Test graph processor.
Usage:
    pytest tests/ut/datavisual
"""
import os
import tempfile
from unittest.mock import patch

import pytest

from mindinsight.datavisual.common import exceptions
from mindinsight.datavisual.common.enums import PluginNameEnum
from mindinsight.datavisual.common.exceptions import GraphNotExistError
from mindinsight.datavisual.common.exceptions import NodeNotInGraphError
from mindinsight.datavisual.data_transform import data_manager
from mindinsight.datavisual.data_transform.data_manager import DataManager
from mindinsight.datavisual.processors.graph_processor import GraphProcessor
from mindinsight.utils.exceptions import ParamValueError
from ..mock import MockLogger
from ....utils.log_operations import LogOperations
from ....utils.tools import compare_result_with_file, delete_files_or_dirs


class TestGraphProcessor:
    """Test Graph Processor api."""
    _steps_list = [1, 3, 5]

    _temp_path = None
    _graph_dict = None
    _mock_data_manager = None
    _train_id = None

    _generated_path = []

    graph_results_dir = os.path.join(os.path.dirname(__file__), 'graph_results')

    @classmethod
    def setup_class(cls):
        """Mock common environment for graph unittest."""
        data_manager.logger = MockLogger

    def teardown_class(self):
        """Delete temp files."""
        delete_files_or_dirs(self._generated_path)

    @pytest.fixture(scope='function')
    def load_graph_record(self):
        """Load graph record."""
        summary_base_dir = tempfile.mkdtemp()
        log_dir = tempfile.mkdtemp(dir=summary_base_dir)
        self._train_id = log_dir.replace(summary_base_dir, ".")

        log_operation = LogOperations()
        self._temp_path, self._graph_dict, _ = log_operation.generate_log(PluginNameEnum.GRAPH.value, log_dir)
        self._generated_path.append(summary_base_dir)

        self._mock_data_manager = data_manager.DataManager(summary_base_dir)
        thread, brief_thread = self._mock_data_manager.start_load_data()
        thread.join()
        brief_thread.join()

    @pytest.fixture(scope='function')
    def load_no_graph_record(self):
        """Load no graph record."""
        summary_base_dir = tempfile.mkdtemp()
        log_dir = tempfile.mkdtemp(dir=summary_base_dir)
        self._train_id = log_dir.replace(summary_base_dir, ".")

        log_operation = LogOperations()
        self._temp_path, _, _ = log_operation.generate_log(PluginNameEnum.IMAGE.value, log_dir,
                                                           dict(steps=self._steps_list, tag="image"))

        self._generated_path.append(summary_base_dir)

        self._mock_data_manager = data_manager.DataManager(summary_base_dir)
        thread, brief_thread = self._mock_data_manager.start_load_data()
        thread.join()
        brief_thread.join()

    @pytest.mark.usefixtures('load_graph_record')
    def test_get_nodes_with_not_exist_train_id(self):
        """Test getting nodes with not exist train id."""
        test_train_id = "not_exist_train_id"
        with pytest.raises(exceptions.TrainJobNotExistError) as exc_info:
            GraphProcessor(test_train_id, self._mock_data_manager)
        assert exc_info.value.message == "Train job is not exist. Detail: Can not find the train job in data manager."

    @pytest.mark.usefixtures('load_graph_record')
    @patch.object(DataManager, 'get_train_job_by_plugin')
    def test_get_nodes_with_loader_is_none(self, mock_get_train_job_by_plugin):
        """Test get nodes with loader is None."""
        mock_get_train_job_by_plugin.return_value = None
        with pytest.raises(exceptions.TrainJobNotExistError):
            GraphProcessor(self._train_id, self._mock_data_manager)

        assert mock_get_train_job_by_plugin.called

    @pytest.mark.usefixtures('load_graph_record')
    @pytest.mark.parametrize("name", ["not_exist_name"])
    def test_get_nodes_with_not_exist_name(self, name):
        """Test getting nodes with not exist name."""
        with pytest.raises(NodeNotInGraphError) as exc_info:
            graph_processor = GraphProcessor(self._train_id, self._mock_data_manager)
            graph_processor.list_nodes(name)

        assert 'Can not find node in graph by the given node name' in exc_info.value.message

    @pytest.mark.usefixtures('load_graph_record')
    @pytest.mark.parametrize(
        "name, result_file",
        [(None, 'test_get_nodes_success_expected_results1.json'),
         ('Default/conv1-Conv2d', 'test_get_nodes_success_expected_results2.json'),
         ('Default/bn1/Reshape[12]_1', 'test_get_nodes_success_expected_results3.json'),
         ('Default/bn1-BatchNorm2d', 'test_get_nodes_success_expected_results4.json'),
         ])
    def test_get_nodes_success(self, name, result_file):
        """Test getting nodes successfully."""
        graph_processor = GraphProcessor(self._train_id, self._mock_data_manager)
        results = graph_processor.list_nodes(name)

        expected_file_path = os.path.join(self.graph_results_dir, result_file)
        compare_result_with_file(results, expected_file_path)

    @pytest.mark.usefixtures('load_graph_record')
    @pytest.mark.parametrize("search_content, result_file",
                             [(None, 'test_search_node_names_with_search_content_expected_results1.json'),
                              ('Default/bn1', 'test_search_node_names_with_search_content_expected_results2.json'),
                              ('not_exist_search_content', None)])
    def test_search_node_names_with_search_content(self, search_content, result_file):
        """Test search node names with search content."""
        test_offset = 0
        test_limit = 1000

        graph_processor = GraphProcessor(self._train_id, self._mock_data_manager)
        results = graph_processor.search_node_names(search_content, test_offset, test_limit)
        if search_content == 'not_exist_search_content':
            expected_results = {'nodes': []}
            assert results == expected_results
        else:
            expected_file_path = os.path.join(self.graph_results_dir, result_file)
            compare_result_with_file(results, expected_file_path)

    @pytest.mark.usefixtures('load_graph_record')
    @pytest.mark.parametrize("offset", [-100, -1])
    def test_search_node_names_with_negative_offset(self, offset):
        """Test search node names with negative offset."""
        test_search_content = ""
        test_limit = 3

        graph_processor = GraphProcessor(self._train_id, self._mock_data_manager)
        with pytest.raises(ParamValueError) as exc_info:
            graph_processor.search_node_names(test_search_content, offset, test_limit)
        assert "'offset' should be greater than or equal to 0." in exc_info.value.message

    @pytest.mark.usefixtures('load_graph_record')
    @pytest.mark.parametrize("offset, result_file", [(1, 'test_search_node_names_with_offset_expected_results1.json')])
    def test_search_node_names_with_offset(self, offset, result_file):
        """Test search node names with offset."""
        test_search_content = "Default/bn1"
        test_offset = offset
        test_limit = 1

        graph_processor = GraphProcessor(self._train_id, self._mock_data_manager)
        results = graph_processor.search_node_names(test_search_content, test_offset, test_limit)
        expected_file_path = os.path.join(self.graph_results_dir, result_file)
        compare_result_with_file(results, expected_file_path)

    @pytest.mark.usefixtures('load_graph_record')
    def test_search_node_names_with_wrong_limit(self):
        """Test search node names with wrong limit."""
        test_search_content = ""
        test_offset = 0
        test_limit = 0

        graph_processor = GraphProcessor(self._train_id, self._mock_data_manager)
        with pytest.raises(ParamValueError) as exc_info:
            graph_processor.search_node_names(test_search_content, test_offset, test_limit)
        assert "'limit' should in [1, 1000]." in exc_info.value.message

    @pytest.mark.usefixtures('load_graph_record')
    @pytest.mark.parametrize("name, result_file",
                             [('Default/bn1', 'test_search_single_node_success_expected_results1.json')])
    def test_search_single_node_success(self, name, result_file):
        """Test searching single node successfully."""

        graph_processor = GraphProcessor(self._train_id, self._mock_data_manager)
        results = graph_processor.search_single_node(name)
        expected_file_path = os.path.join(self.graph_results_dir, result_file)
        compare_result_with_file(results, expected_file_path)

    @pytest.mark.usefixtures('load_graph_record')
    def test_search_single_node_with_not_exist_name(self):
        """Test searching single node with not exist name."""
        test_name = "not_exist_name"

        with pytest.raises(exceptions.NodeNotInGraphError):
            graph_processor = GraphProcessor(self._train_id, self._mock_data_manager)
            graph_processor.search_single_node(test_name)

    @pytest.mark.usefixtures('load_no_graph_record')
    def test_check_graph_status_no_graph(self):
        """Test checking graph status no graph."""
        with pytest.raises(GraphNotExistError) as exc_info:
            GraphProcessor(self._train_id, self._mock_data_manager)

        assert exc_info.value.error_code == '5054500C'
        assert exc_info.value.message == "Graph is not exist."

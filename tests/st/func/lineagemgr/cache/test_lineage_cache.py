# Copyright 2020 Huawei Technologies Co., Ltd
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
    Test the query module about lineage information.
Usage:
    The query module test should be run after lineagemgr/collection/model/test_model_lineage.py
    pytest lineagemgr
"""
from unittest import TestCase

import pytest

from mindinsight.datavisual.data_transform.data_manager import DataManager
from mindinsight.lineagemgr.cache_item_updater import LineageCacheItemUpdater
from mindinsight.lineagemgr.api.model import general_filter_summary_lineage, \
    general_get_summary_lineage

from ..api.test_model_api import LINEAGE_INFO_RUN1, LINEAGE_FILTRATION_EXCEPT_RUN, \
    LINEAGE_FILTRATION_RUN1, LINEAGE_FILTRATION_RUN2
from ..conftest import BASE_SUMMARY_DIR
from .....ut.lineagemgr.querier import event_data
from .....utils.tools import check_loading_done, assert_equal_lineages


@pytest.mark.usefixtures("create_summary_dir")
class TestModelApi(TestCase):
    """Test get lineage from data_manager."""
    @classmethod
    def setup_class(cls):
        data_manager = DataManager(BASE_SUMMARY_DIR)
        data_manager.register_brief_cache_item_updater(LineageCacheItemUpdater())
        data_manager.start_load_data(reload_interval=0)
        check_loading_done(data_manager)

        cls._data_manger = data_manager

    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_get_summary_lineage(self):
        """Test the interface of get_summary_lineage."""
        total_res = general_get_summary_lineage(data_manager=self._data_manger, summary_dir="./run1")
        expect_total_res = LINEAGE_INFO_RUN1
        assert_equal_lineages(expect_total_res, total_res, self.assertDictEqual)

    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_filter_summary_lineage(self):
        """Test the interface of filter_summary_lineage."""
        expect_result = {
            'customized': event_data.CUSTOMIZED__1,
            'object': [
                LINEAGE_FILTRATION_EXCEPT_RUN,
                LINEAGE_FILTRATION_RUN1,
                LINEAGE_FILTRATION_RUN2
            ],
            'count': 3
        }

        search_condition = {
            'sorted_name': 'summary_dir'
        }
        res = general_filter_summary_lineage(data_manager=self._data_manger, search_condition=search_condition)
        expect_objects = expect_result.get('object')
        for idx, res_object in enumerate(res.get('object')):
            expect_objects[idx]['model_lineage']['dataset_mark'] = res_object['model_lineage'].get('dataset_mark')
        assert_equal_lineages(expect_result, res, self.assertDictEqual)

        expect_result = {
            'customized': {},
            'object': [],
            'count': 0
        }

        search_condition = {
            'summary_dir': {
                "in": ['./dir_with_empty_lineage']
            }
        }
        res = general_filter_summary_lineage(data_manager=self._data_manger, search_condition=search_condition)
        assert_equal_lineages(expect_result, res, self.assertDictEqual)

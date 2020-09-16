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
"""Test the query_model module."""
from unittest import TestCase

from mindinsight.lineagemgr.common.exceptions.exceptions import (LineageEventFieldNotExistException,
                                                                 LineageEventNotExistException)
from mindinsight.lineagemgr.querier.query_model import LineageObj

from . import event_data
from .test_querier import create_filtration_result, create_lineage_info
from ....utils.tools import assert_equal_lineages


class TestLineageObj(TestCase):
    """Test the class of `LineageObj`."""

    def setUp(self):
        """Initialization before test case execution."""
        lineage_info = create_lineage_info(
            event_data.EVENT_TRAIN_DICT_0,
            event_data.EVENT_EVAL_DICT_0,
            event_data.EVENT_DATASET_DICT_0
        )
        self.summary_dir = '/path/to/summary0'
        self.lineage_obj = LineageObj(
            self.summary_dir,
            train_lineage=lineage_info.train_lineage,
            evaluation_lineage=lineage_info.eval_lineage,
            dataset_graph=lineage_info.dataset_graph,
        )

        lineage_info = create_lineage_info(
            event_data.EVENT_TRAIN_DICT_0,
            None, None)
        self.lineage_obj_no_eval = LineageObj(
            self.summary_dir,
            train_lineage=lineage_info.train_lineage,
            evaluation_lineage=lineage_info.eval_lineage
        )

    def test_property(self):
        """Test the function of getting property."""
        self.assertEqual(self.summary_dir, self.lineage_obj.summary_dir)
        assert_equal_lineages(
            event_data.EVENT_TRAIN_DICT_0['train_lineage']['algorithm'],
            self.lineage_obj.algorithm,
            self.assertDictEqual
        )
        assert_equal_lineages(
            event_data.EVENT_TRAIN_DICT_0['train_lineage']['model'],
            self.lineage_obj.model,
            self.assertDictEqual
        )
        assert_equal_lineages(
            event_data.EVENT_TRAIN_DICT_0['train_lineage']['train_dataset'],
            self.lineage_obj.train_dataset,
            self.assertDictEqual
        )
        assert_equal_lineages(
            event_data.EVENT_TRAIN_DICT_0['train_lineage']['hyper_parameters'],
            self.lineage_obj.hyper_parameters,
            self.assertDictEqual
        )
        assert_equal_lineages(
            event_data.METRIC_0,
            self.lineage_obj.metric,
            self.assertDictEqual
        )
        assert_equal_lineages(
            event_data.EVENT_EVAL_DICT_0['evaluation_lineage']['valid_dataset'],
            self.lineage_obj.valid_dataset,
            self.assertDictEqual
        )

    def test_property_eval_not_exist(self):
        """Test the function of getting property with no evaluation event."""
        self.assertEqual(self.summary_dir, self.lineage_obj.summary_dir)
        assert_equal_lineages(
            event_data.EVENT_TRAIN_DICT_0['train_lineage']['algorithm'],
            self.lineage_obj_no_eval.algorithm,
            self.assertDictEqual
        )
        assert_equal_lineages(
            event_data.EVENT_TRAIN_DICT_0['train_lineage']['model'],
            self.lineage_obj_no_eval.model,
            self.assertDictEqual
        )
        assert_equal_lineages(
            event_data.EVENT_TRAIN_DICT_0['train_lineage']['train_dataset'],
            self.lineage_obj_no_eval.train_dataset,
            self.assertDictEqual
        )
        assert_equal_lineages(
            event_data.EVENT_TRAIN_DICT_0['train_lineage']['hyper_parameters'],
            self.lineage_obj_no_eval.hyper_parameters,
            self.assertDictEqual
        )
        assert_equal_lineages({}, self.lineage_obj_no_eval.metric, self.assertDictEqual)
        assert_equal_lineages({}, self.lineage_obj_no_eval.valid_dataset, self.assertDictEqual)

    def test_get_summary_info(self):
        """Test the function of get_summary_info."""
        filter_keys = ['algorithm', 'model']
        expected_result = {
            'summary_dir': self.summary_dir,
            'algorithm': event_data.EVENT_TRAIN_DICT_0['train_lineage']['algorithm'],
            'model': event_data.EVENT_TRAIN_DICT_0['train_lineage']['model']
        }
        result = self.lineage_obj.get_summary_info(filter_keys)
        assert_equal_lineages(expected_result, result, self.assertDictEqual)

    def test_to_model_lineage_dict(self):
        """Test the function of to_model_lineage_dict."""
        expected_result = create_filtration_result(
            self.summary_dir,
            event_data.EVENT_TRAIN_DICT_0,
            event_data.EVENT_EVAL_DICT_0,
            event_data.METRIC_0,
            event_data.DATASET_DICT_0
        )
        expected_result['model_lineage']['dataset_mark'] = None
        expected_result.pop('dataset_graph')
        expected_result.pop('added_info')
        result = self.lineage_obj.to_model_lineage_dict()
        assert_equal_lineages(expected_result, result, self.assertDictEqual)

    def test_to_dataset_lineage_dict(self):
        """Test the function of to_dataset_lineage_dict."""
        expected_result = {
            "summary_dir": self.summary_dir,
            "dataset_graph": event_data.DATASET_DICT_0
        }
        result = self.lineage_obj.to_dataset_lineage_dict()
        self.assertDictEqual(expected_result, result)

    def test_get_value_by_key(self):
        """Test the function of get_value_by_key."""
        result = self.lineage_obj.get_value_by_key('model_size')
        self.assertEqual(
            event_data.EVENT_TRAIN_DICT_0['train_lineage']['model']['size'],
            result
        )

    def test_init_fail(self):
        """Test the function of init with exception."""
        with self.assertRaises(LineageEventNotExistException):
            LineageObj(self.summary_dir)

        lineage_info = create_lineage_info(
            event_data.EVENT_TRAIN_DICT_EXCEPTION, None, None
        )
        with self.assertRaises(LineageEventFieldNotExistException):
            self.lineage_obj = LineageObj(
                self.summary_dir,
                train_lineage=lineage_info.train_lineage,
                evaluation_lineage=lineage_info.eval_lineage
            )

        lineage_info = create_lineage_info(
            event_data.EVENT_TRAIN_DICT_0,
            event_data.EVENT_EVAL_DICT_EXCEPTION,
            event_data.EVENT_DATASET_DICT_0
        )
        with self.assertRaises(LineageEventFieldNotExistException):
            self.lineage_obj = LineageObj(
                self.summary_dir,
                train_lineage=lineage_info.train_lineage,
                evaluation_lineage=lineage_info.eval_lineage
            )

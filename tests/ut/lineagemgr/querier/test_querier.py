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
"""Test the querier module."""
import os
import time

from unittest import TestCase, mock
from unittest.mock import MagicMock

from google.protobuf.json_format import ParseDict

import mindinsight.datavisual.proto_files.mindinsight_lineage_pb2 as summary_pb2
from mindinsight.lineagemgr.common.exceptions.exceptions import LineageParamTypeError, LineageQuerierParamException
from mindinsight.lineagemgr.lineage_parser import LineageParser
from mindinsight.lineagemgr.querier.querier import Querier
from mindinsight.lineagemgr.summary.lineage_summary_analyzer import LineageInfo

from . import event_data
from ....utils.tools import assert_equal_lineages


def create_lineage_info(train_event_dict, eval_event_dict, dataset_event_dict):
    """
    Create parsed lineage info tuple.

    Args:
        train_event_dict (Union[dict, None]): The dict of train event.
        eval_event_dict (Union[dict, None]): The dict of evaluation event.
        dataset_event_dict (Union[dict, None]): The dict of dataset graph event.

    Returns:
        namedtuple, parsed lineage info.
    """
    if train_event_dict is not None:
        train_event = summary_pb2.LineageEvent()
        ParseDict(train_event_dict, train_event)
    else:
        train_event = None

    if eval_event_dict is not None:
        eval_event = summary_pb2.LineageEvent()
        ParseDict(eval_event_dict, eval_event)
    else:
        eval_event = None

    if dataset_event_dict is not None:
        dataset_event = summary_pb2.LineageEvent()
        ParseDict(dataset_event_dict, dataset_event)
    else:
        dataset_event = None

    lineage_info = LineageInfo(
        train_lineage=train_event,
        eval_lineage=eval_event,
        dataset_graph=dataset_event,
    )
    return lineage_info


def create_filtration_result(summary_dir, train_event_dict,
                             eval_event_dict, metric_dict, dataset_dict):
    """
    Create filteration result.

    Args:
        summary_dir (str): The summary dir.
        train_event_dict (dict): The dict of train event.
        eval_event_dict (dict): The dict of evaluation event.
        metric_dict (dict): The dict of metric.
        dataset_dict (dict): The dict of dataset graph.

    Returns:
        dict, the filteration result.
    """
    filtration_result = {
        "summary_dir": summary_dir,
        "model_lineage": {
            "loss_function": train_event_dict['train_lineage']['hyper_parameters']['loss_function'],
            "train_dataset_path": train_event_dict['train_lineage']['train_dataset']['train_dataset_path'],
            "train_dataset_count": train_event_dict['train_lineage']['train_dataset']['train_dataset_size'],
            "test_dataset_path": eval_event_dict['evaluation_lineage']['valid_dataset']['valid_dataset_path'],
            "test_dataset_count": eval_event_dict['evaluation_lineage']['valid_dataset']['valid_dataset_size'],
            "network": train_event_dict['train_lineage']['algorithm']['network'],
            "optimizer": train_event_dict['train_lineage']['hyper_parameters']['optimizer'],
            "learning_rate": train_event_dict['train_lineage']['hyper_parameters']['learning_rate'],
            "epoch": train_event_dict['train_lineage']['hyper_parameters']['epoch'],
            "batch_size": train_event_dict['train_lineage']['hyper_parameters']['batch_size'],
            "device_num": train_event_dict['train_lineage']['hyper_parameters']['device_num'],
            "loss": train_event_dict['train_lineage']['algorithm']['loss'],
            "model_size": train_event_dict['train_lineage']['model']['size'],
            "metric": metric_dict,
            "dataset_mark": '2',
            "user_defined": {}
        },
        "dataset_graph": dataset_dict,
        'added_info': {}
    }
    return filtration_result


def get_lineage_infos():
    """
    Get tuples of lineage info, simulate the function of summary analyzer.

    Returns:
        list[namedtuple], tuples of lineage info.
    """
    train_events = [
        event_data.EVENT_TRAIN_DICT_0,
        event_data.EVENT_TRAIN_DICT_1,
        event_data.EVENT_TRAIN_DICT_2,
        event_data.EVENT_TRAIN_DICT_3,
        event_data.EVENT_TRAIN_DICT_4,
        event_data.EVENT_TRAIN_DICT_5,
        None
    ]
    eval_events = [
        event_data.EVENT_EVAL_DICT_0,
        event_data.EVENT_EVAL_DICT_1,
        event_data.EVENT_EVAL_DICT_2,
        event_data.EVENT_EVAL_DICT_3,
        event_data.EVENT_EVAL_DICT_4,
        None,
        event_data.EVENT_EVAL_DICT_5
    ]
    dataset_events = [
        event_data.EVENT_DATASET_DICT_0
    ]*7

    lineage_infos = list(
        map(
            lambda event: create_lineage_info(event[0], event[1], event[2]),
            zip(train_events, eval_events, dataset_events)
        )
    )

    return lineage_infos


LINEAGE_INFO_0 = {
    'summary_dir': '/path/to/summary0',
    **event_data.EVENT_TRAIN_DICT_0['train_lineage'],
    'metric': event_data.METRIC_0,
    'valid_dataset': event_data.EVENT_EVAL_DICT_0['evaluation_lineage']['valid_dataset'],
    'dataset_graph': event_data.DATASET_DICT_0
}
LINEAGE_INFO_1 = {
    'summary_dir': '/path/to/summary1',
    **event_data.EVENT_TRAIN_DICT_1['train_lineage'],
    'metric': event_data.METRIC_1,
    'valid_dataset': event_data.EVENT_EVAL_DICT_1['evaluation_lineage']['valid_dataset'],
    'dataset_graph': event_data.DATASET_DICT_0
}
LINEAGE_FILTRATION_0 = create_filtration_result(
    './summary0',
    event_data.EVENT_TRAIN_DICT_0,
    event_data.EVENT_EVAL_DICT_0,
    event_data.METRIC_0,
    event_data.DATASET_DICT_0
)
LINEAGE_FILTRATION_1 = create_filtration_result(
    './summary1',
    event_data.EVENT_TRAIN_DICT_1,
    event_data.EVENT_EVAL_DICT_1,
    event_data.METRIC_1,
    event_data.DATASET_DICT_0
)
LINEAGE_FILTRATION_2 = create_filtration_result(
    './summary2',
    event_data.EVENT_TRAIN_DICT_2,
    event_data.EVENT_EVAL_DICT_2,
    event_data.METRIC_2,
    event_data.DATASET_DICT_0
)
LINEAGE_FILTRATION_3 = create_filtration_result(
    './summary3',
    event_data.EVENT_TRAIN_DICT_3,
    event_data.EVENT_EVAL_DICT_3,
    event_data.METRIC_3,
    event_data.DATASET_DICT_0
)
LINEAGE_FILTRATION_4 = create_filtration_result(
    './summary4',
    event_data.EVENT_TRAIN_DICT_4,
    event_data.EVENT_EVAL_DICT_4,
    event_data.METRIC_4,
    event_data.DATASET_DICT_0
)
LINEAGE_FILTRATION_5 = {
    "summary_dir": './summary5',
    "model_lineage": {
        "loss_function":
            event_data.EVENT_TRAIN_DICT_5['train_lineage']['hyper_parameters']['loss_function'],
        "train_dataset_path": None,
        "train_dataset_count":
            event_data.EVENT_TRAIN_DICT_5['train_lineage']['train_dataset']['train_dataset_size'],
        "test_dataset_path": None,
        "test_dataset_count": None,
        "network": event_data.EVENT_TRAIN_DICT_5['train_lineage']['algorithm']['network'],
        "optimizer": event_data.EVENT_TRAIN_DICT_5['train_lineage']['hyper_parameters']['optimizer'],
        "learning_rate":
            event_data.EVENT_TRAIN_DICT_5['train_lineage']['hyper_parameters']['learning_rate'],
        "epoch": event_data.EVENT_TRAIN_DICT_5['train_lineage']['hyper_parameters']['epoch'],
        "batch_size": event_data.EVENT_TRAIN_DICT_5['train_lineage']['hyper_parameters']['batch_size'],
        "device_num": event_data.EVENT_TRAIN_DICT_5['train_lineage']['hyper_parameters']['device_num'],
        "loss": event_data.EVENT_TRAIN_DICT_5['train_lineage']['algorithm']['loss'],
        "model_size": event_data.EVENT_TRAIN_DICT_5['train_lineage']['model']['size'],
        "metric": {},
        "dataset_mark": '2',
        "user_defined": {}
    },
    "dataset_graph": event_data.DATASET_DICT_0,
    "added_info": {}
}
LINEAGE_FILTRATION_6 = {
    "summary_dir": './summary6',
    "model_lineage": {
        "loss_function": None,
        "train_dataset_path": None,
        "train_dataset_count": None,
        "test_dataset_path":
            event_data.EVENT_EVAL_DICT_5['evaluation_lineage']['valid_dataset']['valid_dataset_path'],
        "test_dataset_count":
            event_data.EVENT_EVAL_DICT_5['evaluation_lineage']['valid_dataset']['valid_dataset_size'],
        "network": None,
        "optimizer": None,
        "learning_rate": None,
        "epoch": None,
        "batch_size": None,
        "device_num": None,
        "loss": None,
        "model_size": None,
        "metric": event_data.METRIC_5,
        "dataset_mark": '2',
        "user_defined": {}
    },
    "dataset_graph": event_data.DATASET_DICT_0,
    "added_info": {}
}


class TestQuerier(TestCase):
    """Test the class of `Querier`."""
    _MOCK_DATA_MANAGER = MagicMock()

    @mock.patch('mindinsight.lineagemgr.lineage_parser.SummaryPathParser.get_lineage_summaries')
    @mock.patch('mindinsight.lineagemgr.lineage_parser.LineageSummaryAnalyzer.get_user_defined_info')
    @mock.patch('mindinsight.lineagemgr.lineage_parser.LineageSummaryAnalyzer.get_summary_infos')
    @mock.patch('mindinsight.lineagemgr.lineage_parser.FileHandler')
    def setUp(self, mock_file_handler, *args):
        """Initialization before test case execution."""
        args[0].return_value = create_lineage_info(
            event_data.EVENT_TRAIN_DICT_0,
            event_data.EVENT_EVAL_DICT_0,
            event_data.EVENT_DATASET_DICT_0
        )
        args[1].return_value = []
        args[2].return_value = ['path']
        mock_file_handler = MagicMock()
        mock_file_handler.size = 1

        summary_dir = '/path/test/'

        lineage_infos = get_lineage_infos()
        args[0].side_effect = lineage_infos
        lineage_objects = {}
        for i in range(7):
            train_id = f'./summary{i}'
            summary_dir = os.path.join(summary_dir, train_id)
            update_time = time.time() - i
            lineage_parser = LineageParser(train_id, summary_dir, update_time)
            lineage_objects.update({train_id: lineage_parser.super_lineage_obj})

        self.multi_querier = Querier(lineage_objects)

    def test_filter_summary_lineage_success_1(self):
        """Test the success of filter_summary_lineage."""
        condition = {
            'optimizer': {
                'in': [
                    'ApplyMomentum0',
                    'ApplyMomentum1',
                    'ApplyMomentum2',
                    'ApplyMomentum4'
                ]
            },
            'learning_rate': {
                'lt': 0.5,
                'gt': 0.2
            },
            'sorted_name': 'summary_dir'
        }
        expected_result = {
            'customized': event_data.CUSTOMIZED_0,
            'object': [
                LINEAGE_FILTRATION_1,
                LINEAGE_FILTRATION_2
            ],
            'count': 2,
        }
        result = self.multi_querier.filter_summary_lineage(condition=condition)
        assert_equal_lineages(expected_result, result, self.assertDictEqual)

    def test_filter_summary_lineage_success_2(self):
        """Test the success of filter_summary_lineage."""
        condition = {
            'batch_size': {
                'le': 50,
                'ge': 35
            },
            'model_size': {
                'lt': 400716934,
                'gt': 400716931
            },
            'sorted_name': 'batch_size',
            'sorted_type': 'descending'
        }
        expected_result = {
            'customized': event_data.CUSTOMIZED_0,
            'object': [
                LINEAGE_FILTRATION_2,
                LINEAGE_FILTRATION_3
            ],
            'count': 2,
        }
        result = self.multi_querier.filter_summary_lineage(condition=condition)
        assert_equal_lineages(expected_result, result, self.assertDictEqual)

    def test_filter_summary_lineage_success_3(self):
        """Test the success of filter_summary_lineage."""
        condition = {
            'limit': 2,
            'offset': 1
        }
        expected_result = {
            'customized': event_data.CUSTOMIZED_0,
            'object': [
                LINEAGE_FILTRATION_2,
                LINEAGE_FILTRATION_3
            ],
            'count': 7,
        }
        result = self.multi_querier.filter_summary_lineage(condition=condition)
        assert_equal_lineages(expected_result, result, self.assertDictEqual)

    def test_filter_summary_lineage_success_4(self):
        """Test the success of filter_summary_lineage."""
        expected_result = {
            'customized': event_data.CUSTOMIZED_2,
            'object': [
                LINEAGE_FILTRATION_0,
                LINEAGE_FILTRATION_1,
                LINEAGE_FILTRATION_2,
                LINEAGE_FILTRATION_3,
                LINEAGE_FILTRATION_4,
                LINEAGE_FILTRATION_5,
                LINEAGE_FILTRATION_6
            ],
            'count': 7,
        }
        result = self.multi_querier.filter_summary_lineage()
        assert_equal_lineages(expected_result, result, self.assertDictEqual)

    def test_filter_summary_lineage_success_5(self):
        """Test the success of filter_summary_lineage."""
        condition = {
            'optimizer': {
                'eq': 'ApplyMomentum4'
            }
        }
        expected_result = {
            'customized': event_data.CUSTOMIZED_0,
            'object': [LINEAGE_FILTRATION_4],
            'count': 1,
        }
        result = self.multi_querier.filter_summary_lineage(condition=condition)
        assert_equal_lineages(expected_result, result, self.assertDictEqual)

    def test_filter_summary_lineage_success_6(self):
        """Test the success of filter_summary_lineage."""
        condition = {
            'sorted_name': 'metric/accuracy',
            'sorted_type': 'ascending'
        }
        expected_result = {
            'customized': event_data.CUSTOMIZED_2,
            'object': [
                LINEAGE_FILTRATION_0,
                LINEAGE_FILTRATION_5,
                LINEAGE_FILTRATION_1,
                LINEAGE_FILTRATION_2,
                LINEAGE_FILTRATION_3,
                LINEAGE_FILTRATION_4,
                LINEAGE_FILTRATION_6
            ],
            'count': 7,
        }
        result = self.multi_querier.filter_summary_lineage(condition=condition)
        assert_equal_lineages(expected_result, result, self.assertDictEqual)

    def test_filter_summary_lineage_success_7(self):
        """Test the success of filter_summary_lineage."""
        condition = {
            'sorted_name': 'metric/accuracy',
            'sorted_type': 'descending'
        }
        expected_result = {
            'customized': event_data.CUSTOMIZED_2,
            'object': [
                LINEAGE_FILTRATION_6,
                LINEAGE_FILTRATION_4,
                LINEAGE_FILTRATION_3,
                LINEAGE_FILTRATION_2,
                LINEAGE_FILTRATION_1,
                LINEAGE_FILTRATION_0,
                LINEAGE_FILTRATION_5
            ],
            'count': 7,
        }
        result = self.multi_querier.filter_summary_lineage(condition=condition)
        assert_equal_lineages(expected_result, result, self.assertDictEqual)

    def test_filter_summary_lineage_success_8(self):
        """Test the success of filter_summary_lineage."""
        condition = {
            'metric/accuracy': {
                'lt': 1.6000006,
                'gt': 1.4000004
            }
        }
        expected_result = {
            'customized': event_data.CUSTOMIZED_0,
            'object': [LINEAGE_FILTRATION_4],
            'count': 1,
        }
        result = self.multi_querier.filter_summary_lineage(condition=condition)
        assert_equal_lineages(expected_result, result, self.assertDictEqual)

    def test_filter_summary_lineage_success_9(self):
        """Test the success of filter_summary_lineage."""
        condition = {
            'limit': 3,
            'offset': 3
        }
        expected_result = {
            'customized': {},
            'object': [],
            'count': 7,
        }
        result = self.multi_querier.filter_summary_lineage(condition=condition)
        assert_equal_lineages(expected_result, result, self.assertDictEqual)

    def test_filter_summary_lineage_fail(self):
        """Test the function of filter_summary_lineage with exception."""
        condition = {
            'xxx': {
                'lt': 1.6000006,
                'gt': 1.4000004
            }
        }
        self.assertRaises(
            LineageQuerierParamException,
            self.multi_querier.filter_summary_lineage,
            condition=condition
        )

        condition = {
            'accuracy': {
                'xxx': 1
            }
        }
        self.assertRaises(
            LineageQuerierParamException,
            self.multi_querier.filter_summary_lineage,
            condition=condition
        )

        condition = {
            'sorted_name': 'xxx'
        }
        self.assertRaises(
            LineageQuerierParamException,
            self.multi_querier.filter_summary_lineage,
            condition=condition
        )

    def test_init_fail(self):
        """Test the function of init with exception."""
        obj_dict = 'a'
        with self.assertRaises(LineageParamTypeError):
            Querier(obj_dict)

        obj_dict = None
        with self.assertRaises(LineageQuerierParamException):
            Querier(obj_dict)

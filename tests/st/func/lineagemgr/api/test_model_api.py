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
    Test the query module about lineage information.
Usage:
    The query module test should be run after lineagemgr/collection/model/test_model_lineage.py
    pytest lineagemgr
"""
import os
from unittest import TestCase

import pytest

from mindinsight.lineagemgr import filter_summary_lineage, get_summary_lineage
from mindinsight.lineagemgr.common.exceptions.exceptions import (LineageFileNotFoundError, LineageParamSummaryPathError,
                                                                 LineageParamTypeError, LineageParamValueError,
                                                                 LineageSearchConditionParamError)
from ..conftest import BASE_SUMMARY_DIR, DATASET_GRAPH, SUMMARY_DIR, SUMMARY_DIR_2
from .....ut.lineagemgr.querier import event_data

LINEAGE_INFO_RUN1 = {
    'summary_dir': os.path.join(BASE_SUMMARY_DIR, 'run1'),
    'metric': {
        'accuracy': 0.78
    },
    'hyper_parameters': {
        'optimizer': 'Momentum',
        'learning_rate': 0.11999999731779099,
        'loss_function': 'SoftmaxCrossEntropyWithLogits',
        'epoch': 14,
        'parallel_mode': 'stand_alone',
        'device_num': 2,
        'batch_size': 32
    },
    'algorithm': {
        'network': 'ResNet'
    },
    'train_dataset': {
        'train_dataset_size': 731
    },
    'valid_dataset': {
        'valid_dataset_size': 10240
    },
    'model': {
        'path': '{"ckpt": "'
                + BASE_SUMMARY_DIR + '/run1/CKPtest_model.ckpt"}',
        'size': 64
    },
    'dataset_graph': DATASET_GRAPH
}
LINEAGE_FILTRATION_EXCEPT_RUN = {
    'summary_dir': os.path.join(BASE_SUMMARY_DIR, 'except_run'),
    'model_lineage': {
        'loss_function': 'SoftmaxCrossEntropyWithLogits',
        'train_dataset_path': None,
        'train_dataset_count': 1024,
        'test_dataset_path': None,
        'test_dataset_count': None,
        'user_defined': {},
        'network': 'ResNet',
        'optimizer': 'Momentum',
        'learning_rate': 0.11999999731779099,
        'epoch': 10,
        'batch_size': 32,
        'device_num': 2,
        'loss': 0.029999999329447746,
        'model_size': 64,
        'metric': {},
        'dataset_mark': 2
    },
    'dataset_graph': DATASET_GRAPH
}
LINEAGE_FILTRATION_RUN1 = {
    'summary_dir': os.path.join(BASE_SUMMARY_DIR, 'run1'),
    'model_lineage': {
        'loss_function': 'SoftmaxCrossEntropyWithLogits',
        'train_dataset_path': None,
        'train_dataset_count': 731,
        'test_dataset_path': None,
        'test_dataset_count': 10240,
        'user_defined': {},
        'network': 'ResNet',
        'optimizer': 'Momentum',
        'learning_rate': 0.11999999731779099,
        'epoch': 14,
        'batch_size': 32,
        'device_num': 2,
        'loss': None,
        'model_size': 64,
        'metric': {
            'accuracy': 0.78
        },
        'dataset_mark': 2
    },
    'dataset_graph': DATASET_GRAPH
}
LINEAGE_FILTRATION_RUN2 = {
    'summary_dir': os.path.join(BASE_SUMMARY_DIR, 'run2'),
    'model_lineage': {
        'loss_function': None,
        'train_dataset_path': None,
        'train_dataset_count': None,
        'test_dataset_path': None,
        'test_dataset_count': 10240,
        'user_defined': {},
        'network': None,
        'optimizer': None,
        'learning_rate': None,
        'epoch': None,
        'batch_size': None,
        'device_num': None,
        'loss': None,
        'model_size': None,
        'metric': {
            'accuracy': 2.7800000000000002
        },
        'dataset_mark': 3
    },
    'dataset_graph': {}
}


@pytest.mark.usefixtures("create_summary_dir")
class TestModelApi(TestCase):
    """Test lineage information query interface."""

    @classmethod
    def setup_class(cls):
        """The initial process."""
        cls.dir_with_empty_lineage = os.path.join(
            BASE_SUMMARY_DIR, 'dir_with_empty_lineage'
        )
        os.makedirs(cls.dir_with_empty_lineage)
        ms_file = os.path.join(
            cls.dir_with_empty_lineage, 'empty.summary.1581499502.bms_MS'
        )
        lineage_file = ms_file + '_lineage'
        with open(ms_file, mode='w'):
            pass
        with open(lineage_file, mode='w'):
            pass

        cls.empty_dir = os.path.join(BASE_SUMMARY_DIR, 'empty_dir')
        os.makedirs(cls.empty_dir)

    def generate_lineage_object(self, lineage):
        lineage = dict(lineage)
        lineage_object = dict()
        lineage_object.update({'summary_dir': lineage.pop('summary_dir')})
        lineage_object.update({'dataset_graph': lineage.pop('dataset_graph')})
        lineage_object.update({'model_lineage': lineage})
        return lineage_object

    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_get_summary_lineage(self):
        """Test the interface of get_summary_lineage."""
        total_res = get_summary_lineage(SUMMARY_DIR)
        partial_res1 = get_summary_lineage(SUMMARY_DIR, ['hyper_parameters'])
        partial_res2 = get_summary_lineage(SUMMARY_DIR, ['metric', 'algorithm'])
        expect_total_res = LINEAGE_INFO_RUN1
        expect_partial_res1 = {
            'summary_dir': os.path.join(BASE_SUMMARY_DIR, 'run1'),
            'hyper_parameters': {
                'optimizer': 'Momentum',
                'learning_rate': 0.11999999731779099,
                'loss_function': 'SoftmaxCrossEntropyWithLogits',
                'epoch': 14,
                'parallel_mode': 'stand_alone',
                'device_num': 2,
                'batch_size': 32
            }
        }
        expect_partial_res2 = {
            'summary_dir': os.path.join(BASE_SUMMARY_DIR, 'run1'),
            'metric': {
                'accuracy': 0.78
            },
            'algorithm': {
                'network': 'ResNet'
            }
        }
        assert expect_total_res == total_res
        assert expect_partial_res1 == partial_res1
        assert expect_partial_res2 == partial_res2

        # the lineage summary file is empty
        result = get_summary_lineage(self.dir_with_empty_lineage)
        assert {} == result

        # keys is empty list
        expect_result = {
            'summary_dir': SUMMARY_DIR
        }
        result = get_summary_lineage(SUMMARY_DIR, [])
        assert expect_result == result

    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_get_summary_lineage_exception_1(self):
        """Test the interface of get_summary_lineage with exception."""
        # summary path does not exist
        self.assertRaisesRegex(
            LineageParamSummaryPathError,
            'The summary path does not exist or is not a dir.',
            get_summary_lineage,
            '/tmp/fake/dir'
        )

        # summary path is relative path
        self.assertRaisesRegex(
            LineageParamSummaryPathError,
            'The summary path is invalid.',
            get_summary_lineage,
            'tmp'
        )

        # the type of input param is invalid
        self.assertRaisesRegex(
            LineageParamSummaryPathError,
            'The summary path is invalid.',
            get_summary_lineage,
            ['/root/linage1', '/root/lineage2']
        )

        # summary path is empty str
        self.assertRaisesRegex(
            LineageParamSummaryPathError,
            'The summary path is invalid.',
            get_summary_lineage,
            '',
            keys=None
        )

        # summary path invalid
        self.assertRaisesRegex(
            LineageParamSummaryPathError,
            'The summary path is invalid.',
            get_summary_lineage,
            '\\',
            keys=None
        )

    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_get_summary_lineage_exception_2(self):
        """Test the interface of get_summary_lineage with exception."""
        # keys is invalid
        self.assertRaisesRegex(
            LineageParamValueError,
            'Keys must be in',
            get_summary_lineage,
            SUMMARY_DIR,
            ['metric', 'fake_name']
        )

        self.assertRaisesRegex(
            LineageParamTypeError,
            'Keys must be list.',
            get_summary_lineage,
            SUMMARY_DIR,
            0
        )

        self.assertRaisesRegex(
            LineageParamTypeError,
            'Keys must be list.',
            get_summary_lineage,
            SUMMARY_DIR,
            0.1
        )

        self.assertRaisesRegex(
            LineageParamTypeError,
            'Keys must be list.',
            get_summary_lineage,
            SUMMARY_DIR,
            True
        )

        self.assertRaisesRegex(
            LineageParamTypeError,
            'Element of keys must be str.',
            get_summary_lineage,
            SUMMARY_DIR,
            [1, 2, 3]
        )

        self.assertRaisesRegex(
            LineageParamTypeError,
            'Keys must be list.',
            get_summary_lineage,
            SUMMARY_DIR,
            (3, 4)
        )

        self.assertRaisesRegex(
            LineageParamTypeError,
            'Keys must be list.',
            get_summary_lineage,
            SUMMARY_DIR,
            {'a': 'b'}
        )

    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_filter_summary_lineage(self):
        """Test the interface of filter_summary_lineage."""
        expect_result = {
            'customized': event_data.CUSTOMIZED__0,
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
        res = filter_summary_lineage(BASE_SUMMARY_DIR, search_condition)
        expect_objects = expect_result.get('object')
        for idx, res_object in enumerate(res.get('object')):
            expect_objects[idx]['model_lineage']['dataset_mark'] = res_object['model_lineage'].get('dataset_mark')
        assert expect_result == res

        expect_result = {
            'object': [],
            'count': 0
        }
        res = filter_summary_lineage(self.dir_with_empty_lineage)
        expect_objects = expect_result.get('object')
        for idx, res_object in enumerate(res.get('object')):
            expect_objects[idx]['model_lineage']['dataset_mark'] = res_object['model_lineage'].get('dataset_mark')
        assert expect_result == res

    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_filter_summary_lineage_with_condition_1(self):
        """Test the interface of filter_summary_lineage with condition."""
        search_condition = {
            'summary_dir': {
                'in': [
                    SUMMARY_DIR,
                    SUMMARY_DIR_2
                ]
            },
            'metric/accuracy': {
                'lt': 3.0,
                'gt': 0.5
            },
            'sorted_name': 'metric/accuracy',
            'sorted_type': 'descending',
            'limit': 3,
            'offset': 0
        }
        expect_result = {
            'customized': event_data.CUSTOMIZED__0,
            'object': [
                LINEAGE_FILTRATION_RUN2,
                LINEAGE_FILTRATION_RUN1
            ],
            'count': 2
        }
        partial_res = filter_summary_lineage(BASE_SUMMARY_DIR, search_condition)
        expect_objects = expect_result.get('object')
        for idx, res_object in enumerate(partial_res.get('object')):
            expect_objects[idx]['model_lineage']['dataset_mark'] = res_object['model_lineage'].get('dataset_mark')
        assert expect_result == partial_res

    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_filter_summary_lineage_with_condition_2(self):
        """Test the interface of filter_summary_lineage with condition."""
        search_condition = {
            'summary_dir': {
                'in': [
                    './run1',
                    './run2'
                ]
            },
            'metric/accuracy': {
                'lt': 3.0,
                'gt': 0.5
            },
            'sorted_name': 'metric/accuracy',
            'sorted_type': 'descending',
            'limit': 3,
            'offset': 0
        }
        expect_result = {
            'customized': event_data.CUSTOMIZED__0,
            'object': [
                LINEAGE_FILTRATION_RUN2,
                LINEAGE_FILTRATION_RUN1
            ],
            'count': 2
        }
        partial_res = filter_summary_lineage(BASE_SUMMARY_DIR, search_condition)
        expect_objects = expect_result.get('object')
        for idx, res_object in enumerate(partial_res.get('object')):
            expect_objects[idx]['model_lineage']['dataset_mark'] = res_object['model_lineage'].get('dataset_mark')
        assert expect_result == partial_res

    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_filter_summary_lineage_with_condition_3(self):
        """Test the interface of filter_summary_lineage with condition."""
        search_condition1 = {
            'batch_size': {
                'ge': 30
            },
            'sorted_name': 'metric/accuracy',
        }
        expect_result = {
            'customized': event_data.CUSTOMIZED__0,
            'object': [
                LINEAGE_FILTRATION_EXCEPT_RUN,
                LINEAGE_FILTRATION_RUN1
            ],
            'count': 2
        }
        partial_res1 = filter_summary_lineage(BASE_SUMMARY_DIR, search_condition1)
        expect_objects = expect_result.get('object')
        for idx, res_object in enumerate(partial_res1.get('object')):
            expect_objects[idx]['model_lineage']['dataset_mark'] = res_object['model_lineage'].get('dataset_mark')
        assert expect_result == partial_res1

        search_condition2 = {
            'batch_size': {
                'lt': 30
            },
            'lineage_type': {
                'eq': 'model'
            },
        }
        expect_result = {
            'customized': {},
            'object': [],
            'count': 0
        }
        partial_res2 = filter_summary_lineage(BASE_SUMMARY_DIR, search_condition2)
        expect_objects = expect_result.get('object')
        for idx, res_object in enumerate(partial_res2.get('object')):
            expect_objects[idx]['model_lineage']['dataset_mark'] = res_object['model_lineage'].get('dataset_mark')
        assert expect_result == partial_res2

    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_filter_summary_lineage_with_lineage_type(self):
        """Test the interface of filter_summary_lineage with lineage_type."""
        summary_dir = os.path.join(BASE_SUMMARY_DIR, 'except_run')
        search_condition = {
            'summary_dir': {
                'in': [summary_dir]
            },
            'lineage_type': {
                'eq': 'dataset'
            },
        }
        expect_result = {
            'customized': {},
            'object': [
                {
                    'summary_dir': summary_dir,
                    'dataset_graph': DATASET_GRAPH
                }
            ],
            'count': 1
        }
        res = filter_summary_lineage(BASE_SUMMARY_DIR, search_condition)
        assert expect_result == res

    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_filter_summary_lineage_exception_1(self):
        """Test the abnormal execution of the filter_summary_lineage interface."""
        # summary base dir is relative path
        self.assertRaisesRegex(
            LineageParamSummaryPathError,
            'The summary path is invalid.',
            filter_summary_lineage,
            'relative_path'
        )

        # summary base dir does not exist
        self.assertRaisesRegex(
            LineageParamSummaryPathError,
            'The summary path does not exist or is not a dir.',
            filter_summary_lineage,
            '/path/does/not/exist'
        )

        # no summary log file under summary_base_dir
        self.assertRaisesRegex(
            LineageFileNotFoundError,
            'There is no summary log file under summary_base_dir.',
            filter_summary_lineage,
            self.empty_dir
        )

    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_filter_summary_lineage_exception_2(self):
        """Test the abnormal execution of the filter_summary_lineage interface."""
        # search_condition type error
        search_condition = {
            'summary_dir': 1.0
        }
        self.assertRaisesRegex(
            LineageSearchConditionParamError,
            'The search_condition element summary_dir should be dict.',
            filter_summary_lineage,
            BASE_SUMMARY_DIR,
            search_condition
        )

        # only sorted_type (no sorted_name)
        search_condition = {
            'sorted_type': 'descending'
        }
        self.assertRaisesRegex(
            LineageSearchConditionParamError,
            'The sorted_name have to exist when sorted_type exists.',
            filter_summary_lineage,
            BASE_SUMMARY_DIR,
            search_condition
        )

        # search condition is not dict or None
        search_condition = []
        self.assertRaisesRegex(
            LineageSearchConditionParamError,
            'Invalid search_condition type, it should be dict.',
            filter_summary_lineage,
            BASE_SUMMARY_DIR,
            search_condition
        )

        # the condition of limit is invalid
        search_condition = {
            'limit': True
        }
        self.assertRaisesRegex(
            LineageSearchConditionParamError,
            'The limit must be int.',
            filter_summary_lineage,
            BASE_SUMMARY_DIR,
            search_condition
        )

    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_filter_summary_lineage_exception_3(self):
        """Test the abnormal execution of the filter_summary_lineage interface."""
        # the condition of offset is invalid
        search_condition = {
            'offset': 1.0
        }
        self.assertRaisesRegex(
            LineageSearchConditionParamError,
            'The offset must be int.',
            filter_summary_lineage,
            BASE_SUMMARY_DIR,
            search_condition
        )

        # the search attribute not supported
        search_condition = {
            'dataset_graph': {
                'le': 1
            }
        }
        self.assertRaisesRegex(
            LineageSearchConditionParamError,
            'The search attribute not supported.',
            filter_summary_lineage,
            BASE_SUMMARY_DIR,
            search_condition
        )

    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_filter_summary_lineage_exception_4(self):
        """Test the abnormal execution of the filter_summary_lineage interface."""
        # the sorted_type not supported
        search_condition = {
            'sorted_name': 'summary_dir',
            'sorted_type': 'xxx'
        }
        self.assertRaisesRegex(
            LineageSearchConditionParamError,
            'The sorted_type must be ascending or descending',
            filter_summary_lineage,
            BASE_SUMMARY_DIR,
            search_condition
        )

        # the search condition not supported
        search_condition = {
            'batch_size': {
                'dd': 30
            }
        }
        self.assertRaisesRegex(
            LineageSearchConditionParamError,
            'The compare condition should be in',
            filter_summary_lineage,
            BASE_SUMMARY_DIR,
            search_condition
        )

        # the search condition type error
        search_condition = {
            'metric/accuracy': {
                'lt': 'xxx'
            }
        }
        self.assertRaisesRegex(
            LineageSearchConditionParamError,
            'The parameter metric/accuracy is invalid.',
            filter_summary_lineage,
            BASE_SUMMARY_DIR,
            search_condition
        )

    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_filter_summary_lineage_exception_5(self):
        """Test the abnormal execution of the filter_summary_lineage interface."""
        # the summary dir is invalid in search condition
        search_condition = {
            'summary_dir': {
                'in': [
                    'xxx'
                ]
            }
        }
        self.assertRaisesRegex(
            LineageParamSummaryPathError,
            'The summary path is invalid.',
            filter_summary_lineage,
            BASE_SUMMARY_DIR,
            search_condition
        )

    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_filter_summary_lineage_exception_6(self):
        """Test the abnormal execution of the filter_summary_lineage interface."""
        # gt > lt
        search_condition1 = {
            'metric/accuracy': {
                'gt': 1,
                'lt': 0.5
            }
        }
        expect_result = {
            'customized': {},
            'object': [],
            'count': 0
        }
        partial_res1 = filter_summary_lineage(BASE_SUMMARY_DIR, search_condition1)
        assert expect_result == partial_res1

        # the (offset + 1) * limit > count
        search_condition2 = {
            'loss': {
                'lt': 1
            },
            'limit': 1,
            'offset': 4
        }
        expect_result = {
            'customized': {},
            'object': [],
            'count': 1
        }
        partial_res2 = filter_summary_lineage(BASE_SUMMARY_DIR, search_condition2)
        assert expect_result == partial_res2

    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_filter_summary_lineage_exception_7(self):
        """Test the abnormal execution of the filter_summary_lineage interface."""
        condition_keys = ["summary_dir", "lineage_type"]
        for condition_key in condition_keys:
            # the condition type not supported in summary_dir and lineage_type
            search_condition = {
                condition_key: {
                    'lt': '/xxx'
                }
            }
            self.assertRaisesRegex(
                LineageSearchConditionParamError,
                f'Invalid operation of {condition_key}.',
                filter_summary_lineage,
                BASE_SUMMARY_DIR,
                search_condition
            )

            # more than one operation in summary_dir and lineage_type
            search_condition = {
                condition_key: {
                    'in': ['/xxx', '/yyy'],
                    'eq': '/zzz',
                }
            }
            self.assertRaisesRegex(
                LineageSearchConditionParamError,
                f'More than one operation of {condition_key}.',
                filter_summary_lineage,
                BASE_SUMMARY_DIR,
                search_condition
            )

    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_filter_summary_lineage_exception_8(self):
        invalid_lineage_types = ['xxx', None]
        for lineage_type in invalid_lineage_types:
            search_condition = {
                'lineage_type': {
                    'in': lineage_type
                }
            }
            self.assertRaisesRegex(
                LineageSearchConditionParamError,
                "The parameter lineage_type is invalid. It should be 'dataset' or 'model'.",
                filter_summary_lineage,
                BASE_SUMMARY_DIR,
                search_condition
            )

    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_filter_summary_lineage_exception_9(self):
        invalid_sorted_names = ['xxx', 'metric_', 1]
        for sorted_name in invalid_sorted_names:
            search_condition = {
                'sorted_name': sorted_name
            }
            self.assertRaisesRegex(
                LineageSearchConditionParamError,
                'The sorted_name must be in',
                filter_summary_lineage,
                BASE_SUMMARY_DIR,
                search_condition
            )

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
"""Lineage writer to record lineage to summary log."""
import json
import os
import random
import shutil

from ._summary_record import LineageSummary
from .base import Metadata

CHILDREN_0 = {
    'dataset_dir': '/home/anthony/MindData/tests/dataset/data/testMnistData',
    'op_module': 'minddata.dataengine.datasets',
    'num_shards': None,
    'num_parallel_workers': None,
    'shuffle': None,
    'op_type': 'MnistDataset',
    'shard_id': None,
    'num_samples': 100,
    'sampler': {
        'sampler_module': 'minddata.dataengine.samplers',
        'sampler_name': 'RandomSampler',
        'replacement': True,
        'num_samples': 100
    },
    'children': []
}

CHILDREN_1 = {
    'op_type': 'MapDataset',
    'op_module': 'minddata.dataengine.datasets',
    'num_parallel_workers': None,
    'input_columns': ['image'],
    'operations': [],
    'children': []
}

CHILDREN_2 = {
    'op_type': 'MapDataset',
    'op_module': 'minddata.dataengine.datasets',
    'num_parallel_workers': None,
    'output_columns': [None],
    'input_columns': ['label'],
    'operations': [{
        'tensor_op_module': 'minddata.transforms.c_transforms',
        'tensor_op_name': 'OneHot',
        'num_classes': 10
    }],
    'children': []
}

CHILDREN_3 = {
    'op_type': 'ShuffleDataset',
    'op_module': 'minddata.dataengine.datasets',
    'num_parallel_workers': None,
    'buffer_size': 10,
    'children': []
}


def _get_operations(rescale=0.003921, normalize_weight=0.48):
    """Get operations."""
    operation_0 = {
        'tensor_op_module': 'minddata.transforms.c_transforms',
        'tensor_op_name': 'RandomCrop',
        'weight': [32, 32, 4, 4, 4, 4],
        'padding_mode': "constant",
        'pad_if_needed': False,
        'fill_value': 0
    }
    operation_1 = {
        'tensor_op_module': 'minddata.transforms.c_transforms',
        'tensor_op_name': 'Rescale',
        'rescale': rescale,
        'shift': 0,
        'num_classes': 10
    }
    operation_2 = {
        'tensor_op_module': 'minddata.transforms.c_transforms',
        'tensor_op_name': 'Normalize',
        'weights': [normalize_weight]
    }

    return [operation_0, operation_1, operation_2]


def generate_graph(dataset_name='MnistDataset', batch_size=16, buffer_size=10,
                   rescale=0.003921, num_samples=100, normalize_weight=0.48):
    """Generate dataset graph."""
    children_0 = dict(CHILDREN_0)
    children_0['op_type'] = dataset_name
    children_0['num_samples'] = num_samples
    children_0['sampler']['num_samples'] = num_samples

    children_1 = dict(CHILDREN_1)
    children_1['operations'] = _get_operations(rescale, normalize_weight)
    children_1['children'] = [children_0]

    children_2 = dict(CHILDREN_2)
    children_2['buffer_size'] = buffer_size
    children_2['children'] = [children_1]

    children_3 = dict(CHILDREN_3)
    children_3['children'] = [children_2]

    dataset_graph = {
        'num_parallel_workers': None,
        'op_type': 'BatchDataset',
        'op_module': 'minddata.dataengine.datasets',
        'drop_remainder': True,
        'batch_size': batch_size,
        'children': [children_3]
    }
    return dataset_graph


def get_train_args():
    """Get default train args."""
    train_args = dict()
    train_args[Metadata.train_network] = "LeNet5"
    train_args[Metadata.loss] = 0.01
    train_args[Metadata.learning_rate] = 0.01
    train_args[Metadata.optimizer] = "Momentum"
    train_args[Metadata.loss_function] = "SoftmaxCrossEntropyWithLogits"
    train_args[Metadata.epoch] = 500
    train_args[Metadata.parallel_mode] = ""
    train_args[Metadata.device_num] = 1
    train_args[Metadata.batch_size] = 32
    train_args[Metadata.train_dataset_path] = "/home/data/train"
    train_args[Metadata.train_dataset_size] = 301234
    train_args[Metadata.model_path] = "/home/demo/demo_model.pkl"
    train_args[Metadata.model_size] = 100 * 1024 * 1024
    train_args["user_defined_info"] = {"Version_train": "v1"}
    train_args["dataset_graph"] = generate_graph()

    return train_args


def get_eval_args():
    """Get default eval args."""
    eval_args = dict()
    eval_args[Metadata.metrics] = json.dumps({"acc": 0.88})
    eval_args[Metadata.valid_dataset_path] = "/home/data/test"
    eval_args[Metadata.valid_dataset_size] = 5000
    eval_args["user_defined_info"] = {"Version_eval": "v1"}

    return eval_args


class LineageWriter:
    """Lineage writer."""
    def __init__(self, base_dir, summary_type=None):
        if summary_type is None:
            self._summary_type = ['train', 'eval']

        self.base_dir = base_dir
        self._init_summary_base_dir()

    def _init_summary_base_dir(self, clean_base_dir=False):
        """Init summary base dir."""
        if clean_base_dir and os.path.exists(self.base_dir):
            shutil.rmtree(self.base_dir)
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def _create_event(self, lineage_summary, args, mode='train'):
        """Create event."""
        if mode == 'train':
            lineage_summary.record_train_lineage(args)
            lineage_summary.record_user_defined_info(args["user_defined_info"])
            lineage_summary.record_dataset_graph(args["dataset_graph"])
        else:
            lineage_summary.record_evaluation_lineage(args)
            lineage_summary.record_user_defined_info(args["user_defined_info"])

    def _get_random_train_args(self):
        """Get random train args."""
        network = ['ResNet', 'LeNet5', 'AlexNet']
        optimizer = ['SGD', 'Adam', 'Momentum']
        loss_function = ["SoftmaxCrossEntropyWithLogits", "CrossEntropyLoss"]
        dataset = ['MindDataset', 'MnistDataset', 'Cifar10Datset']

        train_args = dict()
        train_args[Metadata.learning_rate] = random.uniform(0.001, 0.005)
        train_args[Metadata.loss] = random.uniform(0.001, 0.005)
        train_args[Metadata.epoch] = random.choice([100, 200, 300])
        train_args[Metadata.batch_size] = random.choice([16, 32, 64])
        train_args[Metadata.model_size] = random.randint(350, 450) * 1024 * 1024
        train_args[Metadata.train_network] = random.choice(network)
        train_args[Metadata.optimizer] = random.choice(optimizer)
        train_args[Metadata.device_num] = random.choice([1, 2, 4, 6, 8])
        train_args[Metadata.loss_function] = random.choice(loss_function)
        train_args[Metadata.train_dataset_size] = random.choice([56, 67, 78]) * 10000

        dataset_graph = generate_graph(
            dataset_name=random.choice(dataset),
            batch_size=random.choice([8, 16, 32, 64]),
            buffer_size=random.choice([10, 20, 30]),
            rescale=random.choice([0.003921, 0.005632, 0.0078, 0.005678]),
            num_samples=random.choice([100, 200, 300]),
            normalize_weight=random.choice([0.20, 0.50])  # random.uniform(0.2, 0.5)
        )
        train_args["dataset_graph"] = dataset_graph

        return train_args

    def _get_random_eval_args(self):
        """Get random eval args."""
        eval_args = dict()
        eval_args[Metadata.valid_dataset_size] = random.choice([13, 24, 28]) * 100
        eval_args[Metadata.metrics] = json.dumps({'Accuracy': random.uniform(0.85, 0.96)})

        return eval_args

    def create_summary_for_one_train(self, train_id, mode='train', random_mode=True, user_defined_params=None):
        """Create summary for one train."""
        summary_dir = os.path.join(self.base_dir, train_id)

        if not os.path.exists(summary_dir):
            os.makedirs(summary_dir)

        lineage_summary = LineageSummary(summary_dir)
        args = {}

        if mode == 'train':
            args = get_train_args()
            params = self._get_random_train_args() if random_mode else {}
            args.update(params)
        elif mode == 'eval':
            args = get_eval_args()
            params = self._get_random_eval_args() if random_mode else {}
            args.update(params)

        if user_defined_params is not None:
            args.update(user_defined_params)

        self._create_event(lineage_summary, args, mode)

    def create_summaries(self, train_id_prefix='train_', start_id=1, train_job_num=1, random_mode=True, params=None):
        """Create summaries for several trains."""
        if params is None:
            params = {}

        train_ids = [f'./{train_id_prefix}{i}' for i in range(start_id, start_id + train_job_num)]

        for train_id in train_ids:
            user_defined_params = params.get(train_id, {})
            for mode in self._summary_type:
                self.create_summary_for_one_train(train_id, mode, random_mode, user_defined_params.get(mode))

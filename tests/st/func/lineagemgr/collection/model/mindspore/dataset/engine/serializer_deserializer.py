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
"""Mock the MindSpore mindspore/dataset/engine/serializer_deserializer.py."""
import json

SERIALIZED_PIPELINE = {
    'op_type': 'BatchDataset',
    'op_module': 'minddata.dataengine.datasets',
    'num_parallel_workers': None,
    'drop_remainder': True,
    'batch_size': 10,
    'children': [
        {
            'op_type': 'MapDataset',
            'op_module': 'minddata.dataengine.datasets',
            'num_parallel_workers': None,
            'input_columns': [
                'label'
            ],
            'output_columns': [
                None
            ],
            'operations': [
                {
                    'tensor_op_module': 'minddata.transforms.c_transforms',
                    'tensor_op_name': 'OneHot',
                    'num_classes': 10
                }
            ],
            'children': [
                {
                    'op_type': 'MnistDataset',
                    'shard_id': None,
                    'num_shards': None,
                    'op_module': 'minddata.dataengine.datasets',
                    'dataset_dir': '/home/anthony/MindData/tests/dataset/data/testMnistData',
                    'num_parallel_workers': None,
                    'shuffle': None,
                    'num_samples': 100,
                    'sampler': {
                        'sampler_module': 'minddata.dataengine.samplers',
                        'sampler_name': 'RandomSampler',
                        'replacement': True,
                        'num_samples': 100
                    },
                    'children': []
                }
            ]
        }
    ]
}

def serialize(dataset, json_filepath=None):
    """Mock the MindSpore serialize method."""
    serialized_pipeline = SERIALIZED_PIPELINE
    if dataset is None:
        return json.dumps({'key': 'value'})
    if json_filepath:
        with open(json_filepath, 'w') as json_file:
            json.dump(serialized_pipeline, json_file, indent=2)
    return serialized_pipeline

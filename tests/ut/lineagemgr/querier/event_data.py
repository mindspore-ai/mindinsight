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
"""The event data in querier test."""
import json

from ....utils.mindspore.dataset.engine.serializer_deserializer import SERIALIZED_PIPELINE

EVENT_TRAIN_DICT_0 = {
    'wall_time': 1581499557.7017336,
    'train_lineage': {
        'hyper_parameters': {
            'optimizer': 'ApplyMomentum0',
            'learning_rate': 0.10000000149011612,
            'loss_function': '',
            'epoch': 1,
            'parallel_mode': 'stand_alone0',
            'device_num': 1,
            'batch_size': 31
        },
        'algorithm': {
            'network': 'TrainOneStepCell0',
            'loss': 2.3025848865509033
        },
        'train_dataset': {
            'train_dataset_path': '',
            'train_dataset_size': 31
        },
        'model': {
            'path': 'xxx0',
            'size': 400716930
        }
    }
}

EVENT_TRAIN_DICT_1 = {
    'wall_time': 1581499557.7017336,
    'train_lineage': {
        'hyper_parameters': {
            'optimizer': 'ApplyMomentum1',
            'learning_rate': 0.20000000298023224,
            'loss_function': 'loss_function1',
            'epoch': 1,
            'parallel_mode': 'stand_alone1',
            'device_num': 2,
            'batch_size': 35
        },
        'algorithm': {
            'network': 'TrainOneStepCell1',
            'loss': 2.4025847911834717
        },
        'train_dataset': {
            'train_dataset_path': '/path/to/train_dataset1',
            'train_dataset_size': 32
        },
        'model': {
            'path': 'xxx1',
            'size': 400716931
        }
    }
}

EVENT_TRAIN_DICT_2 = {
    'wall_time': 1581499557.7017336,
    'train_lineage': {
        'hyper_parameters': {
            'optimizer': 'ApplyMomentum2',
            'learning_rate': 0.30000001192092896,
            'loss_function': 'loss_function2',
            'epoch': 2,
            'parallel_mode': 'stand_alone2',
            'device_num': 3,
            'batch_size': 38
        },
        'algorithm': {
            'network': 'TrainOneStepCell2',
            'loss': 2.502584934234619
        },
        'train_dataset': {
            'train_dataset_path': '/path/to/train_dataset2',
            'train_dataset_size': 33
        },
        'model': {
            'path': 'xxx2',
            'size': 400716932
        }
    }
}

EVENT_TRAIN_DICT_3 = {
    'wall_time': 1581499557.7017336,
    'train_lineage': {
        'hyper_parameters': {
            'optimizer': 'ApplyMomentum3',
            'learning_rate': 0.4000000059604645,
            'loss_function': 'loss_function3',
            'epoch': 2,
            'parallel_mode': 'stand_alone3',
            'device_num': 3,
            'batch_size': 35
        },
        'algorithm': {
            'network': 'TrainOneStepCell3',
            'loss': 2.6025848388671875
        },
        'train_dataset': {
            'train_dataset_path': '/path/to/train_dataset3',
            'train_dataset_size': 34
        },
        'model': {
            'path': 'xxx3',
            'size': 400716933
        }
    }
}

EVENT_TRAIN_DICT_4 = {
    'wall_time': 1581499557.7017336,
    'train_lineage': {
        'hyper_parameters': {
            'optimizer': 'ApplyMomentum4',
            'learning_rate': 0.5,
            'loss_function': 'loss_function1',
            'epoch': 3,
            'parallel_mode': 'stand_alone4',
            'device_num': 1,
            'batch_size': 50
        },
        'algorithm': {
            'network': 'TrainOneStepCell4',
            'loss': 2.702584981918335
        },
        'train_dataset': {
            'train_dataset_path': '/path/to/train_dataset4',
            'train_dataset_size': 35
        },
        'model': {
            'path': 'xxx4',
            'size': 400716934
        }
    }
}

EVENT_TRAIN_DICT_5 = {
    'wall_time': 1581499557.7017336,
    'train_lineage': {
        'hyper_parameters': {
            'optimizer': 'ApplyMomentum5',
            'learning_rate': 0.5,
            'loss_function': 'loss_function1',
            'epoch': 3,
            'parallel_mode': 'stand_alone5',
            'device_num': 1,
            'batch_size': 51
        },
        'algorithm': {
            'network': 'TrainOneStepCell5',
            'loss': 2.702584981918335
        },
        'train_dataset': {
            'train_dataset_size': 35
        },
        'model': {
            'path': 'xxx4',
            'size': 400716934
        }
    }
}

EVENT_TRAIN_DICT_EXCEPTION = {
    'wall_time': 1581499557.7017336
}

METRIC_0 = {
    'accuracy': None,
    'mae': 2.00000001,
    'mse': 3.00000001
}

CUSTOMIZED__0 = {
    'metric/accuracy': {'label': 'metric/accuracy', 'required': True, 'type': 'float'},
}

CUSTOMIZED_0 = {
    **CUSTOMIZED__0,
    'metric/mae': {'label': 'metric/mae', 'required': True, 'type': 'float'},
    'metric/mse': {'label': 'metric/mse', 'required': True, 'type': 'float'}
}

CUSTOMIZED_1 = {
    'metric/accuracy': {'label': 'metric/accuracy', 'required': True, 'type': 'NoneType'},
    'metric/mae': {'label': 'metric/mae', 'required': True, 'type': 'float'},
    'metric/mse': {'label': 'metric/mse', 'required': True, 'type': 'float'}
}

CUSTOMIZED_2 = {
    'metric/accuracy': {'label': 'metric/accuracy', 'required': True, 'type': 'mixed'},
    'metric/mae': {'label': 'metric/mae', 'required': True, 'type': 'float'},
    'metric/mse': {'label': 'metric/mse', 'required': True, 'type': 'float'}
}

METRIC_1 = {
    'accuracy': 1.0000002,
    'mae': 2.00000002,
    'mse': 3.00000002
}

METRIC_2 = {
    'accuracy': 1.0000003,
    'mae': 2.00000003,
    'mse': 3.00000003
}

METRIC_3 = {
    'accuracy': 1.0000004,
    'mae': 2.00000004,
    'mse': 3.00000004
}

METRIC_4 = {
    'accuracy': 1.0000005,
    'mae': 2.00000005,
    'mse': 3.00000005
}

METRIC_5 = {
    'accuracy': 1.0000006,
    'mae': 2.00000006,
    'mse': 3.00000006
}

EVENT_EVAL_DICT_0 = {
    'wall_time': 1581499557.7017336,
    'evaluation_lineage': {
        'metric': json.dumps(METRIC_0),
        'valid_dataset': {
            'valid_dataset_path': '',
            'valid_dataset_size': 400716931
        }
    }
}

EVENT_EVAL_DICT_1 = {
    'wall_time': 1581499557.7017336,
    'evaluation_lineage': {
        'metric': json.dumps(METRIC_1),
        'valid_dataset': {
            'valid_dataset_path': '/path/to/valid_dataset1',
            'valid_dataset_size': 400716931
        }
    }
}

EVENT_EVAL_DICT_2 = {
    'wall_time': 1581499557.7017336,
    'evaluation_lineage': {
        'metric': json.dumps(METRIC_2),
        'valid_dataset': {
            'valid_dataset_path': '/path/to/valid_dataset2',
            'valid_dataset_size': 400716931
        }
    }
}

EVENT_EVAL_DICT_3 = {
    'wall_time': 1581499557.7017336,
    'evaluation_lineage': {
        'metric': json.dumps(METRIC_3),
        'valid_dataset': {
            'valid_dataset_path': '/path/to/valid_dataset3',
            'valid_dataset_size': 400716931
        }
    }
}

EVENT_EVAL_DICT_4 = {
    'wall_time': 1581499557.7017336,
    'evaluation_lineage': {
        'metric': json.dumps(METRIC_4),
        'valid_dataset': {
            'valid_dataset_path': '/path/to/valid_dataset4',
            'valid_dataset_size': 400716931
        }
    }
}

EVENT_EVAL_DICT_5 = {
    'wall_time': 1581499557.7017336,
    'evaluation_lineage': {
        'metric': json.dumps(METRIC_5),
        'valid_dataset': {
            'valid_dataset_path': '/path/to/valid_dataset5',
            'valid_dataset_size': 400716931
        }
    }
}

EVENT_EVAL_DICT_EXCEPTION = {
    'wall_time': 1581499557.7017336
}

EVENT_DATASET_DICT_0 = {
    'wall_time': 1583317727.4949381,
    'dataset_graph': {
        'children': [
            {
                'children': [
                    {
                        'parameter': {
                            'mapStr': {
                                'op_type': 'MnistDataset',
                                'shard_id': 'None',
                                'num_shards': 'None',
                                'op_module': 'minddata.dataengine.datasets',
                                'dataset_dir': '/home/anthony/MindData/tests/dataset/data/testMnistData',
                                'num_parallel_workers': 'None',
                                'shuffle': 'None'
                            },
                            'mapInt': {
                                'num_samples': 100
                            }
                        },
                        'sampler': {
                            'operationParam': {
                                'mapStr': {
                                    'sampler_name': 'RandomSampler',
                                    'sampler_module': 'minddata.dataengine.samplers'
                                },
                                'mapBool': {
                                    'replacement': True
                                },
                                'mapInt': {
                                    'num_samples': 100
                                }
                            }
                        }
                    }
                ],
                'parameter': {
                    'mapStr': {
                        'op_module': 'minddata.dataengine.datasets',
                        'op_type': 'MapDataset',
                        'num_parallel_workers': 'None'
                    },
                    'mapStrList': {
                        'output_columns': {
                            'strValue': [
                                ''
                            ]
                        },
                        'input_columns': {
                            'strValue': [
                                'label'
                            ]
                        }
                    }
                },
                'operations': [
                    {
                        'operationParam': {
                            'mapStr': {
                                'tensor_op_module': 'minddata.transforms.c_transforms',
                                'tensor_op_name': 'OneHot'
                            },
                            'mapInt': {
                                'num_classes': 10
                            }
                        }
                    }
                ]
            }
        ],
        'parameter': {
            'mapStr': {
                'op_module': 'minddata.dataengine.datasets',
                'op_type': 'BatchDataset',
                'num_parallel_workers': 'None'
            },
            'mapBool': {
                'drop_remainder': True
            },
            'mapInt': {
                'batch_size': 10
            }
        }
    }
}

DATASET_DICT_0 = SERIALIZED_PIPELINE

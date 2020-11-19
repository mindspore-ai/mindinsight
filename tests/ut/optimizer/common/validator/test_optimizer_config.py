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
"""Test optimizer config schema."""
from copy import deepcopy

import pytest

from mindinsight.optimizer.common.validator.optimizer_config import OptimizerConfig
from mindinsight.optimizer.common.enums import TargetGroup, HyperParamSource

_BASE_DATA = {
    'command': 'python ./test.py',
    'summary_base_dir': './demo_lineage_r0.3',
    'tuner': {
        'name': 'gp',
        'args': {
            'method': 'ucb'
        }
    },
    'target': {
        'group': 'metric',
        'name': 'Accuracy',
        'goal': 'maximize'
    },
    'parameters': {
        'learning_rate': {
            'bounds': [0.0001, 0.001],
            'type': 'float'
        },
        'batch_size': {
            'choice': [32, 64, 128, 256],
            'type': 'int'
        },
        'decay_step': {
            'choice': [20],
            'type': 'int'
        }
    }
}


class TestOptimizerConfig:
    """Test the method of validate_search_model_condition."""
    _config_dict = dict(_BASE_DATA)

    def test_config_dict_with_wrong_type(self):
        """Test config dict with wrong type."""
        config_dict = deepcopy(self._config_dict)
        init_list = ['a']
        init_str = 'a'

        config_dict['command'] = init_list
        config_dict['summary_base_dir'] = init_list
        config_dict['target']['name'] = init_list
        config_dict['target']['goal'] = init_list
        config_dict['parameters']['learning_rate']['bounds'] = init_str
        config_dict['parameters']['learning_rate']['choice'] = init_str
        config_dict['parameters']['learning_rate']['type'] = init_list
        expected_err = {
            'command': ['Value should be a string.'],
            'parameters': {
                'learning_rate': {
                    'type': "The value(s) should be float number, please config its type as 'float'."
                }
            },
            'summary_base_dir': ['Value should be a string.'],
            'target': {
                'goal': ['Value should be a string.'],
                'name': ['Value should be a string.']
            }
        }
        err = OptimizerConfig().validate(config_dict)
        assert expected_err == err

    def test_config_dict_with_wrong_value(self):
        """Test config dict with wrong value."""
        config_dict = deepcopy(self._config_dict)
        init_list = ['a']
        init_str = 'a'

        config_dict['target']['group'] = init_str
        config_dict['target']['goal'] = init_str
        config_dict['tuner']['name'] = init_str
        config_dict['parameters']['learning_rate']['bounds'] = init_list
        config_dict['parameters']['learning_rate']['choice'] = init_list
        config_dict['parameters']['learning_rate']['type'] = init_str
        expected_err = {
            'parameters': {
                'learning_rate': {
                    'type': "The value(s) should be float number, please config its type as 'float'."
                }
            },
            'target': {
                'goal': ["Value should be in ['maximize', 'minimize']. Current value is 'a'."],
                'group': ["Value should be in ['system_defined', 'metric']. Current value is 'a'."]
            },
            'tuner': {
                'name': ['Must be one of: gp.']
            }
        }
        err = OptimizerConfig().validate(config_dict)
        assert expected_err == err

    def test_target_combination(self):
        """Test target combination."""
        config_dict = deepcopy(self._config_dict)

        config_dict['target']['group'] = TargetGroup.SYSTEM_DEFINED.value
        config_dict['target']['name'] = 'a'
        expected_err = {
            'target': {
                'group': "This target is not system defined. Current group is 'system_defined'."
            }
        }
        err = OptimizerConfig().validate(config_dict)
        assert expected_err == err

    def test_parameters_combination1(self):
        """Test parameters combination."""
        config_dict = deepcopy(self._config_dict)

        config_dict['parameters']['decay_step']['source'] = HyperParamSource.SYSTEM_DEFINED.value
        expected_err = {
            'parameters': {
                'decay_step': {
                    'source': "This param is not system defined. Current source is 'system_defined'."
                }
            }
        }
        err = OptimizerConfig().validate(config_dict)
        assert expected_err == err

    def test_parameters_combination2(self):
        """Test parameters combination."""
        config_dict = deepcopy(self._config_dict)

        config_dict['parameters']['decay_step']['bounds'] = [1, 40]
        expected_err = {
            'parameters': {
                'decay_step': {
                    '_schema': ["Only one of ['bounds', 'choice'] should be specified."]
                }
            }
        }
        err = OptimizerConfig().validate(config_dict)
        assert expected_err == err

    def test_learning_rate(self):
        """Test learning rate with wrong value."""
        config_dict = deepcopy(self._config_dict)

        config_dict['parameters']['learning_rate']['bounds'] = [-0.1, 1]
        expected_err = {
            'parameters': {
                'learning_rate': {
                    'bounds': 'The value(s) should be positive number.'
                }
            }
        }
        err = OptimizerConfig().validate(config_dict)
        assert expected_err == err

        config_dict['parameters']['learning_rate']['bounds'] = [0.1, 1.1]
        expected_err = {
            'parameters': {
                'learning_rate': {
                    'bounds': 'The upper bound should be less than and equal to 1.'
                }
            }
        }
        err = OptimizerConfig().validate(config_dict)
        assert expected_err == err

    def test_learning_rate_type(self):
        """Test learning rate with wrong type."""
        config_dict = deepcopy(self._config_dict)
        config_dict['parameters']['learning_rate']['type'] = 'int'
        expected_err = {
            'parameters': {
                'learning_rate': {
                    'type': "The value(s) should be float number, please config its type as 'float'."
                }
            }
        }
        err = OptimizerConfig().validate(config_dict)
        assert expected_err == err

    @pytest.mark.parametrize("param_name", ['batch_size', 'epoch'])
    def test_batch_size_and_epoch(self, param_name):
        """Test parameters combination."""
        config_dict = deepcopy(self._config_dict)
        config_dict['parameters'] = {
            param_name: {'choice': [-0.1, 1]}
        }
        expected_err = {
            'parameters': {
                param_name: {
                    'choice': 'The value(s) should be positive number.'
                }
            }
        }
        err = OptimizerConfig().validate(config_dict)
        assert expected_err == err

        config_dict['parameters'][param_name] = {'choice': [0.1, 0.2]}
        expected_err = {
            'parameters': {
                param_name: {
                    'choice': 'The value(s) should be integer.'
                }
            }
        }
        err = OptimizerConfig().validate(config_dict)
        assert expected_err == err

        config_dict['parameters'] = {}
        config_dict['parameters'][param_name] = {
            'bounds': [1, 22],
            'type': 'float'
        }
        expected_err = {
            'parameters': {
                param_name: {
                    'type': "The value(s) should be integer, please config its type as 'int'."
                }
            }
        }
        err = OptimizerConfig().validate(config_dict)
        assert expected_err == err

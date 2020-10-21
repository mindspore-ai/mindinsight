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
"""Test the model module."""
import numpy as np
import pandas as pd
import pytest

from mindinsight.optimizer.common.exceptions import SamplesNotEnoughError, CorrelationNanError
from mindinsight.optimizer.utils.importances import calc_hyper_param_importance
from mindinsight.optimizer.utils.utils import is_simple_numpy_number, calc_histogram


def test_is_simple_numpy_number():
    assert is_simple_numpy_number(np.int8)
    assert is_simple_numpy_number(np.int16)
    assert is_simple_numpy_number(np.float)
    assert not is_simple_numpy_number(str)


def test_calc_histogram():
    """Test calc_histogram function"""
    data = np.array([2, 2, 3, 4, 5])
    output = calc_histogram(data)
    assert output[0][1] == pytest.approx(0.6, 1e-6)
    assert output[1][1] == pytest.approx(0.6, 1e-6)
    assert output[0][2] == pytest.approx(2.0, 1e-6)


def test_calc_hyper_param_importance_exception_1():
    """Test calc_hyper_param_importance function when number of samples is less or equal than 2"""
    flattened_lineage = {'epoch': [10, 10], 'accuracy': [32, 32]}
    with pytest.raises(SamplesNotEnoughError) as info:
        calc_hyper_param_importance(pd.DataFrame(flattened_lineage), 'epoch', 'accuracy')
    assert "Number of samples is less or equal than 2." in str(info.value)


def test_calc_hyper_param_importance_exception_2():
    """Test calc_hyper_param_importance function when correlation equals to NaN"""
    flattened_lineage = {'epoch': [10, 10, 10], 'accuracy': [0.6432, 0.6281, 0.6692]}
    with pytest.raises(CorrelationNanError) as info:
        calc_hyper_param_importance(pd.DataFrame(flattened_lineage), 'epoch', 'accuracy')
    assert "Correlation is nan!" in str(info.value)


def test_calc_hyper_param_importance():
    """Test calc_hyper_param_importance function"""
    flattened_lineage = {'epoch': [10, 20, 30], 'accuracy': [30, 40, 50]}
    result = calc_hyper_param_importance(pd.DataFrame(flattened_lineage), 'epoch', 'accuracy')
    assert result == pytest.approx(1.0, 1e-6)

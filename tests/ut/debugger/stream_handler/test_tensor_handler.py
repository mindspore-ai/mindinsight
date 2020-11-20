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
"""Test tensor_handler.py"""
from unittest import mock
import pytest

from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.stream_handler.tensor_handler import TensorHandler


class TestTensorHandler:
    """Test TensorHandler."""

    def setup_method(self):
        """Setup method for each test case."""
        self.tensor_handler = TensorHandler()

    @mock.patch.object(TensorHandler, '_get_tensor')
    @mock.patch.object(log, "error")
    def test_get(self, mock_get_tensor, mock_error):
        """Test get full tensor value."""
        mock_get_tensor.return_value = None
        mock_error.return_value = None
        with pytest.raises(DebuggerParamValueError) as ex:
            self.tensor_handler.get({})
        assert "No tensor named {}".format(None) in str(ex.value)

    def test_get_tensor_value_by_name_none(self):
        """Test get_tensor_value_by_name."""
        res = self.tensor_handler.get_valid_tensor_by_name('tensor_name', True)
        assert res is None

    @mock.patch.object(log, "error")
    @pytest.mark.parametrize("tensor_name", "name")
    def test_get_tensors_diff_error(self, mock_error, tensor_name):
        """Test get_tensors_diff."""
        mock_error.return_value = None
        with pytest.raises(DebuggerParamValueError) as ex:
            self.tensor_handler.get_tensors_diff(tensor_name, {1, 1})
        assert f"Get current step and previous step for this tensor name {tensor_name} failed." in str(ex.value)

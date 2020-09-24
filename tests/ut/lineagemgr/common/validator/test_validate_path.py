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
"""Test the validate module."""
import os
from unittest import mock
from marshmallow import ValidationError
import pytest

from mindinsight.lineagemgr.common.validator.validate_path import safe_normalize_path, validate_and_normalize_path


class TestValidatePath:
    """Test the method of validate_path."""
    @pytest.mark.parametrize('path, check, allow',
                             [('', False, False), ('../', False, False), ('invalid', True, False)])
    def test_validate_and_normalize_path(self, path, check, allow):
        """Test the method of validate_path with ValidationError."""
        key = 'path'
        path = ''
        with pytest.raises(ValidationError) as info:
            validate_and_normalize_path(path, key, check, allow)
        assert "The path is invalid!" in str(info.value)

        path = '/a/b'
        assert validate_and_normalize_path(path, key, False, True) == os.path.realpath(path)

    @mock.patch('mindinsight.lineagemgr.common.validator.validate_path.validate_and_normalize_path')
    @pytest.mark.parametrize('prefix', [None, ['/']])
    def test_safe_normalize_path(self, mock_validate_and_normalize_path, prefix):
        """Test the method of safe_normalize_path."""
        key = 'path'
        path = '/a/b'
        mock_validate_and_normalize_path.return_value = os.path.realpath(path)

        assert safe_normalize_path(path, key, prefix, False, True) == os.path.realpath(path)

    def test_safe_normalize_path_exception(self):
        """Test the method of safe_normalize_path with invalid prefix"""
        key = 'path'
        path = '/a/b'
        prefix = ['invalid']
        with pytest.raises(ValidationError) as info:
            safe_normalize_path(path, key, prefix, False, True)
        assert "The path is invalid!" in str(info.value)

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
"""Test file_handler.py."""
from unittest import mock, TestCase

from mindinsight.lineagemgr.summary.file_handler import FileHandler


class TestFileHandler(TestCase):
    """Test file_handler.py"""

    @mock.patch("os.path.getsize", return_value=12)
    @mock.patch("builtins.open")
    def setUp(self, *args):
        args[0].return_value.__enter__.return_value.read.return_value = b'\x0a\x0b\x0c' * 4
        self.file_handler = FileHandler("fake_path.log")

    def test_seek(self):
        """Test seek method."""
        self.file_handler.seek(5)
        cur_pos = self.file_handler.tell()
        self.assertEqual(cur_pos, 5)

    def test_read(self):
        """Test read method."""
        res = self.file_handler.read(3)
        self.assertEqual(res, b'\x0a\x0b\x0c')

    def test_read_with_pos(self):
        """Test read method with specific position."""
        res = self.file_handler.read(3, 1)
        self.assertEqual(res, b'\x0b\x0c\x0a')

    def test_size(self):
        """Test size property."""
        size = self.file_handler.size
        self.assertEqual(size, 12)

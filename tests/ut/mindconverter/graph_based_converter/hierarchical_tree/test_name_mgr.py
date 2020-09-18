# Copyright 2020 Huawei Technologies Co., Ltd.All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Test name manager module."""
from unittest import TestCase
from mindinsight.mindconverter.graph_based_converter.hierarchical_tree.name_mgr import NameMgr, GlobalVarNameMgr, \
    global_op_namespace


class TestNameMgr(TestCase):
    """Tester of name mgr."""

    def test_global_get_name_not_in_record(self):
        """Test global name mgr."""
        name = GlobalVarNameMgr().get_name("onnx::Conv")
        assert isinstance(name, str)

    def test_global_get_name_in_record(self):
        """Test global name mgr."""
        global_op_namespace['abc'] = 0
        name_mgr = GlobalVarNameMgr()
        name = name_mgr.get_name('abc')
        assert isinstance(name, str)

    def test_get_name_not_in_record(self):
        """Test get_name old_name not in self.record"""
        name_mgr = NameMgr()
        name = name_mgr.get_name('abc')
        assert isinstance(name, str)

    def test_get_name_in_record(self):
        """Test get_name old_name in self.record"""
        name_mgr = NameMgr()
        name_mgr.record = {'abc': ['123']}
        name = name_mgr.get_name('abc')
        assert isinstance(name, str)

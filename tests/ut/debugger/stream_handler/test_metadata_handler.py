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
"""Test metadata_handler.py."""
from mindinsight.debugger.common.utils import ServerStatus
from mindinsight.debugger.stream_handler.metadata_handler import MetadataHandler
from mindinsight.debugger.proto.debug_grpc_pb2 import Metadata

class TestMetadataHandler:
    """test class for MetadataHandler"""
    def setup_method(self):
        """set up function, init a MetaDataHandler for use"""
        self.metadata_handler = MetadataHandler()

    def test_device_name(self):
        """test device_name property"""
        res = self.metadata_handler.device_name
        assert res == ""

    def test_step(self):
        """test step property."""
        res = self.metadata_handler.step
        assert res == 0

    def test_node_name(self):
        """test property of current node name"""
        res = self.metadata_handler.node_name
        assert res == ""

    def test_node_name_setter(self):
        """test set property of node name"""
        self.metadata_handler.node_name = "node_name"
        res = self.metadata_handler.node_name
        assert res == "node_name"

    def test_full_name(self):
        """test full_name property"""
        res = self.metadata_handler.full_name
        assert res == ""

    def test_backend(self):
        """test backend property"""
        res = self.metadata_handler.backend
        assert res == ""

    def test_state(self):
        """test state property"""
        res = self.metadata_handler.state
        assert res == ServerStatus.PENDING.value

    def test_state_setter(self):
        """test set the property of state"""
        self.metadata_handler.state = ServerStatus.RUNNING
        res = self.metadata_handler.state
        assert res == ServerStatus.RUNNING.value

    def test_client_ip(self):
        """test client_ip property"""
        res = self.metadata_handler.client_ip
        assert res == ""

    def test_put(self):
        """test put value into metadata cache"""
        value = Metadata()
        self.metadata_handler.put(value)
        res_device_name = self.metadata_handler.device_name
        assert res_device_name == value.device_name.split(':')[0]
        res_step = self.metadata_handler.step
        assert res_step == value.cur_step
        res_cur_node = self.metadata_handler.full_name
        assert res_cur_node == value.cur_node
        res_backend = self.metadata_handler.backend
        expect_backend = value.backend if value.backend else "Ascend"
        assert res_backend == expect_backend

    def test_get(self):
        """test get updated value"""
        res = self.metadata_handler.get('state')
        assert res == {'metadata': {'state': ServerStatus.PENDING.value}}

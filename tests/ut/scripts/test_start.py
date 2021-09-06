# Copyright 2021 Huawei Technologies Co., Ltd
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
"""
Function:
    Test start script.
Usage:
    pytest tests/ut/script/test_start.py
"""
import pytest

from mindinsight.conf import settings
from mindinsight.scripts.start import Command
from mindinsight.utils.exceptions import SettingValueError


class TestStartScript:
    """Test start script."""

    @pytest.mark.parametrize('value', [6143, 2147483648, 2.1, True, False, 'str'])
    def test_offline_debugger_mem_limit_value(self, value):
        """Test offline debugger mem limit value."""
        cmd = Command()
        settings.OFFLINE_DEBUGGER_MEM_LIMIT = value
        with pytest.raises(SettingValueError) as exc:
            cmd.check_offline_debugger_setting()
        expected_msg = f"[SettingValueError] code: 5054000D, msg: Offline debugger memory limit " \
                       f"should be integer ranging from 6144 to 2147483647 MB, but got %s. Please check the " \
                       f"environment variable MINDINSIGHT_OFFLINE_DEBUGGER_MEM_LIMIT" % value
        assert expected_msg == str(exc.value)
        settings.OFFLINE_DEBUGGER_MEM_LIMIT = 16 * 1024

    @pytest.mark.parametrize('value', [0, 3, 1.1, True, False, 'str'])
    def test_max_offline_debugger_session_num_value(self, value):
        """Test offline debugger mem limit type."""
        cmd = Command()
        settings.MAX_OFFLINE_DEBUGGER_SESSION_NUM = value
        with pytest.raises(SettingValueError) as exc:
            cmd.check_offline_debugger_setting()
        expected_msg = f"[SettingValueError] code: 5054000D, msg: Max offline debugger session number " \
                       f"should be integer ranging from 1 to 2, but got %s. Please check the environment " \
                       f"variable MINDINSIGHT_MAX_OFFLINE_DEBUGGER_SESSION_NUM" % value
        assert expected_msg == str(exc.value)
        settings.MAX_OFFLINE_DEBUGGER_SESSION_NUM = 2

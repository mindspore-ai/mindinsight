# Copyright 2020-2021 Huawei Technologies Co., Ltd
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
"""Modelarts exceptions module."""
from mindinsight.utils.exceptions import MindInsightException
from mindinsight.utils.constant import GeneralErrors


class PortReuseException(MindInsightException):
    """Port reuse exception."""
    def __init__(self, error_detail):
        error_msg = '{}'.format(error_detail)
        super(PortReuseException, self).__init__(
            GeneralErrors.PORT_NOT_AVAILABLE_ERROR,
            error_msg,
            http_code=400)

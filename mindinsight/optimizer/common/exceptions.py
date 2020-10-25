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
"""Define custom exception."""

from mindinsight.utils.constant import OptimizerErrors
from mindinsight.utils.exceptions import MindInsightException


class SamplesNotEnoughError(MindInsightException):
    """Param importance calculated error."""
    def __init__(self, error_msg="Param importance calculated error."):
        super(SamplesNotEnoughError, self).__init__(OptimizerErrors.SAMPLES_NOT_ENOUGH,
                                                    error_msg,
                                                    http_code=400)


class CorrelationNanError(MindInsightException):
    """Param importance calculated error."""
    def __init__(self, error_msg="Param importance calculated error."):
        super(CorrelationNanError, self).__init__(OptimizerErrors.CORRELATION_NAN,
                                                  error_msg,
                                                  http_code=400)


class HyperConfigError(MindInsightException):
    """Hyper config error."""
    def __init__(self, error_msg="Hyper config is not correct."):
        super(HyperConfigError, self).__init__(OptimizerErrors.HYPER_CONFIG_ERROR,
                                               error_msg,
                                               http_code=400)


class OptimizerTerminateError(MindInsightException):
    """Hyper config error."""
    def __init__(self, error_msg="Auto tuning has been terminated."):
        super(OptimizerTerminateError, self).__init__(OptimizerErrors.OPTIMIZER_TERMINATE,
                                                      error_msg,
                                                      http_code=400)


class ConfigParamError(MindInsightException):
    """Hyper config error."""
    def __init__(self, error_msg="Invalid parameter."):
        super(ConfigParamError, self).__init__(OptimizerErrors.OPTIMIZER_TERMINATE,
                                               error_msg,
                                               http_code=400)


class HyperConfigEnvError(MindInsightException):
    """Hyper config error."""
    def __init__(self, error_msg="Hyper config is not correct."):
        super(HyperConfigEnvError, self).__init__(OptimizerErrors.HYPER_CONFIG_ENV_ERROR,
                                                  error_msg,
                                                  http_code=400)

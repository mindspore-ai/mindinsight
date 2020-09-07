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
"""Utils for calculate importance."""
import numpy as np

from mindinsight.optimizer.common.exceptions import SamplesNotEnoughError, CorrelationNanError
from mindinsight.optimizer.common.log import logger


def calc_hyper_param_importance(df, hyper_param, target):
    """Calc hyper param importance relative to given target."""
    logger.debug("Calculating importance for hyper_param %s, target is %s.", hyper_param, target)

    new_df = df[[hyper_param, target]]
    no_missing_value_df = new_df.dropna()

    # Can not calc pearson correlation coefficient when number of samples is less or equal than 2
    if len(no_missing_value_df) <= 2:
        raise SamplesNotEnoughError("Number of samples is less or equal than 2.")

    correlation = no_missing_value_df[target].corr(no_missing_value_df[hyper_param])
    if np.isnan(correlation):
        logger.warning("Correlation is nan!")
        raise CorrelationNanError("Correlation is nan!")
    return abs(correlation)

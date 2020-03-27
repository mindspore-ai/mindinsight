# Copyright 2019 Huawei Technologies Co., Ltd
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
Lineagemgr Module Introduction.

This module provides Python APIs to collect and query the lineage of models.
Users can add the TrainLineage/EvalLineage callback to the MindSpore train/eval callback list to
collect the key parameters and results, such as, the name of the network and optimizer, the
evaluation metric and results.
The APIs can be used to get the lineage information of the models. For example,
what hyperparameter is used in the model training, which model has the highest
accuracy among all the versions, etc.
"""
from mindinsight.lineagemgr.api.model import get_summary_lineage, filter_summary_lineage
from mindinsight.lineagemgr.common.log import logger
try:
    from mindinsight.lineagemgr.collection.model.model_lineage import TrainLineage, EvalLineage
except (ModuleNotFoundError, NameError, ImportError):
    logger.warning('Not found MindSpore!')

__all__ = ["TrainLineage", "EvalLineage", "get_summary_lineage", "filter_summary_lineage"]

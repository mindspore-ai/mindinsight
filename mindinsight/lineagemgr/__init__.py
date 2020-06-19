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

This module provides Python APIs to query the lineage of models.
The APIs can be used to get the lineage information of the models. For example,
what hyperparameter is used in the model training, which model has the highest
accuracy among all the versions, etc.
"""
from mindinsight.lineagemgr.api.model import get_summary_lineage, filter_summary_lineage


__all__ = ["get_summary_lineage", "filter_summary_lineage"]

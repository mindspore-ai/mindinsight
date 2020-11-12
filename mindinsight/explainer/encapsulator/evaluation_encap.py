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
"""Explainer evaluation encapsulator."""

import copy

from mindinsight.explainer.encapsulator.explain_data_encap import ExplainDataEncap
from mindinsight.datavisual.common.exceptions import TrainJobNotExistError


class EvaluationEncap(ExplainDataEncap):
    """Explainer evaluation encapsulator."""

    def query_explainer_scores(self, train_id):
        """Query evaluation scores."""
        job = self.job_manager.get_job(train_id)
        if job is None:
            raise TrainJobNotExistError(train_id)
        return copy.deepcopy(job.explainer_scores)

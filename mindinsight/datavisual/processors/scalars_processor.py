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
"""Scalar Processor APIs."""
from mindinsight.datavisual.common.validation import Validation
from mindinsight.datavisual.processors.base_processor import BaseProcessor


class ScalarsProcessor(BaseProcessor):
    """Scalar Processor."""

    def get_metadata_list(self, train_id, tag):
        """
        Builds a JSON-serializable object with information about scalars.

        Args:
            train_id (str): The ID of the events data.
            tag (str): The name of the tag the scalars all belonging to.

        Returns:
            list[dict], a list of dictionaries containing the `wall_time`, `step`, `value` for each scalar.
        """
        Validation.check_param_empty(train_id=train_id, tag=tag)
        job_response = []
        tensors = self._data_manager.list_tensors(train_id, tag)

        for tensor in tensors:
            job_response.append({
                'wall_time': tensor.wall_time,
                'step': tensor.step,
                'value': tensor.value})
        return dict(metadatas=job_response)

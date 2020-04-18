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
"""Histogram Processor APIs."""
from mindinsight.utils.exceptions import ParamValueError
from mindinsight.datavisual.common.log import logger
from mindinsight.datavisual.common.validation import Validation
from mindinsight.datavisual.common.exceptions import HistogramNotExistError
from mindinsight.datavisual.processors.base_processor import BaseProcessor


class HistogramProcessor(BaseProcessor):
    """Histogram Processor."""
    def get_histograms(self, train_id, tag):
        """
        Builds a JSON-serializable object with information about histogram data.

        Args:
            train_id (str): The ID of the events data.
            tag (str): The name of the tag the histogram data all belong to.

        Returns:
            dict, a dict including the `train_id`, `tag`, and `histograms'.
                    {
                        "train_id": ****,
                        "tag": ****,
                        "histograms": [{
                            "wall_time": ****,
                            "step": ****,
                            "bucket": [[**, **, **]],
                            },
                            {...}
                        ]
                    }
        """
        Validation.check_param_empty(train_id=train_id, tag=tag)
        logger.info("Start to process histogram data...")
        try:
            tensors = self._data_manager.list_tensors(train_id, tag)
        except ParamValueError as err:
            raise HistogramNotExistError(err.message)

        histograms = []
        for tensor in tensors:
            histogram = tensor.value
            buckets = histogram.buckets()
            histograms.append({
                "wall_time": tensor.wall_time,
                "step": tensor.step,
                "buckets": buckets
            })

        logger.info("Histogram data processing is finished!")
        response = {
            "train_id": train_id,
            "tag": tag,
            "histograms": histograms
        }
        return response

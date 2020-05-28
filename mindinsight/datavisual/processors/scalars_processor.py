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
from urllib.parse import unquote

from mindinsight.utils.exceptions import ParamValueError, UrlDecodeError
from mindinsight.datavisual.common.log import logger
from mindinsight.datavisual.utils.tools import if_nan_inf_to_none
from mindinsight.datavisual.common.exceptions import ScalarNotExistError
from mindinsight.datavisual.common.exceptions import TrainJobNotExistError
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
        try:
            tensors = self._data_manager.list_tensors(train_id, tag)
        except ParamValueError as ex:
            raise ScalarNotExistError(ex.message)

        for tensor in tensors:
            job_response.append({
                'wall_time': tensor.wall_time,
                'step': tensor.step,
                'value': tensor.value})
        return dict(metadatas=job_response)

    def get_scalars(self, train_ids, tags):
        """
        Get scalar data for given train_ids and tags.

        Args:
            train_ids (list): Specify list of train job ID.
            tags (list): Specify list of tags.

        Returns:
            list[dict], a list of dictionaries containing the `wall_time`, `step`, `value` for each scalar.
        """
        for index, train_id in enumerate(train_ids):
            try:
                train_id = unquote(train_id, errors='strict')
            except UnicodeDecodeError:
                raise UrlDecodeError('Unquote train id error with strict mode')
            else:
                train_ids[index] = train_id

        scalars = []
        for train_id in train_ids:
            scalars += self._get_train_scalars(train_id, tags)

        return scalars

    def _get_train_scalars(self, train_id, tags):
        """
        Get scalar data for given train_id and tags.

        Args:
            train_id (str): Specify train job ID.
            tags (list): Specify list of tags.

        Returns:
            list[dict], a list of dictionaries containing the `wall_time`, `step`, `value` for each scalar.
        """
        scalars = []
        for tag in tags:
            try:
                tensors = self._data_manager.list_tensors(train_id, tag)
            except ParamValueError:
                continue
            except TrainJobNotExistError:
                logger.warning('Can not find the given train job in cache.')
                return []

            scalar = {
                'train_id': train_id,
                'tag': tag,
                'values': [],
            }

            for tensor in tensors:
                scalar['values'].append({
                    'wall_time': tensor.wall_time,
                    'step': tensor.step,
                    'value': if_nan_inf_to_none('scalar_value', tensor.value),
                })

            scalars.append(scalar)

        return scalars

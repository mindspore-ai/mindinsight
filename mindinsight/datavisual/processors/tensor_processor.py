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
"""Tensor Processor APIs."""
from urllib.parse import unquote

import numpy as np

from mindinsight.datavisual.utils.tools import to_int
from mindinsight.utils.exceptions import ParamValueError, UrlDecodeError
from mindinsight.utils.tensor import TensorUtils, MAX_DIMENSIONS_FOR_TENSOR
from mindinsight.conf.constants import MAX_TENSOR_RESPONSE_DATA_SIZE
from mindinsight.datavisual.common.validation import Validation
from mindinsight.datavisual.common.exceptions import StepTensorDataNotInCacheError, TensorNotExistError
from mindinsight.datavisual.common.exceptions import ResponseDataExceedMaxValueError, TensorTooLargeError
from mindinsight.datavisual.data_transform.tensor_container import TensorContainer
from mindinsight.datavisual.processors.base_processor import BaseProcessor
from mindinsight.datavisual.proto_files import mindinsight_anf_ir_pb2 as anf_ir_pb2


class TensorProcessor(BaseProcessor):
    """Tensor Processor."""
    def get_tensors(self, train_ids, tags, step, dims, detail):
        """
        Get tensor data for given train_ids, tags, step, dims and detail.

        Args:
            train_ids (list): Specify list of train job ID.
            tags (list): Specify list of tag.
            step (int): Specify step of tag, it's necessary when detail is equal to 'data'.
            dims (str): Specify dims of step, it's necessary when detail is equal to 'data'.
            detail (str): Specify which data to query, available values: 'stats', 'histogram' and 'data'.

        Returns:
            dict, a dict including the `tensors`.

        Raises:
            UrlDecodeError, If unquote train id error with strict mode.
        """
        Validation.check_param_empty(train_id=train_ids, tag=tags)

        try:
            dims = unquote(dims, errors='strict') if dims else None
        except UnicodeDecodeError:
            raise UrlDecodeError('Unquote dims error with strict mode')

        for index, train_id in enumerate(train_ids):
            try:
                train_id = unquote(train_id, errors='strict')
            except UnicodeDecodeError:
                raise UrlDecodeError('Unquote train id error with strict mode')
            else:
                train_ids[index] = train_id

        tensors = []
        for train_id in train_ids:
            tensors += self._get_train_tensors(train_id, tags, step, dims, detail)

        return {"tensors": tensors}

    def _get_train_tensors(self, train_id, tags, step, dims, detail):
        """
        Get tensor data for given train_id, tags, step, dims and detail.

        Args:
            train_id (str): Specify list of train job ID.
            tags (list): Specify list of tag.
            step (int): Specify step of tensor, it's necessary when detail is set to 'data'.
            dims (str): Specify dims of tensor, it's necessary when detail is set to 'data'.
            detail (str): Specify which data to query, available values: 'stats', 'histogram' and 'data'.

        Returns:
            list[dict], a list of dictionaries containing the `train_id`, `tag`, `values`.

        Raises:
            TensorNotExistError, If tensor with specific train_id and tag is not exist in cache.
            ParamValueError, If the value of detail is not within available values:
                            'stats', 'histogram' and 'data'.
        """

        tensors_response = []
        for tag in tags:
            try:
                tensors = self._data_manager.list_tensors(train_id, tag)
            except ParamValueError as err:
                raise TensorNotExistError(err.message)

            if tensors and not isinstance(tensors[0].value, TensorContainer):
                raise TensorNotExistError("there is no tensor data in this tag: {}".format(tag))

            if detail is None or detail == 'stats':
                values = self._get_tensors_summary(detail, tensors)
            elif detail == 'data':
                Validation.check_param_empty(step=step, dims=dims)
                # Limit to query max two dimensions for tensor in table view.
                dims = TensorUtils.parse_shape(dims, limit=MAX_DIMENSIONS_FOR_TENSOR)
                step = to_int(step, "step")
                values = self._get_tensors_data(step, dims, tensors)
            elif detail == 'histogram':
                values = self._get_tensors_histogram(tensors)
            else:
                raise ParamValueError('Can not support this value: {} of detail.'.format(detail))

            tensor = {
                "train_id": train_id,
                "tag": tag,
                "values": values
            }
            tensors_response.append(tensor)

        return tensors_response

    def _get_tensors_summary(self, detail, tensors):
        """
        Builds a JSON-serializable object with information about tensor summary.

        Args:
            detail (str): Specify which data to query, detail value is None or 'stats' at this method.
            tensors (list): The list of _Tensor data.

        Returns:
            dict, a dict including the `wall_time`, `step`, and `value' for each tensor.
                    {
                        "wall_time": 0,
                        "step": 0,
                        "value": {
                            "dims": [1],
                            "data_type": "DT_FLOAT32"
                            "statistics": {
                                "max": 0,
                                "min": 0,
                                "avg": 0,
                                "count": 1,
                                "nan_count": 0,
                                "neg_inf_count": 0,
                                "pos_inf_count": 0
                            } This dict is being set when detail is equal to stats.
                        }
                    }
        """
        values = []
        for tensor in tensors:
            # This value is an instance of TensorContainer
            value = tensor.value
            value_dict = {
                "dims": value.dims,
                "data_type": anf_ir_pb2.DataType.Name(value.data_type)
            }
            if detail and detail == 'stats':
                stats = None
                if value.error_code is None:
                    stats = TensorUtils.get_statistics_dict(stats=value.stats, overall_stats=value.stats)
                value_dict.update({"statistics": stats})

            values.append({
                "wall_time": tensor.wall_time,
                "step": tensor.step,
                "value": value_dict
            })

        return values

    def _get_tensors_data(self, step, dims, tensors):
        """
        Builds a JSON-serializable object with information about tensor dims data.

        Args:
            step (int): Specify step of tensor.
            dims (tuple): Specify dims of tensor.
            tensors (list): The list of _Tensor data.

        Returns:
            dict, a dict including the `wall_time`, `step`, and `value' for each tensor.
                    {
                        "wall_time": 0,
                        "step": 0,
                        "value": {
                            "dims": [1],
                            "data_type": "DT_FLOAT32",
                            "data": [[0.1]]
                            "statistics": {
                                "max": 0,
                                "min": 0,
                                "avg": 0,
                                "count": 1,
                                "nan_count": 0,
                                "neg_inf_count": 0,
                                "pos_inf_count": 0
                            }
                        }
                    }

        Raises:
            ResponseDataExceedMaxValueError, If the size of response data exceed max value.
            StepTensorDataNotInCacheError, If query step is not in cache.
        """
        values = []
        step_in_cache = False
        for tensor in tensors:
            # This value is an instance of TensorContainer
            value = tensor.value
            if step != tensor.step:
                continue
            step_in_cache = True
            if value.error_code is not None:
                raise TensorTooLargeError("Step: {}".format(tensor.step))
            res_data = TensorUtils.get_specific_dims_data(value.ndarray, dims)
            flatten_data = res_data.flatten().tolist()
            if len(flatten_data) > MAX_TENSOR_RESPONSE_DATA_SIZE:
                raise ResponseDataExceedMaxValueError("the size of response data: {} exceed max value: {}."
                                                      .format(len(flatten_data), MAX_TENSOR_RESPONSE_DATA_SIZE))

            def transfer(array):
                if not isinstance(array, np.ndarray):
                    # The list is used here so that len function can be used
                    # when the value of array is `NAN`、｀-INF｀ or ｀INF｀.
                    array = [array]
                transfer_data = [None] * len(array)
                for index, data in enumerate(array):
                    if isinstance(data, np.ndarray):
                        transfer_data[index] = transfer(data)
                    else:
                        if np.isnan(data):
                            transfer_data[index] = 'NAN'
                        elif np.isneginf(data):
                            transfer_data[index] = '-INF'
                        elif np.isposinf(data):
                            transfer_data[index] = 'INF'
                        else:
                            transfer_data[index] = float(data)
                return transfer_data

            stats = TensorUtils.get_statistics_from_tensor(res_data)
            if stats.nan_count + stats.neg_inf_count + stats.pos_inf_count > 0:
                tensor_data = transfer(res_data)
            else:
                tensor_data = res_data.tolist()
            values.append({
                "wall_time": tensor.wall_time,
                "step": tensor.step,
                "value": {
                    "dims": value.dims,
                    "data_type": anf_ir_pb2.DataType.Name(value.data_type),
                    "data": tensor_data,
                    "statistics": TensorUtils.get_statistics_dict(stats=stats, overall_stats=value.stats)
                }
            })
            break
        if not step_in_cache:
            raise StepTensorDataNotInCacheError("this step: {} data may has been dropped.".format(step))

        return values

    def _get_tensors_histogram(self, tensors):
        """
        Builds a JSON-serializable object with information about tensor histogram data.

        Args:
            tensors (list): The list of _Tensor data.

        Returns:
            dict, a dict including the `wall_time`, `step`, and `value' for each tensor.
                    {
                        "wall_time": 0,
                        "step": 0,
                        "value": {
                            "dims": [1],
                            "data_type": "DT_FLOAT32",
                            "histogram_buckets": [[0.1, 0.2, 3]]
                            "statistics": {
                                "max": 0,
                                "min": 0,
                                "avg": 0,
                                "count": 1,
                                "nan_count": 0,
                                "neg_inf_count": 0,
                                "pos_inf_count": 0
                            }
                        }
                    }
        """
        values = []
        for tensor in tensors:
            # This value is an instance of TensorContainer
            value = tensor.value
            if value.error_code is not None:
                raise TensorTooLargeError("Step: {}".format(tensor.step))
            buckets = value.buckets()
            values.append({
                "wall_time": tensor.wall_time,
                "step": tensor.step,
                "value": {
                    "dims": value.dims,
                    "data_type": anf_ir_pb2.DataType.Name(value.data_type),
                    "histogram_buckets": buckets,
                    "statistics": TensorUtils.get_statistics_dict(stats=value.stats, overall_stats=value.stats)
                }
            })

        return values

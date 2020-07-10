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
from mindinsight.conf.constants import MAX_TENSOR_RESPONSE_DATA_SIZE
from mindinsight.datavisual.common.validation import Validation
from mindinsight.datavisual.common.exceptions import StepTensorDataNotInCacheError, TensorNotExistError
from mindinsight.datavisual.common.exceptions import ResponseDataExceedMaxValueError
from mindinsight.datavisual.data_transform.tensor_container import TensorContainer, get_statistics_from_tensor
from mindinsight.datavisual.processors.base_processor import BaseProcessor
from mindinsight.datavisual.proto_files import mindinsight_anf_ir_pb2 as anf_ir_pb2


def convert_array_from_str(dims, limit=0):
    """
    Convert string of dims data to array.

    Args:
        dims (str): Specify dims of tensor.
        limit (int): The max flexible dimension count, default value is 0 which means that there is no limitation.

    Returns:
        list, a string like this: "[0, 0, :, :]" will convert to this value: [0, 0, None, None].

    Raises:
        ParamValueError, If flexible dimensions exceed limit value.
    """
    dims = dims.replace('[', '') \
               .replace(']', '')
    dims_list = []
    count = 0
    for dim in dims.split(','):
        dim = dim.strip()
        if dim == ':':
            dims_list.append(None)
            count += 1
        else:
            dims_list.append(to_int(dim, "dim"))
    if limit and count > limit:
        raise ParamValueError("Flexible dimensions cannot exceed limit value: {}, size: {}"
                              .format(limit, count))
    return dims_list


def get_specific_dims_data(ndarray, dims, tensor_dims):
    """
    Get specific dims data.

    Args:
        ndarray (numpy.ndarray): An ndarray of numpy.
        dims (list): A list of specific dims.
        tensor_dims (list): A list of tensor dims.

    Returns:
        numpy.ndarray, an ndarray of specific dims tensor data.

    Raises:
        ParamValueError, If the length of param dims is not equal to the length of tensor dims or
                         the index of param dims out of range.
    """
    if len(dims) != len(tensor_dims):
        raise ParamValueError("The length of param dims: {}, is not equal to the "
                              "length of tensor dims: {}.".format(len(dims), len(tensor_dims)))
    indices = []
    for k, d in enumerate(dims):
        if d is not None:
            if d >= tensor_dims[k]:
                raise ParamValueError("The index: {} of param dims out of range: {}.".format(d, tensor_dims[k]))
            indices.append(d)
        else:
            indices.append(slice(0, tensor_dims[k]))
    return ndarray[tuple(indices)]


def get_statistics_dict(tensor_container, tensors):
    """
    Get statistics dict according to tensor data.

    Args:
        tensor_container (TensorContainer): An instance of TensorContainer.
        tensors (numpy.ndarray or number): An numpy.ndarray or number of tensor data.

    Returns:
        dict, a dict including 'max', 'min', 'avg', 'count', 'nan_count', 'neg_inf_count', 'pos_inf_count'.
    """
    if tensors is None:
        statistics = {
            "max": tensor_container.stats.max,
            "min": tensor_container.stats.min,
            "avg": tensor_container.stats.avg,
            "count": tensor_container.stats.count,
            "nan_count": tensor_container.stats.nan_count,
            "neg_inf_count": tensor_container.stats.neg_inf_count,
            "pos_inf_count": tensor_container.stats.pos_inf_count
        }
        return statistics

    if not isinstance(tensors, np.ndarray):
        tensors = np.array(tensors)

    stats = get_statistics_from_tensor(tensors)
    statistics = {
        "max": stats.max,
        "min": stats.min,
        "avg": stats.avg,
        "count": stats.count,
        "nan_count": stats.nan_count,
        "neg_inf_count": stats.neg_inf_count,
        "pos_inf_count": stats.pos_inf_count
    }
    return statistics


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
                "dims": tuple(value.dims),
                "data_type": anf_ir_pb2.DataType.Name(value.data_type)
            }
            if detail and detail == 'stats':
                stats = get_statistics_dict(value, None)
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
            dims (str): Specify dims of tensor.
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
        dims = convert_array_from_str(dims, limit=2)
        for tensor in tensors:
            # This value is an instance of TensorContainer
            value = tensor.value
            if step != tensor.step:
                continue
            step_in_cache = True
            ndarray = value.get_or_calc_ndarray()
            res_data = get_specific_dims_data(ndarray, dims, list(value.dims))
            flatten_data = res_data.flatten().tolist()
            if len(flatten_data) > MAX_TENSOR_RESPONSE_DATA_SIZE:
                raise ResponseDataExceedMaxValueError("the size of response data: {} exceed max value: {}."
                                                      .format(len(flatten_data), MAX_TENSOR_RESPONSE_DATA_SIZE))
            values.append({
                "wall_time": tensor.wall_time,
                "step": tensor.step,
                "value": {
                    "dims": tuple(value.dims),
                    "data_type": anf_ir_pb2.DataType.Name(value.data_type),
                    "data": res_data.tolist(),
                    "statistics": get_statistics_dict(value, flatten_data)
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
            buckets = value.buckets()
            values.append({
                "wall_time": tensor.wall_time,
                "step": tensor.step,
                "value": {
                    "dims": tuple(value.dims),
                    "data_type": anf_ir_pb2.DataType.Name(value.data_type),
                    "histogram_buckets": buckets,
                    "statistics": get_statistics_dict(value, None)
                }
            })

        return values

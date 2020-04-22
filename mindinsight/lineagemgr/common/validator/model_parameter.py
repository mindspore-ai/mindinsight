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
"""Define schema of model lineage input parameters."""
from marshmallow import Schema, fields, ValidationError, pre_load, validates
from marshmallow.validate import Range

from mindinsight.lineagemgr.common.exceptions.error_code import LineageErrorMsg, \
    LineageErrors
from mindinsight.lineagemgr.common.exceptions.exceptions import \
    LineageParamTypeError, LineageParamValueError
from mindinsight.lineagemgr.common.log import logger
from mindinsight.lineagemgr.common.utils import enum_to_list
from mindinsight.lineagemgr.querier.querier import LineageType
from mindinsight.lineagemgr.querier.query_model import FIELD_MAPPING
from mindinsight.utils.exceptions import MindInsightException

try:
    from mindspore.dataset.engine import Dataset
    from mindspore.nn import Cell, Optimizer
    from mindspore.common.tensor import Tensor
    from mindspore.train.callback import _ListCallback
except (ImportError, ModuleNotFoundError):
    logger.error('MindSpore Not Found!')


class RunContextArgs(Schema):
    """Define the parameter schema for RunContext."""
    optimizer = fields.Function(allow_none=True)
    loss_fn = fields.Function(allow_none=True)
    net_outputs = fields.Function(allow_none=True)
    train_network = fields.Function(allow_none=True)
    train_dataset = fields.Function(allow_none=True)
    epoch_num = fields.Int(allow_none=True, validate=Range(min=1))
    batch_num = fields.Int(allow_none=True, validate=Range(min=0))
    cur_step_num = fields.Int(allow_none=True, validate=Range(min=0))
    parallel_mode = fields.Str(allow_none=True)
    device_number = fields.Int(allow_none=True, validate=Range(min=1))
    list_callback = fields.Function(allow_none=True)

    @pre_load
    def check_optimizer(self, data, **kwargs):
        optimizer = data.get("optimizer")
        if optimizer and not isinstance(optimizer, Optimizer):
            raise ValidationError({'optimizer': [
                "Parameter optimizer must be an instance of mindspore.nn.optim.Optimizer."
            ]})
        return data

    @pre_load
    def check_train_network(self, data, **kwargs):
        train_network = data.get("train_network")
        if train_network and not isinstance(train_network, Cell):
            raise ValidationError({'train_network': [
                "Parameter train_network must be an instance of mindspore.nn.Cell."]})
        return data

    @pre_load
    def check_train_dataset(self, data, **kwargs):
        train_dataset = data.get("train_dataset")
        if train_dataset and not isinstance(train_dataset, Dataset):
            raise ValidationError({'train_dataset': [
                "Parameter train_dataset must be an instance of "
                "mindspore.dataengine.datasets.Dataset"]})
        return data

    @pre_load
    def check_loss(self, data, **kwargs):
        net_outputs = data.get("net_outputs")
        if net_outputs and not isinstance(net_outputs, Tensor):
            raise ValidationError({'net_outpus': [
                "The parameter net_outputs is invalid. It should be a Tensor."
            ]})
        return data

    @pre_load
    def check_list_callback(self, data, **kwargs):
        list_callback = data.get("list_callback")
        if list_callback and not isinstance(list_callback, _ListCallback):
            raise ValidationError({'list_callback': [
                "Parameter list_callback must be an instance of "
                "mindspore.train.callback._ListCallback."
            ]})
        return data


class EvalParameter(Schema):
    """Define the parameter schema for Evaluation job."""
    valid_dataset = fields.Function(allow_none=True)
    metrics = fields.Dict(allow_none=True)

    @pre_load
    def check_valid_dataset(self, data, **kwargs):
        valid_dataset = data.get("valid_dataset")
        if valid_dataset and not isinstance(valid_dataset, Dataset):
            raise ValidationError({'valid_dataset': [
                "Parameter valid_dataset must be an instance of "
                "mindspore.dataengine.datasets.Dataset"]})
        return data


class SearchModelConditionParameter(Schema):
    """Define the search model condition parameter schema."""
    summary_dir = fields.Dict()
    loss_function = fields.Dict()
    train_dataset_path = fields.Dict()
    train_dataset_count = fields.Dict()
    test_dataset_path = fields.Dict()
    test_dataset_count = fields.Dict()
    network = fields.Dict()
    optimizer = fields.Dict()
    learning_rate = fields.Dict()
    epoch = fields.Dict()
    batch_size = fields.Dict()
    device_num = fields.Dict()
    loss = fields.Dict()
    model_size = fields.Dict()
    limit = fields.Int(validate=lambda n: 0 < n <= 100)
    offset = fields.Int(validate=lambda n: 0 <= n <= 100000)
    sorted_name = fields.Str()
    sorted_type = fields.Str(allow_none=True)
    dataset_mark = fields.Dict()
    lineage_type = fields.Dict()

    @staticmethod
    def check_dict_value_type(data, value_type):
        """Check dict value type and int scope."""
        for key, value in data.items():
            if key == "in":
                if not isinstance(value, (list, tuple)):
                    raise ValidationError("The value of `in` operation must be list or tuple.")
            else:
                if not isinstance(value, value_type):
                    raise ValidationError("Wrong value type.")
                if value_type is int:
                    if value < 0 or value > pow(2, 63) - 1:
                        raise ValidationError("Int value should <= pow(2, 63) - 1.")
                    if isinstance(value, bool):
                        raise ValidationError("Wrong value type.")

    @staticmethod
    def check_param_value_type(data):
        """Check input param's value type."""
        for key, value in data.items():
            if key == "in":
                if not isinstance(value, (list, tuple)):
                    raise ValidationError("The value of `in` operation must be list or tuple.")
            else:
                if isinstance(value, bool) or \
                        (not isinstance(value, float) and not isinstance(value, int)):
                    raise ValidationError("Wrong value type.")

    @staticmethod
    def check_operation(data):
        """Check input param's compare operation."""
        if not set(data.keys()).issubset(['in', 'eq']):
            raise ValidationError("Its operation should be `in` or `eq`.")
        if len(data.keys()) > 1:
            raise ValidationError("More than one operation.")

    @validates("loss")
    def check_loss(self, data):
        """Check loss."""
        SearchModelConditionParameter.check_param_value_type(data)

    @validates("learning_rate")
    def check_learning_rate(self, data):
        """Check learning_rate."""
        SearchModelConditionParameter.check_param_value_type(data)

    @validates("loss_function")
    def check_loss_function(self, data):
        """Check loss function."""
        SearchModelConditionParameter.check_operation(data)
        SearchModelConditionParameter.check_dict_value_type(data, str)

    @validates("train_dataset_path")
    def check_train_dataset_path(self, data):
        """Check train dataset path."""
        SearchModelConditionParameter.check_operation(data)
        SearchModelConditionParameter.check_dict_value_type(data, str)

    @validates("train_dataset_count")
    def check_train_dataset_count(self, data):
        """Check train dataset count."""
        SearchModelConditionParameter.check_dict_value_type(data, int)

    @validates("test_dataset_path")
    def check_test_dataset_path(self, data):
        """Check test dataset path."""
        SearchModelConditionParameter.check_operation(data)
        SearchModelConditionParameter.check_dict_value_type(data, str)

    @validates("test_dataset_count")
    def check_test_dataset_count(self, data):
        """Check test dataset count."""
        SearchModelConditionParameter.check_dict_value_type(data, int)

    @validates("network")
    def check_network(self, data):
        """Check network."""
        SearchModelConditionParameter.check_operation(data)
        SearchModelConditionParameter.check_dict_value_type(data, str)

    @validates("optimizer")
    def check_optimizer(self, data):
        """Check optimizer."""
        SearchModelConditionParameter.check_operation(data)
        SearchModelConditionParameter.check_dict_value_type(data, str)

    @validates("epoch")
    def check_epoch(self, data):
        """Check epoch."""
        SearchModelConditionParameter.check_dict_value_type(data, int)

    @validates("batch_size")
    def check_batch_size(self, data):
        """Check batch size."""
        SearchModelConditionParameter.check_dict_value_type(data, int)

    @validates("device_num")
    def check_device_num(self, data):
        """Check device num."""
        SearchModelConditionParameter.check_dict_value_type(data, int)

    @validates("model_size")
    def check_model_size(self, data):
        """Check model size."""
        SearchModelConditionParameter.check_dict_value_type(data, int)

    @validates("summary_dir")
    def check_summary_dir(self, data):
        """Check summary dir."""
        SearchModelConditionParameter.check_operation(data)
        SearchModelConditionParameter.check_dict_value_type(data, str)

    @validates("dataset_mark")
    def check_dataset_mark(self, data):
        """Check dataset mark."""
        SearchModelConditionParameter.check_operation(data)
        SearchModelConditionParameter.check_dict_value_type(data, str)

    @validates("lineage_type")
    def check_lineage_type(self, data):
        """Check lineage type."""
        SearchModelConditionParameter.check_operation(data)
        SearchModelConditionParameter.check_dict_value_type(data, str)
        recv_types = []
        for key, value in data.items():
            if key == "in":
                recv_types = value
            else:
                recv_types.append(value)

        lineage_types = enum_to_list(LineageType)
        if not set(recv_types).issubset(lineage_types):
            raise ValidationError("Given lineage type should be one of %s." % lineage_types)

    @pre_load
    def check_comparision(self, data, **kwargs):
        """Check comparision for all parameters in schema."""
        for attr, condition in data.items():
            if attr in ["limit", "offset", "sorted_name", "sorted_type", 'lineage_type']:
                continue

            if not isinstance(attr, str):
                raise LineageParamValueError('The search attribute not supported.')

            if attr not in FIELD_MAPPING and not attr.startswith(('metric/', 'user_defined/')):
                raise LineageParamValueError('The search attribute not supported.')

            if not isinstance(condition, dict):
                raise LineageParamTypeError("The search_condition element {} should be dict."
                                            .format(attr))

            for key in condition.keys():
                if key not in ["eq", "lt", "gt", "le", "ge", "in"]:
                    raise LineageParamValueError("The compare condition should be in "
                                                 "('eq', 'lt', 'gt', 'le', 'ge', 'in').")

            if attr.startswith('metric/'):
                if len(attr) == 7:
                    raise LineageParamValueError(
                        'The search attribute not supported.'
                    )
                try:
                    SearchModelConditionParameter.check_param_value_type(condition)
                except ValidationError:
                    raise MindInsightException(
                        error=LineageErrors.LINEAGE_PARAM_METRIC_ERROR,
                        message=LineageErrorMsg.LINEAGE_METRIC_ERROR.value.format(attr)
                    )
        return data

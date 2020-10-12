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

from mindinsight.lineagemgr.common.exceptions.error_code import LineageErrorMsg, LineageErrors
from mindinsight.lineagemgr.common.exceptions.exceptions import LineageParamTypeError, LineageParamValueError
from mindinsight.lineagemgr.common.utils import enum_to_list
from mindinsight.lineagemgr.querier.querier import LineageType
from mindinsight.lineagemgr.querier.query_model import FIELD_MAPPING
from mindinsight.utils.exceptions import MindInsightException


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
            if key in ["in", "not_in"]:
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
        if not set(data.keys()).issubset(['in', 'eq', 'not_in']):
            raise ValidationError("Its operation should be `eq`, `in` or `not_in`.")

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
    def check_comparison(self, data, **kwargs):
        """Check comparison for all parameters in schema."""
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
                if key not in ["eq", "lt", "gt", "le", "ge", "in", "not_in"]:
                    raise LineageParamValueError("The compare condition should be in "
                                                 "('eq', 'lt', 'gt', 'le', 'ge', 'in', 'not_in').")

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

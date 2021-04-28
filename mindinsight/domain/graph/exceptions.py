# Copyright 2021 Huawei Technologies Co., Ltd
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
"""Parse exceptions module."""

from mindinsight.utils.exceptions import MindInsightException
from mindinsight.utils.constant import GraphDomainErrors


class UnknownDataTypeError(MindInsightException):
    """Unknwn data type error."""

    def __init__(self, proto_type):
        super().__init__(
            error=GraphDomainErrors.UNKNOWN_DATA_TYPE_ERROR,
            message=str(proto_type))


class TupleGetitemIndexError(MindInsightException):
    """Tuple getitem index error."""

    def __init__(self, op_name, index_name):
        super().__init__(
            error=GraphDomainErrors.TUPLE_GETITEM_INDEX_ERROR,
            message=f'op : {op_name}, index: {index_name}')


class UnknownTensorError(MindInsightException):
    """Unknwn tensor error."""

    def __init__(self, is_op, file_name):
        super().__init__(
            error=GraphDomainErrors.UNKNOWN_TENSOR_ERROR,
            message=f'is_op : {is_op}, file_name: {file_name}')

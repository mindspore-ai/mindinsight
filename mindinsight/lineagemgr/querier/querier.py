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
"""This file is used to define lineage info querier."""
import enum
import functools
import operator

from mindinsight.lineagemgr.common.exceptions.exceptions import LineageQuerierParamException, LineageParamTypeError
from mindinsight.lineagemgr.common.utils import enum_to_list
from mindinsight.lineagemgr.lineage_parser import SuperLineageObj
from mindinsight.lineagemgr.querier.query_model import FIELD_MAPPING


@enum.unique
class ConditionParam(enum.Enum):
    """
    Filtering and sorting field names.

    `LIMIT` represents the number of lineage info per page. `OFFSET` represents
    page number. `SORTED_NAME` means to sort by this field. `SORTED_TYPE` means
    ascending or descending.
    """
    LIMIT = 'limit'
    OFFSET = 'offset'
    SORTED_NAME = 'sorted_name'
    SORTED_TYPE = 'sorted_type'
    LINEAGE_TYPE = 'lineage_type'

    @classmethod
    def is_condition_type(cls, value):
        """
        Judge that the input param is one of field names in the class.

        Args:
            value (str): The input field name.

        Returns:
            bool, `True` if the input field name in the class, else `False`.
        """
        return value in cls._value2member_map_


@enum.unique
class ExpressionType(enum.Enum):
    """
    Filter condition name definition.

    `EQ` means `==`. `LT` means `<`. `GT` means `>`. `LE` means `<=`. `GE` means
    `>=`. `IN` means filter value in the specified list.
    """
    EQ = 'eq'
    LT = 'lt'
    GT = 'gt'
    LE = 'le'
    GE = 'ge'
    IN = 'in'
    NOT_IN = 'not_in'

    @classmethod
    def is_valid_exp(cls, key):
        """
        Judge that the input param is one of filter condition names in the class.

        Args:
            key (str): The input filter condition name.

        Returns:
            bool, `True` if the input filter condition name in the class,
            else `False`.
        """
        return key in cls._value2member_map_

    @classmethod
    def is_match(cls, except_key, except_value, actual_value):
        """
        Determine whether the value meets the expected requirement.

        Args:
            except_key (str): The expression key.
            except_value (Union[str, int, float, list, tuple]): The expected
                value.
            actual_value (Union[str, int, float]): The actual value.

        Returns:
            bool, `True` if the actual value meets the expected requirement,
            else `False`.
        """
        if actual_value is None and except_key in [cls.LT.value, cls.GT.value,
                                                   cls.LE.value, cls.GE.value]:
            return False

        try:
            if except_key == cls.IN.value:
                state = operator.contains(except_value, actual_value)
            elif except_key == cls.NOT_IN.value:
                state = not operator.contains(except_value, actual_value)
            else:
                state = getattr(operator, except_key)(actual_value, except_value)
        except TypeError:
            # actual_value can not compare with except_value
            return False
        return state


@enum.unique
class LineageFilterKey(enum.Enum):
    """Summary lineage information filter key."""
    METRIC = 'metric'
    HYPER_PARAM = 'hyper_parameters'
    ALGORITHM = 'algorithm'
    TRAIN_DATASET = 'train_dataset'
    VALID_DATASET = 'valid_dataset'
    MODEL = 'model'
    DATASET_GRAPH = 'dataset_graph'

    @classmethod
    def is_valid_filter_key(cls, key):
        """
        Judge that the input param is one of field names in the class.

        Args:
            key (str): The input field name.

        Returns:
            bool, `True` if the input field name in the class, else `False`.
        """
        return key in cls._value2member_map_

    @classmethod
    def get_key_list(cls):
        """
        Get the filter key name list.

        Returns:
            list[str], the filter key name list.
        """
        return [member.value for member in cls]


@enum.unique
class LineageType(enum.Enum):
    """Lineage search type."""
    DATASET = 'dataset'
    MODEL = 'model'


class Querier:
    """
    The querier of model lineage information.

    The class provides model lineage information query function. The information
    includes hyper parameters, train dataset, algorithm, model information,
    metric, valid dataset, etc.

    The class also provides search and sorting capabilities about model lineage
    information. You can search and sort by the specified condition.
    The condition explain in `ConditionParam` and `ExpressionType` class.
    See the method `filter_summary_lineage` for supported fields.

    Args:
        super_lineage_objs (dict): A dict of <summary_dir, SuperLineageObject>.

    Raises:
        LineageParamTypeError: If the input parameter type is invalid.
        LineageQuerierParamException: If the input parameter value is invalid.
        LineageSummaryParseException: If all summary logs parsing failed.
    """
    def __init__(self, super_lineage_objs):
        self._super_lineage_objs = self._check_objs(super_lineage_objs)

    def _check_objs(self, super_lineage_objs):
        if super_lineage_objs is None:
            raise LineageQuerierParamException(
                'querier_init_param', 'The querier init param is empty.'
            )
        if not isinstance(super_lineage_objs, dict):
            raise LineageParamTypeError("Init param should be a dict.")
        return super_lineage_objs

    def filter_summary_lineage(self, condition=None):
        """
        Filter and sort lineage information based on the specified condition.

        See `ConditionType` and `ExpressionType` class for the rule of filtering
        and sorting. The filtering and sorting fields are defined in
        `FIELD_MAPPING` or prefixed with `metric/` or 'user_defined/'.

        If the condition is `None`, all model lineage information will be
        returned.

        Args:
            condition (Union[dict, None]): Filter and sort condition.
                Default: None.

        Returns:
            dict, filtered and sorted model lineage information.
        """
        def _filter(super_lineage_obj: SuperLineageObj):
            for condition_key, condition_value in condition.items():
                if ConditionParam.is_condition_type(condition_key):
                    continue
                if self._is_valid_field(condition_key):
                    raise LineageQuerierParamException(
                        'condition',
                        'The field {} not supported'.format(condition_key)
                    )

                value = super_lineage_obj.lineage_obj.get_value_by_key(condition_key)
                for exp_key, exp_value in condition_value.items():
                    if not ExpressionType.is_valid_exp(exp_key):
                        raise LineageQuerierParamException(
                            'condition',
                            'The expression {} not supported.'.format(exp_key)
                        )
                    if not ExpressionType.is_match(exp_key, exp_value, value):
                        return False
            return True

        if condition is None:
            condition = {}

        self._add_dataset_mark()
        super_lineage_objs = list(self._super_lineage_objs.values())
        super_lineage_objs.sort(key=lambda x: x.update_time, reverse=True)

        results = list(filter(_filter, super_lineage_objs))
        results = self._sorted_results(results, condition)

        offset_results = self._handle_limit_and_offset(condition, results)

        customized = self._organize_customized(offset_results)

        lineage_types = condition.get(ConditionParam.LINEAGE_TYPE.value)
        lineage_types = self._get_lineage_types(lineage_types)

        object_items = []
        for item in offset_results:
            lineage_object = dict()
            if LineageType.MODEL.value in lineage_types:
                lineage_object.update(item.lineage_obj.to_model_lineage_dict())
            if LineageType.DATASET.value in lineage_types:
                lineage_object.update(item.lineage_obj.to_dataset_lineage_dict())
            lineage_object.update({"added_info": item.added_info})
            object_items.append(lineage_object)

        lineage_info = {
            'customized': customized,
            'object': object_items,
            'count': len(results)
        }

        return lineage_info

    def _sorted_results(self, results, condition):
        """Get sorted results."""
        def _cmp(value1, value2):
            if value1 is None and value2 is None:
                cmp_result = 0
            elif value1 is None:
                cmp_result = -1
            elif value2 is None:
                cmp_result = 1
            else:
                try:
                    cmp_result = (value1 > value2) - (value1 < value2)
                except TypeError:
                    type1 = type(value1).__name__
                    type2 = type(value2).__name__
                    cmp_result = (type1 > type2) - (type1 < type2)
            return cmp_result

        def _cmp_added_info(obj1: SuperLineageObj, obj2: SuperLineageObj):
            value1 = obj1.added_info.get(sorted_name)
            value2 = obj2.added_info.get(sorted_name)
            return _cmp(value1, value2)

        def _cmp_super_lineage_obj(obj1: SuperLineageObj, obj2: SuperLineageObj):
            value1 = obj1.lineage_obj.get_value_by_key(sorted_name)
            value2 = obj2.lineage_obj.get_value_by_key(sorted_name)

            return _cmp(value1, value2)

        if ConditionParam.SORTED_NAME.value in condition:
            sorted_name = condition.get(ConditionParam.SORTED_NAME.value)
            sorted_type = condition.get(ConditionParam.SORTED_TYPE.value)
            reverse = sorted_type == 'descending'
            if sorted_name in ['tag']:
                results = sorted(
                    results, key=functools.cmp_to_key(_cmp_added_info), reverse=reverse
                )
                return results

            if self._is_valid_field(sorted_name):
                raise LineageQuerierParamException(
                    'condition',
                    'The sorted name {} not supported.'.format(sorted_name)
                )
            results = sorted(
                results, key=functools.cmp_to_key(_cmp_super_lineage_obj), reverse=reverse
            )
        return results

    def _organize_customized(self, offset_results):
        """Organize customized."""
        customized = dict()
        for offset_result in offset_results:
            for obj_name in ["metric", "user_defined"]:
                self._organize_customized_item(customized, offset_result.lineage_obj, obj_name)

        # If types contain numbers and string, it will be "mixed".
        # If types contain "int" and "float", it will be "float".
        for key, value in customized.items():
            types = value["type"]
            if len(types) == 1:
                customized[key]["type"] = list(types)[0]
            elif types.issubset(["int", "float"]):
                customized[key]["type"] = "float"
            else:
                customized[key]["type"] = "mixed"
        return customized

    def _organize_customized_item(self, customized, offset_result, obj_name):
        """Organize customized item."""
        obj = getattr(offset_result, obj_name)
        require = bool(obj_name == "metric")
        if obj and isinstance(obj, dict):
            for key, value in obj.items():
                label = f'{obj_name}/{key}'
                current_type = type(value).__name__
                if customized.get(label) is None:
                    customized[label] = dict()
                    customized[label]["label"] = label
                    # user defined info is not displayed by default
                    customized[label]["required"] = require
                    customized[label]["type"] = set()
                customized[label]["type"].add(current_type)

    def _get_lineage_types(self, lineage_type_param):
        """
        Get lineage types.

        Args:
            lineage_type_param (dict): A dict contains "in" or "eq".

        Returns:
            list, lineage type.

        """
        # lineage_type_param is None or an empty dict
        if not lineage_type_param:
            return enum_to_list(LineageType)

        if lineage_type_param.get("in") is not None:
            return lineage_type_param.get("in")

        return [lineage_type_param.get("eq")]

    def _is_valid_field(self, field_name):
        """
        Check if field name is valid.

        Args:
            field_name (str): Field name.

        Returns:
            bool, `True` if the field name is valid, else `False`.
        """
        return field_name not in FIELD_MAPPING \
               and not field_name.startswith(('metric/', 'user_defined/'))

    def _handle_limit_and_offset(self, condition, result):
        """
        Handling the condition of `limit` and `offset`.

        Args:
            condition (dict): Filter and sort condition.
            result (list[SuperLineageObj]): Filtered and sorted result.

        Returns:
            list[SuperLineageObj], paginated result.
        """
        offset = 0
        limit = 10
        if ConditionParam.OFFSET.value in condition:
            offset = condition.get(ConditionParam.OFFSET.value)
        if ConditionParam.LIMIT.value in condition:
            limit = condition.get(ConditionParam.LIMIT.value)
        if ConditionParam.OFFSET.value not in condition \
                and ConditionParam.LIMIT.value not in condition:
            offset_result = result
        else:
            offset_result = result[offset * limit: limit * (offset + 1)]
        return offset_result

    def _add_dataset_mark(self):
        """Add dataset mark into LineageObj."""
        # give a dataset mark for each dataset graph in lineage information
        marked_dataset_group = {'1': None}
        for super_lineage_obj in self._super_lineage_objs.values():
            lineage = super_lineage_obj.lineage_obj
            dataset_mark = '0'
            for dataset_graph_mark, marked_dataset_graph in marked_dataset_group.items():
                if marked_dataset_graph == lineage.dataset_graph:
                    dataset_mark = dataset_graph_mark
                    break
            # if no matched, add the new dataset graph into group
            if dataset_mark == '0':
                dataset_mark = str(int(max(marked_dataset_group.keys())) + 1)
                marked_dataset_group.update({
                    dataset_mark:
                        lineage.dataset_graph
                })
            lineage.dataset_mark = dataset_mark

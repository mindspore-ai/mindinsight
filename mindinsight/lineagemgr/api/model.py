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
"""This file is used to define the model lineage python api."""
import os

from mindinsight.lineagemgr.common.exceptions.exceptions import LineageParamValueError, \
    LineageQuerySummaryDataError, LineageParamSummaryPathError, \
    LineageQuerierParamException, LineageDirNotExistError, LineageSearchConditionParamError, \
    LineageParamTypeError, LineageSummaryParseException
from mindinsight.lineagemgr.common.log import logger as log
from mindinsight.lineagemgr.common.utils import normalize_summary_dir
from mindinsight.lineagemgr.common.validator.model_parameter import SearchModelConditionParameter
from mindinsight.lineagemgr.common.validator.validate import validate_filter_key, validate_search_model_condition, \
    validate_condition, validate_path, validate_train_id
from mindinsight.lineagemgr.lineage_parser import LineageParser, LineageOrganizer
from mindinsight.lineagemgr.querier.querier import Querier
from mindinsight.utils.exceptions import MindInsightException


def get_summary_lineage(summary_dir, keys=None):
    """
    Get the lineage information according to summary directory and keys.

    The function queries lineage information of single train process
    corresponding to the given summary directory. Users can query the
    information according to `keys`.

    Args:
        summary_dir (str): The summary directory. It contains summary logs for
            one training.
        keys (list[str]): The filter keys of lineage information. The acceptable
            keys are `metric`, `user_defined`, `hyper_parameters`, `algorithm`,
            `train_dataset`, `model`, `valid_dataset` and `dataset_graph`.
            If it is `None`, all information will be returned. Default: None.

    Returns:
        dict, the lineage information for one training.

    Raises:
        LineageParamSummaryPathError: If summary path is invalid.
        LineageQuerySummaryDataError: If querying summary data fails.
        LineageFileNotFoundError: If the summary log file is not found.

    Examples:
        >>> summary_dir = "/path/to/summary"
        >>> summary_lineage_info = get_summary_lineage(summary_dir)
        >>> hyper_parameters = get_summary_lineage(summary_dir, keys=["hyper_parameters"])
    """
    return general_get_summary_lineage(summary_dir=summary_dir, keys=keys)


def general_get_summary_lineage(data_manager=None, summary_dir=None, keys=None):
    """
    Get summary lineage from data_manager or parsing from summaries.

    One of data_manager or summary_dir needs to be specified. Support getting
    super_lineage_obj from data_manager or parsing summaries by summary_dir.

    Args:
        data_manager (DataManager): Data manager defined as
            mindinsight.datavisual.data_transform.data_manager.DataManager
        summary_dir (str): The summary directory. It contains summary logs for
            one training.
        keys (list[str]): The filter keys of lineage information. The acceptable
            keys are `metric`, `user_defined`, `hyper_parameters`, `algorithm`,
            `train_dataset`, `model`, `valid_dataset` and `dataset_graph`.
            If it is `None`, all information will be returned. Default: None.

    Returns:
        dict, the lineage information for one training.

    Raises:
        LineageParamSummaryPathError: If summary path is invalid.
        LineageQuerySummaryDataError: If querying summary data fails.
        LineageFileNotFoundError: If the summary log file is not found.

    """
    default_result = {}
    if data_manager is None and summary_dir is None:
        raise LineageParamTypeError("One of data_manager or summary_dir needs to be specified.")
    if data_manager is not None and summary_dir is None:
        raise LineageParamTypeError("If data_manager is specified, the summary_dir needs to be "
                                    "specified as relative path.")

    if keys is not None:
        validate_filter_key(keys)

    if data_manager is None:
        normalize_summary_dir(summary_dir)
        super_lineage_obj = LineageParser(summary_dir).super_lineage_obj
    else:
        validate_train_id(summary_dir)
        super_lineage_obj = LineageOrganizer(data_manager=data_manager).get_super_lineage_obj(summary_dir)

    if super_lineage_obj is None:
        return default_result

    try:
        result = Querier({summary_dir: super_lineage_obj}).get_summary_lineage(summary_dir, keys)
    except (LineageQuerierParamException, LineageParamTypeError) as error:
        log.error(str(error))
        log.exception(error)
        raise LineageQuerySummaryDataError("Get summary lineage failed.")
    return result[0]


def filter_summary_lineage(summary_base_dir, search_condition=None):
    """
    Filter the lineage information under summary base directory according to search condition.

    Users can filter and sort all lineage information according to the search
    condition. The supported filter fields include `summary_dir`, `network`,
    etc. The filter conditions include `eq`, `lt`, `gt`, `le`, `ge` and `in`.
    If the value type of filter condition is `str`, such as summary_dir and
    lineage_type, then its key can only be `in` and `eq`. At the same time,
    the combined use of these fields and conditions is supported. If you want
    to sort based on filter fields, the field of `sorted_name` and `sorted_type`
    should be specified.

    Users can use `lineage_type` to decide what kind of lineage information to
    query. If the `lineage_type` is not defined, the query result is all lineage
    information.

    Users can paginate query result based on `offset` and `limit`. The `offset`
    refers to page number. The `limit` refers to the number in one page.

    Args:
        summary_base_dir (str): The summary base directory. It contains summary
            directories generated by training.
        search_condition (dict): The search condition. When filtering and
            sorting, in addition to the following supported fields, fields
            prefixed with `metric/` and `user_defined/` are also supported.
            For example, the field should be `metric/accuracy` if the key
            of `metrics` parameter is `accuracy`. The fields prefixed with
            `metric/` and `user_defined/` are related to the `metrics`
            parameter in the training script and user defined information in
            TrainLineage/EvalLineage callback, respectively. Default: None.

            - summary_dir (dict): The filter condition of summary directory.

            - loss_function (dict): The filter condition of loss function.

            - train_dataset_path (dict): The filter condition of train dataset path.

            - train_dataset_count (dict): The filter condition of train dataset count.

            - test_dataset_path (dict): The filter condition of test dataset path.

            - test_dataset_count (dict): The filter condition of test dataset count.

            - network (dict): The filter condition of network.

            - optimizer (dict): The filter condition of optimizer.

            - learning_rate (dict): The filter condition of learning rate.

            - epoch (dict): The filter condition of epoch.

            - batch_size (dict): The filter condition of batch size.

            - device_num (dict): The filter condition of device num.

            - loss (dict): The filter condition of loss.

            - model_size (dict): The filter condition of model size.

            - dataset_mark (dict): The filter condition of dataset mark.

            - lineage_type (dict): The filter condition of lineage type. It decides
              what kind of lineage information to query. Its value can be `dataset`
              or `model`, e.g., {'in': ['dataset', 'model']}, {'eq': 'model'}, etc.
              If its values contain `dataset`, the query result will contain the
              lineage information related to data augmentation. If its values contain
              `model`, the query result will contain model lineage information.
              If it is not defined or it is a dict like {'in': ['dataset', 'model']},
              the query result is all lineage information.

            - offset (int): Page number, the value range is [0, 100000].

            - limit (int): The number in one page, the value range is [1, 100].

            - sorted_name (str): Specify which field to sort by.

            - sorted_type (str): Specify sort order. It can be `ascending` or
              `descending`.

    Returns:
        dict, lineage information under summary base directory according to
        search condition.

    Raises:
        LineageSearchConditionParamError: If search_condition param is invalid.
        LineageParamSummaryPathError: If summary path is invalid.
        LineageFileNotFoundError: If the summary log file is not found.
        LineageQuerySummaryDataError: If querying summary log file data fails.

    Examples:
        >>> summary_base_dir = "/path/to/summary_base"
        >>> search_condition = {
        >>>     'summary_dir': {
        >>>         'in': [
        >>>             os.path.join(summary_base_dir, 'summary_1'),
        >>>             os.path.join(summary_base_dir, 'summary_2'),
        >>>             os.path.join(summary_base_dir, 'summary_3')
        >>>         ]
        >>>     },
        >>>     'loss': {
        >>>         'gt': 2.0
        >>>     },
        >>>     'batch_size': {
        >>>         'ge': 128,
        >>>         'le': 256
        >>>     },
        >>>     'metric/accuracy': {
        >>>         'lt': 0.1
        >>>     },
        >>>     'sorted_name': 'summary_dir',
        >>>     'sorted_type': 'descending',
        >>>     'limit': 3,
        >>>     'offset': 0,
        >>>     'lineage_type': {
        >>>         'eq': 'model'
        >>>     }
        >>> }
        >>> summary_lineage = filter_summary_lineage(summary_base_dir)
        >>> summary_lineage_filter = filter_summary_lineage(summary_base_dir, search_condition)
    """
    return general_filter_summary_lineage(summary_base_dir=summary_base_dir, search_condition=search_condition)


def general_filter_summary_lineage(data_manager=None, summary_base_dir=None, search_condition=None, added=False):
    """
    Filter summary lineage from data_manager or parsing from summaries.

    One of data_manager or summary_base_dir needs to be specified. Support getting
    super_lineage_obj from data_manager or parsing summaries by summary_base_dir.

    Args:
        data_manager (DataManager): Data manager defined as
            mindinsight.datavisual.data_transform.data_manager.DataManager
        summary_base_dir (str): The summary base directory. It contains summary
            directories generated by training.
        search_condition (dict): The search condition.
    """
    if data_manager is None and summary_base_dir is None:
        raise LineageParamTypeError("One of data_manager or summary_base_dir needs to be specified.")

    if data_manager is None:
        summary_base_dir = normalize_summary_dir(summary_base_dir)
    else:
        summary_base_dir = data_manager.summary_base_dir

    search_condition = {} if search_condition is None else search_condition

    try:
        validate_condition(search_condition)
        validate_search_model_condition(SearchModelConditionParameter, search_condition)
    except MindInsightException as error:
        log.error(str(error))
        log.exception(error)
        raise LineageSearchConditionParamError(str(error.message))

    try:
        search_condition = _convert_relative_path_to_abspath(summary_base_dir, search_condition)
    except (LineageParamValueError, LineageDirNotExistError) as error:
        log.error(str(error))
        log.exception(error)
        raise LineageParamSummaryPathError(str(error.message))

    try:
        lineage_objects = LineageOrganizer(data_manager, summary_base_dir).super_lineage_objs
        result = Querier(lineage_objects).filter_summary_lineage(
            condition=search_condition,
            added=added
        )
    except LineageSummaryParseException:
        result = {'object': [], 'count': 0}
    except (LineageQuerierParamException, LineageParamTypeError) as error:
        log.error(str(error))
        log.exception(error)
        raise LineageQuerySummaryDataError("Filter summary lineage failed.")

    return result


def _convert_relative_path_to_abspath(summary_base_dir, search_condition):
    """
    Convert relative path to absolute path.

    Args:
        summary_base_dir (str): The summary base directory.
        search_condition (dict): The search condition.

    Returns:
        dict, the updated search_condition.

    Raises:
        LineageParamValueError: If the value of input_name is invalid.
    """
    if ("summary_dir" not in search_condition) or (not search_condition.get("summary_dir")):
        return search_condition

    summary_dir_condition = search_condition.get("summary_dir")

    if 'in' in summary_dir_condition:
        summary_paths = []
        for summary_dir in summary_dir_condition.get('in'):
            if summary_dir.startswith('./'):
                abs_dir = os.path.join(
                    summary_base_dir, summary_dir[2:]
                )
                abs_dir = validate_path(abs_dir)
            else:
                abs_dir = validate_path(summary_dir)
            summary_paths.append(abs_dir)
        search_condition.get('summary_dir')['in'] = summary_paths

    if 'eq' in summary_dir_condition:
        summary_dir = summary_dir_condition.get('eq')
        if summary_dir.startswith('./'):
            abs_dir = os.path.join(
                summary_base_dir, summary_dir[2:]
            )
            abs_dir = validate_path(abs_dir)
        else:
            abs_dir = validate_path(summary_dir)
        search_condition.get('summary_dir')['eq'] = abs_dir

    return search_condition

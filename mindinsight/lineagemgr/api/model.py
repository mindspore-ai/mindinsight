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
    LineageFileNotFoundError, LineageQuerySummaryDataError, LineageParamSummaryPathError, \
    LineageQuerierParamException, LineageDirNotExistError, LineageSearchConditionParamError, \
    LineageParamTypeError, LineageSummaryParseException
from mindinsight.lineagemgr.common.log import logger as log
from mindinsight.lineagemgr.common.path_parser import SummaryPathParser
from mindinsight.lineagemgr.common.validator.model_parameter import SearchModelConditionParameter
from mindinsight.lineagemgr.common.validator.validate import validate_filter_key
from mindinsight.lineagemgr.common.validator.validate import validate_search_model_condition, \
    validate_condition, validate_path
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
            keys are `metric`, `hyper_parameters`, `algorithm`, `train_dataset`,
            `model`, `valid_dataset` and `dataset_graph`. If it is `None`, all
            information will be returned. Default: None.

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
    try:
        summary_dir = validate_path(summary_dir)
    except MindInsightException as error:
        log.error(str(error))
        log.exception(error)
        raise LineageParamSummaryPathError(str(error.message))

    if keys is not None:
        validate_filter_key(keys)

    summary_path = SummaryPathParser.get_latest_lineage_summary(summary_dir)
    if summary_path is None:
        log.error('There is no summary log file under summary_dir.')
        raise LineageFileNotFoundError(
            'There is no summary log file under summary_dir.'
        )

    try:
        result = Querier(summary_path).get_summary_lineage(
            summary_dir, filter_keys=keys)
    except LineageSummaryParseException:
        return {}
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
    At the same time, the combined use of these fields and conditions is
    supported. If you want to sort based on filter fields, the field of
    `sorted_name` and `sorted_type` should be specified.

    Users can use `lineage_type` to decide what kind of lineage information to
    query. If the `lineage_type` is `dataset`, the query result is only the
    lineage information related to data augmentation. If the `lineage_type` is
    `model` or `None`, the query result is all lineage information.

    Users can paginate query result based on `offset` and `limit`. The `offset`
    refers to page number. The `limit` refers to the number in one page.

    Args:
        summary_base_dir (str): The summary base directory. It contains summary
            directories generated by training.
        search_condition (dict): The search condition. When filtering and
            sorting, in addition to the following supported fields, fields
            prefixed with `metric/` are also supported. The fields prefixed with
            `metric/` are related to the `metrics` parameter in the training
            script. For example, if the key of `metrics` parameter is
            `accuracy`, the field should be `metric/accuracy`. Default: None.

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

            - loss (dict): The filter condition of loss.

            - model_size (dict): The filter condition of model size.

            - dataset_mark (dict): The filter condition of dataset mark.

            - offset (int): Page number, the value range is [0, 100000].

            - limit (int): The number in one page, the value range is [1, 100].

            - sorted_name (str): Specify which field to sort by.

            - sorted_type (str): Specify sort order. It can be `ascending` or
              `descending`.

            - lineage_type (str): It decides what kind of lineage information to
              query. It can be `dataset` or `model`. If it is `dataset`,
              the query result is only the lineage information related to data
              augmentation. If it is `model` or `None`, the query result is all
              lineage information.

    Returns:
        dict, all lineage information under summary base directory according to
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
        >>>     'lineage_type': 'model'
        >>> }
        >>> summary_lineage = filter_summary_lineage(summary_base_dir)
        >>> summary_lineage_filter = filter_summary_lineage(summary_base_dir, search_condition)
    """
    try:
        summary_base_dir = validate_path(summary_base_dir)
    except (LineageParamValueError, LineageDirNotExistError) as error:
        log.error(str(error))
        log.exception(error)
        raise LineageParamSummaryPathError(str(error.message))

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

    summary_path = SummaryPathParser.get_latest_lineage_summaries(summary_base_dir)
    if not summary_path:
        log.error('There is no summary log file under summary_base_dir.')
        raise LineageFileNotFoundError(
            'There is no summary log file under summary_base_dir.'
        )

    try:
        result = Querier(summary_path).filter_summary_lineage(
            condition=search_condition
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

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
"""The converter between proto format event of lineage and dict."""
import time

from mindinsight.datavisual.proto_files.mindinsight_lineage_pb2 import LineageEvent
from mindinsight.lineagemgr.common.exceptions.exceptions import LineageParamTypeError
from mindinsight.lineagemgr.common.log import logger as log


def package_dataset_graph(graph):
    """
    Package dataset graph.

    Args:
        graph (dict): Dataset graph.

    Returns:
        LineageEvent, the proto message event contains dataset graph.
    """
    dataset_graph_event = LineageEvent()
    dataset_graph_event.wall_time = time.time()

    dataset_graph = dataset_graph_event.dataset_graph
    if "children" in graph:
        children = graph.pop("children")
        if children:
            _package_children(children=children, message=dataset_graph)
        _package_current_dataset(operation=graph, message=dataset_graph)

    return dataset_graph_event


def _package_children(children, message):
    """
    Package children in dataset operation.

    Args:
        children (list[dict]): Child operations.
        message (DatasetGraph): Children proto message.
    """
    for child in children:
        if child:
            child_graph_message = getattr(message, "children").add()
            grandson = child.pop("children")
            if grandson:
                _package_children(children=grandson, message=child_graph_message)
            # package other parameters
            _package_current_dataset(operation=child, message=child_graph_message)


def _package_current_dataset(operation, message):
    """
    Package operation parameters in event message.

    Args:
        operation (dict): Operation dict.
        message (Operation): Operation proto message.
    """
    for key, value in operation.items():
        if value and key == "operations":
            for operator in value:
                _package_enhancement_operation(
                    operator,
                    message.operations.add()
                )
        elif value and key == "sampler":
            _package_enhancement_operation(
                value,
                message.sampler
            )
        else:
            _package_parameter(key, value, message.parameter)


def _package_enhancement_operation(operation, message):
    """
    Package enhancement operation in MapDataset.

    Args:
        operation (dict): Enhancement operation.
        message (Operation): Enhancement operation proto message.
    """
    for key, value in operation.items():
        if isinstance(value, list):
            if all(isinstance(ele, int) for ele in value):
                message.size.extend(value)
            else:
                message.weights.extend(value)
        else:
            _package_parameter(key, value, message.operationParam)


def _package_parameter(key, value, message):
    """
    Package parameters in operation.

    Args:
        key (str): Operation name.
        value (Union[str, bool, int, float, list, None]): Operation args.
        message (OperationParameter): Operation proto message.
    """
    if isinstance(value, str):
        message.mapStr[key] = value
    elif isinstance(value, bool):
        message.mapBool[key] = value
    elif isinstance(value, int):
        message.mapInt[key] = value
    elif isinstance(value, float):
        message.mapDouble[key] = value
    elif isinstance(value, list) and key != "operations":
        if value:
            replace_value_list = list(map(lambda x: "" if x is None else x, value))
            message.mapStrList[key].strValue.extend(replace_value_list)
    elif value is None:
        message.mapStr[key] = "None"
    else:
        error_msg = "Parameter {} is not supported " \
                    "in event package.".format(key)
        log.error(error_msg)
        raise LineageParamTypeError(error_msg)


def organize_graph(graph_message):
    """
    Convert a dataset graph to its dict format.

    Args:
        graph_message (DatasetGraph): Graph event message.

    Returns:
        dict, dataset graph.
    """
    result = {}
    # update current dataset graph dict
    result.update(_organize_current_dataset(
        parameter=getattr(graph_message, 'parameter'),
        operations=getattr(graph_message, 'operations'),
        sampler=getattr(graph_message, 'sampler')
    ))
    # update children dataset graph dict
    result.update(
        _organize_children(getattr(graph_message, 'children'))
    )

    return result


def _organize_children(children_message):
    """
    Convert children message to its dict format.

    Args:
        children_message (list[DatasetGraph]): Children message.

    Returns:
        dict, children dict of dataset graph.
    """
    children_list = []
    children_dict = {'children': children_list}
    if children_message:
        for child_event in children_message:
            child_dict = {}
            # update current dataset to child
            child_dict.update(
                _organize_current_dataset(
                    parameter=getattr(child_event, 'parameter'),
                    operations=getattr(child_event, 'operations'),
                    sampler=getattr(child_event, 'sampler')
                )
            )
            # update child's children
            child_dict.update(
                _organize_children(getattr(child_event, 'children'))
            )
            children_list.append(child_dict)
        children_dict['children'] = children_list

    return children_dict


def _organize_current_dataset(parameter, operations, sampler):
    """
    Convert current dataset message to its dict format.

    Note:
        Current dataset message include parameter, operations,
        sampler message of dataset graph event.

    Args:
        parameter (OperationParameter): Parameter message.
        operations (Operation): Operations message.
        sampler (Operation): Sampler message.

    Returns:
        dict, current dataset.
    """
    current_dataset = {}
    if parameter:
        current_dataset.update(
            _organize_parameter(parameter)
        )
    if operations:
        operation_list = []
        for operation in operations:
            operation_list.append(
                _organize_operation(operation)
            )
        current_dataset.update(
            {'operations': operation_list}
        )
    if sampler:
        if _organize_operation(sampler):
            current_dataset.update({
                'sampler':
                    _organize_operation(sampler)
            })
    return current_dataset


def _organize_operation(operation):
    """
    Convert operation message to its dict format.

    Args:
        operation (Operation): Operation message.

    Returns:
        dict, operation.
    """
    operation_dict = {}
    operation_dict.update(_organize_parameter(getattr(operation, 'operationParam')))
    tmp_list = []
    repeated_keys = ['size', 'weights']
    for key in repeated_keys:
        for str_ele in getattr(operation, key):
            tmp_list.append(str_ele)
            dict()
        if tmp_list:
            operation_dict.update({key: tmp_list})
    return operation_dict


def _organize_parameter(parameter):
    """
    Convert operation parameter message to its dict format.

    Args:
        parameter (OperationParameter): Operation parameter message.

    Returns:
        dict, operation parameter.
    """
    parameter_result = dict()
    parameter_keys = [
        'mapStr',
        'mapBool',
        'mapInt',
        'mapDouble',
    ]
    for parameter_key in parameter_keys:
        base_attr = getattr(parameter, parameter_key)
        parameter_value = dict(base_attr)
        # convert str 'None' to None
        for key, value in parameter_value.items():
            if value == 'None':
                parameter_value[key] = None
        parameter_result.update(parameter_value)
    # drop `mapStrList` and `strValue` keys in result parameter
    str_list_para = dict(getattr(parameter, 'mapStrList'))
    result_str_list_para = dict()
    for key, value in str_list_para.items():
        str_list_para_list = list()
        for str_ele in getattr(value, 'strValue'):
            str_list_para_list.append(str_ele)
        str_list_para_list = list(map(lambda x: None if x == '' else x, str_list_para_list))
        result_str_list_para[key] = str_list_para_list
    parameter_result.update(result_str_list_para)

    return parameter_result


def package_user_defined_info(user_dict):
    """
    Package user defined info.

    Args:
        user_dict(dict): User defined info dict.

    Returns:
        LineageEvent, the proto message event contains user defined info.

    """
    user_event = LineageEvent()
    user_event.wall_time = time.time()
    user_defined_info = user_event.user_defined_info
    _package_user_defined_info(user_dict, user_defined_info)

    return user_event


def _package_user_defined_info(user_defined_dict, user_defined_message):
    """
    Setting attribute in user defined proto message.

    Args:
        user_defined_dict (dict): User define info dict.
        user_defined_message (LineageEvent): Proto message of user defined info.

    Raises:
        LineageParamValueError: When the value is out of range.
        LineageParamTypeError: When given a type not support yet.
    """
    for key, value in user_defined_dict.items():
        if not isinstance(key, str):
            error_msg = f"Invalid key type in user defined info. The {key}'s type" \
                        f"'{type(key).__name__}' is not supported. It should be str."
            log.error(error_msg)

        if isinstance(value, int):
            attr_name = "map_int32"
        elif isinstance(value, float):
            attr_name = "map_double"
        elif isinstance(value, str):
            attr_name = "map_str"
        else:
            attr_name = "attr_name"

        add_user_defined_info = user_defined_message.user_info.add()
        try:
            getattr(add_user_defined_info, attr_name)[key] = value
        except AttributeError:
            error_msg = f"Invalid value type in user defined info. The {value}'s type" \
                        f"'{type(value).__name__}' is not supported. It should be float, int or str."
            log.error(error_msg)

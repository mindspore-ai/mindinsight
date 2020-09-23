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

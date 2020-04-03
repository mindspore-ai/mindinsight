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
"""Define a validation class which contain all check methods of datavisual module."""
from numbers import Number
from mindinsight.utils.exceptions import ParamValueError
from mindinsight.utils.exceptions import ParamMissError
from mindinsight.datavisual.common.exceptions import PluginNotAvailableError
from mindinsight.datavisual.common.enums import PluginNameEnum
from mindinsight.datavisual.utils.tools import to_int


class Validation:
    """Validation class, define all check methods."""

    @classmethod
    def check_offset(cls, offset, default_value=0):
        """
        Check offset parameter, it must be greater or equal 0.

        Args:
            offset (Union[str, int]): Value can be string number or int.
            default_value (int): Default value for checked offset. Default: 0.

        Returns:
            int, offset.
        """

        if offset is None:
            return default_value
        offset = to_int(offset, 'offset')
        if offset < 0:
            raise ParamValueError("'offset' should be greater than or equal to 0.")
        return offset

    @classmethod
    def check_limit(cls, limit, min_value=1, max_value=1000, default_value=100):
        """
        Check limit parameter, it should between min_value and max_value.

        Args:
            limit (Union[str, int]): Value can be string number or int.
            min_value (int): Limit should greater or equal this value. Default: 1.
            max_value (int): Limit should less or equal this value. Default: 1000.
            default_value (int): Default value for limit. Default: 100.

        Returns:
            int, limit.
        """

        if limit is None:
            return default_value

        limit = to_int(limit, 'limit')
        if limit < min_value or limit > max_value:
            raise ParamValueError("'limit' should in [{}, {}].".format(min_value, max_value))
        return limit

    @classmethod
    def check_param_empty(cls, **kwargs):
        """
        Check param.

        Args:
            kwargs (Any): Check if arg is truthy.

        Raises:
            ParamMissError: When param missing.
        """
        for key, value in kwargs.items():
            # When value is 0, 0.0 or False, it is not empty.
            if isinstance(value, Number):
                continue

            if not value:
                raise ParamMissError(key)

    @classmethod
    def check_plugin_name(cls, plugin_name):
        """
        Check plugin name.

        Args:
            plugin_name (str): The plugin name.

        Raises:
            PluginNotAvailableError: When plugin name is not valid.
        """
        plugin_name_list = PluginNameEnum.list_members()
        if plugin_name not in plugin_name_list:
            raise PluginNotAvailableError(f"'plugin_name' only can be one of {plugin_name_list}")

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
"""The analyser factory."""
import threading

from mindinsight.profiler import analyser as analyser_module
from mindinsight.profiler.common.exceptions.exceptions import \
    ProfilerAnalyserNotExistException


class AnalyserFactory:
    """
    The analyser factory is used to create analyser special instance.

    Depending on the analyser type, different analyzers can be created. Users
    can use the created analyser to query and analyse profiling data, such as
    operator information, step trace data and so on.

    Examples:
        >>> analyser = AnalyserFactory.instance().get_analyser(
        >>>     'aicore_type', '/path/to/profiling/dir', '0'
        >>> )
    """
    _lock = threading.Lock()
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    @classmethod
    def instance(cls):
        """The factory instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_analyser(self, analyser_type, *args):
        """
        Get the specified analyser according to the analyser type.

        Args:
            analyser_type (str): The analyser type.
            args (list): The parameters required for the specific analyser class.

        Returns:
            BaseAnalyser, the specified analyser instance.

        Raises:
            ProfilerAnalyserNotExistException: If the analyser type does not exist.
        """
        subnames = analyser_type.split('_')
        analyser_class_name = ''.join([name.capitalize() for name in subnames])
        analyser_class_name += 'Analyser'

        analyser_sub_modules = dir(analyser_module)
        for sub_module in analyser_sub_modules:
            if sub_module.endswith('analyser') and sub_module != 'base_analyser':
                analyser_sub_module = getattr(analyser_module, sub_module)
                if hasattr(analyser_sub_module, analyser_class_name):
                    return getattr(analyser_sub_module, analyser_class_name)(*args)
        raise ProfilerAnalyserNotExistException(analyser_type)

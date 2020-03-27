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
"""log operations module."""
import json
import os
import time

from tests.ut.datavisual.utils.log_generators.graph_log_generator import GraphLogGenerator
from tests.ut.datavisual.utils.log_generators.images_log_generator import ImagesLogGenerator
from tests.ut.datavisual.utils.log_generators.scalars_log_generator import ScalarsLogGenerator

from mindinsight.datavisual.common.enums import PluginNameEnum

log_generators = {
    PluginNameEnum.GRAPH.value: GraphLogGenerator(),
    PluginNameEnum.IMAGE.value: ImagesLogGenerator(),
    PluginNameEnum.SCALAR.value: ScalarsLogGenerator()
}


class LogOperations:
    """Log Operations class."""

    @staticmethod
    def generate_log(plugin_name, log_dir, log_settings, valid=True):
        """
        Generate log.

        Args:
            plugin_name (str): Plugin name, contains 'graph', 'image', and 'scalar'.
            log_dir (str): Log path to write log.
            log_settings (dict): Info about the log, e.g.:
                {
                    current_time (int): Timestamp in summary file name, not necessary.
                    graph_base_path (str): Path of graph_bas.json, necessary for `graph`.
                    steps (list[int]): Steps for `image` and `scalar`, default is [1].
                    tag (str): Tag name, default is 'default_tag'.
                }
            valid (bool): If true, summary name will be valid.

        Returns:
            str, Summary log path.


        """
        current_time = log_settings.get('time', int(time.time()))
        current_time = int(current_time)

        log_generator = log_generators.get(plugin_name)
        if valid:
            temp_path = os.path.join(log_dir, '%s.%s' % ('test.summary', str(current_time)))
        else:
            temp_path = os.path.join(log_dir, '%s.%s' % ('test.invalid', str(current_time)))

        if plugin_name == PluginNameEnum.GRAPH.value:
            graph_base_path = log_settings.get('graph_base_path')
            with open(graph_base_path, 'r') as load_f:
                graph_dict = json.load(load_f)

            graph_dict = log_generator.generate_log(temp_path, graph_dict)
            return temp_path, graph_dict

        steps_list = log_settings.get('steps', [1])
        tag_name = log_settings.get('tag', 'default_tag')
        metadata, values = log_generator.generate_log(temp_path, steps_list, tag_name)
        return temp_path, metadata, values

    @staticmethod
    def get_log_generator(plugin_name):
        """Get log generator."""
        return log_generators.get(plugin_name)

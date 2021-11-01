# Copyright 2019-2021 Huawei Technologies Co., Ltd
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
"""
Log operations.
"""
import json
import os
import time

from mindinsight.datavisual.common.enums import PluginNameEnum

from .log_generators.graph_log_generator import GraphLogGenerator
from .log_generators.images_log_generator import ImagesLogGenerator
from .log_generators.scalars_log_generator import ScalarsLogGenerator
from .log_generators.histogram_log_generator import HistogramLogGenerator
from .log_generators.tensor_log_generator import TensorLogGenerator
from .log_generators.landscape_log_generator import LandscapeLogGenerator

log_generators = {
    PluginNameEnum.GRAPH.value: GraphLogGenerator(),
    PluginNameEnum.IMAGE.value: ImagesLogGenerator(),
    PluginNameEnum.SCALAR.value: ScalarsLogGenerator(),
    PluginNameEnum.HISTOGRAM.value: HistogramLogGenerator(),
    PluginNameEnum.TENSOR.value: TensorLogGenerator(),
    PluginNameEnum.LANDSCAPE.value: LandscapeLogGenerator()
}


class LogOperations:
    """Log Operations."""

    def __init__(self):
        self._step_num = 3
        self._tag_num = 2
        self._time_count = 0
        self._graph_base_path = os.path.join(os.path.dirname(__file__), "log_generators", "graph_base.json")

    def _get_steps(self):
        """Get steps."""
        return range(self._step_num)

    def _get_tags(self):
        """Get tags."""
        return ["%s%d" % ("tag_name_", i) for i in range(self._tag_num)]

    def create_summary(self, log_dir, steps_list, tag_name_list):
        """Create summary in log_dir."""
        metadata_dict = dict()
        timestamp = time.time() + self._time_count
        file_path = os.path.join(log_dir, f'test.summary.{int(timestamp)}')

        metadata_dict.update({"plugins": dict()})
        metadata_dict.update({"metadata": dict()})
        metadata_dict.update({"actual_values": dict()})
        for plugin_name in PluginNameEnum.list_members():
            metadata_dict["plugins"].update({plugin_name: list()})
            log_generator = log_generators.get(plugin_name)
            if plugin_name == PluginNameEnum.GRAPH.value:
                with open(self._graph_base_path, 'r') as load_f:
                    graph_dict = json.load(load_f)
                values = log_generator.generate_log(file_path, graph_dict)
                metadata_dict["actual_values"].update({plugin_name: values})
                metadata_dict["plugins"][plugin_name].append("UUID str")
            else:
                for tag_name in tag_name_list:
                    metadata, values = log_generator.generate_log(file_path, steps_list, tag_name)
                    full_tag_name = f'{tag_name}/{plugin_name}'
                    metadata_dict["metadata"].update({full_tag_name: metadata})
                    metadata_dict["plugins"][plugin_name].append(full_tag_name)

                    if plugin_name == PluginNameEnum.IMAGE.value:
                        metadata_dict["actual_values"].update({full_tag_name: values})

        os.utime(file_path, (timestamp, timestamp))
        self._time_count += 1
        return metadata_dict

    def create_summary_logs(self, summary_base_dir, summary_dir_num, dir_prefix, start_index=0):
        """Create summary logs in summary_base_dir."""
        summary_metadata = dict()
        steps_list = self._get_steps()
        tag_name_list = self._get_tags()
        for i in range(start_index, summary_dir_num + start_index):
            log_dir = os.path.join(summary_base_dir, f'{dir_prefix}{i}')
            os.makedirs(log_dir)
            train_id = log_dir.replace(summary_base_dir, ".")

            metadata_dict = self.create_summary(log_dir, steps_list, tag_name_list)

            summary_metadata.update({train_id: metadata_dict})
        return summary_metadata

    def create_multiple_logs(self, summary_base_dir, dir_name, log_nums):
        """Create multiple logs in summary_base_dir."""
        metadata_dict = None
        steps_list = self._get_steps()
        tag_name_list = self._get_tags()
        log_dir = os.path.join(summary_base_dir, dir_name)
        os.makedirs(log_dir)
        train_id = log_dir.replace(summary_base_dir, ".")
        for _ in range(log_nums):
            metadata_dict = self.create_summary(log_dir, steps_list, tag_name_list)

        return {train_id: metadata_dict}

    def create_reservoir_log(self, summary_base_dir, dir_name, step_num):
        """Create reservoir log in summary_base_dir."""
        steps_list = range(step_num)
        tag_name_list = self._get_tags()
        log_dir = os.path.join(summary_base_dir, dir_name)
        os.makedirs(log_dir)
        train_id = log_dir.replace(summary_base_dir, ".")
        metadata_dict = self.create_summary(log_dir, steps_list, tag_name_list)

        return {train_id: metadata_dict}

    def generate_log(self, plugin_name, log_dir, log_settings=None, valid=True):
        """
        Generate log for ut.

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
        if log_settings is None:
            log_settings = dict()
        current_time = log_settings.get('time', int(time.time()))
        current_time = int(current_time)

        log_generator = log_generators.get(plugin_name)
        if valid:
            temp_path = os.path.join(log_dir, '%s.%s' % ('test.summary', str(current_time)))
        else:
            temp_path = os.path.join(log_dir, '%s.%s' % ('test.invalid', str(current_time)))

        if plugin_name == PluginNameEnum.GRAPH.value:
            with open(self._graph_base_path, 'r') as load_f:
                graph_dict = json.load(load_f)

            graph_dict = log_generator.generate_log(temp_path, graph_dict)
            return temp_path, graph_dict, None

        steps_list = log_settings.get('steps', [1])
        tag_name = log_settings.get('tag', 'default_tag')
        metadata, values = log_generator.generate_log(temp_path, steps_list, tag_name)
        return temp_path, metadata, values

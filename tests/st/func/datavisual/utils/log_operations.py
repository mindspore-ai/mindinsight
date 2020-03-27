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
"""
Log operations.
"""
import json
import os
import time

from tests.st.func.datavisual.constants import SUMMARY_PREFIX
from tests.st.func.datavisual.utils.log_generators.graph_log_generator import GraphLogGenerator
from tests.st.func.datavisual.utils.log_generators.images_log_generator import ImagesLogGenerator
from tests.st.func.datavisual.utils.log_generators.scalars_log_generator import ScalarsLogGenerator

from mindinsight.datavisual.common.enums import PluginNameEnum

log_generators = {
    PluginNameEnum.GRAPH.value: GraphLogGenerator(),
    PluginNameEnum.IMAGE.value: ImagesLogGenerator(),
    PluginNameEnum.SCALAR.value: ScalarsLogGenerator()
}


class LogOperations:
    """Log Operations."""
    def __init__(self):
        self._step_num = 3
        self._tag_num = 2
        self._time_count = 0

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
                graph_base_path = os.path.join(os.path.dirname(__file__),
                                               os.pardir, "utils", "log_generators", "graph_base.json")
                with open(graph_base_path, 'r') as load_f:
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

    def create_summary_logs(self, summary_base_dir, summary_dir_num, start_index=0):
        """Create summary logs in summary_base_dir."""
        summary_metadata = dict()
        steps_list = self._get_steps()
        tag_name_list = self._get_tags()
        for i in range(start_index, summary_dir_num + start_index):
            log_dir = os.path.join(summary_base_dir, f'{SUMMARY_PREFIX}{i}')
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

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
"""The Timeline Analyser."""
import json
import os

from mindinsight.profiler.analyser.base_analyser import BaseAnalyser
from mindinsight.profiler.common.exceptions.exceptions import ProfilerIOException
from mindinsight.profiler.common.log import logger
from mindinsight.profiler.common.validator.validate_path import validate_and_normalize_path
from mindinsight.utils.exceptions import ParamValueError
from mindinsight.profiler.analyser.timeline_processor import TimelineService


class TimelineAnalyser(BaseAnalyser):
    """
    Analyse timeline data from file.
    """
    _ascend_display_filename = 'ascend_timeline_display_{}.json'
    _gpu_display_filename = 'gpu_timeline_display_{}.json'
    _ascend_timeline_summary_filename = 'ascend_timeline_summary_{}.json'
    _gpu_timeline_summary_filename = 'gpu_timeline_summary_{}.json'

    def _load(self):
        """Load data according to the parsed profiling files."""

    def _filter(self, filter_condition):
        """
        Filter the profiling data according to the filter condition.

        Args:
            filter_condition (dict): The filter condition.
        """

    def get_display_timeline(self, device_type, scope_name_num):
        """
        Get timeline data for UI display.

        Returns:
            json, the content of timeline data.
        """
        if device_type == "ascend":
            display_filename = self._ascend_display_filename.format(self._device_id)
        elif device_type == "gpu":
            display_filename = self._gpu_display_filename.format(self._device_id)
        else:
            logger.info('device type should be ascend or gpu. Please check the device type.')
            raise ParamValueError("Invalid device_type.")
        file_path = os.path.join(self._profiling_dir, display_filename)
        file_path = validate_and_normalize_path(
            file_path, raise_key='Invalid timeline json path.'
        )

        timeline = []
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f_obj:
                    timeline = json.load(f_obj)
                    for idx, time_item in enumerate(timeline):
                        if time_item.get("tid") == 100001 and \
                                time_item["ph"] != "M" and \
                                int(time_item["scope_level"]) >= int(scope_name_num):
                            timeline[idx] = None
                    timeline = list(filter(lambda x: x, timeline))
            except (IOError, OSError, json.JSONDecodeError) as err:
                logger.error('Error occurred when read timeline display file: %s', err)
                raise ProfilerIOException()
        else:
            logger.info('No timeline file. Please check the output path.')

        return timeline

    def get_timeline_summary(self, device_type):
        """
        Get timeline summary information for UI display.

        Returns:
            json, the content of timeline summary information.
        """
        if device_type == "ascend":
            summary_filename = self._ascend_timeline_summary_filename.format(self._device_id)
        elif device_type == "gpu":
            summary_filename = self._gpu_timeline_summary_filename.format(self._device_id)
        else:
            logger.info('device type should be ascend or gpu. Please check the device type.')
            raise ParamValueError("Invalid device_type.")
        file_path = os.path.join(self._profiling_dir, summary_filename)
        file_path = validate_and_normalize_path(
            file_path, raise_key='Invalid timeline summary path.'
        )

        timeline_summary = {}
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f_obj:
                    timeline_summary = json.load(f_obj)
            except (IOError, OSError, json.JSONDecodeError) as err:
                logger.error('Error occurred when read timeline summary file: %s', err)
                raise ProfilerIOException()
        else:
            logger.info('No timeline summary file. Please check the output path.')

        timeline_summary.setdefault("max_scope_name_num", 0)

        return timeline_summary

    def get_marey_timeline(self, step, device_list):
        operator_time_maps, min_time, max_time, stage_data = TimelineService(self._profiling_dir,
                                                                             device_list).get_ops_by_step(step)
        ret = {"maps": operator_time_maps, "minT": min_time, "maxT": max_time, "stage_data": stage_data}
        return ret

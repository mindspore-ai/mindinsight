# Copyright 2022 Huawei Technologies Co., Ltd
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
"""The Timeline Processor for Marey's Graph."""
import os
import re
import json
import collections
from mindinsight.profiler.common.util import analyse_device_list_from_profiler_dir
from mindinsight.profiler.common.validator.validate_path import validate_and_normalize_path


class TimelineService:
    """
    Analyse timeline data for marey's graph from file.
    """
    _ascend_display_filename = 'ascend_timeline_display_{}.json'
    _gpu_display_filename = 'gpu_timeline_display_{}.json'

    def __init__(self, path, device_list):
        self._display_timeline = True
        self.__read_data(path, device_list)
        self.__align_time()

    def get_ops_by_step(self, step):
        """
        Get the operators of the given step.

        Args:
            step (int): The current step.
        """
        min_time = float('inf')
        max_time = 0
        operator_time_maps = {}

        for device_name, cur_op_nodes in self.op_nodes.items():
            step_start = 0.0
            step_end = float('inf')
            for item in self.all_data.get(device_name):
                if item['name'] == step:
                    step_start = float(item['ts'])
                    step_end = step_start + float(item['dur'])
                    break

            operator_time_maps[device_name] = {}
            for item in cur_op_nodes:
                ts = float(item['ts'])
                dur = float(item['dur'])
                if step_start < ts < step_end or dur < step_start < ts + dur:
                    operator_time_maps.get(device_name)[item['name']] = {"st": ts,
                                                                         "ed": ts + dur,
                                                                         "dur": dur}
                    max_time = max(max_time, ts + dur)
                    min_time = min(min_time, ts)

        def cmp(a):
            return int(re.search(r'\d+', a[0]).group())

        a = 0
        stage_data = {}
        for device_names in sorted(self.stage_info, key=cmp):
            stage_name = 'stage' + str(a)
            a += 1
            data = {}
            for device_name in device_names:
                nodes = operator_time_maps.get(device_name)
                for node_name, node in nodes.items():
                    if node_name in data:
                        aggre_node = data.get(node_name)
                        aggre_node['st_max'] = max(aggre_node.get('st_max'), node.get('st'))
                        aggre_node['st_min'] = min(aggre_node.get('st_min'), node.get('st'))
                        aggre_node['ed_max'] = max(aggre_node.get('ed_max'), node.get('ed'))
                        aggre_node['ed_min'] = min(aggre_node.get('ed_min'), node.get('ed'))
                        aggre_node['st_avg'] = (node['st'] + aggre_node['st_avg'] *
                                                aggre_node['n']) / (aggre_node['n'] + 1)
                        aggre_node['ed_avg'] = (node['ed'] + aggre_node['ed_avg'] *
                                                aggre_node['n']) / (aggre_node['n'] + 1)
                        aggre_node['n'] += 1
                    else:
                        data[node_name] = {
                            'st_max': node['st'],
                            'st_min': node['st'],
                            'st_avg': node['st'],
                            'ed_max': node['ed'],
                            'ed_min': node['ed'],
                            'ed_avg': node['ed'],
                            'n': 1
                        }
            stage_data[stage_name] = {"data": data, "devices": device_names}
        TimelineData = collections.namedtuple('TimelineData',
                                              ['operator_time_maps', 'min_time', 'max_time', 'stage_data'])
        timeline_data = TimelineData(operator_time_maps, min_time, max_time, stage_data)
        return timeline_data

    def __read_data(self, path, device_list):
        """
        Get timeline data.

        Args:
            path (string): The current train log directory.
        """
        if device_list is None:
            device_list, _, _ = analyse_device_list_from_profiler_dir(path)
            sorted_device_list = sorted(device_list, key=int)
            device_list = sorted_device_list[:8]
        else:
            device_list = device_list.split(",")

        self.all_data = {}
        self.op_nodes = {}
        for device in device_list:
            display_filename = self._ascend_display_filename.format(device)
            device_entry = "device" + device
            file_path = os.path.join(path, display_filename)
            file_path = validate_and_normalize_path(
                file_path, raise_key='Invalid timeline display file path.'
            )
            if not os.path.exists(file_path):
                continue
            with open(file_path, "r") as fp:
                j_data = json.loads(fp.read())
                self.all_data[device_entry] = j_data
        for device_name, cur_data in self.all_data.items():
            self.op_nodes[device_name] = list(filter(_filt_op, cur_data))

    def __align_time(self):
        """Align timeline on each device."""
        self.stage_info = []
        if not self._display_timeline:
            return
        visited = set()
        self.align_info = {}
        one_step_op = self.__get_raw_ops_by_step("1")
        stages = []
        for device_name, cur_one_step_op in one_step_op.items():
            if device_name in visited:
                continue
            visited.add(device_name)
            stages.append(device_name)
            self.align_info[device_name] = 0
            min_all_reduce = ""
            minn = float('inf')
            for item in cur_one_step_op:
                if 'name' in item and 'AllReduce' in item['name']:
                    ts = float(item['ts'])
                    if ts < minn:
                        minn = ts
                        min_all_reduce = item
            if min_all_reduce == '':
                continue
            for device_name2 in self.all_data:
                if device_name2 in visited:
                    continue
                for item in one_step_op.get(device_name2):
                    if item['name'] == min_all_reduce['name']:
                        visited.add(device_name2)
                        min_all_reduce['ed'] = float(min_all_reduce['ts']) + float(min_all_reduce['dur'])
                        item['ed'] = float(item['ts']) + float(item['dur'])
                        self.align_info[device_name2] = min_all_reduce['ed'] - item['ed']
                        stages.append(device_name2)
                        break
            self.stage_info.append(stages)
            stages = []
        if stages:
            self.stage_info.append(stages)
        for device_name, cur_data in self.all_data.items():
            for item in cur_data:
                if 'ts' in item:
                    item['ts'] = float(item['ts']) + self.align_info.get(device_name)
        self.stage_device_map = {}

        def cmp(a):
            return int(re.search(r'\d+', a[0]).group())

        a = 0
        for device_names in sorted(self.stage_info, key=cmp):
            stage_name = 'stage' + str(a)
            a += 1
            self.stage_device_map[stage_name] = device_names

    def __get_raw_ops_by_step(self, step):
        """
        Get the raw operators of the given step.

        Args:
            step (int): The current step.
        """
        ret = {}
        for device_name, cur_op_nodes in self.op_nodes.items():
            ret[device_name] = []
            step_start = 0.0
            step_end = float('inf')
            for item in self.all_data.get(device_name):
                if item['name'] == step:
                    step_start = float(item['ts'])
                    step_end = step_start + float(item['dur'])
                    break
            for item in cur_op_nodes:
                if step_start < float(item['ts']) < step_end:
                    ret.get(device_name).append(item)
        return ret

    def __get_scopes_by_step(self, step):
        """
        Get the name scopes of the given step.

        Args:
            step (int): The current step.
        """
        ret = {}
        for device_name, cur_data in self.all_data.items():
            ret[device_name] = []
            step_start = 0.0
            step_end = float('inf')
            for item in cur_data:
                if item['name'] == step:
                    step_start = float(item['ts'])
                    step_end = step_start + float(item['dur'])
                    break
            for item in cur_data:
                if 'scope_level' in item:
                    if step_start < float(item['ts']) < step_end:
                        ret.get(device_name).append(item)
        return ret


def _filt_op(item):
    if 'AtomicAddrClean' in item['name'] or 'StreamSend' in item['name'] or 'StreamReceive' in item['name']:
        return False
    if 'tid' in item and '-op' in item['name'] and 'dur' in item and 'ts' in item:
        return True
    return False


def _find_scope(cur_scope_by_level, op):
    """Judge if op is in current scope."""
    for cur_scope in cur_scope_by_level:
        intervals = cur_scope_by_level[cur_scope]
        l = 0
        r = len(intervals) - 1
        ans = -1
        t = float(op['ts'])
        while l <= r:
            mid = (l + r) >> 1
            if intervals[mid][0] <= t:
                ans = max(ans, mid)
                l = mid + 1
            else:
                r = mid - 1
        if ans != -1 and intervals[ans][0] + intervals[ans][1] >= float(op['ts']) + float(op['dur']):
            return cur_scope, True
    return "", False

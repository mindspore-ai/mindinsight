# Copyright 2020-2023 Huawei Technologies Co., Ltd
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
import csv
import json
import os
import glob
import re
import time
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
from marshmallow import ValidationError

from mindinsight.profiler.analyser.base_analyser import BaseAnalyser
from mindinsight.profiler.common.log import logger


def get_diff_time(rank_id, prof_path):
    """
    Get difference time between ranks
    """
    profiler_info_file = os.path.join(prof_path, os.pardir, f'profiler_info_{rank_id}.json')
    if not os.path.exists(profiler_info_file):
        return Decimal(0).quantize(Decimal('0.000'))

    with open(profiler_info_file, 'r') as fr:
        diff_time = json.load(fr).get('diff_time', 0)

    return Decimal(diff_time).quantize(Decimal('0.000'))


def get_rank_id_from_info_json(pro_path):
    """
    Get rank id and device id from PROFXXX
    """
    info_json = ""
    rank_id = 0
    device_id = 0
    for root, _, files in os.walk(pro_path):
        for file in files:
            if "info.json." in file and ".done" not in file:
                info_json = os.path.join(root, file)
                break

    if info_json:
        with open(info_json, "r+") as f:
            info = json.load(f)
        rank_id = int(info.get('rank_id', rank_id))
        device_id = int(info.get('devices', device_id))

    if rank_id == -1:
        rank_id = 0

    return rank_id, device_id


def get_timeline_info(prof_dirs):
    """
    Get the newest prof dirs
    """
    # need get the newest dirs
    timeline_info = {}

    for prof_path in prof_dirs:
        rank_id, _ = get_rank_id_from_info_json(prof_path)
        ts_difference_us = get_diff_time(rank_id, prof_path)
        if rank_id is None:
            logger.warning('Could not find the rank id in %s, ignore this file.', prof_path)
            continue

        if rank_id not in timeline_info or (rank_id in timeline_info and prof_path > timeline_info.get(rank_id)[0]):
            prof_path = os.path.join(prof_path, 'mindstudio_profiler_output')
            timeline_info[rank_id] = (prof_path, ts_difference_us)

    return timeline_info


def get_job_dir(parent_path):
    job_path_list = glob.glob(fr'{parent_path}/PROF_*_*')
    return get_timeline_info(job_path_list)


def get_newest_file(file_list):
    '''
    Find the newest files
    :param file_list:
    :return:
    '''
    newest_file_list = []
    newest_timestamp = '0'
    for file_path in file_list:
        timestamp = file_path.split('.')[0].split('/')[-1].split('_')[-1]
        newest_timestamp = max(timestamp, newest_timestamp)

    for file_path in file_list:
        if file_path.split('.')[0].split('/')[-1].split('_')[-1] == newest_timestamp:
            newest_file_list.append(file_path)

    newest_file_list.sort()
    return newest_file_list


class MsprofTimelineAnalyser(BaseAnalyser):
    """
    Analyse timeline data from file.
    """

    def __init__(self, profiling_dir, device_id=None):
        super(MsprofTimelineAnalyser, self).__init__(profiling_dir, device_id)
        self.top_scope_name = ('Default', 'Gradients', 'recompute_Default')
        self.step_trace_index = 1
        self.cann_index = 2
        self.scope_index = 3
        self.ascend_hardware_index = 4
        self.hccl_index = 5
        self.cpu_index = 6
        self.overlap_index = 7

    def get_merged_timeline(self, rank_list, model_list, kind, merge_model=True, scope_name=False):
        """
        Get the merged timeline
        """

        # get all job path, like PROF_*
        sub_dirs = get_job_dir(self._profiling_dir)

        if rank_list:
            new_sub_dirs = {}
            for key, value in sub_dirs.items():
                if key in rank_list:
                    new_sub_dirs[key] = value
            sub_dirs = new_sub_dirs

        if not sub_dirs:
            logger.error('Could not found any rank from %s', rank_list)
            return []

        if kind == 'summary':
            start = time.time()
            summary_data = self._get_summary_timeline_data(sub_dirs, merge_model)
            logger.info("Summary timeline time consuming: %s", time.time() - start)
            return summary_data

        if kind == 'detail':
            start = time.time()
            detail_data = self._get_detail_timeline_data(sub_dirs, model_list, merge_model, scope_name)
            logger.info("Detail timeline time consuming: %s", time.time() - start)
            return detail_data
        return []

    def parse_cpu_timeline(self, file_list, rank_id, difference_ts, scope_name):
        """Load cpu operator data from file"""
        ms_to_us = 1e3
        ps_to_ns = 1e-3
        new_pid = int(f'{self.cpu_index}{rank_id}')
        process_list = [{"name": "process_name",
                         "pid": new_pid,
                         "args": {
                             "name": f"CPU OP Rank{rank_id}"
                         },
                         "ph": "M"
                         }, {"name": "process_sort_index", "pid": new_pid,
                             "args": {"sort_index": self.cpu_index}, "ph": "M"}
                        ]
        tid_set = set()
        thread_list = []
        new_timeline = []
        scope_data = []
        try:
            flags = os.O_RDONLY
            for file_path in file_list:
                with os.fdopen(os.open(file_path, flags, 0o400), 'r') as fr:
                    for line in fr:
                        op_list = line.strip().split(';')
                        op_full_name = op_list[0]
                        time_arr = op_list[-1]
                        time_arr = time_arr.split(" ")
                        for time_str in time_arr:
                            ts, dur, tid = time_str.split(",")
                            ts = Decimal(ts).quantize(Decimal('0.000')) * Decimal(ps_to_ns).quantize(Decimal('0.000'))

                            if scope_name and op_full_name and op_full_name.startswith(self.top_scope_name):
                                te = ts + Decimal(dur).quantize(Decimal('0.000'))
                                scope_data.append((op_full_name.split('/')[:-1], ts, te))

                            ts -= difference_ts

                            if int(tid) not in tid_set:
                                tid_set.add(int(tid))
                                thread_list.append({"name": "thread_name",
                                                    "pid": new_pid,
                                                    "tid": int(tid),
                                                    "ph": "M",
                                                    'args': {'name': f'thread {tid}'}
                                                    })

                            new_timeline.append({'name': op_list[0],
                                                 'pid': new_pid,
                                                 'tid': int(tid),
                                                 'ph': 'X',
                                                 'ts': str(ts),
                                                 'dur': float(dur) * ms_to_us,
                                                 'args':
                                                     {'type': op_list[1]}
                                                 })
                break

            return process_list + thread_list + new_timeline, scope_data

        except (ValidationError, IOError, OSError, json.JSONDecodeError) as err:
            logger.error('parse_cann_data failed! please theck. detail: %s', err)
            return []

    def get_option(self):
        """
        Get the option values
        """
        # get all job path, like PROF_*
        sub_dirs = get_job_dir(self._profiling_dir)
        rank_list = list(sub_dirs.keys())
        rank_list.sort()

        _, model_merged = self._get_models(sub_dirs)
        model_list = list(model_merged)
        model_list.sort()

        return {'rank_list': rank_list, 'model_list': model_list}

    def _load(self):
        """Load data according to the parsed profiling files."""

    def _filter(self, filter_condition):
        """
        Filter the profiling data according to the filter condition.

        Args:
            filter_condition (dict): The filter condition.
        """

    def _parse_overlap_analysis_data(self, file_list, rank_id, difference_ts):
        """
        parse overlap analysis data
        """
        try:
            flags = os.O_RDONLY
            raw_data = []
            for file_path in file_list:
                with os.fdopen(os.open(file_path, flags, 0o400), 'r') as fr:
                    raw_data.extend(json.load(fr))

            pid = None
            for event in raw_data:
                if event.get('name') == 'process_name' and event.get("ph") == "M" and \
                        event.get('args').get('name') == 'Overlap Analysis':
                    pid = event.get('pid')
                    break

            if not pid:
                logger.warning('Could not found process_name pid. method: _parse_overlap_analysis_data')
                return []

            new_events = []
            new_pid = int(f'{self.overlap_index}{rank_id}')
            for event in raw_data:
                if event.get('pid') != pid:
                    continue

                if event.get('name') == 'process_name' and event.get("ph") == "M":
                    event["args"]["name"] += f" Rank{rank_id}"

                if event.get('name') == 'process_sort_index' and event.get("ph") == "M":
                    event["args"]["sort_index"] = self.overlap_index

                event['pid'] = new_pid
                if event.get('ts'):
                    ts = Decimal(event.get('ts')).quantize(Decimal('0.000'))
                    ts += difference_ts
                    event['ts'] = str(ts)

                new_events.append(event)

            return new_events

        except (ValidationError, IOError, OSError, json.JSONDecodeError) as err:
            logger.error('parse_overlap_analysis_data failed! please theck. detail: %s', err)
            return []

    def _parse_step_trace_metadata(self, raw_data, model_list):
        """
        Get step trace by merge models
        """
        pattern1 = re.compile(r'Step Trace\(Model ID:(\d)+\)')
        pattern2 = re.compile(r'(\d)+')
        tid_mapper = {}
        pid = None
        for event in raw_data:
            if event.get("ph") != "M":
                continue

            if event.get('name') == 'process_name':
                pid = event.get('pid')
                continue

            if event.get('name') == 'thread_name':
                arg_name = event.get('args', {}).get('name')
                arg_name = re.search(pattern1, arg_name)
                if not arg_name:
                    continue
                model_id = re.search(pattern2, arg_name.group())
                if not model_id:
                    continue
                model_id = model_id.group()
                tid = event.get('tid')
                if not model_list or int(model_id) in model_list:
                    tid_mapper[tid] = f'Model {model_id}'

        return tid_mapper, pid

    def _parse_step_trace_merge(self, old_pid, new_pid, rank_id, raw_data, tid_mapper, difference_ts):
        """merge step trace data"""
        new_events = [{
            "name": "process_name",
            "pid": new_pid,
            "args": {
                "name": f"Step Trace Rank{rank_id}"
            },
            "ph": "M"
        }, {
            "name": "process_sort_index",
            "pid": new_pid,
            "args": {
                "sort_index": self.step_trace_index
            },
            "ph": "M"
        }, {
            "name": "thread_name",
            "pid": new_pid,
            "tid": 0,
            "args": {
                "name": "iterations"
            },
            "ph": "M"
        }]

        for event in raw_data:
            arg_name = tid_mapper.get(event.get('tid'))
            if event.get('ph') == 'M' or event.get('pid') != old_pid or not arg_name:
                continue

            event_name = event.get('name').strip()
            if event.get('ph') == 'X' and event_name.startswith('Iteration') and len(
                    event_name.split(' ')) == 2:
                event['name'] = f"{arg_name} {event_name}"

            if event.get('ts'):
                ts = Decimal(event.get('ts')).quantize(Decimal('0.000'))
                ts -= difference_ts
                event['ts'] = str(ts)
            event['pid'] = new_pid
            event['tid'] = 0
            new_events.append(event)
        return new_events

    def _parse_step_trace_not_merge(self, old_pid, new_pid, rank_id, raw_data, difference_ts):
        """not merge step trace data"""
        new_events = []
        for event in raw_data:
            if event.get('pid') != old_pid:
                continue
            if event.get('name') == 'process_name' and event.get('ph') == 'M':
                event['args']['name'] = f"Step Trace Rank{rank_id}"
            elif event.get('name') == 'process_sort_index' and event.get('ph') == 'M':
                event['args']['sort_index'] = self.step_trace_index

            event['pid'] = new_pid
            if event.get('ts'):
                ts = Decimal(event.get('ts')).quantize(Decimal('0.000'))
                ts -= difference_ts
                event['ts'] = str(ts)
            new_events.append(event)
        return new_events

    def _parse_step_trace_data(self, file_list, rank_id, difference_ts, model_list, merge_model):
        """
        parse step trace data
        """
        try:
            flags = os.O_RDONLY
            raw_data = []
            for file_path in file_list:
                with os.fdopen(os.open(file_path, flags, 0o400), 'r') as fr:
                    raw_data.extend(json.load(fr))

            tid_mapper, pid = self._parse_step_trace_metadata(raw_data, model_list)
            if not pid:
                logger.error('Could not found process_name pid. method: _parse_step_trace_data')
                return []

            new_pid = int(f'{self.step_trace_index}{rank_id}')

            if merge_model:
                return self._parse_step_trace_merge(pid, new_pid, rank_id, raw_data, tid_mapper, difference_ts)

            return self._parse_step_trace_not_merge(pid, new_pid, rank_id, raw_data, difference_ts)

        except (ValidationError, IOError, OSError, json.JSONDecodeError) as err:
            logger.error('parse_step_trace_data failed! please theck. detail: %s', err)
            return []

    def _parse_msprof_metadata(self, new_pid_hardware, raw_data):
        """
        Get msprof by merge models
        """
        tid_mapper_hardware = {}
        pid_hardware = None
        pid_hccl = None
        pid_cann = None
        pid_overlap = None
        for event in raw_data:
            if event.get('name') == 'process_name' and event.get("ph") == "M" and \
                    event.get('args').get('name') == 'Ascend Hardware':
                pid_hardware = event.get('pid')

            elif event.get('name') == 'thread_name' and event.get("ph") == "M" and \
                    'Stream' in event.get('args').get('name'):
                event['pid'] = new_pid_hardware
                tid_mapper_hardware.update({event.get('tid'): event})

            elif event.get('name') == 'process_name' and event.get("ph") == "M" and \
                    event.get('args').get('name') == 'HCCL':
                pid_hccl = event.get('pid')

            elif event.get('name') == 'process_name' and event.get("ph") == "M" and \
                    event.get('args').get('name') == 'CANN':
                pid_cann = event.get('pid')

            elif event.get('name') == 'process_name' and event.get("ph") == "M" and \
                    event.get('args').get('name') == 'Overlap Analysis':
                pid_overlap = event.get('pid')

        result = (pid_hardware, tid_mapper_hardware, pid_hccl, pid_cann, pid_overlap)
        return result

    def _parse_msprof_raw_data(self, raw_data, difference_ts, tid_mapper_hardware, model_list, scope_name, **kwargs):
        """
        Parse the msprof raw data
        """

        new_events_hardware = []
        new_events_hccl = []
        new_events_cann = []
        new_events_overlap = []

        scope_data = []

        for event in raw_data:
            model_id = event.get('args', {}).get('Model Id')
            is_process = event.get('ph') == 'M' \
                         and (event.get('name') == 'process_name' or event.get('name') == 'process_sort_index')
            if is_process or (model_list and model_id not in model_list):
                continue

            op_full_name = event.get('name')
            if scope_name and op_full_name and op_full_name.startswith(self.top_scope_name):
                ts = Decimal(event.get('ts')).quantize(Decimal('0.000'))
                te = ts + Decimal(event.get('dur')).quantize(Decimal('0.000'))
                scope_data.append((op_full_name.split('/')[:-1], ts, te))

            if event.get('ts'):
                ts = Decimal(event.get('ts')).quantize(Decimal('0.000'))
                ts -= difference_ts
                event['ts'] = str(ts)

            if event.get('pid') == kwargs.get('pid_hardware') and event.get('ph') != 'M' \
                    and event.get('tid') in tid_mapper_hardware:
                event['pid'] = kwargs.get('new_pid_hardware')
                new_events_hardware.append(event)

            elif event.get('pid') == kwargs.get('pid_hccl'):
                event['pid'] = kwargs.get('new_pid_hccl')
                new_events_hccl.append(event)

            elif not model_list and event.get('pid') == kwargs.get('pid_cann'):
                event['pid'] = kwargs.get('new_pid_cann')
                new_events_cann.append(event)

            elif not model_list and event.get('pid') == kwargs.get('pid_overlap'):
                event['pid'] = kwargs.get('new_pid_overlap')
                new_events_overlap.append(event)

        return new_events_hardware + new_events_hccl + new_events_cann + new_events_overlap, scope_data

    def _parse_msprof_data(self, file_list, rank_id, difference_ts, model_list, scope_name):
        """
        parse ascend hardware and hccl and cann data
        """
        flags = os.O_RDONLY
        raw_data = []

        new_pid_hardware = int(f'{self.ascend_hardware_index}{rank_id}')
        new_pid_hccl = int(f'{self.hccl_index}{rank_id}')
        new_pid_cann = int(f'{self.cann_index}{rank_id}')
        new_pid_overlap = int(f'{self.overlap_index}{rank_id}')
        new_metadata = [
            {
                "name": "process_name",
                "pid": new_pid_hardware,
                "args": {
                    "name": f"Ascend Hardware Rank{rank_id}"
                },
                "ph": "M"
            }, {"name": "process_sort_index", "pid": new_pid_hardware,
                "args": {"sort_index": self.ascend_hardware_index}, "ph": "M"},
            {
                "name": "process_name",
                "pid": new_pid_hccl,
                "args": {
                    "name": f"HCCL Rank{rank_id}"
                },
                "ph": "M"
            }, {"name": "process_sort_index", "pid": new_pid_hccl,
                "args": {"sort_index": self.hccl_index}, "ph": "M"},
            {
                "name": "process_name",
                "pid": new_pid_cann,
                "args": {
                    "name": f"CANN Rank{rank_id}"
                },
                "ph": "M"
            }, {"name": "process_sort_index", "pid": new_pid_cann,
                "args": {"sort_index": self.cann_index}, "ph": "M"},
            {
                "name": "process_name",
                "pid": new_pid_overlap,
                "args": {
                    "name": f"Overlap Analysis Rank{rank_id}"
                },
                "ph": "M"
            }, {"name": "process_sort_index", "pid": new_pid_overlap,
                "args": {"sort_index": self.overlap_index}, "ph": "M"}
        ]

        try:
            for file_path in file_list:
                with os.fdopen(os.open(file_path, flags, 0o400), 'r') as fr:
                    raw_data.extend(json.load(fr))

            pid_hardware, tid_mapper_hardware, pid_hccl, pid_cann, pid_overlap \
                = self._parse_msprof_metadata(new_pid_hardware, raw_data)

            is_pid_valid = not pid_hardware and not pid_hccl and pid_cann and pid_overlap

            if is_pid_valid:
                logger.error('Could not found process_name pid. method: _parse_msprof_data')
                return []

            pid_dict = {'pid_hardware': pid_hardware, 'pid_hccl': pid_hccl,
                        'pid_cann': pid_cann, 'pid_overlap': pid_overlap,
                        'new_pid_hardware': new_pid_hardware, 'new_pid_hccl': new_pid_hccl,
                        'new_pid_cann': new_pid_cann, 'new_pid_overlap': new_pid_overlap}

            new_events, scope_data = self._parse_msprof_raw_data(raw_data, difference_ts, tid_mapper_hardware,
                                                                 model_list, scope_name, **pid_dict)
            return new_metadata + list(tid_mapper_hardware.values()) + new_events, scope_data

        except (ValidationError, IOError, OSError, json.JSONDecodeError) as err:
            logger.error('_parse_msprof_data failed! please theck. detail: %s', err)
            return []

    def _parse_scope_info(self, scope_data, rank_id, difference_ts):
        """parse scope layer"""
        if not scope_data:
            return []
        new_pid = int(f'{self.scope_index}{rank_id}')
        scope_data.sort(key=lambda x: x[1])
        process_list = [
            {"name": "process_name",
             "pid": new_pid,
             "args": {
                 "name": f"Scope Layer Rank{rank_id}"
             },
             "ph": "M"},
            {"name": "process_sort_index",
             "pid": new_pid,
             "args": {"sort_index": self.scope_index},
             "ph": "M"}
        ]

        new_events = []
        layer_stack = []
        for layer_name in scope_data[0][0]:
            layer_stack.append([layer_name, scope_data[0][1], scope_data[0][2]])

        for op in scope_data[1:]:
            if op[1] < layer_stack[0][2]:
                # 并行算子只保留前面的
                continue
            flag = True  # 判断上层是否合并， 上层不合并下层也不合并
            for layer_depth, layer_name in enumerate(op[0]):
                if layer_depth >= len(layer_stack):
                    layer_stack.append([layer_name, op[1], op[2]])
                else:
                    if layer_stack[layer_depth][0] == layer_name and flag:
                        layer_stack[layer_depth][2] = op[2]  # 合并
                    else:
                        ts = layer_stack[layer_depth][1]
                        ts -= difference_ts
                        new_events.append({
                            "name": layer_stack[layer_depth][0],
                            "pid": new_pid,
                            "tid": layer_depth,
                            "ph": "X",
                            "ts": str(ts),
                            "dur": float(layer_stack[layer_depth][2] - layer_stack[layer_depth][1])
                        })
                        layer_stack[layer_depth] = [layer_name, op[1], op[2]]
                        flag = False

        thread_list = []
        for index, layer in enumerate(layer_stack):
            thread_list.extend([{
                "name": "thread_name",
                "pid": new_pid,
                "tid": index,
                "args": {
                    "name": f"layer{index}"
                },
                "ph": "M"
            }, {
                "name": "thread_sort_index",
                "pid": new_pid,
                "tid": index,
                "args": {"sort_index": index},
                "ph": "M"
            }])
            if layer:
                ts = layer[1]
                ts -= difference_ts
                new_events.append({
                    "name": layer[0],
                    "pid": new_pid,
                    "tid": index,
                    "ph": "X",
                    "ts": str(ts),
                    "dur": float(layer[2] - layer[1])
                })

        return process_list + thread_list + new_events

    def _get_summary_timeline_data(self, sub_dirs, merge_model):
        """
        Get summary timeline
        Returns:
            json, the content of timeline data.
        """
        task_list = []
        timeline_data = []
        with ThreadPoolExecutor() as pool:
            for rank_id, (job_dir, difference_ts) in sub_dirs.items():

                # get step trace
                step_trace_file_name = fr'{job_dir}/step_trace_*.json'
                file_list = get_newest_file(glob.glob(step_trace_file_name))

                if not file_list:
                    logger.warning('Could not find step trace file in %s', job_dir)
                else:
                    task_list.append(pool.submit(self._parse_step_trace_data, file_list,
                                                 rank_id, difference_ts, None,
                                                 merge_model))

                # get overlap analysis
                overlap_file_name = fr'{job_dir}/msprof_*.json'
                file_list = get_newest_file(glob.glob(overlap_file_name))

                if not file_list:
                    logger.warning('Could not find overlap analysis file in %s', job_dir)
                else:
                    task_list.append(pool.submit(self._parse_overlap_analysis_data, file_list,
                                                 rank_id, difference_ts))

            all_done = list(range(len(task_list)))
            while all_done:
                for ind, t in enumerate(task_list):
                    if ind in all_done and t.done():
                        timeline_data.extend(t.result())
                        all_done.remove(ind)

        return timeline_data

    def _get_detail_timeline_data(self, sub_dirs, model_list, merge_model, scope_name):
        """
        Get detail timeline
        Returns:
            json, the content of timeline data.
        """

        timeline_data = []
        task_list = []

        _, model_merged = self._get_models(sub_dirs)
        model_list_all = list(model_merged)
        if model_list_all:
            model_list_all.sort()
        if model_list:
            model_list.sort()
        if model_list_all == model_list:
            model_list = None

        with ThreadPoolExecutor() as pool:
            for rank_id, (job_dir, difference_ts) in sub_dirs.items():
                all_scope_data = []  # 所有带scope的算子

                # get step_trace data
                step_trace_file_name = fr'{job_dir}/step_trace_*.json'
                file_list_step_trace = get_newest_file(glob.glob(step_trace_file_name))
                if not file_list_step_trace:
                    logger.warning('Could not find step trace file in %s', job_dir)
                else:
                    task_list.append(pool.submit(self._parse_step_trace_data, file_list_step_trace,
                                                 rank_id, difference_ts, model_list, merge_model))

                # get Ascend Hardware 、Hccl、CANN、overlap
                msprof_file_name = fr'{job_dir}/msprof_*.json'
                file_list_msprof = get_newest_file(glob.glob(msprof_file_name))
                if not file_list_msprof:
                    logger.warning('Could not find msprof file in %s', job_dir)
                else:
                    ascend_timeline, scope_data = self._parse_msprof_data(file_list_msprof,
                                                                          rank_id, difference_ts, model_list,
                                                                          scope_name)
                    timeline_data.extend(ascend_timeline)
                    all_scope_data.extend(scope_data)

                if not model_list:
                    # get cpu op
                    cpu_op_file_name = fr'{self._profiling_dir}/cpu_op_execute_timestamp_{rank_id}.txt'
                    file_list = glob.glob(cpu_op_file_name)

                    if not file_list:
                        logger.warning('Could not find cpu op file in %s', job_dir)
                    else:
                        cpu_timeline, scope_data = self.parse_cpu_timeline(get_newest_file(file_list),
                                                                           rank_id, difference_ts, scope_name)
                        timeline_data.extend(cpu_timeline)
                        all_scope_data.extend(scope_data)

                # parse scope info
                task_list.append(pool.submit(self._parse_scope_info, all_scope_data,
                                             rank_id, difference_ts))

            all_done = list(range(len(task_list)))
            while all_done:
                for ind, t in enumerate(task_list):
                    if ind in all_done and t.done():
                        timeline_data.extend(t.result())
                        all_done.remove(ind)

        return timeline_data

    def _get_models(self, sub_dirs):
        """
        Get all models
        """
        model_dict = {}
        model_merged = set()
        for rank_id, (job_dir, _) in sub_dirs.items():
            step_trace_file_name = fr'{job_dir}/step_trace_*.csv'
            file_list = get_newest_file(glob.glob(step_trace_file_name))
            if not file_list:
                continue
            model_set = set()
            with open(file_list[0], 'r', newline='') as fr:
                reader = csv.DictReader(fr, delimiter=',', quotechar='"')
                for row in reader:
                    model_id = row.get('Model ID')
                    if model_id:
                        model_set.add(float(model_id))

            model_dict[rank_id] = model_set
            model_merged.update(model_set)
        return model_dict, model_merged

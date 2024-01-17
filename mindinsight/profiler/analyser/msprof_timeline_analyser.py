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
import logging as logger
from concurrent.futures import ThreadPoolExecutor
from marshmallow import ValidationError

from mindinsight.profiler.analyser.base_analyser import BaseAnalyser
from mindinsight.profiler.common.log import logger
from mindinsight.profiler.common.validator.validate_path import validate_and_normalize_path


def get_absolute_ts_start_info(pro_path) -> float:
    """
    Get difference time between ranks
    """
    start_json = None
    for root, _, files in os.walk(pro_path):
        for file in files:
            if "start_info" in file and ".done" not in file:
                start_json = os.path.join(root, file)
                break
    if start_json:
        with open(start_json, "r+") as f:
            info = json.load(f)
        ts_us = Decimal(info.get("collectionTimeBegin", 0)).quantize(Decimal('0.000'))
        ts_ns = Decimal(info.get("clockMonotonicRaw", 0)).quantize(Decimal('0.000'))
        return ts_us - ts_ns / Decimal(1000)
    return 0


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
        rank_id, device_id = get_rank_id_from_info_json(prof_path)
        ts_difference_us = get_absolute_ts_start_info(prof_path)
        if rank_id is None:
            logger.warning('Could not find the rank id in %s, ignore this file.', prof_path)
            continue

        if rank_id not in timeline_info or (rank_id in timeline_info and prof_path > timeline_info.get(rank_id)[0]):
            prof_path = os.path.join(prof_path, f'device_{device_id}')
            timeline_info[rank_id] = (prof_path, ts_difference_us)

    return timeline_info


def get_job_dir(parent_path):
    job_path_list = glob.glob(fr'{parent_path}/PROF_*_*')
    return get_timeline_info(job_path_list)


def get_newest_file(file_list):
    new_file_list = {}
    for file_path in file_list:
        key = '_'.join(file_path.split('.')[0].split('/')[-1].split('_')[:-1])
        if key not in new_file_list or new_file_list[key] < file_path:
            new_file_list[key] = file_path
    return list(new_file_list.values())


class MsprofTimelineOldAnalyser(BaseAnalyser):
    """
    Analyse timeline data from file.
    """

    def _load(self):
        """Load data according to the parsed profiling files."""

    def _filter(self, filter_condition):
        """
        Filter the profiling data according to the filter condition.

        Args:
            filter_condition (dict): The filter condition.
        """

    def _parse_step_trace_merge_model(self, raw_data, model_list):
        """
        Get step trace by merge models
        """
        pid = None
        tids = {}
        for event in raw_data:
            if event.get('name') == 'process_name' and event.get("ph") == "M":
                pid = event.get('pid')
            elif event.get('name') == 'thread_name' and event.get("ph") == "M":
                arg_name = event.get('args', {}).get('name')
                if not model_list or (arg_name and int(arg_name.split(':')[-1].strip()) in model_list):
                    tids[event.get('tid')] = arg_name
        return pid, tids

    def _parse_step_trace_not_merge_model(self, raw_data, model_list):
        """
        Get step trace by not merge models
        """
        tids = []
        for event in raw_data:
            if event.get('name') == 'thread_name' and event.get("ph") == "M":
                arg_name = event.get('args', {}).get('name')
                if not model_list or (arg_name and int(arg_name.split(':')[-1].strip()) in model_list):
                    tids.append(event.get('tid'))
        return tids

    def _parse_step_trace_data(self, step_trace_file, difference_ts, model_list, merge_model):
        """
        parse step trace data
        """
        try:
            step_trace_file = validate_and_normalize_path(
                step_trace_file, raise_key='Invalid timeline path, could not found step trace file.'
            )
            flags = os.O_RDONLY
            with os.fdopen(os.open(step_trace_file, flags, 0o200), 'r') as fr:
                raw_data = json.load(fr)

            new_events = []
            if merge_model:
                pid, tids = self._parse_step_trace_merge_model(raw_data, model_list)

                if not pid:
                    logger.error('Could not found process_name pid. method: _parse_step_trace_data')
                    return []

                process_meta = {
                    "name": "process_name",
                    "pid": pid,
                    "tid": 0,
                    "args": {
                        "name": "Step Trace"
                    },
                    "ph": "M"
                }

                thread_meta = {
                    "name": "thread_name",
                    "pid": pid,
                    "tid": pid,
                    "args": {
                        "name": "iterations"
                    },
                    "ph": "M"
                }

                new_events = [process_meta, thread_meta]
                for event in raw_data:
                    if event.get('ph') == 'M' or event.get('tid') not in tids:
                        continue

                    event_name = event.get('name').strip()
                    if event_name.startswith('Iteration') and len(event_name.split(' ')) == 2:
                        event['name'] = f"{tids.get(event.get('tid'))} {event_name}"

                    if event.get('ts'):
                        ts = Decimal(event.get('ts')).quantize(Decimal('0.000'))
                        ts += difference_ts
                        event['ts'] = str(ts)

                    event['tid'] = pid

                    new_events.append(event)

            else:
                tids = self._parse_step_trace_not_merge_model(raw_data, model_list)

                for event in raw_data:
                    if (event.get('name') == 'process_name' and event.get("ph") == "M") or \
                            event.get('tid') in tids:
                        if event.get('ts'):
                            ts = Decimal(event.get('ts')).quantize(Decimal('0.000'))
                            event['ts'] = str(ts + difference_ts)
                        new_events.append(event)

            return new_events

        except (ValidationError, IOError, OSError, json.JSONDecodeError) as err:
            logger.error('parse_step_trace_data failed! please theck. detail: %s', err)
            return []

    def _parse_overlap_analysis_data(self, file_list, difference_ts):
        """
        parse overlap analysis data
        """
        try:
            file_list = [validate_and_normalize_path(
                file_path, raise_key='Invalid timeline path, could not found msprof json file.'
            ) for file_path in file_list]
            flags = os.O_RDONLY
            with os.fdopen(os.open(file_list[0], flags, 0o200), 'r') as fr:
                raw_data = json.load(fr)

            pid = None
            for event in raw_data:
                if event.get('name') == 'process_name' and event.get("ph") == "M" and \
                        event.get('args').get('name') == 'Overlap Analysis':
                    pid = event.get('pid')
                    break

            if not pid:
                logger.error('Could not found process_name pid. method: _parse_overlap_analysis_data')
                return []

            process_name = {
                "name": "process_name",
                "pid": pid,
                "tid": 0,
                "args": {
                    "name": "Overlap Analysis"
                },
                "ph": "M"
            }

            thread_name = [{
                "name": "thread_name",
                "pid": pid,
                "tid": 0,
                "args": {
                    "name": "Computing"
                },
                "ph": "M"
            }, {
                "name": "thread_name",
                "pid": pid,
                "tid": 1,
                "args": {
                    "name": "Communication"
                },
                "ph": "M"
            }, {
                "name": "thread_name",
                "pid": pid,
                "tid": 2,
                "args": {
                    "name": "Communication(Not Overlapped)"
                },
                "ph": "M"
            }, {
                "name": "thread_name",
                "pid": pid,
                "tid": 3,
                "args": {
                    "name": "Free"
                },
                "ph": "M"
            }]
            new_events = [process_name] + thread_name

            tid_mapper = {
                'Computing': 0,
                'Communication': 1,
                'Communication(Not Overlapped)': 2,
                'Free': 3
            }

            for msprof_file in file_list:
                flags = os.O_RDONLY
                with os.fdopen(os.open(msprof_file, flags, 0o200), 'r') as fr:
                    raw_data = json.load(fr)

                for event in raw_data:
                    if event.get('ph') == 'M':
                        continue

                    if event.get('name') in tid_mapper:
                        event['pid'] = pid
                        event['tid'] = tid_mapper.get(event.get('name'))
                        if event.get('ts'):
                            ts = Decimal(event.get('ts')).quantize(Decimal('0.000'))
                            ts += difference_ts
                            event['ts'] = str(ts)
                        new_events.append(event)
            return new_events

        except (ValidationError, IOError, OSError, json.JSONDecodeError) as err:
            logger.error('parse_overlap_analysis_data failed! please theck. detail: %s', err)
            return []

    def _parse_ascend_hardware_data(self, file_list, difference_ts):
        """
        parse ascend hardware data
        """
        try:
            file_list = [validate_and_normalize_path(
                file_path, raise_key='Invalid timeline path, could not found task json file.'
            ) for file_path in file_list]
            flags = os.O_RDONLY
            with os.fdopen(os.open(file_list[0], flags, 0o200), 'r') as fr:
                raw_data = json.load(fr)

            pid = None
            tid_mapper = {}
            for event in raw_data:
                if event.get('name') == 'process_name' and event.get("ph") == "M" and \
                        event.get('args').get('name') == 'Ascend Hardware':
                    pid = event.get('pid')

                if event.get('name') == 'thread_name' and event.get("ph") == "M" and \
                        'Stream' in event.get('args').get('name'):
                    thread_name = event.get('args').get('name')
                    if event.get('tid') not in tid_mapper:
                        tid_mapper[event.get('tid')] = thread_name

            if not pid:
                logger.error('Could not found process_name pid. method: _parse_ascend_hardware_data')
                return []

            process_name = {
                "name": "process_name",
                "pid": pid,
                "tid": 0,
                "args": {
                    "name": "Ascend Hardware"
                },
                "ph": "M"
            }

            thread_name_list = [{
                "name": "thread_name",
                "pid": pid,
                "tid": k,
                "args": {
                    "name": v
                },
                "ph": "M"
            } for k, v in tid_mapper.items()]

            new_events = [process_name] + thread_name_list

            for msprof_file in file_list:
                with open(msprof_file, 'r') as fr:
                    raw_data = json.load(fr)

                for event in raw_data:

                    if event.get('ph') == 'M':
                        continue

                    event['pid'] = pid
                    if event.get('ts'):
                        ts = Decimal(event.get('ts')).quantize(Decimal('0.000'))
                        ts += difference_ts
                        event['ts'] = str(ts)
                    new_events.append(event)

            return new_events

        except (ValidationError, IOError, OSError, json.JSONDecodeError) as err:
            logger.error('parse_ascend_hardware_data failed! please theck. detail: %s', err)
            return []

    def _parse_hccl_data(self, file_list, difference_ts):
        """
        parse hccl data
        """
        try:
            file_list[0] = validate_and_normalize_path(
                file_list[0], raise_key='Invalid timeline path, could not found hccl json file.'
            )
            flags = os.O_RDONLY
            with os.fdopen(os.open(file_list[0], flags, 0o200), 'r') as fr:
                raw_data = json.load(fr)

            pid = None
            tid_mapper = {}
            for event in raw_data:
                if event.get('name') == 'process_name' and event.get("ph") == "M" and \
                        event.get('args').get('name') == 'HCCL':
                    pid = event.get('pid')

                elif event.get('name') == 'thread_name' and event.get("ph") == "M" and \
                        ('Plane' in event.get('args').get('name') or 'Communication' in event.get('args').get('name')) \
                        and event.get('tid') not in tid_mapper:
                    tid_mapper[event.get('tid')] = event.get('args').get('name')

            if not pid:
                logger.error('Could not found process_name pid. method: _parse_hccl_data')
                return []

            process_name = {
                "name": "process_name",
                "pid": pid,
                "tid": 0,
                "args": {
                    "name": "HCCL"
                },
                "ph": "M"
            }

            thread_name_list = [{
                "name": "thread_name",
                "pid": pid,
                "tid": k,
                "args": {
                    "name": v
                },
                "ph": "M"
            } for k, v in tid_mapper.items()]

            new_events = [process_name] + thread_name_list

            for hccl_file in file_list:
                hccl_file = validate_and_normalize_path(
                    hccl_file, raise_key='Invalid timeline path, could not found hccl json file.'
                )
                flags = os.O_RDONLY
                with os.fdopen(os.open(hccl_file, flags, 0o200), 'r') as fr:
                    raw_data = json.load(fr)

                for event in raw_data:
                    if event.get('ph') == 'M':
                        continue
                    event['pid'] = pid

                    if event.get('ts'):
                        ts = Decimal(event.get('ts')).quantize(Decimal('0.000'))
                        event['ts'] = str(ts + difference_ts)
                    new_events.append(event)

            return new_events

        except (ValidationError, IOError, OSError, json.JSONDecodeError) as err:
            logger.error('parse_hccl_data failed! please theck. detail: %s', err)
            return []

    def _get_summary_timeline_data(self, sub_dirs, model_list, merge_model):
        """
        Get summary timeline
        Returns:
            json, the content of timeline data.
        """
        timeline_data = {}
        for rank_id, (job_dir, difference_ts) in sub_dirs.items():
            data_list = []

            # get step trace
            step_trace_file_name = fr'{job_dir}/timeline/step_trace_*_*_*.json'
            file_list = glob.glob(step_trace_file_name)
            if not file_list:
                logger.error('Could not find step trace file in %s/device_%s/timeline', job_dir, rank_id)
            else:
                data_list.extend(self._parse_step_trace_data(file_list[0], difference_ts, model_list, merge_model))

            # get overlap analysis
            file_list = []
            if model_list:
                for model_id in model_list:
                    overlap_file_name = fr'{job_dir}/timeline/msprof_*_{model_id}_*.json'
                    file_list.extend(glob.glob(overlap_file_name))
            else:
                overlap_file_name = fr'{job_dir}/timeline/msprof_*_*_*.json'
                file_list.extend(glob.glob(overlap_file_name))

            if not file_list:
                logger.error('Could not find overlap analysis file in %s/device_%s/timeline', job_dir, rank_id)
            else:
                data_list.extend(self._parse_overlap_analysis_data(get_newest_file(file_list), difference_ts))

            timeline_data[rank_id] = data_list

        return timeline_data

    def _get_detail_timeline_data(self, sub_dirs, model_list, merge_model):
        """
        Get detail timeline
        Returns:
            json, the content of timeline data.
        """

        # get summary timeline data. include step_trace data and overlap data
        summary_data = self._get_summary_timeline_data(sub_dirs, model_list, merge_model)

        timeline_data = {}
        for rank_id, (job_dir, difference_ts) in sub_dirs.items():
            data_list = []

            # get Ascend Hardware
            file_list_hardware = []
            # get hccl
            file_list_hccl = []

            if model_list:
                for model_id in model_list:
                    hardware_file_name = fr'{job_dir}/timeline/task_time_*_{model_id}_*.json'
                    file_list_hardware.extend(glob.glob(hardware_file_name))

                    hccl_file_name = fr'{job_dir}/timeline/hccl_*_{model_id}_*.json'
                    file_list_hccl.extend(glob.glob(hccl_file_name))
            else:
                hardware_file_name = fr'{job_dir}/timeline/task_time_*_*_*.json'
                file_list_hardware.extend(glob.glob(hardware_file_name))

                hccl_file_name = fr'{job_dir}/timeline/hccl_*_*_*.json'
                file_list_hccl.extend(glob.glob(hccl_file_name))

            if not file_list_hardware:
                logger.error('Could not find ascend hardware file in %s/device_%s/timeline', job_dir, rank_id)
            else:
                data_list.extend(self._parse_ascend_hardware_data(get_newest_file(file_list_hardware),
                                                                  difference_ts))

            if not file_list_hccl:
                logger.error('Could not find hccl file in %s/device_%s/timeline', job_dir, rank_id)
            else:
                data_list.extend(self._parse_hccl_data(get_newest_file(file_list_hccl), difference_ts))

            timeline_data[rank_id] = data_list

        detail_data = {}
        for rank_id, data_d in timeline_data.items():
            data_s = summary_data.get(rank_id)
            detail_data[rank_id] = data_s + data_d

        return detail_data

    def _merge_timeline(self, timeline_data):
        """
        merge all timeline data
        """
        new_events = []
        for rank_id, events in timeline_data.items():

            for event in events:
                # 区分不同rank的同一进程的pid
                event["pid"] = int(''.join(x for x in str(event.get("pid")) if x.isdigit()) + str(rank_id))

                # 进程名加上rank_id区分不同rank
                if event.get("name") == "process_name" and event.get("ph") == "M":
                    event["args"]["name"] += f" rank{rank_id}"
                new_events.append(event)
        return new_events

    def get_merged_timeline(self, rank_list, model_list, kind, merge_model=True):
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
            summary_data = self._get_summary_timeline_data(sub_dirs, model_list, merge_model)
            return self._merge_timeline(summary_data)

        if kind == 'detail':
            detail_data = self._get_detail_timeline_data(sub_dirs, model_list, merge_model)
            return self._merge_timeline(detail_data)
        return []

    def _get_models(self, sub_dirs):
        """
        Get all models
        """
        model_dict = {}
        model_merged = set()
        for rank_id, (job_dir, _) in sub_dirs.items():
            step_trace_file_name = fr'{job_dir}/timeline/step_trace_*_*_*.json'
            file_list = glob.glob(step_trace_file_name)
            model_set = set()
            for file_name in file_list:
                last_name = file_name.rsplit('/', maxsplit=1)[-1]
                last_name_suffix = last_name.split(f'step_trace_')[-1]
                model_id = last_name_suffix.split('_')[1]
                model_set.add(int(model_id))
            model_dict[rank_id] = model_set
            model_merged.update(model_set)
        return model_dict, model_merged

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

                            ts += difference_ts

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
                ts += difference_ts
                event['ts'] = str(ts)
            event['pid'] = new_pid
            event['tid'] = 0
            new_events.append(event)
        return new_events

    def _parse_step_trace_not_merge(self, old_pid, new_pid, rank_id, raw_data, tid_mapper, difference_ts):
        """not merge step trace data"""
        new_events = []
        for event in raw_data:
            arg_name = tid_mapper.get(event.get('tid'))
            if event.get('pid') != old_pid or not arg_name:
                continue
            if event.get('name') == 'process_name' and event.get('ph') == 'M':
                event['args']['name'] = f"Step Trace Rank{rank_id}"
            elif event.get('name') == 'process_sort_index' and event.get('ph') == 'M':
                event['args']['sort_index'] = self.step_trace_index

            event['pid'] = new_pid
            if event.get('ts'):
                ts = Decimal(event.get('ts')).quantize(Decimal('0.000'))
                ts += difference_ts
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

            return self._parse_step_trace_not_merge(pid, new_pid, rank_id, raw_data, tid_mapper, difference_ts)

        except (ValidationError, IOError, OSError, json.JSONDecodeError) as err:
            logger.error('parse_step_trace_data failed! please theck. detail: %s', err)
            return []

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

    def _parse_ascend_hardware_metadata(self, new_pid, raw_data):
        """
        Get ascend hardware by merge models
        """
        tid_mapper = {}
        pid = None
        for event in raw_data:
            if event.get('name') == 'process_name' and event.get("ph") == "M" and \
                    event.get('args').get('name') == 'Ascend Hardware':
                pid = event.get('pid')

            elif event.get('name') == 'thread_name' and event.get("ph") == "M" and \
                    'Stream' in event.get('args').get('name'):
                event['pid'] = new_pid
                tid_mapper.update({event.get('tid'): event})
        return pid, tid_mapper

    def _parse_ascend_hardware_data(self, file_list, rank_id, difference_ts, model_list, scope_name):
        """
        parse ascend hardware data
        """
        flags = os.O_RDONLY
        raw_data = []

        new_events = []
        tid_set = set()
        new_pid = int(f'{self.ascend_hardware_index}{rank_id}')
        new_metadata = [{
            "name": "process_name",
            "pid": new_pid,
            "args": {
                "name": f"Ascend Hardware Rank{rank_id}"
            },
            "ph": "M"
        }, {"name": "process_sort_index", "pid": new_pid,
            "args": {"sort_index": self.ascend_hardware_index}, "ph": "M"}]
        scope_data = []
        model_id_set = set()
        try:
            for file_path in file_list:
                with os.fdopen(os.open(file_path, flags, 0o400), 'r') as fr:
                    raw_data.extend(json.load(fr))

            pid, tid_mapper = self._parse_ascend_hardware_metadata(new_pid, raw_data)

            if not pid:
                logger.error('Could not found process_name pid. method: _parse_ascend_hardware_data')
                return []

            for event in raw_data:
                model_id = event.get('args', {}).get('Model Id')
                model_id_set.add(model_id)
                if event.get("ph") == "M" or (model_list and model_id not in model_list):
                    continue

                op_full_name = event.get('name')
                if scope_name and op_full_name and op_full_name.startswith(self.top_scope_name):
                    ts = Decimal(event.get('ts')).quantize(Decimal('0.000'))
                    te = ts + Decimal(event.get('dur')).quantize(Decimal('0.000'))
                    scope_data.append((op_full_name.split('/')[:-1], ts, te))

                if event.get('ts'):
                    ts = Decimal(event.get('ts')).quantize(Decimal('0.000'))
                    ts += difference_ts
                    event['ts'] = str(ts)
                event['pid'] = new_pid
                tid_set.add(event.get('tid'))
                new_events.append(event)

            for tid in tid_set:
                thread_event = tid_mapper.get(tid)
                if thread_event is None:
                    thread_event = {"name": "thread_name", "pid": new_pid,
                                    "tid": tid, "args": {"name": f"Stream {tid}"}, "ph": "M"}
                new_metadata.append(thread_event)
            return new_metadata + new_events, scope_data

        except (ValidationError, IOError, OSError, json.JSONDecodeError) as err:
            logger.error('parse_ascend_hardware_data failed! please theck. detail: %s', err)
            return []

    def _parse_hccl_data(self, file_list, rank_id, difference_ts, model_list):
        """
        parse hccl data
        """
        try:
            flags = os.O_RDONLY
            raw_data = []
            for file_path in file_list:
                with os.fdopen(os.open(file_path, flags, 0o400), 'r') as fr:
                    raw_data.extend(json.load(fr))

            pid = None
            tid_mapper = {}
            tid_set = set()
            new_events = []
            new_pid = int(f'{self.hccl_index}{rank_id}')
            model_id_set = set()

            for event in raw_data:
                if event.get('name') == 'process_name' and event.get("ph") == "M" and \
                        event.get('args').get('name') == 'HCCL':
                    pid = event.get('pid')

                elif event.get('name') == 'thread_name' and event.get("ph") == "M" and \
                        ('Plane' in event.get('args').get('name') or 'Communication' in event.get('args').get('name')):
                    event['pid'] = new_pid
                    tid_mapper.update({event.get('tid'): event})

            if not pid:
                logger.error('Could not found process_name pid. method: _parse_hccl_data')
                return []

            for event in raw_data:
                model_id = event.get('args', {}).get('model id')
                model_id_set.add(model_id)
                if event.get("ph") == "M" or (model_list and model_id not in model_list):
                    continue

                if event.get('ts'):
                    ts = Decimal(event.get('ts')).quantize(Decimal('0.000'))
                    ts += difference_ts
                    event['ts'] = str(ts)

                event['pid'] = new_pid
                new_events.append(event)

                tid = event.get('tid')
                tid_set.add(tid)

            new_metadata = [{
                "name": "process_name",
                "pid": new_pid,
                "args": {
                    "name": f"HCCL Rank{rank_id}"
                },
                "ph": "M"
            }, {"name": "process_sort_index", "pid": new_pid,
                "args": {"sort_index": self.hccl_index}, "ph": "M"}]

            for tid in tid_set:
                new_metadata.append(tid_mapper.get(tid))
            return new_metadata + new_events

        except (ValidationError, IOError, OSError, json.JSONDecodeError) as err:
            logger.error('parse_hccl_data failed! please theck. detail: %s', err)
            return []

    def _parse_cann_data(self, file_list, rank_id, difference_ts):
        """
        pid: 1 rank
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
                        event.get('args').get('name') == 'CANN':
                    pid = event.get('pid')
                    break

            if not pid:
                logger.warning('Could not found process_name pid. method: _parse_cann_data')
                return []

            new_events = []
            new_pid = int(f'{self.cann_index}{rank_id}')
            for event in raw_data:
                if event.get('pid') != pid:
                    continue
                if event.get('name') == 'process_name' and event.get("ph") == "M":
                    event["args"]["name"] += f" Rank{rank_id}"

                if event.get('name') == 'process_sort_index' and event.get("ph") == "M":
                    event["args"]["sort_index"] = self.cann_index

                event['pid'] = new_pid
                if event.get('ts'):
                    ts = Decimal(event.get('ts')).quantize(Decimal('0.000'))
                    ts += difference_ts
                    event['ts'] = str(ts)

                new_events.append(event)

            return new_events

        except (ValidationError, IOError, OSError, json.JSONDecodeError) as err:
            logger.error('parse_cann_data failed! please theck. detail: %s', err)
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
                        ts += difference_ts
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
                ts += difference_ts
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
                step_trace_file_name = fr'{job_dir}/timeline/step_trace_*.json'
                file_list = glob.glob(step_trace_file_name)
                if not file_list:
                    logger.error('Could not find step trace file in %s/device_%s/timeline', job_dir, rank_id)
                else:
                    task_list.append(pool.submit(self._parse_step_trace_data, get_newest_file(file_list),
                                                 rank_id, difference_ts, None,
                                                 merge_model))

                # get overlap analysis
                overlap_file_name = fr'{job_dir}/timeline/msprof_*.json'
                file_list = glob.glob(overlap_file_name)

                if not file_list:
                    logger.error('Could not find overlap analysis file in %s/device_%s/timeline', job_dir, rank_id)
                else:
                    task_list.append(pool.submit(self._parse_overlap_analysis_data, get_newest_file(file_list),
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
                step_trace_file_name = fr'{job_dir}/timeline/step_trace_*.json'
                file_list_step_trace = glob.glob(step_trace_file_name)
                if not file_list_step_trace:
                    logger.error('Could not find step trace file in %s/device_%s/timeline', job_dir, rank_id)
                else:
                    task_list.append(pool.submit(self._parse_step_trace_data, get_newest_file(file_list_step_trace),
                                                 rank_id, difference_ts, model_list, merge_model))

                # get Ascend Hardware
                hardware_file_name = fr'{job_dir}/timeline/task_time_*.json'
                file_list_hardware = glob.glob(hardware_file_name)
                if not file_list_hardware:
                    logger.error('Could not find ascend hardware file in %s/device_%s/timeline', job_dir, rank_id)
                else:
                    ascend_timeline, scope_data = self._parse_ascend_hardware_data(get_newest_file(file_list_hardware),
                                                                                   rank_id, difference_ts, model_list,
                                                                                   scope_name)
                    timeline_data.extend(ascend_timeline)
                    all_scope_data.extend(scope_data)

                # get hccl
                hccl_file_name = fr'{job_dir}/timeline/hccl_*.json'
                file_list_hccl = glob.glob(hccl_file_name)
                if not file_list_hccl:
                    logger.error('Could not find hccl file in %s/device_%s/timeline', job_dir, rank_id)
                else:
                    task_list.append(pool.submit(self._parse_hccl_data, get_newest_file(file_list_hccl),
                                                 rank_id, difference_ts, model_list))

                if not model_list:
                    # get CANN
                    cann_file_name = fr'{job_dir}/timeline/msprof_*.json'
                    file_list = glob.glob(cann_file_name)

                    if not file_list:
                        logger.error('Could not find overlap analysis file in %s/device_%s/timeline', job_dir, rank_id)
                    else:
                        task_list.append(pool.submit(self._parse_cann_data, get_newest_file(file_list),
                                                     rank_id, difference_ts))

                    # get overlap analysis
                    overlap_file_name = fr'{job_dir}/timeline/msprof_*.json'
                    file_list = glob.glob(overlap_file_name)
                    if not file_list:
                        logger.error('Could not find overlap analysis file in %s/device_%s/timeline', job_dir, rank_id)
                    else:
                        task_list.append(pool.submit(self._parse_overlap_analysis_data, get_newest_file(file_list),
                                                     rank_id, difference_ts))

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
            step_trace_file_name = fr'{job_dir}/summary/step_trace_*.csv'
            file_list = glob.glob(step_trace_file_name)
            model_set = set()
            if not file_list:
                model_dict[rank_id] = model_set
                model_merged.update(model_set)
                continue

            with open(max(file_list), 'r', newline='') as fr:
                reader = csv.DictReader(fr, delimiter=',', quotechar='"')
                for row in reader:
                    model_id = row.get('Model ID')
                    if model_id:
                        model_set.add(int(model_id))

            model_dict[rank_id] = model_set
            model_merged.update(model_set)
        return model_dict, model_merged

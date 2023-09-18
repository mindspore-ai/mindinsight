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
import json
import os
import glob
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
        ts_us = float(info.get("collectionTimeBegin", 0))
        ts_ns = float(info.get("clockMonotonicRaw", 0))
        if not ts_us and not ts_ns:
            return 0
        return ts_us - ts_ns / 1000
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
        device_id = int(info.get('deviced', device_id))

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
    timeline_info = get_timeline_info(job_path_list)
    return timeline_info


def get_newest_file(file_list, split_num=4):
    new_file_list = {}
    for file_path in file_list:
        key = '_'.join(file_path.split('/')[-1].split('_')[:split_num])
        if key not in new_file_list or new_file_list[key] < file_path:
            new_file_list[key] = file_path
    return list(new_file_list.values())


class MsprofTimelineAnalyser(BaseAnalyser):
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

                    if difference_ts and event.get('ts'):
                        event['ts'] += difference_ts

                    event['tid'] = pid

                    new_events.append(event)

            else:
                tids = self._parse_step_trace_not_merge_model(raw_data, model_list)

                for event in raw_data:
                    if (event.get('name') == 'process_name' and event.get("ph") == "M") or \
                            event.get('tid') in tids:
                        if difference_ts and event.get('ts'):
                            event['ts'] += difference_ts
                        new_events.append(event)

            return new_events
        except ValidationError as err:
            logger.error('parse_step_trace_data failed! please theck. detail: %s', err)
            raise ValidationError from err

        except (IOError, OSError, json.JSONDecodeError) as err:
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

                        if difference_ts and event.get('ts'):
                            event['ts'] += difference_ts
                        new_events.append(event)
            return new_events

        except ValidationError as err:
            logger.error('parse_overlap_analysis_data failed! please theck. detail: %s', err)
            raise ValidationError from err

        except (IOError, OSError, json.JSONDecodeError) as err:
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

                    if difference_ts and event.get('ts'):
                        event['ts'] += difference_ts
                    new_events.append(event)

            return new_events

        except ValidationError as err:
            logger.error('parse_ascend_hardware_data failed! please theck. detail: %s', err)
            raise ValidationError from err

        except (IOError, OSError, json.JSONDecodeError) as err:
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

                    if difference_ts and event.get('ts'):
                        event['ts'] += difference_ts
                    new_events.append(event)

            return new_events

        except ValidationError as err:
            logger.error('parse_hccl_data failed! please theck. detail: %s', err)
            raise ValidationError from err

        except (IOError, OSError, json.JSONDecodeError) as err:
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
                data_list.extend(self._parse_ascend_hardware_data(get_newest_file(file_list_hardware, 5),
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
            for key in sub_dirs:
                if key not in rank_list: sub_dirs.pop(key)

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

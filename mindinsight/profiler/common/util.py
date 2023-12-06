# Copyright 2020-2022 Huawei Technologies Co., Ltd
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
Profiler util.

This module provides the utils.
"""
import json
import os
import re
import glob

from mindinsight import __version__ as mi_version
from mindinsight.datavisual.utils.tools import to_int
from mindinsight.profiler.common.exceptions.exceptions import ProfilerDirNotFoundException
from mindinsight.profiler.common.exceptions.exceptions import ProfilerInfoFieldMissingException
from mindinsight.datavisual.common.exceptions import TrainJobNotExistError
from mindinsight.common.util import version_match

# one sys count takes 10 ns, 1 ms has 100000 system count
PER_MS_SYSCNT = 100000


def analyse_device_list_from_profiler_dir(profiler_dir):
    """
    Analyse device list from profiler dir.

    Args:
        profiler_dir (str): The profiler data dir.

    Returns:
        list, the device_id list.
    """
    profiler_file_prefix = ("ascend_timeline_display*", "output_op_compute_time*")
    gpu_profiler_file_prefix = ("gpu_op_detail_info*", "gpu_activity_data*", "gpu_op_type_info*")
    cpu_profiler_file_prefix = ("cpu_op_detail_info*", "cpu_op_type_info*")

    def get_device_list_and_profiler_mode():
        profiler_info_list = glob.glob(fr'{profiler_dir}/profiler_info_*.json')
        device_id_list = set()
        profiler_mode = ''
        for profiler_info_file in profiler_info_list:
            if not profiler_mode:
                with os.fdopen(os.open(profiler_info_file, os.O_RDONLY, 0o400), 'r') as fr:
                    json_data = json.load(fr)
                profiler_mode = json_data.get('context_mode', '')
            device_id = profiler_info_file.split('profiler_info_')[-1].split('.')[0]
            device_id_list.add(device_id)
        return sorted(list(device_id_list)), profiler_mode

    device_id_list, profiler_mode = get_device_list_and_profiler_mode()

    def get_profiler_type(file_prefix):
        for file_name in file_prefix:
            if glob.glob(fr'{profiler_dir}/{file_name}'):
                return True
        return False

    if get_profiler_type(profiler_file_prefix):
        return device_id_list, 'ascend', profiler_mode

    if get_profiler_type(gpu_profiler_file_prefix):
        return device_id_list, 'gpu', profiler_mode

    if get_profiler_type(cpu_profiler_file_prefix):
        return device_id_list, 'cpu', profiler_mode

    return device_id_list, '', profiler_mode


def query_latest_trace_time_file(profiler_dir, device_id=0):
    """
    Query the latest trace time file.

    Args:
        profiler_dir (str): The profiler directory.
        device_id (int): The id of device.

    Returns:
        str, the latest trace time file path.
    """
    files = os.listdir(profiler_dir)
    target_file = f'step_trace_raw_{device_id}_detail_time.csv'
    try:
        latest_file = max(
            filter(
                lambda file: file == target_file,
                files
            ),
            key=lambda file: os.stat(os.path.join(profiler_dir, file)).st_mtime
        )
    except ValueError:
        return None
    return os.path.join(profiler_dir, latest_file)


def query_profiling_graph_mode(profiler_dir):
    graph_mode = 'static'
    dynamic_shape_file_prefix = "dynamic_shape_info"
    all_file = os.listdir(profiler_dir)
    for file in all_file:
        if file.startswith(dynamic_shape_file_prefix):
            graph_mode = 'dynamic'
            return graph_mode
    return graph_mode


def query_step_trace_file(profiler_dir):
    """
    Query for all step trace file.

    Args:
        profiler_dir (str): The directory that contains all step trace files.

    Returns:
        str, the file path of step trace time.
    """
    files = os.listdir(profiler_dir)
    training_trace_file = list(
        filter(
            lambda file: file.startswith('training_trace') and not file.endswith('.done'),
            files
        )
    )
    if training_trace_file:
        return os.path.join(profiler_dir, training_trace_file[0])
    return None


def get_summary_for_step_trace(average_info, header):
    """The property of summary info."""
    if not average_info or not header:
        return {}
    total_time = get_field_value(average_info, 'total', header)
    iteration_interval = get_field_value(average_info, 'iteration_interval',
                                         header)
    summary_part = {
        'total_time': total_time,
        'iteration_interval': iteration_interval,
        'iteration_interval_percent': calculate_percent(iteration_interval, total_time),
    }
    # training scene data for ui display
    if 'fp_and_bp' in header:
        fp_and_bp = get_field_value(average_info, 'fp_and_bp', header)
        tail = get_field_value(average_info, 'tail', header)
        summary = {
            'fp_and_bp': fp_and_bp,
            'fp_and_bp_percent': calculate_percent(fp_and_bp, total_time),
            'tail': tail,
            'tail_percent': calculate_percent(tail, total_time)
        }
    # inference scene data for ui display
    else:
        fp = get_field_value(average_info, 'fp', header)
        summary = {
            'fp': fp,
            'fp_percent': calculate_percent(fp, total_time)
        }
    summary.update(summary_part)
    return summary


def calculate_percent(partial, total):
    """Calculate percent value."""
    if total:
        percent = round(partial / total * 100, 2)
    else:
        percent = 0
    return f'{percent}%'


def to_millisecond(sys_count, limit=4):
    """Translate system count to millisecond."""
    return round(sys_count / PER_MS_SYSCNT, limit)


def get_field_value(row_info, field_name, header, time_type='realtime'):
    """
    Extract basic info through row_info.

    Args:
        row_info (list): The list of data info in one row.
        field_name (str): The name in header.
        header (list[str]): The list of field names.
        time_type (str): The type of value, `realtime` or `systime`. Default: `realtime`.

    Returns:
        dict, step trace info in dict format.
    """
    field_index = header.index(field_name)
    value = row_info[field_index]
    value = to_int(value, field_name)
    if time_type == 'realtime':
        value = to_millisecond(value)

    return value


def get_options(options):
    """Get options."""
    if options is None:
        options = {}
    return options


def check_train_job_and_profiler_dir(profiler_dir_abs):
    """ check the existence of train_job and profiler dir """
    train_job_dir_abs = os.path.abspath(os.path.join(profiler_dir_abs, '..'))
    if not os.path.exists(train_job_dir_abs):
        raise TrainJobNotExistError(error_detail=train_job_dir_abs)
    if not os.path.exists(profiler_dir_abs):
        raise ProfilerDirNotFoundException(msg=profiler_dir_abs)


def get_profile_data_version(profiler_dir):
    """ get the profiler data version """

    profile_info_pattern = re.compile(r"profiler_info_(\d+).json")
    profile_info_file = None
    for f_name in os.listdir(profiler_dir):
        re_match = re.match(profile_info_pattern, f_name)
        if re_match:
            profile_info_file = re_match.group()
            break
    if profile_info_file:
        full_path = os.path.join(profiler_dir, profile_info_file)
        with open(full_path, 'r') as fr:
            data = json.load(fr)
        ms_data_version = data.get('ms_version', '')
        if ms_data_version:
            data_match_stat = version_match(ms_data_version, mi_version)
            stat_reply = True
            if data_match_stat >= 1:
                stat_reply = False
            result_data = {'state': stat_reply,
                           'ms': ms_data_version,
                           'mi': mi_version}
            return result_data
    return {}


def get_all_export_flag(profiler_dir):
    """ get the flag what means whether support all-export mode. """

    profile_info_pattern = re.compile(r"profiler_info_(\d+).json")
    profile_info_file = None
    for f_name in os.listdir(profiler_dir):
        re_match = re.match(profile_info_pattern, f_name)
        if re_match:
            profile_info_file = re_match.group()
            break
    if profile_info_file:
        full_path = os.path.join(profiler_dir, profile_info_file)
        with open(full_path, 'r') as fr:
            data = json.load(fr)
        return data.get('all_export', False)

    return False


def get_parallel_message(profiler_dir):
    """get the parallel message"""

    profile_info_pattern = re.compile(r"profiler_info_(\d+).json")
    profile_info_file = None
    for f_name in os.listdir(profiler_dir):
        re_match = re.match(profile_info_pattern, f_name)
        if re_match:
            profile_info_file = re_match.group()
            break
    if profile_info_file:
        full_path = os.path.join(profiler_dir, profile_info_file)
        with open(full_path, 'r') as fr:
            data = json.load(fr)
        parallel_mode = data.get('parallel_mode')
        stage_num = data.get('stage_num')
        rank_size = data.get('rank_size')
        if not parallel_mode or not stage_num or not rank_size:
            msg = f"file: {full_path}, fields: parallel_mode, stage_num, rank_size"
            raise ProfilerInfoFieldMissingException(msg=msg)
        return {'parallel_mode': parallel_mode, 'stage_num': stage_num, 'rank_size': rank_size}
    return {}

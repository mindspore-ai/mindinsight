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
"""Profiler utils."""
import os
import re


def fwrite_format(output_data_path, data_source=None, is_print=False, is_start=False):
    """
    Write data to the output file.

    Args:
         output_data_path (str): The output file path of the data.
         data_source (list): The data to write.
         is_print (bool): whether to print the data to stdout.
         is_start (bool): Whether is the first line of the output file, will remove the old file if True."
    """

    if is_start is True and os.path.exists(output_data_path):
        os.remove(output_data_path)

    if data_source.startswith("title:"):
        title_label = '=' * 20
        data_source = title_label + data_source[6:] + title_label

    with open(output_data_path, 'a+') as f:
        f.write(data_source)
        f.write("\n")

    if is_print:
        print(data_source)


def get_log_slice_id(file_name):
    pattern = re.compile(r'(?<=slice_)\d+')
    slice_list = pattern.findall(file_name)
    index = re.findall(r'\d+', slice_list[0])
    return int(index[0])


def get_file_join_name(input_path, file_name):
    """
    Search files under the special path, and will join all the files to one file.

    Args:
        input_path (str): The source path, will search files under it.
        file_name (str): The target of the filename, such as 'hwts.log.data.45.dev'.

    Returns:
        str, the join file name.
    """
    name_list = []
    file_join_name = ''
    input_path = os.path.realpath(input_path)
    if os.path.exists(input_path):
        files = os.listdir(input_path)
        for f in files:
            if file_name in f and not f.endswith('.done') and not f.endswith('.join') \
                    and not f.endswith('.zip'):
                name_list.append(f)

        # resort name_list
        name_list.sort(key=get_log_slice_id)

    if len(name_list) == 1:
        file_join_name = os.path.join(input_path, name_list[0])
    elif len(name_list) > 1:
        file_join_name = os.path.join(input_path, '%s.join' % file_name)
        if os.path.exists(file_join_name):
            os.remove(file_join_name)
        with open(file_join_name, 'ab') as bin_data:
            for i in name_list:
                file = input_path + os.sep + i
                with open(file, 'rb') as txt:
                    bin_data.write(txt.read())
    return file_join_name

def get_file_names(input_path, file_name):
    """
    Search files under the special path.

    Args:
        input_path (str): The source path, will search files under it.
        file_name (str): The target of the filename, such as 'host_start_log'.

    Returns:
        list, file name list.
    """

    input_path = os.path.realpath(input_path)
    name_list = []
    if os.path.exists(input_path):
        files = os.listdir(input_path)
        for f in files:
            if file_name in f and not f.endswith('.done') \
                    and not f.endswith('.zip'):
                name_list.append(f)
                break

    return name_list

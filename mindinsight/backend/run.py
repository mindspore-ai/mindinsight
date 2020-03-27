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
"""Web service entrance."""
import os
import stat
import re
import subprocess
import time
import shlex

from gunicorn.glogging import Logger

from mindinsight.backend.config import gunicorn_conf
from mindinsight.backend.config import WEB_CONFIG_DIR
from mindinsight.conf import settings
from mindinsight.utils.log import setup_logger


MINDBOARD_APP_MODULE = "mindinsight.backend.application:APP"
GUNICORN_LOGGER = "mindinsight.backend.run.GunicornLogger"

_MIN_PORT = 1
_MAX_PORT = 65535


def _get_file_size(file_path):
    """
    Get the file size.

    Args:
        file_path (str): The file path.

    Returns:
        int, the file size. If file is not existed, then return 0.
    """
    try:
        file_size = os.path.getsize(file_path)
    except FileNotFoundError:
        file_size = 0
    return file_size


def _is_match_one(sub_string_list, src_string):
    """
    Whether the sub-string in the list can match the source string.

    Args:
        sub_string_list (list): The sub-string list.
        src_string (str): The source string.

    Returns:
        bool, if matched return True, else return False.
    """
    for match_info in sub_string_list:
        if match_info in src_string:
            return True
    return False


def _check_stat_from_log(log_info):
    """
    Determine the service startup status based on the log information.

    Args:
        log_info (str): The output log of service startup.

    Returns:
        str, the state value that is one of the follows: "unknown", "failed" and "success".
    """
    server_state = "unknown"
    match_success_info = "Listening at: http://%s:%d" % \
                         (settings.HOST, int(settings.PORT))
    common_failed_info_list = [
        "[ERROR] Retrying in 1 second",
        "[INFO] Reason: App failed to load",
        "[ERROR] Exception in worker process"
    ]
    re_pattern = "\\[ERROR\\].+%s.+%d" % \
                 (settings.HOST, int(settings.PORT))

    # matched failed output log by fuzzy match
    if re.search(re_pattern, log_info) or \
            _is_match_one(common_failed_info_list, log_info):
        server_state = "failed"

    if match_success_info in log_info:
        server_state = "success"

    return server_state


def _get_error_log_path():
    """
    Get gunicorn error log path.

    Returns:
        str, the path of error log.
    """

    path = os.path.join(settings.WORKSPACE, 'log/gunicorn/error.log')
    errorlog_abspath = os.path.realpath(path)
    return errorlog_abspath


def _get_access_log_path():
    """Get gunicorn access log path."""
    access_log_path = os.path.join(settings.WORKSPACE, 'log/gunicorn/access.log')
    access_log_path = os.path.realpath(access_log_path)
    return access_log_path


def _check_state_from_log(log_abspath, start_pos=0):
    """
    Check the service startup status based on the log file.

    Args:
        log_abspath (str): Absolute path of the log file.
        start_pos (int): Offset position of the log file.

    Returns:
        dict, a dict with "state" and "prompt_message" key.
        The value of the "state" key is as follows:"unknown", "failed" and "success".
        The value of the "prompt_message" key is a list of prompt messages.

    """
    server_is_start = False
    state_result = {"state": "unknown", "prompt_message": []}
    prompt_messages = []
    match_start_log = "Starting gunicorn"
    with open(log_abspath) as f_log:
        f_log.seek(start_pos)
        for line in f_log.readlines():
            if match_start_log in line:
                if server_is_start:
                    break
                server_is_start = True
                continue
            if server_is_start:
                log_result = _check_stat_from_log(line)
                # ignore "unknown" result
                if log_result != "unknown":
                    state_result["state"] = log_result

                if log_result == "failed":
                    prompt_messages.append(line.strip())
                    prompt_messages.append(
                        "more failed details in log: %s" % log_abspath)
                    break
    state_result["prompt_message"].append(
        "service start state: %s" % state_result["state"])
    for prompt_message in prompt_messages:
        state_result["prompt_message"].append(prompt_message)

    return state_result


def _check_server_start_stat(log_abspath, start_pos=None):
    """
    Checking the Server Startup Status.

    Args:
        log_abspath (str): The log file path.
        start_pos (int): The log file start position.

    Returns:
        dict, an dict object that contains the state and prompt_message fields.
        The state values are as follows: "unknown", "failed" and "success".

    """
    state_result = {"state": "unknown", "prompt_message": []}
    # return unknown when not config gunicorn error log file
    if not log_abspath:
        return state_result

    log_pos = _get_file_size(log_abspath) if start_pos is None else start_pos
    try_cnt = 0
    try_cnt_max = 2

    while try_cnt < try_cnt_max:
        try_cnt += 1
        time.sleep(1)
        if _get_file_size(log_abspath) > log_pos:
            state_result.update(_check_state_from_log(log_abspath, log_pos))
            break

    return state_result


class GunicornLogger(Logger):
    """Rewrite gunicorn default logger."""

    def __init__(self, cfg):
        self.access_log = setup_logger('gunicorn', 'access')
        self.error_log = setup_logger('gunicorn', 'error')
        super(GunicornLogger, self).__init__(cfg)
        access_log_path = _get_access_log_path()
        error_log_path = _get_error_log_path()
        os.chmod(access_log_path, stat.S_IREAD | stat.S_IWRITE)
        os.chmod(error_log_path, stat.S_IREAD | stat.S_IWRITE)


def start():
    """Start web service."""
    errorlog_abspath = _get_error_log_path()

    gunicorn_conf_file = os.path.join(WEB_CONFIG_DIR, "gunicorn_conf.py")
    cmd = "gunicorn " \
          "-b {host}:{port} {app_module} " \
          "-c {conf_file} " \
          "--logger-class {logger_class} " \
          "--access-logformat {log_format}"\
        .format(host=settings.HOST,
                port=settings.PORT,
                conf_file=gunicorn_conf_file,
                app_module=MINDBOARD_APP_MODULE,
                logger_class=GUNICORN_LOGGER,
                log_format=settings.GUNICORN_ACCESS_FORMAT
                )

    log_size = _get_file_size(errorlog_abspath)

    # start server
    process = subprocess.Popen(
        shlex.split(cmd),
        shell=False,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    _, stderr = process.communicate()
    if stderr:
        print(stderr.decode())

    # wait command success to end when gunicorn running in daemon.
    if gunicorn_conf.daemon and process.wait() == 0:
        state_result = _check_server_start_stat(errorlog_abspath, log_size)
        # print gunicorn start state to stdout
        print('Web address: http://{}:{}'.format(settings.HOST, settings.PORT))
        for line in state_result["prompt_message"]:
            print(line)


if __name__ == '__main__':
    start()

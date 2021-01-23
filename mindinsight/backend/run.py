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
import re
import shlex
import stat
import subprocess
import sys
import time
from enum import Enum, unique

from gunicorn.glogging import Logger
from mindinsight.backend.config import WEB_CONFIG_DIR
from mindinsight.conf import settings
from mindinsight.utils.log import setup_logger

MINDBOARD_APP_MODULE = "mindinsight.backend.application:APP"
GUNICORN_LOGGER = "mindinsight.backend.run.GunicornLogger"

_MIN_PORT = 1
_MAX_PORT = 65535


@unique
class ServerStateEnum(Enum):
    """
    The service startup status are as follows: "unknown", "failed" and "success"
    """
    UNKNOWN = "unknown"
    FAILED = "failed"
    SUCCESS = "success"


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


def _check_stat_from_log(pid, log_info):
    """
    Determine the service startup status based on the log information.

    Args:
        pid (int): The gunicorn process ID.
        log_info (str): The output log of service startup.

    Returns:
        str, the state value that is one of the follows: "unknown", "failed" and "success".
    """
    server_state = ServerStateEnum.UNKNOWN.value

    # should be synchronized to startup log in gunicorn post_worker_init hook
    # refer to mindinsight/backend/config/gunicorn_conf.py
    match_success_info = "Server pid: %d, start to listening." % pid

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
        server_state = ServerStateEnum.FAILED.value

    if match_success_info in log_info:
        server_state = ServerStateEnum.SUCCESS.value

    return server_state


def _get_error_log_path():
    """
    Get gunicorn error log path.

    Returns:
        str, the path of error log.
    """

    path = os.path.join(settings.WORKSPACE, 'log/gunicorn/error.{}.log'.format(settings.PORT))
    errorlog_abspath = os.path.realpath(path)
    return errorlog_abspath


def _get_access_log_path():
    """Get gunicorn access log path."""
    access_log_path = os.path.join(settings.WORKSPACE, 'log/gunicorn/access.{}.log'.format(settings.PORT))
    access_log_path = os.path.realpath(access_log_path)
    return access_log_path


def _check_state_from_log(pid, log_abspath, start_pos=0):
    """
    Check the service startup status based on the log file.

    Args:
        pid (int): The gunicorn process ID.
        log_abspath (str): Absolute path of the log file.
        start_pos (int): Offset position of the log file.

    Returns:
        dict, a dict with "state" and "prompt_message" key.
        The value of the "state" key is as follows:"unknown", "failed" and "success".
        The value of the "prompt_message" key is a list of prompt messages.

    """
    state_result = {"state": ServerStateEnum.UNKNOWN.value, "prompt_message": []}
    prompt_messages = []
    with open(log_abspath) as f_log:
        f_log.seek(start_pos)
        for line in f_log.readlines():
            log_result = _check_stat_from_log(pid, line)
            # ignore "unknown" result
            if log_result != ServerStateEnum.UNKNOWN.value:
                state_result["state"] = log_result

            if log_result == ServerStateEnum.FAILED.value:
                prompt_messages.append(line.strip())
                prompt_messages.append(
                    "more failed details in log: %s" % log_abspath)
                break
    if log_result == ServerStateEnum.UNKNOWN.value:
        prompt_messages.append(
            "more details in log: %s" % log_abspath)
    state_result["prompt_message"].append(
        "service start state: %s" % state_result["state"])
    for prompt_message in prompt_messages:
        state_result["prompt_message"].append(prompt_message)

    return state_result


def _check_server_start_stat(pid, log_abspath, log_pos):
    """
    Checking the Server Startup Status.

    Args:
        pid (int): The gunicorn process ID.
        log_abspath (str): The log file path.

    Returns:
        dict, an dict object that contains the state and prompt_message fields.
        The state values are as follows: "unknown", "failed" and "success".

    """
    state_result = {"state": ServerStateEnum.UNKNOWN.value, "prompt_message": []}
    # return unknown when not config gunicorn error log file
    if not log_abspath:
        return state_result

    # sleep 1 second for gunicorn master to be ready
    time.sleep(1)

    try_cnt = 0
    try_cnt_max = 2

    while try_cnt < try_cnt_max:
        time.sleep(1)
        try_cnt += 1
        file_size = _get_file_size(log_abspath)
        if file_size > log_pos:
            state_result.update(_check_state_from_log(pid, log_abspath, log_pos))
            break

    if not state_result['prompt_message']:
        state_result["prompt_message"].append(
            "service start state: %s" % state_result["state"])

    return state_result


class GunicornLogger(Logger):
    """Rewrite gunicorn default logger."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.access_log = setup_logger('gunicorn', 'access', formatter='%(message)s')
        self.error_log = setup_logger('gunicorn', 'error', formatter=self.error_fmt)
        access_log_path = _get_access_log_path()
        error_log_path = _get_error_log_path()
        os.chmod(access_log_path, stat.S_IREAD | stat.S_IWRITE)
        os.chmod(error_log_path, stat.S_IREAD | stat.S_IWRITE)
        super(GunicornLogger, self).__init__(cfg)

    def now(self):
        """Get log format."""
        return time.strftime('[%Y-%m-%d-%H:%M:%S %z]')

    def setup(self, cfg):
        """Rewrite the setup method of Logger, and we don't need to do anything"""


def start():
    """Start web service."""
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

    error_log_abspath = _get_error_log_path()

    # Init the logger file
    setup_logger('gunicorn', 'error')
    log_handler = open(error_log_abspath, 'a+')
    pre_log_pos = _get_file_size(error_log_abspath)
    # start server
    process = subprocess.Popen(
        shlex.split(cmd),
        shell=False,
        # Change stdout to DEVNULL to prevent broken pipe error when creating new processes.
        stdin=subprocess.DEVNULL,
        stdout=log_handler,
        stderr=subprocess.STDOUT
    )

    # sleep 1 second for gunicorn application to load modules
    time.sleep(1)

    # check if gunicorn application is running
    console = setup_logger('mindinsight', 'console', console=True, logfile=False, formatter='%(message)s')
    if process.poll() is not None:
        console.error("Start MindInsight failed. See log for details, log path: %s.", error_log_abspath)
        sys.exit(1)
    else:
        state_result = _check_server_start_stat(process.pid, error_log_abspath, pre_log_pos)
        # print gunicorn start state to stdout
        label = 'Web address:'
        format_args = label, settings.HOST, str(settings.PORT), settings.URL_PATH_PREFIX
        console.info('%s http://%s:%s%s', *format_args)
        for line in state_result["prompt_message"]:
            console.info(line)
        if state_result["state"] == ServerStateEnum.FAILED.value:
            sys.exit(1)


if __name__ == '__main__':
    start()

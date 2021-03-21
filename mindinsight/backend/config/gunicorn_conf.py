# Copyright 2019-2021 Huawei Technologies Co., Ltd
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
"""Config file for gunicorn."""

import os
import time
import signal
import sys
import multiprocessing
import threading
from importlib import import_module

import psutil
import gunicorn

from mindinsight.utils.computing_resource_mgr import terminate


gunicorn.SERVER_SOFTWARE = 'unknown'

worker_class = 'sync'
workers = 1
threads = min(30, os.cpu_count() * 2 + 1)
worker_connections = 1000

timeout = 30
graceful_timeout = 30
daemon = False

captureoutput = False

# write gunicorn default log to devnull, and using mindinsight logger write gunicorn log to file.
accesslog = os.devnull


def on_starting(server):
    """Hook function on starting gunicorn process."""
    hook_module = import_module('mindinsight.utils.hook')
    for hook in hook_module.HookUtils.instance().hooks():
        threading.Thread(target=hook.on_startup, args=(server.log,)).start()


# This global variable is to manage the listen process so that we can close the
# process when gunicorn is exiting.
LISTEN_PROCESS = None


def post_worker_init(worker):
    """
    Launch a process to listen worker after gunicorn worker is initialized.

    Children processes of gunicorn worker should be killed when worker has been killed
    because gunicorn master murders this worker for some reasons such as worker timeout.

    Args:
        worker (ThreadWorker): worker instance.
    """
    def murder_worker_children_processes():
        signal.signal(
            signal.SIGTERM,
            lambda signal_num, handler: sys.exit(0))
        processes_to_kill = []
        # sleep 3 seconds so that all worker children processes have been launched.
        time.sleep(3)
        process = psutil.Process(worker.pid)
        for child in process.children(recursive=True):
            if child.pid != os.getpid():
                processes_to_kill.append(child)
        while True:
            if os.getppid() != worker.pid:
                # Kill the remaining sub-processed after the worker process died
                _, alive = psutil.wait_procs(processes_to_kill, 0.1)
                current_worker_pid = os.getppid()
                for proc in alive:
                    worker.log.info("Original worker pid: %d, current worker pid: %d, stop process %d",
                                    worker.pid, current_worker_pid, proc.pid)
                    try:
                        proc.send_signal(signal.SIGKILL)
                    except psutil.NoSuchProcess:
                        continue
                    except psutil.Error as ex:
                        worker.log.error("Stop process %d failed. Detail: %s.", proc.pid, str(ex))
                worker.log.info("%d processes have been terminated by listener.", len(alive))
                break
            time.sleep(1)

    listen_process = multiprocessing.Process(target=murder_worker_children_processes,
                                             name="murder_worker_children_processes")
    listen_process.start()
    global LISTEN_PROCESS
    LISTEN_PROCESS = listen_process
    worker.log.info("Server pid: %d, start to listening.", worker.ppid)


def worker_int(worker):
    """Terminate child processes when worker is interrupted."""
    terminate()
    global LISTEN_PROCESS
    if LISTEN_PROCESS is not None:
        LISTEN_PROCESS.terminate()
    worker.log.info("Worker int processed.")

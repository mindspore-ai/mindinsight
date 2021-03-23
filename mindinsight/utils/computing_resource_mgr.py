# Copyright 2020-2021 Huawei Technologies Co., Ltd
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
"""Compute resource manager."""


import functools
import multiprocessing
import threading
from concurrent import futures

import _thread

from mindinsight.utils.log import setup_logger

_MP_CONTEXT = multiprocessing.get_context(method="forkserver")


class ComputingResourceManager:
    """
    Manager for computing resources.

    Note:
        1. Please always use the get_instance method to get instance.
        2. This class will be used in a multi-threaded env, so it needs to be
           thread-safe.
    """
    _cls_lock = threading.Lock()
    _instance = None
    _exiting = False

    def __init__(self):
        self._executors = {}
        self._executor_id_counter = 1
        self._lock = threading.Lock()
        self._exiting = False
        self._logger = setup_logger("utils", "utils")

    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        with cls._cls_lock:
            if cls._instance is None:
                cls._instance = ComputingResourceManager()
            return cls._instance

    def exit(self):
        """
        Called when the gunicorn worker process is exiting.

        This method will be called in the signal handling thread, which is not
        the same thread with get_executor. Also, this method will hold the lock
        to block other threads from operating the singleton or executors.
        """
        with self._lock:
            self._logger.info("Start to exit.")
            self._exiting = True
            for executor in self._executors.values():
                # It's safe to call executor.shutdown() multiple times.
                executor.shutdown(wait=True)
        self._logger.info("Exited.")

    def get_executor(self, max_processes_cnt=1):
        """
        Get an executor.

        This method may be called by different business from different threads.
        So it needs to be tread-safe.
        """
        with self._lock:
            if self._exiting:
                self._logger.info(
                    "System is exiting, will terminate the thread.")
                _thread.exit()

            executor = Executor(
                max_processes_cnt=max_processes_cnt,
                exit_callback=functools.partial(
                    self._remove_executor,
                    executor_id=self._executor_id_counter),
                exit_check_fn=self._check_exit
            )

            self._executors[self._executor_id_counter] = executor
            self._executor_id_counter += 1
            return executor

    def _remove_executor(self, executor_id):
        with self._lock:
            self._executors.pop(executor_id)

    def _check_exit(self):
        with self._lock:
            return self._exiting


class Executor:
    """
    Wrapped ProcessPoolExecutor to help global management.

    Args:
        max_processes_cnt (int): Max processes to use.
        exit_callback (Callable): A callback that will be called after process
            pool exit.
        exit_check_fn (Callable): A function to check whether the system is
            exiting.
    """
    def __init__(self, max_processes_cnt, exit_callback, exit_check_fn):
        self._backend = futures.ProcessPoolExecutor(
            max_workers=max_processes_cnt,
            mp_context=_MP_CONTEXT)
        self._exit_callback = exit_callback
        self._task_slots = threading.Semaphore(value=max_processes_cnt)
        self._exit_check_fn = exit_check_fn
        self._logger = setup_logger("utils", "utils")

    def __enter__(self):
        self._backend.__enter__()
        return self

    def __exit__(self, *args, **kwargs):
        ret = self._backend.__exit__(*args, **kwargs)
        self._exit_callback()
        return ret

    def submit(self, *args, **kwargs):
        if self._exit_check_fn():
            self._logger.warning(
                "System exiting, will terminate current thread.")
            _thread.exit()
        self._task_slots.acquire()
        future = self._backend.submit(*args, **kwargs)
        # The future object is not needed for releasing semaphores.
        future.add_done_callback(lambda future_obj: self._task_slots.release())
        return future

    submit.__doc__ = futures.Executor.submit.__doc__

    def shutdown(self, wait):
        self._backend.shutdown(wait)

    shutdown.__doc__ = futures.Executor.shutdown.__doc__


def terminate():
    """Set the terminating flag."""
    ComputingResourceManager.get_instance().exit()

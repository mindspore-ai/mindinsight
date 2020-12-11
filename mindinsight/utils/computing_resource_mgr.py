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
"""Compute resource manager."""
import fractions
import math
import threading
import multiprocessing
from concurrent import futures

from mindinsight.utils.log import setup_logger
from mindinsight.utils.constant import GeneralErrors
from mindinsight.utils.exceptions import MindInsightException


_MP_CONTEXT = multiprocessing.get_context(method="forkserver")


class ComputingResourceManager:
    """
    Manager for computing resources.

    This class provides executors for computing tasks. Executors can only be used once.

    Args:
        executors_cnt (int): Number of executors to be provided by this class.
        max_processes_cnt (int): Max number of processes to be used for computing.
    """
    def __init__(self, executors_cnt=1, max_processes_cnt=4):
        self._max_processes_cnt = max_processes_cnt
        self._executors_cnt = executors_cnt
        self._lock = threading.Lock()
        self._executors = {
            ind: Executor(
                self, executor_id=ind,
                available_workers=fractions.Fraction(self._max_processes_cnt, self._executors_cnt))
            for ind in range(self._executors_cnt)
        }
        self._remaining_executors = len(self._executors)
        self._backend = futures.ProcessPoolExecutor(max_workers=max_processes_cnt, mp_context=_MP_CONTEXT)
        self.logger = setup_logger("utils", "utils")
        self.logger.info("Initialized ComputingResourceManager with executors_cnt=%s, max_processes_cnt=%s.",
                         executors_cnt, max_processes_cnt)

    def __enter__(self):
        """This method is not thread safe."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        This should not block because every executor have waited. If it blocks, there may be some problem.

        This method is not thread safe.
        """
        self._backend.shutdown()

    def get_executor(self):
        """
        Get an executor.

        Returns:
            Executor, which can be used for submitting tasks.

        Raises:
            ComputeResourceManagerException: when no more executor is available.
        """
        with self._lock:
            self._remaining_executors -= 1
            if self._remaining_executors < 0:
                raise ComputingResourceManagerException("No more executors.")
            return self._executors[self._remaining_executors]

    def destroy_executor(self, executor_id):
        """
        Destroy an executor to reuse it's workers.

        Args:
            executor_id (int): Id of the executor to be destroyed.
        """
        with self._lock:
            released_workers = self._executors[executor_id].available_workers
            self._executors.pop(executor_id)

            remaining_executors = len(self._executors)
            self.logger.info("Destroy executor %s. Will release %s worker(s). Remaining executors: %s.",
                             executor_id, released_workers, remaining_executors)
            if not remaining_executors:
                return

            for executor in self._executors.values():
                executor.add_worker(
                    fractions.Fraction(
                        released_workers.numerator,
                        released_workers.denominator * remaining_executors))

    def submit(self, *args, **kwargs):
        """
        Submit a task.

        See concurrent.futures.Executor.submit() for details.

        This method should only be called by Executor. Users should not call this method directly.
        """
        with self._lock:
            return self._backend.submit(*args, **kwargs)


class ComputingResourceManagerException(MindInsightException):
    """
    Indicates a computing resource error has occurred.

    This exception should not be presented to end users.

    Args:
        msg (str): Exception message.
    """
    def __init__(self, msg):
        super().__init__(error=GeneralErrors.COMPUTING_RESOURCE_ERROR, message=msg)


class WrappedFuture:
    """
    Wrap Future objects with custom logics to release compute slots.

    Args:
         executor (Executor): The executor which generates this future.
         original_future (futures.Future): Original future object.
    """
    def __init__(self, executor, original_future: futures.Future):
        self._original_future = original_future
        self._executor = executor
        self.logger = setup_logger("utils", "utils")

    def add_done_callback(self, callback):
        """
        Add done callback.

        See futures.Future.add_done_callback() for details.
        """
        def _wrapped_callback(*args, **kwargs):
            self.logger.debug("Future callback called.")
            try:
                return callback(*args, **kwargs)
            finally:
                self._executor.release_slot()
                self._executor.remove_done_future(self._original_future)
        self._original_future.add_done_callback(_wrapped_callback)


class Executor:
    """
    Task executor.

    Args:
        mgr (ComputingResourceManager): The ComputingResourceManager that generates this executor.
        executor_id (int): Executor id.
        available_workers (fractions.Fraction): Available workers.
    """
    def __init__(self, mgr: ComputingResourceManager, executor_id, available_workers):
        self._mgr = mgr
        self.closed = False
        self._available_workers = available_workers
        self._effective_workers = self._calc_effective_workers(self._available_workers)
        self._slots = threading.Semaphore(value=self._effective_workers)
        self._id = executor_id
        self._futures = set()

        self._lock = threading.Lock()
        self.logger = setup_logger("utils", "utils")
        self.logger.debug("Available workers: %s.", available_workers)

    def __enter__(self):
        """This method is not thread safe."""
        if self.closed:
            raise ComputingResourceManagerException("Can not reopen closed executor.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """This method is not thread safe."""
        self._close()

    def submit(self, *args, **kwargs):
        """
        Submit task.

        See concurrent.futures.Executor.submit() for details. This method is not thread safe.
        """
        self.logger.debug("Task submitted to executor %s.", self._id)

        if self.closed:
            raise ComputingResourceManagerException("Cannot submit task to a closed executor.")

        # Thread will wait on acquire().
        self._slots.acquire()
        future = self._mgr.submit(*args, **kwargs)

        # set.add is atomic in c-python.
        self._futures.add(future)
        return WrappedFuture(self, future)

    def release_slot(self):
        """
        Release a slot for new tasks to be submitted.

        Semaphore is itself thread safe, so no lock is needed.

        This method should only be called by ExecutorFuture.
        """
        self._slots.release()

    def remove_done_future(self, future):
        """
        Remove done futures so the executor will not track them.

        This method should only be called by WrappedFuture.
        """
        # set.remove is atomic in c-python so no lock is needed.
        self._futures.remove(future)

    @staticmethod
    def _calc_effective_workers(available_workers):
        return 1 if available_workers <= 1 else math.floor(available_workers)

    def _close(self):
        self.closed = True
        self.logger.debug("Executor is being closed, futures to wait: %s", self._futures)
        futures.wait(self._futures)
        self.logger.debug("Executor wait futures completed.")
        self._mgr.destroy_executor(self._id)
        self.logger.debug("Executor is closed.")

    @property
    def available_workers(self):
        """Get available workers."""
        with self._lock:
            return self._available_workers

    def add_worker(self, added_available_workers):
        """This method should only be called by ComputeResourceManager."""
        self.logger.debug("Add worker: %s", added_available_workers)
        with self._lock:
            self._available_workers += added_available_workers
            new_effective_workers = self._calc_effective_workers(self._available_workers)
            if new_effective_workers > self._effective_workers:
                for _ in range(new_effective_workers - self._effective_workers):
                    self._slots.release()

            self._effective_workers = new_effective_workers

    def wait_all_tasks_finish(self):
        """
        Wait all tasks finish.

        This method is not thread safe.
        """
        futures.wait(self._futures)

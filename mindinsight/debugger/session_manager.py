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
"""Implement the session manager."""
import os
import threading
from urllib.parse import unquote

import _thread

from mindinsight.conf import settings
from mindinsight.debugger.common.log import LOGGER as logger
from mindinsight.debugger.common.exceptions.exceptions import DebuggerSessionNumOverBoundError, \
    DebuggerSessionNotFoundError, DebuggerOnlineSessionUnavailable
from mindinsight.debugger.debugger_services.debugger_server_factory import DebuggerServerContext
from mindinsight.debugger.debugger_session import DebuggerSession


class SessionManager:
    """The server manager of debugger."""

    ONLINE_TYPE = "ONLINE"
    MAX_OFFLINE_SESSION_NUM = settings.MAX_OFFLINE_DEBUGGER_SESSION_NUM
    ONLINE_SESSION_ID = "0"
    _instance = None
    _cls_lock = threading.Lock()

    def __init__(self):
        self.train_jobs = {}
        self.sessions = {}
        # The offline session id is start from 1, and the online session id is 0.
        self._next_session_id = 1
        self._lock = threading.Lock()
        self._exiting = False
        enable_debugger = settings.ENABLE_DEBUGGER if hasattr(settings, 'ENABLE_DEBUGGER') else False
        if enable_debugger:
            self._create_online_session()

    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        with cls._cls_lock:
            if cls._instance is None:
                cls._instance = SessionManager()
            return cls._instance

    def exit(self):
        """Called when the gunicorn worker process is exiting."""
        with self._lock:
            logger.info("Start to exit sessions.")
            self._exiting = True
            for session in self.sessions.values():
                session.stop()
        logger.info("Sessions exited.")

    def get_session(self, session_id):
        """
        Get session by session id or get all session info.

        Args:
            session_id (Union[None, str]): The id of session.

        Returns:
            DebuggerSession, debugger session object.
        """
        with self._lock:
            if session_id in self.sessions:
                return self.sessions.get(session_id)

            logger.error('Debugger session %s is not found.', session_id)
            raise DebuggerSessionNotFoundError("{}".format(session_id))

    def _create_online_session(self):
        """Create online session."""
        with self._lock:
            context = DebuggerServerContext(dbg_mode='online')
            online_session = DebuggerSession(context)
            online_session.start()
            self.sessions[self.ONLINE_SESSION_ID] = online_session

    def _create_offline_session(self, train_job):
        """Create offline session."""
        self._check_session_num()
        if not isinstance(train_job, str):
            logger.error('The train job path should be string.')
            raise ValueError("The train job path should be string.")
        summary_base_dir = settings.SUMMARY_BASE_DIR
        unquote_path = unquote(train_job, errors='strict')
        whole_path = os.path.join(summary_base_dir, unquote_path)
        normalized_path = validate_and_normalize_path(whole_path)
        context = DebuggerServerContext(dbg_mode='offline', train_job=train_job, dbg_dir=normalized_path)
        session = DebuggerSession(context)
        session.start()
        session_id = str(self._next_session_id)
        self.sessions[session_id] = session
        self.train_jobs[train_job] = session_id
        self._next_session_id += 1
        return session_id

    def create_session(self, session_type, train_job=None):
        """
        Create the session by the train job info or session type if the session doesn't exist.

        Args:
            session_type (str): The session_type.
            train_job (str): The train job info.

        Returns:
            str, session id.
        """
        with self._lock:
            if self._exiting:
                logger.info(
                    "System is exiting, will terminate the thread.")
                _thread.exit()

            if session_type == self.ONLINE_TYPE:
                if self.ONLINE_SESSION_ID not in self.sessions:
                    logger.error(
                        'Online session is unavailable, set --enable-debugger as true/1 to enable debugger '
                        'when start Mindinsight server.')
                    raise DebuggerOnlineSessionUnavailable()
                return self.ONLINE_SESSION_ID

            if train_job in self.train_jobs:
                return self.train_jobs.get(train_job)

            return self._create_offline_session(train_job)

    def delete_session(self, session_id):
        """Delete session by session id."""
        with self._lock:
            if session_id == self.ONLINE_SESSION_ID:
                logger.error('Online session can not be deleted.')
                raise ValueError("Online session can not be delete.")

            if session_id not in self.sessions:
                logger.error('Debugger session %s is not found', session_id)
                raise DebuggerSessionNotFoundError("session id {}".format(session_id))

            session = self.sessions.get(session_id)
            session.stop()
            self.sessions.pop(session_id)
            self.train_jobs.pop(session.train_job)
            return

    def get_train_jobs(self):
        """Get all train jobs."""
        return {"train_jobs": self.train_jobs}

    def _check_session_num(self):
        """Check the amount of sessions."""
        session_limitation = self.MAX_OFFLINE_SESSION_NUM
        if self.ONLINE_SESSION_ID in self.sessions:
            session_limitation += 1
        if len(self.sessions) >= session_limitation:
            logger.warning('Offline debugger session num %s is reach the limitation %s', len(self.sessions),
                           session_limitation)
            raise DebuggerSessionNumOverBoundError()


def validate_and_normalize_path(path):
    """Validate and normalize_path"""
    if not path:
        logger.error('The whole path of dump directory is None.')
        raise ValueError("The whole path of dump directory is None.")

    path_str = str(path)

    if not path_str.startswith("/"):
        logger.error('The whole path of dump directory is not start with \'/\'')
        raise ValueError("The whole path of dump directory is not start with \'/\'")

    try:
        normalized_path = os.path.realpath(path)
    except ValueError:
        logger.error('The whole path of dump directory is invalid.')
        raise ValueError("The whole path of dump directory is invalid.")

    return normalized_path

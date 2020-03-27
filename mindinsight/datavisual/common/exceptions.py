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
"""Define custom exception."""

from mindinsight.utils.constant import DataVisualErrors
from mindinsight.utils.exceptions import MindInsightException


class RestfulApiNotExist(MindInsightException):
    """404 not found."""
    def __init__(self):
        error_msg = '404 Not Found.'
        super(RestfulApiNotExist, self).__init__(DataVisualErrors.RESTFUL_API_NOT_EXIST,
                                                 error_msg,
                                                 http_code=404)


class RequestMethodNotAllowed(MindInsightException):
    """Request method not allowed."""
    def __init__(self):
        error_msg = '405 Method Not Allowed.'
        super(RequestMethodNotAllowed, self).__init__(DataVisualErrors.REQUEST_METHOD_NOT_ALLOWED,
                                                      error_msg,
                                                      http_code=405)


class PathNotDirectoryError(MindInsightException):
    """Raised when specified path do not exist."""
    def __init__(self, error_detail):
        """Initialize PathNotExistError"""
        error_msg = 'Specified path is not a directory. Detail: {}'.format(error_detail)
        super(PathNotDirectoryError, self).__init__(DataVisualErrors.PATH_NOT_DIRECTORY_ERROR,
                                                    error_msg,
                                                    http_code=400)


class SummaryLogPathInvalid(MindInsightException):
    """No valid log file in the path."""
    def __init__(self):
        error_msg = 'No valid summary log file in path'
        super(SummaryLogPathInvalid, self).__init__(DataVisualErrors.SUMMARY_LOG_PATH_INVALID,
                                                    error_msg,
                                                    http_code=400)


class CRCFailedError(MindInsightException):
    """CRC fail, record corrupted."""
    def __init__(self):
        error_msg = 'CRC Failed.'
        super(CRCFailedError, self).__init__(DataVisualErrors.CRC_FAILED,
                                             error_msg,
                                             http_code=400)


class SummaryLogIsLoading(MindInsightException):
    """Data is loading."""

    def __init__(self, error_detail):
        error_msg = "Data is loading. Detail: %s" % error_detail
        super(SummaryLogIsLoading, self).__init__(DataVisualErrors.SUMMARY_LOG_IS_LOADING,
                                                  error_msg,
                                                  http_code=400)


class NodeNotInGraphError(MindInsightException):
    """Can not find node in graph error."""
    def __init__(self):
        error_msg = "Can not find node in graph by given node name."
        super(NodeNotInGraphError, self).__init__(DataVisualErrors.NODE_NOT_IN_GRAPH_ERROR,
                                                  error_msg,
                                                  http_code=400)

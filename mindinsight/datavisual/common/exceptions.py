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
    def __init__(self, node_name, node_type=None):
        if node_type is not None:
            error_msg = f"Can not find node in graph by the given node name. node name: {node_name}, type: {node_type}."
        else:
            error_msg = f"Can not find node in graph by the given node name. node name: {node_name}."
        super(NodeNotInGraphError, self).__init__(DataVisualErrors.NODE_NOT_IN_GRAPH_ERROR,
                                                  error_msg,
                                                  http_code=400)


class MaxCountExceededError(MindInsightException):
    """Count is out of limit."""
    def __init__(self):
        error_msg = "Count is out of limit."
        super(MaxCountExceededError, self).__init__(DataVisualErrors.MAX_COUNT_EXCEEDED_ERROR,
                                                    error_msg,
                                                    http_code=400)


class TrainJobNotExistError(MindInsightException):
    """Can not find the given train job."""
    def __init__(self, error_detail=None):
        if error_detail is None:
            error_msg = f"Train job is not exist."
        else:
            error_msg = f"Train job is not exist. Detail: {error_detail}"
        super(TrainJobNotExistError, self).__init__(DataVisualErrors.TRAIN_JOB_NOT_EXIST,
                                                    error_msg,
                                                    http_code=400)


class PluginNotAvailableError(MindInsightException):
    """The given plugin is not available."""
    def __init__(self, error_detail):
        error_msg = f"Plugin is not available. Detail: {error_detail}"
        super(PluginNotAvailableError, self).__init__(DataVisualErrors.PLUGIN_NOT_AVAILABLE,
                                                      error_msg,
                                                      http_code=400)


class GraphNotExistError(MindInsightException):
    """Can not found the given graph."""
    def __init__(self):
        error_msg = 'Graph is not exist.'
        super(GraphNotExistError, self).__init__(DataVisualErrors.GRAPH_NOT_EXIST,
                                                 error_msg,
                                                 http_code=400)


class ImageNotExistError(MindInsightException):
    """Unable to get a image based on a given condition."""
    def __init__(self, error_detail):
        error_msg = f'Image is not exist. Detail: {error_detail}'
        super(ImageNotExistError, self).__init__(DataVisualErrors.IMAGE_NOT_EXIST,
                                                 error_msg,
                                                 http_code=400)


class ScalarNotExistError(MindInsightException):
    """Unable to get scalar values based on a given condition."""
    def __init__(self, error_detail):
        error_msg = f'Scalar value is not exist. Detail: {error_detail}'
        super(ScalarNotExistError, self).__init__(DataVisualErrors.SCALAR_NOT_EXIST,
                                                  error_msg,
                                                  http_code=400)

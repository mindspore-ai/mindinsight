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
    def __init__(self, error_detail):
        error_msg = 'CRC Failed. Detail: %s' % error_detail
        super(CRCFailedError, self).__init__(DataVisualErrors.CRC_FAILED,
                                             error_msg,
                                             http_code=400)


class CRCLengthFailedError(MindInsightException):
    """CRC length fail, record corrupted."""
    def __init__(self, error_detail):
        error_msg = 'CRC Length Failed. Detail: %s' % error_detail
        super(CRCLengthFailedError, self).__init__(DataVisualErrors.CRC_LENGTH_FAILED,
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


class QueryStringContainsNullByteError(MindInsightException):
    """Query string contains null byte error."""
    def __init__(self, error_detail):
        error_msg = f"Query string contains null byte error. Detail: {error_detail}"
        super(QueryStringContainsNullByteError, self).__init__(DataVisualErrors.QUERY_STRING_CONTAINS_NULL_BYTE,
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
    def __init__(self, error_detail=None):
        error_msg = 'Graph is not exist.' if error_detail is None else f'Graph is not exist. Detail: {error_detail}'
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


class HistogramNotExistError(MindInsightException):
    """Unable to get histogram values based on a given condition."""
    def __init__(self, error_detail):
        error_msg = f'Histogram value is not exist. Detail: {error_detail}'
        super(HistogramNotExistError, self).__init__(DataVisualErrors.HISTOGRAM_NOT_EXIST,
                                                     error_msg,
                                                     http_code=400)


class TensorNotExistError(MindInsightException):
    """Unable to get tensor values based on a given condition."""
    def __init__(self, error_detail):
        error_msg = f'Tensor value is not exist. Detail: {error_detail}'
        super(TensorNotExistError, self).__init__(DataVisualErrors.TENSOR_NOT_EXIST,
                                                  error_msg,
                                                  http_code=400)


class StepTensorDataNotInCacheError(MindInsightException):
    """Tensor data with specific step does not in cache."""
    def __init__(self, error_detail):
        error_msg = f'Tensor data not in cache. Detail: {error_detail}'
        super(StepTensorDataNotInCacheError, self).__init__(DataVisualErrors.STEP_TENSOR_DATA_NOT_IN_CACHE,
                                                            error_msg,
                                                            http_code=400)


class ResponseDataExceedMaxValueError(MindInsightException):
    """Response data exceed max value based on a given condition."""
    def __init__(self, error_detail):
        error_msg = f'Response data exceed max value. Detail: {error_detail}'
        super(ResponseDataExceedMaxValueError, self).__init__(DataVisualErrors.MAX_RESPONSE_DATA_EXCEEDED_ERROR,
                                                              error_msg,
                                                              http_code=400)


class TrainJobDetailNotInCacheError(MindInsightException):
    """Detail info of given train job is not in cache."""
    def __init__(self, error_detail="no detail provided."):
        error_msg = f'Detail info of the given train job is not in cache. Detail: {error_detail}'
        super().__init__(DataVisualErrors.TRAIN_JOB_DETAIL_NOT_IN_CACHE,
                         error_msg,
                         http_code=400)


class TensorTooLargeError(MindInsightException):
    """The given tensor is too large to shown on UI."""
    def __init__(self, error_detail):
        error_msg = f'Tensor is too large to show on UI. Detail: {error_detail}'
        super(TensorTooLargeError, self).__init__(DataVisualErrors.TENSOR_TOO_LARGE,
                                                  error_msg,
                                                  http_code=400)

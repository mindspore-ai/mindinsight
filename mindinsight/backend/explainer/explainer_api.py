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
"""Explainer restful api."""

import json
import os
import urllib.parse

from flask import Blueprint
from flask import jsonify
from flask import request

from mindinsight.conf import settings
from mindinsight.datavisual.common.validation import Validation
from mindinsight.datavisual.data_transform.summary_watcher import SummaryWatcher
from mindinsight.datavisual.utils.tools import get_train_id
from mindinsight.explainer.encapsulator.datafile_encap import DatafileEncap
from mindinsight.explainer.encapsulator.evaluation_encap import EvaluationEncap
from mindinsight.explainer.encapsulator.explain_job_encap import ExplainJobEncap
from mindinsight.explainer.encapsulator.hierarchical_occlusion_encap import HierarchicalOcclusionEncap
from mindinsight.explainer.encapsulator.saliency_encap import SaliencyEncap
from mindinsight.explainer.manager.explain_manager import EXPLAIN_MANAGER
from mindinsight.utils.exceptions import ParamMissError
from mindinsight.utils.exceptions import ParamTypeError
from mindinsight.utils.exceptions import ParamValueError

URL_PREFIX = settings.URL_PATH_PREFIX + settings.API_PREFIX
BLUEPRINT = Blueprint("explainer", __name__, url_prefix=URL_PREFIX)


def _validate_type(param, name, expected_types):
    """
    Common function to validate type.

    Args:
        param (object): Parameter to be validated.
        name (str): Name of the parameter.
        expected_types (type, tuple[type]): Expected type(s) of param.

    Raises:
        ParamTypeError: When param is not an instance of expected_types.
    """

    if not isinstance(param, expected_types):
        raise ParamTypeError(name, expected_types)


def _validate_value(param, name, expected_values):
    """
    Common function to validate values of param.

    Args:
        param (object): Parameter to be validated.
        name (str): Name of the parameter.
        expected_values (tuple) : Expected values of param.

    Raises:
        ParamValueError: When param is not in expected_values.
    """

    if param not in expected_values:
        raise ParamValueError(f"Valid options for {name} are {expected_values}, but got {param}.")


def _image_url_formatter(train_id, image_path, image_type):
    """
    Returns image url.

    Args:
        train_id (str): Id that specifies explain job.
        image_path (str): Local path or unique string that specifies the image for query.
        image_type (str): Image query type.

    Returns:
        str, url string for image query.
    """
    data = {
        "train_id": train_id,
        "path": image_path,
        "type": image_type
    }
    return f"{URL_PREFIX}/explainer/image?{urllib.parse.urlencode(data)}"


def _read_post_request(post_request):
    """
    Extract the body of post request.

    Args:
        post_request (object): The post request.

    Returns:
        dict, the deserialized body of request.
    """
    body = post_request.stream.read()
    try:
        body = json.loads(body if body else "{}")
    except json.decoder.JSONDecodeError:
        raise ParamValueError("Json data parse failed.")
    return body


def _get_query_sample_parameters(data):
    """
    Get parameter for query.

    Args:
        data (dict): Dict that contains request info.

    Returns:
        dict, key-value pairs to call backend query functions.

    Raises:
        ParamMissError: If train_id info is not in the request.
        ParamTypeError: If certain key is not in the expected type in the request.
        ParamValueError: If certain key does not have the expected value in the request.
    """

    train_id = data.get("train_id")
    if train_id is None:
        raise ParamMissError('train_id')

    labels = data.get("labels")
    if labels is not None:
        _validate_type(labels, "labels", list)
    if labels:
        for item in labels:
            _validate_type(item, "element of labels", str)

    limit = data.get("limit", 10)
    limit = Validation.check_limit(limit, min_value=1, max_value=100)
    offset = data.get("offset", 0)
    offset = Validation.check_offset(offset=offset)
    sorted_name = data.get("sorted_name", "")
    _validate_value(sorted_name, "sorted_name", ('', 'confidence', 'uncertainty'))

    sorted_type = data.get("sorted_type", "descending")
    _validate_value(sorted_type, "sorted_type", ("ascending", "descending"))

    prediction_types = data.get("prediction_types")
    if prediction_types is not None:
        _validate_type(prediction_types, "element of labels", list)
    if prediction_types:
        for item in prediction_types:
            _validate_value(item, "element of prediction_types", ('TP', 'FN', 'FP'))

    query_kwarg = {"train_id": train_id,
                   "labels": labels,
                   "limit": limit,
                   "offset": offset,
                   "sorted_name": sorted_name,
                   "sorted_type": sorted_type,
                   "prediction_types": prediction_types}
    return query_kwarg


@BLUEPRINT.route("/explainer/explain-jobs", methods=["GET"])
def query_explain_jobs():
    """
    Query explain jobs.

    Returns:
        Response, contains dict that stores base directory, total number of jobs and their detailed job metadata.

    Raises:
        ParamMissError: If train_id info is not in the request.
        ParamTypeError: If one of (offset, limit) is not integer in the request.
        ParamValueError: If one of (offset, limit) does not have the expected value in the request.
    """
    offset = request.args.get("offset", default=0)
    limit = request.args.get("limit", default=10)
    offset = Validation.check_offset(offset=offset)
    limit = Validation.check_limit(limit, min_value=1, max_value=SummaryWatcher.MAX_SUMMARY_DIR_COUNT)

    encapsulator = ExplainJobEncap(EXPLAIN_MANAGER)
    total, jobs = encapsulator.query_explain_jobs(offset, limit)

    return jsonify({
        'name': os.path.basename(os.path.realpath(settings.SUMMARY_BASE_DIR)),
        'total': total,
        'explain_jobs': jobs,
    })


@BLUEPRINT.route("/explainer/explain-job", methods=["GET"])
def query_explain_job():
    """
    Query explain job meta-data.

    Returns:
        Response, contains dict that stores metadata of the requested job.

    Raises:
        ParamMissError: If train_id info is not in the request.
    """
    train_id = get_train_id(request)
    if train_id is None:
        raise ParamMissError("train_id")
    encapsulator = ExplainJobEncap(EXPLAIN_MANAGER)
    metadata = encapsulator.query_meta(train_id)
    return jsonify(metadata)


@BLUEPRINT.route("/explainer/saliency", methods=["POST"])
def query_saliency():
    """
    Query saliency map related results.

    Returns:
        Response, contains dict that stores number of samples and the detailed sample info.

    Raises:
        ParamTypeError: If certain key is not in the expected type in the request.
        ParamValueError: If certain key does not have the expected value in the request.
    """
    data = _read_post_request(request)
    query_kwarg = _get_query_sample_parameters(data)
    explainers = data.get("explainers")
    if explainers is not None and not isinstance(explainers, list):
        raise ParamTypeError("explainers", (list, None))
    if explainers:
        for item in explainers:
            if not isinstance(item, str):
                raise ParamTypeError("element of explainers", str)

    query_kwarg["explainers"] = explainers

    encapsulator = SaliencyEncap(
        _image_url_formatter,
        EXPLAIN_MANAGER)
    count, samples = encapsulator.query_saliency_maps(**query_kwarg)

    return jsonify({
        "count": count,
        "samples": samples
    })


@BLUEPRINT.route("/explainer/hoc", methods=["POST"])
def query_hoc():
    """
    Query hierarchical occlusion related results.

    Returns:
        Response, contains dict that stores number of samples and the detailed sample info.

    Raises:
        ParamTypeError: If certain key is not in the expected type in the request.
        ParamValueError: If certain key does not have the expected value in the request.
    """
    data = _read_post_request(request)

    query_kwargs = _get_query_sample_parameters(data)

    filter_empty = data.get("drop_empty", True)
    if not isinstance(filter_empty, bool):
        raise ParamTypeError("drop_empty", bool)

    query_kwargs["drop_empty"] = filter_empty

    encapsulator = HierarchicalOcclusionEncap(
        _image_url_formatter,
        EXPLAIN_MANAGER)
    count, samples = encapsulator.query_hierarchical_occlusion(**query_kwargs)

    return jsonify({
        "count": count,
        "samples": samples
    })


@BLUEPRINT.route("/explainer/evaluation", methods=["GET"])
def query_evaluation():
    """
    Query saliency explainer evaluation scores.

    Returns:
        Response, contains dict that stores evaluation scores.

    Raises:
        ParamMissError: If train_id info is not in the request.
    """
    train_id = get_train_id(request)
    if train_id is None:
        raise ParamMissError("train_id")
    encapsulator = EvaluationEncap(EXPLAIN_MANAGER)
    scores = encapsulator.query_explainer_scores(train_id)
    return jsonify({
        "explainer_scores": scores,
    })


@BLUEPRINT.route("/explainer/image", methods=["GET"])
def query_image():
    """
    Query image.

    Returns:
        bytes, image binary content for UI to demonstrate.
    """
    train_id = get_train_id(request)
    if train_id is None:
        raise ParamMissError("train_id")
    image_path = request.args.get("path")
    if image_path is None:
        raise ParamMissError("path")
    image_type = request.args.get("type")
    if image_type is None:
        raise ParamMissError("type")
    if image_type not in ("original", "overlay", "outcome"):
        raise ParamValueError(f"type:{image_type}, valid options: 'original' 'overlay' 'outcome'")

    encapsulator = DatafileEncap(EXPLAIN_MANAGER)
    image = encapsulator.query_image_binary(train_id, image_path, image_type)

    return image


def init_module(app):
    """
    Init module entry.

    Args:
        app (flask.app): The application obj.
    """
    app.register_blueprint(BLUEPRINT)

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
"""
Backend interface module.

This module provides the interfaces to train processors functions.
"""
from flask import Blueprint
from flask import request
from flask import jsonify

from mindinsight.conf import settings
from mindinsight.datavisual.utils.tools import get_train_id
from mindinsight.datavisual.utils.tools import if_nan_inf_to_none
from mindinsight.datavisual.processors.histogram_processor import HistogramProcessor
from mindinsight.datavisual.processors.tensor_processor import TensorProcessor
from mindinsight.datavisual.processors.images_processor import ImageProcessor
from mindinsight.datavisual.processors.scalars_processor import ScalarsProcessor
from mindinsight.datavisual.processors.graph_processor import GraphProcessor
from mindinsight.datavisual.data_transform.data_manager import DATA_MANAGER


BLUEPRINT = Blueprint("train_visual", __name__, url_prefix=settings.URL_PATH_PREFIX+settings.API_PREFIX)


@BLUEPRINT.route("/datavisual/image/metadata", methods=["GET"])
def image_metadata():
    """
    Interface to fetch metadata about the images for the particular run,tag, and zero-indexed sample.

    Returns:
        Response, which contains a list in JSON containing image events, each
            one of which is an object containing items wall_time, step, width,
            height, and query.
    """
    tag = request.args.get("tag")
    train_id = get_train_id(request)

    processor = ImageProcessor(DATA_MANAGER)
    response = processor.get_metadata_list(train_id, tag)
    return jsonify(response)


@BLUEPRINT.route("/datavisual/image/single-image", methods=["GET"])
def single_image():
    """
    Interface to fetch raw image data for a particular image.

    Returns:
        Response, which contains a byte string of image.
    """
    tag = request.args.get("tag")
    step = request.args.get("step")
    train_id = get_train_id(request)

    processor = ImageProcessor(DATA_MANAGER)
    img_data = processor.get_single_image(train_id, tag, step)
    return img_data


@BLUEPRINT.route("/datavisual/scalar/metadata", methods=["GET"])
def scalar_metadata():
    """
    Interface to fetch metadata about the scalars for the particular run and tag.

    Returns:
        Response, which contains a list in JSON containing scalar events, each
            one of which is an object containing items' wall_time, step and value.
    """
    tag = request.args.get("tag")
    train_id = get_train_id(request)

    processor = ScalarsProcessor(DATA_MANAGER)
    response = processor.get_metadata_list(train_id, tag)

    metadatas = response['metadatas']
    for metadata in metadatas:
        value = metadata.get("value")
        metadata["value"] = if_nan_inf_to_none('scalar_value', value)

    return jsonify(response)


@BLUEPRINT.route("/datavisual/graphs/nodes", methods=["GET"])
def graph_nodes():
    """
    Interface to get graph nodes.

    Returns:
        Response, which contains a JSON object.

    """
    name = request.args.get('name', default=None)
    tag = request.args.get("tag", default=None)
    train_id = get_train_id(request)

    graph_process = GraphProcessor(train_id, DATA_MANAGER, tag)
    response = graph_process.list_nodes(scope=name)
    return jsonify(response)


@BLUEPRINT.route("/datavisual/graphs/nodes/names", methods=["GET"])
def graph_node_names():
    """
    Interface to query node names.

    Returns:
        Response, which contains a JSON object.
    """
    search_content = request.args.get("search")
    offset = request.args.get("offset", default=0)
    limit = request.args.get("limit", default=100)
    tag = request.args.get("tag", default=None)
    train_id = get_train_id(request)

    graph_process = GraphProcessor(train_id, DATA_MANAGER, tag)
    resp = graph_process.search_node_names(search_content, offset, limit)
    return jsonify(resp)


@BLUEPRINT.route("/datavisual/graphs/single-node", methods=["GET"])
def graph_search_single_node():
    """
    Interface to search single node.

    Returns:
         Response, which contains a JSON object.
    """
    name = request.args.get("name")
    tag = request.args.get("tag", default=None)
    train_id = get_train_id(request)

    graph_process = GraphProcessor(train_id, DATA_MANAGER, tag)
    resp = graph_process.search_single_node(name)
    return jsonify(resp)


@BLUEPRINT.route("/datavisual/histograms", methods=["GET"])
def histogram():
    """
    Interface to obtain histogram data.

    Returns:
        Response, which contains a JSON object.
    """
    tag = request.args.get("tag", default=None)
    train_id = get_train_id(request)

    processor = HistogramProcessor(DATA_MANAGER)
    response = processor.get_histograms(train_id, tag)
    return jsonify(response)


@BLUEPRINT.route("/datavisual/scalars", methods=["GET"])
def get_scalars():
    """Get scalar data for given train_ids and tags."""
    train_ids = request.args.getlist('train_id')
    tags = request.args.getlist('tag')

    processor = ScalarsProcessor(DATA_MANAGER)
    scalars = processor.get_scalars(train_ids, tags)
    return jsonify({'scalars': scalars})


@BLUEPRINT.route("/datavisual/tensors", methods=["GET"])
def get_tensors():
    """
    Interface to obtain tensor data.

    Returns:
        Response, which contains a JSON object.
    """
    train_ids = request.args.getlist('train_id')
    tags = request.args.getlist('tag')
    step = request.args.get("step", default=None)
    dims = request.args.get("dims", default=None)
    detail = request.args.get("detail", default=None)

    processor = TensorProcessor(DATA_MANAGER)
    response = processor.get_tensors(train_ids, tags, step, dims, detail)
    return jsonify(response)


def init_module(app):
    """
    Init module entry.

    Args:
        app (Flask): The application obj.
    """
    app.register_blueprint(BLUEPRINT)

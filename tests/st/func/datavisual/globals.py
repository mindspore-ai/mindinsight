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
"""
Description: Global variables.
"""
summaries_metadata = dict()
mock_data_manager = None


def get_tags(train_id, plugin_name):
    """
    Get plugins.

    Args:
        train_id (str): The train ID.
        plugin_name (str): The plugin name.

    Returns:
        list, tag names by given `train_id` and `plugin_name`.

    """
    return summaries_metadata.get(train_id).get("plugins").get(plugin_name)


def get_single_image(train_id, tag_name, step):
    """Get single image."""
    data = summaries_metadata.get(train_id).get("actual_values").get(tag_name).get(step)
    return data


def get_metadata(train_id, tag_name):
    """Get metadata."""
    return summaries_metadata.get(train_id).get("metadata").get(tag_name)


def get_train_ids():
    """Get train ids."""
    return list(summaries_metadata.keys())

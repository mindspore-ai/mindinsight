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
"""Takes a generator of values, and collects them for a frontend."""

import collections
import threading

from mindinsight.conf import settings
from mindinsight.datavisual.common.enums import PluginNameEnum
from mindinsight.datavisual.common.log import logger
from mindinsight.datavisual.data_transform import reservoir

# Type of the tensor event from external component
_Tensor = collections.namedtuple('_Tensor', ['wall_time', 'step', 'value', 'filename'])
TensorEvent = collections.namedtuple(
    'TensorEvent', ['wall_time', 'step', 'tag', 'plugin_name', 'value', 'filename'])

# config for `EventsData`
_DEFAULT_STEP_SIZES_PER_TAG = settings.DEFAULT_STEP_SIZES_PER_TAG
_MAX_DELETED_TAGS_SIZE = settings.MAX_TAG_SIZE_PER_EVENTS_DATA * 100
CONFIG = {
    'max_total_tag_sizes': settings.MAX_TAG_SIZE_PER_EVENTS_DATA,
    'max_tag_sizes_per_plugin':
        {
            PluginNameEnum.GRAPH.value: settings.MAX_GRAPH_TAG_SIZE,
            PluginNameEnum.TENSOR.value: settings.MAX_TENSOR_TAG_SIZE
        },
    'max_step_sizes_per_tag':
        {
            PluginNameEnum.SCALAR.value: settings.MAX_SCALAR_STEP_SIZE_PER_TAG,
            PluginNameEnum.IMAGE.value: settings.MAX_IMAGE_STEP_SIZE_PER_TAG,
            PluginNameEnum.GRAPH.value: settings.MAX_GRAPH_STEP_SIZE_PER_TAG,
            PluginNameEnum.HISTOGRAM.value: settings.MAX_HISTOGRAM_STEP_SIZE_PER_TAG,
            PluginNameEnum.TENSOR.value: settings.MAX_TENSOR_STEP_SIZE_PER_TAG
        }
}


class EventsData:
    """
    EventsData is an event data manager.

    It manages the log events generated during a training process.
    The log event records information such as graph, tag, and tensor.
    Data such as tensor can be retrieved based on its tag.
    """

    def __init__(self):
        self._config = CONFIG
        self._max_step_sizes_per_tag = self._config['max_step_sizes_per_tag']

        self._tags = list()
        self._deleted_tags = set()
        self._reservoir_by_tag = {}
        self._reservoir_mutex_lock = threading.Lock()

        self._tags_by_plugin = collections.defaultdict(list)
        self._tags_by_plugin_mutex_lock = collections.defaultdict(threading.Lock)

    def add_tensor_event(self, tensor_event):
        """
        Add a new tensor event to the tensors_data.

        Args:
            tensor_event (TensorEvent): Refer to `TensorEvent` object.
        """
        if not isinstance(tensor_event, TensorEvent):
            raise TypeError('Expect to get data of type `TensorEvent`.')

        tag = tensor_event.tag
        plugin_name = tensor_event.plugin_name

        if tag not in set(self._tags):
            deleted_tag = self._check_tag_out_of_spec(plugin_name)
            if deleted_tag is not None:
                if tag in self._deleted_tags:
                    logger.debug("Tag is in deleted tags: %s.", tag)
                    return
                self.delete_tensor_event(deleted_tag)

            self._tags.append(tag)

        with self._tags_by_plugin_mutex_lock[plugin_name]:
            if tag not in self._tags_by_plugin[plugin_name]:
                self._tags_by_plugin[plugin_name].append(tag)

        with self._reservoir_mutex_lock:
            if tag not in self._reservoir_by_tag:
                reservoir_size = self._get_reservoir_size(tensor_event.plugin_name)
                self._reservoir_by_tag[tag] = reservoir.ReservoirFactory().create_reservoir(
                    plugin_name, reservoir_size
                )

        tensor = _Tensor(wall_time=tensor_event.wall_time,
                         step=tensor_event.step,
                         value=tensor_event.value,
                         filename=tensor_event.filename)

        if self._is_out_of_order_step(tensor_event.step, tensor_event.tag):
            self.purge_reservoir_data(tensor_event.filename, tensor_event.step, self._reservoir_by_tag[tag])

        self._reservoir_by_tag[tag].add_sample(tensor)

    def delete_tensor_event(self, tag):
        """
        This function will delete tensor event by the given tag in memory record.

        Args:
            tag (str): The tag name.
        """
        if len(self._deleted_tags) < _MAX_DELETED_TAGS_SIZE:
            self._deleted_tags.add(tag)
        else:
            logger.warning(
                'Too many deleted tags, %d upper limit reached, tags updating may not function hereafter',
                _MAX_DELETED_TAGS_SIZE)
        logger.info('%r and all related samples are going to be deleted', tag)
        self._tags.remove(tag)
        for plugin_name, lock in self._tags_by_plugin_mutex_lock.items():
            with lock:
                if tag in self._tags_by_plugin[plugin_name]:
                    self._tags_by_plugin[plugin_name].remove(tag)
                    break

        with self._reservoir_mutex_lock:
            if tag in self._reservoir_by_tag:
                self._reservoir_by_tag.pop(tag)

    def list_tags_by_plugin(self, plugin_name):
        """
        Return all the tag names of the plugin.

        Args:
            plugin_name (str): The Plugin name.

        Returns:
            list[str], tags of the plugin.

        Raises:
            KeyError: when plugin name could not be found.
        """
        if plugin_name not in self._tags_by_plugin:
            raise KeyError('Plugin %r could not be found.' % plugin_name)
        with self._tags_by_plugin_mutex_lock[plugin_name]:
            # Return a snapshot to avoid concurrent mutation and iteration issues.
            return sorted(list(self._tags_by_plugin[plugin_name]))

    def tensors(self, tag):
        """
         Return all tensors of the tag.

        Args:
            tag (str): The tag name.

        Returns:
            list[_Tensor], the list of tensors to the tag.
        """
        if tag not in self._reservoir_by_tag:
            raise KeyError('TAG %r could not be found.' % tag)
        return self._reservoir_by_tag[tag].samples()

    def _is_out_of_order_step(self, step, tag):
        """
        If the current step is smaller than the latest one, it is out-of-order step.

        Args:
            step (int): Check if the given step out of order.
            tag (str): The checked tensor of the given tag.

        Returns:
            bool, boolean value.
        """
        if self.tensors(tag):
            tensors = self.tensors(tag)
            last_step = tensors[-1].step
            if step <= last_step:
                return True
        return False

    @staticmethod
    def purge_reservoir_data(filename, start_step, tensor_reservoir):
        """
        Purge all tensor event that are out-of-order step after the given start step.

        Args:
            start_step (int): Urge start step. All previously seen events with
                a greater or equal to step will be purged.
            tensor_reservoir (Reservoir): A `Reservoir` object.

        Returns:
            int, the number of items removed.
        """
        cnt_out_of_order = tensor_reservoir.remove_sample(
            lambda x: x.step < start_step or (x.step > start_step and x.filename == filename))

        return cnt_out_of_order

    def _get_reservoir_size(self, plugin_name):
        max_step_sizes_per_tag = self._config['max_step_sizes_per_tag']
        return max_step_sizes_per_tag.get(plugin_name, _DEFAULT_STEP_SIZES_PER_TAG)

    def _check_tag_out_of_spec(self, plugin_name):
        """
        Check whether the tag is out of specification.

        Args:
            plugin_name (str): The given plugin name.

        Returns:
            Union[str, None], if out of specification, will return the first tag, else return None.

        """
        tag_specifications = self._config['max_tag_sizes_per_plugin'].get(plugin_name)
        if tag_specifications is not None and len(self._tags_by_plugin[plugin_name]) >= tag_specifications:
            deleted_tag = self._tags_by_plugin[plugin_name][0]
            return deleted_tag

        if len(self._tags) >= self._config['max_total_tag_sizes']:
            deleted_tag = self._tags[0]
            return deleted_tag

        return None

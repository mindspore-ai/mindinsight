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
Function:
    Test mindinsight.datavisual.data_transform.events_data.
Usage:
    pytest tests/ut/datavisual
"""
import threading
from collections import namedtuple

import pytest

from mindinsight.conf import settings
from mindinsight.datavisual.data_transform import events_data
from mindinsight.datavisual.data_transform.events_data import EventsData, TensorEvent, _Tensor

from ..mock import MockLogger


class MockReservoir:
    """Use this class to replace reservoir.Reservoir in test."""

    def __init__(self, size):
        self.size = size
        self._samples = [
            _Tensor('wall_time1', 1, 'value1', 'filename1'),
            _Tensor('wall_time2', 2, 'value2', 'filename2'),
            _Tensor('wall_time3', 3, 'value3', 'filename3')
        ]

    def samples(self):
        """Replace the samples function."""

        return self._samples

    def add_sample(self, sample):
        """Replace the add_sample function."""

        self._samples.append(sample)

    def remove_sample(self, sample):
        """Replace the remove_sample function."""

        self._samples.remove(sample)


# use for test parameters when tensor event does not have the required attrs
Event1 = namedtuple('tensor_event', 'EVENT_TAG VALUE')


class TestEventsData:
    """Test EventsData class."""

    def setup_method(self):
        """Mock original logger, init a EventsData object for use."""
        self._ev_data = EventsData()
        self._ev_data._tags_by_plugin = {
            'plugin_name1': [f'tag{i}' for i in range(10)],
            'plugin_name2': [f'tag{i}' for i in range(20, 30)]
        }
        self._ev_data._tags_by_plugin_mutex_lock.update({'plugin_name1': threading.Lock()})
        self._ev_data._reservoir_by_tag = {'tag0': MockReservoir(500), 'new_tag': MockReservoir(500)}
        self._ev_data._tags = [f'tag{i}' for i in range(settings.MAX_TAG_SIZE_PER_EVENTS_DATA)]

    def get_ev_data(self):
        """Get the EventsData object."""
        return self._ev_data

    def test_get_tags_by_plugin_name_with_not_exist_key(self):
        """Test get_tags_by_plugin_name method when key not exist."""

        ev_data = self.get_ev_data()
        with pytest.raises(KeyError):
            ev_data.list_tags_by_plugin('plugin_name3')

    def test_get_tags_by_plugin_name_success(self):
        """Test get_tags_by_plugin_name method success."""

        ev_data = self.get_ev_data()
        res = ev_data.list_tags_by_plugin('plugin_name1')
        assert set(res) == set(f'tag{i}' for i in range(10))

    @pytest.mark.parametrize('t_event', [Event1(1, 2)])
    def test_add_tensor_event_with_not_events_data(self, t_event):
        """Test when given event do not have attrs tag or value."""
        events_data.logger = MockLogger
        ev_data = self.get_ev_data()

        with pytest.raises(TypeError) as ex:
            ev_data.add_tensor_event(t_event)
        assert ex.value.args[0] == 'Expect to get data of type `TensorEvent`.'

    def test_add_tensor_event_success(self):
        """Test add_tensor_event success."""

        ev_data = self.get_ev_data()
        t_event = TensorEvent(wall_time=1, step=4, tag='new_tag',
                              plugin_name='plugin_name1', value='value1', filename='filename')

        ev_data.add_tensor_event(t_event)
        assert 'tag0' not in ev_data._tags
        assert ev_data._tags[-1] == 'new_tag'
        assert 'tag0' not in ev_data._tags_by_plugin['plugin_name1']
        assert 'tag0' not in ev_data._reservoir_by_tag
        assert 'new_tag' in ev_data._tags_by_plugin['plugin_name1']
        assert ev_data._reservoir_by_tag['new_tag'].samples()[-1] == _Tensor(t_event.wall_time, t_event.step,
                                                                             t_event.value, 'filename')

    def test_add_tensor_event_out_of_order(self):
        """Test add_tensor_event success for out_of_order summaries."""
        wall_time = 1
        value = '1'
        tag = 'tag'
        plugin_name = 'scalar'
        file1 = 'file1'
        ev_data = EventsData()
        steps = [i for i in range(2, 10)]
        for step in steps:
            t_event = TensorEvent(wall_time=1, step=step, tag=tag,
                                  plugin_name=plugin_name, value=value, filename=file1)
            ev_data.add_tensor_event(t_event)

        t_event = TensorEvent(wall_time=1, step=1, tag=tag,
                              plugin_name=plugin_name, value=value, filename=file1)
        ev_data.add_tensor_event(t_event)

        # Current steps should be: [1, 2, 3, 4, 5, 6, 7, 8, 9]
        assert len(ev_data._reservoir_by_tag[tag].samples()) == len(steps) + 1

        file2 = 'file2'
        new_steps_1 = [5, 10]
        for step in new_steps_1:
            t_event = TensorEvent(wall_time=1, step=step, tag=tag,
                                  plugin_name=plugin_name, value=value, filename=file2)
            ev_data.add_tensor_event(t_event)
            assert ev_data._reservoir_by_tag[tag].samples()[-1] == _Tensor(wall_time, step, value, file2)

        # Current steps should be: [1, 2, 3, 4, 5, 10]
        steps = [1, 2, 3, 4, 5, 10]
        samples = ev_data._reservoir_by_tag[tag].samples()
        for i in range(len(samples)):
            filename = file1 if samples[i].step < 5 else file2
            assert samples[i] == _Tensor(wall_time, steps[i], value, filename)

        new_steps_2 = [7, 11, 3]
        for step in new_steps_2:
            t_event = TensorEvent(wall_time=1, step=step, tag=tag,
                                  plugin_name=plugin_name, value=value, filename=file2)
            ev_data.add_tensor_event(t_event)

        # Current steps should be: [1, 2, 3, 5, 7, 10, 11], file2: [3, 5, 7, 10, 11]
        steps = [1, 2, 3, 5, 7, 10, 11]
        new_steps_2.extend(new_steps_1)
        samples = ev_data._reservoir_by_tag[tag].samples()
        for i in range(len(samples)):
            filename = file2 if samples[i].step in new_steps_2 else file1
            assert samples[i] == _Tensor(wall_time, steps[i], value, filename)

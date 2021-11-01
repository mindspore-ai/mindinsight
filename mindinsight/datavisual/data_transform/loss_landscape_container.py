# Copyright 2021 Huawei Technologies Co., Ltd
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
"""Loss landscape container, used for converting proto to python object."""
from mindinsight.datavisual.data_transform.tensor_container import TensorContainer


class PointContainer:
    """
    Point data container.

    Args:
        point (mindinsight_summary.proto.LossLandscape.Point): landscape point data.
    """
    def __init__(self, point):
        self._x = TensorContainer(point.x)
        self._y = TensorContainer(point.y)
        self._z = TensorContainer(point.z)

    @property
    def x(self):
        """Get the x-coordinate of the point."""
        return self._x

    @property
    def y(self):
        """Get the y-coordinate of the point."""
        return self._y

    @property
    def z(self):
        """Get the z-coordinate of the point."""
        return self._z


class LossPathContainer:
    """
    LossPath data container.

    Args:
        loss_point (mindinsight_summary.proto.LossLandscape.LossPath): loss path data.
    """
    def __init__(self, loss_point):
        self._intervals = [interval for interval in loss_point.intervals]
        self._points = PointContainer(loss_point.points)

    @property
    def intervals(self):
        """Get the intervals."""
        return self._intervals

    @property
    def points(self):
        """Get the points."""
        return self._points


class MetadataContainer:
    """Metadata container."""
    def __init__(self, metadata):
        self._decomposition = metadata.decomposition
        self._unit = metadata.unit
        self._step_per_epoch = metadata.step_per_epoch

    @property
    def decomposition(self):
        """Get the decomposition."""
        return self._decomposition

    @property
    def unit(self):
        """Get the unit."""
        return self._unit

    @property
    def step_per_epoch(self):
        """Get the step per epoch."""
        return self._step_per_epoch


class LossLandscapeContainer:
    """Loss landscape container."""
    def __init__(self, loss_landscape_message):
        self._landscape = PointContainer(loss_landscape_message.landscape)
        self._loss_path = LossPathContainer(loss_landscape_message.loss_path)
        self._metadata = MetadataContainer(loss_landscape_message.metadata)
        self._convergence_point = PointContainer(loss_landscape_message.convergence_point)

    @property
    def landscape(self):
        """Get the landscape."""
        return self._landscape

    @property
    def loss_path(self):
        """Get the loss_path."""
        return self._loss_path

    @property
    def metadata(self):
        """Get the metadata."""
        return self._metadata

    @property
    def convergence_point(self):
        """Get the convergence_point."""
        return self._convergence_point

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
"""Loss landscape processor Apis."""
from mindinsight.datavisual.common.enums import PluginNameEnum
from mindinsight.datavisual.common.exceptions import TrainJobNotExistError, LandscapeNotExistError
from mindinsight.datavisual.common.log import logger
from mindinsight.datavisual.common.validation import Validation
from mindinsight.datavisual.processors.base_processor import BaseProcessor
from mindinsight.lineagemgr.model import filter_summary_lineage
from mindinsight.utils.exceptions import MindInsightException, ParamValueError
from mindinsight.datavisual.data_transform.tensor_container import TensorContainer


class LandscapeProcessor(BaseProcessor):
    """Landscape processor."""

    def list_intervals(self, train_id):
        """Get the step intervals."""
        Validation.check_param_empty(train_id=train_id)
        train_job = self._data_manager.get_train_job_by_plugin(train_id, PluginNameEnum.LANDSCAPE.value)
        if train_job is None:
            raise TrainJobNotExistError("train_id {}".format(train_id))

        tags = train_job['tags']
        intervals = []
        for tag in tags:
            tensors = self._data_manager.list_tensors(train_id, tag)
            for tensor in tensors:
                loss_landscape = tensor.value
                if self._is_final_landscape(loss_landscape):
                    continue
                # Use the first value and last value to show the step or epoch interval
                intervals.append(dict(
                    id=self._get_interval_id(loss_landscape),
                    value=[loss_landscape.loss_path.intervals[0], loss_landscape.loss_path.intervals[-1]]
                ))
        intervals.sort(key=lambda interval: interval.get("value")[0])
        return dict(intervals=intervals)

    def list_landscapes(self, train_ids, landscape_type='interval', interval_id=None):
        """Get the landscape data for all train jobs."""
        landscapes = []
        for train_id in train_ids:
            if not isinstance(train_id, str) or not train_id.startswith('./'):
                logger.warning("The train id %s is invalid, it should be an relative path", train_id)
                landscape = {"error_code": ParamValueError().error_code, "train_id": train_id}
            else:
                landscape = self._get_landscape(train_id, landscape_type, interval_id)
            landscapes.append(landscape)
        return dict(landscapes=landscapes)

    def _get_landscape(self, train_id, landscape_type, interval_id):
        """Get the landscape data."""
        train_job = self._data_manager.get_train_job_by_plugin(train_id, PluginNameEnum.LANDSCAPE.value)
        if train_job is None:
            logger.warning("The train job for train id %s is not exist.", train_id)
            return {"error_code": TrainJobNotExistError().error_code, "train_id": train_id}

        for tag in train_job['tags']:
            landscape_events = self._data_manager.list_tensors(train_id, tag)
            for landscape_event in landscape_events:
                landscape = {}
                loss_landscape = landscape_event.value
                if landscape_type == 'interval' \
                        and not self._is_final_landscape(loss_landscape) \
                        and self._get_interval_id(loss_landscape) == interval_id:
                    landscape['train_id'] = train_id
                    landscape['points'] = self._get_points(loss_landscape)
                    landscape['path'] = self._get_path(loss_landscape)

                if landscape_type == 'final' and self._is_final_landscape(loss_landscape):
                    landscape['train_id'] = train_id
                    landscape['points'] = self._get_points(loss_landscape)

                if landscape:
                    landscape['metadata'] = self._get_metadata(loss_landscape, train_id)
                    landscape['convergence_point'] = self._get_convergence_point(loss_landscape)
                    return landscape

        logger.warning("The landscape value for train id %s is not found.", train_id)
        return {"error_code": LandscapeNotExistError().error_code, "train_id": train_id}

    @staticmethod
    def _get_interval_id(loss_landscape):
        """Get the interval id."""
        return str(hash(str(loss_landscape.loss_path.intervals)))

    @staticmethod
    def _is_final_landscape(loss_landscape):
        """If the landscape is the final one."""
        return not bool(loss_landscape.loss_path.intervals)

    def _get_points(self, loss_landscape):
        """Get points data."""
        points = dict(
            x=self._transform_tensor_to_list(loss_landscape.landscape.x),
            y=self._transform_tensor_to_list(loss_landscape.landscape.y),
            z=self._transform_tensor_to_list(loss_landscape.landscape.z)
        )
        return points

    def _get_path(self, loss_landscape):
        """Get the path of landscape."""
        path = dict(
            x=self._transform_tensor_to_list(loss_landscape.loss_path.points.x),
            y=self._transform_tensor_to_list(loss_landscape.loss_path.points.y),
            z=self._transform_tensor_to_list(loss_landscape.loss_path.points.z),
            intervals=list(loss_landscape.loss_path.intervals),
        )
        return path

    @staticmethod
    def _transform_tensor_to_list(tensor: TensorContainer):
        """Convert the tensor to list."""
        data = tensor.tensor_value
        return data.tolist()

    def _get_metadata(self, loss_landscape, train_id):
        """Get the metadata."""
        metadata = dict(
            decomposition=loss_landscape.metadata.decomposition,
            unit=loss_landscape.metadata.unit,
            step_per_epoch=loss_landscape.metadata.step_per_epoch
        )
        lineage_data = self._get_lineage_data(train_id)
        metadata.update(lineage_data)
        return metadata

    def _get_lineage_data(self, train_id):
        """Get the lineage data."""
        try:
            lineage_info = filter_summary_lineage(self._data_manager)
        except MindInsightException:
            lineage_info = {}
        lineage_objects = lineage_info.get("object", [])
        for lineage_data in lineage_objects:
            if lineage_data.get("summary_dir") == train_id:
                learning_rate = lineage_data.get('model_lineage', {}).get('learning_rate', None)
                loss = lineage_data.get('model_lineage', {}).get('loss', None)
                result = dict(
                    network=lineage_data.get('model_lineage', {}).get('network', None),
                    learning_rate=format(learning_rate, '6e') if learning_rate is not None else None,
                    optimizer=lineage_data.get('model_lineage', {}).get('optimizer', None),
                    metric=lineage_data.get('model_lineage', {}).get('metric', {}),
                    loss=format(loss, '6e') if loss is not None else None,
                )
                return result
        return dict(
            network=None,
            learning_rate=None,
            optimizer=None,
            metric={},
        )

    def _get_convergence_point(self, loss_landscape):
        """Get the convergence point data."""
        if loss_landscape.convergence_point.x.empty or loss_landscape.convergence_point.y.empty or \
                loss_landscape.convergence_point.z.empty:
            return [0, 0, 0]
        point = [
            self._transform_tensor_to_list(loss_landscape.convergence_point.x)[0],
            self._transform_tensor_to_list(loss_landscape.convergence_point.y)[0],
            self._transform_tensor_to_list(loss_landscape.convergence_point.z)[0],
        ]
        return point

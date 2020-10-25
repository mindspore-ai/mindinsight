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
"""ExplainJob."""

import os
from datetime import datetime
from typing import List, Iterable, Union

from mindinsight.explainer.common.enums import PluginNameEnum
from mindinsight.explainer.common.log import logger
from mindinsight.explainer.manager.explain_parser import _ExplainParser
from mindinsight.explainer.manager.event_parse import EventParser
from mindinsight.datavisual.data_access.file_handler import FileHandler
from mindinsight.datavisual.common.exceptions import TrainJobNotExistError


class ExplainJob:
    """ExplainJob which manage the record in the summary file."""

    def __init__(self,
                 job_id: str,
                 summary_dir: str,
                 create_time: float,
                 latest_update_time: float):

        self._job_id = job_id
        self._summary_dir = summary_dir
        self._parser = _ExplainParser(summary_dir)

        self._event_parser = EventParser(self)
        self._latest_update_time = latest_update_time
        self._create_time = create_time
        self._labels = []
        self._metrics = []
        self._explainers = []
        self._samples_info = {}
        self._labels_info = {}
        self._benchmark = {}
        self._overlay_dict = {}
        self._image_dict = {}

    @property
    def all_classes(self):
        """
        Return a list of label info

        Returns:
            class_objs (List[ClassObj]): a list of class_objects, each object
                contains:

                - id (int): label id
                - label (str): label name
                - sample_count (int): number of samples for each label
        """
        all_classes_return = []
        for label_id, label_info in self._labels_info.items():
            single_info = {'id': label_id,
                           'label': label_info['label'],
                           'sample_count': len(label_info['sample_ids'])}
            all_classes_return.append(single_info)
        return all_classes_return

    @property
    def explainers(self):
        """
        Return a list of explainer names

        Returns:
            list(str), explainer names
        """
        return self._explainers

    @property
    def explainer_scores(self):
        """Return evaluation results for every explainer."""
        return [score for score in self._benchmark.values()]

    @property
    def sample_count(self):
        """
        Return total number of samples in the job.

        Return:
            int, total number of samples

        """
        return len(self._samples_info)

    @property
    def train_id(self):
        """
        Return ID of explain job

        Returns:
            str, id of ExplainJob object
        """
        return self._job_id

    @property
    def metrics(self):
        """
        Return a list of metric names

        Returns:
            list(str), metric names
        """
        return self._metrics

    @property
    def min_confidence(self):
        """
        Return minimum confidence

        Returns:
            min_confidence (float):
        """
        return None

    @property
    def create_time(self):
        """
        Return the create time of summary file

        Returns:
            creation timestamp (float)

        """
        return self._create_time

    @property
    def labels(self):
        """Return the label contained in the job."""
        return self._labels

    @property
    def latest_update_time(self):
        """
        Return last modification time stamp of summary file.

        Returns:
            float, last_modification_time stamp
        """
        return self._latest_update_time

    @latest_update_time.setter
    def latest_update_time(self, new_time: Union[float, datetime]):
        """
        Update the latest_update_time timestamp manually.

        Args:
            new_time stamp (union[float, datetime]): updated time for the job
        """
        if isinstance(new_time, datetime):
            self._latest_update_time = new_time.timestamp()
        elif isinstance(new_time, str):
            self._latest_update_time = new_time
        else:
            raise TypeError('new_time should have type of str or datetime')

    @property
    def loader_id(self):
        """Return the job id."""
        return self._job_id

    @property
    def samples(self):
        """Return the information of all samples in the job."""
        return self._samples_info

    @staticmethod
    def get_create_time(file_path: str) -> float:
        """Return timestamp of create time of specific path."""
        create_time = os.stat(file_path).st_ctime
        return create_time

    @staticmethod
    def get_update_time(file_path: str) -> float:
        """Return timestamp of update time of specific path."""
        update_time = os.stat(file_path).st_mtime
        return update_time

    @staticmethod
    def _total_score_to_dict(total_scores: Iterable):
        """Transfer a list of benchmark score to a list of dict."""
        evaluation_info = []
        for total_score in total_scores:
            metric_result = {'metric': total_score.benchmark_method,
                             'score': total_score.score}
            evaluation_info.append(metric_result)
        return evaluation_info

    @staticmethod
    def _label_score_to_dict(label_scores: Iterable, labels: List[str]):
        """Transfer a list of benchmark score."""
        evaluation_info = [{'label': label, 'evaluations': []}
                           for label in labels]
        for label_score in label_scores:
            metric = label_score.benchmark_method
            for i, score in enumerate(label_score.score):
                label_metric_score = dict()
                label_metric_score['metric'] = metric
                label_metric_score['score'] = score
                evaluation_info[i]['evaluations'].append(label_metric_score)
        return evaluation_info

    def _initialize_labels_info(self):
        """Initialize a dict for labels in the job."""
        if self._labels is None:
            logger.warning('No labels is provided in job %s', self._job_id)
            return

        for label_id, label in enumerate(self._labels):
            self._labels_info[label_id] = {'label': label,
                                           'sample_ids': set()}

    def _explanation_to_dict(self, explanation, sample_id):
        """Transfer the explanation from event to dict storage."""
        explainer_name = explanation.explain_method
        explain_label = explanation.label
        saliency = explanation.heatmap
        saliency_id = '{}_{}_{}'.format(
            sample_id, explain_label, explainer_name)
        explain_info = {
            'explainer': explainer_name,
            'overlay': saliency_id,
        }
        self._overlay_dict[saliency_id] = saliency
        return explain_info

    def _image_container_to_dict(self, sample_data):
        """Transfer the image container to dict storage."""
        sample_id = sample_data.image_id

        sample_info = {
            'id': sample_id,
            'name': sample_id,
            'labels': [self._labels_info[x]['label']
                       for x in sample_data.ground_truth_label],
            'inferences': []}
        self._image_dict[sample_id] = sample_data.image_data

        ground_truth_labels = list(sample_data.ground_truth_label)
        ground_truth_probs = list(sample_data.inference.ground_truth_prob)
        predicted_labels = list(sample_data.inference.predicted_label)
        predicted_probs = list(sample_data.inference.predicted_prob)

        inference_info = {}
        for label, prob in zip(
                ground_truth_labels + predicted_labels,
                ground_truth_probs + predicted_probs):
            inference_info[label] = {
                'label': self._labels_info[label]['label'],
                'confidence': prob,
                'saliency_maps': []}

        if EventParser.is_attr_ready(sample_data, 'explanation'):
            for explanation in sample_data.explanation:
                explanation_dict = self._explanation_to_dict(
                    explanation, sample_id)
                inference_info[explanation.label]['saliency_maps'].append(explanation_dict)

        sample_info['inferences'] = list(inference_info.values())
        return sample_info

    def _import_sample(self, sample):
        """Add sample object of given sample id."""
        for label_id in sample.ground_truth_label:
            self._labels_info[label_id]['sample_ids'].add(sample.image_id)

        sample_info = self._image_container_to_dict(sample)
        self._samples_info.update({sample_info['id']: sample_info})

    def retrieve_image(self, image_id: str):
        """
        Retrieve image data from the job given image_id.

        Return:
            string, image data in base64 byte

        """
        return self._image_dict.get(image_id, None)

    def retrieve_overlay(self, overlay_id: str):
        """
        Retrieve sample map from the job given overlay_id.

        Return:
            string, saliency_map data in base64 byte
        """
        return self._overlay_dict.get(overlay_id, None)

    def get_all_samples(self):
        """
        Return a list of sample information cachced in the explain job

        Returns:
            sample_list (List[SampleObj]): a list of sample objects, each object
                consists of:

                - id (int): sample id
                - name (str): basename of image
                - labels (list[str]): list of labels
                - inferences list[dict])
        """
        samples_in_list = list(self._samples_info.values())
        return samples_in_list

    def _is_metadata_empty(self):
        """Check whether metadata is loaded first."""
        if not self._explainers or not self._metrics or not self._labels:
            return True
        return False

    def _import_data_from_event(self, event):
        """Parse and import data from the event data."""
        tags = {
            'image_id': PluginNameEnum.IMAGE_ID,
            'benchmark': PluginNameEnum.BENCHMARK,
            'metadata': PluginNameEnum.METADATA
        }

        if 'metadata' not in event and self._is_metadata_empty():
            raise ValueError('metadata is empty, should write metadata first'
                             'in the summary.')
        for tag in tags:
            if tag not in event:
                continue

            if tag == PluginNameEnum.IMAGE_ID.value:
                sample_event = event[tag]
                sample_data = self._event_parser.parse_sample(sample_event)
                if sample_data is not None:
                    self._import_sample(sample_data)
                continue

            if tag == PluginNameEnum.BENCHMARK.value:
                benchmark_event = event[tag].benchmark
                benchmark = self._event_parser.parse_benchmark(benchmark_event)
                self._benchmark = benchmark

            elif tag == PluginNameEnum.METADATA.value:
                metadata_event = event[tag].metadata
                metadata = self._event_parser.parse_metadata(metadata_event)
                self._explainers, self._metrics, self._labels = metadata
                self._initialize_labels_info()

    def load(self):
        """
        Start loading data from parser.
        """
        valid_file_names = []
        for filename in FileHandler.list_dir(self._summary_dir):
            if FileHandler.is_file(
                    FileHandler.join(self._summary_dir, filename)):
                valid_file_names.append(filename)

        if not valid_file_names:
            raise TrainJobNotExistError('No summary file found in %s, explain job will be delete.' % self._summary_dir)

        is_end = False
        while not is_end:
            is_clean, is_end, event = self._parser.parse_explain(valid_file_names)

            if is_clean:
                logger.info('Summary file in %s update, reload the clean the loaded data.', self._summary_dir)
                self._clean_job()

            if event:
                self._import_data_from_event(event)

    def _clean_job(self):
        """Clean the cached data in job."""
        self._latest_update_time = ExplainJob.get_update_time(self._summary_dir)
        self._create_time = ExplainJob.get_update_time(self._summary_dir)
        self._labels.clear()
        self._metrics.clear()
        self._explainers.clear()
        self._samples_info.clear()
        self._labels_info.clear()
        self._benchmark.clear()
        self._overlay_dict.clear()
        self._image_dict.clear()
        self._event_parser.clear()

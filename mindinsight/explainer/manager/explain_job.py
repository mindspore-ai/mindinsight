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
from collections import defaultdict
from datetime import datetime
from typing import Union

from mindinsight.explainer.common.enums import PluginNameEnum
from mindinsight.explainer.common.log import logger
from mindinsight.explainer.manager.explain_parser import _ExplainParser
from mindinsight.explainer.manager.event_parse import EventParser
from mindinsight.datavisual.data_access.file_handler import FileHandler
from mindinsight.datavisual.common.exceptions import TrainJobNotExistError

_NUM_DIGIT = 7


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
        self._uncertainty_enabled = False
        self._labels = []
        self._metrics = []
        self._explainers = []
        self._samples_info = {}
        self._labels_info = {}
        self._explainer_score_dict = defaultdict(list)
        self._label_score_dict = defaultdict(dict)

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
            single_info = {
                'id': label_id,
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
        merged_scores = []
        for explainer, explainer_score_on_metric in self._explainer_score_dict.items():
            label_scores = []
            for label, label_score_on_metric in self._label_score_dict[explainer].items():
                score_single_label = {
                    'label': self._labels[label],
                    'evaluations': label_score_on_metric,
                }
                label_scores.append(score_single_label)
            merged_scores.append({
                'explainer': explainer,
                'evaluations': explainer_score_on_metric,
                'class_scores': label_scores,
            })
        return merged_scores

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
    def uncertainty_enabled(self):
        return self._uncertainty_enabled

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
        elif isinstance(new_time, float):
            self._latest_update_time = new_time
        else:
            raise TypeError('new_time should have type of float or datetime')

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

    def _initialize_labels_info(self):
        """Initialize a dict for labels in the job."""
        if self._labels is None:
            logger.warning('No labels is provided in job %s', self._job_id)
            return

        for label_id, label in enumerate(self._labels):
            self._labels_info[label_id] = {'label': label,
                                           'sample_ids': set()}

    def _explanation_to_dict(self, explanation):
        """Transfer the explanation from event to dict storage."""
        explain_info = {
            'explainer': explanation.explain_method,
            'overlay': explanation.heatmap_path,
        }
        return explain_info

    def _image_container_to_dict(self, sample_data):
        """Transfer the image container to dict storage."""
        has_uncertainty = False
        sample_id = sample_data.sample_id

        sample_info = {
            'id': sample_id,
            'image': sample_data.image_path,
            'name': str(sample_id),
            'labels': [self._labels_info[x]['label']
                       for x in sample_data.ground_truth_label],
            'inferences': []}

        ground_truth_labels = list(sample_data.ground_truth_label)
        ground_truth_probs = list(sample_data.inference.ground_truth_prob)
        predicted_labels = list(sample_data.inference.predicted_label)
        predicted_probs = list(sample_data.inference.predicted_prob)

        if sample_data.inference.predicted_prob_sd or sample_data.inference.ground_truth_prob_sd:
            ground_truth_prob_sds = list(sample_data.inference.ground_truth_prob_sd)
            ground_truth_prob_lows = list(sample_data.inference.ground_truth_prob_itl95_low)
            ground_truth_prob_his = list(sample_data.inference.ground_truth_prob_itl95_hi)
            predicted_prob_sds = list(sample_data.inference.predicted_prob_sd)
            predicted_prob_lows = list(sample_data.inference.predicted_prob_itl95_low)
            predicted_prob_his = list(sample_data.inference.predicted_prob_itl95_hi)
            has_uncertainty = True
        else:
            ground_truth_prob_sds = ground_truth_prob_lows = ground_truth_prob_his = None
            predicted_prob_sds = predicted_prob_lows = predicted_prob_his = None

        inference_info = {}
        for label, prob in zip(
                ground_truth_labels + predicted_labels,
                ground_truth_probs + predicted_probs):
            inference_info[label] = {
                'label': self._labels_info[label]['label'],
                'confidence': round(prob, _NUM_DIGIT),
                'saliency_maps': []}

        if ground_truth_prob_sds or predicted_prob_sds:
            for label, sd, low, hi in zip(
                    ground_truth_labels + predicted_labels,
                    ground_truth_prob_sds + predicted_prob_sds,
                    ground_truth_prob_lows + predicted_prob_lows,
                    ground_truth_prob_his + predicted_prob_his):
                inference_info[label]['confidence_sd'] = sd
                inference_info[label]['confidence_itl95'] = [low, hi]

        if EventParser.is_attr_ready(sample_data, 'explanation'):
            for explanation in sample_data.explanation:
                explanation_dict = self._explanation_to_dict(explanation)
                inference_info[explanation.label]['saliency_maps'].append(explanation_dict)

        sample_info['inferences'] = list(inference_info.values())
        return sample_info, has_uncertainty

    def _import_sample(self, sample):
        """Add sample object of given sample id."""
        for label_id in sample.ground_truth_label:
            self._labels_info[label_id]['sample_ids'].add(sample.sample_id)

        sample_info, has_uncertainty = self._image_container_to_dict(sample)
        self._samples_info.update({sample_info['id']: sample_info})
        self._uncertainty_enabled |= has_uncertainty

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
            'sample_id': PluginNameEnum.SAMPLE_ID,
            'benchmark': PluginNameEnum.BENCHMARK,
            'metadata': PluginNameEnum.METADATA
        }

        if 'metadata' not in event and self._is_metadata_empty():
            raise ValueError('metadata is empty, should write metadata first in the summary.')
        for tag in tags:
            if tag not in event:
                continue

            if tag == PluginNameEnum.SAMPLE_ID.value:
                sample_event = event[tag]
                sample_data = self._event_parser.parse_sample(sample_event)
                if sample_data is not None:
                    self._import_sample(sample_data)
                continue

            if tag == PluginNameEnum.BENCHMARK.value:
                benchmark_event = event[tag].benchmark
                explain_score_dict, label_score_dict = EventParser.parse_benchmark(benchmark_event)
                self._update_benchmark(explain_score_dict, label_score_dict)

            elif tag == PluginNameEnum.METADATA.value:
                metadata_event = event[tag].metadata
                metadata = EventParser.parse_metadata(metadata_event)
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
        self._explainer_score_dict.clear()
        self._label_score_dict.clear()
        self._event_parser.clear()

    def _update_benchmark(self, explainer_score_dict, labels_score_dict):
        """Update the benchmark info."""
        for explainer, score in explainer_score_dict.items():
            self._explainer_score_dict[explainer].extend(score)

        for explainer, score in labels_score_dict.items():
            for label, score_of_label in score.items():
                self._label_score_dict[explainer][label] = (self._label_score_dict[explainer].get(label, [])
                                                            + score_of_label)

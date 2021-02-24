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
"""ExplainLoader."""

import math
import os
import re
import threading
from collections import defaultdict
from datetime import datetime
from enum import Enum
from typing import Dict, Iterable, List, Optional, Union

from mindinsight.datavisual.common.exceptions import TrainJobNotExistError
from mindinsight.datavisual.data_access.file_handler import FileHandler
from mindinsight.explainer.common.enums import ExplainFieldsEnum
from mindinsight.explainer.common.log import logger
from mindinsight.explainer.manager.explain_parser import ExplainParser
from mindinsight.utils.exceptions import ParamValueError, UnknownError

_NAN_CONSTANT = 'NaN'
_NUM_DIGITS = 6

_EXPLAIN_FIELD_NAMES = [
    ExplainFieldsEnum.SAMPLE_ID,
    ExplainFieldsEnum.BENCHMARK,
    ExplainFieldsEnum.METADATA,
]

_SAMPLE_FIELD_NAMES = [
    ExplainFieldsEnum.GROUND_TRUTH_LABEL,
    ExplainFieldsEnum.INFERENCE,
    ExplainFieldsEnum.EXPLANATION,
    ExplainFieldsEnum.HIERARCHICAL_OCCLUSION
]


class _LoaderStatus(Enum):
    STOP = 'STOP'
    LOADING = 'LOADING'
    PENDING = 'PENDING'
    LOADED = 'LOADED'


def _round(score):
    """Take round of a number to given precision."""
    try:
        return round(score, _NUM_DIGITS)
    except TypeError:
        return score


class ExplainLoader:
    """ExplainLoader which manage the record in the summary file."""

    def __init__(self,
                 loader_id: str,
                 summary_dir: str):

        self._parser = ExplainParser(summary_dir)

        self._loader_info = {
            'loader_id': loader_id,
            'summary_dir': summary_dir,
            'create_time': os.stat(summary_dir).st_ctime,
            'update_time': os.stat(summary_dir).st_mtime,
            'query_time': os.stat(summary_dir).st_ctime,
            'uncertainty_enabled': False,
        }
        self._samples = defaultdict(dict)
        self._metadata = {'explainers': [], 'metrics': [], 'labels': [], 'min_confidence': 0.5}
        self._benchmark = {'explainer_score': defaultdict(dict), 'label_score': defaultdict(dict)}

        self._status = _LoaderStatus.PENDING.value
        self._status_mutex = threading.Lock()

    @property
    def all_classes(self) -> List[Dict]:
        """
        Return a list of detailed label information, including label id, label name and sample count of each label.

        Returns:
            list[dict], a list of dict, each dict contains:

                - id (int): Label id.
                - label (str): Label name.
                - sample_count (int): Number of samples for each label.
        """
        sample_count_per_label = defaultdict(int)
        saliency_count_per_label = defaultdict(int)
        hoc_count_per_label = defaultdict(int)
        for sample in self._samples.values():
            if sample.get('image') and (sample.get('ground_truth_label') or sample.get('predicted_label')):
                for label in set(sample['ground_truth_label'] + sample['predicted_label']):
                    sample_count_per_label[label] += 1
                    if sample['inferences'][label]['saliency_maps']:
                        saliency_count_per_label[label] += 1
                    if sample['inferences'][label]['hoc_layers']:
                        hoc_count_per_label[label] += 1

        all_classes_return = [{'id': label_id,
                               'label': label_name,
                               'sample_count': sample_count_per_label[label_id],
                               'saliency_sample_count': saliency_count_per_label[label_id],
                               'hoc_sample_count': hoc_count_per_label[label_id]}
                              for label_id, label_name in enumerate(self._metadata['labels'])]
        return all_classes_return

    @property
    def query_time(self) -> float:
        """Return query timestamp of explain loader."""
        return self._loader_info['query_time']

    @query_time.setter
    def query_time(self, new_time: Union[datetime, float]):
        """
        Update the query_time timestamp manually.

        Args:
            new_time (datetime.datetime or float): Updated query_time for the explain loader.
        """
        if isinstance(new_time, datetime):
            self._loader_info['query_time'] = new_time.timestamp()
        elif isinstance(new_time, float):
            self._loader_info['query_time'] = new_time
        else:
            raise TypeError('new_time should have type of datetime.datetime or float, but receive {}'
                            .format(type(new_time)))

    @property
    def create_time(self) -> float:
        """Return the create timestamp of summary file."""
        return self._loader_info['create_time']

    @create_time.setter
    def create_time(self, new_time: Union[datetime, float]):
        """
        Update the create_time manually

        Args:
            new_time (datetime.datetime or float): Updated create_time of summary_file.
        """
        if isinstance(new_time, datetime):
            self._loader_info['create_time'] = new_time.timestamp()
        elif isinstance(new_time, float):
            self._loader_info['create_time'] = new_time
        else:
            raise TypeError('new_time should have type of datetime.datetime or float, but receive {}'
                            .format(type(new_time)))

    @property
    def explainers(self) -> List[str]:
        """Return a list of explainer names recorded in the summary file."""
        return self._metadata['explainers']

    @property
    def explainer_scores(self) -> List[Dict]:
        """
        Return evaluation results for every explainer.

        Returns:
            list[dict], A list of evaluation results of each explainer. Each item contains:

                - explainer (str): Name of evaluated explainer.
                - evaluations (list[dict]): A list of evaluation results by different metrics.
                - class_scores (list[dict]): A list of evaluation results on different labels.

                Each item in the evaluations contains:

                    - metric (str): name of metric method
                    - score (float): evaluation result

                Each item in the class_scores contains:

                    - label (str): Name of label
                    - evaluations (list[dict]): A list of evaluation results on different labels by different metrics.

                    Each item in evaluations contains:

                        - metric (str): Name of metric method
                        - score (float): Evaluation scores of explainer on specific label by the metric.
        """
        explainer_scores = []
        for explainer, explainer_score_on_metric in self._benchmark['explainer_score'].copy().items():
            metric_scores = [{'metric': metric, 'score': _round(score)}
                             for metric, score in explainer_score_on_metric.items()]
            label_scores = []
            for label, label_score_on_metric in self._benchmark['label_score'][explainer].copy().items():
                score_of_single_label = {
                    'label': self._metadata['labels'][label],
                    'evaluations': [
                        {'metric': metric, 'score': _round(score)} for metric, score in label_score_on_metric.items()
                    ],
                }
                label_scores.append(score_of_single_label)
            explainer_scores.append({
                'explainer': explainer,
                'evaluations': metric_scores,
                'class_scores': label_scores,
            })
        return explainer_scores

    @property
    def labels(self) -> List[str]:
        """Return the label recorded in the summary."""
        return self._metadata['labels']

    @property
    def metrics(self) -> List[str]:
        """Return a list of metric names recorded in the summary file."""
        return self._metadata['metrics']

    @property
    def min_confidence(self) -> Optional[float]:
        """Return minimum confidence used to filter the predicted labels."""
        return self._metadata['min_confidence']

    @property
    def sample_count(self) -> int:
        """
        Return total number of samples in the loader.

        Since the loader only return available samples (i.e. with original image data and ground_truth_label loaded in
        cache), the returned count only takes the available samples into account.

        Return:
            int, total number of available samples in the loading job.
        """
        sample_count = 0
        for sample in self._samples.values():
            if sample.get('image', False):
                sample_count += 1
        return sample_count

    @property
    def samples(self) -> List[Dict]:
        """Return the information of all samples in the job."""
        return self._samples

    @property
    def train_id(self) -> str:
        """Return ID of explain loader."""
        return self._loader_info['loader_id']

    @property
    def uncertainty_enabled(self):
        """Whether uncertainty is enabled."""
        return self._loader_info['uncertainty_enabled']

    @property
    def update_time(self) -> float:
        """Return latest modification timestamp of summary file."""
        return self._loader_info['update_time']

    @update_time.setter
    def update_time(self, new_time: Union[datetime, float]):
        """
        Update the update_time manually.

        Args:
            new_time (datetime.datetime or float): Updated time for the summary file.
        """
        if isinstance(new_time, datetime):
            self._loader_info['update_time'] = new_time.timestamp()
        elif isinstance(new_time, float):
            self._loader_info['update_time'] = new_time
        else:
            raise TypeError('new_time should have type of datetime.datetime or float, but receive {}'
                            .format(type(new_time)))

    def load(self):
        """Start loading data from the latest summary file to the loader."""
        if self.status != _LoaderStatus.LOADED.value:
            self.status = _LoaderStatus.LOADING.value

        filenames = []
        for filename in FileHandler.list_dir(self._loader_info['summary_dir']):
            if FileHandler.is_file(FileHandler.join(self._loader_info['summary_dir'], filename)):
                filenames.append(filename)
        filenames = ExplainLoader._filter_files(filenames)

        if not filenames:
            raise TrainJobNotExistError('No summary file found in %s, explain job will be delete.'
                                        % self._loader_info['summary_dir'])

        is_end = False
        while not is_end and self.status != _LoaderStatus.STOP.value:
            try:
                file_changed, is_end, event_dict = self._parser.list_events(filenames)
            except UnknownError:
                is_end = True
                break

            if file_changed:
                logger.info('Summary file in %s update, reload the data in the summary.',
                            self._loader_info['summary_dir'])
                self._clear_job()
                if self.status != _LoaderStatus.STOP.value:
                    self.status = _LoaderStatus.LOADING.value
            if event_dict:
                self._import_data_from_event(event_dict)
        self._reform_sample_info()
        if is_end:
            self.status = _LoaderStatus.LOADED.value

    @property
    def status(self):
        """Get the status of this class with lock."""
        with self._status_mutex:
            return self._status

    @status.setter
    def status(self, status):
        """Set the status of this class with lock."""
        with self._status_mutex:
            self._status = status

    def stop(self):
        """Stop load data."""
        self.status = _LoaderStatus.STOP.value

    def get_all_samples(self) -> List[Dict]:
        """
        Return a list of sample information cached in the explain job.

        Returns:
            sample_list (list[SampleObj]): a list of sample objects, each object consists of:

                - id (int): Sample id.
                - name (str): Basename of image.
                - inferences (list[dict]): List of inferences for all labels.
        """
        returned_samples = [{'id': sample_id, 'name': info['name'], 'image': info['image'],
                             'inferences': list(info['inferences'].values())} for sample_id, info in
                            self._samples.items() if info.get('image', False)]
        return returned_samples

    def _import_data_from_event(self, event_dict: Dict):
        """Parse and import data from the event data."""
        if 'metadata' not in event_dict and self._is_metadata_empty():
            raise ParamValueError('metadata is incomplete, should write metadata first in the summary.')

        for tag, event in event_dict.items():
            if tag == ExplainFieldsEnum.METADATA.value:
                self._import_metadata_from_event(event.metadata)
            elif tag == ExplainFieldsEnum.BENCHMARK.value:
                self._import_benchmark_from_event(event.benchmark)
            elif tag == ExplainFieldsEnum.SAMPLE_ID.value:
                self._import_sample_from_event(event)
            else:
                logger.info('Unknown ExplainField: %s.', tag)

    def _is_metadata_empty(self):
        """Check whether metadata is completely loaded first."""
        if not self._metadata['labels']:
            return True
        return False

    def _import_metadata_from_event(self, metadata_event):
        """Import the metadata from event into loader."""

        def take_union(existed_list, imported_data):
            """Take union of existed_list and imported_data."""
            if isinstance(imported_data, Iterable):
                for sample in imported_data:
                    if sample not in existed_list:
                        existed_list.append(sample)

        take_union(self._metadata['explainers'], metadata_event.explain_method)
        take_union(self._metadata['metrics'], metadata_event.benchmark_method)
        take_union(self._metadata['labels'], metadata_event.label)

    def _import_benchmark_from_event(self, benchmarks):
        """
        Parse the benchmark event.

        Benchmark data are separated into 'explainer_score' and 'label_score'. 'explainer_score' contains overall
        evaluation results of each explainer by different metrics, while 'label_score' additionally divides the results
        w.r.t different labels.

            The structure of self._benchmark['explainer_score'] demonstrates below:
                 {
                    explainer_1: {metric_name_1: score_1, ...},
                    explainer_2: {metric_name_1: score_1, ...},
                    ...
                 }

            The structure of self._benchmark['label_score'] is:
                {
                    explainer_1: {label_id: {metric_1: score_1, metric_2: score_2, ...}, ...},
                    explainer_2: {label_id: {metric_1: score_1, metric_2: score_2, ...}, ...},
                    ...
                }

        Args:
            benchmarks (BenchmarkContainer): Parsed benchmarks data from summary file.
        """
        explainer_score = self._benchmark['explainer_score']
        label_score = self._benchmark['label_score']

        for benchmark in benchmarks:
            explainer = benchmark.explain_method
            metric = benchmark.benchmark_method
            metric_score = benchmark.total_score
            label_score_event = benchmark.label_score

            explainer_score[explainer][metric] = _NAN_CONSTANT if math.isnan(metric_score) else metric_score
            new_label_score_dict = ExplainLoader._score_event_to_dict(label_score_event, metric)
            for label, scores_of_metric in new_label_score_dict.items():
                if label not in label_score[explainer]:
                    label_score[explainer][label] = {}
                label_score[explainer][label].update(scores_of_metric)

    def _import_sample_from_event(self, sample):
        """
        Parse the sample event.

        Detailed data of each sample are store in self._samples, identified by sample_id. Each sample data are stored
        in the following structure:

            - ground_truth_labels (list[int]): A list of ground truth labels of the sample.
            - ground_truth_probs (list[float]): A list of confidences of ground-truth label from black-box model.
            - predicted_labels (list[int]): A list of predicted labels from the black-box model.
            - predicted_probs (list[int]): A list of confidences w.r.t the predicted labels.
            - explanations (dict): Explanations is a dictionary where the each explainer name mapping to a dictionary
                of saliency maps. The structure of explanations demonstrates below:
                {
                    explainer_name_1: {label_1: saliency_id_1, label_2: saliency_id_2, ...},
                    explainer_name_2: {label_1: saliency_id_1, label_2: saliency_id_2, ...},
                    ...
                }
            - hierarchical_occlusion (dict):  A dictionary where each label is matched to a dictionary:
                {label_1: [{prob: layer1_prob, bbox: []}, {prob: layer2_prob, bbox: []}],
                 label_2:
                }
        """
        if getattr(sample, 'sample_id', None) is None:
            raise ParamValueError('sample_event has no sample_id')
        sample_id = sample.sample_id
        if sample_id not in self._samples:
            self._samples[sample_id] = {
                'id': sample_id,
                'name': str(sample_id),
                'image': sample.image_path,
                'ground_truth_label': [],
                'predicted_label': [],
                'inferences': defaultdict(dict),
                'explanation': defaultdict(dict),
                'hierarchical_occlusion': defaultdict(dict)
            }

        if sample.image_path:
            self._samples[sample_id]['image'] = sample.image_path

        for tag in _SAMPLE_FIELD_NAMES:
            if tag == ExplainFieldsEnum.GROUND_TRUTH_LABEL:
                if not self._samples[sample_id]['ground_truth_label']:
                    self._samples[sample_id]['ground_truth_label'].extend(list(sample.ground_truth_label))
            elif tag == ExplainFieldsEnum.INFERENCE:
                self._import_inference_from_event(sample, sample_id)
            elif tag == ExplainFieldsEnum.EXPLANATION:
                self._import_explanation_from_event(sample, sample_id)
            elif tag == ExplainFieldsEnum.HIERARCHICAL_OCCLUSION:
                self._import_hoc_from_event(sample, sample_id)

    def _reform_sample_info(self):
        """Reform the sample info."""
        for _, sample_info in self._samples.items():
            inferences = sample_info['inferences']
            res_dict = defaultdict(list)
            for explainer, label_heatmap_path_dict in sample_info['explanation'].items():
                for label, heatmap_path in label_heatmap_path_dict.items():
                    res_dict[label].append({'explainer': explainer, 'overlay': heatmap_path})

            for label, item in inferences.items():
                item['saliency_maps'] = res_dict[label]

            for label, item in sample_info['hierarchical_occlusion'].items():
                inferences[label]['hoc_layers'] = item['hoc_layers']

    def _import_inference_from_event(self, event, sample_id):
        """Parse the inference event."""
        inference = event.inference
        if inference.ground_truth_prob_sd or inference.predicted_prob_sd:
            self._loader_info['uncertainty_enabled'] = True
        if not self._samples[sample_id]['predicted_label']:
            self._samples[sample_id]['predicted_label'].extend(list(inference.predicted_label))
        if not self._samples[sample_id]['inferences']:
            inferences = {}
            for label, prob in zip(list(event.ground_truth_label) + list(inference.predicted_label),
                                   list(inference.ground_truth_prob) + list(inference.predicted_prob)):
                inferences[label] = {
                    'label': self._metadata['labels'][label],
                    'confidence': _round(prob),
                    'saliency_maps': [],
                    'hoc_layers': {},
                }
                if not event.ground_truth_label:
                    inferences[label]['prediction_type'] = None
                else:
                    if prob < self.min_confidence:
                        inferences[label]['prediction_type'] = 'FN'
                    elif label in event.ground_truth_label:
                        inferences[label]['prediction_type'] = 'TP'
                    else:
                        inferences[label]['prediction_type'] = 'FP'
            if self._loader_info['uncertainty_enabled']:
                for label, std, low, high in zip(
                        list(event.ground_truth_label) + list(inference.predicted_label),
                        list(inference.ground_truth_prob_sd) + list(inference.predicted_prob_sd),
                        list(inference.ground_truth_prob_itl95_low) + list(inference.predicted_prob_itl95_low),
                        list(inference.ground_truth_prob_itl95_hi) + list(inference.predicted_prob_itl95_hi)):
                    inferences[label]['confidence_sd'] = _round(std)
                    inferences[label]['confidence_itl95'] = [_round(low), _round(high)]

            self._samples[sample_id]['inferences'] = inferences

    def _import_explanation_from_event(self, event, sample_id):
        """Parse the explanation event."""
        if self._samples[sample_id]['explanation'] is None:
            self._samples[sample_id]['explanation'] = defaultdict(dict)
        sample_explanation = self._samples[sample_id]['explanation']

        for explanation_item in event.explanation:
            explainer = explanation_item.explain_method
            label = explanation_item.label
            sample_explanation[explainer][label] = explanation_item.heatmap_path

    def _import_hoc_from_event(self, event, sample_id):
        """Parse the mango event."""
        sample_hoc = self._samples[sample_id]['hierarchical_occlusion']
        if event.hierarchical_occlusion:
            for hoc_item in event.hierarchical_occlusion:
                label = hoc_item.label
                sample_hoc[label] = {}
                sample_hoc[label]['label'] = label
                sample_hoc[label]['mask'] = hoc_item.mask
                sample_hoc[label]['confidence'] = self._samples[sample_id]['inferences'][label]['confidence']
                sample_hoc[label]['hoc_layers'] = []
                for hoc_layer in hoc_item.layer:
                    sample_hoc_dict = {'confidence': hoc_layer.prob}
                    box_lst = list(hoc_layer.box)
                    box = [box_lst[i: i + 4] for i in range(0, len(hoc_layer.box), 4)]
                    sample_hoc_dict['boxes'] = box
                    sample_hoc[label]['hoc_layers'].append(sample_hoc_dict)

    def _clear_job(self):
        """Clear the cached data and update the time info of the loader."""
        self._samples.clear()
        self._loader_info['create_time'] = os.stat(self._loader_info['summary_dir']).st_ctime
        self._loader_info['update_time'] = os.stat(self._loader_info['summary_dir']).st_mtime
        self._loader_info['query_time'] = max(self._loader_info['update_time'], self._loader_info['query_time'])

        def clear_inner_dict(outer_dict):
            """Clear the inner structured data of the given dict."""
            for item in outer_dict.values():
                item.clear()

        map(clear_inner_dict, [self._metadata, self._benchmark])

    @staticmethod
    def _filter_files(filenames):
        """
        Gets a list of summary files.

        Args:
            filenames (list[str]): File name list, like [filename1, filename2].

        Returns:
            list[str], filename list.
        """
        return list(filter(
            lambda filename: (re.search(r'summary\.\d+', filename) and filename.endswith("_explain")), filenames))

    @staticmethod
    def _is_inference_valid(sample):
        """
        Check whether the inference data is empty or have the same length.

        If probs have different length with the labels, it can be confusing when assigning each prob to label.
        '_is_inference_valid' returns True only when the data size of match to each other. Note that prob data could be
        empty, so empty prob will pass the check.
        """
        ground_truth_len = len(sample['ground_truth_label'])
        for name in ['ground_truth_prob', 'ground_truth_prob_sd',
                     'ground_truth_prob_itl95_low', 'ground_truth_prob_itl95_hi']:
            if sample[name] and len(sample[name]) != ground_truth_len:
                logger.info('Length of %s not match the ground_truth_label. Length of ground_truth_label: %d,'
                            'length of %s: %d', name, ground_truth_len, name, len(sample[name]))
                return False

        predicted_len = len(sample['predicted_label'])
        for name in ['predicted_prob', 'predicted_prob_sd',
                     'predicted_prob_itl95_low', 'predicted_prob_itl95_hi']:
            if sample[name] and len(sample[name]) != predicted_len:
                logger.info('Length of %s not match the predicted_labels. Length of predicted_label: %d,'
                            'length of %s: %d', name, predicted_len, name, len(sample[name]))
                return False
        return True

    @staticmethod
    def _score_event_to_dict(label_score_event, metric) -> Dict:
        """Transfer metric scores per label to pre-defined structure."""
        new_label_score_dict = defaultdict(dict)
        for label_id, label_score in enumerate(label_score_event):
            new_label_score_dict[label_id][metric] = _NAN_CONSTANT if math.isnan(label_score) else label_score
        return new_label_score_dict

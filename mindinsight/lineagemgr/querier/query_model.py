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
"""This file is used to define lineage info model."""
import json
from collections import namedtuple

from google.protobuf.json_format import MessageToDict

from mindinsight.lineagemgr.common.exceptions.exceptions import \
    LineageEventFieldNotExistException, LineageEventNotExistException
from mindinsight.lineagemgr.summary._summary_adapter import organize_graph

Field = namedtuple('Field', ['base_name', 'sub_name'])
FIELD_MAPPING = {
    "summary_dir": Field('summary_dir', None),
    "loss_function": Field("hyper_parameters", 'loss_function'),
    "train_dataset_path": Field('train_dataset', 'train_dataset_path'),
    "train_dataset_count": Field("train_dataset", 'train_dataset_size'),
    "test_dataset_path": Field('valid_dataset', 'valid_dataset_path'),
    "test_dataset_count": Field('valid_dataset', 'valid_dataset_size'),
    "network": Field('algorithm', 'network'),
    "optimizer": Field('hyper_parameters', 'optimizer'),
    "learning_rate": Field('hyper_parameters', 'learning_rate'),
    "epoch": Field('hyper_parameters', 'epoch'),
    "batch_size": Field('hyper_parameters', 'batch_size'),
    "device_num": Field('hyper_parameters', 'device_num'),
    "loss": Field('algorithm', 'loss'),
    "model_size": Field('model', 'size'),
    "dataset_mark": Field('dataset_mark', None)
}


class LineageObj:
    """
    Lineage information class.

    An instance of the class hold lineage information for a training session.

    Args:
        summary_dir (str): Summary log dir.
        kwargs (dict): Params to init the instance.

            - train_lineage (Event): Train lineage object.

            - evaluation_lineage (Event): Evaluation lineage object.

            - dataset_graph (Event): Dataset graph object.

            - user_defined_info (Event): User defined info object.

    Raises:
        LineageEventNotExistException: If train and evaluation event not exist.
        LineageEventFieldNotExistException: If the special event field not exist.
    """
    _name_train_lineage = 'train_lineage'
    _name_evaluation_lineage = 'evaluation_lineage'
    _name_summary_dir = 'summary_dir'
    _name_metric = 'metric'
    _name_hyper_parameters = 'hyper_parameters'
    _name_algorithm = 'algorithm'
    _name_train_dataset = 'train_dataset'
    _name_model = 'model'
    _name_valid_dataset = 'valid_dataset'
    _name_dataset_graph = 'dataset_graph'
    _name_dataset_mark = 'dataset_mark'
    _name_user_defined = 'user_defined'
    _name_model_lineage = 'model_lineage'

    def __init__(self, summary_dir, **kwargs):
        self._lineage_info = {
            self._name_summary_dir: summary_dir
        }
        self._init_lineage()
        self.parse_and_update_lineage(**kwargs)

    def _init_lineage(self):
        """Init lineage info."""
        # train
        self._lineage_info[self._name_model] = {}
        self._lineage_info[self._name_algorithm] = {}
        self._lineage_info[self._name_hyper_parameters] = {}
        self._lineage_info[self._name_train_dataset] = {}

        # eval
        self._lineage_info[self._name_metric] = {}
        self._lineage_info[self._name_valid_dataset] = {}

        # dataset graph
        self._lineage_info[self._name_dataset_graph] = {}

        # user defined
        self._lineage_info[self._name_user_defined] = {}

    def parse_and_update_lineage(self, **kwargs):
        """Parse and update lineage."""
        user_defined_info_list = kwargs.get('user_defined_info', [])
        train_lineage = kwargs.get('train_lineage')
        evaluation_lineage = kwargs.get('evaluation_lineage')
        dataset_graph = kwargs.get('dataset_graph')
        if not any([train_lineage, evaluation_lineage, dataset_graph]):
            raise LineageEventNotExistException()

        # If new train lineage, will clean the lineage saved before.
        if train_lineage is not None or dataset_graph is not None:
            self._init_lineage()

        self._parse_user_defined_info(user_defined_info_list)
        self._parse_train_lineage(train_lineage)
        self._parse_evaluation_lineage(evaluation_lineage)
        self._parse_dataset_graph(dataset_graph)

        self._filtration_result = self._organize_filtration_result()

    @property
    def summary_dir(self):
        """
        Get summary log dir.

        Returns:
            str, the summary log dir.
        """
        return self._lineage_info.get(self._name_summary_dir)

    @property
    def metric(self):
        """
        Get metric information.

        Returns:
            dict, the metric information.
        """
        return self._lineage_info.get(self._name_metric)

    @property
    def user_defined(self):
        """
        Get user defined information.

        Returns:
            dict, the user defined information.
        """
        return self._lineage_info.get(self._name_user_defined)

    @property
    def hyper_parameters(self):
        """
        Get hyperparameters.

        Returns:
            dict, the hyperparameters.
        """
        return self._lineage_info.get(self._name_hyper_parameters)

    @property
    def algorithm(self):
        """
        Get algorithm.

        Returns:
            dict, the algorithm.
        """
        return self._lineage_info.get(self._name_algorithm)

    @property
    def train_dataset(self):
        """
        Get train dataset information.

        Returns:
            dict, the train dataset information.
        """
        return self._lineage_info.get(self._name_train_dataset)

    @property
    def model(self):
        """
        Get model information.

        Returns:
            dict, the model information.
        """
        return self._lineage_info.get(self._name_model)

    @property
    def valid_dataset(self):
        """
        Get valid dataset information.

        Returns:
            dict, the valid dataset information.
        """
        return self._lineage_info.get(self._name_valid_dataset)

    @property
    def dataset_graph(self):
        """
        Get dataset_graph.

        Returns:
            dict, the dataset graph information.
        """
        return self._lineage_info.get(self._name_dataset_graph)

    @property
    def dataset_mark(self):
        """
        Get dataset_mark.

        Returns:
            dict, the dataset mark information.
        """
        return self._lineage_info.get(self._name_dataset_mark)

    @dataset_mark.setter
    def dataset_mark(self, dataset_mark):
        """
        Set dataset mark.

        Args:
            dataset_mark (int): Dataset mark.
        """
        self._lineage_info[self._name_dataset_mark] = dataset_mark
        # update dataset_mark into filtration result
        self._filtration_result[self._name_dataset_mark] = dataset_mark

    def get_summary_info(self, filter_keys: list):
        """
        Get the summary lineage information.

        Returns the content corresponding to the specified field in the filter
        key. The contents of the filter key include `metric`, `hyper_parameters`,
        `algorithm`, `train_dataset`, `valid_dataset` and `model`. You can
        specify multiple filter keys in the `filter_keys`

        Args:
            filter_keys (list): Filter keys.

        Returns:
            dict, the summary lineage information.
        """
        result = {
            self._name_summary_dir: self.summary_dir,
        }

        for key in filter_keys:
            result[key] = getattr(self, key)
        return result

    def to_dataset_lineage_dict(self):
        """
        Returns the dataset part lineage information.

        Returns:
            dict, the dataset lineage information.
        """
        dataset_lineage = {
            key: self._filtration_result.get(key)
            for key in [self._name_summary_dir, self._name_dataset_graph]
        }

        return dataset_lineage

    def to_model_lineage_dict(self):
        """
        Returns the model part lineage information.

        Returns:
            dict, the model lineage information.
        """
        filtration_result = dict(self._filtration_result)
        filtration_result.pop(self._name_dataset_graph)

        model_lineage = dict()
        model_lineage.update({self._name_summary_dir: filtration_result.pop(self._name_summary_dir)})
        model_lineage.update({self._name_model_lineage: filtration_result})

        return model_lineage

    def get_value_by_key(self, key):
        """
        Get the value based on the key in `FIELD_MAPPING` or
            the key prefixed with `metric/` or `user_defined/`.

        Args:
            key (str): The key in `FIELD_MAPPING`
                or prefixed with `metric/` or `user_defined/`.

        Returns:
            object, the value.
        """
        if key.startswith(('metric/', 'user_defined/')):
            key_name, sub_key = key.split('/', 1)
            sub_value_name = self._name_metric if key_name == 'metric' else self._name_user_defined
            sub_value = self._filtration_result.get(sub_value_name)
            if sub_value:
                return sub_value.get(sub_key)
        return self._filtration_result.get(key)

    def _organize_filtration_result(self):
        """
        Organize filtration result.

        Returns:
            dict, the filtration result.
        """
        result = {}
        for key, field in FIELD_MAPPING.items():
            if field.base_name is not None:
                base_attr = getattr(self, field.base_name)
                result[key] = base_attr.get(field.sub_name) \
                    if field.sub_name else base_attr
        # add metric into filtration result
        result[self._name_metric] = self.metric

        result[self._name_user_defined] = self.user_defined
        # add dataset_graph into filtration result
        result[self._name_dataset_graph] = getattr(self, self._name_dataset_graph)

        return result

    def _parse_train_lineage(self, train_lineage):
        """
        Parse train lineage.

        Args:
            train_lineage (Event): Train lineage.
        """
        if train_lineage is None:
            return

        event_dict = MessageToDict(
            train_lineage, preserving_proto_field_name=True
        )
        train_dict = event_dict.get(self._name_train_lineage)
        if train_dict is None:
            raise LineageEventFieldNotExistException(
                self._name_train_lineage
            )

        # when MessageToDict is converted to dict, int64 type is converted
        # to string, so we convert it to an int in python
        if train_dict.get(self._name_model):
            model_size = train_dict.get(self._name_model).get('size')
            if model_size:
                train_dict[self._name_model]['size'] = int(model_size)

        self._lineage_info.update(**train_dict)

    def _parse_evaluation_lineage(self, evaluation_lineage):
        """
        Parse evaluation lineage.

        Args:
            evaluation_lineage (Event): Evaluation lineage.
        """
        if evaluation_lineage is None:
            return

        event_dict = MessageToDict(
            evaluation_lineage, preserving_proto_field_name=True
        )
        evaluation_dict = event_dict.get(self._name_evaluation_lineage)
        if evaluation_dict is None:
            raise LineageEventFieldNotExistException(
                self._name_evaluation_lineage
            )
        self._lineage_info.update(**evaluation_dict)
        metric = self._lineage_info.get(self._name_metric)
        self._lineage_info[self._name_metric] = json.loads(metric) if metric else {}

    def _parse_dataset_graph(self, dataset_graph):
        """
        Parse dataset graph.

        Args:
            dataset_graph (Event): Dataset graph.
        """
        if dataset_graph is not None:
            # convert message to dict
            event_dict = organize_graph(dataset_graph.dataset_graph)
            if event_dict is None:
                raise LineageEventFieldNotExistException(self._name_evaluation_lineage)
            self._lineage_info[self._name_dataset_graph] = event_dict if event_dict else {}

    def _parse_user_defined_info(self, user_defined_info_list):
        """
        Parse user defined info.

        Args:
            user_defined_info_list (list): user defined info list.
        """
        if not user_defined_info_list:
            return
        for user_defined_info in user_defined_info_list:
            self._lineage_info[self._name_user_defined].update(user_defined_info)

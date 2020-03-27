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
"""Log generator for graph."""
import json
import os
import time

from google.protobuf import json_format

from tests.ut.datavisual.utils.log_generators.log_generator import LogGenerator

from mindinsight.datavisual.proto_files import mindinsight_summary_pb2 as summary_pb2


class GraphLogGenerator(LogGenerator):
    """
    Log generator for graph.

    This is a log generator writing graph. User can use it to generate fake
    summary logs about graph.
    """

    def generate_log(self, file_path, graph_dict):
        """
        Generate log for external calls.

        Args:
            file_path (str): Path to write logs.
            graph_dict (dict): A dict consists of graph node information.

        Returns:
            dict, generated scalar metadata.

        """

        graph_event = self.generate_event(dict(graph=graph_dict))

        self._write_log_from_event(file_path, graph_event)

        return graph_dict

    def generate_event(self, values):
        """
        Method for generating graph event.

        Args:
            values (dict): Graph values. e.g. {'graph': graph_dict}.

        Returns:
            summary_pb2.Event.

        """
        graph_json = {
            'wall_time': time.time(),
            'graph_def': values.get('graph'),
        }
        graph_event = json_format.Parse(json.dumps(graph_json), summary_pb2.Event())

        return graph_event


if __name__ == "__main__":
    graph_log_generator = GraphLogGenerator()
    test_file_name = '%s.%s.%s' % ('graph', 'summary', str(time.time()))
    graph_base_path = os.path.join(os.path.dirname(__file__), os.pardir, "log_generators", "graph_base.json")
    with open(graph_base_path, 'r') as load_f:
        graph = json.load(load_f)
    graph_log_generator.generate_log(test_file_name, graph)

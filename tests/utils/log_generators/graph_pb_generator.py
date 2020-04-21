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
"""Log generator for graph pb file."""
import os
import json

from google.protobuf import json_format

from mindinsight.datavisual.proto_files import mindinsight_anf_ir_pb2 as anf_ir_pb2


def create_graph_pb_file(output_dir='./', filename='ms_output.pb'):
    """Create graph pb file, and return file path."""
    graph_base = os.path.join(os.path.dirname(__file__), "graph_base.json")
    with open(graph_base, 'r') as fp:
        data = json.load(fp)
    model_def = dict(graph=data)
    model_proto = json_format.Parse(json.dumps(model_def), anf_ir_pb2.ModelProto())
    msg = model_proto.SerializeToString()
    output_path = os.path.realpath(os.path.join(output_dir, filename))
    with open(output_path, 'wb') as fp:
        fp.write(msg)

    return output_path


if __name__ == '__main__':
    create_graph_pb_file()

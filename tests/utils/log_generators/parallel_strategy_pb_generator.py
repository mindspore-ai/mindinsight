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
"""A class used to generate parallel strategy data."""
import os
import json

from google.protobuf import json_format

from mindinsight.datavisual.proto_files import mindinsight_profiling_parallel_pb2 as parallel_pb2


def create_parallel_strategy_pb_file(json_path, output_dir=None):
    """Create graph pb file, and return file path."""
    root, _ = os.path.splitext(os.path.realpath(json_path))
    with open(json_path, 'r') as fp:
        data = json.load(fp)
    model_proto = json_format.Parse(json.dumps(data), parallel_pb2.ProfilingParallel())
    msg = model_proto.SerializeToString()
    output_path = root + '.pb'
    if output_dir:
        output_path = os.path.join(output_dir, os.path.basename(output_path))
    with open(output_path, 'wb') as fp:
        fp.write(msg)

    return output_path


if __name__ == '__main__':
    create_parallel_strategy_pb_file('../resource/parallel_strategy/parallel_strategy_0.json')

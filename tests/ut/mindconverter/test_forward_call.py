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
"""Test forward_call module."""
import ast
import textwrap

from mindinsight.mindconverter.forward_call import ForwardCall


class TestForwardCall:
    """Test the class of ForwardCall."""
    source = textwrap.dedent("""\
        import a
        import a.nn as nn
        import a.nn.functional as F
        class TestNet:
            def __init__(self):
                self.conv1 = nn.Conv2d(3, 6, 5)
                self.conv2 = nn.Conv2d(6, 16, 5)
                self.fc1 = nn.Linear(16 * 5 * 5, 120)
                self.fc2 = nn.Linear(120, 84)
                self.fc3 = nn.Linear(84, 10)

            def forward(self, x):
                out = self.forward1(x)
                return out

            def forward1(self, x):
                out = F.relu(self.conv1(x))
                out = F.max_pool2d(out, 2)
                out = F.relu(self.conv2(out))
                out = F.max_pool2d(out, 2)
                out = out.view(out.size(0), -1)
                out = F.relu(self.fc1(out))
                out = F.relu(self.fc2(out))
                out = self.fc3(out)
                return out
    """)

    def test_process(self):
        """Test the function of visit ast tree to find out forward functions."""
        ast_tree = ast.parse(self.source)
        forward_call = ForwardCall(ast_tree)

        expect_calls = ['TestNet.forward',
                        'TestNet.forward1',
                        'F.relu',
                        'TestNet.conv1',
                        'F.max_pool2d',
                        'TestNet.conv2',
                        'out.view',
                        'out.size',
                        'TestNet.fc1',
                        'TestNet.fc2',
                        'TestNet.fc3',
                        ]
        expect_calls.sort()
        real_calls = list(forward_call.calls.keys())
        real_calls.sort()
        assert real_calls == expect_calls

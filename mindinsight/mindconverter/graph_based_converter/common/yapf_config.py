# Copyright 2021 Huawei Technologies Co., Ltd.All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Define code format configuration."""
from yapf.yapflib.style import CreatePEP8Style


def mindspore_yapf_config():
    """Create the PEP8 formatting style."""
    style = CreatePEP8Style()
    style['ALLOW_SPLIT_BEFORE_DEFAULT_OR_NAMED_ASSIGNS'] = False
    style['ALLOW_MULTILINE_LAMBDAS'] = True
    style['ALLOW_SPLIT_BEFORE_DICT_VALUE'] = False
    style['COLUMN_LIMIT'] = 120
    style['COALESCE_BRACKETS'] = True
    style['FORCE_MULTILINE_DICT'] = True
    style['DISABLE_ENDING_COMMA_HEURISTIC'] = True
    style['INDENT_DICTIONARY_VALUE'] = True
    style['JOIN_MULTIPLE_LINES'] = False
    style['SPACES_BEFORE_COMMENT'] = 2
    style['SPLIT_PENALTY_AFTER_OPENING_BRACKET'] = 30
    style['SPLIT_PENALTY_BEFORE_IF_EXPR'] = 30
    style['SPLIT_PENALTY_FOR_ADDED_LINE_SPLIT'] = 30
    style['SPLIT_BEFORE_LOGICAL_OPERATOR'] = False
    style['SPLIT_BEFORE_BITWISE_OPERATOR'] = False
    return style

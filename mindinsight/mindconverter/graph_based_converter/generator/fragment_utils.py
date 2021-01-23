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
"""Miscellaneous Fragment related classes and functions. """

from mindinsight.mindconverter.graph_based_converter.common.code_fragment import NewFragment


class FragmentHandler:
    """
    Define a handler to process the information contained by Fragment.

    Args:
        fragment (NewFragment): The refactored fragment class.
    """
    def __init__(self, fragment: NewFragment):
        self._fragment = fragment
        # set the var in the fragment to be load and save.
        self._target_var = "var_0"

    @property
    def target_var(self):
        """Return the target var name the handler currently set to be read."""
        return self._target_var

    @target_var.setter
    def target_var(self, target):
        """Set the target var the handler will read."""
        if not target in self.exchange_msg.keys():
            raise ValueError(f"Unable to set target var {target} where fragment does not have it.")
        self._target_var = target

    @property
    def fragment(self):
        """Return the fragment instance the handler currently processed."""
        return self._fragment

    @property
    def converted(self):
        """Return the status of the op successfully converted."""
        return bool(self._fragment.exchange_msg)

    # The following section is intended for Fragment exchange message.
    @property
    def exchange_msg(self):
        """Return the exchange message dictionary the fragment contains."""
        return self._fragment.exchange_msg

    @property
    def var(self):
        """Return the var dictionary the handler currently set to be processed."""
        try:
            return self.exchange_msg.get(self.target_var)
        except AttributeError:
            return None

    @property
    def default_var(self):
        """Return the default var dictionary the handler processed."""
        try:
            return self.exchange_msg.get("var_0")
        except AttributeError:
            return None

    # For metadata
    @property
    def metadata(self):
        """Return the metadata of the onnx node info dictionary."""
        return self._fragment.exchange_msg.get("metadata")

    @property
    def input_shape(self):
        """Return the input shape of this node."""
        return self.metadata.get('inputs_shape')

    @property
    def output_shape(self):
        """Return the output shape of this node."""
        return self.metadata.get('outputs_shape')

    # For outputs
    @property
    def outputs_manager(self):
        """Return the outputs manager of this node."""
        return self._fragment.outputs_mapping

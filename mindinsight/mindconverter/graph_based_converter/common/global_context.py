# Copyright 2020-2021 Huawei Technologies Co., Ltd.All Rights Reserved.
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
"""Define GlobalContext class to save required resources during whole conversion procedure."""
from collections import OrderedDict
from mindinsight.mindconverter.graph_based_converter.common.outputs import OutputStorage


class Singleton(type):
    """Metaclass to make the globalcontext single instance."""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

    @classmethod
    def release(mcs):
        """Clear singleton object."""
        mcs._instances.clear()


class GlobalContext(metaclass=Singleton):
    """
    A universal global context library for easy data exchanging in MindConverter.

    Note:
        In order to avoid reference loops, it is unable to check functions
        arguments' type in GlobalContext. You MUST check all inputs
        have its correct type before calling functions.
    """

    def __init__(self):
        # Define data stored from onnx_utils
        # Key as Onnx Name
        self._onnx_nodes_collection = OrderedDict()
        # key is topo_idx, value is onnx_node_name
        self._onnx_nodes_topo_index = dict()
        self.onnx_node_name_to_topo_idx = dict()
        self.onnx_node_inputs = dict()
        self._onnx_tensors_collection = dict()
        self.onnx_graph_info = dict()

        # Define data stored from generator
        # Key as Node Identifier
        self.node_struct_collections = OrderedDict()
        self.node_struct_adder_counter = 0
        # Define onnx_utils <---> generator mapping
        self.node_struct_to_onnx_node_map = dict()
        self.onnx_node_name_to_node_struct_map = dict()

        # Define Module pattern to customize name mapping
        self.module_customized_name = dict()

        # Define Fragments
        self.node_fragments = OrderedDict()
        self.module_fragments = OrderedDict()

        # Define Known module mapping
        self.known_module_name = dict()
        # Define Structs
        # key is pattern_id, value is [ModuleStructs]
        self.module_structs = dict()
        self.code_structs = dict()

        # Define extra inputs
        # key is target node (which use this opt), value is opt_var_name
        self.extra_input_dict = dict()

        self.outputs_storage = OutputStorage()

        # Record weights name that used many times.
        self.repeated_weights = dict()
        self.repeated_weights_declaration = dict()
        # Define Module Struct Build Status
        self.build_struct_finished = False

    def get_onnx_node_from_identifier(self, identifier):
        """Return an OnnxUtils defined node by its identifier."""
        onnx_node_name = self.node_struct_to_onnx_node_map.get(identifier)
        return self.onnx_nodes_collection.get(onnx_node_name)

    def get_onnx_node_from_onnx_topo_idx(self, idx):
        """Return an OnnxUtils defined node name by its topological index."""
        return self._onnx_nodes_topo_index.get(idx)

    def get_onnx_tensor(self, tensor_name):
        """Return an OnnxUtils defined tensor."""
        return self.onnx_tensors_collection.get(tensor_name)

    def get_identifier_from_onnx_node_name(self, node_name):
        """Return the node identifier by Onnx Node name."""
        identifier = self.onnx_node_name_to_node_struct_map.get(node_name)
        return identifier

    @property
    def onnx_nodes_collection(self) -> OrderedDict:
        """
        Return the onnx nodes collections.

        Returns:
            dict, dictionary contains all OnnxUtils defined onnx nodes.
        """
        return self._onnx_nodes_collection

    @onnx_nodes_collection.setter
    def onnx_nodes_collection(self, arg):
        """Set the onnx nodes collection."""
        if isinstance(arg, OrderedDict):
            self._onnx_nodes_collection = arg  # arg must be nodes_dict in OnnxDataLoader
        else:
            raise TypeError("GlobalContext received an unsupported variable to assign to onnx_nodes_collection.")

    @property
    def onnx_nodes_topo_index(self) -> dict:
        """Return the onnx nodes and topological index."""
        return self._onnx_nodes_topo_index

    @onnx_nodes_topo_index.setter
    def onnx_nodes_topo_index(self, index_list):
        """
        Set the onnx nodes and topological index.

        Args:
            index_list (list[tuple[int, str]]): a list of tuple contains the topological index and onnx node name.

        """
        if not isinstance(index_list, list):
            raise TypeError("The argument index_list must be a list of tuple (index, onnx_node_name).")
        if not isinstance(index_list[0], tuple):
            raise TypeError("The item in index_list must by a tuple of (index, onnx_node_name)")
        for (topo_idx, onnx_node_name) in index_list:
            self._onnx_nodes_topo_index[topo_idx] = onnx_node_name

    @property
    def onnx_tensors_collection(self):
        """Return the onnx tensors collection."""
        return self._onnx_tensors_collection

    @onnx_tensors_collection.setter
    def onnx_tensors_collection(self, arg):
        """
        Set the onnx tensors collection by OnnxDataLoader.

        Args:
            arg (dict): The OnnxDataLoader generated tensors_dict.
        """
        if isinstance(arg, dict):
            self._onnx_tensors_collection = arg  # arg must be tensors_dict in OnnxDataLoader
        else:
            raise TypeError("GlobalContext received an unsupported variable to assign to onnx_tensors_collection.")

    @property
    def latest_node_struct_count(self):
        """
        Return the latest node struct count.

        Note:
            The counter will increase by 1 to tracking the number of nodes added.
        """
        ret = self.node_struct_adder_counter
        self.node_struct_adder_counter += 1
        return ret

    def get_extra_input(self, topo_idx) -> list:
        """
        Get the extra input of the node topological index provided.

        Args:
            topo_idx (int): The topological index of the node required extra input.
        """
        return self.extra_input_dict.get(topo_idx)

    def add_extra_input(self, target_topo_idx, opt_var_name):
        """
        Add the extra input(s) required for the target node.

        Args:
            target_topo_idx (int): The index of node which requires the input.
            opt_var_name (Union[str, list]): The output(s) name the target node will use.
        """
        if isinstance(opt_var_name, str):
            opt_var_name = [opt_var_name]
        if isinstance(opt_var_name, list):
            self.extra_input_dict[target_topo_idx] = opt_var_name
        else:
            raise TypeError("Global Context does not support the type {} of opt_var_name.".format(type(opt_var_name)))

    def get_module_customized_name(self, pattern_id) -> str:
        """
        Get the customized name of the module with pattern id provied.

        Args:
            pattern_id (int): The pattern the module belongs to.

        Returns,
            str, the customized name of the module.
        """
        return self.module_customized_name.get(pattern_id)

    def set_module_customized_name(self, pattern_id, customized_name):
        """
        Set the customized name of the module with pattern id provided.

        Args:
            pattern_id (int): The pattern id the module has.
            customized_name (str): The customized name of the module.
        """
        self.module_customized_name[pattern_id] = customized_name

    def get_node_fragment(self, identifier):
        """Return the node fragment by identifier."""
        return self.node_fragments.get(identifier)

    def add_code_fragment(self, identifier, frag):
        """Add the node fragment by identifier."""
        self.node_fragments[identifier] = frag

    def get_module_fragment(self, identifier):
        """Return the module fragment by identifier."""
        return self.module_fragments.get(identifier)

    def add_module_fragment(self, identifier, frag):
        """Add the module fragment by identifier."""
        self.module_fragments[identifier] = frag

    def add_module_struct(self, pattern_id, module_struct):
        """
        Add module struct by its pattern_id.

        Args:
            pattern_id (int): The pattern which represents the structure of the module.
            module_struct (ModuleStruct): The ModuleStruct instance.
        """
        if self.module_structs.get(pattern_id) is None:
            self.module_structs[pattern_id] = [module_struct]
        else:
            self.module_structs[pattern_id].append(module_struct)

    @classmethod
    def release(cls):
        """Clear singleton object."""
        Singleton.release()

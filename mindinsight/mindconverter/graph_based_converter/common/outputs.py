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
"""Define basic classes for generator use."""
import abc
import copy
from typing import Union, Iterable

from mindinsight.mindconverter.graph_based_converter.common.code_fragment import NewFragment


class BaseOutput:
    """
    Define the class of output providing a universal nodes' and modules' output data collection.

    Args:
        output_mapping (tuple[tuple]): The mapping of outputs from onnx to mindspore.
    """
    def __init__(self, output_mapping) -> None:
        super(BaseOutput).__init__()
        self.idx_in_ms_provider = output_mapping[0]
        self.idx_in_onnx_provider = output_mapping[1]

        # For multi users, key as user and value as index
        self.idx_in_ms_user = dict()
        self.idx_in_onnx_user = dict()

        # The following attributes to be set by who referenced this object.
        self.onnx_edge_name = None
        self.to_external = False
        self.opt_var_name = None
        # Only for module output edge and its name inside its module
        self.inner_ret_name = None

    @property
    def ms_user(self):
        """Return the output's user in the MindSpore."""
        return self.idx_in_ms_user.keys()

    @property
    def onnx_user(self):
        """Return the output's user in the ONNX."""
        return self.idx_in_onnx_user.keys()

    def deepcopy(self):
        """Return a deepcopy of self instance."""
        return copy.deepcopy(self)


class BaseOutputManager(abc.ABC):
    """
    Base Output Manager class.

    Args:
        output_mappings (list): A list of output mapping.
    """
    def __init__(self, identifier, output_mappings: Iterable):
        if isinstance(self, ModuleOutputManager):
            return
        self._base_output_dict = dict()
        self.identifier = identifier

        # init base output obj
        for (onnx_edge_name, mapping) in output_mappings:
            obj = BaseOutput(mapping)
            self._base_output_dict[onnx_edge_name] = obj
            obj.onnx_edge_name = onnx_edge_name

    @property
    def outputs(self):
        """Return the list of BaseOutput in this manager."""
        return self._base_output_dict.values()

    @property
    def outputs_edges(self):
        """Return the list of outputs edge names in this manager."""
        return self._base_output_dict.keys()

    @outputs.setter
    def outputs(self, val: list):
        """Set the list of BaseOutput in this manager."""
        tmp = dict()
        for v in val:
            if not isinstance(v, BaseOutput):
                raise TypeError(f"{self.__class__} does not accept the type {type(v)} in the list given.")
            tmp[v.onnx_edge_name] = v
        self._base_output_dict = tmp

    def get_base_out(self, onnx_edge_name: str) -> BaseOutput:
        """Return the BaseOut by key."""
        return self._base_output_dict.get(onnx_edge_name)

    @abc.abstractmethod
    def deepcopy(self):
        """Return the deepcopy of this instance."""
        cls = self.__class__
        result = cls.__new__(cls)
        result.outputs = list()
        for out in self._base_output_dict.values():
            result.outputs.append(out.deepcopy())
        return result


class NodeOutputManager(BaseOutputManager):
    """
    Node Output Manager class.

    Args:
        identifier (str): The identifier of the node.
        output_mappings (list): A list of the output mapping.
    """
    def __init__(self, identifier, output_mappings=None) -> None:
        super(NodeOutputManager, self).__init__(identifier, output_mappings)

    def deepcopy(self):
        """Self defined deepcopy method."""
        new_mgr = super().deepcopy()
        new_mgr.identifier = self.identifier
        return new_mgr

    def bind_opt_var_names(self, fragment: NewFragment):
        """Get the opt_var_name in return statement."""
        for base_out in self._base_output_dict.values():
            base_out.opt_var_name = fragment.get_outputs_by_idx(base_out.idx_in_ms_provider)


class ModuleOutputManager(BaseOutputManager):
    """
    Module Output Manager class.

    Args:
        identifier (str): The identifier of the module.
        output_mappings (list): a list of output mapping
    """
    def __init__(self, identifier, base_out: Union[BaseOutput, Iterable[BaseOutput]]) -> None:
        super(ModuleOutputManager, self).__init__(identifier, None)
        self._return_list_counter = 0
        self._base_output_dict = dict()
        if isinstance(base_out, BaseOutput):
            self.outputs = [base_out]
        else:
            self.outputs = base_out

    @property
    def return_num(self):
        """Return the number of outputs to be returned."""
        return self._return_list_counter

    @return_num.setter
    def return_num(self, num: int):
        """Set the number of outputs to be returned."""
        self._return_list_counter = num

    def assign_opt_var_name_to_each_output(self, opt_var_name_base: str):
        """Assign opt_var_name for each output."""
        for idx, base_out in enumerate(self._base_output_dict.values()):
            postfix = str(idx) if idx > 0 else ""
            base_out.opt_var_name = '_'.join([opt_var_name_base, postfix]) if idx > 0 else opt_var_name_base

    def deepcopy(self):
        """Return a deepcopy of current instance."""
        new_mgr = super().deepcopy()
        new_mgr.identifier = self.identifier
        new_mgr.return_num = self._return_list_counter
        return new_mgr

    def bind_module_outputs_internal_name(self, outputs_register: dict):
        """
        Get the opt_var_name in return list.

        Args:
            opt_var_name_list (list): List from module outputs register, registered by submodule and nodes.
        """
        for base_out in self._base_output_dict.values():
            # bind the edge name inside module
            base_out.inner_ret_name = outputs_register.get(base_out.onnx_edge_name)

    def bind_opt_var_name(self, opt_var_names: list):
        """
        Assign the opt_var_name for outputs of this module.

        Args:
            opt_var_names (list): A list of opt_var_name of this module, generated by module itself.
        """
        if len(opt_var_names) != len(self._base_output_dict.values()):
            raise ValueError(f"Unable to bind the opt_var_name of the Module {self.identifier}" \
                             f" has inconsistent outputs number.")
        for idx, base_out in enumerate(self._base_output_dict.values()):
            base_out.opt_var_name = opt_var_names[idx]


class OutputStorage:
    """A class saves all outputs."""
    def __init__(self):
        self._base_output_edge_to_instance = dict()
        self._base_output_edge_to_onnx_node_name = dict()
        self._base_output_edge_to_ms_identifier = dict()

    @property
    def outputs_collections(self) -> dict:
        """Return the dict of edge name to output instance."""
        return self._base_output_edge_to_instance

    def onnx_name(self, output_edge) -> str:
        """Return the dict of edge name to onnx node name."""
        return self._base_output_edge_to_onnx_node_name.get(output_edge)

    def node_identifier(self, output_edge):
        """Return the dict of edge name to node identifier."""
        return self._base_output_edge_to_ms_identifier.get(output_edge)

    def add_output(self, out: BaseOutput) -> str:
        """
        Add a BaseOutput instance to the storage.

        Args:
            out (BaseOutput): The BaseOutput instance.
        """
        if out.onnx_edge_name:
            self._base_output_edge_to_instance[out.onnx_edge_name] = out
        else:
            raise ValueError("Unable to add a BaseOutput instance with unknown ONNX edge.")

    def add_onnx_node_name(self, edge: str, onnx_node_name: str):
        """
        Add the onnx node name with the edge name.

        Args:
            edge (str): The edge name of this output.
            onnx_node_name (str): The onnx node which has the edge.
        """
        self._base_output_edge_to_onnx_node_name[edge] = onnx_node_name

    def add_ms_identifier(self, edge: str, ms_identifier: str):
        """
        Add the node identifier with the edge name.

        Args:
            edge (str): The edge name of this output.
            ms_identifier (str): The identifier of the node which has the edge.
        """
        self._base_output_edge_to_ms_identifier[edge] = ms_identifier

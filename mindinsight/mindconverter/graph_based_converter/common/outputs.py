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
    def __init__(self, output_mappings):
        if isinstance(self.__class__, ModuleOutputManager):
            return
        self._base_output_list = list()

        # init base output obj
        for mapping in output_mappings:
            obj = BaseOutput(mapping)
            self._base_output_list.append(obj)

    @property
    def outputs(self):
        """Return the list of BaseOutput in this manager."""
        return self._base_output_list

    @outputs.setter
    def outputs(self, val: list):
        """Set the list of BaseOutput in this manager."""
        for v in val:
            if not isinstance(v, BaseOutput):
                raise TypeError(f"{self.__class__} does not accept the type {type(v)} in the list given.")
        self._base_output_list = val

    @abc.abstractmethod
    def deepcopy(self):
        """Return the deepcopy of this instance."""
        cls = self.__class__
        result = cls.__new__(cls)
        result.outputs = list()
        for out in self._base_output_list:
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
        super(NodeOutputManager, self).__init__(output_mappings)
        self.identifier = identifier

    def deepcopy(self):
        new_mgr = super().deepcopy()
        new_mgr.identifier = self.identifier
        return new_mgr


class ModuleOutputManager(BaseOutputManager):
    """
    Module Output Manager class.

    Args:
        identifier (str): The identifier of the module.
        output_mappings (list): a list of output mapping
    """
    def __init__(self, identifier, base_out: Union[BaseOutput, Iterable[BaseOutput]]) -> None:
        super(ModuleOutputManager, self).__init__(None)
        self.identifier = identifier
        self._return_list_counter = 0
        self._base_output_list = list()
        if isinstance(base_out, BaseOutput):
            self._base_output_list.append(base_out)
        else:
            self._base_output_list += base_out

    @property
    def return_num(self):
        """Return the number of outputs to be returned."""
        return self._return_list_counter

    @return_num.setter
    def return_num(self, num: int):
        """Set the number of outputs to be returned."""
        self._return_list_counter = num

    def deepcopy(self):
        """Return a deepcopy of current instance."""
        new_mgr = super().deepcopy()
        new_mgr.identifier = self.identifier
        new_mgr.return_num = self._return_list_counter
        return new_mgr


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

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
"""Parse tensor files from async dump structure."""
import csv
import os
import stat
import sys
from collections import namedtuple
from importlib import import_module
from pathlib import Path

import numpy as np

from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError

PARSE_ARGS_FIELDS = ['dump_path', 'format', 'output_path', 'output_file_type',
                     'input', 'output', 'shape',
                     'custom_script_path', 'dump_version']
CannTool = namedtuple("CannTool", ['utils', 'common', 'log', 'format_conversion',
                                   'compare_error', 'compare_exception'])

class ArgsParser(namedtuple("ArgsParser", PARSE_ARGS_FIELDS)):
    """Args Parser object."""

    __slots__ = ()

    def __new__(cls, **kwargs):
        new_kwargs = {field: kwargs.get(field) for field in PARSE_ARGS_FIELDS}
        new_kwargs['dump_version'] = kwargs.get('dump_version', '2.0')
        return super().__new__(cls, **new_kwargs)


def load_cann_tools(msaccucmp_path=None):
    """
    Load CANN tools.

    Args:
        msaccucmp_path (Path): The path object of msaccucmp.py path.

    Returns:
        tuple, the tuple of utils, common, shape_conversion module in toolkit package.
    """
    msaccucmp_path = get_msaccucmp_path(msaccucmp_path)
    cann_tool_path = msaccucmp_path.parent
    if str(cann_tool_path) not in sys.path:
        sys.path.insert(0, str(cann_tool_path))
    try:
        cann_utils = import_module('utils')
        cann_common = import_module('common')
        cann_format_conversion = import_module('shape_conversion').FormatConversionMain
        cann_log = import_module('log')
    except ModuleNotFoundError:
        raise ModuleNotFoundError(f'Failed to load CANN tools under {cann_tool_path}')
    if not hasattr(cann_log, 'print_error_log'):
        cann_log = cann_utils
    try:
        compare_error = import_module('compare_error')
        cann_compare_error = compare_error.CompareError.MSACCUCMP_NONE_ERROR
        cann_compare_exception = compare_error.CompareError
    except ModuleNotFoundError:
        cann_compare_error = cann_utils.VECTOR_COMPARISON_NONE_ERROR
        cann_compare_exception = cann_utils.CompareError
    return CannTool(cann_utils, cann_common, cann_log, cann_format_conversion,
                    cann_compare_error, cann_compare_exception)


def get_msaccucmp_path(msaccucmp_path=None):
    """
    Get the Path of CANN msaccucmp file.

    Args:
        msaccucmp_path (str): The path of `msaccucmp.py` or `msaccucmp.pyc`. Default: None.

    Returns:
        Path, the msaccucmp.py file path object.
    """
    if msaccucmp_path is not None:
        msaccucmp_path = Path(msaccucmp_path).resolve()
        if not msaccucmp_path.exists():
            raise FileNotFoundError(f"File {msaccucmp_path} doesn't exists. Please check the input value.")
        return msaccucmp_path
    # search msaccucmp file under $ASCEND_AICPU_PATH
    ascend_toolkit_path = os.environ.get('ASCEND_TOOLKIT_PATH', '/usr/local/Ascend/')
    ascend_toolkit_path = Path(ascend_toolkit_path).resolve()
    msaccucmp_files = list(ascend_toolkit_path.rglob('msaccucmp.py*'))
    if not msaccucmp_files:
        # the tools might be soft-link path
        ascend_tool_path = (ascend_toolkit_path / "tools").resolve()
        msaccucmp_files = list(ascend_tool_path.rglob('msaccucmp.py*'))
        if not msaccucmp_files:
            raise FileNotFoundError(f"Failed to find msaccucmp.py or msaccucmp.pyc file under {ascend_toolkit_path}. "
                                    f"Please make sure you have installed toolkit package and set "
                                    f"`ASCEND_TOOLKIT_PATH` in the environment correctly.")
    return msaccucmp_files[0]


class DumpRootDirConverter:
    """Convert the async dump data under dump root directory into host format."""

    def __init__(self, data_loader, msaccucmp_path=None):
        self.data_loader = data_loader
        self.dump_data_dir = Path(data_loader.get_dump_dir())
        self.failed_summary_file = self.dump_data_dir.joinpath('convert_failed_files_summary.txt')
        self._cann_tools = load_cann_tools(msaccucmp_path)
        self.check_async_dir()

    def check_async_dir(self):
        """Check if this directory is dumped asynchronously on Ascend."""
        is_sync = self.data_loader.get_sync_flag()
        if is_sync:
            raise ValueError(f"The data under {str(self.dump_data_dir)} is not dumped asynchronously.")

    def convert(self):
        """Convert dump data under root dump data directory from device format to host format."""
        source_iterations = self.data_loader.get_step_iter()
        failed_lines = []
        if self.failed_summary_file.is_file():
            self.failed_summary_file.unlink()
        for iter_path in source_iterations:
            dump_path = str(iter_path)
            res = DirConvert(dump_path=dump_path, output_path=dump_path, cann_tools=self._cann_tools).convert()
            failed_lines.extend(res)
        # add tensor format in file name

        if failed_lines:
            self.save_failed_fines(failed_lines)
        return failed_lines

    def save_failed_fines(self, failed_lines):
        """Save failed fines to file."""
        with self.failed_summary_file.open('w') as handler:
            for line in failed_lines:
                handler.write(line + '\n')
        self.failed_summary_file.chmod(stat.S_IRUSR)
        self._cann_tools.log.print_info_log(f"Failed summary has saved to {str(self.failed_summary_file)}")


class DirConvert:
    """Convert the async dump data under one directory into host format."""
    MAPPING_FILE_NAME = 'mapping.csv'
    OP_DEBUG_TYPE = 'Opdebug'

    def __init__(self, dump_path, output_path, target_format='NCHW', output_file_type='npy', cann_tools=None):
        self.args_parser = ArgsParser(dump_path=dump_path,
                                      format=target_format,
                                      output_path=output_path,
                                      output_file_type=output_file_type)
        self.output_path = Path(output_path).absolute()
        self.failed_file_path = self.output_path.joinpath('convert_failed_file_list.txt')
        self.cann_tools = load_cann_tools() if cann_tools is None else cann_tools
        self.node_map = self._load_mapping_info()

    def _is_npy_target(self):
        """Check if the output_file type is npy."""
        return self.args_parser.output_file_type == 'npy'

    def clean_old_files(self):
        """Clean old files."""
        # clean failed file record
        if self.failed_file_path.is_file():
            self.failed_file_path.unlink()
        # clean old converted data.
        old_data_files = self.output_path.glob(f'*.{self.args_parser.output_file_type}')
        for file in old_data_files:
            file.unlink()

    def convert(self):
        """Convert async dump data of src_dir to target_format and saved in output_dir."""
        conversion = self.cann_tools.format_conversion(self.args_parser)
        self.clean_old_files()
        failed_lines = []
        ret = conversion.convert_format()
        self.rename_generated_npy_file()
        if ret != self.cann_tools.compare_error:
            self.cann_tools.log.print_info_log(
                f"Begin to convert failed operator in {str(self.failed_file_path)} one by one.")
            failed_lines = self.convert_failed_tensors()
        else:
            self.cann_tools.log.print_info_log(
                f"All tensor under {self.args_parser.dump_path} have been converted to {self.output_path} "
                f"successfully.")
        return failed_lines

    def rename_generated_npy_file(self):
        """Rename the npy file generated by CANN tool to MS file name format."""
        # before change
        # file is {op_type}.{op_name_with_scope}.{task_id}.{stream_id}.{timestamp}.{tensor_type}.{slot}.{shape}.npy
        # or
        # {uuid}.{tensor_type}.{slot}.{shape}.npy
        # after change
        # file is {op_type}.{op_name}.{task_id}.{stream_id}.{timestamp}.{tensor_type}.{slot}.{format}.npy
        if not self._is_npy_target():
            return
        self.cann_tools.log.print_info_log(
            f"Start to rename npy files under {self.output_path}")
        target_format = self.args_parser.format
        old_data_files = self.output_path.glob('*.npy')
        for file in old_data_files:
            name_splits = file.name.split('.')
            node_type = name_splits[0]
            if node_type == DirConvert.OP_DEBUG_TYPE:
                continue
            if node_type.isdigit() and self.node_map.get(node_type) is not None:
                real_name_splits = self.node_map[node_type].split('.')
                real_name_splits[1] = real_name_splits[1].split('_')[-1]
                real_name_splits.extend(name_splits[1:])
                name_splits = real_name_splits
            else:
                name_splits[1] = name_splits[1].split('_')[-1]
            name_splits[-2] = target_format
            new_file_name = '.'.join(name_splits)
            file.chmod(stat.S_IRUSR)
            file.rename(file.with_name(new_file_name))

    def _load_mapping_info(self):
        """Load node name mapping information."""
        mapping_path = self.output_path / DirConvert.MAPPING_FILE_NAME
        node_map = {}
        if mapping_path.is_file():
            with mapping_path.open('r') as handler:
                csv_reader = csv.reader(handler, delimiter=',')
                for row in csv_reader:
                    node_map[row[0]] = row[1]
        return node_map

    def convert_failed_tensors(self):
        """Convert failed tensors from failed txt."""
        failed_lines = []
        if not self.failed_file_path.is_file():
            return failed_lines
        os.chmod(self.failed_file_path, stat.S_IRUSR)
        with self.failed_file_path.open() as handler:
            failed_line = handler.readline().strip('\n')
            while failed_line:
                try:
                    self.convert_operator_by_failed_line(failed_line)
                except (ValueError, OSError, AttributeError) as err:
                    self.cann_tools.log.print_error_log(f'Failed to convert {failed_line} to Host '
                                                        f'format. \n {str(err)}')
                    failed_lines.append(failed_line)
                except self.cann_tools.compare_exception as err:
                    self.cann_tools.log.print_error_log(f'Failed to convert {failed_line} to Host '
                                                        f'format. \n {str(err)}')
                    failed_lines.append(failed_line)
                failed_line = handler.readline().strip('\n')
        if failed_lines:
            self.cann_tools.log.print_error_log(f"Failed to convert: {failed_lines}")
        self.cann_tools.log.print_info_log("Finish convert failed operators to host format.")
        return failed_lines

    def convert_operator_by_failed_line(self, failed_line):
        """Convert operator by failed line."""
        fields = failed_line.split(',')
        if len(fields) > 1:
            op_file = fields[0]
            if os.path.basename(op_file).startswith(DirConvert.OP_DEBUG_TYPE):
                return
            op_data = self.cann_tools.utils.parse_dump_file(op_file, self.args_parser.dump_version)
            missing_tensors = fields[1:]
            for missing_tensor in missing_tensors:
                tensor_type, idx = missing_tensor.split(':')
                idx = int(idx)
                tensor = getattr(op_data, tensor_type)[idx]
                dump_data_array = self.get_tensor_numpy_value(tensor)
                self.save_tensor_file(op_file, tensor_type, idx, tensor, dump_data_array)

    def get_tensor_numpy_value(self, tensor):
        """Convert tensor from device format to host format."""
        dump_data_array = self.cann_tools.utils.deserialize_dump_data_to_array(tensor)
        array = dump_data_array.reshape(tensor.shape.dim)
        return array

    def save_tensor_file(self, op_file, tensor_type, idx, tensor, dump_data_array):
        """
        Save tensor file.

        Args:
            op_file (str): Source operator file path.
            tensor_type (str): The tensor type of the operator, `input` or `output`.
            idx (int): Tensor slot index.
            tensor (TensorProto): Tensor data in proto format.
            dump_data_array (numpy.array): Tensor data in numpy format.
        """
        op_name = os.path.basename(op_file)
        # shorten the op_name to meet the linux file name len limit.
        op_name = self._remove_scope_in_op_name(op_name)
        if self._is_npy_target():
            self._save_tensor_in_npy(op_name, tensor_type, idx, tensor, dump_data_array)
        else:
            self._save_tensor_in_bin(op_name, tensor_type, idx, tensor, dump_data_array)

    def _remove_scope_in_op_name(self, op_name):
        """Remove scope in operation name."""
        name_splits = op_name.split('.')
        node_type = name_splits[0]
        if node_type.isdigit() and self.node_map.get(node_type) is not None:
            name_splits = self.node_map[node_type].split('.')
        name_splits[1] = name_splits[1].split('_')[-1]
        return '.'.join(name_splits)

    def _save_tensor_in_npy(self, op_name, tensor_type, idx, tensor, dump_data_array):
        """
        Save tensor file in `npy` format.

        Args:
            op_name (str): Operator name without scope.
            tensor_type (str): The tensor type of the operator, `input` or `output`.
            idx (int): Tensor slot index.
            tensor (TensorProto): Tensor data in proto format.
            dump_data_array (numpy.array): Tensor data in numpy format.
        """
        out_file_name = "%s.%s.%d.%s.npy" % (
            op_name,
            tensor_type,
            idx,
            self.cann_tools.common.get_format_string(tensor.format)
        )
        out_path = os.path.join(self.args_parser.output_path, out_file_name)
        np.save(out_path, dump_data_array)
        os.chmod(out_path, stat.S_IRUSR)

    def _save_tensor_in_bin(self, op_name, tensor_type, idx, tensor, dump_data_array):
        """
        Save tensor file in `bin` format.

        Args:
            op_name (str): Operator name without scope.
            tensor_type (str): The tensor type of the operator, `input` or `output`.
            idx (int): Tensor slot index.
            tensor (TensorProto): Tensor data in proto format.
            dump_data_array (numpy.array): Tensor data in numpy format.

        Returns:
            str, output tensor file name.
        """
        out_file_name = "%s.%s.%d.%s.%s.bin" % (
            op_name,
            tensor_type,
            idx,
            self.cann_tools.utils.get_string_from_list(dump_data_array.shape, 'x'),
            self.cann_tools.common.get_format_string(tensor.format),
        )
        out_path = os.path.join(self.args_parser.output_path, out_file_name)
        dump_data_array.tofile(out_path)
        os.chmod(out_path, stat.S_IRUSR)


class FileMapping:
    """Mapping op pattern to files."""

    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.output_path = Path(data_loader.get_dump_dir()).absolute()

    def find_tensor_file(self, pattern, rank_ids=None, iterations=None):
        """
        Find tensor files.

        Args:
            pattern (str): File name pattern.
            rank_ids (Union[None, list[int]]): Filter condition of rank id. Default: None.
            iterations (Union[None, list[int]]): Filter condition of iteration id. Default: None.

        Returns:
            OpPathManager, operator path object.
        """
        op_path = OpPathManager(pattern)
        if rank_ids is None:
            rank_dirs = self.data_loader.rank_dirs
        else:
            rank_dirs = []
            for rank_id in rank_ids:
                if not isinstance(rank_id, int):
                    raise DebuggerParamValueError("rank_ids should be list of int.")
                rank_dirs.append(self.data_loader.get_rank_dir(rank_id))

        for rank_dir in rank_dirs:
            op_device_obj = self.find_tensor_file_per_device(pattern, rank_dir.rank_id, iterations)
            op_path.add(op_device_obj)
        return op_path

    def find_tensor_file_per_device(self, pattern, rank_id, iterations):
        """
        Find tensor files per device directory.

        Args:
            pattern (str): File name pattern.
            rank_id (int): The rank id.
            iterations (Union[None, list[int]]): Filter condition of iteration id. Default: None.

        Returns:
            OpDevicePath, operator file path object of one device.
        """
        op_device_obj = OpDevicePath(rank_id)

        def _find_by_iter_dirs(dirs):
            for iter_dir in dirs:
                op_path_per_iter = self.find_tensor_file_per_iter(pattern, iter_dir)
                op_device_obj.add(op_path_per_iter)
        if iterations is None:
            iter_dirs = self.data_loader.get_step_iter(rank_id=rank_id)
            _find_by_iter_dirs(iter_dirs)
        else:
            for iteration in iterations:
                iter_dirs = self.data_loader.get_step_iter(rank_id=rank_id, step=iteration)
                _find_by_iter_dirs(iter_dirs)
        return op_device_obj

    @staticmethod
    def find_tensor_file_per_iter(pattern, iter_dir):
        """
        Find tensor files per iteration directory.

        Args:
            pattern (str): File name pattern.
            iter_dir (Union[Path, str]): Iteration path.

        Returns:
            OpPath, the operator file path object of one iteration.
        """
        dir_path = Path(iter_dir)

        def _get_file_generator(tensor_type):
            return dir_path.glob(f'*{pattern}.*{tensor_type}.[0-9]*.npy')

        in_gen = _get_file_generator('input')
        out_gen = _get_file_generator('output')
        iteration = int(dir_path.name)
        op_path_obj = OpPath(iteration, in_gen, out_gen)
        return op_path_obj


class OpPathManager:
    """The manager of tensor files of one operator."""

    def __init__(self, pattern, op_full_name=None):
        self.pattern = pattern
        self.op_full_name = op_full_name
        self._op_path = {}

    @property
    def devices(self):
        """Get list of iterations in cache."""
        return list(self._op_path.keys())

    def add(self, op_device_path):
        """Add OpDevicePath object."""
        self._op_path[op_device_path.rank_id] = op_device_path

    def rank(self, rank_id):
        """Get OpDevicePath object according to rank id."""
        return self._op_path.get(rank_id)

    def to_dict(self):
        """Get operator files of all devices in dict format."""
        res = {}
        for rank_id, op_path in self._op_path.items():
            key = f'rank_{rank_id}'
            res[key] = op_path.to_dict()
        return res


class OpDevicePath:
    """The operator file object of specific device."""

    def __init__(self, rank_id):
        self._rank_id = rank_id
        # record the operation path object of different iteration
        # the format is like <int, OpPath>
        self._op_path = {}

    @property
    def rank_id(self):
        """The property of rank id."""
        return self._rank_id

    @property
    def iterations(self):
        """Get list of iterations in cache."""
        return list(self._op_path.keys())

    def iteration(self, iteration):
        """Get the op path object according to iteration."""
        return self._op_path.get(iteration)

    def add(self, op_path):
        """Add OpPath object."""
        self._op_path[op_path.iteration] = op_path

    def to_dict(self):
        """Get operator files of one device in dict format."""
        res = {}
        for iteration, op_path in self._op_path.items():
            res[iteration] = op_path.to_dict()
        return res


class OpPath:
    """The operator file object of specific iteration."""

    def __init__(self, iteration, input_gen, output_gen):
        self._iter = iteration
        self._input_files = None
        self._input_gen = input_gen
        self._output_files = None
        self._output_gen = output_gen

    @staticmethod
    def _convert_path_gen_to_list(path_gen):
        """Convert generator of Path.glob to list of string."""
        return [str(path) for path in path_gen]

    @property
    def inputs(self):
        """The list of input tensor files."""
        if self._input_files is None:
            self._input_files = self._convert_path_gen_to_list(self._input_gen)
        return self._input_files

    @property
    def outputs(self):
        """The list of output tensor file paths."""
        if self._output_files is None:
            self._output_files = self._convert_path_gen_to_list(self._output_gen)
        return self._output_files

    @property
    def iteration(self):
        """The iteration of the tensor file."""
        return self._iter

    def to_dict(self):
        """Get operator files of one iteration in dict format."""
        res = {
            'input': self.inputs,
            'output': self.outputs
        }
        return res

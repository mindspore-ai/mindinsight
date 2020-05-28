# Copyright 2020 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless REQUIRED by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""converter module"""
import copy
import importlib
import inspect
import os
import stat

from mindinsight.mindconverter.config import ALL_MAPPING
from mindinsight.mindconverter.config import NN_LIST
from mindinsight.mindconverter.config import ALL_TORCH_APIS
from mindinsight.mindconverter.config import ALL_2P_LIST
from mindinsight.mindconverter.config import UNSUPPORTED_WARN_INFOS
from mindinsight.mindconverter.config import ALL_UNSUPPORTED
from mindinsight.mindconverter.common.log import logger
from mindinsight.mindconverter.forward_call import ForwardCall

LINE_NO_INDEX_DIFF = 1


class Converter:
    """Convert class"""

    convert_info = ''
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    modes = stat.S_IWUSR | stat.S_IRUSR

    @staticmethod
    def is_local_defined(obj, member):
        """
        Check if obj and member are both defined in the same source file.

        Args:
            obj (Union[object, module]): A module or a class.
            member (func): A function of obj.

        Returns:
            bool, True or False.
        """
        srcfile = inspect.getsourcefile(obj)
        return inspect.getsourcefile(member) == srcfile

    @classmethod
    def is_valid_module(cls, obj, member):
        """
        Check if obj and member defined in same source file and member is inherited from torch.nn.Module.

        Args:
            obj (Union[object, module]): A module or a class.
            member (func): A function.

        Returns:
            bool, True or False.
        """
        if inspect.isclass(member):
            is_subclass = member.__base__.__name__ in ['Module',
                                                       'Sequential',
                                                       'ModuleList',
                                                       'ModuleDict',
                                                       'ParameterList',
                                                       'ParameterDict']
            return is_subclass and cls.is_local_defined(obj, member)
        return False

    @classmethod
    def is_valid_function(cls, obj, member):
        """
        Check if member is function and defined in the file same as obj.

        Args:
            obj (Union[object, module]: The obj.
            member (func): The func.

        Returns:
            bool, True or False.
        """
        return inspect.isfunction(member) and cls.is_local_defined(obj, member)

    @staticmethod
    def find_left_parentheses(string, right):
        """
        Find index of the first left parenthesis.

        Args:
            string (str): A line of code.
            right (int): The right index for string to find from.

        Returns:
            int, index of the first parenthesis.

        Raises:
            ValueError: If line of code doesn't contain any pair of `()` or `(` and `)` are not paired.
        """
        if string[right] != ')':
            raise ValueError('code [{}] at index {} not ")".'.format(string, right))
        stack = []
        for i in range(right, -1, -1):
            if string[i] == ')':
                stack.append(')')
            elif string[i] == '(':
                stack.pop()
                if not stack:
                    return i
        raise ValueError("{} should contain ()".format(string))

    @staticmethod
    def find_right_parentheses(string, left):
        """
        Find first index of right parenthesis which make all left parenthesis make sense.

        Args:
            string (str): A line of code.
            left (int): Start index of string to find from.

        Returns:
            int, index of the found right parenthesis.

        Raises:
            ValueError: If line of code doesn't contain any pair of `()` or `(` and `)` are not paired.
        """
        stack = []
        for i in range(left, len(string)):
            if string[i] == '(':
                stack.append('(')
            elif string[i] == ')':
                stack.pop()
                if not stack:
                    return i
        raise ValueError("{} should contain ()".format(string))

    @staticmethod
    def get_call_name(code, end):
        """
        Traverse code in a reversed function from index end and get the call name and start index of the call name,
        if call name not found, return a null character string and -1

        Args:
            code (str): The str of code to find from.
            end (int): Start index to find.

        Returns:
            tuple(str, int), one is founded api name if found, else a null character string, the other is start index
            of founded api name, -1 if api name not found
        """
        stack = []
        for i in range(end - 1, -1, -1):
            if code[i] in ["(", "[", "{"]:
                if stack:
                    stack.pop()
                else:
                    return code[i + 1:end], i + 1
            elif code[i] in [")", "]", "}"]:
                stack.append(code[i])
            elif stack:
                continue
            elif not (code[i].isalpha() or code[i].isdigit() or code[i] == '_' or code[i] == '.'):
                return code[i + 1:end], i + 1
        return "", -1

    def convert_api(self, code, start, api_name=""):
        """
        Convert api_name in code to MindSpore api with start as a start index, if api_name is a python api,
        code will not convert.

        Args:
            code (str): The str code to convert.
            start (int): The index of code to start convert from.
            api_name (str): The api name to convert.

        Returns:
            str, the converted code.
            int, index of converted api_name in code.
        """
        # handle format like .shape(
        if api_name.startswith('.'):
            call_name, new_start = self.get_call_name(code, start)
            if start == -1 or call_name == "self":
                return code, start + 1
        else:
            call_name = api_name
            new_start = start

        # find full api expected to be converted. eg:expr="nn.Conv2d(1,2,3)" args_str="(1,2,3)"
        left = code.find("(", start)
        if left == -1:
            raise ValueError('"(" not found, {} should work with "("'.format(call_name))
        right = self.find_right_parentheses(code, left)
        end = right

        expr = code[start:end + 1]
        args_str = code[left:right + 1]

        map_helper = ALL_MAPPING[api_name]
        new_expr = map_helper.convert(call_name, args_str)
        next_newline = code.find("\n", end + 1)
        fill_num = (expr.count("\n") - new_expr.count("\n"))
        if next_newline != -1:
            code = code[:new_start] + new_expr + code[end + 1:next_newline] + ("\n" * fill_num) + code[next_newline:]
        else:
            code = code[:new_start] + new_expr + ")" + ("\n" * fill_num) + code[end + 2:]

        return code, start + len(map_helper.ms_api.name)

    @staticmethod
    def find_api(code, i, is_forward):
        """
        Find api name from code with a start index i, check api name ok with a is_forward condition.

        Args:
            code (str): The code from which to find api name.
            i (int): The start index to find.
            is_forward (bool): Check if the found api name ok.

        Returns:
            str, api name if find api name and check ok with is_forward condition, else a null character string.
        """
        if code[i:].startswith("nn.") \
                or code[i:].startswith("F.") \
                or code[i:].startswith("torch.") \
                or code[i:].startswith('.'):
            j = code.find('(', i)
            if j != -1 and code[i:j] in ALL_TORCH_APIS:
                api_name = code[i:j]
                if (not is_forward and api_name in NN_LIST) or (is_forward and api_name in ALL_2P_LIST):
                    return api_name
        return ""

    def convert_function(self, fun_name, fun, is_forward):
        """
        Convert a PyTorch function into MindSpore function.

        Args:
            fun_name (str): The str of function name.
            fun (func): The function to convert.
            is_forward (bool): If the function is defined in forward function in nn.Module in torch.

        Returns:
            dict, old code and converted code map if convert happens, else {}.
        """
        _, line_no = inspect.getsourcelines(fun)
        logger.info("Line %3d: start converting function %s()", line_no, fun_name)

        code = inspect.getsource(fun)
        code_saved = copy.copy(code)

        i = 0
        while i < len(code):
            api_name = self.find_api(code, i, is_forward)
            if api_name:
                line_no1 = line_no + code[:i].count('\n')
                if api_name in ALL_MAPPING:
                    logger.info("Line %3d start converting API: %s", line_no1, api_name)
                    code, i = self.convert_api(code, i, api_name)
                    self.convert_info += "[Convert][Line{:3d}] {} is converted.\n".format(line_no1, api_name)
                    continue
                if api_name in ALL_UNSUPPORTED:
                    warn_info = ". " + UNSUPPORTED_WARN_INFOS[api_name] if api_name in UNSUPPORTED_WARN_INFOS else ""
                    logger.warning("Line %3d: found unsupported API: %s%s", line_no1, api_name, warn_info)
                    self.convert_info += "[Unconvert][Line{:3d}] {} didn't convert{}\n".format(line_no1,
                                                                                               api_name, warn_info)
            i += 1
        return {code_saved: code} if code_saved != code else {}

    @staticmethod
    def judge_forward(name, forward_list):
        """
        Check if function is a forward function.

        Args:
            name (str): The function name.
            forward_list (set): A set of forward function.

        Returns:
            bool, True or False
        """
        is_forward = name in forward_list or name.split(".")[-1] == "forward"
        if is_forward:
            logger.debug("%s is a forward function", name)
        return is_forward

    def convert_module(self, module_name, module, forward_list):
        """
        Convert a PyTorch module code into MindSpore module code.

        Args:
            module_name (str): The module's name.
            module (module): The module to convert.
            forward_list (set): A set of forward function.

        Returns:
            dict, map of old code and converted code.
        """
        _, line_no = inspect.getsourcelines(module)
        logger.info("Line {:3d}: start converting nn.Module {}".format(line_no, module_name))

        mapped = {}
        for name, member in inspect.getmembers(module):
            if self.is_valid_function(module, member):
                is_forward = self.judge_forward("{}.{}".format(module_name, name), forward_list)
                mapped.update(self.convert_function(name, member, is_forward))
        return mapped

    def get_mapping(self, import_mod, forward_list):
        """
        Convert code of a module and get mapping of old code and convert code.

        Args:
            import_mod (module): The module to convert.
            forward_list (set): A set of forward function.

        Returns:
            dict, mapping for old code and converted code of the module
        """
        mapping = {}
        tasks = []
        for name, member in inspect.getmembers(import_mod):
            if self.is_valid_module(import_mod, member):
                _, line_no = inspect.getsourcelines(member)
                tasks.append((line_no, self.convert_module, (name, member, forward_list)))
            elif self.is_valid_function(import_mod, member):
                _, line_no = inspect.getsourcelines(member)
                is_forward = self.judge_forward("{}.{}".format(import_mod, name), forward_list)
                tasks.append((line_no, self.convert_function, (name, member, is_forward)))
        tasks.sort()
        for _, convert_fun, args in tasks:
            mapping.update(convert_fun(*args))
        return mapping

    @staticmethod
    def get_code_start_line_num(source_lines):
        """
        Get the start code line number exclude comments.

        Args:
            source_lines (list[str]): Split results of original code.

        Returns:
            int, the start line number.
        """
        stack = []
        index = 0
        for i, line in enumerate(source_lines):
            if line.strip().startswith('#'):
                continue
            if line.strip().startswith('"""'):
                if not line.endswith('"""\n'):
                    stack.append('"""')
                continue
            if line.strip().startswith("'''"):
                if not line.endswith("'''\n"):
                    stack.append("'''")
                continue
            if line.endswith('"""\n') or line.endswith("'''\n"):
                stack.pop()
                continue
            if line.strip() != '' and not stack:
                index = i
                break
        return index

    def update_code_and_convert_info(self, code, mapping):
        """
        Replace code according to mapping, and update convert info.

        Args:
            code (str): The code to replace.
            mapping (dict): Mapping for original code and the replaced code.

        Returns:
            str, the replaced code.
        """

        for key, value in mapping.items():
            code = code.replace(key, value)

        source_lines = code.splitlines(keepends=True)
        start_line_number = self.get_code_start_line_num(source_lines)
        add_import_infos = ['import mindspore\n',
                            'import mindspore.nn as nn\n',
                            'import mindspore.ops.operations as P\n']
        for i, add_import_info in enumerate(add_import_infos):
            source_lines.insert(start_line_number + i, add_import_info)
            self.convert_info += '[Add Import] {}.\n'.format(add_import_info.strip())

        insert_count = len(add_import_infos)
        line_diff = insert_count - LINE_NO_INDEX_DIFF

        for i in range(start_line_number + insert_count, len(source_lines)):
            line = source_lines[i]

            if (line.startswith('from torch') and 'import' in line) or line.startswith('import torch'):
                new_line = '# ' + line
                source_lines[i] = new_line
                self.convert_info += '[Annotate][Line{:3d}] {} is annotated.\n'.format(i - line_diff, line.strip())
            if line.strip().startswith('class') and '(nn.Module)' in line:
                new_line = line.replace('nn.Module', 'nn.Cell')
                source_lines[i] = new_line
                self.convert_info += '[Convert][Line{:3d}] nn.Module is converted.\n'.format(i - line_diff)
            if line.strip().startswith('def forward('):
                new_line = line.replace('forward', 'construct')
                source_lines[i] = new_line
                self.convert_info += '[Convert][Line{:3d}] forward is converted.\n'.format(i - line_diff)
            if 'nn.Linear' in line:
                new_line = line.replace('nn.Linear', 'nn.Dense')
                source_lines[i] = new_line
                self.convert_info += '[Convert][Line{:3d}] nn.Linear is converted.\n'.format(i - line_diff)
            if '(nn.Sequential)' in line:
                new_line = line.replace('nn.Sequential', 'nn.SequentialCell')
                source_lines[i] = new_line
                self.convert_info += '[Convert][Line{:3d}] nn.Sequential is converted.\n'.format(i - line_diff)
            if 'nn.init.' in line:
                new_line = line.replace('nn.init', 'pass  # nn.init')
                source_lines[i] = new_line
                self.convert_info += '[Annotate][Line{:3d}] {} is annotated.\n'.format(i - line_diff, 'nn.init')

        code = ''.join(source_lines)
        return code

    def convert(self, import_name, output_dir, report_dir):
        """
        Convert a module's code, code converted will be save in output_dir, and a report will be save in report_dir.

        Args:
            import_name (str): The module from which to import the module to convert.
            output_dir (str): The path to save converted file.
            report_dir (str): The path to save report file.
        """
        logger.info("Start converting %s", import_name)
        start_info = '[Start Convert]\n'
        module_info = 'The module is {}.\n'.format(import_name)

        import_mod = importlib.import_module(import_name)
        srcfile = inspect.getsourcefile(import_mod)
        logger.info("Script file is %s", srcfile)

        forward_list = set(ForwardCall(srcfile).calls)
        logger.debug("Forward_list: %s", forward_list)

        # replace python function under nn.Module
        mapping = self.get_mapping(import_mod, forward_list)
        code = inspect.getsource(import_mod)
        code = self.update_code_and_convert_info(code, mapping)
        convert_info_split = self.convert_info.splitlines(keepends=True)
        convert_info_split = sorted(convert_info_split)
        convert_info_split.insert(0, start_info)
        convert_info_split.insert(1, module_info)
        convert_info_split.append('[Convert Over]')
        self.convert_info = ''.join(convert_info_split)

        dest_file = os.path.join(output_dir, os.path.basename(srcfile))
        with os.fdopen(os.open(dest_file, self.flags, self.modes), 'w') as file:
            file.write(code)
        logger.info("Convert success. Result is wrote to %s.", dest_file)

        dest_report_file = os.path.join(report_dir,
                                        '_'.join(os.path.basename(srcfile).split('.')[:-1]) + '_report.txt')
        with os.fdopen(os.open(dest_report_file, self.flags, self.modes), 'a') as file:
            file.write(self.convert_info)
        logger.info("Convert report is saved in %s", dest_report_file)


def _get_name_ext(file):
    """
    Split a file name in name and extension.

    Args:
        file (str): Full file path.

    Returns:
        tuple (str, str), name and extension.
    """
    _, name = os.path.split(file)
    return os.path.splitext(name)


def _path_split(file):
    """
    Split a path in head and tail.

    Args:
        file (str): The file path.

    Returns:
        list[str], list of file tail
    """
    file_dir, name = os.path.split(file)
    if file_dir:
        sep = file[len(file_dir)-1]
        if file_dir.startswith(sep):
            return file.split(sep)[1:]

        return file.split(sep)
    return [name]


def main(files_config):
    """
    The entrance for converter, script files will be converted.

    Args:
        files_config (dict): The config of files which to convert.
    """
    convert_ins = Converter()
    root_path = files_config['root_path']
    in_files = files_config['in_files']
    for in_file in in_files:
        in_file_split = _path_split(in_file[len(root_path):])
        in_file_split[-1], _ = _get_name_ext(in_file_split[-1])
        module_name = '.'.join(in_file_split)
        convert_ins.convert(module_name, files_config['outfile_dir'], files_config['report_dir'])

    in_module = files_config.get('in_module')
    if in_module:
        convert_ins.convert(in_module, files_config['outfile_dir'], files_config['report_dir'])

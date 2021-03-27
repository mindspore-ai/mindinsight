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
"""Fix weight names in CheckPoint file when user edits converted MindSpore scripts."""
import os
import re
import argparse
import sys
import ast
from ast import NodeTransformer, ClassDef, Assign, FunctionDef
from importlib import import_module

from mindspore import load_checkpoint, Tensor, save_checkpoint, load_param_into_net
from mindinsight.mindconverter.common.log import logger_console


class FixCheckPointGenerator(NodeTransformer):
    """Fix weight names in CheckPoint file."""

    def __init__(self, source_script_path, target_script_path):
        self._source_script_name = os.path.basename(source_script_path)
        self._target_script_name = os.path.basename(target_script_path)

        self._source_variable_mapper = self._extract(source_script_path)
        self._target_variable_mapper = self._extract(target_script_path)

        self._fixed_mapper = self._generator()

    def _extract(self, script_path):
        """Extract info from AST Tree."""

        with open(script_path, 'r') as rf:
            tree = ast.parse(rf.read())

        variable_mapper = dict()
        for block in tree.body:
            if not isinstance(block, ClassDef):
                continue
            module_name = block.name
            valid_body = [block_pick for block_pick in block.body if isinstance(block_pick, FunctionDef)]
            init_body = valid_body[0]

            variable_name = self._extract_init(init_body)

            if not variable_mapper.get(module_name):
                variable_mapper[module_name] = variable_name
            else:
                variable_mapper[module_name].extend(variable_name)
        return variable_mapper

    @staticmethod
    def _extract_init(init_body):
        """Extract init information."""

        variable_names = list()
        for block in init_body.body:
            if not isinstance(block, Assign):
                continue
            variable_name = block.targets[0].attr
            variable_names.append(variable_name)
        return variable_names

    def _check_data(self, data_1, data_2):
        """Check the shape of two inputs."""

        if len(data_1) != len(data_2):
            logger_console.error(
                f"The construct of {self._source_script_name} and that of {self._target_script_name} ars not matched.")
            exit(0)

    def _generator(self):
        """Generator fixed_mapper."""

        main_module_name = list(self._target_variable_mapper.keys())[-1].lower()
        fixed_variable_mapper = dict()
        fixed_module_mapper = dict()

        self._check_data(self._source_variable_mapper, self._target_variable_mapper)

        for source_module_name, target_module_name in zip(self._source_variable_mapper, self._target_variable_mapper):
            fixed_variable_mapper[target_module_name.lower()] = self._fixed_variable_mapper_generator(
                self._source_variable_mapper[source_module_name], self._target_variable_mapper[target_module_name])

            if source_module_name != target_module_name:
                fixed_module_mapper[source_module_name.lower()] = target_module_name.lower()

        return {
            'main_module_name': main_module_name,
            'fixed_variable_mapper': fixed_variable_mapper,
            'fixed_module_mapper': fixed_module_mapper
        }

    def _fixed_variable_mapper_generator(self, source_variable_names, target_variable_names):
        """Generate fixed_variable_mapper."""

        self._check_data(source_variable_names, target_variable_names)

        fixed_variable_mapper = dict()
        for source_variable_name, target_variable_name in zip(source_variable_names, target_variable_names):
            if source_variable_name != target_variable_name:
                fixed_variable_mapper[source_variable_name] = target_variable_name
        return fixed_variable_mapper

    def fix_ckpt(self, ckpt_path, new_ckpt_path):
        """Fix checkpoint file."""

        param_dict = load_checkpoint(ckpt_path)

        main_module_name = self._fixed_mapper['main_module_name']
        fixed_variable_dict = self._fixed_mapper['fixed_variable_mapper']
        fixed_module_dict = self._fixed_mapper['fixed_module_mapper']

        save_obj = list()
        for weight_name, weight_value in param_dict.items():
            weight_name_scopes = weight_name.split('.')
            weight_name_scopes.insert(0, main_module_name)
            for idx, w in enumerate(weight_name_scopes[:-1]):
                for fixed_variable_module, fixed_variable_name_mapper in fixed_variable_dict.items():
                    if re.match(fixed_variable_module, fixed_module_dict.get('_'.join(w.split('_')[:-1]), w)):
                        weight_name = weight_name.replace(
                            weight_name_scopes[idx + 1],
                            fixed_variable_name_mapper.get(weight_name_scopes[idx + 1], weight_name_scopes[idx + 1]))

            obj = {
                'name': weight_name,
                'data': Tensor(weight_value)
            }
            save_obj.append(obj)

        save_checkpoint(save_obj, new_ckpt_path)
        logger_console.info(f'Saved new checkpoint file to {new_ckpt_path}.')


def source_checker(py_path, ckpt_path):
    """Check source model script and source checkpoint file."""

    sys.path.append(os.path.dirname(py_path))
    model = getattr(import_module(os.path.basename(py_path).replace('.py', '')), 'Model')()
    param_dict = load_checkpoint(ckpt_path)
    not_load_name = load_param_into_net(model, param_dict)
    return not bool(not_load_name)


def file_existed_checker(parser_in, in_file, action_type):
    """Check file exists or not."""

    out_file = os.path.realpath(in_file)
    if not os.path.exists(out_file):
        if action_type == 'in':
            parser_in.error(f"{out_file} does NOT exist, check it.")
        elif not os.path.exists(os.path.dirname(out_file)):
            os.makedirs(os.path.dirname(out_file))
    return out_file


def file_validation_checker(parser_in, in_file, expected_type):
    """Check file is valid or not."""

    if not in_file.endswith(expected_type):
        parser_in.error(f"'xxx{expected_type}' is expected, but gotten {os.path.basename(in_file)}.")


class ScriptAction(argparse.Action):
    """Script action class definition."""

    def __call__(self, parser_in, namespace, values, option_string=None):
        """
        Inherited __call__ method from argparse.Action.

        Args:
            parser_in (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (str): Argument values.
            option_string (str): Optional string for specific argument name. Default: None.
        """

        out_file = file_existed_checker(parser_in, values, "in")
        file_validation_checker(parser_in, out_file, ".py")

        setattr(namespace, self.dest, out_file)


class InCheckPointAction(argparse.Action):
    """In CheckPoint action class definition."""

    def __call__(self, parser_in, namespace, values, option_string=None):
        """
        Inherited __call__ method from argparse.Action.

        Args:
            parser_in (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (str): Argument values.
            option_string (str): Optional string for specific argument name. Default: None.
        """

        out_file = file_existed_checker(parser_in, values, "in")
        file_validation_checker(parser_in, out_file, ".ckpt")

        setattr(namespace, self.dest, out_file)


class OutCheckPointAction(argparse.Action):
    """Out CheckPoint action class definition."""

    def __call__(self, parser_in, namespace, values, option_string=None):
        """
        Inherited __call__ method from argparse.Action.

        Args:
            parser_in (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (str): Argument values.
            option_string (str): Optional string for specific argument name. Default: None.
        """

        out_file = file_existed_checker(parser_in, values, "out")
        file_validation_checker(parser_in, out_file, ".ckpt")

        setattr(namespace, self.dest, out_file)


parser = argparse.ArgumentParser(description="Fix weight names in CheckPoint file.")
parser.add_argument(
    "source_py_file",
    action=ScriptAction,
    help="source model script file")
parser.add_argument(
    "fixed_py_file",
    action=ScriptAction,
    help="fixed model script file")
parser.add_argument(
    "source_ckpt_file",
    action=InCheckPointAction,
    help="source checkpoint file")
parser.add_argument(
    "fixed_ckpt_file",
    action=OutCheckPointAction,
    help="fixed checkpoint file")

if __name__ == '__main__':

    argv = sys.argv[1:]
    if not argv:
        argv = ['-h']
        args = parser.parse_args(argv)
    else:
        args = parser.parse_args()

    source_py_file = args.source_py_file
    fixed_py_file = args.fixed_py_file
    source_ckpt_file = args.source_ckpt_file
    fixed_ckpt_file = args.fixed_ckpt_file

    if not source_checker(source_py_file, source_ckpt_file):
        logger_console.error("source checkpoint file is not inconsistent with source model script.")
        exit(0)

    fix_checkpoint_generator = FixCheckPointGenerator(source_py_file, fixed_py_file)
    fix_checkpoint_generator.fix_ckpt(source_ckpt_file, fixed_ckpt_file)

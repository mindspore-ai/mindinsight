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
"""Define arguments translation related operations for params name changing."""
import copy


class ArgsTranslation:
    """Define a universal arguments translation manager."""

    def __init__(self, original_actual_args: dict, var_name: str, translated_args: list):
        """
        Init the ArgsTranslation.

        Args:
            original_actual_args (dict): The full original args from fragments.
            var_name (str): The var name for current Node / Module.
            translated_args (list): The list of args need to translate to formal args.
        """
        if not var_name:
            raise ValueError("Initialize ArgsTranslation requires the var_name.")

        self.var_name = var_name
        self.actual_args = dict()  # e.g. key is 'num_features', value is 2048
        self.formal_args = dict()  # e.g. key is 'num_features', value is 'var_name_num_features'}
        self.formal_args_values = dict()  # e.g. key 'var_name_num_features', value 2048. Value use for up-level
        self.actual_args_backup = dict()  # backup actual args before translation

        self.actual_args_to_str_list = list()
        self.formal_args_to_str_list = list()
        self.formal_args_values_to_str_list = list()
        self.actual_args_backup_to_str_list = list()

        if all([original_actual_args, translated_args]):
            # MUST ensure only one var_name in a scope.
            for arg_name, arg_value in original_actual_args.items():
                if arg_name in translated_args:
                    formal_arg_name = '_'.join([var_name, arg_name])
                    self.formal_args[arg_name] = formal_arg_name
                    self.formal_args_values[formal_arg_name] = arg_value
                else:
                    self.actual_args[arg_name] = arg_value

            self.make_str()

    @staticmethod
    def dict_data_to_args_str_list(any_dict):
        """
        Output a list of string of dict data by "key=value" format.

        Args:
            any_dict (dict): Any dictionary

        Returns:
            list, the list of strings showing dictionary as "key=value" format.
        """
        ret = []
        for key, val in any_dict.items():
            ret.append('='.join([key, str(val)]))
        return ret

    def make_str(self):
        """Make string used in code generation."""
        self.actual_args_to_str_list = list()
        self.formal_args_to_str_list = list()
        self.formal_args_values_to_str_list = list()
        self.actual_args_backup_to_str_list = list()

        if self.actual_args:
            self.actual_args_to_str_list = ArgsTranslation.dict_data_to_args_str_list(self.actual_args)

        if self.formal_args:
            self.formal_args_to_str_list = ArgsTranslation.dict_data_to_args_str_list(self.formal_args)

        if self.formal_args_values:
            self.formal_args_values_to_str_list = ArgsTranslation.dict_data_to_args_str_list(self.formal_args_values)

        if self.actual_args_backup:
            self.actual_args_backup_to_str_list = ArgsTranslation.dict_data_to_args_str_list(self.actual_args_backup)

    def __repr__(self):
        return str({
            "address": hex(id(self)),
            "var_name": self.var_name,
            "actual_args": self.actual_args,
            "actual_bak": self.actual_args_backup,
            "formal_args": self.formal_args,
            "formal_val ": self.formal_args_values
        })

    def set_actual_args_backup(self):
        """Backup the actual args before translating to formal."""
        self.actual_args_backup = copy.deepcopy(self.actual_args)

    def deepcopy(self):
        """Return a deepcopy of self."""
        return copy.deepcopy(self)

    def make_actual_arg_to_formal(self, actual_arg_name):
        """
        Make the actual arg to a formal arg.

        Args:
            actual_arg_name (str): The name of the actual arg to be formal.
        """
        val = self.actual_args.get(actual_arg_name)
        if val is None:
            raise ValueError("Unable to convert the actual arg to formal due to missing arg.")
        formal_arg_name = ('_').join([self.var_name, actual_arg_name])
        self.actual_args.pop(actual_arg_name)
        self.formal_args[actual_arg_name] = formal_arg_name
        self.formal_args_values[formal_arg_name] = val
        self.make_str()

    def _update_dict_for_upper_level(self, d, upper_level_var_name):
        """Add upper level var name to key name of selected dictionary."""
        new_d = dict()
        for arg_name, val in d.items():
            new_arg_name = '_'.join([upper_level_var_name, arg_name])  # e.g. conv2d_0_in_channels_Module_3_0
            new_d[new_arg_name] = val
        return new_d

    def escalate_to_upper_level(self, upper_level_var_name):
        """
        Escalate this args translator for upper level module use.

        Note:
            You MUST deepcopy this translator first to avoid editing values in the original translator.
        """
        # update all args name by adding upper_level_var_name.
        tmp_actual_args = self._update_dict_for_upper_level(self.actual_args, upper_level_var_name)
        tmp_formal_args = self._update_dict_for_upper_level(self.formal_args, upper_level_var_name)
        tmp_formal_args_values = self._update_dict_for_upper_level(self.formal_args_values, upper_level_var_name)

        self.actual_args = tmp_actual_args
        self.formal_args = tmp_formal_args
        self.formal_args_values = tmp_formal_args_values

        self.make_str()

    def make_formal_args_back_to_actual(self, formal_arg):
        """
        Move the formal arg back to actual arg.

        Note:
            This does not reset the formal arg name back,
            Only used for module init statement.

        Args:
            formal_arg (str): formal argument name.
        """
        if isinstance(formal_arg, str):
            val = self.formal_args_values.pop(formal_arg)
            self.actual_args[formal_arg] = val
        if isinstance(formal_arg, list):
            for arg in formal_arg:
                val = self.formal_args_values.pop(arg)
                self.actual_args[formal_arg] = val

        self.make_str()

    def take_formal_args_from_args_translator(self, args_translator, escalate_sub=False):
        """
        Add submodule's or node's args translator to this translator.

        Args:
            args_translator (ArgsTranslation): submodule's or node's args translator.
        """
        if escalate_sub:
            sub_args_translator = args_translator.deepcopy()
            sub_args_translator.escalate_to_upper_level(self.var_name)
        else:
            sub_args_translator = args_translator

        original_actual_args = sub_args_translator.formal_args_values
        self.actual_args.update(original_actual_args)
        self.make_str()

    def take_formal_args_from_nodes_and_submodules(self, args_translators: list, escalate_sub=False):
        """
        Take all formal args from nodes and submodules from passed in args_translators.

        Args:
            args_translators (ArgsTranslation): A list of ArgsTranslation instances.
            escalate_sub (Bool): should escalate all formal args. Default: False
        """
        for arg_t in args_translators:
            self.take_formal_args_from_args_translator(arg_t, escalate_sub=escalate_sub)


class ArgsTranslationHelper:
    """Define operations related to ArgsTranslation instances."""

    @staticmethod
    def find_formal_args_in_modules(args_translators):
        """
        Find formal args among multiple args translators.

        Args:
            args_translators(list[ArgsTranslation]): a list of args translator to be checked.

        Returns:
            list, name of args to be formal.
        """
        ret = list()
        if len(args_translators) < 2:
            # only one args_translator provided, no formal args.
            return ret

        base_args_t = args_translators[0]
        for arg_name, arg_val in base_args_t.actual_args.items():
            for args_t in args_translators[1:]:
                val = args_t.actual_args.get(arg_name)

                if val is None:
                    raise ValueError("Unable to find the given args as the args translator is not consistent.")
                if val != arg_val:  # val not equal
                    ret.append(arg_name)
                    break
        return ret

    @staticmethod
    def change_args_to_formal_for_all_translators(args_name, args_translators):
        """
        Change args to formal for all translators provided.

        Args:
            args_name (str): The name of args to be changing.
            args_translators (ArgsTranslation): The args to be changed in args translators.
        """
        if isinstance(args_name, str):
            args_name = [args_name]
        if isinstance(args_translators, ArgsTranslation):
            args_translators = [args_translators]

        for arg in args_name:
            for args_t in args_translators:
                args_t.set_actual_args_backup()
                args_t.make_actual_arg_to_formal(arg)

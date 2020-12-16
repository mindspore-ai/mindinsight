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
import os
import stat

import pasta

from mindinsight.mindconverter.common.exceptions import ScriptNotSupport
from mindinsight.mindconverter.common.log import logger
from mindinsight.mindconverter.ast_edits import AstEditVisitor


class Converter:
    """Convert class"""

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    modes = stat.S_IWUSR | stat.S_IRUSR

    def __init__(self):
        self._tree = None
        self._infile = None
        self._code_analyzer = None
        self._ast_editor = None
        self._report = []

    def convert(self, infile, output_dir, report_dir):
        """
        Convert a module's code, code converted will be save in output_dir, and a report will be save in report_dir.

        Args:
            infile (str): The script to convert.
            output_dir (str): The path to save converted file.
            report_dir (str): The path to save report file.
        """
        in_file_split = _path_split(infile)
        in_file_split[-1], _ = _get_name_ext(in_file_split[-1])
        module_name = '.'.join(in_file_split)
        with open(infile, 'r') as file:
            content = ''.join(file.readlines())

        self._infile = infile
        self._tree = pasta.parse(content)
        self._report.clear()
        try:
            logger.info("Script file is %s", infile)
            logger.info("Start converting %s", module_name)
            self._report.append('[Start Convert]')
            self._ast_editor = AstEditVisitor()
            self._ast_editor.process(self._tree)
            self._report.extend(self._ast_editor.get_logs())
            self._report.append('[Convert Over]')
            dest_file = os.path.join(output_dir, os.path.basename(infile))
            with os.fdopen(os.open(dest_file, self.flags, self.modes), 'w') as file:
                script = pasta.dump(self._tree)
                script = adjust_mindspore_import_position(script)
                file.write(script)
            logger.info("Convert success. Result is wrote to %s.", dest_file)
        except ScriptNotSupport as error:
            self._report.append('[ScriptNotSupport] ' + error.message)
            self._report.append('[Convert failed]')
            raise error
        except Exception as error:
            self._report.clear()
            raise error
        finally:
            if self._report:
                dest_report_file = os.path.join(report_dir, f"report_of_{os.path.basename(infile).split('.')[0]}.txt")
                with os.fdopen(os.open(dest_report_file, self.flags, self.modes), 'a') as file:
                    file.write('\n'.join(self._report))
                logger.info("Convert report is saved in %s", dest_report_file)

    @staticmethod
    def convert_api(source_code):
        """
        Convert api_name in code to MindSpore api, if api_name is a python api, code will not convert.

        Args:
            source_code (ast.Call): The ast node to convert.
        Returns:
            str, the converted code.
        """
        ast_node = pasta.parse(source_code).body[0].value
        check_context = False
        replaced_code = AstEditVisitor().mapping_api(ast_node, check_context)
        return replaced_code


def get_code_start_line_num(source_lines):
    """
    Get the start code line number exclude comments.

    Args:
        source_lines (list[str]): Split results of code.

    Returns:
        int, the start line number.
    """
    stack = []
    index = 0
    for i, line in enumerate(source_lines):
        line_strip = line.strip()
        if line_strip.startswith('#'):
            continue
        if line_strip.startswith('"""'):
            if not line_strip.endswith('"""'):
                stack.append('"""')
            continue
        if line_strip.startswith("'''"):
            if not line_strip.endswith("'''"):
                stack.append("'''")
            continue
        if line_strip.endswith('"""') or line_strip.endswith("'''"):
            stack.pop()
            continue
        if line_strip != '' and not stack:
            index = i
            break
    return index


def adjust_mindspore_import_position(script):
    """
    Adjust code sentence `import mindspore` in script to a proper position if the sentence is set before a comment.

    Args:
        script (str): code script before adjust.

    Returns:
        str, code script adjusted.
    """
    script_list = script.split('\n')
    import_ms_sentence = 'import mindspore'
    if import_ms_sentence in script_list:
        import_index = script_list.index(import_ms_sentence)
        if script_list[import_index + 1].startswith('"""') or script_list[import_index + 1].startswith("'''"):
            script_list.pop(import_index)
            new_index = get_code_start_line_num(script_list)
            script_list.insert(new_index, import_ms_sentence)
            script = '\n'.join(script_list)
    return script


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
        sep = file[len(file_dir) - 1]
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
    in_files = files_config['in_files']
    for in_file in in_files:
        convert_ins.convert(in_file, files_config['outfile_dir'], files_config['report_dir'])

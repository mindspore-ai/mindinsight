# Copyright 2020 Huawei Technologies Co., Ltd
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
"""BaseNetwork module."""
import os

from jinja2 import Template

from mindinsight.wizard.base.source_file import SourceFile


def render_template(template_file_path, context):
    with open(template_file_path, encoding='utf-8') as fp:
        content = fp.read()
    template = Template(content, trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
    return template.render(context)


class TemplateManager:
    """BaseNetwork code generator."""
    replace_template_suffixes = [('.py-tpl', '.py'), ('.sh-tpl', '.sh'), ('.md-tpl', '.md')]

    def __init__(self, template_base_dir, exclude_dirs=None, exclude_files=None):
        self.template_base_dir = template_base_dir
        self.exclude_dirs = self._get_exclude_paths(template_base_dir, exclude_dirs)
        self.exclude_files = self._get_exclude_paths(template_base_dir, exclude_files)

    @staticmethod
    def _get_exclude_paths(base_dir, exclude_paths):
        """Convert exclude path to absolute directory path."""
        exclude_abs_paths = []
        if exclude_paths is None:
            return exclude_abs_paths

        for exclude_path in exclude_paths:
            if exclude_path.startswith(base_dir):
                exclude_abs_paths.append(exclude_path)
            else:
                exclude_abs_paths.append(os.path.join(base_dir, exclude_path))
        return exclude_abs_paths

    def get_template_files(self):
        """Get template files for template directory."""
        template_files = []
        for root, sub_dirs, files in os.walk(self.template_base_dir):
            for sub_dir in sub_dirs[:]:
                if sub_dir.startswith('.') or \
                        sub_dir == '__pycache__' or \
                        os.path.join(root, sub_dir) in self.exclude_dirs:
                    sub_dirs.remove(sub_dir)

            for filename in files:
                if os.path.join(root, filename) not in self.exclude_files:
                    template_file_path = os.path.join(root, filename)
                    template_files.append(template_file_path)
        return template_files

    def render(self, **options):
        """Generate the network files."""
        source_files = []
        template_files = self.get_template_files()
        extensions = tuple([new_extension for _, new_extension in self.replace_template_suffixes])
        for template_file in template_files:
            new_file_path = template_file
            template_file_path = template_file
            for template_suffix, new_file_suffix in self.replace_template_suffixes:
                if new_file_path.endswith(template_suffix):
                    new_file_path = new_file_path[:-len(template_suffix)] + new_file_suffix
                    break

            source_file = SourceFile()
            source_file.file_relative_path = new_file_path[len(self.template_base_dir) + 1:]
            source_file.template_file_path = template_file_path
            if new_file_path.endswith(extensions):
                source_file.content = render_template(template_file_path, options)
            else:
                with open(template_file_path, encoding='utf-8') as fp:
                    source_file.content = fp.read()
            source_files.append(source_file)
        return source_files

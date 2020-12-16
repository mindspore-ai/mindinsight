# Copyright 2020 Huawei Technologies Co., Ltd.All Rights Reserved.
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
"""Generate report."""
import abc
import re
from mindinsight.mindconverter.graph_based_converter.constant import NEW_LINE, SEPARATOR_IN_ONNX_OP


class ReportGenerator(metaclass=abc.ABCMeta):
    """Generate report of scripts transformation."""

    def __init__(self):
        self._title = self._gen_title()
        self._extra = self._gen_extra()
        self._content = ''

    @staticmethod
    def _gen_title():
        """
        Generate title of scripts transformation.

        Returns:
            str, title of scripts transformation report.
        """
        title_info = ''
        return title_info

    @staticmethod
    def _gen_extra():
        """
        Generate extra information.

        Returns:
            str, body of scripts transformation report.
        """
        extra_info = {'start': '[Start Convert]',
                      'end': '[Convert Over]'}
        return extra_info

    @property
    def title(self):
        """Title property."""
        return self._title

    @property
    def extra(self):
        """Extra property."""
        return self._extra

    @staticmethod
    def _gen_converted_operator_content(converted_location: list,
                                        converted_operator_name):
        """
        Generate converted operator content.

        Args:
            converted_location (list): Location of converted operator.
            converted_operator_name (str): Name of converted operator.

        Returns:
            String, report content of converted operator.
        """
        unconverted_operator_name = ''
        content = \
            f"line {':'.join(converted_location)}: " \
            f"[Convert]'{unconverted_operator_name}' is converted to " \
            f"{converted_operator_name}."
        return content

    @staticmethod
    def _gen_unconverted_operator_content(unconverted_location: list,
                                          unconverted_operator_name):
        """
        Generate unconverted operator content.

        Args:
            unconverted_location (list): Location of unconverted operator.
            unconverted_operator_name (str): Name of unconverted operator.

        Returns:
            String, report content of unconverted operator.
        """
        content = f"line {':'.join(unconverted_location)}: " \
                  f"[UnConvert] '{unconverted_operator_name}' didn't convert."
        return content

    @staticmethod
    def _get_unsupported_params(num_line, code_line):
        """Get unsupported params in converted operator."""
        if 'UNSUPPORTED' in code_line:
            unsupported_params = re.findall(r"(.*).*[=][{]SUPPORTED", code_line)
            unsupported_msg = re.findall(r".*UNSUPPORTED[:] (.*)[}]", code_line)
            location = [f"{num_line + 1}", f"{code_line.index('UNSUPPORTED') + 1}"]
            unsupported_params_info = \
                f"line {':'.join(location)}: " \
                f"[Unsupported params] {unsupported_params}: {unsupported_msg}."
        else:
            unsupported_params_info = None

        return unsupported_params_info

    def gen_report(self, code: str):
        """
        Generate report.

        Args:
            code (list): Code of converted script.

        Returns:
            String, report of converted script.
        """
        code_lines = code.split(NEW_LINE)
        num_all_lines = len(code_lines)

        num_unconverted_operator = 0
        num_converted_operator = 0
        converted_operator = None
        self._content = self._extra['start']
        for num_line in range(0, num_all_lines):
            code_line = code_lines[num_line]

            if 'P.ResizeNearestNeighbor' in code_line:
                warning_msg = f"[WARNING] {num_line + 1}:{code_line.index('P.ResizeNearestNeighbor') + 1} " \
                    f"The operator ResizeNearestNeighbor may not be converted accurately. " \
                    f"Please check its parameters with your original model and MindSpore official documents."
                self._content = f"{NEW_LINE}".join((self._content, warning_msg))

            if 'onnx.' in code_line:
                num_unconverted_operator += 1
                unconverted_operator = SEPARATOR_IN_ONNX_OP.join(
                    ('onnx', re.findall(r".*onnx.([a-zA-Z]+).*", code_line)[0]))
                info_unconverted_line = self._gen_unconverted_operator_content(
                    [f"{num_line + 1}", f"{code_line.index('onnx.') + 1}"],
                    unconverted_operator
                )
                self._content = f"{NEW_LINE}".join((self._content,
                                                    info_unconverted_line))

            if 'P.' in code_line or 'nn.' in code_line:
                converted_operator = re.findall(r".*(?:nn.|P.)(.*)[(]", code_line)

                if converted_operator:
                    num_converted_operator += 1

            info_unsupported_params = self._get_unsupported_params(
                num_line,
                code_line
            )
            if info_unsupported_params:
                self._content = f"{NEW_LINE}".join((self._content,
                                                    info_unsupported_params))

        self._content = f"{NEW_LINE}".join((self._content, self._extra['end']))

        converted_rate = \
            num_converted_operator / (num_converted_operator + num_unconverted_operator)
        info_converted_rate = f"Converted Rate: {converted_rate * 100:.2f}%.{NEW_LINE}"
        self._content = f"{NEW_LINE}".join((self._content, info_converted_rate))

        return self._content

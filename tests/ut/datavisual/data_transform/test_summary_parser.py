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
"""
Function:
    Test mindinsight.datavisual.data_transform.ms_data_loader.
Usage:
    pytest tests/ut/datavisual
"""
import os
import csv
import time
import shutil
import tempfile
from urllib.parse import quote

from mindinsight.datavisual.data_transform.summary_parser.event_parser import EventParser
from tests.utils.log_generators.images_log_generator import ImagesLogGenerator
from tests.utils.log_generators.scalars_log_generator import ScalarsLogGenerator

ROUND_NUM = 4


class TestSummaryParser:
    """Test ms_data_loader."""

    def setup_class(self):
        """Run before test this class."""
        self.base_summary_dir = tempfile.mkdtemp(suffix='summary')

    def teardown_class(self):
        """Run after test this class."""
        if os.path.exists(self.base_summary_dir):
            shutil.rmtree(self.base_summary_dir)

    def test_parse_and_export_save_csv_file(self):
        """Test parse summary file and save scalar to csv file."""
        summary_dir = tempfile.mkdtemp(dir=self.base_summary_dir)
        test_file_name = '%s/%s.%s.%s' % (summary_dir, 'scalar', 'summary', str(time.time()))
        metadata, _ = TestSummaryParser.prepare_scalar_summary_file(test_file_name)
        event_parse = EventParser(test_file_name, summary_dir)
        event_parse.parse()
        result = TestSummaryParser.parse_csv_file(summary_dir)
        expect_value = TestSummaryParser.get_expect_value(metadata)
        shutil.rmtree(summary_dir)
        assert result == expect_value

    def test_parse_and_export_png_file(self):
        """Test parse summary file and save image to png files."""
        summary_dir = tempfile.mkdtemp(dir=self.base_summary_dir)
        image_dir = os.path.join(summary_dir, 'image')
        os.makedirs(image_dir, mode=0o700)
        test_file_name = '%s/%s.%s.%s' % (summary_dir, 'image', 'summary', str(time.time()))
        expect_names = TestSummaryParser.prepare_image_summary_file(test_file_name)
        event_parse = EventParser(test_file_name, summary_dir)
        event_parse.parse()
        result = sorted(os.listdir(image_dir))
        shutil.rmtree(summary_dir)
        assert result == expect_names

    @staticmethod
    def prepare_scalar_summary_file(test_file_name):
        """Prepare the summary file with scalar data."""
        scalars_log_generator = ScalarsLogGenerator()
        test_steps = [1, 3, 5]
        test_tag = "test_scalar_tag_name"
        return scalars_log_generator.generate_log(test_file_name, test_steps, test_tag)

    @staticmethod
    def prepare_image_summary_file(test_file_name):
        """Prepare the summary file with image data."""
        images_log_generator = ImagesLogGenerator()
        test_steps = [1, 3, 5]
        test_tags = "test_image_tag_name"
        images_log_generator.generate_log(test_file_name, test_steps, test_tags)
        return TestSummaryParser.get_expect_image_names(test_tags, test_steps)

    @staticmethod
    def parse_csv_file(summary_dir):
        """parse csv file to compare the result with expect value."""
        export_path = os.path.join(summary_dir, "scalar.csv")
        results = []
        with open(export_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file, dialect='excel')
            for line in csv_reader:
                results.append(line)
            # The first line is title, so no need to round the value
            for result in results[1:]:
                # The result[3] is the value of scalar, we want to compare the rounded value.
                result[3] = str(round(float(result[3]), ROUND_NUM))

        return results

    @staticmethod
    def get_expect_value(metadata):
        """change the format of expect value to compare with result."""
        expect_value = [['tag', 'step', 'wall_time (unit: seconds)', 'value']]
        for line in metadata:
            expect_value.append(
                [line.get('tag'), str(line.get('step')), str(line.get('wall_time')),
                 str(round(line.get('value'), ROUND_NUM))])

        return expect_value

    @staticmethod
    def get_expect_image_names(test_tags, test_steps):
        """get the names of expected images to compare with result."""
        expect_names = []
        tag = quote(test_tags, safe="")
        for step in test_steps:
            expect_names.append("{}_{}.png".format(tag, step))

        return sorted(expect_names)

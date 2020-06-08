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
"""Profiling api file."""
import os
import time

from marshmallow import ValidationError
from tabulate import tabulate

from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from mindinsight.profiler.analyser.integrator import Integrator
from mindinsight.profiler.common._utils import get_file_names, fwrite_format
from mindinsight.profiler.common.exceptions.exceptions import ProfilerFileNotFoundException, \
    ProfilerIOException
from mindinsight.profiler.common.log import logger
from mindinsight.profiler.common.validator.checkparam import \
    check_bool, check_subgraph
from mindinsight.profiler.common.validator.validate_path import \
    validate_and_normalize_path
from mindinsight.profiler.parser.aicpu_data_parser import DataPreProcessParser
from mindinsight.profiler.parser.framework_parser import FrameworkParser
from mindinsight.profiler.parser.hwts_log_parser import HWTSLogParser
from mindinsight.profiler.parser.minddata_parser import MinddataParser
from mindinsight.profiler.parser.minddata_pipeline_parser import \
    MinddataPipelineParser
from mindinsight.profiler.parser.optime_parser import OPComputeTimeParser
from mindinsight.profiler.parser.step_trace_parser import StepTraceParser
from mindinsight.utils.exceptions import MindInsightException

PROFILING_LOG_BASE_PATH = "/var/log/npu/profiling"
INIT_OP_NAME = 'Default/InitDataSetQueue'


class Profiler:
    """
    Performance profiling API.

    Enable MindSpore users to profile the performance of neural network.

    Args:
        subgraph (str): Define which subgraph to monitor and analyse, can be 'all', 'Default', 'Gradients'.
        is_detail (bool): Whether to show profiling data for op_instance level, only show optype level if False.
        is_show_op_path (bool): Whether to save the full path for each op instance.
        output_path (str): Output data path.
        optypes_to_deal (str): Op type names, the data of which optype should be collected and analysed,
            will deal with all op if null; Different op types should be seperated by comma.
        optypes_not_deal (str): Op type names, the data of which optype will not be collected and analysed;
            Different op types should be seperated by comma.

    Examples:
        >>> from mindinsight.profiler import Profiler
        >>> context.set_context(mode=context.GRAPH_MODE, device_target="Ascend",
        >>>                     device_id=int(os.environ["DEVICE_ID"]))
        >>> profiler = Profiler(subgraph='all', is_detail=True, is_show_op_path=False, output_path='./data')
        >>> model = Model(train_network)
        >>> dataset = get_dataset()
        >>> model.train(2, dataset)
        >>> profiler.analyse()
    """

    _base_profiling_container_path = "/var/log/npu/profiling/container"
    _hwts_output_filename_target = "output_format_data_hwts_"
    _opcompute_output_filename_target = "output_op_compute_time_"
    _aicpu_op_output_filename_target = "output_data_preprocess_aicpu_"

    def __init__(self, subgraph='all', is_detail=True, is_show_op_path=False, output_path='./data',
                 optypes_to_deal='', optypes_not_deal='Variable', job_id=""):
        # get device_id and device_target
        device_target = ""
        dev_id = ""
        try:
            import mindspore.context as context
            dev_id = str(context.get_context("device_id"))
            device_target = context.get_context("device_target")
        except ImportError:
            logger.error("Profiling: fail to import context from mindspore.")
        except ValueError as err:
            logger.error("Profiling: fail to get context, %s", err)

        if not dev_id:
            dev_id = os.getenv('DEVICE_ID')
        if not dev_id:
            dev_id = "0"
            logger.error("Fail to get DEVICE_ID, use 0 instead.")

        if device_target and device_target != "Davinci" \
            and device_target != "Ascend":
            msg = ("Profiling: unsupport backend: %s" \
                   % device_target)
            raise RuntimeError(msg)

        self._dev_id = dev_id
        self._container_path = os.path.join(self._base_profiling_container_path, dev_id)
        data_path = os.path.join(self._container_path, "data")
        if not os.path.exists(data_path):
            os.makedirs(data_path)
        self._output_path = validate_and_normalize_path(output_path,
                                                        'Profiler output path (' + output_path + ')')
        self._output_path = os.path.join(self._output_path, "profiler")
        if not os.path.exists(self._output_path):
            os.makedirs(self._output_path)

        os.environ['PROFILING_MODE'] = 'true'
        os.environ['PROFILING_OPTIONS'] = 'training_trace:task_trace'
        os.environ['MINDDATA_PROFILING_DIR'] = self._output_path
        # use context interface to open profiling, for the new mindspore version(after 2020.5.21)
        try:
            import mindspore.context as context
            context.set_context(enable_profiling=True, profiling_options="training_trace:task_trace")
        except ImportError:
            logger.error("Profiling: fail to import context from mindspore.")
        except ValueError as err:
            logger.error("Profiling: fail to set context, %s", err.message)

        os.environ['AICPU_PROFILING_MODE'] = 'true'
        os.environ['PROFILING_DIR'] = str(self._container_path)
        self._subgraph = check_subgraph(subgraph)
        self._valid_optype_name = optypes_to_deal.split(",") if optypes_to_deal else []
        self._filt_optype_names = optypes_not_deal.split(",") if optypes_not_deal else []
        self._detail = check_bool(is_detail, 'is_detail')
        self._withfullpath = check_bool(is_show_op_path, 'is_show_op_path')
        self._profiling_job_id = job_id
        # add job id env through user input later
        self._job_id_env = 0
        self._start_time = int(time.time() * 10000000)
        logger.info("Profiling: profiling start time: %d", self._start_time)

    def analyse(self):
        """
        Collect and analyse performance data, called after training or during training.

        Examples:
            >>> from mindinsight.profiler import Profiler
            >>> context.set_context(mode=context.GRAPH_MODE, device_target="Ascend",
            >>>                     device_id=int(os.environ["DEVICE_ID"]))
            >>> profiler = Profiler(subgraph='all', is_detail=True, is_show_op_path=False, output_path='./data')
            >>> model = Model(train_network)
            >>> dataset = get_dataset()
            >>> model.train(2, dataset)
            >>> profiler.analyse()
        """

        try:
            from mindspore.communication.management import release
            release()
        except ImportError:
            logger.error("Profiling: fail to import release from mindspore.")

        logger.info("begin profiler analyse")

        job_id = self._get_profiling_job_id()
        if not job_id:
            msg = ("Fail to get profiling job, please check whether job dir was generated under path %s" \
                   % PROFILING_LOG_BASE_PATH)
            raise RuntimeError(msg)

        logger.info("Profiling: job id is %s ", job_id)

        source_path = os.path.join(PROFILING_LOG_BASE_PATH, job_id)
        # parse hwts.log.data.45.dev file, and get task profiling data
        hwts_output_filename = self._hwts_output_filename_target + self._dev_id + ".txt"
        hwts_output_filename = os.path.join(self._output_path, hwts_output_filename)
        hwtslog_parser = HWTSLogParser(source_path, hwts_output_filename)
        result = hwtslog_parser.execute()
        if not result:
            logger.error("Profiling: fail to parse hwts log file.")
            return

        # parse Framework file, and get the relation of op and tasks
        framework_parser = FrameworkParser(job_id, self._dev_id, self._output_path)
        framework_parser.parse()
        op_task_dict = framework_parser.to_task_id_full_op_name_dict()
        if not op_task_dict:
            logger.error("Profiling: fail to parse framework files.")
            return

        # get op compute time from hwts data and framework data, write output_op_compute_time.txt
        opcompute_output_filename = self._opcompute_output_filename_target + self._dev_id + ".txt"
        opcompute_output_filename = os.path.join(self._output_path, opcompute_output_filename)
        optime_parser = OPComputeTimeParser(
            hwts_output_filename, opcompute_output_filename,
            op_task_dict, self._output_path, self._dev_id
        )
        optime_parser.execute()

        # parse DATA_PREPROCESS.dev.AICPU file, write output_data_preprocess_aicpu_x.txt
        output_data_preprocess_aicpu = self._aicpu_op_output_filename_target + self._dev_id + ".txt"
        output_data_preprocess_aicpu = os.path.join(self._output_path, output_data_preprocess_aicpu)
        try:
            aicpu_data_parser = DataPreProcessParser(source_path, output_data_preprocess_aicpu)
            aicpu_data_parser.execute()
        except FileNotFoundError as err:
            logger.exception(err)

        # Parsing minddata AICPU profiling
        MinddataParser.execute(source_path, self._output_path, self._dev_id)

        # parse minddata pipeline operator and queue
        try:
            pipeline_parser = MinddataPipelineParser(job_id, self._dev_id)
            pipeline_parser.parse()
        except MindInsightException as err:
            logger.warning(err.message)

        # analyse op compute time info
        try:
            self._analyser_op_info()
        except MindInsightException as err:
            logger.warning(err.message)

        # analyse step trace info
        self._analyse_step_trace(source_path, framework_parser)

        # analyse timeline info
        self._analyse_timeline()

    def _analyse_step_trace(self, source_path, framework_parser):
        """
        Analyse step trace data and save the result.

        Args:
            source_path (str): The directory that contains the step trace original data.
            framework_parser (FrameworkParser): The framework parse instance.
        """
        logger.info("Begin to parse step trace.")
        # construct output path
        step_trace_intermediate_file_path = os.path.join(
            self._output_path,
            f'step_trace_raw_{self._dev_id}_detail_time.csv'
        )
        # whether keep the first step
        skip_first_step_flag = framework_parser.check_op_name(INIT_OP_NAME)
        # parser the step trace files and save the result to disk
        parser = StepTraceParser(input_dir=source_path,
                                 output_file_path=step_trace_intermediate_file_path,
                                 job_id=self._job_id_env,
                                 skip_first_step=skip_first_step_flag)
        parser.parse_and_save()
        # print parser result
        parser.show()

    def _analyse_timeline(self):
        """
        Analyse and parse timeline info.
        """
        # Get framework info
        aicoredetail_analyser = AnalyserFactory.instance().get_analyser(
            'aicore_detail', self._output_path, self._dev_id
        )
        framework_info = aicoredetail_analyser.query()

        # Get all reduce info
        step_trace_analyser = AnalyserFactory.instance().get_analyser(
            'step_trace', self._output_path, self._dev_id
        )
        all_reduce_info = step_trace_analyser.query_for_all_reduce()

        # Get timeline info
        timeline_analyser = AnalyserFactory.instance().get_analyser(
            'timeline', self._output_path, self._dev_id
        )
        timeline_analyser.add_framework_info(framework_info)
        timeline_analyser.add_all_reduce_info(all_reduce_info)
        try:
            timeline_analyser.write_timeline()
            timeline_analyser.write_timeline_summary()
        except (ProfilerIOException, ProfilerFileNotFoundException, ValidationError) as err:
            logger.warning('Fail to write timeline data: %s', err)

    def __del__(self):
        """Disable the profiling collection service, called after training."""

        os.environ['PROFILING_MODE'] = str("false")

    def _get_profiling_job_id(self):
        """Get profiling job id, which was generated by ada service.

        Returns:
            str: profiling jon id.
        """

        if self._profiling_job_id:
            return self._profiling_job_id

        job_id = ""
        cmd = "ls -t " + PROFILING_LOG_BASE_PATH + "|grep JOB|awk '{print $1}'"
        r = os.popen(cmd)
        profiling_job_dirs = r.readlines()
        r.close()
        for item in profiling_job_dirs:
            path = os.path.join(PROFILING_LOG_BASE_PATH, item.strip())
            log_file = get_file_names(path, "host_start.log")
            if not log_file:
                logger.error("Profiling: job path %s, host_start.log not exist.", path)
                continue

            log_file = os.path.join(path, log_file[0])
            item_dict = self._parse_host_start_log(log_file)

            if not item_dict:
                logger.error("Profiling: job path %s, fail to get job start info.", path)
                continue
            if self._start_time > int(item_dict["start_time"]):
                logger.info("Profiling: job path %s, start_time %s, training start_time %d.",
                            path, item_dict["start_time"], self._start_time)
                break

            if self._dev_id != item_dict["device_id"]:
                logger.info("Profiling: job path %s, dev id %s, training device id %s.",
                            path, item_dict["device_id"], self._dev_id)
                continue

            job_id = item.strip()
            break

        return job_id

    def _parse_host_start_log(self, input_file):
        """
        Parse host start log file, get the device id and start time of the job.

        Args:
             input_file (str): The file path of the host start log file.

        Returns:
            dict, job start time and device id.
        """

        item_dict = {}
        for line in open(input_file):
            if "Device" in line:
                item_dict["device_id"] = line[7:len(line)-2]
            elif "clock_realtime" in line:
                item_dict["start_time"] = line[16:len(line)-3]

        return item_dict

    def _analyser_op_info(self):
        """Analyse the operator information."""
        integrator = Integrator(self._output_path, self._dev_id)
        integrator.integrate()

        aicore_type_result = self._query_op_type_info()
        detail_file_path = os.path.join(
            self._output_path,
            'output_op_compute_time_detail_{}.txt'.format(self._dev_id)
        )
        fwrite_format(detail_file_path, data_source='title:op compute time')
        display_names = [
            'optype_name', 'compute_time(ms, per-step)',
            'called_times(per-step)', 'percent'
        ]
        data_source = tabulate(aicore_type_result, display_names)
        fwrite_format(detail_file_path, data_source=data_source, is_print=True)

        if self._detail:
            op_type_order = [item[0] for item in aicore_type_result]
            aicore_detail_result = self._query_op_detail_info(op_type_order)
            fwrite_format(detail_file_path, data_source='', is_print=True)
            fwrite_format(detail_file_path, data_source='Detail:', is_print=True)
            data_source = tabulate(
                aicore_detail_result.get('object'),
                aicore_detail_result.get('col_name')
            )
            fwrite_format(detail_file_path, data_source=data_source, is_print=True)

    def _query_op_type_info(self):
        """
        Query AICORE operator type information.

        Returns:
            list[list], the AICORE operator type and execution time information.
        """
        condition = {
            'sort_condition': {
                'name': 'execution_time',
                'type': 'descending'
            }
        }
        analyser = AnalyserFactory.instance().get_analyser(
            'aicore_type', self._output_path, self._dev_id
        )
        result = analyser.query(condition)
        return result.get('object')

    def _query_op_detail_info(self, op_type_order):
        """
        Query AICORE operator detail information.

        Args:
            op_type_order(list): The name of the op type in order.

        Returns:
            dict, the AICORE operator detail information.
        """

        op_type_condition = {}
        if self._valid_optype_name:
            op_type_condition['in'] = self._valid_optype_name
        if self._filt_optype_names:
            op_type_condition['not_in'] = self._filt_optype_names

        subgraph_condition = {}
        if self._subgraph != 'all':
            subgraph_condition['in'] = [self._subgraph]

        filter_condition = {
            'op_type': op_type_condition,
            'subgraph': subgraph_condition,
            'is_display_detail': False,
            'is_display_full_op_name': self._withfullpath
        }
        analyser = AnalyserFactory.instance().get_analyser(
            'aicore_detail', self._output_path, self._dev_id
        )
        result = analyser.query_and_sort_by_op_type(
            filter_condition, op_type_order
        )
        return result

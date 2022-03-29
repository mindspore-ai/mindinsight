<!--
Copyright 2021 Huawei Technologies Co., Ltd.All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
<template>
  <div class="operator">
    <div class="operator-title">{{$t('profiling.operatorDetail')}}</div>
    <div class="cl-profiler">
      <el-tabs v-model="apiType"
               @tab-click="tabChange">
        <el-tab-pane label="HOSTCPU"
                     name="host">
          <operator-unit chartId="host-echarts"
                         :currentCard="currentCard"
                         :opType="hostType"
                         :opSortCondition="hostSortCondition"
                         :search="hostSearch"
                         :chart="hostChart"
                         :accuracy="3"
                         :headerFilder="hostHeaderFilder"
                         :unit="$t('profiling.unit')"
                         ref="host" />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>
<script>
import operatorUnit from '../../components/operator-unit.vue';
export default {
  components: { operatorUnit },
  data() {
    return {
      apiType: 'host',
      currentCard: '',
      gpuOpType: {
        all: 'gpu_op_type',
        detail: 'gpu_op_info',
      },
      gpuCudaType: {
        all: 'gpu_cuda_activity',
        detail: 'gpu_cuda_activity',
      },
      hostType: {
        all: 'cpu_op_type',
        detail: 'cpu_op_info',
      },
      gpuOpSortCondition: {
        all: {
          name: 'avg_time',
          type: 'descending',
        },
        detail: {
          name: 'op_avg_time',
          type: 'descending',
        },
      },
      gpuCudaSortCondition: {
        all: {
          name: 'avg_duration',
          type: 'descending',
        },
        detail: {
          name: 'avg_duration',
          type: 'descending',
        },
      },
      hostSortCondition: {
        all: {
          name: 'avg_time',
          type: 'descending',
        },
        detail: {
          name: 'op_avg_time',
          type: 'descending',
        },
      },
      headerFilder: {
        total_time: 'total_time (us)',
        avg_time: `avg_time (${this.$t('profiling.gpuunit')})`,
        op_total_time: 'op_total_time (us)',
        op_avg_time: `op_avg_time (${this.$t('profiling.gpuunit')})`,
        max_duration: 'max_duration (us)',
        min_duration: 'min_duration (us)',
        avg_duration: `avg_duration (${this.$t('profiling.gpuunit')})`,
        total_duration: 'total_duration (us)',
        proportion: 'total_time_proportion (%)',
        cuda_activity_cost_time: 'cuda_activity_cost_time (us)',
        cuda_activity_call_count: `cuda_activity_call_count (${this.$t('profiling.countUnit')})`,
        type_occurrences: `type_occurrences (${this.$t('profiling.countUnit')})`,
        op_occurrences: `op_occurrences (${this.$t('profiling.countUnit')})`,
        occurrences: `occurrences (${this.$t('profiling.countUnit')})`,
        execution_frequency: `execution_frequency (${this.$t('profiling.countUnit')})`,
        percent: 'percent (%)',
        avg_execution_time: `avg_execution_time (${this.$t('profiling.unit')})`,
        total_compute_time: 'total_compute_time (ms)',
        compute_time: `compute_time (${this.$t('profiling.unit')})`,
        total_proportion: 'total_proportion (%)',
      },
      hostHeaderFilder: {
        type_occurrences: `type_occurrences (${this.$t('profiling.countUnit')})`,
        execution_frequency: `execution_frequency (${this.$t('profiling.countUnit')})`,
        percent: 'percent (%)',
        avg_execution_time: `avg_execution_time (${this.$t('profiling.unit')})`,
        total_compute_time: 'total_compute_time (ms)',
        compute_time: `compute_time (${this.$t('profiling.unit')})`,
        total_time_proportion: 'total_time_proportion (%)',
        op_occurrences: `op_occurrences (${this.$t('profiling.countUnit')})`,
        op_total_time: 'op_total_time (ms)',
        avg_time: `avg_time (${this.$t('profiling.unit')})`,
        op_avg_time: `op_avg_time (${this.$t('profiling.unit')})`,
      },
      gpuOpSearch: {
        all: {
          label:
            this.$t('operator.searchByType') +
            this.$t('symbols.leftbracket') +
            this.$t('public.caseMode') +
            this.$t('symbols.rightbracket'),
          type: 'op_type',
        },
        detail: {
          label:
            this.$t('operator.searchByName') +
            this.$t('symbols.leftbracket') +
            this.$t('public.caseMode') +
            this.$t('symbols.rightbracket'),
          type: 'op_name',
        },
      },
      gpuCudaSearch: {
        all: {
          label:
            this.$t('operator.searchByType') +
            this.$t('symbols.leftbracket') +
            this.$t('public.caseMode') +
            this.$t('symbols.rightbracket'),
          type: 'op_type',
        },
        detail: {
          label:
            this.$t('operator.searchByType') +
            this.$t('symbols.leftbracket') +
            this.$t('public.caseMode') +
            this.$t('symbols.rightbracket'),
          type: 'op_type',
        },
      },
      hostSearch: {
        all: {
          label:
            this.$t('operator.searchByType') +
            this.$t('symbols.leftbracket') +
            this.$t('public.caseMode') +
            this.$t('symbols.rightbracket'),
          type: 'op_type',
        },
        detail: {
          label:
            this.$t('operator.searchByName') +
            this.$t('symbols.leftbracket') +
            this.$t('public.caseMode') +
            this.$t('symbols.rightbracket'),
          type: 'op_name',
        },
      },
      gpuOpChart: {
        value: 4,
      },
      gpuCudaChart: {
        value: 8,
      },
      hostChart: {
        value: 4,
        percent: 5,
      },
      gpuCudaSearchType: 'name',
      gpuCudaSearchOptions: [
        {
          label: 'name',
          value: 'name',
          placeHolder:
            this.$t('operator.searchByCoreName') +
            this.$t('symbols.leftbracket') +
            this.$t('public.caseMode') +
            this.$t('symbols.rightbracket'),
        },
        {
          label: 'op_full_name',
          value: 'op_full_name',
          placeHolder:
            this.$t('operator.searchByCoreFullName') +
            this.$t('symbols.leftbracket') +
            this.$t('public.caseMode') +
            this.$t('symbols.rightbracket'),
        },
      ],
    };
  },
  watch: {
    '$parent.curDashboardInfo': {
      handler(newValue, oldValue) {
        if (newValue.curCardNum) {
          this.currentCard = newValue.curCardNum;
          this.initOver = false;
          this.$nextTick(() => {
            this.cardChange();
          });
        }
        if (newValue.initOver) {
          this.initOver = true;
        }
      },
      deep: true,
      immediate: true,
    },
  },
  destroyed() {},
  methods: {
    cardChange() {
      const ref = this.$refs[this.apiType];
      ref.clearCoreData();
      if (this.apiType !== 'cuda') {
        ref.coreStatisticType = 0;
      } else {
        ref.coreTableChange();
      }
      ref.getCoreTypeList();
    },
    tabChange() {
      const ref = this.$refs[this.apiType];
      if (this.currentCard !== ref.coreCharts.device_id) {
        ref.getCoreTypeList();
        if (this.apiType === 'cuda') {
          setTimeout(() => {
            ref.coreTableChange();
          }, 100);
        }
      } else {
        this.$nextTick(() => {
          ref.resizeCallback();
        });
      }
    },
  },
  mounted() {
    if (this.train_id) {
      document.title = `${this.train_id}-${this.$t('profiling.operatorDetail')}-MindInsight`;
    } else {
      document.title = `${this.$t('profiling.operatorDetail')}-MindInsight`;
    }
  },
};
</script>
<style>
.operator {
  height: 100%;
}
.operator .clear {
  clear: both;
}
.operator .el-tabs__item {
  color: #6c7280;
  line-height: 36px;
  height: 36px;
}
.operator .el-tabs__item.is-active {
  color: #00a5a7;
  font-weight: bold;
}
.operator .operator-title {
  padding: 0 15px;
  font-size: 18px;
  font-weight: bold;
}
.operator .cl-profiler {
  height: calc(100% - 24px);
  overflow-y: auto;
  width: 100%;
  padding: 0 16px;
  overflow: hidden;
}
.operator .cl-profiler .custom-label {
  max-width: calc(100% - 25px);
  padding: 0;
  vertical-align: middle;
}
.operator .cl-profiler .el-tabs {
  height: 100%;
}
.operator .cl-profiler .el-tabs .el-tabs__header {
  margin-bottom: 10px;
}
.operator .cl-profiler .el-tabs__content {
  height: calc(100% - 46px);
}
.operator .cl-profiler .el-tab-pane {
  height: 100%;
}
</style>

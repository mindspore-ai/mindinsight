<!--
Copyright 2020-2021 Huawei Technologies Co., Ltd.All Rights Reserved.

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
    <div class="profiling-content-title">{{$t('profiling.operatorDetail')}}</div>
    <div class="cl-profiler">
      <el-tabs v-model="apiType"
               @tab-click="tabChange">
        <el-tab-pane label="AICORE"
                     name="core">
          <operator-unit chartId="core-echarts"
                         :currentCard="rankID"
                         :opType="coreOpType"
                         :opSortCondition="coreOpSortCondition"
                         :search="coreSearch"
                         :accuracy="6"
                         :headerFilder="headerFilder"
                         :chart="aicoreOpChart"
                         :unit="$t('profiling.gpuunit')"
                         :hasFlopsInfo="true"
                         ref="core" />
        </el-tab-pane>
        <el-tab-pane label="AICPU"
                     class="cpu-tab"
                     name="cpu">
          <operator-unit chartId="cpu-echarts"
                         :currentCard="rankID"
                         :opType="cpuOpType"
                         :opSortCondition="cpuOpSortCondition"
                         :search="cpuSearch"
                         :accuracy="6"
                         :headerFilder="headerFilder"
                         :chart="aicpuOpChart"
                         :unit="$t('profiling.gpuunit')"
                         ref="cpu" />
        </el-tab-pane>
        <el-tab-pane label="HOSTCPU"
                     class="cpu-tab"
                     name="host">
          <operator-unit chartId="host-echarts"
                         :currentCard="rankID"
                         :opType="hostType"
                         :opSortCondition="hostSortCondition"
                         :search="hostSearch"
                         :accuracy="6"
                         :headerFilder="hostHeaderFilder"
                         :chart="hostOpChart"
                         :unit="$t('profiling.gpuunit')"
                         ref="host" />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>
<script>
import operatorUnit from '@/components/operator-unit.vue';
import {isInteger} from '@/js/utils';
export default {
  components: {operatorUnit},
  props: {
    rankID: String,
  },
  data() {
    return {
      trainInfo: {
        id: this.$route.query.id,
        path: this.$route.query.path,
        dir: this.$route.query.dir,
      }, // Complete train info
      labelName: "AICORE",
      apiType: 'core',
      coreOpType: {
        all: 'aicore_type',
        detail: 'aicore_detail',
      },
      cpuOpType: {
        all: 'aicpu_type',
        detail: 'aicpu_detail',
      },
      hostType: {
        all: 'cpu_op_type',
        detail: 'cpu_op_info',
      },
      coreOpSortCondition: {
        all: {
          name: 'total_time',
          type: 'descending',
        },
        detail: {
          name: 'avg_execution_time',
          type: 'descending',
        },
      },
      cpuOpSortCondition: {
        all: {
          name: 'total_time',
          type: 'descending',
        },
        detail: {
          name: 'avg_execution_time',
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
        execution_time: `execution_time (${this.$t('profiling.gpuunit')})`,
        avg_execution_time: `avg_execution_time (${this.$t('profiling.gpuunit')})`,
        execution_frequency: `execution_frequency (${this.$t('profiling.countUnit')})`,
        total_percent: 'total_percent (%)',
        total_time: 'total_time (us)',
        dispatch_time: 'dispatch_time (us)',
        total_compute_time: 'total_compute_time (us)',
        compute_time: `compute_time (${this.$t('profiling.gpuunit')})`,
        total_time_proportion: 'total_time_proportion (%)',
        op_total_time: 'op_total_time (us)',
        avg_time: `avg_time (${this.$t('profiling.gpuunit')})`,
        op_avg_time: 'op_avg_time (us)',
        FLOPs: 'FLOPs (M)',
        FLOPS: 'FLOPS (G/s)',
        FLOPS_Utilization: 'FLOPS_Utilization (%)',
      },
      hostHeaderFilder: {
        type_occurrences: `type_occurrences (${this.$t('profiling.countUnit')})`,
        execution_frequency: `execution_frequency (${this.$t('profiling.countUnit')})`,
        percent: 'percent (%)',
        avg_execution_time: `avg_execution_time (${this.$t('profiling.gpuunit')})`,
        total_compute_time: 'total_compute_time (us)',
        compute_time: `compute_time (${this.$t('profiling.gpuunit')})`,
        total_time_proportion: 'total_time_proportion (%)',
        op_occurrences: `op_occurrences (${this.$t('profiling.countUnit')})`,
        op_total_time: 'op_total_time (us)',
        avg_time: `avg_time (${this.$t('profiling.gpuunit')})`,
        op_avg_time: `op_avg_time (${this.$t('profiling.gpuunit')})`,
      },
      coreSearch: {
        all: {
          label:
            this.$t('operator.searchByKernelType') +
            this.$t('symbols.leftbracket') +
            this.$t('public.caseMode') +
            this.$t('symbols.rightbracket'),
          type: 'kernel_type',
        },
        detail: {
          label:
            this.$t('operator.searchByKernelName') +
            this.$t('symbols.leftbracket') +
            this.$t('public.caseMode') +
            this.$t('symbols.rightbracket'),
          type: 'kernel_name',
        },
      },
      cpuSearch: {
        all: {
          label:
            this.$t('operator.searchByKernelType') +
            this.$t('symbols.leftbracket') +
            this.$t('public.caseMode') +
            this.$t('symbols.rightbracket'),
          type: 'kernel_type',
        },
        detail: {
          label:
            this.$t('operator.searchByKernelType') +
            this.$t('symbols.leftbracket') +
            this.$t('public.caseMode') +
            this.$t('symbols.rightbracket'),
          type: 'kernel_type',
        },
      },
      hostSearch: {
        all: {
          label:
            this.$t('operator.searchByKernelType') +
            this.$t('symbols.leftbracket') +
            this.$t('public.caseMode') +
            this.$t('symbols.rightbracket'),
          type: 'kernel_type',
        },
        detail: {
          label:
            this.$t('operator.searchByKernelName') +
            this.$t('symbols.leftbracket') +
            this.$t('public.caseMode') +
            this.$t('symbols.rightbracket'),
          type: 'kernel_name',
        },
      },
      aicoreOpChart:{
        value: 4,
      },
      aicpuOpChart:{
        value: 1,
      },
      hostOpChart: {
        value: 4,
        percent: 5,
      },
    };
  },
  watch: {
    rankID: {
      handler(newValue) {
        if (isInteger(newValue)) {
          this.initOver = false;
          this.$nextTick(() => {
            this.cardChange();
          });
        } else {
          if (newValue === '') {
            this.initOver = true;
          }
        }
      },
      immediate: true,
    },
  },
  destroyed() {},
  methods: {
    cardChange() {
      const ref = this.$refs[this.apiType];
      ref.clearCoreData();
      ref.coreStatisticType = 0;
      ref.getCoreTypeList();
      if (this.apiType === 'core') {
        ref.getFlopsSummary();
      }
    },
    tabChange() {
      const ref = this.$refs[this.apiType];
      if (this.rankID !== ref.coreCharts.device_id) {
        ref.getCoreTypeList();
      } else {
        this.$nextTick(() => {
          ref.resizeCallback();
        });
      }
    },
  },
  mounted() {
    const id = this.trainInfo.id;
    document.title = `${id ? id + '-' : ''}${this.$t('profiling.operatorDetail')}-MindInsight`;
  },
  created() {
    const mode = this.$route.query.mode;
  }
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
  height: 24px;
}
.operator .cl-profiler {
  height: calc(100% - 30px);
  overflow-y: auto;
  width: 100%;
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

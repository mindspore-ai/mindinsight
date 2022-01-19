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
  <!-- cl-cluster-->
  <div class="cl-cluster">
    <div class="cl-cluster-bk">
      <div class="profiling-content-title">
        {{$t("profilingCluster.clusterStepView")}}
        <el-tooltip class="item"
                    effect="light"
                    placement="top-start"
                    v-if="tips.length">
          <div slot="content"
               class="step-trace-tooltip-contain">
            <div v-for="(item,key) in tips"
                 :key="key"
                 class="step-trace-tooltip-contain-item">
              <span class="label">{{item.label}}</span> {{ item.value }}
            </div>
          </div>
          <i class="el-icon-info"></i>
        </el-tooltip>
      </div>
      <div class="cl-step-filter">
        <label>{{stepTip}}</label>
        <el-input class="step-input"
                  clearable
                  @clear="viewStepFilter"
                  v-model.number="step.showStep"></el-input>
        <el-button @click="viewStepFilter">{{$t("public.sure")}}</el-button>
        <label>{{stageTip}}</label>
        <el-select v-model="stageId"
                   @change="queryStepTraceInfo(true)">
          <el-option v-for="item in stageArr"
                     :key="item"
                     :label="item"
                     :value="item"></el-option>
        </el-select>
      </div>
      <div class="cl-cluster-chart"
           ref="clusterChart">
      </div>
      <div class="cl-cluster-table">
        <el-table :data="tableData"
                  height="100%"
                  width="100%"
                  ref="table"
                  stripe
                  @sort-change="tableSortChange">
          <el-table-column width="120"
                           prop="rank_id"
                           :label="$t('profilingCluster.rankID')">
          </el-table-column>
          <template v-for="item in cols">
            <el-table-column :prop="item"
                             :key="item"
                             sortable="custom">
              <template slot="header">
                <div :title="`${getHeaderField(item)}(ms)`"
                     class="col-name">{{getHeaderField(item)}}(ms)</div>
              </template>
            </el-table-column>
          </template>
          <el-table-column fixed="right"
                           width="180">
            <template slot="header">
              {{$t("summaryManage.operation")}}
            </template>
            <template slot-scope="scope">
              <el-button type="text"
                         size="small"
                         @click="viewProfilingDetail(scope.row)">{{$t("profiling.viewDetail")}}</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="cl-cluster-page">
        <el-pagination @current-change="currentPageChange"
                       @size-change="currentPageSizeChange"
                       :page-sizes="pageSizes"
                       :page-size="group_condition.limit"
                       :current-page="group_condition.offset+1"
                       layout="total,sizes,prev,pager,next,jumper"
                       :total="totalCount">
        </el-pagination>
      </div>
    </div>

    <div class="no-data-img"
         v-show="!chartData.length">
      <div>
        <img :src="require('@/assets/images/nodata.png')"
             alt="">
        <p>{{initOver?$t("public.noData"):$t("public.dataLoading")}}</p>
      </div>
    </div>
  </div>
</template>

<script>
import echarts, { echartsThemeName } from '@/js/echarts';
import RequestService from '@/services/request-service';
export default {
  data() {
    return {
      trainInfo: {
        id: this.$route.query.id,
        path: this.$route.query.path,
        dir: this.$route.query.dir,
      },
      chartObj: null, // chart obj
      chartData: [], // chart data
      chartOption: {
        // chart option
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow',
          },
          confine: true,
        },
        legend: {
          right: 70,
          top: 8,
          data: '',
        },
        grid: {
          top: 35,
          left: 80,
          right: 80,
        },
        dataset: {},
        xAxis: {
          name: this.$t('profilingCluster.rankID'),
          nameTextStyle: {
            align: 'left',
            padding: [0, 5],
          },
          type: 'category',
        },
        yAxis: {
          name: this.$t('profilingCluster.timeTitle'),
          nameGap: 20,
          nameTextStyle: {
            align: 'right',
            padding: [0, 5],
          },
          splitLine: {
            lineStyle: {
              width: 1,
              type: 'dashed',
            },
          },
        },
        series: [],
        dataZoom: [],
      },
      chartResizeTimer: null, // delay after the window size is changed
      tableData: [], // table data
      initOver: false, // init over
      pageSizes: [10, 20, 50],
      group_condition: {
        // page setting
        offset: 0,
        limit: 10,
      },
      sort_condition: {},
      totalCount: 0,
      step: {
        // step info
        maxStep: '',
        filterStep: '',
        showStep: '',
      },
      stepTip: this.$t('profiling.stepInputTip'),
      cols: [],
      stageId: '',
      stageArr: [],
      stageTip: this.$t('profiling.stageTip'),
      tips: [], // Proper noun explanation tips
    };
  },
  mounted() {
    const id = this.trainInfo.id;
    if (!id) {
      this.$message.error(this.$t('trainingDashboard.invalidId'));
      this.initOver = true;
      return;
    }
    document.title = (id ? id + '-' : '') + `${this.$t('profilingCluster.clusterView')}-MindInsight`;
    // adding a Listener
    window.addEventListener('resize', this.resizeCallback, false);
    this.$bus.$on('collapse', this.resizeCallback);
    this.queryStepTraceInfo(true);
  },
  destroyed() {
    // remove the size of a window and change the listener
    window.removeEventListener('resize', this.resizeCallback);
    this.$bus.$off('collapse', this.resizeCallback);
    // remove chart calculation delay
    if (this.chartResizeTimer) {
      clearTimeout(this.chartResizeTimer);
      this.chartResizeTimer = null;
    }
  },
  methods: {
    getHeaderField(item) {
      const headerFields = {
        iteration_interval: this.$t('profiling.iterationGapTime'),
        fp_and_bp: this.$t('profiling.fpBpTime'),
        tail: this.$t('profiling.tailTime'),
        communication_alone: this.$t('profilingCluster.communicationAloneTime'),
        computation: this.$t('profilingCluster.computationTime'),
        receive_alone: this.$t('profilingCluster.receiveAloneTime'),
        stage: this.$t('profilingCluster.stageTime'),
        collective_communication_alone: this.$t('profilingCluster.collectiveCommunicationAlone'),
      };
      return headerFields[item];
    },
    /**
     *  initialize
     *  @param {Boolean} isInit whether get all data
     */

    queryStepTraceInfo(isInit) {
      const params = {
        params: { train_id: this.trainInfo.id },
        body: { filter_condition: {} },
      };
      if (this.sort_condition.type) {
        params.body.sort_condition = this.sort_condition;
      }
      if (!isInit) {
        params.body.group_condition = this.group_condition;
      }
      if (this.step.filterStep !== '') {
        params.body.filter_condition.step_id = this.step.filterStep;
      }
      if (this.stageId !== '' && this.stageId !== this.$t('debugger.all')) {
        params.body.filter_condition.stage_id = this.stageId;
      }
      RequestService.getClusterInfo(params)
        .then((res) => {
          if (res && res.data && res.data.info && res.data.info.length) {
            this.initOver = true;
            this.step.maxStep = res.data.total_step_num;
            this.stepTip = this.$t('profiling.stepInputTip', { max: this.step.maxStep });
            this.totalCount = res.data.size;
            this.stageArr = new Array(res.data.stage_num).fill().map((val, key) => key + 1);
            if (this.stageArr.length > 1) this.stageArr.unshift(this.$t('debugger.all'));
            if (!this.stageId) this.stageId = this.stageArr[0];
            const tempChartData = [];
            const parallelMode = res.data['parallel-mode'];
            const parallelModes = {
              'data-parallel': {
                model: 'step_trace_info',
                dimensions: [
                  this.$t('profilingCluster.rankID'),
                  this.$t('profiling.iterationGapTime'),
                  this.$t('profiling.fpBpTime'),
                  this.$t('profiling.tailTime'),
                ],
                cols: ['iteration_interval', 'fp_and_bp', 'tail'],
                tips: [
                  {
                    label: this.$t('profiling.iterationGapTime'),
                    value: this.$t('profilingCluster.iterationGapTimeTip'),
                  },
                  {
                    label: this.$t('profiling.fpBpTime'),
                    value: this.$t('profilingCluster.fpBpTimeTip'),
                  },
                  {
                    label: this.$t('profiling.tailTime'),
                    value: this.$t('profilingCluster.tailTimeTip'),
                  },
                ],
              },
              'model-parallel': {
                model: 'step_bottleneck_info',
                dimensions: [
                  this.$t('profilingCluster.rankID'),
                  this.$t('profiling.iterationGapTime'),
                  this.$t('profilingCluster.computationTime'),
                  this.$t('profilingCluster.communicationAloneTime'),
                ],
                cols: ['iteration_interval', 'computation', 'communication_alone'],
                tips: [
                  {
                    label: this.$t('profiling.iterationGapTime'),
                    value: this.$t('profilingCluster.iterationGapTimeTip'),
                  },
                  {
                    label: this.$t('profilingCluster.communicationAloneTime'),
                    value: this.$t('profilingCluster.communicationAloneTimeTip'),
                  },
                  {
                    label: this.$t('profilingCluster.computationTime'),
                    value: this.$t('profilingCluster.computationTimeTip'),
                  },
                ],
              },
              'pipeline-parallel': {
                model: 'step_bottleneck_info',
                dimensions: [
                  this.$t('profilingCluster.rankID'),
                  this.$t('profiling.iterationGapTime'),
                  this.$t('profilingCluster.computationTime'),
                  this.$t('profilingCluster.stageTime'),
                  this.$t('profilingCluster.communicationAloneTime'),
                  this.$t('profilingCluster.collectiveCommunicationAlone'),
                  this.$t('profilingCluster.receiveAloneTime'),
                ],
                cols: [
                  'iteration_interval',
                  'computation',
                  'stage',
                  'communication_alone',
                  'collective_communication_alone',
                  'receive_alone',
                ],
                tips: [
                  {
                    label: this.$t('profiling.iterationGapTime'),
                    value: this.$t('profilingCluster.iterationGapTimeTip'),
                  },
                  {
                    label: this.$t('profilingCluster.receiveAloneTime'),
                    value: this.$t('profilingCluster.receiveAloneTimeTip'),
                  },
                  {
                    label: this.$t('profilingCluster.stageTime'),
                    value: this.$t('profilingCluster.stageTimeTip'),
                  },
                  {
                    label: this.$t('profilingCluster.communicationAloneTime'),
                    value: this.$t('profilingCluster.communicationAloneTimeTip'),
                  },
                  {
                    label: this.$t('profilingCluster.computationTime'),
                    value: this.$t('profilingCluster.computationTimeTip'),
                  },
                  {
                    label: this.$t('profilingCluster.collectiveCommunicationAlone'),
                    value: this.$t('profilingCluster.collectiveCommunicationAloneTip'),
                  },
                ],
              },
            };
            this.tips = parallelModes[parallelMode].tips;
            if (isInit) {
              res.data.info.forEach((item) => {
                const chartItem = [item.rank_id].concat(item[parallelModes[parallelMode].model]);
                tempChartData.push(chartItem);
              });
              // sort
              this.chartData = [];
              if (parallelMode === 'pipeline-parallel') {
                tempChartData.forEach((val) => {
                  this.chartData.push([val[0], val[1], val[2], val[4], val[3], val[6], val[5]]);
                });
              } else {
                this.chartData = tempChartData;
              }
              this.initChart(parallelModes[parallelMode].dimensions);
            }
            this.cols = parallelModes[parallelMode].cols;
            const tempTableData = res.data.info.slice(0, this.group_condition.limit);
            this.tableData = [];
            tempTableData.forEach((item) => {
              const tableItem = {};
              tableItem.rank_id = item.rank_id;
              tableItem.profiler_dir = item.profiler_dir;
              let stepTraceInfo = item[parallelModes[parallelMode].model];
              if (parallelMode === 'pipeline-parallel') {
                stepTraceInfo = [
                  stepTraceInfo[0],
                  stepTraceInfo[1],
                  stepTraceInfo[3],
                  stepTraceInfo[2],
                  stepTraceInfo[5],
                  stepTraceInfo[4],
                ];
              }
              stepTraceInfo.forEach((val, key) => {
                tableItem[this.cols[key]] = stepTraceInfo[key];
              });
              this.tableData.push(tableItem);
            });
          }
        })
        .catch((error) => {
          this.initOver = true;
          this.chartData = [];
          this.tableData = [];
        });
    },
    /**
     *  init chart
     * @param {Array} dimensions
     */
    initChart(dimensions) {
      this.chartOption.dataset = {
        dimensions,
        source: [dimensions].concat(this.chartData),
      };
      const endValue = this.chartData.length > 25 ? 25 : this.chartData.length; // show bar numbers as default
      this.chartOption.dataZoom = [
        {
          startValue: 0,
          endValue: endValue,
        },
        {
          startValue: 0,
          endValue: endValue,
          type: 'inside',
        },
      ];
      this.chartOption.series = new Array(dimensions.length - 1).fill({
        type: 'bar',
        barWidth: 8,
      });
      this.$nextTick(() => {
        if (!this.chartObj) {
          this.chartObj = echarts.init(this.$refs.clusterChart, echartsThemeName);
        }
        this.chartObj.setOption(this.chartOption, true);
      });
    },
    /**
     *  window resize
     */

    resizeCallback() {
      if (this.chartResizeTimer) {
        clearTimeout(this.chartResizeTimer);
        this.chartResizeTimer = null;
      }

      this.chartResizeTimer = setTimeout(() => {
        if (this.chartObj) {
          this.chartObj.resize();
        }
      }, 200);
    },

    /**
     *  route jump
     *  @param {Object} row
     */

    viewProfilingDetail(row) {
      this.$router.push({
        path: '/profiling/single/performance',
        query: Object.assign(this.trainInfo, { rankID: row.rank_id }),
      })
    },

    /**
     *  current page change
     * @param {Number} val current page
     */
    currentPageChange(val) {
      this.group_condition.offset = val - 1;
      this.queryStepTraceInfo(false);
    },
    /**
     *  current page size change
     * @param {Number} pageSize current page size
     */
    currentPageSizeChange(pageSize) {
      this.group_condition.offset = 0;
      this.group_condition.limit = pageSize;
      this.queryStepTraceInfo(false);
    },
    /**
     *  table sort change
     *  @param {Object} column current column
     */
    tableSortChange(column) {
      this.sort_condition = {
        name: column.prop,
        type: column.order,
      };
      this.group_condition.offset = 0;
      this.queryStepTraceInfo(true);
    },
    /**
     *  filter step to overview
     */
    viewStepFilter() {
      if (/^[0-9]*[1-9][0-9]*$/.test(this.step.showStep) && this.step.showStep <= this.step.maxStep) {
        this.step.filterStep = this.step.showStep;
        this.group_condition.offset = 0;
        this.queryStepTraceInfo(true);
      } else if (this.step.showStep === '') {
        this.step.filterStep = '';
        this.group_condition.offset = 0;
        this.queryStepTraceInfo(true); // show average data
      } else {
        this.step.showStep = this.step.filterStep;
        this.$message.error(this.$t('profiling.inputError').replace('{max}', this.step.maxStep));
      }
    },
  },
};
</script>
<style>
.cl-cluster {
  height: 100%;
  background-color: var(--bg-color);
}
.cl-cluster .cl-cluster-bk {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.step-trace-tooltip-contain .step-trace-tooltip-contain-item {
  line-height: 20px;
  margin-bottom: 3px;
}
.step-trace-tooltip-contain .step-trace-tooltip-contain-item span.label {
  font-weight: bold;
  margin-right: 3px;
}
.cl-cluster .no-data-img {
  background: var(--bg-color);
  text-align: center;
  position: absolute;
  top: 56px;
  bottom: 0px;
  width: 100%;
  z-index: 999;
  display: flex;
  justify-content: center;
  align-items: center;
}
.cl-cluster .no-data-img p {
  font-size: 16px;
  padding-top: 10px;
}
.cl-cluster .el-table th > .cell {
  color: var(--font-color);
}
.cl-cluster .el-table td > .cell {
  margin-left: 10px;
}
.cl-cluster .el-table td:first-child .cell {
  margin-left: 0;
}
.cl-cluster .el-table th {
  user-select: auto;
}
.cl-cluster .thSpan {
  color: #d4d9e6;
  margin-right: 8px;
}
.cl-cluster .col-name {
  max-width: calc(100% - 25px);
  vertical-align: middle;
}
.cl-cluster .cl-cluster-chart {
  height: 280px;
  margin-top: 5px;
  flex-shrink: 0;
}
.cl-cluster .cl-cluster-table {
  flex: 1;
  margin-top: 20px;
  overflow: hidden;
}
.cl-cluster .cl-cluster-page {
  padding-top: 10px;
  text-align: right;
}
.cl-cluster .cl-step-filter .cl-step-filter {
  display: inline-block;
}
.cl-cluster .cl-step-filter .el-input {
  width: 120px;
  margin: 0 20px;
}
.cl-cluster .cl-step-filter .el-button {
  border: 1px solid #00a5a7;
  border-radius: 2px;
  background-color: var(--bg-color);
  color: var(--theme-color);
  padding: 7px 15px;
  margin-right: 20px;
}
</style>

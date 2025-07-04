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
  <div class="performance-dashboard">
    <div class="container">
      <div class="header"
           @click="jump('step-trace', performanceState === normalState)">
        <span class="title">{{ performanceChart.title }}</span>
        <span :class="{
                'jump': true,
                'is-effective': performanceState === normalState
              }">
          {{ $t('profiling.viewDetail') }}
          <i class="el-icon-d-arrow-right"></i>
        </span>
      </div>
      <div class="content"
           ref="performance">
        <empty :state="performanceState"></empty>
      </div>
    </div>
    <div class="container">
      <div class="header"
           @click="jump('communication', commState === normalState)">
        <span class="title">{{ commChart.title }}</span>
        <span :class="{
                'jump': true,
                'is-effective': commState === normalState
              }">
          {{ $t('profiling.viewDetail') }}
          <i class="el-icon-d-arrow-right"></i>
        </span>
      </div>
      <div class="content"
           ref="comm">
        <empty :state="commState"></empty>
      </div>
    </div>
  </div>
</template>

<script>
import echarts, { echartsThemeName } from '@/js/echarts';
import RequestService from '@/services/request-service';
import empty, { NO_DATA, LOADING_DATA, HETEROGENEOUS } from '@/components/empty';
import { keepDecimalPlaces } from '@/js/utils';
const DEFAULT_DECIMAL_PLACES = 4;
export default {
  components: {
    empty,
  },
  data() {
    return {
      trainInfo: {
        id: this.$route.query.id,
        path: this.$route.query.path,
        dir: this.$route.query.dir,
      }, // Info of current training job
      resizeTimer: null, // Timer ID of Debounce of resize event callback
      performanceState: LOADING_DATA, // State of performance window
      performanceChart: {
        dom: null,
        instance: null,
        data: null,
        dimensions: [
          this.$t('profilingCluster.rankID'),
          this.$t('profiling.iterationGapTime'),
          this.$t('profiling.fpBpTime'),
          this.$t('profiling.tailTime'),
          this.$t('profiling.iterTotalTime')
        ],
        title: this.$t('profilingCluster.stepChartTitle'),
      }, // Chart object of performance window
      commState: LOADING_DATA,
      commChart: {
        dom: null,
        instance: null,
        data: null,
        dimensions: [
          this.$t('profilingCluster.rankID'),
          this.$t('profilingCluster.commCost'),
          this.$t('profilingCluster.waitCost'),
        ],
        title: this.$t('profilingCluster.commChartTitle'),
      },
      normalState: 'normal', // Normal page state
      themeIndex: this.$store.state.themeIndex, // Index of theme color
    };
  },
  mounted() {
    this.performanceChart.dom = this.$refs.performance ? this.$refs.performance : null;
    this.commChart.dom = this.$refs.comm ? this.$refs.comm : null;
    this.queryPerformanceInfo().then((state) => {
      if (state) this.initChart(this.performanceChart);
    });
    this.queryCommInfo().then((state) => {
      if (state) this.initChart(this.commChart);
    });
    window.addEventListener('resize', this.resizeCallBack);
    this.$bus.$on('collapse', this.resizeCallBack);
  },
  methods: {
    /**
     * The logic of callback of resize event
     */
    resizeCallBack() {
      if (this.resizeTimer) {
        clearTimeout(this.resizeTimer);
      }
      this.resizeTimer = setTimeout(() => {
        if (this.performanceChart.dom && this.performanceChart.instance) {
          this.performanceChart.instance.resize();
        }
        if (this.commChart.dom && this.commChart.instance) {
          this.commChart.instance.resize();
        }
      }, 100); // 100: Delay of debounce of callback
    },
    /**
     * The logic of click details
     * @param {string} path
     * @param {boolean} effective
     */
    jump(path, effective) {
      if (!effective) return;
      this.$emit('viewDetail', path);
    },
    /**
     * The logic of query performance info
     * @return {Promise}
     */
    queryPerformanceInfo() {
      return new Promise((resolve) => {
        const params = {};
        params.params = {
          train_id: this.trainInfo.id,
        };
        RequestService.getClusterInfo(params)
          .then((res) => {
            if (res?.data?.info?.length > 0) {
              let chartData = [];
              const parallelMode = res.data['parallel-mode'];
              const parallelModes = {
                'data-parallel': {
                  model: 'step_trace_info',
                  dimensions: [
                    this.$t('profilingCluster.rankID'),
                    this.$t('profiling.iterationGapTime'),
                    this.$t('profiling.fpBpTime'),
                    this.$t('profiling.tailTime'),
                    this.$t('profiling.iterTotalTime')
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
                },
              };
              const tempChartData = [];
              res.data.info.forEach((item) => {
                const chartItem = [item.rank_id].concat(item[parallelModes[parallelMode].model]);
                tempChartData.push(chartItem);
              });
              // sort
              if (parallelMode === 'pipeline-parallel') {
                tempChartData.forEach((val) => {
                  chartData.push([val[0], val[1], val[2], val[4], val[3], val[6], val[5]]);
                });
              } else {
                chartData = tempChartData;
              }
              this.performanceChart.data = chartData;
              this.performanceChart.dimensions = parallelModes[parallelMode].dimensions;
              this.performanceState = this.normalState;
              resolve(true);
            } else {
              this.performanceState = NO_DATA;
            }
          })
          .catch((e) => {
            this.performanceState = NO_DATA;
            resolve(false);
          });
      });
    },
    /**
     * The logic of query communication info
     * @return {Promise}
     */
    queryCommInfo() {
      return new Promise((resolve) => {
        const params = {};
        params.params = {
          train_id: this.trainInfo.id,
        };
        RequestService.getCommInfo(params)
          .then((res) => {
            if (res?.data?.communication.length > 0) {
              const chartData = [];
              res.data.communication.forEach((item) => {
                chartData.push([
                  item.rank_id,
                  keepDecimalPlaces(item.communication_info[0], DEFAULT_DECIMAL_PLACES),
                  keepDecimalPlaces(item.communication_info[1], DEFAULT_DECIMAL_PLACES),
                ]);
              });
              this.commChart.data = chartData;
              this.commState = this.normalState;
              resolve(true);
            } else {
              this.commState = NO_DATA;
            }
          })
          .catch((e) => {
            this.commState = NO_DATA;
            resolve(false);
          });
      });
    },

    /**
     * The logic of init echart
     * @param {Object} chart
     */
    initChart(chart) {
      if (!chart.dom) return;
      if (!chart.instance) {
        chart.instance = echarts.init(chart.dom, echartsThemeName);
      }
      chart.instance.setOption({
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow',
          },
          confine: true,
        },
        legend: {
          right: 70,
          top: 15,
          data: '',
        },
        grid: {
          top: 60,
          left: 80,
          right: 80,
        },
        dataset: {
          source: [chart.dimensions].concat(chart.data),
        },
        xAxis: {
          name: this.$t('profilingCluster.rankID'),
          nameTextStyle: {
            align: 'left',
            padding: [0, 5],
          },
          type: 'category',
          axisLine: {
            lineStyle: {
              width: 2,
            },
          },
        },
        yAxis: {
          name: this.$t('profilingCluster.timeTitle'),
          nameGap: 20,
          nameTextStyle: {
            align: 'right',
            padding: [0, 5],
          },
          axisLine: {
            lineStyle: {
              width: 2,
            },
          },
          splitLine: {
            lineStyle: {
              type: 'dashed',
            },
          },
        },
        series: new Array(chart.dimensions.length - 1).fill({ type: 'bar', barWidth: 8 }),
      });
    },
  },
  beforeDestroy() {
    if (this.resizeTimer) {
      clearTimeout(this.resizeTimer);
    }
    window.removeEventListener('resize', this.resizeCallBack);
    this.$bus.$off('collapse', this.resizeCallBack);
  },
};
</script>

<style scoped>
.performance-dashboard {
  display: grid;
  grid-template-rows: calc(50% - 10px) calc(50% - 10px);
  grid-template-columns: 100%;
  height: 100%;
  row-gap: 20px;
}
.performance-dashboard .container {
  width: 100%;
  height: 100%;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 15px;
  position: relative;
}
.performance-dashboard .content {
  width: 100%;
  height: calc(100% - 24px);
}
.performance-dashboard .header {
  width: 100%;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.performance-dashboard .header .title {
  font-size: 16px;
  font-weight: bold;
}
.performance-dashboard .header .jump {
  cursor: not-allowed;
  color: var(--button-disabled-font-color);
  font-size: 12px;
}
.performance-dashboard .header .is-effective {
  color: var(--theme-color);
  cursor: pointer;
}
</style>

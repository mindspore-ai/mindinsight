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
      <div class="header" @click="jump('performance', performanceState === normalState)">
        <span class="title">{{ performanceChart.title }}</span>
        <span :class="{
                'jump': true,
                'is-effective': performanceState === normalState
              }">
          {{ $t('profiling.viewDetail') }}
          <i class="el-icon-d-arrow-right"></i>
        </span>
      </div>
      <div class="content" ref="performance">
        <empty :state="performanceState"></empty>
      </div>
    </div>
  </div>
</template>

<script>
import echarts from '../../js/echarts';
import RequestService from '../../services/request-service';
import empty, {NO_DATA, LOADING_DATA} from '../../components/empty';
export default {
  props: {
    activeName: String,
  },
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
        ],
        title: this.$t('profilingCluster.performanceChartTitle'),
      }, // Chart object of performance window
      normalState: 'normal', // Normal page state
    };
  },
  mounted() {
    this.performanceChart.dom = this.$refs.performance ? this.$refs.performance : null;
    this.queryPerformanceInfo().then((state) => {
      if (state) this.initChart(this.performanceChart);
    });
    window.addEventListener('resize', this.resizeCallBack);
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
      }, 100); // 100: Delay of debounce of callback
    },
    /**
     * The logic of click details
     * @param {string} path
     * @param {boolean} effective
     */
    jump(path, effective) {
      if (!effective) return;
      this.$router.push({
        path: `profiling-${path}`,
        query: Object.assign({
          activeName: this.activeName,
        }, this.trainInfo),
      });
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
              if (res?.data?.step_trace.length > 0) {
                const chartData = [];
                res.data.step_trace.forEach((item) => {
                  const chartItem = [item.rank_id].concat(item.step_trace_info);
                  chartData.push(chartItem);
                });
                this.performanceChart.data = chartData;
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
     * The logic of init echart
     * @param {Object} chart
     */
    initChart(chart) {
      if (!chart.dom) return;
      if (!chart.instance) {
        chart.instance = echarts.init(chart.dom);
      }
      chart.instance.setOption({
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow',
          },
          backgroundColor: 'rgba(50, 50, 50, 0.7)',
          borderWidth: 0,
          textStyle: {
            color: '#fff',
          },
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
          dimensions: chart.dimensions,
          source: chart.data,
        },
        xAxis: {
          name: this.$t('profilingCluster.rankID'),
          nameTextStyle: {
            align: 'left',
            padding: [0, 5],
            color: '#9EA4B3',
          },
          type: 'category',
          axisLine: {
            lineStyle: {
              color: '#E6EBF5',
              width: 2,
            },
          },
          axisLabel: {
            color: '#9EA4B3',
          },
        },
        yAxis: {
          name: this.$t('profilingCluster.timeTitle'),
          nameGap: 20,
          nameTextStyle: {
            align: 'right',
            padding: [0, 5],
            color: '#9EA4B3',
          },
          axisLine: {
            lineStyle: {
              color: '#E6EBF5',
              width: 2,
            },
          },
          axisLabel: {
            color: '#9EA4B3',
          },
          splitLine: {
            lineStyle: {
              color: ['#E6EBF5'],
              width: 1,
              type: 'dashed',
            },
          },
        },
        series: new Array(chart.dimensions.length - 1).fill(
            {type: 'bar', barWidth: 8},
        ),
      });
    },
  },
  beforeDestroy() {
    if (this.resizeTimer) {
      clearTimeout(this.resizeTimer);
    }
    window.removeEventListener('resize', this.resizeCallBack);
  },
};
</script>

<style scoped>
.performance-dashboard {
  display: grid;
  grid-template-rows: 100%;
  grid-template-columns: 100%;
  height: 100%;
  row-gap: 20px;
}
.performance-dashboard .container {
  width: 100%;
  height: 100%;
  border: 1px solid #d9d9d9;
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
  font-size: 18px;
  font-weight: 700;
}
.performance-dashboard .header .jump {
  cursor: pointer;
  color: #b8b8b8;
  font-size: 12px;
}
.performance-dashboard .header .is-effective {
  color: #00a5a7;
}
</style>

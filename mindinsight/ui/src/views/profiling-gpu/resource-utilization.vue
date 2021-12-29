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
  <div class="cl-resource-content">
    <div class="dashboard-item">
      <div class="title-item">
        <div class="title-text">
          {{$t('profiling.structuralCpuUtil')}}
        </div>
        <div class="detail-link"
             :class="{disabled:!cpuInfo.initOver || cpuInfo.noData}">
          <button :disabled="!cpuInfo.initOver || cpuInfo.noData"
                  @click="jumpToCpuDetail">
            {{$t('profiling.viewDetail')}}
            <i class="el-icon-d-arrow-right"></i>
          </button>
        </div>
      </div>
      <div class="content-item">
        <div class="cpu-info"
             v-show="!cpuInfo.noData">
          <div class="cpu-chart"
               id="deviceCpuChart"
               ref="deviceCpuChart"></div>
          <div class="cpu-chart-info">
            <div class="info-line">
              <span>{{$t('profiling.logicCores')}}</span><span>{{deviceCpuChart.logicCores}}</span>
            </div>
            <div class="info-line">
              <span>{{$t('profiling.avgUserUtilization')}}</span>
              <span>{{addPercentSign(deviceCpuChart.cpuAvgUser)}}</span>
            </div>
            <div class="info-line">
              <span>{{$t('profiling.avgSysUtilization')}}</span>
              <span>{{addPercentSign(deviceCpuChart.cpuAvgSystem)}}</span>
            </div>
            <div class="info-line">
              <span>{{$t('profiling.avgIOUtilization')}}</span>
              <span>{{addPercentSign(deviceCpuChart.cpuAvgIO)}}</span>
            </div>
            <div class="info-line">
              <span>{{$t('profiling.avgIdleUtilization')}}</span>
              <span>{{addPercentSign(deviceCpuChart.cpuAvgFree)}}</span>
            </div>
            <div class="info-line">
              <span>{{$t('profiling.avgWaitingProcess')}}</span><span>{{deviceCpuChart.cpuAvgProcess}}</span>
            </div>
            <div class="info-line">
              <span>{{$t('profiling.avgSwitchCount')}}</span><span>{{deviceCpuChart.cpuAvgSwitch}}</span>
            </div>
          </div>
        </div>
        <div class="noData-content"
             v-show="cpuInfo.noData">
          <img :src="require('@/assets/images/nodata.png')"
               alt="" />
          <p>{{cpuInfo.initOver?$t("public.noData"):$t("public.dataLoading")}}</p>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import RequestService from '../../services/request-service';
import echarts, { echartsThemeName } from '../../js/echarts';
import CommonProperty from '../../common/common-property';
export default {
  data() {
    return {
      // ------------------------common--------------------
      queryData: {
        dir: '',
        id: '',
        path: '',
        activePane: '',
      },
      summaryPath: '',
      curCardNum: '',
      pageResizeTimer: null, // Timer for changing the window size
      firstInit: true, // First init of page
      // ------------------------cpu-----------------------
      deviceCpuChart: {
        id: 'deviceCpuChart',
        chartDom: null,
        option: {
          color: ['#c23531', '#2f4554', '#61a0a8', '#d48265'],
          tooltip: {
            trigger: 'axis',
            formatter: null,
            confine: true,
          },
          legend: {
            right: 70,
            top: 8,
            data: [],
            textStyle: {
              color: CommonProperty.commonChartTheme[this.$store.state.themeIndex].legendTextColor,
            },
          },
          xAxis: {
            name: '',
            data: [],
          },
          yAxis: {
            name: this.$t('profiling.utilizationTitle'),
            type: 'value',
          },
          dataZoom: [
            {
              start: 0,
              end: 100,
              bottom: 0,
            },
            {
              start: 0,
              end: 100,
              type: 'inside',
              bottom: 0,
            },
          ],
          grid: {
            left: 60,
            top: 40,
            right: 70,
            bottom: 60,
          },
          series: [],
        },
        logicCores: 0,
        cpuAvgUser: 0,
        cpuAvgSystem: 0,
        cpuAvgIO: 0,
        cpuAvgFree: 0,
        cpuAvgProcess: 0,
        cpuAvgSwitch: 0,
      }, // The total data of device cpu info
      cpuInfo: {
        initOver: false,
        noData: true,
        stepArray: [],
        cpuInfoStr: {
          user_utilization: this.$t('profiling.userUtilization'),
          sys_utilization: this.$t('profiling.sysUtilization'),
          io_utilization: this.$t('profiling.ioUtilization'),
          idle_utilization: this.$t('profiling.idleUtilization'),
        },
        samplingInterval: 0,
      },
    };
  },
  watch: {
    // Listening card number
    '$parent.curDashboardInfo.curCardNum': {
      handler(newValue) {
        if (isNaN(newValue) || newValue === this.curCardNum || this.firstInit) {
          return;
        }
        this.curCardNum = newValue;
        this.noGraphicsDataFlag = false;
        this.graphicsInitOver = false;
        this.init();
      },
      deep: true,
      immediate: true,
    },
  },
  mounted() {
    window.addEventListener('resize', this.resizeCallback, false);
    this.$bus.$on('collapse', this.resizeCallback);
    this.queryData = {
      dir: this.$route.query.dir,
      id: this.$route.query.id,
      path: this.$route.query.path,
      activePane: this.$route.query.activePane,
    };
    if (this.$route.query && this.$route.query.path && !isNaN(this.$route.query.cardNum)) {
      this.summaryPath = this.$route.query.path;
      this.curCardNum = this.$route.query.cardNum;
      this.init();
    }
    this.firstInit = false;
  },
  methods: {
    // ------------------common---------------------
    init() {
      this.queryCpuInfo();
    },
    /**
     * Window resize
     */
    resizeCallback() {
      if (this.pageResizeTimer) {
        clearTimeout(this.pageResizeTimer);
        this.pageResizeTimer = null;
      }
      this.pageResizeTimer = setTimeout(() => {
        if (this.deviceCpuChart.chartDom) {
          this.deviceCpuChart.chartDom.resize();
        }
      }, 300);
    },
    // ----------------cpu-----------------------------------
    /**
     * The logic of add percent sign
     * @param {number | string} number
     * @return {string}
     */
    addPercentSign(number) {
      if (number === 0 || number === '0') {
        return '0';
      } else {
        return `${number}%`;
      }
    },
    /**
     * Query cpu info
     */
    queryCpuInfo() {
      const params = {
        params: {
          profile: this.queryData.dir,
          train_id: this.queryData.id,
        },
        body: {
          device_id: this.curCardNum,
          filter_condition: {},
        },
      };
      this.cpuInfo.noData = true;
      this.cpuInfo.initOver = false;
      RequestService.getCpuUtilization(params).then(
        (res) => {
          this.cpuInfo.initOver = true;
          if (res && res.data) {
            this.cpuInfo.noData = !res.data.step_total_num;
            this.cpuInfo.stepArray = res.data.step_info;
            this.samplingInterval = res.data.sampling_interval;
            this.deviceCpuChart.logicCores = res.data.cpu_processor_num;
            const deviceInfo = res.data.device_info;
            if (deviceInfo && this.samplingInterval) {
              this.initDeviceCpu(deviceInfo);
            } else {
              this.clearCpuChart();
              this.cpuInfo.noData = true;
            }
          } else {
            this.clearCpuChart();
          }
        },
        () => {
          this.clearCpuChart();
          this.cpuInfo.initOver = true;
        }
      );
    },
    /**
     * clear cpu chart
     */
    clearCpuChart() {
      if (this.deviceCpuChart.chartDom) {
        this.deviceCpuChart.chartDom.clear();
      }
    },
    /**
     * format chart tip
     * @param {Object} params
     * @param {Array} stepArray
     * @return {String}
     */
    formatCpuChartTip(params, stepArray) {
      const data = params;
      let str = '';
      if (data && data.length) {
        const colorArray = ['#c23531', '#2f4554', '#61a0a8', '#d48265'];
        const index = data[0].dataIndex;
        str += `step: ${stepArray[index]}`;
        data.forEach((item, index) => {
          str +=
            `<br><span class="cpu-chart-tip" style="background-color:${colorArray[index]};"></span>` +
            `${item.seriesName}: ${item.data}`;
        });
        str += `</div>`;
      }
      return str;
    },
    /**
     * Init device cpu chart
     * @param {Object} deviceInfo
     */
    initDeviceCpu(deviceInfo) {
      const series = [];
      const legend = [];
      Object.keys(this.cpuInfo.cpuInfoStr).forEach((val) => {
        const info = deviceInfo[val];
        if (info && info.metrics) {
          const item = {
            type: 'line',
            name: this.cpuInfo.cpuInfoStr[val],
            data: info.metrics,
            showSymbol: false,
          };
          series.push(item);
          legend.push(item.name);
        }
      });
      this.deviceCpuChart.cpuAvgUser = deviceInfo.user_utilization.avg_value;
      this.deviceCpuChart.cpuAvgSystem = deviceInfo.sys_utilization.avg_value;
      this.deviceCpuChart.cpuAvgIO = deviceInfo.io_utilization.avg_value;
      this.deviceCpuChart.cpuAvgFree = deviceInfo.idle_utilization.avg_value;
      this.deviceCpuChart.cpuAvgProcess = deviceInfo.runable_processes.avg_value;
      this.deviceCpuChart.cpuAvgSwitch = deviceInfo.context_switch_count.avg_value;
      this.deviceCpuChart.option.series = series;
      this.deviceCpuChart.option.xAxis.name = `${this.$t('profiling.sampleInterval')}\n${this.samplingInterval}ms`;
      this.deviceCpuChart.option.xAxis.data = deviceInfo[Object.keys(deviceInfo)[0]].metrics.map(
        (val, index) => index + 1
      );
      this.deviceCpuChart.option.legend.data = legend;
      this.deviceCpuChart.option.tooltip.formatter = (params) => {
        return this.formatCpuChartTip(params, this.cpuInfo.stepArray);
      };
      this.$nextTick(() => {
        if (!this.deviceCpuChart.chartDom) {
          if (this.$refs.deviceCpuChart) {
            this.deviceCpuChart.chartDom = echarts.init(this.$refs.deviceCpuChart, echartsThemeName);
          }
        }
        this.deviceCpuChart.chartDom.setOption(this.deviceCpuChart.option);
      });
    },
    /**
     * Router to memory-detail
     */
    jumpToCpuDetail() {
      this.$router.push({
        path: '/profiling-gpu/cpu-detail',
        query: {
          dir: this.queryData.dir,
          id: this.queryData.id,
          cardNum: this.curCardNum,
          path: this.queryData.path,
          activePane: this.queryData.activePane,
        },
      });
    },
  },
  destroyed() {
    // Remove the listener of window size change
    window.removeEventListener('resize', this.resizeCallback);
    // Remove timer
    if (this.pageResizeTimer) {
      clearTimeout(this.pageResizeTimer);
      this.pageResizeTimer = null;
    }
    // Remove bus
    this.$bus.$off('collapse');
  },
};
</script>
<style scoped>
.cl-resource-content {
  height: 100%;
}
.cl-resource-content .dashboard-item {
  width: 100%;
  height: 100%;
  padding: 15px;
  border: solid 1px var(--border-color);
  border-radius: 4px;
}
.cl-resource-content .dashboard-item .title-item {
  display: flex;
  height: 24px;
}
.cl-resource-content .dashboard-item .title-item .title-text {
  flex: 1;
  font-size: 18px;
  font-weight: bold;
  line-height: 24px;
}
.cl-resource-content .dashboard-item .title-item .detail-link {
  cursor: pointer;
  font-size: 12px;
  height: 18px;
  line-height: 12px;
  padding-top: 2px;
}
.cl-resource-content .dashboard-item .title-item .detail-link a {
  color: #00a5a7;
  padding-right: 6px;
}
.cl-resource-content .dashboard-item .title-item .detail-link button {
  color: #00a5a7;
  border: none;
  background-color: var(--bg-color);
  cursor: pointer;
}
.cl-resource-content .dashboard-item .title-item .detail-link.disabled button {
  color: #c0c4cc;
  cursor: not-allowed;
}
.cl-resource-content .dashboard-item .content-item {
  height: calc(100% - 38px);
  margin-top: 20px;
}
.cl-resource-content .dashboard-item .content-item .dashboard-chart-content {
  width: 100%;
  height: 100%;
}
.cl-resource-content .margin-item {
  margin-top: 20px;
}
.cl-resource-content .noData-content {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}
.cl-resource-content .noData-content p,
.cl-resource-content .noData-content .noData-text {
  font-size: 16px;
}
.content-item .cpu-info {
  display: grid;
  grid-template-columns: 1fr 300px;
  height: 100%;
}
.content-item .cpu-info .cpu-chart {
  height: 100%;
  width: 100%;
}
.content-item .cpu-info .cpu-chart-info {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding-left: 20px;
  background-color: var(--module-bg-color);
}
.content-item .cpu-chart-info .info-title {
  font-size: 14px;
  font-weight: bold;
  line-height: 30px;
}
.content-item .cpu-chart-info .info-line {
  line-height: 30px;
}
.cpu-chart-tip {
  display: inline-block;
  margin-right: 5px;
  border-radius: 10px;
  width: 10px;
  height: 10px;
}
</style>

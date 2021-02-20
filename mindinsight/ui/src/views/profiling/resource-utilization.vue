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
        <div class="cpu-info" v-if="!cpuInfo.noData">
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
        <div class="noData-content" v-else>
          <img :src="require('@/assets/images/nodata.png')" alt="" />
          <p>{{cpuInfo.initOver?$t("public.noData"):$t("public.dataLoading")}}</p>
        </div>
      </div>
    </div>
    <div class="dashboard-item margin-item">
      <div class="title-item">
        <div class="title-text">
          {{$t('profiling.memory.usedMemory')}}
        </div>
        <div class="detail-link"
             :class="{disabled:!graphicsInitOver || noGraphicsDataFlag}">
          <button :disabled="!graphicsInitOver || noGraphicsDataFlag"
             @click="jumpToMemoryDetail">
            {{$t('profiling.viewDetail')}}
            <i class="el-icon-d-arrow-right"></i>
          </button>
        </div>
      </div>
      <div class="content-item">
        <div class="noData-content"
             v-show="!graphicsInitOver || noGraphicsDataFlag">
          <div>
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
          </div>
          <div v-if="graphicsInitOver && noGraphicsDataFlag"
               class="noData-text">{{$t("public.noData")}}</div>
          <div v-else
               class="noData-text">{{$t("public.dataLoading")}}</div>
        </div>
        <div class="dashboard-chart-content"
             v-show="!noGraphicsDataFlag && graphicsInitOver"
             ref="dashboardMemoryChart"></div>
      </div>
    </div>
  </div>
</template>
<script>
import RequestService from '../../services/request-service';
import echarts from 'echarts';
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
      // ------------------------memory--------------------
      graphicsInitOver: false, // Graphics loading completed
      noGraphicsDataFlag: false, // No graphics data
      totalMemory: '-', // Total memory
      memoryGraphicsChart: null, // Memory chart object
      // ------------------------cpu-----------------------
      deviceCpuChart: {
        id: 'deviceCpuChart',
        chartDom: null,
        option: {
          tooltip: {
            trigger: 'axis',
            formatter: null,
            confine: true,
          },
          legend: {
            right: 70,
            top: 8,
            data: [],
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
            left: 40,
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
    if (
      this.$route.query &&
      this.$route.query.path &&
      !isNaN(this.$route.query.cardNum)
    ) {
      this.summaryPath = this.$route.query.path;
      this.curCardNum = this.$route.query.cardNum;
      this.init();
    }
    this.firstInit = false;
  },
  methods: {
    // ------------------common---------------------
    init() {
      this.getMemorySummary();
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
        if (this.memoryGraphicsChart) {
          this.memoryGraphicsChart.resize();
        }
        if (this.deviceCpuChart.chartDom) {
          this.deviceCpuChart.chartDom.resize();
        }
      }, 300);
    },
    // ----------------memory-----------------------------------
    /**
     * Router to memory-detail
     */
    jumpToMemoryDetail() {
      this.$router.push({
        path: '/profiling/memory-detail',
        query: {
          dir: this.queryData.dir,
          id: this.queryData.id,
          cardNum: this.curCardNum,
          path: this.queryData.path,
          activePane: this.queryData.activePane,
        },
      });
    },
    /**
     * Obtains base memory information
     */
    getMemorySummary() {
      if (!this.summaryPath || isNaN(this.curCardNum)) {
        this.noGraphicsDataFlag = true;
        this.graphicsInitOver = true;
        return;
      }
      const params = {
        dir: this.summaryPath,
        device_id: this.curCardNum,
      };
      RequestService.queryMemorySummary(params)
          .then(
              (res) => {
                if (res && res.data && res.data.summary) {
                  const resData = res.data.summary;
                  this.totalMemory = isNaN(resData.capacity)
                ? '-'
                : resData.capacity;
                } else {
                  this.totalMemory = '-';
                }
              },
              () => {
                this.overViewInitOver = true;
              },
          )
          .then(() => {
            this.getMemoryGraphics();
          });
    },
    /**
     * Obtains memory details
     */
    getMemoryGraphics() {
      const params = {
        dir: this.summaryPath,
        device_id: this.curCardNum,
      };
      RequestService.queryMemoryGraphics(params).then(
          (res) => {
            this.graphicsInitOver = true;
            if (!res || !res.data || !Object.keys(res.data).length) {
              this.noGraphicsDataFlag = true;
              return;
            }
            this.noGraphicsDataFlag = false;
            const resData = res.data[Object.keys(res.data)[0]];
            this.currentGraphicsDic = resData;
            this.graphicsOption = this.formatGraphicsOption();
            this.drawGraphics();
          },
          () => {
            this.graphicsInitOver = true;
            this.noGraphicsDataFlag = true;
          },
      );
    },
    /**
     * Sorting chart data
     * @return {Object} Chart data
     */
    formatGraphicsOption() {
      if (!this.currentGraphicsDic) {
        return {};
      }
      const that = this;
      const allocationData = [];
      const topData = [];
      const staticData = [];
      const lifeCycle = [];
      let startIndex = -1;
      let endIndex = -1;
      this.currentGraphicsDic.nodes.forEach((node, index) => {
        if (node.node_id === this.currentGraphicsDic.fp_start) {
          startIndex = index;
        } else if (node.node_id === this.currentGraphicsDic.bp_end) {
          endIndex = index;
        }
        allocationData.push([
          node.node_id,
          this.currentGraphicsDic.lines[index],
        ]);
        topData.push([node.node_id, this.totalMemory]);
        staticData.push([node.node_id, this.currentGraphicsDic.static_mem]);
        const curLifeCycle = [];
        node.outputs.forEach((output) => {
          curLifeCycle.push([output.life_start, output.life_end]);
        });
        lifeCycle.push(curLifeCycle);
      });
      const allocationLine = {
        id: this.graphicsId,
        name: this.$t('profiling.memory.curMemorySize'),
        data: allocationData,
        type: 'line',
        showSymbol: false,
        lineStyle: {
          color: '#00a5a7',
        },
        color: '#00a5a7',
        markLine: {
          lineStyle: {
            color: '#00a5a7',
          },
          label: {
            formatter(param) {
              let labelStr = '';
              if (param.dataIndex) {
                labelStr = `${that.$t('profiling.memory.bpEnd')}${that.$t(
                    'symbols.colon',
                )}${endIndex}`;
              } else {
                labelStr = `${that.$t('profiling.memory.fpStart')}${that.$t(
                    'symbols.colon',
                )}${startIndex}`;
              }
              return labelStr;
            },
          },
          symbol: ['none', 'none'],
          data: [{xAxis: startIndex}, {xAxis: endIndex}],
        },
        markPoint: {
          symbol: 'emptyCircle',
          symbolSize: 8,
          itemStyle: {
            color: '#f45c5e',
          },
          data: [
            {
              coord: allocationData[this.curSelectedPointIndex],
            },
          ],
        },
      };
      const topLine = {
        data: topData,
        name: this.$t('profiling.memory.totalMemory'),
        type: 'line',
        smooth: 0,
        symbol: 'none',
        lineStyle: {
          color: '#fdca5a',
        },
        color: '#fdca5a',
      };
      const staticLine = {
        data: staticData,
        name: this.$t('profiling.memory.staticMenory'),
        type: 'line',
        smooth: 0,
        symbol: 'none',
        lineStyle: {
          color: '#3d58a6',
        },
        color: '#3d58a6',
      };
      const seriesData = [allocationLine, staticLine];
      const selectedDic = {};
      selectedDic[this.$t('profiling.memory.curMemorySize')] = true;
      selectedDic[this.$t('profiling.memory.staticMenory')] = true;
      const legendData = [
        this.$t('profiling.memory.curMemorySize'),
        this.$t('profiling.memory.staticMenory'),
      ];
      if (!isNaN(this.totalMemory)) {
        seriesData.push(topLine);
        legendData.unshift(this.$t('profiling.memory.totalMemory'));
        selectedDic[this.$t('profiling.memory.totalMemory')] = false;
      }

      const optionData = {
        legend: {
          show: true,
          icon: 'circle',
          data: legendData,
          selected: selectedDic,
        },
        grid: {
          top: 60,
          bottom: 60,
        },
        xAxis: {
          name: this.$t('profiling.memory.chartXaxisUnit'),
          type: 'value',
          show: true,
        },
        yAxis: {
          name: this.$t('profiling.memory.chartYaxisUnit'),
          scale: true,
          nameGap: 24,
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'line',
          },
          formatter(params) {
            let tipStr = '';
            params.forEach((param) => {
              if (param.seriesId === that.graphicsId) {
                const dataIndex = param.dataIndex;
                const curData = that.currentGraphicsDic.nodes[dataIndex];
                if (curData) {
                  tipStr =
                    `<div>${that.$t('profiling.memory.curOperaterId')}` +
                    `${that.$t('symbols.colon')}${curData.node_id}</div>` +
                    `<div>${that.$t('profiling.memory.curOperator')}` +
                    `${that.$t('symbols.colon')}${curData.name}</div>` +
                    `<div>${that.$t(
                        'profiling.memory.curOperatorMemorySize',
                    )}` +
                    `${that.$t('symbols.colon')}${that.formmateNummber(
                        curData.size,
                    )}</div>` +
                    `<div>${that.$t('profiling.memory.curMemorySize')}` +
                    `${that.$t('symbols.colon')}${that.formmateNummber(
                        that.currentGraphicsDic.lines[dataIndex],
                    )}</div>` +
                    `<div>${that.$t('profiling.memory.memoryChanged')}` +
                    `${that.$t('symbols.colon')}${that.formmateNummber(
                        curData.allocated,
                    )}</div>`;
                }
              }
            });
            return tipStr;
          },
        },
        dataZoom: [
          {
            type: 'inside',
            filterMode: 'empty',
            orient: 'horizontal',
            xAxisIndex: 0,
          },
          {
            type: 'slider',
            filterMode: 'empty',
            orient: 'horizontal',
            xAxisIndex: 0,
            bottom: 10,
          },
        ],
        series: seriesData,
      };
      return optionData;
    },
    /**
     * Charting
     */
    drawGraphics() {
      if (!this.graphicsOption) {
        return;
      }
      this.$nextTick(() => {
        if (!this.memoryGraphicsChart) {
          this.memoryGraphicsChart = echarts.init(
              this.$refs.dashboardMemoryChart,
              null,
          );
        }
        this.memoryGraphicsChart.setOption(this.graphicsOption);
        this.memoryGraphicsChart.resize();
      });
    },
    /**
     * Convert Numeric display format
     * @param {Number} number
     * @return {String} Formatted number
     */
    formmateNummber(number) {
      const digitMax = 10;
      const digitMin = 1;
      if (!isNaN(number) && number.toString().length > this.numberLimit) {
        if (number > digitMin && number < digitMax) {
          return number.toFixed(4);
        } else {
          return number.toExponential(4);
        }
      } else {
        return number;
      }
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
    queryCpuInfo( ) {
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
          },
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
        const colorArray = [
          '#c23531',
          '#2f4554',
          '#61a0a8',
          '#d48265',
        ];
        const index = data[0].dataIndex;
        str += `step: ${stepArray[index]}`;
        data.forEach((item, index) => {
          str += `<br><span class="cpu-chart-tip" style="background-color:${colorArray[index]};"></span>` +
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
      this.deviceCpuChart.option.xAxis.name = `${this.$t('profiling.sampleInterval')}\n${
        this.$t('symbols.leftbracket')}${this.samplingInterval}ms${this.$t('symbols.rightbracket')}`;
      this.deviceCpuChart.option.xAxis.data = deviceInfo[Object.keys(deviceInfo)[0]].metrics.map(
          (val, index) => index + 1,
      );
      this.deviceCpuChart.option.legend.data = legend;
      this.deviceCpuChart.option.tooltip.formatter = (params) => {
        return this.formatCpuChartTip(params, this.cpuInfo.stepArray);
      };
      this.$nextTick(() => {
        if (!this.deviceCpuChart.chartDom) {
          if (this.$refs.deviceCpuChart) {
            this.deviceCpuChart.chartDom = echarts.init(this.$refs.deviceCpuChart);
          }
        }
        this.deviceCpuChart.chartDom.setOption(this.deviceCpuChart.option);
      });
    },
    /**
     * Router to memory-detail
     */
    jumpToCpuDetail() {
      if (this.$route.path !== '/profiling/cpu-detail') {
        this.$router.push({
          path: '/profiling/cpu-detail',
          query: {
            dir: this.queryData.dir,
            id: this.queryData.id,
            cardNum: this.curCardNum,
            path: this.queryData.path,
            activePane: this.queryData.activePane,
          },
        });
      }
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
<style>
.cl-resource-content {
  height: 100%;
}
.cl-resource-content .dashboard-item {
  width: 100%;
  height: calc(50% - 10px);
  padding: 15px;
  border: solid 1px #d9d9d9;
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
  background-color: #fff;
  cursor: pointer;
}
.cl-resource-content .dashboard-item .title-item .detail-link.disabled button {
  color: #c0c4cc;
  cursor: not-allowed;
}
.cl-resource-content .dashboard-item .content-item {
  height: calc(100% - 44px);
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
  width: 100%
}
.content-item .cpu-info .cpu-chart-info {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding-left: 20px;
  background-color: #f1f1f1;
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

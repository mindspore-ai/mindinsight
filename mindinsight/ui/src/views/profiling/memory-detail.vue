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
  <div class="cl-memory-detail">
    <div class="memory-bk">
      <div class="title-content">
        <div class="title-text">
          {{$t("profiling.memory.memoryDetailLink")}}
        </div>
      </div>
      <div class="main-content">
        <div class="top-content"
             :class="tableFullScreen?'full-screen':''">
          <div class="title-item">
            {{$t('profiling.memory.overView')}}
          </div>
          <div class="content-item">
            <div class="detail-item">
              <div class="value-item">{{overViewData.currentCard}}</div>
              <div class="label-item">{{$t('profiling.memory.currentCard')}}</div>
            </div>
            <div class="detail-item">
              <div class="value-item">{{overViewData.memoryAssign}}</div>
              <div class="label-item">{{$t('profiling.memory.memoryAssign')}}</div>
            </div>
            <div class="detail-item">
              <div class="value-item">{{overViewData.memoryRelease}}</div>
              <div class="label-item">{{$t('profiling.memory.memoryRelease')}}</div>
            </div>
            <div class="detail-item">
              <div>
                <span class="value-item">
                  {{formatUnit(overViewData.totalMemory, 1)}}
                </span>
                <span class="unit-item">
                  {{formatUnit(overViewData.totalMemory, 2)}}
                </span>
              </div>
              <div class="label-item">{{$t('profiling.memory.totalMemory')}}</div>
            </div>
            <div class="detail-item">
              <div>
                <span class="value-item">
                  {{formatUnit(overViewData.staticMemory, 1)}}
                </span>
                <span class="unit-item">
                  {{formatUnit(overViewData.staticMemory, 2)}}
                </span>
              </div>
              <div class="label-item">{{$t('profiling.memory.staticMenory')}}</div>
            </div>
            <div class="detail-item">
              <div>
                <span class="value-item">
                  {{formatUnit(overViewData.memoryPeak, 1)}}
                </span>
                <span class="unit-item">
                  {{formatUnit(overViewData.memoryPeak, 2)}}
                </span>
              </div>
              <div class="label-item">{{$t('profiling.memory.memoryPeak')}}</div>
            </div>
          </div>
        </div>
        <div class="chart-container"
             :class="tableFullScreen?'full-screen':''">
          <div class="title-item">
            {{$t('profiling.memory.usedMemory')}}
          </div>
          <div class="chart-content"
               v-show="!graphicsInitOver || noGraphicsDataFlag">
            <div class="noData-content">
              <div>
                <img :src="require('@/assets/images/nodata.png')" />
              </div>
              <div v-if="graphicsInitOver && noGraphicsDataFlag"
                   class="noData-text">{{$t("public.noData")}}</div>
              <div v-else
                   class="noData-text">{{$t("public.dataLoading")}}</div>
            </div>
          </div>
          <div class="chart-content"
               v-show="!noGraphicsDataFlag && graphicsInitOver"
               ref="memoryChart"></div>
        </div>
        <div class="table-container"
             :class="tableFullScreen?'full-screen':''">
          <div class="title-item">
            <span>
              {{$t('profiling.memory.operatorMemoryAssign')}}
            </span>
            <img src="../../assets/images/full-screen.png"
                 :title="$t('graph.fullScreen')"
                 class="fullScreen-icon"
                 @click="toggleFullScreen">
          </div>
          <div class="table-content">
            <el-table :data="currentBreakdownsData"
                      stripe
                      height="100%"
                      tooltip-effect="light"
                      :empty-text="breakdownsInitOver ? $t('public.noData') : $t('public.dataLoading')">
              <el-table-column prop="name"
                               sortable>
                <template slot="header">
                  <span :title="$t('profiling.memory.tensorName')">
                    {{$t('profiling.memory.tensorName')}}
                  </span>
                </template>
                <template slot-scope="scope">
                  <div class="cell">{{scope.row.name}}</div>
                </template>
              </el-table-column>
              <el-table-column prop="size"
                               sortable>
                <template slot="header">
                  <span :title="$t('profiling.memory.totalTensorMemoryAssign')">
                    {{$t('profiling.memory.totalTensorMemoryAssign')}}
                  </span>
                </template>
                <template slot-scope="scope">
                  <div class="cell">{{formatUnit(scope.row.size)}}</div>
                </template>
              </el-table-column>
              <el-table-column prop="type">
                <template slot="header">
                  <span :title="$t('profiling.memory.tensorType')">
                    {{$t('profiling.memory.tensorType')}}
                  </span>
                </template>
                <template slot-scope="scope">
                  <div class="cell">{{scope.row.type}}</div>
                </template>
              </el-table-column>
              <el-table-column prop="dataType">
                <template slot="header">
                  <span :title="$t('profiling.memory.dataType')">
                    {{$t('profiling.memory.dataType')}}
                  </span>
                </template>
                <template slot-scope="scope">
                  <div class="cell">{{scope.row.dataType}}</div>
                </template>
              </el-table-column>
              <el-table-column prop="shape">
                <template slot="header">
                  <span :title="$t('profiling.memory.shapes')">
                    {{$t('profiling.memory.shapes')}}
                  </span>
                </template>
                <template slot-scope="scope">
                  <div class="cell">{{scope.row.shape}}</div>
                </template>
              </el-table-column>
              <el-table-column prop="format">
                <template slot="header">
                  <span :title="$t('profiling.memory.format')">
                    {{$t('profiling.memory.format')}}
                  </span>
                </template>
                <template slot-scope="scope">
                  <div class="cell">{{scope.row.format}}</div>
                </template>
              </el-table-column>
              <el-table-column prop="lifeCycle">
                <template slot="header">
                  <span :title="$t('profiling.memory.lifeCycle')">
                    {{$t('profiling.memory.lifeCycle')}}
                  </span>
                </template>
                <template slot-scope="scope">
                  <div class="cell">{{scope.row.lifeCycle}}</div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import echarts, {echartsThemeName} from '../../js/echarts';
import RequestService from '../../services/request-service';
import CommonProperty from '../../common/common-property';
export default {
  data() {
    return {
      summaryPath: '', // Current summary path
      curCardNum: null, // Current card number
      // Data related to the date overview
      overViewData: {
        currentCard: '-',
        memoryAssign: '-',
        memoryRelease: '-',
        staticMemory: '-',
        totalMemory: '-',
        memoryPeak: '-',
      },
      overViewInitOver: false, // Overview loading completed
      graphicsInitOver: false, // Graphics loading completed
      noGraphicsDataFlag: false, // No graphics data
      pageResizeTimer: null, // Timer for changing the window size
      currentGraphicsDic: [], // Dictionary of current graphics data
      currentBreakdownsData: [], // current breakdowns data
      graphicsChart: null, // Chart object
      graphicsOption: null,
      graphicsId: 'allocationLine', // ID of the memory data in the chart
      numberLimit: 10, // Maximum length of a number displayed
      unitBase: 1024, // Memory size unit
      unitList: [
        this.$t('profiling.memory.memoryGiBUnit'),
        this.$t('profiling.memory.memoryMiBUnit'),
        this.$t('profiling.memory.memoryKiBUnit'),
        this.$t('profiling.memory.memoryByteUnit'),
      ],
      chartClickListenerOn: false, // Listening on discount click events
      curSelectedPointIndex: 0, // Subscript of the current selection point
      curGraphId: '', // ID of the current graphics
      breakdownsInitOver: false, // BreakDown data request complete
      themeIndex: this.$store.state.themeIndex, // Index of theme color
      firstInit: true, // First init of page
      tableFullScreen: false, // Table show full screen
    };
  },
  watch: {
    // Listening card number
    '$parent.curDashboardInfo.curCardNum': {
      handler(newValue) {
        if (isNaN(parseInt(newValue)) || newValue === this.curCardNum || this.firstInit) {
          return;
        }
        this.curCardNum = newValue;
        this.overViewInitOver = false;
        this.noGraphicsDataFlag = false;
        this.graphicsInitOver = false;
        this.breakdownsInitOver = false;
        this.overViewData = {
          currentCard: '-',
          memoryAssign: '-',
          memoryRelease: '-',
          staticMemory: '-',
          totalMemory: '-',
          memoryPeak: '-',
        };
        this.curGraphId = '';
        this.curSelectedPointIndex = 0;
        this.currentBreakdownsData = [];
        this.init();
      },
      deep: true,
      immediate: true,
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
    // Remove listener
    if (this.chartClickListenerOn && this.graphicsChart) {
      this.chartClickListenerOn = false;
      this.graphicsChart.off('click');
    }
  },
  methods: {
    init() {
      this.getMemorySummary();
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
        if (this.graphicsChart) {
          this.graphicsChart.resize();
        }
      }, 300);
    },
    /**
     * Obtains base memory information
     */
    getMemorySummary() {
      if (!this.summaryPath || isNaN(this.curCardNum)) {
        this.overViewInitOver = true;
        this.noGraphicsDataFlag = true;
        this.graphicsInitOver = true;
        this.breakdownsInitOver = true;
        return;
      }
      const params = {
        dir: this.summaryPath,
        device_id: this.curCardNum,
      };
      RequestService.queryMemorySummary(params)
          .then(
              (res) => {
                this.overViewInitOver = true;
                if (res && res.data && res.data.summary) {
                  const resData = res.data.summary;
                  this.overViewData = {
                    currentCard: params.device_id,
                    memoryAssign: resData.allocations || '-',
                    memoryRelease: resData.deallocations || '-',
                    staticMemory: isNaN(resData.static_mem) ? '-' : resData.static_mem,
                    totalMemory: isNaN(resData.capacity) ? '-' : resData.capacity,
                    memoryPeak: isNaN(resData.peak_mem) ? '-' : resData.peak_mem,
                  };
                } else {
                  this.overViewData = {
                    currentCard: '-',
                    memoryAssign: '-',
                    memoryRelease: '-',
                    staticMemory: '-',
                    totalMemory: '-',
                    memoryPeak: '-',
                  };
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
              this.breakdownsInitOver = true;
              return;
            }
            this.noGraphicsDataFlag = false;
            const resData = res.data[Object.keys(res.data)[0]];
            this.curGraphId = resData.graph_id;
            this.currentGraphicsDic = resData;
            this.graphicsOption = this.formatGraphicsOption();
            this.drawGraphics();
            this.$nextTick(() => {
              this.formatBreakdowns();
            });
          },
          () => {
            this.graphicsInitOver = true;
            this.noGraphicsDataFlag = true;
            this.breakdownsInitOver = true;
          },
      );
    },
    /**
     * Sort out the memory allocation data in a table
     */
    formatBreakdowns() {
      this.breakdownsInitOver = false;
      this.currentBreakdownsData = [];
      if (!this.currentGraphicsDic.nodes) {
        this.currentBreakdownsData = [];
        this.breakdownsInitOver = true;
        return;
      }
      const tempNodeData = this.currentGraphicsDic.nodes[this.curSelectedPointIndex];
      if (!tempNodeData) {
        this.currentBreakdownsData = [];
        this.breakdownsInitOver = true;
        return;
      }
      const params = {
        dir: this.summaryPath,
        device_id: this.curCardNum,
        graph_id: this.curGraphId,
        node_id: tempNodeData.node_id,
      };
      const tempSelectedPointIndex = this.curSelectedPointIndex;
      RequestService.queryMemoryBreakdowns(params).then(
          (res) => {
            if (tempSelectedPointIndex !== this.curSelectedPointIndex) {
              return;
            }
            this.breakdownsInitOver = true;
            if (!res || !res.data || !res.data.breakdowns) {
              this.currentBreakdownsData = [];
              return;
            }
            const tempBreakdowns = res.data.breakdowns;
            const breakdownData = [];
            tempBreakdowns.forEach((breakdown) => {
              breakdownData.push({
                name: breakdown.tensor_name,
                size: breakdown.size,
                type: breakdown.type,
                dataType: breakdown.data_type,
                shape: breakdown.shape,
                format: breakdown.format,
                lifeCycle: `[${breakdown.life_start}, ${breakdown.life_end}]`,
              });
            });
            this.currentBreakdownsData = breakdownData;
          },
          () => {
            this.breakdownsInitOver = true;
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
      const themeColorObj = CommonProperty.commonThemes[this.themeIndex];
      this.currentGraphicsDic.nodes.forEach((node, index) => {
        if (node.node_id === this.currentGraphicsDic.fp_start) {
          startIndex = index;
        } else if (node.node_id === this.currentGraphicsDic.bp_end) {
          endIndex = index;
        }
        allocationData.push([node.node_id, this.currentGraphicsDic.lines[index]]);
        topData.push([node.node_id, this.overViewData.totalMemory]);
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
                labelStr = `${that.$t('profiling.memory.bpEnd')}${that.$t('symbols.colon')}${endIndex}`;
              } else {
                labelStr = `${that.$t('profiling.memory.fpStart')}${that.$t('symbols.colon')}${startIndex}`;
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
      const legendData = [this.$t('profiling.memory.curMemorySize'), this.$t('profiling.memory.staticMenory')];
      if (!isNaN(this.overViewData.totalMemory)) {
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
          inactiveColor: themeColorObj.inactiveFontColor,
          textStyle: {
            color: themeColorObj.fontColor,
          },
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
                    `<div>${that.$t('profiling.memory.curOperatorMemorySize')}` +
                    `${that.$t('symbols.colon')}${that.formatNumber(curData.size)}</div>` +
                    `<div>${that.$t('profiling.memory.curMemorySize')}` +
                    `${that.$t('symbols.colon')}${that.formatNumber(
                        that.currentGraphicsDic.lines[dataIndex],
                    )}</div>` +
                    `<div>${that.$t('profiling.memory.memoryChanged')}` +
                    `${that.$t('symbols.colon')}${that.formatNumber(curData.allocated)}</div>`;
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
        if (!this.graphicsChart) {
          this.graphicsChart = echarts.init(this.$refs.memoryChart, echartsThemeName);
        }
        this.graphicsChart.setOption(this.graphicsOption);
        if (!this.chartClickListenerOn) {
          this.chartClickListenerOn = true;
          this.graphicsChart.on('click', {seriesName: this.$t('profiling.memory.curMemorySize')}, (param) => {
            this.pointChanged(param);
          });
        }
        this.graphicsChart.resize();
      });
    },
    /**
     * Point change
     * @param {Object} param Point object
     *
     */
    pointChanged(param) {
      if (!param) {
        return;
      }
      let dataIndex = 0;
      if (param.componentType === 'markLine') {
        dataIndex = param.value;
      } else if (param.componentType === 'series') {
        dataIndex = param.dataIndex;
      } else {
        return;
      }
      const seriesData = this.graphicsOption.series[0];
      if (seriesData) {
        seriesData.markPoint.data[0].coord = seriesData.data[dataIndex];
        this.drawGraphics();
        this.curSelectedPointIndex = dataIndex;
        this.formatBreakdowns();
      }
    },
    /**
     * Convert Numeric display format
     * @param {Number} number
     * @return {String} Formatted number
     */
    formatNumber(number) {
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
    /**
     * Convert Numeric unit display format
     * @param {Number} number
     * @param {Number} type default: number and unit; 1: number only; 2: unit only
     * @return {String} Formatted string
     */
    formatUnit(number, type) {
      const baseStr = '-';
      if (number === baseStr) {
        return baseStr;
      }
      const loopCount = this.unitList.length - 1;
      const fixedLimit = 2;
      let baseNumber = number;
      let utilIndex = loopCount;
      let resultStr = '';
      for (let i = 0; i < loopCount; i++) {
        if (baseNumber >= 1) {
          utilIndex = i;
          break;
        } else {
          baseNumber = baseNumber * this.unitBase;
        }
      }
      if (type === 1) {
        resultStr = `${Number(baseNumber.toFixed(fixedLimit))}`;
      } else if (type === 2) {
        resultStr = `${this.unitList[utilIndex]}`;
      } else {
        resultStr = `${Number(baseNumber.toFixed(fixedLimit))} ${this.unitList[utilIndex]}`;
      }
      return resultStr;
    },
    /**
     * Toggle full screen of table
     */
    toggleFullScreen() {
      this.tableFullScreen = !this.tableFullScreen;
      if (!this.tableFullScreen) {
        this.$nextTick(() => {
          this.resizeCallback();
        });
      }
    },
  },
  mounted() {
    if (this.train_id) {
      document.title = `${decodeURIComponent(this.train_id)}-${this.$t(
          'profiling.memory.memoryDetailLink',
      )}-MindInsight`;
    } else {
      document.title = `${this.$t('profiling.memory.memoryDetailLink')}-MindInsight`;
    }
    window.addEventListener('resize', this.resizeCallback, false);
    this.$bus.$on('collapse', this.resizeCallback);
    if (this.$route.query && this.$route.query.path && !isNaN(this.$route.query.cardNum)) {
      this.summaryPath = this.$route.query.path;
      this.curCardNum = this.$route.query.cardNum;
      this.init();
    }
    this.firstInit = false;
  },
};
</script>
<style>
.cl-memory-detail {
  width: 100%;
  height: 100%;
  padding-left: 24px;
  display: flex;
}
.cl-memory-detail .top-content.full-screen {
  display: none;
}
.cl-memory-detail .chart-container.full-screen {
  display: none;
}
.cl-memory-detail .table-container.full-screen {
  margin-top: 0;
  height: 100%;
}
.cl-memory-detail .memory-bk {
  width: 100%;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.cl-memory-detail .title-content {
  height: 44px;
  padding-bottom: 20px;
  color: var(--font-color);
  font-weight: bold;
  font-size: 20px;
}

.cl-memory-detail .title-content .title-text {
  font-size: 18px;
}

.cl-memory-detail .top-content .content-item {
  display: flex;
  height: calc(100% - 21px);
  width: 100%;
}

.cl-memory-detail .main-content {
  height: calc(100% - 44px);
  overflow-y: auto;
}

.cl-memory-detail .noData-content {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}
.cl-memory-detail .top-content {
  width: 100%;
  height: 137px;
  padding: 24px;
  border: solid 1px #d9d9d9;
  border-radius: 4px;
  background: var(--item-bg-color);
}
.cl-memory-detail .top-content .detail-item {
  width: 16.6%;
  display: flex;
  flex-direction: column;
  padding: 24px 5px 0 5px;
  text-align: center;
}
.cl-memory-detail .top-content .label-item,
.cl-memory-detail .top-content .unit-item {
  font-size: 12px;
  line-height: 12px;
  color: var(--icon-info-color);
}
.cl-memory-detail .top-content .value-item {
  font-size: 24px;
  font-weight: bold;
}

.cl-memory-detail .chart-container,
.cl-memory-detail .table-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  border: solid 1px #ccc;
  border-radius: 4px;
  padding: 20px 24px;
  background: var(--item-bg-color);
}
.cl-memory-detail .chart-container {
  background: var(--bg-color);
}
.cl-memory-detail .table-container .fullScreen-icon {
  float: right;
  margin-top: 2px;
  cursor: pointer;
}
.cl-memory-detail .chart-container .chart-content,
.cl-memory-detail .table-container .table-content {
  margin-top: 16px;
  height: calc(100% - 37px);
}
.cl-memory-detail .chart-container {
  height: calc(60% - 106px);
  margin-top: 20px;
  min-height: 280px;
}
.cl-memory-detail .table-container {
  margin-top: 20px;
  height: calc(40% - 71px);
  min-height: 160px;
}
.cl-memory-detail .title-item {
  font-size: 16px;
  font-weight: bold;
}
.cl-memory-detail .el-table td,
.cl-memory-detail .el-table th {
  border: solid 1px #ebeef5;
}
</style>

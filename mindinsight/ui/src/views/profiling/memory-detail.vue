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
      <div class="left-content">
        <div class="title-item">
          {{$t('profiling.memory.overView')}}
        </div>
        <div class="content-item">
          <div class="detail-row">
            <span class="label-item">{{$t('profiling.memory.currentCard')}}</span>
            <span class="value-item">{{overViewData.currentCard}}</span>
          </div>
          <div class="detail-row">
            <span class="label-item">{{$t('profiling.memory.memoryAssign')}}</span>
            <span class="value-item">{{overViewData.memoryAssign}}</span>
          </div>
          <div class="detail-row">
            <span class="label-item">{{$t('profiling.memory.memoryRelease')}}</span>
            <span class="value-item">{{overViewData.memoryRelease}}</span>
          </div>
          <div class="detail-row">
            <span class="label-item">{{$t('profiling.memory.totalMemory')}}</span>
            <span class="value-item">
              {{formmateUnit(overViewData.totalMemory)}}
            </span>
          </div>
          <div class="detail-row">
            <span class="label-item">{{$t('profiling.memory.staticMenory')}}</span>
            <span class="value-item">
              {{formmateUnit(overViewData.staticMemory)}}
            </span>
          </div>
          <div class="detail-row">
            <span class="label-item">{{$t('profiling.memory.memoryPeak')}}</span>
            <span class="value-item">
              {{formmateUnit(overViewData.memoryPeak)}}
            </span>
          </div>
        </div>
      </div>
      <div class="right-content">
        <div class="chart-container">
          <div class="title-item">
            {{$t('profiling.memory.usedMemory')}}
          </div>
          <div class="chart-content"
               v-show="!graphicsInitOver">
            <div class="noData-content">
              <div>
                <img :src="require('@/assets/images/nodata.png')"
                     alt="" />
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
        <div class="table-container">
          <div class="title-item">
            {{$t('profiling.memory.operatorMemoryAssign')}}
          </div>
          <div class="table-content">
            <el-table :data="currentBreakdownsData"
                      stripe
                      height="100%"
                      :span-method="columnSpanMethod"
                      tooltip-effect="light"
                      :empty-text="overViewInitOver ? $t('public.noData') : $t('public.dataLoading')">
              <el-table-column prop="name"
                               :label="$t('profiling.memory.operatorName')">
                <template slot="header">
                  <span :title="$t('profiling.memory.operatorName')">
                    {{$t('profiling.memory.operatorName')}}
                  </span>
                </template>
                <template slot-scope="scope">
                  <div class="cell">{{scope.row.name}}</div>
                </template>
              </el-table-column>
              <el-table-column prop="allocations"
                               :label="$t('profiling.memory.assignNum')">
                <template slot="header">
                  <span :title="$t('profiling.memory.assignNum')">
                    {{$t('profiling.memory.assignNum')}}
                  </span>
                </template>
                <template slot-scope="scope">
                  <div class="cell">{{scope.row.allocations}}</div>
                </template>
              </el-table-column>
              <el-table-column prop="size"
                               :label="$t('profiling.memory.totalMemoryAssign')">
                <template slot="header">
                  <span :title="$t('profiling.memory.totalMemoryAssign')">
                    {{$t('profiling.memory.totalMemoryAssign')}}
                  </span>
                </template>
                <template slot-scope="scope">
                  <div class="cell">{{formmateUnit(scope.row.size)}}</div>
                </template>
              </el-table-column>
              <el-table-column prop="type"
                               :label="$t('profiling.memory.memoryType')">
                <template slot="header">
                  <span :title="$t('profiling.memory.memoryType')">
                    {{$t('profiling.memory.memoryType')}}
                  </span>
                </template>
                <template slot-scope="scope">
                  <div class="cell">{{scope.row.type}}</div>
                </template>
              </el-table-column>
              <el-table-column prop="dataType"
                               :label="$t('profiling.memory.dataType')">
                <template slot="header">
                  <span :title="$t('profiling.memory.dataType')">
                    {{$t('profiling.memory.dataType')}}
                  </span>
                </template>
                <template slot-scope="scope">
                  <div class="cell">{{scope.row.dataType}}</div>
                </template>
              </el-table-column>
              <el-table-column prop="shape"
                               :label="$t('profiling.memory.shapes')">
                <template slot="header">
                  <span :title="$t('profiling.memory.shapes')">
                    {{$t('profiling.memory.shapes')}}
                  </span>
                </template>
                <template slot-scope="scope">
                  <div class="cell">{{scope.row.shape}}</div>
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
import echarts from 'echarts';
import RequestService from '../../services/request-service';
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
      // Dictionary of breakdowns data
      breakdownMarks: {
        markIndex: {},
        markLength: [],
      },
      graphicsChart: null, // Chart object
      graphicsId: 'allocationLine', // ID of the memory data in the chart
      numberLimit: 10, // Maximum length of a number displayed
      unitBase: 1024, // Memory size unit
      unitList: [
        this.$t('profiling.memory.memoryGiBUnit'),
        this.$t('profiling.memory.memoryMiBUnit'),
        this.$t('profiling.memory.memoryKiBUnit'),
      ],
    };
  },
  watch: {
    // Listening card number
    '$parent.curDashboardInfo.curCardNum': {
      handler(newValue, oldValue) {
        if (isNaN(newValue) || newValue === this.curCardNum) {
          return;
        }
        this.curCardNum = newValue;
        this.overViewInitOver = false;
        this.noGraphicsDataFlag = false;
        this.graphicsInitOver = false;
        this.overViewData = {
          currentCard: '-',
          memoryAssign: '-',
          memoryRelease: '-',
          staticMemory: '-',
          totalMemory: '-',
          memoryPeak: '-',
        };
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
  },
  methods: {
    init() {
      this.getMemorySummary(this.getMemoryGraphics);
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
     * @param {Function} successCallback callback upon success
     */
    getMemorySummary(successCallback) {
      if (!this.summaryPath || isNaN(this.curCardNum)) {
        return;
      }
      const params = {
        dir: this.summaryPath,
        device_id: this.curCardNum,
      };
      RequestService.queryMemorySummary(params).then(
          (res) => {
            this.overViewInitOver = true;
            if (res && res.data && res.data.summary) {
              const resData = res.data.summary;
              this.overViewData = {
                currentCard: params.device_id,
                memoryAssign: resData.allocations || '-',
                memoryRelease: resData.deallocations || '-',
                staticMemory: isNaN(resData.static_mem)
                ? '-'
                : resData.static_mem,
                totalMemory: isNaN(resData.capacity) ? '-' : resData.capacity,
                memoryPeak: isNaN(resData.peak_mem) ? '-' : resData.peak_mem,
              };
              this.$nextTick(() => {
                this.formateBreakdowns(resData.breakdowns);
              });
              if (successCallback) {
                successCallback();
              }
            } else {
              this.graphicsInitOver = true;
              this.noGraphicsDataFlag = true;
              this.overViewData = {
                currentCard: '-',
                memoryAssign: '-',
                memoryRelease: '-',
                staticMemory: '-',
                totalMemory: '-',
                memoryPeak: '-',
              };
              this.currentBreakdownsData = [];
            }
          },
          () => {
            this.overViewInitOver = true;
            this.graphicsInitOver = true;
            this.noGraphicsDataFlag = true;
          },
      );
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
            const resData = res.data[Object.keys(res.data)[0]];
            this.currentGraphicsDic = resData;
            this.drawGraphics(this.formateGraphicsOption());
          },
          () => {
            this.graphicsInitOver = true;
            this.noGraphicsDataFlag = true;
          },
      );
    },
    /**
     * Sort out the memory allocation data in a table
     * @param {Object} breakdowns breakdowns data
     */
    formateBreakdowns(breakdowns) {
      const markIndex = {};
      const markLength = [];
      const breakdownData = [];
      let startIndex = 0;
      if (breakdowns) {
        breakdowns.forEach((nodeData, dataIndex) => {
          let count = 0;
          //  Processing output data
          if (nodeData.outputs) {
            count += nodeData.outputs.length;
            nodeData.outputs.forEach((output) => {
              breakdownData.push({
                name: nodeData.name,
                allocations: nodeData.allocations,
                type: output.type,
                size: output.size,
                shape: output.shape,
                dataType: output.data_type,
              });
            });
          }
          // Processing workspace data
          if (nodeData.workspaces) {
            count += nodeData.workspaces.length;
            nodeData.workspaces.forEach((workspace) => {
              breakdownData.push({
                name: nodeData.name,
                allocations: nodeData.allocations,
                type: workspace.type,
                size: workspace.size,
                shape: workspace.shape,
                dataType: workspace.data_type,
              });
            });
          }
          if (!count) {
            count++;
            breakdownData.push({
              name: nodeData.name,
              allocations: nodeData.allocations,
              type: '-',
              size: '-',
              shape: '-',
              dataType: '-',
            });
          }
          markIndex[startIndex] = dataIndex;
          markLength.push(count);
          startIndex += count;
        });
      }
      this.currentBreakdownsData = breakdownData;
      this.breakdownMarks = {
        markIndex: markIndex,
        markLength: markLength,
      };
    },
    /**
     * merge Cells
     * @param {Object} data Data in the current cell
     * @return {Object} Cells to be merged
     */
    columnSpanMethod(data) {
      if (data.columnIndex <= 1) {
        const index = this.breakdownMarks.markIndex[data.rowIndex];
        if (isNaN(index)) {
          return {
            rowspan: 0,
            colspan: 0,
          };
        } else {
          return {
            rowspan: this.breakdownMarks.markLength[index],
            colspan: 1,
          };
        }
      }
    },
    /**
     * Sorting chart data
     * @return {Object} Chart data
     */
    formateGraphicsOption() {
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
      const seriesData = [topLine, allocationLine, staticLine];
      const selectedDic = {};
      selectedDic[this.$t('profiling.memory.curMemorySize')] = true;
      selectedDic[this.$t('profiling.memory.totalMemory')] = false;
      selectedDic[this.$t('profiling.memory.staticMenory')] = true;

      const optionData = {
        legend: {
          show: true,
          icon: 'circle',
          data: [
            this.$t('profiling.memory.curMemorySize'),
            this.$t('profiling.memory.totalMemory'),
            this.$t('profiling.memory.staticMenory'),
          ],
          selected: selectedDic,
        },
        grid: {
          top: 80,
        },
        xAxis: {
          name: this.$t('profiling.memory.chartXaxisUnit'),
          type: 'value',
          show: true,
        },
        yAxis: {
          name: this.$t('profiling.memory.chartYaxisUnit'),
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
                    `<div>${that.$t('profiling.memory.curMemorySize')}` +
                    `${that.$t('symbols.colon')}${that.formmateNummber(
                        curData.size,
                    )}</div>` +
                    `<div>${that.$t('profiling.memory.memoryChanged')}` +
                    `${that.$t('symbols.colon')}${that.formmateNummber(
                        curData.allocated,
                    )}</div>` +
                    `<div>${that.$t('profiling.memory.lifeCycle')}` +
                    `${that.$t('symbols.colon')}${JSON.stringify(
                        lifeCycle[dataIndex],
                    )}</div>`;
                }
              }
            });
            return tipStr;
          },
        },
        series: seriesData,
      };
      return optionData;
    },
    /**
     * Charting
     * @param {Object} optionData Chart data
     */
    drawGraphics(optionData) {
      if (!optionData) {
        return;
      }
      this.$nextTick(() => {
        if (!this.graphicsChart) {
          this.graphicsChart = echarts.init(this.$refs.memoryChart, null);
        }
        this.graphicsChart.setOption(optionData, false);
        this.graphicsChart.resize();
      });
    },
    /**
     * Convert Numeric display format
     * @param {Number} number
     * @return {String} Formatted number
     */
    formmateNummber(number) {
      if (!isNaN(number) && number.toString().length > this.numberLimit) {
        return number.toExponential(6);
      } else {
        return number;
      }
    },
    /**
     * Convert Numeric unit display format
     * @param {Number} number
     * @return {String} Formatted string
     */
    formmateUnit(number) {
      const baseStr = '-';
      if (number === baseStr) {
        return baseStr;
      }
      const loopCount = this.unitList.length;
      let baseNumber = number;
      let resultStr = '';
      for (let i = 0; i < loopCount; i++) {
        if (baseNumber >= 1) {
          resultStr = `${baseNumber} ${this.unitList[i]}`;
          break;
        } else {
          baseNumber = baseNumber * this.unitBase;
        }
      }
      if (!resultStr) {
        resultStr = `${baseNumber} ${this.unitList[loopCount - 1]}`;
      }
      return resultStr;
    },
  },
  mounted() {
    if (this.train_id) {
      document.title = `${decodeURIComponent(this.train_id)}-${this.$t(
          'profiling.memory.memoryDetailLink',
      )}-MindInsight`;
    } else {
      document.title = `${this.$t(
          'profiling.memory.memoryDetailLink',
      )}-MindInsight`;
    }
    window.addEventListener('resize', this.resizeCallback, false);
    if (
      this.$route.query &&
      this.$route.query.path &&
      !isNaN(this.$route.query.cardNum)
    ) {
      this.summaryPath = this.$route.query.path;
      this.curCardNum = this.$route.query.cardNum;
      this.init();
    }
    this.$bus.$on('collapse', this.resizeCallback);
  },
};
</script>
<style>
.cl-memory-detail {
  width: 100%;
  height: 100%;
  padding: 0 24px 0 16px;
  display: flex;
}
.cl-memory-detail .memory-bk {
  width: 100%;
  height: 100%;
  overflow: hidden;
  display: flex;
}
.cl-memory-detail .noData-content {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}
.cl-memory-detail .left-content {
  width: 30%;
  max-width: 350px;
  min-width: 335px;
  height: 100%;
  padding: 0 10px;
  border: solid 1px #ccc;
  border-radius: 4px;
}
.cl-memory-detail .left-content .detail-row {
  width: 100%;
  margin-bottom: 10px;
  display: flex;
}
.cl-memory-detail .left-content .label-item {
  width: 50%;
  padding-left: 20px;
}
.cl-memory-detail .left-content .value-item {
  width: 50%;
}
.cl-memory-detail .right-content {
  flex: 1;
  height: 100%;
  padding-left: 10px;
  overflow: hidden;
}
.cl-memory-detail .right-content .chart-container,
.cl-memory-detail .right-content .table-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  border: solid 1px #ccc;
  border-radius: 4px;
}
.cl-memory-detail .right-content .chart-container .chart-content,
.cl-memory-detail .right-content .table-container .table-content {
  flex: 1;
}
.cl-memory-detail .right-content .chart-container {
  height: calc(60% - 20px);
}
.cl-memory-detail .right-content .table-container {
  margin-top: 20px;
  height: 40%;
}
.cl-memory-detail .title-item {
  font-size: 20px;
  font-weight: bold;
  margin-right: 15px;
  margin: 15px 0 20px 0;
  padding-left: 20px;
}
.cl-memory-detail .el-table td,
.cl-memory-detail .el-table th {
  border: solid 1px #ebeef5;
}
</style>

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
<script>
import echarts from 'echarts';
import {select, selectAll} from 'd3';
const d3 = {select, selectAll};
import 'd3-graphviz';
import RequestService from '@/services/request-service';
import initDot from '../mixins/init-dot';
export default {
  data() {
    return {
      chartGrid: {
        grid: {
          left: 40,
          top: 40,
          right: 70,
          bottom: 60,
        },
      }, // The grid setting of chart
      chartDataZoom: {
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
      }, // The data zoom setting of chart
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
      processCpuChart: {
        id: 'processCpuChart',
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
          series: [],
        },
        cpuAvgUser: 0,
        cpuAvgSystem: 0,
      }, // The total data of process cpu info
      operatorCpuChart: {
        id: 'operatorCpuChart',
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
          series: [],
        },
        opList: {},
        cpuAvgTotalUser: 0,
        cpuAvgTotalSystem: 0,
        cpuAvgOpUser: 0,
        cpuAvgOpSystem: 0,
        processNumber: 0,
      }, // The total data of operator cpu info
      cpuInfo: {
        initOver: false,
        noData: true,
        startStep: {
          step: '',
          showStep: '',
        },
        endStep: {
          step: '',
          showStep: '',
        },
        stepArray: [],
        step: 0,
        deviceId: null,
        stepTip: this.$t('profiling.cpuStepTip'),
        cpuStepInputTip: '',
        cpuInfoStr: {
          user_utilization: this.$t('profiling.userUtilization'),
          sys_utilization: this.$t('profiling.sysUtilization'),
          io_utilization: this.$t('profiling.ioUtilization'),
          idle_utilization: this.$t('profiling.idleUtilization'),
        },
        samplingInterval: 0,
      }, // The common data of page
      strokeBeforeClick: undefined, // The stroke info of original dom
      prevNode: undefined, // The previous clicked node
      prevGraph: undefined, // The previous clicked graph
      operatorCPUList: [], // The list of operator cpu info
      selIndex: null, // The index of selected graph node, to get right operator cpu info
    };
  },
  created() {
    Object.assign(this.deviceCpuChart.option, this.chartGrid, this.chartDataZoom);
    Object.assign(this.processCpuChart.option, this.chartGrid, this.chartDataZoom);
    Object.assign(this.operatorCpuChart.option, this.chartGrid, this.chartDataZoom);
  },
  methods: {
    /**
     * The logic of query and render graph info of cpu
     * @return {Promise}
     */
    initCPUGraph() {
      return new Promise((resolve) => {
        const params = {
          params: {
            train_id: this.trainId,
            profile: this.dir,
          },
          body: {
            device_id: this.currentCard,
          },
        };
        RequestService.queryOpQueue(params)
            .then((res) => {
              if (res.data && res.data.object) {
              // Keep data order right
                const newData = this.ensureDataOrder(res.data.object);
                // Process data
                const graphData = this.processGraphData(newData);
                // Transform to dot
                const dot = initDot.objectToDot(graphData);
                // Render dot
                this.initOperatorGraph(dot).then(() => {
                  const nodes = d3.selectAll('g.node');
                  // Add click event
                  this.addGraphEvent(nodes);
                  // Add cursor style
                  this.updateGraphStyle(nodes);
                  resolve(true);
                });
              }
            });
      });
    },
    /**
     * The logic of make sure the index of data is same to id
     * @param {Array} dataArr
     * @return {Array}
     */
    ensureDataOrder(dataArr) {
      const newArr = [];
      dataArr.forEach((data) => {
        newArr[data[0]] = data;
        this.operatorCPUList[data[0]] = `${data[1]}_${data[0]}`;
      });
      this.selIndex = newArr.findIndex((data) => {
        return data.parent_id === null || newArr[data.parent_id] === undefined;
      });
      return newArr;
    },
    /**
     * The logic of process operator data into 'initDot' format
     * @param {Array} dataArr
     * @return {Object}
     */
    processGraphData(dataArr) {
      const graphData = {
        total: {
          compound: 'true',
          rankdir: 'LR',
          id: 'operatorGraph',
          bgcolor: 'transparent',
        },
        node: {
          style: 'filled',
          fontsize: '10px',
        },
        edge: {
          fontsize: '6px',
          style: 'filled',
          fillcolor: '#e6ebf5',
          color: '#e6ebf5',
        },
        nodes: [],
      };
      const nodeStyle = {
        shape: 'Mrecord',
        fillcolor: '#c6e2ff',
        color: '#c6e2ff',
      };
      if (Array.isArray(dataArr)) {
        dataArr.forEach((data) => {
          const text = `${data[1]}_${data[0]}`;
          const node = Object.assign({
            name: text,
            id: text,
            label: text,
          }, nodeStyle);
            // If has the parent node
          if (typeof data[6] === 'number') {
            const next = data[6];
            node.next = [
              {
                name: `${dataArr[next][1]}_${dataArr[next][0]}`,
              },
            ];
          }
          graphData.nodes.push(node);
        });
      }
      return graphData;
    },
    /**
     * Init operator graph
     * @param {String} dot
     * @return {Object}
     */
    initOperatorGraph(dot) {
      return new Promise((resolve) => {
        d3.select('#operator-graph')
            .graphviz()
            .height('100%')
            .width('100%')
            .fit(true)
            .dot(dot)
            .render(() => {
              resolve(true);
            });
      });
    },
    /**
     * Add operator graph Event
     * @param {Array} nodes
     */
    addGraphEvent(nodes) {
      if (nodes) {
        nodes.on(
            'click',
            (target, index, nodeslist) => {
              this.clickEvent(nodeslist[index]);
            },
            false,
        );
      }
    },
    /**
     * Update operator graph style
     * @param {Array} nodes
     */
    updateGraphStyle(nodes) {
      nodes.attr('cursor', 'pointer');
    },
    /**
     * The logic of operator graph click event
     * @param {Object} node
     */
    clickEvent(node) {
      if (this.prevGraph) {
        this.prevGraph.setAttribute('stroke', this.strokeBeforeClick);
      }
      if (this.prevNode === Node) {
        return;
      } else {
        this.prevNode = node;
      }
      const children = node.children;
      for (let i = 0; i < children.length; i++) {
        if (children[i].nodeName === 'path') {
          this.prevGraph = children[i];
          this.strokeBeforeClick = children[i].getAttribute('stroke');
          children[i].setAttribute('stroke', '#409eff');
        }
      }
      const strArr = node.id.split('_');
      this.selIndex = strArr[strArr.length - 1];
      this.updateOperatorCpuChart(this.selIndex);
    },

    /**
     * Query average rate info
     * @param {Boolean} isFilter wherter filter step
     * @param {Boolean} isInitGraph wherter init graph
     */
    queryCpuInfo(isFilter, isInitGraph) {
      this.cpuInfo.deviceId = this.currentCard;
      const params = {
        params: {
          profile: this.dir,
          train_id: this.trainId,
        },
        body: {
          device_id: this.currentCard,
          filter_condition: {},
        },
      };
      if (isFilter) {
        params.body.filter_condition.start_step = this.cpuInfo.startStep.step;
        params.body.filter_condition.end_step = this.cpuInfo.endStep.step;
      }
      this.cpuInfo.initOver = false;
      RequestService.getCpuUtilization(params).then(
          (res) => {
            this.cpuInfo.initOver = true;
            if (res && res.data) {
              this.cpuInfo.noData = !res.data.step_total_num;
              this.cpuInfo.step = res.data.step_total_num;
              this.cpuInfo.stepArray = res.data.step_info;
              this.cpuInfo.stepTip = this.$t('profiling.cpuStepTip', {max: `${this.cpuInfo.step}`});
              this.cpuInfo.cpuStepInputTip = this.$t('profiling.cpuStepInputTip', {max: `${this.cpuInfo.step}`});
              this.samplingInterval = res.data.sampling_interval;
              this.deviceCpuChart.logicCores = res.data.cpu_processor_num;
              const deviceInfo = res.data.device_info;
              const processInfo = res.data.process_info;
              const opInfo = res.data.op_info;
              if (deviceInfo && processInfo && opInfo && this.samplingInterval) {
                this.initDeviceCpu(deviceInfo);
                this.initProcessCpu(processInfo);
                if (isInitGraph) {
                  this.$nextTick(() => {
                    this.initCPUGraph().then(() => {
                      this.initOperatorCpu(opInfo, true);
                    });
                  });
                } else {
                  this.$nextTick(() => {
                    this.initOperatorCpu(opInfo, false);
                  });
                }
              } else {
                this.clearCpuChart();
              }
            } else {
              this.clearCpuChart();
              this.cpuInfo.noData = true;
            }
          },
          () => {
            this.clearCpuChart();
            this.cpuInfo.initOver = true;
            this.cpuInfo.noData = true;
          },
      );
    },
    /**
     * clear cpu chart and graph
     */
    clearCpuChart() {
      if (this.deviceCpuChart.chartDom) {
        this.deviceCpuChart.chartDom.clear();
      }
      if (this.processCpuChart.chartDom) {
        this.processCpuChart.chartDom.clear();
      }
      if (this.operatorCpuChart.chartDom) {
        this.operatorCpuChart.chartDom.clear();
      }
    },
    /**
     * filter step to view cpu info
     */
    viewStepFilter() {
      if (
        /^[0-9]*[1-9][0-9]*$/.test(this.cpuInfo.startStep.showStep) &&
        /^[0-9]*[1-9][0-9]*$/.test(this.cpuInfo.endStep.showStep) &&
        this.cpuInfo.startStep.showStep <= this.cpuInfo.endStep.showStep &&
        this.cpuInfo.endStep.showStep <= this.cpuInfo.step
      ) {
        this.cpuInfo.startStep.step = this.cpuInfo.startStep.showStep;
        this.cpuInfo.endStep.step = this.cpuInfo.endStep.showStep;
        this.queryCpuInfo(true, false);
      } else if (this.cpuInfo.endStep.showStep === '' &&
      /^[0-9]*[1-9][0-9]*$/.test(this.cpuInfo.startStep.showStep) &&
      this.cpuInfo.startStep.showStep <= this.cpuInfo.step) {
        this.cpuInfo.startStep.step = this.cpuInfo.startStep.showStep;
        this.cpuInfo.endStep.step = this.cpuInfo.step;
        this.cpuInfo.endStep.showStep = this.cpuInfo.step;
        this.queryCpuInfo(true, false);
      } else if (this.cpuInfo.startStep.showStep === '' &&
      /^[0-9]*[1-9][0-9]*$/.test(this.cpuInfo.endStep.showStep) &&
      this.cpuInfo.endStep.showStep <= this.cpuInfo.step) {
        this.cpuInfo.startStep.step = 1;
        this.cpuInfo.startStep.showStep = 1;
        this.cpuInfo.endStep.step = this.cpuInfo.endStep.showStep;
        this.queryCpuInfo(true, false);
      } else if (this.cpuInfo.startStep.showStep === '' &&
      this.cpuInfo.endStep.showStep === '') {
        this.resetStepFilter();
      } else {
        this.cpuInfo.startStep.showStep = this.cpuInfo.startStep.step;
        this.cpuInfo.endStep.showStep = this.cpuInfo.endStep.step;
        this.$message.error(this.cpuInfo.cpuStepInputTip);
      }
    },
    /**
     * reset to view all cpu info
     */
    resetStepFilter() {
      this.cpuInfo.startStep.showStep = '';
      this.cpuInfo.startStep.step = '';
      this.cpuInfo.endStep.showStep = '';
      this.cpuInfo.endStep.step = '';
      this.queryCpuInfo(false, false);
    },
    /**
     * format chart tip
     * @param {Object} params
     * @param {Array} stepArray
     * @return {String}
     */
    formateCpuChartTip(params, stepArray) {
      const data = params;
      let str = '';
      if (data && data.length) {
        const colorArray = [
          '#c23531',
          '#2f4554',
          '#61a0a8',
          '#d48265',
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
        return this.formateCpuChartTip(params, this.cpuInfo.stepArray);
      };
      this.$nextTick(() => {
        if (this.$refs.deviceCpuChart) {
          this.deviceCpuChart.chartDom = echarts.init(this.$refs.deviceCpuChart);
        }
        this.deviceCpuChart.chartDom.setOption(this.deviceCpuChart.option);
      });
    },
    /**
     * Init process cpu chart
     * @param {Object} processInfo
     */
    initProcessCpu(processInfo) {
      const series = [];
      const legend = [];
      Object.keys(this.cpuInfo.cpuInfoStr).forEach((val) => {
        const info = processInfo[val];
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
      this.processCpuChart.cpuAvgUser = processInfo.user_utilization.avg_value;
      this.processCpuChart.cpuAvgSystem = processInfo.sys_utilization.avg_value;
      this.processCpuChart.option.series = series;
      this.processCpuChart.option.xAxis.name = `${this.$t('profiling.sampleInterval')}\n${
        this.$t('symbols.leftbracket')}${this.samplingInterval}ms${this.$t('symbols.rightbracket')}`;
      this.processCpuChart.option.xAxis.data = processInfo[Object.keys(processInfo)[0]].metrics.map(
          (val, index) => index + 1,
      );
      this.processCpuChart.option.legend.data = legend;
      this.processCpuChart.option.tooltip.formatter = (params) => {
        return this.formateCpuChartTip(params, this.cpuInfo.stepArray);
      };
      this.$nextTick(() => {
        if (this.$refs.processCpuChart) {
          this.processCpuChart.chartDom = echarts.init(this.$refs.processCpuChart);
        }
        this.processCpuChart.chartDom.setOption(this.processCpuChart.option);
      });
    },

    /**
     * Init operator cpu chart
     * @param {Object} opInfo
     * @param {Boolean} isClickNode
     */
    initOperatorCpu(opInfo, isClickNode) {
      this.operatorCpuChart.opList = {};
      opInfo.op_list.forEach((data) => {
        this.operatorCpuChart.opList[data.op_id] = data;
      });
      if (isClickNode) {
        // Select first node as default node, and keep it in right style when page mounted
        const node = document.getElementById(this.operatorCPUList[this.selIndex]);
        if (node) {
          this.clickEvent(node);
        };
      }
      this.operatorCpuChart.cpuAvgTotalUser = opInfo.total_op_avg_value.user_utilization;
      this.operatorCpuChart.cpuAvgTotalSystem = opInfo.total_op_avg_value.sys_utilization;
      this.updateOperatorCpuChart(this.selIndex);
    },
    /**
     * update cpu chart
     * @param {String} opId
     */
    updateOperatorCpuChart(opId) {
      const series = [];
      const legend = [];
      if (this.operatorCpuChart.opList[opId]) {
        const currentOpInfo = this.operatorCpuChart.opList[opId].metrics;
        const numWorkers = this.operatorCpuChart.opList[opId].num_workers;
        if (currentOpInfo) {
          Object.keys(this.cpuInfo.cpuInfoStr).forEach((val) => {
            const info = currentOpInfo[val];
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
          this.operatorCpuChart.cpuAvgOpUser = currentOpInfo.user_utilization.avg_value;
          this.operatorCpuChart.cpuAvgOpSystem = currentOpInfo.sys_utilization.avg_value;
          this.operatorCpuChart.processNumber = numWorkers;
          this.operatorCpuChart.option.series = series;
          this.operatorCpuChart.option.xAxis.name = `${this.$t('profiling.sampleInterval')}\n${
            this.$t('symbols.leftbracket')}${this.samplingInterval}ms${this.$t('symbols.rightbracket')}`;
          this.operatorCpuChart.option.xAxis.data = currentOpInfo[Object.keys(currentOpInfo)[0]].metrics.map(
              (val, index) => index + 1,
          );
          this.operatorCpuChart.option.legend.data = legend;
          this.operatorCpuChart.option.tooltip.formatter = (params) => {
            return this.formateCpuChartTip(params, this.cpuInfo.stepArray);
          };
          this.$nextTick(() => {
            if (this.$refs.operatorCpuChart) {
              if (!this.operatorCpuChart.chartDom) {
                this.operatorCpuChart.chartDom = echarts.init(this.$refs.operatorCpuChart);
              }
            }
            this.operatorCpuChart.chartDom.setOption(this.operatorCpuChart.option);
          });
        }
      }
    },
  },
};
</script>

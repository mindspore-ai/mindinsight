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
  <div class="data-process-wrap">
    <div class="title">{{$t('profiling.cpuUtilization')}}</div>
    <div class="cpu-info"
         v-show="!cpuInfo.noData">
      <div class="step-filter">
        <label>{{cpuInfo.stepTip}}</label>
        <label>{{$t('profiling.startStep')}}</label>
        <el-input class="step-input"
                  v-model.number="cpuInfo.startStep.showStep"></el-input>
        <label>{{$t('profiling.endStep')}}</label>
        <el-input class="step-input"
                  v-model.number="cpuInfo.endStep.showStep"></el-input>
        <el-button @click="viewStepFilter">{{$t('profiling.filterStep')}}</el-button>
        <el-button @click="resetStepFilter">{{$t('profiling.resetStep')}}</el-button>
      </div>
      <div class="cpu-detail">
        <div class="cpu-detail-item">
          <div class="detail-item-title">{{$t('profiling.structuralCpuUtil')}}</div>
          <div class="detail-item">
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
        </div>
        <div class="cpu-detail-item cpu-detail-item-top">
          <div class="detail-item-title">{{$t('profiling.processCpuUtil')}}</div>
          <div class="detail-item">
            <div class="cpu-chart"
                 id="processCpuChart"
                 ref="processCpuChart">
            </div>
            <div class="cpu-chart-info">
              <div class="info-line">
                <span>{{$t('profiling.avgUserUtilization')}}</span>
                <span>{{addPercentSign(processCpuChart.cpuAvgUser)}}</span>
              </div>
              <div class="info-line">
                <span>{{$t('profiling.avgSysUtilization')}}</span>
                <span>{{addPercentSign(processCpuChart.cpuAvgSystem)}}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="cpu-detail-item cpu-detail-item-top">
          <div class="detail-item-title">{{$t('profiling.operatorCpuUtil')}}</div>
          <div class="detail-item-graph"
               id="operator-graph"></div>
          <div class="detail-item">
            <div class="cpu-chart"
                 id="operatorCpuChart"
                 ref="operatorCpuChart">
            </div>
            <div class="cpu-chart-info">
              <div class="info-title">
                {{$t('profiling.allOperators')}}
              </div>
              <div class="info-line">
                <span>{{$t('profiling.avgUserUtilization')}}</span>
                <span>{{addPercentSign(operatorCpuChart.cpuAvgTotalUser)}}</span>
              </div>
              <div class="info-line">
                <span>{{$t('profiling.avgSysUtilization')}}</span>
                <span>{{addPercentSign(operatorCpuChart.cpuAvgTotalSystem)}}</span>
              </div>
              <div class="info-title">
                {{$t('profiling.currentOperator')}}
              </div>
              <div class="info-line">
                <span>{{$t('profiling.avgUserUtilization')}}</span>
                <span>{{addPercentSign(operatorCpuChart.cpuAvgOpUser)}}</span>
              </div>
              <div class="info-line">
                <span>{{$t('profiling.avgSysUtilization')}}</span>
                <span>{{addPercentSign(operatorCpuChart.cpuAvgOpSystem)}}</span>
              </div>
              <div class="info-line">
                <span>{{$t('profiling.workersNum')}}{{$t('symbols.colon')}}</span>
                <span>{{operatorCpuChart.processNumber}}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="image-noData"
         v-show="cpuInfo.noData">
      <div>
        <img :src="require('@/assets/images/nodata.png')"
             alt="" />
      </div>
      <p>{{cpuInfo.initOver?$t("public.noData"):$t("public.dataLoading")}}</p>
    </div>
  </div>
</template>
<script>
import echarts, {echartsThemeName} from '../../js/echarts';
import RequestService from '../../services/request-service';
import initDot from '../../mixins/init-dot';
import {select, selectAll, zoom} from 'd3';
import 'd3-graphviz';
const d3 = {select, selectAll, zoom};
export default {
  props: {},
  data() {
    return {
      dir: '', // Profiler path
      currentCard: '', // Current card number
      trainId: '',
      chartOptions: {
        grid: {
          left: 60,
          top: 40,
          right: 70,
          bottom: 60,
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
        color: ['#c23531', '#2f4554', '#61a0a8', '#d48265'],
      }, // The options setting of chart
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
      resizeDebounce: null, // The function of resize callback
    };
  },
  watch: {
    '$parent.curDashboardInfo.curCardNum': {
      handler(newValue) {
        if (newValue || newValue === 0) {
          this.dir = this.$route.query.dir;
          this.trainId = this.$route.query.id;
          this.currentCard = newValue;
          if (this.trainId) {
            document.title =
              `${decodeURIComponent(this.trainId)}` + `-${this.$t('profiling.cpuUtilization')}-MindInsight`;
          } else {
            document.title = `${this.$t('profiling.cpuUtilization')}-MindInsight`;
          }
          this.cpuInfo.startStep.showStep = '';
          this.cpuInfo.startStep.step = '';
          this.cpuInfo.endStep.showStep = '';
          this.cpuInfo.endStep.step = '';
          this.queryCpuInfo(false, true);
        }
      },
      deep: true,
      immediate: true,
    },
  },
  computed: {},
  created() {
    Object.assign(this.deviceCpuChart.option, this.chartOptions);
    Object.assign(this.processCpuChart.option, this.chartOptions);
    Object.assign(this.operatorCpuChart.option, this.chartOptions);
  },
  mounted() {
    this.resizeDebounce = this.debounce(this.resizeCallback, 200);
    window.addEventListener('resize', this.resizeDebounce, false);
    setTimeout(() => {
      this.$bus.$on('collapse', this.debounce(this.resizeCallback, 200));
    }, 500);
  },
  methods: {
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
     * Anti-shake
     * @param { Function } fn callback function
     * @param { Number } delay delay time
     * @return { Function }
     */
    debounce(fn, delay) {
      let timer = null;
      return function() {
        if (timer) {
          clearTimeout(timer);
        }
        timer = setTimeout(fn, delay);
      };
    },
    init() {
      this.queryCpuInfo();
    },
    /**
     *  Resize callback function
     */
    resizeCallback() {
      const chartArr = ['deviceCpuChart', 'processCpuChart', 'operatorCpuChart'];
      chartArr.forEach((val) => {
        if (this[val].chartDom) {
          this[val].chartDom.resize();
        }
      });
    },

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
        RequestService.queryOpQueue(params).then((res) => {
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
          const node = Object.assign(
              {
                name: text,
                id: text,
                label: text,
              },
              nodeStyle,
          );
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
     * Query cpu info
     * @param {Boolean} isFilter whether filter step
     * @param {Boolean} isInitGraph whether init graph
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
              this.cpuInfo.stepTip = this.$t('profiling.cpuStepTip', {max: this.cpuInfo.step});
              this.cpuInfo.cpuStepInputTip = this.$t('profiling.cpuStepInputTip', {max: this.cpuInfo.step});
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
                this.cpuInfo.noData = true;
              }
            } else {
              this.clearCpuChart();
              this.cpuInfo.noData = true;
            }
          },
          () => {
            this.clearCpuChart();
            this.cpuInfo.noData = true;
            this.cpuInfo.initOver = true;
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
      const stepValidation = new RegExp('^[0-9]*[1-9][0-9]*$');
      if (
        stepValidation.test(this.cpuInfo.startStep.showStep) &&
        stepValidation.test(this.cpuInfo.endStep.showStep) &&
        this.cpuInfo.startStep.showStep <= this.cpuInfo.endStep.showStep &&
        this.cpuInfo.endStep.showStep <= this.cpuInfo.step
      ) {
        this.cpuInfo.startStep.step = this.cpuInfo.startStep.showStep;
        this.cpuInfo.endStep.step = this.cpuInfo.endStep.showStep;
        this.queryCpuInfo(true, false);
      } else if (
        this.cpuInfo.endStep.showStep === '' &&
        stepValidation.test(this.cpuInfo.startStep.showStep) &&
        this.cpuInfo.startStep.showStep <= this.cpuInfo.step
      ) {
        this.cpuInfo.startStep.step = this.cpuInfo.startStep.showStep;
        this.cpuInfo.endStep.step = this.cpuInfo.step;
        this.cpuInfo.endStep.showStep = this.cpuInfo.step;
        this.queryCpuInfo(true, false);
      } else if (
        this.cpuInfo.startStep.showStep === '' &&
        stepValidation.test(this.cpuInfo.endStep.showStep) &&
        this.cpuInfo.endStep.showStep <= this.cpuInfo.step
      ) {
        this.cpuInfo.startStep.step = 1;
        this.cpuInfo.startStep.showStep = 1;
        this.cpuInfo.endStep.step = this.cpuInfo.endStep.showStep;
        this.queryCpuInfo(true, false);
      } else if (this.cpuInfo.startStep.showStep === '' && this.cpuInfo.endStep.showStep === '') {
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
      this.deviceCpuChart.option.xAxis.name = `${this.$t('profiling.sampleInterval')}\n${this.$t(
          'symbols.leftbracket',
      )}${this.samplingInterval}ms${this.$t('symbols.rightbracket')}`;
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
            this.deviceCpuChart.chartDom = echarts.init(this.$refs.deviceCpuChart, echartsThemeName);
          }
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
      this.processCpuChart.option.xAxis.name = `${this.$t('profiling.sampleInterval')}\n${this.$t(
          'symbols.leftbracket',
      )}${this.samplingInterval}ms${this.$t('symbols.rightbracket')}`;
      this.processCpuChart.option.xAxis.data = processInfo[Object.keys(processInfo)[0]].metrics.map(
          (val, index) => index + 1,
      );
      this.processCpuChart.option.legend.data = legend;
      this.processCpuChart.option.tooltip.formatter = (params) => {
        return this.formatCpuChartTip(params, this.cpuInfo.stepArray);
      };
      this.$nextTick(() => {
        if (!this.processCpuChart.chartDom) {
          if (this.$refs.processCpuChart) {
            this.processCpuChart.chartDom = echarts.init(this.$refs.processCpuChart, echartsThemeName);
          }
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
        }
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
          this.operatorCpuChart.option.xAxis.name = `${this.$t('profiling.sampleInterval')}\n${this.$t(
              'symbols.leftbracket',
          )}${this.samplingInterval}ms${this.$t('symbols.rightbracket')}`;
          this.operatorCpuChart.option.xAxis.data = currentOpInfo[Object.keys(currentOpInfo)[0]].metrics.map(
              (val, index) => index + 1,
          );
          this.operatorCpuChart.option.legend.data = legend;
          this.operatorCpuChart.option.tooltip.formatter = (params) => {
            return this.formatCpuChartTip(params, this.cpuInfo.stepArray);
          };
          this.$nextTick(() => {
            if (!this.operatorCpuChart.chartDom) {
              if (this.$refs.operatorCpuChart) {
                this.operatorCpuChart.chartDom = echarts.init(this.$refs.operatorCpuChart, echartsThemeName);
              }
            }
            this.operatorCpuChart.chartDom.setOption(this.operatorCpuChart.option);
          });
        }
      }
    },
  },
  destroyed() {
    // Remove the listener of window size change
    window.removeEventListener('resize', this.resizeDebounce);
    this.$bus.$off('collapse');
  },
};
</script>
<style>
.data-process-wrap {
  height: 100%;
  padding: 0 16px;
}
.data-process-wrap .title {
  font-size: 18px;
  font-weight: bold;
  text-align: left;
}
.data-process-wrap .image-noData {
  width: 100%;
  height: calc(100% - 37px);
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}
.data-process-wrap .image-noData p {
  font-size: 16px;
  padding-top: 10px;
}
.data-process-wrap .el-button {
  border: 1px solid #00a5a7;
  border-radius: 2px;
  background-color: var(--bg-color);
  color: #00a5a7;
  padding: 7px 15px;
}
.data-process-wrap .el-button:hover {
  background: var(--button-hover-tip);
}
.cpu-info {
  height: calc(100% - 24px);
  display: flex;
  flex-direction: column;
}
.cpu-info .step-filter {
  min-height: 44px;
}
.cpu-info .step-filter .step-input {
  width: 100px;
  margin-right: 20px;
}
.cpu-info .step-filter:first-child label {
  margin-right: 10px;
}
.cpu-info .cpu-detail {
  height: calc(100% - 44px);
  flex-grow: 1;
  overflow-x: hidden;
  overflow-y: scroll;
}
.cpu-info .cpu-detail .cpu-detail-item {
  padding: 16px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  margin-right: 8px;
}
.cpu-info .cpu-detail .cpu-detail-item-top {
  margin-top: 16px;
}
.cpu-info .cpu-detail .detail-item-title {
  height: 20px;
  font-size: 15px;
  font-weight: bold;
}
.cpu-info .cpu-detail .detail-item-graph {
  height: 120px;
  background-color: var(--graph-bg-color);
  margin: 10px 0;
}
.cpu-info .cpu-detail .detail-item-graph svg path {
  fill: var(--data-process-operator-color);
  stroke: #e6ebf5;
}
.cpu-info .cpu-detail .detail-item-graph svg text {
  fill: var(--font-color);
}
.cpu-info .cpu-detail .detail-item-graph .is-active {
  stroke: red;
}
.cpu-info .cpu-detail .detail-item {
  height: 400px;
  display: flex;
}
.cpu-info .cpu-detail .detail-item:last-of-type {
  padding-bottom: 0;
  border-bottom: none;
}
.cpu-info .cpu-detail .detail-item .cpu-chart {
  height: 100%;
  flex-grow: 1;
}
.cpu-info .cpu-detail .detail-item .cpu-chart-info {
  height: 100%;
  width: 300px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding-left: 20px;
  background-color: var(--module-bg-color);
}
.cpu-info .cpu-detail .detail-item .cpu-chart-info .info-title {
  font-size: 14px;
  font-weight: bold;
  line-height: 30px;
}
.cpu-info .cpu-detail .detail-item .cpu-chart-info .info-line {
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

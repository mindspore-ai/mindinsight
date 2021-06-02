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
  <div class="data-process-wrap">
    <div class="title">{{$t('profiling.minddataTitle')}}</div>
    <el-tabs v-model="activeName"
             @tab-click="handleClick">
      <el-tab-pane :label="$t('profiling.queueInfo')"
                   name="queueInfo">
        <div class="data-process-top"
             v-show="!processSummary.noData">
          <div class="cell-container data-process">
            <div class="title">
              {{$t('profiling.pipeline')}}
            </div>
          </div>

          <div class="queue-container">
            <div class="img">
              <div class="edge">
                <img src="@/assets/images/data-flow.png" />
              </div>
              <div class="icon">
                <img src="@/assets/images/queue.svg"
                     @click="highlight('connector_queue')"
                     clickKey="connector_queue" />
              </div>
              <div class="edge">
                <img src="@/assets/images/data-flow.png" />
              </div>
            </div>
            <div class="title">{{connectorQuene}}</div>
            <div class="description">
              <div class="item"
                   v-if="processSummary.device.empty || processSummary.device.empty === 0">
                {{$t('profiling.queueTip2')}}
                <span class="num">
                  {{processSummary.device.empty}}/{{processSummary.device.total}}
                </span>
              </div>
              <div class="item"
                   v-if="processSummary.device.full || processSummary.device.full === 0">
                {{$t('profiling.queueTip1')}}
                <span class="num">
                  {{processSummary.device.full}}/{{processSummary.device.total}}
                </span>
              </div>
            </div>
          </div>

          <div class="cell-container device_queue_op"
               @click="highlight('device_queue_op')"
               clickKey="device_queue_op"
               :style="{cursor: processSummary.count !== processSummary.maxCount ? 'default' : 'pointer'}">
            <div class="title">
              {{$t('profiling.deviceQueueOp')}}
            </div>
          </div>

          <div class="queue-container"
               v-show="processSummary.count === processSummary.maxCount">
            <div class="img">
              <div class="edge">
                <img src="@/assets/images/data-flow.png" />
              </div>
              <div class="icon">
                <img src="@/assets/images/queue.svg"
                     @click="highlight('data_queue')"
                     clickKey="data_queue" />
              </div>
              <div class="edge">
                <img src="@/assets/images/data-flow.png" />
              </div>
            </div>
            <div class="title">{{$t('profiling.dataQueue')}}</div>
            <div class="description">
              <div class="item"
                   v-if="processSummary.get_next.empty || processSummary.get_next.empty === 0">
                {{$t('profiling.queueTip2')}}
                <span class="num">
                  {{processSummary.get_next.empty}}/{{processSummary.get_next.total}}
                </span>
              </div>
              <div class="item"
                   v-if="processSummary.get_next.full || processSummary.get_next.full === 0">
                {{$t('profiling.queueTip1')}}
                <span class="num">
                  {{processSummary.get_next.full}}/{{processSummary.get_next.total}}
                </span>
              </div>
            </div>
          </div>

          <div class="cell-container get-next"
               @click="highlight('get_next')"
               clickKey="get_next"
               v-if="processSummary.count === processSummary.maxCount">
            <div class="title">
              {{$t('profiling.getData')}}
            </div>
          </div>
        </div>
        <div class="data-process-bottom"
             v-show="!processSummary.noData">
          <div class="queue-step-wrap"
               v-if="processSummary.count === processSummary.maxCount">
            <div class="title">{{$t('profiling.queueStep')}}</div>
            <div class="chart-content">
              <div class="chart-wrap"
                   :class="{highlight:selected==='connector_queue'}">
                <div class="title">{{connectorQuene}}</div>
                <template v-if="!connectQueueChart.noData">
                  <div class="data-tips"
                       v-if="connectQueueChart.queueSummary.empty_queue!==undefined">
                    <div>
                      {{$t('profiling.queueTip2')}}{{connectQueueChart.queueSummary.empty_queue}}
                      /{{connectQueueChart.size}}</div>
                    <div>
                      {{$t('profiling.queueTip1')}}
                      {{connectQueueChart.size - connectQueueChart.queueSummary.empty_queue}}
                      /{{connectQueueChart.size}}</div>
                  </div>
                  <div id="connect-queue"
                       class="chart"></div>
                </template>
                <div class="image-noData"
                     v-else>
                  <div>
                    <img :src="require('@/assets/images/nodata.png')" />
                  </div>
                  <p>{{(connectQueueChart.initOver)?$t("public.noData"):$t("public.dataLoading")}}</p>
                </div>
              </div>
              <div class="chart-wrap"
                   :class="{highlight:selected==='data_queue'}">
                <div class="title">{{$t('profiling.dataQueue')}}</div>
                <template v-if="!dataQueueChart.noData">
                  <div class="data-tips"
                       v-if="dataQueueChart.queueSummary.empty_queue!==undefined">
                    <div>
                      {{$t('profiling.queueTip2')}}{{dataQueueChart.queueSummary.empty_queue}}
                      /{{dataQueueChart.size}}</div>
                    <div>
                      {{$t('profiling.queueTip1')}}
                      {{dataQueueChart.size - dataQueueChart.queueSummary.empty_queue}}
                      /{{dataQueueChart.size}}</div>
                  </div>
                  <div id="data-queue"
                       class="chart"></div>
                </template>
                <div class="image-noData"
                     v-else>
                  <div>
                    <img :src="require('@/assets/images/nodata.png')" />
                  </div>
                  <p>{{(dataQueueChart.initOver)?$t("public.noData"):$t("public.dataLoading")}}</p>
                </div>
              </div>
            </div>
          </div>
          <div class="queue-step-wrap"
               v-if="processSummary.count === processSummary.maxCount">
            <div class="title">{{$t('profiling.operatorTimeConAnalysis')}}</div>
            <div class="chart-content second">
              <div class="chart-wrap analysis"
                   :class="{highlight:selected==='device_queue_op'}">
                <div class="title">{{$t('profiling.deviceQueueOp')}}</div>
                <template v-if="!deviceQueueOpChart.noData">
                  <div class="data-tips">
                    <div v-if="deviceQueueOpChart.timeSummary.avg_cost!==undefined">
                      {{$t('profiling.avgCost')}}{{deviceQueueOpChart.timeSummary.avg_cost}}ms</div>
                    <div v-if="deviceQueueOpChart.timeSummary.get_cost!==undefined">
                      {{$t('profiling.getCost')}}{{deviceQueueOpChart.timeSummary.get_cost}}ms</div>
                    <div v-if="deviceQueueOpChart.timeSummary.push_cost!==undefined">
                      {{$t('profiling.pushCost')}}{{deviceQueueOpChart.timeSummary.push_cost}}ms</div>
                  </div>
                  <div id="device_queue_op"
                       class="chart"></div>
                </template>
                <div class="image-noData"
                     v-else>
                  <div>
                    <img :src="require('@/assets/images/nodata.png')" />
                  </div>
                  <p>{{(deviceQueueOpChart.initOver)?$t("public.noData"):$t("public.dataLoading")}}</p>
                </div>
              </div>
              <div class="chart-wrap analysis"
                   :class="{highlight:selected==='get_next'}">
                <div class="title">{{$t('profiling.getNext')}}</div>
                <template v-if="!getNextChart.noData">
                  <div class="data-tips">
                    <div v-if="getNextChart.timeSummary.avg_cost!==undefined">
                      {{$t('profiling.avgCost')}}{{getNextChart.timeSummary.avg_cost}}ms</div>
                    <div v-if="getNextChart.timeSummary.get_cost!==undefined">
                      {{$t('profiling.getCost')}}{{getNextChart.timeSummary.get_cost}}ms</div>
                    <div v-if="getNextChart.timeSummary.push_cost!==undefined">
                      {{$t('profiling.pushCost')}}{{getNextChart.timeSummary.push_cost}}ms</div>
                  </div>
                  <div id="get_next"
                       class="chart"></div>
                </template>
                <div class="image-noData"
                     v-else>
                  <div>
                    <img :src="require('@/assets/images/nodata.png')" />
                  </div>
                  <p>{{(getNextChart.initOver)?$t("public.noData"):$t("public.dataLoading")}}</p>
                </div>
              </div>
            </div>
          </div>
          <div class="queue-step-wrap single"
               v-if="processSummary.count !== processSummary.maxCount">
            <div class="title">{{$t('profiling.queueStep')}}</div>
            <div class="chart-content">
              <div class="chart-wrap"
                   :class="{highlight:selected==='connector_queue'}">
                <div class="title">{{connectorQuene}}</div>
                <template v-if="!connectQueueChart.noData">
                  <div class="data-tips"
                       v-if="connectQueueChart.queueSummary.empty_queue!==undefined">
                    <div>
                      {{$t('profiling.queueTip2')}}{{connectQueueChart.queueSummary.empty_queue}}
                      /{{connectQueueChart.size}}</div>
                    <div>
                      {{$t('profiling.queueTip1')}}
                      {{connectQueueChart.size - connectQueueChart.queueSummary.empty_queue}}
                      /{{connectQueueChart.size}}</div>
                  </div>
                  <div id="connect-queue"
                       class="chart"></div>
                </template>
              </div>
            </div>
          </div>
        </div>
        <div class="image-noData"
             v-if="processSummary.noData">
          <div>
            <img :src="require('@/assets/images/nodata.png')" />
          </div>
          <p>{{(initOver)?$t("public.noData"):$t("public.dataLoading")}}</p>
        </div>
      </el-tab-pane>
      <el-tab-pane :label="$t('profiling.pipeline')"
                   name="pipeLine">
        <div class="pipeline-wrap"
             v-show="!pipeData">
          <div class="pipeline-top">
            <div class="pipeline-top-title">
              {{$t('profiling.pipelineTopTitle')}}
            </div>
            <div class="average-rate-wrap">
              <div id="average-rate"></div>
            </div>
          </div>
          <div class="pipeline-middle">
            <div class="pipeline-middle-title">
              {{$t('profiling.pipelineMiddleTitle')}}
            </div>
            <div class="operator-graph">
              <div id="graph"></div>
            </div>
          </div>
          <div class="pipeline-bottom">
            <div class="queue-deep-wrap">
              <div class="left">
                <div id="queue-deep"></div>
              </div>
              <div class="right">
                <div class="title">{{$t('profiling.operatorInfo',{msg1:current_op.name,msg2:parent_op.name})}}</div>
                <div class="item-wrap">
                  <div class="item"><span>{{current_op.name}} ID:</span>{{current_op.op_id}}</div>
                  <div class="item"><span>{{current_op.name}} type:</span>{{current_op.op_type}}</div>
                  <div class="item">
                    <span>{{current_op.name}} {{$t('profiling.workersNum')}}:</span>
                    {{current_op.num_workers}}
                  </div>
                  <div class="item"><span>{{parent_op.name}} ID:</span>{{parent_op.op_id}}</div>
                  <div class="item"><span>{{parent_op.name}} type:</span>{{parent_op.op_type}}</div>
                  <div class="item">
                    <span>{{parent_op.name}} {{$t('profiling.workersNum')}}:</span>
                    {{parent_op.num_workers}}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="image-noData"
             v-if="pipeData">
          <div>
            <img :src="require('@/assets/images/nodata.png')" />
          </div>
          <p>{{initOver?$t("public.noData"):$t("public.dataLoading")}}</p>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
<script>
import echarts from '../../js/echarts';
import RequestService from '../../services/request-service';
import {select, selectAll, zoom} from 'd3';
import {event as currentEvent} from 'd3-selection';
import 'd3-graphviz';
const d3 = {select, selectAll, zoom};
export default {
  props: {},
  data() {
    return {
      dir: '', // Profiler path
      currentCard: '', // Purrent card number
      connectQueueChart: {
        // Connect queue chart object
        id: 'connect-queue',
        chartDom: null,
        data: [],
        queueSummary: {},
        type: 0,
        params: 'device_queue',
        noData: true,
        size: null,
        deviceId: null,
        initOver: false,
      },
      dataQueueChart: {
        // Data queue chart object
        id: 'data-queue',
        chartDom: null,
        data: [],
        queueSummary: {},
        type: 0,
        params: 'get_next',
        noData: true,
        size: null,
        initOver: false,
      },
      deviceQueueOpChart: {
        // Device queue chart object
        id: 'device_queue_op',
        chartDom: null,
        data: [],
        timeSummary: {},
        type: 1,
        params: 'device_queue',
        noData: true,
        initOver: false,
      },
      getNextChart: {
        // Get next chart object
        id: 'get_next',
        chartDom: null,
        data: [],
        timeSummary: {},
        type: 1,
        params: 'get_next',
        noData: true,
        initOver: false,
      },
      processSummary: {
        // Process summary object
        noData: true,
        count: 6,
        maxCount: 6,
        device: {
          empty: 0,
          full: 0,
          total: 0,
        },
        get_next: {
          empty: 0,
          full: 0,
          total: 0,
        },
      },
      activeName: 'queueInfo',
      averageRateChart: {
        // Average rate chart object
        id: 'average-rate',
        chartDom: null,
        deviceId: null,
      },
      queueDeepChart: {
        // Queue deep chart object
        id: 'queue-deep',
        chartDom: null,
      },
      current_op: {},
      parent_op: {},
      pipeData: true,
      initOver: false, // Identify whether the interface returns
      allGraphData: {},
      graphviz: null,
      totalMemory: 16777216 * 2, // Memory size of the graph plug-in
      scaleRange: [0.0001, 10000], // Graph zooms in and zooms out.
      initQueue: '',
      trainId: '',
      selected: '',
      connectorQuene: '',
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
            document.title = `${decodeURIComponent(this.trainId)}` + `-${this.$t('profiling.mindData')}-MindInsight`;
          } else {
            document.title = `${this.$t('profiling.mindData')}-MindInsight`;
          }
          if (this.activeName === 'queueInfo') {
            this.init();
          } else if (this.activeName === 'pipeLine') {
            this.queryAverageRate();
          }
        }
        if (this.activeName === 'queueInfo' && this.$parent.curDashboardInfo.initOver) {
          this.initOver = true;
        }
      },
      deep: true,
      immediate: true,
    },
  },
  computed: {},
  mounted() {
    window.addEventListener('resize', this.debounce(this.resizeCallback, 200), false);
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
    /**
     *  Tabs switch
     */
    handleClick() {
      if (this.activeName === 'pipeLine' && this.averageRateChart.deviceId !== this.currentCard) {
        this.queryAverageRate();
      } else if (this.activeName === 'queueInfo' && this.connectQueueChart.deviceId !== this.currentCard) {
        this.init();
      }
      this.$nextTick(() => {
        this.resizeCallback();
      });
    },
    init() {
      this.connectorQuene = this.$t('profiling.connectorQuene');
      this.queryProcessSummary();
    },
    /**
     *  Resize callback function
     */
    resizeCallback() {
      const chartArr = [
        'connectQueueChart',
        'dataQueueChart',
        'deviceQueueOpChart',
        'getNextChart',
        'averageRateChart',
        'queueDeepChart',
      ];
      chartArr.forEach((val) => {
        if (this[val].chartDom) {
          this[val].chartDom.resize();
        }
      });
    },
    /**
     * Query minddata data
     * @param {Object} chart Chart object
     */
    queryMinddataOp(chart) {
      const params = {
        profile: this.dir,
        device_id: this.currentCard,
        type: chart.params,
        train_id: this.trainId,
      };
      RequestService.minddataOp(params).then(
          (res) => {
            if (res && res.data) {
              chart.initOver = true;
              const result = res.data;
              chart.data = result.info;
              if (result.summary) {
                chart.timeSummary = result.summary.time_summary || {};
                Object.keys(chart.timeSummary).forEach((val) => {
                  chart.timeSummary[val] = parseFloat(chart.timeSummary[val]).toFixed(3);
                });
              }
              if (result.size > 0) {
                chart.noData = false;
                this.$nextTick(() => {
                  this.setOption(chart);
                });
              } else {
                if (chart.chartDom) {
                  chart.chartDom.clear();
                }
                chart.noData = true;
              }
            }
          },
          (err) => {
            if (chart.chartDom) {
              chart.chartDom.clear();
            }
            chart.initOver = true;
            chart.noData = true;
          },
      );
    },
    /**
     * Query queue info
     * @param {Object} chart Chart object
     */
    queryQueueInfo(chart) {
      const params = {
        profile: this.dir,
        device_id: this.currentCard,
        type: chart.params,
        train_id: this.trainId,
      };
      RequestService.queueInfo(params).then(
          (res) => {
            if (res && res.data) {
              chart.initOver = true;
              const result = res.data;
              chart.data = result.info;
              if (result.summary) {
                chart.queueSummary = result.summary.queue_summary || {};
              }
              if (result.size > 0) {
                chart.noData = false;
                chart.size = result.size;
                this.$nextTick(() => {
                  this.setOption(chart);
                });
              } else {
                if (chart.chartDom) {
                  chart.chartDom.clear();
                }
                chart.noData = true;
              }
            }
          },
          (err) => {
            chart.initOver = true;
            chart.noData = true;
            if (chart.chartDom) {
              chart.chartDom.clear();
            }
          },
      );
    },
    /**
     * Chart set option
     * @param {Object} chart Chart object
     */
    setOption(chart) {
      const myChart = echarts.init(document.getElementById(chart.id));
      const option = {
        tooltip: {
          trigger: 'axis',
          confine: true,
          backgroundColor: 'rgba(50, 50, 50, 0.7)',
          borderWidth: 0,
          textStyle: {
            color: '#fff',
          },
        },
        toolbox: {
          show: true,
        },
        xAxis: {
          name: 'step',
          data: [],
        },
        yAxis: {},
        series: [],
        grid: {
          left: 50,
          top: 20,
          right: 50,
          bottom: 60,
        },
      };
      option.dataZoom = [
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
      ];
      const arr = [];
      Object.keys(chart.data).forEach((val, index) => {
        const item = {};
        item.type = 'line';
        item.data = chart.data[val];
        item.name = val;
        if (chart.type === 0) {
          const markPointArr = [];
          item.data.forEach((val, key) => {
            if (val === 0) {
              markPointArr.push({xAxis: key, yAxis: val, symbolSize: 20});
            }
          });
          item.markPoint = {data: markPointArr};
        }
        arr.push(item);
      });
      option.series = arr;
      option.xAxis.data = chart.data[Object.keys(chart.data)[0]].map(
          (val, index) => index + 1,
      );

      myChart.setOption(option);
      chart.chartDom = myChart;
      if (this.connectQueueChart.chartDom && this.deviceQueueOpChart.chartDom) {
        echarts.connect([
          this.connectQueueChart.chartDom,
          this.deviceQueueOpChart.chartDom,
        ]);
      }
      if (this.getNextChart.chartDom && this.dataQueueChart.chartDom) {
        echarts.connect([
          this.getNextChart.chartDom,
          this.dataQueueChart.chartDom,
        ]);
      }
    },
    /**
     * Query process summary info
     */
    queryProcessSummary() {
      const params = {
        profile: this.dir,
        device_id: this.currentCard,
        train_id: this.trainId,
      };
      this.connectQueueChart.deviceId = this.currentCard;
      this.initOver = false;
      RequestService.queryProcessSummary(params).then(
          (res) => {
            if (res && res.data) {
              const data = JSON.parse(JSON.stringify(res.data));
              this.processSummary.count = Object.keys(data).length;
              if (this.processSummary.count) {
                this.dealProcess(data);
                this.$nextTick(() => {
                  if (this.processSummary.count < this.processSummary.maxCount) {
                    this.queryQueueInfo(this.connectQueueChart);
                    this.dataQueueChart.noData = false;
                    this.deviceQueueOpChart.noData = false;
                    this.getNextChart.noData = false;
                  } else {
                    this.queryQueueInfo(this.connectQueueChart);
                    this.queryQueueInfo(this.dataQueueChart);
                    this.queryMinddataOp(this.deviceQueueOpChart);
                    this.queryMinddataOp(this.getNextChart);
                  }
                });
              } else {
                this.dealProcess(null);
              }
            } else {
              this.dealProcess(null);
            }
          },
          (error) => {
            this.dealProcess(null);
          },
      );
    },
    /**
     * Deal process data
     * @param {Object} data Process data
     */
    dealProcess(data) {
      this.processSummary.device = {
        empty: 0,
        full: 0,
        total: 0,
      };
      this.processSummary.get_next = {
        empty: 0,
        full: 0,
        total: 0,
      };
      this.processSummary.noData = true;
      this.initOver = true;

      if (data) {
        if (data.device_queue_info && data.device_queue_info.summary) {
          this.processSummary.device = {
            empty: data.device_queue_info.summary.empty_batch_count,
            full: data.device_queue_info.summary.total_batch - data.device_queue_info.summary.empty_batch_count,
            total: data.device_queue_info.summary.total_batch,
          };
        }
        if (data.get_next_queue_info && data.get_next_queue_info.summary) {
          this.processSummary.get_next = {
            empty: data.get_next_queue_info.summary.empty_batch_count,
            full: data.get_next_queue_info.summary.total_batch - data.get_next_queue_info.summary.empty_batch_count,
            total: data.get_next_queue_info.summary.total_batch,
          };
        }
        this.processSummary.noData = false;
      }
    },
    /**
     * Query average rate info
     */
    queryAverageRate() {
      const params = {
        params: {
          train_id: this.trainId,
          profile: this.dir,
        },
        body: {
          device_id: this.currentCard,
        },
      };
      this.averageRateChart.deviceId = this.currentCard;
      this.initOver = false;
      RequestService.queryOpQueue(params).then(
          (res) => {
            this.initOver = true;
            if (res && res.data) {
              this.removeGraph();
              const data = JSON.parse(JSON.stringify(res.data));
              this.dealPipeLineData(data);

              this.pipeData = !!!(res.data.object && res.data.object.length);
              if (res.data.object && res.data.object.length && res.data.col_name) {
                const result = res.data.object.map((val) => {
                  const obj = {};
                  res.data.col_name.forEach((value, key) => {
                    obj[value] = val[key];
                  });
                  return obj;
                });
                const data = result
                    .sort((a, b) => {
                      return a.output_queue_usage_rate - b.output_queue_usage_rate;
                    })
                    .filter((val) => {
                      return val.parent_id !== null;
                    });

                const dataY = data.map((val) => {
                  return (val.output_queue_usage_rate * 100).toFixed(4);
                });
                const dataX = data.map((val) => {
                  return `Queue_${val.op_id}`;
                });

                const profiling = this.$t('profiling');
                const option = {
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
                    confine: true,
                    formatter(params) {
                      let value = {};
                      data.forEach((val) => {
                        if (`${val.op_id}` === params[0].axisValue.split('')[6]) {
                          value = val;
                        }
                      });
                      return (
                        `${params[0].axisValue}<br>${params[0].marker}` +
                      `${profiling.averageCapacity}：${value.output_queue_average_size}<br>` +
                      `${params[0].marker}${profiling.totalCapacity}：` +
                      `${value.output_queue_length}`
                      );
                    },
                  },
                  grid: {
                    left: 70,
                    top: 20,
                    right: 100,
                    bottom: 50,
                  },
                  xAxis: {
                    type: 'value',
                    boundaryGap: [0, 0.01],
                    max: 100,
                    axisLabel: {
                      formatter(params) {
                        return `${params}%`;
                      },
                    },
                  },
                  yAxis: {
                    type: 'category',
                    data: dataX,
                  },
                  series: [
                    {
                      type: 'bar',
                      data: dataY,
                      itemStyle: {
                        color: '#00a5a7',
                      },
                      label: {
                        show: true,
                        position: 'right',
                        color: '#000',
                        formatter(params) {
                          return `${params.value}%`;
                        },
                      },
                    },
                  ],
                  dataZoom: [
                    {start: 0, end: 100, orient: 'vertical', right: 10},
                    {
                      start: 0,
                      end: 100,
                      type: 'inside',
                      orient: 'vertical',
                      right: 10,
                    },
                  ],
                };
                this.$nextTick(() => {
                  const echart = echarts.init(
                      document.getElementById(this.averageRateChart.id),
                  );
                  echart.setOption(option);
                  this.averageRateChart.chartDom = echart;
                });
              }
            }
          },
          () => {
            this.initOver = true;
            this.pipeData = true;
            this.removeGraph();
          },
      );
    },
    /**
     * Query queue info
     * @param {Number} id Op id
     */
    queryQueue(id) {
      const params = {
        profile: this.dir,
        train_id: this.trainId,
        device_id: this.currentCard,
        op_id: id,
      };
      RequestService.queryQueue(params).then((res) => {
        if (res && res.data) {
          const data = res.data.queue_info;
          const dataY = data.output_queue_size;
          this.current_op = res.data.current_op || {};
          this.parent_op = res.data.parent_op || {};
          this.current_op.name = `${this.current_op.op_type}_${this.current_op.op_id}`;
          this.parent_op.name = `${this.parent_op.op_type}_${this.parent_op.op_id}`;
          const option = {
            title: {
              text: this.$t('profiling.queueDeepChartTitle', {
                msg: `Queue${id}`,
              }),
              textStyle: {
                fontSize: 13,
              },
              left: 20,
              top: 10,
            },
            tooltip: {
              trigger: 'axis',
              confine: true,
              backgroundColor: 'rgba(50, 50, 50, 0.7)',
              borderWidth: 0,
              textStyle: {
                color: '#fff',
              },
            },
            xAxis: {
              name: `${this.$t('profiling.sampleInterval')}/${
                data.sample_interval
              }ms`
                  .split(' ')
                  .join('\n'),
              data: dataY.map((val, index) => index + 1),
            },
            yAxis: {
              name: '',
            },
            series: [
              {
                type: 'line',
                data: dataY,
                itemStyle: {
                  color: '#00a5a7',
                },
              },
            ],
            grid: {
              left: 50,
              top: 40,
              right: 100,
              bottom: 60,
            },
            dataZoom: [
              {
                start: 0,
                end: 100,
                bottom: 10,
              },
              {start: 0, end: 100, type: 'inside', bottom: 10},
            ],
          };
          this.$nextTick(() => {
            const echart = echarts.init(
                document.getElementById(this.queueDeepChart.id),
            );
            echart.setOption(option);
            this.queueDeepChart.chartDom = echart;
          });
        }
      });
    },
    highlight(key) {
      if (
        key === 'device_queue_op' &&
        this.processSummary.count !== this.processSummary.maxCount
      ) {
        return;
      }
      const domList = document.querySelectorAll('.data-process-top *[clickKey]');
      Array.prototype.forEach.call(domList, (dom) => {
        if (dom.getAttribute('clickKey') === key) {
          dom.classList.add('selected');
        } else {
          dom.classList.remove('selected');
        }
      });
      this.selected = key;
    },

    /** ************************ graph  ****************************/

    /**
     * Processing Graph Data
     * @param {Object} data Data of the graph
     */
    dealPipeLineData(data) {
      const colName = data.col_name;
      const colCount = colName.length;
      const list = data.object;

      list.forEach((i) => {
        if (i && i.length === colCount) {
          const obj = {
            output: '',
          };
          colName.forEach((key, index) => {
            obj[key] = i[index];
          });

          if (obj.op_id || obj.op_id === 0) {
            obj.key = `${obj.op_id}_operator`;
            if (obj.parent_id || obj.parent_id === 0) {
              const queueKey = `${obj.op_id}_queue`;
              obj.output = queueKey;

              const queueObj = JSON.parse(JSON.stringify(obj));
              queueObj.key = queueKey;
              queueObj.op_type = 'queue';
              queueObj.output = `${obj.parent_id}_operator`;
              this.allGraphData[queueKey] = queueObj;

              if (!(this.initQueue || this.initQueue === 0)) {
                this.initQueue = queueObj.op_id;
              }
            }

            this.allGraphData[obj.key] = obj;
          }
        }
      });
      if (Object.keys(this.allGraphData).length) {
        const dot = this.packageGraphData();
        this.initGraph(dot);
      } else {
        this.removeGraph();
      }
    },
    /**
     * Encapsulates graph data into dot data.
     * @return {String} Dot string for packing graph data
     */
    packageGraphData() {
      let nodeStr = '';
      let edgeStr = '';
      Object.keys(this.allGraphData).forEach((key) => {
        const node = this.allGraphData[key];
        nodeStr +=
          `<${key}>[id="${key}";` +
          `${
            node.op_type === 'queue'
              ? `shape=rect;class="queue";label="Queue_${
                node.op_id
              }(${parseFloat(
                  ((node.output_queue_usage_rate || 0) * 100).toFixed(4),
              )}%)";`
              : `shape=Mrecord;class="operator";label="${node.op_type}_${node.op_id}";`
          }];`;

        if (node.output) {
          edgeStr += `<${node.key}>-><${node.output}>`;
        }
      });

      const initSetting =
        'node[style="filled";fontsize="10px"];edge[fontsize="6px";];';
      return `digraph {compound=true;rankdir=LR;${initSetting}${nodeStr}${edgeStr}}`;
    },

    /**
     * Initializing the dataset graph
     * @param {String} dot Dot statement encapsulated in graph data
     */
    initGraph(dot) {
      this.graphviz = d3
          .select('#graph')
          .graphviz({useWorker: false, totalMemory: this.totalMemory})
          .zoomScaleExtent(this.scaleRange)
          .dot(dot)
          .attributer(this.attributer)
          .render(this.startApp);
    },
    /**
     * Default method of the graph rendering adjustment. Set the node format.
     * @param {Object} datum Object of the current rendering element.
     * @param {Number} index Indicates the subscript of the current rendering element.
     * @param {Array} nodes An array encapsulated with the current rendering element.
     */
    attributer(datum, index, nodes) {
      if (datum.tag === 'svg') {
        const width = '100%';
        const height = '100%';
        datum.attributes.width = width;
        datum.attributes.height = height;
      }
    },
    /**
     * Initialization method executed after the graph rendering is complete
     */
    startApp() {
      setTimeout(() => {
        if (this.graphviz) {
          this.graphviz._data = null;
          this.graphviz._dictionary = null;
          this.graphviz = null;
        }
      }, 500);
      d3.select('#graph').selectAll('.operator>title').remove();

      const queueList = Array.from(document.querySelectorAll('#graph .queue'));
      for (let i = 0, len = queueList.length; i < len; i++) {
        const node = queueList[i];
        const data = this.allGraphData[node.id];
        if (data) {
          const polygon = node.querySelector('polygon');
          const color = `rgba(19, 171, 173, ${data.output_queue_usage_rate})`;
          polygon.setAttribute('fill', color);
          polygon.setAttribute('stroke', color);

          const title = node.querySelector('title');
          title.textContent =
            `${this.$t('profiling.averageCapacity')}:${
              data.output_queue_average_size || 0
            }\n` +
            `${this.$t('profiling.totalCapacity')}:${
              data.output_queue_length || 0
            }`;
        }
      }

      this.initZooming();
      const nodes = d3.selectAll('g.queue');
      nodes.on('click', (target, index, nodesList) => {
        const selectedNode = nodesList[index];
        nodes.classed('selected', false);
        d3.select(`g[id="${selectedNode.id}"]`).classed('selected', true);
        const nodeData = this.allGraphData[selectedNode.id];
        if (nodeData) {
          this.queryQueue(nodeData.op_id);
        }
      });

      d3.select(`g[id="${this.initQueue}_queue"]`).classed('selected', true);
      this.queryQueue(this.initQueue);
    },

    /**
     * Initializing the Zoom Function of a Graph
     */
    initZooming() {
      const svgDom = document.querySelector('#graph svg');
      const svgRect = svgDom.getBoundingClientRect();

      const graphDom = document.querySelector('#graph #graph0');
      const graphBox = graphDom.getBBox();
      const graphRect = graphDom.getBoundingClientRect();
      let graphTransform = {};

      const minScale = Math.min(
          svgRect.width / 2 / graphRect.width,
          svgRect.height / 2 / graphRect.height,
      );

      const padding = 4;
      const minDistance = 20;
      const pointer = {start: {x: 0, y: 0}, end: {x: 0, y: 0}};

      const zoom = d3
          .zoom()
          .on('start', () => {
            const event = currentEvent.sourceEvent;
            pointer.start.x = event.x;
            pointer.start.y = event.y;
          })
          .on('zoom', () => {
            const event = currentEvent.sourceEvent;
            const transformData = this.getTransformData(graphDom);
            if (!Object.keys(graphTransform).length) {
              graphTransform = {
                x: transformData.translate[0],
                y: transformData.translate[1],
                k: transformData.scale[0],
              };
            }

            let tempStr = '';
            let change = {};
            let scale = transformData.scale[0];
            const graphRect = graphDom.getBoundingClientRect();
            const transRate = graphBox.width / graphRect.width;
            if (event.type === 'mousemove') {
              pointer.end.x = event.x;
              pointer.end.y = event.y;
              let tempX = pointer.end.x - pointer.start.x;
              let tempY = pointer.end.y - pointer.start.y;
              const paddingTrans = Math.max(
                  (padding / transRate) * scale,
                  minDistance,
              );
              if (
                graphRect.left + paddingTrans + tempX >=
              svgRect.left + svgRect.width
              ) {
                tempX = Math.min(tempX, 0);
              }
              if (
                graphRect.left + graphRect.width - paddingTrans + tempX <=
              svgRect.left
              ) {
                tempX = Math.max(tempX, 0);
              }
              if (
                graphRect.top + paddingTrans + tempY >=
              svgRect.top + svgRect.height
              ) {
                tempY = Math.min(tempY, 0);
              }
              if (
                graphRect.top + graphRect.height - paddingTrans + tempY <=
              svgRect.top
              ) {
                tempY = Math.max(tempY, 0);
              }

              change = {
                x: tempX * transRate * scale,
                y: tempY * transRate * scale,
              };
              pointer.start.x = pointer.end.x;
              pointer.start.y = pointer.end.y;
            } else if (event.type === 'wheel') {
              const wheelDelta = -event.deltaY;
              const rate = 1.2;
              scale =
              wheelDelta > 0
                ? transformData.scale[0] * rate
                : transformData.scale[0] / rate;

              scale = Math.max(this.scaleRange[0], scale, minScale);
              scale = Math.min(this.scaleRange[1], scale);
              change = {
                x:
                (graphRect.x + padding / transRate - event.x) *
                transRate *
                (scale - transformData.scale[0]),
                y:
                (graphRect.bottom - padding / transRate - event.y) *
                transRate *
                (scale - transformData.scale[0]),
              };
            }

            graphTransform = {
              x: transformData.translate[0] + change.x,
              y: transformData.translate[1] + change.y,
              k: scale,
            };

            tempStr = `translate(${graphTransform.x},${graphTransform.y}) scale(${graphTransform.k})`;
            graphDom.setAttribute('transform', tempStr);
            event.stopPropagation();
            event.preventDefault();
          });

      const svg = d3.select('#graph svg');
      svg.on('.zoom', null);
      svg.call(zoom);
      svg.on('dblclick.zoom', null);
      svg.on('wheel.zoom', null);

      const graph0 = d3.select('#graph #graph0');
      graph0.on('.zoom', null);
      graph0.call(zoom);
    },
    /**
     * Obtains the transform data of a node.
     * @param {Object} node Node dom data
     * @return {Object} Transform data of a node
     */
    getTransformData(node) {
      if (!node) {
        return [];
      }
      const transformData = node.getAttribute('transform');
      const attrObj = {};
      if (transformData) {
        const lists = transformData.trim().split(' ');
        lists.forEach((item) => {
          const index1 = item.indexOf('(');
          const index2 = item.indexOf(')');
          const name = item.substring(0, index1);
          const params = item
              .substring(index1 + 1, index2)
              .split(',')
              .map((i) => {
                return parseFloat(i) || 0;
              });
          attrObj[name] = params;
        });
      }
      return attrObj;
    },
    removeGraph() {
      const svg = document.querySelector('#graph svg');
      if (svg) {
        svg.remove();
      }
      this.allGraphData = {};
    },
  },
  destroyed() {
    // Remove the listener of window size change
    window.removeEventListener(
        'resize',
        this.debounce(this.resizeCallback, 200),
        false,
    );
    this.$bus.$off('collapse');
  },
};
</script>
<style>
.data-process-wrap {
  height: 100%;
  background: #fff;
  padding: 0 16px;
}
.data-process-wrap .title {
  font-size: 18px;
  font-weight: bold;
  text-align: left;
}
.data-process-wrap .el-tabs.el-tabs--top {
  height: calc(100% - 24px);
}
.data-process-wrap .el-tabs__content {
  height: calc(100% - 54px);
}
.data-process-wrap .el-tabs__content > .el-tab-pane {
  height: 100%;
}
.data-process-wrap .el-tabs__item.is-active {
  color: #00a5a7;
  font-weight: bold;
}
.data-process-wrap .data-process-top {
  height: 156px;
  font-size: 0;
  display: flex;
  align-items: flex-start;
  padding-top: 20px;
}
.data-process-wrap .data-process-top .cell-container {
  width: 20%;
  cursor: pointer;
  padding: 20px 0;
  border: 2px solid transparent;
}
.data-process-wrap .data-process-top .cell-container .title {
  font-size: 14px;
  line-height: 20px;
  padding: 0 0 0 20px;
  font-weight: bold;
}
.data-process-wrap .data-process-top .data-process {
  background-color: #e3f8eb;
  cursor: default;
}
.data-process-wrap .data-process-top .data-process .title {
  border-left: 2px solid #00a5a7;
}
.data-process-wrap .data-process-top .device_queue_op {
  background-color: #e1f2ff;
}
.data-process-wrap .data-process-top .device_queue_op .title {
  border-left: 2px solid #6cbfff;
}
.data-process-wrap .data-process-top .get-next {
  background-color: #fef4dd;
}
.data-process-wrap .data-process-top .get-next .title {
  border-left: 2px solid #fdca5a;
}
.data-process-wrap .data-process-top .queue-container {
  width: 20%;
  position: relative;
}
.data-process-wrap .data-process-top .queue-container .img {
  width: 100%;
  height: 37px;
  margin-top: 13px;
}
.data-process-wrap .data-process-top .queue-container .img .edge {
  width: calc(50% - 40px);
  display: inline-block;
  padding-top: 11px;
}
.data-process-wrap .data-process-top .queue-container .img .edge img {
  width: 100%;
}
.data-process-wrap .data-process-top .queue-container .img .icon {
  width: 80px;
  padding: 0 20px;
  display: inline-block;
  vertical-align: middle;
}
.data-process-wrap .data-process-top .queue-container .img .icon img {
  padding: 3px;
  border: 2px solid transparent;
  cursor: pointer;
}
.data-process-wrap .data-process-top .queue-container .title {
  text-align: center;
  font-size: 14px;
  margin-top: 10px;
  font-weight: bold;
}
.data-process-wrap .data-process-top .queue-container .description {
  position: absolute;
  font-size: 12px;
  line-height: 12px;
  white-space: nowrap;
  overflow: hidden;
  width: 100%;
  text-align: center;
}
.data-process-wrap .data-process-top .queue-container .description .item {
  font-size: 12px;
  line-height: 16px;
  white-space: normal;
}
.data-process-wrap .data-process-top .queue-container .description .item .num {
  color: #07a695;
}
.data-process-wrap .data-process-top .selected {
  border: 2px solid #3399ff !important;
}
.data-process-wrap .data-process-bottom {
  height: calc(100% - 156px);
}
.data-process-wrap .data-process-bottom .queue-step-wrap:first-child {
  height: 50%;
}
.data-process-wrap .data-process-bottom .queue-step-wrap:last-child {
  height: 50%;
}
.data-process-wrap .data-process-bottom .queue-step-wrap > .title {
  margin-bottom: 15px;
  font-weight: bold;
  font-size: 16px;
}
.data-process-wrap .data-process-bottom .queue-step-wrap .chart-content {
  height: calc(100% - 31px);
}
.data-process-wrap .data-process-bottom .queue-step-wrap .chart-content .chart-wrap {
  float: left;
  width: calc(50% - 12px);
  height: calc(100% - 10px);
  border-radius: 4px;
  overflow-y: auto;
  border: 1px solid #D9D9D9;
}
.data-process-wrap .data-process-bottom .queue-step-wrap .chart-content .chart-wrap:first-child {
  margin-right: 20px;
}
.data-process-wrap .data-process-bottom .queue-step-wrap .chart-content .chart-wrap .title {
  font-size: 13px;
  padding: 10px;
  font-weight: bold;
}
.data-process-wrap .data-process-bottom .queue-step-wrap .chart-content .chart-wrap .data-tips {
  color: #999;
  padding: 0 0 0 10px;
}
.data-process-wrap .data-process-bottom .queue-step-wrap .chart-content .chart-wrap .data-tips > div {
  display: inline-block;
  margin-right: 10px;
}
.data-process-wrap .data-process-bottom .queue-step-wrap .chart-content .chart-wrap .chart {
  height: calc(100% - 70px);
  min-height: 150px;
  overflow: hidden;
}
.data-process-wrap .data-process-bottom .queue-step-wrap .chart-content .chart-wrap.highlight {
  border-color: #3399ff;
}
.data-process-wrap .data-process-bottom .queue-step-wrap .chart-content.second {
  height: calc(100% - 26px);
}
.data-process-wrap .data-process-bottom .queue-step-wrap.single {
  height: 100%;
}
.data-process-wrap .data-process-bottom .queue-step-wrap.single .chart-content .chart-wrap {
  width: 100%;
}
.data-process-wrap .pipeline-wrap {
  height: 100%;
}
.data-process-wrap .pipeline-wrap .pipeline-top {
  height: 35%;
}
.data-process-wrap .pipeline-wrap .pipeline-top .pipeline-top-title {
  font-size: 16px;
  font-weight: bold;
}
.data-process-wrap .pipeline-wrap .pipeline-top .average-rate-wrap {
  overflow-y: auto;
  height: calc(100% - 21px);
}
.data-process-wrap .pipeline-wrap .pipeline-top .average-rate-wrap #average-rate {
  height: 100%;
  min-height: 180px;
  overflow: hidden;
}
.data-process-wrap .pipeline-wrap .pipeline-middle {
  height: 30%;
}
.data-process-wrap .pipeline-wrap .pipeline-middle .pipeline-middle-title {
  font-size: 16px;
  font-weight: bold;
}
.data-process-wrap .pipeline-wrap .pipeline-middle .operator-graph {
  height: calc(100% - 21px);
}
.data-process-wrap .pipeline-wrap .pipeline-middle .operator-graph #graph {
  width: 100%;
  height: 100%;
  background-color: #f7faff;
}
.data-process-wrap .pipeline-wrap .pipeline-middle .operator-graph #graph #graph0 > polygon {
  fill: transparent;
}
.data-process-wrap .pipeline-wrap .pipeline-middle .operator-graph #graph .node.queue {
  cursor: pointer;
}
.data-process-wrap .pipeline-wrap .pipeline-middle .operator-graph #graph .operator path {
  stroke: #e6ebf5;
  fill: #e6ebf5;
}
.data-process-wrap .pipeline-wrap .pipeline-middle .operator-graph #graph .selected path,
.data-process-wrap .pipeline-wrap .pipeline-middle .operator-graph #graph .selected polygon {
  stroke: red;
}
.data-process-wrap .pipeline-wrap .pipeline-middle .operator-graph #graph .edge path,
.data-process-wrap .pipeline-wrap .pipeline-middle .operator-graph #graph .edge polygon {
  stroke: #e6ebf5;
  fill: #e6ebf5;
}
.data-process-wrap .pipeline-wrap .pipeline-bottom {
  height: 35%;
}
.data-process-wrap .pipeline-wrap .pipeline-bottom .queue-deep-wrap {
  height: 100%;
  background: #fafbfc;
}
.data-process-wrap .pipeline-wrap .pipeline-bottom .queue-deep-wrap > div {
  float: left;
  height: 100%;
}
.data-process-wrap .pipeline-wrap .pipeline-bottom .queue-deep-wrap .left {
  width: calc(60% - 20px);
  overflow-y: auto;
  height: 100%;
  border-right: 1px dashed #ccc;
  padding-right: 20px;
  margin-right: 20px;
}
.data-process-wrap .pipeline-wrap .pipeline-bottom .queue-deep-wrap .left #queue-deep {
  height: 100%;
  width: 100%;
  min-height: 220px;
  overflow: hidden;
}
.data-process-wrap .pipeline-wrap .pipeline-bottom .queue-deep-wrap .right {
  width: 40%;
}
.data-process-wrap .pipeline-wrap .pipeline-bottom .queue-deep-wrap .right .title {
  font-size: 13px;
  margin-top: 7px;
}
.data-process-wrap .pipeline-wrap .pipeline-bottom .queue-deep-wrap .right .item-wrap {
  padding-top: 10px;
  height: calc(100% - 26px);
  overflow-y: auto;
}
.data-process-wrap .pipeline-wrap .pipeline-bottom .queue-deep-wrap .right .item-wrap .item {
  margin-top: 10px;
}
.data-process-wrap .pipeline-wrap .pipeline-bottom .queue-deep-wrap .right .item-wrap .item > span {
  color: #757b88;
  display: inline-block;
  width: 50%;
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
  background-color: white;
  color: #00a5a7;
  padding: 7px 15px;
}
.data-process-wrap .el-button:hover {
  background: rgb(230, 246, 246);
}
</style>

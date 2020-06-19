<!--
Copyright 2020 Huawei Technologies Co., Ltd.All Rights Reserved.

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
  <div class="md-wrap">
    <div class="title">{{$t('profiling.minddataTitle')}}</div>
    <el-tabs v-model="activeName"
             @tab-click="handleClick">
      <el-tab-pane :label="$t('profiling.queueInfo')"
                   name="queueInfo">
        <div class="md-top"
             v-if="!(connectQueueChart.noData && dataQueueChart.noData &&
              deviceQueueOpChart && getNextChart.getNextChart)">
          <div class="cell-container data-process"
               v-show="!processSummary.noData">
            <div class="title">
              {{$t('profiling.pipeline')}}
            </div>
          </div>

          <div class="queue-container"
               v-show="!processSummary.noData">
            <div class="img">
              <div class="edge">
                <img src="@/assets/images/data-flow.png"
                     alt="" />
              </div>
              <div class="icon">
                <img src="@/assets/images/queue.svg"
                     alt=""
                     @click="highlight('connector_queue')"
                     clickKey="connector_queue" />
              </div>
              <div class="edge">
                <img src="@/assets/images/data-flow.png"
                     alt="" />
              </div>
            </div>
            <div class="title">{{$t('profiling.connectorQuene')}}</div>
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
               v-show="!processSummary.noData">
            <div class="title">
              {{$t('profiling.deviceQueueOp')}}
            </div>
            <div class="content">{{$t('profiling.deviceQueueOpTip')}} | TDT</div>
          </div>

          <div class="queue-container"
               v-show="processSummary.count === 6 && !processSummary.noData">
            <div class="img">
              <div class="edge">
                <img src="@/assets/images/data-flow.png"
                     alt="" />
              </div>
              <div class="icon">
                <img src="@/assets/images/queue.svg"
                     @click="highlight('data_queue')"
                     clickKey="data_queue"
                     alt="" />
              </div>
              <div class="edge">
                <img src="@/assets/images/data-flow.png"
                     alt="" />
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
               v-if="processSummary.count === 6 && !processSummary.noData">
            <div class="title">
              {{$t('profiling.getData')}}
            </div>
          </div>
        </div>
        <div class="md-bottom"
             v-if="!(connectQueueChart.noData && dataQueueChart.noData && deviceQueueOpChart
             && getNextChart.getNextChart)">
          <div class="queue-step-wrap">
            <div class="title">{{$t('profiling.queueStep')}}</div>
            <div class="chart-content">
              <div class="chart-wrap"
                   :class="{highlight:selected==='connector_queue'}">
                <div class="title">{{$t('profiling.connectorQuene')}}</div>
                <template v-if="!connectQueueChart.noData">
                  <div class="data-tips">
                    <div v-if="connectQueueChart.queueSummary.empty_queue!==undefined">
                      {{$t('profiling.queueEmptyRatio')}}{{connectQueueChart.queueSummary.empty_queue}}</div>
                    <div v-if="connectQueueChart.queueSummary.full_queue!==undefined">
                      {{$t('profiling.queueFullRatio')}}{{connectQueueChart.queueSummary.full_queue}}</div>
                  </div>
                  <div id="connect-queue"
                       class="chart"></div>
                </template>
                <div class="image-noData"
                     v-if="connectQueueChart.noData">
                  <div>
                    <img :src="require('@/assets/images/nodata.png')"
                         alt="" />
                  </div>
                  <p>{{$t("public.noData")}}</p>
                </div>
              </div>
              <div class="chart-wrap"
                   :class="{highlight:selected==='data_queue'}">
                <div class="title">{{$t('profiling.dataQueue')}}</div>
                <template v-if="!dataQueueChart.noData">
                  <div class="data-tips">
                    <div v-if="dataQueueChart.queueSummary.empty_queue!==undefined">
                      {{$t('profiling.queueEmptyRatio')}}{{dataQueueChart.queueSummary.empty_queue}}</div>
                    <div v-if="dataQueueChart.queueSummary.full_queue!==undefined">
                      {{$t('profiling.queueFullRatio')}}{{dataQueueChart.queueSummary.full_queue}}</div>
                  </div>
                  <div id="data-queue"
                       class="chart"></div>
                </template>
                <div class="image-noData"
                     v-if="dataQueueChart.noData">
                  <div>
                    <img :src="require('@/assets/images/nodata.png')"
                         alt="" />
                  </div>
                  <p>{{$t("public.noData")}}</p>
                </div>
              </div>
            </div>
          </div>
          <div class="queue-step-wrap">
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
                     v-if="deviceQueueOpChart.noData">
                  <div>
                    <img :src="require('@/assets/images/nodata.png')"
                         alt="" />
                  </div>
                  <p>{{$t("public.noData")}}</p>
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
                     v-if="getNextChart.noData">
                  <div>
                    <img :src="require('@/assets/images/nodata.png')"
                         alt="" />
                  </div>
                  <p>{{$t("public.noData")}}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="image-noData"
             v-if="(connectQueueChart.noData && dataQueueChart.noData &&
                deviceQueueOpChart && getNextChart.getNextChart)">
          <div>
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
          </div>
          <p>{{$t("public.noData")}}</p>
        </div>
      </el-tab-pane>
      <el-tab-pane :label="$t('profiling.pipeline')"
                   name="pipeLine">
        <div class="pipeline-wrap"
             v-show="pipeData">
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
                    {{current_op.num_workers}}</div>
                  <div class="item"><span>{{parent_op.name}} ID:</span>{{parent_op.op_id}}</div>
                  <div class="item"><span>{{parent_op.name}} type:</span>{{parent_op.op_type}}</div>
                  <div class="item">
                    <span>{{parent_op.name}} {{$t('profiling.workersNum')}}:</span>
                    {{parent_op.num_workers}}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="image-noData"
             v-if="!pipeData">
          <div>
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
          </div>
          <p>{{$t("public.noData")}}</p>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
<script>
import echarts from 'echarts';
import RequestService from '../../services/request-service';
import {select, selectAll, zoom} from 'd3';
import 'd3-graphviz';
const d3 = {select, selectAll, zoom};
export default {
  props: {},
  data() {
    return {
      dir: '',
      currentCard: '',
      connectQueueChart: {
        id: 'connect-queue',
        chartDom: null,
        data: [],
        queueSummary: {},
        advise: '',
        type: 0,
        params: 'device_queue',
        noData: false,
      },
      dataQueueChart: {
        id: 'data-queue',
        chartDom: null,
        data: [],
        queueSummary: {},
        advise: '',
        type: 0,
        params: 'get_next',
        noData: false,
      },
      deviceQueueOpChart: {
        id: 'device_queue_op',
        chartDom: null,
        data: [],
        timeSummary: {},
        type: 1,
        params: 'device_queue',
        noData: false,
      },
      getNextChart: {
        id: 'get_next',
        chartDom: null,
        data: [],
        timeSummary: {},
        type: 1,
        params: 'get_next',
        noData: false,
      },
      processSummary: {
        noData: true,
        count: 6,
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
        id: 'average-rate',
        chartDom: null,
      },
      queueDeepChart: {
        id: 'queue-deep',
        chartDom: null,
      },
      current_op: {},
      parent_op: {},
      pipeData: true,
      allGraphData: {},
      graphviz: null,
      totalMemory: 16777216 * 2, // Memory size of the graph plug-in
      scaleRange: [0.0001, 10000], // graph zooms in and zooms out.
      initQueue: '',
      trainId: '',
      selected: '',
    };
  },
  watch: {
    '$parent.curDashboardInfo': {
      handler(newValue, oldValue) {
        if (newValue.curCardNum || newValue.curCardNum === 0) {
          this.dir = newValue.query.dir;
          this.trainId = newValue.query.id;
          this.currentCard = newValue.curCardNum;
          if (this.trainId) {
            document.title =
              `${decodeURIComponent(this.trainId)}` +
              `-${this.$t('profiling.mindData')}-MindInsight`;
          } else {
            document.title = `${this.$t('profiling.mindData')}-MindInsight`;
          }
          if (this.activeName === 'queueInfo') {
            this.init();
          } else {
            this.queryAverageRate();
          }
        }
      },
      deep: true,
      immediate: true,
    },
  },
  computed: {},
  mounted() {
    window.addEventListener('resize', this.resizeCallback, false);
    setTimeout(() => {
      this.$bus.$on('collapse', this.resizeCallback);
    }, 500);
  },
  methods: {
    handleClick() {
      if (this.activeName === 'pipeLine') {
        if (!Object.keys(this.allGraphData).length) {
          this.$nextTick(() => {
            this.queryAverageRate();
          });
        }
      }
      this.resizeCallback();
    },
    init() {
      this.queryQueueInfo(this.connectQueueChart);
      this.queryQueueInfo(this.dataQueueChart);
      this.queryMinddataOp(this.deviceQueueOpChart);
      this.queryMinddataOp(this.getNextChart);
      this.queryProcessSummary();
    },
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
          setTimeout(() => {
            this[val].chartDom.resize();
          }, 200);
        }
      });
    },
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
              const result = res.data;
              chart.data = result.info;
              if (result.summary) {
                chart.timeSummary = result.summary.time_summary || {};
                Object.keys(chart.timeSummary).forEach((val) => {
                  chart.timeSummary[val] = parseFloat(
                      chart.timeSummary[val],
                  ).toFixed(3);
                });
              }
              chart.advise = result.advise;
              if (result.size > 0) {
                this.setOption(chart);
                chart.noData = false;
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
            chart.noData = true;
          },
      );
    },
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
              const result = res.data;
              chart.data = result.info;
              if (result.summary) {
                chart.queueSummary = result.summary.queue_summary || {};
              }
              chart.advise = result.advise;
              if (result.size > 0) {
                this.setOption(chart, result.size);
                chart.noData = false;
              } else {
                if (chart.chartDom) {
                  chart.chartDom.clear();
                }
                chart.noData = true;
              }
            }
          },
          (err) => {
            chart.noData = true;
            if (chart.chartDom) {
              chart.chartDom.clear();
            }
          },
      );
    },
    setOption(chart, size) {
      const myChart = echarts.init(document.getElementById(chart.id));
      const option = {
        title: {
          text: '',
        },
        tooltip: {
          trigger: 'axis',
        },
        toolbox: {
          show: true,
        },
        xAxis: {
          name: 'step',
          data: [],
          max: size,
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
          startValue: 0,
          bottom: 0,
        },
        {
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
    queryProcessSummary() {
      const params = {
        profile: this.dir,
        device_id: this.currentCard,
        train_id: this.trainId,
      };
      RequestService.queryProcessSummary(params).then(
          (res) => {
            if (res && res.data) {
              const data = JSON.parse(JSON.stringify(res.data));
              this.processSummary.count = Object.keys(data).length;

              this.dealProcess(data);
            } else {
              this.dealProcess(null);
            }
          },
          (error) => {
            this.dealProcess(null);
          },
      );
    },
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

      if (data) {
        if (data.device_queue_info && data.device_queue_info.summary) {
          this.processSummary.device = {
            empty: data.device_queue_info.summary.empty_batch_count,
            full: data.device_queue_info.summary.full_batch_count,
            total: data.device_queue_info.summary.total_batch,
          };
        }
        if (data.get_next_queue_info && data.get_next_queue_info.summary) {
          this.processSummary.get_next = {
            empty: data.get_next_queue_info.summary.empty_batch_count,
            full: data.get_next_queue_info.summary.full_batch_count,
            total: data.get_next_queue_info.summary.total_batch,
          };
        }
        this.processSummary.noData = false;
      }
    },
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
      RequestService.queryOpQueue(params).then(
          (res) => {
            if (res && res.data) {
              this.removeGraph();
              const data = JSON.parse(JSON.stringify(res.data));
              this.dealPipeLineData(data);

              this.pipeData = !!(res.data.object && res.data.object.length);
              if (
                res.data.object &&
              res.data.object.length &&
              res.data.col_name
              ) {
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
                    {
                      orient: 'vertical',
                      right: 10,
                    },
                    {
                      type: 'inside',
                      orient: 'vertical',
                      right: 10,
                    },
                  ],
                };
                const echart = echarts.init(
                    document.getElementById(this.averageRateChart.id),
                );
                echart.setOption(option);
                this.averageRateChart.chartDom = echart;
              }
            }
          },
          () => {
            this.pipeData = false;
            this.removeGraph();
          },
      );
    },
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
          const echart = echarts.init(
              document.getElementById(this.queueDeepChart.id),
          );
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
            },
            xAxis: {
              name: `${this.$t('profiling.sampleInterval')}/${
                data.sample_interval
              }ms`,
              data: dataY.map((val, index) => index + 1),
              max: dataY.length,
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
                startValue: 0,
                bottom: 10,
              },
              {
                type: 'inside',
                bottom: 10,
              },
            ],
          };
          echart.setOption(option);
          this.queueDeepChart.chartDom = echart;
        }
      });
    },
    highlight(key) {
      const domList = document.querySelectorAll('.md-top *[clickKey]');
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
     * @return {String} dot string for packing graph data
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
     * @param {String} dot dot statement encapsulated in graph data
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
      d3.select('#graph')
          .selectAll('.operator>title')
          .remove();

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
            `${this.$t(
                'profiling.averageCapacity',
            )}:${data.output_queue_average_size || 0}\n` +
            `${this.$t('profiling.totalCapacity')}:${data.output_queue_length ||
              0}`;
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
            pointer.start.x = event.x;
            pointer.start.y = event.y;
          })
          .on('zoom', () => {
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
              const wheelDelta = event.wheelDelta;
              const rate = Math.abs(wheelDelta / 100);
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
     * @return {Object} transform data of a node
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
    window.removeEventListener('resize', this.resizeCallback);
    this.$bus.$off('collapse');
  },
};
</script>
<style lang="scss">
.md-wrap {
  height: 100%;
  background: #fff;
  padding: 0 32px;
  .title {
    font-size: 16px;
    font-weight: bold;
    text-align: left;
  }
  .el-tabs.el-tabs--top {
    height: calc(100% - 22px);
  }
  .el-tabs__content {
    height: calc(100% - 54px);
    & > .el-tab-pane {
      height: 100%;
    }
  }
  .md-top {
    height: 20%;
    font-size: 0;
    display: flex;
    align-items: baseline;
    .cell-container {
      width: 20%;
      cursor: pointer;
      padding: 20px 0;
      border: 2px solid transparent;
      .title {
        font-size: 14px;
        line-height: 20px;
        padding: 0 0 0 20px;
        font-weight: bold;
      }
      .content {
        padding: 10px 20px 0px 20px;
        font-size: 12px;
      }
    }
    .data-process {
      background-color: #e3f8eb;
      cursor: default;
      .title {
        border-left: 2px solid #00a5a7;
      }
    }
    .device_queue_op {
      background-color: #e1f2ff;
      .title {
        border-left: 2px solid #6cbfff;
      }
    }
    .get-next {
      background-color: #fef4dd;
      .title {
        border-left: 2px solid #fdca5a;
      }
    }
    .queue-container {
      width: 20%;
      position: relative;
      .img {
        width: 100%;
        height: 24px;
        margin-top: 30px;
        .edge {
          width: calc(50% - 40px);
          display: inline-block;
          vertical-align: middle;
          img {
            width: 100%;
          }
        }
        .icon {
          padding: 0 20px;
          display: inline-block;
          vertical-align: middle;
          img {
            padding: 3px;
            border: 2px solid transparent;
            cursor: pointer;
          }
        }
      }

      .title {
        text-align: center;
        font-size: 14px;
        margin-top: 10px;
        font-weight: bold;
      }
      .description {
        position: absolute;
        font-size: 12px;
        line-height: 12px;
        white-space: nowrap;
        overflow: hidden;
        width: 100%;
        text-align: center;
        .item {
          font-size: 12px;
          line-height: 16px;
          white-space: normal;
          .num {
            color: #07a695;
          }
        }
      }
    }
    .selected {
      border: 2px solid #3399ff !important;
    }
  }
  .md-bottom {
    height: 80%;
    .queue-step-wrap {
      &:first-child {
        height: 50%;
      }
      &:last-child {
        height: 50%;
      }
      & > .title {
        margin-bottom: 15px;
        font-weight: bold;
        font-size: 15px;
      }
      .chart-content {
        height: calc(100% - 30px);
        .chart-wrap {
          float: left;
          width: calc(50% - 12px);
          height: calc(100% - 10px);
          border-radius: 4px;
          overflow-y: auto;
          border: 1px solid #eee;
          &:first-child {
            margin-right: 20px;
          }
          .title {
            font-size: 13px;
            padding: 10px;
            font-weight: bold;
          }
          .data-tips {
            color: #999;
            padding: 0 0 0 10px;
            & > div {
              display: inline-block;
              margin-right: 10px;
            }
          }
          .chart {
            height: calc(100% - 70px);
            min-height: 150px;
          }
        }
        .chart-wrap.highlight {
          border-color: #3399ff;
        }
      }
      .chart-content.second {
        height: calc(100% - 25px);
      }
    }
  }
  .pipeline-wrap {
    height: 100%;
    .pipeline-top {
      height: 35%;
      .pipeline-top-title {
        font-size: 15px;
        font-weight: bold;
      }
      .average-rate-wrap {
        overflow-y: auto;
        height: calc(100% - 20px);
        #average-rate {
          height: 100%;
          min-height: 180px;
        }
      }
    }
    .pipeline-middle {
      height: 30%;
      .pipeline-middle-title {
        font-size: 15px;
        font-weight: bold;
      }
      .operator-graph {
        height: calc(100% - 20px);
        #graph {
          width: 100%;
          height: 100%;
          background-color: #f7faff;
          #graph0 > polygon {
            fill: transparent;
          }
          .node.queue {
            cursor: pointer;
          }
          .operator {
            path {
              stroke: #e6ebf5;
              fill: #e6ebf5;
            }
          }
          .selected {
            path,
            polygon {
              stroke: red;
            }
          }
          .edge {
            path,
            polygon {
              stroke: #e6ebf5;
              fill: #e6ebf5;
            }
          }
        }
      }
    }
    .pipeline-bottom {
      height: 35%;
      .queue-deep-wrap {
        height: 100%;
        background: #fafbfc;
        & > div {
          float: left;
          height: 100%;
        }
        .left {
          width: calc(60% - 20px);
          overflow-y: auto;
          height: 100%;
          border-right: 1px dashed #ccc;
          padding-right: 20px;
          margin-right: 20px;
          #queue-deep {
            height: 100%;
            width: 100%;
            min-height: 220px;
          }
        }
        .right {
          width: 40%;
          .title {
            font-size: 13px;
            margin-top: 7px;
          }
          .item-wrap {
            padding-top: 10px;
            height: calc(100% - 26px);
            overflow-y: auto;
            .item {
              margin-top: 10px;
              & > span {
                color: #757b88;
                display: inline-block;
                width: 50%;
              }
            }
          }
        }
      }
    }
  }
  .image-noData {
    width: 100%;
    height: calc(100% - 37px);
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
    p {
      font-size: 16px;
      padding-top: 10px;
    }
  }
}
</style>

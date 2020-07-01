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
  <div class="pro-router-wrap">
    <div class="pro-router-left">
      <div class="step-trace">
        <div class="title-wrap">
          <div class="title">{{ $t('profiling.stepTrace') }}</div>
          <div class="view-detail">
            <button @click="viewDetail('step-trace')"
                    :disabled="svg.noData && svg.data.length === 0"
                    :class="{disabled:svg.noData && svg.data.length === 0}">{{ $t('profiling.viewDetail') }}
              <i class="el-icon-d-arrow-right"></i></button>
          </div>
          <div class="tip-icon">
            <el-tooltip placement="bottom"
                        effect="light">
              <div slot="content"
                   class="tooltip-container">
                <div class="font-size-style">{{$t("profiling.features")}}</div>
                <div>{{$t('profiling.iterationInfo')}}</div>
                <div>
                  <span class="font-style">{{$t('profiling.queueInfo')}}&nbsp;</span>
                  <span>{{$t('profiling.iterationGapInfo')}}</span>
                </div>
                <div>
                  <span class="font-style">{{$t('profiling.fpbpTitle')}}&nbsp;</span>
                  <span>{{$t('profiling.fpbpInfo')}}</span>
                </div>
                <div>
                  <span class="font-style">{{$t('profiling.iterativeTailingTitle')}}&nbsp;</span>
                  <span>{{$t('profiling.iterativeTailingInfo')}}</span>
                </div>
                <br />
                <div class="font-size-style">{{$t('profiling.statistics')}}</div>
                <div>{{$t('profiling.totalTime')}}
                  <span>{{totalTime}}{{$t('profiling.millisecond')}}</span>
                </div>
                <div>{{$t('profiling.totalSteps')}}<span>{{totalSteps}}</span></div>
                <div>{{$t('profiling.iterationGapTimeRatio')}}<span>{{iteration_interval_percent}}</span></div>
                <div>{{$t('profiling.fpbpTimeRatio')}}<span>{{fp_and_bp_percent}}</span></div>
                <div>{{$t('profiling.iterativeTailingTimeRatio')}}<span>{{tail_percent}}</span></div>
              </div>
              <i class="el-icon-info"></i>
            </el-tooltip>
          </div>
        </div>
        <div class="trace-container">
          <div id="trace"
               class="training-trace">
            <svg version="1.1"
                 xmlns="http://www.w3.org/2000/svg"
                 height="100%"
                 width="100%">
              <defs>
                <marker id="marker_end"
                        refX="5"
                        refY="4"
                        markerWidth="10"
                        markerHeight="8"
                        orient="auto">
                  <path d="M1,1 L1,7 L9,4 z"
                        fill="#E6EBF5"
                        stroke="#E6EBF5"></path>
                </marker>
                <marker id="marker_start"
                        refX="5"
                        refY="4"
                        markerWidth="10"
                        markerHeight="8"
                        orient="auto">
                  <path d="M9,1 L9,7 L1,4 z"
                        fill="#E6EBF5"
                        stroke="#E6EBF5"></path>
                </marker>
              </defs>
            </svg>
          </div>
          <div class="image-noData"
               v-if="svg.noData">
            <div>
              <img :src="require('@/assets/images/nodata.png')"
                   alt="" />
            </div>
            <p>{{$t("public.noData")}}</p>
          </div>
        </div>
      </div>
      <div class="minddata">
        <div class="title-wrap">
          <div class="title">{{ $t('profiling.mindData') }}</div>
          <div class="view-detail">
            <button @click="viewDetail('data-process')"
                    :disabled="processSummary.noData"
                    :class="{disabled:processSummary.noData}">
              {{ $t('profiling.viewDetail') }}
              <i class="el-icon-d-arrow-right"></i></button>
          </div>
          <div class="tip-icon">
            <el-tooltip placement="bottom"
                        effect="light">
              <div slot="content"
                   class="tooltip-container">
                <div class="font-size-style">{{$t("profiling.features")}}</div>
                <div>{{$t('profiling.dataProcess')}}</div>
                <div>{{$t('profiling.dataProcessInfo')}}</div>
                <div>{{$t('profiling.analysisOne')}}</div>
                <div>{{$t('profiling.analysisTwo')}}</div>
                <div v-show="deviceInfoShow || queueInfoShow">{{$t('profiling.higherAnalysis')}}</div>
                <br />
                <div v-show="deviceInfoShow || queueInfoShow"
                     class="font-size-style">{{$t('profiling.statistics')}}</div>
                <div v-show="queueInfoShow">{{$t('profiling.chipInfo')}}
                  <span>{{queueInfoEmptyNum}} / {{queueInfoTotalNum}}</span>
                </div>
                <div v-show="deviceInfoShow">
                  <div>{{$t('profiling.hostIsEmpty')}}
                    <span>{{deviceInfoEmptyNum}} / {{deviceInfoTotalNum}}</span>
                  </div>
                  <div>{{$t('profiling.hostIsFull')}}
                    <span>{{deviceInfoFullNum}} / {{deviceInfoTotalNum}}</span>
                  </div>
                </div>
              </div>
              <i class="el-icon-info"></i>
            </el-tooltip>
          </div>
        </div>
        <div class="pipeline-container"
             v-show="!processSummary.noData">
          <div class="cell-container data-process">
            <div class="title">
              {{$t('profiling.pipeline')}}
            </div>
          </div>

          <div class="queue-container">
            <div class="img">
              <div class="edge">
                <img src="@/assets/images/data-flow.png"
                     alt="" />
              </div>
              <div class="icon">
                <img src="@/assets/images/queue.svg"
                     alt=""
                     clickKey="connector_queue" />
              </div>
              <div class="edge">
                <img src="@/assets/images/data-flow.png"
                     alt="" />
              </div>
            </div>
            <div class="title">{{$t('profiling.connectorQuene')}}</div>
            <div class="description">
              <div class="line"></div>
              <div class="item"
                   v-if="processSummary.device.empty || processSummary.device.empty === 0">
                {{$t('profiling.queueTip2')}}
                <span class="num">
                  {{processSummary.device.empty}} / {{processSummary.device.total}}
                </span>
              </div>
              <div class="item"
                   v-if="processSummary.device.full || processSummary.device.full === 0">
                {{$t('profiling.queueTip1')}}
                <span class="num">
                  {{processSummary.device.full}} / {{processSummary.device.total}}
                </span>
              </div>
            </div>
          </div>

          <div class="cell-container device_queue_op"
               clickKey="device_queue_op">
            <div class="title">
              {{$t('profiling.deviceQueueOp')}}
            </div>
          </div>

          <div class="queue-container"
               v-if="processSummary.count === processSummary.maxCount">
            <div class="img">
              <div class="edge">
                <img src="@/assets/images/data-flow.png"
                     alt="" />
              </div>
              <div class="icon">
                <img src="@/assets/images/queue.svg"
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
              <div class="line"></div>
              <div class="item"
                   v-if="processSummary.get_next.empty || processSummary.get_next.empty === 0">
                {{$t('profiling.queueTip2')}}
                <span class="num">
                  {{processSummary.get_next.empty}} / {{processSummary.get_next.total}}
                </span>
              </div>
              <div class="item"
                   v-if="processSummary.get_next.full || processSummary.get_next.full === 0">
                {{$t('profiling.queueTip1')}}
                <span class="num">
                  {{processSummary.get_next.full}} / {{processSummary.get_next.total}}
                </span>
              </div>
            </div>
          </div>

          <div class="cell-container get-next"
               clickKey="get_next"
               v-if="processSummary.count === processSummary.maxCount">
            <div class="title">
              {{$t('profiling.getData')}}
            </div>
          </div>
        </div>
        <div class="image-noData"
             v-if="processSummary.noData">
          <div>
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
          </div>
          <p>{{$t("public.noData")}}</p>
        </div>
      </div>
    </div>
    <div class="pro-router-right">
      <div class="op-time-consume">
        <div class="title-wrap">
          <div class="title">{{ $t('profiling.rankOfOperator') }}</div>
          <div class="view-detail">
            <button @click="viewDetail('operator')"
                    :disabled="pieChart.noData && pieChart.data.length === 0"
                    :class="{disabled:pieChart.noData && pieChart.data.length === 0}">{{ $t('profiling.viewDetail') }}
              <i class="el-icon-d-arrow-right"></i></button>
          </div>
        </div>
        <div class="image-noData"
             v-if="pieChart.noData && pieChart.data.length === 0">
          <div>
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
          </div>
          <p>{{$t("public.noData")}}</p>
        </div>
        <div class="op-time-content">
          <div id="pieChart"
               class="pie-chart"
               v-if="pieChart.data.length"></div>
          <div class="time-list"
               v-if="pieChart.data.length">
            <ul>
              <li v-for="(item, index) in pieChart.topN"
                  :key="index"
                  class="item">
                <span class="index"
                      :style="{'background-color': pieChart.colorList[index]}">{{index + 1}}</span>
                <span class="name">{{item.name}}</span>
                <span class="num">{{item.frequency + $t('profiling.times')}}</span>
                <span class="time">
                  <span class="bar"
                        :style="{width: item.time / pieChart.topN[0].time * 100 + '%'}"></span>
                  <span class="value">{{item.time}}ms</span>
                </span>
              </li>
            </ul>
          </div>
        </div>
      </div>
      <div class="time-line">
        <div class="title-wrap">
          <div class="title">{{ $t('profiling.timeLine') }}</div>
          <div class="view-detail">
            <button @click="downloadPerfetto()"
                    :disabled="timeLine.waiting"
                    :class="{disabled:timeLine.waiting}">{{ $t('profiling.downloadTimeline') }}
            </button>
          </div>
          <div class="tip-icon">
            <el-tooltip placement="bottom"
                        effect="light">
              <div slot="content"
                   class="tooltip-container">
                <div class="font-size-style">{{$t("profiling.features")}}</div>
                <div class="font-style">{{$t("profiling.timelineTips.title1")}}</div>
                <div>{{$t("profiling.timelineTips.content11")}}</div>
                <div>{{$t("profiling.timelineTips.content12")}}</div>
                <div>{{$t("profiling.timelineTips.content13")}}</div>
                <br>
                <div class="font-style">{{$t("profiling.timelineTips.title2")}}</div>
                <div>{{$t("profiling.timelineTips.content21")}}</div>
                <div>{{$t("profiling.timelineTips.content22")}}</div>
                <div>{{$t("profiling.timelineTips.content23")}}</div>
                <br>
                <div class="font-style">{{$t("profiling.timelineTips.title3")}}</div>
                <div>{{$t("profiling.timelineTips.content31")}}</div>
                <div>{{$t("profiling.timelineTips.content32")}}</div>
              </div>
              <i class="el-icon-info"></i>
            </el-tooltip>
          </div>
        </div>
        <div class="timeline-info"
             v-if="!timelineInfo.noData">
          <div class="info-line">
            <span>{{$t('profiling.opTotalTime')}}</span><span>{{timelineInfo.totalTime}}ms</span>
          </div>
          <div class="info-line">
            <span>{{$t('profiling.streamNum')}}</span><span>{{timelineInfo.streamNum}}</span>
          </div>
          <div class="info-line">
            <span>{{$t('profiling.opNum')}}</span><span>{{timelineInfo.opNum}}</span></div>
          <div class="info-line">
            <span>{{$t('profiling.opTimes')}}</span><span>{{timelineInfo.opTimes + $t('profiling.times')}}</span>
          </div>

        </div>
        <div class="image-noData"
             v-if="timelineInfo.noData">
          <div>
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
          </div>
          <p>{{$t("public.noData")}}</p>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import echarts from 'echarts';
import RequestService from '../../services/request-service';
import CommonProperty from '../../common/common-property';
export default {
  data() {
    return {
      fp_and_bp_percent: '--',
      iteration_interval_percent: '--',
      totalSteps: '--',
      totalTime: '--',
      tail_percent: '--',
      queueInfoShow: false,
      deviceInfoShow: false,
      queueInfoEmptyNum: '--',
      queueInfoTotalNum: '--',
      deviceInfoEmptyNum: '--',
      deviceInfoTotalNum: '--',
      deviceInfoFullNum: '--',
      svg: {
        data: [],
        svgPadding: 20,
        totalWidth: 0,
        totalTime: 0,
        rowHeight: 60,
        markerPadding: 4,
        minRate: 0.05,
        namespaceURI: 'http://www.w3.org/2000/svg',
        resizeTimer: null,
        colorList: [
          ['#A6DD82', '#edf8e6'],
          ['#6CBFFF', '#e2f2ff'],
          ['#fa8e5b', '#fff4de'],
          ['#01a5a7', '#cceded'],
        ],
        colorIndex: 0,
        noData: false,
      },
      trainingJobId: this.$route.query.id,
      summaryPath: this.$route.query.dir,
      relativePath: this.$route.query.path,
      currentCard: '',
      pieChart: {
        chartDom: null,
        data: [],
        noData: false,
        topN: [],
        colorList: ['#6C92FA', '#6CBFFF', '#4EDED2', '#7ADFA0', '#A6DD82'],
      },
      timeLine: {
        data: null,
        waiting: true,
      },
      timelineInfo: {
        totalTime: 0,
        streamNum: 0,
        opNum: 0,
        opTimes: 0,
        noData: true,
      },
      processSummary: {
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
    };
  },
  mounted() {
    setTimeout(() => {
      this.$bus.$on('collapse', this.resizeTrace);
    }, 500);
  },
  watch: {
    '$parent.curDashboardInfo': {
      handler(newValue, oldValue) {
        if (newValue.curCardNum === '') {
          this.pieChart.noData = true;
          this.svg.noData = true;
        }
        if (newValue.query.dir && newValue.query.id && newValue.query.path) {
          this.summaryPath = newValue.query.dir;
          this.trainingJobId = newValue.query.id;
          this.relativePath = newValue.query.path;
          this.currentCard = newValue.curCardNum;
          if (this.trainingJobId) {
            document.title = `${decodeURIComponent(
                this.trainingJobId,
            )}-${this.$t('profiling.profilingDashboard')}
        -MindInsight`;
          } else {
            document.title = `${this.$t(
                'profiling.profilingDashboard',
            )}-MindInsight`;
          }
          this.init();
        }
      },
      deep: true,
      immediate: true,
    },
  },
  methods: {
    init() {
      this.queryTimeline();
      this.queryTrainingTrace();
      this.getProccessSummary();
      this.initPieChart();
      window.addEventListener('resize', this.resizeTrace, false);
    },
    getProccessSummary() {
      const params = {
        train_id: this.trainingJobId,
        profile: this.summaryPath,
        device_id: this.currentCard,
      };
      RequestService.queryProcessSummary(params).then((resp) => {
        if (resp && resp.data) {
          const data = JSON.parse(JSON.stringify(resp.data));
          this.processSummary.count = Object.keys(data).length;
          this.dealProcess(data);
          // Chip side
          if (resp.data.get_next_queue_info) {
            this.queueInfoShow = true;
            this.queueInfoEmptyNum =
              resp.data.get_next_queue_info.summary.empty_batch_count;
            this.queueInfoTotalNum =
              resp.data.get_next_queue_info.summary.total_batch;
          }
          // Host side
          if (resp.data.device_queue_info) {
            this.deviceInfoShow = true;
            this.deviceInfoEmptyNum =
              resp.data.device_queue_info.summary.empty_batch_count;
            this.deviceInfoTotalNum =
              resp.data.device_queue_info.summary.total_batch;
            this.deviceInfoFullNum =
              resp.data.device_queue_info.summary.full_batch_count;
          }
        } else {
          this.dealProcess(null);
        }
      });
    },
    viewDetail(path) {
      this.$router.push({
        path,
        query: {
          id: this.trainingJobId,
          dir: this.summaryPath,
          path: this.relativePath,
        },
      });
    },
    setPieOption() {
      const option = {};
      option.tooltip = {
        trigger: 'item',
        formatter: (params) => {
          return `${params.data.name}<br>${params.marker}${params.percent}%`;
        },
        confine: true,
        extraCssText: 'white-space:normal; word-break:break-word;',
      };
      option.series = [
        {
          type: 'pie',
          center: ['50%', '50%'],
          data: this.pieChart.data,
          radius: '80%',
          label: {
            normal: {
              show: false,
              positionL: 'inner',
            },
          },
          itemStyle: {
            normal: {
              color: function(params) {
                return CommonProperty.pieColorArr[params.dataIndex];
              },
            },
          },
        },
      ];
      this.$nextTick(() => {
        const dom = document.getElementById('pieChart');
        if (dom) {
          this.pieChart.chartDom = echarts.init(dom, null);
        } else {
          if (this.pieChart.chartDom) {
            this.pieChart.chartDom.clear();
          }
          return;
        }
        this.pieChart.chartDom.setOption(option, true);
        this.pieChart.chartDom.resize();
      }, 10);
    },
    initPieChart() {
      const params = {};
      params.params = {
        profile: this.summaryPath,
        train_id: this.trainingJobId,
      };
      params.body = {
        op_type: 'aicore_type',
        device_id: this.currentCard,
        filter_condition: {},
        sort_condition: {
          name: 'execution_time',
          type: 'descending',
        },
      };
      RequestService.getProfilerOpData(params)
          .then((res) => {
            if (res && res.data) {
              if (res.data.object) {
                this.pieChart.data = [];
                res.data.object.forEach((item) => {
                  if (this.pieChart.data && this.pieChart.data.length < 5) {
                    this.pieChart.data.push({
                      name: item[0],
                      value: item[1],
                      frequency: item[2],
                      percent: item[3],
                    });
                  } else {
                    if (!this.pieChart.data[5]) {
                      this.pieChart.data[5] = {
                        name: 'Other',
                        value: 0,
                        percent: 0,
                      };
                    }
                    this.pieChart.data[5].value += item[1];
                    this.pieChart.data[5].percent += item[3];
                  }
                });
                this.setPieOption();
                if (this.pieChart.data.length === 0) {
                  this.pieChart.noData = true;
                }
                this.pieChart.topN = this.pieChart.data
                    .slice(0, Math.min(this.pieChart.data.length, 5))
                    .map((i) => {
                      return {
                        name: i.name,
                        time: i.value,
                        frequency: i.frequency,
                      };
                    });
              }
            }
          })
          .catch(() => {
            this.pieChart.noData = true;
          });
    },
    queryTrainingTrace() {
      const params = {
        dir: this.relativePath,
        type: 0,
        device_id: this.currentCard,
      };
      RequestService.queryTrainingTrace(params).then(
          (res) => {
            if (
              res.data &&
            res.data.training_trace_graph &&
            res.data.training_trace_graph.length
            ) {
              this.svg.noData = false;
              document.querySelector('#trace').style.height = `${res.data
                  .training_trace_graph.length * this.svg.rowHeight}px`;
              this.svg.data = JSON.parse(
                  JSON.stringify(res.data.training_trace_graph),
              );
              this.removeTrace();
              setTimeout(() => {
                this.dealTraceData();
              }, 100);
              if (res.data.summary) {
                this.fp_and_bp_percent = res.data.summary.fp_and_bp_percent;
                this.iteration_interval_percent =
                res.data.summary.iteration_interval_percent;
                this.totalSteps = res.data.summary.total_steps;
                this.totalTime = res.data.summary.total_time;
                this.tail_percent = res.data.summary.tail_percent;
              } else {
                this.fp_and_bp_percent = '--';
                this.iteration_interval_percent = '--';
                this.totalSteps = '--';
                this.totalTime = '--';
                this.tail_percent = '--';
              }
            } else {
              document.querySelector('#trace').style.height = '0px';
              this.svg.noData = true;
              this.svg.data = [];
              this.removeTrace();
            }
          },
          (error) => {
            document.querySelector('#trace').style.height = '0px';
            this.svg.noData = true;
            this.svg.data = [];
            this.removeTrace();
          },
      );
    },

    dealTraceData() {
      const traceDom = document.querySelector('#trace');
      if (traceDom) {
        this.svg.totalWidth = traceDom.offsetWidth - this.svg.svgPadding * 2;

        if (this.svg.data[0] && this.svg.data[0].length) {
          const svg = traceDom.querySelector('svg');
          this.svg.totalTime = this.svg.data[0][0].duration;

          if (this.svg.totalTime) {
            this.svg.colorIndex = 0;
            const minTime = this.svg.minRate * this.svg.totalTime;

            this.svg.data.forEach((row, index) => {
              if (row && row.length) {
                const dashedLine = this.addDashedLine(index);
                svg.insertBefore(dashedLine, svg.querySelector('g'));

                row.forEach((i) => {
                  if (i.duration) {
                    if (i.name) {
                      const tempDom = this.createRect(i, index);
                      const tempStr = `g${
                        i.duration > minTime ? '' : '.arrow'
                      }`;
                      svg.insertBefore(tempDom, svg.querySelector(tempStr));
                    } else {
                      const tempDom = this.createArrow(i, index);
                      svg.appendChild(tempDom);
                    }
                  }
                });
              }
            });
          }
        } else {
          this.removeTrace();
        }
      }
    },
    addDashedLine(index) {
      const x1 = this.svg.svgPadding;
      const x2 = this.svg.svgPadding + this.svg.totalWidth;
      const y = index * this.svg.rowHeight;
      const line = document.createElementNS(this.svg.namespaceURI, 'line');
      line.setAttribute('x1', x1);
      line.setAttribute('y1', y);
      line.setAttribute('x2', x2);
      line.setAttribute('y2', y);
      line.setAttribute('style', 'stroke:#E2E2E2;stroke-width:1');
      line.setAttribute('stroke-dasharray', '5 5');
      const g = document.createElementNS(this.svg.namespaceURI, 'g');
      g.setAttribute('class', 'dashedLine');
      g.appendChild(line);
      return g;
    },
    createRect(data, rowIndex) {
      const color = this.svg.colorList[
        rowIndex > 1 ? 3 : this.svg.colorIndex++ % 4
      ];
      const height = 40;
      const width = (data.duration / this.svg.totalTime) * this.svg.totalWidth;
      const fontSize = 12;
      const normalRect = data.duration > this.svg.minRate * this.svg.totalTime;

      const x1 =
        (data.start / this.svg.totalTime) * this.svg.totalWidth +
        this.svg.svgPadding;
      const y1 =
        rowIndex * this.svg.rowHeight + (this.svg.rowHeight - height) / 2;

      const g = document.createElementNS(this.svg.namespaceURI, 'g');
      g.setAttribute('class', 'rect');
      const gChild = document.createElementNS(this.svg.namespaceURI, 'g');
      let name = '';
      switch (data.name) {
        case 'iteration_interval':
          name = this.$t('profiling.lterationGap');
          break;
        case 'fp_and_bp':
          name = this.$t('profiling.deviceQueueOpTip');
          break;
        case 'tail':
          name = this.$t('profiling.lterationTail');
          break;
        default:
          name = data.name;
          break;
      }

      const rect = document.createElementNS(this.svg.namespaceURI, 'rect');
      rect.setAttribute('x', x1);
      rect.setAttribute('y', y1);
      rect.setAttribute('height', height);
      rect.setAttribute('width', width);
      rect.setAttribute('style', `fill:${color[1]};stroke:${color[1]};`);

      const foreignObject = document.createElementNS(
          this.svg.namespaceURI,
          'foreignObject',
      );
      foreignObject.textContent = `${name}: ${data.duration.toFixed(4)}ms`;
      const textWidth = this.getTextWidth(foreignObject.textContent);

      foreignObject.setAttribute(
          'x',
        normalRect
          ? x1
          : Math.min(
              this.svg.svgPadding * 2 + this.svg.totalWidth - textWidth,
              Math.max(0, x1 + width / 2 - textWidth / 2),
          ),
      );

      foreignObject.setAttribute(
          'y',
          y1 + (height - fontSize) / 2 + (normalRect ? 0 : fontSize),
      );
      foreignObject.setAttribute('height', fontSize);
      foreignObject.setAttribute('width', width);
      foreignObject.setAttribute('style', `color:${color[0]}`);
      foreignObject.setAttribute(
          'class',
          `content${normalRect ? '' : ' content-mini'}`,
      );

      const title = document.createElementNS(this.svg.namespaceURI, 'title');
      title.textContent = `${name}: ${data.duration.toFixed(4)}ms`;

      gChild.appendChild(rect);
      gChild.appendChild(foreignObject);
      gChild.appendChild(title);
      g.appendChild(gChild);
      return g;
    },

    createArrow(data, rowIndex) {
      const width = (data.duration / this.svg.totalTime) * this.svg.totalWidth;
      const x1 =
        (data.start / this.svg.totalTime) * this.svg.totalWidth +
        this.svg.markerPadding +
        this.svg.svgPadding;
      const x2 = x1 + width - this.svg.markerPadding * 2;
      const y = rowIndex * this.svg.rowHeight + this.svg.rowHeight / 2;
      const g = document.createElementNS(this.svg.namespaceURI, 'g');
      g.setAttribute('class', 'arrow');

      const line = document.createElementNS(this.svg.namespaceURI, 'line');
      line.setAttribute('x1', x1);
      line.setAttribute('y1', y);
      line.setAttribute('x2', x2);
      line.setAttribute('y2', y);
      line.setAttribute('style', 'stroke:#E6EBF5;stroke-width:1');
      line.setAttribute('marker-end', 'url(#marker_end)');
      line.setAttribute('marker-start', 'url(#marker_start)');

      const text = document.createElementNS(this.svg.namespaceURI, 'text');
      text.textContent = `${
        rowIndex === 0 ? this.$t('profiling.approximateTime') : ''
      }${data.duration.toFixed(4)}ms`;
      const textWidth = this.getTextWidth(text.textContent);
      text.setAttribute(
          'x',
          Math.min(
              this.svg.svgPadding * 2 + this.svg.totalWidth - textWidth,
              Math.max(0, (x2 - x1) / 2 + x1 - textWidth / 2),
          ),
      );
      text.setAttribute('y', y - 6);
      text.setAttribute('font-size', 12);
      text.setAttribute('fill', '#6c7280');

      const startLine = document.createElementNS(this.svg.namespaceURI, 'line');
      startLine.setAttribute('x1', x1 - this.svg.markerPadding);
      startLine.setAttribute('y1', y - this.svg.rowHeight / 4);
      startLine.setAttribute('x2', x1 - this.svg.markerPadding);
      startLine.setAttribute('y2', y + this.svg.rowHeight / 4);
      startLine.setAttribute('style', 'stroke:#E6EBF5;stroke-width:1');
      g.appendChild(startLine);

      const endLine = document.createElementNS(this.svg.namespaceURI, 'line');
      endLine.setAttribute('x1', x1 + width - this.svg.markerPadding);
      endLine.setAttribute('y1', y - this.svg.rowHeight / 4);
      endLine.setAttribute('x2', x1 + width - this.svg.markerPadding);
      endLine.setAttribute('y2', y + this.svg.rowHeight / 4);
      endLine.setAttribute('style', 'stroke:#E6EBF5;stroke-width:1');
      g.appendChild(endLine);
      g.appendChild(line);
      g.appendChild(text);
      return g;
    },
    getTextWidth(text) {
      const body = document.querySelector('body');
      const temp = document.createElement('span');
      temp.style['font-size'] = '12px';
      temp.textContent = text;
      body.appendChild(temp);
      const textWidth = temp.offsetWidth;
      body.removeChild(temp);
      return textWidth;
    },
    removeTrace() {
      const svgDom = document.querySelector('#trace svg');
      if (svgDom) {
        const gDoms = svgDom.children;
        if (gDoms) {
          for (let i = 0; i < gDoms.length; i++) {
            if (gDoms[i].nodeName === 'g') {
              svgDom.removeChild(gDoms[i--]);
            }
          }
        }
      }
    },
    resizeTrace() {
      if (this.svg.resizeTimer) {
        clearTimeout(this.svg.resizeTimer);
      }
      this.svg.resizeTimer = setTimeout(() => {
        this.removeTrace();
        this.dealTraceData();
        this.svg.resizeTimer = null;
      }, 500);
    },
    stringToUint8Array(str) {
      const arr = [];
      for (let i = 0, strLen = str.length; i < strLen; i++) {
        arr.push(str.charCodeAt(i));
      }
      return new Uint8Array(arr);
    },
    queryTimeline() {
      const params = {
        dir: this.relativePath,
        device_id: this.currentCard,
      };
      RequestService.queryTimlineInfo(params)
          .then((res) => {
            if (res && res.data) {
              this.timelineInfo.noData = false;
              this.timelineInfo.totalTime = res.data.total_time.toFixed(4);
              this.timelineInfo.streamNum = res.data.num_of_streams;
              this.timelineInfo.opNum = res.data.num_of_ops;
              this.timelineInfo.opTimes = res.data.op_exe_times;
            } else {
              this.timelineInfo.noData = true;
            }
          })
          .catch(() => {
            this.timelineInfo.noData = true;
          });
      this.timeLine.waiting = true;
      RequestService.queryTimeline(params)
          .then((res) => {
            if (res && res.data && res.data.length) {
              this.timeLine.data = this.stringToUint8Array(
                  JSON.stringify(res.data),
              );
              this.timeLine.waiting = false;
            }
          })
          .catch(() => {});
    },
    downloadPerfetto() {
      const downloadLink = document.createElement('a');
      downloadLink.download = this.getDocName();
      downloadLink.style.display = 'none';
      const blob = new Blob([this.timeLine.data]);
      downloadLink.href = URL.createObjectURL(blob);
      document.body.appendChild(downloadLink);
      downloadLink.click();
      document.body.removeChild(downloadLink);
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

      if (data && Object.keys(data).length) {
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
    getDocName() {
      const dealNumber = (value) => {
        const prefix = value < 10 ? '0' : '';
        return prefix + value;
      };
      const date = new Date();
      const year = date.getFullYear();
      const mouth = dealNumber(date.getMonth() + 1);
      const day = dealNumber(date.getDate());
      const hour = dealNumber(date.getHours());
      const minute = dealNumber(date.getMinutes());
      const second = dealNumber(date.getSeconds());
      const millisecond = date.getMilliseconds();
      const timestamp = `${year}${mouth}${day}${hour}${minute}${second}${millisecond}`;
      return `timeline_${this.trainingJobId}_${this.currentCard}_${timestamp}.json`;
    },
  },
  destroyed() {
    window.removeEventListener('resize', this.resizeTrace, false);
    this.$bus.$off('collapse');
  },
};
</script>
<style lang="scss">
.el-tooltip-popper {
  max-width: 500px;
}
.tooltip-container {
  line-height: 20px;
  padding: 10px;
  .font-style {
    font-weight: bold;
  }
  .font-size-style {
    font-weight: bold;
    font-size: 16px;
  }
}
.pro-router-wrap {
  height: 100%;
  & > div {
    float: left;
    height: 100%;
    & > div {
      border: 1px solid #eee;
      border-radius: 4px;
    }
    .title-wrap {
      padding: 15px;
      .title {
        float: left;
        font-weight: bold;
        font-size: 16px;
      }
      .tip-icon {
        float: right;
        margin-right: 10px;
        font-size: 20px;
        color: #6c7280;
        .el-icon-warning {
          cursor: pointer;
          &:hover::before {
            color: #00a5a7;
          }
        }
      }
      .view-detail {
        float: right;
        cursor: pointer;
        color: #00a5a7;
        font-size: 12px;
        height: 24px;
        line-height: 24px;
        a {
          color: #00a5a7 !important;
          padding-right: 6px;
        }
        button {
          color: #00a5a7;
          border: none;
          background-color: #fff;
          cursor: pointer;
        }
        button.disabled {
          cursor: not-allowed;
          color: #c0c4cc;
        }
      }
      &::after {
        content: '';
        clear: both;
        display: block;
      }
    }
    .coming-soon-content {
      height: calc(100% - 50px);
      position: relative;
      .coming-soon-container {
        text-align: center;
        position: absolute;
        top: 50%;
        left: 50%;
        border-radius: 5px;
        -webkit-transform: translate(-50%, -50%);
        -moz-transform: translate(-50%, -50%);
        transform: translate(-50%, -50%);
      }
      .coming-soon-text {
        font-size: 16px;
      }
    }
  }
  .pro-router-left {
    width: calc(100% - 400px);
    padding-right: 15px;
    .step-trace {
      height: 45%;
      margin-bottom: 15px;
      .trace-container {
        width: 100%;
        height: calc(100% - 50px);
        overflow: auto;
        .training-trace {
          position: relative;
          height: 0;
          .content {
            overflow: hidden;
            text-align: center;
            text-overflow: ellipsis;
            white-space: nowrap;
            font-size: 12px;
            line-height: 12px;
          }
          .content-mini {
            overflow: visible;
          }
        }
      }
    }
    .minddata {
      height: calc(55% - 15px);
      .pipeline-container {
        width: 100%;
        padding: 20px 20px;
        height: calc(100% - 52px);
        display: flex;
        font-size: 0;
        align-items: baseline;
        .cell-container {
          width: 20%;
          padding: 20px 0;
          border: 2px solid transparent;
          .title {
            font-size: 14px;
            line-height: 20px;
            padding: 0 0 0 20px;
            font-weight: bold;
          }
        }
        .data-process {
          background-color: #e3f8eb;
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
            .line {
              width: 1px;
              height: 40px;
              margin: 20px 0;
              border-left: 1px solid #979797;
              display: inline-block;
            }
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
      }
    }
  }
  .pro-router-right {
    width: 400px;
    .op-time-consume {
      height: calc(60% - 15px);
      margin-bottom: 15px;
      .time-list {
        height: calc(40% - 52px);
        .item {
          height: 25px;
          line-height: 25px;
          padding: 0 20px;
          & > span {
            display: inline-block;
            height: 100%;
            vertical-align: middle;
          }
          .index {
            color: white;
            background-color: rgb(108, 146, 250);
            width: 20px;
            height: 20px;
            border-radius: 20px;
            text-align: center;
            vertical-align: middle;
            line-height: 20px;
          }
          .name {
            margin-left: 10px;
            width: calc(50% - 30px);
            text-overflow: ellipsis;
            overflow: hidden;
          }
          .num {
            width: 20%;
          }
          .time {
            width: 30%;
            position: relative;
            span {
              display: inline-block;
              position: absolute;
              left: 0;
              height: 20px;
            }
            .bar {
              background-color: #cceded;
              top: 2px;
            }
            .value {
              line-height: 25px;
              height: 25px;
            }
          }
        }
      }
    }
    .time-line {
      height: 40%;
      overflow: hidden;
      .timeline-info {
        width: 100%;
        height: calc(100% - 54px);
        padding-left: 36px;
      }
      .info-line {
        line-height: 30px;
      }
    }
  }
  .op-time-content {
    height: calc(100% - 54px);
    overflow: auto;
  }
  .pie-chart {
    width: 100%;
    height: 260px;
    overflow: hidden;
  }
  .image-noData {
    width: 100%;
    height: calc(100% - 52px);
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

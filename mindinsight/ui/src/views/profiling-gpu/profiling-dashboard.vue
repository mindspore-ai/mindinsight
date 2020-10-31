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
      <!-- Timeline display area -->
      <div class="step-trace">
        <div class="title-wrap">
          <div class="title">{{ $t('profiling.stepTrace') }}</div>
        </div>
        <!-- Timeline SVG container -->
        <div class="trace-container">
          <div class="image-noData">
            <div>
              <img :src="require('@/assets/images/coming-soon.png')"
                   alt="" />
            </div>
            <p>{{$t("public.stayTuned")}}</p>
          </div>
        </div>
      </div>
      <!-- Process summary display area -->
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
               <div>{{$t('profilingGPU.dataProcess')}}</div>
                <div>{{$t('profilingGPU.dataProcessInfo')}}</div>
                <div>{{$t('profilingGPU.analysisOne')}}</div>
                <div>{{$t('profilingGPU.analysisTwo')}}</div>
                <div v-show="deviceInfoShow || queueInfoShow">{{$t('profiling.higherAnalysis')}}</div>
                <br />
                <div v-show="deviceInfoShow || queueInfoShow"
                     class="font-size-style">{{$t('profiling.statistics')}}</div>
                <div v-show="queueInfoShow">{{$t('profilingGPU.chipInfo')}}
                  <span>{{processSummary.get_next.empty}} / {{processSummary.get_next.total}}</span>
                </div>
                <div v-show="deviceInfoShow">
                  <div>{{$t('profiling.hostIsEmpty')}}
                    <span>{{processSummary.device.empty}} / {{processSummary.device.total}}</span>
                  </div>
                  <div>{{$t('profiling.hostIsFull')}}
                    <span>{{processSummary.device.full}} / {{processSummary.device.total}}</span>
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
          <p v-show="!processSummary.initOver">{{$t("public.dataLoading")}}</p>
          <p v-show="processSummary.initOver">{{$t("public.noData")}}</p>
        </div>
      </div>
    </div>
    <!-- Operator information display area -->
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
             v-if="pieChart.noData">
          <div>
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
          </div>
          <p v-show="!pieChart.initOver">{{$t("public.dataLoading")}}</p>
          <p v-show="pieChart.initOver">{{$t("public.noData")}}</p>
        </div>

        <div class="op-time-content">
          <div id="pieChart"
               class="pie-chart"
               v-if="pieChart.data.length"></div>
          <!-- Operator time consumption top5 -->
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
                  <span class="value">{{item.time + $t('profiling.gpuunit')}}</span>
                </span>
              </li>
            </ul>
          </div>
        </div>
      </div>
      <!-- Time line display area -->
      <div class="time-line">
        <div class="title-wrap">
          <div class="title">{{ $t('profiling.timeLine') }}</div>
          <div class="view-detail">
            <button @click="downloadTimelineFile()"
                    v-show="!timeLine.waiting"
                    :disabled="timeLine.disable"
                    :class="{disabled:timeLine.disable}">{{ $t('profiling.downloadTimeline') }}
            </button>
            <div class="el-icon-loading loading-icon"
                 v-show="timeLine.waiting"></div>
          </div>
          <div class="tip-icon">
            <el-tooltip placement="bottom"
                        effect="light">
              <div slot="content"
                   class="tooltip-container">
                <div class="font-size-style">{{$t("profiling.features")}}</div>
                <div class="font-style">{{$t("profiling.timelineTips.title1")}}</div>
                <div>{{$t("profiling.timelineTips.content12")}}</div>
                <div>{{$t("profiling.timelineTips.content13")}}</div>
                <br>
                <div class="font-style">{{$t("profiling.timelineTips.title2")}}</div>
                <div>
                  {{$t("profiling.timelineTips.content21.part1")}}
                  <b>{{$t("profiling.timelineTips.content21.part2")}}</b>
                  {{$t("profiling.timelineTips.content21.part3")}}
                </div>
                <div>{{$t("profiling.timelineTips.content22")}}</div>
                <div>
                  {{$t("profiling.timelineTips.content23.part1")}}
                  <b>{{$t("profiling.timelineTips.content23.part2")}}</b>
                  {{$t("profiling.timelineTips.content23.part3")}}
                  <b>{{$t("profiling.timelineTips.content23.part4")}}</b>
                  {{$t("profiling.timelineTips.content23.part5")}}
                  <b>{{$t("profiling.timelineTips.content23.part6")}}</b>
                  {{$t("profiling.timelineTips.content23.part7")}}
                </div>
                <br>
                <div class="font-style">{{$t("profiling.timelineTips.title3")}}</div>
                <div>{{$t("profiling.timelineTips.content31")}}</div>
                <div>{{$t("profiling.timelineTips.content32")}}</div>
              </div>
              <i class="el-icon-info"></i>
            </el-tooltip>
          </div>
        </div>
        <!-- Time line detail  -->
        <div class="timeline-info"
             v-if="!timelineInfo.noData">
          <div class="info-line">
            <span>{{$t('profiling.opTotalTime')}}</span><span>{{timelineInfo.totalTime}}ms</span>
          </div>
          <div class="info-line">
            <span>{{$t('profiling.streamNum')}}</span><span>{{timelineInfo.streamNum}}</span>
          </div>
          <div class="info-line">
            <span>{{$t('profiling.opNum')}}</span><span>{{timelineInfo.opNum}}</span>
          </div>
          <div class="info-line">
            <span>{{$t('profiling.opTimes')}}</span><span>{{timelineInfo.opTimes}}{{$t('profiling.times')}}</span>
          </div>
        </div>
        <div class="image-noData"
             v-if="timelineInfo.noData">
          <div>
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
          </div>
          <p v-show="!timelineInfo.initOver">{{$t("public.dataLoading")}}</p>
          <p v-show="timelineInfo.initOver">{{$t("public.noData")}}</p>
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
      trainingJobId: this.$route.query.id, // Training job id
      summaryPath: this.$route.query.dir, // Summary path data
      relativePath: this.$route.query.path, // Relative path of summary log
      currentCard: '', // Data of current card
      queueInfoShow: false, // Whether to show queue information
      deviceInfoShow: false, // Whether to show device information
      processSummary: {
        // Data of process summary
        noData: true,
        count: 6,
        maxCount: 6,
        device: {
          empty: 0, // Number of empty devices
          full: 0, // Number of full devices
          total: 0, // Total number of devices
        },
        get_next: {
          empty: 0,
          full: 0,
          total: 0,
        },
        initOver: false, // Is initialization complete
      },
      pieChart: {
        // Pie graph information of operators
        chartDom: null,
        data: [],
        noData: true,
        topN: [],
        colorList: ['#6C92FA', '#6CBFFF', '#4EDED2', '#7ADFA0', '#A6DD82'],
        initOver: false, // Is initialization complete
      },
      timeLine: {
        // Time line data
        data: null,
        waiting: true, // Is it waiting for interface return
        disable: true,
      },
      timelineInfo: {
        // Time line information
        totalTime: 0,
        streamNum: 0,
        opNum: 0, // Number of operators
        opTimes: 0, // Operator time consuming
        noData: true,
        initOver: false, // Is initialization complete
      },
    };
  },
  mounted() {},
  watch: {
    // Monitor current card information
    '$parent.curDashboardInfo': {
      handler(newValue, oldValue) {
        if (newValue.curCardNum === '') {
          this.pieChart.noData = true;
          this.pieChart.initOver = true;
          this.processSummary.initOver = true;
          this.timelineInfo.initOver = true;
          this.timeLine.waiting = false;
        }
        if (newValue.query.dir &&
            newValue.query.id &&
            newValue.query.path &&
            newValue.curCardNum
        ) {
          this.summaryPath = newValue.query.dir;
          this.trainingJobId = newValue.query.id;
          this.relativePath = newValue.query.path;
          this.currentCard = newValue.curCardNum;
          if (this.trainingJobId) {
            document.title = `${decodeURIComponent(
                this.trainingJobId,
            )}-${this.$t('profiling.profilingDashboard')}-MindInsight`;
          } else {
            document.title = `${this.$t(
                'profiling.profilingDashboard',
            )}-MindInsight`;
          }
          this.pieChart.initOver = false;
          this.processSummary.initOver = false;
          this.timelineInfo.initOver = false;
          this.init();
        }
      },
      deep: true,
      immediate: true,
    },
  },
  methods: {
    /**
     * Initialization function
     */
    init() {
      this.queryTimeline();
      this.initPieChart();
      this.getProccessSummary();
    },
    /**
     * Get the data of proccess summary
     */
    getProccessSummary() {
      const params = {
        train_id: this.trainingJobId,
        profile: this.summaryPath,
        device_id: this.currentCard,
      };
      RequestService.queryProcessSummary(params).then((resp) => {
        this.processSummary.initOver = true;
        if (resp && resp.data) {
          const data = JSON.parse(JSON.stringify(resp.data));
          this.processSummary.count = Object.keys(data).length;
          this.dealProcess(data);
        } else {
          this.dealProcess(null);
          this.processSummary.initOver = true;
        }
      });
    },
    /**
     * Set the data of process
     * @param {Object} data The data of process
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

      if (data && Object.keys(data).length) {
        if (data.device_queue_info && data.device_queue_info.summary) {
          this.deviceInfoShow = true;
          this.processSummary.device = {
            empty: data.device_queue_info.summary.empty_batch_count,
            full: data.device_queue_info.summary.full_batch_count,
            total: data.device_queue_info.summary.total_batch,
          };
        }
        if (data.get_next_queue_info && data.get_next_queue_info.summary) {
          this.queueInfoShow = true;
          this.processSummary.get_next = {
            empty: data.get_next_queue_info.summary.empty_batch_count,
            full: data.get_next_queue_info.summary.full_batch_count,
            total: data.get_next_queue_info.summary.total_batch,
          };
        }
        this.processSummary.noData = false;
      }
    },
    /**
     * Router link
     * @param { String } path  router path
     */
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
    /**
     * Chart setOption
     */
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
    /**
     * Init chart
     */
    initPieChart() {
      const params = {};
      params.params = {
        profile: this.summaryPath,
        train_id: this.trainingJobId,
      };
      params.body = {
        op_type: 'gpu_op_type',
        device_id: this.currentCard,
        filter_condition: {},
        sort_condition: {
          name: 'avg_time',
          type: 'descending',
        },
      };
      RequestService.getProfilerOpData(params)
          .then((res) => {
            this.pieChart.initOver = true;
            if (res && res.data) {
              if (res.data.object) {
                this.pieChart.data = [];
                res.data.object.forEach((item) => {
                  if (this.pieChart.data && this.pieChart.data.length < 5) {
                    this.pieChart.data.push({
                      name: item[0],
                      value: item[4],
                      frequency: item[1],
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
                    this.pieChart.data[5].value += item[4];
                    this.pieChart.data[5].percent += item[3];
                  }
                });
                this.setPieOption();
                this.pieChart.noData = !!!this.pieChart.data.length;
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
            this.pieChart.data = [];
            this.pieChart.noData = true;
            this.pieChart.initOver = true;
          });
    },
    /**
     * Query the data of time line
     */
    queryTimeline() {
      this.timeLine.waiting = true;
      this.timeLine.disable = true;
      const params = {
        dir: this.relativePath,
        device_id: this.currentCard,
        device_type: 'gpu',
      };
      RequestService.queryTimlineInfo(params)
          .then((res) => {
            this.timelineInfo.initOver = true;
            if (res && res.data) {
              this.timelineInfo.noData = false;

              this.timelineInfo.totalTime =
              this.toFixedFun(res.data.total_time, 4) ||
              (res.data.total_time === 0 ? 0 : '--');
              this.timelineInfo.streamNum =
              res.data.num_of_streams ||
              (res.data.num_of_streams === 0 ? 0 : '--');
              this.timelineInfo.opNum =
              res.data.num_of_ops || (res.data.num_of_ops === 0 ? 0 : '--');
              this.timelineInfo.opTimes =
              res.data.op_exe_times || (res.data.op_exe_times === 0 ? 0 : '--');
            } else {
              this.timelineInfo.noData = true;
            }
          })
          .catch(() => {
            this.timelineInfo.noData = true;
            this.timelineInfo.initOver = true;
          });
      RequestService.queryTimeline(params)
          .then((res) => {
            this.timeLine.waiting = false;
            if (res && res.data && res.data.length) {
              this.timeLine.data = JSON.stringify(res.data);
              this.timeLine.disable = false;
            }
          })
          .catch(() => {
            this.timeLine.waiting = false;
          });
    },
    /**
     * Download timeline data file
     */
    downloadTimelineFile() {
      const downloadLink = document.createElement('a');
      downloadLink.download = this.getDocName();
      downloadLink.style.display = 'none';
      const blob = new Blob([this.timeLine.data]);
      downloadLink.href = URL.createObjectURL(blob);
      document.body.appendChild(downloadLink);
      downloadLink.click();
      document.body.removeChild(downloadLink);
    },
    /**
     * Generate a download file name
     * @return {String}
     */
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
    /**
     * Keep the number with n decimal places.
     * @param {Number} num
     * @param {Number} pow Number of decimal places
     * @return {Number}
     */
    toFixedFun(num, pow) {
      if (isNaN(num) || isNaN(pow) || !num || !pow) {
        return num;
      }
      return Math.round(num * Math.pow(10, pow)) / Math.pow(10, pow);
    },
  },
  destroyed() {
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
    .loading-icon {
      margin-left: 5px;
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
        height: calc(100% - 54px);
        overflow: auto;
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
          min-width: 110px;
          padding: 20px 0;
          border: 2px solid transparent;
          .title {
            font-size: 14px;
            line-height: 20px;
            padding: 0 0 0 10px;
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
            overflow: visible;
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
              overflow: visible;
              .num {
                white-space: nowrap;
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
      // overflow: hidden;
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
    min-height: 194px;
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

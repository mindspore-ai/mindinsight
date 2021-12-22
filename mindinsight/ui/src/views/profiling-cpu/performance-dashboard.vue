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
  <div class="pro-router-wrap">
    <div class="pro-router-left">
      <!-- Step trace area -->
      <div class="step-trace">
        <div class="title-wrap">
          <div class="title">{{ $t('profiling.stepTrace') }}</div>
          <div class="view-detail">
            <button :disabled="true"
                    :class="{disabled: true}">{{ $t('profiling.viewDetail') }}
              <i class="el-icon-d-arrow-right"></i></button>
          </div>
        </div>
        <!-- Step trace SVG container -->
        <div class="trace-container">
          <div class="image-noData">
            <div>
              <img :src="require('@/assets/images/nodata.png')"
                   alt="" />
            </div>
            <p>{{$t("public.noSupport")}}</p>
          </div>
        </div>
      </div>
      <!-- Process summary display area -->
      <div class="minddata">
        <div class="title-wrap">
          <div class="title">{{ $t('profiling.mindData') }}</div>
          <div class="view-detail">
            <button :disabled="true"
                    :class="{disabled: true}">
              {{ $t('profiling.viewDetail') }}
              <i class="el-icon-d-arrow-right"></i></button>
          </div>
        </div>
        <div class="image-noData">
          <div>
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
          </div>
          <p>{{$t("public.noSupport")}}</p>
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
                  <span class="value">{{item.time + $t('profiling.unit')}}</span>
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
            <button :disabled="true"
                    :class="{disabled: true}">{{ $t('profiling.downloadTimeline') }}
            </button>
          </div>
          <div class="tip-icon">
            <el-tooltip placement="bottom"
                        effect="light">
              <div slot="content"
                   class="tooltip-container">
                <div class="pro-dash-tooltip">
                  <div class="font-size-style">{{$t("profiling.features")}}</div>
                  <div class="font-style">{{$t("profiling.timelineTips.title1")}}</div>
                  <div>{{$t("profiling.timelineTips.content12")}}</div>
                  <div>{{$t("profiling.timelineTips.content13")}}</div>
                  <div>{{$t("profiling.timelineTips.content14")}}</div>
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
                  <br>
                  <div class="font-style">{{$t("profiling.timelineTips.title4")}}</div>
                  <div>{{$t("profiling.timelineTips.content41")}}</div>
                  <div class="indent">{{$t("profiling.timelineTips.content42")}}</div>
                  <div class="indent">{{$t("profiling.timelineTips.content43")}}</div>
                  <div class="indent">{{$t("profiling.timelineTips.content44")}}</div>
                  <div>{{$t("profiling.timelineTips.content45")}}</div>
                  <div>{{$t("profiling.timelineTips.content46")}}</div>
                  <div>{{$t("profiling.timelineTips.content47")}}</div>
                  <div>{{$t("profiling.timelineTips.content48")}}</div>
                  <div class="indent">{{$t("profiling.timelineTips.content49")}}</div>
                  <div class="indent">{{$t("profiling.timelineTips.content410")}}</div>
                  <div class="indent">{{$t("profiling.timelineTips.content411")}}</div>
                  <div class="indent">{{$t("profiling.timelineTips.content412")}}</div>
                </div>
              </div>
              <i class="el-icon-info"></i>
            </el-tooltip>
          </div>
        </div>
        <!-- Time line detail  -->
        <div class="image-noData">
          <div>
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
          </div>
          <p>{{$t("public.noSupport")}}</p>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import echarts from '../../js/echarts';
import RequestService from '../../services/request-service';
import CommonProperty from '../../common/common-property';
export default {
  data() {
    return {
      trainInfo: {
        id: this.$route.query.id,
        dir: this.$route.query.dir,
        path: this.$route.query.path,
      },
      currentCard: '', // current device card
      queueInfoShow: false, // Whether to show queue information
      deviceInfoShow: false, // Whether to show device information
      fpBpPercent: '--', // Ratio of time consumed by forward and backward propagation
      fpPercent: '--', // Ratio of time consumed by forward propagation
      iterationIntervalPercent: '--', // Ratio of time consumed by step interval
      totalSteps: '--',
      totalTime: '--',
      tailPercent: '--', // Ratio of time consumed by step tail
      pieChart: {
        // Pie graph information of operators
        chartDom: null,
        data: [],
        noData: true,
        topN: [],
        colorList: CommonProperty.pieColorArr[this.$store.state.themeIndex],
        initOver: false, // Is initialization complete
      },
      themeIndex: this.$store.state.themeIndex,
    };
  },
  watch: {
    // Monitor current card information
    '$parent.curDashboardInfo': {
      handler(newValue) {
        if (newValue.curCardNum === '') {
          this.pieChart.noData = true;
          this.pieChart.initOver = true;
        }
        if (newValue.query.dir && newValue.query.id && newValue.query.path && newValue.curCardNum) {
          this.trainInfo = newValue.query;
          this.currentCard = newValue.curCardNum;
          if (this.trainingJobId) {
            document.title = `${this.trainingJobId}-${this.$t('profiling.profilingDashboard')}-MindInsight`;
          } else {
            document.title = `${this.$t('profiling.profilingDashboard')}-MindInsight`;
          }
          this.pieChart.initOver = false;
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
      this.initPieChart();
    },
    /**
     * Router link
     * @param { String } path router path
     */
    viewDetail(path) {
      this.$router.push({
        path,
        query: this.trainInfo,
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
              color: (params) => {
                return CommonProperty.pieColorArr[this.$store.state.themeIndex][params.dataIndex];
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
      const params = {
        params: {
          profile: this.trainInfo.dir,
          train_id: this.trainInfo.id,
        },
        body: {
          op_type: 'cpu_op_type',
          device_id: this.currentCard,
          filter_condition: {
            op_type: {
              not_in: [],
            },
          },
          sort_condition: {
            name: 'avg_time',
            type: 'descending',
          },
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
              this.pieChart.noData = !this.pieChart.data.length;
              this.pieChart.topN = this.pieChart.data.slice(0, Math.min(this.pieChart.data.length, 5)).map((i) => {
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
  },
};
</script>
<style>
.el-tooltip-popper {
  max-width: 500px;
}

.tooltip-container .pro-dash-tooltip {
  line-height: 20px;
  padding: 10px;
}
.tooltip-container .pro-dash-tooltip .font-style {
  font-weight: bold;
}
.tooltip-container .pro-dash-tooltip .font-size-style {
  font-weight: bold;
  font-size: 16px;
}
.tooltip-container .pro-dash-tooltip .indent {
  padding-left: 30px;
}
.pro-router-wrap {
  height: 100%;
}
.pro-router-wrap > div {
  float: left;
  height: 100%;
}
.pro-router-wrap > div > div {
  border: 1px solid var(--border-color);
  border-radius: 1px;
}
.pro-router-wrap > div .title-wrap {
  padding: 15px;
}
.pro-router-wrap > div .title-wrap .title {
  float: left;
  font-weight: bold;
  font-size: 18px;
  max-width: 300px;
}
.pro-router-wrap > div .title-wrap .tip-icon {
  float: right;
  margin-right: 10px;
  font-size: 20px;
  color: #6c7280;
}
.pro-router-wrap > div .title-wrap .tip-icon .el-icon-warning {
  cursor: pointer;
}
.pro-router-wrap > div .title-wrap .tip-icon .el-icon-warning:hover::before {
  color: var(--theme-color);
}
.pro-router-wrap > div .title-wrap .view-detail {
  float: right;
  cursor: pointer;
  font-size: 12px;
  height: 24px;
  line-height: 24px;
}
.pro-router-wrap > div .title-wrap .view-detail a {
  color: var(--theme-color) !important;
  padding-right: 6px;
}
.pro-router-wrap > div .title-wrap .view-detail button {
  color: var(--theme-color);
  border: none;
  background-color: var(--bg-color);
  cursor: pointer;
}
.pro-router-wrap > div .title-wrap .view-detail button.disabled {
  cursor: not-allowed;
  color: var(--button-disabled-font-color);
}
.pro-router-wrap > div .title-wrap::after {
  content: '';
  clear: both;
  display: block;
}
.pro-router-wrap > div .loading-icon {
  margin-left: 5px;
}
.pro-router-wrap .pro-router-left {
  width: calc(100% - 400px);
  padding-right: 15px;
}
.pro-router-wrap .pro-router-left .step-trace {
  height: calc(100% - 275px);
  margin-bottom: 15px;
}
.pro-router-wrap .pro-router-left .step-trace .trace-container {
  width: 100%;
  height: calc(100% - 54px);
  overflow: auto;
}
.pro-router-wrap .pro-router-left .minddata {
  height: 260px;
}
.pro-router-wrap .pro-router-right {
  width: 400px;
}
.pro-router-wrap .pro-router-right .op-time-consume {
  height: calc(100% - 275px);
  margin-bottom: 15px;
}
.pro-router-wrap .pro-router-right .op-time-consume .time-list {
  height: calc(40% - 52px);
}
.pro-router-wrap .pro-router-right .op-time-consume .time-list .item {
  height: 25px;
  line-height: 25px;
  padding: 0 20px;
}
.pro-router-wrap .pro-router-right .op-time-consume .time-list .item > span {
  display: inline-block;
  height: 100%;
  vertical-align: middle;
}
.pro-router-wrap .pro-router-right .op-time-consume .time-list .item .index {
  color: white;
  background-color: #6c92fa;
  width: 20px;
  height: 20px;
  border-radius: 20px;
  text-align: center;
  vertical-align: middle;
  line-height: 20px;
}
.pro-router-wrap .pro-router-right .op-time-consume .time-list .item .name {
  margin-left: 10px;
  width: calc(50% - 30px);
  text-overflow: ellipsis;
  overflow: hidden;
}
.pro-router-wrap .pro-router-right .op-time-consume .time-list .item .num {
  width: 20%;
}
.pro-router-wrap .pro-router-right .op-time-consume .time-list .item .time {
  width: 30%;
  position: relative;
}
.pro-router-wrap .pro-router-right .op-time-consume .time-list .item .time span {
  display: inline-block;
  position: absolute;
  left: 0;
  height: 20px;
}
.pro-router-wrap .pro-router-right .op-time-consume .time-list .item .time .bar {
  background-color: var(--operator-bar-bg-color);
  top: 2px;
}
.pro-router-wrap .pro-router-right .op-time-consume .time-list .item .time .value {
  line-height: 25px;
  height: 25px;
}
.pro-router-wrap .pro-router-right .time-line {
  height: 260px;
}
.pro-router-wrap .op-time-content {
  height: calc(100% - 72px);
  overflow: auto;
}
.pro-router-wrap .pie-chart {
  width: 100%;
  height: 260px;
  overflow: hidden;
}
.pro-router-wrap .image-noData {
  width: 100%;
  height: calc(100% - 52px);
  min-height: 194px;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}
.pro-router-wrap .image-noData p {
  font-size: 16px;
  padding-top: 10px;
}
</style>

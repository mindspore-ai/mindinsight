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
          <div class="tip-icon"
               v-show="false">
            <el-tooltip content=""
                        placement="top"
                        effect="light">
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
          <div class="view-detail"
               v-if="false">
            <button @click="viewDetail('minddata')">{{ $t('profiling.viewDetail') }}
              <i class="el-icon-d-arrow-right"></i></button>
          </div>
        </div>
        <div class="coming-soon-content">
          <div class="coming-soon-container">
            <img :src="require('@/assets/images/coming-soon.png')" />
            <p class='coming-soon-text'>
              {{$t("public.stayTuned")}}
            </p>
          </div>
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
          <div class="view-detail"
               v-show="false">
            <a @click="toPerfetto()">{{ $t('profiling.viewDetail') }} <i class="el-icon-d-arrow-right"></i></a>
          </div>
        </div>
        <div class="coming-soon-content">
          <div class="coming-soon-container">
            <img :src="require('@/assets/images/coming-soon.png')" />
            <p class='coming-soon-text'>
              {{$t("public.stayTuned")}}
            </p>
          </div>
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
      svg: {
        data: [],
        svgPadding: 20,
        totalWidth: 0,
        totalTime: 0,
        rowHeight: 60,
        markerPadding: 4,
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
      this.queryTrainingTrace();
      this.initPieChart();
      window.addEventListener('resize', this.resizeTrace, false);
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
          return `${params.marker} ${params.data.name} ${params.percent}%`;
        },
      };
      option.series = [
        {
          type: 'pie',
          center: ['50%', '50%'],
          data: this.pieChart.data,
          radius: '50%',
          lable: {
            position: 'outer',
            alignTo: 'none',
            bleedMargin: 5,
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
                  if (this.pieChart.data && this.pieChart.data.length < 19) {
                    this.pieChart.data.push({
                      name: item[0],
                      value: item[1],
                      frequency: item[2],
                      percent: item[3],
                    });
                  } else {
                    if (!this.pieChart.data[19]) {
                      this.pieChart.data[19] = {
                        name: 'Other',
                        value: 0,
                        percent: 0,
                      };
                    }
                    this.pieChart.data[19].value += item[1];
                    this.pieChart.data[19].percent += item[3];
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
          const svg = document.querySelector('#trace svg');
          this.svg.totalTime = this.svg.data[0][0].duration;
          if (this.svg.totalTime) {
            this.svg.data.forEach((row, index) => {
              if (row && row.length) {
                const dashedLine = this.addDashedLine(index);
                svg.insertBefore(dashedLine, svg.querySelector('g'));
                row.forEach((i) => {
                  if (i.duration) {
                    if (i.name) {
                      const tempDom = this.createRect(i, index);
                      svg.insertBefore(tempDom, svg.querySelector('g'));
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
      g.appendChild(line);
      return g;
    },
    createRect(data, rowIndex) {
      const color = this.svg.colorList[this.svg.colorIndex++ % 4];
      const height = 40;
      const width = (data.duration / this.svg.totalTime) * this.svg.totalWidth;
      const x1 =
        (data.start / this.svg.totalTime) * this.svg.totalWidth +
        this.svg.svgPadding;
      const y1 =
        rowIndex * this.svg.rowHeight + (this.svg.rowHeight - height) / 2;
      const g = document.createElementNS(this.svg.namespaceURI, 'g');
      const gChild = document.createElementNS(this.svg.namespaceURI, 'g');

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
      foreignObject.setAttribute('x', x1);
      foreignObject.setAttribute('y', y1);
      foreignObject.setAttribute('height', height);
      foreignObject.setAttribute('width', width);
      foreignObject.setAttribute(
          'style',
          `overflow:hidden;text-align:center;text-overflow:ellipsis;` +
          `white-space:nowrap;font-size:12px;line-height:${height}px;color:${color[0]}`,
      );
      foreignObject.textContent = `${data.name}: ${data.duration.toFixed(4)}ms`;

      const title = document.createElementNS(this.svg.namespaceURI, 'title');
      title.textContent = `${data.name}: ${data.duration.toFixed(4)}ms`;

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

      const line = document.createElementNS(this.svg.namespaceURI, 'line');
      line.setAttribute('x1', x1);
      line.setAttribute('y1', y);
      line.setAttribute('x2', x2);
      line.setAttribute('y2', y);
      line.setAttribute('style', 'stroke:#E6EBF5;stroke-width:1');
      line.setAttribute('marker-end', 'url(#marker_end)');
      line.setAttribute('marker-start', 'url(#marker_start)');

      const text = document.createElementNS(this.svg.namespaceURI, 'text');
      text.textContent = `${data.duration.toFixed(4)}ms`;
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
  },
  destroyed() {
    window.removeEventListener('resize', this.resizeTrace, false);
    this.$bus.$off('collapse');
  },
};
</script>
<style lang="scss">
.pro-router-wrap {
  height: 100%;
  & > div {
    float: left;
    height: 100%;
    & > div {
      border: 1px solid #ddd;
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
        margin-right: 18px;
        font-size: 20px;
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
    width: calc(100% - 350px);
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
        }
      }
    }
    .minddata {
      height: calc(55% - 15px);
    }
  }
  .pro-router-right {
    width: 350px;
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
    }
  }
  .op-time-content {
    height: calc(100% - 54px);
    overflow: auto;
  }
  .pie-chart {
    width: 100%;
    height: 260px;
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

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
  <div class="step-trace">
    <div class="step-trace-title">{{$t('profiling.stepTraceDetail')}}
      <el-tooltip class="item"
                  effect="light"
                  :content="$t('profiling.defaultTip')"
                  placement="top">
        <span class="el-icon-info"></span>
      </el-tooltip>

      <div class="pf-content-right">
        <div class="input-wrap">
          <label>{{steps.label}}</label>
          <el-input ref="step"
                    v-model.number="steps.step"
                    :disabled="steps.disabled"
                    @blur="resetStep"
                    @keyup.native.enter="changeStep">
          </el-input>
          <el-button @click="changeStep"
                     :disabled="steps.disabled">
            {{$t('public.sure')}}
          </el-button>
        </div>
      </div>
      <el-button class="show-average"
                 @click="changeStep(0)"
                 :disabled="steps.disabled">
        {{$t('profiling.showAverage')}}
      </el-button>
    </div>
    <div class="step-message">
      <div class="step-left-padding-right">
        <span class="font-weight-style">{{$t('profiling.FPMessage')}}</span>
        <span>{{fp_start}}</span>
      </div>
      <div class="step-padding-right">
        <span class="font-weight-style">{{$t('profiling.BPMessage')}}</span>
        <span>{{bp_end}}</span>
      </div>
    </div>
    <div class="pf-content-middle">
      <div id="trace-container">
        <div id="trace"
             class="training-trace"
             :style="{height: svg.totalHeight + 'px'}">
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
                      fill="#6c7280"
                      stroke="#6c7280"></path>
              </marker>
              <marker id="marker_start"
                      refX="5"
                      refY="4"
                      markerWidth="10"
                      markerHeight="8"
                      orient="auto">
                <path d="M9,1 L9,7 L1,4 z"
                      fill="#6c7280"
                      stroke="#6c7280"></path>
              </marker>
            </defs>
          </svg>
        </div>
        <div class="image-noData svg"
             v-if="svg.noData">
          <div>
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
          </div>
          <p>{{svg.initOver?$t("public.noData"):$t("public.dataLoading")}}</p>
        </div>
      </div>

      <div v-for="(item,key) in tabsArr"
           :key="key"
           class="chart-wrap">
        <div class="title">{{ item.name }}</div>
        <div class="rate-wrap">
          <div v-if="item.timeSummary[item.rate] !== undefined">
            <span>{{item.timeLabel}}:</span>
            {{item.timeSummary[item.rate]}}ms</div>
          <div v-if="item.timeSummary[item.percent] !== undefined">
            <span>{{item.rateLabel}}:</span>{{item.timeSummary[item.percent]}}</div>
          <div v-if="item.timeSummary.total_steps !== undefined">
            <span>{{$t('profiling.stepNum')}}:</span>{{item.timeSummary.total_steps}}</div>
        </div>
        <div class="chart"
             :id="item.id"
             v-show="!item.noData"></div>
        <div class="image-noData"
             v-if="item.noData">
          <div>
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
          </div>
          <p>{{item.initOver?$t("public.noData"):$t("public.dataLoading")}}</p>
        </div>
      </div>
    </div>
    <div class="image-noData"
         v-if="!(!tabsArr[0].noData && !tabsArr[1].noData && !tabsArr[2].noData && !svg.noData)">
      <div>
        <img :src="require('@/assets/images/nodata.png')"
             alt="" />
      </div>
      <p>{{$t("public.noData")}}</p>
    </div>
  </div>
</template>

<script>
import echarts from 'echarts';
import RequestService from '../../services/request-service';
export default {
  data() {
    return {
      dir: this.$route.query.dir,
      train_id: this.$route.query.id,
      relativePath: this.$route.query.path,
      fp_start: '--',
      bp_end: '--',
      steps: {
        step: null,
        trueStep: null,
        max: 0,
        disabled: true,
        label: this.$t('profiling.stepInputTip'),
      },
      charts: [],
      svg: {
        data: [],
        svgPadding: 20,
        totalWidth: 0,
        totalTime: 0,
        cellHeight: 40,
        cellPadding: 0,
        rowPadding: 20,
        rowMargin: 10,
        totalHeight: 0,
        markerPadding: 4,
        minRate: 0.1,
        minTime: 0,
        minWidth: 1,
        fontSize: 12,
        textMargin: 21,
        namespaceURI: 'http://www.w3.org/2000/svg',
        resizeTimer: null,
        colors: {
          iteration_interval: ['#A6DD82', '#edf8e6'],
          fp_and_bp: ['#6CBFFF', '#e2f2ff'],
          tail: ['#fa8e5b', '#fff4de'],
          stream_parallel: ['#01a5a7', '#cceded'],
        },
        noData: true,
        initOver: false,
      },
      deviceId: 0,
      radio: this.$t('profiling.lterationGap'),
      tabsArr: [
        {
          name: this.$t('profiling.lterationGap'),
          id: 'iter-gap',
          timeSummary: {},
          rate: 'iteration_interval',
          timeLabel: this.$t('profiling.iterGapTimeLabel'),
          rateLabel: this.$t('profiling.iterGapRateLabel'),
          noData: true,
          percent: 'iteration_interval_percent',
          initOver: false,
        },
        {
          name: this.$t('profiling.deviceQueueOpTip'),
          id: 'fp-bp',
          timeSummary: {},
          rate: 'fp_and_bp',
          timeLabel: this.$t('profiling.fpBpTimeLabel'),
          rateLabel: this.$t('profiling.fpBpRateLabel'),
          noData: true,
          percent: 'fp_and_bp_percent',
          initOver: false,
        },
        {
          name: this.$t('profiling.lterationTail'),
          id: 'tailing',
          timeSummary: {},
          rate: 'tail',
          timeLabel: this.$t('profiling.tailTimeLabel'),
          rateLabel: this.$t('profiling.tailRateLabel'),
          noData: true,
          percent: 'tail_percent',
          initOver: false,
        },
      ],
    };
  },
  watch: {
    '$parent.curDashboardInfo': {
      handler(newValue, oldValue) {
        if (newValue.curCardNum || newValue.curCardNum === 0) {
          this.dir = newValue.query.dir;
          this.train_id = newValue.query.id;
          this.deviceId = newValue.curCardNum;
          this.relativePath = newValue.query.path;
          if (this.train_id) {
            document.title = `${decodeURIComponent(this.train_id)}-${this.$t(
                'profiling.stepTrace',
            )}-MindInsight`;
          } else {
            document.title = `${this.$t('profiling.stepTrace')}-MindInsight`;
          }
          this.svg.noData = true;
          this.svg.initOver = false;
          this.tabsArr.forEach((val) => {
            val.noData = true;
            val.initOver = false;
          });
          this.init();
        } else {
          this.svg.initOver = true;
          this.tabsArr.forEach((val) => {
            val.initOver = true;
          });
        }
      },
      deep: true,
      immediate: true,
    },
  },
  computed: {},
  mounted() {
    setTimeout(() => {
      this.$bus.$on('collapse', () => {
        this.resizeTrace();
        this.resizeEchart();
      });
    }, 500);
  },
  methods: {
    init() {
      window.addEventListener('resize', this.resizeTrace, false);
      window.addEventListener('resize', this.resizeEchart, false);
      if (this.charts.length) {
        this.charts.forEach((val) => {
          val.clear();
        });
      }
      this.steps = {
        step: null,
        trueStep: null,
        max: 0,
        disabled: true,
        label: this.$t('profiling.stepInputTip'),
      };

      this.getTimeInfo('fp-bp', 'fp_and_bp');
      this.getTimeInfo('iter-gap', 'iteration_interval');
      this.getTimeInfo('tailing', 'tail');
      this.queryTrainingTrace(0);
    },
    changeStep(value) {
      if (value === 0 || (!this.steps.step && this.steps.step !== 0)) {
        this.steps.step = null;
        this.steps.trueStep = null;
        this.queryTrainingTrace(0);
      } else if (
        /^[0-9]*[1-9][0-9]*$/.test(this.steps.step) &&
        this.steps.step <= this.steps.max
      ) {
        this.steps.trueStep = this.steps.step;
        this.queryTrainingTrace(this.steps.step);
      } else {
        this.steps.step = this.steps.trueStep;
        this.$message.error(
            this.$t('profiling.inputError').replace('{max}', this.steps.max),
        );
      }
    },
    resetStep() {
      setTimeout(() => {
        this.steps.step = this.steps.trueStep;
      }, 200);
    },
    getTimeInfo(id, type) {
      const params = {
        dir: this.relativePath,
        type,
        device_id: this.deviceId,
      };
      RequestService.targetTimeInfo(params).then(
          (res) => {
            if (res && res.data && res.data.summary) {
              const summary = res.data.summary;
              Object.keys(summary).forEach((val) => {
                summary[val] = summary[val];
              });
              this.tabsArr.forEach((val) => {
                if (id === val.id) {
                  val.timeSummary = summary;
                }
              });
            }
            if (res && res.data && res.data.info) {
              if (res.data.size && !this.steps.max) {
                this.steps.max = res.data.size;
                this.steps.disabled = false;
                this.steps.label = this.steps.label.replace(
                    '{max}',
                    this.steps.max,
                );
              }

              const xAxisData = [];
              for (let i = 1; i <= this.steps.max; i++) {
                xAxisData.push(i);
              }
              const timeInfo = [];
              Object.keys(res.data.info).forEach((val) => {
                timeInfo.push({
                  data: res.data.info[val],
                  name: val,
                  type: 'line',
                });
              });
              if (timeInfo.length) {
                const option = {
                  xAxis: {
                    type: 'category',
                    data: xAxisData,
                    name: 'step',
                  },
                  yAxis: {
                    type: 'value',
                    name: '',
                    nameTextStyle: {
                      padding: [0, 0, 0, 30],
                    },
                  },
                  grid: {
                    left: 50,
                    top: 50,
                    right: 50,
                    bottom: 50,
                  },
                  series: timeInfo,
                  tooltip: {
                    trigger: 'axis',
                    confine: true,
                  },
                  dataZoom: [
                    {
                      bottom: 0,
                    },
                    {
                      type: 'inside',
                      bottom: 0,
                    },
                  ],
                };
                if (type === 'iteration_interval') {
                  option.yAxis.name = `${this.$t(
                      'profiling.iterationGapTime',
                  )}(ms)`;
                  this.tabsArr[0].noData = this.steps.max ? false : true;
                  this.tabsArr[0].initOver = true;
                } else if (type === 'fp_and_bp') {
                  option.yAxis.name = `${this.$t(
                      'profiling.deviceQueueOpTip',
                  )}${this.$t('profiling.time')}(ms)`;
                  this.tabsArr[1].noData = this.steps.max ? false : true;
                  this.tabsArr[1].initOver = true;
                } else if (type === 'tail') {
                  option.yAxis.name = `${this.$t(
                      'profiling.lterationTail',
                  )}${this.$t('profiling.time')}(ms)`;
                  this.tabsArr[2].noData = this.steps.max ? false : true;
                  this.tabsArr[2].initOver = true;
                }
                this.initChart(option, id);
              }
            }
          },
          (error) => {
            if (type === 'iteration_interval') {
              this.tabsArr[0].noData = true;
            } else if (type === 'fp_and_bp') {
              this.tabsArr[1].noData = true;
            } else if (type === 'tail') {
              this.tabsArr[2].noData = true;
            }
          },
      );
    },
    initChart(option, id) {
      this.$nextTick(() => {
        const chart = echarts.init(document.getElementById(id));
        chart.setOption(option, true);
        this.charts.push(chart);
      });
    },
    resizeEchart() {
      setTimeout(() => {
        this.charts.forEach((val) => {
          val.resize();
        });
      }, 300);
    },
    queryTrainingTrace(step) {
      const params = {
        dir: this.relativePath,
        type: step,
        device_id: this.deviceId,
      };
      RequestService.queryTrainingTrace(params).then(
          (res) => {
            this.svg.initOver = true;
            if (
              res &&
            res.data &&
            res.data.training_trace_graph &&
            res.data.training_trace_graph.length
            ) {
              this.svg.noData = false;
              if (res.data.point_info) {
                this.fp_start = res.data.point_info.fp_start
                ? res.data.point_info.fp_start
                : '--';
                this.bp_end = res.data.point_info.bp_end
                ? res.data.point_info.bp_end
                : '--';
              } else {
                this.fp_start = '--';
                this.bp_end = '--';
              }

              this.removeTrace();
              this.$nextTick(() => {
                this.packageTraceData(
                    JSON.parse(JSON.stringify(res.data.training_trace_graph)),
                );
              });
            } else {
              this.fp_start = '--';
              this.bp_end = '--';
              this.svg.data = [];
              this.svg.noData = true;
              this.removeTrace();
            }
          },
          (error) => {
            this.fp_start = '--';
            this.bp_end = '--';
            this.svg.data = [];
            this.svg.noData = true;
            this.svg.initOver = true;
            this.removeTrace();
          },
      );
    },
    packageTraceData(traceGraph) {
      this.svg.totalTime = 0;
      this.svg.minTime = 0;
      this.svg.totalHeight = 0;
      const data = [];

      if (traceGraph && traceGraph[0] && traceGraph[0][0]) {
        this.svg.totalTime = traceGraph[0][0].duration;
        this.svg.minTime = this.svg.minRate * this.svg.totalTime;

        traceGraph.forEach((row, index) => {
          const rowObj = {
            rowCount: 0,
            data: [],
            height: 0,
            startY: this.svg.totalHeight,
          };
          let obj = [];
          for (let i = 0; i < row.length; i++) {
            if (row[i].duration < this.svg.minTime) {
              if (obj.length) {
                rowObj.data.push(obj);
                obj = [];
                rowObj.rowCount++;
              }
              rowObj.data.push([row[i]]);
              rowObj.rowCount++;
            } else {
              obj.push(row[i]);
            }

            if (i === row.length - 1 && obj.length) {
              rowObj.data.push(obj);
              obj = [];
              rowObj.rowCount++;
            }
          }
          rowObj.height =
            rowObj.rowCount * this.svg.cellHeight +
            (rowObj.rowCount - 1) * this.svg.cellPadding +
            (index ? this.svg.rowPadding * 2 : 0);

          this.svg.totalHeight += rowObj.height + this.svg.rowMargin;
          data.push(rowObj);
        });

        this.svg.totalHeight += this.svg.rowPadding;
        this.svg.data = JSON.parse(JSON.stringify(data));

        this.$nextTick(() => {
          this.dealTraceData();
        });
      }
    },

    dealTraceData() {
      const traceDom = document.querySelector('#trace');
      if (traceDom) {
        this.svg.totalWidth = traceDom.offsetWidth - this.svg.svgPadding * 2;

        if (this.svg.data[0] && this.svg.data[0].data.length) {
          const svg = traceDom.querySelector('svg');
          if (this.svg.totalTime) {
            this.svg.data.forEach((item, index) => {
              let itemDom = {};
              if (index) {
                itemDom = this.createMultipleRowContainer(item);
              } else {
                itemDom = this.createRowContainer(item.data, item.startY);
              }
              svg.appendChild(itemDom);
            });
          }
        } else {
          this.removeTrace();
        }
      }
    },

    createMultipleRowContainer(item) {
      const rectContainer = document.createElementNS(
          this.svg.namespaceURI,
          'g',
      );
      rectContainer.setAttribute('class', 'container');

      const rect = document.createElementNS(this.svg.namespaceURI, 'rect');
      rect.setAttribute('x', this.svg.svgPadding);
      rect.setAttribute('y', item.startY + this.svg.rowPadding);
      rect.setAttribute('height', item.height);
      rect.setAttribute('width', this.svg.totalWidth);
      rect.setAttribute('style', 'fill:#edf0f5;stroke:#E2E2E2;stroke-width:1');
      rectContainer.appendChild(rect);

      const temp = this.createRowContainer(
          item.data,
          item.startY + this.svg.rowPadding,
      );
      rectContainer.appendChild(temp);
      return rectContainer;
    },

    createRowContainer(data, startY) {
      const g = document.createElementNS(this.svg.namespaceURI, 'g');

      data.forEach((row, index) => {
        const y =
          startY +
          this.svg.rowPadding +
          index * (this.svg.cellPadding + this.svg.cellHeight);
        row.forEach((i) => {
          if (i.duration) {
            let temp;
            if (i.name) {
              temp = this.createRect(i, y);
              g.insertBefore(temp, g.querySelector('g'));
            } else {
              temp = this.createArrow(i, y);
              g.appendChild(temp);
            }
          }
        });
      });
      return g;
    },

    createRect(data, startY) {
      const color =
        data.name && this.svg.colors[data.name]
          ? this.svg.colors[data.name]
          : this.svg.colors.stream_parallel;

      const x1 =
        (data.start / this.svg.totalTime) * this.svg.totalWidth +
        this.svg.svgPadding;

      const width = Math.max(
          this.svg.minWidth,
          (data.duration / this.svg.totalTime) * this.svg.totalWidth,
      );

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

      const textContent = `${name}: ${this.toFixedFun(data.duration, 4)}ms`;
      const textWidth = this.getTextWidth(textContent);
      const normalSize = data.duration >= this.svg.minTime;

      const g = document.createElementNS(this.svg.namespaceURI, 'g');
      g.setAttribute('class', 'rect');

      const rect = document.createElementNS(this.svg.namespaceURI, 'rect');
      rect.setAttribute('x', x1);
      rect.setAttribute('y', startY);
      rect.setAttribute('height', this.svg.cellHeight);
      rect.setAttribute('width', width);
      rect.setAttribute('style', `fill:${color[1]};stroke:${color[0]};`);

      const foreignObject = document.createElementNS(
          this.svg.namespaceURI,
          'foreignObject',
      );
      foreignObject.textContent = textContent;
      foreignObject.setAttribute(
          'x',
        normalSize
          ? x1
          : Math.min(
              this.svg.svgPadding * 2 +
                this.svg.totalWidth -
                textWidth -
                this.svg.textMargin,
              Math.max(this.svg.textMargin, x1 + width / 2 - textWidth / 2),
          ),
      );

      foreignObject.setAttribute('y', startY);
      foreignObject.setAttribute('height', this.svg.cellHeight);
      foreignObject.setAttribute('width', width);
      foreignObject.setAttribute('style', `color:${color[0]}`);
      foreignObject.setAttribute(
          'class',
          `content${normalSize ? '' : ' content-mini'}`,
      );

      const title = document.createElementNS(this.svg.namespaceURI, 'title');
      title.textContent = textContent;

      g.appendChild(rect);
      g.appendChild(foreignObject);
      g.appendChild(title);
      return g;
    },

    createArrow(data, startY) {
      const width = (data.duration / this.svg.totalTime) * this.svg.totalWidth;
      const x1 =
        (data.start / this.svg.totalTime) * this.svg.totalWidth +
        this.svg.svgPadding;
      const centerY = startY + this.svg.cellHeight / 2;

      const g = document.createElementNS(this.svg.namespaceURI, 'g');
      g.setAttribute('class', 'arrow');

      const line = document.createElementNS(this.svg.namespaceURI, 'line');
      line.setAttribute('y1', centerY);
      line.setAttribute('y2', centerY);
      line.setAttribute('style', 'stroke:#6c7280;stroke-width:1');
      if (width > this.svg.markerPadding) {
        line.setAttribute('x1', x1 + this.svg.markerPadding);
        line.setAttribute('x2', x1 + width - this.svg.markerPadding);
        line.setAttribute('marker-end', 'url(#marker_end)');
        line.setAttribute('marker-start', 'url(#marker_start)');
      } else {
        line.setAttribute('x1', x1);
        line.setAttribute('x2', x1 + width);
      }

      const text = document.createElementNS(this.svg.namespaceURI, 'text');
      text.textContent = `${
        data.duration === this.svg.totalTime
          ? this.$t('profiling.approximateTime')
          : ''
      }${this.toFixedFun(data.duration, 4)}ms`;
      const textWidth = text.textContent
        ? this.getTextWidth(text.textContent)
        : 0;
      text.setAttribute(
          'x',
          Math.min(
              this.svg.svgPadding * 2 +
            this.svg.totalWidth -
            textWidth -
            this.svg.textMargin,
              Math.max(this.svg.textMargin, width / 2 + x1 - textWidth / 2),
          ),
      );
      text.setAttribute('y', centerY - this.svg.fontSize / 2);
      text.setAttribute('font-size', this.svg.fontSize);
      text.setAttribute('fill', 'black');

      const startLine = document.createElementNS(this.svg.namespaceURI, 'line');
      startLine.setAttribute('x1', x1);
      startLine.setAttribute('y1', startY);
      startLine.setAttribute('x2', x1);
      startLine.setAttribute('y2', startY + this.svg.cellHeight);
      startLine.setAttribute('style', 'stroke:#6c7280;stroke-width:1');
      g.appendChild(startLine);

      const endLine = document.createElementNS(this.svg.namespaceURI, 'line');
      endLine.setAttribute('x1', x1 + width);
      endLine.setAttribute('y1', startY);
      endLine.setAttribute('x2', x1 + width);
      endLine.setAttribute('y2', startY + this.svg.cellHeight);
      endLine.setAttribute('style', 'stroke:#6c7280;stroke-width:1');
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
    window.removeEventListener('resize', this.resizeTrace, false);
    window.removeEventListener('resize', this.resizeEchart, false);
    this.$bus.$off('collapse');
  },
};
</script>
<style lang="scss">
.step-trace {
  width: 100%;
  height: 100%;
  .step-trace-title {
    padding: 0 15px;
    font-size: 16px;
    font-weight: bold;
    .el-icon-question {
      cursor: pointer;
    }
    .pf-content-right {
      display: inline-block;
      margin-left: 35px;
      .input-wrap {
        font-weight: normal;
        label {
          margin-right: 20px;
        }
        .el-input {
          width: 150px;
          margin-right: 16px;
        }
      }
    }
    .el-button {
      border: 1px solid #00a5a7;
      border-radius: 2px;
      background-color: white;
      color: #00a5a7;
      padding: 7px 15px;
      &:hover {
        background: rgb(230, 246, 246);
      }
    }
    .show-average {
      float: right;
      margin-right: 20px;
    }
  }
  .step-message {
    height: 32px;
    line-height: 16px;
    margin-top: 6px;
    margin-left: 14px;
    overflow-y: auto;
  }
  .step-padding-right {
    padding-right: 20px;
    display: inline-block;
  }
  .step-left-padding-right {
    padding-right: 30px;
    display: inline-block;
  }
  .font-weight-style {
    font-weight: bold;
  }
  .pf-content-middle {
    padding: 10px 15px 0;
    height: calc(100% - 62px);
    #trace-container {
      width: 100%;
      height: 50%;
      border: 1px solid #ccc;
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
          line-height: 40px;
        }
        .content-mini {
          overflow: visible;
        }
      }
    }
    .chart-wrap {
      float: left;
      height: calc(50% - 20px);
      margin-top: 20px;
      margin-right: 15px;
      width: calc(33.3% - 10px);
      border: 1px solid #ccc;
      padding: 30px 30px 0;
      border-radius: 4px;
      overflow: auto;
      &:last-child {
        margin-right: 0;
      }
      .chart {
        height: calc(100% - 85px);
        min-height: 180px;
        overflow: hidden;
      }
      .title {
        margin: 0 0 15px 20px;
        font-weight: bold;
      }
      .rate-wrap {
        font-size: 12px;
        padding-left: 20px;
        & > div {
          display: inline-block;
          margin: 0 15px 5px 0;
          color: #464950;
          span {
            margin-right: 10px;
            color: #6c7280;
          }
        }
      }
    }
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
  .image-noData.svg {
    height: 100%;
  }
  .el-icon-info {
    font-size: 18px;
    color: #6c7280;
  }
}
</style>

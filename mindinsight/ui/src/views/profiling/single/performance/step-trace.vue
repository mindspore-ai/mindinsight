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
  <div class="step-trace">
    <div :class="[`profiling-content-title${isGPU ? '-gpu' : ''}`, 'step-trace-title']">
      {{$t('profiling.stepTraceDetail')}}
      <el-tooltip class="item"
                  effect="light"
                  :content="$t('profiling.defaultTip')"
                  placement="top">
        <span class="el-icon-info"></span>
      </el-tooltip>

      <div class="pf-content-right"
           v-show="!(tabsArr[0].noData && tabsArr[1].noData && tabsArr[2].noData && svg.noData)">
        <div class="input-wrap">
          <label>{{steps.label}}</label>
          <el-input ref="step"
                    v-model.number="steps.step"
                    :disabled="steps.disabled"
                    @blur="resetStep"
                    @keyup.native.enter="changeStep"
                    @clear="clearStep"
                    clearable>
          </el-input>
          <el-button @click="changeStep"
                     :disabled="steps.disabled">
            {{$t('public.sure')}}
          </el-button>
        </div>
      </div>
      <el-button class="show-average"
                 @click="changeStep(0)"
                 :disabled="steps.disabled"
                 v-show="!(tabsArr[0].noData && tabsArr[1].noData && tabsArr[2].noData && svg.noData)">
        {{$t('profiling.showAverage')}}
      </el-button>
    </div>
    <div class="step-message"
         v-show="!(tabsArr[0].noData && tabsArr[1].noData && tabsArr[2].noData && svg.noData)">
      <div class="step-left-padding-right">
        <span class="font-weight-style">{{$t('profiling.FPMessage')}}</span>
        <span>{{fp_start}}</span>
      </div>
      <div class="step-padding-right"
           v-if="bp_end">
        <span class="font-weight-style">{{$t('profiling.BPMessage')}}</span>
        <span>{{bp_end}}</span>
      </div>
    </div>
    <div class="pf-content-middle"
         v-show="!(tabsArr[0].noData && tabsArr[1].noData && tabsArr[2].noData && svg.noData)">
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
      <div class="chart-container">
        <template v-for="(item,key) in tabsArr">
          <div :key="key"
               class="chart-wrap"
               :class="{'chart-show':key!==2 && !bp_end}"
               v-if="!(key===2 && !bp_end)">
            <div class="title">{{ item.name }}</div>
            <div class="rate-wrap">
              <div v-if="item.timeSummary[item.rate] !== undefined">
                <span>{{item.timeLabel}}:</span>
                {{item.timeSummary[item.rate]}}ms
              </div>
              <div v-if="item.timeSummary[item.percent] !== undefined">
                <span>{{item.rateLabel}}:</span>{{item.timeSummary[item.percent]}}
              </div>
              <div v-if="item.timeSummary.total_steps !== undefined">
                <span>{{$t('profiling.stepNum')}}:</span>{{item.timeSummary.total_steps}}
              </div>
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
        </template>
      </div>
    </div>
    <div class="image-noData"
         v-if="tabsArr[0].noData && tabsArr[1].noData && tabsArr[2].noData && svg.noData">
      <div>
        <img :src="require('@/assets/images/nodata.png')"
             alt="" />
      </div>
      <p>{{svg.initOver?$t("public.noData"):$t("public.dataLoading")}}</p>
    </div>
  </div>
</template>

<script>
import echarts, {echartsThemeName} from '@/js/echarts';
import RequestService from '@/services/request-service';
import CommonProperty from '@/common/common-property';
import {isInteger} from '@/js/utils';
export default {
  props: {
    rankID: String,
  },
  data() {
    return {
      isGPU: this.$route.path.includes('profiling-gpu'),
      trainInfo: {
        dir: this.$route.query.dir, // Summary path data
        id: this.$route.query.id, // Training job id
        path: this.$route.query.path, // Relative path of summary log
      },
      fp_start: '--', // FP start operator
      bp_end: '--', // BP termination operator
      steps: {
        // Information of training steps
        step: null, // Step value of page presentation
        trueStep: null, // True step value
        max: 0, // Maximum value of step
        disabled: true,
        label: this.$t('profiling.stepInputTip'),
      },
      charts: [],
      svg: {
        // Step trace svg information
        data: [], // Data of svg
        svgPadding: 20, // Padding of svg
        totalWidth: 0, // Total width of svg
        totalTime: 0, // Total time
        cellHeight: 40,
        cellPadding: 0,
        rowPadding: 20,
        rowMargin: 10,
        totalHeight: 0,
        markerPadding: 4,
        minRate: 0.1, // Minimum time share threshold of non wrapping display
        minTime: 0, // Minimum time for non wrapping display
        minWidth: 1, // Minimum width of graphics in SVG
        fontSize: 12,
        textMargin: 21, // The minimum margin of the text from the border
        namespaceURI: 'http://www.w3.org/2000/svg', // XML namespace
        resizeTimer: null, // Response delay of resize event
        colors: {
          // Colors of different types of data presentation
          iteration_interval: [
            CommonProperty.stepTraceThemes[this.$store.state.themeIndex].reactIterationIntervalStroke,
            CommonProperty.stepTraceThemes[this.$store.state.themeIndex].reactIterationIntervalFill,
          ],
          fp_and_bp: [
            CommonProperty.stepTraceThemes[this.$store.state.themeIndex].reactFpAndBpstroke,
            CommonProperty.stepTraceThemes[this.$store.state.themeIndex].reactFpAndBpFill,
          ],
          tail: [
            CommonProperty.stepTraceThemes[this.$store.state.themeIndex].reactTailStroke,
            CommonProperty.stepTraceThemes[this.$store.state.themeIndex].reactTailFill,
          ],
          stream_parallel: ['#01a5a7', '#cceded'],
        },
        noData: true,
        initOver: false,
      },
      radio: this.$t('profiling.iterationGap'),
      tabsArr: [
        // Detailed chart of data in step trace
        {
          name: this.$t('profiling.iterationGap'),
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
          name: this.$t('profiling.iterationTail'),
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
    // Monitor current card information
    rankID: {
      handler(newValue) {
        if (isInteger(newValue)) {
          this.svg.noData = true;
          this.svg.initOver = false;
          this.tabsArr.forEach((val) => {
            val.noData = true;
            val.initOver = false;
          });
          this.init();
        } else {
          if (newValue === '') {
            this.svg.initOver = true;
            this.tabsArr.forEach((val) => {
              val.initOver = true;
            });
          }
        }
      },
      immediate: true,
    },
  },
  computed: {},
  mounted() {
    const id = this.trainInfo.id;
    document.title = (id ? id + '-' : '') + `${this.$t('profiling.stepTrace')}-MindInsight`;
    window.addEventListener('resize', this.resizeTrace, false);
    window.addEventListener('resize', this.resizeEchart, false);
    // Collapse the left column to respond to events
    setTimeout(() => {
      this.$bus.$on('collapse', () => {
        this.resizeTrace();
        this.resizeEchart();
      });
    }, 500);
  },
  methods: {
    /**
     * Initialization function
     */
    init() {
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
      this.queryTrainingTrace(0, true);
    },
    /**
     * Change the current step value
     * @param {Number} value The current step value
     */
    changeStep(value) {
      if (value === 0 || (!this.steps.step && this.steps.step !== 0)) {
        this.steps.step = null;
        this.steps.trueStep = null;
        this.queryTrainingTrace(0, false);
      } else if (/^[0-9]*[1-9][0-9]*$/.test(this.steps.step) && this.steps.step <= this.steps.max) {
        this.steps.trueStep = this.steps.step;
        this.queryTrainingTrace(this.steps.step, false);
      } else {
        this.steps.step = this.steps.trueStep;
        this.$message.error(this.$t('profiling.inputError').replace('{max}', this.steps.max));
      }
    },
    /**
     * Reset the current step value
     */
    resetStep() {
      setTimeout(() => {
        if (!this.$refs.step.focused) {
          this.steps.step = this.steps.trueStep;
        }
      }, 200);
    },
    /**
     * Clear the current step value
     */
    clearStep() {
      this.steps.step = null;
      this.$refs.step.focus();
    },
    /**
     * Get different types of time information
     * @param {String} id Dom id
     * @param {String} type Types of time information
     */
    getTimeInfo(id, type) {
      const params = {
        dir: this.trainInfo.path,
        type,
        device_id: this.rankID,
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
                this.steps.label = this.steps.label.replace('{max}', this.steps.max);
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
                      padding: [0, 0, 0, -30],
                      align: 'left',
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
                  option.yAxis.name = `${this.$t('profiling.iterationGapTime')}(ms)`;
                  this.tabsArr[0].noData = this.steps.max ? false : true;
                  this.tabsArr[0].initOver = true;
                } else if (type === 'fp_and_bp' || type === 'fp') {
                  option.yAxis.name =
                  type === 'fp_and_bp'
                    ? `${this.$t('profiling.fpBpTime')}(ms)`
                    : `${this.$t('profiling.fpTime')}(ms)`;
                  this.tabsArr[1].noData = this.steps.max ? false : true;
                  this.tabsArr[1].initOver = true;
                  if (type === 'fp_and_bp') {
                    this.tabsArr[1].name = this.$t('profiling.deviceQueueOpTip');
                  } else {
                    this.tabsArr[1].name = this.$t('profiling.deviceQueueOpFpTip');
                  }
                } else if (type === 'tail') {
                  option.yAxis.name = `${this.$t('profiling.tailTime')}(ms)`;
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
              this.tabsArr[0].initOver = true;
            } else if (type === 'fp_and_bp' || type === 'fp') {
              this.tabsArr[1].noData = true;
              this.tabsArr[1].initOver = true;
              if (type === 'fp_and_bp') {
                this.tabsArr[1].name = this.$t('profiling.deviceQueueOpTip');
              } else {
                this.tabsArr[1].name = this.$t('profiling.deviceQueueOpFpTip');
              }
            } else if (type === 'tail') {
              this.tabsArr[2].noData = true;
              this.tabsArr[2].initOver = true;
            }
          },
      );
    },
    /**
     * Initialization chart
     * @param {Object} option Chart options
     * @param {String} id Dom id
     */
    initChart(option, id) {
      this.$nextTick(() => {
        const chart = echarts.init(document.getElementById(id), echartsThemeName);
        chart.setOption(option, true);
        this.charts.push(chart);
      });
    },
    /**
     * Resize chart
     */
    resizeEchart() {
      setTimeout(() => {
        this.charts.forEach((val) => {
          val.resize();
        });
      }, 300);
    },
    /**
     * Get training trace information
     * @param {Number} step Current step value
     * @param {Boolean} init Init flag
     */
    queryTrainingTrace(step, init) {
      const params = {
        dir: this.trainInfo.path,
        type: step,
        device_id: this.rankID,
      };
      RequestService.queryTrainingTrace(params).then(
          (res) => {
            this.svg.initOver = true;
            if (res && res.data && res.data.training_trace_graph && res.data.training_trace_graph.length) {
              this.svg.noData = false;
              if (res.data.point_info) {
                this.fp_start = res.data.point_info.fp_start ? res.data.point_info.fp_start : '--';
                this.bp_end = res.data.point_info.bp_end ? res.data.point_info.bp_end : '';
              } else {
                this.fp_start = '--';
                this.bp_end = '--';
              }

              this.removeTrace();
              this.$nextTick(() => {
                this.packageTraceData(JSON.parse(JSON.stringify(res.data.training_trace_graph)));
              });
              if (init) {
                this.getTimeInfo('fp-bp', this.bp_end ? 'fp_and_bp' : 'fp');
                this.getTimeInfo('iter-gap', 'iteration_interval');
                if (this.bp_end) {
                  this.getTimeInfo('tailing', 'tail');
                }
              }
            } else {
              this.fp_start = '--';
              this.bp_end = '--';
              this.svg.data = [];
              this.svg.noData = true;
              this.removeTrace();
              this.tabsArr.forEach((val) => {
                val.noData = true;
                val.initOver = true;
              });
            }
          },
          (error) => {
            this.fp_start = '--';
            this.bp_end = '--';
            this.svg.data = [];
            this.svg.noData = true;
            this.svg.initOver = true;
            this.removeTrace();
            this.tabsArr.forEach((val) => {
              val.noData = true;
              val.initOver = true;
            });
          },
      );
    },
    /**
     * Encapsulating the data of training trace
     * @param {Object} traceGraph Data of training trace
     */
    packageTraceData(traceGraph) {
      this.svg.totalTime = 0;
      this.svg.minTime = 0;
      this.svg.totalHeight = 0;
      const data = [];

      if (traceGraph && traceGraph[0] && traceGraph[0][0]) {
        this.svg.totalTime = traceGraph[0][0].duration;
        this.svg.minTime = this.svg.minRate * this.svg.totalTime;

        // If there is data less than the minimum time in each row,
        // the data in each row is divided into several rows
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

    /**
     * Processing the data of training trace, Control data generation svg
     */
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

    /**
     * Generate a container with multiple rows
     * @param {Object} item Multi row data
     * @return {Object} Generated DOM object
     */
    createMultipleRowContainer(item) {
      const rectContainer = document.createElementNS(this.svg.namespaceURI, 'g');
      rectContainer.setAttribute('class', 'container');

      const rect = document.createElementNS(this.svg.namespaceURI, 'rect');
      rect.setAttribute('x', this.svg.svgPadding);
      rect.setAttribute('y', item.startY + this.svg.rowPadding);
      rect.setAttribute('height', item.height);
      rect.setAttribute('width', this.svg.totalWidth);
      rect.setAttribute(
          'style',
          `fill:${CommonProperty.stepTraceThemes[this.$store.state.themeIndex].reactContainerFill};stroke:${
            CommonProperty.stepTraceThemes[this.$store.state.themeIndex].reactContainerStroke
          };stroke-width:1`,
      );
      rectContainer.appendChild(rect);

      const temp = this.createRowContainer(item.data, item.startY + this.svg.rowPadding);
      rectContainer.appendChild(temp);
      return rectContainer;
    },

    /**
     * DOM for generating a single SVG image
     * @param {Object} data Data of single SVG image
     * @param {Number} startY Start y position of box
     * @return {Object}
     */
    createRowContainer(data, startY) {
      const g = document.createElementNS(this.svg.namespaceURI, 'g');

      data.forEach((row, index) => {
        const y = startY + this.svg.rowPadding + index * (this.svg.cellPadding + this.svg.cellHeight);
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

    /**
     * Create a box DOM from the data
     * @param {Object} data Data of single SVG image
     * @param {Number} startY Start y position of box
     * @return {Object}
     */
    createRect(data, startY) {
      const color =
        data.name && this.svg.colors[data.name] ? this.svg.colors[data.name] : this.svg.colors.stream_parallel;
      // Start x position of box
      const x1 = (data.start / this.svg.totalTime) * this.svg.totalWidth + this.svg.svgPadding;
      // The width of the box
      const width = Math.max(this.svg.minWidth, (data.duration / this.svg.totalTime) * this.svg.totalWidth);

      // Contents of the box
      let name = '';
      switch (data.name) {
        case 'iteration_interval':
          name = this.$t('profiling.iterationGap');
          break;
        case 'fp_and_bp':
          name = this.$t('profiling.deviceQueueOpTip');
          break;
        case 'fp':
          name = this.$t('profiling.deviceQueueOpFpTip');
          break;
        case 'tail':
          name = this.$t('profiling.iterationTail');
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

      const foreignObject = document.createElementNS(this.svg.namespaceURI, 'foreignObject');
      foreignObject.textContent = textContent;
      foreignObject.setAttribute(
          'x',
        normalSize
          ? x1
          : Math.min(
              this.svg.svgPadding * 2 + this.svg.totalWidth - textWidth - this.svg.textMargin,
              Math.max(this.svg.textMargin, x1 + width / 2 - textWidth / 2),
          ),
      );

      foreignObject.setAttribute('y', startY);
      foreignObject.setAttribute('height', this.svg.cellHeight);
      foreignObject.setAttribute('width', width);
      foreignObject.setAttribute('style', `color:${color[0]}`);
      foreignObject.setAttribute('class', `content${normalSize ? '' : ' content-mini'}`);

      const title = document.createElementNS(this.svg.namespaceURI, 'title');
      title.textContent = textContent;

      g.appendChild(rect);
      g.appendChild(foreignObject);
      g.appendChild(title);
      return g;
    },

    /**
     * Create a arrow DOM from the data
     * @param {Object} data Data of single SVG image
     * @param {Number} startY Start y position of arrow
     * @return {Object}
     */
    createArrow(data, startY) {
      const width = (data.duration / this.svg.totalTime) * this.svg.totalWidth;
      const x1 = (data.start / this.svg.totalTime) * this.svg.totalWidth + this.svg.svgPadding;
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
        data.duration === this.svg.totalTime ? this.$t('profiling.approximateTime') : ''
      }${this.toFixedFun(data.duration, 4)}ms`;
      const textWidth = text.textContent ? this.getTextWidth(text.textContent) : 0;

      // The position of the text cannot go beyond the border of the SVG
      text.setAttribute(
          'x',
          Math.min(
              this.svg.svgPadding * 2 + this.svg.totalWidth - textWidth - this.svg.textMargin,
              Math.max(this.svg.textMargin, width / 2 + x1 - textWidth / 2),
          ),
      );
      text.setAttribute('y', centerY - this.svg.fontSize / 2);
      text.setAttribute('font-size', this.svg.fontSize);
      text.setAttribute('fill', CommonProperty.stepTraceThemes[this.$store.state.themeIndex].reactFontColor);

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
    /**
     * Gets the width of a string
     * @param {String} text
     * @return {Number}
     */
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
    /**
     * Remove SVG DOM from page
     */
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
    /**
     * Respond to the reset event and update the page display
     */
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
<style>
.step-trace {
  width: 100%;
  height: 100%;
}
.step-trace .step-trace-title {
  height: 32px;
}
.step-trace .step-trace-title .el-icon-question {
  cursor: pointer;
}
.step-trace .step-trace-title .pf-content-right {
  display: inline-block;
  margin-left: 35px;
}
.step-trace .step-trace-title .pf-content-right .input-wrap {
  font-weight: normal;
}
.step-trace .step-trace-title .pf-content-right .input-wrap label {
  margin-right: 20px;
}
.step-trace .step-trace-title .pf-content-right .input-wrap .el-input {
  width: 150px;
  margin-right: 16px;
}
.step-trace .step-trace-title .el-button {
  border: 1px solid var(--theme-color);
  border-radius: 2px;
  background-color: var(--bg-color);
  color: var(--theme-color);
  padding: 7px 15px;
}
.step-trace .step-trace-title .el-button:hover {
  background: var(--button-hover-color);
}
.step-trace .step-trace-title .show-average {
  position: absolute;
  right: 36px;
}
.step-trace .step-message {
  height: 32px;
  line-height: 16px;
  margin-top: 8px;
  overflow-y: auto;
}
.step-trace .step-padding-right {
  padding-right: 20px;
  display: inline-block;
}
.step-trace .step-left-padding-right {
  padding-right: 30px;
  display: inline-block;
}
.step-trace .font-weight-style {
  font-weight: bold;
}
.step-trace .pf-content-middle {
  display: grid;
  grid-template-rows: repeat(2, calc(50% - 10px));
  gap: 20px;
  padding-top: 10px;
  height: calc(100% - 72px);
}
.step-trace .pf-content-middle #trace-container {
  width: 100%;
  height: 100%;
  border: 1px solid var(--border-color);
  overflow: auto;
}
.step-trace .pf-content-middle #trace-container .training-trace {
  position: relative;
  height: 0;
}
.step-trace .pf-content-middle #trace-container .training-trace .content {
  overflow: hidden;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  line-height: 40px;
}
.step-trace .pf-content-middle #trace-container .training-trace .content-mini {
  overflow: visible;
}
.step-trace .chart-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  height: 100%;
}
.step-trace .pf-content-middle .chart-wrap {
  height: 100%;
  width: 100%;
  border: 1px solid var(--border-color);
  padding-top: 20px;
  border-radius: 1px;
  overflow: auto;
}
.step-trace .pf-content-middle .chart-wrap .chart {
  height: calc(100% - 110px);
  min-height: 180px;
  min-width: 250px;
  overflow: hidden;
}
.step-trace .pf-content-middle .chart-wrap .title {
  margin: 0 0 15px 20px;
  font-weight: bold;
  font-size: 16px;
}
.step-trace .pf-content-middle .chart-wrap .rate-wrap {
  font-size: 12px;
  padding-left: 20px;
}
.step-trace .pf-content-middle .chart-wrap .rate-wrap > div {
  display: inline-block;
  margin: 0 15px 5px 0;
  color: var(--step-trace-chart-text-color);
}
.step-trace .pf-content-middle .chart-wrap .rate-wrap > div span {
  margin-right: 10px;
  color: var(--step-trace-chart-label-color);
}
.step-trace .pf-content-middle .chart-wrap.chart-show {
  width: calc(50% - 7.5px);
}
.step-trace .image-noData {
  width: 100%;
  height: calc(100% - 52px);
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}
.step-trace .image-noData p {
  font-size: 16px;
  padding-top: 10px;
}
.step-trace .image-noData.svg {
  height: 100%;
}
.step-trace .el-icon-info {
  font-size: 18px;
  color: #6c7280;
}
</style>

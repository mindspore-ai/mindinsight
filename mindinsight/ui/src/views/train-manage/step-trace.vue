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
      <div class="pf-content-right">
        <div class="input-wrap">
          <label>{{$t('profiling.stepSelect')}}</label>
          <el-select v-model="selectedStep"
                     filterable
                     :placeholder="$t('profiling.selectStep')"
                     @change="changeStep">
            <el-option v-for="item in steps"
                       :key="item.value"
                       :label="item.label"
                       :value="item.value">
            </el-option>
          </el-select>
        </div>
      </div>
    </div>
    <div class="pf-content-middle"
         v-show="!tabsArr[0].noData && !tabsArr[1].noData && !tabsArr[2].noData && !svg.noData">
      <div id="trace-container">
        <div id="trace"
             class="training-trace">
          <div :title="$t('graph.downloadPic')"
               class="download-button"
               @click="downloadSVG">
          </div>
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
        <div class="image-noData svg"
             v-if="svg.data.length === 0">
          <div>
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
          </div>
          <p>{{$t("public.noData")}}</p>
        </div>
      </div>

      <div v-for="(item,key) in tabsArr"
           :key="key"
           class="chart-wrap">
        <div class="title">{{ item.name }}</div>
        <div class="rate-wrap">
          <div v-if="item.timeSummary.total_time !== undefined && item.timeSummary[item.rate] !== undefined">
            <span>{{item.timeLabel}}:</span>
            {{(item.timeSummary.total_time*parseFloat(item.timeSummary[item.rate])/100).toFixed(4)}}ms</div>
          <div v-if="item.timeSummary[item.rate] !== undefined">
            <span>{{item.rateLabel}}:</span>{{item.timeSummary[item.rate]}}</div>
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
          <p>{{$t("public.noData")}}</p>
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
      steps: [],
      selectedStep: '',
      charts: [],
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
          noData: false,
        },
        {
          name: 'Fp+bp',
          id: 'fp-bp',
          timeSummary: {},
          rate: 'fp_and_bp',
          timeLabel: this.$t('profiling.fpBpTimeLabel'),
          rateLabel: this.$t('profiling.fpBpRateLabel'),
          noData: false,
        },
        {
          name: this.$t('profiling.lterationTail'),
          id: 'tailing',
          timeSummary: {},
          rate: 'tail',
          timeLabel: this.$t('profiling.tailTimeLabel'),
          rateLabel: this.$t('profiling.tailRateLabel'),
          noData: false,
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
          this.svg.noData = false;
          this.tabsArr.forEach((val) => {
            val.noData = false;
          });
          this.init();
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
      this.setStep();
      this.getTimeInfo('fp-bp', 'fp_and_bp');
      this.getTimeInfo('iter-gap', 'iteration_interval');
      this.getTimeInfo('tailing', 'tail');
      this.queryTrainingTrace(0);
    },
    changeStep(value) {
      if (value === this.$t('profiling.showAverage')) {
        value = 0;
      }
      this.queryTrainingTrace(value);
    },
    getTimeInfo(id, type) {
      const params = {
        dir: this.relativePath,
        type,
        device_id: this.deviceId,
      };
      RequestService.targetTimeInfo(params).then(
          (res) => {
            if (res.data && res.data.summary) {
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
            if (res.data && res.data.info) {
              if (this.steps.length <= 1) {
                this.setStep(res.data.size);
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
                    data: this.steps.map((val, index) => index + 1),
                    name: 'step',
                    max: this.steps.length,
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
                    bottom: 20,
                  },
                  series: timeInfo,
                  tooltip: {
                    trigger: 'axis',
                    confine: true,
                  },
                };
                if (type === 'iteration_interval') {
                  option.yAxis.name = `${this.$t(
                      'profiling.iterationGapTime',
                  )}(ms)`;
                  this.tabsArr[0].noData = this.steps.length ? false : true;
                } else if (type === 'fp_and_bp') {
                  option.yAxis.name = `fp+bp${this.$t('profiling.time')}(ms)`;
                  this.tabsArr[1].noData = this.steps.length ? false : true;
                } else if (type === 'tail') {
                  option.yAxis.name = `tail${this.$t('profiling.time')}(ms)`;
                  this.tabsArr[2].noData = this.steps.length ? false : true;
                }
                this.initChart(option, id);
              } else {
                this.steps = [];
                this.selectedStep = '';
              }
            }
          },
          (error) => {
            this.steps = [];
            this.selectedStep = '';
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
    setStep(step = 0) {
      this.steps = [];
      this.steps.push({
        label: this.$t('profiling.showAverage'),
        value: this.$t('profiling.showAverage'),
      });
      for (let i = 1; i <= step; i++) {
        this.steps.push({
          label: i,
          value: i,
        });
      }
      this.selectedStep = this.$t('profiling.showAverage');
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
        this.charts.forEach((val)=>{
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
              this.svg.data = [];
              this.svg.noData = true;
              this.removeTrace();
            }
          },
          (error) => {
            this.svg.data = [];
            this.svg.noData = true;
            this.removeTrace();
          },
      );
    },

    dealTraceData() {
      this.svg.totalWidth =
        document.querySelector('#trace').offsetWidth - this.svg.svgPadding * 2;
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
    downloadSVG() {
      const svgDom = document.querySelector('svg').outerHTML;
      const src = `data:image/svg+xml;base64,
      ${window.btoa(unescape(encodeURIComponent(svgDom)))}`;
      const a = document.createElement('a');
      a.href = src;
      a.download = new Date().valueOf();
      a.click();
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
    .pf-content-right {
      display: inline-block;
      margin-left: 35px;
      label {
        margin-right: 10px;
      }
    }
    .input-wrap {
      font-weight: normal;
    }
  }
  .pf-content-middle {
    padding: 15px 15px 0;
    height: calc(100% - 32px);
    #trace-container {
      width: 100%;
      height: 50%;
      border: 1px solid #ccc;
      overflow: auto;
      .training-trace {
        position: relative;
        height: 0;
        .download-button {
          display: none;
          position: absolute;
          width: 12px;
          height: 12px;
          right: 10px;
          top: 10px;
          cursor: pointer;
          background-image: url('../../assets/images/download.png');
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
      padding: 30px;
      border-radius: 4px;
      overflow: auto;
      &:last-child {
        margin-right: 0;
      }
      .chart {
        height: calc(100% - 85px);
        min-height: 180px;
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
}
</style>

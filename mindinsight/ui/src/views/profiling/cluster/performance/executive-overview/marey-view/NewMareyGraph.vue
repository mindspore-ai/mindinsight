<!--
Copyright 2022 Huawei Technologies Co., Ltd.All Rights Reserved.

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
  <div ref="container" class="marey-graph-container">
    <div
      class="marey-graph-tooltip"
      v-show="hoveredNodeInfo.show"
      :style="{
        transform: `translate3d(${hoveredNodeInfo.x}px, ${hoveredNodeInfo.y}px, 0px)`,
      }"
    >
      <div>{{ hoveredNodeInfo.class }}</div>
      <div>name: {{ hoveredNodeInfo.opName }}</div>
      <div v-show="!hoveredNodeInfo.isMareyGraph">
        time: {{ hoveredNodeInfo.xValue }}
      </div>
      <div v-show="!hoveredNodeInfo.isMareyGraph">
        {{ hoveredNodeInfo.type }}: {{ hoveredNodeInfo.yValue }}
      </div>
    </div>
    <div class="brush-switch">
      <svg id="icon-huanyuan" viewBox="0 0 1024 1024" @click="handleClickReset">
        <path
          d="M85.333333 468.949333l-2.218666-0.042666-1.92-0.128a42.709333 42.709333 0 0 1-3.370667-0.469334l-1.749333-0.341333a26.368 26.368 0 0 1-2.474667-0.64l-2.474667-0.768a42.88 42.88 0 0 1-16.896-11.050667l3.370667 3.2a55.168 55.168 0 0 1-3.242667-3.072l-0.426666-0.469333a44.373333 44.373333 0 0 1-7.509334-11.349333l-1.066666-2.517334-0.768-2.176-0.682667-2.432a28.288 28.288 0 0 1-0.554667-2.602666l-0.341333-2.133334A49.450667 49.450667 0 0 1 42.666667 426.282667l0.085333 3.029333a51.285333 51.285333 0 0 1-0.085333-2.56V170.282667a42.666667 42.666667 0 0 1 85.333333 0v157.354666l125.141333-117.589333a426.666667 426.666667 0 0 1 496.469334-77.525333l11.392 6.101333a426.709333 426.709333 0 0 1-181.888 799.402667 426.666667 426.666667 0 0 1-426.922667-284.202667 42.624 42.624 0 1 1 80.469333-28.330667 341.290667 341.290667 0 0 0 654.762667-37.717333 341.333333 341.333333 0 0 0-167.68-374.485333A341.717333 341.717333 0 0 0 312.533333 271.36L193.024 383.573333 341.333333 383.616a42.666667 42.666667 0 0 1 42.368 37.674667L384 426.282667a42.666667 42.666667 0 0 1-42.666667 42.666666H85.333333z"
        ></path>
      </svg>
      <div>Whether to open the brush</div>
      <el-switch
        v-model="isOpenSwitch"
        active-color="#13ce66"
        inactive-color="#ccc"
        @change="handleSwitchChange"
      >
      </el-switch>
    </div>
    <svg
      id="marey-graph"
      :viewbox="`0 0 ${width} ${height}`"
      :width="width"
      :height="height"
    >
      <g
        id="marey-graph-group"
        :transform="`translate(${margin.left}, ${margin.top})`"
        @dblclick="handleDblclick"
      >
        <g class="stage-device-line">
          <rect
            v-for="name in stageDeviceArr"
            :key="name"
            x="0"
            :y="yScale(name) - offset"
            :width="innerWidth"
            :height="2 * offset"
            style="stroke: #cecece; stroke-width: 1px; fill: none"
          ></rect>
        </g>
        <defs>
          <clipPath id="clip">
            <rect
              x="0"
              :y="-offset"
              :width="innerWidth"
              :height="innerHeight"
            />
          </clipPath>
        </defs>
        <!-- marey-graph -->
        <g class="marey-graph" clip-path="url(#clip)">
          <polygon
            v-for="(data, index) in polygonData"
            class="marey-graph-polygon"
            :key="`${stepNumber}-${data.op}-${index}`"
            :points="data.data"
            :fill="OperatorColor.get(getOperatorType(data.op))"
            fill-opacity="0.5"
            :stroke="
              highLightOpSet && highLightOpSet.has(data.op) ? 'black' : ''
            "
            stroke-width="2px"
            @mousemove="onNodeMouseover($event, data, 'device')"
            @mouseout="onNodeMouseout"
            @click="handleClick(data.op, data.device)"
          />
        </g>
        <!-- stage-marey-graph -->
        <g class="stage-marey-graph" clip-path="url(#clip)">
          <polygon
            v-for="(data, index) in stagePolygonData"
            class="stage-marey-graph-polygon"
            :key="`${stepNumber}-stage-${data.op}-${index}`"
            :points="data.data"
            fill="#789395"
            fill-opacity="0.8"
            :stroke="
              highLightOpSet && highLightOpSet.has(data.op) ? 'black' : ''
            "
            stroke-width="2px"
            @mousemove="onNodeMouseover($event, data, 'stage')"
            @mouseout="onNodeMouseout"
          />
        </g>
        <g v-if="isOpenSwitch" class="brush"></g>
        <!-- flops-chart -->
        <g class="flops-chart" clip-path="url(#clip)">
          <path
            v-for="(d, i) in MFLOPsData.filter((arr, index) =>
              stageDeviceArr.includes(arr[0].device)
            )"
            :key="`FLOPs-Chart-${i}`"
            :d="MFLOPsLinePath(d)"
            class="performance-cls-2"
            @mousemove="onNodeMouseover($event, d, 'FLOPs')"
            @mouseout="onNodeMouseout"
          />
        </g>
        <!--memory-chart  -->
        <g class="memory-chart" clip-path="url(#clip)">
          <path
            v-for="(d, i) in MemoryData.filter((arr, index) =>
              stageDeviceArr.includes(arr[0].device)
            )"
            :key="`Memory-Chart-${i}`"
            :d="MemoryLinePath(d)"
            class="performance-cls-3"
            @mousemove="onNodeMouseover($event, d, 'memory')"
            @mouseout="onNodeMouseout"
          />
        </g>
      </g>
    </svg>
  </div>
</template>

<script>
import * as d3 from "d3";
import { Switch, Icon } from "ant-design-vue";

const FBOP = "forward and backward propagation";
const CCOP = "collective communication";
const SOP = "send operator";
const ROP = "receive operator";
const OuterLayer = "OuterLayer";
const MiddleLayer = "MiddleLayer";
const InnerLayer = "InnerLayer";

export default {
  name: "MareyGraph",
  components: {
    "a-switch": Switch,
    "a-icon": Icon,
  },
  props: {
    stepNumber: Number,
    stageDeviceArr: Array,
    timeLineData: Object,
    FLOPsData: Object,
    MemoryDataProps: Object,
    deviceToStage: Map,
  },
  watch: {
    stageDeviceArr: function (newVal, oldVal) {
      if (oldVal.length) {
        this.height += (newVal.length - oldVal.length) * 10;
      }
      this.stageMareyGraphRender();
      this.mareyGraphReRender();
    },
    timeLineData: function () {
      this.stageDataProcessing();
      this.stageMareyGraphRender();

      this.timeLineDataProcessing();
      this.mareyGraphReRender();
      this.nameScopeProcessing();
    },
    FLOPsData: function () {
      requestIdleCallback(this.FLOPsDataProcessing);
    },
    MemoryDataProps: function () {
      requestIdleCallback(this.MemoryDataProcessing);
    },
    nameScope: function (newVal, oldVal) {
      const opArr = this.nameScopeToOp.get("/" + newVal);
      if (!opArr || !opArr.length) {
        return;
      }
      let minT = Infinity;
      let maxT = -Infinity;
      opArr.forEach((op) => {
        const curOpDeviceData = this.displayedData[op] || [];
        curOpDeviceData.forEach((dt) => {
          minT = Math.min(dt.x1, minT);
          maxT = Math.max(dt.x2, maxT);
        });
      });
      if (minT === Infinity || maxT === -Infinity) {
        return;
      }
      this.highLightOpSet = new Set(opArr);
      this.reRenderChart(minT, maxT);
    },
    errorOp: function () {
      const opName = this.errorOp;
      let minT = Infinity;
      let maxT = -Infinity;
      const curOpDeviceData = this.displayedData[opName] || [];
      curOpDeviceData.forEach((dt) => {
        minT = Math.min(dt.x1, minT);
        maxT = Math.max(dt.x2, maxT);
      });
      if (minT === Infinity || maxT === -Infinity) {
        return;
      }

      this.highLightOpSet = new Set([opName]);
      this.reRenderChart(minT, maxT);
    },
    dataSource: function (newVal) {
      this.isOpenFilter = newVal === "pangu_16p_0115";
    },
  },
  data() {
    return {
      svg: null,
      g: null,
      margin: { top: 50, right: 50, bottom: 10, left: 0 },
      width: 1000,
      height: 200,
      offset: 8,

      data: null,
      deviceName: null,
      stageName: null,
      minT: Number.MAX_VALUE,
      maxT: Number.MIN_VALUE,
      constantMinT: 0,
      constantMaxT: 0,
      timeStack: [],
      displayedData: null,
      stageDisplayedData: null,
      polygonData: [],
      stagePolygonData: [],
      MFLOPsData: [],
      MFLOPs: { min: 0, max: 0 },
      MemoryData: [],
      Memory: { min: 0, max: 0 },
      nameScopeToOp: null,
      opToNameScope: null,
      highLightOpSet: null,

      hoveredNodeInfo: {
        show: false,
        isMareyGraph: false,
        x: 0,
        y: 0,
        opName: "",
        class: "",
        xValue: 0,
        yValue: 0,
        type: "",
      },
      OperatorColor: new Map(),
      OperatorColorOpacity: new Map(),
      isOpenSwitch: true,
      isOpenFilter: false,
    };
  },
  computed: {
    innerWidth() {
      return this.width - this.margin.left - this.margin.right;
    },
    innerHeight() {
      return this.height - this.margin.top - this.margin.bottom;
    },
    yScale() {
      return d3
        .scaleBand()
        .domain(this.stageDeviceArr)
        .range([0, this.innerHeight]);
    },
    xScale() {
      return d3
        .scaleLinear()
        .domain([this.minT, this.maxT])
        .range([0, this.innerWidth]);
    },
    MFLOPsScale() {
      return d3
        .scaleLinear()
        .domain([this.MFLOPs.min, this.MFLOPs.max])
        .range([this.offset, -this.offset]);
    },
    MemoryScale() {
      return d3
        .scaleLinear()
        .domain([this.Memory.min, this.Memory.max])
        .range([this.offset, -this.offset]);
    },
    MFLOPsLinePath() {
      return d3
        .line()
        .x((d) => this.xScale(d.x))
        .y((d) => this.yScale(d.device) + this.MFLOPsScale(d.y));
    },
    MemoryLinePath() {
      return (
        d3
          .line()
          .x((d) => this.xScale(d.x))
          .y((d) => this.yScale(d.device) + this.MemoryScale(d.y))
      );
    },
    nameScope() {
      return this.$store.state.nameScopeToPerformanceView;
    },
    brush() {
      return d3
        .brushX() // Add the brush feature using the d3.brush function
        .extent([
          [0, -this.offset],
          [this.innerWidth, this.height - 3 * this.offset],
        ]) // initialise the brush area: start at 0,0 and finishes at width,height: it means I select the whole graph area
        .on("end", this.updateChart);
    },
    errorOp() {
      return this.$store.state.selectErrorOp;
    },
    dataSource() {
      return this.$store.state.dataSource;
    },
  },
  mounted() {
    const { width, height } = this.$refs.container.getBoundingClientRect();

    this.width = Math.floor(width);
    this.height = Math.floor(height);

    this.svg = d3.select("#marey-graph");
    this.g = d3.select("#marey-graph-group");

    this.initColor();
    this.initBrush();
  },
  methods: {
    initColor() {
      this.OperatorColor.set(FBOP, "#74ba62");
      this.OperatorColor.set(SOP, "#bf73d6");
      this.OperatorColor.set(ROP, "#4192d3");
      this.OperatorColor.set(CCOP, "#e6882e");
    },
    stageMareyGraphRender(left = Number.MIN_VALUE, right = Number.MAX_VALUE) {
      if (!this.stageDisplayedData) {
        return;
      }
      const priorityQueue = [];
      const stagePolygonData = [];
      const offset = 100;
      Object.keys(this.stageDisplayedData).forEach((op) => {
        const curOpStageData = this.stageDisplayedData[op];
        for (let i = 0; i < curOpStageData.length; i++) {
          const d = curOpStageData[i];
          if (d.x[0] < left - offset || d.x[d.x.length - 1] > right + offset) {
            continue;
          }
          for (let j = 1; j < d.x.length; j++) {
            if(d.x.length > 2) {
              console.log(d)
            }
            const x1 = d.x[j - 1];
            const x2 = d.x[j];
            const area = `${this.xScale(x1)},${this.yScale(d.y) - this.offset} 
            ${this.xScale(x1)},${ this.yScale(d.y) + this.offset} 
            ${this.xScale(x2)},${this.yScale(d.y) + this.offset} 
            ${this.xScale(x2)},${this.yScale(d.y) - this.offset}`;
            const areaObj = {
              op,
              data: area,
              stage: d.y,
            };
            if (this.highLightOpSet && this.highLightOpSet.has(op)) {
              priorityQueue.push(areaObj);
            } else {
              stagePolygonData.push(areaObj);
            }
          }
        }
      });
      if (stagePolygonData.length > 100) {
        stagePolygonData.sort((objA, objB) => {
          const xA = parseFloat(
            objA.data.split(" ").map((item) => item.split(","))[0][0]
          );
          const xB = parseFloat(
            objB.data.split(" ").map((item) => item.split(","))[0][0]
          );
          return xA - xB;
        });

        stagePolygonData.sort((objA, objB) => {
          const yA = parseFloat(
            objA.data.split(" ").map((item) => item.split(","))[0][1]
          );
          const yB = parseFloat(
            objB.data.split(" ").map((item) => item.split(","))[0][1]
          );
          return yA - yB;
        });

        let filterRes = [stagePolygonData[0]];
        for (let i = 1; i < stagePolygonData.length; i++) {
          const preRect = filterRes[filterRes.length - 1];
          const currentRectangle = stagePolygonData[i];
          if (
            this.getOperatorType(preRect.op) !==
            this.getOperatorType(currentRectangle.op)
          ) {
            filterRes.push(stagePolygonData[i]);
          } else {
            let preRectDataArr = preRect.data.split(" ");
            let currentRectangleDataArr = currentRectangle.data.split(" ");

            preRectDataArr = preRectDataArr.map((item) =>
              item.split(",").map((d) => parseFloat(d))
            );
            currentRectangleDataArr = currentRectangleDataArr.map((item) =>
              item.split(",").map((d) => parseFloat(d))
            );
            let [preLeftTop, preLeftBottom, preRightBottom, preRightTop] =
              preRectDataArr;
            let [curLeftTop, curLeftBottom, curRightBottom, curRightTop] =
              currentRectangleDataArr;
            const threshold = this.innerWidth * 0.01;
            if (
              preLeftTop[1] !== curLeftTop[1] ||
              preLeftBottom[1] !== curLeftBottom[1] ||
              Math.max(
                Math.abs(curLeftTop[0] - preRightTop[0]),
                Math.abs(curLeftBottom[0] - preRightBottom[0])
              ) > threshold
            ) {
              filterRes.push(stagePolygonData[i]);
            } else {
              preLeftTop[0] = Math.min(preLeftTop[0], curLeftTop[0]);
              preLeftBottom[0] = Math.min(preLeftBottom[0], curLeftBottom[0]);
              preRightBottom[0] = Math.max(
                preRightBottom[0],
                curRightBottom[0]
              );
              preRightTop[0] = Math.max(preRightTop[0], curRightTop[0]);
              const data = [
                preLeftTop,
                preLeftBottom,
                preRightBottom,
                preRightTop,
              ]
                .map((item) => item.join(","))
                .join(" ");

              preRect.data = data;
            }
          }
        }

        if (this.isOpenFilter) {
          filterRes = filterRes.filter((item, index) => index % 2);
        }
        filterRes.push(...priorityQueue);
        this.stagePolygonData = filterRes;
      } else {
        stagePolygonData.push(...priorityQueue);
        this.stagePolygonData = stagePolygonData;
      }
    },
    mareyGraphReRender(left = Number.MIN_VALUE, right = Number.MAX_VALUE) {
      if (!this.displayedData) {
        return;
      }
      let polygonData = [];
      const priorityQueue = [];
      const offset = 100;
      Object.keys(this.displayedData).forEach((op) => {
        const curOpDeviceData = this.displayedData[op];
        if (this.highLightOpSet && this.highLightOpSet.has(op)) {
          let points = "";
          const deviceArr = [];
          for (let i = 0; i < curOpDeviceData.length; i++) {
            const dt = curOpDeviceData[i];
            if (
              dt.x1 < left - offset ||
              dt.x2 > right + offset ||
              !this.stageDeviceArr.includes(dt.y)
            ) {
              continue;
            }
            points += `${this.xScale(dt.x1)},${
              this.yScale(dt.y) - this.offset
            } ${this.xScale(dt.x1)},${this.yScale(dt.y) + this.offset} `;
            deviceArr.push(dt.y);
          }
          for (let i = curOpDeviceData.length - 1; i >= 0; i--) {
            const dt = curOpDeviceData[i];
            if (
              dt.x1 < left - offset ||
              dt.x2 > right + offset ||
              !this.stageDeviceArr.includes(dt.y)
            ) {
              continue;
            }
            points += `${this.xScale(dt.x2)},${
              this.yScale(dt.y) + this.offset
            } ${this.xScale(dt.x2)},${this.yScale(dt.y) - this.offset} `;
          }
          priorityQueue.push({
            op,
            data: points,
            device: deviceArr,
            type: "selected",
          });
          return;
        }
        const areaArr = [];
        let pointsArr = [];
        let preDevice = "";
        for (let i = 0; i < curOpDeviceData.length; i++) {
          const dt = curOpDeviceData[i];
          if (
            dt.x1 < left - offset ||
            dt.x2 > right + offset ||
            !this.stageDeviceArr.includes(dt.y)
          ) {
            continue;
          }
          const areaD = `${this.xScale(dt.x1)},${
            this.yScale(dt.y) - this.offset
          } ${this.xScale(dt.x1)},${
            this.yScale(dt.y) + this.offset
          } ${this.xScale(dt.x2)},${
            this.yScale(dt.y) + this.offset
          } ${this.xScale(dt.x2)},${this.yScale(dt.y) - this.offset}`;
          areaArr.push({
            op,
            data: areaD,
            device: [dt.y],
            type: "block",
          });

          const leftBottom = `${this.xScale(dt.x1)},${
            this.yScale(dt.y) + this.offset
          }`;
          const rightBootm = `${this.xScale(dt.x2)},${
            this.yScale(dt.y) + this.offset
          }`;

          if (i === 0) {
            pointsArr.push(leftBottom, rightBootm);
            preDevice = dt.y;
          } else if (i > 0) {
            const leftTop = `${this.xScale(dt.x1)},${
              this.yScale(dt.y) - this.offset
            }`;
            const rightTop = `${this.xScale(dt.x2)},${
              this.yScale(dt.y) - this.offset
            }`;
            pointsArr.splice(1, 0, leftTop, rightTop);
            areaArr.push({
              op,
              data: pointsArr.join(" "),
              device: [preDevice, dt.y],
              type: "gap",
            });
            pointsArr = [leftBottom, rightBootm];
            preDevice = dt.y;
          }
        }
        if (areaArr.length) {
          polygonData.push(...areaArr);
        }
      });

      if (polygonData.length > 100) {
        polygonData.sort((objA, objB) => {
          const xA = parseFloat(
            objA.data.split(" ").map((item) => item.split(","))[0][0]
          );
          const xB = parseFloat(
            objB.data.split(" ").map((item) => item.split(","))[0][0]
          );
          return xA - xB;
        });

        polygonData.sort((objA, objB) => {
          const yA = parseFloat(
            objA.data.split(" ").map((item) => item.split(","))[0][1]
          );
          const yB = parseFloat(
            objB.data.split(" ").map((item) => item.split(","))[0][1]
          );
          return yA - yB;
        });

        let filterRes = [polygonData[0]];
        for (let i = 1; i < polygonData.length; i++) {
          const preRect = filterRes[filterRes.length - 1];
          const currentRectangle = polygonData[i];
          if (
            this.getOperatorType(preRect.op) !==
            this.getOperatorType(currentRectangle.op)
          ) {
            filterRes.push(polygonData[i]);
          } else {
            let preRectDataArr = preRect.data.split(" ");
            let currentRectangleDataArr = currentRectangle.data.split(" ");

            preRectDataArr = preRectDataArr.map((item) =>
              item.split(",").map((d) => parseFloat(d))
            );
            currentRectangleDataArr = currentRectangleDataArr.map((item) =>
              item.split(",").map((d) => parseFloat(d))
            );

            let [preLeftTop, preLeftBottom, preRightBottom, preRightTop] =
              preRectDataArr;
            let [curLeftTop, curLeftBottom, curRightBottom, curRightTop] =
              currentRectangleDataArr;

            const threshold = this.innerWidth * 0.01;

            if (
              preLeftTop[1] !== curLeftTop[1] ||
              preLeftBottom[1] !== curLeftBottom[1] ||
              Math.max(
                Math.abs(curLeftTop[0] - preRightTop[0]),
                Math.abs(curLeftBottom[0] - preRightBottom[0])
              ) > threshold
            ) {
              filterRes.push(polygonData[i]);
            } else {
              preLeftTop[0] = Math.min(preLeftTop[0], curLeftTop[0]);
              preLeftBottom[0] = Math.min(preLeftBottom[0], curLeftBottom[0]);
              preRightBottom[0] = Math.max(
                preRightBottom[0],
                curRightBottom[0]
              );
              preRightTop[0] = Math.max(preRightTop[0], curRightTop[0]);
              const data = [
                preLeftTop,
                preLeftBottom,
                preRightBottom,
                preRightTop,
              ]
                .map((item) => item.join(","))
                .join(" ");

              preRect.data = data;
            }
          }
        }
        if (this.isOpenFilter) {
          filterRes = filterRes.filter((item, index) => index % 2);
        }
        filterRes.push(...priorityQueue);
        this.polygonData = filterRes;
      } else {
        polygonData.push(...priorityQueue);
        this.polygonData = polygonData;
      }
    },
    nameScopeProcessing() {
      const { scope_map } = this.timeLineData || {};
      const map = new Map();
      Object.keys(scope_map).forEach((op) => {
        const nameScope = scope_map[op];
        if (!map.has(nameScope)) {
          map.set(nameScope, []);
        }
        map.get(nameScope).push(op);
      });
      this.opToNameScope = scope_map;
      this.nameScopeToOp = map;
    },
    timeLineDataProcessing() {
      const { maps } = this.timeLineData || {};
      this.data = maps;

      const devices = Object.keys(maps).sort((a, b) => {
        const [num1] = a.match(/\d+/g);
        const [num2] = b.match(/\d+/g);
        return parseInt(num1, 10) - parseInt(num2, 10);
      });
      this.deviceName = devices;

      let minT = Infinity,
        maxT = -Infinity;
      const displayedData = {};
      devices.forEach((deviceName) => {
        const curDeviceData = maps[deviceName];
        Object.keys(curDeviceData).forEach((op) => {
          if (!op.startsWith("Stream") && !op.startsWith("AtomicAddrClean")) {
            if (!displayedData[op]) displayedData[op] = [];
            const curOp = curDeviceData[op];
            minT = Math.min(curOp.st, minT);
            maxT = Math.max(curOp.ed, maxT);
            displayedData[op].push({
              x1: curOp.st,
              x2: curOp.ed,
              y: deviceName,
            });
          }
        });
      });
      if (minT < this.minT) {
        this.minT = minT;
      }
      if (maxT > this.maxT) {
        this.maxT = maxT;
      }
      this.timeStack.push([minT, maxT]);
      this.displayedData = displayedData;
    },
    stageDataProcessing() {
      const { stage_data } = this.timeLineData || {};
      const stages = Object.keys(stage_data);
      const stageDisplayedData = {};
      let minT = Infinity,
        maxT = -Infinity;
      stages.forEach((stageName) => {
        const curStageData = stage_data[stageName].data;
        Object.keys(curStageData).forEach((op) => {
          if (!op.startsWith("Stream") && !op.startsWith("AtomicAddrClean")) {
            if (!stageDisplayedData[op]) stageDisplayedData[op] = [];
            const curOp = curStageData[op];
            minT = Math.min(curOp.st_avg, minT);
            maxT = Math.max(curOp.ed_avg, maxT);
            stageDisplayedData[op].push({
              x: [
                curOp.st_avg,
                curOp.ed_avg,
              ],
              y: stageName,
            });
          }
        });
      });

      if (minT < this.minT) {
        this.minT = minT;
      }
      if (maxT > this.maxT) {
        this.maxT = maxT;
      }
      this.stageDisplayedData = stageDisplayedData;
    },
    getOperatorType(op) {
      if (op.startsWith("All")) {
        return CCOP;
      } else if (op.startsWith("Send")) {
        return SOP;
      } else if (op.startsWith("Receive")) {
        return ROP;
      } else {
        return FBOP;
      }
    },
    FLOPsDataProcessing() {
      if (!this.data) return;
      const MFLOPsData = [];
      let min = Infinity;
      let max = -Infinity;
      Object.keys(this.FLOPsData).forEach((device) => {
        const curDeviceMFIPsData = [];
        const arr = this.FLOPsData[device]["details"] || [];
        arr.forEach((opInfo) => {
          const opName = opInfo["op_full_name"].split("/").pop();
          const opData = this.data[device][opName];
          const x = opData ? (opData.st + opData.ed) / 2 : NaN;
          const y = parseFloat(opInfo[" MFLOPs(10^6)"], 10);
          if (
            !isNaN(x) &&
            !isNaN(y) &&
            !opName.startsWith("Stream") &&
            !opName.startsWith("AtomicAddrClean")
          ) {
            min = Math.min(min, y);
            max = Math.max(max, y);
            curDeviceMFIPsData.push({ x, y, device, opName });
          }
        });
        if (curDeviceMFIPsData.length) {
          curDeviceMFIPsData.sort((objA, objB) => objA.x - objB.x);
          MFLOPsData.push(curDeviceMFIPsData);
        }
      });
      this.MFLOPsData = MFLOPsData;
      this.MFLOPs.min = min;
      this.MFLOPs.max = max;
    },
    MemoryDataProcessing() {
      if (!this.data) return;
      const MemoryData = [];
      let min = Infinity;
      let max = -Infinity;

      Object.keys(this.MemoryDataProps).forEach((device) => {
        const curDeviceMemoryData = [];
        const { lines, nodes = [] } =
          this.MemoryDataProps[device]["details"]["1"] || {};

        for (let i = 0; i < nodes.length; i++) {
          const opName = nodes[i].name;
          const opData = this.data[device][opName];
          const x = opData ? (opData.st + opData.ed) / 2 : NaN;
          const y = parseFloat(lines[i], 10);

          if (
            !isNaN(x) &&
            !isNaN(y) &&
            !opName.startsWith("Stream") &&
            !opName.startsWith("AtomicAddrClean")
          ) {
            min = Math.min(min, y);
            max = Math.max(max, y);
            curDeviceMemoryData.push({ x, y, device, opName });
          }
        }
        if (curDeviceMemoryData.length) {
          curDeviceMemoryData.sort((objA, objB) => objA.x - objB.x);
          MemoryData.push(curDeviceMemoryData);
        }
      });
      this.MemoryData = MemoryData;
      this.Memory.min = min;
      this.Memory.max = max;
    },
    initBrush() {
      this.g.select(".brush").call(this.brush);
    },
    updateChart() {
      const extent = d3.event.selection;
      if (!extent) return;

      const [left, right] = extent.map((d) => this.xScale.invert(d));
      this.reRenderChart(left, right);

      this.g.select(".brush").call(this.brush.move, null); // This remove the grey brush area as soon as the selection has been done
    },
    reRenderChart(left, right) {
      this.timeStack.push([this.minT, this.maxT]);
      this.minT = left;
      this.maxT = right;
      this.stageMareyGraphRender(left, right);
      this.mareyGraphReRender(left, right);
    },
    handleClick(opName, deviceArr) {
      const nameScope = this.opToNameScope[opName];
      if (!nameScope) {
        console.log("没有该命名空间");
        return;
      }
      const stageSet = new Set();
      deviceArr.forEach((device) => {
        const stage = this.deviceToStage.get(device);
        stageSet.add(stage);
      });
      this.$store.commit("setNameScopeToParallelStrategy", {
        nameScope,
        opName,
        stage: [...stageSet],
      });
    },
    handleDblclick() {
      console.log("双击");
      if (!this.timeStack.length) {
        this.highLightOpSet = null;
        return;
      }
      const [preMinT, preMaxT] = this.timeStack.pop();
      this.minT = preMinT;
      this.maxT = preMaxT;
      this.stageMareyGraphRender(preMinT, preMaxT);
      this.mareyGraphReRender(preMinT, preMaxT);
    },
    onNodeMouseover(e, data, type) {
      const { layerX, layerY } = e || {};
      if (type === "stage") {
        const { op: opName, stage } = data || {};
        this.hoveredNodeInfo = {
          show: true,
          isMareyGraph: true,
          x: layerX + 15,
          y: layerY - 55,
          opName,
          type: data.type,
          class: stage,
          xValue: null,
          yValue: null,
        };
      } else if (type === "device") {
        const { op: opName, device } = data || {};
        this.hoveredNodeInfo = {
          show: true,
          isMareyGraph: true,
          x: layerX + 15,
          y: layerY - 55,
          opName,
          class: device.join("-"),
          xValue: null,
          yValue: null,
        };
      } else {
        const bisect = d3.bisector((d) => d.x).left;
        const x = this.xScale.invert(layerX - 50);
        const index = bisect(data, x);
        const { opName, device, x: xValue, y: yValue } = data[index];
        this.hoveredNodeInfo = {
          show: true,
          isMareyGraph: false,
          x: layerX + 15,
          y: layerY - 55,
          opName,
          class: device,
          type,
          xValue,
          yValue,
        };
      }
    },
    onNodeMouseout() {
      this.hoveredNodeInfo.show = false;
    },
    handleSwitchChange() {
      if (!this.isOpenSwitch) {
        return;
      }
      this.$nextTick(() => {
        this.g.select(".brush").call(this.brush);
      });
    },
    handleClickReset() {
      console.log("重置");
      this.highLightOpSet = null;
      if (!this.timeStack.length) {
        return;
      }
      const [preMinT, preMaxT] = this.timeStack.shift();
      this.timeStack = [];
      this.minT = preMinT;
      this.maxT = preMaxT;
      this.stageMareyGraphRender(preMinT, preMaxT);
      this.mareyGraphReRender(preMinT, preMaxT);
    },
  },
};
</script>
<style scoped>
.marey-graph-container {
  position: relative;
  width: 100%;
  height: 100%;
}
#marey-graph-group {
  background: #ccc;
  position: relative;
}
.performance-cls-2,
.performance-cls-3 {
  fill: none;
  stroke-miterlimit: 10;
}
.performance-cls-2 {
  stroke: var(--performance-flops);
}
.performance-cls-3 {
  stroke: var(--performance-memory);
}
.marey-graph-polygon {
  pointer-events: fill;
}
.marey-graph-tooltip {
  position: absolute;
  top: 0px;
  left: 0px;
  padding: 10px;
  opacity: 0.8;
  width: fit-content;
  height: fit-content;
  background-color: #fff;
  border: 1px solid #fff;
  box-shadow: rgba(0, 0, 0, 0.2) 1px 2px 10px;
  border-radius: 4px;
  pointer-events: none;
  padding: 10px;
  z-index: 99;
  font: 14px / 21px sans-serif;
  color: #333;

  border-style: solid;
  white-space: nowrap;
  box-shadow: rgba(0, 0, 0, 0.2) 1px 2px 10px;
  transition: opacity 0.2s cubic-bezier(0.23, 1, 0.32, 1) 0s,
    visibility 0.2s cubic-bezier(0.23, 1, 0.32, 1) 0s,
    transform 0.4s cubic-bezier(0.23, 1, 0.32, 1) 0s;
}
.brush {
  pointer-events: none;
}
.brush-switch {
  position: absolute;
  top: 0;
  right: 0;
  display: flex;
  line-height: 20px;
}
.brush-switch div {
  margin-left: 10px;
  margin-right: 4px;
}

.brush-switch svg {
  width: 16px;
  height: 16px;
  margin: 2px 0;
  cursor: pointer;
}
</style>

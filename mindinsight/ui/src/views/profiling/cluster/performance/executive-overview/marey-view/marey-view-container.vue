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
  <div id="marey-view-container">
    <div
      class="tooltip"
      v-show="hoveredNodeInfo.show"
      :style="{
        transform: `translate(${hoveredNodeInfo.x}px, ${hoveredNodeInfo.y}px)`,
      }"
    >
      <div>{{ hoveredNodeInfo.title }}</div>
      <template v-if="Array.isArray(hoveredNodeInfo.content)">
        <div v-for="text in hoveredNodeInfo.content" :key="`${text}`">
          {{ text }}
        </div>
      </template>
      <template v-else>
        <div
          v-for="(text, index) in hoveredNodeInfo.content"
          :key="`${text}-${index}`"
        >
          {{ index }}:{{ text }}
        </div>
      </template>
    </div>
    <div class="legend">
      <legend-performance />
    </div>
    <div class="brush-switch">
      <div>{{ $t("profilingCluster.openBrush") }}</div>
      <el-switch
        v-model="isOpenSwitch"
        active-color="#13ce66"
        inactive-color="#ccc"
        @change="handleSwitchChange"
      >
      </el-switch>
    </div>
    <div class="content">
      <div class="view" ref="container">
        <canvas
          ref="graph"
          class="graph"
          :width="width - margin.left - margin.padding - margin.right"
          :height="height - margin.top - margin.bottom"
          :style="{
            left: margin.left + margin.padding + 'px',
            top: margin.top + 'px',
          }"
        />
        <svg
          :viewbox="`0 0 ${width} ${height}`"
          :width="width"
          :height="height"
        >
          <defs>
            <clipPath id="clip">
              <rect x="0" y="0" :width="innerWidth" :height="innerHeight" />
            </clipPath>
          </defs>
          <g :transform="`translate(${margin.left}, ${margin.top})`">
            <g v-for="item in stageDeviceRelationship" :key="item.stage">
              <foreignObject
                x="0"
                :y="yScale(item.stage)"
                width="16"
                height="16"
                @click="clickStageMenu(item.stage)"
              >
                <svg
                  viewBox="0 0 1024 1024"
                  :transform="isStageExpand[item.stage] ? 'rotate(90)' : ''"
                >
                  <path
                    fill="#ccc"
                    d="M761.856 405.504l-255.68-170.432A128 128 0 0 0 307.2 341.568
                      v340.864a128 128 0 0 0 199.008 106.496l255.648-170.432a128 128 0 0 0 0-212.992z"
                  ></path>
                </svg>
              </foreignObject>
              <path
                fill="none"
                stroke="#ccc"
                :d="`M8,${yScale(item.stage) + bannerHeight} L8,${
                  10 + yScale(item.devices[item.devices.length - 1])
                }`"
              />
              <text
                x="30"
                :y="yScale(item.stage) + bannerHeight"
                dominant-baseline="middle"
              >
                {{ item.stage }}
              </text>

              <template v-if="isStageExpand[item.stage]">
                <text
                  v-for="device in item.devices"
                  :key="device + '-text'"
                  x="30"
                  :y="yScale(device) + bannerHeight"
                  dominant-baseline="middle"
                >
                  {{ device }}
                </text>

                <path
                  v-for="device in item.devices"
                  :key="device + '-path'"
                  fill="none"
                  stroke="#ccc"
                  :d="`M8,${yScale(device) + 10} L30,${yScale(device) + 10}`"
                  dominant-baseline="middle"
                />
              </template>
            </g>
          </g>
          <g :transform="`translate(${margin.left}, 0)`">
            <template v-for="data in memoryDataInfo">
              <rect
                v-if="yScale(data.y) !== undefined"
                :key="`${data.y}-${data.x}`"
                :x="infoXScale(data.x) - bannerHeight"
                :y="yScale(data.y) + bannerHeight"
                :width="bannerHeight * 2"
                :height="bannerHeight * 2"
                :fill="colorScale(data.value)"
                :stroke="colorScale(0.5)"
                @mouseover="onMouseOverInfo($event, data, 'memory')"
                @mouseout="onMouseOutInfo"
              ></rect>
            </template>

            <template v-for="data in flopsDataInfo">
              <rect
                v-if="yScale(data.y) !== undefined"
                :key="`${data.y}-${data.x}`"
                :x="infoXScale(data.x) - bannerHeight"
                :y="yScale(data.y) + bannerHeight"
                :width="bannerHeight * 2"
                :height="bannerHeight * 2"
                :fill="colorScale(data.value)"
                :stroke="colorScale(0.5)"
                @mouseover="onMouseOverInfo($event, data, 'flops')"
                @mouseout="onMouseOutInfo"
              ></rect>
            </template>
          </g>
          <g
            :transform="`translate(${margin.left + margin.padding}, ${
              margin.top
            })`"
            @dblclick="handleDoubleClick"
            clip-path="url(#clip)"
          >
            <g v-for="item in stageDeviceRelationship" :key="item.stage">
              <rect
                x="0"
                :y="yScale(item.stage)"
                :width="innerWidth"
                :height="2 * bannerHeight"
                class="stage-banner"
              />

              <template v-if="isStageExpand[item.stage]">
                <rect
                  v-for="device in item.devices"
                  :key="device"
                  x="0"
                  :y="yScale(device)"
                  :width="innerWidth"
                  :height="2 * bannerHeight"
                  class="stage-banner"
                  @mousemove="onMouseOverPolygon($event, device)"
                  @mouseout="onMouseOutInfo"
                />
              </template>
            </g>

            <g ref="g"></g>

            <g class="flops-chart" clip-path="url(#clip)">
              <template v-for="d in FLOPsData">
                <path
                  v-if="isStageExpand[d.stage]"
                  :key="d.device"
                  :transform="`translate(0, ${yScale(d.device)})`"
                  :d="MFLOPsLinePath(d.data)"
                  class="performance-cls-2"
                  @mousemove="onMouseOverInfo($event, d.data, 'chart')"
                  @mouseout="onMouseOutInfo"
                />
              </template>
            </g>

            <g class="memory-chart" clip-path="url(#clip)" v-if="memoryData">
              <template v-for="d in memoryData">
                <path
                  v-if="isStageExpand[d.stage]"
                  :key="`memory-${d.device}`"
                  :transform="`translate(0, ${yScale(d.device)})`"
                  :d="memoryLinePath(d.data)"
                  class="performance-cls-3"
                  @mousemove="onMouseOverInfo($event, d.data, 'chart')"
                  @mouseout="onMouseOutInfo"
                />
              </template>
            </g>
          </g>
        </svg>
      </div>
    </div>
  </div>
</template>

<script>
import * as d3 from "d3";
import $store from "../store";
import LegendPerformance from "./LegendPerformance.vue";
import RequestService from "@/services/request-service";
import { mergeNearbyRects, mergeNearbyGap } from "./util";

const FBOP = "f";
const CCOP = "c";
const SOP = "s";
const ROP = "r";

// remove unimportant operator nodes
const filterNode = (op) => {
  return !op.startsWith("Stream") && !op.startsWith("AtomicAddrClean");
};

export default {
  components: {
    LegendPerformance,
  },
  data() {
    return {
      width: 0,
      height: 0,
      top: 0,
      elementHeight: 0,
      margin: {
        top: 10,
        right: 10,
        bottom: 0,
        left: 10,
        padding: 200,
      },
      // half bannerHeight
      bannerHeight: 10,
      operatorColor: {
        [FBOP]: "#74ba62",
        [SOP]: "#bf73d6",
        [ROP]: "#4192d3",
        [CCOP]: "#e6882e",
      },
      isStageExpand: {},
      stageDeviceRelationship: [],
      minT: Number.MAX_VALUE,
      maxT: Number.MIN_VALUE,
      timeLineData: null,
      // deviceDisplayedData: null,
      stagePolygon: [],
      devicePolygon: [],
      deviceGapPolygon: [],
      device2PolygonIndex: {},
      timeStack: [], // store time extent

      FLOPsData: null,
      mFLOPsMin: Number.MAX_VALUE,
      mFLOPsMax: Number.MIN_VALUE,
      flopsDataInfo: [],
      memoryData: null,
      memoryDataInfo: [],
      scopeMap: {},

      isOpenSwitch: true, // open brush
      hoveredNodeInfo: {
        show: false,
        x: 0,
        y: 0,
        title: "",
        content: {},
      },
    };
  },
  created() {
    this.deviceDisplayedData = null;
  },
  watch: {
    stageDeviceArr(newV) {
      const minHeight =
        this.bannerHeight * 2 * newV.length +
        this.bannerHeight * 2 * (newV.length - 1);
      this.height = Math.max(minHeight, this.elementHeight);

      if (this.isOpenSwitch) {
        this.initBrush();
      }
    },
    stepNumber(newV) {
      this.getTimeLineData();
      this.getScopeData();
    },
  },
  computed: {
    stepNumber() {
      return $store.state.stepNum;
    },
    stageDeviceArr() {
      const stageDeviceArr = [];
      this.stageDeviceRelationship.forEach(({ stage, devices }) => {
        stageDeviceArr.push(stage);
        if (this.isStageExpand[stage]) {
          stageDeviceArr.push(...devices);
        }
      });

      return stageDeviceArr;
    },
    innerHeight() {
      return this.height - this.margin.top - this.margin.bottom;
    },
    innerWidth() {
      return (
        this.width - this.margin.left - this.margin.right - this.margin.padding
      );
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
    infoXScale() {
      return d3
        .scaleBand()
        .domain(["FLOPs", "FLOPS", "PeakMem"])
        .range([
          this.margin.left + this.margin.padding / 2,
          this.margin.padding + this.margin.left,
        ]);
    },
    colorScale() {
      return d3.scaleLinear().domain([0, 1]).range(["#fff", "#000"]);
    },
    threshold() {
      return this.innerWidth * 0.01;
    },
    MFLOPsScale() {
      return d3
        .scaleLinear()
        .domain([this.mFLOPsMin, this.mFLOPsMax])
        .range([this.bannerHeight * 2, 0]);
    },
    MFLOPsLinePath() {
      return (
        d3
          .line()
          .x((d) => this.xScale(d.x))
          .y((d) => this.MFLOPsScale(d.y))
      );
    },
    memoryScale() {
      return d3
        .scaleLinear()
        .domain([this.memoryMin, this.memoryMax])
        .range([this.bannerHeight * 2, 0]);
    },
    memoryLinePath() {
      return d3
        .line()
        .x((d) => this.xScale(d.x))
        .y((d) => this.memoryScale(d.y));
    },
  },
  mounted() {
    this.getBoundingRect();
    this.getTimeLineData();
    this.initBrush();
    this.getScopeData();
  },
  methods: {
    initBrush() {
      const brush = d3
        .brushX()
        .extent([
          [0, 0],
          [this.innerWidth, this.innerHeight],
        ])
        .on("end", this.updateChart);
      this.brush = brush;
      d3.select(this.$refs.g).call(this.brush);
    },
    updateChart() {
      const extent = d3.event.selection;
      if (!extent) return;

      const [left, right] = extent.map((d) => this.xScale.invert(d));
      this.timeStack.push([this.minT, this.maxT]);
      this.reRenderChart(left, right);

      d3.select(this.$refs.g).call(this.brush.move, null);
    },
    reRenderChart(left, right) {
      this.minT = left;
      this.maxT = right;
      this.processStageData(left, right);
      this.processDeviceData(left, right);
      this.render();
    },
    getBoundingRect() {
      const { width, height, top } =
        this.$refs.container.getBoundingClientRect();

      this.width = Math.floor(width);
      this.height = Math.floor(height);
      this.top = top;
      this.elementHeight = Math.floor(height - 15);
    },
    getScopeData() {
      const params = {
        train_id: this.$route.query.path,
        device_type: "ascend",
        step: this.stepNumber,
      };
      RequestService.getScopeMap(params)
        .then(({ data }) => {
          this.scopeMap = Object.freeze(data.scope_map);
        })
        .catch((err) => {
          console.log(err);
        });
    },
    getTimeLineData() {
      RequestService.getTimeLineData(this.$route.query.path, this.stepNumber)
        .then(({ data }) => {
          const { stage_data, maps } = data || {};
          const stages = Object.keys(stage_data);
          const stageDisplayedData = [];
          const deviceDisplayedData = {};

          let minT = Infinity;
          let maxT = -Infinity;
          for (let i = 0; i < stages.length; i++) {
            let curStartOffset = 0;
            let curEndOffset = 0;
            if (i !== 0) {
              // timestamp alignment
              const preDevice = stage_data[stages[i - 1]].devices[0];
              const curDevice = stage_data[stages[i]].devices[0];

              const { startOffset, endOffset } =
                this.getOffsetBetweenStageByDevice(
                  maps[preDevice],
                  maps[curDevice]
                );

              curStartOffset = startOffset;
              curEndOffset = endOffset;
            }

            const curStageData = stage_data[stages[i]].data;

            Object.keys(curStageData).forEach((op) => {
              if (filterNode(op)) {
                const curOp = curStageData[op];
                curOp.st_avg += curStartOffset;
                curOp.ed_avg += curEndOffset;

                minT = Math.min(curOp.st_avg, minT);
                maxT = Math.max(curOp.ed_avg, maxT);

                stageDisplayedData.push({
                  x1: curOp.st_avg,
                  x2: curOp.ed_avg,
                  y: stages[i],
                  op,
                  type: this.getOperatorType(op),
                });
              }
            });

            const curDevice = stage_data[stages[i]].devices.sort((a, b) => {
              const [num1] = a.match(/\d+/g);
              const [num2] = b.match(/\d+/g);

              return +num1 - +num2;
            });

            curDevice.forEach((device, deviceIndex) => {
              if (!deviceDisplayedData[stages[i]]) {
                deviceDisplayedData[stages[i]] = {};
              }
              const curStageDeviceData = deviceDisplayedData[stages[i]];

              Object.keys(maps[device]).forEach((op) => {
                if (filterNode(op)) {
                  if (!curStageDeviceData[op]) curStageDeviceData[op] = [];

                  const curOp = maps[device][op];
                  curOp.st += curStartOffset;
                  curOp.ed += curEndOffset;

                  minT = Math.min(curOp.st, minT);
                  maxT = Math.max(curOp.ed, maxT);
                  curStageDeviceData[op].push({
                    y: device,
                    x1: curOp.st,
                    x2: curOp.ed,
                  });
                }
              });

              deviceDisplayedData[stages[i]] = curStageDeviceData;
            });
          }

          stageDisplayedData.sort((a, b) => {
            if (a.type !== b.type) {
              return a.type - b.type;
            } else if (a.x1 !== b.x1) {
              return a.x1 - b.x1;
            } else {
              return a.y.localCompare(b.y);
            }
          });

          Object.keys(deviceDisplayedData).forEach((stage) => {
            const data = deviceDisplayedData[stage];
            const opArr = [];
            Object.keys(data).forEach((op) => {
              opArr.push({
                op,
                data: data[op],
              });
            });
            deviceDisplayedData[stage] = opArr;
          });

          this.timeLineData = Object.freeze(stageDisplayedData);
          this.deviceDisplayedData = Object.freeze(deviceDisplayedData);
          this.minT = minT;
          this.maxT = maxT;
          this.timeStack.push([minT, maxT]);
          this.opNameProcessing(maps);
          this.processStageDeviceRelationship(stage_data);

          const device2stage = {};
          Object.keys(stage_data).forEach((stage) => {
            stage_data[stage].devices.forEach((device) => {
              device2stage[device] = stage;
            });
          });

          this.getFLOPsData(maps, device2stage, stages);
          this.getMemoryData(maps, device2stage, stages);
          this.$nextTick(() => {
            this.processStageData();
            this.processDeviceData();
            this.render();
          });
        })
        .catch(console.error);
    },
    getFLOPsData(maps, device2stage, stages) {
      RequestService.getFLOPsData(this.$route.query.path)
        .then(({ data }) => {
          let maxFLOPS = -Infinity;
          let maxFLOPs = -Infinity;
          const flopsDataInfo = [];
          // every stage data
          const stageData = stages.reduce(
            (acc, cur) => ({
              ...acc,
              [cur]: {
                sumFLOPS: 0,
                sumFLOPs: 0,
                cnt: 0,
                isAnomaly: false,
                abnormalContent: [],
              },
            }),
            {}
          );

          const MFLOPsData = [];
          let min = Infinity;
          let max = -Infinity;
          Object.keys(data).forEach((device) => {
            // summary
            const {
              FLOPS = 0,
              FLOPs = 0,
              abnormalContent = [],
              isAnomaly = false,
            } = data[device]["summary"];
            const curStage = device2stage[device];

            if (!curStage) return;
            stageData[curStage].sumFLOPS += FLOPS;
            stageData[curStage].sumFLOPs += FLOPs;
            stageData[curStage].cnt++;
            stageData[curStage].isAnomaly =
              stageData[curStage].isAnomaly || isAnomaly;
            stageData[curStage]["abnormalContent"].push(...abnormalContent);

            maxFLOPS = Math.max(maxFLOPS, FLOPS);
            maxFLOPs = Math.max(maxFLOPs, FLOPs);

            flopsDataInfo.push({
              x: "FLOPS",
              y: device,
              value: FLOPS / maxFLOPS,
              initValue: FLOPs,
              isAnomaly,
              abnormalContent,
            });
            flopsDataInfo.push({
              x: "FLOPs",
              y: device,
              value: FLOPs / maxFLOPs,
              initValue: FLOPs,
              isAnomaly,
              abnormalContent,
            });

            // detail
            const curDeviceMFIPsData = [];
            const arr = data[device]["details"] || [];
            arr.forEach((opInfo) => {
              const opName = opInfo["op_full_name"].split("/").pop();
              const opData = maps[device][opName];
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
                curDeviceMFIPsData.push({ x, y, opName });
              }
            });
            if (curDeviceMFIPsData.length) {
              curDeviceMFIPsData.sort((objA, objB) => objA.x - objB.x);
              MFLOPsData.push({
                device,
                stage: device2stage[device],
                data: curDeviceMFIPsData,
              });
            }
          });

          // average stage data
          Object.keys(stageData).forEach((stage) => {
            const { sumFLOPS, sumFLOPs, cnt, isAnomaly, abnomalContent } =
              stageData[stage];
            flopsDataInfo.push({
              x: "FLOPS",
              y: stage,
              value: sumFLOPS / cnt / maxFLOPS,
              initValue: sumFLOPS / cnt,
              isAnomaly,
              abnomalContent,
            });
            flopsDataInfo.push({
              x: "FLOPs",
              y: stage,
              value: sumFLOPs / cnt / maxFLOPs,
              initValue: sumFLOPs / cnt,
              isAnomaly,
              abnomalContent,
            });
          });
          this.FLOPsData = MFLOPsData;
          this.flopsDataInfo = flopsDataInfo;
          this.mFLOPsMin = min;
          this.mFLOPsMax = max;
        })
        .catch(console.error);
    },
    getMemoryData(maps, device2stage, stages) {
      RequestService.getMemoryData(this.$route.query.path)
        .then(({ data }) => {
          const memoryDataInfo = [];
          const memoryData = [];
          let min = Infinity;
          let max = -Infinity;

          const stageData = stages.reduce(
            (acc, cur) => ({
              ...acc,
              [cur]: {
                sumPeakMem: 0,
                sumCapacity: 0,
                averageValue: 0,
                cnt: 0,
              },
            }),
            {}
          );

          Object.keys(data).forEach((device) => {
            const { capacity, peak_mem: peakMem } = data[device].summary || {};
            const stageOfDevice = device2stage[device];
            if (!stageOfDevice) {
              return;
            }
            // update data of stage
            const value = peakMem / capacity;
            stageData[stageOfDevice].averageValue += value;
            stageData[stageOfDevice].sumPeakMem += peakMem;
            stageData[stageOfDevice].sumCapacity += capacity;
            stageData[stageOfDevice].cnt++;

            // push device data
            memoryDataInfo.push({
              x: "PeakMem",
              y: device,
              peakMem,
              capacity,
              value,
            });

            const curDeviceMemoryData = [];
            const { lines, nodes = [] } =
              data[device]["details"]["0"] ||
              data[device]["details"]["1"] ||
              {};

            for (let i = 0; i < nodes.length; i++) {
              const opName = nodes[i].name;
              const opData = maps[device][opName];
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
                curDeviceMemoryData.push({ x, y, opName });
              }
            }
            if (curDeviceMemoryData.length) {
              curDeviceMemoryData.sort((objA, objB) => objA.x - objB.x);
              memoryData.push({
                stage: device2stage[device],
                device,
                data: curDeviceMemoryData,
              });
            }
          });

          Object.keys(stageData).forEach((stage) => {
            const { averageValue, cnt, sumPeakMem, sumCapacity } =
              stageData[stage];
            memoryDataInfo.push({
              x: "PeakMem",
              y: stage,
              peakMem: sumPeakMem / cnt,
              capacity: sumCapacity / cnt,
              value: averageValue / cnt,
            });
          });
          this.memoryData = memoryData;
          this.memoryDataInfo = memoryDataInfo;
          this.memoryMin = min;
          this.memoryMax = max;
        })
        .catch(console.error);
    },
    opNameProcessing(maps) {
      const opNameMap = {};
      Object.keys(maps).forEach((device) => {
        if (!opNameMap[device]) {
          opNameMap[device] = {};
        }
        Object.keys(maps[device]).forEach((opName) => {
          if (
            opName.startsWith("All") ||
            opName.startsWith("Send") ||
            opName.startsWith("Receive") ||
            opName.startsWith("ReduceScatter")
          ) {
            const opType = opName.split("-")[0];
            if (!opNameMap[device][opType]) {
              opNameMap[device][opType] = [];
            }
            opNameMap[device][opType].push(opName);
          }
        });
      });
      // all - send - receive - reduceScatter operator nodes of each device
      $store.commit("setOpNameMap", opNameMap);
    },
    processStageDeviceRelationship(stageData) {
      const stageDeviceRelationship = [];
      const isStageExpand = {};

      const stages = Object.keys(stageData).sort((a, b) => {
        const [num1] = a.match(/\d+/g);
        const [num2] = b.match(/\d+/g);

        return +num1 - +num2;
      });
      stages.forEach((stageName) => {
        const stage = stageData[stageName];
        const devices = stage.devices.sort((a, b) => {
          const [num1] = a.match(/\d+/g);
          const [num2] = b.match(/\d+/g);

          return +num1 - +num2;
        });

        stageDeviceRelationship.push({
          stage: stageName,
          devices,
        });
        isStageExpand[stageName] = true;
      });

      this.stageDeviceRelationship = stageDeviceRelationship;
      this.isStageExpand = isStageExpand;
    },
    getOffsetBetweenStageByDevice(preDeviceOps, curDeviceOps) {
      // prefix of nodes
      const SEND = "Send";
      const RECEIVE = "Receive";

      const preDeviceOpNames = Object.keys(preDeviceOps);
      const curDeviceOpNames = Object.keys(curDeviceOps);

      const sendOp = preDeviceOpNames.find((op) => op.startsWith(SEND));
      const receiveOp = curDeviceOpNames.find((op) => op.startsWith(RECEIVE));

      let startOffset = 0;
      let endOffset = 0;
      if (sendOp && receiveOp) {
        startOffset = Math.abs(
          preDeviceOps[sendOp].st - curDeviceOps[receiveOp].st
        );
        endOffset = Math.abs(
          preDeviceOps[sendOp].ed - curDeviceOps[receiveOp].ed
        );
      }

      return {
        startOffset,
        endOffset,
      };
    },
    processDeviceData(left = Number.MIN_VALUE, right = Number.MAX_VALUE) {
      const data = this.deviceDisplayedData;
      if (!data) return;
      const xScale = this.xScale;
      const threshold =
        right - left > 1000 ? this.threshold : xScale(0.01 * (right - left));

      const devicePolygonData = [];
      const deviceGapPolygonData = [];

      const devicePolygonCnt = {};

      Object.keys(data).forEach((stage) => {
        const stageData = data[stage];
        const filteredStageData = [];
        const curStageGapData = [];

        for (let i = 0; i < stageData.length; i++) {
          let preX1 = null;
          let preX2 = null;
          let preY = null;

          for (let j = 0; j < stageData[i].data.length; j++) {
            const { x1, x2, y } = stageData[i].data[j];
            if (x2 < left || x1 > right) {
              continue;
            }

            const type = this.getOperatorType(stageData[i].op);

            filteredStageData.push({
              op: stageData[i].op,
              x1: xScale(x1),
              x2: xScale(x2),
              y,
              type,
            });

            if (preX1 !== null) {
              // gap between device
              curStageGapData.push({
                op: stageData[i].op,
                y1: preY,
                x1: preX1,
                x2: preX2,
                y2: y,
                x3: xScale(x1),
                x4: xScale(x2),
                type,
              });
            }
            preX1 = xScale(x1);
            preX2 = xScale(x2);
            preY = y;
          }
        }

        if (filteredStageData.length > 0) {
          filteredStageData.sort((a, b) => {
            if (a.y !== b.y) {
              return a.y.localeCompare(b.y);
            } else if (a.x1 !== b.x1) {
              return a.x1 - b.x1;
            } else {
              return a.x2 - b.x2;
            }
          });

          const mergedData = mergeNearbyRects(filteredStageData, threshold);
          mergedData.forEach((block) => {
            const y = block.y;

            devicePolygonData.push(block);
            devicePolygonCnt[y] = (devicePolygonCnt[y] || 0) + 1;
          });
        }

        if (curStageGapData.length > 0) {
          curStageGapData.sort((a, b) => {
            if (a.y1 !== b.y1) {
              return a.y1.localeCompare(b.y1);
            } else if (a.x1 !== b.x1) {
              return a.x1 - b.x1;
            } else {
              return a.x2 - b.x2;
            }
          });
          const mergedData = mergeNearbyGap(curStageGapData, threshold);
          mergedData.forEach((block) => {
            deviceGapPolygonData.push(block);
          });
        }
      });

      this.devicePolygon = devicePolygonData;
      this.deviceGapPolygon = deviceGapPolygonData;

      const devices = Object.keys(devicePolygonCnt).sort((a, b) =>
        a.localeCompare(b)
      );
      const device2PolygonIndex = {};
      let index = 0;
      devices.forEach((device) => {
        device2PolygonIndex[device] = [
          index,
          index + devicePolygonCnt[device] - 1,
        ];
        index += devicePolygonCnt[device];
      });
      this.device2PolygonIndex = device2PolygonIndex;
    },
    processStageData(left = Number.MIN_VALUE, right = Number.MAX_VALUE) {
      const data = this.timeLineData;
      if (!data) {
        return;
      }
      const offset = 0; // brush

      const stagePolygonData = [];
      const xScale = this.xScale;

      for (let i = 0; i < data.length; i++) {
        const { op, x1, x2, y } = data[i];

        if (x1 < left - offset || x2 > right + offset) {
          continue;
        }

        stagePolygonData.push({
          stage: y,
          data: [xScale(x1), xScale(x2)],
          type: this.getOperatorType(op),
        });
      }

      const threshold =
        right - left > 1000 ? this.threshold : xScale(0.01 * (right - left));
      const mergedData = [stagePolygonData[0]];
      for (let i = 1; i < stagePolygonData.length; i++) {
        const pre = mergedData[mergedData.length - 1];
        const cur = stagePolygonData[i];
        // skip different type、stage
        if (
          pre.stage !== cur.stage ||
          Math.abs(cur.data[0] - pre.data[1]) > threshold ||
          Math.max(cur.data[0], pre.data[0]) <
            Math.min(cur.data[1], pre.data[1])
        ) {
          mergedData.push(cur);
        } else {
          pre.data[0] = Math.min(pre.data[0], cur.data[0]);
          pre.data[1] = Math.max(pre.data[1], cur.data[1]);
          mergedData[mergedData.length - 1] = pre;
        }
      }

      const stagePolygon = [];
      for (let i = 0; i < mergedData.length; ++i) {
        const d = mergedData[i];
        if (d) {
          stagePolygon.push({
            x1: d.data[0],
            x2: d.data[1],
            y: d.stage,
            type: d.type,
          });
        }
      }

      this.stagePolygon = stagePolygon;
    },

    render() {
      const yScale = this.yScale;
      const bannerHeight = this.bannerHeight * 2;
      const ctx = this.$refs.graph.getContext("2d");
      ctx.globalAlpha = 0.5;
      ctx.clearRect(0, 0, this.width, this.height);
      for (const data of this.stagePolygon) {
        ctx.fillStyle = "#789395";
        const { x1, x2, y } = data;
        ctx.beginPath();

        ctx.moveTo(x1, yScale(y));
        ctx.lineTo(x1, yScale(y) + bannerHeight);
        ctx.lineTo(x2, yScale(y) + bannerHeight);
        ctx.lineTo(x2, yScale(y));

        ctx.closePath();
        ctx.fill();
      }

      for (const data of this.devicePolygon) {
        ctx.fillStyle = this.operatorColor[data.type];
        const { x1, x2, y } = data;
        if (yScale(y) === undefined) {
          continue;
        }
        ctx.beginPath();

        ctx.moveTo(x1, yScale(y));
        ctx.lineTo(x1, yScale(y) + bannerHeight);
        ctx.lineTo(x2, yScale(y) + bannerHeight);
        ctx.lineTo(x2, yScale(y));

        ctx.closePath();
        ctx.fill();
      }

      for (const data of this.deviceGapPolygon) {
        ctx.fillStyle = this.operatorColor[data.type];
        const { x1, x2, y1, y2, x3, x4 } = data;
        if (yScale(y1) === undefined) {
          continue;
        }
        ctx.beginPath();
        ctx.moveTo(x3, yScale(y2));
        ctx.lineTo(x1, yScale(y1) + bannerHeight);
        ctx.lineTo(x2, yScale(y1) + bannerHeight);
        ctx.lineTo(x4, yScale(y2));

        ctx.closePath();
        ctx.fill();
      }
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
    handleDoubleClick() {
      if (!this.timeStack.length) {
        return;
      }

      const [minT, maxT] = this.timeStack.pop();
      this.reRenderChart(minT, maxT);
    },

    // show or hide device polygons when clicking stage menu
    clickStageMenu(stage) {
      this.isStageExpand[stage] = !this.isStageExpand[stage];
      this.render();
    },

    onMouseOverInfo(e, data, type) {
      const { offsetX, clientY } = e;
      const y = clientY - this.top + 15;
      switch (type) {
        case "memory":
          this.hoveredNodeInfo = {
            show: true,
            x: offsetX,
            y,
            title: data.y,
            content: {
              ratio: data.value,
              peakMem: data.peakMem,
              capacity: data.capacity,
            },
          };
          break;
        case "flops":
          this.hoveredNodeInfo = {
            show: true,
            x: offsetX,
            y,
            title: data.y,
            content: {
              ratio: data.value,
              [data.x]: data.initValue,
            },
          };
          break;
        case "chart":
          const bisect = d3.bisector((d) => d.x).left;
          const x = this.xScale.invert(
            offsetX - this.margin.left - this.margin.padding
          );
          const index = bisect(data, x);
          if (!data[index]) return;
          const { opName, x: xValue, y: yValue } = data[index];
          this.hoveredNodeInfo = {
            show: true,
            x: offsetX,
            y,
            title: opName,
            content: {
              xValue,
              yValue,
            },
          };
      }
    },
    onMouseOutInfo() {
      this.hoveredNodeInfo = {
        show: false,
      };
    },
    getOpNameByEvent(e, device) {
      const { offsetX } = e;
      const devicePolygon = this.devicePolygon;
      if (!this.device2PolygonIndex[device]) {
        return;
      }
      const [L, R] = this.device2PolygonIndex[device];

      let res = "";
      let left = L;
      let right = R;
      const x = offsetX - this.margin.left - this.margin.padding;
      while (left <= right) {
        const mid = Math.floor((right + left) / 2);
        const { x1, x2, op } = devicePolygon[mid];
        if (x1 <= x && x <= x2) {
          res = op;
          break;
        } else if (x1 > x) {
          right = mid - 1;
        } else {
          left = mid + 1;
        }
      }
      return res;
    },
    onMouseOverPolygon(e, device) {
      const res = this.getOpNameByEvent(e, device);
      const { offsetX, offsetY } = e;
      if (res !== "") {
        this.hoveredNodeInfo = {
          show: true,
          x: offsetX - 10,
          y: offsetY - 10,
          content: res.split("\n"),
        };
      } else {
        this.hoveredNodeInfo = {
          show: false,
        };
      }
    },

    handleSwitchChange(value) {
      if (value) {
        this.initBrush();
      } else {
        d3.select(this.$refs.g).selectAll("rect").remove();
      }
    },
  },
};
</script>

<style scoped>
#marey-view-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  position: relative;
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
.content {
  flex: 1;
  display: flex;
  overflow-y: auto;
  overflow-x: hidden;
}

.tooltip {
  position: absolute;
  padding: 10px;
  margin: 10px;
  opacity: 0.8;
  background-color: #edf0f5;
  border: 1px solid #edf0f5;
  pointer-events: none;
  border-radius: 4px;
  z-index: 2;
  font: 14px / 21px sans-serif;
  white-space: nowrap;
  transition: all 300ms ease-in-out;
}
.view {
  width: 100%;
  height: 100%;
  position: relative;
}

.graph {
  position: absolute;
  pointer-events: none;
}

.menu-header {
  display: flex;
}

.menu-header svg {
  width: 16px;
  height: 16px;
}
.stage-banner {
  stroke: #cecece;
  stroke-width: 1px;
  fill: #fff;
}

.brush {
  pointer-events: none;
}

.performance-cls-2,
.performance-cls-3 {
  fill: none;
  stroke-miterlimit: 10;
}
.performance-cls-2 {
  stroke: var(--performance-flops);
}
</style>

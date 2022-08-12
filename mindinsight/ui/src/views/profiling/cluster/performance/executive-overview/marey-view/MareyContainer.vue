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
  <div class="performance-view-container">
    <div class="legend">
      <LegendPerformance />
    </div>
    <div class="view">
      <div class="stage-tree">
        <StageTree
          :stageDeviceArr="stageDeviceArr"
          :stageDeviceRelationship="stageDeviceRelationship"
          :deviceToStage="deviceToStage"
          :FLOPsData="FLOPsData"
          :MemoryData="MemoryData"
          :closeCircleProps="closeCircleProps"
          @clickArrowIcon="handleClickArrowIcon"
        />
      </div>
      <div class="marey-graph">
        <MareyGraph
          :stepNumber="stepNumber"
          :stageDeviceArr="stageDeviceArr"
          :deviceToStage="deviceToStage"
          :timeLineData="timeLineData"
          :FLOPsData="FLOPsData"
          :MemoryDataProps="MemoryData"
        />
      </div>
    </div>
  </div>
</template>
<script>
import $store from "../store";
import RequestService from "@/services/request-service";
import MareyGraph from "./NewMareyGraph.vue";
import StageTree from "./StageTree.vue";
import LegendPerformance from "./LegendPerformance.vue";

export default {
  name: "MareyView",
  components: {
    MareyGraph,
    StageTree,
    LegendPerformance,
  },
  computed: {
    stepNumber() {
      return $store.state.stepNum;
    },
  },
  data() {
    return {
      overViewData: null,
      timeLineData: null,
      FLOPsData: null,
      MemoryData: null,
      stageDeviceArr: [],
      isStageExpand: new Map(),
      stageDeviceRelationship: null,
      deviceToStage: null,
      closeCircleProps: null,
    };
  },
  mounted() {
    this.getTimeLineData();
    this.getFLOPsData();
    this.getMemoryData();
  },
  methods: {
    getStepNumber(stepNumber) {
      $store.commit("setStepNum", stepNumber);
      this.getTimeLineData();
      this.getCloseCircleProps();
    },
    getTimeLineData() {
      RequestService.getTimeLineData(this.$route.query.path, this.stepNumber)
        .then(({ data }) => {
          const { stage_data, maps } = data || {};
          const stages = Object.keys(stage_data);
          stages.forEach((stageName) => {
            this.isStageExpand.set(stageName, false);
          });
          for (let i = 1; i < stages.length; i++) {
            const preDevice = stage_data[stages[i - 1]].devices[0];
            const curDevice = stage_data[stages[i]].devices[0];
            const preDeviceOpName = Object.keys(maps[preDevice]);
            const curDeviceOpName = Object.keys(maps[curDevice]);
            let sendOp;
            let receiveOp;
            for (let j = 0; j < preDeviceOpName.length; j++) {
              if (preDeviceOpName[j].startsWith("Send")) {
                sendOp = preDeviceOpName[j];
                break;
              }
            }
            for (let j = 0; j < curDeviceOpName.length; j++) {
              if (curDeviceOpName[j].startsWith("Receive")) {
                receiveOp = curDeviceOpName[j];
                break;
              }
            }
            const startOffset = Math.abs(
              maps[preDevice][sendOp].st - maps[curDevice][receiveOp].st
            );
            const endOffset = Math.abs(
              maps[preDevice][sendOp].ed - maps[curDevice][receiveOp].ed
            );
            stage_data[stages[i]].devices.forEach((device) => {
              Object.keys(maps[device]).forEach((op) => {
                const opInfo = maps[device][op];
                opInfo.st += startOffset;
                opInfo.ed += endOffset;
              });
            });
            Object.keys(stage_data[stages[i]].data).forEach((op) => {
              const opInfo = stage_data[stages[i]].data[op];
              opInfo.ed_avg += endOffset;
              opInfo.ed_max += endOffset;
              opInfo.ed_min += endOffset;
              opInfo.st_avg += startOffset;
              opInfo.st_max += startOffset;
              opInfo.st_min += startOffset;
            });
          }
          Object.keys(maps).forEach((device) => {
            Object.keys(maps[device]).forEach((op) => {
              const opInfo = maps[device][op];
              if (opInfo.dur <= 0.1) {
                opInfo.ed += 1;
              }
            });
          });

          this.timeLineData = data;
          this.opNameProcessing(maps);
          this.stageDeviceArrProcessing();
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
      console.log("opNameMap", opNameMap);
      // all - send - receive - reduceScatter operator nodes of each device
      $store.commit("setOpNameMap", opNameMap);
    },
    stageDeviceArrProcessing() {
      const stageDeviceArr = [];
      const stageDeviceRelationship = {};
      const deviceToStage = new Map();
      const { stage_data } = this.timeLineData || {};
      Object.keys(stage_data).forEach((stageName) => {
        stageDeviceArr.push(stageName);
        const curStageDevice = stage_data[stageName].devices;
        if (!stageDeviceRelationship[stageName]) {
          stageDeviceRelationship[stageName] = [];
        }
        curStageDevice.sort((a, b) => {
          const [num1] = a.match(/\d+/g);
          const [num2] = b.match(/\d+/g);
          return parseInt(num1, 10) - parseInt(num2, 10);
        });
        curStageDevice.forEach((device) => {
          deviceToStage.set(device, stageName);
          if (this.isStageExpand.get(stageName)) {
            stageDeviceArr.push(device);
            stageDeviceRelationship[stageName].push(device);
          }
        });
      });
      this.stageDeviceArr = stageDeviceArr;
      this.stageDeviceRelationship = stageDeviceRelationship;
      this.deviceToStage = deviceToStage;
    },
    getFLOPsData() {
      RequestService.getFLOPsData(this.$route.query.path)
        .then(({ data }) => {
          this.FLOPsData = data;
        })
        .catch(console.error);
    },
    getMemoryData() {
      RequestService.getMemoryData(this.$route.query.path)
        .then(({ data }) => {
          this.MemoryData = data;
        })
        .catch(console.error);
    },
    handleClickArrowIcon(stage) {
      this.isStageExpand.set(stage, !this.isStageExpand.get(stage));
      this.stageDeviceArrProcessing();
    },
  },
};
</script>
<style scoped>
.performance-view-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.performance-view-container .legend {
  width: 100%;
}
.performance-view-container .view {
  height: 80%;
  flex-grow: 1;
  display: flex;
  flex-direction: row;
  overflow-y: scroll;
}
.performance-view-container .view::-webkit-scrollbar {
  width: 8px;
}
.performance-view-container .view::-webkit-scrollbar-track {
  background: rgb(239, 239, 239);
  border-radius: 2px;
}
.performance-view-container .view::-webkit-scrollbar-thumb {
  background: #bfbfbf;
  border-radius: 10px;
}
.performance-view-container .view::-webkit-scrollbar-thumb:hover {
  background: #333;
}
.performance-view-container .view::-webkit-scrollbar-corner {
  background: #179a16;
}
.performance-view-container .view .stage-tree {
  min-height: 101%;
  width: 260px;
  flex-basis: 260px;
}
.performance-view-container .view .marey-graph {
  min-height: 101%;
  flex: 1;
}
.title {
  font-size: 18px;
  font-weight: 600;
  margin-left: 16px;
}
</style>

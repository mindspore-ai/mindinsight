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
    <LineChart @getStepNumber="getStepNumber" />
  </div>
</template>
<script>
import RequestService from "@/services/request-service";
import LineChart from "./LineChart.vue";
import $store from "../store";

export default {
  name: "TimelineView",
  components: {
    LineChart,
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
      deviceToStage: null, //device - stage的映射
      closeCircleProps: null,
      communicateNodes: null,
    };
  },
  mounted() {
    this.getOverviewTimeData();
    this.getCommunicateNodes();
  },
  methods: {
    getOverviewTimeData() {
      RequestService.getOverviewTime(this.$route.query.path)
        .then(({ data }) => {
          // this.overViewData = data;
          $store.commit("setOverviewData", data);
        })
        .catch((err) => {
          console.error(err);
        });
    },
    getStepNumber(stepNumber) {
      $store.commit("setStepNum", stepNumber);
    },
    getCommunicateNodes() {
      RequestService.getCommunicationGraph(this.$route.query.path).then(
        ({ data }) => {
          var res = {};
          for (var device in data) {
            for (var i in data[device]) {
              var step_info = data[device][i];
              var new_node = {
                name: null,
                communication_cost: null,
                wait_cost: null,
                opNodes: null,
              };
              new_node.name = device;
              new_node.communication_cost = step_info["communication_cost"];
              new_node.wait_cost = step_info["wait_cost"];
              new_node.opNodes = step_info["communication_operator_cost"];
              if (!res.hasOwnProperty(step_info["step_num"])) {
                res[step_info["step_num"]] = [];
              }
              res[step_info["step_num"]].push(new_node);
            }
          }
          this.communicateNodes = res;
          $store.commit("setCommunicateNodes", res);
        }
      );
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
  border-top: 2px solid #ccc;
}
</style>
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
    <empty
      v-if="isLoading.comm && isLoading.overview"
      class="strategy-loading"
      :state="loadingState"
      style="position: absolute; z-index: 999"
    ></empty>
    <LineChart @getStepNumber="getStepNumber" />
  </div>
</template>
<script>
import RequestService from "@/services/request-service";
import LineChart from "./LineChart.vue";
import $store from "../store";
import empty, { LOADING_DATA } from "@/components/empty.vue";

export default {
  name: "TimelineView",
  components: {
    LineChart,
    empty,
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
      isLoading: { overview: true, comm: true },
      loadingState: LOADING_DATA,
    };
  },
  mounted() {
    this.isLoading = { overview: true, comm: true };
    this.loadingState = LOADING_DATA;
    this.getOverviewTimeData();
    this.getCommunicateNodes();
  },
  methods: {
    getOverviewTimeData() {
      RequestService.getOverviewTime(this.$route.query.path)
        .then(({ data }) => {
          $store.commit("setOverviewData", data);
          this.isLoading.overview = false;
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
              if (step_info["step_num"] == "-") {
                continue;
              }
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
          this.isLoading.comm = false;
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
}
</style>

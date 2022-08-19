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
  <div class="communication-container">
    <div class="communication-sub-title">
      <svg class="subtitle-svg" width="90%" height="100%">
        <defs>
          <linearGradient
            id="myLinearGradient1"
            x1="0%"
            y1="0%"
            x2="100%"
            y2="0%"
            spreadMethod="pad"
          >
            <stop offset="0%" stop-color="#fbe7d5" stop-opacity="1" />
            <stop offset="100%" stop-color="#e6882e" stop-opacity="1" />
          </linearGradient>
        </defs>
        <g class="subtitle-container">
          <g id="subtitle-line1">
            <text x="0" y="15">{{ $t("profilingCluster.nodelinkGraph") }}</text>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="-2.75 0 48 13">
              <g transform="scale(0.25)">
                <circle class="cls-1" cx="3.5" cy="6.5" r="3" />
                <circle class="cls-1" cx="21.5" cy="6.5" r="6" />
                <line class="cls-2" x1="3.5" y1="3.5" x2="21.5" y2="0.5" />
                <line class="cls-2" x1="3.5" y1="9.5" x2="21.5" y2="12.5" />
              </g>
            </svg>
            <text x="155" y="15">{{ $t("profilingCluster.totalcomm") }}</text>
          </g>
          <g id="subtitle-line2">
            <text x="0" y="40">0</text>
            <rect
              x="15"
              y="30"
              width="65"
              height="10"
              fill="url(#myLinearGradient1)"
            ></rect>
            <text x="85" y="40">1</text>
            <text x="100" y="40">
              {{ $t("profilingCluster.commProportion") }}
            </text>
          </g>
          <g id="subtitle-line3">
            <text x="0" y="65">
              {{ $t("profilingCluster.matrixDescription") }}
            </text>
            <rect x="50" y="55" width="10" height="10" fill="#f6b59a"></rect>
            <text x="63" y="65">{{ $t("profilingCluster.commTime") }}</text>
            <rect x="200" y="55" width="10" height="10" fill="#a8d2e5"></rect>
            <text x="213" y="65">{{ $t("profilingCluster.traffic") }}</text>
            <rect x="260" y="55" width="10" height="10" fill="#378dc0"></rect>
            <text x="273" y="65">{{ $t("profilingCluster.bandwidth") }}</text>
          </g>
        </g>
      </svg>
    </div>
    <div class="communication-graph-box">
      <div id="networkPlot"></div>
    </div>
  </div>
</template>

<style>
.communication-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.communication-sub-title {
  width: 100%;
  height: 75px;
  padding-top: 5px;
  margin-left: 16px;
}
.communication-view {
  height: 100%;
}

#networkPlot {
  position: relative;
  width: 100%;
  height: 100%;
}
.communication-graph-box {
  /* position: relative; */
  height: 100%;
  width: 100%;
  /* flex-grow: 1; */
}
.el-icon-magic-stick {
  position: absolute;
  top: 0;
  right: 5%;
  z-index: 999;
}

.lasso path {
  stroke: rgb(80, 80, 80);
  stroke-width: 2px;
}

.lasso .drawn {
  fill-opacity: 0.05;
}

.lasso .loop_close {
  fill: none;
  stroke-dasharray: 4, 4;
}

.lasso .origin {
  fill: #3399ff;
  fill-opacity: 0.5;
}
.cls-1,
.cls-2 {
  fill: none;
  stroke: #cbcbcb;
  stroke-miterlimit: 10;
}
.cls-2 {
  stroke-dasharray: 2;
}
</style>
<script>
import {
  device_node,
  communicate_link,
} from "@/js/communicate-view/build-graph.js";
import RequestService from "@/services/request-service";
import * as d3 from "d3";
import { Graph } from "@/js/communicate-view/graph.js";
export default {
  props: {
    stepNumber: String,
  },
  data() {
    return {
      stepNum: 1,
      communicateNodes: {},
      communicateEdges: {},
      communicateOps: {},
      communicateGraphData: {},
      linecharOption: null,
      linechart: null,
      opNameMap: null,
    };
  },
  mounted() {
    this.initGraph();
  },
  watch: {
    stepNumber: function (val) {
      this.stepNum = val;
      this.renderNetwork();
    }
  },

  methods: {
    async initGraph() {
      await this.fetchData();
      this.renderNetwork();
    },
    async fetchData() {
      const res = (
        await RequestService.getCommunicationGraph(this.$route.query.path)
      ).data;
      this.communicateGraphData = res;
      for (var device in this.communicateGraphData) {
        for (var i in this.communicateGraphData[device]) {
          var step_info = this.communicateGraphData[device][i];
          if (step_info["step_num"] == '-') {
            continue;
          }
          var new_node = Object.create(device_node);
          new_node.name = device;
          new_node.communication_cost = step_info["communication_cost"];
          new_node.wait_cost = step_info["wait_cost"];
          new_node.opNodes = step_info["communication_operator_cost"];
          if (!this.communicateNodes.hasOwnProperty(step_info["step_num"])) {
            this.communicateNodes[step_info["step_num"]] = [];
          }
          this.communicateNodes[step_info["step_num"]].push(new_node);
          var link_info = step_info["link_info"];
          if (!this.communicateEdges.hasOwnProperty(step_info["step_num"])) {
            this.communicateEdges[step_info["step_num"]] = [];
          }
          if (!this.communicateOps.hasOwnProperty(step_info["step_num"])) {
            this.communicateOps[step_info["step_num"]] = {};
          }

          for (var link in link_info) {
            for (var type in link_info[link]) {
              var new_link = Object.create(communicate_link);
              var node_pair = link.split("-");
              new_link.source = node_pair[0];
              new_link.target = node_pair[1];

              if (
                !this.communicateGraphData.hasOwnProperty(
                  "device" + new_link.source
                ) ||
                !this.communicateGraphData.hasOwnProperty(
                  "device" + new_link.target
                )
              ) {
                continue;
              }
              new_link.type = type;
              new_link.value = link_info[link][type][0];
              new_link.communication_duration = link_info[link][type][0];
              new_link.traffic = link_info[link][type][1];
              new_link.bandWidth = link_info[link][type][2];
              this.communicateEdges[step_info["step_num"]].push(new_link);
            }
          }

          var op_info = step_info["communication_operator_cost"];

          var step = step_info["step_num"];
          for (var op_name in op_info) {
            for (var link in op_info[op_name][3]) {
              if (!this.communicateOps[step].hasOwnProperty(link)) {
                this.communicateOps[step][link] = [];
              }
              for (var link_type in op_info[op_name][3][link]) {
                var duration = op_info[op_name][3][link][link_type][0];
                var traffic = op_info[op_name][3][link][link_type][1];
                var bandWidth = op_info[op_name][3][link][link_type][2];

                this.communicateOps[step][link].push({
                  device: device,
                  op_name: op_name,
                  duration: duration,
                  traffic: traffic,
                  bandWidth: bandWidth,
                });
              }
            }
          }
        }
      }
    },
    renderNetwork() {
      // network data
      if (!this.communicateNodes[this.stepNum]) return;
      var dataLink = [];
      var dataNode = [];

      this.communicateNodes[this.stepNum].forEach(function (d) {
        dataNode.push({
          id: d.name,
          label: d.name.replace("device", ""),
          c_cost: d.communication_cost,
          w_cost: d.wait_cost,
        });
      });

      this.communicateEdges[this.stepNum].forEach((d) => {
        var op_duration = [],
          op_traffic = [],
          op_bandWidth = [];
        var link_str = d.source + "-" + d.target;
        var op_info = this.communicateOps[this.stepNum][link_str];
        op_info.forEach((i) => {
          op_duration.push({
            name: i["op_name"],
            value: i["duration"],
            device: i["device"],
          });
          op_traffic.push({
            name: i["op_name"],
            value: i["traffic"],
            device: i["device"],
          });
          op_bandWidth.push({
            name: i["op_name"],
            value: i["bandWidth"],
            device: i["device"],
          });
        });
        dataLink.push({
          source: "device" + d.source,
          target: "device" + d.target,
          weight: d.value,
          link_type: d.type,
          communication_duration: d.communication_duration,
          traffic: d.traffic,
          bandWidth: d.bandWidth,
          op_duration: op_duration.sort((a, b) => a.value - b.value),
          op_traffic: op_traffic.sort((a, b) => a.value - b.value),
          op_bandWidth: op_bandWidth.sort((a, b) => a.value - b.value),
        });
      });

      var width = document.getElementById("networkPlot").clientWidth;
      var height = document.getElementById("networkPlot").clientHeight;

      d3.selectAll("#networkPlot>*").remove();
      var svg = d3
        .select("#networkPlot")
        .append("svg")
        .attr("id", "mainsvg")
        .attr("width", width)
        .attr("height", height);

      d3.selectAll("#matrix > *").remove();
      d3.selectAll("#force > *").remove();
      d3.selectAll("#path > *").remove();

      svg.append("g").attr("id", "matrix");
      svg.append("g").attr("id", "force");
      svg.append("g").attr("id", "path");
      window.communicategraph = new Graph(width, height, this);
      window.communicategraph.init(dataLink, dataNode);
    }
  },
};
</script>

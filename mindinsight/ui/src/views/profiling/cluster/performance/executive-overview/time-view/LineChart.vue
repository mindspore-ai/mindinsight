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
  <div class="line-chart-container">
    <svg style="position: absolute; top: 4%" width="100%" height="15px">
      <rect
        x="10%"
        y="1"
        width="25px"
        height="14px"
        fill-opacity="0.5"
        style="rx: 4px; fill: #a1a1a1"
      ></rect>
      <text x="14%" y="13" style="font-size: 13px; opacity: 0.7">
        {{ $t("profilingCluster.totalTrainingTime") }}
      </text>
      <rect
        x="33%"
        y="1"
        width="25px"
        height="14px"
        style="rx: 4px; fill: #c69b7b"
      ></rect>
      <text x="37%" y="13" style="font-size: 13px; opacity: 0.7">
        {{ $t("profilingCluster.averageCommTime") }}
      </text>
      <rect
        x="63%"
        y="1"
        width="25px"
        height="14px"
        style="rx: 4px; fill: #826f66"
      ></rect>
      <text x="67%" y="13" style="font-size: 13px; opacity: 0.7">
        {{ $t("profilingCluster.averageWaitingTime") }}
      </text>
    </svg>
    <div id="line-chart"></div>
  </div>
</template>

<script>
import * as echarts from "echarts/core";
import * as _ from "lodash";
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
} from "echarts/components";
import { LineChart } from "echarts/charts";
import { UniversalTransition } from "echarts/features";
import { CanvasRenderer } from "echarts/renderers";
import { DataZoomComponent } from "echarts/components";
import $store from "../store";

echarts.use([
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  LineChart,
  CanvasRenderer,
  UniversalTransition,
  DataZoomComponent,
]);

export default {
  name: "LineChart",
  components: {},
  data() {
    return {
      data: [],
      overViewData: Object,
      communicateNodes: Object,
      lineChart: null,
      option: null,
    };
  },
  watch: {
    storeOverviewData: function (val) {
      this.overViewData = val;
      this.overViewDataProcessing();
      this.renderUpdate();
    },
    storeCommunicateNodes: function (val) {
      this.communicateNodes = val;
      this.communicateNodesProcessing();
      this.renderUpdate();
    },
  },
  mounted() {
    this.renderInit();
  },
  beforeDestroy() {
    this.lineChart.clear();
  },
  computed: {
    storeOverviewData() {
      return $store.state.overviewData;
    },
    storeCommunicateNodes() {
      return $store.state.communicateNodes;
    },
  },
  methods: {
    renderInit() {
      const chartDom = document.getElementById("line-chart");
      const myChart = echarts.init(chartDom);
      this.lineChart = myChart;
      const option = {
        tooltip: {
          trigger: "axis",
        },
        grid: {
          top: "20%",
          left: "5%",
          right: "10%",
          bottom: "20%",
          containLabel: true,
        },
        xAxis: {
          name: "Step",
          type: "category",
          boundaryGap: true,
          nameLocation: "middle",
          axisTick: {
            show: true,
            alignWithLabel: true,
          },
          nameGap: 18,
          nameTextStyle: {
            fontStyle: "normal",
            fontWeight: "normal",
            fontSize: 12,
            align: "center",
          },
          data: [],
        },
        yAxis: [
          {
            type: "value",
            name: "Total training time(ms)",
            min: function (value) {
              return value.min - 20;
            },
            axisLine: {
              symbol: ["none", "triangle"],
              show: true,
              symbolSize: 10,
              symbolOffset: 5,
            },
            axisLabel: {
              show: true,
              // showMaxLabel: true,
              showMinLabel: true,
              formatter: function (value) {
                return value.toExponential(2);
              },
            },
            splitLine: {
              show: false,
            },
            nameLocation: "middle",
            nameGap: 65,
            nameTextStyle: {
              fontStyle: "normal",
              fontWeight: "bold",
              fontSize: 12,
            },
          },
          {
            type: "value",
            name: "Communication cost(ms)",
            // minInterval: 1000,
            nameLocation: "middle",
            nameGap: 60,
            nameTextStyle: {
              fontStyle: "normal",
              fontWeight: "bold",
              fontSize: 12,
              align: "center",
              verticalAlign: "bottom",
            },
            axisLine: {
              symbol: ["none", "triangle"],
              show: true,
              symbolSize: 10,
              symbolOffset: 5,
            },
            splitLine: {
              show: false,
            },
            axisLabel: {
              show: true,
            },
          },
        ],
        dataZoom: [
          {
            type: "inside",
            start: 0,
            end: 100,
          },
          {
            type: "slider",
            start: 0,
            end: 100,
            height: 20,
            moveHandleSize: 1,
            top: "86%",
          },
        ],
        series: [],
      };
      this.option = option;
    },
    renderUpdate() {
      this.lineChart.setOption(this.option);
      const handleClickFn = (params) => {
        this.$emit("getStepNumber", parseInt(params.name, 10));
      };
      this.lineChart.on("click", _.debounce(handleClickFn, 150));
    },
    communicateNodesProcessing() {
      this.option.xAxis.data = Object.keys(this.communicateNodes);
      const communicationList = [];
      const waitingList = [];

      for (let i in this.communicateNodes) {
        let totCommunication = 0;
        let totWaiting = 0;
        for (let j in this.communicateNodes[i]) {
          totCommunication += this.communicateNodes[i][j].communication_cost;
          totWaiting += this.communicateNodes[i][j].wait_cost;
        }
        communicationList.push(
          totCommunication / this.communicateNodes[i].length
        );
        waitingList.push(totWaiting / this.communicateNodes[i].length);
      }
      const series = [
        {
          name: "Average communication time of devices",
          yAxisIndex: 1,
          type: "line",
          stack: "Total",
          color: "#C69B7B",
          lineStyle: {
            width: 1.5,
          },
          showSymbol: false,
          data: communicationList,
        },
        {
          name: "Average waiting time of devices",
          yAxisIndex: 1,
          type: "line",
          stack: "Total",
          color: "#826F66",
          lineStyle: {
            width: 1.5,
          },
          showSymbol: false,
          data: waitingList,
        },
      ];
      this.option.series.push(...series);
    },
    overViewDataProcessing() {
      const series = [];
      Object.keys(this.overViewData).forEach((device) => {
        const obj = {
          name: device,
          yAxisIndex: 0,
          type: "line",
          stack: "Total",
          color: "#a1a1a1",
          lineStyle: {
            width: 1.5,
          },
          showSymbol: false,
          data: this.overViewData[device].map((o) => {
            return o.total;
          }),
        };
        series.push(obj);
      });

      this.option.series.push(...series);
    },
  },
};
</script>

<style scoped>
.line-chart-container {
  position: relative;
  width: 100%;
  height: 100%;
}
#line-chart {
  height: 100%;
  width: 100%;
}
</style>

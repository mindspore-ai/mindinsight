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
    <div id="line-chart" ref="chart"></div>
  </div>
</template>

<script>
import * as _ from "lodash";
import echarts, { echartsThemeName } from "@/js/echarts";
import $store from "../store";

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
      chart: {
        dom: null,
        instance: null,
        seriesData: { overviewData: null, commData: null, waitingData: null },
        xAxisData: null,
        legend: ["communication cost", "waiting cost", "overview"],
        grid: {
          top: "20%",
          left: "10%",
          right: "10%",
          bottom: "15%",
        },
      },
      state: false,
    };
  },
  watch: {
    storeOverviewData: function (val) {
      this.overViewData = val;
      this.overViewDataProcessing();
      this.initChart();
    },
    storeCommunicateNodes: function (val) {
      this.communicateNodes = val;
      this.communicateNodesProcessing();
      this.initChart();
    },
  },
  mounted() {
    this.state = false;
    this.chart.dom = this.$refs.chart ? this.$refs.chart : null;
  },
  beforeDestroy() {},
  computed: {
    storeOverviewData() {
      return $store.state.overviewData;
    },
    storeCommunicateNodes() {
      return $store.state.communicateNodes;
    },
  },
  methods: {
    initChart() {
      if (!this.chart.dom) return;
      if (this.state) return;
      if (!this.chart.instance) {
        this.chart.instance = echarts.init(this.chart.dom, echartsThemeName);
      }
      if (
        this.chart.seriesData.overviewData &&
        this.chart.seriesData.commData &&
        this.chart.seriesData.waitingData
      ) {
        this.setChartOption();
        this.setChartAction();
        this.state = true;
      }
    },
    setMarkArea(index) {
      let options = this.chart.instance.getOption();
      options.series[0].markArea.data = this.getMarkArea(index);
      this.chart.instance.setOption(options);
    },
    getMarkArea(index) {
      const areaWidth = 0.2;
      let left = parseFloat(this.chart.grid.left);
      let right = 100 - parseFloat(this.chart.grid.right);
      let axisLength = this.chart.xAxisData.length;
      let onePixel = (right - left) / axisLength;
      let x = left + (index + 0.5) * onePixel;
      return [
        [
          { x: String(x - areaWidth * onePixel) + "%" },
          { x: String(x + areaWidth * onePixel) + "%" },
        ],
      ];
    },
    setChartAction() {
      this.chart.instance.getZr().on("click", (params) => {
        let pointInPixel = [params.offsetX, params.offsetY];
        if (this.chart.instance.containPixel("grid", pointInPixel)) {
          let pointInGrid = this.chart.instance.convertFromPixel(
            {
              seriesIndex: 0,
            },
            pointInPixel
          );
          let handleIndex = Number(pointInGrid[0]);
          var op = this.chart.instance.getOption();
          var clickStep = op.xAxis[0].data[handleIndex];
          this.$emit("getStepNumber", parseInt(clickStep, 10));
          this.setMarkArea(handleIndex);
        }
      });
    },
    setChartOption() {
      var series = [];
      var commSeries = {
        name: this.chart.legend[0],
        type: "line",
        yAxisIndex: 0,
        color: "#C69B7B",
        data: this.chart.seriesData.commData.map((v) => {
          return { value: v, name: this.chart.legend[0] };
        }),
        markArea: {
          itemStyle: {
            color: "rgba(255, 173, 177, 0.4)",
          },
          data: this.getMarkArea(0),
        },
      };
      var waitSeries = {
        name: this.chart.legend[1],
        type: "line",
        yAxisIndex: 0,
        color: "#826F66",
        data: this.chart.seriesData.waitingData.map((v) => {
          return { value: v, name: this.chart.legend[1] };
        }),
      };
      series.push(commSeries);
      series.push(waitSeries);
      var overviewSeires = this.chart.seriesData.overviewData.map((d) => {
        return {
          name: this.chart.legend[2],
          type: "line",
          yAxisIndex: 1,
          color: "#a1a1a1",
          data: d.data.map((v) => {
            return { value: v, name: d.name };
          }),
        };
      });
      series.push(...overviewSeires);
      this.chart.instance.setOption({
        tooltip: {
          trigger: "axis",
          axisPointer: {
            type: "shadow",
          },
          formatter: (params) => {
            var str = "";
            params.forEach((item) => {
              str +=
                item.marker + " " + item.data.name + ":" + item.value + "</br>";
            });
            return str;
          },
        },
        legend: {
          center: true,
          data: this.chart.legend,
          textStyle: {
            fontSize: 14,
          },
        },
        grid: this.chart.grid,
        xAxis: {
          name: "step",
          type: "category",
          boundaryGap: true,
          nameLocation: "middle",
          nameTextStyle: {
            align: "left",
            padding: [0, 5],
          },
          axisTick: {
            show: true,
            alignWithLabel: true,
          },
          axisLine: {
            lineStyle: {
              width: 2,
            },
          },
          nameGap: 18,
          nameTextStyle: {
            fontStyle: "normal",
            fontWeight: "normal",
            fontSize: 12,
            align: "center",
          },
          data: this.chart.xAxisData,
        },
        yAxis: [
          {
            type: "value",
            name: "Communication cost(ms)",
            splitLine: {
              show: false,
            },
            nameLocation: "middle",
            nameGap: 70,
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
            name: "Total training time(ms)",
            splitLine: {
              show: false,
            },
            nameLocation: "middle",
            nameGap: 50,
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
        ],
        series: series,
      });
    },
    communicateNodesProcessing() {
      this.chart.xAxisData = Object.keys(this.communicateNodes);
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
      this.chart.seriesData.commData = communicationList;
      this.chart.seriesData.waitingData = waitingList;
    },
    overViewDataProcessing() {
      var overviewList = [];
      Object.keys(this.overViewData).forEach((device) => {
        let overview = this.overViewData[device].map((o) => {
          if (o.step_num != "-") return o.total;
        });
        overview = overview.filter((o) => o != undefined);
        overviewList.push({ name: device, data: overview });
      });
      this.chart.seriesData.overviewData = overviewList;
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

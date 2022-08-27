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
  <div
    class="legend-container"
    :style="{
      width: `${width}%`,
    }"
  >
    <div class="one-legend">
      <svg width="105px" height="100%" fill="var(--font-color)">
        <defs>
          <linearGradient id="gradient">
            <stop
              v-for="data in colorStop"
              :key="data.offset"
              :offset="data.offset"
              :stop-color="data.color"
            ></stop>
          </linearGradient>
        </defs>
        <text x="5" y="17.5" font-size="14" alignment-baseline="middle">0</text>
        <rect
          x="22"
          y="12"
          height="9"
          width="60"
          style="fill: url(#gradient)"
        ></rect>
        <text x="92" y="17.5" font-size="14" alignment-baseline="middle">
          1
        </text>
      </svg>
      <div>{{ $t("profilingCluster.ratio") }}</div>
    </div>
    <div class="vertical-dashed-line operator-legend"></div>
    <div class="one-legend">
      <div>{{ $t("profilingCluster." + performance_legend[0]["name"]) }}</div>
      <svg width="70px" height="100%">
        <g transform="translate(10,10)">
          <rect class="cls-1" x="6.62" y="0.5" width="37.06" height="15.28" />
          <polyline
            class="cls-2"
            points="12.06 6.97 21.2 6.97 25.78 4.52 30.68 6.97 39.9 6.97"
          />
          <polyline
            class="cls-3"
            points="12.06 9.97 19.01 9.97 23.65 9.97 29.98 11.97 33.97 10.97 39.19 9.97"
          />
          <line class="cls-1" x1="0.01" y1="7.14" x2="10.64" y2="6.97" />
          <line class="cls-1" x1="40.72" y1="9.97" x2="51.03" y2="9.97" />
        </g>
      </svg>
      <div>{{ $t("profilingCluster." + performance_legend[1]["name"]) }}</div>
    </div>
    <div class="vertical-dashed-line operator-legend"></div>
    <div class="one-legend">
      <svg width="20px" height="100%" fill="var(--font-color)">
        <g>
          <polygon
            transform="translate(5,10)"
            :fill="performance_legend[2]['color']"
            opacity="0.5"
            points="0 0 0 8.55 3.23 15.77 11 15.77 9.16 7.91 11.61 0 0 0"
          />
        </g>
      </svg>
      <div>{{ $t("profilingCluster." + performance_legend[2]["name"]) }}</div>
    </div>
    <div class="one-legend">
      <svg width="20px" height="100%" fill="var(--font-color)">
        <g>
          <polygon
            transform="translate(5,10)"
            :fill="performance_legend[3]['color']"
            opacity="0.5"
            points="0 0 0 8.55 3.23 15.77 11 15.77 9.16 7.91 11.61 0 0 0"
          />
        </g>
      </svg>
      <div>{{ $t("profilingCluster." + performance_legend[3]["name"]) }}</div>
    </div>
    <div class="vertical-dashed-line operator-legend"></div>

    <div>{{ $t("profilingCluster.p2pcomm") }}</div>
    <div class="one-legend">
      <svg width="30px" height="100%" fill="var(--font-color)">
        <g>
          <polygon
            transform="translate(10,10)"
            :fill="performance_legend[4]['color']"
            opacity="0.5"
            points="0 0 0 8.55 3.23 15.77 11 15.77 9.16 7.91 11.61 0 0 0"
          />
        </g>
      </svg>
      <div>{{ $t("profilingCluster." + performance_legend[4]["name"]) }}</div>
    </div>
    <div class="one-legend">
      <svg width="20px" height="100%" fill="var(--font-color)">
        <g>
          <polygon
            transform="translate(5,10)"
            :fill="performance_legend[5]['color']"
            opacity="0.5"
            points="0 0 0 8.55 3.23 15.77 11 15.77 9.16 7.91 11.61 0 0 0"
          />
        </g>
      </svg>
      <div>{{ $t("profilingCluster." + performance_legend[5]["name"]) }}</div>
    </div>
    <div class="vertical-dashed-line operator-legend"></div>
    <div class="one-legend">
      <svg width="20px" height="100%" fill="var(--font-color)">
        <g>
          <polygon
            transform="translate(5,10)"
            fill="#789395"
            opacity="0.8"
            points="0 0 0 8.55 3.23 15.77 11 15.77 9.16 7.91 11.61 0 0 0"
          />
        </g>
      </svg>
      <div>{{ $t("profilingCluster.averageCondition") }}</div>
    </div>
  </div>
</template>

<style>
.legend-container {
  position: relative;
  display: flex;
  flex-direction: row;
  margin-right: 10px;
  height: 35px;
  line-height: 35px;
  /* width: 100%; */
  justify-content: space-around;
}
.one-legend {
  display: flex;
  flex-direction: row;
  height: 35px;
  line-height: 35px;
  width: fit-content;
}
.legend-container div {
  white-space: nowrap;
}
.legend-linear-gradient {
  width: 140px;
  height: 100%;
}
.legend-linechart {
  width: 185px;
  height: 100%;
}
.legend-operators {
  height: 100%;
  width: 465px;
}
.legend-communication {
  height: 100%;
  width: 475px;
}
.operator-legend {
  position: relative;
  float: left;
}
.vertical-dashed-line {
  height: 60%;
  width: 1px;
  top: 20%;
  border-right: 1px dashed #aaaaaa;
  margin-left: 8px;
  margin-right: 8px;
}
.stage-legend {
  height: 100%;
  width: 180px;
  flex-grow: 1;
}
.performance-cls-1,
.performance-cls-2,
.performance-cls-3 {
  fill: none;
  stroke-miterlimit: 10;
}
.performance-cls-1 {
  stroke: #aaa;
}
.performance-cls-2 {
  stroke: var(--performance-flops);
}
.performance-cls-3 {
  stroke: var(--performance-memory);
}
.cls-1,
.cls-2,
.cls-3 {
  fill: none;
  stroke-miterlimit: 10;
}
.cls-1 {
  stroke: #aaa;
}
.cls-2 {
  stroke: #585393;
}
.cls-3 {
  stroke: #7e93bf;
}
</style>

<script>
import * as d3 from "d3";

export default {
  data() {
    return {
      performance_legend: [
        {
          name: "FLOPs",
          color: "var(--performance-flops)",
        },
        {
          name: "memory",
          color: "var(--performance-memory)",
        },
        {
          name: "fpbpTitle",
          color: "var(--performance-fb)",
        },
        {
          name: "collectiveCommunication",
          color: "var(--performance-collective)",
        },
        {
          name: "sendOperator",
          color: "var(--performance-send)",
        },
        {
          name: "receiveOperator",
          color: "var(--performance-receive)",
        },
      ],
      colorStop: null,
      width: 100,
    };
  },
  mounted() {
    this.colorStop = d3.range(0.2, 1.01, 0.1).map((d) => {
      return { offset: d, color: this.colorScale(d), value: d };
    });
    this.width = this.$store.state.language === "en-us" ? 80 : 70;
  },
  computed: {
    colorScale() {
      return d3
        .scaleSequential()
        .domain([0, 1])
        .interpolator(d3.interpolateGreys);
    },
  },
};
</script>

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
    class="parallel-legend"
    :style="{
      paddingRight: `${padding}px`,
    }"
  >
    <div class="one-legend">
      <svg width="24px" height="100%">
        <g fill="var(--font-color)">
          <circle
            cx="12"
            cy="17.5"
            r="6"
            :fill="normal_strategy_legend[0]['color']"
            stroke="white"
            stroke-width="1px"
          ></circle>
        </g>
      </svg>
      <div>
        {{ $t("profilingCluster." + normal_strategy_legend[0]["name"]) }}
      </div>
    </div>
    <div class="one-legend">
      <svg width="12px" height="100%">
        <g fill="var(--font-color)">
          <circle
            cx="6"
            cy="17.5"
            r="3"
            :fill="normal_strategy_legend[1]['color']"
            stroke="white"
            stroke-width="1px"
          ></circle>
        </g>
      </svg>
      <div>
        {{ $t("profilingCluster." + normal_strategy_legend[1]["name"]) }}
      </div>
    </div>
    <div class="vertical-dashed-line operator-legend"></div>
    <div>{{ $t("profilingCluster.specialTypeOperator") }}</div>
    <div class="one-legend">
      <svg width="24px" height="100%">
        <g fill="var(--font-color)">
          <circle
            r="6"
            cy="17.5"
            cx="12"
            :fill="special_strategy_legend[0]['color']"
            stroke="white"
            stroke-width="1px"
          ></circle>
        </g>
      </svg>
      <div>
        {{ $t("profilingCluster." + special_strategy_legend[0]["name"]) }}
      </div>
    </div>
    <div class="one-legend">
      <svg width="24px" height="100%">
        <g fill="var(--font-color)">
          <circle
            r="6"
            cy="17.5"
            cx="12"
            :fill="special_strategy_legend[1]['color']"
            stroke="white"
            stroke-width="1px"
          ></circle>
        </g>
      </svg>
      <div>
        {{ $t("profilingCluster." + special_strategy_legend[1]["name"]) }}
      </div>
    </div>
    <div class="one-legend">
      <svg width="24px" height="100%">
        <g fill="var(--font-color)">
          <circle
            r="6"
            cy="17.5"
            cx="12"
            :fill="special_strategy_legend[2]['color']"
            stroke="white"
            stroke-width="1px"
          ></circle>
        </g>
      </svg>
      <div>
        {{ $t("profilingCluster." + special_strategy_legend[2]["name"]) }}
      </div>
    </div>
    <div class="one-legend">
      <svg width="24px" height="100%">
        <g fill="var(--font-color)">
          <circle
            r="6"
            cy="17.5"
            cx="12"
            :fill="special_strategy_legend[3]['color']"
            stroke="white"
            stroke-width="1px"
          ></circle>
        </g>
      </svg>
      <div>
        {{ $t("profilingCluster." + special_strategy_legend[3]["name"]) }}
      </div>
    </div>
    <div class="one-legend">
      <svg width="24px" height="100%">
        <g fill="var(--font-color)">
          <circle
            r="6"
            cy="17.5"
            cx="12"
            :fill="special_strategy_legend[4]['color']"
            stroke="white"
            stroke-width="1px"
          ></circle>
        </g>
      </svg>
      <div>
        {{ $t("profilingCluster." + special_strategy_legend[4]["name"]) }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.parallel-legend {
  float: right;
  height: 35px;
  display: flex;
  flex-direction: row;
  width: 1350px;
  flex-direction: row;
  line-height: 35px;
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
.normal-operator {
  width: 200px;
  height: 100%;
  float: left;
}
.special-operator {
  height: 100%;
  width: 1000px;
  float: left;
}
.vertical-dashed-line {
  height: 60%;
  width: 1px;
  top: 20%;
  border-right: 1px dashed #aaaaaa;
  float: left;
}

.text {
  font-size: 14px;
}
</style>

<script>
export default {
  data() {
    return {
      padding: 200,
      normal_strategy_legend: [
        {
          name: "operator",
          color: "var(--normal-operator-color)",
        },
        {
          name: "parameter",
          color: "var(--parameter-operator-color)",
        },
      ],
      special_strategy_legend: [
        {
          name: "sendOperator",
          color: "var(--send-operator-color)",
        },
        {
          name: "receiveOperator",
          color: "var(--receive-operator-color)",
        },
        {
          name: "parallelShardOperator",
          color: "var(--slice-operator-color)",
        },
        {
          name: "redistributionOperator",
          color: "var(--redistribution-operator-color)",
        },
        {
          name: "gradientAggOperator",
          color: "var(--allreduce-operator-color)",
        },
      ],
    };
  },
  mounted() {
    this.padding = this.$store.state.language === "en-us" ? 265 : 250;
  },
};
</script>

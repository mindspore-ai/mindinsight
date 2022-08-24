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
  <div class="parallel-legend">
    <div class="normal-operator operator-legend">
      <svg width="100%" height="100%">
        <g>
          <circle
            cx="18"
            cy="17.5"
            r="6"
            :fill="normal_strategy_legend[0]['color']"
            stroke="white"
            stroke-width="1px"
          ></circle>
          <text x="32" y="17.5" class="text" alignment-baseline="middle">
            {{ $t("profilingCluster." + normal_strategy_legend[0]['name']) }}
          </text>
          <circle
            cx="112"
            cy="17.5"
            r="3"
            :fill="normal_strategy_legend[1]['color']"
            stroke="white"
            stroke-width="1px"
          ></circle>
          <text x="122" y="17.5" class="text" alignment-baseline="middle">
            {{ $t("profilingCluster." + normal_strategy_legend[1]['name']) }}
          </text>
        </g>
      </svg>
    </div>
    <div class="vertical-dashed-line operator-legend"></div>
    <div class="special-operator operator-legend">
      <svg width="100%" height="100%">
        <g>
          <text x="15" y="17.5" class="text" alignment-baseline="middle">
            {{ $t("profilingCluster.specialTypeOperator") }}
          </text>
          <circle
            r="6"
            cy="17.5"
            cx="170"
            :fill="special_strategy_legend[0]['color']"
            stroke="white"
            stroke-width="1px"
          ></circle>
          <text x="182" y="17.5" class="text" alignment-baseline="middle">
            {{ $t("profilingCluster." + special_strategy_legend[0]['name']) }}
          </text>
          <circle
            r="6"
            cy="17.5"
            cx="290"
            :fill="special_strategy_legend[1]['color']"
            stroke="white"
            stroke-width="1px"
          ></circle>
          <text x="302" y="17.5" class="text" alignment-baseline="middle">
            {{ $t("profilingCluster." + special_strategy_legend[1]['name']) }}
          </text>
          <circle
            r="6"
            cy="17.5"
            cx="425"
            :fill="special_strategy_legend[2]['color']"
            stroke="white"
            stroke-width="1px"
          ></circle>
          <text x="437" y="17.5" class="text" alignment-baseline="middle">
            {{ $t("profilingCluster." + special_strategy_legend[2]['name']) }}
          </text>

          <circle
            r="6"
            cy="17.5"
            cx="600"
            :fill="special_strategy_legend[3]['color']"
            stroke="white"
            stroke-width="1px"
          ></circle>
          <text x="612" y="17.5" class="text" alignment-baseline="middle">
            {{ $t("profilingCluster." + special_strategy_legend[3]['name']) }}
          </text>

          <circle
            r="6"
            cy="17.5"
            cx="780"
            :fill="special_strategy_legend[4]['color']"
            stroke="white"
            stroke-width="1px"
          ></circle>
          <text x="792" y="17.5" class="text" alignment-baseline="middle">
            {{ $t("profilingCluster." + special_strategy_legend[4]['name']) }}
          </text>
        </g>
      </svg>
    </div>
  </div>
</template>

<style scoped>
.parallel-legend {
  float: right;
  height: 35px;
  display: flex;
  width: 1250px;
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
      normal_strategy_legend: [
        {
          name: 'operator',
          color: 'var(--normal-operator-color)',
        },
        {
          name: 'parameter',
          color: 'var(--parameter-operator-color)',
        },
      ],
      special_strategy_legend: [
        {
          name: 'sendOperator',
          color: 'var(--send-operator-color)',
        },
        {
          name: 'receiveOperator',
          color: 'var(--receive-operator-color)',
        },
        {
          name: 'parallelShardOperator',
          color: 'var(--slice-operator-color)',
        },
        {
          name: 'redistributionOperator',
          color: 'var(--redistribution-operator-color)',
        },
        {
          name: 'gradientAggOperator',
          color: 'var(--allreduce-operator-color)',
        },
      ],
    };
  },
};
</script>

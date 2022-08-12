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
  <div class="legend-container">
    <div class="normal-operator operator-legend">
      <svg width="100%" height="100%">
        <g>
          <svg>
            <defs>
              <linearGradient id="myLinearGradient1"
                              x1="0%" y1="0%"
                              x2="100%" y2="0%"
                              spreadMethod="pad">
                <stop offset="0%"   stop-color="#fae7d7" stop-opacity="1"/>
                <stop offset="100%" stop-color="#E6882E" stop-opacity="1"/>
              </linearGradient>
            </defs>
          
            <rect x="10" y="10" width="40" height="15"
              style="fill:url(#myLinearGradient1); stroke: #005000; stroke-width: 1;" />
          </svg>
        </g>
      </svg>
    </div>
    <div class="vertical-dashed-line operator-legend"></div>
    <div class="special-operator operator-legend">
      <svg width="100%" height="100%">
        <g>
          
        </g>
      </svg>
    </div>
  </div>
</template>

<style>
.legend-container {
  position: relative;
  float: left;
  margin-right: 10px;
  height: 35px;
  width: 100%;
}
.normal-operator {
  width: 50%;
  height: 100%;
  
}
.special-operator {
  height: 100%;
  width: 50%;
}
.vertical-dashed-line {
  height: 60%;
  width: 1px;
  top: 20%;
  border-right: 1px dashed #aaaaaa;
}

.operator-legend {
  position: relative;
  float: left;
}
</style>

<script>
export default {
  data() {
    return {
      communication_matrix_legend : [
        {
          "name": "time",
          "color": COMMINICATION_MATRIX_TIME,
        },
        {
          "name": "traffic",
          "color": COMMINICATION_MATRIX_TRAFFIC,
        },
        {
          "name": "bandwidth",
          "color": COMMINICATION_MATRIX_BANDWIDTH,
        },
      ],
    };
  },
}
</script>
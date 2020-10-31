<!--
Copyright 2020 Huawei Technologies Co., Ltd.All Rights Reserved.

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
  <div class="scatter"
       ref="scatter">
  </div>
</template>
<script>
import echarts from 'echarts';

export default {
  props: {
    data: Array,
    tooltipsData: Array,
    yTitle: String,
    xTitle: String,
    showTooltip: Boolean,
  },
  watch: {
    data: {
      handler(newValue, oldValue) {
        this.chartOption = this.formateCharOption();
        this.createChart();
      },
    },
  },
  data() {
    return {
      chartObj: null,
      chartOption: {},
      charResizeTimer: null,
    };
  },
  destroyed() {
    // remove the size of a window and change the listener
    window.removeEventListener('resize', this.resizeCallback);
    // Remove Chart Calculation Delay
    if (this.charResizeTimer) {
      clearTimeout(this.charResizeTimer);
      this.charResizeTimer = null;
    }
  },

  mounted() {
    window.addEventListener('resize', this.resizeCallback, false);
  },
  methods: {
    /**
     * formate Chart option
     */

    formateCharOption() {
      const tempOption = {
        // Set the top, bottom, left, and right blanks of the echart diagram
        grid: {
          left: 20,
          right: 20,
          x2: 20,
          y2: 20,
          containLabel: true,
        },
        tooltip: {
          trigger: 'item',
          show: this.showTooltip,
          axisPointer: {
            type: 'cross',
          },
          confine: true,
          formatter: (params) => {
            const dataIndex = params.dataIndex;
            const item = this.tooltipsData[dataIndex];
            let res = '';
            const obj = Object.keys(item);
            for (let i = 0; i < obj.length; i++) {
              if (obj[i] && item[obj[i]] !== null) {
                if (typeof item[obj[i]] === 'number') {
                  if (item[obj[i]] < 0.0001 && item[obj[i]] > 0) {
                    item[obj[i]] = item[obj[i]].toExponential(4);
                  } else {
                    item[obj[i]] =
                      Math.round(item[obj[i]] * Math.pow(10, 4)) /
                      Math.pow(10, 4);
                  }
                }
                res += `<p>${obj[i]}:&nbsp;&nbsp;${item[obj[i]]}</p>`;
              }
            }
            return `<div class="tooltip-msg">${res}</div>`;
          },
        },
        xAxis: {
          name: this.xTitle,
          nameLocation: 'end',
          nameTextStyle: {
            align: 'right',
            padding: [60, 0, 0, 0],
          },
          axisLine: {
            show: true,
          },
          axisTick: {
            show: false,
          },
          axisLabel: {},
        },
        yAxis: {
          name: this.yTitle,
          nameGap: 20,
          nameTextStyle: {
            align: 'middle',
          },
          axisLine: {
            show: true,
          },
          axisTick: {
            show: false,
          },
          axisLabel: {
            formatter: (value) => {
              const symbol = Math.abs(value);
              if (symbol.toString().length > 6) {
                return value.toExponential(4);
              } else if (value >= 1000 || value <= -1000) {
                return parseFloat((value / 1000).toFixed(2)) + 'k';
              } else if (value > 0) {
                return value;
              } else {
                return parseFloat(value.toFixed(3));
              }
            },
          },
          splitLine: {
            lineStyle: {
              color: '#E6EBF5',
              width: 1,
            },
          },
        },
        series: [
          {
            symbol: 'circle',
            data: this.data,
            name: this.yTitle,
            type: 'scatter',
            // Set scatter color
            color: '#cc5b58',
          },
        ],
      };
      return tempOption;
    },

    /**
     * formate Chart option
     */

    createChart() {
      if (!this.data.length) {
        this.clearScatter();
        return;
      }
      if (!this.chartObj) {
        this.chartObj = echarts.init(this.$refs.scatter);
        this.chartObj.setOption(this.chartOption, true);
      } else {
        this.chartObj.setOption(this.chartOption, false);
      }
    },
    /**
     *Clear chart
     */
    clearScatter() {
      if (this.chartObj) {
        this.chartObj.clear();
      }
    },
    /**
     *window resize
     */
    resizeCallback() {
      this.charResizeTimer = setTimeout(() => {
        if (this.chartObj) {
          this.chartObj.resize();
        }
      }, 500);
    },
  },
  components: {},
};
</script>
<style lang="scss">
.scatter {
  height: 100%;
}
.tooltip-msg {
  white-space: normal;
  word-break: break-all;
  max-width: 250px;
}
</style>

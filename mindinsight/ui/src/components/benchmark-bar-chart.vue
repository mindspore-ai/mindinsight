<!--
Copyright 2020-2021 Huawei Technologies Co., Ltd.All Rights Reserved.

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
  <div ref="evaluationtDom"
       class="cl-bar-chart"></div>
</template>

<script type="text/javascript">
import echarts, {echartsThemeName} from '../js/echarts';
import CommonProperty from '../common/common-property';

export default {
  name: 'BenchmarkBarChart',
  props: ['barData', 'theme', 'resizeFlag'],
  data: function() {
    return {
      option: {}, // Chart data
      echartInstance: null, // Chart instantiation object
      barStart: 0, // Zoom start value
      barEnd: 100, // Zoom end value
      firstInit: true, // Identification of the first load data
      limitCount: 20, // Limit number of bars
      legendLimit: 16, // Limit number of characters in legend
      themeIndex: this.$store.state.themeIndex, // Index of theme color
    };
  },

  mounted: function() {
    this.initEcharts();
  },

  watch: {
    barData: {
      handler() {
        this.setSeries();
      },
      deep: true,
    },
    resizeFlag: {
      handler() {
        if (this.echartInstance) {
          this.echartInstance.resize();
        }
      },
    },
  },

  methods: {
    /**
     * Refresh the chart based on the latest data
     */
    setSeries() {
      const self = this;
      self.option.series = [];
      let totalCount = 0;
      const highligntDic = {};

      for (let i = 0; i < self.barData.series.length; i++) {
        const tempValues = self.barData.series[i].values;
        for (let j = 0; j < tempValues.length; j++) {
          if (isNaN(tempValues[j])) {
            highligntDic[j] = true;
          }
        }
        self.option.series.push({
          name: self.barData.series[i].name,
          type: 'bar',
          data: self.barData.series[i].values,
        });
        totalCount += self.barData.series[i].values.length;
      }
      if (self.firstInit && totalCount) {
        self.firstInit = false;
        if (totalCount > self.limitCount) {
          const base = (self.limitCount / totalCount) * 100;
          self.barEnd = base;
          self.option.dataZoom.forEach((zoommData) => {
            zoommData.end = self.barEnd;
          });
        }
      } else if (self.echartInstance) {
        const optionData = self.echartInstance.getOption();
        if (optionData && optionData.dataZoom) {
          self.option.dataZoom = optionData.dataZoom;
        }
      }

      self.option.legend.data = self.barData.legend;
      const tempYaxisData = self.barData.yAxis.concat([]);
      const highligntArr = Object.keys(highligntDic);
      highligntArr.forEach((index) => {
        if (tempYaxisData[index]) {
          tempYaxisData[index] = {
            value: tempYaxisData[index],
            textStyle: {
              color: '#f00',
            },
          };
        }
      });
      self.option.yAxis.data = tempYaxisData;

      // Charting
      if (self.echartInstance) {
        self.echartInstance.setOption(self.option, true);
        self.echartInstance.resize();
      }
    },

    /**
     * Instantiate the chart object and set the basic parameters
     */
    initEcharts() {
      const self = this;
      const dom = this.$refs.evaluationtDom;

      if (dom) {
        self.echartInstance = echarts.init(dom, echartsThemeName);
      }
      self.option = {
        color: CommonProperty.XAIColorArr[this.themeIndex],
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow',
          },
          formatter(params) {
            const colon = self.$t('symbols.colon');
            let tipStr = '';
            if (params.length) {
              tipStr += `<div>${params[0].name}</div>`;
              params.forEach((param) => {
                tipStr +=
                  `<div><span style="border-radius:50%;width:10px;height:10px;vertical-align:middle;` +
                  `margin-right:5px;background-color:${param.color};display:inline-block;">` +
                  `</span>${param.seriesName}${colon}<span>` +
                  `</span>${param.value}<span></span></div>`;
              });
            }
            return tipStr;
          },
        },
        legend: {
          textStyle: {
            color: CommonProperty.echartsTextStyle[this.themeIndex],
          },
          orient: 'vertical',
          data: [],
          right: 10,
          formatter: (param) => {
            let str = '';
            if (param.length > self.legendLimit) {
              const splitCount = Math.ceil(param.length / self.legendLimit);
              const strArr = [];
              for (let i = 0; i < splitCount; i++) {
                const start = i * self.legendLimit;
                const end = start + self.legendLimit;
                strArr.push(param.slice(start, end));
              }
              str = strArr.join('\n');
            } else {
              str = param;
            }
            return str;
          },
          tooltip: {
            show: true,
            formatter: (param) => {
              const tip = param.name;
              return tip;
            },
          },
        },
        grid: {
          left: '10%',
          right: 280,
          bottom: '3%',
          top: 30,
        },
        xAxis: {
          type: 'value',
          position: 'top',
          boundaryGap: [0, 0.01],
          name: this.$t('metric.evaluationScore'),
        },
        yAxis: {
          type: 'category',
          data: [],
          inverse: true,
        },
        dataZoom: [
          {
            type: 'inside',
            filterMode: 'empty',
            orient: 'vertical',
            yAxisIndex: 0,
            start: this.barStart,
            end: this.barEnd,
          },
          {
            type: 'slider',
            filterMode: 'empty',
            orient: 'vertical',
            yAxisIndex: 0,
            start: this.barStart,
            end: this.barEnd,
            right: 200,
            top: 50,
            bottom: 30,
          },
        ],
        barGap: '20%',
        series: [],
      };
    },
  },
};
</script>

<style>
.cl-bar-chart {
  width: 100%;
  height: 100%;
}
</style>

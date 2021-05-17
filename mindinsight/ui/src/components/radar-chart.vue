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
  <div class="radar"
       ref="radar"
       :style="{
         'min-height': minHeight + 'px',
       }">
  </div>
</template>
<script>
import echarts from '../js/echarts';
import common from '../common/common-property';

export default {
  name: 'RadarChart',
  data() {
    return {
      option: {}, // The chart option
      instance: null, // The chart instance created by echarts init
      indicators: [], // The list of indicator in string
      defaultRadius: '73%', // The default radius of radar
      defaultEWidth: 5, // The default width of emphasis width
      defaultLegendSetting: {
        padding: [0, 16],
        itemWidth: 25,
        itemHeight: 4,
        textStyle: {
          padding: [0, 0, 0, 4],
        },
      }, // The default setting of legend
      minHeight: 500, // The default min-height
      titleHeight: 50, // The default height of title
      legendHeight: 20, // The default height of every legend line
      resizeDelay: 100, // The delay of resize's event
    };
  },
  props: [
    'data', // The processed radar data
    'nowHoverName', // The hover item name
    'radius', // The radius of radar
    'eWidth', // The width of emphasis width
    'legendSetting', // The setting of legend
    'ifTwo', // If show two legend item per line, default is 'true'
    'ifResetTooltip', // If fix the tooltip in the upper left and right corner, default is 'true'
  ],
  mounted() {
    this.initRadarChart(this.data);
    window.addEventListener('resize', this.resizeRadarChart);
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.resizeRadarChart);
  },
  watch: {
    /**
     * The logic executed when hover item changed
     */
    nowHoverName() {
      this.emphasisRadarChart(this.nowHoverName);
    },
  },
  methods: {
    /**
     * The logic of resize radar chart
     */
    resizeRadarChart() {
      clearTimeout(this.timer);
      this.timer = setTimeout(() => {
        if (this.instance) {
          this.instance.resize();
        }
        this.timer = null;
      }, this.resizeDelay);
    },
    /**
     * The logic of cal min-height of radar chart
     * @param {Number} length the number of legends
     */
    calMinHeight(length) {
      // Show two legends per line
      const count = Math.ceil(length / 2);
      if (this.$refs.radar) {
        const width = parseFloat(
            getComputedStyle(this.$refs.radar)['width'].replace('px', ''),
        );
        const minHeight = width + count * this.legendHeight + this.titleHeight;
        this.minHeight = minHeight;
      }
    },
    /**
     * The logic of cal center of radar chart
     * @param {Number} length the number of legends
     * @return {Array}
     */
    calCenter(length) {
      const count = Math.ceil(length / 2);
      const pos = '50%';
      if (this.$refs.radar) {
        const height = parseFloat(
            getComputedStyle(this.$refs.radar)['height'].replace('px', ''),
        );
        // 100 : transform to percentage
        const headerPer = (count * this.legendHeight + this.titleHeight) / height * 100;
        const yPos = (100 - headerPer) / 2 + headerPer + '%';
        return [pos, yPos];
      }
      return [pos, pos];
    },
    /**
     * The logic of init radar chart with default setting
     * @param {Object} data Original data
     */
    initRadarChart(data) {
      for (let i = 0; i < data.indicator.length; i++) {
        this.indicators.push(data.indicator[i].name);
      }
      const dom = this.$refs.radar;
      if (dom) {
        this.calMinHeight(data.legend.length);
        this.instance = echarts.init(dom);
      } else {
        return;
      }
      this.instance.setOption({
        tooltip: {
          formatter: (params) => {
            let temp = `${params.data.name}<br>`;
            for (let i = 0; i < this.indicators.length; i++) {
              temp += `${this.indicators[i]}: ${params.data.value[i]}<br>`;
            }
            return temp;
          },
          backgroundColor: 'rgba(50, 50, 50, 0.7)',
          borderWidth: 0,
          textStyle: {
            color: '#fff',
          },
        },
        title: {
          text: data.title ? data.title : '',
          textStyle: {
            lineHeight: '20',
            fontSize: '14',
            fontWeight: '600',
          },
          padding: [15, 16],
        },
        color: common.radarColorArr,
        radar: {
          shape: 'circle',
          name: {
            textStyle: {
              color: '#909399',
            },
            formatter: (text) => {
              return this.formatIndicator(
                  text,
                  this.indicators,
              );
            },
          },
          center: this.calCenter(data.legend.length),
          radius: this.radius ? this.radius : this.defaultRadius,
        },
        series: [
          {
            type: 'radar',
            emphasis: {
              lineStyle: {
                width: this.eWidth ? this.eWidth : this.defaultEWidth,
              },
            },
            data: [],
          },
        ],
      });
      this.updateRadarChart(data);
    },
    /**
     * The logic of update radar chart with new data
     * The new data should be like that
     * {legend: Array<string>, indicator: [{name: string,max: number}], series: [{value: [], name: string}]}
     * @param {Object} data Original data
     */
    updateRadarChart(data) {
      this.instance.setOption({
        legend: data.legend
          ? this.formatLegend(
              data.legend,
              this.legendSetting
                ? this.legendSetting
                : this.defaultLegendSetting,
              this.ifTwo ? this.ifTwo : true,
          )
          : [],
        radar: {
          indicator: data.indicator ? data.indicator : [],
        },
        series: [
          {
            data: data.series ? data.series : [],
          },
        ],
      });
      this.$nextTick(() => {
        this.instance.resize();
      });
    },
    /**
     * The logic of update radar chart with new data
     * The new data should be like that
     * {legend: Array<string>, indicator: [{name: string,max: number}], series: [{value: [], name: string}]}
     * @param {Object} seriesName The name of series item which need to be emphasised
     */
    emphasisRadarChart(seriesName) {
      const option = this.instance.getOption();
      const series = Array.from(option.series[0].data);
      for (let i = 0; i < series.length; i++) {
        if (series[i].name === seriesName) {
          series[i].lineStyle = {
            width: this.eWidth ? this.eWidth : this.defaultEWidth,
          };
        } else {
          // Line style rollback
          Reflect.deleteProperty(series[i], 'lineStyle');
        }
      }
      this.instance.setOption({
        series: [
          {
            data: series,
          },
        ],
      });
    },
    /**
     * The logic of init the legend style
     * @param {Array<string>} legend Original data
     * @param {Object} setting
     * @param {boolean} two If make the legend layout with two item per line
     * @return {Array<Object>}
     */
    formatLegend(legend, setting, two) {
      const newLegend = [];
      let count = 0;
      // The height of title and legend line
      const titleHeigth = 50;
      const legendHeight = 20;
      for (let i = 0; i < legend.length; i++) {
        if (two) {
          let left = '';
          let top = '';
          if (i % 2 === 0) {
            left = '0%';
            top = `${count * legendHeight + titleHeigth}px`;
          } else {
            left = '50%';
            top = `${count * legendHeight + titleHeigth}px`;
            count++;
          }
          newLegend.push(
              Object.assign(
                  {
                    data: [legend[i]],
                    top: top,
                    left: left,
                  },
                  setting,
              ),
          );
        } else {
          return Object.assign(
              {
                data: legend,
                top: '50px',
              },
              setting,
          );
        }
      }
      return newLegend;
    },
    /**
     * The logic of resolve the problem that the indicator cant show complete
     * @param {String} indicator
     * @param {Array<string>} indicators
     * @return {String}
     */
    formatIndicator(indicator, indicators) {
      if (!Array.isArray(indicators)) {
        return indicator;
      }
      const index = indicators.indexOf(indicator);
      if (index < 0) {
        return indicator;
      }
      // 360 : Degree of circle
      const degree = (360 / indicators.length) * index;
      const radiusString = this.radius ? this.radius : this.defaultRadius;
      // 100 : The parameter to convert percentage to decimal
      const radiusNumber = radiusString.replace('%', '') / 100;
      const dom = this.$refs.radar;
      const indicatorSpace = this.getSpace(
          degree,
          radiusNumber,
          dom.offsetWidth,
      );
      // 10 : The maximum PX of a single English letter in the current font size
      const split = Math.ceil(indicatorSpace / 10);
      const chars = indicator.split('');
      for (let i = 0; i < chars.length; i++) {
        if ((i + 1) % split === 0 && i !== chars.length - 1) {
          chars[i] += '-\n';
        }
      }
      return chars.join('');
    },
    /**
     * The logic of cal the space of indicator
     * @param {Number} degree
     * @param {Number} radius
     * @param {Number} width
     * @return {Number}
     */
    getSpace(degree, radius, width) {
      const uprightDegree = 90; // Angle of quarter circle
      if (degree === 0 || degree === uprightDegree * 2) {
        return width;
      }
      if (degree === uprightDegree || degree === uprightDegree * 3) {
        return (width - width * radius) / 2;
      }
      const x = Math.PI / (uprightDegree * 2);
      const half = (width * radius) / 2;
      let calDegree;
      if (degree < uprightDegree) {
        calDegree = degree;
      } else if (uprightDegree < degree && degree < uprightDegree * 2) {
        calDegree = uprightDegree - (degree % uprightDegree);
      } else if (uprightDegree * 2 < degree && degree < uprightDegree * 3) {
        calDegree = degree % uprightDegree;
      } else {
        calDegree = uprightDegree - (degree % uprightDegree);
      }
      const length = half * Math.sin(calDegree * x);
      return width / 2 - length;
    },
  },
};
</script>
<style>
.radar {
  width: 100%;
  height: 100%;
}
</style>

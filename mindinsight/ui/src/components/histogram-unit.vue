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
  <div class="cl-histogram-container">
    <div class="data-show-container">
      <div v-show="requestError"
           class="error-msg-container">
        {{errorMsg}}
      </div>
      <div :id="itemId"
           v-show="!!fullData.length && !requestError"
           class="data-item"></div>
    </div>
  </div>
</template>

<script>
import echarts from 'echarts';
import CommonProperty from '../common/common-property';
import {format, precisionRound} from 'd3';
const d3 = {format, precisionRound};
export default {
  props: {
    // Histogram data
    fullData: {
      type: Array,
      default() {
        return [];
      },
    },
    // View name
    viewName: {
      type: Number,
      default: 1,
    },
    // Axis name
    axisName: {
      type: Number,
      default: 0,
    },
    // Display full screen
    fullScreen: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      itemId: '', // Dom id
      oriData: {}, // Original data
      charOption: {}, // Chart configuration
      charObj: null, // Chart Object
      updated: false, // Updated
      zrDrawElement: {hoverDots: []},
      zr: null,
      chartTipFlag: false, // Wheather to display tips of the histogram
      requestError: false, // Exceeded the specification
      errorMsg: '', // Error message
      viewResizeFlag: false, // Size reset flag
    };
  },
  computed: {},
  watch: {},
  mounted() {
    this.init();
  },
  methods: {
    /**
     * Initialize
     */
    init() {
      this.itemId =
        `${new Date().getTime()}` + `${this.$store.state.componentsCount}`;
      this.$store.commit('componentsNum');
    },
    /**
     * Update the view Size
     */
    resizeView() {
      if (this.charObj) {
        if (this.requestError) {
          this.viewResizeFlag = true;
        } else {
          this.charObj.resize();
        }
      }
    },
    /**
     * Convert to chart data
     */
    formatDataToChar() {
      const chartData = this.fullData;
      const seriesData = [];
      let maxX = -Infinity;
      let minX = Infinity;
      let maxZ = -Infinity;
      let minZ = Infinity;
      const gridData = [];
      if (chartData && chartData.length) {
        chartData.forEach((histogram) => {
          const seriesItem = [];
          gridData.push(histogram.step);
          histogram.items.forEach((bucket) => {
            if (this.viewName === 0) {
              seriesItem.push([bucket[2], bucket[3]]);
            } else if (this.viewName === 1) {
              seriesItem.push(bucket[2], histogram.step, bucket[3]);
            }
            maxX = Math.max(maxX, bucket[2]);
            minX = Math.min(minX, bucket[2]);
            minZ = Math.min(minZ, bucket[3]);
            maxZ = Math.max(maxZ, bucket[3]);
          });
          seriesData.push(seriesItem);
        });
      }
      this.oriData = {
        seriesData,
        maxX,
        minX,
        maxZ,
        minZ,
        gridData,
      };
    },
    /**
     * Update sample data
     */
    updateSampleData() {
      this.charOption = this.formatCharOption();
      if (!this.charObj) {
        const chartItem = document.getElementById(this.itemId);
        if (!chartItem) {
          return;
        }
        this.charObj = echarts.init(chartItem, null);
      }
      this.removeTooltip();
      this.charObj.setOption(this.charOption, true);
      if (this.viewResizeFlag) {
        this.charObj.resize();
        this.viewResizeFlag = false;
      }
    },
    /**
     * Binding interaction event
     */
    sampleEventBind() {
      if (!this.zr) {
        this.zr = this.charObj.getZr();
        this.zr.off('mouseout', 'mousemove');
        this.zr.on('mouseout', (e) => {
          this.removeTooltip();
          this.chartTipFlag = false;
          this.$emit('chartTipFlagChange', this.chartTipFlag);
        });
        this.zr.on('mousemove', (e) => {
          this.removeTooltip();
          this.mousemoveEvent(e);
        });
      }
    },
    /**
     * Formate chart option
     * @return {Object} chatr option
     */
    formatCharOption() {
      const colorMin = '#346E69';
      const colorMax = '#EBFFFD';
      const oriData = this.oriData;
      const colorArr = this.getGrientColor(
          colorMin,
          colorMax,
          oriData.seriesData.length,
      );
      const fullScreenFun = this.toggleFullScreen;
      const axisName = this.axisName;
      const that = this;
      const option = {
        grid: {
          left: 40,
          top: 60,
          right: 80,
          bottom: 60,
        },
        xAxis: {
          max: oriData.maxX,
          min: oriData.minX,
          axisLine: {onZero: false},
          axisLabel: {
            fontSize: '11',
            formatter: function(value) {
              return that.formateNUmber(value);
            },
          },
          splitLine: {show: false},
        },
        yAxis: {
          position: 'right',
          axisLine: {onZero: false, show: false},
          splitLine: {show: true},
          axisTick: {show: false},
          boundaryGap: false,
          axisLabel: {
            fontSize: '11',
            formatter: function(value) {
              return that.formateNUmber(value);
            },
          },
        },
        toolbox: {
          top: 20,
          right: 20,
          emphasis: {
            iconStyle: {
              textPosition: 'top',
              borderColor: '#00A5A7',
            },
          },
          // toolbox
          feature: {
            // fullScreen
            myToolFullScreen: {
              show: true,
              title: this.$t('histogram.fullScreen'),
              iconStyle: {
                borderColor: this.fullScreen ? '#00A5A7' : '#6D7278',
              },
              icon: CommonProperty.fullScreenIcon,
              onclick() {
                fullScreenFun();
              },
            },
          },
        },
      };
      if (this.viewName === 1) {
        const seriesData = [];
        oriData.seriesData.forEach((item, dataIndex) => {
          const dataItem = {
            name: item[1],
            value: item,
            itemStyle: {
              color: colorArr[dataIndex],
            },
          };
          seriesData.push(dataItem);
        });
        option.series = [
          {
            type: 'custom',
            dimensions: ['x', 'y'],
            renderItem: (params, api) => {
              const points = this.makePolyPoints(
                  params.dataIndex,
                  api.coord,
                  params.coordSys.y - 10,
              );

              return {
                type: 'polyline',
                z2: params.dataIndex,
                silent: true,
                shape: {
                  points,
                },
                style: api.style({
                  stroke: '#bbb',
                  lineWidth: 1,
                }),
              };
            },
            data: seriesData,
          },
        ];
        option.yAxis.data = oriData.gridData;
        option.yAxis.type = 'category';
        option.grid.top = 126;
        if (axisName === 2 && this.fullScreen) {
          option.grid.right = 140;
        }
        option.yAxis.inverse = true;
        option.yAxis.axisLabel.formatter = function(value) {
          return that.yAxisFormatter(value);
        };
      } else if (this.viewName === 0) {
        option.color = colorArr;
        option.series = [];
        oriData.seriesData.forEach((k) => {
          option.series.push({
            type: 'line',
            symbol: 'none',
            lineStyle: {
              width: 1,
            },
            data: k.slice(1, -1),
          });
        });
      }
      return option;
    },
    /**
     * Expand/Collapse in full screen
     */
    toggleFullScreen() {
      this.removeTooltip();
      if (!this.fullScreen) {
        if (this.axisName === 2) {
          this.charOption.grid.right = 140;
        }
        this.charOption.toolbox.feature.myToolFullScreen.iconStyle.borderColor =
          '#00A5A7';
      } else {
        this.charOption.grid.right = 80;
        this.charOption.toolbox.feature.myToolFullScreen.iconStyle.borderColor =
          '#6D7278';
      }
      this.charObj.setOption(this.charOption);
      this.$emit('toggleFullScreen');
    },
    /**
     * Remove tooltip
     */
    removeTooltip() {
      if (this.zr) {
        if (this.zrDrawElement.hoverDots) {
          this.zrDrawElement.hoverDots.forEach((dot) => this.zr.remove(dot));
        }
        if (this.zrDrawElement.hoverLine) {
          this.zr.remove(this.zrDrawElement.hoverLine);
        }
        if (this.zrDrawElement.tooltip) {
          this.zr.remove(this.zrDrawElement.tooltip);
        }
        if (this.zrDrawElement.tooltipY) {
          this.zr.remove(this.zrDrawElement.tooltipY);
        }
        if (this.zrDrawElement.tooltipX) {
          this.zr.remove(this.zrDrawElement.tooltipX);
        }
      }
    },
    /**
     * Calculate polygon points
     * @param {Number} dataIndex
     * @param {Object} getCoord
     * @param {Number} yValueMapHeight
     * @return {Array} Array of ploygon points
     */
    makePolyPoints(dataIndex, getCoord, yValueMapHeight) {
      const points = [];
      const rawData = this.oriData.seriesData;
      const maxZ = this.oriData.maxZ;
      const minZ = this.oriData.minZ;
      for (let i = 0; i < rawData[dataIndex].length; ) {
        const x = this.getValue(rawData, dataIndex, i++);
        const y = this.getValue(rawData, dataIndex, i++);
        const z = this.getValue(rawData, dataIndex, i++);
        const pt = getCoord([x, y]);
        // Linear map in z axis
        if (maxZ !== minZ) {
          pt[1] -= ((z - minZ) / (maxZ - minZ)) * yValueMapHeight;
        }
        points.push(pt);
      }
      return points;
    },
    /**
     * Get convert point
     * @param {Array} pt value
     * @return {Array}
     */
    getCoord(pt) {
      return this.charObj.convertToPixel('grid', pt);
    },
    /**
     * Formate Y coordinate display
     * @param {Number} value
     * @return {Object}
     */
    yAxisFormatter(value) {
      let data = '';
      const filter = this.fullData.filter((k) => k.step === value);
      if (filter.length) {
        if (this.axisName === 2) {
          data = this.fullScreen
            ? this.dealrelativeTime(
                new Date(filter[0].wall_time * 1000).toString(),
            )
            : [];
        } else if (this.axisName === 1) {
          data = `${this.formateNUmber(
              (filter[0].relative_time).toFixed(0),
          )}s`;
        } else {
          data = this.formateNUmber(filter[0].step);
        }
      }
      return data;
    },
    /**
     * Formate time display
     * @param {Number} value
     * @return {Number} Formatted number
     */
    formateNUmber(value) {
      value = Number(value);
      if (value.toString().length > 6) {
        return value.toExponential(3);
      } else {
        return Math.round(value * 1000) / 1000;
      }
    },
    /**
     * Formate time display
     * @param {Object} time
     * @return {String} Formatted time
     */
    dealrelativeTime(time) {
      const arr = time.split(' ');
      const str = arr[0] + ' ' + arr[1] + ' ' + arr[2] + ',' + ' ' + arr[4];
      return str;
    },
    /**
     * Mouse move event
     * @param {Object} e Original event
     */
    mousemoveEvent(e) {
      const unit = 's';
      const nearestIndex = this.findNearestValue([e.offsetX, e.offsetY]);
      if (
        nearestIndex &&
        nearestIndex.yIndex !== null &&
        nearestIndex.binIndex !== null
      ) {
        const {binIndex, yIndex} = nearestIndex;
        const chartData = this.fullData;
        const hoveredItem = chartData[yIndex];
        const p = Math.max(0, d3.precisionRound(0.01, 1.01) - 1);
        const yValueFormat = d3.format(`.${p}e`);
        const gridRect = this.charObj
            .getModel()
            .getComponent('grid', 0)
            .coordinateSystem.getRect();
        const gridRectY = gridRect.y - 10;
        let linePoints = [];
        if (!hoveredItem || !hoveredItem.items[binIndex]) {
          return;
        }
        if (!this.chartTipFlag) {
          this.chartTipFlag = true;
          this.$emit('chartTipFlagChange', this.chartTipFlag);
        }
        if (this.viewName === 1 && yIndex !== null) {
          linePoints = this.makePolyPoints(yIndex, this.getCoord, gridRectY);
        } else if (this.viewName === 0 && hoveredItem.items) {
          hoveredItem.items.forEach((item) => {
            linePoints.push(this.getCoord([item[2], item[3]]));
          });
        }

        this.zrDrawElement.hoverLine = new echarts.graphic.Polyline({
          silent: true,
          shape: {
            points: linePoints.slice(1, -1),
          },
          z: 999,
        });
        this.zr.add(this.zrDrawElement.hoverLine);

        this.zrDrawElement.tooltip = new echarts.graphic.Text({});
        let itemX;
        const x = hoveredItem.items[binIndex][2];
        let z = 0;
        chartData.forEach((dataItem, index) => {
          const y = dataItem.step;
          const pt = this.getCoord([x, y]);
          if (index === yIndex) {
            z = hoveredItem.items[binIndex][3];
          } else {
            const items = dataItem.items;
            for (let k = 1; k < items.length - 1; k++) {
              const nextX = items[k + 1][2];
              const nextZ = items[k + 1][3];
              if (items[k][2] === x) {
                z = items[k][3];
                break;
              } else if (items[k][2] < x && nextX > x) {
                const proportionX = (x - items[k][2]) / (nextX - items[k][2]);
                z = (nextZ - items[k][3]) * proportionX + items[k][3];
                break;
              }
            }
          }
          itemX = pt[0];
          const circleOption = {
            z: 1000,
          };
          if (this.viewName === 1) {
            pt[1] -=
              ((z - this.oriData.minZ) /
                (this.oriData.maxZ - this.oriData.minZ)) *
              gridRectY;
            circleOption.shape = {
              cx: itemX,
              cy: pt[1],
              r: 1.5,
            };
          } else {
            circleOption.shape = {
              cx: 0,
              cy: 0,
              r: 1.5,
            };
            circleOption.position = this.charObj.convertToPixel('grid', [x, z]);
          }
          const dot = new echarts.graphic.Circle(circleOption);
          this.zr.add(dot);
          this.zrDrawElement.hoverDots.push(dot);
        });
        this.zrDrawElement.tooltip = new echarts.graphic.Text({});

        let htmlStr = '';
        const hoveredAxis = hoveredItem.items[binIndex][3];
        htmlStr = `<td>${
          hoveredAxis.toString().length >= 6
            ? yValueFormat(hoveredAxis)
            : hoveredAxis
        }</td><td style="text-align:center;">${this.formateNUmber(
            hoveredItem.step,
        )}</td><td>${this.formateNUmber(
            (hoveredItem.relative_time).toFixed(0),
        )}${unit}</td><td>${this.dealrelativeTime(
            new Date(hoveredItem.wall_time * 1000).toString(),
        )}</td>`;
        const dom = document.querySelector('#tipTr');
        dom.innerHTML = htmlStr;
        const chartElement = document.getElementById(this.itemId);
        if (chartElement) {
          if (!this.fullScreen) {
            const chartWidth =
              chartElement.parentNode.parentNode.parentNode.parentNode
                  .clientWidth;
            const chartHeight =
              chartElement.parentNode.parentNode.parentNode.parentNode
                  .clientHeight;
            const left =
              chartElement.parentNode.parentNode.parentNode.parentNode
                  .offsetLeft;
            const top =
              chartElement.parentNode.parentNode.parentNode.parentNode
                  .offsetTop;
            const echartTip = document.querySelector('#echartTip');
            echartTip.style.top = `${top + chartHeight - 60}px`;
            if (left > echartTip.clientWidth) {
              echartTip.style.left = `${left - echartTip.clientWidth}px`;
            } else {
              echartTip.style.left = `${left + chartWidth}px`;
            }
          } else {
            const width = document.querySelector('#echartTip').clientWidth;
            const height = document.querySelector('#echartTip').clientHeight;
            const screenWidth = document.body.scrollWidth;
            const screenHeight = document.body.scrollHeight;
            const scrollTop = document.querySelector('.cl-show-data-content')
                .scrollTop;
            const offsetTop = document.querySelector('.cl-show-data-content')
                .offsetTop;
            if (
              height + e.event.y + 20 > screenHeight &&
              screenHeight > height
            ) {
              document.querySelector('#echartTip').style.top = `${e.event.y +
                scrollTop -
                height -
                20 -
                offsetTop}px`;
            } else {
              document.querySelector('#echartTip').style.top = `${e.event.y +
                scrollTop +
                20 -
                offsetTop}px`;
            }
            // Blank area on the right of the chart is 80
            if (width + e.event.x + 80 > screenWidth && screenWidth > width) {
              document.querySelector('#echartTip').style.left = `${e.event.x -
                width -
                20}px`;
            } else {
              document.querySelector('#echartTip').style.left = `${e.event.x +
                20}px`;
            }
          }
        }

        this.zrDrawElement.tooltipX = new echarts.graphic.Text({
          position: [itemX, gridRect.y + gridRect.height],
          style: {
            text:
              x.toString().length >= 6
                ? x.toExponential(3)
                : Math.round(x * 1000) / 1000,
            textFill: '#fff',
            textAlign: 'center',
            fontSize: 12,
            textBackgroundColor: '#333',
            textBorderWidth: 2,
            textPadding: [5, 7],
            rich: {},
          },
          z: 2000,
        });
        this.zr.add(this.zrDrawElement.tooltipX);
        if (this.viewName === 1 && linePoints && linePoints.length) {
          let text = '';
          if (yIndex !== null) {
            text = this.yAxisFormatter(hoveredItem.step);
          }
          this.zrDrawElement.tooltipY = new echarts.graphic.Text({
            position: [
              gridRect.x + gridRect.width,
              linePoints[linePoints.length - 1][1],
            ],
            style: {
              text: text,
              textFill: '#fff',
              textVerticalAlign: 'middle',
              fontSize: 12,
              textBackgroundColor: '#333',
              textBorderWidth: 2,
              textPadding: [5, 7],
              rich: {},
            },
            z: 2000,
          });
          this.zr.add(this.zrDrawElement.tooltipY);
        }
      }
    },
    /**
     * Find nearest value
     * @param {Array} eventPoint Value
     * @return {Object}
     */
    findNearestValue(eventPoint) {
      if (!eventPoint || !eventPoint.length || !this.charObj || !this.oriData) {
        return;
      }
      const value = this.charObj.convertFromPixel('grid', eventPoint);
      if (!value || !value.length) {
        return;
      }
      let binIndex = null;
      let yIndex = null;
      let nearestX = Infinity;
      let nearestY = -Infinity;
      let nearestYData = Infinity;
      const gridRect = this.charObj
          .getModel()
          .getComponent('grid', 0)
          .coordinateSystem.getRect();
      const gridRectY = gridRect.y - 10;
      const x = value[0];
      this.fullData.forEach((dataItem, i) => {
        let distY;
        let yAxis;
        for (let k = 0; k < dataItem.items.length - 1; k++) {
          const item = dataItem.items[k];
          const itemNext = dataItem.items[k + 1];
          const nextX = itemNext[2];
          const nextZ = itemNext[3];
          if (item.length >= 4) {
            if (item[2] < x && nextX >= x) {
              const proportionX = (x - item[2]) / (nextX - item[2]);
              yAxis = (nextZ - item[3]) * proportionX + item[3];
              distY = Math.abs(value[1] - yAxis);
              break;
            }
          }
        }
        if (this.viewName === 0 && distY < nearestYData) {
          nearestYData = distY;
          yIndex = i;
        } else if (this.viewName === 1) {
          const pt = this.getCoord([x, dataItem.step]);
          const ptStep = pt[1];
          pt[1] -=
            ((yAxis - this.oriData.minZ) /
              (this.oriData.maxZ - this.oriData.minZ)) *
            gridRectY;
          if (
            eventPoint[1] > pt[1] &&
            eventPoint[1] < ptStep &&
            ptStep > nearestY
          ) {
            nearestY = ptStep;
            yIndex = i;
          }
        }
      });
      if (yIndex === null && this.viewName === 1) {
        this.fullData.forEach((item, index) => {
          if (index >= value[1]) {
            yIndex = yIndex === null ? index : Math.min(yIndex, index);
          }
        });
      }
      if (yIndex !== null) {
        const yData = this.fullData[yIndex].items;
        yData.forEach((ele, index) => {
          const distX = Math.abs(ele[2] - value[0]);
          if (distX < nearestX) {
            nearestX = distX;
            binIndex = index;
          }
        });
        binIndex =
          binIndex === 0
            ? 1
            : binIndex === yData.length - 1
            ? yData.length - 2
            : binIndex;
      }
      return {
        binIndex,
        yIndex,
      };
    },
    /**
     * Calculate gradient color
     * @param {String} startColor
     * @param {String} endColor
     * @param {Number} step
     * @return {Array} Array of gradient color
     */
    getGrientColor(startColor, endColor, step) {
      const startRgb = this.formatColor(startColor);
      const endRgb = this.formatColor(endColor);
      const gapRgbR = (endRgb[0] - startRgb[0]) / step;
      const gapRgbG = (endRgb[1] - startRgb[1]) / step;
      const gapRgbB = (endRgb[2] - startRgb[2]) / step;
      const colorResult = [];
      for (let i = 0; i < step; i++) {
        const sR = parseInt(gapRgbR * i + startRgb[0]);
        const sG = parseInt(gapRgbG * i + startRgb[1]);
        const sB = parseInt(gapRgbB * i + startRgb[2]);
        const hex = this.formatColorToHex(`rgb(${sR},${sG},${sB})`);
        colorResult.push(hex);
      }
      return colorResult;
    },
    /**
     * Converts a color string to recognizable format
     * @param {String} str Color string
     * @return {String}
     */
    formatColor(str) {
      if (!str) {
        return;
      }
      const colorReg = /^([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/;
      let colorStr = str.toLowerCase().slice(1);
      if (colorReg.test(colorStr)) {
        let colorStrNew = '';
        if (colorStr.length === 3) {
          for (let i = 0; i < 3; i++) {
            colorStrNew += colorStrNew
                .slice(i, i + 1)
                .concat(colorStrNew.slice(i, i + 1));
          }
          colorStr = colorStrNew;
        }
        const colorFormat = [];
        for (let i = 0; i < 6; i += 2) {
          colorFormat.push(parseInt(`0x${colorStr.slice(i, i + 2)}`));
        }
        return colorFormat;
      } else {
        return colorStr;
      }
    },
    /**
     * Converts rgb color string to hex
     * @param {String} rgb Rgb color
     * @return {String} Hex color
     */
    formatColorToHex(rgb) {
      const regRgb = /^(rgb|RGB)/g;
      if (regRgb.test(rgb)) {
        const colorSplit = rgb.replace(/(?:(|)|rgb|RGB)*/g, '').split(',');
        let hexStr = '';
        for (let i = 0; i < colorSplit.length; i++) {
          let hexItem = Number(colorSplit[i]).toString(16);
          hexItem = hexItem < 10 ? `0${hexItem}` : hexItem;
          if (hexItem === '0') {
            hexItem += hexItem;
          }
          hexStr += hexItem;
        }
        if (hexStr.length !== 6) {
          hexStr = rgb;
        }
        return hexStr;
      }
    },
    /**
     * Get value
     * @param {Object} seriesData
     * @param {Number} dataIndex
     * @param {Number} i
     * @return {Number}
     */
    getValue(seriesData, dataIndex, i) {
      return seriesData[dataIndex][i];
    },
    /**
     * Unbing event
     */
    clearZrData() {
      if (this.zr) {
        this.removeTooltip();
        this.zr.off('mouseout', 'mousemove');
        this.zr = null;
      }
    },
    /**
     * Update histogram data
     */
    updateHistogramData() {
      this.$nextTick(() => {
        if (this.requestError) {
          this.requestError = false;
          this.viewResizeFlag = true;
        }
        this.formatDataToChar();
        this.updateSampleData();
        this.sampleEventBind();
      });
    },
    /**
     * Show error message
     * @param {String} errorMsg Error message
     */
    showRequestErrorMessage(errorMsg) {
      this.errorMsg = errorMsg;
      this.requestError = true;
    },
  },
  destroyed() {
    this.clearZrData();
  },
};
</script>
<style lang="scss">
.cl-histogram-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  .data-show-container {
    width: 100%;
    flex: 1;
    .data-item {
      width: 100%;
      height: 100%;
    }
    .error-msg-container {
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
    }
  }
}
</style>

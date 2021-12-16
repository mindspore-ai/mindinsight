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
  <div class="cl-slickgrid-container">
    <div class="data-show-container">
      <div v-show="incorrectData"
           class="error-msg-container">
        {{$t('components.gridIncorrectDataError')}}
      </div>
      <div v-show="!incorrectData && requestError"
           class="error-msg-container">
        {{errorMsg}}
      </div>
      <div v-show="!fullData.length && updated && !incorrectData && !requestError"
           class="error-msg-container">
        {{$t('components.gridTableNoData')}}
      </div>
      <!-- Chart Mode -->
      <div v-show="!!fullData.length && !incorrectData && displayMode === displayModes[0].value"
           class="heatmap"
           ref="heatmap"></div>
      <!-- Table Mode -->
      <div :id="itemId"
           v-show="!!fullData.length && !incorrectData && displayMode === displayModes[1].value"
           class="grid-item"></div>
    </div>
    <!-- Operators container -->
    <div class="operators-container"
         v-if="showOperators && (fullData.length || requestError)">
      <!-- Left -->
      <div class="operators">
        <!-- Filter -->
        <div class="filter-container"
             v-if="showFilterInput"
             @keyup.enter="filterChange">
          <div class="filter-input-title">{{$t('components.dimsFilterInputTitle')}}
            <span :title="$t('components.dimsFilterInputTip')"
                  class="el-icon-info"></span>
          </div>
          <div v-for="(item, itemIndex) in filterArr"
               class="filter-item"
               :key="itemIndex">
            <el-input class="filter-input long-input"
                      :class="item.showError ? 'error-border' : ''"
                      v-model="item.model"></el-input>
            <span class="input-behind"
                  v-if="itemIndex === filterArr.length - 1">{{$t('symbols.slashes')}}</span>
            <span class="input-behind"
                  v-else>{{$t('symbols.point')}}</span>
          </div>
          <el-button class="filter-check"
                     size="mini"
                     v-if="!!filterArr.length"
                     @click="filterChange">
            <i class="el-icon-check"></i>
          </el-button>
          <span class="filter-incorrect-text"
                v-if="!filterCorrect">{{$t('components.inCorrectInput')}}</span>
        </div>
        <!-- Shape -->
        <span>{{ $t('tensors.dimension') }} {{ shape }}</span>
      </div>
      <!-- Right -->
      <div class="operators">
        <!-- Mode -->
        {{ $t('tensors.mode') }}
        <el-select v-model="displayMode"
                   class="mode-selector"
                   :style="{
                     width:`${modeWidth}px`
                   }"
                   @change="handleDisplayModeChange">
          <el-option v-for="mode of displayModes"
                     :key="mode.value"
                     :label="mode.label"
                     :value="mode.value"></el-option>
        </el-select>
        <!-- Category -->
        {{$t('components.category')}}
        <el-select v-model="category"
                   class="category-selector"
                   :style="{
                     width:`${categoryWidth}px`
                   }"
                   @change="accuracyChange">
          <el-option v-for="item in categoryArr"
                     :key="item.label"
                     :label="item.label"
                     :value="item.value"></el-option>
        </el-select>
        <!-- Accuracy -->
        {{$t('components.gridAccuracy')}}
        <span :title="$t('components.accuracyTips')"
              class="el-icon-info"></span>
        <el-select v-model="accuracy"
                   class="accuracy-selector"
                   @change="accuracyChange">
          <el-option v-for="item in accuracyArr"
                     :key="item.label"
                     :label="item.label"
                     :value="item.value"></el-option>
        </el-select>
      </div>

    </div>
  </div>
</template>

<script>
import 'slickgrid/css/smoothness/jquery-ui-1.11.3.custom.css';
import 'slickgrid/slick.grid.css';
import 'slickgrid/lib/jquery-3.1.0';
import 'slickgrid/lib/jquery-ui-1.9.2';
import 'slickgrid/lib/jquery.event.drag-2.3.0.js';
import 'slickgrid/slick.core.js';
import 'slickgrid/slick.dataview.js';
import 'slickgrid/slick.grid.js';
import CommonProperty from '@/common/common-property.js';
import echarts, { echartsThemeName } from '@/js/echarts';

// Data display mode
const [TABLE, CHART] = ['table', 'chart'];
const gridPadding = [40, 0, 10, 40]; // Same as padding in CSS rule order
const enCategoryWidth = 103; //en-us category selecter width
const enModeWidth = 82; //en-us mode selecter width
const cnWidth = 103; //zh-cn mode ande category selecter width
export default {
  props: {
    // Original data
    fullData: {
      type: Array,
      default() {
        return [];
      },
    },
    // Display operation Bar
    showOperators: {
      type: Boolean,
      default: true,
    },
    showFilterInput: {
      type: Boolean,
      default: true,
    },
    // Display full screen
    fullScreen: {
      type: Boolean,
      default: false,
    },
    gridType: {
      type: String,
      default: 'value',
    },
    // Maximum number of columns
    // If the value is less then 0, there is no maximum value.
    columnLimitNum: {
      type: Number,
      default: -1,
    },
  },
  data() {
    return {
      itemId: '', // Dom id
      gridObj: null, // Slickgrid object
      columnsData: [], // Column information
      columnsLength: 0, // Column length
      filterArr: [], // Dimension selection array
      formateData: [], // Formatted data
      formateArr: [], // Formatted array
      statistics: {}, // Object contain maximum and minimum
      accuracy: 10, // Accuracy value
      incorrectData: false, // Whether the dimension is correctly selected
      updated: false, // Updated
      scrollTop: false, // Whether scroll to the top
      filterCorrect: true, // Whether the dimension input is correct
      requestError: false, // Exceeded the specification
      errorMsg: '', // Error message
      viewResizeFlag: false, // Size reset flag
      // Accuracy options
      accuracyArr: new Array(11).fill(null).map((_, i) => {
        return { label: i, value: i };
      }),
      // Table configuration items
      optionObj: {
        enableColumnReorder: false,
        enableCellNavigation: true,
        frozenColumn: 0,
        frozenRow: 0,
      },
      gridTypeKeys: {
        value: 'value',
        compare: 'compare',
      },
      axisStartIndex: {
        rowStartIndex: 0,
        colStartIndex: 0,
      },
      shape: '',
      categoryArr: [
        { label: this.$t('components.value'), value: 'value' },
        { label: this.$t('components.scientificCounting'), value: 'science' },
      ],
      category: 'value', // value:Numerical notation      science:Scientific notation
      gridTableThemeObj: CommonProperty.tensorThemes[this.$store.state.themeIndex],
      displayMode: CHART,
      displayModes: [
        { label: this.$t('tensors.chartMode'), value: CHART },
        { label: this.$t('tensors.tableMode'), value: TABLE },
      ],
      chartInstance: null,
      filterStr: null,
      categoryWidth: 0,
      modeWidth: 0,
    };
  },
  watch: {
    showFilterInput() {
      this.resizeView();
    },
  },
  mounted() {
    this.init();
  },
  methods: {
    /**
     * Init common info of tensor value
     * @param {Boolean} newDataFlag Whether data is updated
     * @param {Array} dimension Array of dimension
     * @param {Object} statistics Object contains maximum and minimum
     * @param {String} filterStr String of dimension selection
     */
    initCommonInfo(newDataFlag, dimension, statistics, filterStr) {
      this.shape = dimension;
      this.updated = true;
      this.requestError = false;
      if (!this.fullData || !this.fullData.length) {
        return;
      }
      if (newDataFlag) {
        this.viewResizeFlag = true;
        this.initializeFilterArr(dimension, filterStr);
        this.scrollTop = true;
      } else if (!this.filterArr.length && dimension && filterStr) {
        this.initializeFilterArr(dimension, filterStr);
      }
      if (newDataFlag || this.statistics.overall_max === undefined) {
        this.statistics = statistics;
      }
      this.handleDisplayModeChange();
    },
    handleDisplayModeChange() {
      this.$nextTick(() => {
        switch (this.displayMode) {
          case TABLE:
            this.updateGridData();
            break;
          case CHART:
            this.chartInstance && this.chartInstance.resize();
            this.renderHeatmapChart();
            break;
        }
      });
    },
    /**
     * Initialize
     */
    init() {
      this.itemId = `${new Date().getTime()}` + `${this.$store.state.componentsCount}`;
      this.$store.commit('componentsNum');
      if (this.$store.state.language === 'en-us') {
        this.categoryWidth = enCategoryWidth;
        this.modeWidth = enModeWidth;
      } else {
        this.categoryWidth = cnWidth;
        this.modeWidth = cnWidth;
      }
    },
    /**
     * judge the value type and transform to Float
     * @param {String} value
     */
    processData(value) {
      const {judgeDataType, accuracy} = this;
      return value === 'null' 
        ? 0 : 
        judgeDataType(value) 
        ? value 
        : +value.toFixed(accuracy);
    },
    /**
     * Render heatmap chart by fullData
     * @param {Object} statistics Object contains maximum and minimum
     * @param {string} filterStr String of dimension selection
     */
    renderHeatmapChart() {
      const data = this.fullData;
      if (!data || !data.length) {
        return;
      }
      if (!this.initHeatmapChart()) {
        return;
      }
      const seriesData = [];
      const xAxisData = [];
      const yAxisData = [];
      const { rowStartIndex, colStartIndex } = this.axisStartIndex;
      if (Array.isArray(data)) {
        if (Array.isArray(data[0])) {
          // Matrix
          data.forEach((row, rowIndex) => {
            yAxisData.push(rowStartIndex + rowIndex);
            row.forEach((item, columnIndex) => {
              if (!rowIndex) {
                xAxisData.push(colStartIndex + columnIndex);
              }
              seriesData.push([columnIndex, rowIndex, item, this.processData(item)]);
            });
          });
        } else {
          // Array
          yAxisData.push(rowStartIndex);
          data.forEach((item, columnIndex) => {
            xAxisData.push(colStartIndex + columnIndex);
            seriesData.push([columnIndex, 0, item, this.processData(item)]);
          });
        }
      } else {
        // Number
        xAxisData.push(colStartIndex);
        yAxisData.push(rowStartIndex);
        seriesData.push([0, 0, data, this.processData(data)]);
      }
      const { overall_min, overall_max } = this.statistics;
      const minAbs = Math.abs(overall_min);
      const maxAbs = Math.abs(overall_max);
      let ultimate = 0;
      if (!Number.isNaN(minAbs) && !Number.isNaN(maxAbs)) {
        ultimate = minAbs < maxAbs ? maxAbs : minAbs;
      } else if (!Number.isNaN(minAbs) && Number.isNaN(maxAbs)) {
        ultimate = minAbs;
      } else if (Number.isNaN(minAbs) && !Number.isNaN(maxAbs)) {
        ultimate = maxAbs;
      }
      this.chartInstance.setOption({
        visualMap: {
          min: -ultimate,
          max: ultimate,
          inRange: {
            color: [
              `rgb(${this.gridTableThemeObj.negativeColor})`,
              this.gridTableThemeObj.middleColor,
              `rgb(${this.gridTableThemeObj.positiveColor})`,
            ],
          },
        },
        xAxis: {
          data: xAxisData,
        },
        yAxis: {
          data: yAxisData,
        },
        series: {
          data: seriesData,
        },
      });
    },
    initHeatmapChart() {
      if (this.displayMode === CHART && this.$refs.heatmap) {
        if (!this.chartInstance) {
          this.chartInstance = echarts.init(this.$refs.heatmap, echartsThemeName);
          this.chartInstance.setOption({
            tooltip: {
              position: 'top',
            },
            grid: {
              top: gridPadding[0],
              right: gridPadding[1],
              bottom: gridPadding[2],
              left: gridPadding[3],
            },
            dataZoom: [
              {
                type: 'inside',
                xAxisIndex: 0,
                yAxisIndex: 0,
              },
            ],
            xAxis: {
              type: 'category',
              data: [],
              position: 'top',
              splitArea: {
                show: true,
              },
            },
            yAxis: {
              type: 'category',
              data: [],
              splitArea: {
                show: true,
              },
              inverse: true,
            },
            visualMap: {
              show: false,
            },
            series: [
              {
                name: 'tensorHeatmap',
                type: 'heatmap',
                data: [],
                label: {
                  show: false,
                },
                emphasis: {
                  itemStyle: {
                    shadowBlur: 10,
                    shadowColor: 'rgba(0, 0, 0, 0.5)',
                  },
                },
                tooltip: {
                  formatter: (params) => {
                    const { category, accuracy, judgeDataType } = this;
                    let value = params.data[3]; // Original data
                    value = judgeDataType(value)
                      ? value
                      : category === 'science'
                      ? value.toExponential(accuracy)
                      : value.toFixed(accuracy);
                    return `
                      x: ${params.data[0]}<br>
                      y: ${params.data[1]}<br>
                      value: ${value}
                    `;
                  },
                },
              },
            ],
          });
        }
        return true;
      }
      return false;
    },
    /**
     * Initialize dimension selection
     * @param {Array} dimension Dimension array
     * @param {String} filterStrs Dimension String
     */
    initializeFilterArr(dimension, filterStrs) {
      this.filterCorrect = true;
      if (!filterStrs) {
        this.filterArr = [];
        return;
      }
      const fitlerStrList = filterStrs.slice(1, filterStrs.length - 1).split(',');
      const filterInputList = [];
      const specificDimensions = [];
      const rangeDimensions = [];
      let dimensionNumber = fitlerStrList.length;
      fitlerStrList.forEach((filterStr, i) => {
        filterInputList.push({
          model: filterStr,
          max: dimension[i] - 1,
          showError: false,
        });
        if (filterStr.includes(':')) {
          // Range in dimension
          if (dimensionNumber <= 2) {
            const [startIndexStr] = filterStr.split(':');
            if (startIndexStr) {
              const startIndex = +startIndexStr < 0 ? dimension[i] + +startIndexStr : +startIndexStr;
              rangeDimensions.push(startIndex);
            } else {
              rangeDimensions.push(0);
            }
          }
        } else {
          // Specific Index in dimension
          dimensionNumber--;
          if (dimensionNumber < 2) {
            const filterNumber = +filterStr;
            const startIndex = filterNumber < 0 ? dimension[i] + filterNumber : filterNumber;
            specificDimensions.push(startIndex);
          }
        }
      });
      this.filterArr = filterInputList;
      if (rangeDimensions.length === 2) {
        this.axisStartIndex = {
          rowStartIndex: rangeDimensions[0],
          colStartIndex: rangeDimensions[1],
        };
      } else if (rangeDimensions.length === 1) {
        this.axisStartIndex = {
          rowStartIndex: specificDimensions.length ? specificDimensions[0] : 0,
          colStartIndex: rangeDimensions[0],
        };
      } else {
        if (specificDimensions.length) {
          this.axisStartIndex = {
            rowStartIndex: specificDimensions[0],
            colStartIndex: specificDimensions.length > 1 ? specificDimensions[1] : 0,
          };
        } else {
          this.axisStartIndex = {
            rowStartIndex: 0,
            colStartIndex: 0,
          };
        }
      }
    },
    /**
     * Initialize column information
     */
    formatColumnsData() {
      this.columnsData = [
        {
          id: -1,
          name: ' ',
          field: -1,
          width: 120,
          headerCssClass: 'headerStyle',
        },
      ];
      const columnSample = this.formateData[0];
      if (columnSample) {
        columnSample.forEach((num, numIndex) => {
          const order = numIndex + this.axisStartIndex.colStartIndex;
          this.columnsData.push({
            id: order,
            name: order,
            field: order,
            width: 120,
            headerCssClass: 'headerStyle',
            formatter: this.gridType === this.gridTypeKeys.compare ? this.formatCompareColor : this.formatValueColor,
          });
        });
      } else {
        this.columnsData = [];
      }
    },
    /**
     * Setting the Background color of data
     * @param {Number} row
     * @param {Number} cell
     * @param {String} value,
     * @param {Object} columnDef
     * @param {Object} dataContext
     * @return {String}
     */
    formatValueColor(row, cell, value, columnDef, dataContext) {
      if (!cell || !value || this.judgeDataType(value)) {
        return value;
      } else if (value < 0) {
        return `<span class="table-item-span" style="background:rgba(${this.gridTableThemeObj.negativeColor}, ${
          value / this.statistics.overall_min
        })">${value}</span>`;
      } else {
        return `<span class="table-item-span" style="background:rgba(${this.gridTableThemeObj.positiveColor}, ${
          value / this.statistics.overall_max
        })">${value}</span>`;
      }
    },
    judgeDataType(value) {
      return (
        isNaN(value) ||
        value === 'Infinity' ||
        value === '-Infinity' ||
        typeof value === 'boolean' ||
        value === 'null'
      );
    },
    /**
     * Setting the background color of data
     * @param {Number} row
     * @param {Number} cell
     * @param {String} value,
     * @param {Object} columnDef
     * @param {Object} dataContext
     * @return {String}
     */
    formatCompareColor(row, cell, value, columnDef, dataContext) {
      if (value instanceof Array && value.length >= 3) {
        const valueNum = value[2];
        if (!cell || !valueNum || this.judgeDataType(valueNum)) {
          return `<span class="table-item-span" title="${value[0]}→${value[1]}">${valueNum}</span>`;
        } else if (valueNum < 0) {
          return `<span class="table-item-span" title="${value[0]}→${
            value[1]
          }" style="background:rgba(227, 125, 41, ${valueNum / this.statistics.overall_min})">${valueNum}</span>`;
        } else {
          return `<span class="table-item-span" title="${value[0]}→${value[1]}" style="background:rgba(0, 165, 167, ${
            valueNum / this.statistics.overall_max
          })">${valueNum}</span>`;
        }
      } else {
        return value;
      }
    },
    calcForArrDims(array) {
      let dims = 0;
      let curValue = array;
      while (curValue instanceof Array && dims <= 3) {
        dims++;
        curValue = curValue[0];
      }
      return dims;
    },
    /**
     * Convetring raw data into table data
     */
    formatGridArray() {
      const dims = this.calcForArrDims(this.fullData);
      if (dims > 3) {
        this.formateData = [[[]]];
        this.columnsData = [];
      } else if (dims === 0) {
        this.formateData = [[this.fullData]];
      } else if (dims === 1) {
        this.formateData = [this.fullData];
      } else {
        this.formateData = this.fullData;
      }
      if (this.gridType === this.gridTypeKeys.compare && dims === 2) {
        this.formateData = [this.formateData];
      }
      const tempArr = [];
      if (this.gridType === this.gridTypeKeys.compare) {
        this.formateData.forEach((outerData, outerIndex) => {
          const tempData = {
            '-1': outerIndex + this.axisStartIndex.rowStartIndex,
          };
          outerData.forEach((innerData, innerIndex) => {
            const innerOrder = innerIndex + this.axisStartIndex.colStartIndex;
            const tempArr = [];
            innerData.forEach((innerValue) => {
              if (this.judgeDataType(innerValue)) {
                tempArr.push(innerValue);
              } else {
                if (this.category === 'science') {
                  tempArr.push(innerValue.toExponential(this.accuracy));
                } else {
                  tempArr.push(innerValue.toFixed(this.accuracy));
                }
              }
            });
            tempData[innerOrder] = tempArr;
          });
          tempArr.push(tempData);
        });
      } else {
        this.formateData.forEach((outerData, outerIndex) => {
          const tempData = {
            '-1': outerIndex + this.axisStartIndex.rowStartIndex,
          };
          outerData.forEach((innerData, innerIndex) => {
            const innerOrder = innerIndex + this.axisStartIndex.colStartIndex;
            if (this.judgeDataType(innerData)) {
              tempData[innerOrder] = innerData;
            } else {
              if (this.category === 'science') {
                tempData[innerOrder] = innerData.toExponential(this.accuracy);
              } else {
                tempData[innerOrder] = innerData.toFixed(this.accuracy);
              }
            }
          });
          tempArr.push(tempData);
        });
      }
      this.formateArr = tempArr;
    },
    /**
     * Update the table
     */
    updateGrid() {
      this.$nextTick(() => {
        if (!this.gridObj) {
          this.gridObj = new window.Slick.Grid(`#${this.itemId}`, this.formateArr, this.columnsData, this.optionObj);
          this.columnsLength = this.columnsData.length;
        }
        this.gridObj.setData(this.formateArr, this.scrollTop);
        this.scrollTop = false;
        const columnsLength = this.columnsData.length;
        if (this.columnsLength !== columnsLength || this.viewResizeFlag) {
          this.gridObj.setColumns(this.columnsData);
          this.columnsLength = columnsLength;
          this.viewResizeFlag = false;
        }
        this.gridObj.render();
      });
    },
    /**
     * Accuracy changed
     * @param {Number} value The value after changed
     */
    accuracyChange(value) {
      this.formatGridArray();
      if (this.displayMode === CHART) {
        this.renderHeatmapChart()
      } else {
        if (!this.requestError && !this.incorrectData) {
          this.updateGrid();
        }
      }
    },
    /**
     * Dimension selection changed
     */
    filterChange() {
      // filter condition
      let filterCorrect = true;
      let incorrectData = false;
      let limitCount = 2;
      const indexArr = [];
      const tempArr = [];
      this.filterArr.forEach((filter, index) => {
        let value = filter.model.trim();
        if (!isNaN(value)) {
          if (value < -(filter.max + 1) || value > filter.max || value === '' || value % 1) {
            filter.showError = true;
            filterCorrect = false;
          } else {
            filter.showError = false;
            value = Number(value);
          }
        } else if (value.indexOf(':') !== -1) {
          indexArr.push(index);
          const tempResult = this.checkCombinatorialInput(filter);
          if (tempResult) {
            filter.showError = false;
            if (!limitCount) {
              incorrectData = true;
            } else {
              limitCount--;
            }
          } else {
            filter.showError = true;
            filterCorrect = false;
          }
        } else {
          filter.showError = true;
          filterCorrect = false;
        }
        tempArr.push(value);
      });
      if (indexArr.length) {
        const lastIndex = indexArr.pop();
        const filterItem = this.filterArr[lastIndex];
        if (this.columnLimitNum > 0 && filterItem && !filterItem.showError && filterItem.max >= this.columnLimitNum) {
          const result = this.checkFilterLimitOver(filterItem);
          if (result) {
            filterItem.showError = true;
            filterCorrect = false;
          }
        }
      }
      this.filterCorrect = filterCorrect;
      if (incorrectData && filterCorrect) {
        this.incorrectData = true;
        return;
      } else {
        this.incorrectData = false;
      }
      if (filterCorrect) {
        this.viewResizeFlag = true;
        this.$emit('martixFilterChange', tempArr);
      }
    },
    /**
     * Check filter input limit
     * @param {Object} filter Filter item
     * @return {Boolean} Filter over limit
     */
    checkFilterLimitOver(filter) {
      let result = false;
      const value = filter.model.trim();
      const tempArr = value.split(':');
      let startValue = tempArr[0] ? tempArr[0] : 0;
      let endValue = tempArr[1] ? tempArr[1] : filter.max + 1;
      startValue = startValue < 0 ? filter.max + Number(startValue) + 1 : Number(startValue);
      endValue = endValue < 0 ? filter.max + Number(endValue) + 1 : Number(endValue);
      if (endValue - startValue > this.columnLimitNum) {
        result = true;
      }
      return result;
    },
    /**
     * Check combinatorial input
     * @param {Object} filter Filter item
     * @return {Boolean} Verification result
     */
    checkCombinatorialInput(filter) {
      const value = filter.model.trim();
      const tempArr = value.split(':');
      const startValue = tempArr[0];
      const endValue = tempArr[1];
      const limitCount = 2;
      if (!!startValue && (isNaN(startValue) || startValue < -(filter.max + 1) || startValue > filter.max)) {
        return false;
      }
      if (
        !!endValue &&
        (isNaN(endValue) || endValue <= -(filter.max + 1) || endValue > filter.max + 1 || !Number(endValue))
      ) {
        return false;
      }
      if (tempArr.length > limitCount) {
        return false;
      } else if (!startValue && !endValue) {
        return true;
      } else if (!!startValue && !!endValue) {
        const sv = startValue < 0 ? filter.max + Number(startValue) + 1 : Number(startValue);
        const ev = endValue < 0 ? filter.max + Number(endValue) + 1 : Number(endValue);
        if (ev <= sv) {
          return false;
        } else {
          return true;
        }
      } else {
        return true;
      }
    },
    updateGridData() {
      this.formatGridArray();
      this.formatColumnsData();
      if (!this.incorrectData) {
        this.updateGrid();
      }
    },
    /**
     * Update the view Size
     */
    resizeView() {
      this.$nextTick(() => {
        switch (this.displayMode) {
          case CHART:
            this.chartInstance && this.chartInstance.resize();
            break;
          case TABLE:
            if (this.gridObj) {
              if (this.incorrectData || this.requestError) {
                this.viewResizeFlag = true;
              } else {
                this.$nextTick(() => {
                  this.gridObj.resizeCanvas();
                  this.gridObj.render();
                });
              }
            }
            break;
        }
      });
    },
    /**
     * Expand/Collapse in full screen
     */
    toggleFullScreen() {
      this.$emit('toggleFullScreen');
    },
    /**
     * Show error message
     * @param {String} errorMsg Error message
     * @param {Array} dimension Array of dimension
     * @param {String} filterStr String of dimension selection
     * @param {Boolean} isUpdate Whether to reset
     */
    showRequestErrorMessage(errorMsg, dimension, filterStr, isUpdate) {
      this.shape = dimension;
      this.errorMsg = errorMsg;
      if ((!this.filterArr.length && dimension && filterStr) || isUpdate) {
        this.initializeFilterArr(dimension, filterStr);
      }
      this.requestError = true;
    },
  },
  destroyed() {},
};
</script>
<style>
.cl-slickgrid-container .operators-container {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
}
.cl-slickgrid-container .operators-container .operators {
  display: flex;
  gap: 4px;
  align-items: center;
}
.cl-slickgrid-container .operators-container .operators .filter-container {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: nowrap;
}
.cl-slickgrid-container .operators-container .operators .long-input {
  width: 100px;
}
.cl-slickgrid-container .operators-container .operators .long-input input {
  text-align: center;
}
.cl-slickgrid-container .operators-container .operators .error-border input {
  border-color: red;
}
.cl-slickgrid-container .operators-container .filter-incorrect-text {
  color: red;
}
.cl-slickgrid-container .operators-container .operators .filter-item {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: nowrap;
}
.cl-slickgrid-container .operators-container .operators .mode-selector {
  width: 100px;
}
.cl-slickgrid-container .operators-container .operators .category-selector {
  width: 100px;
}
.cl-slickgrid-container .operators-container .operators .accuracy-selector {
  width: 65px;
}
.cl-slickgrid-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.cl-slickgrid-container .data-show-container {
  width: 100%;
  flex: 1;
}
.cl-slickgrid-container .data-show-container .heatmap {
  height: 100%;
}
.cl-slickgrid-container .data-show-container .grid-item {
  width: 100%;
  height: 100%;
}
.cl-slickgrid-container .data-show-container .grid-item ::-webkit-scrollbar-button {
  z-index: 200;
  width: 10px;
  height: 10px;
  background: var(--bg-color);
  cursor: pointer;
}
.cl-slickgrid-container .data-show-container .grid-item ::-webkit-scrollbar-button:horizontal:single-button:start {
  background-image: url('../assets/images/scroll-btn-left.png');
  background-position: center;
}
.cl-slickgrid-container .data-show-container .grid-item ::-webkit-scrollbar-button:horizontal:single-button:end {
  background-image: url('../assets/images/scroll-btn-right.png');
  background-position: center;
}
.cl-slickgrid-container .data-show-container .grid-item ::-webkit-scrollbar-button:vertical:single-button:start {
  background-image: url('../assets/images/scroll-btn-up.png');
  background-position: center;
}
.cl-slickgrid-container .data-show-container .grid-item ::-webkit-scrollbar-button:vertical:single-button:end {
  background-image: url('../assets/images/scroll-btn-down.png');
  background-position: center;
}
.cl-slickgrid-container .data-show-container .grid-item ::-webkit-scrollbar-thumb {
  background-color: #bac5cc;
}
.cl-slickgrid-container .data-show-container .grid-item ::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}
.cl-slickgrid-container .data-show-container .error-msg-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.cl-slickgrid-container .info-show-container {
  width: 100%;
}
.cl-slickgrid-container .operate-container {
  width: 100%;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
  z-index: 9;
  flex-wrap: wrap;
}
.cl-slickgrid-container .operate-container .full-screen-icon {
  float: right;
  margin-left: 15px;
  height: 100%;
  line-height: 34px;
  cursor: pointer;
}
.cl-slickgrid-container .operate-container .full-screen-icon :hover {
  color: #00a5a7;
}
.cl-slickgrid-container .operate-container .active-color {
  color: #00a5a7;
}

.slick-cell,
.slick-headerrow-column,
.slick-footerrow-column {
  padding: 0;
  border-top: none;
  border-left: none;
  text-align: center;
}

.ui-widget-content {
  background: none;
  color: var(--grid-table-content-color);
}

.headerStyle {
  vertical-align: middle;
  text-align: center;
}

.filter-check {
  font-size: 18px;
  color: #00a5a7;
  cursor: pointer;
}

.table-item-span {
  display: block;
  width: 100%;
  height: 100%;
  text-align: center;
}
</style>

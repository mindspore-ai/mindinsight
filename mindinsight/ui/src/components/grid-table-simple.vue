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
      <div :id="itemId"
           v-show="!!fullData.length && !incorrectData"
           class="grid-item"></div>
    </div>
    <div class="operate-container"
         v-if="showOperate && (fullData.length || requestError)">
      <div class="filter-container"
           @keyup.enter="filterChange">
        <div class="filter-input-title">{{$t('components.dimsFilterInputTitle')}}
          <span :title="$t('components.dimsFilterInputTip')"
                class="el-icon-info"></span>
        </div>
        <div v-for="(item, itemIndex) in filterArr"
             :key="itemIndex">
          <el-input class="filter-input"
                    :class="[item.showError ? 'error-border' : '', fullScreen ? 'long-input' : 'short-input']"
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
      <div class="accuracy-container">
        {{$t('components.category')}}<el-select v-model="category"
                   class="select-category"
                   @change="accuracyChange">
          <el-option v-for="item in categoryArr"
                     :key="item.label"
                     :label="item.label"
                     :value="item.value"></el-option>
        </el-select>
        {{$t('components.gridAccuracy')}}
        <span :title="$t('components.accuracyTips')"
              class="el-icon-info"></span>
        <el-select v-model="accuracy"
                   class="select-item"
                   @change="accuracyChange">
          <el-option v-for="item in accuracyArr"
                     :key="item.label"
                     :label="item.label"
                     :value="item.value"></el-option>
        </el-select>
        <div class="full-screen-icon"
             :title="$t('scalar.fullScreen')"
             @click="toggleFullScreen"
             :class="fullScreen ? 'active-color' : ''">
          <i class="el-icon-full-screen"></i>
        </div>
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
export default {
  props: {
    // Table data
    fullData: {
      type: Array,
      default() {
        return [];
      },
    },
    // Display operation Bar
    showOperate: {
      type: Boolean,
      default: true,
    },
    // Display full screen
    fullScreen: {
      type: Boolean,
      default: false,
    },
    // Maximum number of columns
    // If the value is less then 0, there is no maximun value.
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
      statistics: {}, // Object contain maximun and minimun
      accuracy: 5, // Accuracy value
      incorrectData: false, // Wheather the dimension is correctly selected
      updated: false, // Updated
      scrollTop: false, // Wheather scroll to the top
      filterCorrect: true, // Wheather the dimension input is correct
      requestError: false, // Exceeded the specification
      errorMsg: '', // Error message
      viewResizeFlag: false, // Size reset flag
      // Accuray options
      accuracyArr: [
        {label: 0, value: 0},
        {label: 1, value: 1},
        {label: 2, value: 2},
        {label: 3, value: 3},
        {label: 4, value: 4},
        {label: 5, value: 5},
      ],
      // Table configuration items
      optionObj: {
        enableColumnReorder: false,
        enableCellNavigation: true,
        frozenColumn: 0,
        frozenRow: 0,
      },
      tableStartIndex: {
        rowStartIndex: 0,
        colStartIndex: 0,
      },
      categoryArr: [
        {
          label: this.$t('components.value'),
          value: 'value',
        },
        {
          label: this.$t('components.scientificCounting'),
          value: 'science',
        },
      ],
      category: 'value', // value: Numerical; science: Scientific notation
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
     * Initialize dimension selection
     * @param {Array} dimension Dimension array
     * @param {String} filterStr Dimension String
     */
    initializeFilterArr(dimension, filterStr) {
      this.filterCorrect = true;
      if (!filterStr) {
        this.filterArr = [];
        return;
      }
      const tempFilterArr = filterStr.slice(1, filterStr.length - 1).split(',');
      const tempArr = [];
      const multiDimsArr = [];
      for (let i = 0; i < tempFilterArr.length; i++) {
        tempArr.push({
          model: tempFilterArr[i],
          max: dimension[i] - 1,
          showError: false,
        });
        if (tempFilterArr[i].indexOf(':') !== -1) {
          const curFilterArr = tempFilterArr[i].split(':');
          if (curFilterArr[0]) {
            let startIndex = Number(curFilterArr[0]);
            startIndex =
              startIndex < 0 ? dimension[i] + startIndex : startIndex;
            multiDimsArr.push(startIndex);
          } else {
            multiDimsArr.push(0);
          }
        }
      }
      this.filterArr = tempArr;
      if (!multiDimsArr.length) {
        this.tableStartIndex = {
          rowStartIndex: 0,
          colStartIndex: 0,
        };
      } else if (multiDimsArr.length >= 2) {
        this.tableStartIndex = {
          rowStartIndex: multiDimsArr[0],
          colStartIndex: multiDimsArr[1],
        };
      } else {
        this.tableStartIndex = {
          rowStartIndex: 0,
          colStartIndex: multiDimsArr[0],
        };
      }
    },
    /**
     * Initialize column information
     */
    formateColumnsData() {
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
          const order = numIndex + this.tableStartIndex.colStartIndex;
          this.columnsData.push({
            id: order,
            name: order,
            field: order,
            width: 120,
            headerCssClass: 'headerStyle',
            formatter: this.formateValueColor,
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
    formateValueColor(row, cell, value, columnDef, dataContext) {
      if (
        !cell ||
        !value ||
        isNaN(value) ||
        value === Infinity ||
        value === -Infinity
      ) {
        return value;
      } else if (value < 0) {
        return `<span class="table-item-span" style="background:rgba(227, 125, 41, ${
          value / this.statistics.overall_min
        })">${value}</span>`;
      } else {
        return `<span class="table-item-span" style="background:rgba(0, 165, 167, ${
          value / this.statistics.overall_max
        })">${value}</span>`;
      }
    },
    /**
     * Convetring raw data into table data
     */
    formateGridArray() {
      if (this.fullData instanceof Array) {
        if (this.fullData.length) {
          if (this.fullData[0] instanceof Array) {
            this.formateData = this.fullData;
          } else {
            this.formateData = [this.fullData];
          }
        } else {
          this.formateData = [[]];
          this.columnsData = [];
        }
      } else {
        this.formateData = [[this.fullData]];
      }
      const tempArr = [];
      this.formateData.forEach((outerData, outerIndex) => {
        const tempData = {
          '-1': outerIndex + this.tableStartIndex.rowStartIndex,
        };
        outerData.forEach((innerData, innerIndex) => {
          const innerOrder = innerIndex + this.tableStartIndex.colStartIndex;
          if (isNaN(innerData)) {
            tempData[innerOrder] = innerData;
          } else {
            if (this.category === this.categoryArr[0].value) {
              tempData[innerOrder] = innerData.toFixed(this.accuracy);
            } else {
              tempData[innerOrder] = innerData.toExponential(this.accuracy);
            }
          }
        });
        tempArr.push(tempData);
      });
      this.formateArr = tempArr;
    },
    /**
     * Update the table
     */
    updateGrid() {
      this.$nextTick(() => {
        if (!this.gridObj) {
          this.gridObj = new Slick.Grid(
              `#${this.itemId}`,
              this.formateArr,
              this.columnsData,
              this.optionObj,
          );
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
     */
    accuracyChange() {
      this.formateGridArray();
      if (!this.requestError && !this.incorrectData) {
        this.updateGrid();
      }
    },
    /**
     * Dimension selection changed
     */
    filterChange() {
      // 校验检索条件
      let filterCorrect = true;
      let incorrectData = false;
      let limitCount = 2;
      const indexArr = [];
      const tempArr = [];
      this.filterArr.forEach((filter, index) => {
        let value = filter.model.trim();
        if (!isNaN(value)) {
          if (
            value < -(filter.max + 1) ||
            value > filter.max ||
            value === '' ||
            value % 1
          ) {
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
        if (
          this.columnLimitNum > 0 &&
          filterItem &&
          !filterItem.showError &&
          filterItem.max >= this.columnLimitNum
        ) {
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
      if ((endValue - startValue) > this.columnLimitNum) {
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
      if (
        !!startValue &&
        (isNaN(startValue) ||
          startValue < -(filter + 1) ||
          startValue > filter.max)
      ) {
        return false;
      }
      if (
        !!endValue &&
        (isNaN(endValue) ||
          endValue <= -(filter.max + 1) ||
          endValue > (filter.max + 1) ||
          !Number(endValue))
      ) {
        return false;
      }
      if (tempArr.length > limitCount) {
        return false;
      } else if (!startValue && !endValue) {
        return true;
      } else if (!!startValue && !!endValue) {
        const sv =
          startValue < 0
            ? filter.max + Number(startValue) + 1
            : Number(startValue);
        const ev =
          endValue < 0 ? filter.max + Number(endValue) + 1 : Number(endValue);
        if (ev <= sv) {
          return false;
        } else {
          return true;
        }
      } else {
        return true;
      }
    },
    /**
     * Updating Table Data
     * @param {Boolean} newDataFlag Wheather data is updated
     * @param {Array} dimension Array of dimension
     * @param {Object} statistics Object contains maximun and minimun
     * @param {String} filterStr String of dimension selection
     */
    updateGridData(newDataFlag, dimension, statistics, filterStr) {
      this.updated = true;
      this.requestError = false;
      this.$nextTick(() => {
        if (!this.fullData || !this.fullData.length) {
          return;
        }
        if (newDataFlag) {
          this.initializeFilterArr(dimension, filterStr);
          this.scrollTop = true;
        }
        if (newDataFlag || this.statistics.overall_max === undefined) {
          this.statistics = statistics;
        }
        this.formateGridArray();
        this.formateColumnsData();
        if (!this.incorrectData) {
          this.updateGrid();
        }
      });
    },
    /**
     * Update the view Size
     */
    resizeView() {
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
     */
    showRequestErrorMessage(errorMsg, dimension, filterStr) {
      this.errorMsg = errorMsg;
      if (!this.filterArr.length && dimension && filterStr) {
        this.initializeFilterArr(dimension, filterStr);
      }
      this.requestError = true;
    },
  },
  destroyed() {},
};
</script>
<style>
.cl-slickgrid-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.cl-slickgrid-container .data-show-container {
  width: 100%;
  flex: 1;
}
.cl-slickgrid-container .data-show-container .grid-item {
  width: 100%;
  height: 100%;
}
.cl-slickgrid-container .data-show-container .grid-item ::-webkit-scrollbar-button {
  z-index: 200;
  width: 10px;
  height: 10px;
  background: #fff;
  cursor: pointer;
}
.cl-slickgrid-container .data-show-container .grid-item ::-webkit-scrollbar-button:horizontal:single-button:start {
  background-image: url("../assets/images/scroll-btn-left.png");
  background-position: center;
}
.cl-slickgrid-container .data-show-container .grid-item ::-webkit-scrollbar-button:horizontal:single-button:end {
  background-image: url("../assets/images/scroll-btn-right.png");
  background-position: center;
}
.cl-slickgrid-container .data-show-container .grid-item ::-webkit-scrollbar-button:vertical:single-button:start {
  background-image: url("../assets/images/scroll-btn-up.png");
  background-position: center;
}
.cl-slickgrid-container .data-show-container .grid-item ::-webkit-scrollbar-button:vertical:single-button:end {
  background-image: url("../assets/images/scroll-btn-down.png");
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
  z-index: 99;
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
.cl-slickgrid-container .operate-container .filter-container {
  float: left;
  flex-wrap: wrap;
  display: flex;
}
.cl-slickgrid-container .operate-container .filter-container .error-border input {
  border-color: red;
}
.cl-slickgrid-container .operate-container .filter-container .filter-input {
  text-align: center;
}
.cl-slickgrid-container .operate-container .filter-container .short-input {
  width: 50px;
}
.cl-slickgrid-container .operate-container .filter-container .long-input {
  width: 120px;
}
.cl-slickgrid-container .operate-container .filter-container .input-behind {
  padding: 0 5px;
}
.cl-slickgrid-container .operate-container .filter-container .filter-incorrect-text {
  margin-left: 10px;
  line-height: 32px;
  color: red;
}
.cl-slickgrid-container .operate-container .filter-container .filter-input-title {
  line-height: 34px;
  margin-right: 10px;
}
.cl-slickgrid-container .operate-container .accuracy-container {
  float: right;
}
.cl-slickgrid-container .operate-container .accuracy-container .select-item {
  width: 60px;
}
.cl-slickgrid-container .operate-container .accuracy-container .select-category {
  width: 105px;
  margin-left: 5px;
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

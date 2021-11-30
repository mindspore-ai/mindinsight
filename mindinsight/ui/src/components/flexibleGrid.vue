<!--
Copyright 2021 Huawei Technologies Co., Ltd.All Rights Reserved.

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
  <div class="mi-flex-grid"
       id="mi-flex-grid"
       ref="grid"
       :style="gridStyle"
       @mousemove="handleMouseMove"
       @mouseleave="handleMouseLeave"
       @mouseup="handleMouseUp">
    <div v-for="(area, index) in areaList"
         :key="area.name"
         :class="[(gapAreas['columnGap'].includes(area.name)
           || gapAreas['rowGap'].includes(area.name)) ? 'grid-item-gap' : 'grid-item']"
         :style="{gridArea: area.name}"
         @mousedown="stopPropagation">
      <slot :name="area.name"></slot>
      <div v-if="gapAreas['columnGap'].includes(area.name)"
           class="grid-columnGap"
           @mousedown="handleMouseDown"></div>
      <div v-if="gapAreas['rowGap'].includes(area.name)"
           class="grid-rowGap"
           @mousedown="handleMouseDown"></div>
      <div v-if="index > 0 && areaList[index - 1].hide"
           :class="[
             'hide-button',
             `is-${areaList[index - 1].hide}`,
           ]">
        <img @click="isDisplayView(areaList[index - 1].name)"
             :src="require(`@/assets/images/${theme}/collapse-${areaList[index - 1].isHide ? 'right' : 'left'}.svg`)">
      </div>
      <div v-if="index === areaList.length - 2 && areaList[index + 1].hide"
           :class="[
             'hide-button',
             `is-${areaList[index + 1].hide}`,
           ]">
        <img @click="isDisplayView(areaList[index + 1].name)"
             :src="require(`@/assets/images/${theme}/collapse-${areaList[index + 1].isHide ? 'right' : 'left'}.svg`)">
      </div>
    </div>
    <div class="mi-flex-grid-preview"
         :style="previewStyle"
         v-show="showPreview">
      <div v-for="area in areaList"
           :key="area.name"
           :style="{gridArea: area.name}"
           class="grid-preview-item">
        <div v-if="gapAreas['columnGap'].includes(area.name)"
             class="grid-columnGap"></div>
        <div v-if="gapAreas['rowGap'].includes(area.name)"
             class="grid-rowGap"></div>
      </div>
    </div>
  </div>
</template>
<script>
/**
 * Class of grid layout style
 */
class GridStyle {
  gridTemplateAreas;
  gridTemplateRows;
  gridTemplateColumns;
  /**
   * Constructor
   */
  constructor() {
    this.gridTemplateAreas = '';
    this.gridTemplateRows = '';
    this.gridTemplateColumns = '';
  }
}

/**
 * Class of grid layout structure
 */
class GridStructure {
  count = 0;
  px = 0;
  fr = 0;
}

export default {
  props: {
    areas: Array, // [['name1', 'name2', 'name2'], ['name1', 'name3', 'name4']] as css rule 'grid-areas' in array
    rowSize: Array, // Such as Array<Row>
    columnSize: Array, // Such as Array<Column>
    hideAreas: Object, // Configuration item area hidden
    showFixed: Boolean, // Whether to display a fixed area
    gridStyleKey: String, // Display different page grid styles according to the key
  },
  data() {
    return {
      theme: this.$store.state.themeIndex, // Multi-theme style
      previewStyle: new GridStyle(), // Mask layer style
      gridStyle: new GridStyle(), // Gird layout style
      areaList: [], // An array of pages divided into regions
      areaMap: {}, // Object of area map
      rowStructure: null, // Row layout structure
      rowFR: 0, // Height occupied by one fr
      rows: [], //  Array of rows
      rowGaps: [], // Array of row gaps
      rowGap: '16px', // The size of row gap
      columnGap: '16px', // The size of column gap
      differIndex: 2, // Index of the difference between adjacent rows or columns
      resizeDelayTime: 200, // The delay of resize's event
      columnStructure: null, // Column layout structure
      columnFR: 0, // Width occupied by one fr
      columns: [], // Array of columns
      columnGaps: [], // Array of column gaps
      showPreview: false, // Whether to show the mask layer
      width: '', // The total width of the page
      viewResizeTimer: null, // Page resize time
      callBackTimer: null, // Slickgrid layout resize time
      gapAreas: {
        columnGap: [],
        rowGap: [],
      }, // Gap areas object
      saveGridStyleObj: [
        {
          key: 'debugger',
          value: null,
        },
        {
          key: 'debugger-tensor',
          value: null,
        },
        {
          key: 'debugger-tensor-inner',
          value: null,
        },
        {
          key: 'offline-debugger',
          value: null,
        },
        {
          key: 'offline-debugger-tensor',
          value: null,
        },
        {
          key: 'offline-debugger-tensor-inner',
          value: null,
        },
        {
          key: 'step-trace',
          value: null,
        },
        {
          key: 'profiling-gpu',
          value: null,
        },
        {
          key: 'model-traceback',
          value: null,
        },
        {
          key: 'graph',
          value: null,
        },
      ], // Save an array of grid styles for different pages
    };
  },
  watch: {
    // Shrink button style of the listening columns
    columns: {
      handler(newValue) {
        newValue.forEach((value) => {
          if (['left', 'right'].includes(value.hide)) {
            value.isHide = !Boolean(value.currentWidth);
            this.areaList.find((area) => area.hide === value.hide).isHide = value.isHide;
          }
        });
      },
      deep: true,
    },
    // Shrink button style of the listening rows
    rows: {
      handler(newValue) {
        const { differIndex, areaList } = this;
        const rowCount = 1; // The page is laid out in one line
        if (newValue.length === rowCount) return;
        const hideAreasIndex = newValue.findIndex((item) => {
          return Object.keys(this.hideAreas).includes(item.name);
        });
        if (!newValue[hideAreasIndex]['currentHeight']) {
          newValue[hideAreasIndex + differIndex]['hide'] = '';
          newValue[hideAreasIndex]['hide'] = 'top-center';
          newValue[hideAreasIndex]['isHide'] = true;
        } else {
          newValue[hideAreasIndex + differIndex]['hide'] = 'bottom';
          newValue[hideAreasIndex]['isHide'] = false;
        }
        if (!newValue[hideAreasIndex + differIndex]['currentHeight']) {
          newValue[hideAreasIndex]['hide'] = '';
          newValue[hideAreasIndex + differIndex]['hide'] = 'bottom-center';
          newValue[hideAreasIndex + differIndex]['isHide'] = true;
        } else {
          newValue[hideAreasIndex]['hide'] = 'top';
          newValue[hideAreasIndex + differIndex]['isHide'] = false;
        }
        areaList.forEach((area) => {
          if (newValue[hideAreasIndex].name === area.name) {
            area.hide = newValue[hideAreasIndex].hide;
            area.isHide = newValue[hideAreasIndex].isHide;
          }
          if (newValue[hideAreasIndex + differIndex].name === area.name) {
            area.hide = newValue[hideAreasIndex + differIndex].hide;
            area.isHide = newValue[hideAreasIndex + differIndex].isHide;
          }
        });
      },
      deep: true,
    },
  },
  created() {
    this.calGapAreas();
    this.parseGridInfo();
  },
  mounted() {
    this.calFRValue();
    this.calTriggerPosition();
    this.updatePreviewStyle();
    // Window resize to add a listener
    window.addEventListener('resize', this.resizeGridStyle, false);
  },
  destroyed() {
    // remove the size of a window and change the listener
    window.removeEventListener('resize', this.resizeGridStyle);
    // Remove View Calculation Delay
    if (this.viewResizeTimer) {
      clearTimeout(this.viewResizeTimer);
      this.viewResizeTimer = null;
    }
    if (this.callBackTimer) {
      clearTimeout(this.callBackTimer);
      this.callBackTimer = null;
    }
  },
  methods: {
    /**
     * Resize the page layout according to the window
     */
    resizeGridStyle() {
      this.viewResizeTimer = setTimeout(() => {
        this.getSaveGridStyle();
        this.calFRValue();
        this.calTriggerPosition();
        this.updatePreviewStyle(false);
      }, this.resizeDelayTime);
    },
    /**
     * Show or hide a certain area view
     * @param {String} areaName
     * @param {Boolean} storageFlag
     */
    isDisplayView(areaName, storageFlag = true) {
      const { columns, rows, differIndex, gridStyleKey, areaList } = this;
      columns.forEach((column, index) => {
        if (column.name === areaName && column.hide === 'left') {
          if (!column.isHide) {
            if (storageFlag) localStorage.setItem(`${gridStyleKey}${column.name}Width`, column.currentWidth);
            columns[index + differIndex].currentWidth += column.currentWidth;
            columns[index].currentWidth = 0;
          } else {
            const offsetWidth = +localStorage.getItem(`${gridStyleKey}${column.name}Width`);
            columns[index + differIndex].currentWidth -= offsetWidth;
            columns[index].currentWidth = offsetWidth;
          }
          column.isHide = !column.isHide;
        }
        if (column.name === areaName && column.hide === 'right') {
          if (!column.isHide) {
            if (storageFlag) localStorage.setItem(`${gridStyleKey}${column.name}Width`, column.currentWidth);
            columns[index - differIndex].currentWidth += column.currentWidth;
            columns[index].currentWidth = 0;
          } else {
            const offsetWidth = +localStorage.getItem(`${gridStyleKey}${column.name}Width`);
            columns[index - differIndex].currentWidth -= offsetWidth;
            columns[index].currentWidth = offsetWidth;
          }
          column.isHide = !column.isHide;
        }
      });
      rows.forEach((row, index) => {
        if (row.name === areaName && /top/.test(row.hide)) {
          if (!row.isHide) {
            if (storageFlag) localStorage.setItem(`${gridStyleKey}${row.name}Height`, row.currentHeight);
            rows[index + differIndex].currentHeight += row.currentHeight;
            rows[index].currentHeight = 0;
          } else {
            const offsetHeight = +localStorage.getItem(`${gridStyleKey}${row.name}Height`);
            rows[index + differIndex].currentHeight -= offsetHeight;
            rows[index].currentHeight = offsetHeight;
          }
          row.isHide = !row.isHide;
        }
        if (row.name === areaName && /bottom/.test(row.hide)) {
          if (!row.isHide) {
            if (storageFlag) localStorage.setItem(`${gridStyleKey}${row.name}Height`, row.currentHeight);
            rows[index - differIndex].currentHeight += row.currentHeight;
            rows[index].currentHeight = 0;
          } else {
            const offsetHeight = +localStorage.getItem(`${gridStyleKey}${row.name}Height`);
            rows[index - differIndex].currentHeight -= offsetHeight;
            rows[index].currentHeight = offsetHeight;
          }
          row.isHide = !row.isHide;
        }
      });
      areaList.filter((area) => {
        area.isHide = area.name === areaName ? !area.isHide : area.isHide;
      });
      this.updatePreviewStyle();
      if (storageFlag) this.updateGridStyle(false, true);
    },
    /**
     * Calculate the location of all page gaps
     */
    calTriggerPosition() {
      const { rows, rowGaps, columns, columnGaps, differIndex } = this;
      const factor = 1; // Used to determine the location of the gap
      let rowPoint = 0; // Used to calculate the position of the row gap
      let rowGapNum = 0; // To count the number of row gaps
      for (let i = 0; i < rows.length - 1; i++) {
        rowPoint += rows[i].currentHeight;
        if (i % differIndex === factor) {
          rowGaps[rowGapNum] = {
            start: rowPoint - rows[i].currentHeight,
            end: rowPoint,
          };
          rowGapNum++;
        }
      }
      let columnPoint = 0; // Used to calculate the position of the column gap
      let columnGapNum = 0; // To count the number of column gaps
      for (let i = 0; i < columns.length - 1; i++) {
        columnPoint += columns[i].currentWidth;
        if (i % differIndex === factor) {
          columnGaps[columnGapNum] = {
            start: columnPoint - columns[i].currentWidth,
            end: columnPoint,
          };
          columnGapNum++;
        }
      }
    },
    /**
     * Calculate fr as the page value size
     */
    calFRValue() {
      const { rowStructure, columnStructure, rows, columns, gridStyleKey } = this;
      const { width, height } = this.$refs.grid.getBoundingClientRect();
      const ratio = 2; // Set the maximum width of the page to half of the screen
      this.width = width;
      // Column
      this.columnFR = (width - columnStructure.px) / columnStructure.fr;
      // Row
      this.rowFR = (height - rowStructure.px) / rowStructure.fr;
      rows.forEach((row) => {
        const currentHeight = row.currentHeight;
        const value = parseInt(currentHeight);
        if (currentHeight.includes('fr')) {
          row.currentHeight = value * this.rowFR;
        } else {
          row.currentHeight = value;
        }
      });
      columns.forEach((column) => {
        const currentWidth = column.currentWidth;
        const value = parseInt(currentWidth);
        if (currentWidth.includes('fr')) {
          column.currentWidth = value * this.columnFR;
        } else {
          column.currentWidth = value;
        }
        if (
          column.hasOwnProperty('maxWidth') &&
          ['debugger-tensor', 'offline-debugger-tensor', 'debugger', 'offline-debugger'].includes(gridStyleKey)
        ) {
          column.maxWidth = width / ratio;
        }
      });
    },
    /**
     * Convert page value to fr
     * @param {String} gridTemplate
     * @param {String} type
     * @return {String}
     */
    calValueToFR(gridTemplate, type) {
      if (/fr/.test(gridTemplate)) return gridTemplate;
      const gridTemplateArray = gridTemplate.split(' ');
      const structure = new GridStructure();
      for (let i = 0; i < gridTemplateArray.length; i++) {
        // 0px: The template style in the grid layout
        if (['0px', this.rowGap, this.columnGap].includes(gridTemplateArray[i])) {
          this.handleGridSize(gridTemplateArray[i], structure);
          continue;
        }
        gridTemplateArray[i] = gridTemplateArray[i].replace(/px/, 'fr');
        this.handleGridSize(gridTemplateArray[i], structure);
      }
      if (type === 'column') this.columnStructure = structure;
      if (type === 'row') this.rowStructure = structure;
      return gridTemplateArray.join(' ');
    },
    /**
     * Update mask layer style
     */
    updatePreviewStyle(resizeFlag = true) {
      const { previewStyle, rows, columns } = this;
      previewStyle.gridTemplateRows = rows.map((r) => r.currentHeight + 'px').join(' ');
      previewStyle.gridTemplateColumns = columns.map((r) => r.currentWidth + 'px').join(' ');
      if (resizeFlag) {
        const resizeObj = {};
        this.areaList.forEach((area) => {
          if (!this.gapAreas.columnGap.includes(area.name) && !this.gapAreas.rowGap.includes(area.name)) {
            resizeObj[area.name] = { isHide: area.isHide };
          }
        });
        this.$nextTick(() => {
          this.$emit('resizeGridStyle', resizeObj);
        });
      }
    },
    /**
     * Initialize dimension selection
     * @param {Boolean} first Load for the first time
     * @param {Boolean} click Make a shrink button click
     */
    updateGridStyle(first = false, click = false) {
      const { gridStyle, previewStyle, columns, rows, gridStyleKey, saveGridStyleObj } = this;
      if (!first && !click) {
        // When dragging the page, it is automatically hidden if it is less than the minimum width or height
        columns.forEach((column) => {
          if (['left', 'right'].includes(column.hide)) {
            if (column.currentWidth < parseInt(column.minWidth) && !column.isHide) {
              localStorage.setItem(`${gridStyleKey}${column.name}Width`, parseInt(column.minWidth));
              this.isDisplayView(column.name, column.isHide);
            }
          }
        });
        rows.forEach((row) => {
          if (['top', 'bottom'].includes(row.hide)) {
            if (row.currentHeight < parseInt(row.minHeight) && !row.isHide) {
              localStorage.setItem(`${gridStyleKey}${row.name}Height`, parseInt(row.minHeight));
              this.isDisplayView(row.name, row.isHide);
            }
          }
        });
      }
      if (first) {
        gridStyle.gridTemplateAreas = previewStyle.gridTemplateAreas;
      }
      gridStyle.gridTemplateRows = previewStyle.gridTemplateRows;
      gridStyle.gridTemplateColumns = previewStyle.gridTemplateColumns;
      // Store the grid layout style of the page in localstorage
      if (localStorage.saveGridStyle) {
        const saveGridStyle = JSON.parse(localStorage.saveGridStyle);
        saveGridStyle.find((item) => item.key === gridStyleKey).value = gridStyle;
        localStorage.setItem('saveGridStyle', JSON.stringify(saveGridStyle));
      } else {
        saveGridStyleObj.find((item) => item.key === gridStyleKey).value = gridStyle;
        localStorage.setItem('saveGridStyle', JSON.stringify(saveGridStyleObj));
      }
      // Resize the layout of slickgrid in debugger-tensor and offline-debugger-tensor pages
      if (['debugger-tensor', 'offline-debugger-tensor'].includes(gridStyleKey) && !first) {
        this.callBackTimer = setTimeout(() => {
          this.$emit('resizeCallback');
        }, this.resizeDelayTime);
      }
      this.calTriggerPosition();
    },
    /**
     * Save grid styles of different pages
     */
    getSaveGridStyle() {
      const { gridStyle, gridStyleKey } = this;
      let gridStyleData = '';
      gridStyleData = JSON.parse(localStorage.saveGridStyle).find((item) => item.key === gridStyleKey).value;
      const { gridTemplateAreas, gridTemplateColumns, gridTemplateRows } = gridStyleData;
      gridStyle.gridTemplateAreas = gridTemplateAreas;
      gridStyle.gridTemplateColumns = this.calValueToFR(gridTemplateColumns, 'column');
      gridStyle.gridTemplateRows = this.calValueToFR(gridTemplateRows, 'row');
      const gridTemplateColumnsArray = gridStyle.gridTemplateColumns.split(' ');
      const gridTemplateRowsArray = gridStyle.gridTemplateRows.split(' ');
      // According to changing column and row, columnsize configuration items, recalculate the page layout
      this.columns.forEach((column, index) => {
        if (/px/.test(gridTemplateColumnsArray[index])) {
          column.currentWidth = gridTemplateColumnsArray[index].replace(/px/, '');
        } else {
          column.currentWidth = gridTemplateColumnsArray[index];
        }
      });
      this.rows.forEach((row, index) => {
        if (/px/.test(gridTemplateRowsArray[index])) {
          row.currentHeight = gridTemplateRowsArray[index].replace(/px/, '');
        } else {
          row.currentHeight = gridTemplateRowsArray[index];
        }
      });
    },
    /**
     * Calculate the gap area
     */
    calGapAreas() {
      const { areas, differIndex, gapAreas, rowSize, columnSize, rowGap, columnGap, showFixed } = this;
      const factor = 1; // Used to determine where to add
      let columnGapNum = 1; // Used to define the column gap name
      let areaIndex = 1; // Add the position of the column gap
      let columnIndex = 1; // Add the same column gap to the same column
      let rowGapNum = 1; // Used to Define the row gap name
      let areaArray = []; // Array of area or gap
      let rowSizeIndex = 1; // Add the position of the row gap size
      let columnSizeIndex = 1; // Add the position of the column gap size
      // Add column gap
      areas.forEach((area) => {
        area.forEach((item, index) => {
          if (index >= factor && index !== columnIndex) {
            columnIndex = index;
            areaIndex += differIndex;
            columnGapNum++;
          }
          if (index >= factor && index === columnIndex) {
            area.splice(areaIndex, 0, `columnGap${columnGapNum}`);
            if (!gapAreas['columnGap'].includes(`columnGap${columnGapNum}`)) {
              gapAreas['columnGap'].push(`columnGap${columnGapNum}`);
            }
          }
        });
        areaIndex = 1;
        columnIndex = 1;
        columnGapNum = 1;
      });
      // Add row gap
      for (let i = 0; i < areas.length; i++) {
        if (i % differIndex === factor) {
          for (let j = 0; j < areas[i].length; j++) {
            if (areas[i - factor][j] === areas[i][j]) {
              areaArray.push(areas[i][j]);
            } else {
              areaArray.push(`rowGap${rowGapNum}`);
              if (!gapAreas['rowGap'].includes(`rowGap${rowGapNum}`)) {
                gapAreas['rowGap'].push(`rowGap${rowGapNum}`);
              }
            }
          }
          areas.splice(i, 0, areaArray);
          rowGapNum++;
          areaArray = [];
        }
      }
      // Add row gap size
      rowSize.forEach((item, index) => {
        if (index >= factor) {
          if (index === factor && showFixed) {
            rowSize.splice(rowSizeIndex, 0, '0px');
          } else {
            rowSize.splice(rowSizeIndex, 0, rowGap);
          }
          rowSizeIndex += differIndex;
        }
      });
      // Add column gap size
      columnSize.forEach((item, index) => {
        if (index >= factor) {
          columnSize.splice(columnSizeIndex, 0, columnGap);
          columnSizeIndex += differIndex;
        }
      });
    },
    /**
     * Initialize grid layout style
     */
    parseGridInfo() {
      const { areas, rowSize, columnSize, areaMap, previewStyle, hideAreas } = this;
      const rowDescription = this.generateGridDescription(rowSize, 'row');
      this.rows = rowDescription.info;
      this.rowStructure = rowDescription.structure;
      const columnDescription = this.generateGridDescription(columnSize, 'column');
      this.columns = columnDescription.info;
      this.columnStructure = columnDescription.structure;
      const areaName = [];
      areas.forEach((row, rowIndex) => {
        const rowAreaName = [];
        row.forEach((areaName, columnIndex) => {
          rowAreaName.push(areaName);
          if (!areaMap.hasOwnProperty(areaName)) {
            // First meet, add map item
            areaMap[areaName] = {
              name: areaName,
              rowIndex: [rowIndex],
              columnIndex: [columnIndex],
              hide: hideAreas[areaName],
              isHide: false,
            };
          }
          const areaInfo = areaMap[areaName];
          if (!areaInfo.rowIndex.includes(rowIndex)) {
            areaInfo.rowIndex.push(rowIndex);
          }
          if (!areaInfo.columnIndex.includes(columnIndex)) {
            areaInfo.columnIndex.push(columnIndex);
          }
        });
        areaName.push(`"${rowAreaName.join(' ')}"`);
      });
      this.areaList = Object.values(areaMap);
      // Reconstruct the row and column arrays
      const columnAreas = [];
      let rowAreas = [];
      for (let i = 0; i < this.areaList.length; i++) {
        for (let j = 0; j < this.areaList[i]['columnIndex'].length; j++) {
          if (this.areaList[i]['columnIndex'].includes(i)) {
            columnAreas.push(this.areaList[i]);
            break;
          }
        }
      }
      const startIndex = this.areaList.indexOf(columnAreas[columnAreas.length - 1]);
      rowAreas = this.areaList.slice(startIndex, this.areaList.length);
      this.columns.forEach((item, index) => {
        Object.assign(this.columns[index], columnAreas[index]);
      });
      this.rows.forEach((item, index) => {
        if (index !== this.rows.length) {
          Object.assign(this.rows[index], rowAreas[index]);
        }
      });
      // Update previewStyle
      previewStyle.gridTemplateAreas = areaName.join(' ');
      previewStyle.gridTemplateRows = rowDescription.template;
      previewStyle.gridTemplateColumns = columnDescription.template;
      // Determine whether there is a saved page layout in localstroage
      if (
        localStorage.saveGridStyle &&
        JSON.parse(localStorage.saveGridStyle).find((item) => item.key === this.gridStyleKey).value
      ) {
        this.getSaveGridStyle();
      } else {
        this.updateGridStyle(true);
      }
    },
    /**
     * Construct an array of row and column
     * @param {Array<string | Row | Column>} array
     * @param {String} type
     * @return {Object}
     */
    generateGridDescription(array, type) {
      const structure = new GridStructure();
      const templateList = [];
      const infoList = [];
      if (type === 'row') {
        // Row
        array.forEach((item) => {
          if (typeof item === 'string') {
            templateList.push(this.handleGridSize(item, structure));
            infoList.push({
              defaultHeight: item,
              currentHeight: item,
              minHeight: 0,
            });
          } else {
            if (typeof item === 'object' && item.hasOwnProperty('defaultHeight')) {
              const defaultHeight = item.defaultHeight;
              templateList.push(this.handleGridSize(defaultHeight, structure));
              infoList.push({
                defaultHeight,
                currentHeight: defaultHeight,
                minHeight: item.minHeight,
                maxHeight: item.maxHeight,
              });
            }
          }
        });
      } else {
        // Column
        array.forEach((item) => {
          if (typeof item === 'string') {
            templateList.push(this.handleGridSize(item, structure));
            infoList.push({
              defaultWidth: item,
              currentWidth: item,
              minWidth: 0,
            });
          } else {
            if (item.hasOwnProperty('defaultWidth')) {
              const defaultWidth = item.defaultWidth;
              templateList.push(this.handleGridSize(defaultWidth, structure));
              infoList.push({
                defaultWidth,
                currentWidth: defaultWidth,
                minWidth: item.minWidth,
                maxWidth: item.maxWidth,
              });
            }
          }
        });
      }
      return {
        info: infoList,
        structure,
        template: templateList.join(' '),
      };
    },
    /**
     * Calculate the structure of the ranks
     * @param {String} str
     * @param {Object} structure
     * @return {String} The size of each area
     */
    handleGridSize(str, structure) {
      const num = parseInt(str);
      if (Number.isNaN(num)) return; // Wrong size info
      if (str.includes('px')) {
        structure.count++;
        structure.px += num;
      } else if (str.includes('fr')) {
        structure.count++;
        structure.fr += num;
      } else {
        // Wrong size info
        return;
      }
      return str;
    },
    /**
     * Mouse down event when dragging the page
     * @param {Object} event
     */
    handleMouseDown(event) {
      this.showPreview = true;
      const { rowGaps, columnGaps, differIndex } = this;
      let { offsetX, offsetY } = event;
      let rowGapIndex;
      for (let i = 0; i < rowGaps.length; i++) {
        const { start, end } = rowGaps[i];
        if (start <= offsetY + start && offsetY + start <= end) {
          rowGapIndex = differIndex * i;
          break;
        }
      }
      let columnGapIndex;
      for (let i = 0; i < columnGaps.length; i++) {
        const { start, end } = columnGaps[i];
        if (start <= offsetX + start && offsetX + start <= end) {
          columnGapIndex = differIndex * i;
          break;
        }
      }
      if (typeof rowGapIndex === 'number') {
        // Drag row
        this.dragRow = rowGapIndex;
        offsetY += rowGaps[this.dragRow / differIndex]['start'];
      }
      if (typeof columnGapIndex === 'number') {
        // Drag column
        this.dragColumn = columnGapIndex;
        offsetX += columnGaps[this.dragColumn / differIndex]['start'];
      }
      this.mouseEvent = { offsetX, offsetY };
    },
    /**
     * Mouse move event when dragging the page
     * @param {Object} event
     */
    handleMouseMove(event) {
      const { differIndex, columns, areaList, rows, width, columnGap } = this;
      const dragColumn = typeof this.dragColumn === 'number';
      const dragRow = typeof this.dragRow === 'number';
      if (!dragColumn && !dragRow) return;
      const { pageX, pageY } = event;
      const { top, left } = this.$refs.grid.getBoundingClientRect();
      const offsetX = pageX - left;
      const offsetY = pageY - top;
      if (dragColumn) {
        const columnLeftIndex = this.dragColumn;
        const columnRightIndex = this.dragColumn + differIndex;
        const offset = offsetX - this.mouseEvent.offsetX;
        // When dragging the page, it cannot be larger than the maximum width
        if (columns[columnLeftIndex].hide === 'left') {
          columns[columnLeftIndex].currentWidth += offset;
          if (parseInt(columns[columnLeftIndex].currentWidth) >= parseInt(columns[columnLeftIndex]['maxWidth'])) {
            areaList[columnLeftIndex]['isHide'] = false;
            columns[columnLeftIndex]['isHide'] = false;
            columns[columnLeftIndex].currentWidth = parseInt(columns[columnLeftIndex]['maxWidth']);
            columns[columnRightIndex].currentWidth =
              width - parseInt(columnGap) - parseInt(columns[columnLeftIndex]['maxWidth']);
          } else {
            columns[columnRightIndex].currentWidth -= offset;
          }
        }
        if (columns[columnRightIndex].hide === 'right') {
          columns[columnRightIndex].currentWidth -= offset;
          if (parseInt(columns[columnRightIndex].currentWidth) >= parseInt(columns[columnRightIndex]['maxWidth'])) {
            areaList[columnRightIndex]['isHide'] = false;
            columns[columnRightIndex]['isHide'] = false;
            columns[columnRightIndex].currentWidth = parseInt(columns[columnRightIndex]['maxWidth']);
            columns[columnLeftIndex].currentWidth =
              width - parseInt(columnGap) - parseInt(columns[columnRightIndex]['maxWidth']);
          } else {
            columns[columnLeftIndex].currentWidth += offset;
          }
        }
      }
      if (dragRow) {
        const rowTopIndex = this.dragRow;
        const rowBottomIndex = this.dragRow + differIndex;
        const offset = offsetY - this.mouseEvent.offsetY;
        rows[rowTopIndex].currentHeight += offset;
        rows[rowBottomIndex].currentHeight -= offset;
      }
      this.mouseEvent = { offsetX, offsetY };
      this.updatePreviewStyle();
    },
    /**
     * Mouse move leave when dragging the page
     */
    handleMouseLeave() {
      if (!this.showPreview) return;
      this.acceptChange();
    },
    /**
     * Mouse up event when dragging the page
     */
    handleMouseUp() {
      if (!this.showPreview) return;
      this.acceptChange();
    },
    /**
     * When the page is dragged and dropped, the page changes
     */
    acceptChange() {
      this.updateGridStyle();
      this.showPreview = false;
      this.dragRow = null;
      this.dragColumn = null;
      this.mouseEvent = null;
    },
    /**
     * Prevent further propagation of mouse down events in the capture and bubbling phase
     * @param {Object} event
     */
    stopPropagation(event) {
      event.stopPropagation();
    },
  },
};
</script>

<style scoped>
.mi-flex-grid {
  display: grid;
  width: 100%;
  height: 100%;
  position: relative;
  -moz-user-select: none;
  -khtml-user-select: none;
  user-select: none;
}
.mi-flex-grid .grid-item {
  position: relative;
  z-index: 3;
  overflow: hidden;
}
.mi-flex-grid .grid-item-gap {
  position: relative;
  z-index: 1;
}
.mi-flex-grid .grid-item-gap .grid-columnGap {
  width: 100%;
  height: 100%;
  cursor: col-resize;
}
.mi-flex-grid .grid-item-gap .grid-rowGap {
  width: 100%;
  height: 100%;
  cursor: row-resize;
}
.mi-flex-grid .grid-item-gap .hide-button {
  position: absolute;
  cursor: pointer;
}
.mi-flex-grid .grid-item-gap .is-right {
  top: 50%;
  left: 0;
  transform: translateX(-7px) translateY(-50%) rotate(-180deg);
}
.mi-flex-grid .grid-item-gap .is-top {
  bottom: 0;
  right: 50%;
  transform: translateX(-30px) translateY(41px) rotate(90deg);
}
.mi-flex-grid .grid-item-gap .is-bottom {
  top: 0;
  left: 50%;
  transform: translateX(40%) translateY(-41px) rotate(-90deg);
}
.mi-flex-grid .grid-item-gap .is-left {
  top: 50%;
  right: 0;
  transform: translateX(6px) translateY(-50%);
}
.mi-flex-grid .grid-item-gap .is-bottom-center {
  top: 0;
  left: 50%;
  transform: translateX(-50%) translateY(-42px) rotate(-90deg);
}
.mi-flex-grid .grid-item-gap .is-top-center {
  bottom: 0;
  right: 50%;
  transform: translateX(13px) translateY(57px) rotate(90deg);
}
.mi-flex-grid .grid-item-gap .is-show-0 {
  background-image: url('../assets/images/0/collapse-left.svg');
}
.mi-flex-grid .grid-item-gap .is-show-1 {
  background-image: url('../assets/images/1/collapse-left.svg');
}
.mi-flex-grid .grid-item-gap .is-hide-0 {
  background-image: url('../assets/images/0/collapse-right.svg');
}
.mi-flex-grid .grid-item-gap .is-hide-1 {
  background-image: url('../assets/images/1/collapse-right.svg');
}
.mi-flex-grid-preview {
  position: absolute;
  top: 0;
  left: 0;
  display: grid;
  width: 100%;
  height: 100%;
  background-color: var(--grid-preview-bg-color);
  z-index: 999;
}
.grid-preview-item {
  background-color: var(--grid-preview-bg-color);
  border: 1px dashed #000;
}
.grid-preview-item .grid-columnGap {
  width: 100%;
  height: 100%;
  cursor: col-resize;
}
.grid-preview-item .grid-rowGap {
  width: 100%;
  height: 100%;
  cursor: row-resize;
}
</style>

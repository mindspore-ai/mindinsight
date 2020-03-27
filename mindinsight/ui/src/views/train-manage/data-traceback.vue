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
  <div id='cl-data-traceback'>
    <div class="cl-data-right">
      <!-- select area -->
      <div class="data-checkbox-area"
           v-show="totalSeries && totalSeries.length">
        <!-- show all data button -->
        <el-button class="reset-btn custom-btn"
                   @click="echartShowAllData"
                   type="primary"
                   size="mini"
                   plain>
          {{$t('modelTraceback.showAllData')}}
        </el-button>
        <div class="fixed-checkbox-group">
          <el-checkbox v-for="item in fixedSeries"
                       :key="item.id"
                       :checked="item.checked"
                       :disabled="true">
            {{item.name}}
          </el-checkbox>
          <br>
        </div>
        <div class="data-checkbox">
          <!-- check box -->
          <div class="check-box-div">
            <el-checkbox v-model="checkAll"
                         :indeterminate="isIndeterminate"
                         class="select-all"
                         @change="handleCheckAllChange">
              {{$t('scalar.selectAll')}}
            </el-checkbox>
          </div>
          <div class="checkbox-scroll">
            <div class="checkbox-group-div">
              <el-checkbox v-for="item in noFixedSeries"
                           @change="handleCheckedSeriesChange()"
                           v-model="item.checked"
                           :key="item.id">
                {{item.name}}
              </el-checkbox>
            </div>
          </div>

        </div>
      </div>
      <!-- echart drawing area -->
      <div id="data-echart"></div>
      <div v-if="echartNoData"
           class="echart-no-data">
        <div class="echart-no-data-container">
          <img :src="require('@/assets/images/nodata.png')"
               alt="" />
          <p class='no-data-text'>
            {{$t("public.noData")}}
          </p>
        </div>
      </div>

      <!-- table area -->
      <div class="table-container"
           v-show="lineagedata.serData && !!lineagedata.serData.length">
        <el-table ref="table"
                  :data="table.data"
                  tooltip-effect="light"
                  height="calc(100% - 54px)"
                  row-key='summaryDir'
                  @selection-change="handleSelectionChange">
          <el-table-column type="selection"
                           width="55"
                           :reserve-selection="true">
          </el-table-column>
          <el-table-column v-for="key in table.column"
                           :key="key"
                           :prop="key"
                           :label="table.columnOptions[key].label"
                           min-width='200'
                           show-overflow-tooltip>
            <template slot-scope="scope">
              <span class="icon-container"
                    v-show='table.columnOptions[key].label===text'>
                <el-tooltip effect="light"
                            :content="$t('dataTraceback.dataTraceTips')"
                            placement="top"
                            v-show='scope.row.children'>
                  <i class="el-icon-warning"></i>
                </el-tooltip>
              </span>
              <span @click="jumpToTrainDashboard(scope.row[key])"
                    v-if='table.columnOptions[key].label===text'
                    class="href-color"> {{scope.row[key]}} </span>
              <span v-else-if="table.columnOptions[key].label===repeatTitle
              ||table.columnOptions[key].label===shuffleTitle
              ||table.columnOptions[key].label===batchNode
              ||scope.row[key]===emptyObject
              ||!scope.row[key]">
                {{scope.row[key]}}
              </span>
              <span v-else
                    @click="showDialogData(scope.row[key], scope)"
                    class="click-span">
                {{scope.row[key]}}
              </span>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination @current-change="handleCurrentChange"
                       :current-page="pagination.currentPage"
                       :page-size="pagination.pageSize"
                       :layout="pagination.layout"
                       :total="pagination.total">
        </el-pagination>
      </div>
      <div v-show="(!lineagedata.serData || !lineagedata.serData.length) && initOver"
           class="no-data-page">
        <div class="no-data-img">
          <img :src="require('@/assets/images/nodata.png')"
               alt="" />
          <p class='no-data-text'>
            {{$t("public.noData")}}
          </p>
        </div>
      </div>
    </div>
    <el-dialog :title="rowName"
               :visible.sync="detailsDialogVisible"
               width="50%"
               :close-on-click-modal="false"
               class="details-data-list">
      <div class="details-data-title">{{detailsDataTitle}}</div>
      <el-table :data="detailsDataList"
                row-key="id"
                lazy
                tooltip-effect="light"
                :load="loadDataListChildren"
                :tree-props="{children: 'children', hasChildren: 'hasChildren'}">
        <el-table-column width="50" />
        <el-table-column prop="key"
                         width="180"
                         label="Key">
        </el-table-column>
        <el-table-column prop="value"
                         show-overflow-tooltip
                         label="Value">
          <template slot-scope="scope">
            {{scope.row.value}}
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>
<script>
import RequestService from '../../services/request-service';
import CommonProperty from '@/common/common-property.js';
import Echarts from 'echarts';
export default {
  data() {
    return {
      initOver: false, // Page initialization completed.
      echartNoData: false,
      // Encapsulate the data returned by the background interface.
      lineagedata: {},
      // Create an array of the type and filter the mandatory options from the array.
      createType: {
        StorageDataset: true,
        ImageFolderDataset: true,
        ImageFolderDatasetV2: true,
        MnistDataset: true,
        MindDataset: true,
        GeneratorDataset: true,
        TFRecordDataset: true,
        ManifestDataset: true,
        Cifar10Dataset: true,
        Cifar100Dataset: true,
        Schema: true,
        VOCDataset: true,
      },
      // echart parallel line coordinate system
      parallelEchart: null,
      shuffleTitle: 'Shuffle',
      repeatTitle: 'Repeat',
      categoryType: 'category',
      emptyObject: '{}',
      objectType: 'object',
      type: {
        batch: 'BatchDataset',
        shuffle: 'ShuffleDataset',
        repeat: 'RepeatDataset',
        mapData: 'MapDataset',
      },
      batchNode: 'Batch',
      echart: {
        brushData: [],
        // Data of echart  need to be displayed
        showData: [],
      },
      text: this.$t('modelTraceback.summaryPath'),
      checkAll: false,
      // Selected option
      checkedSeries: [],
      // fixed option
      fixedSeries: [],
      // other option can be selected
      noFixedSeries: [],
      // Array of all options
      totalSeries: [],
      // Setting the style attributes of all boxes
      isIndeterminate: false,
      // Page data
      pagination: {
        currentPage: 1,
        pageSize: 8,
        total: 0,
        layout: 'total, prev, pager, next, jumper',
      },
      // Summary path column
      summaryList: ['summaryDir'],
      table: {
        columnOptions: {
          summaryDir: {
            label: this.$t('modelTraceback.summaryPath'),
            required: true,
          },
        },
        // All options of the column in the table
        column: [],
        // Data of the table
        data: [],
      },

      tempFormateData: {},
      detailsDialogVisible: false,
      detailsDataTitle: '',
      detailsDataList: [],
      rowName: this.$t('dataTraceback.details'),
    };
  },
  computed: {},
  mounted() {
    this.$nextTick(() => {
      this.init();
    });
  },
  methods: {
    /**
     * init
     */
    init() {
      this.getDatasetLineage();
    },

    /*
     * Initialize the echart diagram.
     */
    initChart() {
      const parallelAxis = [];
      const data = [];
      this.echart.showData.forEach((val, i) => {
        const item = {
          lineStyle: {
            normal: {
              color: CommonProperty.commonColorArr[i % 10],
            },
          },
          value: [],
        };
        this.checkedSeries.forEach((obj) => {
          item.value.push(val[obj.id]);
        });
        data.push(item);
      });

      this.checkedSeries.forEach((content, i) => {
        const obj = {dim: i, name: content.name, id: content.id};
        if (
          content.name === this.repeatTitle ||
          content.name === this.shuffleTitle
        ) {
          obj.scale = true;
        } else {
          // Character string
          obj.type = this.categoryType;
          obj.axisLabel = {
            show: false,
          };
          const values = {};
          this.echart.showData.forEach((i) => {
            if (i[content.id] || i[content.id] === 0) {
              values[i[content.id]] = '';
            }
          });
          obj.data = Object.keys(values);
        }
        parallelAxis.push(obj);
      });

      const option = {
        backgroundColor: 'white',
        parallelAxis: parallelAxis,
        tooltip: {
          trigger: 'axis',
        },
        parallel: {
          top: 30,
          left: 80,
          right: 80,
          bottom: 12,
          parallelAxisDefault: {
            areaSelectStyle: {
              width: 40,
            },
            minInterval: 1,
            tooltip: {
              show: true,
            },
            realtime: false,
          },
        },
        series: {
          type: 'parallel',
          lineStyle: {
            width: 2,
          },
          data: data,
        },
      };
      if (this.parallelEchart) {
        this.parallelEchart.off('axisareaselected', null);
        window.removeEventListener('resize', this.resizeChart, false);
      }
      this.parallelEchart = Echarts.init(
          document.querySelector('#data-echart'),
      );
      this.parallelEchart.setOption(option, true);
      window.addEventListener('resize', this.resizeChart, false);

      this.parallelEchart.on('axisareaselected', (params) => {
        const key = params.parallelAxisId;
        const range = params.intervals[0] || [];
        const [axisData] = parallelAxis.filter((i) => {
          return i.id === key;
        });
        if (axisData && range.length === 2) {
          if (axisData.type === this.categoryType) {
            const selectedAxisKeys = axisData.data.slice(
                range[0],
                range[1] + 1,
            );
            this.echart.brushData = this.echart.showData.filter((i) => {
              return selectedAxisKeys.includes(i[key]);
            });
          } else {
            this.echart.brushData = this.echart.showData.filter((i) => {
              return i[key] >= range[0] && i[key] <= range[1];
            });
          }
          this.echart.showData = this.echart.brushData;
          this.initChart();

          this.pagination.currentPage = 1;
          this.pagination.total = this.echart.brushData.length;
          this.table.data = this.echart.brushData.slice(
              (this.pagination.currentPage - 1) * this.pagination.pageSize,
              this.pagination.currentPage * this.pagination.pageSize,
          );
        }
      });
    },

    /**
     * jump to train dashboard
     * @param {String} val
     */
    jumpToTrainDashboard(val) {
      const trainId = encodeURIComponent(val);
      const routeUrl = this.$router.resolve({
        path: '/train-manage/training-dashboard',
        query: {id: trainId},
      });
      window.open(routeUrl.href, '_blank');
    },

    /**
     * The detailed information is displayed in the dialog box.
     * @param {String} val
     * @param {Object} scope
     */
    showDialogData(val, scope) {
      this.rowName = `${scope.column.property}${this.$t(
          'dataTraceback.details',
      )}`;
      this.detailsDialogVisible = true;
      this.detailsDataTitle = scope.row.summaryDir;
      this.detailsDataList = this.formateJsonString(val);
    },

    /**
     * set object value
     * @param {Array} array
     * @param {boolean} booleanValue
     */
    setObjectValue(array, booleanValue) {
      array.forEach((val) => {
        const obj = {};
        obj.label = val.name;
        obj.required = booleanValue;
        this.table.columnOptions[val.id] = obj;
      });
    },

    /**
     * Method of invoking the interface
     */
    getDatasetLineage() {
      RequestService.getDatasetLineage()
          .then(
              (res) => {
                this.initOver = true;
                if (!res || !res.data) {
                  return;
                }
                this.fixedSeries = [];
                this.noFixedSeries = [];
                this.checkedSeries = [];
                this.lineagedata = this.formateOriginData(res.data);
                this.totalSeries = this.lineagedata.fullNodeList;
                this.totalSeries.forEach((nodeItem) => {
                  if (this.createType[nodeItem.name]) {
                    nodeItem.checked = true;
                    this.fixedSeries.push(nodeItem);
                  } else {
                    nodeItem.checked = false;
                    this.noFixedSeries.push(nodeItem);
                  }
                });
                this.noFixedSeries.forEach((item) => {
                  item.checked = true;
                });
                this.getCheckedSerList();
                if (this.fixedSeries.length) {
                  this.setObjectValue(this.fixedSeries, true);
                }
                if (this.noFixedSeries.length) {
                  this.setObjectValue(this.noFixedSeries, false);
                }
                this.echart.brushData = this.lineagedata.serData;
                this.echart.showData = this.echart.brushData;
                if (this.totalSeries.length) {
                  document.querySelector('#data-echart').style.display = 'block';
                } else {
                  this.echartNoData = true;
                }

                // Total number of pages in the table
                this.pagination.total = this.lineagedata.serData.length;
                // Data encapsulation of the table
                this.setTableData();
                this.table.column = this.summaryList.concat(
                    this.checkedSeries.map((i) => i.id),
                );
                this.initChart();
              },
              (error) => {
                this.initOver = true;
              },
          )
          .catch(() => {
            this.initOver = true;
          });
    },

    /**
     *  Gets the selected items and updates the select all state.
     */
    getCheckedSerList() {
      this.checkedSeries = [];
      this.totalSeries.forEach((nodeItem) => {
        if (nodeItem.checked) {
          this.checkedSeries.push(nodeItem);
        }
      });
      if (this.checkedSeries.length == this.totalSeries.length) {
        this.checkAll = true;
      } else {
        this.checkAll = false;
      }
    },

    /**
     *  The window size changes. Resizing Chart
     */
    resizeChart() {
      this.parallelEchart.resize();
    },

    /**
     * reset echart data.Show all data
     *
     */
    echartShowAllData() {
      // The first page is displayed.
      this.pagination.currentPage = 1;
      this.echart.brushData = this.lineagedata.serData;
      this.echart.showData = this.echart.brushData;
      this.initChart();
      this.$refs.table.clearSelection();
      this.setTableData();
      this.pagination.total = this.echart.brushData.length;
    },

    /**
     * Select All
     */
    handleCheckAllChange() {
      // Selected option
      this.noFixedSeries.forEach((nodeItem) => {
        nodeItem.checked = this.checkAll;
      });
      this.$forceUpdate();
      this.getCheckedSerList();
      // Value assignment in the table column
      this.table.column = this.summaryList.concat(
          this.checkedSeries.map((i) => i.id),
      );
      this.isIndeterminate = false;
      this.initChart();
    },

    /**
     * The column options in the table are changed
     */
    handleCheckedSeriesChange() {
      this.$forceUpdate();
      this.getCheckedSerList();
      // Value assignment in the table column
      this.table.column = this.summaryList.concat(
          this.checkedSeries.map((i) => i.id),
      );
      this.isIndeterminate =
        this.checkedSeries.length > this.fixedSeries.length && !this.checkAll;
      this.initChart();
    },

    /**
     * Selected rows of tables
     * @param {Object} val
     */
    handleSelectionChange(val) {
      if (val.length) {
        this.echart.showData = val;
      } else {
        this.echart.showData = this.echart.brushData;
      }
      this.initChart();
    },

    /**
     * Setting Table Data
     * @param {Number} val
     */
    handleCurrentChange(val) {
      this.pagination.currentPage = val;
      this.setTableData();
    },

    /**
     * Setting Table Data
     */
    setTableData() {
      // Table data encapsulation
      const pathData = JSON.parse(JSON.stringify(this.echart.brushData));
      // Obtain table data based on the page number and number of records.
      this.table.data = pathData.slice(
          (this.pagination.currentPage - 1) * this.pagination.pageSize,
          this.pagination.currentPage * this.pagination.pageSize,
      );
    },

    /**
     * Chart data encapsulation
     * @param {Object} data
     * @return {Object}
     */
    formateOriginData(data) {
      if (!data || !data.object) {
        return {};
      }
      // Preliminarily filter the required data from the original data and form a unified format.
      const objectDataArr = [];
      data.object.forEach((object) => {
        this.tempFormateData = {
          nodeList: [],
          children: false,
          summary_dir: object.summary_dir,
        };
        if (JSON.stringify(object.dataset_graph) !== '{}') {
          this.getSingleRunData(object.dataset_graph);
        }
        objectDataArr.push(JSON.parse(JSON.stringify(this.tempFormateData)));
      });
      // The data in the unified format is combined by category.
      const fullNodeList = [];
      const tempDic = {};
      objectDataArr.forEach((objectData) => {
        if (fullNodeList.length) {
          let startIndex = 0;
          let tempNodeListMap = fullNodeList.map((nodeObj) => nodeObj.name);
          objectData.nodeList.forEach((nodeItem) => {
            const tempIndex = tempNodeListMap.indexOf(
                nodeItem.name,
                startIndex,
            );
            if (tempIndex === -1) {
              if (!tempDic[nodeItem.name]) {
                tempDic[nodeItem.name] = 0;
              }
              tempDic[nodeItem.name]++;
              const tempId = `${nodeItem.name}${tempDic[nodeItem.name]}`;
              fullNodeList.splice(startIndex, 0, {
                name: nodeItem.name,
                id: tempId,
              });
              nodeItem.id = tempId;
              startIndex++;
              tempNodeListMap = fullNodeList.map((nodeObj) => nodeObj.name);
            } else {
              nodeItem.id = fullNodeList[tempIndex].id;
              startIndex = tempIndex + 1;
            }
          });
        } else {
          objectData.nodeList.forEach((nodeItem) => {
            if (!tempDic[nodeItem.name]) {
              tempDic[nodeItem.name] = 0;
            }
            tempDic[nodeItem.name]++;
            fullNodeList.push({
              name: nodeItem.name,
              id: `${nodeItem.name}${tempDic[nodeItem.name]}`,
            });
            nodeItem.id = `${nodeItem.name}${tempDic[nodeItem.name]}`;
          });
        }
      });
      // Obtain the value of run on each coordinate.
      const serData = [];
      objectDataArr.forEach((objectData) => {
        const curDataObj = {};
        objectData.nodeList.forEach((nodeItem) => {
          curDataObj[nodeItem.id] = nodeItem.value;
        });
        curDataObj.children = objectData.children;
        curDataObj.summaryDir = objectData.summary_dir;
        serData.push(curDataObj);
      });
      const formateData = {
        fullNodeList: fullNodeList,
        serData: serData,
      };
      return formateData;
    },

    /**
     * Get single run data
     * @param {Object} nodeObj
     */
    getSingleRunData(nodeObj) {
      if (nodeObj.children && nodeObj.children.length) {
        if (nodeObj.children.length > 1) {
          this.tempFormateData.children = true;
        }
        this.getSingleRunData(nodeObj.children[0]);
      }
      let nodeType = nodeObj.op_type;
      let nodeName = '';
      let nodeValue = '';

      if (nodeType === this.type.batch) {
        nodeName = this.batchNode;
        nodeValue = `batch_size:${nodeObj.batch_size},drop_remainder:${nodeObj.drop_remainder}`;
      } else if (nodeType === this.type.shuffle) {
        nodeName = this.shuffleTitle;
        nodeValue = nodeObj.buffer_size;
      } else if (nodeType === this.type.repeat) {
        nodeValue = nodeObj.count;
        nodeName = this.repeatTitle;
      } else if (nodeType === this.type.mapData) {
        const nodeOptions = nodeObj.operations;
        nodeType = nodeOptions.forEach((nodeOption) => {
          nodeName = `Map_${nodeOption.tensor_op_name}`;
          delete nodeOption.tensor_op_module;
          delete nodeOption.tensor_op_name;
          nodeValue = JSON.stringify(nodeOption);
          this.tempFormateData.nodeList.push({
            name: nodeName,
            id: ``,
            value: nodeValue,
          });
        });
      } else {
        nodeValue = JSON.stringify(nodeObj);
        nodeName = nodeType;
      }
      if (nodeObj.op_type !== this.type.mapData) {
        this.tempFormateData.nodeList.push({
          name: nodeName,
          id: ``,
          value: nodeValue,
        });
      }
    },
    /**
     * Converts JSON strings.
     * @param {String} str
     * @return {Array}
     */
    formateJsonString(str) {
      if (!str) {
        return [];
      }
      const resultArr = [];
      const dataObj = JSON.parse(str);
      const keys = Object.keys(dataObj);
      keys.forEach((key, index) => {
        const tempData = {
          id: index + 1,
          hasChildren: false,
          key: key,
          value: '',
        };
        if (typeof dataObj[key] === this.objectType && dataObj[key] !== null) {
          if (!(dataObj[key] instanceof Array)) {
            tempData.hasChildren = true;
            tempData.children = [];
            Object.keys(dataObj[key]).forEach((k, j) => {
              const item = {};
              item.key = k;
              item.value = dataObj[key][k];
              item.id = (index + 1) * 10 + 1 + j;
              tempData.children.push(item);
            });
          }
          tempData.value = JSON.stringify(dataObj[key]);
        } else {
          tempData.value = dataObj[key];
        }
        resultArr.push(tempData);
      });
      return resultArr;
    },
    loadDataListChildren(tree, treeNode, resolve) {
      setTimeout(() => {
        resolve(tree.children);
      });
    },
  },

  /**
   * Destroy the page
   */
  destroyed() {
    if (this.parallelEchart) {
      window.removeEventListener('resize', this.resizeChart, false);
      this.parallelEchart.clear();
      this.parallelEchart = null;
    }
  },
  components: {},
};
</script>
<style lang="scss">
#cl-data-traceback {
  height: 100%;
  overflow-y: auto;
  position: relative;
  .no-data-page {
    width: 100%;
    height: 100%;
    padding-top: 200px;
  }
  .no-data-img {
    background: #fff;
    text-align: center;
    height: 100%;
    width: 300px;
    margin: auto;
    img {
      max-width: 100%;
    }
  }
  .no-data-text {
    font-size: 16px;
    padding-top: 10px;
  }
  .echart-no-data {
    width: 100%;
    height: 48%;
    text-align: center;
    display: table;
  }
  .echart-no-data-container {
    display: table-cell;
    vertical-align: middle;
  }

  .cl-data-right {
    height: 100%;
    background-color: #ffffff;
    -webkit-box-shadow: 0 1px 0 0 rgba(200, 200, 200, 0.5);
    box-shadow: 0 1px 0 0 rgba(200, 200, 200, 0.5);
    overflow: hidden;

    .data-checkbox-area {
      position: relative;
      margin: 24px 32px 12px;
      .reset-btn {
        position: absolute;
        right: 0px;
        top: 12px;
      }
      .data-checkbox {
        width: calc(100% - 148px);
        height: 38px;
        overflow: hidden;
      }
      .checkbox-scroll {
        height: 38px;
        overflow: auto;
      }
      .check-box-div {
        float: left;
      }
      .checkbox-group-div {
        float: left;
        width: calc(100% - 100px);
      }
      .fixed-checkbox-group {
        width: calc(100% - 160px);
        min-height: 24px;
        max-height: 41px;
        overflow: auto;
      }
      .select-all {
        margin-right: 30px;
      }
    }
    #data-echart {
      height: 39%;
      width: 100%;
      display: none;
    }

    .custom-btn {
      border: 1px solid #00a5a7;
      border-radius: 2px;
      background-color: white;
      color: #00a5a7;
    }
    .custom-btn:hover {
      color: #00a5a7;
      background: #e9f7f7;
    }

    .table-container {
      background-color: white;
      height: calc(60% - 90px);
      margin: 2px 32px 0;
      position: relative;
      .el-icon-warning {
        font-size: 16px;
      }
      .icon-container {
        padding-right: 5px;
        width: 20px;
      }
      .href-color {
        cursor: pointer;
        color: #3399ff;
      }
      .click-span {
        cursor: pointer;
      }
      .el-pagination {
        position: absolute;
        right: 0px;
        bottom: 10px;
      }
    }
  }

  .details-data-list {
    .el-table {
      th {
        padding: 10px 0;
        border-top: 1px solid #ebeef5;
        .cell {
          border-left: 1px solid #d9d8dd;
          height: 14px;
          line-height: 14px;
        }
      }
      th:first-child {
        .cell {
          border-left: none;
        }
      }
      th:nth-child(2),
      td:nth-child(2) {
        max-width: 30%;
      }
      td {
        padding: 8px 0;
      }
    }
    .el-table__row--level-0 td:first-child:after {
      width: 20px;
      height: 1px;
      background: #ebeef5;
      z-index: 11;
      position: absolute;
      left: 0;
      bottom: -1px;
      content: '';
      display: block;
    }
    .el-table__row--level-1 {
      td {
        padding: 4px 0;
        position: relative;
      }
      td:first-child::before {
        width: 20px;
        background: #fff;
        border-right: 3px solid #7693e1;
        z-index: 10;
        position: absolute;
        left: 0;
        top: -1px;
        bottom: 0px;
        content: '';
        display: block;
      }
    }

    .el-table__row--level-1:first-child {
      td:first-child::before {
        bottom: 0;
      }
    }
    .el-dialog__title {
      font-weight: bold;
    }
    .el-dialog__body {
      max-height: 500px;
      padding-top: 10px;
      overflow: auto;
      .details-data-title {
        margin-bottom: 20px;
      }
    }
  }
}
</style>

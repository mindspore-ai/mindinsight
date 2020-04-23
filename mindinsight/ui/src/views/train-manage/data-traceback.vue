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
  <div id="cl-data-traceback">
    <div class="cl-data-right">
      <!-- select area -->
      <div class="data-checkbox-area">
        <!-- show all data button -->
        <el-button class="reset-btn custom-btn"
                   @click="echartShowAllData"
                   type="primary"
                   size="mini"
                   plain
                   v-show="(summaryDirList&&!summaryDirList.length)||(totalSeries&&totalSeries.length)">
          {{ $t('modelTraceback.showAllData') }}
        </el-button>
        <div v-show="totalSeries&&totalSeries.length&&(!summaryDirList||(summaryDirList&&summaryDirList.length))">
          <div class="fixed-checkbox-group">
            <el-checkbox v-for="item in fixedSeries"
                         :key="item.id"
                         :checked="item.checked"
                         :disabled="true">
              {{ item.name }}
            </el-checkbox>
            <br />
          </div>
          <div class="data-checkbox">
            <!-- check box -->
            <div class="check-box-div">
              <el-checkbox v-model="checkAll"
                           :indeterminate="isIndeterminate"
                           class="select-all"
                           @change="handleCheckAllChange">
                {{ $t('scalar.selectAll') }}
              </el-checkbox>
            </div>
            <div class="checkbox-scroll">
              <div class="checkbox-group-div">
                <el-checkbox v-for="item in noFixedSeries"
                             @change="handleCheckedSeriesChange()"
                             v-model="item.checked"
                             :key="item.id">
                  {{ item.name }}
                </el-checkbox>
              </div>
            </div>
          </div>
        </div>
      </div>
      <!-- echart drawing area -->
      <div id="data-echart"></div>
      <!-- table area -->
      <div class="table-container"
           v-show="!echartNoData&&lineagedata.serData && !!lineagedata.serData.length">
        <el-table ref="table"
                  :data="table.data"
                  tooltip-effect="light"
                  height="calc(100% - 54px)"
                  row-key="summary_dir"
                  @selection-change="handleSelectionChange"
                  @sort-change="tableSortChange">
          <el-table-column type="selection"
                           width="55"
                           :reserve-selection="true">
          </el-table-column>
          <el-table-column v-for="key in table.column"
                           :key="key"
                           :prop="key"
                           :label="table.columnOptions[key].label"
                           :sortable="sortArray.includes(table.columnOptions[key].label)?'custom':false"
                           :fixed="table.columnOptions[key].label===text?true:false"
                           min-width="200"
                           show-overflow-tooltip>
            <template slot="header"
                      slot-scope="scope">
              <div class="custom-label"
                   :title="scope.column.label">
                {{scope.column.label}}
              </div>
            </template>
            <template slot-scope="scope">
              <span class="icon-container"
                    v-show="table.columnOptions[key].label === text">
                <el-tooltip effect="light"
                            :content="$t('dataTraceback.dataTraceTips')"
                            placement="top"
                            v-show="scope.row.children">
                  <i class="el-icon-warning"></i>
                </el-tooltip>
              </span>
              <span @click="jumpToTrainDashboard(scope.row[key])"
                    v-if="table.columnOptions[key].label === text"
                    class="href-color">
                {{ scope.row[key] }}
              </span>
              <span v-else
                    @click="showDialogData(scope.row[key], scope)"
                    class="click-span">
                {{formatNumber(key, scope.row[key]) }}
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
      <div v-show="((!lineagedata.serData || !lineagedata.serData.length) && initOver)
         ||(echartNoData&&(lineagedata.serData&&!!lineagedata.serData.length))"
           class="no-data-page">
        <div class="no-data-img">
          <img :src="require('@/assets/images/nodata.png')"
               alt="" />
          <p class="no-data-text"
             v-show="!summaryDirList||(summaryDirList&&summaryDirList.length)&&!lineagedata.serData">
            {{ $t('public.noData') }}
          </p>
          <div v-show="echartNoData&&(lineagedata.serData&&!!lineagedata.serData.length)">
            <p class="no-data-text">{{ $t('dataTraceback.noDataFound') }}</p>
          </div>
          <div v-show="summaryDirList&&!summaryDirList.length">
            <p class="no-data-text">{{ $t('dataTraceback.noDataFound') }}</p>
            <p class="no-data-text">{{ $t('dataTraceback.noDataTips') }}</p>
          </div>
        </div>
      </div>
    </div>
    <el-dialog :title="rowName"
               :visible.sync="detailsDialogVisible"
               width="50%"
               :close-on-click-modal="false"
               class="details-data-list">
      <div class="details-data-title">{{ detailsDataTitle }}</div>
      <el-table :data="detailsDataList"
                row-key="id"
                lazy
                tooltip-effect="light"
                :load="loadDataListChildren"
                :tree-props="{ children: 'children', hasChildren: 'hasChildren' }">
        <el-table-column width="50" />
        <el-table-column prop="key"
                         width="180"
                         label="Key">
        </el-table-column>
        <el-table-column prop="value"
                         show-overflow-tooltip
                         label="Value">
          <template slot-scope="scope">
            {{ scope.row.value }}
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
      dataCheckedSummary: [],
      selectedBarList: [],
      customizedColumnOptions: [],
      // Set the type of customized
      customizedTypeObject: [],
      // Value of the vertical axis query interface brought by model source tracing
      modelObjectArray: [],
      summaryDirList: undefined,
      // Table filter condition
      tableFilter: {},
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
      deviceNum: 'device_num',
      shuffleTitle: 'Shuffle',
      repeatTitle: 'Repeat',
      categoryType: 'category',
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
      dirPathList: ['summary_dir'],
      // Options that support sorting
      sortArray: [
        this.$t('modelTraceback.summaryPath'),
        'loss',
        this.$t('modelTraceback.network'),
        this.$t('modelTraceback.optimizer'),
        this.$t('modelTraceback.trainingSampleNum'),
        this.$t('modelTraceback.testSampleNum'),
        this.$t('modelTraceback.learningRate'),
        'epoch',
        'steps',
        this.$t('modelTraceback.deviceNum'),
        this.$t('modelTraceback.modelSize'),
        this.$t('modelTraceback.lossFunc'),
      ],
      numberTypeIdList: [
        'train_dataset_count',
        'test_dataset_count',
        'epoch',
        'batch_size',
        'model_size',
        'loss',
        'learning_rate',
        'device_num',
      ],
      table: {
        columnOptions: {
          summary_dir: {
            label: this.$t('modelTraceback.summaryPath'),
            required: true,
          },
          dataset_mark: {
            label: this.$t('modelTraceback.dataProcess'),
          },
          model_size: {
            label: this.$t('modelTraceback.modelSize'),
          },
          network: {
            label: this.$t('modelTraceback.network'),
          },
          loss: {
            label: 'loss',
          },
          optimizer: {
            label: this.$t('modelTraceback.optimizer'),
          },
          train_dataset_count: {
            label: this.$t('modelTraceback.trainingSampleNum'),
          },
          test_dataset_count: {
            label: this.$t('modelTraceback.testSampleNum'),
          },
          learning_rate: {
            label: this.$t('modelTraceback.learningRate'),
          },
          epoch: {
            label: 'epoch',
          },
          batch_size: {
            label: 'steps',
          },
          device_num: {
            label: this.$t('modelTraceback.deviceNum'),
          },
          loss_function: {
            label: this.$t('modelTraceback.lossFunc'),
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
      replaceStr: {
        metric: 'metric/',
        userDefined: 'user_defined/',
      },
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
      this.customizedColumnOptions =
        this.$store.state.customizedColumnOptions || [];
      this.table.columnOptions = Object.assign(
          this.table.columnOptions,
          this.customizedColumnOptions,
      );
      // Obtain the value of summary_dir from the store,
      this.summaryDirList = this.$store.state.summaryDirList;
      this.selectedBarList = this.$store.state.selectedBarList;
      if (this.selectedBarList && this.selectedBarList.length) {
        this.tableFilter = {};
      } else {
        this.tableFilter.lineage_type = {in: ['dataset']};
      }
      const params = {};
      if (this.summaryDirList) {
        this.tableFilter.summary_dir = {in: this.summaryDirList};
      } else {
        this.tableFilter.summary_dir = undefined;
      }
      params.body = Object.assign({}, this.tableFilter);
      this.queryLineagesData(params);
    },

    /*
     * Initialize the echart diagram.
     */
    initChart() {
      const parallelAxis = [];
      const selectedBarList = this.$store.state.selectedBarList;
      const data = [];
      const arrayTemp = [];
      if (selectedBarList && selectedBarList.length) {
        selectedBarList.forEach((item) => {
          const value = this.customizedTypeObject[item];
          const obj = {
            name: this.table.columnOptions[item].label,
            id: item,
            checked: true,
          };
          if (value && value.type == 'float') {
            obj.type = 'float';
          }
          arrayTemp.push(obj);
        });
      }
      const totalBarArray = arrayTemp.concat(this.checkedSeries);
      this.echart.showData.forEach((val, i) => {
        const item = {
          lineStyle: {
            normal: {
              color: CommonProperty.commonColorArr[i % 10],
            },
          },
          value: [],
        };
        totalBarArray.forEach((obj) => {
          item.value.push(val[obj.id]);
        });
        data.push(item);
      });

      totalBarArray.forEach((content, i) => {
        const obj = {dim: i, name: content.name, id: content.id};
        if (
          content.name === this.repeatTitle ||
          content.name === this.shuffleTitle ||
          content.id === this.deviceNum
        ) {
          obj.scale = true;
          obj.minInterval = 1;
          this.setColorOfSelectedBar(selectedBarList, obj);
        } else if (
          this.numberTypeIdList.includes(content.id) ||
          (content.type && content.type == 'float')
        ) {
          obj.scale = true;
          this.setColorOfSelectedBar(selectedBarList, obj);
        } else {
          // String type
          obj.type = this.categoryType;
          obj.axisLabel = {
            show: false,
          };
          this.setColorOfSelectedBar(selectedBarList, obj);
          if (content.id === 'dataset_mark') {
            obj.axisLabel = {
              show: false,
            };
          }
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
          left: 50,
          right: 100,
          bottom: 12,
          parallelAxisDefault: {
            areaSelectStyle: {
              width: 40,
            },
            tooltip: {
              show: true,
            },
            realtime: false,
          },
        },
        series: {
          type: 'parallel',
          lineStyle: {
            width: 1,
            opacity: 1,
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
          const tempList = this.echart.brushData;
          const summaryList = [];
          tempList.forEach((item) => {
            summaryList.push(item.summary_dir);
          });
          // The summaryList value could not be saved in the destroy state.
          this.dataCheckedSummary = [];
          this.$store.commit('setSummaryDirList', summaryList);
          if (!tempList.length) {
            this.summaryDirList = [];
            this.lineagedata.serData = undefined;
            document.querySelector('#data-echart').style.display = 'none';
          } else {
            this.echart.showData = this.echart.brushData;
            this.initChart();
            this.pagination.currentPage = 1;
            this.pagination.total = this.echart.brushData.length;
            this.table.data = this.echart.brushData.slice(
                (this.pagination.currentPage - 1) * this.pagination.pageSize,
                this.pagination.currentPage * this.pagination.pageSize,
            );
          }
        }
      });
    },
    /**
     * Set the color of the model tracing axis.
     * @param {Array} selectedBarList
     * @param {Object} obj
     */
    setColorOfSelectedBar(selectedBarList, obj) {
      if (selectedBarList && obj.dim < selectedBarList.length) {
        obj.nameTextStyle = {
          color: '#00a5a7',
        };
        obj.axisLabel = {
          show: true,
          textStyle: {
            color: '#00a5a7',
          },
          formatter: function(val) {
            if (typeof val !== 'string') {
              return val;
            }
            const strs = val.split('');
            let str = '';
            if (val.length > 100) {
              return val.substring(0, 12) + '...';
            } else {
              for (let i = 0, s = ''; (s = strs[i++]); ) {
                str += s;
                if (!(i % 12)) {
                  str += '\n';
                }
              }
              return str;
            }
          },
        };
        obj.axisLine = {
          show: true,
          lineStyle: {
            color: '#00a5a7',
          },
        };
      } else {
        // Text color
        obj.nameTextStyle = {
          color: 'black',
        };
      }
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
     * Formatting Data
     * @param {String} key
     * @param {String} value
     * @return {Object}
     */
    formatNumber(key, value) {
      if (isNaN(value) || !value) {
        return value;
      } else {
        if (key === 'learning_rate') {
          let temp = value.toPrecision(4);
          let row = 0;
          while (temp < 1) {
            temp = temp * 10;
            row += 1;
          }
          temp = this.toFixedFun(temp, 4);
          return `${temp}${row ? `e-${row}` : ''}`;
        } else if (key === 'model_size') {
          return value + 'MB';
        } else {
          if (value < 1000) {
            return Math.round(value * Math.pow(10, 4)) / Math.pow(10, 4);
          } else {
            const reg = /(?=(\B)(\d{3})+$)/g;
            return (value + '').replace(reg, ',');
          }
        }
      }
    },

    /**
     * Keep the number with n decimal places.
     * @param {Number} num
     * @param {Number} pow Number of decimal places
     * @return {Number}
     */
    toFixedFun(num, pow) {
      if (isNaN(num) || isNaN(pow) || !num || !pow) {
        return num;
      }
      return Math.round(num * Math.pow(10, pow)) / Math.pow(10, pow);
    },

    /**
     * The detailed information is displayed in the dialog box.
     * @param {String} val
     * @param {Object} scope
     */
    showDialogData(val, scope) {
      if (typeof val !== 'string' || val == '{}') {
        return;
      } else {
        const isJson = this.isJSON(val);
        if (!isJson) {
          return;
        }
      }
      this.rowName = `${scope.column.label}${this.$t('dataTraceback.details')}`;
      this.detailsDialogVisible = true;
      this.detailsDataTitle = scope.row.summary_dir;
      this.detailsDataList = this.formateJsonString(val);
    },

    /**
     * Checks whether the value is a JSON character string.
     *  @param {String} val
     * @return {Boolean}
     */
    isJSON(val) {
      try {
        JSON.parse(val);
        return true;
      } catch (e) {
        return false;
      }
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
     * @param {Object} params
     */
    queryLineagesData(params) {
      RequestService.queryLineagesData(params)
          .then(
              (res) => {
                this.initOver = true;
                if (!res || !res.data) {
                  return;
                }
                this.customizedTypeObject = res.data.customized;
                let keys = Object.keys(this.customizedTypeObject);
                if (keys.length) {
                  keys = keys.map((i) => {
                    if (i.startsWith(this.replaceStr.userDefined)) {
                      return i.replace(this.replaceStr.userDefined, '[U]');
                    } else if (i.startsWith(this.replaceStr.metric)) {
                      return i.replace(this.replaceStr.metric, '[M]');
                    }
                  });
                  this.sortArray = this.sortArray.concat(keys);
                }
                // Model source tracing filtering parameters
                this.selectedBarList = this.$store.state.selectedBarList;
                if (this.selectedBarList && this.selectedBarList.length) {
                  const tempList = JSON.parse(JSON.stringify(res.data.object));
                  const list = [];
                  const metricKeys = {};
                  tempList.forEach((item) => {
                    if (item.model_lineage) {
                      const modelData = JSON.parse(
                          JSON.stringify(item.model_lineage),
                      );
                      modelData.model_size = parseFloat(
                          ((modelData.model_size || 0) / 1024 / 1024).toFixed(2),
                      );
                      const keys = Object.keys(modelData.metric || {});
                      if (keys.length) {
                        keys.forEach((key) => {
                          if (
                            modelData.metric[key] ||
                        modelData.metric[key] === 0
                          ) {
                            const temp = this.replaceStr.metric + key;
                            metricKeys[temp] = key;
                            modelData[temp] = modelData.metric[key];
                          }
                        });
                        delete modelData.metric;
                      }
                      const udkeys = Object.keys(modelData.user_defined || {});
                      if (udkeys.length) {
                        udkeys.forEach((key) => {
                          if (
                            modelData.user_defined[key] ||
                        modelData.user_defined[key] === 0
                          ) {
                            const temp = this.replaceStr.userDefined + key;
                            modelData[temp] = modelData.user_defined[key];
                          }
                        });
                        delete modelData.user_defined;
                      }
                      list.push(modelData);
                    }
                  });
                  this.modelObjectArray = [];
                  for (let i = 0; i < list.length; i++) {
                    const modelObject = {};
                    for (let j = 0; j < this.selectedBarList.length; j++) {
                      const tempObject = list[i];
                      const key = this.selectedBarList[j];
                      modelObject[key] = tempObject[key];
                    }
                    this.modelObjectArray.push(modelObject);
                  }
                }

                this.fixedSeries = [];
                this.noFixedSeries = [];
                this.checkedSeries = [];
                this.lineagedata = this.formateOriginData(res.data);
                this.totalSeries = this.lineagedata.fullNodeList;
                if (!this.totalSeries.length) {
                  this.echartNoData = true;
                }
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
                }
                this.setEchartValue();
                this.initChart();
                // Total number of pages in the table
                this.pagination.total = res.data.count;
                // Data encapsulation of the table
                this.setTableData();
                if (this.selectedBarList) {
                  const resultArray = this.hideDataMarkTableData();
                  this.table.column = this.dirPathList.concat(
                      resultArray,
                      this.checkedSeries.map((i) => i.id),
                  );
                } else {
                  this.table.column = this.dirPathList.concat(
                      this.checkedSeries.map((i) => i.id),
                  );
                }
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
      this.initOver = false;
      this.echartNoData = false;
      this.pagination.currentPage = 1;
      this.$store.commit('setSummaryDirList', undefined);
      this.$store.commit('setSelectedBarList', []);
      if (this.parallelEchart) {
        this.parallelEchart.clear();
      }
      document.querySelector('#data-echart').style.display = 'block';
      this.$refs.table.clearSelection();
      this.init();
      this.parallelEchart.resize();
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
      if (this.selectedBarList) {
        const resultArray = this.hideDataMarkTableData();
        this.table.column = this.dirPathList.concat(
            resultArray,
            this.checkedSeries.map((i) => i.id),
        );
      } else {
        this.table.column = this.dirPathList.concat(
            this.checkedSeries.map((i) => i.id),
        );
      }

      this.isIndeterminate = false;
      this.initChart();
    },

    /**
     * The table column data is deleted from the data processing result.
     * @return {Array}
     */
    hideDataMarkTableData() {
      const result = [];
      this.selectedBarList.forEach((item) => {
        if (item !== 'dataset_mark') {
          result.push(item);
        }
      });
      return result;
    },

    /**
     * The column options in the table are changed
     */
    handleCheckedSeriesChange() {
      this.$forceUpdate();
      this.getCheckedSerList();
      // Value assignment in the table column
      if (this.selectedBarList) {
        const resultArray = this.hideDataMarkTableData();
        this.table.column = this.dirPathList.concat(
            resultArray,
            this.checkedSeries.map((i) => i.id),
        );
      } else {
        this.table.column = this.dirPathList.concat(
            this.checkedSeries.map((i) => i.id),
        );
      }

      this.isIndeterminate =
        this.checkedSeries.length > this.fixedSeries.length && !this.checkAll;
      this.initChart();
    },

    /**
     * Selected rows of tables
     * @param {Object} val
     */
    handleSelectionChange(val) {
      // summary_dir cannot be stored here.If it is not selected ,it cannot be stroed correctly.
      this.dataCheckedSummary = val;
      if (val.length) {
        this.echart.showData = val;
      } else {
        this.echart.showData = this.echart.brushData;
      }
      this.initChart();
    },

    setEchartValue() {
      if (this.modelObjectArray.length) {
        const list = this.echart.showData;
        for (let i = 0; i < list.length; i++) {
          const temp = this.modelObjectArray[i];
          this.echart.showData[i] = Object.assign(
              this.echart.showData[i],
              temp,
          );
        }
      }
    },

    /**
     * Sort by path parameter
     * @param {Object} data
     */
    tableSortChange(data) {
      const params = {};
      const tempParam = {
        sorted_name: data.prop,
        sorted_type: data.order,
      };
      params.body = Object.assign({}, tempParam, this.tableFilter);
      this.queryLineagesData(params);
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
        curDataObj.summary_dir = objectData.summary_dir;
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
    if (this.dataCheckedSummary && this.dataCheckedSummary.length) {
      const summaryDirList = [];
      this.dataCheckedSummary.forEach((item) => {
        summaryDirList.push(item.summary_dir);
      });
      this.$store.commit('setSummaryDirList', summaryDirList);
    }
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
    padding-top: 184px;
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
    p {
      font-size: 16px;
      padding-top: 10px;
    }
  }
  .no-data-text {
    font-size: 16px;
    padding-top: 10px;
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
      height: 62px;
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
      .custom-label {
        max-width: calc(100% - 25px);
        padding: 0;
        vertical-align: middle;
      }
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

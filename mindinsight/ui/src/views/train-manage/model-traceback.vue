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
  <div id='cl-model-traceback'>
    <div class="cl-model-right">
      <div class="checkbox-area"
           v-if="!noData && echart.allData.length">
        <el-button class="reset-btn custom-btn"
                   @click="resetChart"
                   type="primary"
                   size="mini"
                   plain>
          {{$t('modelTraceback.showAllData')}}
        </el-button>
        <div class="checkbox">
          <el-checkbox v-for="item in table.mandatoryColumn"
                       :key="item"
                       :label="item"
                       :checked="true"
                       :disabled="true"
                       :class="table.optionsNotInCheckbox.includes(item)?'notShow': ''">
            {{table.columnOptions[item].label}}
          </el-checkbox>
          <br>
          <el-checkbox class="select-all"
                       v-model="table.selectAll"
                       :indeterminate="table.isIndeterminate"
                       @change="checkboxSelectAll">
            {{$t('scalar.selectAll')}}
          </el-checkbox>
          <el-checkbox-group v-model="table.selectedColumn"
                             @change="columnSelectionChange">
            <el-checkbox v-for="item in table.optionalColumn"
                         :key="item"
                         :label="item"
                         :class="table.optionsNotInCheckbox.includes(item)?'notShow': 'option'">
              {{table.columnOptions[item].label}}
            </el-checkbox>
          </el-checkbox-group>
        </div>
      </div>
      <div id="echart"
           v-show="!noData"></div>
      <div class="table-container"
           v-show="showTable && !noData">
        <el-table stripe
                  ref="table"
                  :data="table.data"
                  tooltip-effect="light"
                  height="calc(100% - 40px)"
                  @selection-change="selectionChange"
                  @sort-change='sortChange'
                  row-key="summary_dir">
          <el-table-column type="selection"
                           width="55"
                           v-if="table.data.length"
                           :reserve-selection="true">
          </el-table-column>
          <el-table-column v-for="key in table.column"
                           :key="key"
                           :prop="key"
                           :label="table.columnOptions[key].label"
                           show-overflow-tooltip
                           min-width='150'
                           sortable='custom'>
            <template slot-scope="scope">
              <a v-if="key === 'summary_dir'"
                 @click="jumpToTrainDashboard(scope.row[key])">{{scope.row[key]}}</a>
              <span v-else> {{formatNumber(key, scope.row[key])}}</span>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination @current-change="pagination.pageChange"
                       :current-page="pagination.currentPage"
                       :page-size="pagination.pageSize"
                       :layout="pagination.layout"
                       :total="pagination.total">
        </el-pagination>
      </div>
      <div v-if="noData"
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
  </div>
</template>
<script>
import RequestService from '../../services/request-service';
import CommonProperty from '@/common/common-property.js';
import Echarts from 'echarts';

export default {
  props: {},
  watch: {},
  data() {
    return {
      table: {
        columnOptions: {
          train_dataset_path: {
            label: this.$t('modelTraceback.trainSetPath'),
            required: true,
          },
          test_dataset_path: {
            label: this.$t('modelTraceback.testSetPath'),
            required: true,
          },
          loss: {
            label: 'loss',
            required: true,
          },
          network: {
            label: this.$t('modelTraceback.network'),
            required: true,
          },
          optimizer: {
            label: this.$t('modelTraceback.optimizer'),
            required: true,
          },
          train_dataset_count: {
            label: this.$t('modelTraceback.trainingSampleNum'),
            required: false,
          },
          test_dataset_count: {
            label: this.$t('modelTraceback.testSampleNum'),
            required: false,
          },
          learning_rate: {
            label: this.$t('modelTraceback.learningRate'),
            required: false,
          },
          epoch: {
            label: 'epoch',
            required: false,
          },
          batch_size: {
            label: 'steps',
            required: false,
          },
          model_size: {
            label: this.$t('modelTraceback.modelSize'),
            required: false,
          },
          loss_function: {
            label: this.$t('modelTraceback.lossFunc'),
            required: false,
          },
        }, // All options of the column in the table
        column: [], // Table Column
        mandatoryColumn: [], // Mandatory Table Column
        optionalColumn: [], // Optional Table Column
        data: [],
        optionsNotInCheckbox: [
          'summary_dir',
          'train_dataset_path',
          'test_dataset_path',
        ],
        optionsNotInEchart: [
          'summary_dir',
          'train_dataset_path',
          'test_dataset_path',
        ],
        optionsNotInTable: ['dataset_mark'],
        selectedColumn: [],
        selectAll: false, // Whether to select all columns
        indeterminate: false,
      },
      keysOfStringValue: [
        'summary_dir',
        'network',
        'optimizer',
        'loss_function',
        'train_dataset_path',
        'test_dataset_path',
        'dataset_mark',
      ], // All keys whose values are character strings
      keysOfIntValue: [
        'train_dataset_count',
        'test_dataset_count',
        'epoch',
        'batch_size',
      ], // All keys whose values are int
      echart: {
        chart: null,
        allData: [],
        brushData: [],
        showData: [],
      },
      pagination: {
        currentPage: 1,
        pageSize: 8,
        total: 0,
        layout: 'total, prev, pager, next, jumper',
        pageChange: {},
      },
      chartFilter: {}, // chart filter condition
      tableFilter: {}, // table filter condition
      sortInfo: {
        sorted_name: 'summary_dir',
        sorted_type: null,
      },
      showTable: false,
      noData: false,
    };
  },
  computed: {},
  mounted() {
    this.pagination.pageChange = (page) => {
      this.pagination.currentPage = page;
      this.queryModelVersions(false);
    };
    this.$nextTick(() => {
      this.init();
    });
  },
  methods: {
    /**
     * Initialization
     */
    init() {
      this.queryModelVersions(true);
    },
    /**
     * Column initialization
     */
    initColumm() {
      this.table.mandatoryColumn = Object.keys(this.table.columnOptions).filter(
          (i) => {
            return this.table.columnOptions[i].required;
          },
      );
      this.table.optionalColumn = Object.keys(this.table.columnOptions).filter(
          (i) => {
            return !this.table.columnOptions[i].required;
          },
      );
      this.table.column = Object.keys(this.table.columnOptions).filter((i) => {
        return !this.table.optionsNotInTable.includes(i);
      });
      this.table.selectedColumn = this.table.optionalColumn;
      this.table.selectAll = true;
      this.showTable = true;
    },
    /**
     * Querying All Model Version Information
     * @param {Boolean} allData Indicates whether to query all data
     */
    queryModelVersions(allData) {
      const params = {};
      if (!allData) {
        const tempParam = {
          limit: this.pagination.pageSize,
          offset: this.pagination.currentPage - 1,
          sorted_name: this.sortInfo.sorted_name,
          sorted_type: this.sortInfo.sorted_type,
        };
        if (Object.keys(this.chartFilter).length > 0) {
          params.body = Object.assign({}, tempParam, this.chartFilter);
        } else {
          params.body = tempParam;
        }
      }
      RequestService.queryModelVersions(params)
          .then(
              (res) => {
                if (res && res.data && res.data.object) {
                  const list = JSON.parse(JSON.stringify(res.data.object));
                  const metricKeys = {};
                  list.forEach((i) => {
                    i.model_size = parseFloat(
                        ((i.model_size || 0) / 1024 / 1024).toFixed(2),
                    );
                    const keys = Object.keys(i.metric || {});
                    if (keys.length) {
                      keys.forEach((key) => {
                        if (i.metric[key] || i.metric[key] === 0) {
                          const temp = 'metric_' + key;
                          metricKeys[temp] = key;
                          i[temp] = i.metric[key];
                        }
                      });
                      delete i.metric;
                    }
                  });
                  if (allData) {
                    const obj = {};
                    Object.keys(metricKeys).forEach((key) => {
                      obj[key] = {
                        label: metricKeys[key],
                        required: true,
                      };
                    });

                    this.table.columnOptions = Object.assign(
                        {
                          summary_dir: {
                            label: this.$t('modelTraceback.summaryPath'),
                            required: true,
                          },
                          dataset_mark: {
                            label: this.$t('modelTraceback.dataProcess'),
                            required: true,
                          },
                        },
                        obj,
                        this.table.columnOptions,
                    );

                    this.noData = !!!res.data.object.length;
                    this.echart.allData = list;
                    this.echart.showData = this.echart.brushData = this.echart.allData;
                    Object.keys(this.table.columnOptions).forEach((i) => {
                      const flag = list.some((val) => {
                        return val[i] || val[i] === 0;
                      });
                      if (!flag) {
                        let index = this.table.optionsNotInCheckbox.indexOf(i);
                        if (index >= 0) {
                          this.table.optionsNotInCheckbox.splice(index, 1);
                        }
                        index = this.table.optionsNotInEchart.indexOf(i);
                        if (index >= 0) {
                          this.table.optionsNotInEchart.splice(index, 1);
                        }
                        index = this.table.optionsNotInTable.indexOf(i);
                        if (index >= 0) {
                          this.table.optionsNotInTable.splice(index, 1);
                        }

                        delete this.table.columnOptions[i];
                      }
                    });
                    this.initColumm();
                    this.initChart();
                  }

                  this.table.data = list.slice(0, this.pagination.pageSize);
                  this.pagination.total = res.data.count || 0;
                } else {
                  this.noData = allData;
                }
              },
              (error) => {
                if (allData) {
                  this.noData = allData;
                }
              },
          )
          .catch(() => {});
    },
    /**
     * The column options in the table are changed.
     */
    columnSelectionChange() {
      const columnCount =
        Object.keys(this.table.columnOptions).length -
        this.table.optionsNotInCheckbox.length;

      this.table.column = this.table.mandatoryColumn
          .concat(this.table.selectedColumn)
          .filter((i) => {
            return !this.table.optionsNotInTable.includes(i);
          });

      this.table.selectAll =
        this.table.selectedColumn
            .concat(this.table.mandatoryColumn)
            .filter((i) => {
              return !this.table.optionsNotInCheckbox.includes(i);
            }).length === columnCount;

      this.table.isIndeterminate =
        this.table.selectedColumn.length > 0 && !this.table.selectAll;
      this.initChart();
    },
    /**
     * Selected data in the table
     * @param {Array} list Selected data in the table
     */
    selectionChange(list = []) {
      this.echart.showData = list.length ? list : this.echart.brushData;
      this.initChart();
      const summaryDirFilter = [];
      this.echart.showData.forEach((i) => {
        summaryDirFilter.push(i.summary_dir);
      });
      this.tableFilter.summary_dir = {
        in: summaryDirFilter,
      };
    },
    /**
     * Sort data in the table
     * @param {Object} column current column
     */
    sortChange(column) {
      this.sortInfo.sorted_name = column.prop;
      this.sortInfo.sorted_type = column.order;
      const tempParam = {
        limit: this.pagination.pageSize,
        offset: 0,
        sorted_name: this.sortInfo.sorted_name,
        sorted_type: this.sortInfo.sorted_type,
      };
      const params = {};
      if (Object.keys(this.chartFilter).length > 0) {
        params.body = Object.assign({}, tempParam, this.chartFilter);
      } else {
        params.body = tempParam;
      }
      RequestService.queryModelVersions(params)
          .then(
              (res) => {
                if (res && res.data && res.data.object) {
                  const list = JSON.parse(JSON.stringify(res.data.object));
                  list.forEach((i) => {
                    i.model_size = parseFloat(
                        ((i.model_size || 0) / 1024 / 1024).toFixed(2),
                    );
                    const keys = Object.keys(i.metric || {});
                    if (keys.length) {
                      keys.forEach((key) => {
                        if (i.metric[key] || i.metric[key] === 0) {
                          const temp = 'metric_' + key;
                          i[temp] = i.metric[key];
                        }
                      });
                      delete i.metric;
                    }
                  });
                  this.table.data = list;
                  this.pagination.total = res.data.count || 0;
                  this.pagination.currentPage = 0;
                }
              },
              (error) => {},
          )
          .catch(() => {});
    },
    /**
     * Initializing the Eechart
     */
    initChart() {
      const chartAxis = this.table.mandatoryColumn
          .concat(this.table.selectedColumn)
          .filter((i) => {
            return !this.table.optionsNotInEchart.includes(i);
          });
      const data = [];
      this.echart.showData.forEach((i, index) => {
        const item = {
          lineStyle: {
            normal: {
              color: CommonProperty.commonColorArr[index % 10],
            },
          },
          value: [],
        };

        chartAxis.forEach((key) => {
          item.value.push(i[key]);
        });
        data.push(item);
      });

      const parallelAxis = [];
      chartAxis.forEach((key, index) => {
        const obj = {dim: index, scale: true, id: key};
        obj.name = this.table.columnOptions[key].label;
        if (this.keysOfStringValue.includes(key)) {
          const values = {};
          this.echart.showData.forEach((i) => {
            if (i[key] || i[key] === 0) {
              values[i[key]] = i[key];
            }
          });
          obj.type = 'category';
          obj.data = Object.keys(values);
          if (key === 'dataset_mark') {
            obj.axisLabel = {
              show: false,
            };
          }
        }
        if (this.keysOfIntValue.includes(key)) {
          obj.minInterval = 1;
        }
        parallelAxis.push(obj);
      });

      const echartOption = {
        backgroundColor: 'white',
        parallelAxis: parallelAxis,
        parallel: {
          top: 20,
          left: 50,
          right: 80,
          bottom: 10,
          parallelAxisDefault: {
            type: 'value',
            nameLocation: 'end',
            nameGap: 6,
            nameTextStyle: {
              color: '#000000',
              fontSize: 14,
            },
            axisLine: {
              lineStyle: {
                color: '#6D7278',
              },
            },
            axisTick: {
              lineStyle: {
                color: '#6D7278',
              },
            },
            axisLabel: {
              textStyle: {
                fontSize: 10,
                color: '#6C7280',
              },
            },
            areaSelectStyle: {
              width: 40,
            },
            realtime: false,
          },
        },
        series: {
          type: 'parallel',
          lineStyle: {
            normal: {
              width: 1,
              opacity: 1,
            },
          },
          data: data,
        },
      };

      if (this.echart.chart) {
        this.echart.chart.off('axisareaselected', null);
        window.removeEventListener('resize', this.resizeChart, false);
      }

      this.echart.chart = Echarts.init(document.querySelector('#echart'));
      this.echart.chart.setOption(echartOption, true);
      window.addEventListener('resize', this.resizeChart, false);

      // select use api
      this.echart.chart.on('axisareaselected', (params) => {
        const key = params.parallelAxisId;
        let range = params.intervals[0] || [];
        const [axisData] = parallelAxis.filter((i) => {
          return i.id === key;
        });

        if (axisData && range.length === 2) {
          if (axisData && axisData.id === 'model_size') {
            range = [
              parseInt(range[0] * 1024 * 1024, 0),
              parseInt(range[1] * 1024 * 1024, 0),
            ];
          }
          if (axisData.type === 'category') {
            const rangeData = {};
            for (let i = range[0]; i <= range[1]; i++) {
              rangeData[axisData.data[i]] = axisData.data[i];
            }
            const rangeDataKey = Object.keys(rangeData);
            this.chartFilter[key] = {
              in: rangeDataKey,
            };
          } else {
            if (this.keysOfIntValue.includes(key)) {
              range[1] = Math.floor(range[1]);
              range[0] = Math.ceil(range[0]);
            }
            this.chartFilter[key] = {
              le: range[1],
              ge: range[0],
            };
          }
          const filterParams = {};
          filterParams.body = Object.assign(
              {},
              this.chartFilter,
              this.tableFilter,
              this.sortInfo,
          );
          RequestService.queryModelVersions(filterParams)
              .then(
                  (res) => {
                    if (res && res.data && res.data.object) {
                      const list = JSON.parse(JSON.stringify(res.data.object));
                      list.forEach((i) => {
                        i.model_size = parseFloat(
                            ((i.model_size || 0) / 1024 / 1024).toFixed(2),
                        );
                        const keys = Object.keys(i.metric || {});
                        if (keys.length) {
                          keys.forEach((key) => {
                            if (i.metric[key] || i.metric[key] === 0) {
                              const temp = 'metric_' + key;
                              i[temp] = i.metric[key];
                            }
                          });
                          delete i.metric;
                        }
                      });

                      this.echart.showData = this.echart.brushData = list;
                      this.initChart();

                      this.table.data = this.echart.brushData.slice(
                          0,
                          this.pagination.pageSize,
                      );
                      this.pagination.currentPage = 1;
                      this.pagination.total = this.echart.brushData.length;
                      this.$refs.table.clearSelection();
                    }
                  },
                  (error) => {},
              )
              .catch(() => {});
        }
      });
    },
    /**
     * Resetting the Eechart
     */
    resetChart() {
      this.chartFilter = {};
      this.tableFilter = {};
      this.pagination.currentPage = 1;
      this.echart.showData = this.echart.brushData = this.echart.allData;
      this.queryModelVersions(false);
      this.$refs.table.clearSelection();
      this.initChart();
    },
    /**
     * Select all columns in the table.
     * @param {Boolean} value Select All
     */
    checkboxSelectAll(value) {
      this.table.selectedColumn = value ? this.table.optionalColumn : [];
      this.table.column = this.table.mandatoryColumn
          .concat(value ? this.table.optionalColumn : [])
          .filter((i) => {
            return !this.table.optionsNotInTable.includes(i);
          });
      this.table.isIndeterminate = false;
      this.initChart();
    },
    /**
     * Jump to the training dashboard
     * @param {String} id
     */
    jumpToTrainDashboard(id) {
      const trainId = encodeURIComponent(id);
      const routeUrl = this.$router.resolve({
        path: '/train-manage/training-dashboard',
        query: {id: trainId},
      });
      window.open(routeUrl.href, '_blank');
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
     * Formatting Data
     * @param {String} key
     * @param {String} value
     * @return {Object}
     */
    formatNumber(key, value) {
      if (isNaN(value) || !value) {
        return value;
      } else {
        if (key === 'accuracy') {
          return this.toFixedFun(value * 100, 2) + '%';
        } else if (key === 'learning_rate') {
          let temp = value.toPrecision(3);
          let row = 0;
          while (temp < 1) {
            temp = temp * 10;
            row += 1;
          }
          temp = this.toFixedFun(temp, 2);
          return `${temp}${row ? `e-${row}` : ''}`;
        } else if (key === 'model_size') {
          return value + 'MB';
        } else {
          if (value < 1000) {
            return Math.round(value * Math.pow(10, 2)) / Math.pow(10, 2);
          } else {
            const reg = /(?=(\B)(\d{3})+$)/g;
            return (value + '').replace(reg, ',');
          }
        }
      }
    },
    /**
     * Resizing Chart
     */
    resizeChart() {
      this.echart.chart.resize();
    },
  },
  destroyed() {
    if (this.echart.chart) {
      window.removeEventListener('resize', this.resizeChart, false);
      this.echart.chart.clear();
      this.echart.chart = null;
    }
  },
};
</script>
<style lang="scss">
#cl-model-traceback {
  height: 100%;
  overflow-y: auto;
  position: relative;
  .cl-model-right {
    display: flex;
    flex-direction: column;
    height: 100%;
    background-color: #ffffff;
    -webkit-box-shadow: 0 1px 0 0 rgba(200, 200, 200, 0.5);
    box-shadow: 0 1px 0 0 rgba(200, 200, 200, 0.5);
    overflow: hidden;
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

    .checkbox-area {
      margin: 24px 32px 16px;
      position: relative;
      .checkbox {
        width: calc(100% - 264px);
        max-height: 66px;
        overflow: auto;
        .mgr30 {
          margin-right: 30px;
        }
        .notShow {
          display: none;
        }
        .el-checkbox-group {
          display: inline;
          .option {
            margin-top: 4px;
          }
        }
        .select-all {
          margin-right: 30px;
        }
      }

      .reset-btn {
        position: absolute;
        right: 0;
        bottom: 0;
      }
    }
    #echart {
      height: 40%;
    }
    .table-container {
      background-color: white;
      height: calc(60% - 74px);
      padding: 12px 32px;
      position: relative;
      a {
        cursor: pointer;
      }
      .el-pagination {
        margin-right: 32px;
        position: absolute;
        right: 0;
        bottom: 10px;
      }
    }
    .no-data-page {
      width: 100%;
      height: 100%;
      padding-top: 200px;
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
    }
  }
}
</style>

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
  <div id="cl-model-traceback">
    <div class="cl-model-right">
      <div class="top-area">
        <div class="checkbox"
             :style="{'max-height': haveCustomizedParams ? '88px' : '66px',
        'min-height': haveCustomizedParams ? '63px' : '42px'}"
             v-if="!noData && echart.allData.length &&
                   (!summaryDirList || (summaryDirList && summaryDirList.length))">
          <div class="label-legend"
               v-if="haveCustomizedParams">
            <div>[U]: {{$t('modelTraceback.userDefined')}}</div>
            <div>[M]: {{$t('modelTraceback.metric')}}</div>
          </div>
          <el-checkbox v-for="item in table.mandatoryColumn"
                       :key="item"
                       :label="item"
                       :checked="true"
                       :disabled="true"
                       :class="table.optionsNotInCheckbox.includes(item) ? 'notShow' : ''">
            {{ table.columnOptions[item].label }}</el-checkbox>
          <br />
          <el-checkbox class="select-all"
                       v-model="table.selectAll"
                       :indeterminate="table.isIndeterminate"
                       @change="checkboxSelectAll">{{ $t('scalar.selectAll') }}</el-checkbox>
          <el-checkbox-group v-model="table.selectedColumn"
                             @change="columnSelectionChange">
            <el-checkbox v-for="item in table.optionalColumn"
                         :key="item"
                         :label="item"
                         :class="table.optionsNotInCheckbox.includes(item) ? 'notShow' : 'option'">
              {{ table.columnOptions[item].label }}</el-checkbox>
          </el-checkbox-group>
        </div>
        <div class="btns">
          <el-button class="custom-btn"
                     @click="resetChart"
                     type="primary"
                     size="mini"
                     plain
                     v-if="(!noData && echart.allData.length) ||
                   (noData && summaryDirList && !summaryDirList.length)">
            {{ $t('modelTraceback.showAllData') }}</el-button>
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
                  @sort-change="sortChange"
                  row-key="summary_dir">
          <el-table-column type="selection"
                           width="55"
                           v-if="table.data && table.data.length"
                           :reserve-selection="true"></el-table-column>
          <el-table-column v-for="key in table.column"
                           :key="key"
                           :prop="key"
                           :label="table.columnOptions[key].label"
                           :fixed="table.columnOptions[key].label===text?true:false"
                           show-overflow-tooltip
                           min-width="180"
                           sortable="custom">
            <template slot="header"
                      slot-scope="scope">
              <div class="custom-label"
                   :title="scope.column.label">
                {{ scope.column.label }}
              </div>
            </template>
            <template slot-scope="scope">
              <a v-if="key === 'summary_dir'"
                 @click="jumpToTrainDashboard(scope.row[key])">{{ scope.row[key] }}</a>
              <span v-else>{{ formatNumber(key, scope.row[key]) }}</span>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination @current-change="pagination.pageChange"
                       :current-page="pagination.currentPage"
                       :page-size="pagination.pageSize"
                       :layout="pagination.layout"
                       :total="pagination.total"></el-pagination>
      </div>
      <div v-if="noData"
           class="no-data-page">
        <div class="no-data-img">
          <img :src="require('@/assets/images/nodata.png')"
               alt />
          <p class="no-data-text"
             v-show="!summaryDirList || (summaryDirList && summaryDirList.length)">
            {{ $t('public.noData') }}</p>
          <div v-show="summaryDirList && !summaryDirList.length">
            <p class="no-data-text">{{ $t('modelTraceback.noDataFound') }}</p>
            <p class="no-data-text">{{ $t('modelTraceback.noDataTips') }}</p>
          </div>
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
      table: {},
      summaryDirList: undefined,
      text: this.$t('modelTraceback.summaryPath'),
      checkedSummary: [],
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
      tableFilter: {lineage_type: {in: ['model']}}, // table filter condition
      sortInfo: {
        sorted_name: 'summary_dir',
        sorted_type: null,
      },
      showTable: false,
      noData: false,
      haveCustomizedParams: false,
      replaceStr: {
        metric: 'metric/',
        userDefined: 'user_defined/',
      },
    };
  },
  computed: {},
  mounted() {
    this.$store.commit('setSelectedBarList', []);
    this.getStoreList();
    this.pagination.pageChange = (page) => {
      this.pagination.currentPage = page;
      this.queryLineagesData(false);
    };
    this.$nextTick(() => {
      this.init();
    });
  },
  methods: {
    getStoreList() {
      this.summaryDirList = this.$store.state.summaryDirList;
      if (this.summaryDirList) {
        this.tableFilter.summary_dir = {
          in: this.summaryDirList,
        };
      } else {
        this.tableFilter.summary_dir = undefined;
      }
    },

    /**
     * Initialization
     */
    init() {
      this.table = {
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
      };
      this.queryLineagesData(true);
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
    queryLineagesData(allData) {
      const params = {
        body: {},
      };
      const tempParam = {
        sorted_name: this.sortInfo.sorted_name,
        sorted_type: this.sortInfo.sorted_type,
      };
      if (!allData) {
        this.summaryDirList = this.$store.state.summaryDirList;
        this.tableFilter.summary_dir = {
          in: this.summaryDirList,
        };

        tempParam.limit = this.pagination.pageSize;
        tempParam.offset = this.pagination.currentPage - 1;
        params.body = Object.assign(params.body, this.chartFilter);
      }
      params.body = Object.assign(params.body, tempParam, this.tableFilter);

      RequestService.queryLineagesData(params)
          .then(
              (res) => {
                if (res && res.data && res.data.object) {
                  const list = this.setDataOfModel(res.data.object);
                  if (allData) {
                    let customized = {};
                    if (res.data.customized) {
                      customized = JSON.parse(JSON.stringify(res.data.customized));
                      const customizedKeys = Object.keys(customized);
                      if (customizedKeys.length) {
                        customizedKeys.forEach((i) => {
                          if (customized[i].type === 'int') {
                            this.keysOfIntValue.push(i);
                          } else if (customized[i].type === 'str') {
                            this.keysOfStringValue.push(i);
                          }
                          if (i.startsWith(this.replaceStr.userDefined)) {
                            customized[i].label = customized[i].label.replace(
                                this.replaceStr.userDefined,
                                '[U]',
                            );
                          } else if (i.startsWith(this.replaceStr.metric)) {
                            customized[i].label = customized[i].label.replace(
                                this.replaceStr.metric,
                                '[M]',
                            );
                          }
                        });
                        this.haveCustomizedParams = true;
                      }
                    }
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
                        customized,
                        this.table.columnOptions,
                    );
                    this.$store.commit('customizedColumnOptions', customized);

                    this.noData = !res.data.object.length;
                    this.echart.showData = this.echart.brushData = this.echart.allData = list;
                    Object.keys(this.table.columnOptions).forEach((i) => {
                      this.table.columnOptions[i].selected = true;
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
     * Selected data in the table
     * @param {Array} data
     * @return {Array}
     */
    setDataOfModel(data = []) {
      const modelLineageList = [];
      data.forEach((item) => {
        if (item.model_lineage) {
          item.model_lineage.summary_dir = item.summary_dir;
          const modelData = JSON.parse(JSON.stringify(item.model_lineage));
          modelData.model_size = parseFloat(
              ((modelData.model_size || 0) / 1024 / 1024).toFixed(2),
          );
          const keys = Object.keys(modelData.metric || {});
          if (keys.length) {
            keys.forEach((key) => {
              if (modelData.metric[key] || modelData.metric[key] === 0) {
                const temp = this.replaceStr.metric + key;
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
          modelLineageList.push(modelData);
        }
      });
      return modelLineageList;
    },

    /**
     * The column options in the table are changed.
     */
    columnSelectionChange() {
      this.table.optionalColumn.forEach((key) => {
        this.table.columnOptions[key].selected = false;
      });
      this.table.selectedColumn.forEach((key) => {
        this.table.columnOptions[key].selected = true;
      });

      const columnCount =
        Object.keys(this.table.columnOptions).length -
        this.table.optionsNotInCheckbox.length;

      this.table.column = Object.keys(this.table.columnOptions).filter((i) => {
        return (
          this.table.columnOptions[i].selected &&
          !this.table.optionsNotInTable.includes(i)
        );
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
      this.checkedSummary = list;
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
      this.getStoreList();
      const tempParam = {
        limit: this.pagination.pageSize,
        offset: 0,
        sorted_name: this.sortInfo.sorted_name,
        sorted_type: this.sortInfo.sorted_type,
      };
      const params = {};
      params.body = Object.assign(
          {},
          tempParam,
          this.tableFilter,
          this.chartFilter || {},
      );
      RequestService.queryLineagesData(params)
          .then(
              (res) => {
                if (res && res.data && res.data.object) {
                  const list = this.setDataOfModel(res.data.object);
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
      const chartAxis = Object.keys(this.table.columnOptions).filter((i) => {
        return (
          this.table.columnOptions[i].selected &&
          !this.table.optionsNotInEchart.includes(i)
        );
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
          } else {
            obj.axisLabel = {
              formatter: function(val) {
                const strs = val.split('');
                let str = '';
                if (val.length > 100) {
                  return val.substring(0, 12) + '...';
                } else {
                  if (chartAxis.length < 10) {
                    for (let i = 0, s = ''; (s = strs[i++]); ) {
                      str += s;
                      if (!(i % 16)) {
                        str += '\n';
                      }
                    }
                  } else {
                    for (let i = 0, s = ''; (s = strs[i++]); ) {
                      str += s;
                      if (!(i % 12)) {
                        str += '\n';
                      }
                    }
                  }
                  return str;
                }
              },
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
        tooltip: {
          trigger: 'axis',
        },
        parallel: {
          top: 25,
          left: 50,
          right: 100,
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
            tooltip: {
              show: true,
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
        const list = this.$store.state.selectedBarList || [];
        const selectedAxisId = params.parallelAxisId;
        if (list.length) {
          list.forEach((item, index) => {
            if (item == selectedAxisId) {
              list.splice(index, 1);
            }
          });
        }
        list.push(selectedAxisId);
        this.$store.commit('setSelectedBarList', list);

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
          RequestService.queryLineagesData(filterParams)
              .then(
                  (res) => {
                    if (
                      res &&
                  res.data &&
                  res.data.object &&
                  res.data.object.length
                    ) {
                      const list = this.setDataOfModel(res.data.object);
                      const summaryDirList = list.map((i) => i.summary_dir);
                      this.$store.commit('setSummaryDirList', summaryDirList);

                      this.echart.showData = this.echart.brushData = list;
                      this.initChart();

                      this.table.data = this.echart.brushData.slice(
                          0,
                          this.pagination.pageSize,
                      );
                      this.pagination.currentPage = 1;
                      this.pagination.total = this.echart.brushData.length;
                      this.$refs.table.clearSelection();
                    } else {
                      this.summaryDirList = [];
                      this.$store.commit('setSummaryDirList', []);
                      this.checkedSummary = [];
                      this.noData = true;
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
      this.summaryDirList = undefined;
      this.$store.commit('setSummaryDirList', undefined);
      this.$store.commit('setSelectedBarList', []);
      this.noData = false;
      this.showTable = false;
      this.chartFilter = {};
      this.tableFilter.summary_dir = undefined;
      this.pagination.currentPage = 1;
      this.echart.allData = [];
      if (this.echart.chart) {
        this.echart.chart.clear();
      }
      this.init();
      this.$refs.table.clearSelection();
    },
    /**
     * Select all columns in the table.
     * @param {Boolean} value Select All
     */
    checkboxSelectAll(value) {
      this.table.optionalColumn.forEach((key) => {
        this.table.columnOptions[key].selected = value;
      });
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
     * Resizing Chart
     */
    resizeChart() {
      this.echart.chart.resize();
    },
  },
  destroyed() {
    if (this.checkedSummary.length) {
      const tempList = [];
      this.checkedSummary.forEach((item) => {
        tempList.push(item.summary_dir);
      });
      this.$store.commit('setSummaryDirList', tempList);
    }
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

    .top-area {
      margin: 24px 32px 12px;
      display: flex;
      justify-content: flex-end;
      .checkbox {
        overflow: auto;
        flex-grow: 1;
        .label-legend {
          height: 19px;
          margin-bottom: 4px;
          div {
            display: inline-block;
            font-size: 12px;
          }
          div + div {
            margin-left: 30px;
          }
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
      .btns {
        margin-left: 20px;
        padding-top: 12px;
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
      }
    }
    #echart {
      height: 39%;
    }
    .table-container {
      background-color: white;
      height: calc(60% - 74px);
      padding: 2px 32px;
      position: relative;
      .custom-label {
        max-width: calc(100% - 25px);
        padding: 0;
        vertical-align: middle;
      }
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

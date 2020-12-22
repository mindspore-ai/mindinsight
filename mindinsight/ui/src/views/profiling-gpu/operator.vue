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
  <div class="operator">
    <div class="operator-title">{{$t('profiling.operatorDetail')}}</div>
    <div class="cl-profiler">
      <el-tabs v-model="apiType"
               @tab-click="tabChange">
        <el-tab-pane :label="$t('operator.operatorInfo')"
                     name="operator">
          <div class="cl-profiler-top"
               :class="{fullScreen:fullScreen}"
               v-if="operatorCharts.data.length">
            <div>
              <div class="chart-title">{{$t('profiling.chartTitle')}}</div>
              <el-radio-group class="chart-radio-group"
                              v-model="operatorCharts.type"
                              @change="operatorChartChange"
                              fill="#00A5A7"
                              text-color="#FFFFFF"
                              size="small">
                <el-radio-button :label="0">
                  {{$t('operator.pie')}}
                </el-radio-button>
                <el-radio-button :label="1">
                  {{ $t('operator.bar')}}
                </el-radio-button>
              </el-radio-group>
            </div>
            <div class="cl-profiler-echarts">
              <div id="operator-echarts"></div>
            </div>
          </div>
          <div class="cl-profiler-bottom"
               :class="{fullScreen:fullScreen}"
               v-if="operatorCharts.data.length">
            <img src="../../assets/images/full-screen.png"
                 :title="$t('graph.fullScreen')"
                 class="fullScreen"
                 @click="fullScreenControl(0)">
            <div>
              <el-radio-group v-model="statisticType"
                              @change="operatorTableChange"
                              fill="#00A5A7"
                              text-color="#FFFFFF"
                              size="small">
                <el-radio-button :label="1">
                  {{$t('operator.allOperator')}}
                </el-radio-button>
                <el-radio-button :label="0">
                  {{$t('operator.classificationOperator')}}
                </el-radio-button>
              </el-radio-group>
              <div class="cl-search-box">
                <el-input v-model="searchByTypeInput"
                          v-if="!statisticType"
                          :placeholder="$t('operator.searchByType') +
                            $t('symbols.leftbracket') + $t('public.caseMode') + $t('symbols.rightbracket')"
                          clearable
                          @clear="searchOperatorList()"
                          @keyup.enter.native="searchOperatorList()"></el-input>
                <el-input v-model="searchByNameInput"
                          v-if="statisticType"
                          :placeholder="$t('operator.searchByName') +
                            $t('symbols.leftbracket') + $t('public.caseMode') + $t('symbols.rightbracket')"
                          clearable
                          @clear="searchOperatorList()"
                          @keyup.enter.native="searchOperatorList()"></el-input>
              </div>
            </div>
            <el-table v-show="!statisticType && opTypeCol && opTypeCol.length"
                      :data="opTypeList"
                      ref="expandTable"
                      @expand-change="expandTypeItem"
                      @sort-change="opTypeSortChange"
                      stripe
                      height="calc(100% - 40px)"
                      width="100%">
              <el-table-column type="expand">
                <template slot-scope="props">
                  <div class="expand-table">
                    <el-table :data="props.row.opDetailList"
                              stripe
                              ref="expandChild"
                              width="100%"
                              tooltip-effect="light"
                              @sort-change="(...args)=>{operatorDetailSortChange(props.row, ...args)}">
                      <el-table-column v-for="(ele, key) in props.row.opDetailCol"
                                       :property="ele"
                                       :key="key"
                                       :sortable="ele === 'op_info' ? false : 'custom'"
                                       :min-width="(ele === 'op_type') ? 100 : (ele === 'op_name') ?
                                       120 : (ele === 'op_full_name') ? 150 : '' "
                                       :show-overflow-tooltip="(ele === 'op_full_name'||ele === 'op_name'
                                       ||ele==='op_type') ? false : true">
                        <template slot="header">
                          <div class="custom-label"
                               :title="getHeaderField(ele)">
                            {{getHeaderField(ele)}}
                          </div>
                        </template>
                      </el-table-column>
                    </el-table>
                    <el-pagination :current-page="props.row.opDetailPage.offset + 1"
                                   :page-size="props.row.opDetailPage.limit"
                                   :page-sizes="[10, 20, 50]"
                                   @current-change="(...args)=>{opDetailPageChange(props.row, ...args)}"
                                   @size-change="(...args)=>{opDetailPageSizeChange(props.row, ...args)}"
                                   layout="total, sizes, prev, pager, next, jumper"
                                   :total="props.row.pageTotal">
                    </el-pagination>
                    <div class="clear"></div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column v-for="(item, $index) in opTypeCol"
                               :property="item"
                               :key="$index"
                               sortable>
                <template slot="header">
                  <div class="custom-label"
                       :title="getHeaderField(item)">
                    {{getHeaderField(item)}}
                  </div>
                </template>
              </el-table-column>
            </el-table>
            <el-table v-show="statisticType && opAllTypeList.opDetailCol && opAllTypeList.opDetailCol.length"
                      :data="opAllTypeList.opDetailList"
                      stripe
                      ref="opAllTable"
                      width="100%"
                      height="calc(100% - 80px)"
                      @sort-change="(...args)=>{operatorDetailSortChange(opAllTypeList, ...args)}"
                      tooltip-effect="light">
              <el-table-column v-for="(item, $index) in opAllTypeList.opDetailCol"
                               :property="item"
                               :key="$index"
                               :sortable="item === 'op_info' ? false : 'custom'"
                               :min-width="(item === 'op_type') ? 100 : (item === 'op_name')
                               ? 120 : (item === 'op_full_name') ? 150 : '' "
                               :show-overflow-tooltip="(item === 'op_full_name' || item === 'op_name'
                               || item === 'op_type') ? false : true">
                <template slot="header">
                  <div class="custom-label"
                       :title="getHeaderField(item)">
                    {{getHeaderField(item)}}
                  </div>
                </template>
              </el-table-column>
            </el-table>
            <el-pagination v-show="statisticType"
                           v-if="opAllTypeList.opDetailList.length"
                           :current-page="opAllTypeList.opDetailPage.offset + 1"
                           :page-size="opAllTypeList.opDetailPage.limit"
                           :page-sizes="[10, 20, 50]"
                           @current-change="(...args)=>{opDetailPageChange(opAllTypeList, ...args)}"
                           @size-change="(...args)=>{opDetailPageSizeChange(opAllTypeList, ...args)}"
                           layout="total, sizes, prev, pager, next, jumper"
                           :total="opAllTypeList.pageTotal">
            </el-pagination>
          </div>
          <div class="image-noData"
               v-if="operatorCharts.data.length === 0">
            <div>
              <img :src="require('@/assets/images/nodata.png')"
                   alt="" />
            </div>
            <p>{{ initOver?$t("public.noData"):$t('public.dataLoading') }}</p>
          </div>
        </el-tab-pane>
        <el-tab-pane :label="$t('operator.kernelInfo')"
                     class="core-tab"
                     name="core">
          <div class="cl-profiler-top"
               :class="{fullScreen:fullScreenKernel}"
               v-if="coreCharts.data.length">
            <div>
              <div class="chart-title">{{$t('profiling.chartTitle')}}</div>
            </div>
            <div class="cl-profiler-echarts">
              <div class
                   id="core-echarts"></div>
            </div>
          </div>
          <div class="cl-profiler-bottom"
               :class="{fullScreen:fullScreenKernel}"
               v-if="coreCharts.data.length">
            <img src="../../assets/images/full-screen.png"
                 :title="$t('graph.fullScreen')"
                 class="fullScreen"
                 @click="fullScreenControl(1)">
            <div>
              <div class="cl-search-box">
                <el-input v-model="searchByCoreInput"
                          :placeholder="(coreSearchType ?
                            $t('operator.searchByCoreFullName') :
                            $t('operator.searchByCoreName')) +
                            $t('symbols.leftbracket') + $t('public.caseMode') + $t('symbols.rightbracket')"
                          clearable
                          @clear="searchCoreList()"
                          @keyup.enter.native="searchCoreList()"></el-input>
              </div>
              <el-select v-model="coreSearchType"
                         class="core-search-type"
                         :placeholder="$t('public.select')"
                         @change="searchCoreList()">
                <el-option v-for="item in coreSearchOptions"
                           :key="item.value"
                           :label="item.label"
                           :value="item.value">
                </el-option>
              </el-select>
            </div>
            <el-table v-show="coreList.opDetailCol && coreList.opDetailCol.length"
                      :data="coreList.opDetailList"
                      stripe
                      ref="opCoreTable"
                      width="100%"
                      height="calc(100% - 80px)"
                      tooltip-effect="light"
                      @sort-change="(...args)=>{coreDetailSortChange(coreList, ...args)}">
              <el-table-column v-for="(item, $index) in coreList.opDetailCol"
                               :property="item"
                               :key="$index"
                               sortable="custom"
                               :min-width="(item === 'type') ? 100 : (item === 'name' || item === 'op_full_name')
                                ? 150 : '' "
                               :show-overflow-tooltip="(item === 'op_full_name' || item === 'name'
                               ||item === 'type') ? false : true">
                <template slot="header">
                  <div class="custom-label"
                       :title="getHeaderField(item)">
                    {{getHeaderField(item)}}
                  </div>
                </template>
              </el-table-column>
            </el-table>
            <el-pagination v-if="coreList.opDetailList.length"
                           :current-page="coreList.opDetailPage.offset + 1"
                           :page-size="coreList.opDetailPage.limit"
                           :page-sizes="[10, 20, 50]"
                           @current-change="opCorePageChange"
                           @size-change="opCorePageSizeChange"
                           layout="total, sizes, prev, pager, next, jumper"
                           :total="coreList.pageTotal">
            </el-pagination>
          </div>
          <div class="image-noData"
               v-if="coreCharts.data.length === 0">
            <div>
              <img :src="require('@/assets/images/nodata.png')"
                   alt="" />
            </div>
            <p>{{initOver?$t("public.noData"):$t('public.dataLoading')}}</p>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>
<script>
import echarts from 'echarts';
import requestService from '../../services/request-service';
import CommonProperty from '../../common/common-property';

export default {
  data() {
    return {
      apiType: 'operator',
      currentCard: '',
      coreCharts: {
        type: 0,
        id: 'core-echarts',
        chartDom: null,
        data: [],
      }, // core chart
      operatorCharts: {
        type: 0,
        id: 'operator-echarts',
        chartDom: null,
        data: [],
      }, // operator chart
      statisticType: 0, // operator table statistic type
      searchByTypeInput: '', // search by operator type
      searchByNameInput: '', // search by operator detail name
      searchByCoreInput: '', // search by core name
      opTypeCol: [], // table headers list of operator type
      opTypeList: [], // table list of operator type
      coreList: {
        opDetailCol: [],
        opDetailList: [],
        pageTotal: 0,
        opDetailPage: {
          offset: 0,
          limit: 10,
        },
        op_filter_condition: {},
        op_sort_condition: {
          name: 'avg_duration',
          type: 'descending',
        },
      }, // table data of core
      opAllTypeList: {
        opDetailCol: [],
        opDetailList: [],
        pageTotal: 0,
        opDetailPage: {
          offset: 0,
          limit: 10,
        },
        op_filter_condition: {},
        op_sort_condition: {},
      }, // table data of all operator details
      profile_dir: '', // profile directory
      train_id: '', // train id
      op_filter_condition: {}, // operator type filter
      op_sort_condition: {
        name: 'avg_time',
        type: 'descending',
      }, // operator type filter
      initOver: false,
      objectType: 'object',
      curActiveRow: {
        rowItem: null,
        childProp: null,
        childOrder: null,
      },
      fullScreen: false,
      fullScreenKernel: false,
      coreSearchOptions: [
        {
          value: 0,
          label: 'name',
        },
        {
          value: 1,
          label: 'op_full_name',
        },
      ],
      coreSearchType: 0,
    };
  },
  watch: {
    '$parent.curDashboardInfo': {
      handler(newValue, oldValue) {
        if (newValue.query.dir && newValue.query.id && newValue.curCardNum) {
          this.profile_dir = newValue.query.dir;
          this.train_id = newValue.query.id;
          this.currentCard = newValue.curCardNum;
          this.initOver = false;
          this.cardChange();
        }
        if (newValue.initOver) {
          this.initOver = true;
        }
      },
      deep: true,
      immediate: true,
    },
  },
  destroyed() {
    // Remove the listener of window size change
    window.removeEventListener('resize', this.resizeCallback);
    this.$bus.$off('collapse');

    if (this.operatorCharts.chartDom) {
      this.operatorCharts.chartDom.off('mouseover');
      this.operatorCharts.chartDom.off('mouseout');
    }
    if (this.coreCharts.chartDom) {
      this.coreCharts.chartDom.off('mouseover');
      this.coreCharts.chartDom.off('mouseout');
    }
  },
  methods: {
    getHeaderField(key) {
      const maps = {
        total_time: 'total_time (us)',
        avg_time: `avg_time (${this.$t('profiling.gpuunit')})`,
        op_total_time: 'op_total_time (us)',
        op_avg_time: `op_avg_time (${this.$t('profiling.gpuunit')})`,
        max_duration: 'max_duration (us)',
        min_duration: 'min_duration (us)',
        avg_duration: 'avg_duration (us)',
        total_duration: 'total_duration (us)',
        proportion: 'total_time_proportion (%)',
        cuda_activity_cost_time: 'cuda_activity_cost_time (us)',
        cuda_activity_call_count: `cuda_activity_call_count (${this.$t(
            'profiling.countUnit',
        )})`,
        type_occurrences: `type_occurrences (${this.$t(
            'profiling.countUnit',
        )})`,
        op_occurrences: `op_occurrences (${this.$t('profiling.countUnit')})`,
        occurrences: `occurrences (${this.$t('profiling.countUnit')})`,
      };
      return maps[key] ? maps[key] : key;
    },
    resizeEchart() {
      if (this.operatorCharts.chartDom) {
        setTimeout(() => {
          this.operatorCharts.chartDom.resize();
        }, 300);
      }
    },
    fullScreenControl(type) {
      if (!type) {
        this.fullScreen = !this.fullScreen;
        if (this.operatorCharts.chartDom && !this.fullScreen) {
          this.$nextTick(() => {
            this.operatorCharts.chartDom.resize();
          });
        }
      } else {
        this.fullScreenKernel = !this.fullScreenKernel;
        if (this.coreCharts.chartDom && !this.fullScreenKernel) {
          this.$nextTick(() => {
            this.coreCharts.chartDom.resize();
          });
        }
      }
    },
    /**
     * Current device change
     */
    cardChange() {
      if (this.apiType === 'operator') {
        this.statisticType = 0;
        this.clearOpData();
        this.getOpTypeList();
      } else if (this.apiType === 'core') {
        this.clearCoreData();
        this.getCoreList(true);
      }
    },
    /**
     * Operators type sort
     * @param {Object} sort Sort data
     */
    opTypeSortChange(sort) {
      this.op_sort_condition = {
        name: sort.prop,
        type: sort.order,
      };

      this.$nextTick(() => {
        const item = this.$refs['expandChild'];
        if (item && this.curActiveRow.rowItem) {
          item.sort(this.curActiveRow.childProp, this.curActiveRow.childOrder);
        }
      });
    },
    /**
     * Clear core data
     */
    clearCoreData() {
      this.searchByCoreInput = '';
      this.coreList = {
        opDetailCol: [],
        opDetailList: [],
        pageTotal: 0,
        opDetailPage: {
          offset: 0,
          limit: 10,
        },
        op_filter_condition: {},
        op_sort_condition: {
          name: 'avg_duration',
          type: 'descending',
        },
      };
    },
    /**
     * Clear operator data
     */
    clearOpData() {
      this.searchByTypeInput = '';
      this.searchByNameInput = '';
      this.op_filter_condition = {};
      this.op_sort_condition = {
        name: 'avg_time',
        type: 'descending',
      };
      this.opTypeCol = [];
      this.opTypeList = [];
      this.opAllTypeList = {
        opDetailCol: [],
        opDetailList: [],
        pageTotal: 0,
        opDetailPage: {
          offset: 0,
          limit: 10,
        },
        op_filter_condition: {},
        op_sort_condition: {},
      };
    },
    /**
     * Get operator type list
     */
    getOpTypeList() {
      const params = {};
      params.params = {
        profile: this.profile_dir,
        train_id: this.train_id,
      };
      params.body = {
        op_type: 'gpu_op_type',
        device_id: this.currentCard,
        filter_condition: this.op_filter_condition,
        sort_condition: this.op_sort_condition,
      };
      requestService
          .getProfilerOpData(params)
          .then((res) => {
            this.initOver = true;
            this.opTypeList = [];
            if (res && res.data) {
              this.opTypeCol = res.data.col_name;
              if (res.data.object) {
                res.data.object.forEach((k) => {
                  const object = {
                    isExpanded: false,
                    opDetailList: [],
                    opDetailCol: [],
                    opDetailPage: {
                      offset: 0,
                      limit: 10,
                    },
                    pageTotal: 0,
                    op_filter_condition: {
                      op_type: {
                        in: [k[0]],
                      },
                    },
                    op_sort_condition: {},
                  };
                  res.data.col_name.forEach((item, index) => {
                    object[item] = k[index];
                  });
                  this.opTypeList.push(object);
                });
                this.$nextTick(() => {
                  const elementItem = this.$refs['expandTable'];
                  if (elementItem) {
                    elementItem.sort(
                        this.op_sort_condition.name,
                        this.op_sort_condition.type,
                    );
                  }
                });
                if (
                  !this.operatorCharts.device_id ||
                this.operatorCharts.device_id !== this.currentCard
                ) {
                  this.operatorCharts.device_id = this.currentCard;
                  this.operatorCharts.data = [];
                  res.data.object.forEach((k) => {
                    if (
                      this.operatorCharts.data &&
                    this.operatorCharts.data.length < 19
                    ) {
                      this.operatorCharts.data.push({
                        name: k[0],
                        value: k[4],
                        percent: k[3],
                      });
                    } else {
                      if (!this.operatorCharts.data[19]) {
                        this.operatorCharts.data[19] = {
                          name: 'Other',
                          value: 0,
                          percent: 0,
                        };
                      }
                      this.operatorCharts.data[19].value += k[4];
                      this.operatorCharts.data[19].percent += k[3];
                    }
                  });
                  this.setOption(this.operatorCharts);
                }
              }
            }
          })
          .catch(() => {
            this.opTypeList = [];
            this.initOver = true;
          });
    },
    /**
     * Get operator detail list
     * @param {Object} row type row
     * @param {Boolean} isSort if sort
     */
    getOperatorDetailList(row, isSort) {
      const params = {};
      params.params = {
        profile: this.profile_dir,
        train_id: this.train_id,
      };
      params.body = {
        op_type: 'gpu_op_info',
        device_id: this.currentCard,
        filter_condition: row.op_filter_condition,
        sort_condition: row.op_sort_condition,
        group_condition: row.opDetailPage,
      };
      requestService
          .getProfilerOpData(params)
          .then((res) => {
            if (res && res.data) {
              this.formatterDetailData(row, res.data);
              this.$nextTick(() => {
                let item = null;
                if (this.statisticType) {
                  item = this.$refs['opAllTable'];
                } else {
                  item = this.$refs['expandChild'];
                  this.curActiveRow = {
                    rowItem: row,
                    childProp: row.op_sort_condition.name,
                    childOrder: row.op_sort_condition.type,
                  };
                }
                if (item && isSort) {
                  item.sort(
                      row.op_sort_condition.name,
                      row.op_sort_condition.type,
                  );
                }
                this.$refs.expandTable.doLayout();
              });
            }
          })
          .catch(() => {});
    },
    /**
     * Get core list
     * @param {Boolean} isSort if sort
     */
    getCoreList(isSort) {
      const params = {};
      params.params = {
        profile: this.profile_dir,
        train_id: this.train_id,
      };
      params.body = {
        op_type: 'gpu_cuda_activity',
        device_id: this.currentCard,
        filter_condition: this.coreList.op_filter_condition,
        sort_condition: this.coreList.op_sort_condition,
        group_condition: this.coreList.opDetailPage,
      };
      requestService
          .getProfilerOpData(params)
          .then((res) => {
            this.initOver = true;
            if (res && res.data) {
              if (res.data.object) {
                if (
                  !this.coreCharts.device_id ||
                this.coreCharts.device_id !== this.currentCard
                ) {
                  this.coreCharts.device_id = this.currentCard;
                  this.coreCharts.data = [];
                  res.data.object.forEach((k) => {
                    this.coreCharts.data.push({
                      name: k[0],
                      op_name: k[2],
                      value: k[8],
                    });
                  });
                  this.setOption(this.coreCharts);
                }
                this.formatterDetailData(this.coreList, res.data);
                if (isSort) {
                  this.$nextTick(() => {
                    const item = this.$refs['opCoreTable'];
                    if (item) {
                      item.sort(
                          this.coreList.op_sort_condition.name,
                          this.coreList.op_sort_condition.type,
                      );
                    }
                  });
                }
              }
            }
          })
          .catch(() => {
            this.initOver = true;
          });
    },
    /**
     * Operator detail list page change
     * @param {Object} row table cell
     * @param {Number} pageIndex current page
     */
    opDetailPageChange(row, pageIndex) {
      row.opDetailPage.offset = pageIndex - 1;
      this.getOperatorDetailList(row, false);
    },
    /**
     * Operator detail list page size change
     * @param {Object} row table cell
     * @param {Number} pageSize current page
     */
    opDetailPageSizeChange(row, pageSize) {
      row.opDetailPage.offset = 0;
      row.opDetailPage.limit = pageSize;
      this.getOperatorDetailList(row, false);
    },
    /**
     * Core list page change
     * @param {Number} pageIndex current page
     */
    opCorePageChange(pageIndex) {
      this.coreList.opDetailPage.offset = pageIndex - 1;
      this.getCoreList(false);
    },
    /**
     * Core list page size change
     * @param {Number} pageSize current page size
     */
    opCorePageSizeChange(pageSize) {
      this.coreList.opDetailPage.offset = 0;
      this.coreList.opDetailPage.limit = pageSize;
      this.getCoreList(false);
    },
    /**
     * Get operator list by search
     */
    searchOperatorList() {
      if (this.statisticType) {
        this.opAllTypeList.op_filter_condition = {};
        if (this.searchByNameInput) {
          this.opAllTypeList.op_filter_condition = {
            op_name: {partial_match_str_in: [this.searchByNameInput]},
          };
        } else {
          this.opAllTypeList.op_filter_condition = {};
        }
        this.opAllTypeList.opDetailPage.offset = 0;
        this.getOperatorDetailList(this.opAllTypeList, false);
      } else {
        this.op_filter_condition = {};
        if (this.searchByTypeInput) {
          this.op_filter_condition = {
            op_type: {partial_match_str_in: [this.searchByTypeInput]},
          };
        } else {
          this.op_filter_condition = {};
        }
        if (this.curActiveRow.rowItem) {
          this.curActiveRow = {
            rowItem: null,
            childProp: null,
            childOrder: null,
          };
        }
        this.getOpTypeList();
      }
    },
    /**
     * Get core list by search
     */
    searchCoreList() {
      this.coreList.op_filter_condition = {};
      if (this.searchByCoreInput) {
        if (this.coreSearchType) {
          this.coreList.op_filter_condition = {
            op_full_name: {partial_match_str_in: [this.searchByCoreInput]},
          };
        } else {
          this.coreList.op_filter_condition = {
            name: {partial_match_str_in: [this.searchByCoreInput]},
          };
        }
      } else {
        this.coreList.op_filter_condition = {};
      }
      this.coreList.opDetailPage.offset = 0;
      this.getCoreList(false);
    },
    /**
     * Operator detail sort
     * @param {Object} row table cell
     * @param {Object} column table cell
     */
    operatorDetailSortChange(row, column) {
      row.op_sort_condition = {
        name: column.prop,
        type: column.order,
      };
      row.opDetailPage.offset = 0;
      this.getOperatorDetailList(row, false);
    },
    /**
     * Core detail sort
     * @param {Object} row table cell
     * @param {Object} column table cell
     */
    coreDetailSortChange(row, column) {
      row.op_sort_condition = {
        name: column.prop,
        type: column.order,
      };
      row.opDetailPage.offset = 0;
      this.getCoreList(false);
    },
    /**
     * Format detail data
     * @param {Object} row table cell
     * @param {Object} detailsDataList table detail
     */
    formatterDetailData(row, detailsDataList) {
      row.opDetailList = [];
      row.opDetailCol = detailsDataList.col_name;
      row.pageTotal = detailsDataList.size;
      if (detailsDataList.object) {
        detailsDataList.object.forEach((k) => {
          const data = {};
          detailsDataList.col_name.forEach((item, index) => {
            if (item === 'op_info') {
              data[item] = JSON.stringify(k[index]);
            } else {
              data[item] = k[index];
            }
          });
          row.opDetailList.push(data);
        });
      }
    },
    /**
     * Expand operator type table
     * @param {Object} row table cell
     */
    expandTypeItem(row) {
      row.isExpanded = !row.isExpanded;
      if (row.isExpanded) {
        if (this.curActiveRow.rowItem) {
          const item = this.$refs['expandTable'];
          if (item) {
            item.toggleRowExpansion(this.curActiveRow.rowItem, false);
          }
        }
        this.curActiveRow = {
          rowItem: row,
          childProp: null,
          childOrder: null,
        };
        row.opDetailList = [];
        row.opDetailCol = [];
        row.opDetailPage.offset = 0;
        row.pageTotal = 0;
        row.op_sort_condition = {
          name: 'op_avg_time',
          type: 'descending',
        };
        this.getOperatorDetailList(row, true);
      } else {
        this.curActiveRow = {
          rowItem: null,
          childProp: null,
          childOrder: null,
        };
      }
    },
    /**
     * Tab change
     */
    tabChange() {
      if (
        this.apiType === 'core' &&
        this.coreCharts.device_id !== this.currentCard
      ) {
        this.initOver = false;
        this.clearCoreData();
        this.getCoreList(true);
      } else if (
        this.apiType === 'operator' &&
        this.operatorCharts.device_id !== this.currentCard
      ) {
        this.initOver = false;
        this.clearOpData();
        this.getOpTypeList();
      }
      this.$nextTick(() => {
        this.resizeCallback();
      });
    },
    /**
     * Operator table type change
     */
    operatorTableChange() {
      if (this.statisticType && !this.opAllTypeList.opDetailCol.length) {
        this.opAllTypeList.op_sort_condition = {
          name: 'op_avg_time',
          type: 'descending',
        };
        this.getOperatorDetailList(this.opAllTypeList, true);
      }
    },
    /**
     * Core chart change
     */
    coreChartChange() {
      this.setOption(this.coreCharts);
    },
    /**
     * Operator chart change
     */
    operatorChartChange() {
      this.setOption(this.operatorCharts);
    },
    /**
     * Set chart option
     * @param {Object} chart chart
     */
    setOption(chart) {
      const option = {};
      const maxLabelLength = 20;
      const maxTooltipLen = 50;

      if (!chart.type) {
        option.legend = {
          data: [],
          orient: 'vertical',
          icon: 'circle',
          formatter: (params) => {
            let legendStr = '';
            for (let i = 0; i < chart.data.length; i++) {
              if (chart.data[i].name === params) {
                const name =
                  chart.data[i].name.length > 10
                    ? `${chart.data[i].name.slice(0, 10)}...`
                    : chart.data[i].name;
                legendStr = `{a|${i + 1}}{b|${name}  ${chart.data[
                    i
                ].value.toFixed(3)}}\n{c|}`;
              }
            }
            return legendStr;
          },
          tooltip: {
            show: true,
            formatter: (params) => {
              let name = params.name;
              name = name.replace(/</g, '< ');

              const breakCount = Math.ceil(name.length / maxTooltipLen);
              let str = '';
              for (let i = 0; i < breakCount; i++) {
                const temp = name.substr(i * maxTooltipLen, maxTooltipLen);
                str += str ? '<br/>' + temp : temp;
              }
              return str;
            },
          },
          itemWidth: 18,
          itemHeight: 18,
          padding: [0, 50, 0, 0],
          top: '5%',
          left: '45%',
          textStyle: {
            padding: [15, 0, 0, 0],
            rich: {
              a: {
                width: 24,
                align: 'center',
                padding: [0, 10, 3, -26],
                color: '#FFF',
              },
              b: {
                padding: [0, 0, 3, 0],
              },
              c: {
                width: '100%',
                padding: [0, 0, 5, 10],
                color: '#9EA4B3',
                fontSize: 12,
              },
            },
          },
        };
        option.tooltip = {
          trigger: 'item',
          formatter: (params) => {
            const name = params.data.name.replace(/</g, '< ');
            const strTemp = `${name} ${params.percent.toFixed(2) + '%'}`;

            const breakCount = Math.ceil(strTemp.length / maxTooltipLen);
            let str = '';
            for (let i = 0; i < breakCount; i++) {
              const temp = strTemp.substr(i * maxTooltipLen, maxTooltipLen);
              str += str ? '<br/>' + temp : temp;
            }
            return str;
          },
          confine: true,
        };
        option.series = [
          {
            type: 'pie',
            center: ['23%', '60%'],
            data: chart.data,
            radius: '50%',
            label: {
              position: 'outer',
              alignTo: 'labelLine',
              formatter: (params) => {
                return params.data.name &&
                  params.data.name.length > maxLabelLength
                  ? `${params.data.name.slice(0, maxLabelLength)}...`
                  : params.data.name;
              },
            },
            itemStyle: {
              normal: {
                color: function(params) {
                  return CommonProperty.pieColorArr[params.dataIndex];
                },
              },
            },
          },
        ];
        chart.data.forEach((item) => {
          option.legend.data.push(item.name);
        });
      } else if (chart.type) {
        option.color = ['#6C92FA'];
        option.tooltip = {
          trigger: 'axis',
          formatter: (params) => {
            return `${params[0].axisValue}<br>${params[0].marker}${params[0].value}`;
          },
          confine: true,
        };
        option.series = [
          {
            type: 'bar',
            barWidth: 30,
            data: [],
          },
        ];
        option.xAxis = {
          type: 'category',
          axisLabel: {
            interval: 0,
            rotate: -30,
          },
          data: [],
          triggerEvent: true,
        };
        option.grid = {
          left: 70,
          top: 20,
          right: 0,
          bottom: 50,
        };
        option.yAxis = {
          type: 'value',
          axisLabel: {
            formatter: (value) => {
              const yValueArr = [];
              if (value < 1000000) {
                yValueArr.push(value.toLocaleString());
              } else {
                yValueArr.push(value.toExponential());
              }
              return yValueArr;
            },
          },
        };
        chart.data.forEach((item) => {
          const name = this.apiType === 'core' ? item.op_name : item.name;
          option.xAxis.data.push(name);
          option.series[0].data.push(item.value);
        });
        if (this.apiType === 'core') {
          option.xAxis.axisLabel.formatter = (params, dataIndex) => {
            const xAxisValue = chart.data[dataIndex].op_name;
            return xAxisValue.replace(/^.+\//g, '');
          };
        }
      }
      this.$nextTick(() => {
        const tmpDom = document.getElementById(chart.id);
        if (tmpDom) {
          chart.chartDom = echarts.init(tmpDom, null);
        } else {
          if (chart.chartDom) {
            chart.chartDom.off('mouseover');
            chart.chartDom.off('mouseout');
            chart.chartDom.clear();
          }
          return;
        }
        chart.chartDom.setOption(option, true);
        if (chart.type) {
          chart.chartDom.off('mouseover');
          chart.chartDom.off('mouseout');
          chart.chartDom.on('mouseover', (params) => {
            if (params.componentType === 'xAxis') {
              const offsetX = params.event.offsetX + 10;
              const offsetY = params.event.offsetY + 10;
              chart.chartDom.setOption({
                tooltip: {
                  formatter: params.value,
                  alwaysShowContent: true,
                },
              });
              chart.chartDom.dispatchAction({
                type: 'showTip',
                seriesIndex: 0,
                dataIndex: 0,
                position: [offsetX, offsetY],
              });
            }
          });

          chart.chartDom.on('mouseout', (params) => {
            if (params.componentType === 'xAxis') {
              chart.chartDom.setOption({
                tooltip: {
                  formatter: '',
                  alwaysShowContent: false,
                },
              });
            }
          });
        }
        chart.chartDom.resize();
      }, 10);
    },
    loadDataListChildren(tree, treeNode, resolve) {
      setTimeout(() => {
        resolve(tree.children);
      });
    },
    /**
     * Window resize
     */
    resizeCallback() {
      if (this.operatorCharts.chartDom && this.apiType === 'operator') {
        this.operatorCharts.chartDom.resize();
      }
      if (this.coreCharts.chartDom && this.apiType === 'core') {
        this.coreCharts.chartDom.resize();
      }
    },
  },
  mounted() {
    if (this.train_id) {
      document.title = `${decodeURIComponent(this.train_id)}-${this.$t(
          'profiling.operatorDetail',
      )}-MindInsight`;
    } else {
      document.title = `${this.$t('profiling.operatorDetail')}-MindInsight`;
    }
    window.addEventListener('resize', this.resizeCallback, false);
    setTimeout(() => {
      this.$bus.$on('collapse', this.resizeEchart);
    }, 500);
  },
};
</script>
<style lang="scss">
.operator {
  height: 100%;
  .clear {
    clear: both;
  }
  .el-tabs__item {
    color: #6c7280;
    line-height: 36px;
    height: 36px;
  }
  .el-tabs__item.is-active {
    color: #00a5a7;
    font-weight: bold;
  }
  .operator-title {
    padding: 0 15px;
    font-size: 16px;
    font-weight: bold;
  }
  .cl-profiler {
    height: calc(100% - 21px);
    overflow-y: auto;
    width: 100%;
    background: #fff;
    padding: 0 16px;
    overflow: hidden;
    .custom-label {
      max-width: calc(100% - 25px);
      padding: 0;
      vertical-align: middle;
    }
    .el-tabs {
      height: 100%;
      .el-tabs__header {
        margin-bottom: 10px;
      }
    }
    .el-tabs__content {
      height: calc(100% - 46px);
    }
    .el-tab-pane {
      height: 100%;
    }
    .cl-search-box {
      float: right;
      margin-bottom: 10px;
      margin-right: 20px;
      .el-input {
        width: 300px;
      }
    }
    .cl-profiler-top {
      height: 47%;
      .chart-title {
        float: left;
        font-weight: bold;
        height: 32px;
      }
    }
    .cl-profiler-top.fullScreen {
      display: none;
    }
    .cl-profiler-bottom {
      height: 53%;
      padding-top: 10px;
      .fullScreen {
        float: right;
        margin-top: 5px;
        cursor: pointer;
      }
    }
    .cl-profiler-bottom.fullScreen {
      height: 100%;
    }
    .core-search-type {
      float: right;
      width: 130px;
      margin-right: 10px;
    }
    .cl-profiler-echarts {
      width: 100%;
      height: calc(100% - 32px);
      display: inline-block;
      position: relative;
      overflow: auto;
      #core-echarts,
      #operator-echarts {
        width: 100%;
        height: 100%;
        min-width: 1300px;
        min-height: 321px;
        overflow: hidden;
      }
    }
    .core-tab {
      .cl-profiler-top {
        height: 47%;
      }
      .cl-profiler-bottom {
        height: 53%;
      }
      .cl-profiler-echarts {
        height: calc(100% - 32px);
      }
      .cl-profiler-bottom.fullScreen {
        height: 100%;
      }
    }
    .chart-radio-group {
      float: right;
    }
    .el-radio-group {
      .el-radio-button--small .el-radio-button__inner {
        height: 30px;
        width: 70px;
        font-size: 14px;
        line-height: 10px;
      }
    }
    .cl-profiler-bar {
      display: inline-block;
      width: calc(100% - 400px);
      vertical-align: top;
      height: 100%;
      padding: 20px;
    }
    .cl-profiler-table-type {
      display: inline-block;
      width: calc(100% - 400px);
      vertical-align: top;
      height: 100%;
    }
    .el-pagination {
      margin: 7px 0;
      float: right;
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
          width: 42px;
          background: #f0fdfd;
          border-right: 2px #00a5a7 solid;
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
    }
    .el-table__expanded-cell[class*='cell'] {
      padding: 0;
    }
    .expand-table {
      position: relative;
      padding-left: 44px;
    }
    .expand-table::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      height: 100%;
      background: #f0fdfd;
      width: 42px;
      border-right: 2px #00a5a7 solid;
    }
    .el-radio-button:last-child .el-radio-button__inner,
    .el-radio-button:first-child .el-radio-button__inner {
      border-radius: 0;
    }
    .image-noData {
      width: 100%;
      height: 100%;
      display: flex;
      justify-content: center;
      align-items: center;
      flex-direction: column;
      p {
        font-size: 16px;
        padding-top: 10px;
      }
    }
  }
}
</style>

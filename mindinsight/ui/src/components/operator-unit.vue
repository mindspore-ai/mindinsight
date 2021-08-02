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
  <div class="cl-profiler-wrap">
    <div class="flops-info"
         v-if="hasFlopsInfo">
      <span :title="$t('operator.flops')">
        FLOPs{{$t('symbols.colon')}}{{flops.FLOPs===undefined?'--':flops.FLOPs}}M
      </span>
      <span :title="$t('operator.flopsS')">
        FLOPS{{$t('symbols.colon')}}{{flops.FLOPS===undefined?'--':flops.FLOPS}}G/{{$t('header.timeSecond')}}
      </span>
      <span :title="$t('operator.flopsUtilizationTitle')">
        {{$t('operator.flopsUtilization')}}{{flops.FLOPS_Utilization===undefined?'--':flops.FLOPS_Utilization}}%
      </span>
      <div class="view-detail">
        <button @click="showFlopsDetails"
                :disabled="Object.keys(flops).length===0"
                :class="{disabled:Object.keys(flops).length===0}">{{ $t('profiling.viewDetail') }}
          <i class="el-icon-d-arrow-right"></i></button>
      </div>
    </div>
    <div class="cl-profiler-top"
         :class="{fullScreen:coreFullScreen}"
         v-if="coreCharts.data.length">
      <div>
        <div class="chart-title">{{$t('profiling.chartTitle')}}({{unit}})</div>
        <el-radio-group class="chart-radio-group"
                        v-model="coreCharts.type"
                        @change="coreChartChange"
                        fill="#00A5A7"
                        text-color="#FFFFFF"
                        size="small"
                        v-if="hasBarChart">
          <el-radio-button :label="0">
            {{$t('operator.pie')}}
          </el-radio-button>
          <el-radio-button :label="1">
            {{ $t('operator.bar')}}
          </el-radio-button>
        </el-radio-group>
      </div>
      <div class="cl-profiler-echarts">
        <div :id="chartId"
             class="chart"></div>
      </div>
    </div>
    <div class="cl-profiler-bottom"
         :class="{fullScreen:coreFullScreen,flops:hasFlopsInfo}"
         v-if="coreCharts.data.length">
      <img src="../assets/images/full-screen.png"
           :title="$t('graph.fullScreen')"
           class="fullScreen"
           @click="fullScreenControl">
      <div>
        <el-radio-group v-model="coreStatisticType"
                        @change="coreTableChange"
                        fill="#00A5A7"
                        text-color="#FFFFFF"
                        size="small"
                        v-if="hasBarChart">
          <el-radio-button :label="1">
            {{$t('operator.allOperator')}}
          </el-radio-button>
          <el-radio-button :label="0">
            {{$t('operator.classificationOperator')}}
          </el-radio-button>
        </el-radio-group>
        <div class="cl-search-box">
          <el-input v-model="searchByTypeInput"
                    v-if="!coreStatisticType && hasBarChart"
                    :placeholder="search.all.label"
                    clearable
                    @clear="searchOpCoreList"
                    @keyup.enter.native="searchOpCoreList"></el-input>
          <el-input v-model="searchByNameInput"
                    v-if="coreStatisticType && hasBarChart"
                    :placeholder="search.detail.label"
                    clearable
                    @clear="searchOpCoreList"
                    @keyup.enter.native="searchOpCoreList"></el-input>
          <el-input v-model="searchByNameInput"
                    v-if="!hasBarChart"
                    :placeholder="searchPlaceholder"
                    clearable
                    @clear="searchOpCoreList"
                    @keyup.enter.native="searchOpCoreList"></el-input>
        </div>
        <el-select v-if="!hasBarChart"
                   v-model="searchType"
                   class="core-search-type"
                   :placeholder="$t('public.select')"
                   @change="searchTypeChange">
          <el-option v-for="item in coreSearchOptions"
                     :key="item.value"
                     :label="item.label"
                     :value="item.value">
          </el-option>
        </el-select>
      </div>
      <el-table v-show="!coreStatisticType && opTypeCol && opTypeCol.length"
                :data="opTypeList"
                ref="expandTable"
                @expand-change="expandCoreTypeItem"
                @sort-change="opTypeSortChange"
                stripe
                height="calc(100% - 40px)"
                width="100%">
        <el-table-column type="expand">
          <template slot-scope="props">
            <div class="expand-table">
              <el-table :data="props.row.opDetailList"
                        stripe
                        ref="expandCoreChild"
                        width="100%"
                        tooltip-effect="light"
                        @cell-click="showInfoDetail"
                        @sort-change="(...args)=>{coreDetailSortChange(props.row, ...args)}">
                <el-table-column v-for="(ele, key) in props.row.opDetailCol"
                                 :property="ele"
                                 :key="key"
                                 :sortable="ele === 'op_info' ? false : 'custom'"
                                 :min-width="(ele === 'op_info') ? 350 : (ele === 'full_op_name') ? 220 : ''"
                                 :show-overflow-tooltip="(ele === 'avg_execution_time')">
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
      <el-table v-show="coreStatisticType && opAllTypeList.opDetailCol && opAllTypeList.opDetailCol.length"
                :data="opAllTypeList.opDetailList"
                stripe
                ref="opAllTable"
                width="100%"
                height="calc(100% - 80px)"
                @cell-click="showInfoDetail"
                @sort-change="(...args)=>{coreDetailSortChange(opAllTypeList, ...args)}"
                tooltip-effect="light">
        <el-table-column v-for="(item, $index) in opAllTypeList.opDetailCol"
                         :property="item"
                         :key="$index"
                         :sortable="item === 'op_info' ? false : 'custom'"
                         :min-width="(item === 'op_info') ? 350 : (item === 'full_op_name') ? 220 : ''"
                         :show-overflow-tooltip="(item === 'avg_execution_time')">
          <template slot="header">
            <div class="custom-label"
                 :title="getHeaderField(item)">
              {{getHeaderField(item)}}
            </div>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination v-show="coreStatisticType"
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
         v-if="coreCharts.data.length === 0">
      <div>
        <img :src="require('@/assets/images/nodata.png')"
             alt="" />
      </div>
      <p>{{ initOver?$t("public.noData"):$t('public.dataLoading') }}</p>
    </div>
    <el-dialog :title="rowName"
               :visible.sync="detailsDialogVisible"
               width="50%"
               :close-on-click-modal="false"
               class="details-data-list">
      <el-table :data="detailsDataList"
                row-key="id"
                lazy
                tooltip-effect="light"
                :load="loadDataListChildren"
                :tree-props="{ children: 'children', hasChildren: 'hasChildren' }">
        <el-table-column width="50" />
        <el-table-column prop="key"
                         width="180"
                         label="Key"> </el-table-column>
        <el-table-column prop="value"
                         show-overflow-tooltip
                         label="Value">
          <template slot-scope="scope">
            {{ scope.row.value }}
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
    <el-dialog :title="$t('operator.scopeLevelFlops')"
               :visible.sync="flopsDialogVisible"
               width="70%"
               :close-on-click-modal="false"
               class="flops-data-list">
      <div id="flopsChart"
           v-if="flopsHasData"
           :style="{width:`${flopsChartWidth}px`,height:`${flopsChartHeight}px`}"></div>
      <div class="image-noData"
           v-else>
        <div>
          <img :src="require('@/assets/images/nodata.png')"
               alt="" />
        </div>
        <p>{{ flopsInit?$t("public.noData"):$t('public.dataLoading') }}</p>
      </div>
    </el-dialog>
  </div>
</template>
<script>
import echarts, {echartsThemeName} from '../js/echarts';
import requestService from '../services/request-service';
import CommonProperty from '../common/common-property';

export default {
  props: {
    chartId: {
      type: String,
      default: '',
    },
    currentCard: {
      type: String,
      default: '',
    },
    opType: {
      type: Object,
      default: () => {
        return {
          all: '',
          detail: '',
        };
      },
    },
    opSortCondition: {
      type: Object,
      default: () => {
        return {
          all: {
            name: '',
            type: '',
          },
          detail: {
            name: '',
            type: '',
          },
        };
      },
    },
    headerFilder: {
      type: Object,
      default: () => {
        return {};
      },
    },
    search: {
      type: Object,
      default: () => {
        return {
          all: {
            label: '',
            type: '',
          },
          detail: {
            label: '',
            type: '',
          },
        };
      },
    },
    chart: {
      type: Object,
      default: () => {
        return {
          value: 1,
          percent: 3,
        };
      },
    },
    hasBarChart: {
      type: Boolean,
      default: true,
    },
    coreSearchType: {
      type: String,
      default: '',
    },
    coreSearchOptions: {
      type: Array,
      default: () => {
        return [
          {label: '', value: '', placeHolder: ''},
          {label: '', value: '', placeHolder: ''},
        ];
      },
    },
    accuracy: {
      type: Number,
      default: 3,
    },
    unit: {
      type: String,
      default: '',
    },
    hasFlopsInfo: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      coreCharts: {
        type: 0,
        id: this.chartId,
        chartDom: null,
        data: [],
      }, // ai core chart
      coreStatisticType: this.hasBarChart ? 0 : 1, // ai core table statistic type
      searchByTypeInput: '', // search by ai core type name
      searchByNameInput: '', // search by ai core detail name
      opTypeCol: [], // table headers list of operator type
      opTypeList: [], // table list of operator type
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
      rowName: this.$t('dataTraceback.details'), // dialog title
      detailsDataList: [], // dialog table data
      detailsDialogVisible: false, // show dialog
      profile_dir: this.$route.query.dir, // profile directory
      train_id: this.$route.query.id, // train id
      op_filter_condition: {}, // operator type filter
      op_sort_condition: this.opSortCondition.all, // operator type filter
      initOver: false,
      objectType: 'object',
      curActiveRow: {
        rowItem: null,
        childProp: null,
        childOrder: null,
      },
      coreFullScreen: false,
      searchPlaceholder: this.coreSearchOptions[0].placeHolder,
      searchType: this.coreSearchType,
      flops: {},
      flopsDialogVisible: false,
      flopsChartDom: null,
      flopsChartWidth: 800,
      flopsChartHeight: 540,
      flopsHasData: false,
      flopsInit: false,
    };
  },
  destroyed() {
    // Remove the listener of window size change
    window.removeEventListener('resize', this.resizeCallback);
    this.$bus.$off('collapse');
    if (this.coreCharts.chartDom) {
      this.coreCharts.chartDom.off('mouseover');
      this.coreCharts.chartDom.off('mouseout');
    }
  },
  methods: {
    showFlopsDetails() {
      this.flopsDialogVisible = true;
      this.flopsInit = false;
      const params = {
        train_id: this.train_id,
        device_id: this.currentCard,
      };
      requestService.getFlopsScope(params).then(
          (res) => {
            this.flopsInit = true;
            if (res.data.data && res.data.max_scope_num) {
              const nodes = res.data.data.nodes || [];
              const links = res.data.data.links || [];
              this.flopsHasData = nodes.length ? true : false;
              const maxScopeNum = res.data.max_scope_num;
              let maxNodeNum = 0;
              nodes.forEach((value) => {
                if (!links.find((val) => val.source === value.name)) {
                  maxNodeNum++;
                }
              });
              this.flopsChartWidth = 150 * maxScopeNum;
              this.flopsChartHeight = 25 * maxNodeNum;
              this.$nextTick(() => {
                if (!this.flopsChartDom) {
                  this.flopsChartDom = echarts.init(document.querySelector('#flopsChart'), echartsThemeName);
                }
                this.flopsChartDom.setOption({
                  title: {
                    text: 'Sankey Diagram',
                  },
                  tooltip: {
                    trigger: 'item',
                    triggerOn: 'mousemove',
                    confine: true,
                  },
                  itemStyle: {
                    borderWidth: 1,
                  },
                  label: {
                    width: 100,
                    overflow: 'truncate',
                    ellipsis: '...',
                    color: CommonProperty.modelTracebackChartTheme[this.$store.state.themeIndex].batchSizeTextColor,
                  },
                  series: [
                    {
                      type: 'sankey',
                      data: nodes,
                      links: links,
                      emphasis: {
                        focus: 'adjacency',
                      },
                      nodeGap: 10,
                      left: 0,
                      right: 110,
                      top: 30,
                      bottom: 30,
                      lineStyle: {
                        curveness: 0.5,
                        color: CommonProperty.commonChartTheme[this.$store.state.themeIndex].lineStyleColor,
                      },
                    },
                  ],
                });
              });
            } else {
              this.flopsHasData = false;
            }
          },
          () => {
            this.flopsInit = true;
            this.flopsHasData = false;
          },
      );
    },
    getFlopsSummary() {
      const params = {
        train_id: this.train_id,
        device_id: this.currentCard,
      };
      requestService.getFlopsSummary(params).then((res) => {
        if (res && res.data) {
          this.flops = res.data;
        }
      });
    },
    searchTypeChange() {
      this.coreSearchOptions.forEach((val) => {
        if (val.label === this.searchType) {
          this.searchPlaceholder = val.placeHolder;
        }
      });
      this.searchOpCoreList();
    },
    getHeaderField(key) {
      return this.headerFilder[key] ? this.headerFilder[key] : key;
    },
    resizeEchart() {
      if (this.coreCharts.chartDom) {
        setTimeout(() => {
          this.coreCharts.chartDom.resize();
        }, 300);
      }
    },
    fullScreenControl() {
      this.coreFullScreen = !this.coreFullScreen;
      if (this.coreCharts.chartDom && !this.coreFullScreen) {
        this.$nextTick(() => {
          this.coreCharts.chartDom.resize();
        });
      }
    },
    /**
     * Operators core type sort
     * @param {Object} sort Sort data
     */
    opTypeSortChange(sort) {
      this.op_sort_condition = {
        name: sort.prop,
        type: sort.order,
      };
      this.$nextTick(() => {
        const item = this.$refs['expandCoreChild'];
        if (item && this.curActiveRow.rowItem) {
          item.sort(this.curActiveRow.childProp, this.curActiveRow.childOrder);
        }
      });
    },
    /**
     * Clear core data
     */
    clearCoreData() {
      this.searchByTypeInput = '';
      this.searchByNameInput = '';
      this.op_filter_condition = {};
      this.op_sort_condition = this.opSortCondition.all;
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
     * Get core type list
     */
    getCoreTypeList() {
      const params = {};
      params.params = {
        profile: this.profile_dir,
        train_id: this.train_id,
      };
      params.body = {
        op_type: this.opType.all,
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
                    elementItem.sort(this.op_sort_condition.name, this.op_sort_condition.type);
                  }
                });
                if (!this.coreCharts.device_id || this.coreCharts.device_id !== this.currentCard) {
                  this.coreCharts.device_id = this.currentCard;
                  this.coreCharts.data = [];
                  res.data.object.forEach((k) => {
                    if (this.coreCharts.data.length < 19) {
                      this.coreCharts.data.push({
                        name: k[0],
                        value: k[this.chart.value],
                        percent: k[this.chart.percent],
                      });
                    } else {
                      if (!this.coreCharts.data[19]) {
                        this.coreCharts.data[19] = {
                          name: 'Other',
                          value: 0,
                          percent: 0,
                        };
                      }
                      this.coreCharts.data[19].value += k[this.chart.value];
                      this.coreCharts.data[19].percent += k[this.chart.percent];
                    }
                  });
                  this.setOption(this.coreCharts);
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
     * Get core detail list
     * @param {Object} row type row
     * @param {Boolean} isSort if sort
     */
    getCoreDetailList(row, isSort) {
      const params = {};
      params.params = {
        profile: this.profile_dir,
        train_id: this.train_id,
      };
      params.body = {
        op_type: this.opType.detail,
        device_id: this.currentCard,
        filter_condition: row.op_filter_condition,
        sort_condition: row.op_sort_condition,
        group_condition: row.opDetailPage,
      };
      requestService.getProfilerOpData(params).then((res) => {
        if (res && res.data) {
          this.formatterDetailData(row, res.data);
          this.$nextTick(() => {
            let item = null;
            if (this.coreStatisticType) {
              item = this.$refs['opAllTable'];
            } else {
              item = this.$refs['expandCoreChild'];
              this.curActiveRow = {
                rowItem: row,
                childProp: row.op_sort_condition.name,
                childOrder: row.op_sort_condition.type,
              };
            }
            if (item && isSort) {
              item.sort(row.op_sort_condition.name, row.op_sort_condition.type);
            }
            if (this.$refs.expandTable) {
              this.$refs.expandTable.doLayout();
            }
          });
        }
      });
    },
    /**
     * Operator detail list page change
     * @param {Object} row table cell
     * @param {Number} pageIndex current page
     */
    opDetailPageChange(row, pageIndex) {
      row.opDetailPage.offset = pageIndex - 1;
      this.getCoreDetailList(row, false);
    },
    /**
     * Operator detail list page size change
     * @param {Object} row table cell
     * @param {Number} pageSize current page size
     */
    opDetailPageSizeChange(row, pageSize) {
      row.opDetailPage.offset = 0;
      row.opDetailPage.limit = pageSize;
      this.getCoreDetailList(row, false);
    },
    /**
     * Get core list by search
     */
    searchOpCoreList() {
      if (this.coreStatisticType) {
        this.opAllTypeList.op_filter_condition = {};
        if (this.searchByNameInput) {
          if (!this.hasBarChart) {
            this.opAllTypeList.op_filter_condition[this.searchType] = {
              partial_match_str_in: [this.searchByNameInput],
            };
          } else {
            this.opAllTypeList.op_filter_condition[this.search.detail.type] = {
              partial_match_str_in: [this.searchByNameInput],
            };
          }
        } else {
          this.opAllTypeList.op_filter_condition = {};
        }
        this.opAllTypeList.opDetailPage.offset = 0;
        this.getCoreDetailList(this.opAllTypeList, false);
      } else {
        this.op_filter_condition = {};
        if (this.searchByTypeInput) {
          this.op_filter_condition[this.search.all.type] = {
            partial_match_str_in: [this.searchByTypeInput],
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
        this.getCoreTypeList();
      }
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
      this.getCoreDetailList(row, false);
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
     * Expand core type table
     * @param {Object} row table cell
     */
    expandCoreTypeItem(row) {
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
        row.op_sort_condition = this.opSortCondition.detail;
        this.getCoreDetailList(row, true);
      } else {
        this.curActiveRow = {
          rowItem: null,
          childProp: null,
          childOrder: null,
        };
      }
    },
    /**
     * Core table type change
     */
    coreTableChange() {
      if (this.coreStatisticType && !this.opAllTypeList.opDetailCol.length) {
        this.opAllTypeList.op_sort_condition = this.opSortCondition.detail;
        this.getCoreDetailList(this.opAllTypeList, true);
      }
    },
    /**
     * Operator core chart change
     */
    coreChartChange() {
      this.setOption(this.coreCharts);
    },
    /**
     * Set chart option
     * @param {Object} chart chart
     */
    setOption(chart) {
      const option = {};
      const maxLabelLength = 20;
      const maxTooltipLen = 50;
      const map = {};
      if (!chart.type) {
        option.legend = {
          data: [],
          orient: 'vertical',
          icon: 'circle',
          formatter: (params) => {
            if (Object.keys(map).length < 1) {
              return '';
            }
            let legendStr = '';
            for (let i = 0; i < chart.data.length; i++) {
              if (chart.data[i].name === params) {
                const percent = `${map[params].toFixed(2)}%`;
                const name =
                  chart.data[i].name.length > 10 ? `${chart.data[i].name.slice(0, 10)}...` : chart.data[i].name;
                legendStr = `{a|${i + 1}}{b|${name}  ${chart.data[i].value.toFixed(this.accuracy)}}\n{c|${percent}}`;
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
              const value = chart.data.find((val) => val.name === params.name).value.toFixed(this.accuracy);
              return `${str} ${value}(${this.unit})`;
            },
          },
          itemWidth: 18,
          itemHeight: 18,
          padding: [0, 50, 0, 0],
          top: '5%',
          left: '45%',
          itemGap: 30,
          textStyle: {
            padding: [15, 0, 0, 0],
            rich: {
              a: {
                width: 24,
                align: 'center',
                padding: [0, 10, -4, -26],
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
                map[params.name] = params.percent;
                return params.data.name && params.data.name.length > maxLabelLength
                  ? `${params.data.name.slice(0, maxLabelLength)}...`
                  : params.data.name;
              },
              color: CommonProperty.modelTracebackChartTheme[this.$store.state.themeIndex].batchSizeTextColor,
            },
            itemStyle: {
              color: (params) => {
                return CommonProperty.pieColorArr[this.$store.state.themeIndex][params.dataIndex];
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
            return `${params[0].axisValue}<br>${params[0].marker}${params[0].value} (${this.unit})`;
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
          left: 50,
          top: 20,
          right: 0,
          bottom: 50,
        };
        option.yAxis = {
          type: 'value',
        };
        chart.data.forEach((item) => {
          option.xAxis.data.push(item.name);
          option.series[0].data.push(item.value);
        });
      }
      this.$nextTick(() => {
        const cpuDom = document.getElementById(chart.id);
        if (cpuDom) {
          chart.chartDom = echarts.init(cpuDom, echartsThemeName);
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
                  formatter: (params) => {
                    return `${params[0].axisValue}<br>${params[0].marker}${params[0].value} (${this.unit})`;
                  },
                  alwaysShowContent: false,
                },
              });
            }
          });
        } else {
          chart.chartDom.off('legendselectchanged');
          chart.chartDom.on('legendselectchanged', () => {
            chart.chartDom.setOption({
              legend: {
                formatter: (params) => {
                  let legendStr = '';
                  for (let i = 0; i < chart.data.length; i++) {
                    if (chart.data[i].name === params) {
                      const percent = `${map[params].toFixed(2)}%`;
                      const name =
                        chart.data[i].name.length > 10 ? `${chart.data[i].name.slice(0, 10)}...` : chart.data[i].name;
                      legendStr = `{a|${i + 1}}{b|${name}  ${chart.data[i].value.toFixed(
                          this.accuracy,
                      )}}\n{c|${percent}}`;
                    }
                  }
                  return legendStr;
                },
              },
            });
          });
        }
        chart.chartDom.resize();
      }, 10);
    },
    /**
     * Show operator info deteail
     * @param {Object} cellData cell data
     * @param {Object} column column
     */
    showInfoDetail(cellData, column) {
      if (column.property !== 'op_info' || !cellData || !cellData.op_info) {
        return;
      }
      this.showDialogData(cellData.op_info, column);
    },
    /**
     * The detailed information is displayed in the dialog box.
     * @param {String} val
     * @param {Object} column
     */
    showDialogData(val, column) {
      this.detailsDataList = [];
      if (typeof val !== 'string' || val === '{}') {
        return;
      } else {
        const isJson = this.isJSON(val);
        if (!isJson) {
          return;
        }
      }
      this.$nextTick(() => {
        this.rowName = `op_info${this.$t('dataTraceback.details')}`;
        this.detailsDialogVisible = true;
        this.detailsDataList = this.formatJsonString(val);
      });
    },
    /**
     * Checks whether the value is a JSON character string.
     * @param {String} val
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
     * Converts JSON strings.
     * @param {String} str
     * @return {Array}
     */
    formatJsonString(str) {
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
              item.id = `${new Date().getTime()}${this.$store.state.tableId}`;
              this.$store.commit('increaseTableId');
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
    /**
     * Window resize
     */
    resizeCallback() {
      if (this.coreCharts.chartDom) {
        this.coreCharts.chartDom.resize();
      }
    },
  },
  mounted() {
    window.addEventListener('resize', this.resizeCallback, false);
    setTimeout(() => {
      this.$bus.$on('collapse', this.resizeEchart);
    }, 500);
  },
};
</script>
<style>
.cl-profiler-wrap {
  height: 100%;
}
.flops-info {
  line-height: 30px;
  background: var(--module-bg-color);
  margin-bottom: 8px;
}
.flops-info span {
  margin-right: 15px;
  font-weight: bold;
}
.flops-info .view-detail {
  float: right;
  cursor: pointer;
  font-size: 12px;
  height: 30px;
  line-height: 30px;
}
.flops-info .view-detail button {
  color: var(--theme-color);
  border: none;
  background-color: var(--module-bg-color);
  cursor: pointer;
}
.flops-info .view-detail button.disabled {
  cursor: not-allowed;
  color: var(--button-disabled-font-color);
}
.cl-search-box {
  float: right;
  margin-bottom: 10px;
  margin-right: 20px;
}
.cl-search-box .el-input {
  width: 300px;
}
.core-search-type {
  float: right;
  width: 130px;
  margin-right: 10px;
}
.cl-profiler-top {
  height: 47%;
}
.cl-profiler-top .chart-title {
  float: left;
  font-weight: bold;
  height: 32px;
  font-size: 16px;
}
.cl-profiler-top.fullScreen {
  display: none;
}
.cl-profiler-bottom {
  height: 53%;
  padding-top: 10px;
}
.cl-profiler-bottom.flops {
  height: calc(53% - 38px);
}
.cl-profiler-bottom .fullScreen {
  float: right;
  margin-top: 5px;
  cursor: pointer;
}
.cl-profiler-bottom.fullScreen {
  height: 100%;
}
.cl-profiler-bottom.fullScreen.flops {
  height: calc(100% - 38px);
}
.cl-profiler-echarts {
  width: 100%;
  height: calc(100% - 32px);
  display: inline-block;
  position: relative;
  overflow: auto;
}
.cl-profiler-echarts .chart {
  width: 100%;
  height: 100%;
  min-width: 1300px;
  min-height: 321px;
  overflow: hidden;
}
.chart-radio-group {
  float: right;
}
.el-radio-group .el-radio-button--small .el-radio-button__inner {
  height: 30px;
  width: 70px;
  font-size: 14px;
  line-height: 10px;
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
.details-data-list .el-table th {
  padding: 10px 0;
  border-top: 1px solid #ebeef5;
}
.details-data-list .el-table th .cell {
  border-left: 1px solid #d9d8dd;
  height: 14px;
  line-height: 14px;
}
.details-data-list .el-table th:first-child .cell {
  border-left: none;
}
.details-data-list .el-table th:nth-child(2),
.details-data-list .el-table td:nth-child(2) {
  max-width: 30%;
}
.details-data-list .el-table td {
  padding: 8px 0;
}
.details-data-list .el-table__row--level-0 td:first-child:after {
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
.details-data-list .el-table__row--level-1 td {
  padding: 4px 0;
  position: relative;
}
.details-data-list .el-table__row--level-1 td:first-child::before {
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
.details-data-list .el-table__row--level-1:first-child td:first-child::before {
  bottom: 0;
}
.details-data-list .el-dialog__title {
  font-weight: bold;
}
.details-data-list .el-dialog__body {
  max-height: 500px;
  padding-top: 10px;
  overflow: auto;
}
.flops-data-list .el-dialog__body {
  max-height: 600px;
  padding-top: 10px;
  overflow: auto;
  text-align: center;
}
.details-data-list .el-dialog__body .details-data-title {
  margin-bottom: 20px;
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
}
.image-noData p {
  font-size: 16px;
  padding-top: 10px;
}
#flopsChart {
  display: inline-block;
}
</style>

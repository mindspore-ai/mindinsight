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
        <el-tab-pane label="AI CORE"
                     name="core">
          <div class="cl-profiler-top"
               :class="{fullScreen:coreFullScreen}"
               v-if="coreCharts.data.length">
            <div>
              <div class="chart-title">{{$t('profiling.chartTitle')}}</div>
              <el-radio-group class="chart-radio-group"
                              v-model="coreCharts.type"
                              @change="coreChartChange"
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
              <div id="core-echarts"></div>
            </div>
          </div>
          <div class="cl-profiler-bottom"
               :class="{fullScreen:coreFullScreen}"
               v-if="coreCharts.data.length">
            <img src="../../assets/images/full-screen.png"
                 :title="$t('graph.fullScreen')"
                 class="fullScreen"
                 @click="fullScreenControl()">
            <div>
              <el-radio-group v-model="coreStatisticType"
                              @change="coreTableChange"
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
                          v-if="!coreStatisticType"
                          :placeholder="$t('operator.searchByType')"
                          clearable
                          @clear="searchOpCoreList()"
                          @keyup.enter.native="searchOpCoreList()"></el-input>
                <el-input v-model="searchByNameInput"
                          v-if="coreStatisticType"
                          :placeholder="$t('operator.searchByName')"
                          clearable
                          @clear="searchOpCoreList()"
                          @keyup.enter.native="searchOpCoreList()"></el-input>
              </div>
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
        </el-tab-pane>
        <el-tab-pane label="AI CPU"
                     class="cpu-tab"
                     name="cpu">
           <div class="cl-profiler-top"
               :class="{fullScreen:cpuFullScreen}"
               v-if="cpuCharts.data.length">
            <div>
              <div class="chart-title">{{$t('profiling.chartTitle')}}</div>
              <el-radio-group class="chart-radio-group"
                              v-model="cpuCharts.type"
                              @change="cpuChartChange"
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
              <div id="cpu-echarts"></div>
            </div>
          </div>

          <div class="cl-profiler-bottom"
               :class="{fullScreen:cpuFullScreen}"
               v-if="cpuCharts.data.length">
            <img src="../../assets/images/full-screen.png"
                 :title="$t('graph.fullScreen')"
                 class="fullScreen"
                 @click="fullScreenControl()">
            <div>
              <el-radio-group v-model="cpuStatisticType"
                              @change="cpuTableChange"
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
                <el-input v-model="searchByCpuTypeInput"
                          v-if="!cpuStatisticType"
                          :placeholder="$t('operator.searchByType')"
                          clearable
                          @clear="searchOpCpuList()"
                          @keyup.enter.native="searchOpCpuList()"></el-input>
                <el-input v-model="searchAllByCpuTypeInput"
                          v-if="cpuStatisticType"
                          :placeholder="$t('operator.searchByType')"
                          clearable
                          @clear="searchOpCpuList()"
                          @keyup.enter.native="searchOpCpuList()"></el-input>
              </div>
            </div>
            <el-table v-show="!cpuStatisticType && opCpuTypeCol && opCpuTypeCol.length"
                      :data="opCpuTypeList"
                      ref="expandCpuTable"
                      @expand-change="expandCpuTypeItem"
                      @sort-change="opCpuTypeSortChange"
                      stripe
                      height="calc(100% - 40px)"
                      width="100%">
              <el-table-column type="expand">
                <template slot-scope="props">
                  <div class="expand-table">
                    <el-table :data="props.row.opDetailList"
                              stripe
                              ref="expandCpuChild"
                              width="100%"
                              tooltip-effect="light"
                              @sort-change="(...args)=>{cpuDetailSortChange(props.row, ...args)}">
                      <el-table-column v-for="(ele, key) in props.row.opDetailCol"
                                       :property="ele"
                                       :key="key"
                                       sortable="custom"
                                       show-overflow-tooltip>
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
                                   @current-change="(...args)=>{opCpuDetailPageChange(props.row, ...args)}"
                                   @size-change="(...args)=>{opCpuDetailPageSizeChange(props.row, ...args)}"
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
            <el-table v-show="cpuStatisticType && opCpuAllTypeList.opDetailCol && opCpuAllTypeList.opDetailCol.length"
                      :data="opCpuAllTypeList.opDetailList"
                      stripe
                      ref="opCpuAllTable"
                      width="100%"
                      height="calc(100% - 80px)"
                      tooltip-effect="light"
                      @sort-change="(...args)=>{cpuDetailSortChange(opCpuAllTypeList, ...args)}">
              <el-table-column v-for="(item, $index) in opCpuAllTypeList.opDetailCol"
                               :property="item"
                               :key="$index"
                               sortable="custom"
                               show-overflow-tooltip>
                <template slot="header">
                  <div class="custom-label"
                       :title="getHeaderField(item)">
                    {{getHeaderField(item)}}
                  </div>
                </template>
              </el-table-column>
            </el-table>
            <el-pagination v-show="cpuStatisticType"
                           v-if="opCpuAllTypeList.opDetailList.length"
                           :current-page="opCpuAllTypeList.opDetailPage.offset + 1"
                           :page-size="opCpuAllTypeList.opDetailPage.limit"
                           :page-sizes="[10, 20, 50]"
                           @current-change="(...args)=>{opCpuDetailPageChange(opCpuAllTypeList, ...args)}"
                           @size-change="(...args)=>{opCpuDetailPageSizeChange(opCpuAllTypeList, ...args)}"
                           layout="total, sizes, prev, pager, next, jumper"
                           :total="opCpuAllTypeList.pageTotal">
            </el-pagination>
          </div>
          <div class="image-noData"
               v-if="cpuCharts.data.length === 0">
            <div>
              <img :src="require('@/assets/images/nodata.png')"
                   alt="" />
            </div>
            <p>{{initOver?$t("public.noData"):$t('public.dataLoading')}}</p>
          </div>
        </el-tab-pane>
      </el-tabs>
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
      apiType: 'core',
      currentCard: '',
      cpuCharts: {
        type: 0,
        id: 'cpu-echarts',
        chartDom: null,
        data: [],
      }, // ai cpu chart
      coreCharts: {
        type: 0,
        id: 'core-echarts',
        chartDom: null,
        data: [],
      }, // ai core chart
      coreStatisticType: 0, // ai core table statistic type
      cpuStatisticType: 0, // ai cpu table statistic type
      searchByTypeInput: '', // search by ai core type name
      searchByNameInput: '', // search by ai core detail name
      searchByCpuTypeInput: '', // search by ai cpu type
      searchAllByCpuTypeInput: '', // search by ai cpu type in all list
      opTypeCol: [], // table headers list of operator type
      opTypeList: [], // table list of operator type
      opCpuTypeCol: [], // table headers list of operator type
      opCpuTypeList: [], // table list of operator type
      opCpuAllTypeList: {
        opDetailCol: [],
        opDetailList: [],
        pageTotal: 0,
        opDetailPage: {
          offset: 0,
          limit: 10,
        },
        op_filter_condition: {},
        op_sort_condition: {
          name: 'total_time',
          type: 'descending',
        },
      }, // table data of operator cpu
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
      profile_dir: '', // profile directory
      train_id: '', // train id
      op_filter_condition: {}, // operator type filter
      op_sort_condition: {
        name: 'execution_time',
        type: 'descending',
      }, // operator type filter
      op_cpu_filter_condition: {},
      op_cpu_sort_condition: {
        name: 'execution_time',
        type: 'descending',
      }, // operator cpu type filter
      initOver: false,
      objectType: 'object',
      curActiveRow: {
        rowItem: null,
        childProp: null,
        childOrder: null,
      },
      curCpuActiveRow: {
        rowItem: null,
        childProp: null,
        childOrder: null,
      },
      coreFullScreen: false,
      cpuFullScreen: false,
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

    if (this.cpuCharts.chartDom) {
      this.cpuCharts.chartDom.off('mouseover');
      this.cpuCharts.chartDom.off('mouseout');
    }
    if (this.coreCharts.chartDom) {
      this.coreCharts.chartDom.off('mouseover');
      this.coreCharts.chartDom.off('mouseout');
    }
  },
  methods: {
    getHeaderField(key) {
      const maps = {
        execution_time: `execution_time (${this.$t('profiling.unit')})`,
        avg_execution_time: `avg_execution_time (${this.$t('profiling.unit')})`,
        execution_frequency: `execution_frequency (${this.$t(
            'profiling.countUnit',
        )})`,
        percent: 'percent (%)',
        total_time: 'total_time (ms)',
        dispatch_time: 'dispatch_time (ms)',
      };
      return maps[key] ? maps[key] : key;
    },
    resizeEchart() {
      if (this.coreCharts.chartDom) {
        setTimeout(() => {
          this.coreCharts.chartDom.resize();
        }, 300);
      }
    },
    fullScreenControl() {
      if (this.apiType === 'core') {
        this.coreFullScreen = !this.coreFullScreen;
        if (this.coreCharts.chartDom && !this.coreFullScreen) {
          this.$nextTick(() => {
            this.coreCharts.chartDom.resize();
          });
        }
      } else {
        this.cpuFullScreen = !this.cpuFullScreen;
        if (this.cpuCharts.chartDom && !this.cpuFullScreen) {
          this.$nextTick(() => {
            this.cpuCharts.chartDom.resize();
          });
        }
      }
    },
    /**
     * Current device change
     */
    cardChange() {
      if (this.apiType === 'core') {
        this.coreStatisticType = 0;
        this.clearCoreData();
        this.getCoreTypeList();
      } else if (this.apiType === 'cpu') {
        this.cpuStatisticType = 0;
        this.clearCpuData();
        this.getCpuTypeList();
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
     * Operators cpu type sort
     * @param {Object} sort Sort data
     */
    opCpuTypeSortChange(sort) {
      this.op_cpu_sort_condition = {
        name: sort.prop,
        type: sort.order,
      };
      this.$nextTick(() => {
        const item = this.$refs['expandCpuChild'];
        if (item && this.curCpuActiveRow.rowItem) {
          item.sort(
              this.curCpuActiveRow.childProp,
              this.curCpuActiveRow.childOrder,
          );
        }
      });
    },
    /**
     * Clear cpu data
     */
    clearCpuData() {
      this.searchByCpuTypeInput = '';
      this.searchAllByCpuTypeInput = '';
      this.op_cpu_filter_condition = {};
      this.op_cpu_sort_condition = {
        name: 'execution_time',
        type: 'descending',
      };
      this.opCpuTypeCol = [];
      this.opCpuTypeList = [];
      this.opCpuAllTypeList = {
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
     * Clear core data
     */
    clearCoreData() {
      this.searchByTypeInput = '';
      this.searchByNameInput = '';
      this.op_filter_condition = {};
      this.op_sort_condition = {
        name: 'execution_time',
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
     * Get core type list
     */
    getCoreTypeList() {
      const params = {};
      params.params = {
        profile: this.profile_dir,
        train_id: this.train_id,
      };
      params.body = {
        op_type: 'aicore_type',
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
                  !this.coreCharts.device_id ||
                this.coreCharts.device_id !== this.currentCard
                ) {
                  this.coreCharts.device_id = this.currentCard;
                  this.coreCharts.data = [];
                  res.data.object.forEach((k) => {
                    if (
                      this.coreCharts.data &&
                    this.coreCharts.data.length < 19
                    ) {
                      this.coreCharts.data.push({
                        name: k[0],
                        value: k[1],
                        percent: k[3],
                      });
                    } else {
                      if (!this.coreCharts.data[19]) {
                        this.coreCharts.data[19] = {
                          name: 'Other',
                          value: 0,
                          percent: 0,
                        };
                      }
                      this.coreCharts.data[19].value += k[1];
                      this.coreCharts.data[19].percent += k[3];
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
        op_type: 'aicore_detail',
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
     * Get cpu type list
     */
    getCpuTypeList() {
      const params = {};
      params.params = {
        profile: this.profile_dir,
        train_id: this.train_id,
      };
      params.body = {
        op_type: 'aicpu_type',
        device_id: this.currentCard,
        filter_condition: this.op_cpu_filter_condition,
        sort_condition: this.op_cpu_sort_condition,
      };
      requestService
          .getProfilerOpData(params)
          .then((res) => {
            this.initOver = true;
            this.opCpuTypeList = [];
            if (res && res.data) {
              this.opCpuTypeCol = res.data.col_name;
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
                  this.opCpuTypeList.push(object);
                });
                this.$nextTick(() => {
                  const elementItem = this.$refs['expandCpuTable'];
                  if (elementItem) {
                    elementItem.sort(
                        this.op_sort_condition.name,
                        this.op_sort_condition.type,
                    );
                  }
                });
                if (
                  !this.cpuCharts.device_id ||
                this.cpuCharts.device_id !== this.currentCard
                ) {
                  this.cpuCharts.device_id = this.currentCard;
                  this.cpuCharts.data = [];
                  res.data.object.forEach((k) => {
                    if (this.cpuCharts.data && this.cpuCharts.data.length < 19) {
                      this.cpuCharts.data.push({
                        name: k[0],
                        value: k[1],
                        percent: k[3],
                      });
                    } else {
                      if (!this.cpuCharts.data[19]) {
                        this.cpuCharts.data[19] = {
                          name: 'Other',
                          value: 0,
                          percent: 0,
                        };
                      }
                      this.cpuCharts.data[19].value += k[1];
                      this.cpuCharts.data[19].percent += k[3];
                    }
                  });
                  this.setOption(this.cpuCharts);
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
     * Get cpu list
     * @param {Object} row type row
     * @param {Boolean} isSort if sort
     */
    getCpuDetailList(row, isSort) {
      const params = {};
      params.params = {
        profile: this.profile_dir,
        train_id: this.train_id,
      };
      params.body = {
        op_type: 'aicpu_detail',
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
                if (this.cpuStatisticType) {
                  item = this.$refs['opCpuAllTable'];
                } else {
                  item = this.$refs['expandCpuChild'];
                  this.curCpuActiveRow = {
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
                this.$refs.expandCpuTable.doLayout();
              });
            }
          })
          .catch(() => {});
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
     * Cpu list page change
     * @param {Object} row table cell
     * @param {Number} pageIndex current page
     */
    opCpuDetailPageChange(row, pageIndex) {
      row.opDetailPage.offset = pageIndex - 1;
      this.getCpuDetailList(row, false);
    },
    /**
     * Cpu list page size change
     * @param {Object} row table cell
     * @param {Number} pageSize current page size
     */
    opCpuDetailPageSizeChange(row, pageSize) {
      row.opDetailPage.offset = 0;
      row.opDetailPage.limit = pageSize;
      this.getCpuDetailList(row, false);
    },
    /**
     * Get core list by search
     */
    searchOpCoreList() {
      if (this.coreStatisticType) {
        this.opAllTypeList.op_filter_condition = {};
        if (this.searchByNameInput) {
          this.opAllTypeList.op_filter_condition = {
            op_name: {partial_match_str_in: [this.searchByNameInput]},
          };
        } else {
          this.opAllTypeList.op_filter_condition = {};
        }
        this.opAllTypeList.opDetailPage.offset = 0;
        this.getCoreDetailList(this.opAllTypeList, false);
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
        this.getCoreTypeList();
      }
    },
    /**
     * Get cpu list by search
     */
    searchOpCpuList() {
      if (this.cpuStatisticType) {
        this.opCpuAllTypeList.op_filter_condition = {};
        if (this.searchAllByCpuTypeInput) {
          this.opCpuAllTypeList.op_filter_condition = {
            op_type: {partial_match_str_in: [this.searchAllByCpuTypeInput]},
          };
        } else {
          this.opCpuAllTypeList.op_filter_condition = {};
        }
        this.opCpuAllTypeList.opDetailPage.offset = 0;
        this.getCpuDetailList(this.opCpuAllTypeList, false);
      } else {
        this.op_cpu_filter_condition = {};
        if (this.searchByCpuTypeInput) {
          this.op_cpu_filter_condition = {
            op_type: {partial_match_str_in: [this.searchByCpuTypeInput]},
          };
        } else {
          this.op_cpu_filter_condition = {};
        }
        if (this.curCpuActiveRow.rowItem) {
          this.curCpuActiveRow = {
            rowItem: null,
            childProp: null,
            childOrder: null,
          };
        }
        this.getCpuTypeList();
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
     * Cpu detail sort
     * @param {Object} row table cell
     * @param {Object} column table cell
     */
    cpuDetailSortChange(row, column) {
      row.op_sort_condition = {
        name: column.prop,
        type: column.order,
      };
      row.opDetailPage.offset = 0;
      this.getCpuDetailList(row, false);
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
        row.op_sort_condition = {
          name: 'avg_execution_time',
          type: 'descending',
        };
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
     * Expand cpu type table
     * @param {Object} row table cell
     */
    expandCpuTypeItem(row) {
      row.isExpanded = !row.isExpanded;
      if (row.isExpanded) {
        if (this.curCpuActiveRow.rowItem) {
          const item = this.$refs['expandCpuTable'];
          if (item) {
            item.toggleRowExpansion(this.curCpuActiveRow.rowItem, false);
          }
        }
        this.curCpuActiveRow = {
          rowItem: row,
          childProp: null,
          childOrder: null,
        };
        row.opDetailList = [];
        row.opDetailCol = [];
        row.opDetailPage.offset = 0;
        row.pageTotal = 0;
        row.op_sort_condition = {
          name: 'total_time',
          type: 'descending',
        };
        this.getCpuDetailList(row, true);
      } else {
        this.curCpuActiveRow = {
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
        this.apiType === 'cpu' &&
        this.cpuCharts.device_id !== this.currentCard
      ) {
        this.initOver = false;
        this.clearCpuData();
        this.getCpuTypeList();
      } else if (
        this.apiType === 'core' &&
        this.coreCharts.device_id !== this.currentCard
      ) {
        this.initOver = false;
        this.clearCoreData();
        this.getCoreTypeList();
      }
      this.$nextTick(() => {
        this.resizeCallback();
      });
    },
    /**
     * Core table type change
     */
    coreTableChange() {
      if (this.coreStatisticType && !this.opAllTypeList.opDetailCol.length) {
        this.opAllTypeList.op_sort_condition = {
          name: 'avg_execution_time',
          type: 'descending',
        };
        this.getCoreDetailList(this.opAllTypeList, true);
      }
    },
    /**
     * Cpu table type change
     */
    cpuTableChange() {
      if (this.cpuStatisticType && !this.opCpuAllTypeList.opDetailCol.length) {
        this.opCpuAllTypeList.op_sort_condition = {
          name: 'total_time',
          type: 'descending',
        };
        this.getCpuDetailList(this.opCpuAllTypeList, true);
      }
    },
    /**
     * Operator cpu chart change
     */
    cpuChartChange() {
      this.setOption(this.cpuCharts);
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
                ].value.toFixed(6)}}\n{c|${chart.data[i].percent.toFixed(2)}%}`;
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
          chart.chartDom = echarts.init(cpuDom, null);
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
        this.detailsDataList = this.formateJsonString(val);
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
              item.id =
                `${new Date().getTime()}` + `${this.$store.state.tableId}`;
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
      if (this.coreCharts.chartDom && this.apiType === 'core') {
        this.coreCharts.chartDom.resize();
      }
      if (this.cpuCharts.chartDom && this.apiType === 'cpu') {
        this.cpuCharts.chartDom.resize();
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
    .cl-profiler-echarts {
      width: 100%;
      height: calc(100% - 32px);
      display: inline-block;
      position: relative;
      overflow: auto;
      #cpu-echarts,
      #core-echarts {
        width: 100%;
        height: 100%;
        min-width: 1300px;
        min-height: 321px;
        overflow: hidden;
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
      height: 450px;
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

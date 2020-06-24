<template>
  <div class="operator">
    <div class="operator-title">{{$t('profiling.operatorDetail')}}</div>
    <div class="cl-profiler">
      <el-tabs v-model="apiType"
               @tab-click="tabChange">
        <el-tab-pane label="AI CORE"
                     name="core">
          <div class="cl-profiler-top"
               v-if="coreCharts.data.length">
            <div>
              <span class="profiler-title">
                {{$t('operator.operatorTypeStatistics')}}
              </span>
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
               v-if="coreCharts.data.length">
            <span class="profiler-title">
              {{ $t('operator.operatorStatistics') }}
            </span>
            <div>
              <el-radio-group v-model="statisticType"
                              @change="coreTableChange"
                              fill="#00A5A7"
                              text-color="#FFFFFF"
                              size="small">
                <el-radio-button :label="1">
                  {{$t('operator.allOperator')}}
                </el-radio-button>
                <el-radio-button :label="0">
                  {{$t('operator.ClassificationOperator')}}
                </el-radio-button>
              </el-radio-group>
              <div class="cl-search-box">
                <el-input v-model="searchByTypeInput"
                          v-if="!statisticType"
                          :placeholder="$t('operator.searchByType')"
                          clearable
                          @clear="searchOpCoreList()"
                          @keyup.enter.native="searchOpCoreList()"></el-input>
                <el-input v-model="searchByNameInput"
                          v-if="statisticType"
                          :placeholder="$t('operator.searchByName')"
                          clearable
                          @clear="searchOpCoreList()"
                          @keyup.enter.native="searchOpCoreList()"></el-input>
              </div>
            </div>
            <el-table v-show="!statisticType && opTypeCol && opTypeCol.length"
                      :data="opTypeList"
                      ref="expandTable"
                      @expand-change="expandTypeItem"
                      @sort-change="opTypeSortChange"
                      stripe
                      height="calc(100% - 75px)"
                      width="100%">
              <el-table-column type="expand">
                <template slot-scope="props">
                  <div class="expand-table">
                    <el-table :data="props.row.opDetailList"
                              stripe
                              ref="expandChild"
                              width="100%"
                              tooltip-effect="light"
                              @cell-click="showInfoDetail"
                              @sort-change="(...args)=>{coreDetailSortChange(props.row, ...args)}">
                      <el-table-column v-for="(ele, key) in props.row.opDetailCol"
                                       :property="ele"
                                       :key="key"
                                       :sortable="ele === 'op_info' ? false : 'custom'"
                                       :width="(ele==='execution_time'|| ele==='subgraph' ||
                                        ele==='op_name'|| ele==='op_type')?'220':''"
                                       show-overflow-tooltip
                                       :label="ele">
                      </el-table-column>
                    </el-table>
                    <el-pagination :current-page="props.row.opDetailPage.offset + 1"
                                   :page-size="props.row.opDetailPage.limit"
                                   @current-change="(...args)=>{opDetailPageChange(props.row, ...args)}"
                                   layout="total, prev, pager, next, jumper"
                                   :total="props.row.pageTotal">
                    </el-pagination>
                    <div class="clear"></div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column v-for="(item, $index) in opTypeCol"
                               :property="item"
                               :key="$index"
                               sortable
                               :label="item">
              </el-table-column>
            </el-table>
            <el-table v-show="statisticType && opAllTypeList.opDetailCol && opAllTypeList.opDetailCol.length"
                      :data="opAllTypeList.opDetailList"
                      stripe
                      ref="opAllTable"
                      width="100%"
                      height="calc(100% - 114px)"
                      @cell-click="showInfoDetail"
                      @sort-change="(...args)=>{coreDetailSortChange(opAllTypeList, ...args)}"
                      tooltip-effect="light">
              <el-table-column v-for="(item, $index) in opAllTypeList.opDetailCol"
                               :property="item"
                               :key="$index"
                               :label="item"
                               :sortable="item === 'op_info' ? false : 'custom'"
                               :width="(item==='execution_time'|| item==='subgraph' ||
                                item==='op_name'|| item==='op_type')?'220':''"
                               show-overflow-tooltip>
              </el-table-column>
            </el-table>
            <el-pagination v-show="statisticType"
                           v-if="opAllTypeList.opDetailList.length"
                           :current-page="opAllTypeList.opDetailPage.offset + 1"
                           :page-size="opAllTypeList.opDetailPage.limit"
                           @current-change="(...args)=>{opDetailPageChange(opAllTypeList, ...args)}"
                           layout="total, prev, pager, next, jumper"
                           :total="opAllTypeList.pageTotal">
            </el-pagination>
          </div>
          <div class="image-noData"
               v-if="initOver && coreCharts.data.length === 0">
            <div>
              <img :src="require('@/assets/images/nodata.png')"
                   alt="" />
            </div>
            <p>{{ $t("public.noData") }}</p>
          </div>
        </el-tab-pane>
        <el-tab-pane label="AI CPU"
                     class="cpu-tab"
                     name="cpu"
                     v-if="false">
          <div class="cl-profiler-top"
               v-if="cpuCharts.data.length">
            <div>
              <span class="profiler-title">
                {{ $t('operator.operatorStatistics') }}
              </span>
            </div>
            <div class="cl-profiler-echarts">
              <div class
                   id="cpu-echarts"></div>
            </div>
          </div>
          <div class="cl-profiler-bottom"
               v-if="cpuCharts.data.length">
            <span class="profiler-title">
              {{ $t('operator.operatorStatistics') }}
            </span>
            <div class="cl-search-box">
              <el-input v-model="searchByCPUTypeInput"
                        :placeholder="$t('operator.searchByType')"
                        clearable
                        @clear="searchOpCpuList()"
                        @keyup.enter.native="searchOpCpuList()"></el-input>
            </div>
            <el-table v-show="opCpuList.opDetailCol && opCpuList.opDetailCol.length"
                      :data="opCpuList.opDetailList"
                      stripe
                      ref="opCPUTable"
                      width="100%"
                      height="calc(100% - 82px)"
                      tooltip-effect="light"
                      @sort-change="(...args)=>{cpuDetailSortChange(opCpuList, ...args)}">
              <el-table-column v-for="(item, $index) in opCpuList.opDetailCol"
                               :property="item"
                               :key="$index"
                               :label="item"
                               sortable="custom"
                               show-overflow-tooltip>
              </el-table-column>
            </el-table>
            <el-pagination v-if="opCpuList.opDetailList.length"
                           :current-page="opCpuList.opDetailPage.offset + 1"
                           :page-size="opCpuList.opDetailPage.limit"
                           @current-change="(...args)=>{opCpuPageChange(opCpuList, ...args)}"
                           layout="total, prev, pager, next, jumper"
                           :total="opCpuList.pageTotal">
            </el-pagination>
          </div>
          <div class="image-noData"
               v-if="initOver && cpuCharts.data.length === 0">
            <div>
              <img :src="require('@/assets/images/nodata.png')"
                   alt="" />
            </div>
            <p>{{$t("public.noData")}}</p>
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
        type: 1,
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
      statisticType: 0, // ai core table statistic type
      searchByTypeInput: '', // search by ai core type name
      searchByNameInput: '', // search by ai core detail name
      searchByCPUTypeInput: '', // search by ai cpu name
      opTypeCol: [], // table headers list of operator type
      opTypeList: [], // table list of operator type
      opCpuList: {
        opDetailCol: [],
        opDetailList: [],
        pageTotal: 0,
        opDetailPage: {
          offset: 0,
          limit: 20,
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
          limit: 8,
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
      initOver: false,
      objectType: 'object',
      curActiveRow: {
        rowItem: null,
        childProp: null,
        childOrder: null,
      },
    };
  },
  watch: {
    '$parent.curDashboardInfo': {
      handler(newValue, oldValue) {
        if (newValue.query.dir && newValue.query.id && newValue.curCardNum) {
          this.profile_dir = newValue.query.dir;
          this.train_id = newValue.query.id;
          this.currentCard = newValue.curCardNum;
          this.cardChange();
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
  },
  methods: {
    resizeEchart() {
      if (this.coreCharts.chartDom) {
        setTimeout(() => {
          this.coreCharts.chartDom.resize();
        }, 300);
      }
    },
    /**
     * Current device change
     */
    cardChange() {
      if (this.apiType === 'core') {
        this.statisticType = 0;
        this.clearCoreData();
        this.getCoreTypeList();
      } else if (this.apiType === 'cpu') {
        this.clearCpuData();
        this.getCpuList(true);
      }
    },
    opTypeSortChange() {
      this.$nextTick(() => {
        const item = this.$refs['expandChild'];
        if (item && this.curActiveRow.rowItem) {
          item.sort(this.curActiveRow.childProp, this.curActiveRow.childOrder);
        }
      });
    },
    /**
     * clear cpu data
     */
    clearCpuData() {
      this.searchByCPUTypeInput = '';
      this.opCpuList = {
        opDetailCol: [],
        opDetailList: [],
        pageTotal: 0,
        opDetailPage: {
          offset: 0,
          limit: 20,
        },
        op_filter_condition: {},
        op_sort_condition: {
          name: 'total_time',
          type: 'descending',
        },
      };
    },
    /**
     * clear core data
     */
    clearCoreData() {
      this.searchByTypeInput = '';
      this.searchByNameInput = '';
      this.op_filter_condition = {};
      this.opTypeCol = [];
      this.opTypeList = [];
      this.opAllTypeList = {
        opDetailCol: [],
        opDetailList: [],
        pageTotal: 0,
        opDetailPage: {
          offset: 0,
          limit: 8,
        },
        op_filter_condition: {},
        op_sort_condition: {},
      };
    },
    /**
     * get core list
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
                      limit: 8,
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
     * get core detail list
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
     * get cpu list
     * @param {Boolean} isSort if sort
     */
    getCpuList(isSort) {
      const params = {};
      params.params = {
        profile: this.profile_dir,
        train_id: this.train_id,
      };
      params.body = {
        op_type: 'aicpu',
        device_id: this.currentCard,
        filter_condition: this.opCpuList.op_filter_condition,
        sort_condition: this.opCpuList.op_sort_condition,
        group_condition: this.opCpuList.opDetailPage,
      };
      requestService
          .getProfilerOpData(params)
          .then((res) => {
            this.initOver = true;
            if (res && res.data) {
              if (res.data.object) {
                if (
                  !this.cpuCharts.device_id ||
                this.cpuCharts.device_id !== this.currentCard
                ) {
                  this.cpuCharts.device_id = this.currentCard;
                  this.cpuCharts.data = [];
                  res.data.object.forEach((k) => {
                    this.cpuCharts.data.push({
                      name: k[0],
                      op_name: k[1],
                      value: k[2],
                    });
                  });
                  this.setOption(this.cpuCharts);
                }
                if (res.data.object.length > 8) {
                  this.opCpuList.opDetailPage.limit = 8;
                  res.data.object.splice(8);
                }
                this.formatterDetailData(this.opCpuList, res.data);
                if (isSort) {
                  this.$nextTick(() => {
                    const item = this.$refs['opCPUTable'];
                    if (item) {
                      item.sort(
                          this.opCpuList.op_sort_condition.name,
                          this.opCpuList.op_sort_condition.type,
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
     * operator detail list page change
     * @param {Object} row table cell
     * @param {Number} pageIndex current page
     */
    opDetailPageChange(row, pageIndex) {
      row.opDetailPage.offset = pageIndex - 1;
      this.getCoreDetailList(row, false);
    },
    /**
     * cpu list page change
     * @param {Object} row table cell
     * @param {Number} pageIndex current page
     */
    opCpuPageChange(row, pageIndex) {
      row.opDetailPage.offset = pageIndex - 1;
      this.getCpuList(false);
    },
    /**
     * get core list by search
     */
    searchOpCoreList() {
      if (this.statisticType) {
        this.opAllTypeList.op_filter_condition = {};
        if (this.searchByNameInput) {
          this.opAllTypeList.op_filter_condition = {
            op_name: {partial_match_str_in: [this.searchByNameInput]},
          };
        } else {
          this.opAllTypeList.op_filter_condition = {};
        }
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
     * get cpu list by search
     */
    searchOpCpuList() {
      this.opCpuList.op_filter_condition = {};
      if (this.searchByCPUTypeInput) {
        this.opCpuList.op_filter_condition = {
          op_type: {partial_match_str_in: [this.searchByCPUTypeInput]},
        };
      } else {
        this.opCpuList.op_filter_condition = {};
      }
      this.getCpuList(false);
    },
    /**
     * core detail sort
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
     * cpu detail sort
     * @param {Object} row table cell
     * @param {Object} column table cell
     */
    cpuDetailSortChange(row, column) {
      row.op_sort_condition = {
        name: column.prop,
        type: column.order,
      };
      row.opDetailPage.offset = 0;
      this.getCpuList(false);
    },
    /**
     * format detail data
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
     * expand core type table
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
        row.op_sort_condition = {name: 'execution_time', type: 'descending'};
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
     * tab change
     */
    tabChange() {
      if (
        this.apiType === 'cpu' &&
        this.cpuCharts.device_id !== this.currentCard
      ) {
        this.initOver = false;
        this.clearCpuData();
        this.getCpuList(true);
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
     * core table type change
     */
    coreTableChange() {
      if (this.statisticType && !this.opAllTypeList.opDetailCol.length) {
        this.opAllTypeList.op_sort_condition = {
          name: 'execution_time',
          type: 'descending',
        };
        this.getCoreDetailList(this.opAllTypeList, true);
      }
    },
    /**
     * operator cpu chart change
     */
    cpuChartChange() {
      this.setOption(this.cpuCharts);
    },
    /**
     * operator core chart change
     */
    coreChartChange() {
      this.setOption(this.coreCharts);
    },
    /**
     * set chart option
     * @param {Object} chart chart
     */
    setOption(chart) {
      const option = {};
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
                ].value.toFixed(3)}}\n{c|${chart.data[i].percent.toFixed(2)}%}`;
              }
            }
            return legendStr;
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
            return `${params.marker} ${params.data.name} ${params.percent}%`;
          },
          confine: true,
        };
        option.series = [
          {
            type: 'pie',
            center: ['25%', '65%'],
            data: chart.data,
            radius: '50%',
            lable: {
              position: 'outer',
              alignTo: 'none',
              bleedMargin: 5,
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
            return `${params[0].axisValue}<br>${
              params[0].marker
            }${params[0].value.toFixed(4)}`;
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
          const name = this.apiType === 'cpu' ? item.op_name : item.name;
          option.xAxis.data.push(name);
          option.series[0].data.push(item.value);
        });
        if (this.apiType === 'cpu') {
          option.xAxis.axisLabel.formatter = (params, dataIndex) => {
            const xAxisValue = chart.data[dataIndex].op_name;
            return xAxisValue.replace(/^.+\//g, '');
          };
        }
      }
      this.$nextTick(() => {
        const cpuDom = document.getElementById(chart.id);
        if (cpuDom) {
          chart.chartDom = echarts.init(cpuDom, null);
        } else {
          if (chart.chartDom) {
            chart.chartDom.clear();
          }
          return;
        }
        chart.chartDom.setOption(option, true);
        chart.chartDom.resize();
      }, 10);
    },
    /**
     * show operator info deteail
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
      if (typeof val !== 'string' || val == '{}') {
        return;
      } else {
        const isJson = this.isJSON(val);
        if (!isJson) {
          return;
        }
      }
      this.$nextTick(() => {
        this.rowName = `${column.label}${this.$t('dataTraceback.details')}`;
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
     * window resize
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
}
.clear {
  clear: both;
}
.el-tabs__item {
  color: #6c7280;
  font-size: 16px;
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
  }
  .cl-profiler-top {
    height: 45%;
  }
  .cl-profiler-bottom {
    height: 55%;
    padding-top: 10px;
  }
  .cpu-tab {
    .cl-profiler-top {
      height: calc(36% + 32px);
    }
    .cl-profiler-bottom {
      height: calc(64% - 32px);
    }
  }
  .profiler-title {
    font-size: 16px;
    font-weight: bold;
    line-height: 32px;
    display: inline-block;
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
      min-height: 232px;
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
</style>

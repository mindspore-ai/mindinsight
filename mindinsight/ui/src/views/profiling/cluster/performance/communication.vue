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
  <!-- cl-cluster -->
  <div class="cl-comm">
    <div class="profiling-content-title">
      {{ $t('profilingCluster.clusterCommView') }}
      <el-tooltip placement="bottom"
                  effect="light">
        <div slot="content"
             class="comm-tooltip-container">
          <div class="comm-tooltip-cell">
            <span>{{ $t('profilingCluster.commCost') + $t('symbols.colon') }}</span>
            <br>
            <span>{{ $t('profilingCluster.commCostExplanation') }}</span>
          </div>
          <div class="comm-tooltip-cell">
            <span>{{ $t('profilingCluster.waitCost') + $t('symbols.colon') }}</span>
            <br>
            <span>{{ $t('profilingCluster.waitCostExplanation') }}</span>
          </div>
          <div class="comm-tooltip-cell">
            <span>{{ $t('profilingCluster.linkInfo') + $t('symbols.colon') }}</span>
            <br>
            <span>{{ $t('profilingCluster.linkInfoExplanation') }}</span>
          </div>
          <div class="comm-tooltip-cell">
            <span>{{ $t('profilingCluster.linkType') + $t('symbols.colon') }}</span>
            <br>
            <span>{{ $t('profilingCluster.linkTypeExplanation') }}</span>
          </div>
        </div>
        <i class="el-icon-info"></i>
      </el-tooltip>
    </div>

    <el-tabs v-model="tab"
             @tab-click="handleTabClick">
      <el-tab-pane :label="$t('profilingCluster.commPerformance')"
                   :name="tabNames[0]"></el-tab-pane>
      <el-tab-pane :label="$t('profilingCluster.linkInfo')"
                   :name="tabNames[1]"></el-tab-pane>
    </el-tabs>

    <div v-show="pageState === normalState && tab === tabNames[0]"
         class="comm-content default-tab">
      <div class="content-filter">
        <label>{{ stepTip }}</label>
        <el-input class="step-input"
                  clearable
                  @clear="stepFilter"
                  v-model="step.value"></el-input>
        <el-button @click="stepFilter">{{ $t('public.sure') }}</el-button>
      </div>
      <div class="content-chart"
           ref="commChart"></div>
      <div class="content-table">
        <!-- Page Default Table -->
        <el-table :data="tableData"
                  height="100%"
                  ref="table"
                  stripe
                  :default-sort="tableDefaultSort"
                  @sort-change="tableSortChange">
          <!-- Column 1 / rank_id -->
          <el-table-column width="120"
                           :prop="tableProps[0].prop"
                           :label="tableProps[0].label">
          </el-table-column>
          <!-- Column 2 / communication_cost -->
          <el-table-column :prop="tableProps[1].prop"
                           :label="tableProps[1].label"
                           sortable="custom">
          </el-table-column>
          <!-- Column 3 / wait_cost -->
          <el-table-column :prop="tableProps[2].prop"
                           :label="tableProps[2].label"
                           sortable="custom">
          </el-table-column>
          <!-- Column 4 / view op details -->
          <el-table-column fixed="right"
                           width="180"
                           :label="tableProps[3].label">
            <template slot-scope="scope">
              <span class="table-button"
                    @click="showOpInfo(scope.row)">
                {{ $t('public.details') }}
              </span>
            </template>
          </el-table-column>
          <!-- Column 5 / view link details -->
          <el-table-column fixed="right"
                           width="180"
                           :label="tableProps[4].label">
            <template slot-scope="scope">
              <span class="table-button"
                    @click="showLinkInfo(scope.row)">
                {{ $t('public.details') }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div class="content-pagination">
        <el-pagination @current-change="currentPageChange"
                       @size-change="pageSizeChange"
                       :page-sizes="pageCondition.sizes"
                       :page-size="pageCondition.limit"
                       :current-page="pageCondition.page"
                       layout="total,sizes,prev,pager,next,jumper"
                       :total="pageCondition.total">
        </el-pagination>
      </div>
    </div>

    <div v-show="pageState === normalState && tab === tabNames[1]"
         class="comm-content link-tab">
      <div class="content-filter">
        <span>{{ $t('profilingCluster.startID') }}</span>
        <el-input v-model="linkTable.filter.src_rank"
                  clearable
                  @clear="filterLinkTable"></el-input>
        <span>{{ $t('profilingCluster.endID') }}</span>
        <el-input v-model="linkTable.filter.dst_rank"
                  clearable
                  @clear="filterLinkTable"></el-input>
        <span>{{ $t('profilingCluster.linkType') }}</span>
        <el-select v-model="linkTable.filter.link_type">
          <el-option v-for="type in linkTable.linkTypes"
                     :key="type"
                     :label="type"
                     :value="type">
          </el-option>
        </el-select>
        <el-button @click="filterLinkTable">{{ $t('public.sure') }} </el-button>
      </div>
      <!-- Link Table -->
      <div class="content-link-table">
        <el-table :data="linkTable.tableData"
                  height="100%"
                  ref="table"
                  stripe
                  :default-sort="linkDefaultSort"
                  @sort-change="linkTableSortChange">
          <!-- Column 1 / src_dst -->
          <el-table-column :prop="linkTableProps[0].prop"
                           :label="linkTableProps[0].label">
          </el-table-column>
          <!-- Column 2 / communication_cost -->
          <el-table-column sortable="custom"
                           :prop="linkTableProps[1].prop"
                           :label="linkTableProps[1].label">
          </el-table-column>
          <!-- Column 3 / communication_size -->
          <el-table-column sortable="custom"
                           :prop="linkTableProps[2].prop"
                           :label="linkTableProps[2].label">
          </el-table-column>
          <!-- Column 4 / band_width -->
          <el-table-column sortable="custom"
                           :prop="linkTableProps[3].prop"
                           :label="linkTableProps[3].label">
          </el-table-column>
          <!-- Column 5 / link_type -->
          <el-table-column :prop="linkTableProps[4].prop"
                           :label="linkTableProps[4].label">
          </el-table-column>
        </el-table>
      </div>
      <div class="content-pagination">
        <el-pagination @current-change="linkTablePageChange"
                       @size-change="linkTableSizeChange"
                       :page-sizes="linkTable.pageCondition.sizes"
                       :page-size="linkTable.pageCondition.limit"
                       :current-page.sync="linkTable.pageCondition.page"
                       layout="total,sizes,prev,pager,next,jumper"
                       :total="linkTable.pageCondition.total">
        </el-pagination>
      </div>
    </div>

    <div v-show="pageState !== normalState"
         class="comm-content">
      <empty :state="pageState"></empty>
    </div>

    <el-dialog :title="linkInfo.title"
               :visible.sync="linkInfo.visible"
               width="960px">
      <div class="comm-dialog">
        <div class="dialog-filter">
          <span>{{ $t('profilingCluster.linkType') }}</span>
          <el-select v-model="linkInfo.filterType"
                     @change="filterLinkInfo">
            <el-option v-for="type in linkInfo.linkTypes"
                       :key="type"
                       :label="type"
                       :value="type">
            </el-option>
          </el-select>
        </div>
        <div class="dialog-content"
             :style="{height: linkInfo.tableHeight}">
          <!-- Link Diglog -->
          <el-table :data="linkInfo.tableData"
                    height="100%">
            <!-- Column 1 / src_dst -->
            <el-table-column width="160"
                             :prop="linkTableProps[0].prop"
                             :label="linkTableProps[0].label">
            </el-table-column>
            <!-- Column 2 / communication_cost -->
            <el-table-column sortable
                             :prop="linkTableProps[1].prop"
                             :label="linkTableProps[1].label">
            </el-table-column>
            <!-- Column 3 / communication_size -->
            <el-table-column sortable
                             :prop="linkTableProps[2].prop"
                             :label="linkTableProps[2].label">
            </el-table-column>
            <!-- Column 4 / band_width -->
            <el-table-column sortable
                             :prop="linkTableProps[3].prop"
                             :label="linkTableProps[3].label">
            </el-table-column>
            <!-- Column 5 / link_type -->
            <el-table-column width="100"
                             :prop="linkTableProps[4].prop"
                             :label="linkTableProps[4].label">
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>

    <el-dialog :title="opInfo.title"
               :visible.sync="opInfo.visible"
               width="960px">
      <cluster-comm-op-details :rankID="opInfo.rankID"
                               :dataset="opInfo.dataset">
      </cluster-comm-op-details>
    </el-dialog>
  </div>
</template>

<script>
import echarts, {echartsThemeName} from '@/js/echarts';
import RequestService from '@/services/request-service';
import empty, {NO_DATA, LOADING_DATA} from '@/components/empty';
import clusterCommOpDetails from '@/components/cluster-comm-op-details';
import {keepDecimalPlaces} from '@/js/utils';

const TIME_UNIT = '(ms)';

const SIZE_UNIT = '(KB)';

const BAND_UNIT = '(KB/s)';

const DEFAULT_DECIMAL_PLACES = 4;

export default {
  components: {
    empty,
    clusterCommOpDetails,
  },
  data() {
    return {
      pageState: LOADING_DATA,
      normalState: 'normal', // Normal page state
      tabNames: ['chart', 'table'],
      tab: null, // Selected tab name
      trainInfo: {
        id: this.$route.query.id,
        path: this.$route.query.path,
        dir: this.$route.query.dir,
      }, // Complete train info
      activeName: this.$route.query.activeName, // Active name of cluster dashboard tab
      chartInstance: null, // chart instance
      chartResizeTimer: null, // delay after the window size is changed
      tableData: [], // Data of page default table
      tableDefaultSort: null, // Default sort of page default chart
      tableProps: [
        {
          label: this.$t('profilingCluster.rankID'),
          prop: 'rank_id',
        },
        {
          label: this.$t('profilingCluster.commCost') + TIME_UNIT,
          prop: 'communication_cost',
        },
        {
          label: this.$t('profilingCluster.waitCost') + TIME_UNIT,
          prop: 'wait_cost',
        },
        {
          label: this.$t('profiling.operatorDetail'),
        },
        {
          label: this.$t('profilingCluster.linkInfo'),
        },
      ], // Page default table header label and column prop name
      pageCondition: {
        page: 1,
        limit: 10,
        sizes: [10, 20, 50],
        total: 0,
      }, // Page setting of default page chart
      sortCondition: {}, // sort condition of page default table
      step: {
        min: 1,
        max: null,
        value: '',
        last: null,
      }, // Step info of filter default page chart
      stepTip: this.$t('profiling.stepInputTip'), // Tip of step filter
      linkInfo: {
        title: this.$t('profilingCluster.linkInfo'),
        visible: false,
        filterType: this.$t('public.all'),
        linkTypes: [this.$t('public.all')],
        tableData: [],
        totalData: [],
        tableHeight: '0px',
      }, // Link info dialog data
      linkTableProps: [
        {
          label: this.$t('profilingCluster.linkRange'),
          prop: 'src_dst',
        },
        {
          label: this.$t('profilingCluster.commCost') + TIME_UNIT,
          prop: 'communication_cost',
        },
        {
          label: this.$t('profilingCluster.commSize') + SIZE_UNIT,
          prop: 'communication_size',
        },
        {
          label: this.$t('profilingCluster.bandWidth') + BAND_UNIT,
          prop: 'band_width',
        },
        {
          label: this.$t('profilingCluster.linkType'),
          prop: 'link_type',
        },
      ], // Link info table header label and column prop name
      linkDefaultSort: null, // Default sort of link table
      linkTable: {
        tableData: [],
        sortCondition: {},
        filter: {
          step_id: '',
          src_rank: '',
          dst_rank: '',
          link_type: this.$t('public.all'),
        }, // Filter of link table
        params: null,
        linkTypes: [],
        pageCondition: {
          page: 1,
          limit: 20,
          sizes: [10, 20, 50],
          total: 0,
        }, // Page setting of link table
      },
      opInfo: {
        title: this.$t('profiling.operatorDetail'),
        visible: false,
        dataID: null,
        dataset: [],
      },
    };
  },
  created() {
    // Set default tab
    this.tab = this.tabNames[0];
    // Set default sort of page default table and link table
    this.tableDefaultSort = this.linkDefaultSort = {
      prop: 'communication_cost',
      order: 'descending',
    };
    this.sortCondition = {
      name: 'communication_cost',
      type: 'descending',
    };
    this.linkInfo.sortCondition = {
      name: 'communication_cost',
      type: 'descending',
    };
  },
  mounted() {
    if (!this.trainInfo.id) {
      this.$message.error(this.$t('trainingDashboard.invalidId'));
      document.title = `${this.$t('profilingCluster.commChartTitle')}-MindInsight`;
      this.pageState = NO_DATA;
      return;
    }
    document.title = `${this.trainInfo.path}-${this.$t('profilingCluster.commChartTitle')}-MindInsight`;
    // Add chart resize Listener
    window.addEventListener('resize', this.resizeCallback);
    this.initPage();
    this.initLinkTable();
  },
  beforeDestroy() {
    // remove the size of a window and change the listener
    window.removeEventListener('resize', this.resizeCallback);
    // remove chart calculation delay
    if (this.chartResizeTimer) {
      clearTimeout(this.chartResizeTimer);
      this.chartResizeTimer = null;
    }
  },
  methods: {
    /**
     *  The logic of change happen when click tab
     *  @param {Object} tab
     */
    handleTabClick(tab) {
      if (this.tabNames[0] === tab.name) {
        this.$nextTick(() => {
          if (this.chartInstance) {
            this.chartInstance.resize();
          }
        });
      }
    },
    /**
     *  The logic of change happen filter happened
     */
    filterLinkTable() {
      this.linkTable.pageCondition.page = 1;
      const params = this.useLinkParams();
      this.useLinkTable(params);
    },
    /**
     *  The logic of init link table
     */
    initLinkTable() {
      const params = this.useLinkParams(true);
      this.useLinkTable(params);
    },
    /**
     *  The logic of change happen when table page index changed
     *  @param {number} val
     */
    linkTablePageChange(val) {
      const params = this.linkTable.params;
      params.body.group_condition.offset = val - 1;
      this.useLinkTable(params);
    },
    /**
     *  The logic of change happen when table size changed
     *  @param {number} val
     */
    linkTableSizeChange(val) {
      const params = this.linkTable.params;
      this.linkTable.pageCondition.page = 1;
      params.body.group_condition.offset = 0;
      params.body.group_condition.limit = this.linkTable.pageCondition.limit = val;
      this.useLinkTable(params);
    },
    /**
     *  The logic of change happen when table sort type changed
     *  @param {Object} column
     */
    linkTableSortChange(column) {
      this.linkTable.pageCondition.page = 1;
      this.linkTable.sortCondition = {
        name: column.prop,
        type: column.order,
      };
      const params = this.useLinkParams();
      this.useLinkTable(params);
    },
    /**
     *  The logic of use params used to query link info table
     *  @param {Boolean} isInit
     *  @return {Object}
     */
    useLinkParams(isInit = false) {
      const params = {
        params: {
          train_id: this.trainInfo.id,
        },
        body: {
          group_condition: {
            offset: this.linkTable.pageCondition.page - 1,
            limit: this.linkTable.pageCondition.limit,
          },
        },
      };
      if (this.linkTable.sortCondition.type) {
        params.body.sort_condition = this.linkTable.sortCondition;
      }
      if (isInit) {
        return params;
      }
      const filterCondition = JSON.parse(JSON.stringify(this.linkTable.filter));
      Object.keys(filterCondition).forEach((key) => {
        if (key === 'link_type' && filterCondition[key] === this.$t('public.all')) {
          Reflect.deleteProperty(filterCondition, key);
          return;
        }
        if (!filterCondition[key].length) {
          Reflect.deleteProperty(filterCondition, key);
        }
      });
      if (Object.keys(filterCondition).length) {
        params.body.filter_condition = filterCondition;
      }
      return params;
    },
    /**
     *  The logic of use link table
     *  @param {Object} params
     */
    useLinkTable(params) {
      RequestService.getLinkInfo(params).then((res) => {
        // Save query params
        this.linkTable.params = params;
        if (res?.data?.cluster_link_info.length > 0) {
          this.linkTable.pageCondition.total = res.data.size;
          const tableData = [];
          const types = [this.$t('public.all')];
          res.data.cluster_link_info.forEach((info) => {
            // Init link types when first query
            if (!this.linkTable.linkTypes.length && !types.includes(info[1])) {
              types.push(info[1]);
            }
            tableData.push({
              src_dst: info[0],
              link_type: info[1],
              communication_cost: keepDecimalPlaces(info[2], DEFAULT_DECIMAL_PLACES),
              communication_size: keepDecimalPlaces(info[3], DEFAULT_DECIMAL_PLACES),
              band_width: keepDecimalPlaces(info[4], DEFAULT_DECIMAL_PLACES),
            });
          });
          if (!this.linkTable.linkTypes.length) {
            this.linkTable.linkTypes = types;
          }
          this.linkTable.tableData = tableData;
        } else {
          this.linkTable.pageCondition.total = 0;
          this.linkTable.tableData = [];
        }
      });
    },
    /**
     *  The logic of init page data
     */
    initPage() {
      this.pageCondition.page = 1;
      const params = this.useParams(true);
      this.queryCommInfo(params).then((res) => {
        if (res) {
          this.usePage(res);
        }
      });
    },
    /**
     * The logic of query comm info
     * @param {Object} params
     * @return {Promise}
     */
    queryCommInfo(params) {
      return new Promise((resolve) => {
        RequestService.getCommInfo(params)
            .then((res) => {
              if (res?.data?.communication.length > 0) {
                resolve(res.data);
              } else {
                this.pageState = NO_DATA;
                resolve(false);
              }
            })
            .catch(() => {
              this.pageState = NO_DATA;
              resolve(false);
            });
      });
    },
    /**
     *  The logic of use complete page
     *  @param {Object} data
     */
    usePage(data) {
      this.step.max = data.total_step_num;
      this.stepTip = this.$t('profiling.stepInputTip', {max: this.step.max});
      this.pageCondition.total = data.size;
      this.useChart(data.communication);
      this.useTable(data.communication);
      this.pageState = this.normalState;
    },
    /**
     *  The logic of use request params
     *  @param {Boolean} isInit
     *  @return {Object}
     */
    useParams(isInit = false) {
      const params = {
        params: {
          train_id: this.trainInfo.id,
        },
        body: {},
      };
      if (this.sortCondition.type) {
        params.body.sort_condition = this.sortCondition;
      }
      if (!isInit) {
        params.body.group_condition = {
          offset: this.pageCondition.page - 1,
          limit: this.pageCondition.limit,
        };
      }
      if (this.step.value !== '') {
        params.body.filter_condition = {
          step_id: this.step.value,
        };
      }
      return params;
    },
    /**
     * The logic of use echart
     * @param {Array} data
     */
    useChart(data) {
      const chartData = [];
      data.forEach((item) => {
        chartData.push([
          item.rank_id,
          keepDecimalPlaces(item.communication_info[0], DEFAULT_DECIMAL_PLACES),
          keepDecimalPlaces(item.communication_info[1], DEFAULT_DECIMAL_PLACES),
        ]);
      });
      const options = this.getEChartsOptions(chartData);
      this.$nextTick(() => {
        if (!this.chartInstance) {
          this.chartInstance = echarts.init(this.$refs.commChart, echartsThemeName);
        }
        this.chartInstance.setOption(options, true);
      });
    },
    /**
     *  The logic of use table
     *  @param {Array} data response data
     */
    useTable(data) {
      const tempData = data.length > this.pageCondition.limit ? data.slice(0, this.pageCondition.limit) : data;
      const tableData = [];
      tempData.forEach((item) => {
        const info = item.communication_info;
        tableData.push({
          rank_id: item.rank_id,
          communication_cost: keepDecimalPlaces(info[0], DEFAULT_DECIMAL_PLACES),
          wait_cost: keepDecimalPlaces(info[1], DEFAULT_DECIMAL_PLACES),
          info: info[2],
          op_info: info[3],
        });
      });
      this.tableData = tableData;
    },
    /**
     * Window resize
     */
    resizeCallback() {
      if (this.chartResizeTimer) {
        clearTimeout(this.chartResizeTimer);
      }
      this.chartResizeTimer = setTimeout(() => {
        if (this.chartInstance) {
          this.chartInstance.resize();
        }
        this.chartResizeTimer = null;
      }, 200);
    },
    /**
     * The logic of show operator info
     * @param {Object} row
     */
    showOpInfo(row) {
      this.opInfo.dataset = row.op_info;
      this.opInfo.rankID = row.rank_id;
      this.opInfo.visible = true;
    },
    /**
     * The logic of show link info
     * @param {Object} row
     */
    showLinkInfo(row) {
      const tableData = [];
      const types = [this.$t('public.all')];
      Object.keys(row.info).forEach((range) => {
        Object.keys(row.info[range]).forEach((type) => {
          if (!types.includes(type)) types.push(type);
          const value = row.info[range][type];
          tableData.push({
            src_dst: range,
            communication_cost: keepDecimalPlaces(value[0], DEFAULT_DECIMAL_PLACES),
            communication_size: keepDecimalPlaces(value[1], DEFAULT_DECIMAL_PLACES),
            band_width: keepDecimalPlaces(value[2], DEFAULT_DECIMAL_PLACES),
            link_type: type,
          });
        });
      });
      this.linkInfo.linkTypes = types;
      this.linkInfo.totalData = tableData;
      this.linkInfo.filterType = types[0];
      this.filterLinkInfo();
      this.linkInfo.visible = true;
    },
    /**
     * The logic of filter total link info
     */
    filterLinkInfo() {
      if (this.linkInfo.filterType === this.$t('public.all')) {
        this.linkInfo.tableData = this.linkInfo.totalData;
      } else {
        this.linkInfo.tableData = this.linkInfo.totalData.filter((data) => {
          return data.link_type === this.linkInfo.filterType;
        });
      }
      const tableHeight = (this.linkInfo.tableData.length + 1) * 42; // 42: The table default line-height in 'px'
      this.linkInfo.tableHeight = `${tableHeight > 600 ? 600 : tableHeight}px`; // 600: The table max-height in 'px'
    },
    /**
     * Current page change
     * @param {Number} val current page
     */
    currentPageChange(val) {
      this.pageCondition.page = val;
      const params = this.useParams();
      this.queryCommInfo(params).then((res) => {
        this.useTable(res.communication);
      });
    },
    /**
     * Page size change
     * @param {Number} pageSize current page size
     */
    pageSizeChange(pageSize) {
      this.pageCondition.page = 1;
      this.pageCondition.limit = pageSize;
      const params = this.useParams();
      this.queryCommInfo(params).then((res) => {
        this.useTable(res.communication);
      });
    },
    /**
     * Table sort change
     * @param {Object} column current column
     */
    tableSortChange(column) {
      this.sortCondition = {
        name: column.prop,
        type: column.order,
      };
      this.pageCondition.page = 1;
      const params = this.useParams(true);
      this.queryCommInfo(params).then((res) => {
        this.useChart(res.communication);
        this.useTable(res.communication);
      });
    },
    /**
     * The logic of filter by step
     */
    stepFilter() {
      if (this.step.last === this.step.value) {
        // Same value, no need to send request
        return;
      }
      const strValue = this.step.value;
      if (strValue === '') {
        this.initPage();
        this.step.last = strValue;
        return;
      }
      const intValue = parseInt(strValue);
      if (intValue.toString() === strValue && this.step.min <= intValue && intValue <= this.step.max) {
        this.initPage();
        this.step.last = strValue;
        return;
      }
      this.step.value = this.step.last;
      this.$message.error(this.$t('profiling.inputError').replace('{max}', this.step.max));
    },
    /**
     * The logic of get data which used to set echarts
     * @param {Array} source
     * @return {Object}
     */
    getEChartsOptions(source) {
      const endValue = source.length > 25 ? 25 : source.length; // Default displayed bar number
      return {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow',
          },
        },
        legend: {
          right: 70,
          top: 8,
          data: [
            this.$t('profilingCluster.commCost'),
            this.$t('profilingCluster.waitCost'),
          ],
        },
        grid: {
          top: 35,
          left: 80,
          right: 80,
        },
        dataset: {
          source: [[
            this.$t('profilingCluster.rankID'),
            this.$t('profilingCluster.commCost'),
            this.$t('profilingCluster.waitCost'),
          ]].concat(source),
        },
        xAxis: {
          name: this.$t('profilingCluster.rankID'),
          nameTextStyle: {
            align: 'left',
            padding: [0, 5],
          },
          type: 'category',
        },
        yAxis: {
          name: this.$t('profilingCluster.timeTitle'),
          nameGap: 20,
          nameTextStyle: {
            align: 'right',
            padding: [0, 5],
          },
          splitLine: {
            lineStyle: {
              type: 'dashed',
            },
          },
        },
        series: [
          {type: 'bar', barWidth: 8},
          {type: 'bar', barWidth: 8},
        ],
        dataZoom: [
          {
            startValue: 0,
            endValue: endValue,
          },
          {
            startValue: 0,
            endValue: endValue,
            type: 'inside',
          },
        ],
      };
    },
    /**
     * The logic of return cluster dashboard
     */
    backToDashboard() {
      this.$router.push({
        path: 'cluster-dashboard',
        query: Object.assign({
          activeName: this.activeName,
        }, this.trainInfo),
      });
    },
  },
};
</script>
<style>
.cl-comm .el-dialog__body {
  padding: 20px;
}
.cl-comm .el-tabs__item {
  font-size: 14px;
  line-height: 14px;
  height: 27px;
}
.cl-comm .el-tabs__item .is-active {
  color: var(--theme-color);
  font-weight: bold;
}
.comm-tooltip-container {
  padding: 10px;
}
.comm-tooltip-container .comm-tooltip-cell {
  width: 100%;
  line-height: 24px;
}
.comm-tooltip-container .comm-tooltip-cell span:first-of-type{
  font-weight: bold;
}
</style>
<style scoped>
.cl-comm {
  height: 100%;
  background-color: var(--bg-color);
  display: flex;
  flex-direction: column;
}
.cl-comm .el-select {
  width: 120px;
  margin: 0 20px;
}
.cl-comm .comm-content {
  flex-grow: 1;
  display: flex;
  justify-content: center;
  width: 100%;
  flex-direction: column;
  overflow: hidden;
}
.comm-content .content-filter {
  height: 32px;
  display: flex;
  align-items: center;
  margin-bottom: 5px;
  flex-shrink: 0;
  padding-left: 10px;
}
.comm-content .content-filter .el-input {
  width: 120px;
  margin: 0 20px;
}
.comm-content .content-filter .el-button {
  padding: 7px 15px;
  color: var(--theme-color);
  border-color: var(--theme-color);
}
.comm-content .content-chart {
  height: 280px;
  margin-bottom: 20px;
  flex-shrink: 0;
}
.comm-content .content-table {
  height: calc(100% - 84px);
  margin-bottom: 10px;
}
.comm-content .content-link-table {
  height: calc(100% - 84px);
  margin-bottom: 10px;
}
.content-table .table-button {
  color: var(--theme-color);
  cursor: pointer;
}
.comm-content .content-pagination {
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-shrink: 0;
}
.cl-comm .dialog-pagination {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}
.cl-comm .dialog-content {
  max-height: 600px;
}
</style>

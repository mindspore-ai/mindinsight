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
  <div class="cluster-comm-op-details-modal">
    <div class="modal-content">
      <div class="content-header">
        <el-input v-model="searchOperatorStr"
                  @change="filterOperator"
                  @clear="filterOperator"
                  :placeholder="$t('operator.searchByName')"></el-input>
      </div>
      <!-- Total Operator -->
      <div class="content-container">
        <el-table :data="displayOperatorDataset"
                  @expand-change="onExpandTable"
                  height="100%">
          <!-- Single Operator Expand -->
          <el-table-column type="expand">
            <template>
              <el-table :data="displayLinkDataset"
                        height="100%">
                <!-- Column 1 / link_relationship -->
                <el-table-column :label="linkRel.label"
                                 :prop="linkRel.prop"
                                 width="130">
                </el-table-column>
                <!-- Column 2 / communication_duration -->
                <el-table-column :label="commDur.label"
                                 :prop="commDur.prop"
                                 sortable>
                </el-table-column>
                <!-- Column 3 / communication_size -->
                <el-table-column :label="commSize.label"
                                 :prop="commSize.prop"
                                 width="190"
                                 sortable>
                </el-table-column>
                <!-- Column 4 / band_width -->
                <el-table-column :label="bandwidth.label"
                                 :prop="bandwidth.prop"
                                 width="190"
                                 sortable>
                </el-table-column>
                <!-- Column 5 / link_type -->
                <el-table-column :label="linkType.label"
                                 :prop="linkType.prop"
                                 width="90">
                </el-table-column>
              </el-table>
            </template>
          </el-table-column>
          <!-- Column 1 / op_name -->
          <el-table-column :label="opName.label"
                           :prop="opName.prop">
          </el-table-column>
          <!-- Column 2 / communication_duration -->
          <el-table-column :label="commDur.label"
                           :prop="commDur.prop"
                           :sortable="true">
          </el-table-column>
          <!-- Column 3 / wait_duration -->
          <el-table-column :label="waitDur.label"
                           :prop="waitDur.prop"
                           :sortable="true">
          </el-table-column>
        </el-table>
      </div>
      <div class="content-pagination">
        <el-pagination @size-change="onPageSizeChange"
                       @current-change="onCurrentPageChange"
                       :current-page="pageInfo.currentPage"
                       :page-sizes="pageInfo.pageSizes"
                       :page-size="pageInfo.pageSize"
                       layout="total, sizes, prev, pager, next, jumper"
                       :total="pageInfo.total">
        </el-pagination>
      </div>
    </div>
  </div>
</template>

<script>
import {keepDecimalPlaces} from '../js/utils';

const TIME_UNIT = '(ms)';
const SIZE_UNIT = '(KB)';
const BAND_UNIT = '(KB/s)';
const DEFAULT_PAGESIZE = 20;
const DEFAULT_DECIMAL_PLACES = 4;

export default {
  props: {
    rankID: Number,
    dataset: Object,
  },
  data() {
    return {
      // Labels and props of column
      opName: {label: this.$t('profilingCluster.opName'), prop: 'opName'},
      commDur: {label: this.$t('profilingCluster.commCost') + TIME_UNIT, prop: 'commDur'},
      commSize: {label: this.$t('profilingCluster.commSize') + SIZE_UNIT, prop: 'commSize'},
      waitDur: {label: this.$t('profilingCluster.waitCost') + TIME_UNIT, prop: 'waitDur'},
      bandwidth: {label: this.$t('profilingCluster.bandWidth') + BAND_UNIT, prop: 'bandwidth'},
      linkRel: {label: this.$t('profilingCluster.linkRange'), prop: 'linkRel'},
      linkType: {label: this.$t('profilingCluster.linkType'), prop: 'linkType'},
      totalOperatorDataset: [],
      filterOperatorDataset: [],
      displayOperatorDataset: [],
      displayLinkDataset: [],
      pageInfo: {
        currentPage: null,
        total: null,
        pageSize: null,
        pageSizes: [10, 20, 50],
      }, // Page info of operator list
      searchOperatorStr: '', // String of filter
    };
  },
  created() {
    this.initOperatorTable();
  },
  methods: {
    /**
     * The logic of init operator table
     */
    initOperatorTable() {
      if (!this.dataset) {
        const pageInfo = this.pageInfo;
        pageInfo.currentPage = 1;
        pageInfo.total = 0;
        pageInfo.pageSize = DEFAULT_PAGESIZE;
        return;
      }
      const operatorDataset = [];
      Object.keys(this.dataset).forEach((opName) => {
        const operator = this.dataset[opName];
        operatorDataset.push({
          opName,
          commDur: keepDecimalPlaces(operator[1], DEFAULT_DECIMAL_PLACES),
          waitDur: keepDecimalPlaces(operator[2], DEFAULT_DECIMAL_PLACES),
          linkInfo: operator[3],
        });
      });
      this.searchOperatorStr = '';
      this.totalOperatorDataset = operatorDataset;
      this.filterOperatorDataset = operatorDataset;
      this.pageInfo.total = this.filterOperatorDataset.length;
      this.onPageSizeChange(DEFAULT_PAGESIZE);
    },
    /**
     * The logic of table expanded
     * @param {Object} linkInfo
     */
    initExpandTable(linkInfo) {
      const displayLinkDataset = [];
      Object.keys(linkInfo).forEach((linkRel) => {
        const linkTypeInfo = linkInfo[linkRel];
        Object.keys(linkTypeInfo).forEach((linkType) => {
          const linkUnitInfo = linkTypeInfo[linkType];
          displayLinkDataset.push({
            linkRel,
            commDur: keepDecimalPlaces(linkUnitInfo[0], DEFAULT_DECIMAL_PLACES),
            commSize: keepDecimalPlaces(linkUnitInfo[1], DEFAULT_DECIMAL_PLACES),
            bandwidth: keepDecimalPlaces(linkUnitInfo[2], DEFAULT_DECIMAL_PLACES),
            linkType,
          });
        });
      });
      this.displayLinkDataset = displayLinkDataset;
    },
    /**
     * The logic of table expanded
     * @param {Object} row
     */
    onExpandTable(row) {
      this.initExpandTable(row.linkInfo);
    },
    /**
     * The logic of page size changed
     * @param {Number} val
     */
    onPageSizeChange(val) {
      this.pageInfo.pageSize = val;
      this.pageInfo.currentPage = 1;
      this.displayOperatorDataset = this.filterOperatorDataset.slice(0, val);
    },
    /**
     * The logic of current page changed
     * @param {Number} val
     */
    onCurrentPageChange(val) {
      this.pageInfo.currentPage = val;
      const size = this.pageInfo.pageSize;
      this.displayOperatorDataset = this.filterOperatorDataset.slice((val - 1) * size, val * size);
    },
    /**
     * The logic of filter operator
     * @param {string} filterStr
     */
    filterOperator(filterStr) {
      this.filterOperatorDataset = this.totalOperatorDataset.filter((op) => {
        return op.opName.includes(filterStr);
      });
      this.pageInfo.total = this.filterOperatorDataset.length;
      // Reset currentPage to 1
      this.onCurrentPageChange(1);
    },
  },
  watch: {
    rankID() {
      setTimeout(() => {
        this.initOperatorTable();
      }, 0);
    },
  },
};
</script>

<style>
.cluster-comm-op-details-modal .modal-content .content-header {
  height: 36px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.cluster-comm-op-details-modal .modal-content .content-header .el-input {
  width: 240px;
}
.cluster-comm-op-details-modal .modal-content .content-header .el-radio-button__inner {
  padding: 10px 12px;
}
.cluster-comm-op-details-modal .modal-content .content-container {
  height: 400px;
}
.cluster-comm-op-details-modal .modal-content .content-pagination {
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}
</style>

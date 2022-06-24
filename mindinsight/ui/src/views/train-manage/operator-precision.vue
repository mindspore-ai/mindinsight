<!--
Copyright 2021-2022 Huawei Technologies Co., Ltd.All Rights Reserved.

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
    <div class="cl-operator">
      <div class="operator-tab">
        <span class="operator-tab-item item-active">
          {{$t("operatorPrecision.title")}}
        </span>
        <span class="operator-path">
          <span>{{$t('symbols.leftbracket')}}</span>
          <span>{{$t('trainingDashboard.summaryDirPath')}}</span>
          <span>{{summaryPath}}</span>
          <span>{{$t('symbols.rightbracket')}}</span>
        </span>
        <span class="cl-title-right">
          <span class="cl-close-btn" @click="jumpToTrainDashboard">
            <img :src="require('@/assets/images/close-page.png')">
          </span>
        </span>
      </div>
      <div class="operator-container">
        <el-input v-model="operatorSelectName" 
                  :placeholder="placeTitle" 
                  class="operator-name-input"></el-input>
        <el-button type="primary" 
                   icon="el-icon-search" 
                   @click="filterOperator">{{searchBtn}}</el-button>
        <el-button type="success" @click="downloadOperator">
          <el-icon class="el-icon-download"></el-icon>{{download}}
        </el-button>
        <div class="cl-operator-file">
          <el-tooltip effect="light" placement="top">
            <div slot="content" 
                 class="tooltip-container">
              {{$t('graph.sidebarTip')}}
            </div>
            <i class="el-icon-info"></i>
          </el-tooltip>
          <span class="pie-select-style">
            <el-select v-model="getPbName" class="search" placeholder="search">
                <el-option
                    v-for="item in fileSearchBox.pbFileNameOptions"
                    :key="item.index"
                    :label="item.label"
                    :value="item.label">
                </el-option>
            </el-select>
          </span>
        </div>
      </div>
      <div class="table-container">
        <el-table
            ref="table"
            :data="getTableData"
            border
            tooltip-effect="light"
            :header-cell-style="headerStyle"
            :cell-style="cellStyle"
            style="width: 100%">
            <el-table-column
                prop="id"
                label="ID"
                width="55">
            </el-table-column>
            <el-table-column
                prop="op_name"
                label="op_name"
                min-width="10%">
            </el-table-column>
            <el-table-column
                prop="name"
                label="fullname_with_scope"
                min-width="20%">
              <template slot-scope="scope">
                  <el-popover width="90%" 
                              trigger="hover" 
                              placement="top">
                    <p>{{scope.row.name}}</p>
                    <div slot="reference" class="name-wrapper">
                      <el-tag size="medium">
                        {{scope.row.name.length > 80 ? scope.row.name.substr(0, 80)+'...' : scope.row.name}}
                      </el-tag>
                    </div>
                  </el-popover>
              </template>
            </el-table-column>
            <el-table-column
                prop="type"
                label="op_type"
                min-width="10%">
            </el-table-column>
            <el-table-column
                prop="precision_flag"
                label="precision_flag"
                min-width="12%">
            </el-table-column>
            <el-table-column
              label="is_reduce_flag"
              min-width="8%">
              <template slot-scope="scope">
                <div>{{scope.row.reduce_flag}}
                  <i class="el-icon-bottom" v-show="scope.row.reduce_flag == 'reduce'"></i>
                  <i class="el-icon-top" v-show="scope.row.reduce_flag == 'raise'"></i>
                </div>
              </template>
            </el-table-column>
            <el-table-column
                label="Input" min-width="3%">
              <template slot-scope="scope">
                <el-button @click="viewOperatorInput(scope.row.input)" 
                           type="text" 
                           size="small">{{view}}</el-button>
              </template>
            </el-table-column>
            <el-table-column
                label="Output" min-width="3%">
              <template slot-scope="scope">
                <el-button @click="viewOperatorInput(scope.row.output)" 
                           type="text" 
                           size="small">{{view}}</el-button>
              </template>
            </el-table-column>
        </el-table>
        <div class="pagination-container">
          <el-pagination
              background
              @current-change="handlePageChange"
              @size-change="handleSizeChange"
              :current-page="pagination.currentPage"
              :page-size="pagination.pageSize"
              :page-sizes="pagination.pageSizes"
              :layout="pagination.layout"
              :total="pagination.total">
          </el-pagination>
        </div>
      </div>
      <div v-if="showInputDialog" class="operator-shape-dialog">
        <el-dialog
            title="op_input_detail"
            :visible.sync="showInputDialog"
            width="60%"
            :close-on-click-modal="false"
            class="details-data-list">
            <el-table
                :data="inputShapeData"
                row-key="id"
                lazy
                width="100%"
                :close-on-click-modal4="false"
                tooltip="light">
                <el-table-column
                    property="id"
                    label="Id"
                    type="index"
                    min-width="10%">
                </el-table-column>
                <el-table-column
                    property="key"
                    label="op_name"
                    min-width="40%">
                </el-table-column>
                <el-table-column
                    property="value"
                    label="op_value"
                    min-width="60%">
                    <template slot-scope="scope">
                      {{scope.row.value}}
                    </template>
                </el-table-column>
            </el-table>
        </el-dialog>
      </div>
      <div v-if="showOutputDialog" class="operator-shape-dialog">
        <el-dialog
            title="op_output_detail"
            :visible.sync="showOutputDialog"
            width="60%"
            :close-on-click-modal="false"
            class="details-data-list">
            <el-table
                :data="outputShapeData"
                row-key="id"
                lazy
                width="100%"
                :close-on-click-modal4="false"
                tooltip="light">
                <el-table-column
                    property="id"
                    label="Id"
                    type="index"
                    min-width="10%">
                </el-table-column>
                <el-table-column
                    property="key"
                    label="op_name"
                    min-width="40%">
                </el-table-column>
                <el-table-column
                    property="value"
                    label="op_value"
                    min-width="60%">
                    <template slot-scope="scope">
                      {{scope.row.value}}
                    </template>
                </el-table-column>
            </el-table>
        </el-dialog>
      </div>
    </div>
</template>

<script>
import RequestService from '@/services/request-service';
export default {
  data() {
    return {
      placeTitle: this.$t('operatorPrecision.placeTitle'),
      searchBtn: this.$t('operatorPrecision.searchBtn'),
      download: this.$t('operatorPrecision.download'),
      view: this.$t('operatorPrecision.view'),
      tableData: [],
      tableTotalData: [],
      operatorSelectName: null,
      pbSelectName: null,
      summaryPath: this.$route.query.summaryPath,
      language: '',
      themeIndex: this.$store.state.themeIndex,
      trainJobID: '',
      fileSearchBox: {
        value: '',
        pbFileNameOptions: [],
      },
      pagination: {
        currentPage: 1,
        pageSize: 10,
        pageSizes: [10, 20, 50],
        total: 0,
        layout: 'total, sizes, prev, pager, next, jumper',
        pageChange: {},
        currentPagesizeChange: {},
      },
      inputShapeData: [],
      outputShapeData: [],
      showInputDialog: false,
      showOutputDialog: false,
    }
  },
  mounted() {
    this.trainJobID = this.$route.query.train_id;
    this.language = window.localStorage.getItem('milang');
    const languageList = ['zh-cn', 'en-us'];
    if (!this.language || !languageList.includes(this.language)) {
        this.language = languageList[0];
        window.localStorage.setItem('milang', this.language);
    }
    this.getDatavisualPlugins();
  },
  methods: {
    /**
     * filter the operator
     */
    filterOperator() {
      let arr = [];
      this.tableTotalData.forEach((item) => {
        if (item.name.indexOf(this.operatorSelectName) != -1) {
          arr.push(item);
        }
      });
      this.pagination.total = arr.length;
      this.tableData = arr;
    },
    /**
     * to obtain datavisual plugins 
     */
    getDatavisualPlugins() {
      const params = {
        mode: 'normal',
        train_id: this.trainJobID,
      };
      RequestService.getDatavisualPlugins(params)
        .then((res) => {
          if (res && res.data && res.data.plugins) {
            const plugins = res.data.plugins;
            plugins.graph.forEach((item, index) => {
              this.fileSearchBox.pbFileNameOptions.push({index: index, label: item});
            })
            this.pbSelectName = this.fileSearchBox.pbFileNameOptions[0].label;
            return new Promise((resolve) => {
              resolve(this.queryAllGraphNodesData());
            })
          }
        }).catch(() => {
          this.fileSearchBox.pbFileNameOptions = [];
        })
    },
    /**
     * set table header style
     */
    headerStyle() {
      return {
        background: '#EBEEF5',
        color: '#282B33',
        textAlign: 'center',
        fontSize: '18px',
      }
    },
    /**
     * set table row style 
     * @param {Object} row table row
     */
    cellStyle(row) {
      if (row.columnIndex != 1 && row.columnIndex != 2) {
        return {
          'text-align': 'center',
        }
      }
    },
    /**
     * view operator input detail
     */
    viewOperatorInput(input) {
      this.showInputDialog = true;
      let inputArr = [];
      let inputData = JSON.parse(input);
      Object.keys(inputData).forEach((key) => {
        inputArr.push({key: key, value: inputData[key]});
      });
      this.inputShapeData = inputArr;
    },
    /**
     * view operator output detail
     */
    viewOperatorOutput(output) {
      this.showOutputDialog = true;
      let outputArr = [];
      let outputData = JSON.parse(output);
      Object.keys(outputData).forEach((key) => {
        outputArr.push({key: key, value: outputData[key]});
      });
      this.outputShapeData = outputArr;
    },
    /**
     * Jump back to train dashboard
     */
    jumpToTrainDashboard() {
      this.$router.push({
        path: '/train-manage/training-dashboard',
        query: {
          id: this.trainJobID,
        },
      });
    },
    /**
     * get all nods data
     */
    queryAllGraphNodesData() {
      this.fileSearchBox.value = this.pbSelectName;
      const params = {
        train_id: this.trainJobID,
        tag: this.fileSearchBox.value,
        mode: 'normal',
      };
      RequestService.queryAllGraphNodesData(params)
        .then(
          (response) => {
            if (response && response.data) {
              let data = response.data.all_nodes_detail;
              let showData = [];
              let id = 0;
              data.forEach((item) => {
                id++;
                const name = item.name;
                const op_name = name.split("/").at(-1);
                const type = item.type;
                const input = JSON.stringify(item.input);
                const output = JSON.stringify(item.output);
                const precision_flag = item.attr.hasOwnProperty('precision_flag') ? 
                                            item.attr.precision_flag : 'null';
                let reduce_flag = "null";
                if (precision_flag != 'null') {
                  if (precision_flag.indexOf('reduce') != -1) {
                    reduce_flag = 'reduce';
                  } else {
                    reduce_flag = 'raise';
                  }
                  showData.unshift({id:id, op_name: op_name, name: name, type: type, precision_flag: precision_flag, 
                                    reduce_flag: reduce_flag, input: input, output: output});
                } else {
                  showData.push({id: id, op_name: op_name, name: name, type: type, precision_flag: precision_flag,
                                 reduce_flag: reduce_flag, input: input, output: output});
                }
              })
              this.tableData = showData;
              this.tableTotalData = this.tableData;
              this.pagination.total = showData.length || 0;
            }
          },
          (error) => {
            thi.loading.show = false;
          }
        ).catch((error) => {
          thi.loading.show = false;
        })
    },
    /**
     * download operator info to json
     */
    downloadOperator() {
      const downloadLink = document.createElement('a');
      downloadLink.download = this.getDocName();
      downloadLink.style.display = 'none';
      const blob = new Blob([JSON.stringify(this.tableData)]);
      downloadLink.href = URL.createObjectURL(blob);
      document.body.appendChild(downloadLink);
      downloadLink.click();
      document.body.removeChild(downloadLink);
    },
    /**
     * Generate a download file name
     * @return {String}
     */
    getDocName() {
      const dealNumber = (value) => {
        const prefix = value < 10 ? '0' : '';
        return prefix + value;
      };
      const replacedPrefix = './';
      let dir = this.summaryPath;
      if (dir === replacedPrefix) dir = ' ';
      if (dir.startsWith(replacedPrefix)) dir = dir.replace(replacedPrefix, '');
      const date = new Date();
      const year = date.getFullYear();
      const mouth = dealNumber(date.getMonth() + 1);
      const day = dealNumber(date.getDate());
      const hour = dealNumber(date.getHours());
      const minute = dealNumber(date.getMinutes());
      const second = dealNumber(date.getSeconds());
      const millisecond = date.getMilliseconds();
      const timestamp = `${year}${mouth}${day}${hour}${minute}${second}${millisecond}`;
      return `operator_precision_${timestamp}.json`;
    },
    /**
     * page change
     * @param size: the page size
     */
    handleSizeChange(size) {
      this.pagination.pageSize = size;
    },
    /**
     * @param page: the current page
     */
    handlePageChange(page) {
      this.pagination.currentPage = page;
    }
  },
  computed: {
    getTableData() {
      let start = (this.pagination.currentPage - 1) * this.pagination.pageSize;
      if (start >= this.tableData.length) {
        start = 0;
      }
      let end = this.pagination.currentPage * this.pagination.pageSize;
      if (end >= this.tableData.length) {
        end = this.pagination.total;
      }
      const slice_data = this.tableData.slice(start, end);
      return slice_data.length > 10 ? slice_data.slice(0, 10) : slice_data;
    },
    getPbName: {
      get() {
        return this.pbSelectName;
      },
      set(val) {
        this.pbSelectName = val;
        this.queryAllGraphNodesData();
      }
    }
  }
}
</script>

<style scoped>
.cl-operator {
  height: 100%;
  background-color: var(--bg-color);
  overflow: auto;
}

.operator-tab {
  height: 51px;
  line-height: 56px;
  padding: 0 34px;
  border-bottom: 1px solid var(--table-border-color);
}

.cl-operator .operator-path {
  display: inline-block;
  line-height: 20px;
  padding: 0 4px 15px 4px;
  font-weight: bold;
  vertical-align: bottom;
}

.cl-operator .cl-title-right .cl-close-btn {
  position: sticky;
}

.cl-title-right {
  height: 51px;
  line-height: 56px;
  padding-right: 20px;
  position: absolute;
  right: 60px;
}

.cl-operator .table-container {
  width: 95%;
  margin: 0 auto;
}

.cl-operator .table-container .pagination-container {
  margin: 10px 0;
}

.cl-operator .operator-container {
  margin-top: 30px;
  width: 300px;
  margin-right: 20px;
}

.cl-operator .operator-name-input {
  margin-top: 30px;
  padding: 6px 32px 10px 2.5%;
}

.cl-operator .custom-btn-export {
  display: inline-block;
  width: 300px;
  margin-right: 20px;
}

.cl-operator .search {
  width: 300px;
}

.cl-operator .cl-operator-file {
  float: right;
  margin-left: 1vw;
}

.cl-operator .cl-operator-file .el-icon-info {
  font-size: 24px;
  height: 40px;
  line-height: 40px;
  vertical-align: bottom;
}

.operator-tab-item {
  padding: 0 10px;
  height: 48px;
  -webkit-box-sizing: border-box;
  box-sizing: border-box;
  line-height: 48px;
  display: inline-block;
  list-style: none;
  font-size: 18px;
  color: var(--el-tabs-item-color);
  position: relative;
}

.item-active {
  color: var(--theme-color);
  font-weight: bold;
  border-bottom: 3px solid var(--theme-color);
}

.operator-tab-item:hover {
  color: var(--theme-color);
  cursor: pointer;
}

.cl-operator .el-tag {
  background-color: #ecf5ff;
  display: inline-block;
  padding: 0 10px;
  font-size: 12px;
  color: #409eff;
  border: 1px solid #d9ecff;
  border-radius: 4px;
  box-sizing: border-box;
  white-space: nowrap;
}

.cl-operator .el-icon-buttom {
  padding-left: 2px;
  color: #f00;
}

.cl-operator .el-icon-top {
  padding-left: 2px;
  color: #409eff;
}
</style>

<style>
.cl-operator .operator-container .el-input__inner {
  height: 42px;
  line-height: 42px;
  border-radius: 6px;
}

.el-pagination.is-background .el-pager li:not(.disabled).active {
  color: #FFF;
  background-color: #409eff;
}
</style>
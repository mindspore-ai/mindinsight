<!--
Copyright 2020-2021 Huawei Technologies Co., Ltd.All Rights Reserved.

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
  <div id="cl-summary-manage">
    <div v-show="loading"
         class="no-data-page">
      <div class="no-data-img">
        <img :src="require('@/assets/images/nodata.png')"
             alt="" />
        <p class="no-data-text">{{$t("public.dataLoading")}}</p>
      </div>
    </div>
    <div class="cl-summary-manage-container"
         v-show="!loading">
      <div class="cl-title">
        <div class="cl-title-left">
          <span class="summary-title">{{$t('summaryManage.summaryList')}}</span>
          <span>{{$t("symbols.leftbracket")}}</span>
          <span>{{$t('summaryManage.currentFolder')}}</span>
          <span :title="currentFolder">{{currentFolder}}</span>
          <span>{{$t("symbols.rightbracket")}}</span>
          <div class="btn-wrap">
            <el-button size="mini"
                       class="custom-btn white"
                       :disabled="disableState"
                       @click="goToTracebackAnalysis()">{{ $t('summaryManage.tracebackAnalysis') }}</el-button>
            <el-button size="mini"
                       class="custom-btn white"
                       :disabled="disableState"
                       @click="goToCompareAnalysis()">{{ $t('summaryManage.compareAnalysis') }}</el-button>
          </div>
        </div>
      </div>

      <!--table content area -->
      <div class="container">
        <!-- list table -->
        <div class="list-table">
          <el-table :data="summaryList"
                    stripe
                    height="100%"
                    tooltip-effect="light"
                    class="list-el-table"
                    ref="table">
            <el-table-column width="50"
                             type=index
                             :label="$t('summaryManage.sorting')">
            </el-table-column>
            <el-table-column min-width="600"
                             prop="relative_path"
                             :label="$t('summaryManage.summaryPath')"
                             show-overflow-tooltip>
            </el-table-column>
            <el-table-column width="180"
                             prop="update_time"
                             :label="$t('summaryManage.updateTime')"
                             show-overflow-tooltip>
            </el-table-column>
            <!-- operate -->
            <el-table-column prop="operate"
                             :label="$t('summaryManage.operation')"
                             class-name="operate-container"
                             :width="operateWidth">
              <template slot-scope="scope">
                <span class="menu-item operate-btn first-btn"
                      v-if="scope.row.viewDashboard"
                      @contextmenu.prevent="rightClick(scope.row, $event, 0)"
                      @click.stop="goToTrainDashboard(scope.row)">
                  {{$t('summaryManage.viewDashboard')}} </span>
                <span class="menu-item operate-btn first-btn button-disable"
                      v-else
                      :title="$t('summaryManage.disableDashboardTip')">
                  {{$t('summaryManage.viewDashboard')}}
                </span>
                <span class="menu-item operate-btn"
                      v-if="scope.row.viewProfiler"
                      @contextmenu.prevent="rightClick(scope.row, $event, 1)"
                      @click.stop="goToProfiler(scope.row)">
                  {{$t('summaryManage.viewProfiler')}} </span>
                <span class="menu-item operate-btn button-disable"
                      v-else
                      :title="$t('summaryManage.disableProfilerTip')">
                  {{$t('summaryManage.viewProfiler')}}
                </span>
                <span class="menu-item operate-btn"
                      v-if="scope.row.viewOfflineDebugger"
                      @contextmenu.prevent="rightClick(scope.row, $event, 2)"
                      @click.stop="goToOfflineDebugger(scope.row)">
                  {{$t('summaryManage.viewOfflineDebugger')}} </span>
                <span class="menu-item operate-btn button-disable"
                      v-else
                      :title="$t('summaryManage.disableOfflineDebugger')">
                  {{$t('summaryManage.viewOfflineDebugger')}}
                </span>
                <span class="menu-item operate-btn"
                      v-if="scope.row.paramDetails"
                      @click.stop="showModelDialog(scope.row)">
                  {{$t('summaryManage.paramDetails')}} </span>
                <span class="menu-item operate-btn button-disable"
                      v-else
                      :title="$t('summaryManage.disableParameterTip')">
                  {{$t('summaryManage.paramDetails')}}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </div>

      </div>
      <!-- outer Page -->
      <div class="pagination-content">
        <el-pagination @current-change="currentPageChange"
                       @size-change="currentPagesizeChange"
                       :current-page.sync="pagination.currentPage"
                       :page-size="pagination.pageSize"
                       :page-sizes="pagination.pageSizes"
                       :layout="pagination.layout"
                       :total="pagination.total"
                       class="page">
        </el-pagination>
      </div>
      <!-- dialog of model details -->
      <div v-if="showDialogModel">
        <el-dialog :title="rowName"
                   :visible.sync="showDialogModel"
                   width="50%"
                   :close-on-click-modal="false"
                   class="details-data-list">
          <el-table :data="modelData"
                    row-key="id"
                    lazy
                    tooltip-effect="light"
                    :load="loadDataListChildren"
                    :tree-props="{children:'children',hasChildren:'hasChildren'}">
            <el-table-column width="50" />
            <el-table-column property="key"
                             label="Key"
                             width="200"></el-table-column>
            <el-table-column property="value"
                             label="Value">
              <template slot-scope="scope">
                {{scope.row.value}}
              </template>
            </el-table-column>
          </el-table>
        </el-dialog>
      </div>
    </div>
    <div id="contextMenu"
         v-if="contextMenu.show"
         :style="{left: contextMenu.left, top: contextMenu.top}">
      <ul>
        <li @click="doRightClick()">{{$t('summaryManage.openNewTab')}}</li>
      </ul>
    </div>
    <el-dialog :visible.sync="debuggerDialog.showDialogModel"
               width="50%"
               :close-on-click-modal="false"
               class="details-data-list">
      <span slot="title">
        <span class="sessionMsg">{{ debuggerDialog.title }}</span>
        <el-tooltip placement="right"
                    effect="light"
                    popper-class="legend-tip"
                    :content="$t('summaryManage.sessionLimitNum')">
          <i class="el-icon-info"></i>
        </el-tooltip>
      </span>
      <div class="session-title">{{ $t('summaryManage.sessionLists') }}</div>
      <el-table :data="debuggerDialog.trainJobs">
        <el-table-column width="50"
                         type=index
                         :label="$t('summaryManage.sorting')">
        </el-table-column>
        <el-table-column min-width="300"
                         prop="relative_path"
                         :label="$t('summaryManage.summaryPath')"
                         show-overflow-tooltip>
        </el-table-column>
        <!-- operate -->
        <el-table-column prop="operate"
                         :label="$t('summaryManage.operation')"
                         class-name="operate-container">
          <template slot-scope="scope">
            <span class="menu-item operate-btn first-btn"
                  @click="deleteSession(scope.row.session_id)">
              {{$t('public.delete')}} </span>
            <span class="menu-item operate-btn first-btn"
                  @click="viewSession(scope.row)">
              {{$t('debugger.view')}} </span>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script>
import RequestService from '../../services/request-service';

export default {
  data() {
    return {
      loading: true,
      currentFolder: '--',
      // table filter condition
      tableFilter: {lineage_type: {in: ['model']}},
      showDialogModel: false,
      summaryList: [],
      disableState: true,
      modelData: [],
      objectType: 'object',
      rowName: '--',
      dialogKeys: {
        train_dataset_path: {
          label: this.$t('modelTraceback.trainSetPath'),
        },
        test_dataset_path: {
          label: this.$t('modelTraceback.testSetPath'),
        },
        network: {
          label: this.$t('modelTraceback.network'),
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
        device_num: {
          label: this.$t('modelTraceback.deviceNum'),
        },
        model_size: {
          label: this.$t('modelTraceback.modelSize'),
        },
        loss_function: {
          label: this.$t('modelTraceback.lossFunc'),
        },
      },
      pagination: {
        currentPage: null,
        pageSize: null,
        pageSizes: [10, 20, 50],
        total: 0,
        layout: 'total, sizes, prev, pager, next, jumper',
      },
      contextMenu: {
        show: false,
        left: '',
        top: '',
        data: null,
        type: 0,
      },
      tableDom: null,
      operateWidth: localStorage.getItem('milang') === 'en-us' ? 550 : 400,
      debuggerDialog: {
        title: this.$t('summaryManage.sessionLimit'),
        showDialogModel: false,
        trainJobs: [],
      },
    };
  },
  computed: {},
  watch: {},
  destroyed() {
    window.removeEventListener('resize', this.closeMenu);
    window.removeEventListener('mousewheel', this.closeMenu);
    if (this.tableDom) {
      this.tableDom.removeEventListener('scroll', this.closeMenu);
    }
    document.onclick = null;
    document.onscroll = null;
  },
  created() {
    const pageIndex = sessionStorage.getItem('summaryPageIndex');
    this.pagination.currentPage = pageIndex ? +pageIndex : 1;
    const pageSize = sessionStorage.getItem('summaryPageSize');
    this.pagination.pageSize = pageSize ? +pageSize : 20; // Default page size
  },
  mounted() {
    document.title = `${this.$t('summaryManage.summaryList')}-MindInsight`;
    this.$nextTick(() => {
      this.init();
    });
    setTimeout(() => {
      window.addEventListener('resize', this.closeMenu, false);
      window.addEventListener('mousewheel', this.closeMenu, false);
      this.tableDom = this.$refs.table.bodyWrapper;
      if (this.tableDom) {
        this.tableDom.addEventListener('scroll', this.closeMenu, false);
      }
    }, 300);
  },

  methods: {
    init() {
      document.onclick = () => {
        this.contextMenu.show = false;
      };
      document.onscroll = () => {
        this.contextMenu.show = false;
      };

      const params = {
        limit: this.pagination.pageSize,
        offset: this.pagination.currentPage - 1,
      };
      this.querySummaryList(params);
    },
    /**
     * Querying summary list
     * @param {Object} params page info param
     */
    querySummaryList(params) {
      RequestService.querySummaryList(params, false)
          .then(
              (res) => {
                this.loading = false;
                if (res && res.data && res.data.train_jobs) {
                  const summaryList = JSON.parse(JSON.stringify(res.data.train_jobs));
                  if (params.offset > 0 && !summaryList.length) {
                    this.currentPage.currentPage = 1;
                    this.currentPageChange();
                    return;
                  }
                  summaryList.forEach((i) => {
                    i.relative_path = i.relative_path ? i.relative_path : '--';
                    i.update_time = i.update_time ? i.update_time : '--';
                    i.viewProfiler = i.profiler_dir && i.profiler_dir.length;
                    i.viewDashboard = i.summary_files || i.graph_files || i.lineage_files;
                    i.viewOfflineDebugger = i.dump_dir;
                    i.paramDetails = i.lineage_files;
                  });
                  this.currentFolder = res.data.name ? res.data.name : '--';
                  this.pagination.total = res.data.total;
                  this.summaryList = summaryList;
                  this.disableState = !summaryList.length;
                } else {
                  this.currentFolder = '--';
                  this.pagination.total = 0;
                  this.pagination.currentPage = 1;
                  this.summaryList = [];
                  this.disableState = true;
                }
              },
              (error) => {
                this.loading = false;
              },
          )
          .catch((e) => {
            this.loading = false;
          });
    },
    currentPagesizeChange(pageSize) {
      this.pagination.pageSize = pageSize;
      sessionStorage.setItem('summaryPageSize', pageSize);
      this.pagination.currentPage = 1;
      this.currentPageChange();
    },
    currentPageChange() {
      sessionStorage.setItem('summaryPageIndex', this.pagination.currentPage);
      const params = {
        offset: this.pagination.currentPage - 1,
        limit: this.pagination.pageSize,
      };
      this.querySummaryList(params);
    },
    /**
     * go to train dashboard
     * @param {Object} row select row
     */
    goToTrainDashboard(row) {
      this.contextMenu.show = false;
      const trainId = encodeURIComponent(row.train_id);
      this.$router.push({
        path: '/train-manage/training-dashboard',
        query: {id: trainId},
      });
    },
    /**
     * go to Profiler
     * @param {Object} row select row
     */
    goToProfiler(row) {
      this.contextMenu.show = false;
      const profilerDir = encodeURIComponent(row.profiler_dir);
      const trainId = encodeURIComponent(row.train_id);
      const path = encodeURIComponent(row.relative_path);
      let router = '/profiling';
      if (row.profiler_type === 'gpu') {
        router = '/profiling-gpu';
      } else if (row.profiler_type === 'cluster_ascend') {
        router = '/cluster-dashboard';
      } else if (row.profiler_type === 'cluster_gpu') {
        router = '/cluster-dashboard';
      }
      this.$router.push({
        path: router,
        query: {
          dir: profilerDir,
          id: trainId,
          path: path,
        },
      });
    },
    /**
     * go to Offline Debugger
     * @param {Object} row select row
     */
    goToOfflineDebugger(row) {
      this.contextMenu.show = false;
      const debuggerDir = row.dump_dir;
      const params = {
        session_type: 'OFFLINE',
        dump_dir: debuggerDir,
      };
      this.getSessionId(params).then((value) => {
        if (value !== undefined) {
          this.$router.push({
            path: '/offline-debugger',
            query: {
              dir: debuggerDir,
              sessionId: value,
            },
          });
        }
      });
    },
    getSessionId(params) {
      return RequestService.getSession(params).then(
          (res) => {
            if (res && res.data) {
              const sessionId = res.data;
              return sessionId;
            }
          },
          (error) => {
            if (error && error.response && error.response.data && error.response.data.error_code === '5054B280') {
              this.checkSessions();
            }
          },
      );
    },
    deleteSession(sessionId) {
      this.$confirm(this.$t('summaryManage.deleteSessionConfirm'), this.$t('public.notice'), {
        confirmButtonText: this.$t('public.sure'),
        cancelButtonText: this.$t('public.cancel'),
        type: 'warning',
      }).then(() => {
        RequestService.deleteSession(sessionId).then((res) => {
          this.$message({
            type: 'success',
            message: this.$t('summaryManage.deleteSessionSuccess'),
          });
          this.checkSessions();
        });
      });
    },
    checkSessions() {
      RequestService.checkSessions().then((res) => {
        if (res && res.data && res.data.train_jobs) {
          const trainJobs = res.data.train_jobs;
          this.debuggerDialog.trainJobs = Object.keys(trainJobs).map((val) => {
            return {
              relative_path: decodeURIComponent(val),
              session_id: trainJobs[val],
            };
          });
          this.debuggerDialog.showDialogModel = true;
        }
      });
    },
    viewSession(row) {
      const dir = row.relative_path;
      this.$router.push({
        path: '/offline-debugger',
        query: {
          dir,
          sessionId: row.session_id,
        },
      });
    },
    rightClick(row, event, type) {
      const maxWidth = 175;
      this.contextMenu.data = row;
      this.contextMenu.type = type;
      const width = document.getElementById('cl-summary-manage').clientWidth;
      const left = Math.min(width - maxWidth, event.clientX + window.scrollX);
      this.contextMenu.left = left + 'px';
      this.contextMenu.top = event.clientY + window.scrollY + 'px';
      this.contextMenu.show = true;
    },

    doRightClick(key) {
      const row = this.contextMenu.data;
      if (!row) {
        return;
      }
      if (this.contextMenu.type === 2) {
        // open offline debugger
        this.contextMenu.show = false;
        const debuggerDir = row.dump_dir;
        const params = {
          session_type: 'OFFLINE',
          dump_dir: debuggerDir,
        };
        this.getSessionId(params).then((value) => {
          if (value !== undefined) {
            const routeUrl = this.$router.resolve({
              path: '/offline-debugger',
              query: {
                dir: debuggerDir,
                sessionId: value,
              },
            });
            window.open(routeUrl.href, '_blank');
          }
        });
      } else if (this.contextMenu.type === 1) {
        // open profiling
        this.contextMenu.show = false;
        const profilerDir = encodeURIComponent(row.profiler_dir);
        const trainId = encodeURIComponent(row.train_id);
        const path = encodeURIComponent(row.relative_path);
        let router = '/profiling';
        if (row.profiler_type === 'gpu') {
          router = '/profiling-gpu';
        } else if (row.profiler_type === 'cluster_ascend') {
          router = '/profiling-cluster';
        }
        const routeUrl = this.$router.resolve({
          path: router,
          query: {
            dir: profilerDir,
            id: trainId,
            path: path,
          },
        });
        window.open(routeUrl.href, '_blank');
      } else { // open training dashboard
        this.contextMenu.show = false;
        const trainId = encodeURIComponent(row.train_id);

        const routeUrl = this.$router.resolve({
          path: '/train-manage/training-dashboard',
          query: {id: trainId},
        });
        window.open(routeUrl.href, '_blank');
      }
    },
    closeMenu() {
      this.contextMenu.show = false;
    },
    /**
     * go to traceback analysis
     */
    goToTracebackAnalysis() {
      this.$router.push({
        path: '/model-traceback',
      });
    },
    /**
     * go to compare analysis
     */
    goToCompareAnalysis() {
      this.$router.push({
        path: '/compare-plate',
      });
    },
    /**
     * tree data
     * @param {Object} tree
     * @param {Object} treeNode
     * @param {Object} resolve
     */
    loadDataListChildren(tree, treeNode, resolve) {
      setTimeout(() => {
        resolve(tree.children);
      });
    },
    /**
     * Show dialog of model
     * @param {Object} row select row
     */
    showModelDialog(row) {
      this.rowName =
        row.train_id + ' ' + this.$t('summaryManage.trainingParamDetails');
      const params = {
        body: {},
      };
      this.tableFilter.summary_dir = {in: [row.train_id]};
      params.body = Object.assign({}, this.tableFilter);
      RequestService.queryLineagesData(params)
          .then((resp) => {
            this.showDialogModel = true;
            if (
              resp &&
            resp.data &&
            resp.data.object &&
            resp.data.object.length
            ) {
              const resultArr = [];
              const tempdata = resp.data.object[0].model_lineage;
              const keys = Object.keys(tempdata);
              keys.forEach((key, index) => {
                const data = {
                  id: index + 1,
                  hasChildren: false,
                  key: this.dialogKeys[key] ? this.dialogKeys[key].label : key,
                  value: '',
                };
                if (tempdata[key] === null) {
                  data.value = 'None';
                } else if (
                  typeof tempdata[key] === this.objectType &&
                tempdata[key] !== null
                ) {
                  if (
                    !(tempdata[key] instanceof Array) &&
                  JSON.stringify(tempdata[key]) !== '{}'
                  ) {
                    data.hasChildren = true;
                    data.children = [];
                    Object.keys(tempdata[key]).forEach((k, j) => {
                      const item = {};
                      item.key = k;
                      item.value = tempdata[key][k];
                      item.id =
                      `model` +
                      `${new Date().getTime()}` +
                      `${this.$store.state.tableId}`;
                      this.$store.commit('increaseTableId');
                      data.children.push(item);
                    });
                  }
                  data.value = JSON.stringify(tempdata[key]);
                } else {
                  data.value = tempdata[key];
                }
                resultArr.push(data);
              });
              this.modelData = resultArr;
            } else {
              this.modelData = [];
            }
          })
          .catch(() => {});
    },
  },
  components: {},
};
</script>
<style>
#cl-summary-manage {
  height: 100%;
  width: 100%;
  background-color: #fff;
}
#cl-summary-manage .no-data-page {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}
#cl-summary-manage .no-data-page .no-data-img {
  background: #fff;
  text-align: center;
  height: 200px;
  width: 310px;
  margin: auto;
}
#cl-summary-manage .no-data-page .no-data-img img {
  max-width: 100%;
}
#cl-summary-manage .no-data-page .no-data-img p {
  font-size: 16px;
  padding-top: 10px;
}
#cl-summary-manage .cl-summary-manage-container {
  height: 100%;
  padding: 14px 32px 32px;
}
#cl-summary-manage .cl-title {
  border: none;
  height: 55px;
  line-height: 75px;
}
#cl-summary-manage .cl-title-left {
  padding-left: 0;
  height: 55px;
  line-height: 55px;
}
#cl-summary-manage .cl-title-left .btn-wrap {
  float: right;
}
#cl-summary-manage .summary-title {
  font-size: 20px;
  font-weight: bold;
  margin-right: 15px;
}
#cl-summary-manage .summary-subtitle {
  margin-left: 20px;
}
#cl-summary-manage .container {
  height: calc(100% - 97px);
  overflow-y: auto;
}
#cl-summary-manage .container .list-table {
  height: 100%;
}
#cl-summary-manage .container .list-table .operate-container {
  padding-right: 32px;
}
#cl-summary-manage .pagination-content {
  margin-top: 16px;
  text-align: right;
}
#cl-summary-manage .operate-btn {
  margin-left: 20px;
  padding: 12px 0;
}
#cl-summary-manage .el-dialog {
  min-width: 500px;
  padding-bottom: 30px;
}
#cl-summary-manage .operate-btn.button-disable {
  -moz-user-select: none;
  /*Firefox*/
  -webkit-user-select: none;
  /*webkitbrowser*/
  -ms-user-select: none;
  /*IE10*/
  -khtml-user-select: none;
  /*Early browser*/
  user-select: none;
  color: #c0c4cc;
  cursor: not-allowed;
}
#cl-summary-manage .menu-item {
  color: #00a5a7;
  cursor: pointer;
}
#cl-summary-manage .menu-item.operate-btn.first-btn {
  margin-left: 0;
}
#cl-summary-manage #contextMenu {
  position: absolute;
  min-width: 150px;
  border: 1px solid #d4d4d4;
}
#cl-summary-manage #contextMenu ul {
  background-color: #f7faff;
  border-radius: 2px;
}
#cl-summary-manage #contextMenu ul li {
  padding: 5px 18px;
  cursor: pointer;
}
#cl-summary-manage #contextMenu ul li:hover {
  background-color: #a7a7a7;
  color: white;
}
#cl-summary-manage .details-data-list .el-table td,
#cl-summary-manage .details-data-list .el-table th.is-leaf {
  border: none;
  border-top: 1px solid #ebeef5;
}
#cl-summary-manage .details-data-list .el-table th {
  padding: 10px 0;
  border-top: 1px solid #ebeef5;
}
#cl-summary-manage .details-data-list .el-table th .cell {
  border-left: 1px solid #d9d8dd;
  height: 14px;
  line-height: 14px;
}
#cl-summary-manage .details-data-list .el-table th:first-child .cell {
  border-left: none;
}
#cl-summary-manage .details-data-list .el-table th:nth-child(2),
#cl-summary-manage .details-data-list .el-table td:nth-child(2) {
  max-width: 30%;
}
#cl-summary-manage .details-data-list .el-table td {
  padding: 8px 0;
}
#cl-summary-manage .details-data-list .el-table__row--level-0 td:first-child:after {
  width: 20px;
  height: 1px;
  background: #ebeef5;
  z-index: 11;
  position: absolute;
  left: 0;
  bottom: -1px;
  content: "";
  display: block;
}
#cl-summary-manage .details-data-list .el-table__row--level-1 td {
  padding: 4px 0;
  position: relative;
}
#cl-summary-manage .details-data-list .el-table__row--level-1 td:first-child::before {
  width: 42px;
  background: #f0fdfd;
  border-right: 2px #00a5a7 solid;
  z-index: 10;
  position: absolute;
  left: 0;
  top: -1px;
  bottom: 0px;
  content: "";
  display: block;
}
#cl-summary-manage .details-data-list .el-table__row--level-1:first-child td:first-child::before {
  bottom: 0;
}
#cl-summary-manage .details-data-list .el-dialog__title {
  font-weight: bold;
  display: inline-block;
  width: calc(100% - 20px);
  word-break: break-all;
}
#cl-summary-manage .details-data-list .el-dialog__body {
  max-height: 500px;
  padding-top: 10px;
  padding-bottom: 0px;
  overflow: auto;
}
#cl-summary-manage .details-data-list .el-dialog__body .details-data-title {
  margin-bottom: 20px;
}
#cl-summary-manage .details-data-list .sessionMsg {
  color: #333;
  font-weight: bold;
  font-size: 16px;
  margin-right: 5px;
}
#cl-summary-manage .details-data-list .session-title {
  margin-bottom: 10px;
  color: #333;
}
#cl-summary-manage .is-disabled.custom-btn {
  background-color: #f5f5f6;
  border: 1px solid #dfe1e6 !important;
  color: #adb0b8;
}
#cl-summary-manage .is-disabled.custom-btn:hover {
  background-color: #f5f5f6;
}
#cl-summary-manage .custom-btn {
  border: 1px solid #00a5a7;
  border-radius: 2px;
}
#cl-summary-manage .white {
  background-color: white;
  color: #00a5a7;
}
#cl-summary-manage .white:hover {
  background-color: #e9f7f7;
}
</style>

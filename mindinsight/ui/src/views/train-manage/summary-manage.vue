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
  <div id="cl-summary-manage">
    <div v-if="loading"
         class="no-data-page">
      <div class="no-data-img">
        <img :src="require('@/assets/images/nodata.png')"
             alt="" />
        <p class="no-data-text">{{$t("public.dataLoading")}}</p>
      </div>
    </div>
    <div class="cl-summary-manage-container"
         v-if="!loading">
      <div class="cl-title">
        <div class="cl-title-left">
          <span class="summary-title">{{$t('summaryManage.summaryList')}}</span>
          <span>{{$t("symbols.leftbracket")}}</span>
          <span>{{$t('summaryManage.currentFolder')}}</span>
          <span :title="currentFolder">{{currentFolder}}</span>
          <span>{{$t("symbols.rightbracket")}}</span>
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
                    class="list-el-table">
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
                             prop="create_time"
                             :label="$t('summaryManage.createTime')"
                             show-overflow-tooltip>
            </el-table-column>
            <el-table-column width="180"
                             prop="update_time"
                             :label="$t('summaryManage.updateTime')"
                             show-overflow-tooltip>
            </el-table-column>
            <!--operate   -->
            <el-table-column prop="operate"
                             :label="$t('summaryManage.operation')"
                             width="240">
              <template slot-scope="scope">
                <el-button type="text"
                           @click.stop="goToTrainDashboard(scope.row)">
                  {{$t('summaryManage.viewDashboard')}} </el-button>
                <el-button type="text"
                           class="operate-btn"
                           v-if="scope.row.viewProfiler"
                           @click.stop="goToProfiler(scope.row)">
                  {{$t('summaryManage.viewProfiler')}} </el-button>
                <el-button type="text"
                           class="operate-btn"
                           disabled
                           :title="$t('summaryManage.disableProfilerTip')"
                           v-if="!scope.row.viewProfiler">{{$t('summaryManage.viewProfiler')}} </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

      </div>
      <!--   outer Page   -->
      <div class="pagination-content">
        <el-pagination @current-change="currentPageChange"
                       :current-page="pagination.currentPage"
                       :page-size="pagination.pageSize"
                       :layout="pagination.layout"
                       :total="pagination.total"
                       class="page">
        </el-pagination>
      </div>
    </div>
  </div>
</template>

<script>
import RequestService from '../../services/request-service';

export default {
  data() {
    return {
      loading: true,
      currentFolder: '--',
      summaryList: [],
      pagination: {
        currentPage: 1,
        pageSize: 16,
        total: 0,
        layout: 'total, prev, pager, next, jumper',
      },
    };
  },
  computed: {},
  watch: {},
  destroyed() {},
  activated() {},
  mounted() {
    document.title = `${this.$t('summaryManage.summaryList')}-MindInsight`;
    this.$nextTick(() => {
      this.init();
    });
  },

  methods: {
    init() {
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
                  const summaryList = JSON.parse(
                      JSON.stringify(res.data.train_jobs),
                  );
                  summaryList.forEach((i) => {
                    i.relative_path = i.relative_path ? i.relative_path : '--';
                    i.create_time = i.create_time ? i.create_time : '--';
                    i.update_time = i.update_time ? i.update_time : '--';
                    i.viewProfiler = i.profiler_dir && i.profiler_dir.length;
                  });
                  this.currentFolder = res.data.name ? res.data.name : '--';
                  this.pagination.total = res.data.total;
                  this.summaryList = summaryList;
                } else {
                  this.currentFolder = '--';
                  this.pagination.total = 0;
                  this.summaryList = [];
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
    currentPageChange(currentPage) {
      this.pagination.currentPage = currentPage;
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
      const trainId = encodeURIComponent(row.train_id);

      const routeUrl = this.$router.resolve({
        path: '/train-manage/training-dashboard',
        query: {id: trainId},
      });
      window.open(routeUrl.href, '_blank');
    },
    /**
     * go to Profiler
     * @param {Object} row select row
     */
    goToProfiler(row) {
      const profilerDir = encodeURIComponent(row.profiler_dir);
      const trainId = encodeURIComponent(row.train_id);
      const path = encodeURIComponent(row.relative_path);
      const router = `/profiling${row.profiler_type === 'gpu' ? '-gpu' : ''}`;

      const routeUrl = this.$router.resolve({
        path: router,
        query: {
          dir: profilerDir,
          id: trainId,
          path: path,
        },
      });
      window.open(routeUrl.href, '_blank');
    },
  },
  components: {},
};
</script>
<style lang="scss">
#cl-summary-manage {
  height: 100%;
  width: 100%;
  background-color: #fff;
  .no-data-page {
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    .no-data-img {
      background: #fff;
      text-align: center;
      height: 200px;
      width: 310px;
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
  .cl-summary-manage-container {
    height: 100%;
    padding: 14px 32px 32px;
  }
  .cl-title {
    border: none;
    height: 55px;
    line-height: 75px;
  }
  .cl-title-left {
    padding-left: 0;
    height: 55px;
    line-height: 55px;
  }
  .summary-title {
    font-size: 20px;
    font-weight: bold;
    margin-right: 15px;
  }
  .summary-subtitle {
    margin-left: 20px;
  }
  .container {
    height: calc(100% - 97px);
    overflow-y: auto;
    .list-table {
      height: 100%;
    }
  }
  .pagination-content {
    margin-top: 16px;
    text-align: right;
  }
  .operate-btn {
    margin-left: 20px;
  }
}
</style>

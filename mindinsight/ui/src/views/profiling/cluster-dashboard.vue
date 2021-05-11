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
  <div class="cl-cluster-dashboard">
    <div class="cluster-head">
      <span class="cl-title-left">{{$t('profilingCluster.clusterView')}}</span>
      <div class="path-message">
        <span>{{$t('symbols.leftbracket')}}</span>
        <span>{{$t('trainingDashboard.summaryDirPath')}}</span>
        <span>{{summaryPath}}</span>
        <span>{{$t('symbols.rightbracket')}}</span>
      </div>
    </div>
    <div class="content-container">
      <div class="tab-container">
        <el-tabs v-model="tabData.activeName"
                 @tab-click="onTabClick">
          <el-tab-pane v-for="pane in tabData.tabPanes"
                       :key="pane.label"
                       :label="pane.label"
                       :name="pane.name"></el-tab-pane>
        </el-tabs>
      </div>
      <div class="item-container">
        <PerformanceDashboard v-if="tabData.activeName === '0'"
                              :activeName="'0'"></PerformanceDashboard>
        <ResourceDashboard v-else
                           :activeName="'1'"></ResourceDashboard>
      </div>
    </div>
  </div>
</template>
<script>
import ResourceDashboard from './resource-dashboard-cluster';
import PerformanceDashboard from './performance-dashboard';
export default {
  components: {
    ResourceDashboard,
    PerformanceDashboard,
  },
  props: {},
  data() {
    return {
      summaryPath: decodeURIComponent(this.$route.query.path), // Path of the current training job
      trainingJobId: this.$route.query.id, // ID of the current training job
      summaryDir: this.$route.query.dir, // Dir of the current training job
      tabData: {
        activeName: this.$route.query.activeName || '0',
        tabPanes: [
          {
            name: '0',
            label: this.$t('profiling.trainingPerformance'),
          },
          {
            name: '1',
            label: this.$t('profiling.resourceUtilization'),
          },
        ],
      }, // The data of tab
    };
  },
  created() {
    if (!this.trainingJobId) {
      this.$message.error(this.$t('trainingDashboard.invalidId'));
      document.title = `${this.$t('profilingCluster.clusterView')}-MindInsight`;
      return;
    }
    document.title = `${this.summaryPath}-${this.$t(
        'profilingCluster.clusterView',
    )}-MindInsight`;
  },
  methods: {
    /**
     * The logic of click tab item
     */
    onTabClick() {
      const {dir, id, path} = this.$route.query;
      this.$router.push({
        path: '/cluster-dashboard',
        query: {dir, id, path, activeName: this.tabData.activeName},
      });
    },
  },
};
</script>
<style>
.cl-cluster-dashboard {
  height: 100%;
  background: #FFF;
}
.cl-cluster-dashboard .cluster-head {
  height: 56px;
  line-height: 56px;
  display: inline-block;
}
.cl-cluster-dashboard .cluster-head .path-message {
  display: inline-block;
  line-height: 20px;
  padding: 18px 0;
  font-weight: bold;
  margin-left: 5px;
}
.cl-cluster-dashboard .content-container {
  height: calc(100% - 56px);
  padding: 0 32px 24px 32px;
}
.cl-cluster-dashboard .content-container .item-container{
  height: calc(100% - 47px);
}
.cl-cluster-dashboard .tab-container {
  width: 100%;
  padding-bottom: 5px;
}
.cl-cluster-dashboard .tab-container .el-tabs__item {
  font-size: 14px;
  line-height: 14px;
  height: 27px;
}
.cl-cluster-dashboard .tab-container .el-tabs__item.is-active {
  color: #00a5a7;
  font-weight: bold;
}
</style>

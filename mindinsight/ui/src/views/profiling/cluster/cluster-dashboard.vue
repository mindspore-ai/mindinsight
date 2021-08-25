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
  <div class="cluster-dashboard profiling-dashboard-tab">
    <div class="dashboard-tabs"
         v-show="!showDetail">
      <el-tabs v-model="tab"
               @tab-click="onTabClick">
        <el-tab-pane v-for="tab in tabs"
                     :key="tab.label"
                     :label="tab.label"
                     :name="tab.name"></el-tab-pane>
      </el-tabs>
    </div>
    <div class="dashboard-content">
      <router-view @viewDetail="viewDetail"></router-view>
    </div>
    <div class="dashboard-close-detail"
         @click="closeDetail"
         v-show="showDetail">
      <img src="@/assets/images/close-page.png">
    </div>
  </div>
</template>
<script>
export default {
  props: {},
  data() {
    return {
      showDetail: false, // If show detail page
      tab: null, // Now tab name
      tabs: [
        {
          name: 'performance',
          label: this.$t('profiling.trainingPerformance'),
        },
        {
          name: 'resource',
          label: this.$t('profiling.resourceUtilization'),
        },
      ],
    };
  },
  created() {
    this.updatePage();
    const id = this.$route.query.id;
    document.title = (id ? id + '-' : '') + `${this.$t('profiling.profilingDashboard')}-MindInsight`;
  },
  watch: {
    '$route.path': {
      handler() {
        this.updatePage();
      },
    },
  },
  methods: {
    /**
     * Update page state
     */
    updatePage() {
      const path = this.$route.path;
      this.showDetail = true;
      switch (path) {
        case '/profiling/cluster/performance':
          this.showDetail = false;
        case '/profiling/cluster/step-trace':
        case '/profiling/cluster/communication':
          this.tab = this.tabs[0].name;
          break;
        case '/profiling/cluster/resource':
          this.showDetail = false;
        case '/profiling/cluster/flops-heatmap':
        case '/profiling/cluster/memory-heatmap':
          this.tab = this.tabs[1].name;
          break;
      }
    },
    /**
     * Click tab
     */
    onTabClick() {
      this.$router.push({
        path: '/profiling/cluster/' + this.tab,
        query: this.$route.query,
      });
    },
    /**
     * View detail
     * @param {string} path
     */
    viewDetail(path) {
      this.$router.push({
        path: '/profiling/cluster/' + path,
        query: this.$route.query,
      });
    },
    /**
     * Click close detail button
     */
    closeDetail() {
      this.onTabClick();
    },
  },
};
</script>
<style>
.dashboard-content .cl-cluster-title {
  height: 36px;
  line-height: 36px;
  position: relative;
  font-size: 16px;
  font-weight: bold;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
<style scoped>
.cluster-dashboard {
  flex-direction: column;
}
.cluster-dashboard .dashboard-content .item-container {
  height: calc(100% - 47px);
}
.cluster-dashboard .tab-container {
  width: 100%;
  padding-bottom: 5px;
}
.cluster-dashboard .tab-container .el-tabs__item {
  font-size: 14px;
  line-height: 14px;
  height: 27px;
}
.cluster-dashboard .tab-container .el-tabs__item.is-active {
  color: var(--theme-color);
  font-weight: bold;
}
</style>

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
  <div class="single-dashboard profiling-dashboard-tab">
    <div :class="{
           'dashboard-left': true,
           'is-hidden': !showHelper
         }">
      <helper :defaultRankID="defaultRankID"
              @change="rankIDChanged"
              v-show="showHelper"></helper>
      <div :class="[
             'helper-control',
             !showHelper ? 'collapse' : '',
             `collapse-btn-${this.$store.state.themeIndex}`
           ]"
           @click="controlHelper"></div>
    </div>
    <div class="dashboard-right">
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
      <div class="dashboard-content"
           :style="{
             height: showDetail ? '100%' : 'calc(100% - 44px)',
           }">
        <router-view :key="rankID"
                     :rankID="rankID"
                     @viewDetail="viewDetail"></router-view>
      </div>
    </div>
    <div class="dashboard-close-detail"
         v-show="showDetail"
         @click="closeDetail">
      <img src="@/assets/images/close-page.png">
    </div>
  </div>
</template>
<script>
import helper from './single-helper.vue';
export default {
  components: {
    helper,
  },
  data() {
    return {
      showDetail: false, // If show detail page
      showHelper: true, // If show helper
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
      rankID: null,
      defaultRankID: this.$route.query.rankID,
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
        case '/profiling/single/performance':
          this.showDetail = false;
        case '/profiling/single/step-trace':
        case '/profiling/single/data-process':
        case '/profiling/single/operator':
          this.tab = this.tabs[0].name;
          break;
        case '/profiling/single/resource':
          this.showDetail = false;
        case '/profiling/single/cpu-utilization':
        case '/profiling/single/memory-utilization':
          this.tab = this.tabs[1].name;
          break;
      }
    },
    /**
     * Control helper display
     */
    controlHelper() {
      this.showHelper = !this.showHelper;
      this.$bus.$emit('collapse');
    },
    /**
     * Click tab
     */
    onTabClick() {
      this.$router.push({
        path: '/profiling/single/' + this.tab,
        query: this.$route.query,
      });
    },
    /**
     * On RankID changed
     * @param {string} val
     */
    rankIDChanged(val) {
      this.rankID = val;
    },
    /**
     * View detail
     * @param {string} path
     */
    viewDetail(path) {
      this.$router.push({
        path: '/profiling/single/' + path,
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
<style scoped>
.single-dashboard {
  height: 100%;
}
.dashboard-left {
  width: 22%;
  flex-shrink: 0;
  padding-right: 20px;
  overflow: visible;
  transition: width 0.1s;
  position: relative;
}
.is-hidden {
  width: 0%;
  padding-right: 0;
}
.dashboard-right {
  height: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  flex-grow: 1;
  overflow: hidden;
}
.helper-control {
  position: absolute;
  right: 0px;
  width: 31px;
  height: 100px;
  top: 50%;
  margin-top: -50px;
  cursor: pointer;
  line-height: 86px;
  z-index: 1;
  text-align: center;
}
.collapse-btn-0 {
  background-image: url('../../../assets/images/0/collapse-left.svg');
}
.collapse-btn-1 {
  background-image: url('../../../assets/images/1/collapse-left.svg');
}
.collapse-btn-0.collapse {
  background-image: url('../../../assets/images/0/collapse-right.svg');
}
.collapse-btn-1.collapse {
  background-image: url('../../../assets/images/1/collapse-right.svg');
}

</style>

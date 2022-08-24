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
  <div class="cluster-dashboard-wrap">
    <div :class="{
           'dashboard-left': true,
           'is-hidden': !showHelper
         }">
      <helper v-show="showHelper"></helper>
      <div :class="[
             'helper-control',
             !showHelper ? 'collapse' : '',
             `collapse-btn-${this.$store.state.themeIndex}`
           ]"
           @click="controlHelper"></div>
    </div>
    <div class="cluster-dashboard profiling-dashboard-tab">
      <div class="dashboard-tabs"
           v-show="!showDetail">
        <div class="cluster-dashboard-tabs">
          <el-tabs v-model="tab"
                   @tab-click="onTabClick">
            <el-tab-pane v-for="tab in tabs"
                         :key="tab.label"
                         :label="tab.label"
                         :name="tab.name"></el-tab-pane>
          </el-tabs>
          <div class="custer-dashboard-tabs-link"
               :style="{
             left: `${left}px`
           }">
            <el-tooltip class="item"
                        effect="dark"
                        placement="bottom">
              <div slot="content">
                <p>{{$t("profiling.strategyReference")}}<a :href="$t('profiling.strategyTutorialUrl')"
                     rel="nofollow noreferrer noopener"
                     target="_blank">{{$t("profiling.strategyTutorials")}}</a></p>
              </div>
              <i class="el-icon-info"></i>
            </el-tooltip>

          </div>
        </div>

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
  </div>
</template>
<script>
import helper from './cluster-helper.vue';
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
        {
          name: 'strategy',
          label: this.$t('profiling.strategyPerception'),
        },
        {
          name: 'executive-overview',
          label: this.$t('profiling.executiveOverview'),
        },
      ],
      left: 0,
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
  mounted() {
    let length = 0;
    this.tabs.forEach((t) => {
      length += t.label.length;
    });
    // 6(px of en-us char), 14(px of zh-cn char), 30(padding) used to calculate the position of path label
    this.left = length * (this.$store.state.language === 'en-us' ? 6 : 14) + 30;
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
        case '/profiling/cluster/strategy':
          this.tab = this.tabs[2].name;
          this.showDetail = false;
          break;
        case '/profiling/cluster/resource':
          this.showDetail = false;
        case '/profiling/cluster/flops-heatmap':
        case '/profiling/cluster/memory-heatmap':
          this.tab = this.tabs[1].name;
          break;
        case '/profiling/cluster/executive-overview':
          this.tab = this.tabs[3].name;
          this.showDetail = false;
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
    /**
     * Control helper display
     */
    controlHelper() {
      this.showHelper = !this.showHelper;
      this.$bus.$emit('collapse');
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
.cluster-dashboard-wrap {
  height: 100%;
  display: flex;
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
.cluster-dashboard {
  flex-direction: column;
  flex-grow: 1;
  overflow: hidden;
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
.cluster-dashboard-tabs {
  position: relative;
}
.custer-dashboard-tabs-link {
  z-index: 99;
  position: absolute;
  top: 2px;
}
</style>

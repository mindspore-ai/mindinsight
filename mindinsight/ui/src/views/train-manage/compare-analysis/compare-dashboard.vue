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
  <div class="mi-common-full-page compare-dashboard">
    <div class="compare-tabs">
      <el-tabs v-model="tab"
               @tab-click="onTabClick">
        <el-tab-pane v-for="tab in tabs"
                     :key="tab.name"
                     :label="tab.label"
                     :name="tab.name">
        </el-tab-pane>
      </el-tabs>
    </div>
    <div class="dashboard-content">
      <router-view></router-view>
    </div>
  </div>
</template>

<script>
const [SCALAR, LOSS] = ['scalar', 'loss'];

export default {
  data() {
    return {
      tabs: [
        {
          label: this.$t('summaryManage.scalarComparison'),
          name: SCALAR,
        },
        {
          label: this.$t('summaryManage.lossComparison'),
          name: LOSS,
        },
      ],
      tab: null,
    };
  },
  created() {
    const path = this.$route.path;
    this.tab = path.includes('scalar') ? this.tabs[0].name : this.tabs[1].name;
  },
  methods: {
    onTabClick(val) {
      this.$router.push({
        path: val.name,
      });
    },
  },
};
</script>

<style>
.compare-dashboard .el-tabs__item {
  font-size: 18px;
  font-weight: 700;
}
.compare-dashboard .dashboard-content {
  /* 54px: tabs height */
  height: calc(100% - 54px);
}
</style>

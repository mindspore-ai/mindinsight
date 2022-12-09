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
  <div class="profiling-dashboard">
    <div class="profiling-dashboard-head">
      <el-tabs v-model="tab"
               @tab-click="onTabClick">
        <el-tab-pane v-for="tab in tabs"
                     :key="tab"
                     :label="tab"
                     :name="tab"
                     v-if="!(isSingle && (tab === $t('profiling.cluster')))"
        >
        </el-tab-pane>
      </el-tabs>
      <div class="path"
           :style="{
             left: `${left}px`
           }">
        {{
          $t('symbols.leftbracket') +
          $t('trainingDashboard.summaryDirPath') +
          trainInfo.path +
          $t('symbols.rightbracket')
        }}
      </div>
    </div>
    <div class="profiling-dashboard-content">
      <router-view></router-view>
    </div>
  </div>
</template>
<script>
  import RequestService from '@/services/request-service';
  export default {
  data() {
    return {
      trainInfo: {
        id: this.$route.query.id,
        path: this.$route.query.path,
        dir: this.$route.query.dir,
      },
      tab: null,
      tabs: [
        this.$t('profiling.singleHost'),
        this.$t('profiling.cluster'),
      ],
      left: 0,
      isSingle:true,
      tabsSingle:[
        this.$t('profiling.singleHost'),
      ]
    };
  },
  created() {
    this.checkProfilerDataVersion();
    this.updateTab();
    this.initProfilerInfo();
  },
  updated() {
    this.updateTab();
  },
  mounted() {
    let length = 0;
    if(this.isSingle){
      this.tabsSingle.forEach((t) => length += t.length);
      this.left = length * (this.$store.state.language === 'en-us' ? 10 : 20) + 10;
    }else {
      this.tabs.forEach((t) => length += t.length);
      // 10(px of en-us char), 20(px of zh-cn char), 40(padding) used to calculate the position of path label
      this.left = length * (this.$store.state.language === 'en-us' ? 10 : 20) + 40;
    }
  },
  watch:{
    isSingle:{
      handler(newValue,oldValue){
        if(newValue != oldValue){
          let length = 0;
          if(this.isSingle){
            this.tabsSingle.forEach((t) => length += t.length);
            this.left = length * (this.$store.state.language === 'en-us' ? 10 : 20) + 10;
          }else{
            this.tabs.forEach((t) => length += t.length);
            // 10(px of en-us char), 20(px of zh-cn char), 40(padding) used to calculate the position of path label
            this.left = length * (this.$store.state.language === 'en-us' ? 10 : 20) + 40;
          }
        }
      }
    }
  },
  methods: {
    /**
     * Update page state
     */
    updateTab() {
      const path = this.$route.path;
      this.tab = path.includes('/profiling-gpu/cluster') ? this.tabs[1] : this.tabs[0];
    },
    /**
     * On tab click
     */
    onTabClick() {
      const path = this.tab === this.tabs[0] ? 'single' : 'cluster';
      this.$router.push({
        path: '/profiling-gpu/' + path,
        query: this.$route.query,
      });
    },
    /**
     *  init
     */
    initProfilerInfo() {
      return new Promise((resolve) => {
        const params = {
          profile: this.trainInfo.dir,
          train_id: this.trainInfo.id,
        };
        RequestService.getProfilerDeviceData(params)
                .then(
                        (res) => {
                          if (Object.keys(res.data).length > 0) {
                            const rankIDList = res.data.device_list.sort((a, b) => +a - +b);
                            this.isSingle =  rankIDList.length > 1 ? false : true;
                            resolve(true);
                          } else {
                            resolve(false);
                          };
                        },
                )
                .catch(() => {
                  this.rankID = '';
                  resolve(false);
                });
      });
    },
    /**
     * check profiler data version
     */
    checkProfilerDataVersion() {
      let params = {'profile': this.trainInfo.dir, "train_id": this.trainInfo.id};
      RequestService.getProfilerInfo(params).then(
        (res) => {
          if (res.data && !res.data.status) {
            this.$message({
              type: 'warning',
              offset: 50,
              center: true,
              message: this.$t('profiling.dataVersionTips',
                {ms_version: res.data.ms_data_version, mi_version: res.data.mi_version})
            });
          }
        },(error) => {}
      ).catch((e) => {})
    },
  },
};
</script>
<style>
.profiling-dashboard {
  height: 100%;
  background-color: var(--bg-color);
  --tabs-height: 48px;
  padding: 0 32px 24px 32px;
}
.profiling-dashboard .profiling-dashboard-head {
  height: var(--tabs-height);
  position: relative;
}
.profiling-dashboard .profiling-dashboard-head .path {
  position: absolute;
  font-weight: bold;
  top: 12px;
}
.profiling-dashboard .profiling-dashboard-head .el-tabs {
  height: 100%;
}
.profiling-dashboard .profiling-dashboard-head .el-tabs__item {
  font-size: 18px;
  font-weight: bold;
}
.profiling-dashboard .profiling-dashboard-content {
  height: calc(100% - var(--tabs-height));
}
/* Public style of second level of page */
.profiling-dashboard .profiling-dashboard-content .profiling-content-title {
  display: flex;
  font-size: 16px;
  font-weight: bold;
  line-height: 24px;
  align-items: center;
  margin-bottom: 6px;
}
.profiling-dashboard .profiling-dashboard-tab {
  display: flex;
  height: 100%;
  background: var(--bg-color);
  position: relative;
}
.profiling-dashboard .profiling-dashboard-tab .el-tabs__item {
  height: 30px;
  line-height: normal;
}
.profiling-dashboard .profiling-dashboard-tab .dashboard-close-detail {
  position: absolute;
  top: 6px;
  right: 0;
  cursor: pointer;
}
.profiling-dashboard .profiling-dashboard-tab .dashboard-content {
  flex-grow: 1;
  overflow: hidden;
}
</style>

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
  <div class="prof-wrap">
    <div class="prof-head">
      <span class="cl-title-left">{{$t('summaryManage.viewProfiler')}}</span>
      <div class="path-message">
        <span>{{$t('symbols.leftbracket')}}</span>
        <span>{{$t('trainingDashboard.summaryDirPath')}}</span>
        <span>{{summaryPath}}</span>
        <span>{{$t('symbols.rightbracket')}}</span>
      </div>
    </div>
    <div class="prof-content">
      <div class="prof-content-left"
           :class="{collapse:collapse}">
        <div class="helper"
             v-show="!collapse">
          <div class="cur-card">
            <label>{{$t('profiling.curCard')}}</label>
            <el-select v-model="curDashboardInfo.curCardNum"
                       class="card-select"
                       :placeholder="$t('public.select')"
                       @change="selectValueChange">
              <el-option v-for="item in CardNumArr"
                         :key="item.value"
                         :label="item.value + $t('operator.card')"
                         :value="item.value">
              </el-option>
            </el-select>
          </div>
          <div class="helper-title">
            {{$t("profiling.smartHelper")}}
          </div>
          <div class="suggested-title">{{$t("profiling.suggestions")}}</div>
          <div id="helper-tips"></div>
        </div>
        <div class="collapse-btn"
             :class="{collapse:collapse}"
             @click="collapseLeft()">
        </div>
      </div>
      <div class="prof-content-right"
           :class="{collapse:collapse}">
        <div class="tab-container"
             v-show="$route.path === '/profiling-gpu/profiling-dashboard'
                || $route.path === '/profiling-gpu/resource-utilization'">
          <el-tabs v-model="tabData.activeName"
                   @tab-click="paneChange">
            <el-tab-pane v-for="pane in tabData.tabPanes"
                         :key="pane.name"
                         :label="pane.label"
                         :name="pane.name"></el-tab-pane>
          </el-tabs>
        </div>
        <div class="router-container"
             :class="$route.path === '/profiling-gpu/profiling-dashboard'
           || $route.path === '/profiling-gpu/resource-utilization'?'dashboard':'detail'">
          <router-view></router-view>
        </div>
        <div class="close"
             @click="backToDdashboard"
             v-if="$route.path !== '/profiling-gpu/profiling-dashboard'
            && $route.path !== '/profiling-gpu/resource-utilization'">
          <img src="@/assets/images/close-page.png">
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import RequestService from '../../services/request-service';
export default {
  data() {
    return {
      summaryPath: '',
      tipsArrayList: [
        'step_trace-iter_interval',
        'minddata_pipeline-general',
        'minddata_pipeline-dataset_op',
        'minddata_pipeline-generator_op',
        'minddata_pipeline-map_op',
        'minddata_pipeline-batch_op',
        'minddata_cpu_utilization',
        'minddata_warning_op',
      ],
      moreParameter: ['minddata_device_queue', 'minddata_get_next_queue'],
      CardNumArr: [], // Card list
      collapse: false,
      curDashboardInfo: {
        // Current Select card info
        curCardNum: null,
        query: {},
      },
      tabData: {
        activeName: '0',
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
      },
    };
  },
  watch: {},
  mounted() {
    if (
      this.$route.path === 'resource-utilization') {
      this.tabData.activeName = this.tabData.tabPanes[1].name;
    }
    this.$nextTick(() => {
      this.init();
    });
  },
  methods: {
    /**
     * Init function
     */
    init() {
      if (this.$route.query && this.$route.query.id && this.$route.query.dir) {
        this.curDashboardInfo.query.id = this.$route.query.id;
        this.curDashboardInfo.query.dir = this.$route.query.dir;
        this.curDashboardInfo.query.path = this.$route.query.path;
        this.tabData.activeName =
          this.$route.query.activePane || this.tabData.tabPanes[0].name;
        this.summaryPath = decodeURIComponent(this.$route.query.id);
        this.getDeviceList();
      } else {
        this.curDashboardInfo.query.trainingJobId = '';
        this.curDashboardInfo.query.dir = '';
        this.curDashboardInfo.query.path = '';
        this.tabData.activeName = this.tabData.tabPanes[0].name;
        this.$message.error(this.$t('trainingDashboard.invalidId'));
      }
    },
    /**
     * When card number changed,request data again.
     */
    selectValueChange() {
      const helperDiv = document.getElementById('helper-tips');
      helperDiv.innerHTML = '';
      this.getDataOfProfileHelper();
    },
    /**
     * Get card number list
     */
    getDeviceList() {
      const params = {
        profile: this.curDashboardInfo.query.dir,
        train_id: this.curDashboardInfo.query.id,
      };
      RequestService.getProfilerDeviceData(params)
          .then(
              (res) => {
                if (res && res.data && res.data.length) {
                  const deviceList = res.data;
                  deviceList.forEach((item) => {
                    this.CardNumArr.push({
                      value: item,
                    });
                  });
                  this.curDashboardInfo.curCardNum = this.CardNumArr[0].value;
                  this.getDataOfProfileHelper();
                } else {
                  this.CardNumArr = [];
                  this.curDashboardInfo.curCardNum = '';
                  this.curDashboardInfo.initOver = true;
                }
              },
              (error) => {
                this.CardNumArr = [];
                this.curDashboardInfo.curCardNum = '';
                this.curDashboardInfo.initOver = true;
              },
          )
          .catch(() => {
            this.curDashboardInfo.initOver = true;
          });
    },
    /**
     * Get profile helper data
     */
    getDataOfProfileHelper() {
      const params = {
        train_id: this.curDashboardInfo.query.id,
        profile: this.curDashboardInfo.query.dir,
        device_id: this.curDashboardInfo.curCardNum.toString()
          ? this.curDashboardInfo.curCardNum.toString()
          : '0',
      };
      RequestService.queryDataOfProfileHelper(params)
          .then((resp) => {
            if (resp && resp.data) {
              const dataKeys = Object.keys(resp.data);
              const helperDiv = document.getElementById('helper-tips');
              helperDiv.innerHTML = '';
              dataKeys.forEach((item) => {
                if (
                  !this.tipsArrayList.includes(item) &&
                !this.moreParameter.includes(item) &&
                resp.data[item]
                ) {
                  this.$t(`profiling`)[item] = resp.data[item];
                }
                if (item.endsWith('type_label')) {
                  const divDom = document.createElement('div');
                  divDom.setAttribute('class', 'suggested-items-style');
                  divDom.innerHTML = `<div class="helper-icon"></div>
              <div class="helper-container-title">
              ${this.$t(`profiling`)[item].desc}
              </div>`;
                  helperDiv.appendChild(divDom);
                } else if (this.tipsArrayList.includes(item)) {
                  const divDom = document.createElement('div');
                  divDom.setAttribute('class', 'content-style');
                  const content = `${this.$t(`profiling`)[item].desc}`.replace(
                      `{n1}`,
                      resp.data[item][0],
                  );
                  divDom.innerHTML = `<div class="content-icon el-icon-caret-right"></div>
              <div class="helper-content-style">${content}</div>`;
                  helperDiv.appendChild(divDom);
                } else if (item === 'minddata_device_queue') {
                  const deviceEmpty =
                  resp.data['minddata_device_queue'][0] >= 0
                    ? resp.data['minddata_device_queue'][0]
                    : '--';
                  const deviceTotal =
                  resp.data['minddata_device_queue'][1] >= 0
                    ? resp.data['minddata_device_queue'][1]
                    : '--';
                  const deviceFull =
                  resp.data['minddata_device_queue'][2] >= 0
                    ? resp.data['minddata_device_queue'][2]
                    : '--';
                  const divDom = document.createElement('div');
                  divDom.setAttribute('class', 'content-style');
                  const content = `${this.$t(`profilingGPU`)[item].desc}`
                      .replace(
                          `{n1}`,
                          `<span class="nowrap-style"> ${deviceEmpty}</span>`,
                      )
                      .replace(
                          `{n2}`,
                          `<span class="nowrap-style"> ${deviceTotal}</span>`,
                      )
                      .replace(
                          `{n3}`,
                          `<span class="nowrap-style"> ${deviceFull}</span>`,
                      )
                      .replace(
                          `{n4}`,
                          `<span class="nowrap-style"> ${deviceTotal}</span>`,
                      );
                  divDom.innerHTML = `<div class="content-icon el-icon-caret-right"></div>
              <div class="helper-content-style">${content}</div>`;
                  helperDiv.appendChild(divDom);
                } else if (item === 'minddata_get_next_queue') {
                  const getNextEmpty =
                  resp.data['minddata_get_next_queue'][0] >= 0
                    ? resp.data['minddata_get_next_queue'][0]
                    : '--';
                  const getNextTotal =
                  resp.data['minddata_get_next_queue'][1] >= 0
                    ? resp.data['minddata_get_next_queue'][1]
                    : '--';
                  const divDom = document.createElement('div');
                  divDom.setAttribute('class', 'content-style');
                  const content = `${this.$t(`profilingGPU`)[item].desc}`
                      .replace(
                          `{n1}`,
                          `<span class="nowrap-style"> ${getNextEmpty}</span>`,
                      )
                      .replace(
                          `{n2}`,
                          `<span class="nowrap-style"> ${getNextTotal}</span>`,
                      );
                  divDom.innerHTML = `<div class="content-icon el-icon-caret-right"></div>
              <div class="helper-content-style">${content}</div>`;
                  helperDiv.appendChild(divDom);
                } else if (this.$t(`profiling`)[item].anchor) {
                  if (this.$t(`profiling`)[item].anchor.length === 1) {
                    const divDom = document.createElement('div');
                    divDom.setAttribute('class', 'content-style');
                    divDom.innerHTML = `<div class="content-icon el-icon-caret-right"></div>
                <div class="helper-content-style">
                <a target="_blank" href="${this.$t(`profiling`)[item].gpuUrl[0]}">
                ${this.$t(`profiling`)[item].desc}</a></div>`;
                    helperDiv.appendChild(divDom);
                  } else {
                    const divDom = document.createElement('div');
                    divDom.setAttribute('class', 'content-style');
                    const anchorList = this.$t(`profiling`)[item].anchor;
                    let anchorContent = this.$t(`profiling`)[item].desc;
                    for (let i = 0; i < anchorList.length; i++) {
                      const desc = anchorContent.relpace(
                          anchorList[i],
                          `<a target="_blank" href="${
                            this.$t(`profiling`)[item].gpuUrl[i]
                          }">
                      ${anchorList[i]}</a>`,
                      );
                      anchorContent = desc;
                    }
                    divDom.innerHTML = `<div class="content-icon el-icon-caret-right">
                </div><div class="helper-content-style">${anchorContent}</div>`;
                    helperDiv.appendChild(divDom);
                  }
                } else {
                  const divDom = document.createElement('div');
                  divDom.setAttribute('class', 'content-style');
                  divDom.innerHTML = `${this.$t(`profiling`)[item].desc}`;
                  helperDiv.appendChild(divDom);
                }
              });
            }
          })
          .catch(() => {});
    },
    /**
     * Router back to profiling-dashboard
     */
    backToDdashboard() {
      let path = '/profiling-gpu/profiling-dashboard';
      if (this.tabData.activeName === this.tabData.tabPanes[1].name) {
        path = '/profiling-gpu/resource-utilization';
      }
      this.$router.push({
        path: path,
        query: {
          dir: this.curDashboardInfo.query.dir,
          id: this.curDashboardInfo.query.id,
          path: this.curDashboardInfo.query.path,
          activePane: this.tabData.activeName,
          cardNum: this.curDashboardInfo.curCardNum,
        },
      });
    },
    collapseLeft() {
      this.collapse = !this.collapse;
      this.$bus.$emit('collapse');
    },
    /**
     * Tab button click
     * @param {Object} tabItem Tab
     */
    paneChange(tabItem) {
      if (tabItem && tabItem.name) {
        let path = '';
        switch (tabItem.name) {
          case this.tabData.tabPanes[0].name:
            path = '/profiling-gpu/profiling-dashboard';
            break;
          case this.tabData.tabPanes[1].name:
            path = '/profiling-gpu/resource-utilization';
            break;
        }
        if (path) {
          this.$router.push({
            path: path,
            query: {
              dir: this.curDashboardInfo.query.dir,
              id: this.curDashboardInfo.query.id,
              path: this.curDashboardInfo.query.path,
              activePane: this.tabData.activeName,
              cardNum: this.curDashboardInfo.curCardNum,
            },
          });
        }
      }
    },
  },
  destroyed() {
    this.$bus.$off('collapse');
  },
};
</script>
<style>
.prof-wrap {
  height: 100%;
  background: #fff;
}
.prof-wrap .prof-head {
  height: 50px;
  line-height: 50px;
  display: inline-block;
}
.prof-wrap .prof-head .path-message {
  display: inline-block;
  line-height: 20px;
  padding: 18px 0;
  font-weight: bold;
}
.prof-wrap .prof-content {
  height: calc(100% - 50px);
  padding: 0 24px 24px 0;
}
.prof-wrap .prof-content > div {
  float: left;
  height: 100%;
}
.prof-wrap .prof-content .prof-content-left {
  width: 22%;
  transition: width 0.2s;
  position: relative;
}
.prof-wrap .prof-content .prof-content-left .el-input__inner {
  padding: 0 10px;
}
.prof-wrap .prof-content .prof-content-left .helper {
  padding: 32px;
  padding-top: 20px;
  height: 100%;
  overflow-y: auto;
  margin-left: 24px;
  background: #edf0f5;
  word-wrap: break-word;
}
.prof-wrap .prof-content .prof-content-left .helper .nowrap-style {
  white-space: nowrap;
}
.prof-wrap .prof-content .prof-content-left .helper .cur-card {
  padding-bottom: 20px;
  border-bottom: 1px solid #d9d9d9;
}
.prof-wrap .prof-content .prof-content-left .helper .cur-card .card-select {
  width: calc(100% - 120px);
}
.prof-wrap .prof-content .prof-content-left .helper .cur-card > label {
  margin-right: 14px;
}
.prof-wrap .prof-content .prof-content-left .helper .helper-title {
  font-size: 18px;
  font-weight: bold;
  margin: 24px 0;
}
.prof-wrap .prof-content .prof-content-left .helper .helper-title .el-icon-rank {
  float: right;
  cursor: pointer;
}
.prof-wrap .prof-content .prof-content-left .helper .helper-container-title {
  display: inline-block;
  padding: 0 6px;
}
.prof-wrap .prof-content .prof-content-left .helper .helper-icon {
  display: inline-block;
  width: 6px;
  height: 6px;
  margin-top: 6px;
  border-radius: 3px;
  background-color: #00a5a7;
}
.prof-wrap .prof-content .prof-content-left .helper .suggested-title {
  font-weight: bold;
  margin-bottom: 20px;
  font-size: 16px;
}

.prof-wrap .prof-content .prof-content-left .helper .link-title {
  cursor: pointer;
}
.prof-wrap .prof-content .prof-content-left .helper .container-bottom {
  margin-bottom: 16px;
}
.prof-wrap .prof-content .prof-content-left .helper .suggested-items-style {
  display: flex;
  font-weight: bold;
  margin-bottom: 6px;
  margin-top: 10px;
}
.prof-wrap .prof-content .prof-content-left .helper .helper-content-style {
  margin-left: 6px;
  line-height: 20px;
  word-break: break-all;
  text-overflow: ellipsis;
  overflow: hidden;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 8;
}
.prof-wrap .prof-content .prof-content-left .content-icon {
  color: #00a5a7;
  padding-top: 3px;
}
.prof-wrap .prof-content .prof-content-left .content-style {
  display: flex;
}
.prof-wrap .prof-content .prof-content-left .collapse-btn {
  position: absolute;
  right: -21px;
  width: 31px;
  height: 100px;
  top: 50%;
  margin-top: -50px;
  cursor: pointer;
  line-height: 86px;
  z-index: 1;
  text-align: center;
  background-image: url("../../assets/images/collapse-left.svg");
}
.prof-wrap .prof-content .prof-content-left .collapse-btn.collapse {
  background-image: url("../../assets/images/collapse-right.svg");
}
.prof-wrap .prof-content .prof-content-left.collapse {
  width: 0;
}
.prof-wrap .prof-content .prof-content-right {
  width: 78%;
  padding-left: 20px;
  transition: width 0.2s;
  position: relative;
}
.prof-content-right .tab-container {
  width: 100%;
  padding-bottom: 5px;
}
.prof-content-right .tab-container .el-tabs__item {
  font-size: 14px;
  line-height: 14px;
  height: 27px;
}
.prof-content-right .tab-container .el-tabs__item.is-active {
  color: #00a5a7;
  font-weight: bold;
}
.prof-content-right .router-container.detail {
  height: 100%;
}
.prof-content-right .router-container.dashboard {
  height: calc(100% - 46px);
}
.prof-wrap .prof-content .prof-content-right .close {
  position: absolute;
  right: 0;
  top: -10px;
  cursor: pointer;
}
.prof-wrap .prof-content .prof-content-right.collapse {
  width: 100%;
}
</style>

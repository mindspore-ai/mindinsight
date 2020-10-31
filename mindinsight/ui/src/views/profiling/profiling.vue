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
  <div class="prof-wrap">
    <div class="prof-content">
      <div class="prof-content-left"
           :class="{collapse:collapse}">
        <div class="helper"
             v-show="!collapse">
          <div class="summary-path">
            {{$t('trainingDashboard.summaryDirPath')}}
            <span>{{ summaryPath}}</span>
          </div>
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
        <router-view></router-view>
        <div class="close"
             @click="backToDdashboard"
             v-if="$route.path !== '/profiling/profiling-dashboard'">
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
        'minddata_warning_op',
      ],
      moreParameter: ['minddata_device_queue', 'minddata_get_next_queue'],
      CardNumArr: [], // Card list
      collapse: false,
      curDashboardInfo: {
        // Current Select card info
        curCardNum: null,
        query: {},
        initOver: false,
      },
    };
  },
  watch: {},
  mounted() {
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
        this.summaryPath = decodeURIComponent( this.$route.query.id);
        this.getDeviceList();
      } else {
        this.curDashboardInfo.query.trainingJobId = '';
        this.curDashboardInfo.query.dir = '';
        this.curDashboardInfo.query.path = '';
        this.$message.error(this.$t('trainingDashboard.invalidId'));
      }
    },
    /**
     * When card mumber changed,request data again.
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
                  const content = `${this.$t(`profiling`)[item].desc}`
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
                  const content = `${this.$t(`profiling`)[item].desc}`
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
                <a target="_blank" href="${this.$t(`profiling`)[item].url[0]}">
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
                            this.$t(`profiling`)[item].url[i]
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
      this.$router.push({
        path: '/profiling/profiling-dashboard',
        query: {
          dir: this.curDashboardInfo.query.dir,
          id: this.curDashboardInfo.query.id,
          path: this.curDashboardInfo.query.path,
        },
      });
    },
    collapseLeft() {
      this.collapse = !this.collapse;
      this.$bus.$emit('collapse');
    },
  },
  destroyed() {
    this.$bus.$off('collapse');
  },
};
</script>
<style lang="scss">
.prof-wrap {
  height: 100%;
  background: #fff;
  .prof-content {
    height: 100%;
    padding: 24px 24px 24px 0;
    & > div {
      float: left;
      height: 100%;
    }
    .prof-content-left {
      width: 22%;
      transition: width 0.2s;
      position: relative;
      .el-input__inner {
        padding: 0 10px;
      }
      .helper {
        padding: 32px;
        padding-top: 20px;
        height: 100%;
        overflow-y: auto;
        margin-left: 24px;
        background: #edf0f5;
        word-wrap: break-word;
        .summary-path {
          line-height: 24px;
          font-size: 14px;
          overflow: hidden;
          font-weight: bold;
          padding-bottom: 10px;
          word-break: break-all;
          text-overflow: -o-ellipsis-lastline;
          overflow: hidden;
          text-overflow: ellipsis;
          display: -webkit-box;
          -webkit-line-clamp: 4;
          -webkit-box-orient: vertical;
        }
        .nowrap-style {
          white-space: nowrap;
        }
        .cur-card {
          margin-bottom: 32px;
          .card-select {
            width: calc(100% - 120px);
          }
          & > label {
            margin-right: 14px;
          }
        }
        .helper-title {
          font-size: 20px;
          font-weight: bold;
          margin-bottom: 32px;
          .el-icon-rank {
            float: right;
            cursor: pointer;
          }
        }
        .helper-container-title {
          display: inline-block;
          padding: 0 6px;
        }
        .helper-icon {
          display: inline-block;
          width: 6px;
          height: 6px;
          margin-top: 6px;
          border-radius: 3px;
          background-color: #00a5a7;
        }
        .suggested-title {
          font-weight: bold;
          margin-bottom: 20px;
          font-size: 16px;
        }
        .container-bottom {
          margin-bottom: 16px;
        }
        .suggested-items-style {
          display: flex;
          font-weight: bold;
          margin-bottom: 6px;
          margin-top: 10px;
        }
        .helper-content-style {
          margin-left: 6px;
          line-height: 20px;
          word-break: break-all;
          text-overflow: ellipsis;
          overflow: hidden;
          display: -webkit-box;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 8;
        }
      }
      .content-icon {
        color: #00a5a7;
        padding-top: 3px;
      }
      .content-style {
        display: flex;
      }
      .collapse-btn {
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
        background-image: url('../../assets/images/collapse-left.svg');
      }
      .collapse-btn.collapse {
        background-image: url('../../assets/images/collapse-right.svg');
      }
    }
    .prof-content-left.collapse {
      width: 0;
    }
    .prof-content-right {
      width: 78%;
      padding-left: 20px;
      transition: width 0.2s;
      position: relative;
      .close {
        position: absolute;
        right: 0;
        top: -10px;
        cursor: pointer;
      }
    }
    .prof-content-right.collapse {
      width: 100%;
    }
  }
}
</style>

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
          <div class="cur-card">
            <label>{{$t('profiling.curCard')}}</label>
            <el-select v-model="curDashboardInfo.curCardNum"
                       class="card-select"
                       :placeholder="$t('public.select')">
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
      CardNumArr: [],
      collapse: false,
      curDashboardInfo: {
        curCardNum: '',
        query: {},
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
    init() {
      if (this.$route.query && this.$route.query.id && this.$route.query.dir) {
        this.curDashboardInfo.query.id = this.$route.query.id;
        this.curDashboardInfo.query.dir = this.$route.query.dir;
        this.curDashboardInfo.query.path = this.$route.query.path;
        this.getDeviceList();
      } else {
        this.curDashboardInfo.query.trainingJobId = '';
        this.curDashboardInfo.query.dir = '';
        this.curDashboardInfo.query.path = '';
        this.$message.error(this.$t('trainingDashboard.invalidId'));
      }
    },
    getDeviceList() {
      const params = {
        profile: this.curDashboardInfo.query.dir,
        train_id: this.curDashboardInfo.query.id,
      };
      RequestService.getProfilerDeviceData(params)
          .then((res) => {
            if (res && res.data) {
              const deviceList = res.data;
              if (deviceList.length) {
                deviceList.forEach((item) => {
                  this.CardNumArr.push({
                    value: item,
                  });
                });
                this.curDashboardInfo.curCardNum = this.CardNumArr[0].value;
              }
            } else {
              this.CardNumArr = [];
              this.curDashboardInfo.curCardNum = '';
            }
          })
          .catch(() => {});
    },
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
    padding: 32px 32px 32px 0;
    & > div {
      float: left;
      height: 100%;
    }
    .prof-content-left {
      width: 25%;
      transition: width 0.2s;
      position: relative;
      .el-input__inner {
        padding: 0 10px;
      }
      .helper {
        padding: 32px;
        height: 100%;
        margin-left: 32px;
        background: #edf0f5;
        .cur-card {
          margin-bottom: 32px;
          .card-select {
            width: calc(100% - 70px);
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
       .collapse-btn.collapse{
         background-image: url('../../assets/images/collapse-right.svg');
       }
    }
    .prof-content-left.collapse {
      width: 0;
    }
    .prof-content-right {
      width: 75%;
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

<!--
Copyright 2019 Huawei Technologies Co., Ltd.All Rights Reserved.

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
  <div class="cl-header">
    <!-- head logo and click -->
    <div class="cl-header-logo"
         @click="relPath('/')">
      <img src="../assets/images/logo.png"
           alt="" />
    </div>
    <div class="cl-header-nav">
      <div>
        <el-menu router
                 unique-opened
                 :default-active="getActive()"
                 class="el-menu-demo"
                 mode="horizontal">
          <el-menu-item index="/summary-manage">{{$t("summaryManage.summaryList")}}</el-menu-item>
          <el-menu-item index="/model-traceback">{{$t("summaryManage.modelTraceback")}}</el-menu-item>
          <el-menu-item index="/data-traceback">{{$t("summaryManage.dataTraceback")}}</el-menu-item>
        </el-menu>
      </div>
    </div>
    <!-- head tool on the right -->
    <div class="cl-header-right"
         v-if="this.$route.path.indexOf('/scalar') > 0
         || this.$route.path.indexOf('/image') > 0
         || this.$route.path.indexOf('/histogram') > 0
         || this.$route.path.indexOf('/training-dashboard') > 0">
      <!-- automatic refresh switch -->
      <el-switch v-model="isTimeReload"
                 :active-text="$t('header.timeReload')+$t('symbols.leftbracket')+
                 timeReloadValue+$t('header.timeSecond')+$t('symbols.rightbracket')"
                 @change="timeReload"></el-switch>
      <i class="el-icon-edit"
         v-if="isTimeReload && !isShowInp"
         @click="editTime"></i>

      <el-input v-if="isTimeReload && isShowInp"
                v-model="newReloadValue"
                type="text"
                @input="timeValueChange"></el-input>

      <i class="el-icon-check"
         v-if="isTimeReload && isShowInp"
         @click="saveTimeValue"></i>
      <i class="el-icon-close"
         v-if="isTimeReload && isShowInp"
         @click="cancleTimeValue"></i>

      <!-- manual refresh switch -->
      <img src="../assets/images/reload.png"
           alt=""
           width="24"
           class="cl-header-img"
           v-if="!isReload"
           @click="setReload"
           :title="$t('header.refreshData')" />
      <img src="../assets/images/reload.png"
           alt=""
           width="24"
           class="cl-header-img cl-reload"
           v-if="isReload"
           :title="$t('header.RefreshingData')" />
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      isShowInp: false,
      timeReloadValue: this.$store.state.timeReloadValue,
      newReloadValue: this.$store.state.timeReloadValue,
    };
  },
  computed: {
    // return isReload status
    isReload() {
      return this.$store.state.isReload;
    },
    // set and get isTimeReload status
    isTimeReload: {
      get() {
        return this.$store.state.isTimeReload;
      },
      set(val) {},
    },
  },
  watch: {},
  mounted() {},
  methods: {
    // click reload
    setReload() {
      this.$store.commit('clearToken');
      this.$store.commit('setIsReload', true);
    },
    // redirecton
    relPath(path) {
      this.$router.push(path);
    },
    // save isTimeReload status
    timeReload(val) {
      localStorage.isTimeReload = val;
      this.$store.commit('setIsTimeReload', val);
    },

    editTime() {
      this.isShowInp = true;
    },

    saveTimeValue() {
      if (this.newReloadValue) {
        this.newReloadValue =
          this.newReloadValue < 3
            ? 3
            : this.newReloadValue > 300
            ? 300
            : this.newReloadValue;
        const timeValue = this.newReloadValue;
        this.timeReloadValue = timeValue;
        localStorage.timeReloadValue = timeValue;
        this.$store.commit('setTimeReloadValue', timeValue);
        this.isShowInp = false;
      } else {
        this.cancleTimeValue();
      }
    },
    cancleTimeValue() {
      this.isShowInp = false;
      this.newReloadValue = this.timeReloadValue;
    },
    timeValueChange() {
      this.newReloadValue = this.newReloadValue
          .toString()
          .replace(/[^\.\d]/g, '')
          .replace(/\./g, '');
    },
    // get active menu item
    getActive() {
      const str = this.$route.path.split('/');
      if (str.length > 2) {
        if (str[1] === 'train-manage') {
          return '/summary-manage';
        } else {
          return '/' + str[1];
        }
      } else {
        return this.$route.path;
      }
    },
  },
};
</script>
<style lang="scss">
@import '@/assets/css/variable';

// header style
.cl-header {
  height: $headerHeight;
  background-image: $headerBackground;
  display: flex;
  color: $headerColor;
  flex-shrink: 0;
  // logo style
  .cl-header-logo {
    width: 161px;
    margin-left: 36px;
    margin-top: 17px;
    img {
      cursor: pointer;
    }
  }

  // header right style
  .cl-header-right {
    flex: 1;
    padding-right: 36px;
    color: #9ea4b3;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    .cl-header-img {
      margin-left: 20px;
      cursor: pointer;
    }
    .el-icon-edit {
      margin-left: 5px;
    }

    i {
      font-size: 18px;
      margin: 0 2px;
      color: #00a5a7;
      cursor: pointer;
    }

    .el-icon-close {
      color: #f56c6c;
    }
  }

  // reload style
  .cl-reload {
    animation: rotate 1s infinite linear;
  }
  @keyframes rotate {
    0% {
      transform: rotate(0deg);
    }

    100% {
      transform: rotate(1turn);
    }
  }
  .cl-header-right .el-input {
    width: 45px;
    input {
      padding: 0;
      text-align: center;
    }
  }
  .cl-header-nav {
    margin-left: 50px;
    flex: 1;

    .el-menu {
      border-bottom: none;
    }
    .el-menu--horizontal > .el-menu-item {
      font-size: 16px;
      color: #fff;
      padding-top: 4px;
    }
    .el-menu--horizontal > .el-menu-item.is-active {
      color: #00a5a7 !important;
      background: none;
    }

    .el-menu--horizontal > .el-menu-item:not(.is-disabled):focus,
    .el-menu--horizontal > .el-menu-item:not(.is-disabled):hover,
    .el-menu--horizontal > .el-submenu .el-submenu__title:hover {
      background: none;
      color: #fff;
    }
  }
}
</style>

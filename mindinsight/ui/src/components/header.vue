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
          <el-menu-item index="/summary-manage"
                        :title='$t("summaryManage.summaryList")'>
            {{$t("summaryManage.summaryList")}}
          </el-menu-item>
          <el-menu-item index="/model-traceback"
                        :title='$t("summaryManage.modelTraceback")'>
            {{$t("summaryManage.modelTraceback")}}
          </el-menu-item>
          <el-menu-item index="/data-traceback"
                        :title='$t("summaryManage.dataTraceback")'>
            {{$t("summaryManage.dataTraceback")}}
          </el-menu-item>
          <el-menu-item index="/compare-plate"
                        :title='$t("summaryManage.comparePlate")'>
            {{$t("summaryManage.comparePlate")}}
          </el-menu-item>
          <el-menu-item index="/hardware-visual"
                        :title='$t("summaryManage.hardwareVisual")'>
            {{$t("summaryManage.hardwareVisual")}}
          </el-menu-item>
        </el-menu>
      </div>
    </div>
    <!-- head tool on the right -->
    <div class="cl-header-right"
         v-if="this.$route.path.indexOf('/scalar') > 0
         || this.$route.path.indexOf('/image') > 0
         || this.$route.path.indexOf('/histogram') > 0
         || this.$route.path.indexOf('/tensor') > 0
         || this.$route.path.indexOf('/training-dashboard') > 0
         || !this.$route.path.indexOf('/compare-plate')
         || !this.$route.path.indexOf('/hardware-visual')">
      <div class="reload-training"
           v-if="this.$route.path.indexOf('/scalar') > 0
          || this.$route.path.indexOf('/image') > 0
          || this.$route.path.indexOf('/histogram') > 0
          || this.$route.path.indexOf('/tensor') > 0
          || this.$route.path.indexOf('/training-dashboard') > 0
          || !this.$route.path.indexOf('/compare-plate')">
        <!-- automatic refresh switch -->
        <el-switch v-model="isTimeReload"
                   :active-text="$t('header.timeReload')+$t('symbols.leftbracket')+
                  timeReloadValue+$t('header.timeSecond')+$t('symbols.rightbracket')"
                   @change="timeReload"></el-switch>
        <i class="el-icon-edit"
           :title="$t('header.timeReloadScope')"
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
           @click="cancelTimeValue"></i>
      </div>
      <div class="reload-hardware"
           v-if="!this.$route.path.indexOf('/hardware-visual')">
        <!-- automatic refresh switch -->
        <el-switch v-model="isHardwareTimeReload"
                   :active-text="$t('header.timeReload')+$t('symbols.leftbracket')+
                  hardwareTimeReloadValue+$t('header.timeSecond')+$t('symbols.rightbracket')"
                   @change="hardwareTimeReload"></el-switch>
        <i class="el-icon-edit"
           :title="$t('header.timeReloadScope')"
           v-if="isHardwareTimeReload && !isShowHardwareInp"
           @click="editHardwareTime"></i>

        <el-input v-if="isHardwareTimeReload && isShowHardwareInp"
                  v-model="newHardwareReloadValue"
                  type="text"
                  @input="hardwareTimeValueChange"></el-input>

        <i class="el-icon-check"
           v-if="isHardwareTimeReload && isShowHardwareInp"
           @click="saveHardwareTimeValue"></i>
        <i class="el-icon-close"
           v-if="isHardwareTimeReload && isShowHardwareInp"
           @click="cancelHardwareTimeValue"></i>
      </div>

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
           :title="$t('header.refreshingData')" />
    </div>
    <div class="md-header-language"
         v-show="isLanguage">
      <span class="spanLanguage"
            :class="[isChinese?'active':'']"
            @click="changeLanguage('zh-cn')">
        {{$t('public.zhLanguage')}}
      </span>
      <span class="spanLine">/</span>
      <span class="spanLanguage"
            :class="[!isChinese?'active':'']"
            @click="changeLanguage('en-us')">
        {{$t('public.enLanguage')}}
      </span>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      isShowInp: false,
      isLanguage: true,
      timeReloadValue: this.$store.state.timeReloadValue,
      newReloadValue: this.$store.state.timeReloadValue,
      isShowHardwareInp: false,
      hardwareTimeReloadValue: this.$store.state.hardwareTimeReloadValue,
      newHardwareReloadValue: this.$store.state.hardwareTimeReloadValue,
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
    isChinese() {
      let isChinese = true;
      const languageList = ['zh-cn', 'en-us'];
      const language = window.localStorage.getItem('milang');

      if (language && languageList.includes(language)) {
        isChinese = language === languageList[0];
      } else {
        window.localStorage.setItem('milang', languageList[0]);
      }
      return isChinese;
    },
    // set and get isHardwareTimeReload status
    isHardwareTimeReload: {
      get() {
        return this.$store.state.isHardwareTimeReload;
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
    // training reload setting
    timeReload(val) {
      localStorage.isTimeReload = val;
      this.$store.commit('setIsTimeReload', val);
    },

    editTime() {
      this.isShowInp = true;
    },

    saveTimeValue() {
      if (this.newReloadValue >= 0) {
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
        this.cancelTimeValue();
      }
    },
    cancelTimeValue() {
      this.isShowInp = false;
      this.newReloadValue = this.timeReloadValue;
    },
    timeValueChange() {
      if (this.newReloadValue === '') {
        return;
      }
      this.newReloadValue = this.newReloadValue
          .toString()
          .replace(/[^\.\d]/g, '')
          .replace(/\./g, '');
      this.newReloadValue = Number(this.newReloadValue);
    },
    // hardware reload setting
    hardwareTimeReload(val) {
      localStorage.isHardwareTimeReload = val;
      this.$store.commit('setIsHardwareTimeReload', val);
    },

    editHardwareTime() {
      this.isShowHardwareInp = true;
    },

    saveHardwareTimeValue() {
      if (this.newHardwareReloadValue >= 0) {
        this.newHardwareReloadValue =
          this.newHardwareReloadValue < 3
            ? 3
            : this.newHardwareReloadValue > 300
            ? 300
            : this.newHardwareReloadValue;
        const timeValue = this.newHardwareReloadValue;
        this.hardwareTimeReloadValue = timeValue;
        localStorage.hardwareTimeReloadValue = timeValue;
        this.$store.commit('setHardwareTimeReloadValue', timeValue);
        this.isShowHardwareInp = false;
      } else {
        this.cancelHardwareTimeValue();
      }
    },
    cancelHardwareTimeValue() {
      this.isShowHardwareInp = false;
      this.newHardwareReloadValue = this.hardwareTimeReloadValue;
    },
    hardwareTimeValueChange() {
      if (this.newHardwareReloadValue === '') {
        return;
      }
      this.newHardwareReloadValue = this.newHardwareReloadValue
          .toString()
          .replace(/[^\.\d]/g, '')
          .replace(/\./g, '');
      this.newHardwareReloadValue = Number(this.newHardwareReloadValue);
    },

    // get active menu item
    getActive() {
      const str = this.$route.path.split('/');
      if (str.length > 2) {
        if (str[1] === 'train-manage' || str[1] === 'profiling') {
          return '/summary-manage';
        } else {
          return '/' + str[1];
        }
      } else {
        return this.$route.path;
      }
    },
    changeLanguage(lan) {
      localStorage.setItem('milang', lan);
      window.location.reload();
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
  .md-header-language {
    width: 100px;
    line-height: 64px;
    .spanLine {
      margin: 0 5px;
    }
    .spanLanguage {
      cursor: pointer;
    }
    .active {
      color: #00a5a7;
    }
  }
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
    .el-input {
      width: 45px;
      input {
        padding: 0;
        text-align: center;
      }
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

  .cl-header-nav {
    margin-left: 50px;
    flex: 2.2;

    .el-menu {
      border-bottom: none;
    }
    .el-menu--horizontal > .el-menu-item {
      font-size: 16px;
      color: #fff;
      padding-top: 4px;
      max-width: 20%;
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
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

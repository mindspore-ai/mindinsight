<!--
Copyright 2019-2021 Huawei Technologies Co., Ltd.All Rights Reserved.

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
          <el-menu-item index="/debugger"
                        v-if="showDebugger">{{$t("debugger.debugger")}}</el-menu-item>
          <el-menu-item index="/explain">{{$t("explain.explain")}}</el-menu-item>
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
         || this.$route.path == '/summary-manage'">
      <div class="reload-training">
        <!-- automatic refresh switch -->
        <el-switch v-model="isTimeReload"
                   :title="this.$route.path.includes('/training-dashboard') ?
                   $t('trainingDashboard.switchTitle') : ''"
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
    <div class="theme-container">
      <el-select v-model="themeIndex"
                 @change="themeChange">
        <el-option v-for="option in themeOptions"
                   :key="option.value"
                   :label="option.label"
                   :value="option.value"></el-option>
      </el-select>
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
      showDebugger: window.enableDebugger,
      themeIndex: this.$store.state.themeIndex,
      themeOptions: [
        {
          value: '0',
          label: this.$t('public.light'),
        },
        {
          value: '1',
          label: this.$t('public.dark'),
        },
      ],
      path: null,
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
        this.$store.setLanguage(languageList[0]);
      }
      return isChinese;
    },
  },
  watch: {
    path(newValue, oldValue) {
      if (oldValue) {
        this.clearPageIndex();
      }
    },
  },
  mounted() {},
  methods: {
    /**
     * The logic of clear page index memory
     */
    clearPageIndex() {
      if (sessionStorage.getItem('XAIPageIndex')) {
        sessionStorage.removeItem('XAIPageIndex');
      }
      if (sessionStorage.getItem('summaryPageIndex')) {
        sessionStorage.removeItem('summaryPageIndex');
      }
    },
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
        this.newReloadValue = this.newReloadValue < 3 ? 3 : this.newReloadValue > 300 ? 300 : this.newReloadValue;
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
    // get active menu item
    getActive() {
      const str = this.$route.path.split('/');
      let path;
      if (str.length > 1) {
        if (!str[1]) {
          return;
        }
        if (str[1] === 'debugger') {
          path = '/debugger';
        } else if (str[1] === 'explain') {
          path = '/explain';
        } else {
          path = '/summary-manage';
        }
      } else {
        path = '/summary-manage';
      }
      if (this.path) {
        if (this.path !== path) {
          this.path = path;
        }
      } else {
        this.path = path;
      }
      return path;
    },
    changeLanguage(lan) {
      localStorage.setItem('milang', lan);
      window.location.reload();
    },
    themeChange() {
      localStorage.setItem('miTheme', this.themeIndex);
      window.location.reload();
    },
  },
};
</script>
<style>
.cl-header {
  height: 64px;
  background-image: linear-gradient(180deg, var(--header-bg-min-color) 0%, var(--header-bg-max-color) 100%);
  display: flex;
  color: #fff;
  flex-shrink: 0;
}
.cl-header .md-header-theme {
  width: 100px;
  line-height: 64px;
}
.cl-header .md-header-theme .spanLine {
  margin: 0 5px;
}
.cl-header .md-header-theme .spanTheme {
  cursor: pointer;
}
.cl-header .md-header-theme .active {
  color: #00a5a7;
}
.cl-header .theme-container {
  width: 150px;
  line-height: 64px;
  margin-right: 15px;
}
.cl-header .md-header-language {
  width: 100px;
  line-height: 64px;
}
.cl-header .md-header-language .spanLine {
  margin: 0 5px;
}
.cl-header .md-header-language .spanLanguage {
  cursor: pointer;
}
.cl-header .md-header-language .active {
  color: #00a5a7;
}
.cl-header .cl-header-logo {
  width: 161px;
  margin-left: 36px;
  margin-top: 17px;
}
.cl-header .cl-header-logo img {
  cursor: pointer;
}
.cl-header .cl-header-right {
  flex: 1;
  padding-right: 36px;
  color: #9ea4b3;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}
.cl-header .cl-header-right .cl-header-img {
  margin-left: 20px;
  cursor: pointer;
}
.cl-header .cl-header-right .el-icon-edit {
  margin-left: 5px;
}
.cl-header .cl-header-right i {
  font-size: 18px;
  margin: 0 2px;
  color: #00a5a7;
  cursor: pointer;
}
.cl-header .cl-header-right .el-icon-close {
  color: #f56c6c;
}
.cl-header .cl-header-right .el-input {
  width: 45px;
}
.cl-header .cl-header-right .el-input input {
  padding: 0;
  text-align: center;
}
.cl-header .cl-reload {
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
.cl-header .cl-header-nav {
  margin-left: 50px;
  flex: 2.2;
}
.cl-header .cl-header-nav .el-menu {
  border-bottom: none;
}
.cl-header .cl-header-nav .el-menu--horizontal > .el-menu-item {
  font-size: 16px;
  color: #fff;
  padding-top: 4px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.cl-header .cl-header-nav .el-menu--horizontal > .el-menu-item.is-active {
  color: #00a5a7 !important;
  background: none;
}
.cl-header .cl-header-nav .el-menu--horizontal > .el-menu-item:not(.is-disabled):focus,
.cl-header .cl-header-nav .el-menu--horizontal > .el-menu-item:not(.is-disabled):hover,
.cl-header .cl-header-nav .el-menu--horizontal > .el-submenu .el-submenu__title:hover {
  background: none;
  color: #fff;
}
</style>

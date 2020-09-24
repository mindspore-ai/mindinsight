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
  <div id="app">
    <div v-if="showWarmText"
         class="warm-content">
      <span class="warm-text">{{ $t('public.browserWarning') }}</span>
      <span class="cancel-icon"
            @click="cancelWarmText"></span>
    </div>
    <Header></Header>
    <div class="cl-center"
         :class="showWarmText ? 'cl-center-height' : ''">

      <router-view></router-view>
    </div>
  </div>
</template>
<script>
import Header from '@/components/header.vue';
export default {
  data() {
    return {
      showWarmText: true,
    };
  },

  mounted() {
    // Check the browser
    this.showWarmText = this.$warmBrowser;
    this.$bus.$on('showWarmText', (val) => {
      this.showWarmText = val;
    });
  },
  methods: {
    /**
     * close the browser tip
     */

    cancelWarmText() {
      this.showWarmText = false;
    },
  },
  destroyed() {
    this.$bus.$off('showWarmText');
  },
  components: {
    Header,
  },
};
</script>
<style lang="scss">
#app {
  height: 100%;
  background-color: #e7ecf2;
  min-width: 1260px;
  min-height: 664px;
  .el-slider__runway {
    height: 3px;
  }
  .el-slider__bar {
    height: 3px;
  }
  .el-slider__button-wrapper {
    top: -16px;
  }
}

.warm-content {
  width: 100%;
  height: 40px;
  background: #fff9d9;
  font-size: 12px;
  padding: 0 14px;
  line-height: 40px;
  .cancel-icon {
    width: 12px;
    height: 40px;
    background: url('./assets/images/cancel-warm-text.png') no-repeat
      center/12px 12px;
    cursor: pointer;
    float: right;
    display: block;
  }
}

.cl-center {
  height: calc(100% - 64px);
  overflow: hidden;
  color: #333;
}

.cl-center-height {
  height: calc(100% - 104px);
}
.cl-title {
  height: 50px;
  line-height: 50px;
  display: flex;
  background-color: #fff;
}
.cl-title-left {
  font-size: 20px;
  font-weight: bold;
  padding-left: 32px;
  flex: 1;
}
.cl-title-right {
  padding-right: 32px;
  flex: 1;
  text-align: right;
}
</style>

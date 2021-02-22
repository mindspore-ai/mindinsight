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

  <el-button @click="rightClick"
             ref="scalarBtn"
             size="mini">{{right}}</el-button>
</template>
<script>
export default {
  props: {
    title: {
      type: String,
    },
    right: {
      type: String,
    },
    initOver: {
      type: Boolean,
    },
  },

  watch: {
    initOver(newValue, oldValue) {
      if (newValue) {
        this.initOk = true;
      }
    },
  },
  data() {
    return {
      initOk: false,
    };
  },
  computed: {},
  mounted() {},
  methods: {
    rightClick() {
      this.$emit('compareClick');
      const scalarBtn = this.$refs.scalarBtn.$el;
      scalarBtn.blur();
    },
  },
};
</script>
<style>
</style>

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
  <div class="empty-container">
    <img :src="require('@/assets/images/nodata.png')" />
    <span>{{ text }}</span>
  </div>
</template>

<script>
export const [NO_DATA, EMPTY_DATA, LOADING_DATA, COMING_SOON] = ['noData', 'emptyData', 'dataLoading', 'stayTuned'];
export default {
  props: {
    state: {
      type: String,
      default: LOADING_DATA,
    },
  },
  data() {
    return {
      noData: this.$t('public.noData'),
      emptyData: this.$t('public.emptyData'),
      dataLoading: this.$t('public.dataLoading'),
      stayTuned: this.$t('public.stayTuned'),
    };
  },
  computed: {
    text() {
      if (this[this.state]) return this[this.state];
      return '';
    },
  },
};
</script>

<style scoped>
.empty-container {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.empty-container img {
  margin-bottom: 10px;
  object-fit: none;
}
</style>

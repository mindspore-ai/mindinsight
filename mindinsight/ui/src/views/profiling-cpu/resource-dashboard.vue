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
  <div class="cl-resource-content">
    <div class="dashboard-item">
      <div class="title-item">
        <div class="title-text">
          {{$t('profiling.structuralCpuUtil')}}
        </div>
        <div class="detail-link"
             :class="{disabled: true}">
          <button :disabled="true"
                  @click="viewDetail('cpu-utilization')">
            {{$t('profiling.viewDetail')}}
            <i class="el-icon-d-arrow-right"></i>
          </button>
        </div>
      </div>
      <div class="content-item">
        <div class="noData-content">
          <img :src="require('@/assets/images/nodata.png')" />
          <p>{{$t("public.noSupport")}}</p>
        </div>
      </div>
    </div>
    <div class="dashboard-item margin-item">
      <div class="title-item">
        <div class="title-text">
          {{$t('profiling.memory.usedMemory')}}
        </div>
        <div class="detail-link"
             :class="{disabled: true}">
          <button :disabled="true"
                  @click="viewDetail('memory-utilization')">
            {{$t('profiling.viewDetail')}}
            <i class="el-icon-d-arrow-right"></i>
          </button>
        </div>
      </div>
      <div class="content-item">
        <div class="noData-content">
          <div>
            <img :src="require('@/assets/images/nodata.png')" />
          </div>
          <p>{{$t("public.noSupport")}}</p>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
export default {
  props: {
    rankID: String,
  },
  data() {
    return {
      trainInfo: {
        id: this.$route.query.id,
        path: this.$route.query.path,
        dir: this.$route.query.dir,
      },
    };
  },
};
</script>
<style scoped>
.cl-resource-content {
  height: 100%;
  overflow-y: auto;
}
.cl-resource-content .dashboard-item {
  width: 100%;
  height: calc(50% - 10px);
  padding: 15px;
  border: solid 1px var(--border-color);
  background: var(--bg-color);
  border-radius: 4px;
  min-height: 284px;
}
.cl-resource-content .dashboard-item .title-item {
  display: flex;
  height: 24px;
}
.cl-resource-content .dashboard-item .title-item .title-text {
  flex: 1;
  font-size: 16px;
  font-weight: bold;
  line-height: 24px;
}
.cl-resource-content .dashboard-item .title-item .detail-link {
  cursor: pointer;
  font-size: 12px;
  height: 18px;
  line-height: 12px;
  padding-top: 2px;
}
.cl-resource-content .dashboard-item .title-item .detail-link a {
  color: var(--theme-color);
  padding-right: 6px;
}
.cl-resource-content .dashboard-item .title-item .detail-link button {
  color: var(--theme-color);
  border: none;
  background-color: var(--bg-color);
  cursor: pointer;
}
.cl-resource-content .dashboard-item .title-item .detail-link.disabled button {
  color: #c0c4cc;
  cursor: not-allowed;
}
.cl-resource-content .dashboard-item .content-item {
  height: calc(100% - 44px);
  margin-top: 20px;
}
.cl-resource-content .margin-item {
  margin-top: 20px;
}
.cl-resource-content .noData-content {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}
.cl-resource-content .noData-content p,
.cl-resource-content .noData-content .noData-text {
  font-size: 16px;
}
</style>

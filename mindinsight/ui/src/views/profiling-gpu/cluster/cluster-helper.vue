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
  <div class="helper">
    <div class="helper-title">
      {{$t("profiling.smartHelper")}}
    </div>
    <div class="suggested-title">{{$t("profiling.suggestions")}}</div>
    <div id="helper-tips">
      <div v-for="(item,key) in clusterHelperArr"
           :key="key">
        <div class="suggested-items-style">
          <div class="helper-icon"></div>
          <div class="helper-container-title">{{item.title}}</div>
        </div>
        <div class="content-style"
             v-if="!item.hasChildren">
          <div class="content-icon el-icon-caret-right"></div>
          <div class="helper-content-style">{{item.content}}</div>
        </div>
        <template v-else>
          <div class="content-style"
               v-for="(value,index) in item.children"
               :key="index">
            <div class="content-icon el-icon-caret-right"></div>
            <div class="helper-content-style">{{value.content}}</div>
          </div>
        </template>
      </div>
      <div class="suggested-items-style">
        <div class="helper-icon"></div>
        <div class="helper-container-title">{{ $t('profiling.common-proposer_type_label.desc') }}</div>
      </div>
      <div class="content-style">
        <div class="content-icon el-icon-caret-right"></div>
        <div class="helper-content-style"><a :href="$t('profilingCluster.clusterGPUGuideUrl')">{{$t('profilingCluster.clusterPerformanceTest')}}</a></div>
      </div>
    </div>
  </div>
</template>

<script>
import RequestService from '@/services/request-service';
export default {
  data() {
    return {
      clusterHelperArr: [],
    };
  },
  mounted() {
    this.getDataOfProfileHelper();
  },
  methods: {
    /**
     * Get profile cluster helper data
     */
    getDataOfProfileHelper() {
      const params = {
        train_id: this.$route.query.id,
      };
      RequestService.queryDataOfProfileClusterHelper(params).then((res) => {
        if (res.data) {
          const helperData = res.data || {};
          this.clusterHelperArr = Object.keys(helperData).map((val) => {
            if (val === 'step_interval' || val === 'flops_per_second') {
              return {
                hasChildren: false,
                title: this.$t(`profilingCluster.${val}_title`),
                content: this.$t(`profilingCluster.${val}`, helperData[val]),
              };
            } else if (val === 'parallel_strategy') {
              const children = Object.keys(helperData[val]).map((value) => {
                return {
                  content: this.$t(`profilingCluster.${val}.${value}`, helperData[val][value]),
                };
              });
              return {
                title: this.$t(`profilingCluster.${val}_title`),
                hasChildren: true,
                children,
              };
            } else if (val === 'cluster_link') {
              const children = helperData[val].map((item) => {
                return {
                  content: this.$t(`profilingCluster.${val}`, item),
                };
              });
              return {
                title: this.$t(`profilingCluster.${val}_title`),
                hasChildren: true,
                children,
              };
            }
          });
        }
      });
    },
  },
};
</script>

<style>
.helper {
  box-sizing: border-box;
  padding: 32px;
  padding-top: 20px;
  height: 100%;
  overflow-y: auto;
  background: var(--module-bg-color);
  word-wrap: break-word;
}
.helper .nowrap-style {
  white-space: nowrap;
}
.helper .helper-title {
  font-size: 18px;
  font-weight: bold;
  margin: 24px 0;
}
.helper .helper-title .el-icon-rank {
  float: right;
  cursor: pointer;
}
.helper .helper-container-title {
  display: inline-block;
  padding: 0 6px;
}
.helper .helper-icon {
  display: inline-block;
  width: 6px;
  height: 6px;
  margin-top: 6px;
  border-radius: 3px;
  background-color: var(--theme-color);
}
.helper .suggested-title {
  font-weight: bold;
  margin-bottom: 20px;
  font-size: 16px;
}
.helper .link-title {
  cursor: pointer;
}
.helper .container-bottom {
  margin-bottom: 16px;
}
.helper .suggested-items-style {
  display: flex;
  font-weight: bold;
  margin-bottom: 6px;
  margin-top: 10px;
}
.helper .helper-content-style {
  margin-left: 6px;
  line-height: 20px;
  word-break: break-all;
  text-overflow: ellipsis;
  overflow: hidden;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 8;
}
.helper .content-icon {
  color: var(--theme-color);
  padding-top: 3px;
}
.helper .content-style {
  display: flex;
}
</style>

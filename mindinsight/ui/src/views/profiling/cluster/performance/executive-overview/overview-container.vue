<!--
Copyright 2022 Huawei Technologies Co., Ltd.All Rights Reserved.

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
  <div class="overview-dashboard">
    <div class="container">
      <div class="header">
        <span class="title">{{
          $t("profilingCluster.parallelStrategyView")
        }}</span>
        <LegendStrategy />
        <div class="brush-switch">
          <div>{{ $t("profilingCluster.showHiddenEdges") }}</div>
          <el-switch
            v-model="isShowHiddenEdges"
            active-color="#13ce66"
            inactive-color="#ccc"
            @change="handleSwitchChange"
          >
          </el-switch>
        </div>
      </div>
      <empty
        v-if="profileIsLoading"
        class="strategy-loading"
        :state="profileLoadingState"
        style="position: absolute; z-index: 999"
      ></empty>
      <div class="strategy-content">
        <div class="right strategy-view">
          <ProfileGraph :isShowHiddenEdges="isShowHiddenEdges" />
          <AttributePanel />
        </div>
        <div class="left">
          <ConfigureView />
        </div>
      </div>
    </div>
    <div class="container">
      <div>
        <span class="title">{{ $t("profilingCluster.mareyView") }}</span>
        <el-popover
          placement="bottom"
          width="300"
          trigger="click"
          :visible-arrow="false"
          @show="handleShowPopover"
          @hide="handleHidePopover"
        >
          <el-tree
            ref="tree"
            class="tree-selector tree-selector-scroll"
            :data="options"
            show-checkbox
            node-key="value"
            default-expand-all
          ></el-tree>
          <el-button
            class="button-with-margin"
            size="mini"
            type="primary"
            slot="reference"
            @click="handleClick"
            style="min-width: 100px;"
          >
            {{ buttonText }}
          </el-button>
        </el-popover>
      </div>
      <div class="marey-content">
        <marey-view ref="child" />
      </div>
    </div>
    <div class="container">
      <div class="header">
        <span class="title">{{ $t("profilingCluster.timeOverview") }}</span>
      </div>
      <div class="timeview-content">
        <TimelineView />
      </div>
    </div>
  </div>
</template>

<script>
import requestService from "@/services/request-service";
import $store from "./store";

import LegendStrategy from "./parallel-view/legend-strategy.vue";
import ProfileGraph from "./parallel-view/profile-graph-new.vue";
import AttributePanel from "./parallel-view/attribute-panel-new.vue";
import ConfigureView from "./parallel-view/configure-view-new.vue";
import TimelineView from "./time-view/timeline-view.vue";
import MareyView from "./marey-view/marey-view-container.vue";
import empty, { LOADING_DATA } from "@/components/empty.vue";

export default {
  components: {
    ProfileGraph,
    AttributePanel,
    ConfigureView,
    TimelineView,
    LegendStrategy,
    MareyView,
    empty,
  },
  data() {
    return {
      trainInfo: {
        id: this.$route.query.id,
        path: this.$route.query.path,
        dir: this.$route.query.dir,
      },
      isShowHiddenEdges: true,
      profileIsLoading: true,
      profileLoadingState: LOADING_DATA,
      popoverVisible: false,
      checkedDevices: [],
      options: [],
    }
  },
  computed: {
    buttonText() {
      return this.popoverVisible ? "确定" : "选择设备";
    }
  },
  created() {
    this.profileIsLoading = true;
    this.fetchDevices();
    this.fetchData();
  },
  methods: {
    handleShowPopover() {
      this.popoverVisible = true;
    },
    handleHidePopover() {
      this.popoverVisible = false;
      this.$nextTick(() => {
        this.$refs.tree.setCheckedKeys(this.checkedDevices);
      });
    },
    handleClick() {
      if (this.popoverVisible) {  // user confirmed the device_list settings.
        const device_list = this.$refs.tree.getCheckedKeys();
        const isEqual = device_list.length === this.checkedDevices.length &&
          device_list.every((value, index) => value === this.checkedDevices[index]);
        if (isEqual) return;
        this.checkedDevices = device_list;
        this.$refs.child.getTimeLineData(device_list);
      }
    },

    fetchDevices() {
      const params = {
        profile: this.trainInfo.dir,
        train_id: this.trainInfo.id,
      };
      requestService.getProfilerDeviceData(params).then(({data}) => {
        this.options = data.device_list
        .sort((a, b) => a - b) // sort according to device num
        .map((device, index) => {
          const value = `${device}`;
          const label = `Device ${device}`;
          if (index < 8) { // default checked
            this.checkedDevices.push(value);
          }
          return { value, label };
        });
        this.$nextTick(() => {
          this.$refs.tree.setCheckedKeys(this.checkedDevices);
        });
      })
    },

    async fetchData() {
      const params = {
        profile: this.trainInfo.dir,
        train_id: this.trainInfo.id,
        stage_id: "metadata"     // first fetch metadata
      };
      const fetchFunc = async () => {
        const res = await (
          await requestService
            .getGraphData(params)
            .catch((err) => {
              throw err;
            })
        ).data;
        if (res.status === "loading" || res.status === "pending") {
          setTimeout(fetchFunc, 1500);
          return;
        } else {
          // get the whole graph data
          const metadata = res.data;
          const graphs = {};

          for (var stage_id in Object.keys(res.data.stage_devices)) {
            params['stage_id'] = stage_id;
            let cur_stage_data = await (
              await requestService.getGraphData(params).catch((err) => {
              throw err;
            })).data.data;
            graphs[i] = cur_stage_data;
          }
          $store.commit("setGraphData", {
            "graphs": graphs,
            "metadata": metadata,
            "status": "finish"
          });
        }
      };
      await fetchFunc();
      this.profileIsLoading = false;
    },
    handleSwitchChange(value) {
      this.isShowHiddenEdges = value;
    },
  },
};
</script>

<style scoped>
.overview-dashboard {
  display: grid;
  grid-template-rows: calc(35% - 10px) calc(35% - 10px) calc(30% - 20px);
  grid-template-columns: 100%;
  height: 100%;
  row-gap: 20px;
}
.overview-dashboard .container {
  width: 100%;
  height: 100%;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 15px;
  position: relative;
}
.overview-dashboard .header {
  width: 100%;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.title {
  font-size: 16px;
  font-weight: bold;
}

.strategy-content {
  width: 100%;
  height: calc(100% - 24px);
  display: flex;
  flex-direction: row-reverse;
}

.marey-content {
  width: 100%;
  height: calc(100% - 24px);
}
.strategy-loading {
  width: 100%;
  height: calc(100% - 24px);
}
.line-content {
  width: 100%;
  height: calc(100% - 24px);
}

.strategy-content .left {
  width: 400px;
}
.strategy-content .right {
  width: calc(100% - 400px);
}
.timeview-content {
  width: 100%;
  height: calc(100% - 24px);
}
.brush-switch {
  position: absolute;
  top: 16px;
  right: 16px;
  display: flex;
  line-height: 20px;
}
.brush-switch div {
  margin-left: 10px;
  margin-right: 4px;
}
.brush-switch svg {
  width: 16px;
  height: 16px;
  margin: 2px 0;
  cursor: pointer;
}
.button-with-margin {
  margin-left: 8px;
}
.tree-selector-scroll {
  max-height: 300px;
  overflow-y: auto;
}
</style>

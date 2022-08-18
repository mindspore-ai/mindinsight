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
  <div class="configuration-view-box">
    <div class="namescope-configure">
      <div class="configure-title">{{ $t("profilingCluster.namescope") }}</div>
      <div class="configure-content">
        <el-tree
          :data="showTreeData"
          show-checkbox
          node-key="key"
          default-expand-all
          ref="tree"
          @check="handleTreeChange"
        >
          <span class="custom-tree-node" slot-scope="{ node, data }">
            <svg
              viewBox="0 0 15 10"
              width="15"
              height="10"
              v-if="selectNamespaces.includes(data.key)"
            >
              <rect
                x="0"
                y="0"
                width="15"
                height="10"
                rx="3"
                ry="3"
                :fill="haloColorScale(data.key)"
              ></rect>
            </svg>
            <span>{{ data.titleText }}</span>
          </span>
        </el-tree>
      </div>
    </div>
  </div>
</template>

<script>
import $store from "../store";
import * as d3 from "d3";
import { getTreeData, levelOrder } from "@/js/profile-graph/build-graph.js";
export default {
  data() {
    return {
      specialEdgeTypes: [],
      showSpecialEdgeTypes: [],
      nameScopeFromMarey: [],

      graphData: {},
      showTreeData: [],
      selectNamespaces: [],
    };
  },
  watch: {
    storeProfileSpecialEdgeTypes(val) {
      this.specialEdgeTypes = val;
    },
    showSpecialEdgeTypes(newVal, oldVal) {
      $store.commit("setProfileShowSpecialEdgeTypes", [oldVal, newVal]);
    },
    storeGraphData(val) {
      this.graphData = val;
      this.initView();
    },
    "$store.state.nameScopeToParallelStrategy": function (val) {
      this.selectNewScopeFromMarey(val);
    },
  },
  computed: {
    storeProfileSpecialEdgeTypes() {
      return $store.state.profileSpecialEdgeTypes;
    },
    storeGraphData() {
      return $store.state.graphData;
    },
  },
  methods: {
    selectNewScopeFromMarey(val) {
      const { nameScope, opName, stage } = val;
      let depth = 0;
      const data = this.showTreeData;
      let curData = data;
      const nameScopeArr = nameScope.split("/");
      const chosedOps = new Set(opName);
      let chosedKey = [];
      while (curData.length) {
        if (depth >= nameScopeArr.length) {
          if (curData.length === chosedOps.size) {
            chosedKey.push(curData.key);
          } else {
            curData.forEach((child) => {
              if (chosedOps.has(child.titleText)) {
                chosedKey.push(child.key);
              }
            });
          }
          break;
        } else if (depth === 0) {
          // stage
          curData = curData.find((d) => d.titleText === stage[0]);
        } else {
          curData = curData.find((d) => d.titleText === nameScopeArr[depth]);
        }

        if (curData.key) chosedKey = [curData.key];
        curData = curData.children;
        depth++;
      }

      this.$refs.tree.setCheckedKeys(chosedKey);

      this.handleTreeChange(null, {
        checkedKeys: chosedKey,
      });
    },
    haloColorScale: d3.scaleOrdinal(d3.schemeAccent),
    initView() {
      this.fetchData();
    },
    fetchData() {
      const res = this.graphData;
      if ("graphs" in res) {
        levelOrder(getTreeData());
      }
      this.treeData = getTreeData().children;
      $store.commit("setProfileTreeData", this.treeData);
      this.showTreeData = JSON.parse(JSON.stringify(this.treeData));
      for (const child of this.showTreeData) {
        child.scopedSlots = { title: "title" };
        child.titleText = child.title;
        child.title = null;
        this.modifyTreeData(child);
      }
    },
    modifyTreeData(node) {
      if (!node) return;
      const newChildren = [];
      for (const child of node.children) {
        if (child.children.length !== 0) {
          newChildren.push(child);
        }
      }
      node.children = newChildren;
      for (const child of node.children) {
        child.scopedSlots = { title: "title" };
        child.titleText = child.title;
        child.title = null;
        this.modifyTreeData(child);
      }
    },
    handleTreeChange(data, checkedData) {
      const filterRes = [];
      checkedData.checkedKeys.forEach((key) => {
        const keyList = key.split("-");
        keyList.length = keyList.length - 1;
        const father = keyList.join("-");
        if (!checkedData.checkedKeys.includes(father)) {
          filterRes.push(key);
        }
      });
      this.selectNamespaces = filterRes;
      $store.commit("setProfileNamespaces", this.selectNamespaces);
    },
  },
};
</script>

<style scoped>
.configuration-view-box {
  width: 100%;
  height: 100%;
}
.namescope-configure {
  width: 100%;
  height: 100%;
}
.configure-title {
  width: 100%;
  font-size: 16px;
  height: 20px;
}
.configure-content {
  max-height: calc(100% - 20px);
  width: 100%;
  overflow-y: scroll;
}
</style>

<!--
Copyright 2020-2021 Huawei Technologies Co., Ltd.All Rights Reserved.

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
  <div class="el-tree"
       :class="{
      'el-tree--highlight-current': highlightCurrent,
      'is-dragging': !!dragState.draggingNode,
      'is-drop-not-allow': !dragState.allowDrop,
      'is-drop-inner': dragState.dropType === 'inner'
    }"
       role="tree">
    <el-tree-node v-for="child in root.childNodes"
                  :node="child"
                  :props="props"
                  :render-after-expand="renderAfterExpand"
                  :show-checkbox="showCheckbox"
                  :disabled="disabled"
                  :key="getNodeKey(child)"
                  :render-content="renderContent"
                  @node-expand="handleNodeExpand">
    </el-tree-node>
    <div class="el-tree__empty-block"
         v-if="isEmpty">
      <span class="el-tree__empty-text">{{ emptyText }}</span>
    </div>
    <div v-show="dragState.showDropIndicator"
         class="el-tree__drop-indicator"
         ref="dropIndicator">
    </div>
  </div>
</template>
<script>
import {Tree} from 'element-ui';
import ElTreeNode from './tree-node';
export default {
  extends: Tree,
  components: {
    ElTreeNode,
  },
  props: {
    disabled: {
      type: Boolean,
      default: false,
    },
  },
};
</script>

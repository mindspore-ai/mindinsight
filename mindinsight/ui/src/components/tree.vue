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
                  :show-checkbox="showCheckbox && child.data.showCheckbox"
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
};
</script>

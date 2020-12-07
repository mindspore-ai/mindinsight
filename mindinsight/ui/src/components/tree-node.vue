<template>
  <div class="el-tree-node"
       @click.stop="handleClick"
       @contextmenu="($event) => this.handleContextMenu($event)"
       v-show="node.visible"
       :class="{
      'is-expanded': expanded,
      'is-current': node.isCurrent,
      'is-hidden': !node.visible,
      'is-focusable': !node.disabled,
      'is-checked': !node.disabled && node.checked
    }"
       role="treeitem"
       tabindex="-1"
       :aria-expanded="expanded"
       :aria-disabled="node.disabled"
       :aria-checked="node.checked"
       :draggable="tree.draggable"
       @dragstart.stop="handleDragStart"
       @dragover.stop="handleDragOver"
       @dragend.stop="handleDragEnd"
       @drop.stop="handleDrop"
       ref="node">
    <div class="el-tree-node__content"
         :style="{ 'padding-left': (node.level - 1) * tree.indent + 'px' }">
      <span @click.stop="handleExpandIconClick"
            :class="[
          { 'is-leaf': node.isLeaf, expanded: !node.isLeaf && expanded },
          'el-tree-node__expand-icon',
          tree.iconClass ? tree.iconClass : 'el-icon-caret-right'
        ]">
      </span>
      <el-checkbox v-if="showCheckbox && node.data.showCheckbox"
                   v-model="node.checked"
                   :indeterminate="node.indeterminate"
                   :disabled="disabled || !!node.disabled"
                   @click.native.stop
                   @change="handleCheckChange">
      </el-checkbox>
      <span v-if="node.loading"
            class="el-tree-node__loading-icon el-icon-loading">
      </span>
      <node-content :node="node"></node-content>
    </div>
    <el-collapse-transition>
      <div class="el-tree-node__children"
           v-if="!renderAfterExpand || childNodeRendered"
           v-show="expanded"
           role="group"
           :aria-expanded="expanded">
        <el-tree-node :render-content="renderContent"
                      v-for="child in node.childNodes"
                      :render-after-expand="renderAfterExpand"
                      :show-checkbox="showCheckbox"
                      :disabled="disabled"
                      :key="getNodeKey(child)"
                      :node="child"
                      @node-expand="handleChildNodeExpand">
        </el-tree-node>
      </div>
    </el-collapse-transition>
  </div>
</template>
<script>
import ElTreeNode from 'element-ui/packages/tree/src/tree-node';
export default {
  extends: ElTreeNode,
  name: 'ElTreeNode',
  componentName: 'ElTreeNode',
  props: {
    disabled: {
      type: Boolean,
      default: false,
    },
  },
};
</script>

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
  <g
    :opacity="1"
    @mouseenter="mouseenterListener"
    @mouseleave="mouseleaveListener"
    v-if="!expanded"
  >
    <template v-if="type === nodeType.aggregate_scope">
      <g
        @dblclick="emitDblClickOperatorNode($event)"
        @mouseenter="emitMouseEnterOperatorNode($event)"
        @mouseleave="emitMouseLeaveOperatorNode($event)"
      >
        <ellipse
          :transform="`translate(${x + 20}, ${y + height / 2 + 8})`"
          class="graph-common"
          :class="{
            'graph-stroke-click': click,
            'graph-stroke-hover': hover,
            'graph-stroke-search': selected,
            'graph-stroke-focused': focused,
          }"
          :style="{
            fill: fill,
            transition: '0.2s',
          }"
          rx="20"
          ry="8"
        >
        </ellipse>
        <ellipse
          :transform="`translate(${x + 20}, ${y + height / 2 + 4})`"
          class="graph-common"
          :class="{
            'graph-stroke-click': click,
            'graph-stroke-hover': hover,
            'graph-stroke-search': selected,
            'graph-stroke-focused': focused,
          }"
          :style="{
            fill: fill,
            transition: '0.2s',
          }"
          rx="20"
          ry="8"
        >
        </ellipse>
        <ellipse
          :transform="`translate(${x + 20}, ${y + height / 2})`"
          class="graph-common"
          :class="{
            'graph-stroke-click': click,
            'graph-stroke-hover': hover,
            'graph-stroke-search': selected,
            'graph-stroke-focused': focused,
          }"
          :style="{
            fill: fill,
            transition: '0.2s',
          }"
          rx="20"
          ry="8"
        >
        </ellipse>
        <foreignObject
          width="40"
          height="16"
          :x="x"
          :y="y"
          style="transition: '0.2s'"
        >
          <div class="graph-scope-label graph-operator-label">
            {{ stackedCount }}
          </div>
        </foreignObject>
      </g>
    </template>

    <!-- Single operator -->
    <template v-else>
      <ellipse
        :transform="`translate(${x + 20}, ${y + height / 2})`"
        class="graph-common"
        :class="{
          'graph-stroke-click': click,
          'graph-stroke-hover': hover,
          'graph-stroke-search': selected,
          'graph-stroke-focused': focused,
        }"
        :style="{
          fill: fill,
          transition: '0.2s',
        }"
        rx="20"
        ry="8"
      >
      </ellipse>
    </template>

    <foreignObject
      width="120"
      height="16"
      :x="x - 40"
      :y="y + height / 2 - 21"
      style="transition: '0.2s'"
    >
      <div class="graph-scope-label graph-operator-label" :title="label">
        {{ labelToShow }}
      </div>
    </foreignObject>

    <g
      :transform="`translate(${x + HALF_SIDE_PADDING}, ${y + 3})`"
      class="model-parallel"
      v-if="rects"
    >
      <rect
        v-for="i in rects"
        :key="i"
        :transform="`translate(${(i - 1) * (rectWidth + PADDING)},0)`"
        :width="rectWidth"
        :height="height - 6"
        fill="#a47b73"
      />
    </g>
  </g>
</template>

<script>
import graphNodeMixin from './graph-node-mixin';
import {NODE_TYPE} from '../../../../js/const';

const SIDE_PADDING = 12;
const PADDING = 1;

export default {
  mixins: [graphNodeMixin],
  props: {
    stackedCount: Number,
    outline: [String, Number],
    rects: Number,
  },
  data: function() {
    return {
      nodeType: NODE_TYPE,
      HALF_SIDE_PADDING: SIDE_PADDING / 2,
      PADDING,
      labelToShow: '',
    };
  },
  mounted() {
    const rawStr = this.label;
    const showStrLength = 16;
    this.labelToShow =
      rawStr.length > showStrLength
        ? rawStr.slice(0, showStrLength - 2) + '...'
        : rawStr;
  },
  methods: {
    emitDblClickOperatorNode(event) {
      this.$emit('dblclickoperatornode', event, {id: this.id});
    },

    emitMouseEnterOperatorNode(event) {
      this.$emit('mouseenteroperatornode', event, {id: this.id});
    },

    emitMouseLeaveOperatorNode(event) {
      this.$emit('mouseleaveoperatornode', event, {id: this.id});
    },
  },
  computed: {
    rectWidth() {
      if (this.rects) {
        return (
          (this.width - SIDE_PADDING - (this.rects - 1) * PADDING) / this.rects
        );
      }

      return 0;
    },
  },
};
</script>

<style scoped>
.data-parallel-info circle {
  fill: #fff;
}

.data-parallel-info rect {
  filter: none;
  fill: #fff;
  stroke: #5294c2;
}
.data-parallel-info text {
  font-size: 14px;
  transform: scale(0.7);
  user-select: none;
}

.model-parallel rect {
  filter: none;
}
</style>

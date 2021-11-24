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
    :opacity="opacity"
    @mouseenter="mouseenterListener"
    @mouseleave="mouseleaveListener"
    @dblclick="emitDBClickScopeNode($event)"
  >
    <rect
      rx="5"
      ry="5"
      :width="width"
      :height="height"
      :x="x"
      :y="y"
      class="graph-common"
      :class="{
        'graph-stroke-click': click,
        'graph-stroke-hover': hover,
        'graph-stroke-search': selected,
        'graph-stroke-focused': focused,
      }"
      :style="{
        fill: fill,
        transition: '0.2s'
      }"
    />
    <rect
      v-if="type === 'computation'"
      :width="width - PADDING"
      :height="height"
      :x="x + PADDING / 2"
      :y="y"
      class="graph-common"
      :class="{
        'graph-stroke-click': click,
        'graph-stroke-hover': hover,
        'graph-stroke-search': selected,
        'graph-stroke-focused': focused,
      }"
      :style="{
        fill: fill,
        pointerEvents: 'none',
        transition: '0.2s'
      }"
    />
    <foreignObject
      :width="width"
      height="16"
      :x="x"
      :y="y"
      style="transition: '0.2s'"
    >
      <div class="graph-scope-label" :title="label">
        {{ labelToShow }}
      </div>
    </foreignObject>
    <foreignObject
      :width="width"
      height="16"
      :x="x"
      :y="y + height - 16"
      style="transition: '0.2s'"
      v-if="!expanded"
    >
      <div class="graph-scope-label">
        <svg v-if="specialNodesCnt.hasOwnProperty('hasStrategy')"  width="8" height="8">
          <g>
            <rect width="8" height="8" rx="3" fill="rgb(0,0,0)"/>
          </g>
        </svg>
        <svg v-if="specialNodesCnt.hasOwnProperty('hasStrategy')"  width="21" height="8">
          <g>
            <text dx="0" dy="7" font-size="8">{{`:${specialNodesCnt["hasStrategy"] | 0}`}}</text>
          </g>
        </svg>

        <svg v-if="specialNodesCnt.hasOwnProperty('Redistribution')"  width="8" height="8">
          <g>
            <rect width="8" height="8" rx="3" fill="rgb(209,229,209)"/>
          </g>
        </svg>
        <svg v-if="specialNodesCnt.hasOwnProperty('Redistribution')"  width="21" height="8">
          <g>
            <text dx="0" dy="7" font-size="8">{{`:${specialNodesCnt["Redistribution"] | 0}`}}</text>
          </g>
        </svg>

        <svg v-if="specialNodesCnt.hasOwnProperty('GradientAggregation')"  width="8" height="8">
          <g>
            <rect width="8" height="8" rx="3" fill="rgb(245,194,140)"/>
          </g>
        </svg>
        <svg v-if="specialNodesCnt.hasOwnProperty('GradientAggregation')"  width="21" height="8">
          <g>
            <text dx="0" dy="7" font-size="8">{{`:${specialNodesCnt["GradientAggregation"] | 0}`}}</text>
          </g>
        </svg>
      </div>
    </foreignObject>
  </g>
</template>

<script>
import graphNodeMixin from './graph-node-mixin';

export default {
  mixins: [graphNodeMixin],
  data() {
    return {
      PADDING: 15,
      labelToShow: '',
    };
  },
  mounted() {
    this.adjustLabelWidth();
  },
  updated() {
    this.adjustLabelWidth();
  },
  methods: {
    adjustLabelWidth() {
      const rawStr = this.label;
      const maxWidthCapacity = parseInt(this.width / 8);
      this.labelToShow =
      rawStr.length > maxWidthCapacity
        ? rawStr.slice(0, maxWidthCapacity - 2) + '...'
        : rawStr;
    },
    emitDBClickScopeNode(event) {
      this.$emit('dblscopenode', event, {id: this.id});
    },
  },
};
</script>

<style scoped>
.graph-scope-label {
  font-size: 14px;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  user-select: none;
  padding: 0 4px;
}

.graph-common {
  stroke: var(--common-stroke);
  stroke-width: 1;
}
.graph-stroke-hover {
  stroke: #fd9629;
  stroke-width: 2;
}
.graph-marker-hover {
  stroke: #fd9629;
  fill: #fd9629;
}
.graph-stroke-click {
  stroke: #ff0000;
  stroke-width: 2;
}
.graph-stroke-search {
  stroke: #bd39c2;
  stroke-width: 2;
}
.graph-marker-search {
  stroke: #bd39c2;
  fill: #bd39c2;
}
.graph-stroke-focused {
  stroke: red;
  stroke-width: 2;
}
</style>

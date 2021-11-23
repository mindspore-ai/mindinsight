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
  <g :class="parentClass" class="no-fill" :opacity="edgeOpacity">
    <g v-for="edge in edges" :key="edge.id" :class="edge.outline ? 'outline' : ''">
      <polyline :points="edge.points" :marker-end="`url(#${markerEndId})`" :opacity="1" />
    </g>
  </g>
</template>

<script>

export default {
  props: {
    parentClass: String,
    edges: Array,
    markerEndId: String,
    edgeOpacity: {
      type: Number,
      default: 1,
    },
  },
};
</script>

<style scoped>
.graph-stroke-search {
  stroke: var(--search-graph-color);
  stroke-width: var(--active-stroke-width);
}

.graph-stroke-hover {
  stroke: var(--highlight-node-stroke-color);
  stroke-width: var(--active-stroke-width);
}

.no-fill {
  fill: none;
  --common-stroke-color: var(--common-stroke);
}
</style>

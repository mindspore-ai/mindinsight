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
  <div class="svg-element-container"
       @mousedown="ableDraggable"
       @mouseup="disableDraggable"
       @mouseleave="disableDraggable"
       @mousemove="dragHandler"
       @mousewheel="zoomHandler">
    <svg ref="show-graph-area">
      <defs>
        <slot name="marker"></slot>
      </defs>
      <svg ref="whole-compute-graph">
        <g :transform="`translate(${this.x}, ${this.y}) scale(${this.scale})`">
          <slot name="g"></slot>
        </g>
      </svg>
    </svg>
  </div>
</template>

<script>
export default {
  props: {
    zoom: {
      type: Boolean,
      default: true,
    },
    zoomFactor: {
      type: Number,
      default: 0.1,
    },
    zoomRange: {
      type: Array,
      default: () => {
        return [0.1, 10];
      },
    },
    drag: {
      type: Boolean,
      default: true,
    },
  },
  data() {
    return {
      x: 200,
      y: 200,
      scale: 1, // The zoom scale of svg
      originalX: null,
      originalY: null,
      draggable: false, // If the svg draggable
      emitTimer: null,

      showGraphAreaWidth: 0,
      showGraphAreaHeight: 0,
      wholeGraphWidth: 0,
      wholeGraphHeight: 0,

    };
  },
  mounted() {
    this.$emit('mounted');
    this.showGraphAreaWidth = this.$refs['show-graph-area'].getBoundingClientRect().width;
    this.showGraphAreaHeight = this.$refs['show-graph-area'].getBoundingClientRect().height;
  },
  methods: {
    reset() {
      this.wholeGraphWidth = this.$refs['whole-compute-graph'].getBoundingClientRect().width / this.scale;
      this.wholeGraphHeight = this.$refs['whole-compute-graph'].getBoundingClientRect().height / this.scale;
      this.x = this.showGraphAreaWidth / 2 - this.wholeGraphWidth / 2;
      this.y = this.showGraphAreaHeight / 2 - this.wholeGraphHeight / 2;
      this.scale = 1;
      this.originalX = this.originalY = null;
    },
    center() {},
    move(x, y) {
      this.x += x;
      this.y += y;
    },
    moveTo(x, y) {
      this.x = x;
      this.y = y;
    },
    zoomHandler(event) {
      if (!this.zoom) return;
      const {offsetX, offsetY} = event;
      const zoomX = offsetX - this.x;
      const zoomY = offsetY - this.y;
      if (event.deltaY < 0) {
        // zoom in
        if (this.scale === this.zoomRange[1]) return;
        let nextScale = this.scale * (1 + this.zoomFactor);
        if (nextScale > this.zoomRange[1]) {
          nextScale = this.zoomRange[1];
          const factor = (nextScale - this.scale) / this.scale;
          this.x -= zoomX * factor;
          this.y -= zoomY * factor;
          this.scale = nextScale;
        } else {
          this.x -= zoomX * this.zoomFactor;
          this.y -= zoomY * this.zoomFactor;
          this.scale = nextScale;
        }
      } else {
        // zoom out
        if (this.scale === this.zoomRange[0]) return;
        let nextScale = this.scale * (1 - this.zoomFactor);
        if (nextScale < this.zoomRange[0]) {
          nextScale = this.zoomRange[0];
          const factor = (this.scale - nextScale) / this.scale;
          this.x += zoomX * factor;
          this.y += zoomY * factor;
          this.scale = nextScale;
        } else {
          this.x += zoomX * this.zoomFactor;
          this.y += zoomY * this.zoomFactor;
          this.scale = nextScale;
        }
      }
      this.emitZooming();
    },
    ableDraggable(event) {
      if (!this.drag) return;
      this.originalX = event.screenX;
      this.originalY = event.screenY;
      this.draggable = true;
    },
    disableDraggable() {
      if (!this.drag) return;
      this.draggable = false;
    },
    dragHandler(event) {
      if (!this.drag || !this.draggable) return;
      this.x += event.screenX - this.originalX;
      this.y += event.screenY - this.originalY;
      this.originalX = event.screenX;
      this.originalY = event.screenY;
      this.emitZooming();
    },
    emitZooming() {
      if (this.emitTimer) clearTimeout(this.emitTimer);
      const zoomDelay = 200;
      this.emitTimer = setTimeout(() => {
        this.$bus.$emit('zooming');
      }, zoomDelay);
    },
  },
};
</script>

<style scoped>
.svg-element-container {
  height: 100%;
}
.svg-element-container svg {
  height: 100%;
  width: 100%;
}
</style>

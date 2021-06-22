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
  <div class="cl-superpose-image"
       :style="{'height': `${containerSize}px`,'width': `${containerSize}px`}">
    <img :src="backgroundImg"
         class="second-level"
         v-show="ifSuperpose"
         v-if="backgroundReady"
         @error="backgroundError()"
         :style="{'position': 'absolute', 'top':`${backTop}px`,'left':`${backLeft}px`,
                  'height': `${imageHeight}px`, 'width':`${imageWidth}px`}">
    <img v-if="targetReady"
         :src="targetImg"
         :style="{'position': 'absolute', 'top': `${targetTop}px`, 'left':`${targetLeft}px`,
                'height': `${imageHeight}px`, 'width':`${imageWidth}px`}"
         class="first-level"
         :class="!ifSuperpose?'overlay-background':''"
         @error="targetError()">
  </div>
</template>
<script>
export default {
  props: [
    'backgroundImg', // The background at the second level
    'targetImg', // The target image at the first level
    'ifSuperpose', // If show the canvas of background
    'containerSize', // The width and height of container
  ],
  data() {
    return {
      targetReady: true, // The state of target image
      backgroundReady: true, // The state of background image
      targetTop: 0, // top of target
      targetLeft: 0, // left of target
      imageHeight: 0, // height of image
      imageWidth: 0, // width of image
      backTop: 0, // top of background
      backLeft: 0, // left of background
    };
  },
  created() {
    this.calImageSize();
  },
  methods: {
    /**
     * The logic of cal image size
     */
    calImageSize() {
      const backgroundTemp = new Image();
      backgroundTemp.src = this.backgroundImg;
      backgroundTemp.onload = () => {
        if (backgroundTemp.width > backgroundTemp.height) {
          this.imageWidth = this.containerSize;
          this.imageHeight = this.containerSize * (backgroundTemp.height / backgroundTemp.width);
          this.backTop = this.containerSize / 2 - this.imageHeight / 2;
          this.targetTop = this.backTop;
        } else if (backgroundTemp.width < backgroundTemp.height) {
          this.imageHeight = this.containerSize;
          this.imageWidth = this.containerSize * (backgroundTemp.width / backgroundTemp.height);
          this.backLeft = this.containerSize / 2 - this.imageWidth / 2;
          this.targetLeft = this.backLeft;
        } else {
          this.imageWidth = this.containerSize;
          this.imageHeight = this.containerSize;
        }
      };
    },
    /**
     * The logic that is executed when target image loading failed
     */
    targetError() {
      this.targetReady = false;
    },
    /**
     * The logic that is executed when background image loading failed
     */
    backgroundError() {
      this.backgroundReady = false;
    },
  },
};
</script>
<style scoped>
.cl-superpose-image {
  position: relative;
  overflow: hidden;
}
.cl-superpose-image .overlay-background {
  background: #371956;
}
</style>

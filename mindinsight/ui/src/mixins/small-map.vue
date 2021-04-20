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
<script>
import CommonProperty from '@/common/common-property.js';
export default {
  data() {
    return {
      smallContainer: {},
      smallMap: {}, // The container of display area box.
      insideBox: {
        width: 0,
        height: 0,
        left: 0,
        top: 0,
      }, // Basic information about the display area box

      // Which mouse button is triggered when the thumbnail is clicked. -1 indicates that no click event is triggered,
      // 0 indicates the left key, 1 indicates the middle key, and 2 means right key.
      clickSmall: false,
      smallMapEventTimer: null,
      eventDelay: 200,
    };
  },

  methods: {
    initSmallMap() {
      this.initSmallContainer();
      this.drawCanvas();
      this.initGraphRectData();
      this.setSmallMapEvents();
    },
    /**
     * Initialize the small image container
     */
    initSmallContainer() {
      const svgRect = document.querySelector('#graph svg').getBoundingClientRect();
      this.svg.size = {width: svgRect.width, height: svgRect.height, left: svgRect.left, top: svgRect.top};
      this.graph.dom = document.querySelector('#graph #graph0');
      const graphBox = this.graph.dom.getBBox();
      this.graph.size = {width: graphBox.width, height: graphBox.height};
      // Attributes of smallContainer
      const smallContainer = document.querySelector('#small-container');
      const containerRect = smallContainer.getBoundingClientRect();
      const borderWidth = 1;
      this.smallContainer = {
        left: containerRect.left + borderWidth,
        top: containerRect.top + borderWidth,
        height: containerRect.height - borderWidth * 2,
        width: containerRect.width - borderWidth * 2,
      };

      // Initial width of the thumbnail frame
      this.smallMap.width = this.smallContainer.width;
      // The initial height of the thumbnail frame is high.
      this.smallMap.height = this.smallContainer.height;
      this.smallMap.left = this.smallMap.top = 0;
      if (Object.keys(this.allGraphData).length) {
        if (this.graph.size.width / this.graph.size.height < this.smallContainer.width / this.smallContainer.height) {
          this.smallMap.width = (this.smallContainer.height * this.graph.size.width) / this.graph.size.height;
          this.smallMap.left = (this.smallContainer.width - this.smallMap.width) / 2;
        } else {
          this.smallMap.height = (this.smallContainer.width * this.graph.size.height) / this.graph.size.width;
          this.smallMap.top = (this.smallContainer.height - this.smallMap.height) / 2;
        }
      }
    },
    /**
     * Draw canvas image with svg
     */
    drawCanvas() {
      const svgDom = document.querySelector('#graph svg').cloneNode(true);
      const style = document.createElement('style');
      svgDom.append(style);
      style.outerHTML = CommonProperty.graphDownloadStyle;

      svgDom.setAttribute('width', this.graph.size.width);
      svgDom.setAttribute('height', this.graph.size.height);
      const transform = `translate(${this.graph.defaultPadding},${
        this.graph.size.height - this.graph.defaultPadding
      }) scale(1)`;
      svgDom.querySelector('g').setAttribute('transform', transform);

      const svgXml = new XMLSerializer().serializeToString(svgDom);
      const svg = new Blob([svgXml], {type: 'image/svg+xml;charset=utf-8'});

      const domUrl = self.URL || self;
      const url = domUrl.createObjectURL(svg);

      const image = new Image();
      image.onload = () => {
        const canvas = this.$refs.canvas;
        const context = canvas.getContext('2d');
        context.clearRect(0, 0, this.smallContainer.width, this.smallContainer.height);
        context.drawImage(
            image,
            0,
            0,
            this.graph.size.width,
            this.graph.size.height,
            this.smallMap.left,
            this.smallMap.top,
            this.smallMap.width,
            this.smallMap.height,
        );
      };
      image.src = url;
    },
    /**
     * Initialize the svg, width and height of the small image, and transform information.
     */
    initGraphRectData() {
      if (!this.graph.dom) {
        this.insideBox.width = this.smallMap.width;
        this.insideBox.height = this.smallMap.height;
        this.insideBox.top = this.insideBox.left = 0;
        this.insideBox.style.cursor = 'not-allowed';
      } else {
        const transform = this.getTransformData(this.graph.dom);

        this.graph.transform = {
          k: parseFloat(transform.scale[0]),
          x: parseFloat(transform.translate[0]),
          y: parseFloat(transform.translate[1]),
        };

        this.graph.minScale = Math.min(
            this.svg.size.width / 2 / this.graph.size.width,
            this.svg.size.height / 2 / this.graph.size.height,
        );

        this.setInsideBoxData();
      }
    },
    /**
     * Initialize all events of the small image
     */
    setSmallMapEvents() {
      // Attributes of smallContainer
      const smallContainer = document.querySelector('#small-container');

      if (this.graph.dom) {
        smallContainer.onmousedown = (e) => {
          this.clickSmall = true;
          this.insideBoxPositionChange(e);
        };

        smallContainer.onmouseup = () => (this.clickSmall = false);
        smallContainer.onmouseleave = () => (this.clickSmall = false);

        smallContainer.onmousemove = (e) => {
          if (!this.clickSmall) return;
          this.insideBoxPositionChange(e);
        };

        // Mouse wheel event
        smallContainer.onwheel = (e) => {
          e = e || window.event;
          const wheelDelta = e.wheelDelta ? e.wheelDelta : -e.deltaY;
          if (!isNaN(this.graph.transform.k) && this.graph.transform.k !== 0) {
            const rate = wheelDelta > 0 ? 1.2 : 1 / 1.2;

            const scaleTemp = this.graph.transform.k / rate;
            if (scaleTemp < this.graph.minScale || scaleTemp < this.scaleRange[0] || scaleTemp > this.scaleRange[1]) {
              return;
            }

            this.graph.transform.k = scaleTemp;
            this.insideBox.scale = 1 / scaleTemp;
            this.insideBox.left += (this.insideBox.width * (1 - rate)) / 2;
            this.insideBox.top += (this.insideBox.height * (1 - rate)) / 2;
            this.insideBox.height = this.insideBox.height * rate;
            this.insideBox.width = this.insideBox.width * rate;

            this.graphChange();
          }
        };
      } else {
        document.onmouseup = null;
        smallContainer.onmousemove = null;
        smallContainer.onmousedown = null;
        smallContainer.onmousewheel = null;
      }
    },
    /**
     * Small image moving
     * @param {Object} e Event object
     */
    insideBoxPositionChange(e) {
      this.insideBox.left = e.x - this.smallContainer.left - parseFloat(this.insideBox.width) / 2;
      this.insideBox.top = e.y - this.smallContainer.top - parseFloat(this.insideBox.height) / 2;

      if (this.smallMapEventTimer) clearTimeout(this.smallMapEventTimer);
      this.smallMapEventTimer = setTimeout(this.graphChange, this.eventDelay);
    },
    /**
     * Displacement of the large picture when the small picture is changed
     */
    graphChange() {
      if (!this.graph.transform.x || isNaN(this.graph.transform.x)) {
        this.initSmallMap();
      }

      const transRate = this.smallMap.width / (this.graph.size.width * this.graph.transform.k);
      this.graph.transform.x =
        -(this.insideBox.left - this.smallMap.left) / transRate + this.graph.defaultPadding * this.graph.transform.k;
      this.graph.transform.y =
        -(this.insideBox.top - this.smallMap.top) / transRate +
        (this.graph.size.height - this.graph.defaultPadding) * this.graph.transform.k;

      this.graph.dom.setAttribute(
          'transform',
          `translate(${this.graph.transform.x},${this.graph.transform.y}) scale(${this.graph.transform.k})`,
      );
    },
    /**
     * Displacement of the small map when the large picture is changed
     */
    setInsideBoxData() {
      const rate = this.smallMap.width / (this.graph.size.width * this.graph.transform.k);
      this.insideBox.left =
        this.smallMap.left - (this.graph.transform.x - this.graph.defaultPadding * this.graph.transform.k) * rate;
      this.insideBox.top =
        this.smallMap.top -
        (this.graph.transform.y +
          this.graph.defaultPadding * this.graph.transform.k -
          this.graph.size.height * this.graph.transform.k) *
          rate;

      this.insideBox.width = this.svg.size.width * rate;
      this.insideBox.height = this.svg.size.height * rate;
    },
    /**
     * Setting the width and height of a node
     * @param {Object} domData Data of dom
     * @return {Object}
     */
    styleSet(domData) {
      const keys = ['width', 'height', 'left', 'top'];
      const styleObj = {};
      for (const key of keys) {
        styleObj[key] = domData[key] + 'px';
      }
      return styleObj;
    },
  },
  destroyed() {
    document.onmouseup = null;
    const smallContainer = document.querySelector('#small-container');
    if (smallContainer) {
      smallContainer.onmousemove = null;
      smallContainer.onmousedown = null;
      smallContainer.onmousewheel = null;
    }
  },
};
</script>

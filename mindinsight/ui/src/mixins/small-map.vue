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
export default {
  data() {
    return {
      smallResize: {}, // The container of display area box.
      insideBox: {}, // Basic information about the display area box
      eventSmall: {}, // Relative position of the thumbnail in the thumbnail click event

      // Which mouse button is triggered when the thumbnail is clicked. -1 indicates that no click event is triggered,
      // 0 indicates the left key, 1 indicates the middle key, and 2 means right key.
      clickSmall: false,
    };
  },

  methods: {
    /**
     * Initialize the svg, width and height of the small image, and transform information.
     */
    initGraphRectData() {
      this.initSmallContainer();

      if (!this.graph.dom) {
        this.insideBox.width = this.smallResize.width;
        this.insideBox.height = this.smallResize.height;
        this.insideBox.top = this.insideBox.left = 0;
        this.styleSet('#inside-box', this.insideBox);
        this.insideBox.style.cursor = 'not-allowed';
      } else {
        let transformString = '';
        const transTemp = this.graph.dom.attributes.transform || null;
        if (transTemp) {
          // transform information of graph
          transformString = transTemp.nodeValue.split(/[(,)]/);
        } else {
          transformString = ['translate', '0', '0', ' scale', '1'];
        }
        this.graph.transform = {
          k: parseFloat(transformString[4]),
          x: parseFloat(transformString[1]),
          y: parseFloat(transformString[2]),
        };

        const graphRect = this.graph.dom.getBoundingClientRect();
        this.graph.transRate =
          graphRect.width /
          this.graph.dom.getBBox().width /
          this.graph.transform.k;
        this.graph.minScale =
          Math.min(
              this.svg.rect.width / 2 / graphRect.width,
              this.svg.rect.height / 2 / graphRect.height,
          ) * this.graph.transform.k;

        this.setInsideBoxData();
      }
      this.setSmallMapEvents();
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

        document.onmouseup = (e) => {
          this.clickSmall = false;
        };

        smallContainer.onmousemove = (e) => {
          if (this.clickSmall) {
            this.insideBoxPositionChange(e);
          }
        };

        // Mouse wheel event
        smallContainer.onwheel = (e) => {
          e = e || window.event;
          const wheelDelta = e.wheelDelta ? e.wheelDelta : -e.deltaY;
          if (!isNaN(this.graph.transform.k) && this.graph.transform.k !== 0) {
            let rate = wheelDelta > 0 ? 1.2 : 1 / 1.2;

            let scaleTemp = this.graph.transform.k / rate;
            if (scaleTemp <= this.graph.minScale) {
              scaleTemp = this.graph.minScale;
              rate = this.graph.transform.k / this.graph.minScale;
            }

            this.graph.transform.k = Math.max(
                this.scaleRange[0],
                Math.min(scaleTemp, this.scaleRange[1]),
            );
            this.insideBox.scale = 1 / this.graph.transform.k;

            this.insideBox.left += (this.insideBox.width * (1 - rate)) / 2;
            this.insideBox.top += (this.insideBox.height * (1 - rate)) / 2;

            this.insideBox.height = this.insideBox.height * rate;
            this.insideBox.width = this.insideBox.width * rate;

            document
                .querySelector('#graph0')
                .setAttribute(
                    'transform',
                    `translate(${this.graph.transform.x},${this.graph.transform.y}) ` +
                  `scale(${this.graph.transform.k})`,
                );

            this.styleSet('#inside-box', this.insideBox);
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
     * Initialize the small image container
     */
    initSmallContainer() {
      this.graph.dom = document.querySelector('#graph #graph0');
      // Attributes of smallContainer
      const smallContainer = document.querySelector('#small-container');
      // Reset the length and width of the smallResize and locate the fault.
      const smallResize = document.querySelector('#small-resize');

      this.smallResize.width = this.smallResize.initWidth =
        smallContainer.offsetWidth - 2; // Initial width of the thumbnail frame
      this.smallResize.height = this.smallResize.initHeight =
        smallContainer.offsetHeight - 2; // The initial height of the thumbnail frame is high.
      this.smallResize.left = this.smallResize.top = 0;
      if (Object.keys(this.allGraphData).length) {
        if (
          this.svg.originSize.width / this.svg.originSize.height <
          this.smallResize.initWidth / this.smallResize.initHeight
        ) {
          this.smallResize.width =
            (this.smallResize.initHeight * this.svg.originSize.width) /
            this.svg.originSize.height;
          this.smallResize.left =
            (this.smallResize.initWidth - this.smallResize.width) / 2;
        } else {
          this.smallResize.height =
            (this.smallResize.initWidth * this.svg.originSize.height) /
            this.svg.originSize.width;
          this.smallResize.top =
            (this.smallResize.initHeight - this.smallResize.height) / 2;
        }
      }
      this.styleSet('#small-resize', this.smallResize);
      // Distance between the thumbnail frame and the upper part of the window
      this.smallResize.offsetLeft = smallResize.getBoundingClientRect().left;
      // Distance between the thumbnail frame and the upper part of the window
      this.smallResize.offsetTop = smallResize.getBoundingClientRect().top;

      // Attributes of smallMap
      const smallMap = document.querySelector('#small-map');
      const svgOuterHtml =
        `<svg xmlns="http://www.w3.org/2000/svg" ` +
        `xmlns:xlink="http://www.w3.org/1999/xlink" width="100%" height="100%" ` +
        `viewBox="0.00 0.00 ${this.svg.originSize.width} ${this.svg.originSize.height}"` +
        `><g id="smallGraph" class="graph" transform="translate(4,${
          this.svg.originSize.height - 4
        }) scale(1)"` +
        `>${this.graph.dom.innerHTML}</g></svg>`;

      smallMap.innerHTML = svgOuterHtml;
    },
    /**
     * Small image moving
     * @param {Object} e Event object
     */
    insideBoxPositionChange(e) {
      this.eventSmall.x = e.pageX - this.smallResize.offsetLeft;
      this.eventSmall.y = e.pageY - this.smallResize.offsetTop;

      this.insideBox.left =
        this.eventSmall.x - parseFloat(this.insideBox.width) / 2;
      this.insideBox.top =
        this.eventSmall.y - parseFloat(this.insideBox.height) / 2;

      this.styleSet('#inside-box', this.insideBox);
      this.graphChange();
    },
    /**
     * Displacement of the large picture when the small picture is changed
     */
    graphChange() {
      if (!this.graph.transform.x || isNaN(this.graph.transform.x)) {
        this.initGraphRectData();
      }
      const graphRect = this.graph.dom.getBoundingClientRect();

      const graphSizeRate = this.svg.rect.width / this.insideBox.width;

      const change = {
        x:
          (this.insideBox.left * graphSizeRate -
            (this.svg.rect.left - graphRect.left)) /
          this.graph.transRate,
        y:
          (this.insideBox.top * graphSizeRate -
            (this.svg.rect.top - graphRect.top)) /
          this.graph.transRate,
      };

      this.graph.transform.x -= change.x;
      this.graph.transform.y -= change.y;

      this.graph.dom.setAttribute(
          'transform',
          `translate(${this.graph.transform.x},${this.graph.transform.y}) ` +
          `scale(${this.graph.transform.k})`,
      );
    },
    /**
     * Displacement of the small map when the large picture is changed
     */
    setInsideBoxData() {
      const graphRect = this.graph.dom.getBoundingClientRect();
      const transRate = graphRect.width / this.smallResize.width;

      this.insideBox.left = (this.svg.rect.left - graphRect.left) / transRate;
      this.insideBox.top = (this.svg.rect.top - graphRect.top) / transRate;

      this.insideBox.width = this.svg.rect.width / transRate;
      this.insideBox.height = this.svg.rect.height / transRate;
      this.styleSet('#inside-box', this.insideBox);
    },
    /**
     * Setting the width and height of a node
     * @param {String} id Dom id whose style needs to be modified
     * @param {Object} domData Data of dom
     */
    styleSet(id, domData) {
      const dom = document.querySelector(id);
      dom.style.left = `${domData.left}px`;
      dom.style.top = `${domData.top}px`;
      dom.style.width = `${domData.width}px`;
      dom.style.height = `${domData.height}px`;
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

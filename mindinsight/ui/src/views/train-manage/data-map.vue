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
  <!--cl-data-map-manage -->
  <div class="cl-data-map-manage">
    <div class='data-map-p32'>
      <div class="cl-title cl-data-map-title">
        <div class="cl-title-left">{{$t('dataMap.titleText')}}
          <div class="path-message">
            <span>{{$t('symbols.leftbracket')}}</span>
            <span>{{$t('trainingDashboard.summaryDirPath')}}</span>
            <span>{{summaryPath}}</span>
            <span>{{$t('symbols.rightbracket')}}</span>
          </div>
        </div>
        <div class="cl-title-right">
          <div class="cl-close-btn"
               @click="jumpToTrainDashboard">
            <img src="@/assets/images/close-page.png">
          </div>
        </div>
      </div>
      <div class="cl-content">
        <div id="data-maps">
          <div class="cl-data-map"
               :class="fullScreen? 'full-screen':''">
            <!-- data-map -->
            <div class="data-map-container"
                 :class="rightShow?'':'all'">
              <div id="graph"></div>
              <div class="image-noData"
                   v-if="noData">
                <div>
                  <img :src="require('@/assets/images/nodata.png')"
                       alt="" />
                </div>
                <div class="noData-text">{{$t("public.noData")}}</div>
              </div>
              <div :title="$t('graph.fullScreen')"
                   class="full-screen-button"
                   @click="fullScreen = !fullScreen"></div>
              <div :title="$t('graph.fitScreen')"
                   class="fit-screen"
                   @click="fit()"></div>
              <div :title="$t('graph.downloadPic')"
                   class="download-button"
                   @click="downLoadSVG"></div>
            </div>
            <!-- Right column -->
            <div id="sidebar"
                 :class="rightShow ? '' : 'right-hide'">
              <div class="toggle-right"
                   @click="toggleRight"
                   :class="[rightShow?'':'toggle-left',`toggle-${themeIndex}-btn`]">
              </div>
              <!-- Node information -->
              <div class="node-info"
                   :class="showLegend?'node-info-con node-info-container':'node-info-con node-info-container-long'">
                <div class="title">{{$t('graph.nodeInfo')}}</div>
                <div class="node-info-list"
                     v-if="selectedNode && selectedNode.length">
                  <div class="item"
                       v-for="item in selectedNode"
                       :key="item.key">
                    <div class="label">{{item.key}}</div>
                    <div class="value">{{item.value}}</div>
                  </div>
                </div>
              </div>
              <!-- Legend -->
              <div class="legend"
                   v-if="!fullScreen">
                <div class="title">
                  {{ $t('graph.legend') }}
                  <img :src="require('@/assets/images/all-drop-down.png')"
                       v-show="!showLegend"
                       @click="foldLegend"
                       alt="" />
                  <img :src="require('@/assets/images/all-uptake.png')"
                       v-show="showLegend"
                       @click="foldLegend"
                       alt="" />
                </div>
                <div v-show="showLegend"
                     class="legend-content">
                  <div class="legend-item">
                    <div class="pic">
                      <img :src="require(`@/assets/images/${themeIndex}/creat-dataset.svg`)"
                           alt="" />
                    </div>
                    <div>Create</div>
                  </div>
                  <div class="legend-item">
                    <div class="pic">
                      <img :src="require(`@/assets/images/${themeIndex}/map-dataset.svg`)"
                           alt="" />
                    </div>
                    <div>Map</div>
                  </div>
                  <div class="legend-item">
                    <div class="pic">
                      <img :src="require(`@/assets/images/${themeIndex}/operator-node.svg`)"
                           alt="" />
                    </div>
                    <div>Operator</div>
                  </div>
                  <div class="legend-item">
                    <div class="pic">
                      <img :src="require(`@/assets/images/${themeIndex}/shuffle-dataset.svg`)"
                           alt="" />
                    </div>
                    <div>Shuffle</div>
                  </div>
                  <div class="legend-item">
                    <div class="pic">
                      <img :src="require(`@/assets/images/${themeIndex}/batch-img.svg`)"
                           alt="" />
                    </div>
                    <div>Batch</div>
                  </div>
                  <div class="legend-item">
                    <div class="pic">
                      <img :src="require(`@/assets/images/${themeIndex}/repeat-dataset.svg`)"
                           alt="" />
                    </div>
                    <div>Repeat</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import RequestService from '../../services/request-service';
import CommonProperty from '@/common/common-property.js';
import {select, selectAll, zoom} from 'd3';
import {event as currentEvent} from 'd3-selection';
import 'd3-graphviz';
const d3 = {select, selectAll, zoom};
export default {
  data() {
    return {
      allGraphData: {},
      graphviz: null,
      totalMemory: 16777216 * 2, // Memory size of the graph plug-in
      scaleRange: [0.0001, 10000], // graph zooms in and zooms out.
      rightShow: true,
      showLegend: true,
      fullScreen: false,
      trainJobID: '',
      selectedNode: [],
      noData: false,
      summaryPath: this.$route.query.summaryPath,
      themeIndex: this.$store.state.themeIndex,
    };
  },
  mounted() {
    // Judging from the training job overview.
    if (!this.$route.query || !this.$route.query.train_id) {
      this.trainJobID = '';
      this.$message.error(this.$t('trainingDashboard.invalidId'));
      document.title = `${this.$t('trainingDashboard.dataMap')}-MindInsight`;
      return;
    }
    this.trainJobID = this.$route.query.train_id;
    document.title = `${decodeURIComponent(this.trainJobID)}-${this.$t('trainingDashboard.dataMap')}-MindInsight`;
    this.$nextTick(() => {
      this.queryGraphData();
    });
  },
  destroyed() {},
  methods: {
    /**
     * To obtain graph data.
     */
    queryGraphData() {
      const params = {
        train_id: this.trainJobID,
      };
      RequestService.queryDatasetGraph(params).then((res) => {
        if (res && res.data && res.data.dataset_graph) {
          const data = JSON.parse(JSON.stringify(res.data.dataset_graph));
          this.dealResponseData(data);
          if (Object.keys(this.allGraphData).length) {
            this.noData = false;
            const dot = this.packageGraphData();
            this.initGraph(dot);
          } else {
            this.noData = true;
          }
        }
      });
    },
    /**
     * Processing Graph Data
     * @param {Object} data Data of the graph
     * @param {String} parentKey Key value of the parent-level data.
     * @param {Number} index Index of a node.
     */
    dealResponseData(data, parentKey = '', index = 0) {
      if (!data) {
        return;
      }
      const key = `${parentKey ? parentKey + '/' : ''}${data.op_type || ''}_${index}`;
      const obj = {
        key: key,
        id: '',
      };
      Object.keys(data).forEach((k) => {
        {
          if (k !== 'children') {
            obj[k] = JSON.parse(JSON.stringify(data[k]));
          } else {
            obj.children = [];
            if (data.children && data.children.length) {
              data.children.forEach((data, ind) => {
                obj.children.push(`${obj.key}/${data.op_type}_${ind}`);
                this.dealResponseData(data, obj.key, ind);
              });
            }
          }
        }
      });
      this.allGraphData[key] = obj;
    },
    /**
     * Encapsulates graph data into dot data.
     * @return {String} Dot string for packing graph data
     */
    packageGraphData() {
      const nodeType = [
        'BatchDataset',
        'ShuffleDataset',
        'RepeatDataset',
        'MapDataset',
        'Batch',
        'Shuffle',
        'Repeat',
        'Map',
      ];
      const subGraphNodeType = ['Map', 'MapDataset'];
      let nodeStr = '';
      let edgeStr = '';
      Object.keys(this.allGraphData).forEach((key) => {
        const node = this.allGraphData[key];
        if (subGraphNodeType.includes(node.op_type)) {
          nodeStr += this.packageSubGraph(key);
        } else {
          node.id = key;
          nodeStr +=
            `<${node.key}>[id="${node.key}";label="${node.op_type}";` +
            `class=${
              nodeType.includes(node.op_type) ? node.op_type.replace('Dataset', '') : 'Create'
            };shape=rect;fillcolor="#9cc3e5";];`;
        }
      });

      Object.keys(this.allGraphData).forEach((key) => {
        const node = this.allGraphData[key];
        node.children.forEach((k) => {
          const child = this.allGraphData[k];
          edgeStr += `<${child.id}>-><${node.id}>[${
            subGraphNodeType.includes(child.op_type) ? `ltail=<cluster_${child.key}>;` : ''
          }${subGraphNodeType.includes(node.op_type) ? `lhead=<cluster_${node.key}>;` : ''}];`;
        });
      });
      const initSetting = 'node[style="filled";fontsize="10px"];edge[fontsize="6px";];';
      return `digraph {compound=true;rankdir=LR;${initSetting}${nodeStr}${edgeStr}}`;
    },

    /**
     * Encapsulates the data of a subgraph.
     * @param {String} key Key value of a node.
     * @return {String} Dot string
     */
    packageSubGraph(key) {
      const node = this.allGraphData[key];
      let strTemp = '';
      if (node.operations && node.operations.length) {
        let nodeStr = '';
        node.operations.forEach((op, ind) => {
          const id = `${node.key}/${op.tensor_op_name}_${ind}`;
          op.key = id;
          nodeStr += `<${id}>[id="${id}";class=Operator;label="${op.tensor_op_name}";fillcolor="#c5e0b3"];`;
          if (!node.id) {
            node.id = id;
          }
        });
        strTemp +=
          `subgraph <cluster_${key}>{style="filled";id="${key}";` +
          `label="${node.op_type}";fillcolor="#9cc3e5";${nodeStr}};`;
      }
      return strTemp;
    },
    /**
     * Initializing the dataset graph
     * @param {String} dot Dot statement encapsulated in graph data
     */
    initGraph(dot) {
      this.graphviz = d3
          .select('#graph')
          .graphviz({useWorker: false, totalMemory: this.totalMemory})
          .zoomScaleExtent(this.scaleRange)
          .dot(dot)
          .attributer(this.attributer)
          .render(this.afterInitGraph);
    },
    /**
     * Process other data after the dataset graph is initialized.
     */
    afterInitGraph() {
      setTimeout(() => {
        if (this.graphviz) {
          this.graphviz._data = null;
          this.graphviz._dictionary = null;
          this.graphviz = null;
        }
      }, 100);
      d3.select('#graph').selectAll('title').remove();
      this.startApp();
    },
    /**
     * Default method of the graph rendering adjustment. Set the node format.
     * @param {Object} datum Object of the current rendering element.
     * @param {Number} index Indicates the subscript of the current rendering element.
     * @param {Array} nodes An array encapsulated with the current rendering element.
     */
    attributer(datum, index, nodes) {
      if (datum.tag === 'svg') {
        const width = '100%';
        const height = '100%';
        datum.attributes.width = width;
        datum.attributes.height = height;
      }
    },
    /**
     * Initialization method executed after the graph rendering is complete
     */
    startApp() {
      this.initZooming();
      const nodes = d3.selectAll('g.node, g.cluster');
      nodes.on('click', (target, index, nodesList) => {
        this.selectNodeInfo(target);
        const selectedNode = nodesList[index];
        nodes.classed('selected', false);
        d3.select(`g[id="${selectedNode.id}"]`).classed('selected', true);
      });
    },

    /**
     * Initializing the Zoom Function of a Graph
     */
    initZooming() {
      const svgDom = document.querySelector('#graph svg');
      const svgRect = svgDom.getBoundingClientRect();

      const graphDom = document.querySelector('#graph #graph0');
      const graphBox = graphDom.getBBox();
      const graphRect = graphDom.getBoundingClientRect();
      let graphTransform = {};

      const minScale = Math.min(svgRect.width / 2 / graphRect.width, svgRect.height / 2 / graphRect.height);

      const padding = 4;
      const minDistance = 50;
      const pointer = {start: {x: 0, y: 0}, end: {x: 0, y: 0}};

      const zoom = d3
          .zoom()
          .on('start', () => {
            const event = currentEvent.sourceEvent;
            pointer.start.x = event.x;
            pointer.start.y = event.y;
          })
          .on('zoom', () => {
            const event = currentEvent.sourceEvent;
            const transformData = this.getTransformData(graphDom);
            if (!Object.keys(graphTransform).length) {
              graphTransform = {
                x: transformData.translate[0],
                y: transformData.translate[1],
                k: transformData.scale[0],
              };
            }

            let tempStr = '';
            let change = {};
            let scale = transformData.scale[0];
            const graphRect = graphDom.getBoundingClientRect();
            const transRate = graphBox.width / graphRect.width;
            if (event.type === 'mousemove') {
              pointer.end.x = event.x;
              pointer.end.y = event.y;
              let tempX = pointer.end.x - pointer.start.x;
              let tempY = pointer.end.y - pointer.start.y;
              const paddingTrans = Math.max(padding / transRate / scale, minDistance);
              if (graphRect.left + paddingTrans + tempX >= svgRect.left + svgRect.width) {
                tempX = Math.min(tempX, 0);
              }
              if (graphRect.left + graphRect.width - paddingTrans + tempX <= svgRect.left) {
                tempX = Math.max(tempX, 0);
              }
              if (graphRect.top + paddingTrans + tempY >= svgRect.top + svgRect.height) {
                tempY = Math.min(tempY, 0);
              }
              if (graphRect.top + graphRect.height - paddingTrans + tempY <= svgRect.top) {
                tempY = Math.max(tempY, 0);
              }

              change = {
                x: tempX * transRate * scale,
                y: tempY * transRate * scale,
              };
              pointer.start.x = pointer.end.x;
              pointer.start.y = pointer.end.y;
            } else if (event.type === 'wheel') {
              const wheelDelta = -event.deltaY;
              const rate = 1.2;
              scale = wheelDelta > 0 ? transformData.scale[0] * rate : transformData.scale[0] / rate;

              scale = Math.max(this.scaleRange[0], scale, minScale);
              scale = Math.min(this.scaleRange[1], scale);
              change = {
                x: (graphRect.x + padding / transRate - event.x) * transRate * (scale - transformData.scale[0]),
                y: (graphRect.bottom - padding / transRate - event.y) * transRate * (scale - transformData.scale[0]),
              };
            }

            graphTransform = {
              x: transformData.translate[0] + change.x,
              y: transformData.translate[1] + change.y,
              k: scale,
            };

            tempStr = `translate(${graphTransform.x},${graphTransform.y}) scale(${graphTransform.k})`;
            graphDom.setAttribute('transform', tempStr);
            event.stopPropagation();
            event.preventDefault();
          });

      const svg = d3.select('#graph svg');
      svg.on('.zoom', null);
      svg.call(zoom);
      svg.on('dblclick.zoom', null);
      svg.on('wheel.zoom', null);

      const graph0 = d3.select('#graph #graph0');
      graph0.on('.zoom', null);
      graph0.call(zoom);
    },
    /**
     * Obtains the transform data of a node.
     * @param {Object} node Node dom data
     * @return {Object} Transform data of a node
     */
    getTransformData(node) {
      if (!node) {
        return [];
      }
      const transformData = node.getAttribute('transform');
      const attrObj = {};
      if (transformData) {
        const lists = transformData.trim().split(' ');
        lists.forEach((item) => {
          const index1 = item.indexOf('(');
          const index2 = item.indexOf(')');
          const name = item.substring(0, index1);
          const params = item
              .substring(index1 + 1, index2)
              .split(',')
              .map((i) => {
                return parseFloat(i) || 0;
              });
          attrObj[name] = params;
        });
      }
      return attrObj;
    },
    /**
     * Process the selected node information.
     * @param {Object} target Selected Object
     */
    selectNodeInfo(target) {
      this.selectedNode = [];
      if (!target || !target.key) {
        return;
      }
      let id = '';
      let select = '';
      if (target.attributes.class.indexOf('Operator') !== -1) {
        id = target.attributes.id.slice(0, target.attributes.id.lastIndexOf('/'));
        let index = -1;
        if (target.attributes.id.match(/\d+$/)) {
          index = parseInt(target.attributes.id.match(/\d+$/)[0]);
        }
        if (this.allGraphData[id] && index > -1) {
          select = this.allGraphData[id].operations[index];
        }
      } else {
        id = target.attributes.id;
        select = this.allGraphData[id];
      }
      if (select) {
        const ignoreKeys = ['op_module', 'op_type', 'children', 'operations', 'id', 'key'];
        Object.keys(select).forEach((item) => {
          if (!ignoreKeys.includes(item)) {
            const value =
              select[item] instanceof Array ? select[item].join(', ') : select[item] === null ? 'None' : select[item];
            this.selectedNode.push({key: item, value: value});
          }
        });
      }
    },
    /**
     * Adapt to the screen
     */
    fit() {
      const graphDom = document.getElementById('graph0');
      const box = graphDom.getBBox();
      const str = `translate(${-box.x},${-box.y}) scale(1)`;
      graphDom.setAttribute('transform', str);
    },
    /**
     * Download svg
     */
    downLoadSVG() {
      const svgXml = document.querySelector('#graph #graph0').innerHTML;
      const bbox = document.getElementById('graph0').getBBox();
      const viewBoxSize = `${bbox.x} ${bbox.y} ${bbox.width} ${bbox.height}`;
      const encodeStr =
        `<svg xmlns="http://www.w3.org/2000/svg" ` +
        `xmlns:xlink="http://www.w3.org/1999/xlink" ` +
        `width="${bbox.width}" height="${bbox.height}" ` +
        `viewBox="${viewBoxSize}">${
          CommonProperty.dataMapDownloadStyle[this.$store.state.themeIndex]
        }<g>${svgXml}</g></svg>`;

      // Write the svg stream encoded by base64 to the image object.
      const src = `data:image/svg+xml;base64,
      ${window.btoa(unescape(encodeURIComponent(encodeStr)))}`;
      const a = document.createElement('a');
      a.href = src; // Export the information in the canvas as image data.
      a.download = 'dataMap.svg'; // Set the download name.
      const evt = document.createEvent('MouseEvents');
      evt.initEvent('click', true, true);
      a.dispatchEvent(evt);
    },
    /**
     * Collapse on the right
     */
    toggleRight() {
      this.rightShow = !this.rightShow;
    },
    /**
     * Fold the legend area.
     */
    foldLegend() {
      this.showLegend = !this.showLegend;
    },
    /**
     * Jump back to train dashboard
     */
    jumpToTrainDashboard() {
      this.$router.push({
        path: '/train-manage/training-dashboard',
        query: {
          id: this.trainJobID,
        },
      });
    },
  },
};
</script>
<style>
.cl-data-map-manage {
  height: 100%;
}
.cl-data-map-manage .cl-data-map-title {
  height: 56px;
  line-height: 56px;
}
.cl-data-map-manage .cl-data-map-title .path-message {
  display: inline-block;
  line-height: 20px;
  padding: 0px 4px 15px 4px;
  font-weight: bold;
  vertical-align: bottom;
}
.cl-data-map-manage .data-map-p32 {
  height: 100%;
}
.cl-data-map-manage .cl-content {
  height: calc(100% - 50px);
  overflow: auto;
}
.cl-data-map-manage #data-maps {
  width: 100%;
  height: 100%;
  font-size: 0;
  background: #f0f2f5;
}
.cl-data-map-manage #data-maps .cl-data-map {
  position: relative;
  width: 100%;
  height: 100%;
  background-color: var(--bg-color);
  padding: 0 32px 24px;
  min-height: 700px;
  overflow: hidden;
}
.cl-data-map-manage #data-maps .cl-data-map .data-map-container {
  height: 100%;
  width: calc(100% - 442px);
  position: relative;
}
.cl-data-map-manage #data-maps .cl-data-map .data-map-container #graph {
  height: 100%;
  width: 100%;
  padding: 16px;
  background-color: var(--graph-bg-color);
}
.cl-data-map-manage #data-maps .cl-data-map .data-map-container #graph text {
  fill: var(--font-color);
}
.cl-data-map-manage #data-maps .cl-data-map .data-map-container #graph #graph0 > polygon {
  fill: transparent;
}
.cl-data-map-manage #data-maps .cl-data-map .data-map-container #graph .node,
.cl-data-map-manage #data-maps .cl-data-map .data-map-container #graph .cluster {
  cursor: pointer;
}
.cl-data-map-manage #data-maps .cl-data-map .data-map-container #graph .selected polygon,
.cl-data-map-manage #data-maps .cl-data-map .data-map-container #graph .selected ellipse {
  stroke: red !important;
  stroke-width: 2px;
}
.cl-data-map-manage #data-maps .cl-data-map .data-map-container #graph .Create > polygon,
.cl-data-map-manage #data-maps .cl-data-map .data-map-container #graph .Operator > ellipse {
  stroke: var(--create-dataset-polygon-stroke-color);
  fill: var(--create-dataset-polygon-fill-color);
}
.cl-data-map-manage #data-maps .cl-data-map .data-map-container #graph .cluster > polygon {
  fill: var(--graph-polygon-color);
  stroke: var(--theme-color);
}
.cl-data-map-manage #data-maps .cl-data-map .data-map-container #graph .Repeat > polygon {
  stroke: var(--repeat-dataset-polygon-stroke-color);
  fill: var(--repeat-dataset-polygon-fill-color);
}
.cl-data-map-manage #data-maps .cl-data-map .data-map-container #graph .Shuffle > polygon {
  stroke: var(--shuffle-dataset-polygon-stroke-color);
  fill: var(--shuffle-dataset-polygon-fill-color);
}
.cl-data-map-manage #data-maps .cl-data-map .data-map-container #graph .Batch > polygon {
  stroke: var(--batch-dataset-polygon-stroke-color);
  fill: var(--batch-dataset-polygon-fill-color);
}
.cl-data-map-manage #data-maps .cl-data-map .data-map-container #graph .edge path {
  stroke: var(--edge-path-color);
}
.cl-data-map-manage #data-maps .cl-data-map .data-map-container #graph .edge polygon {
  fill: var(--edge-path-color);
  stroke: var(--edge-path-color);
}
.cl-data-map-manage #data-maps .cl-data-map .data-map-container .full-screen-button {
  position: absolute;
  right: 10px;
  top: 10px;
  cursor: pointer;
  width: 12px;
  height: 12px;
  z-index: 999;
  display: inline-block;
  background-image: url('../../assets/images/full-screen.png');
}
.cl-data-map-manage #data-maps .cl-data-map .data-map-container .fit-screen {
  position: absolute;
  width: 16px;
  height: 14px;
  right: 32px;
  top: 10px;
  z-index: 999;
  cursor: pointer;
  display: inline-block;
  background-image: url('../../assets/images/fit.png');
}
.cl-data-map-manage #data-maps .cl-data-map .data-map-container .download-button {
  position: absolute;
  width: 16px;
  height: 14px;
  right: 54px;
  top: 10px;
  z-index: 999;
  cursor: pointer;
  display: inline-block;
  background-image: url('../../assets/images/download.png');
  background-size: 14px 14px;
  background-repeat: no-repeat;
}
.cl-data-map-manage #data-maps .cl-data-map.full-screen {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
  width: auto;
  height: auto;
  padding: 0;
}
.cl-data-map-manage #data-maps .cl-data-map.full-screen .data-map-container {
  width: 100%;
}
.cl-data-map-manage #data-maps .cl-data-map.full-screen #sidebar .node-info-con {
  height: calc(100% - 280px);
}
.cl-data-map-manage #data-maps #sidebar.right-hide {
  right: -442px;
}
.cl-data-map-manage #data-maps #sidebar {
  position: absolute;
  right: 0;
  top: 0;
  width: 442px;
  height: calc(100% - 24px);
  border-radius: 6px;
  text-align: left;
  background-color: var(--item-bg-color);
  display: inline-block;
  color: var(--font-color);
  font-size: 14px;
  line-height: 14px;
  padding: 24px 32px;
  border: 1px solid var(--graph-right-module-border-color);
}
.cl-data-map-manage #data-maps #sidebar div,
.cl-data-map-manage #data-maps #sidebar span,
.cl-data-map-manage #data-maps #sidebar pre {
  font-size: 14px;
}
.cl-data-map-manage #data-maps #sidebar .title {
  padding: 24px 0;
  font-size: 14px;
  color: var(--font-color);
}
.cl-data-map-manage #data-maps #sidebar .title img {
  float: right;
  margin-right: 10px;
  cursor: pointer;
}
.cl-data-map-manage #data-maps #sidebar .node-info-container {
  height: calc(100% - 156px);
}
.cl-data-map-manage #data-maps #sidebar .node-info-container-long {
  height: calc(100% - 62px);
}
.cl-data-map-manage #data-maps #sidebar .node-info .title {
  padding: 0 0 24px;
  font-size: 14px;
  color: var(--font-color);
}
.cl-data-map-manage #data-maps #sidebar .node-info .node-info-list {
  height: calc(100% - 62px);
  overflow-y: auto;
}
.cl-data-map-manage #data-maps #sidebar .node-info .item {
  line-height: 20px;
  padding: 5px 0 5px 20px;
  background-color: var(--graph-legend-bg-color);
}
.cl-data-map-manage #data-maps #sidebar .node-info .item .label {
  vertical-align: top;
  width: 30%;
  word-break: break-all;
  display: inline-block;
}
.cl-data-map-manage #data-maps #sidebar .node-info .item .value {
  padding: 0 10px;
  vertical-align: top;
  display: inline-block;
  width: 70%;
  word-break: break-all;
}
.cl-data-map-manage #data-maps #sidebar .legend .legend-content {
  background-color: var(--graph-legend-bg-color);
  padding: 0 32px;
  height: 94px;
  overflow-y: auto;
}
.cl-data-map-manage #data-maps #sidebar .legend .legend-item {
  padding: 5px 0;
  display: inline-block;
  width: 50%;
  font-size: 14px;
  line-height: 20px;
}
.cl-data-map-manage #data-maps #sidebar .legend .legend-item .pic {
  width: 45px;
  text-align: center;
}
.cl-data-map-manage #data-maps #sidebar .legend .legend-item .pic img {
  width: 45px;
  height: 15px;
  margin-left: -20px;
  vertical-align: middle;
}
.cl-data-map-manage #data-maps #sidebar .legend .legend-item div {
  display: inline-block;
  padding-left: 20px;
  vertical-align: middle;
}
.cl-data-map-manage #data-maps #sidebar .toggle-right {
  position: absolute;
  top: calc(50% - 43px);
  left: -14px;
  width: 24px;
  height: 88px;
  cursor: pointer;
  transform: rotateY(180deg);
}
.cl-data-map-manage #data-maps #sidebar .toggle-right.toggle-0-btn {
  background-image: url('../../assets/images/0/collapse-left.svg');
}
.cl-data-map-manage #data-maps #sidebar .toggle-right.toggle-1-btn {
  background-image: url('../../assets/images/1/collapse-left.svg');
}
.cl-data-map-manage #data-maps #sidebar .toggle-right.toggle-left.toggle-0-btn {
  background-image: url('../../assets/images/0/collapse-right.svg');
}
.cl-data-map-manage #data-maps #sidebar .toggle-right.toggle-left.toggle-1-btn {
  background-image: url('../../assets/images/1/collapse-right.svg');
}
.cl-data-map-manage #data-maps .data-map-container.all {
  width: 100%;
}
.cl-data-map-manage #data-maps .image-noData {
  width: 100%;
  height: 100%;
  background: #fff;
  position: absolute;
  top: 0;
  left: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  z-index: 200;
}
.cl-data-map-manage #data-maps .noData-text {
  margin-top: 33px;
  font-size: 18px;
}
.cl-data-map-manage .cl-close-btn {
  width: 20px;
  height: 20px;
  vertical-align: -3px;
  cursor: pointer;
  display: inline-block;
}
.cl-data-map-manage .cl-title-right {
  padding-right: 32px;
}
</style>

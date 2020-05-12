<!--
Copyright 2019 Huawei Technologies Co., Ltd.All Rights Reserved.

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
  <!--cl-graph-manage -->
  <div class="cl-graph-manage">
    <div class='graph-p32'>
      <div class="cl-title cl-graph-title">
        <div class="cl-title-left">{{$t('graph.titleText')}}</div>
        <div class="cl-title-right">
          <div class="cl-close-btn"
               @click="jumpToTrainDashboard">
            <img src="@/assets/images/close-page.png">
          </div>
        </div>
      </div>
      <div class="cl-content">
        <div id="graphs">
          <div class="cl-graph"
               :class="fullScreen? 'full-screen':''">
            <!-- graph -->
            <div class="graph-container"
                 :class="rightShow?'':'all'">
              <!-- No data is displayed. -->
              <div class="image-noData"
                   v-if="!loading.show && !Object.keys(allGraphData).length">
                <div>
                  <img :src="require('@/assets/images/nodata.png')"
                       alt="" />
                </div>
                <div class="noData-text">{{$t("public.noData")}}</div>
              </div>
              <!-- Operation button column -->
              <div class="operate-button-list">
                <!-- Download button. -->
                <div :title="$t('graph.fullScreen')"
                     class="full-screen-button"
                     @click="toggleScreen"></div>
                <div :title="$t('graph.downloadPic')"
                     class="download-button"
                     @click="downLoadSVG"></div>
              </div>
              <div id="graph"
                   class="graph"
                   v-loading.fullscreen.lock="loading.show"
                   element-loading-background="rgba(0, 0, 0, 0.3)"
                   :element-loading-text="loading.info"></div>
            </div>
            <!-- Right column -->
            <div id="sidebar"
                 :class="rightShow ? '' : 'right-hide'">
              <div class="toggle-right"
                   @click="toggleRight">
                <i :class="rightShow?'icon-toggle':'icon-toggle icon-left'"></i>
              </div>
              <!-- Search box -->
              <el-select @change="fileChange"
                         @visible-change="getSelectList"
                         :popper-append-to-body="false"
                         class='search'
                         v-model="fileSearchBox.value">
                <el-option v-for="item in fileSearchBox.suggestions"
                           :key="item.value"
                           :title="item.value"
                           :label="item.value"
                           :value="item.value">
                </el-option>
              </el-select>
              <!-- Search box -->
              <Autocomplete class='search'
                            v-model="searchBox.value"
                            :disabled="!fileSearchBox.value"
                            :fetch-suggestions="searchNodesNames"
                            :placeholder="$t('graph.inputNodeName')"
                            :popper-append-to-body="false"
                            clearable
                            @select="querySingleNode"
                            @blur="selectBoxVisibleTriggle"
                            @focus="selectBoxVisibleTriggle"
                            select-when-unmatched></Autocomplete>
              <!-- Functional Area -->
              <div id="small-container">
                <div id="small-resize">
                  <div id="small-map"></div>
                  <div id="inside-box"></div>
                </div>
              </div>
              <!-- Node information -->
              <div :class="showLegend?'node-info-con node-info-container':'node-info-con node-info-container-long'">
                <div class="title">
                  {{ $t('graph.nodeInfo') }}
                  <img :src="require('@/assets/images/all-drop-down.png')"
                       fun="fold"
                       hidden
                       alt="" />
                  <img :src="require('@/assets/images/all-uptake.png')"
                       fun="fold"
                       hidden
                       alt="" />
                </div>
                <div class="node-info"
                     v-show='selectedNode.show'>
                  <div class="items">
                    <div class="label item">{{ $t('graph.name') }}</div>
                    <div class="value"><span class="cl-display-block"
                            @dblclick="nodeNameClick">{{ selectedNode.title }}</span></div>
                  </div>
                  <div class="items"
                       v-if="selectedNode.countShow">
                    <div class="label item">{{ $t('graph.count') }}</div>
                    <div class="value items-over">{{ selectedNode.count }}</div>
                  </div>
                  <div class="items"
                       v-if="!selectedNode.countShow">
                    <div class="label item">{{ $t('graph.type') }}</div>
                    <div class="value items-over">{{ selectedNode.type }}</div>
                  </div>
                  <div class="items itemHeight"
                       v-if="!selectedNode.countShow">
                    <div class="item">{{ $t('graph.attr') }} ({{ selectedNode.info.Attributes.length }})</div>
                  </div>
                  <ul v-if="selectedNode.info && !selectedNode.countShow"
                      class="item-content hover"
                      :class="selectedNode.info.Attributes.length>2 ?
                      'item-min2':selectedNode.info.Attributes.length>0?'item-min':''">
                    <li v-for="item in selectedNode.info.Attributes"
                        :key="item.name">
                      <div class="key">
                        {{ item.name }}
                      </div>
                      <div class="input cl-input-value">
                        <pre>{{item.value}}</pre>
                      </div>
                    </li>
                  </ul>
                  <div class="items itemHeight">
                    <div class="item">{{ $t('graph.inputs') }} (
                      {{ selectedNode.info.input.length + selectedNode.info.inputControl.length }})</div>
                  </div>
                  <ul v-if="selectedNode.info"
                      class="item-content hover"
                      :class="selectedNode.info.input.length>1?'item-min2':
                      selectedNode.info.input.length>0?'item-min':''">
                    <li v-for="item in selectedNode.info.input"
                        :key="item.$index"
                        @click="querySingleNode({value: item.name})"
                        class="pointer">
                      <div class="input">{{ item.name }}</div>
                      <div class="size">{{ item.value }}</div>
                      <div class="clear"></div>
                    </li>
                    <li class="control-list"
                        v-if="selectedNode.info && selectedNode.info.inputControl.length">
                      <div class="dependence-title"
                           @click="toggleControl('input')"
                           :class="selectedNode.showControl.input?'':'hide'">
                        <img :src="require('@/assets/images/all-uptake.png')"
                             alt="" />
                        {{ $t('graph.controlDependencies')}}
                      </div>
                      <ul v-show="selectedNode.showControl.input">
                        <li v-for="item in selectedNode.info.inputControl"
                            :key="item.$index"
                            @click="querySingleNode({value: item.name})"
                            class="pointer">
                          <div class="input">{{ item.name }}</div>
                          <div class="size">{{ item.value }}</div>
                          <div class="clear"></div>
                        </li>
                      </ul>
                    </li>
                  </ul>
                  <div class="items">
                    <div class="item">{{ $t('graph.outputs') }} (
                      {{ selectedNode.info.output.length + selectedNode.info.outputControl.length }})</div>
                  </div>
                  <ul v-if="selectedNode.info"
                      class="item-content hover"
                      :class="selectedNode.info.output.length>1?
                      'item-min2':selectedNode.info.output.length>0?'item-min':''">
                    <li v-for="item in selectedNode.info.output"
                        :key="item.$index"
                        @click="querySingleNode({value: item.name})"
                        class="pointer">
                      <div class="input">{{ item.name }}</div>
                      <div class="size">{{ item.value }}</div>
                      <div class="clear"></div>
                    </li>
                    <li class="control-list"
                        v-if="selectedNode.info && selectedNode.info.outputControl.length">
                      <div class="dependence-title"
                           @click="toggleControl('output')"
                           :class="selectedNode.showControl.output?'':'hide'">
                        <img :src="require('@/assets/images/all-uptake.png')"
                             alt="" />
                        {{ $t('graph.controlDependencies')}}
                      </div>
                      <ul v-show="selectedNode.showControl.output">
                        <li v-for="item in selectedNode.info.outputControl"
                            :key="item.$index"
                            @click="querySingleNode({value: item.name})"
                            class="pointer">
                          <div class="input">{{ item.name }}</div>
                          <div class="size">{{ item.value }}</div>
                          <div class="clear"></div>
                        </li>
                      </ul>
                    </li>
                  </ul>
                  <div class="items"
                       v-if="selectedNode.info && selectedNode.info.output_i !== 0">
                    <div class="label item">{{ $t('graph.outputs_i') }}</div>
                    <span class="value">{{ selectedNode.info.output_i }}</span>
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
                      <img :src="require('@/assets/images/name-scope.png')"
                           alt="" />
                    </div>
                    <div class="legend-text"
                         :title="$t('graph.nameSpace')">{{ $t('graph.nameSpace') }}</div>
                  </div>
                  <div class="legend-item">
                    <div class="pic">
                      <img :src="require('@/assets/images/operator-node.png')"
                           alt="" />
                    </div>
                    <div class="legend-text"
                         :title="$t('graph.operatorNode')">{{ $t('graph.operatorNode') }}</div>
                  </div>
                  <div class="legend-item">
                    <div class="pic">
                      <img :src="require('@/assets/images/virtual-node.png')"
                           alt="" />
                    </div>
                    <div class="legend-text"
                         :title="$t('graph.virtualNode')">{{ $t('graph.virtualNode') }}</div>
                  </div>
                  <div class="legend-item">
                    <div class="pic">
                      <img :src="require('@/assets/images/polymetric.png')"
                           alt="" />
                    </div>
                    <div class="legend-text"
                         :title="$t('graph.polymetric')">{{ $t('graph.polymetric') }}</div>
                  </div>
                  <div class="legend-item">
                    <div class="pic">
                      <img :src="require('@/assets/images/constant-node.png')"
                           alt="" />
                    </div>
                    <div class="legend-text"
                         :title="$t('graph.constantNode')">{{ $t('graph.constantNode') }}</div>
                  </div>
                  <div class="legend-item">
                    <div class="pic">
                      <img :src="require('@/assets/images/const.png')"
                           alt="" />
                    </div>
                    <div class="legend-text"
                         :title="$t('graph.virtualConstantNode')">{{ $t('graph.virtualConstantNode') }}</div>
                  </div>
                  <div class="legend-item">
                    <div class="pic">
                      <img :src="require('@/assets/images/data-flow.png')"
                           alt="" />
                    </div>
                    <div class="legend-text"
                         :title="$t('graph.dataFlowEdge')">{{ $t('graph.dataFlowEdge') }}</div>
                  </div>
                  <div class="legend-item">
                    <div class="pic">
                      <img :src="require('@/assets/images/control-dep.png')"
                           alt="" />
                    </div>
                    <div class="legend-text"
                         :title="$t('graph.controllDepEdge')">{{ $t('graph.controllDepEdge') }}</div>
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
import Autocomplete from '@/components/autocomplete';
import CommonProperty from '@/common/common-property.js';
import RequestService from '@/services/request-service';
import {select, selectAll, zoom} from 'd3';
import 'd3-graphviz';
const d3 = {select, selectAll, zoom};
export default {
  data() {
    return {
      clickScope: {}, // Information about the node that is clicked for the first time.
      smallResize: {el: '#small-resize'}, // The container of display area box.
      insideBox: {el: '#inside-box'}, // Basic information about the display area box
      graphDom: {}, // Basic information about graph0 in svg
      graphSmall: {}, // Basic information about graph0 in the thumbnail
      svg: {}, // Basic information about svg
      eventSmall: {}, // Relative position of the thumbnail in the thumbnail click event
      // Which mouse button is triggered when the thumbnail is clicked. -1 indicates that no click event is triggered,
      // 0 indicates the left key, 1 indicates the middle key, and 2 means right key.
      clickSmall: -1,
      allGraphData: {}, // graph Original input data
      firstFloorNodes: [], // ID array of the first layer node.
      // Information about the selected node
      selectedNode: {
        info: {
          inputControl: [],
          input: [],
          outputControl: [],
          output: [],
          Attributes: [],
        },
        showControl: {
          input: true,
          output: true,
        },
      },
      // Training job id
      trainJobID: '',
      frameSpace: 25, // Distance between the namespace border and the internal node
      nodesCountLimit: 1500, // Maximum number of sub-nodes in a namespace.
      curColorIndex: 0,
      // Node search box
      searchBox: {
        value: '',
        suggestions: [],
      },
      fileSearchBox: {
        value: '',
        suggestions: [],
      },
      showLegend: true, // Display Legend
      // Controls whether the loading is displayed.
      loading: {
        show: false,
        info: '',
      },
      scaleRange: [0.0001, 10000], // graph zooms in and zooms out.
      rightShow: true, // Check whether the right side bar is displayed.
      fullScreen: false, // Display Full Screen
      totalMemory: 16777216 * 2, // Memory size of the graph plug-in
      graphviz: null,
      graphvizTemp: null,
      initOver: false,
    };
  },
  computed: {},
  watch: {},
  mounted() {
    // Judging from the training job overview.
    if (!this.$route.query || !this.$route.query.train_id) {
      this.trainJobID = '';
      this.$message.error(this.$t('trainingDashboard.invalidId'));
      return;
    }
    this.trainJobID = this.$route.query.train_id;
    this.getDatavisualPlugins();
    window.onresize = () => {
      const graphDom = document.querySelector('#graph #graph0');
      if (graphDom) {
        this.initGraphRectData();
      }
    };
  },
  destroyed() {
    window.onresize = document.onmousemove = document.onmouseup = null;
    const smallContainer = document.querySelector('#small-container');
    if (smallContainer) {
      smallContainer.onmousedown = smallContainer.onmouseup = null;
      smallContainer.onmousewheel = null;
    }
  },
  methods: {
    /**
     * Initializing the graph
     * @param {String} dot dot statement encapsulated in graph data
     */
    initGraph(dot) {
      this.graphviz = d3
          .select('#graph')
          .graphviz({useWorker: false, totalMemory: this.totalMemory})
          .zoomScaleExtent(this.scaleRange)
          .dot(dot)
          .attributer(this.attributer)
          .render(this.afterInitGraph);
      // Generate the dom of the submap.
      if (!d3.select('#graphTemp').size()) {
        d3.select('body')
            .append('div')
            .attr('id', 'graphTemp')
            .attr('style', 'visibility: collapse');
      }
      // Stores the dom of all the sorted subgraphs.
      if (!d3.select('#subgraphTemp').size()) {
        d3.select('body')
            .append('div')
            .attr('id', 'subgraphTemp')
            .attr('style', 'visibility: collapse');
      }
    },
    /**
     * Initialization method executed after the graph rendering is complete
     */
    startApp() {
      const nodes = d3.selectAll('g.node, g.cluster');
      nodes.on('click', (target, index, nodesList) => {
        // The target value of the element converted from the HTML attribute of the variable is null.
        const clickNode = nodesList[index];
        const nodeId = clickNode.id;
        const nodeClass = clickNode.classList.value;
        setTimeout(() => {
          this.clickScope = {
            id: nodeId,
            class: nodeClass,
          };
        }, 10);
        setTimeout(() => {
          this.clickScope = {};
        }, 1000);
        this.selectedNode.name = nodeId;
        this.selectNode();
        if (!event || !event.type || event.type !== 'click') {
          return;
        }
        event.stopPropagation();
        event.preventDefault();
      });
      // namespaces Expansion or Reduction
      nodes.on('dblclick', (target, index, nodesList) => {
        // The target of the element converted from the HTML attribute of the variable is empty and
        // needs to be manually encapsulated.
        const clickNode = nodesList[index];
        const nodeId = clickNode.id;
        const nodeClass = clickNode.classList.value;
        let name = nodeId;
        this.selectedNode.more =
          name.indexOf('more') !== -1 &&
          document
              .querySelector(`#graph g[id="${name}"]`)
              .attributes.class.value.indexOf('plain') === -1;
        const unfoldFlag =
          (nodeClass.includes('aggregation') ||
            nodeClass.includes('cluster') ||
            this.selectedNode.more) &&
          (!this.clickScope.id ||
            (this.clickScope.id && nodeId === this.clickScope.id));
        if (this.selectedNode.more) {
          this.selectedNode.moreDirection = name.indexOf('right') !== -1;
          this.selectedNode.moreStart = parseInt(
              name.match(/\d+/g)[name.match(/\d+/g).length - 1],
          );
          const id = document.querySelector(`#graph g[id="${name}"]`).parentNode
              .attributes.id.value;
          name = id.replace('_unfold', '');
        }
        if (unfoldFlag) {
          this.dealDoubleClick(name);
        } else if (this.clickScope.id) {
          this.selectedNode.name = this.clickScope.id;
          this.selectNode();
        }
        if (!event || !event.type || event.type !== 'dblclick') {
          return;
        }
        event.stopPropagation();
        event.preventDefault();
      });
      this.initZooming();
      if (this.selectedNode.name) {
        const type =
          /_unfold$/.exec(this.selectedNode.name) || this.selectedNode.more
            ? 'unfoldScope'
            : 'fold';
        this.selectNode(type);
      }
    },
    /**
     * Initializing the graph zoom
     */
    initZooming() {
      let startX = 0;
      let startY = 0;
      let drag = {};
      const graphDomd3 = d3.select('#graph0');
      const graphDom = document.querySelector('#graph #graph0');
      const zoom = d3
          .zoom()
          .on('start', (d) => {
          // Original translate parameter
            if (!event || !event.x || !event.y) {
              return;
            }
            startX = event.x;
            startY = event.y;
            if (!this.graphDom.transform.x || isNaN(this.graphDom.transform.x)) {
              this.initGraphRectData();
            }
            drag = {
              k: this.graphDom.transform.k,
              x: this.graphDom.transform.x,
              y: this.graphDom.transform.y,
            };
          })
          .on('zoom', (d) => {
            if (!event || !event.x || !event.y) {
              return;
            }
            const graphd = d.children[1];
            if (event.type === 'mousemove') {
            // transform Value During Dragging
              drag.x =
              this.graphDom.transform.x +
              ((event.x - startX) / this.graphDom.initWidth) *
                this.svg.viewWidth;
              drag.y =
              this.graphDom.transform.y +
              ((event.y - startY) / this.graphDom.initHeight) *
                this.svg.viewHeight;
            } else if (event.type === 'wheel') {
            // Zooms in and zooms out the transform value.
              const b = event.wheelDelta ? event.wheelDelta : event.detail;
              const lg = b < 0 ? 1 + b / 100 : b > 0 ? b / 100 - 1 : 0;
              const scale = drag.k;
              drag.k = Math.max(
                  this.scaleRange[0],
                  Math.min(drag.k * Math.pow(2, lg), this.scaleRange[1]),
              );

              this.graphDom.offsetLeft = graphDom.getBoundingClientRect().left;
              this.graphDom.offsetTop = graphDom.getBoundingClientRect().top;
              // Zoom in on the mouse.
              const axis = {};
              axis.x = event.x - this.graphDom.offsetLeft;
              axis.y =
              this.graphDom.offsetTop +
              this.graphDom.initHeight * scale -
              event.y;
              axis.smallX = (axis.x / scale) * drag.k;
              axis.smallY = (axis.y / scale) * drag.k;
              drag.x =
              drag.x +
              (axis.x - axis.smallX) *
                (this.svg.viewWidth / this.graphDom.initWidth);
              drag.y =
              drag.y -
              (axis.y - axis.smallY) *
                (this.svg.viewHeight / this.graphDom.initHeight);
              this.insideBox.scale = 1 / drag.k;
            }
            graphDomd3.attr(
                'transform',
                `translate(${drag.x},${drag.y}) scale(${drag.k})`,
            );
            graphd.attributes.transform = `scale(${drag.k}, ${drag.k}) rotate(0) translate(${drag.x} ${drag.y})`;
            graphd.translation.x = drag.x;
            graphd.translation.y = drag.y;
            this.graphDom.width = graphDom.getBoundingClientRect().width;
            this.graphDom.height = graphDom.getBoundingClientRect().height;
            this.bigMapPositionChange();
          })
          .on('end', (d) => {
            if (!drag || !drag.x || !drag.y || !drag.k) {
              return;
            }
            this.graphDom.transform = drag;
          });
      // Large Map Displacement and Amplification Operation
      const svgD3 = d3.select('svg');
      svgD3.on('.zoom', null);
      svgD3.call(zoom);
      svgD3.on('dblclick.zoom', null);
    },
    /**
     * Double-click the processing to be performed on the node to expand or narrow the namespace or aggregation node.
     * @param {String} name Name of the current node (also the ID of the node)
     */
    dealDoubleClick(name) {
      name = name.replace('_unfold', '');
      if (this.allGraphData[name].isUnfold) {
        this.selectedNode.name = name;
        this.deleteNamespace(name);
      } else {
        this.queryGraphData(name);
      }
    },
    /**
     * Default method of the graph rendering adjustment. Set the node format.
     * @param {Object} datum Object of the current rendering element.
     * @param {Number} index Indicates the subscript of the current rendering element.
     * @param {Array} nodes An array encapsulated with the current rendering element.
     */
    attributer(datum, index, nodes) {
      const isChild =
        datum.tag === 'ellipse' ||
        datum.tag === 'circle' ||
        (datum.tag === 'polygon' && datum.attributes.stroke !== 'transparent');
      if (datum.tag === 'svg') {
        const width = '100%';
        const height = '100%';
        datum.attributes.width = width;
        datum.attributes.height = height;
      } else if (isChild) {
        datum.attributes.stroke = 'rgb(167, 167, 167)';
      }
    },
    /**
     * Add the location attribute to each node to facilitate the obtaining of node location parameters.
     */
    afterInitGraph() {
      setTimeout(() => {
        if (this.graphviz) {
          this.graphviz._data = null;
          this.graphviz._dictionary = null;
          this.graphviz = null;
        }

        if (this.graphvizTemp) {
          this.graphvizTemp._data = null;
          this.graphvizTemp._dictionary = null;
          this.graphvizTemp = null;
        }
      }, 100);
      this.fitGraph('graph');
      this.transplantChildrenDom();
      const svg = document.querySelector('#subgraphTemp svg');
      if (svg) {
        svg.remove();
      }
      this.$nextTick(() => {
        this.loading.show = false;
      });
      const elements = d3
          .select('#graph')
          .selectAll('g.node, g.edge')
          .nodes();
      elements.forEach((ele) => {
        if (!ele.hasAttribute('transform')) {
          ele.setAttribute('transform', 'translate(0,0)');
        }
        // The title value needs to be manually set for the virtual node.
        if (Array.prototype.includes.call(ele.classList, 'plain')) {
          const title = ele.querySelector('title');
          title.textContent = title.textContent.split('^')[0];
        }
      });
      // The graph generated by the plug-in has a useless title and needs to be deleted.
      document.querySelector('#graph g#graph0 title').remove();
      this.initGraphRectData();
      this.startApp();
    },
    /**
     * When the value of graph is too large, enlarge the value of graph.
     * Otherwise, the node cannot be clearly displayed.
     * @param {String} id Indicates the ID of the graph diagram.
     */
    fitGraph(id) {
      const graph = document.getElementById(id);
      const maxShowWidth = graph.offsetWidth * 1.5;
      const maxShowHeight = graph.offsetHeight * 1.5;
      const graphDom = document.querySelector(`#${id} #graph0`);
      const box = graphDom.getBBox();
      let transformStr = '';
      if (box.width > maxShowWidth || box.height > maxShowHeight) {
        const graphTransformData = this.getTransformData(graphDom);
        const scale = Math.max(
            box.width / maxShowWidth,
            box.height / maxShowHeight,
        );
        const translate = {x: (box.width - maxShowWidth) / 2};

        if (!this.selectedNode.name) {
          graphTransformData.translate[0] = translate.x;
        }
        graphTransformData.scale[0] = scale;
        Object.keys(graphTransformData).forEach((key) => {
          transformStr += `${key}(${graphTransformData[key].join(',')}) `;
        });
      } else {
        transformStr = `translate(${-box.x},${-box.y}) scale(1)`;
      }
      graphDom.setAttribute('transform', transformStr.trim());
    },
    /**
     * Expand a namespace.
     * @param {String} name Nodes to be expanded or zoomed out
     * @param {Boolean} toUnfold Expand the namespace.
     */
    layoutNamescope(name, toUnfold) {
      const dotStr = this.packageNamescope(name);
      this.graphvizTemp = d3
          .select('#graphTemp')
          .graphviz({useWorker: false, totalMemory: this.totalMemory})
          .dot(dotStr)
          .zoomScaleExtent(this.scaleRange)
          .attributer((datum, index, nodes) => {
            if (
              datum.tag === 'polygon' &&
            datum.attributes.stroke !== 'transparent'
            ) {
              datum.attributes.stroke = 'rgb(167, 167, 167)';
            }
          })
          .render(() => {
            this.fitGraph('graphTemp');
            this.dealNamescopeTempGraph(name);
          });
    },
    /**
     * To obtain graph data, initialize and expand the namespace or aggregate nodes.
     * @param {String} name Name of the current node.
     * @param {String} type Type of the current node.
     */
    queryGraphData(name) {
      const namescopeChildLimit = 3500;
      const independentLayout = this.allGraphData[name]
        ? this.allGraphData[name].independent_layout
        : false;
      const params = {
        name: name,
        train_id: this.trainJobID,
        tag: this.fileSearchBox.value,
      };
      this.loading.info = this.$t('graph.queryLoading');
      this.loading.show = true;
      setTimeout(() => {
        RequestService.queryGraphData(params)
            .then(
                (response) => {
                  if (response && response.data && response.data.nodes) {
                    // If the namespace to be expanded is larger than the maximum number of subnodes,
                    // an error is reported and the namespace is highlighted.
                    const nodesCountLimit = name
                  ? this.nodesCountLimit
                  : namescopeChildLimit;
                    if (
                      !independentLayout &&
                  response.data.nodes.length > nodesCountLimit
                    ) {
                      this.$message.error(this.$t('graph.tooManyNodes'));
                      this.packageDataToObject(name, false);
                      this.loading.show = false;
                    } else {
                      const nodes = this.dealAggregationNodes(
                          JSON.parse(JSON.stringify(response.data.nodes)),
                          name,
                      );
                      if (nodes && nodes.length) {
                        this.packageDataToObject(name, true, nodes);
                        // If the name is empty, it indicates the outermost layer.
                        if (!name) {
                          const dot = this.packageGraphData();
                          this.initGraph(dot);
                        } else {
                          this.allGraphData[name].isUnfold = true;
                          this.selectedNode.name = `${name}_unfold`;
                          this.layoutNamescope(name, true);
                        }
                      } else {
                        this.initGraphRectData();
                        this.loading.show = false;
                      }
                    }
                  }
                },
                (error) => {
                  this.loading.show = false;
                },
            )
            .catch(() => {
            // A non-Google Chrome browser may not work properly.
              this.loading.show = false;
              this.$bus.$emit('showWarmText', true);
            });
      }, 50);
    },
    /**
     * To obtain datavisual plugins
     */
    getDatavisualPlugins() {
      const params = {
        train_id: this.trainJobID,
      };
      RequestService.getDatavisualPlugins(params)
          .then((res) => {
            this.fileSearchBox.suggestions = [];
            if (
              !res ||
            !res.data ||
            !res.data.plugins ||
            !res.data.plugins.graph ||
            !res.data.plugins.graph.length
            ) {
              this.initOver = true;
              return;
            }
            const tags = res.data.plugins.graph;
            let hasFileSearchValue = false;
            tags.forEach((k) => {
              this.fileSearchBox.suggestions.push({
                value: k,
              });
              hasFileSearchValue =
              k === this.fileSearchBox.value || hasFileSearchValue;
            });
            if (!this.initOver) {
              this.initOver = true;
              this.fileSearchBox.value = tags.length ? tags[0] : '';
              this.queryGraphData();
            } else if (!hasFileSearchValue) {
              this.fileSearchBox.value = '';
            }
          })
          .catch(() => {
            this.fileSearchBox.suggestions = [];
            this.initOver = true;
            this.loading.show = false;
          });
    },
    /**
     * Process the data returned by the background interface.
     * @param {Array} nodes Current node array
     * @param {String} name Node name
     * @return {Array} Node array
     */
    dealAggregationNodes(nodes, name) {
      // A maximum of 10 subnodes can be displayed on an aggregation node.
      const aggregationNodeLimit = 10;
      const independentLayout =
        name && this.allGraphData[name]
          ? this.allGraphData[name].independent_layout
          : false;
      if (independentLayout && nodes && nodes.length > aggregationNodeLimit) {
        // The selected node must be included.
        let startIndex = 0;
        if (this.selectedNode.more) {
          startIndex = this.selectedNode.moreDirection
            ? Math.max(0, nodes.length - this.selectedNode.moreStart)
            : Math.max(0, this.selectedNode.moreStart - aggregationNodeLimit);
        } else {
          let nodeIndex = 0;
          nodes.some((node, index) => {
            if (node.name === this.selectedNode.name) {
              nodeIndex = index;
              return true;
            } else {
              return false;
            }
          });
          // The selected node must be included.
          startIndex = nodeIndex - (nodeIndex % 10);
        }
        // If the number of subnodes of the aggregation node is greater than the maximum number of nodes on the
        // aggregation node, a simulation node needs to be generated to replace other nodes.
        const ellipsisNum = Math.max(
            0,
            nodes.length - aggregationNodeLimit - startIndex,
        );
        nodes = nodes.slice(startIndex, startIndex + aggregationNodeLimit);
        if (startIndex !== 0) {
          const ellipsisNodeL = {
            name: `${name}/left/${startIndex} more...`,
            attr: {},
            input: {},
            output: {},
            proxy_input: {},
            proxy_output: {},
            type: '',
          };
          nodes.splice(0, 0, ellipsisNodeL);
        }
        if (startIndex + aggregationNodeLimit < nodes.length) {
          const ellipsisNode = {
            name: `${name}/right/${ellipsisNum} more...`,
            attr: {},
            input: {},
            output: {},
            proxy_input: {},
            proxy_output: {},
            type: '',
          };
          nodes.push(ellipsisNode);
        }
      }
      return nodes || [];
    },
    /**
     * Encapsulates graph data into dot data.
     * @return {String} dot string for packing graph data
     */
    packageGraphData() {
      const initSetting =
        'node[style="filled";fontsize="10px"];edge[fontsize="6px";];';
      return `digraph {${initSetting}${this.packageNodes()}${this.packageEdges()}}`;
    },
    /**
     * Encapsulates node data into dot data.
     * @param {String} name Name of the node to be expanded.
     * @return {String} dot String that are packed into all nodes
     */
    packageNodes(name) {
      const nodes = this.getChildNodesByName(name);
      let tempStr = '';
      nodes.forEach((node) => {
        const name = node.name.split('/').pop();
        // Different types of nodes are generated for different data types.
        if (node.type === 'aggregation_scope') {
          tempStr +=
            `<${node.name}>[id="${node.name}";` +
            `label="${name}";class="aggregation";` +
            `${
              node.isUnfold
                ? `shape="polygon";width=${node.size[0]};height=${node.size[1]};fixedsize=true;`
                : 'shape="octagon";'
            }];`;
        } else if (node.type === 'name_scope') {
          const fillColor = CommonProperty.graphColorArr[this.curColorIndex];
          this.curColorIndex = this.curColorIndex % 4;
          this.curColorIndex++;
          tempStr +=
            `<${node.name}>[id="${node.name}";fillcolor="${fillColor}";` +
            `shape="polygon";label="${name}";class="cluster";` +
            `${
              node.isUnfold
                ? `width=${node.size[0]};height=${node.size[1]};fixedsize=true;`
                : ''
            }];`;
        } else if (node.type === 'Const') {
          tempStr +=
            `<${node.name}>[id="${node.name}";label="${name}\n\n\n";` +
            `shape="circle";width="0.14";height="0.14";fixedsize=true;];`;
        } else {
          tempStr +=
            `<${node.name}>[id="${node.name}";shape="ellipse";` +
            `label="${name}";];`;
        }
        // A maximum of five virtual nodes can be displayed. Other virtual nodes are displayed in XXXmore.
        // The ID of the omitted aggregation node is analogNodesInput||analogNodeOutput^nodeId.
        // After the namespace or aggregation node is expanded, the virtual node does not need to be displayed.
        if (!this.allGraphData[node.name].isUnfold) {
          let keys = Object.keys(node.proxy_input || {});
          let target = node.name;
          let source = '';
          let isConst = false;
          for (let i = 0; i < Math.min(5, keys.length); i++) {
            source = keys[i];
            isConst = !!(
              this.allGraphData[keys[i]] &&
              this.allGraphData[keys[i]].type === 'Const'
            );
            const nodeStr = isConst
              ? `shape="circle";width="0.14";height="0.14";fixedsize=true;` +
                `label="${source.split('/').pop()}\n\n\n";`
              : `shape="Mrecord";label="${source.split('/').pop()}";`;

            tempStr +=
              `<${source}^${target}>[id="${source}^${target}";` +
              `${nodeStr}class="plain"];`;
          }
          if (keys.length > 5) {
            tempStr +=
              `<analogNodesInput^${target}>[id="analogNodesInput^` +
              `${target}";label="${keys.length - 5} more...";shape="Mrecord";` +
              `class="plain";];`;
          }

          keys = Object.keys(node.proxy_output || {});
          source = node.name;
          for (let i = 0; i < Math.min(5, keys.length); i++) {
            target = keys[i];
            isConst = !!(
              this.allGraphData[keys[i]] &&
              this.allGraphData[keys[i]].type === 'Const'
            );
            const nodeStr = isConst
              ? `shape="circle";width="0.14";height="0.14";fixedsize=true;` +
                `label="${target.split('/').pop()}\n\n\n";`
              : `shape="Mrecord";label="${target.split('/').pop()}";`;

            tempStr +=
              `<${target}^${source}>[id="${target}^${source}";` +
              `${nodeStr}class="plain";];`;
          }
          if (keys.length > 5) {
            tempStr +=
              `<analogNodesOutput^${source}>[id="analogNodesOutput^` +
              `${source}";shape="Mrecord";label="${keys.length - 5} more...";` +
              `class="plain";];`;
          }
        }
      });
      return tempStr;
    },
    /**
     * Encapsulates node data into dot data.
     * @param {String} name Name of the node to be expanded.
     * @return {String} dot string packaged by all edges
     */
    packageEdges(name) {
      const nodes = this.getChildNodesByName(name);
      let tempStr = '';
      const edges = [];
      // Construct the input and output virtual nodes and optimize the connection.
      const analogNodesInputId = `analogNodesInputOf${name}`;
      const analogNodesOutputId = `analogNodesOutputOf${name}`;
      let needAnalogInput = false;
      let needAnalogOutput = false;
      const unfoldIndependentScope = name
        ? this.allGraphData[name].independent_layout
        : false;
      nodes.forEach((node) => {
        // No input cable is required for the aggregation node and nodes in the aggregation node without namescoope.
        // When only aggregation nodes are encapsulated, input cables do not need to be considered.
        if (!unfoldIndependentScope) {
          const input = node.input || {};
          const keys = Object.keys(input);
          keys.forEach((key) => {
            if (input[key]) {
              // Cannot connect to the sub-nodes in the aggregation node and cannot be directly connected to the
              // aggregation node. It can only connect to the outer namespace of the aggregation node.
              // If there is no namespace in the outer layer, you do not need to connect cables.
              // Other connections are normal.
              let temp = key;
              if (input[key].independent_layout) {
                const list = key.split('/');
                list.splice(list.length - 2, 2);
                temp = list.join('/');
              }
              const source =
                this.findChildNamescope(temp, name) ||
                (temp ? analogNodesInputId : '');
              let target = node.name;
              if (node.independent_layout) {
                const list = node.name.split('/');
                list.splice(list.length - 2, 2);
                target = `${list.join('/')}_unfold`;
              }
              // The namespace is not nested.
              if (
                source &&
                target &&
                !target.includes(source.replace('_unfold', '') + '/') &&
                !source.includes(target.replace('_unfold', '') + '/')
              ) {
                if (!name || (name && source.startsWith(`${name}/`))) {
                  const obj = {
                    source: source,
                    target: target,
                    shape: input[key].shape,
                    edge_type: input[key].edge_type,
                    data_type: input[key].data_type,
                    count: 1,
                  };
                  edges.push(obj);
                } else {
                  // If it is connected to the outside of the namespace,
                  // it is connected to the virtual input and output node of the namespace.
                  // The connection line of the aggregation node is connected to the namespace of the aggregation node.
                  // If the namespace to be opened is to be opened, you need to delete it.
                  if (target.replace('_unfold', '') !== name) {
                    const obj = {
                      source: analogNodesInputId,
                      target: target,
                      shape: input[key].shape,
                      edge_type: input[key].edge_type,
                      data_type: input[key].data_type,
                      count: 1,
                    };
                    edges.push(obj);
                    needAnalogInput = true;
                  }
                }
              }
            }
          });
          // When the namespace is opened,
          // the line connected to the namespace is connected to the virtual input and output node of the namespace.
          // The aggregation node and its subnodes do not need to consider the situation where the output is connected
          // to the virtual output node.
          if (!node.independent_layout) {
            Object.keys(node.output || {}).forEach((key) => {
              if (!node.output[key].independent_layout) {
                const source = node.name;
                const target =
                  this.findChildNamescope(key, name) || analogNodesOutputId;
                if (source && target) {
                  if (
                    name &&
                    !target.startsWith(`${name}/`) &&
                    source !== name
                  ) {
                    const obj = {
                      source: source,
                      target: analogNodesOutputId,
                      shape: node.output[key].shape,
                      edge_type: node.output[key].edge_type,
                      data_type: node.output[key].data_type,
                      count: 1,
                    };
                    edges.push(obj);
                    needAnalogOutput = true;
                  }
                }
              }
            });
          }
        }
        // Virtual node data
        // The expanded namespace or aggregation node does not need to display virtual nodes.
        if (!this.allGraphData[node.name].isUnfold) {
          let keys = Object.keys(node.proxy_input || {});
          for (let i = 0; i < Math.min(5, keys.length); i++) {
            const target = node.name;
            const source = keys[i];
            const obj = {
              source: `${source}^${target}`,
              target: target,
              shape: node.proxy_input[keys[i]].shape,
              edge_type: node.proxy_input[keys[i]].edge_type,
              data_type: node.proxy_input[keys[i]].data_type,
              count: 1,
            };
            edges.push(obj);
          }
          if (keys.length > 5) {
            const obj = {
              source: `analogNodesInput^${node.name}`,
              target: node.name,
              shape: [],
              edge_type: '',
              data_type: '',
              count: 1,
            };
            edges.push(obj);
          }

          keys = Object.keys(node.proxy_output || {});
          for (let i = 0; i < Math.min(5, keys.length); i++) {
            const source = node.name;
            const target = keys[i];
            const obj = {
              source: source,
              target: `${target}^${source}`,
              shape: node.proxy_output[keys[i]].shape,
              edge_type: node.proxy_output[keys[i]].edge_type,
              data_type: node.proxy_output[keys[i]].data_type,
              count: 1,
            };
            edges.push(obj);
          }
          if (keys.length > 5) {
            const obj = {
              source: node.name,
              target: `analogNodesOutput^${node.name}`,
              shape: [],
              edge_type: '',
              data_type: '',
              count: 1,
            };
            edges.push(obj);
          }
        }
      });

      // Add the virtual input/output node. The aggregation node does not need to be configured.
      if (name && !this.allGraphData[name].independent_layout) {
        if (needAnalogInput) {
          tempStr +=
            `{rank=min;<${analogNodesInputId}>[shape="circle";` +
            `id="${analogNodesInputId}";fixedsize=true;width=0.02;label="";` +
            `class="edge-point"]};`;
        }
        if (needAnalogOutput) {
          tempStr +=
            `{rank=max;<${analogNodesOutputId}>[shape="circle";` +
            `id="${analogNodesOutputId}";width=0.02;fixedsize=true;` +
            `label="";class="edge-point"]};`;
        }
      }

      this.uniqueEdges(edges);
      edges.forEach((edge) => {
        const suffix = edge.edge_type === 'control' ? '_control' : '';
        tempStr +=
          `<${edge.source}>-><${edge.target}>[id="${edge.source}->` +
          `${edge.target}${suffix}";label="${this.getEdgeLabel(edge)}";` +
          `${edge.edge_type === 'control' ? 'style=dashed' : ''}];`;
      });
      return tempStr;
    },
    /**
     * Obtain the label of the edge
     * @param {Object} edge Edge Object
     * @return {String} Edge label
     */
    getEdgeLabel(edge) {
      // The label is not displayed on the control edge
      if (edge.edge_type === 'control') {
        return '';
      }
      let label = '';
      if (!edge.count || edge.count === 1) {
        if (edge.shape && edge.shape.length) {
          const flag = edge.shape.some((i) => {
            return typeof i !== 'number';
          });
          if (flag) {
            label = `tuple(${edge.shape.length} items)`;
          } else {
            label = `${edge.data_type} ${edge.shape.join('×')}`;
          }
        }
      } else {
        label = `${edge.count}tensors`;
      }
      return label;
    },
    /**
     * Obtains the subnode data of the namespace through the namespace name.
     * @param {String} name Namespace name.
     * @return {Array} Subnode array of the namespace.
     */
    getChildNodesByName(name) {
      const nameList = name
        ? this.allGraphData[name].children
        : this.firstFloorNodes;
      const nodes = nameList.map((i) => {
        return this.allGraphData[i];
      });
      return nodes;
    },
    /**
     * Find the node path that exists in the current namescoope through the node path.
     * @param {String} name Target node name
     * @param {String} namescope Namespace Name
     * @return {String} Namespace node of the namespace.
     */
    findChildNamescope(name, namescope) {
      if (!namescope) {
        return name.split('/')[0];
      } else {
        if (name.startsWith(namescope)) {
          const length = namescope.split('/').length;
          return name
              .split('/')
              .slice(0, length + 1)
              .join('/');
        } else {
          return null;
        }
      }
    },
    /**
     * Multiple edges with the same source and target are combined into one.
     * @param {Array} edges Array of edge data.
     */
    uniqueEdges(edges) {
      for (let i = 0; i < edges.length - 1; i++) {
        for (let j = i + 1; j < edges.length; j++) {
          const isSame =
            edges[i].source === edges[j].source &&
            edges[i].target === edges[j].target &&
            edges[i].edge_type === edges[j].edge_type;
          if (isSame) {
            edges[i].count += edges[j].count;
            edges.splice(j--, 1);
          }
        }
      }
    },
    /**
     * 1. Encapsulating the namespace generated by the graphTemp dom
     * 2. Replace the corresponding node in graphTemp with the existing namespace node in subgraphTemp.
     * 3. Move the namespace dom generated in graphTemp to subgraphTemp for storage.
     * 4. Use graphTemp to generate the dom of the new namespace.
     * @param {String} name Name of the namespace to be expanded.
     */
    dealNamescopeTempGraph(name) {
      const type = this.allGraphData[name].type;
      const classText =
        type === 'aggregation_scope'
          ? 'node cluster aggregation'
          : 'node cluster';
      const idStr = '#graphTemp #graph0 ';
      let fillColor = type === 'aggregation_scope' ? '#fff2d4' : '#ffe4d6';
      const curColorIndex = (name.split('/').length - 1) % 4;
      if (type === 'name_scope') {
        fillColor = CommonProperty.graphColorArr[curColorIndex];
      }

      const graphTemp = d3.select(idStr).node();
      let boxTemp = graphTemp.getBBox();

      // Create a namespace node and add it to graphTemp.
      const g = d3
          .select(idStr)
          .insert('g')
          .attr('id', `${name}_unfold`)
          .attr('class', classText)
          .attr('style', `fill:${fillColor};`);
      g.append('title').text(name);
      g.node().appendChild(
          d3
              .select('#graphTemp #graph0>text')
              .attr('y', boxTemp.y - 10)
              .node(),
      );
      // Move all the subnodes of the namespace to the created namespace node.
      Array.prototype.forEach.call(
          document.querySelector(idStr).querySelectorAll('g'),
          (node) => {
            if (node.id !== g.node().id) {
            // The title of all virtual nodes needs to be reset.
              if (Array.prototype.includes.call(node.classList, 'plain')) {
                const title = node.querySelector('title');
                title.textContent = title.textContent.split('^')[0];
              }
              node.setAttribute('transform', 'translate(0,0)');
              g.node().appendChild(node);
            }
          },
      );
      // Add a rectangle to the created namespace node as the border of the namespace.
      g.insert('rect', 'title')
          .attr('style', `fill:${fillColor};`)
          .attr('stroke', 'rgb(167, 167, 167)')
          .attr('x', g.node().getBBox().x - this.frameSpace)
          .attr('y', g.node().getBBox().y - this.frameSpace)
          .attr('width', g.node().getBBox().width + this.frameSpace * 2)
          .attr('height', g.node().getBBox().height + this.frameSpace * 2);

      boxTemp = d3
          .select(`${idStr}g[id="${name}_unfold"]`)
          .node()
          .getBBox();
      // After the namespace dom is successfully encapsulated, set the related data of the data object.
      this.allGraphData[name].isUnfold = true;
      this.allGraphData[name].size = [boxTemp.width / 72, boxTemp.height / 72];

      if (d3.select(`#subgraphTemp svg`).size()) {
        // Migrate the dom file in subgraph to the new namescope file.
        const nodeTemp = document.querySelector('#subgraphTemp #graph0 g');
        const name = nodeTemp.id.replace('_unfold', '');
        const node = document.querySelector(`#graphTemp g[id="${name}"]`);
        const box = node.getBBox();
        const boxTemp = nodeTemp.getBBox();
        const translateStr = `translate(${box.x - boxTemp.x},${box.y -
          boxTemp.y})`;
        nodeTemp.setAttribute('transform', translateStr);
        node.parentNode.appendChild(nodeTemp);
        document.querySelector('#subgraphTemp svg').remove();
        node.remove();
      }
      // Delete unnecessary g nodes from graphTemp.
      const domList = document.querySelector('#graphTemp #graph0').children;
      for (let i = 0; i < domList.length; i++) {
        if (domList[i].id !== `${name}_unfold`) {
          domList[i--].remove();
        }
      }

      this.generateIOBus(name);
      // Move the DOM station in graphTemp to subgraph, and then graphTemp continue to lay out the outer graph.
      document
          .querySelector('#subgraphTemp')
          .appendChild(document.querySelector('#graphTemp svg'));
      this.transplantChildrenDom(name);
      this.layoutController(name);
    },
    /**
     * Move the namespace dom generated in graphTemp to subgraphTemp for storage.
     * @param {String} name Name of the namespace to be expanded.
     */
    transplantChildrenDom(name) {
      let nameList = [];
      let idStr = '#subgraphTemp ';
      if (name) {
        nameList = this.allGraphData[name].children;
      } else {
        idStr = '#graph ';
        nameList = this.firstFloorNodes;
      }
      nameList.forEach((i) => {
        const nodeData = this.allGraphData[i];
        const flag =
          (nodeData.type === 'name_scope' ||
            nodeData.type === 'aggregation_scope') &&
          nodeData.isUnfold;
        if (flag) {
          // Place the dom character string in graphTemp and then move it to the corresponding node of subgraphTemp.
          document.querySelector('#graphTemp').innerHTML = nodeData.html;
          const node = document.querySelector(`${idStr}g[id="${i}"]`);
          const nodeTemp = document.querySelector(
              `#graphTemp #graph0 g[id="${i}_unfold"]`,
          );
          if (node && nodeTemp) {
            const box = node.getBBox();
            const boxTemp = nodeTemp.getBBox();
            const translateStr = `translate(${box.x - boxTemp.x},${box.y -
              boxTemp.y})`;
            nodeTemp.setAttribute('transform', translateStr);
            node.parentNode.appendChild(nodeTemp);
            node.remove();
          }
          document.querySelector('#graphTemp svg').remove();
        }
      });
      if (name) {
        this.allGraphData[name].html = document.querySelector(
            `#subgraphTemp svg`,
        ).outerHTML;
      }
    },
    /**
     * Add the input and output buses of the namespace.
     * @param {String} name Name of the namespace to be expanded.
     */
    generateIOBus(name) {
      if (d3.select(`#graphTemp g[id="analogNodesInputOf${name}"]`).size()) {
        this.generateEdge(
            {source: `${name}_unfold`, target: `analogNodesInputOf${name}`},
            name,
            'input',
        );
      }
      if (d3.select(`#graphTemp g[id="analogNodesOutputOf${name}"]`).size()) {
        this.generateEdge(
            {source: `analogNodesOutputOf${name}`, target: `${name}_unfold`},
            name,
            'output',
        );
      }
    },
    /**
     * Encapsulates the data of the namespace to be expanded.
     * @param {String} name Name of the namespace to be expanded.
     * @return {String} dot string that is used to package the data of the namespace.
     */
    packageNamescope(name) {
      const nodeStr = this.packageNodes(name);
      const edgeStr = this.packageEdges(name);
      const initSetting =
        `node[style="filled";fontsize="10px";];` + `edge[fontsize="6px";];`;
      const dotStr =
        `digraph {${initSetting}label="${name.split('/').pop()}";` +
        `${nodeStr}${edgeStr}}`;
      return dotStr;
    },
    /**
     * Close the expanded namespace.
     * @param {String} name The name of the namespace to be closed.
     */
    deleteNamespace(name) {
      this.loading.info = this.$t('graph.queryLoading');
      this.loading.show = true;
      setTimeout(() => {
        this.packageDataToObject(name, false);
        this.layoutController(name);
        if (this.selectedNode.more) {
          this.queryGraphData(name);
        }
      }, 150);
    },
    /**
     * Controls the invoking method of the next step.
     * @param {String} name Name of the namespace to be expanded.
     */
    layoutController(name) {
      if (name.includes('/')) {
        const subPath = name
            .split('/')
            .slice(0, -1)
            .join('/');
        this.layoutNamescope(subPath, true);
      } else {
        const svg = document.querySelector('#graph svg');
        if (svg) {
          svg.remove();
        }
        const dot = this.packageGraphData();
        this.initGraph(dot);
      }
    },
    /**
     * Generate a edge in graph.
     * @param {Object} edge Edge data
     * @param {String} name Namespace to which the edge belongs.
     * @param {String} port Indicates the input/output type of a edge.
     */
    generateEdge(edge, name, port) {
      const points = this.getEdgePoints(edge, port);
      const text = this.getEdgeLabel(edge);
      const g = d3
          .select(`#graphTemp g#graph0${name ? ` g[id="${name}_unfold"]` : ''}`)
          .append('g')
          .attr(
              'id',
              `${edge.source.replace('_unfold', '')}->${edge.target.replace(
                  '_unfold',
                  '',
              )}`,
          )
          .attr(
              'class',
              `edge${edge.edge_type === 'aggregation' ? ' hide' : ''}`,
          );
      g.append('title').text(text);
      // Because the edges need to be highlighted, marker requires one side of each side.
      const marker = g.append(`marker`);
      marker
          .attr('id', `${name + port}marker`)
          .attr('refX', 6)
          .attr('refY', 3)
          .attr('markerWidth', 8)
          .attr('markerHeight', 6)
          .attr('orient', 'auto');
      marker
          .append('path')
          .attr('d', 'M1,1 L1,5 L6,3 z')
          .attr('fill', 'rgb(167, 167, 167)')
          .attr('stroke', 'rgb(167, 167, 167)');
      g.append('path')
          .attr('stroke', 'rgb(167, 167, 167)')
          .attr('stroke-width', 1)
          .attr(
              'stroke-dasharray',
              `${edge.edge_type === 'control' ? '5,2' : '0'}`,
          )
          .attr('marker-end', `url(#${name + port}marker)`)
          .attr(
              'd',
              `M${points[0].x},${points[0].y}L${points[1].x},${points[1].y}`,
          );
      g.append('text')
          .attr('text-anchor', 'middle')
          .attr('font-family', 'Times,serif')
          .attr('font-size', '6px')
          .attr('fill', '#000000')
          .attr('x', (points[0].x + points[1].x) / 2)
          .attr('y', (points[0].y + points[1].y) / 2)
          .text(text);
    },
    /**
     * Obtain the location data of the source and target edges.
     * @param {Object} edge Edge data
     * @param {String} port Indicates the input/output type of a edge.
     * @return {Array} Coordinate array of the start point and end point of the edge.
     */
    getEdgePoints(edge, port) {
      const source = d3
          .select(`#graphTemp g[id="${edge.source}"]`)
          .node()
          .getBBox();
      const target = d3
          .select(`#graphTemp g[id="${edge.target}"]`)
          .node()
          .getBBox();
      source.points = this.getBoxPoints(source);
      target.points = this.getBoxPoints(target);
      // The input bus is at the top of the namespace, and the output bus is at the bottom of the namespace.
      if (port === 'input') {
        return [source.points.top, target.points.top];
      } else {
        return [source.points.bottom, target.points.bottom];
      }
    },
    /**
     * Obtains the coordinates of the top and button in the node box.
     * @param {Object} box Edge data
     * @return {Object} Object that contains the top and bottom coordinates of the box.
     */
    getBoxPoints(box) {
      const points = {
        top: {
          x: box.x + box.width / 2,
          y: box.y,
        },
        bottom: {
          x: box.x + box.width / 2,
          y: box.y + box.height,
        },
      };
      return points;
    },
    /**
     * Obtains the transform data of a node.
     * @param {Object} node Node dom data
     * @return {Object} transform data of a node
     */
    getTransformData(node) {
      if (!node) {
        return [];
      }
      const transformData = node.getAttribute('transform');
      const attrObj = [];
      if (transformData) {
        const lists = transformData.trim().split(' ');
        lists.forEach((item) => {
          item = item.trim();
          if (item) {
            const index1 = item.indexOf('(');
            const index2 = item.indexOf(')');
            const params = item
                .substring(index1 + 1, index2)
                .split(',')
                .map((i) => {
                  return parseFloat(i) || 0;
                });
            attrObj[item.substring(0, index1)] = params;
          }
        });
      }
      return attrObj;
    },
    /**
     * Selecting a node
     * @param {String} dblclick Click Type
     */
    selectNode(dblclick) {
      const graphDom = document.querySelector('#graph #graph0');
      window.getSelection().removeAllRanges();
      d3.selectAll(
          '.node polygon, .node ellipse, .node rect, .node path',
      ).classed('selected', false);
      const path = this.selectedNode.name.split('^');
      const node = {};
      let id = path[0].replace('_unfold', '');
      id = this.allGraphData[id].isUnfold ? `${id}_unfold` : id;
      node.eld3 = d3.select(`#graph g[id="${id}"]`);
      node.el = node.eld3.node();
      graphDom.style.transition = '';
      if ((dblclick || path.length > 1) && node.el) {
        this.selectNodePosition(node, dblclick);
      }
      node.eld3
          .select('polygon, rect, Mrecord, ellipse, path')
          .classed('selected', true);
      this.setNodeData();
    },
    /**
     * The node information of the selected node is displayed and highlighted.
     */
    setNodeData() {
      this.selectedNode.info = {
        input: [],
        inputControl: [],
        output: [],
        outputControl: [],
        Attributes: [],
      };
      this.selectedNode.showControl = {
        input: true,
        output: true,
      };
      const path = this.selectedNode.name.split('^');
      const select = this.allGraphData[path[0].replace('_unfold', '')]
        ? [this.allGraphData[path[0].replace('_unfold', '')]]
        : [];
      const nodes = d3.selectAll('#graph g.node');
      const node = d3.select(`#graph g[id="${this.selectedNode.name}"]`);
      const text = node.select('text').node()
        ? node.select('text').node().innerText ||
          node.select('text').node().textContent ||
          ''
        : '';
      const nodeId = node.node()
        ? node
            .node()
            .id.replace(/_unfold$/g, '')
            .split('^')
        : [];
      const filter = nodes.nodes().filter((k) => {
        const nodeItem = d3.select(k);
        const nodeText = nodeItem.select('text').node()
          ? nodeItem.select('text').node().innerText ||
            nodeItem.select('text').node().textContent ||
            ''
          : '';
        let path = false;
        nodeItem
            .node()
            .id.split('^')
            .forEach((i) => {
              path = nodeId.filter((j) => j === i).length ? true : path;
            });
        return nodeText === text && path;
      });
      filter.forEach((k) => {
        if (k.childNodes) {
          k.childNodes.forEach((i) => {
            if (
              i.tagName === 'polygon' ||
              i.tagName === 'ellipse' ||
              i.tagName === 'path' ||
              i.tagName === 'rect'
            ) {
              i.setAttribute('class', 'selected');
            }
          });
        }
      });
      if (select.length && select[0].name.indexOf('more') === -1) {
        this.selectedNode.show = true;
        this.selectedNode.name = select[0].name;
        this.selectedNode.title = select[0].name.replace('_unfold', '');
        this.selectedNode.type =
          select[0].type === 'name_scope' ||
          select[0].type === 'aggregation_scope'
            ? ''
            : select[0].type;
        this.selectedNode.countShow =
          select[0].type === 'name_scope' ||
          select[0].type === 'aggregation_scope';
        this.selectedNode.count = select[0].subnode_count;
        Object.keys(select[0].attr).forEach((key) => {
          this.selectedNode.info.Attributes.push({
            name: key,
            value: select[0].attr[key],
          });
        });
        Object.keys(select[0].input).forEach((key) => {
          const value = this.getEdgeLabel(select[0].input[key]);
          if (select[0].input[key].edge_type !== 'control') {
            this.selectedNode.info.input.push({
              name: key,
              value: value,
            });
          } else {
            this.selectedNode.info.inputControl.push({
              name: key,
              value: value,
            });
          }
        });
        Object.keys(select[0].output).forEach((key) => {
          const value = this.getEdgeLabel(select[0].output[key]);
          if (select[0].output[key].edge_type !== 'control') {
            this.selectedNode.info.output.push({
              name: key,
              scope: select[0].output[key].scope,
              value: value,
            });
          } else {
            this.selectedNode.info.outputControl.push({
              name: key,
              scope: select[0].output[key].scope,
              value: value,
            });
          }
        });
        this.selectedNode.info.output_i = select[0].output_i;
        this.highLightEdges(select[0]);
      } else {
        this.selectedNode.show = false;
        this.selectedNode.name = '';
        this.selectedNode.title = '';
        this.selectedNode.type = '';
      }
    },
    /**
     * The position is offset to the current node in the center of the screen.
     * @param {Object} node Selected Node
     * @param {Boolean} dblclick Double-click
     */
    selectNodePosition(node, dblclick) {
      const graphDom = document.querySelector('#graph #graph0');
      node.offsetLeft = node.el.getBoundingClientRect().left;
      node.offsetTop = node.el.getBoundingClientRect().top;
      node.initWidth = node.el.getBoundingClientRect().width;
      node.initHeight = node.el.getBoundingClientRect().height;
      const screenChange = {
        x:
          node.offsetLeft -
          (this.svg.offsetLeft + this.svg.initWidth / 2) +
          node.initWidth / 2,
        y:
          node.offsetTop -
          (this.svg.offsetTop + this.svg.initHeight / 2) +
          node.initHeight / 2,
      };
      this.graphDom.transform = {
        x:
          this.graphDom.transform.x -
          screenChange.x * (this.svg.viewWidth / this.graphDom.initWidth),
        y:
          this.graphDom.transform.y -
          screenChange.y * (this.svg.viewHeight / this.graphDom.initHeight),
        k: this.graphDom.transform.k,
      };
      graphDom.attributes.transform.value = `translate(${this.graphDom.transform.x},
      ${this.graphDom.transform.y}) scale(${this.graphDom.transform.k})`;
      const transition =
        dblclick === 'unfoldScope'
          ? 0
          : Math.min(
              Math.abs(screenChange.x) * 2,
              Math.abs(screenChange.y) * 2,
              800,
          );
      graphDom.style.transition = `${transition / 1000}s`;
      graphDom.style['transition-timing-function'] = 'linear';
      setTimeout(() => {
        graphDom.style.transition = '';
      }, transition);
      let end = 0;
      this.bigMapPositionChange();
      const timer = setInterval(() => {
        this.bigMapPositionChange();
        end += 1;
        if (end > transition) {
          clearInterval(timer);
        }
      }, 1);
    },
    /**
     * Highlight the input and output cables related to the selected node.
     * @param {Object} node Data of the selected node
     */
    highLightEdges(node) {
      // Click an operator or namespace to highlight the connection between the operator or namespace and the node and
      // virtual node.
      // Click the aggregation node or its subnodes to highlight the connection between the node and the virtual
      // node and the connection between the namespace and other nodes.
      const edges = {};
      const input = node.input || {};
      const output = node.output || {};
      const name = this.findExsitNode(node.name);
      // Connects to the edge of the actual node.
      if (name) {
        Object.keys(input).forEach((key) => {
          const source = this.findExsitNode(key);
          if (source) {
            edges[`${source}->${name}`] = {
              source: source,
              target: name,
              edge_type: input[key].edge_type || '',
            };
          }
        });
        Object.keys(output).forEach((key) => {
          const target = this.findExsitNode(key);
          if (target) {
            edges[`${name}->${target}`] = {
              source: name,
              target: target,
              edge_type: output[key].edge_type || '',
            };
          }
        });
      }

      if (!node.isUnfold) {
        // Connects to the edge of a virtual node.
        let keys = Object.keys(node.proxy_input || {});
        for (let i = 0; i < Math.min(5, keys.length); i++) {
          const nameTemp = `${keys[i]}^${node.name}`;
          edges[`${nameTemp}->${node.name}`] = {
            source: nameTemp,
            target: node.name,
            edge_type: node.proxy_input[keys[i]].edge_type || '',
          };
        }
        if (keys.length > 5) {
          const nameTemp = `analogNodesInput^${node.name}`;
          edges[`${nameTemp}->${node.name}`] = {
            source: nameTemp,
            target: node.name,
            edge_type: '',
          };
        }
        keys = Object.keys(node.proxy_output || {});
        for (let i = 0; i < Math.min(5, keys.length); i++) {
          const nameTemp = `${keys[i]}^${node.name}`;
          edges[`${node.name}->${nameTemp}`] = {
            source: node.name,
            target: nameTemp,
            edge_type: node.proxy_output[keys[i]].edge_type || '',
          };
        }
        if (keys.length > 5) {
          const nameTemp = `analogNodesOutput^${node.name}`;
          edges[`${node.name}->${nameTemp}`] = {
            source: node.name,
            target: nameTemp,
            edge_type: '',
          };
        }
      }

      // The line of the virtual node does not need to be managed.
      const edgesList = {};
      Object.keys(edges).forEach((key) => {
        if (key.includes('^')) {
          edgesList[key] = edges[key];
        } else {
          const suffix = edges[key].edge_type === 'control' ? '_control' : '';
          const [source, target] = key.split('->');
          const list = [];
          const sourceList = source.split('/');
          const targetList = target.split('/');
          const lengthMin = Math.min(sourceList.length, targetList.length);
          let commonIndex = -1;
          // Find the same prefix.
          for (let i = 0; i < lengthMin; i++) {
            if (
              sourceList.slice(0, i + 1).join('/') ===
              targetList.slice(0, i + 1).join('/')
            ) {
              commonIndex = i;
            }
          }
          // To split the side into several sections
          for (let i = commonIndex + 2; i < sourceList.length; i++) {
            const source = sourceList.slice(0, i + 1).join('/');
            const target = sourceList.slice(0, i).join('/');
            list.push(`${source}->analogNodesOutputOf${target}${suffix}`);
            list.push(`analogNodesOutputOf${target}->${target}`);
          }
          list.push(
              `${sourceList.slice(0, commonIndex + 2).join('/')}->` +
              `${targetList.slice(0, commonIndex + 2).join('/')}${suffix}`,
          );
          for (let i = commonIndex + 2; i < targetList.length; i++) {
            const source = targetList.slice(0, i).join('/');
            const target = targetList.slice(0, i + 1).join('/');
            list.push(`${source}->analogNodesInputOf${source}`);
            list.push(`analogNodesInputOf${source}->${target}${suffix}`);
          }
          // Deduplication and encapsulation of data
          for (let i = 0; i < list.length; i++) {
            const [sourceTemp, targetTemp] = list[i].split('->');
            // Remove the situation where the aggregation node and node are in the same namespace.
            if (
              !(
                sourceTemp.startsWith(targetTemp + '/') ||
                targetTemp.startsWith(sourceTemp + '/')
              )
            ) {
              edgesList[`${sourceTemp}->${targetTemp}`] = {
                source: sourceTemp,
                target: targetTemp,
                edge_type: edges[key].edge_type,
              };
            }
          }
        }
      });

      d3.selectAll('#graph g.edge').classed('highlighted', false);
      Object.keys(edgesList).forEach((key) => {
        d3.select(`#graph g[id="${key}"]`).classed('highlighted', true);
      });
    },
    /**
     * Find the existing namespace based on the node name.
     * @param {String} name Data of the selected node
     * @return {String} Find the existing node by name.
     */
    findExsitNode(name) {
      let subPsth = '';
      const paths = name.split('/');
      for (let i = paths.length; i > 0; i--) {
        const path = paths.slice(0, i).join('/');
        if (this.allGraphData[path]) {
          subPsth = path;
          break;
        }
      }
      if (subPsth && this.allGraphData[subPsth]) {
        // The virtual node and its subnodes need to return their namespaces.
        if (this.allGraphData[subPsth].independent_layout) {
          subPsth = subPsth
              .split('/')
              .slice(0, -1)
              .join('/');
        }
      }
      return subPsth;
    },
    /**
     * Processes its own and corresponding child node data when expanding or closing namespaces.
     * @param {String} name Data of the selected node
     * @param {Boolean} toUnfold Expand or Not
     * @param {Array} nodes Node array
     */
    packageDataToObject(name, toUnfold, nodes) {
      // If there is no name, it indicates the first layer.
      if (!name) {
        this.allGraphData = {};
        this.firstFloorNodes = [];
        nodes.forEach((node) => {
          node.isUnfold = false;
          node.children = [];
          node.size = [];
          node.html = '';
          this.allGraphData[node.name] = node;
          this.firstFloorNodes.push(node.name);
        });
      } else {
        // Expand the namespace and encapsulate its child node data.
        if (toUnfold) {
          this.allGraphData[name].isUnfold = true;
          nodes.forEach((node) => {
            node.isUnfold = false;
            node.children = [];
            node.size = [];
            node.html = '';
            this.allGraphData[node.name] = node;
            this.allGraphData[name].children.push(node.name);
          });
        } else {
          // Close the namespace and delete all child node data.
          const allChildren = Object.keys(this.allGraphData).filter((key) => {
            return key.startsWith(`${name}/`);
          });
          allChildren.forEach((key) => {
            delete this.allGraphData[key];
          });

          this.allGraphData[name].isUnfold = false;
          this.allGraphData[name].children = [];
          this.allGraphData[name].size = [];
          this.allGraphData[name].html = '';
        }
      }
    },
    /**
     * The drop-down list box of the search drop-down list box is controlled.
     * @param {Object} event Operation event of a component.
     */
    selectBoxVisibleTriggle(event) {
      setTimeout(() => {
        document.querySelector('.el-autocomplete-suggestion').style.display =
          event.type === 'blur' ? 'none' : 'block';
      }, 300);
    },
    /**
     * file select change
     */
    fileChange() {
      this.selectedNode = {
        info: {
          inputControl: [],
          input: [],
          outputControl: [],
          output: [],
          Attributes: [],
        },
        showControl: {
          input: true,
          output: true,
        },
      };
      this.clickScope = {};
      this.searchBox.value = '';
      Object.keys(this.allGraphData).forEach((key) => {
        delete this.allGraphData[key];
      });
      d3.select('#graph svg').remove();
      this.firstFloorNodes = [];
      this.queryGraphData();
    },
    /**
     * refresh select list
     * @param {Boolean} expanded Should get data visual plugins or not.
     */
    getSelectList(expanded) {
      if (expanded) {
        this.getDatavisualPlugins();
      }
    },
    /**
     * The search drop-down list box displays the matched data by entering data.
     * @param {String} content Input parameters
     * @param {Object} callback Callback Function
     */
    searchNodesNames(content, callback) {
      if (!this.trainJobID) {
        callback([]);
        return;
      }
      const params = {
        search: content,
        train_id: this.trainJobID,
        tag: this.fileSearchBox.value,
        offset: 0,
        limit: 1000,
      };
      RequestService.searchNodesNames(params)
          .then(
              (response) => {
                if (response && response.data) {
                  const names = response.data.names || response.data;
                  callback(
                      names.map((name) => {
                        return {value: name};
                      }),
                  );
                }
              },
              (e) => {
                callback([]);
                this.loading.show = false;
              },
          )
          .catch((e) => {
            callback([]);
            this.$message.error(this.$t('public.dataError'));
          });
    },
    /**
     * Search for all data of a specific node and its namespace.
     * @param {Object} option Selected node data object
     */
    querySingleNode(option) {
      this.selectedNode.name = option.value;
      this.selectedNode.more = false;
      // If a node exists on the map, select the node.
      if (this.allGraphData[option.value]) {
        // If the namespace or aggregation node is expanded, you need to close it and select
        if (!this.allGraphData[option.value].isUnfold) {
          this.selectNode('unfold');
        } else {
          this.dealDoubleClick(option.value);
        }
      } else {
        // If the node does not exist and is not a subnode of the aggregation node,
        // directly invoke the background for query.
        // If the node does not exist and is a subnode of the aggregation node, and the aggregation node is not
        // expanded, directly invoke the background to check the node.
        // If the node does not exist and is a child node in the aggregation node,
        // and the aggregation node is expanded but is not displayed on the diagram, you need to zoom out the
        // aggregated node, query the aggregation node again, and intercept the node array again.
        const params = {
          name: option.value,
          train_id: this.trainJobID,
          tag: this.fileSearchBox.value,
        };
        this.loading.info = this.$t('graph.searchLoading');
        this.loading.show = true;
        RequestService.querySingleNode(params)
            .then(
                (response) => {
                  if (response && response.data && response.data.children) {
                    const [data, nameScopeIsUnfold] = this.findStartUnfoldNode(
                        response.data.children,
                    );
                    if (data) {
                      if (nameScopeIsUnfold) {
                        // If the aggregation node is expanded but is not displayed on the diagram,
                        // you need to zoom out the aggregated node, query the aggregation node again,
                        // and intercept the node array again.
                        this.dealDoubleClick(data.scope_name);
                        this.selectedNode.name = option.value;
                      }
                      this.dealAutoUnfoldNamescopesData(data);
                    }
                  }
                },
                (e) => {
                  this.loading.show = false;
                },
            )
            .catch((e) => {
              this.$message.error(this.$t('public.dataError'));
            });
      }
    },
    /**
     * Processes all data of the queried node and the namespace to which the node belongs.
     * @param {Object} data All data of the node and the namespace to which the node belongs
     * @return {Object} The data object of the namespace to expand.
     */
    dealAutoUnfoldNamescopesData(data) {
      if (!data.scope_name) {
        return this.dealAutoUnfoldNamescopesData(data.children);
      } else {
        if (this.allGraphData[data.scope_name].isUnfold) {
          return this.dealAutoUnfoldNamescopesData(data.children);
        } else {
          // If the namespace is a namespace and the number of subnodes exceeds the upper limit,
          // an error is reported and the namespace is selected.
          if (
            this.allGraphData[data.scope_name].type === 'name_scope' &&
            data.nodes.length > this.nodesCountLimit
          ) {
            this.selectedNode.name = data.scope_name;
            this.querySingleNode({value: data.scope_name});
            this.selectNode('unfold');
            this.$message.error(this.$t('graph.tooManyNodes'));
            this.$nextTick(() => {
              this.loading.show = false;
            });
          } else {
            // Normal expansion
            const nodes = this.dealAggregationNodes(
                data.nodes,
                this.allGraphData[data.scope_name].type,
            );
            this.packageDataToObject(data.scope_name, true, nodes);
            if (data.children.scope_name) {
              this.dealAutoUnfoldNamescopesData(data.children);
            } else {
              this.layoutNamescope(data.scope_name, true);
            }
          }
        }
      }
    },
    /**
     * Queries the first layer namespace to be expanded for a search node.
     * @param {Object} data All data of the node and the namespace to which the node belongs
     * @return {Array} First namespace to be expanded
     */
    findStartUnfoldNode(data) {
      if (data && data.scope_name) {
        if (this.allGraphData[data.scope_name].isUnfold) {
          if (
            data.nodes.some((node) => {
              return node.name === this.selectedNode.name;
            })
          ) {
            return [data, true];
          } else {
            return this.findStartUnfoldNode(data.children);
          }
        } else {
          return [data, false];
        }
      } else {
        return [null, null];
      }
    },
    /**
     * Initialize the svg, width and height of the small image, and transform information.
     */
    initGraphRectData() {
      // graph attribute
      const graphHtml = document.querySelector('#graph');

      // svg attribute
      const svg = graphHtml.querySelector('#graph svg');
      if (!svg) {
        return;
      }
      const svgRect = svg.getBoundingClientRect();
      this.svg.initWidth = svgRect.width; // svg width
      this.svg.initHeight = svgRect.height; // svg high
      this.svg.offsetLeft = svgRect.left; // svg Distance to the left of the window
      this.svg.offsetTop = svgRect.top; // svg Distance from the upper part of the window
      this.svg.viewWidth = parseFloat(
          svg.attributes.viewBox.value.split(' ')[2],
      ); // svg viewbox width
      this.svg.viewHeight = parseFloat(
          svg.attributes.viewBox.value.split(' ')[3],
      ); // The viewbox of the svg is high.

      // Attributes of smallContainer
      const smallContainer = document.querySelector('#small-container');

      // Attributes of smallMap
      const smallMap = document.querySelector('#small-map');

      // Reset the length and width of the smallResize and locate the fault.
      const smallResize = document.querySelector('#small-resize');
      this.smallResize.width = this.smallResize.initWidth =
        smallContainer.offsetWidth - 2; // Initial width of the thumbnail frame
      this.smallResize.height = this.smallResize.initHeight =
        smallContainer.offsetHeight - 2; // The initial height of the thumbnail frame is high.
      this.smallResize.left = this.smallResize.top = 0;
      if (Object.keys(this.allGraphData).length) {
        if (
          this.svg.initWidth / this.svg.initHeight <
          this.smallResize.initWidth / this.smallResize.initHeight
        ) {
          this.smallResize.width =
            (this.smallResize.initHeight * this.svg.initWidth) /
            this.svg.initHeight;
          this.smallResize.left =
            (this.smallResize.initWidth - this.smallResize.width) / 2;
        } else {
          this.smallResize.height =
            (this.smallResize.initWidth * this.svg.initHeight) /
            this.svg.initWidth;
          this.smallResize.top =
            (this.smallResize.initHeight - this.smallResize.height) / 2;
        }
      }
      this.styleSet(this.smallResize, true);
      // Distance between the thumbnail frame and the upper part of the window
      this.smallResize.offsetLeft = smallResize.getBoundingClientRect().left;
      // Distance between the thumbnail frame and the upper part of the window
      this.smallResize.offsetTop = smallResize.getBoundingClientRect().top;

      const insideBox = document.querySelector('#inside-box');
      // graph0 information
      const graphDom = graphHtml.querySelector('#graph #graph0');
      smallMap.innerHTML = graphHtml.innerHTML;
      if (!graphDom) {
        document.onmousemove = document.onmouseup = null;
        if (smallContainer) {
          smallContainer.onmousedown = smallContainer.onmouseup = null;
          smallContainer.onmousewheel = null;
        }
        this.insideBox.width = this.smallResize.width;
        this.insideBox.height = this.smallResize.height;
        this.insideBox.top = this.insideBox.left = 0;
        this.styleSet(this.insideBox, true);
        insideBox.style.cursor = 'not-allowed';
      } else {
        let transformString = '';
        if (graphDom.attributes && graphDom.attributes.transform) {
          // transform information of graph
          transformString = graphDom.attributes.transform.nodeValue.split(
              /[(,)]/,
          );
        } else {
          transformString = ['translate', '0', '0', ' scale', '1'];
        }
        this.graphDom.transform = {
          k: parseFloat(transformString[4]),
          x: parseFloat(transformString[1]),
          y: parseFloat(transformString[2]),
        };
        graphDom.childNodes.forEach((k) => {
          if (k.tagName === 'polygon') {
            this.graphDom.pointStartX = parseFloat(
                k.attributes.points.nodeValue.split(/[\s,]/)[0],
            ); // Start point x
            this.graphDom.pointStartY = parseFloat(
                k.attributes.points.nodeValue.split(/[\s,]/)[1],
            ); // Start point y
          }
        });
        this.graphDom.initScale = 1; // Initial amplified value of graph
        this.graphDom.initTranslateY =
          this.svg.viewHeight - this.graphDom.pointStartY; // Initial y of graph
        this.graphDom.initTranslateX = -this.graphDom.pointStartX; // Initial x of graph
        this.graphDom.width = graphDom.getBoundingClientRect().width;
        this.graphDom.height = graphDom.getBoundingClientRect().height;
        this.graphDom.initWidth =
          this.graphDom.width / this.graphDom.transform.k; // Initial width of the graph
        this.graphDom.initHeight =
          this.graphDom.height / this.graphDom.transform.k; // Initial height of the graph
        delete this.graphSmall.el;
        this.graphSmall.el = smallMap.getElementsByClassName('graph')[0];
        this.graphSmall.el.attributes.transform.value = `translate(${this.graphDom.initTranslateX},
         ${this.graphDom.initTranslateY}) scale(${this.graphDom.initScale})`;

        this.graphSmall.initLeft =
          this.graphSmall.el.getBoundingClientRect().left -
          this.smallResize.offsetLeft;
        this.graphSmall.initTop =
          this.graphSmall.el.getBoundingClientRect().top -
          this.smallResize.offsetTop;
        this.graphSmall.initWidth = this.graphSmall.el.getBoundingClientRect().width;
        this.graphSmall.initHeight = this.graphSmall.el.getBoundingClientRect().height;
        // Size control of the shadow frame
        this.insideBox.scale = 1 / this.graphDom.transform.k; // Enlarged value of the shadow frame
        insideBox.style.cursor = 'move';
        this.bigMapPositionChange();

        // Small image location change event
        document.onmousemove = (e) => {
          if (this.clickSmall === 0) {
            this.insideBoxPositionChange(e);
          }
        };

        document.onmouseup = (e) => {
          if (this.clickSmall === 0) {
            this.insideBoxPositionChange(e);
            this.clickSmall = -1;
          }
        };

        smallContainer.onmousedown = (e) => {
          this.clickSmall = e.button;
          this.eventSmall.x = e.pageX - this.smallResize.offsetLeft;
          this.eventSmall.y = e.pageY - this.smallResize.offsetTop;
        };

        // Mouse lifting event
        smallContainer.onmouseup = (e) => {
          if (this.clickSmall === -1) {
            this.insideBoxPositionChange(e);
          }
        };

        // Mouse wheel event
        smallContainer.onmousewheel = (e) => {
          e = e || window.event;
          const b = e.wheelDelta ? e.wheelDelta : e.detail;
          if (
            !isNaN(this.graphDom.transform.k) &&
            this.graphDom.transform.k !== 0
          ) {
            const lg = b < 0 ? Math.abs(b) / 100 - 1 : 1 - b / 100;
            this.graphDom.transform = {
              k: Math.max(
                  this.scaleRange[0],
                  Math.min(
                      this.graphDom.transform.k * Math.pow(2, lg),
                      this.scaleRange[1],
                  ),
              ),
              x: this.graphDom.transform.x,
              y: this.graphDom.transform.y,
            };
            this.insideBox.scale = 1 / this.graphDom.transform.k;
            const width = this.insideBox.width;
            const height = this.insideBox.height;

            this.insideBox.left -=
              (this.smallResize.width * this.insideBox.scale - width) / 2;
            this.insideBox.top -=
              (this.smallResize.height * this.insideBox.scale - height) / 2;
            this.insideBox.height =
              this.smallResize.height * this.insideBox.scale;
            this.insideBox.width =
              this.smallResize.width * this.insideBox.scale;
            this.styleSet(this.insideBox, true);
            this.graphChange();
          }
        };
      }
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
      this.styleSet(this.insideBox, false);
      this.graphChange();
    },
    /**
     * Displacement of the large picture when the small picture is changed
     */
    graphChange() {
      if (!this.graphDom.transform.x || isNaN(this.graphDom.transform.x)) {
        this.initGraphRectData();
      }
      // left and top values in the shadow box when translate is set to the initial value only when the scale is changed
      const topInit =
        (this.graphSmall.initTop +
          (this.graphSmall.initHeight *
            (this.svg.viewHeight - Math.abs(this.graphDom.pointStartY))) /
            this.svg.viewHeight) *
        (1 - this.insideBox.scale);
      const leftInit =
        (this.graphSmall.initLeft +
          (this.graphSmall.initWidth * Math.abs(this.graphDom.pointStartX)) /
            this.svg.viewWidth) *
        (1 - this.insideBox.scale);
      // Move the translate value of the large image corresponding to the shadow frame.
      const topSmall =
        (((this.insideBox.top - topInit) * this.svg.viewHeight) /
          this.graphSmall.initHeight) *
        this.graphDom.transform.k;
      const leftSmall =
        (((this.insideBox.left - leftInit) * this.svg.viewWidth) /
          this.graphSmall.initWidth) *
        this.graphDom.transform.k;
      this.graphDom.transform = {
        k: this.graphDom.transform.k,
        x: this.graphDom.initTranslateX - leftSmall,
        y: this.graphDom.initTranslateY - topSmall,
      };
      const graphDomd3 = d3.select('#graph0');
      const graphDom = document.querySelector('#graph #graph0');
      if (graphDomd3) {
        graphDomd3.attr(
            'transform',
            `translate(${this.graphDom.transform.x},${this.graphDom.transform.y}) scale(${this.graphDom.transform.k})`,
        );
        this.graphDom.width = graphDom.getBoundingClientRect().width;
        this.graphDom.height = graphDom.getBoundingClientRect().height;
      }
    },
    /**
     * Displacement of the small map when the large picture is changed
     */
    bigMapPositionChange() {
      const graphDom = document.querySelector('#graph #graph0');
      this.graphDom.top =
        graphDom.getBoundingClientRect().top - this.svg.offsetTop;
      this.graphDom.left =
        graphDom.getBoundingClientRect().left - this.svg.offsetLeft;
      this.insideBox.left = parseFloat(
          (
            this.graphSmall.initLeft -
          (this.graphDom.left / this.graphDom.width) * this.graphSmall.initWidth
          ).toFixed(3),
      );
      this.insideBox.top = parseFloat(
          (
            this.graphSmall.initTop -
          (this.graphDom.top / this.graphDom.height) *
            this.graphSmall.initHeight
          ).toFixed(3),
      );
      this.insideBox.height = this.smallResize.height * this.insideBox.scale;
      this.insideBox.width = this.smallResize.width * this.insideBox.scale;
      this.styleSet(this.insideBox, true);
    },
    /**
     * Setting the width and height of a node
     * @param {Object} el dom node whose style needs to be modified
     * @param {Boolean} sizeChange Whether to change the width and height
     */
    styleSet(el, sizeChange) {
      const dom = document.querySelector(el.el);
      dom.style.left = `${el.left}px`;
      dom.style.top = `${el.top}px`;
      if (sizeChange) {
        dom.style.width = `${el.width}px`;
        dom.style.height = `${el.height}px`;
      }
    },
    /**
     * Expansion and folding of control edges
     * @param {String} item Determines the control edge of the input or output.
     */
    toggleControl(item) {
      this.selectedNode.showControl[item] = !this.selectedNode.showControl[
          item
      ];
    },
    /**
     * Click the node information name.
     */
    nodeNameClick() {
      const nodeNameText = event.target;
      if (document.body.createTextRange) {
        const nodeNameTextRange = document.body.createTextRange();
        nodeNameTextRange.moveToElementText(nodeNameText);
        nodeNameTextRange.select();
      } else if (window.getSelection) {
        const nodeNameSelection = window.getSelection();
        const nodeNameTextRange = document.createRange();
        nodeNameTextRange.selectNodeContents(nodeNameText);
        nodeNameSelection.removeAllRanges();
        nodeNameSelection.addRange(nodeNameTextRange);
      }
    },
    /**
     * Collapse on the right
     */
    toggleRight() {
      this.rightShow = !this.rightShow;
      setTimeout(() => {
        this.initGraphRectData();
      }, 10);
    },
    /**
     * Full-screen display
     */
    toggleScreen() {
      this.fullScreen = !this.fullScreen;
      setTimeout(() => {
        this.initGraphRectData();
      }, 10);
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
        `viewBox="${viewBoxSize}">${CommonProperty.graphDownloadStyle}<g>${svgXml}</g></svg>`;

      // Write the svg stream encoded by base64 to the image object.
      const src = `data:image/svg+xml;base64,
      ${window.btoa(unescape(encodeURIComponent(encodeStr)))}`;
      const a = document.createElement('a');
      a.href = src; // Export the information in the canvas as image data.
      a.download = 'graph'; // Set the download name.
      a.click(); // Click to trigger download.
    },
    /**
     * Fold the legend area.
     */
    foldLegend() {
      this.showLegend = !this.showLegend;
    },
    // jump back to train dashboard
    jumpToTrainDashboard() {
      this.$router.push({
        path: '/train-manage/training-dashboard',
        query: {
          id: this.trainJobID,
        },
      });
    },
  },
  // Components imported by the page
  components: {
    Autocomplete,
  },
};
</script>
<style lang="scss">
.cl-graph-manage {
  height: 100%;
  .cl-graph-title {
    height: 56px;
    line-height: 56px;
  }
  .graph-p32 {
    height: 100%;
  }
  .cl-content {
    height: calc(100% - 50px);
    overflow: auto;
  }
  #graphs {
    width: 100%;
    height: 100%;
    font-size: 0;
    background: #f0f2f5;
    .search {
      margin-bottom: 15px;
      width: 100%;
      .el-autocomplete-suggestion {
        position: absolute;
        width: 100%;
        z-index: 200;
      }
    }
    .cl-graph {
      position: relative;
      width: 100%;
      height: 100%;
      background-color: #fff;
      padding: 0 32px 24px;
      min-height: 700px;
      overflow: hidden;
    }
    .cl-graph.full-screen {
      position: absolute;
      top: 0;
      bottom: 0;
      left: -280px;
      right: 0;
      width: auto;
      height: auto;
      padding: 0;
      #sidebar {
        .node-info-con {
          height: calc(100% - 280px);
        }
      }
      .graph-container {
        width: 100%;
      }
    }
    #sidebar.right-hide {
      right: -442px;
    }
    #sidebar {
      position: absolute;
      right: 0;
      top: 0;
      width: 442px;
      height: 100%;
      border-radius: 6px;
      text-align: left;
      background-color: #ffffff;
      display: inline-block;
      box-shadow: 0 1px 3px 0px rgba(0, 0, 0, 0.1);
      color: #333333;
      font-size: 14px;
      line-height: 14px;
      padding: 18px 32px 24px;
      div,
      span,
      pre {
        font-size: 14px;
      }
      #small-container {
        height: 209px;
        width: 100%;
        z-index: 100;
        border: 1px solid #e6ebf5;
        overflow: hidden;
        background-color: white;
        position: relative;
        #small-resize {
          width: 100%;
          height: 100%;
          position: absolute;
          left: 0;
          top: 0;
        }
        #small-map {
          height: 100%;
          width: 100%;
          position: relative;
          padding: 0;
        }
        #inside-box {
          background-color: #c0d3ff;
          position: absolute;
          /* Transparency */
          opacity: 0.3;
          width: 100%;
          height: 100%;
          left: 0px;
          top: 0px;
          z-index: 200;
          cursor: move;
        }
      }
      .title {
        padding: 20px 0;
        font-size: 14px;
        color: #333333;
        img {
          float: right;
          margin-right: 10px;
          cursor: pointer;
        }
      }
      .graph-controls {
        padding: 10px 20px 0 20px;
        div {
          cursor: pointer;
          display: inline-block;
          margin-left: 20px;
        }
        img {
          cursor: pointer;
          vertical-align: middle;
        }
      }
      .node-info-con {
        ::-webkit-scrollbar-button {
          z-index: 200;
          width: 10px;
          height: 10px;
          background: #fff;
          cursor: pointer;
        }
        ::-webkit-scrollbar-button:horizontal:single-button:start {
          background-image: url('../../assets/images/scroll-btn-left.png');
          background-position: center;
        }
        ::-webkit-scrollbar-button:horizontal:single-button:end {
          background-image: url('../../assets/images/scroll-btn-right.png');
          background-position: center;
        }
        ::-webkit-scrollbar-button:vertical:single-button:start {
          background-image: url('../../assets/images/scroll-btn-up.png');
          background-position: center;
        }
        ::-webkit-scrollbar-button:vertical:single-button:end {
          background-image: url('../../assets/images/scroll-btn-down.png');
          background-position: center;
        }
        ::-webkit-scrollbar-thumb {
          background-color: #bac5cc;
        }
        ::-webkit-scrollbar {
          width: 6px;
          height: 6px;
        }
      }
      .node-info-container {
        height: calc(100% - 451px);
      }
      .node-info-container-long {
        height: calc(100% - 357px);
      }
      .node-info {
        font-size: 14px;
        padding: 0 20px;
        height: calc(100% - 54px);
        overflow: auto;
        color: #333;
        background-color: #f7faff;
        .clear {
          clear: both;
        }
        .hover {
          li:hover {
            background: #fce8b2;
          }
          .control-list {
            .dependence-title {
              line-height: 30px;
              cursor: pointer;
              font-weight: bold;
              img {
                vertical-align: middle;
                margin-right: 3px;
              }
            }
            .dependence-title.hide {
              img {
                margin-top: -3px;
                transform: rotate(-90deg);
              }
            }
            li:hover {
              background: #fce8b2;
            }
          }
          .control-list:hover {
            background: none;
          }
        }
        .pointer {
          cursor: pointer;
        }
        .item-content {
          max-height: calc(50% - 95px);
          overflow: auto;
          li {
            min-width: 100%;
            width: max-content;
          }
        }
        .item-min {
          min-height: 50px;
        }
        .item-min2 {
          min-height: 87px;
        }
        .items {
          line-height: 20px;
          padding: 9px 0;
          .items-over {
            max-height: 60px;
            overflow: auto;
          }
          .item {
            color: #999;
          }
        }
        .shape {
          vertical-align: top;
          width: 50px;
          word-break: break-all;
          display: inline-table;
          position: absolute;
          left: 0;
        }
        .key {
          vertical-align: top;
          width: 60px;
          word-break: break-all;
          display: inline-table;
        }
        .label {
          vertical-align: top;
          width: 70px;
          word-break: break-all;
          display: inline-block;
        }
        .value {
          vertical-align: top;
          display: inline-block;
          width: calc(100% - 70px);
          white-space: nowrap;
          overflow: auto;
        }
        .size {
          width: 310px;
          font-size: 12px;
          text-align: right;
        }
        .input {
          width: 100%;
          position: relative;
          display: inline-block;
          white-space: nowrap;
        }
        ul {
          li {
            line-height: 20px;
          }
        }
      }
      .legend {
        .legend-content {
          background-color: #f7faff;
          padding: 0 32px;
          height: 94px;
          overflow-y: auto;
        }
        .legend-item {
          padding: 5px 0;
          display: inline-block;
          width: 50%;
          font-size: 14px;
          line-height: 20px;
          .pic {
            width: 45px;
            text-align: center;
            display: inline-block;
            padding-left: 20px;
            vertical-align: middle;
            img {
              max-width: 45px;
              max-height: 15px;
              margin-left: -20px;
              vertical-align: middle;
            }
          }
          .legend-text {
            display: inline-block;
            padding-left: 20px;
            width: calc(100% - 45px);
            vertical-align: middle;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
          .legend-text:hover {
            cursor: default;
          }
        }
      }
      .toggle-right {
        position: absolute;
        top: calc(50% - 43px);
        left: -16px;
        width: 18px;
        height: 86px;
        cursor: pointer;
        background-image: url('../../assets/images/toggle-right-bg.png');
      }
      .icon-toggle {
        width: 6px;
        height: 9px;
        background-image: url('../../assets/images/toggle-right-icon.png');
        position: absolute;
        top: calc(50% - 4.5px);
        left: calc(50% - 3px);
      }
      .icon-toggle.icon-left {
        transform: rotateY(180deg);
      }
    }
    .operate-button-list {
      position: absolute;
      right: 0;
      top: 0;
      z-index: 100;
      div {
        cursor: pointer;
        width: 12px;
        height: 12px;
        display: inline-block;
        margin: 5px;
      }
      .download-button {
        background-image: url('../../assets/images/download.png');
      }
      .full-screen-button {
        background-image: url('../../assets/images/full-screen.png');
      }
    }
    .graph-container.all {
      width: 100%;
    }
    .graph-container {
      .node:hover > path,
      .node:hover > ellipse,
      .node:hover > polygon,
      .node:hover > rect {
        stroke-width: 2px;
      }
      .node.cluster > rect:hover {
        stroke: #f45c5e;
      }
      .selected {
        stroke: red !important;
        stroke-width: 2px;
      }
    }
    .graph-container,
    #small-map {
      font-size: 16px;
      position: relative;
      display: inline-block;
      width: calc(100% - 442px);
      height: 100%;
      text-align: left;
      -webkit-touch-callout: none;
      -webkit-user-select: none;
      -khtml-user-select: none;
      -moz-user-select: none;
      -ms-user-select: none;
      user-select: none;
      .graph {
        height: 100%;
        background-color: #f7faff;
      }
      #graph0 > polygon {
        fill: transparent;
      }
      .node {
        cursor: pointer;
      }
      .edge {
        path {
          stroke: rgb(167, 167, 167);
        }
        polygon {
          fill: rgb(167, 167, 167);
        }
      }
      .edge.highlighted {
        path {
          stroke: red;
        }
        polygon {
          stroke: red;
          fill: red;
        }
        marker {
          path {
            fill: red;
          }
        }
      }
      .node.aggregation > polygon {
        stroke: #fdca5a;
        fill: #ffe8b5;
      }
      .node.cluster.aggregation > rect {
        stroke: #fdca5a;
        fill: #fff2d4;
        stroke-dasharray: 3, 3;
      }
      .node > polygon {
        stroke: #f45c5e;
        fill: #ffba99;
      }
      .node > ellipse {
        stroke: #58a4e0;
        fill: #d1ebff;
      }
      .plain > path,
      .plain ellipse {
        stroke: #56b077;
        fill: #c1f5d5;
        stroke-dasharray: 1.5, 1.5;
      }
      .hide {
        visibility: hidden;
      }
      .show {
        visibility: visible;
      }
      .edge-point ellipse {
        stroke: #a7a7a7;
        fill: #a7a7a7;
      }
      text {
        fill: black;
      }
    }
    // No data available.
    .image-noData {
      // Set the width and white on the right.
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
    .noData-text {
      margin-top: 33px;
      font-size: 18px;
    }
  }
  .cl-display-block {
    display: block;
  }
  .cl-input-value {
    width: calc(100% - 70px) !important;
    margin-left: 10px !important;
  }
  .cl-close-btn {
    width: 20px;
    height: 20px;
    vertical-align: -3px;
    cursor: pointer;
    display: inline-block;
  }
  .cl-title-right {
    padding-right: 32px;
  }
}
</style>

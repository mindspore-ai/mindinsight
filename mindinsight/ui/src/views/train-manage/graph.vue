<!--
Copyright 2019-2021 Huawei Technologies Co., Ltd.All Rights Reserved.

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
    <div class="graph-p32">
      <div class="guide-content"
           v-if="guide.show">
        <el-popover placement="top-start"
                    ref="popover"
                    :style="{ position: 'absolute', top: guide.top, left: guide.left }"
                    :title="guide.title"
                    width="370"
                    v-model="guide.show">
          <i class="el-icon-close"
             @click="closeUserGuide"></i>
          <div v-for="item in guide.content"
               :key="item"
               class="guide-span">{{ item }}</div>
          <div class="step-pic">
            <img :src="require(`@/assets/images/graph-stepimg${guide.step}.svg`)" />
          </div>

          <el-button type="primary"
                     @click="guideNext">{{
            guide.step === 3 ? $t('graph.finish') : $t('graph.next')
          }}</el-button>
        </el-popover>
        <div class="step"
             v-show="guide.step == 1">
          <img :src="require(`@/assets/images/graph-step1${language === 'en-us' ? '-en' : ''}.svg`)"
               alt="" />
        </div>
        <div class="step"
             v-show="guide.step == 2">
          <img :src="require(`@/assets/images/graph-step2${language === 'en-us' ? '-en' : ''}.svg`)"
               alt="" />
        </div>
        <div class="step"
             v-show="guide.step == 3">
          <img :src="require(`@/assets/images/graph-step3${language === 'en-us' ? '-en' : ''}.svg`)"
               alt="" />
        </div>
      </div>
      <div class="cl-title cl-graph-title">
        <div class="cl-title-left">
          {{ $t('graph.titleText') }}
          <div class="path-message">
            <span>{{$t('symbols.leftbracket')}}</span>
            <span>{{$t('trainingDashboard.summaryDirPath')}}</span>
            <span>{{summaryPath}}</span>
            <span>{{$t('symbols.rightbracket')}}</span>
          </div>
          <span @click="showUserGuide"
                class="guide">
            <i class="guide-icon"></i>
            {{$t('graph.guide')}}
          </span>
        </div>
        <div class="cl-title-right">
          <div class="cl-close-btn"
               @click="jumpToTrainDashboard">
            <img src="@/assets/images/close-page.png" />
          </div>
        </div>
      </div>
      <div class="cl-content">
        <div id="graphs">
          <div class="cl-graph"
               :class="fullScreen ? 'full-screen' : ''">
            <!-- graph -->
            <div class="graph-container"
                 :class="rightShow ? '' : 'all'">
              <!-- No data is displayed. -->
              <div class="image-noData"
                   v-if="!loading.show && !Object.keys(allGraphData).length">
                <div>
                  <img :src="require('@/assets/images/nodata.png')"
                       alt="" />
                </div>
                <div class="noData-text">{{ $t('public.noData') }}</div>
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
                <i :class="rightShow ? 'icon-toggle' : 'icon-toggle icon-left'"></i>
              </div>
              <!-- Search box -->
              <div class="sidebar-tooltip">
                <el-tooltip placement="top"
                            effect="light">
                  <div slot="content"
                       class="tooltip-container">
                    <div class="cl-graph-sidebar-tip">
                      {{$t('graph.sidebarTip')}}
                    </div>
                  </div>
                  <i class="el-icon-info"></i>
                </el-tooltip>
              </div>
              <el-select @change="fileChange"
                         @visible-change="getSelectList"
                         :popper-append-to-body="false"
                         class="search"
                         v-model="fileSearchBox.value">
                <el-option v-for="item in fileSearchBox.suggestions"
                           :key="item.value"
                           :title="item.value"
                           :label="item.value"
                           :value="item.value">
                </el-option>
              </el-select>
              <!-- Search box -->
              <div class="search-wrap">
                <el-input class="search"
                          :placeholder="$t('graph.inputNodeName')"
                          v-model="searchBox.value"
                          @input="filterChange"
                          @keyup.enter.native="searchNodesNames"
                          clearable>
                  <el-button slot="append"
                             @click="treeWrapFlag=!treeWrapFlag"
                             class="collapse_i">
                    <i class="el-icon-caret-bottom"
                       v-if="!treeWrapFlag"></i>
                    <i class="el-icon-caret-top"
                       v-else></i>
                  </el-button>
                </el-input>
                <div class="tree-wrap"
                     v-show="treeWrapFlag">
                  <el-tree v-show="treeFlag"
                           :props="props"
                           :load="loadNode"
                           @node-collapse="nodeCollapse"
                           @node-click="handleNodeClick"
                           node-key="name"
                           :expand-on-click-node="false"
                           :lazy="true"
                           :highlight-current="true"
                           ref="tree">
                    <span class="custom-tree-node"
                          slot-scope="{ node ,data }">
                      <span>
                        <img v-if="data.type ==='name_scope'"
                             :src="require('@/assets/images/name-scope.svg')"
                             class="image-type" />
                        <img v-else-if="data.type ==='Const'"
                             :src="require('@/assets/images/constant-node.svg')"
                             class="image-type" />
                        <img v-else-if="data.type ==='aggregation_scope'"
                             :src="require('@/assets/images/polymetric.svg')"
                             class="image-type" />
                        <img v-else
                             :src="require('@/assets/images/operator-node.svg')"
                             class="image-type" />
                      </span>
                      <span class="custom-tree-node">{{ node.label }}</span>
                    </span>
                  </el-tree>
                  <el-tree v-show="!treeFlag"
                           :props="defaultProps"
                           :load="loadSearchNode"
                           :lazy="true"
                           node-key="name"
                           @node-click="handleNodeClick"
                           :expand-on-click-node="false"
                           ref="searchTree">
                    <span class="custom-tree-node"
                          slot-scope="{ node ,data }">
                      <span>
                        <img v-if="data.type ==='name_scope'"
                             :src="require('@/assets/images/name-scope.svg')"
                             class="image-type" />
                        <img v-else-if="data.type ==='Const'"
                             :src="require('@/assets/images/constant-node.svg')"
                             class="image-type" />
                        <img v-else-if="data.type ==='aggregation_scope'"
                             :src="require('@/assets/images/polymetric.svg')"
                             class="image-type" />
                        <img v-else
                             :src="require('@/assets/images/operator-node.svg')"
                             class="image-type" />
                      </span>
                      <span class="custom-tree-node">{{ node.label }}</span>
                    </span>
                  </el-tree>
                </div>
              </div>
              <!-- Functional Area -->
              <div id="small-container">
                <div id="small-resize">
                  <div id="small-map"></div>
                  <div id="inside-box"></div>
                </div>
              </div>
              <!-- Node information -->
              <div :class="
                  showLegend
                    ? 'node-info-con node-info-container'
                    : 'node-info-con node-info-container-long'
                ">
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
                     v-show="selectedNode.show">
                  <div class="items">
                    <div class="label item">{{ $t('graph.name') }}</div>
                    <div class="value">
                      <span class="cl-display-block"
                            @dblclick="nodeNameClick">{{ selectedNode.title }}</span>
                    </div>
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
                    <div class="item">
                      {{ $t('graph.attr') }} ({{
                        selectedNode.info.attributes.length
                      }})
                    </div>
                  </div>
                  <ul v-if="selectedNode.info && !selectedNode.countShow"
                      class="item-content hover"
                      :class="
                      selectedNode.info.attributes.length > 2
                        ? 'item-min2'
                        : selectedNode.info.attributes.length > 0
                        ? 'item-min'
                        : ''
                    ">
                    <li v-for="item in selectedNode.info.attributes"
                        :key="item.name">
                      <div class="key">
                        {{ item.name }}
                      </div>
                      <div class="input cl-input-value">
                        <pre>{{ item.value }}</pre>
                      </div>
                    </li>
                  </ul>
                  <div class="items itemHeight">
                    <div class="item">
                      {{ $t('graph.inputs') }} (
                      {{
                        selectedNode.info.input.length +
                          selectedNode.info.inputControl.length
                      }})
                    </div>
                  </div>
                  <ul v-if="selectedNode.info"
                      class="item-content hover"
                      :class="
                      selectedNode.info.input.length > 1
                        ? 'item-min2'
                        : selectedNode.info.input.length > 0
                        ? 'item-min'
                        : ''
                    ">
                    <li v-for="item in selectedNode.info.input"
                        :key="item.$index"
                        @click="querySingleNode({ value: item.name })"
                        class="pointer">
                      <div class="input">{{ item.name }}</div>
                      <div class="size">{{ item.value }}</div>
                      <div class="clear"></div>
                    </li>
                    <li class="control-list"
                        v-if="
                        selectedNode.info &&
                          selectedNode.info.inputControl.length
                      ">
                      <div class="dependence-title"
                           @click="toggleControl('input')"
                           :class="selectedNode.showControl.input ? '' : 'hide'">
                        <img :src="require('@/assets/images/all-uptake.png')"
                             alt="" />
                        {{ $t('graph.controlDependencies') }}
                      </div>
                      <ul v-show="selectedNode.showControl.input">
                        <li v-for="item in selectedNode.info.inputControl"
                            :key="item.$index"
                            @click="querySingleNode({ value: item.name })"
                            class="pointer">
                          <div class="input">{{ item.name }}</div>
                          <div class="size">{{ item.value }}</div>
                          <div class="clear"></div>
                        </li>
                      </ul>
                    </li>
                  </ul>
                  <div class="items">
                    <div class="item">
                      {{ $t('graph.outputs') }} (
                      {{
                        selectedNode.info.output.length +
                          selectedNode.info.outputControl.length
                      }})
                    </div>
                  </div>
                  <ul v-if="selectedNode.info"
                      class="item-content hover"
                      :class="
                      selectedNode.info.output.length > 1
                        ? 'item-min2'
                        : selectedNode.info.output.length > 0
                        ? 'item-min'
                        : ''
                    ">
                    <li v-for="item in selectedNode.info.output"
                        :key="item.$index"
                        @click="querySingleNode({ value: item.name })"
                        class="pointer">
                      <div class="input">{{ item.name }}</div>
                      <div class="size">{{ item.value }}</div>
                      <div class="clear"></div>
                    </li>
                    <li class="control-list"
                        v-if="
                        selectedNode.info &&
                          selectedNode.info.outputControl.length
                      ">
                      <div class="dependence-title"
                           @click="toggleControl('output')"
                           :class="selectedNode.showControl.output ? '' : 'hide'">
                        <img :src="require('@/assets/images/all-uptake.png')"
                             alt="" />
                        {{ $t('graph.controlDependencies') }}
                      </div>
                      <ul v-show="selectedNode.showControl.output">
                        <li v-for="item in selectedNode.info.outputControl"
                            :key="item.$index"
                            @click="querySingleNode({ value: item.name })"
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
                      <img :src="require('@/assets/images/name-scope.svg')"
                           alt="" />
                    </div>
                    <div class="legend-text"
                         :title="$t('graph.nameSpace')">
                      {{ $t('graph.nameSpace') }}
                    </div>
                  </div>
                  <div class="legend-item">
                    <div class="pic">
                      <img :src="require('@/assets/images/polymetric.svg')"
                           alt="" />
                    </div>
                    <div class="legend-text"
                         :title="$t('graph.polymetric')">
                      {{ $t('graph.polymetric') }}
                    </div>
                  </div>
                  <div class="legend-item">
                    <div class="pic">
                      <img :src="require('@/assets/images/virtual-node.svg')"
                           alt="" />
                    </div>
                    <div class="legend-text"
                         :title="$t('graph.virtualNode')">
                      {{ $t('graph.virtualNode') }}
                    </div>
                  </div>
                  <div class="legend-item">
                    <div class="pic">
                      <img :src="require('@/assets/images/operator-node.svg')"
                           alt="" />
                    </div>
                    <div class="legend-text"
                         :title="$t('graph.operatorNode')">
                      {{ $t('graph.operatorNode') }}
                    </div>
                  </div>
                  <div class="legend-item">
                    <div class="pic">
                      <img :src="require('@/assets/images/constant-node.svg')"
                           alt="" />
                    </div>
                    <div class="legend-text"
                         :title="$t('graph.constantNode')">
                      {{ $t('graph.constantNode') }}
                    </div>
                  </div>
                  <br>
                  <div class="legend-item">
                    <div class="pic">
                      <img :src="require('@/assets/images/data-flow.png')"
                           alt="" />
                    </div>
                    <div class="legend-text"
                         :title="$t('graph.dataFlowEdge')">
                      {{ $t('graph.dataFlowEdge') }}
                    </div>
                  </div>
                  <div class="legend-item">
                    <div class="pic">
                      <img :src="require('@/assets/images/control-dep.png')"
                           alt="" />
                    </div>
                    <div class="legend-text"
                         :title="$t('graph.controllDepEdge')">
                      {{ $t('graph.controllDepEdge') }}
                    </div>
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
import CommonProperty from '@/common/common-property.js';
import RequestService from '@/services/request-service';
import {select, selectAll, zoom} from 'd3';
import 'd3-graphviz';
const d3 = {select, selectAll, zoom};
import commonGraph from '../../mixins/common-graph.vue';
import smallMap from '../../mixins/small-map.vue';

export default {
  mixins: [commonGraph, smallMap],
  data() {
    return {
      summaryPath: this.$route.query.summaryPath,
      graph: {}, // Basic information about graph0 in svg
      svg: {}, // Basic information about svg

      allGraphData: {}, // graph Original input data
      firstFloorNodes: [], // ID array of the first layer node.
      // Information about the selected node
      selectedNode: {
        info: {
          inputControl: [],
          input: [],
          outputControl: [],
          output: [],
          attributes: [],
        },
        showControl: {
          input: true,
          output: true,
        },
      },
      // Training job id
      trainJobID: '',
      nodesCountLimit: 1500, // Maximum number of sub-nodes in a namespace.
      maxChainNum: 70,

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
      scaleRange: [0.001, 1000], // graph zooms in and zooms out.
      rightShow: true, // Check whether the right side bar is displayed.
      fullScreen: false, // Display Full Screen
      graphviz: null,
      graphvizTemp: null,
      initOver: false,
      guide: {
        show: false,
        step: 1,
        top: '0%',
        left: '0%',
        content: [
          this.$t('graph.guideContent11'),
          this.$t('graph.guideContent12'),
          this.$t('graph.guideContent13'),
          this.$t('graph.guideContent14'),
        ],
        title: '',
      },
      language: '',
      defaultProps: {
        children: 'nodes',
        label: 'label',
        isLeaf: 'leaf',
      },
      treeFlag: true,
      props: {
        label: 'label',
        children: 'children',
        isLeaf: 'leaf',
      },
      node: null,
      resolve: null,
      treeWrapFlag: true,
      searchNode: null,
      searchResolve: null,
      isIntoView: true,
    };
  },
  computed: {},
  watch: {
    guide: {
      handler(newVal) {
        if (newVal.step === 1) {
          this.guide.top = '20%';
          this.guide.left = '48%';
        } else if (newVal.step === 2) {
          this.guide.top = '47%';
          this.guide.left = '62%';
        } else if (newVal.step === 3) {
          this.guide.top = '45%';
          this.guide.left = '52%';
        }
        this.guide.title = this.$t(`graph.guideTitle${newVal.step}`);
      },
      deep: true,
    },
  },
  mounted() {
    // Judging from the training job overview.
    if (!this.$route.query || !this.$route.query.train_id) {
      this.trainJobID = '';
      this.$message.error(this.$t('trainingDashboard.invalidId'));
      document.title = `${this.$t('graph.titleText')}-MindInsight`;
      return;
    }
    const showGuide = window.localStorage.getItem('graphShowGuide');
    if (!showGuide) {
      this.guide.show = true;
      window.localStorage.setItem('graphShowGuide', true);
    }

    this.trainJobID = this.$route.query.train_id;

    this.language = window.localStorage.getItem('milang');
    const languageList = ['zh-cn', 'en-us'];
    if (!this.language || !languageList.includes(this.language)) {
      this.language = languageList[0];
      window.localStorage.setItem('milang', this.language);
    }

    document.title = `${decodeURIComponent(this.trainJobID)}-${this.$t(
        'graph.titleText',
    )}-MindInsight`;
    this.getDatavisualPlugins();
    window.onresize = () => {
      if (this.graph.dom) {
        this.$nextTick(() => {
          setTimeout(() => {
            this.initSvg(false);
            this.initGraphRectData();
          }, 500);
        });
      }
    };
  },
  destroyed() {
    window.onresize = null;
  },
  methods: {
    /**
     * Tree linkage with graph  Expand of current node
     * @param {Obejct} nodes Data of children of current node
     * @param {Obejct} name  The name of the current node
     */
    nodeExpandLinkage(nodes, name) {
      const curNodeData = nodes.map((val) => {
        return {
          label: val.name.split('/').pop(),
          ...val,
        };
      });
      const node = this.$refs.tree.getNode(name);
      curNodeData.forEach((val) => {
        this.$refs.tree.append(val, name);
      });
      node.childNodes.forEach((val) => {
        if (
          val.data.type !== 'name_scope' &&
          val.data.type !== 'aggregation_scope'
        ) {
          val.isLeaf = true;
        }
      });
      node.expanded = true;
      node.loading = false;
      this.$refs.tree.setCurrentKey(name);
      this.$nextTick(() => {
        setTimeout(() => {
          const dom = document.querySelector('.el-tree-node.is-current.is-focusable');
          if (dom && this.rightShow) {
            dom.scrollIntoView();
          }
        }, 800);
      });
    },
    /**
     * Collapse node
     * @param {Object} _
     * @param {Object} node node data
     */
    nodeCollapse(_, node) {
      node.loaded = false;
      if (this.treeFlag) {
        this.dealDoubleClick(node.data.name);
      }
    },
    /**
     * Draw the tree
     * @param {Object} node tree root node
     * @param {Function} resolve callback function ,return next node data
     */
    loadNode(node, resolve) {
      if (node.level === 0) {
        node.childNodes = [];
        if (!this.node && !this.resolve) {
          this.node = node;
          this.resolve = resolve;
        }
      } else if (node.level >= 1) {
        this.isIntoView = false;
        this.loading.info = this.$t('graph.queryLoading');
        this.loading.show = true;
        setTimeout(() => {
          this.queryGraphData(node.data.name, resolve);
        }, 200);
      }
    },
    /**
     * Draw the tree
     * @param {Object} node tree root node
     * @param {Function} resolve callback function ,return next node data
     */
    loadSearchNode(node, resolve) {
      if (node.level === 0) {
        node.childNodes = [];
        if (!this.searchNode && !this.searchResolve) {
          this.searchNode = node;
          this.searchResolve = resolve;
        }
      } else if (node.level >= 1) {
        const params = {
          name: node.data.name,
          train_id: this.trainJobID,
          tag: this.fileSearchBox.value,
        };
        if (node.childNodes && node.childNodes.length) {
          node.expanded = true;
          node.loaded = true;
          node.loading = false;
          return;
        }
        RequestService.queryGraphData(params).then((res) => {
          if (res && res.data && res.data.nodes) {
            const data = res.data.nodes.map((val) => {
              return {
                label: val.name.split('/').pop(),
                leaf:
                  val.type === 'name_scope' || val.type === 'aggregation_scope'
                    ? false
                    : true,
                ...val,
              };
            });
            resolve(data);
          }
        });
      }
    },
    /**
     * Deal search data
     * @param {Array} arr search tree data
     */
    dealSearchResult(arr) {
      arr.forEach((val) => {
        if (val.nodes) {
          this.dealSearchResult(val.nodes);
        }
        val.label = val.name.split('/').pop();
      });
    },
    filterChange() {
      if (this.searchBox.value === '') {
        this.treeFlag = true;
        this.$nextTick(() => {
          setTimeout(() => {
            const dom = document.querySelector('.el-tree-node.is-current.is-focusable');
            if (dom && this.rightShow) {
              dom.scrollIntoView();
            }
          }, 800);
        });
      }
    },
    handleNodeClick(data) {
      this.isIntoView = false;
      this.selectedNode.name = data.name;
      if (this.treeFlag) {
        this.selectNode(true);
      } else {
        this.querySingleNode({value: data.name});
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
      const elements = d3.select('#graph').selectAll('g.node, g.edge').nodes();
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
      d3.selectAll('g.edge>title').remove();
      // The graph generated by the plug-in has a useless title and needs to be deleted.
      document.querySelector('#graph g#graph0 title').remove();
      this.initGraphRectData();
      this.startApp();
    },
    /**
     * Initialization method executed after the graph rendering is complete
     */
    startApp() {
      const nodes = d3.selectAll('g.node, g.cluster');
      nodes.on(
          'click',
          (target, index, nodesList) => {
            this.clickEvent(target, index, nodesList, 'graph');
          },
          false,
      );
      // namespaces Expansion or Reduction
      nodes.on(
          'dblclick',
          (target, index, nodesList) => {
            this.dblclickEvent(target, index, nodesList, 'graph');
          },
          false,
      );
      this.initZooming('graph');
      if (this.selectedNode.name) {
        this.selectNode(true);
      }
    },
    /**
     * Double-click the processing to be performed on the node to expand or narrow the namespace or aggregation node.
     * @param {String} name Name of the current node (also the ID of the node)
     */
    dealDoubleClick(name) {
      this.loading.info = this.$t('graph.queryLoading');
      this.loading.show = true;
      this.$nextTick(() => {
        // DOM tree needs time to respond, otherwise the loading icon will not be displayed
        const timeOut = 500;
        setTimeout(() => {
          name = name.replace('_unfold', '');
          if (this.allGraphData[name].isUnfold) {
            this.selectedNode.name = name;
            this.deleteNamespace(name);
          } else {
            this.queryGraphData(name);
          }
        }, timeOut);
      });
    },
    /**
     * To obtain graph data, initialize and expand the namespace or aggregate nodes.
     * @param {String} name Name of the current node.
     * @param {Function} resolve Callback function.
     */
    queryGraphData(name, resolve) {
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
                    this.$refs.tree.getNode(name).loading = false;
                  } else {
                    const nodes = JSON.parse(JSON.stringify(response.data.nodes));
                    if (nodes && nodes.length) {
                      this.packageDataToObject(name, true, nodes);
                      // If the name is empty, it indicates the outermost layer.
                      if (!name) {
                        const dot = this.packageGraphData();
                        this.initGraph(dot);
                      } else {
                        if (this.allGraphData[name].type === 'aggregation_scope') {
                          this.dealAggregationNodes(name);
                          if (
                            this.allGraphData[name].maxChainNum > this.maxChainNum
                          ) {
                            this.$message.error(this.$t('graph.tooManyChain'));
                            this.allGraphData[name].isUnfold = true;
                            this.selectedNode.name = name;
                            this.loading.show = false;
                            this.deleteNamespace(name);
                            this.$refs.tree.getNode(name).loading = false;
                            return;
                          }
                        }
                        this.allGraphData[name].isUnfold = true;
                        this.selectedNode.name = `${name}_unfold`;
                        this.layoutNamescope(name, true);
                      }
                    } else {
                      this.initGraphRectData();
                      this.loading.show = false;
                    }
                    const data = response.data.nodes.map((val) => {
                      return {
                        label: val.name.split('/').pop(),
                        leaf:
                      val.type === 'name_scope' ||
                      val.type === 'aggregation_scope'
                        ? false
                        : true,
                        ...val,
                      };
                    });
                    if (name) {
                      if (resolve) {
                        resolve(JSON.parse(JSON.stringify(data)));
                      } else {
                        this.nodeExpandLinkage(response.data.nodes, name);
                      }
                    } else {
                      this.node.childNodes = [];
                      this.resolve(JSON.parse(JSON.stringify(data)));
                    }
                  }
                }
              },
              (error) => {
                this.loading.show = false;
              },
          )
          .catch((error) => {
          // A non-Google Chrome browser may not work properly.
            this.loading.show = false;
            if (error && error.includes('larger than maximum 65535 allowed')) {
              this.$message.error(this.$t('graph.dataTooLarge'));
            } else {
              this.$bus.$emit('showWarmText', true);
            }
            if (name && this.allGraphData[name]) {
              this.allGraphData[name].isUnfold = false;
              this.allGraphData[name].children = [];
              this.allGraphData[name].size = [];
              this.allGraphData[name].html = '';
            }
          });
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
     * Close the expanded namespace.
     * @param {String} name The name of the namespace to be closed.
     */
    deleteNamespace(name) {
      this.loading.info = this.$t('graph.searchLoading');
      this.loading.show = true;
      if (!this.selectedNode.more) {
        this.packageDataToObject(name, false);
        this.layoutController(name);
      } else {
        this.allGraphData[name].isUnfold = true;
        this.selectedNode.name = `${name}_unfold`;
        this.layoutNamescope(name, true);
      }
    },
    /**
     * Controls the invoking method of the next step.
     * @param {String} name Name of the namespace to be expanded.
     */
    layoutController(name) {
      if (!this.loading.show) {
        this.loading.info = this.$t('graph.searchLoading');
        this.loading.show = true;
      }
      if (name.includes('/')) {
        const subPath = name.split('/').slice(0, -1).join('/');
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
     * Selecting a node
     * @param {Boolean} needFocus Whether to focus on the node
     */
    selectNode(needFocus = false) {
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
      this.graph.dom.style.transition = '';

      const needDelay = path.length > 1;
      if ((needFocus || needDelay) && node.el) {
        this.selectNodePosition(id, needDelay);
      }
      node.eld3
          .select('polygon, rect, ellipse, path')
          .classed('selected', true);
      this.highlightProxyNodes(id.replace('_unfold', ''));
      this.$refs.tree.setCurrentKey(id.replace('_unfold', ''));
      if (this.isIntoView) {
        this.$nextTick(() => {
          setTimeout(() => {
            const dom = document.querySelector('.el-tree-node.is-current.is-focusable');
            if (dom && this.rightShow) {
              dom.scrollIntoView();
            }
          }, 800);
        });
      }
      this.isIntoView = true;
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
        attributes: [],
      };
      this.selectedNode.showControl = {
        input: true,
        output: true,
      };

      const path = this.selectedNode.name.split('^');
      const selectedNode = this.allGraphData[path[0].replace('_unfold', '')];

      if (selectedNode && !selectedNode.name.includes('more...')) {
        this.selectedNode.show = true;
        this.selectedNode.name = selectedNode.name;
        this.selectedNode.title = selectedNode.name.replace('_unfold', '');
        this.selectedNode.type =
          selectedNode.type === 'name_scope' ||
          selectedNode.type === 'aggregation_scope'
            ? ''
            : selectedNode.type;
        this.selectedNode.countShow =
          selectedNode.type === 'name_scope' ||
          selectedNode.type === 'aggregation_scope';
        this.selectedNode.count = selectedNode.subnode_count;
        const attrTemp = JSON.parse(JSON.stringify(selectedNode.attr || {}));
        if (attrTemp.shape) {
          const shape = JSON.parse(attrTemp.shape);
          if (shape.length) {
            let str = '';
            for (let i = 0; i < shape.length; i++) {
              str += (str ? ',' : '') + JSON.stringify(shape[i]);
            }
            attrTemp.shape = str;
          }
        }

        this.selectedNode.info.attributes = Object.keys(attrTemp).map((key) => {
          return {
            name: key,
            value: attrTemp[key],
          };
        });

        Object.keys(selectedNode.input).forEach((key) => {
          const value = this.getEdgeLabel(selectedNode.input[key]);
          if (selectedNode.input[key].edge_type !== 'control') {
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

        Object.keys(selectedNode.output).forEach((key) => {
          const value = this.getEdgeLabel(selectedNode.output[key]);
          if (selectedNode.output[key].edge_type !== 'control') {
            this.selectedNode.info.output.push({
              name: key,
              scope: selectedNode.output[key].scope,
              value: value,
            });
          } else {
            this.selectedNode.info.outputControl.push({
              name: key,
              scope: selectedNode.output[key].scope,
              value: value,
            });
          }
        });
        this.selectedNode.info.output_i = selectedNode.output_i;
        this.highLightEdges(selectedNode);
      } else {
        this.selectedNode.show = false;
        this.selectedNode.name = '';
        this.selectedNode.title = '';
        this.selectedNode.type = '';
      }
    },
    /**
     * The position is offset to the current node in the center of the screen.
     * @param {String} nodeId Selected Node id
     * @param {Boolean} needDelay Delay required
     */
    selectNodePosition(nodeId, needDelay) {
      const nodeDom = document.querySelector(`#graph0 g[id="${nodeId}"]`);
      const nodeRect = nodeDom.getBoundingClientRect();

      const graph = {};
      graph.rect = this.graph.dom.getBoundingClientRect();
      graph.initWidth = graph.rect.width / this.graph.transform.k;
      graph.initHeight = graph.rect.height / this.graph.transform.k;

      const screenChange = {
        x:
          nodeRect.left +
          nodeRect.width / 2 -
          (this.svg.rect.left + this.svg.rect.width / 2),
        y:
          nodeRect.top +
          nodeRect.height / 2 -
          (this.svg.rect.top + this.svg.rect.height / 2),
      };

      this.graph.transform.x -=
        screenChange.x * (this.svg.originSize.width / graph.initWidth);
      this.graph.transform.y -=
        screenChange.y * (this.svg.originSize.height / graph.initHeight);

      this.graph.dom.setAttribute(
          'transform',
          `translate(${this.graph.transform.x},` +
          `${this.graph.transform.y}) scale(${this.graph.transform.k})`,
      );

      const transitionTime = Math.min(
          Math.abs(screenChange.x) * 2,
          Math.abs(screenChange.y) * 2,
        needDelay ? 800 : 0,
      );

      this.graph.dom.style.transition = `${transitionTime / 1000}s`;
      this.graph.dom.style['transition-timing-function'] = 'linear';

      setTimeout(() => {
        this.graph.dom.style.transition = '';
      }, transitionTime);
      let end = 0;
      this.setInsideBoxData();
      const timer = setInterval(() => {
        this.setInsideBoxData();
        end += 1;
        if (end > transitionTime) {
          clearInterval(timer);
        }
      }, 1);
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
          attributes: [],
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
      this.treeFlag = true;
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
    searchNodesNames() {
      const params = {
        search: this.searchBox.value,
        train_id: this.trainJobID,
        tag: this.fileSearchBox.value,
        offset: 0,
        limit: 1000,
      };
      RequestService.searchNodesNames(params)
          .then(
              (response) => {
                if (response && response.data) {
                  this.treeFlag = false;
                  this.treeWrapFlag = true;
                  this.searchNode.childNodes = [];
                  const data = response.data.nodes.map((val) => {
                    return {
                      label: val.name.split('/').pop(),
                      ...val,
                    };
                  });
                  const currentData = JSON.parse(JSON.stringify(data));
                  currentData.forEach((val) => {
                    val.nodes = [];
                  });
                  this.searchResolve(currentData);
                  data.forEach((val, key) => {
                    if (val.nodes && val.nodes.length) {
                      val.nodes.forEach((value) => {
                        value.parentName = val.name;
                      });
                      this.dealSearchTreeData(val.nodes);
                    }
                  });
                }
              },
              (e) => {
                this.loading.show = false;
              },
          )
          .catch((e) => {
            this.$message.error(this.$t('public.dataError'));
          });
    },
    /**
     * Draw the tree
     * @param {Object} children child node
     */
    dealSearchTreeData(children) {
      children.forEach((val) => {
        const node = this.$refs.searchTree.getNode(val.parentName);
        val.label = val.name.split('/').pop();
        val.leaf =
          val.type === 'name_scope' || val.type === 'aggregation_scope'
            ? false
            : true;
        this.$refs.searchTree.append(val, node);
        node.expanded = true;
        if (val.nodes && val.nodes.length) {
          val.nodes.forEach((value) => {
            value.parentName = val.name;
          });
          this.dealSearchTreeData(val.nodes);
        }
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
        if (
          d3
              .select(`g[id="${option.value}"], g[id="${option.value}_unfold"]`)
              .size()
        ) {
          // If the namespace or aggregation node is expanded, you need to close it and select
          if (!this.allGraphData[option.value].isUnfold) {
            this.selectNode(true);
          } else {
            this.dealDoubleClick(option.value);
          }
        } else {
          const parentId = option.value.substring(
              0,
              option.value.lastIndexOf('/'),
          );
          if (
            this.allGraphData[parentId] &&
            this.allGraphData[parentId].isUnfold
          ) {
            const aggregationNode = this.allGraphData[parentId];
            if (aggregationNode && aggregationNode.childIdsList) {
              for (let i = 0; i < aggregationNode.childIdsList.length; i++) {
                if (aggregationNode.childIdsList[i].includes(option.value)) {
                  aggregationNode.index = i;
                  break;
                }
              }
            }
            this.loading.info = this.$t('graph.searchLoading');
            this.loading.show = true;
            this.selectedNode.name = option.value;

            this.$nextTick(() => {
              setTimeout(() => {
                this.layoutNamescope(parentId, true);
              }, 500);
            });
          }
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
                    const data = this.findStartUnfoldNode(response.data.children);
                    if (data) {
                      this.dealAutoUnfoldNamescopesData(data);
                    }
                    if (response.data.children) {
                      this.dealTreeData(response.data.children, option.value);
                    }
                  }
                },
                (e) => {
                  this.loading.show = false;
                },
            )
            .catch((e) => {
              this.loading.show = false;
              this.$message.error(this.$t('public.dataError'));
            });
      }
    },
    /**
     * Draw the tree
     * @param {Object} children child node
     * @param {String} name The name of the node that needs to be highlighted
     */
    dealTreeData(children, name) {
      if (children.nodes) {
        if (
          (children.nodes.length > this.nodesCountLimit &&
            this.$refs.tree.getNode(children.scope_name).data.type === 'name_scope') ||
          this.allGraphData[children.scope_name].maxChainNum > this.maxChainNum
        ) {
          return;
        }
        const data = children.nodes.map((val) => {
          return {
            label: val.name.split('/').pop(),
            ...val,
          };
        });
        data.forEach((val) => {
          const node = this.$refs.tree.getNode(children.scope_name);
          if (node.childNodes) {
            if (
              node.childNodes
                  .map((value) => value.data.name)
                  .indexOf(val.name) === -1
            ) {
              this.$refs.tree.append(val, node);
            }
          } else {
            this.$refs.tree.append(val, node);
          }
        });
        const node = this.$refs.tree.getNode(children.scope_name);
        node.childNodes.forEach((val) => {
          if (
            val.data.type !== 'name_scope' &&
            val.data.type !== 'aggregation_scope'
          ) {
            val.isLeaf = true;
          }
        });
        node.expanded = true;
        node.loading = false;
      } else {
        this.$refs.tree.setCurrentKey(name);
        this.$nextTick(() => {
          setTimeout(() => {
            const dom = document.querySelector('.el-tree-node.is-current.is-focusable');
            if (dom && this.rightShow) {
              dom.scrollIntoView();
            }
          }, 800);
        });
      }
      if (children.children && Object.keys(children.children).length) {
        this.dealTreeData(children.children, name);
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
            this.$message.error(this.$t('graph.tooManyNodes'));
            this.$nextTick(() => {
              this.loading.show = false;
            });
          } else {
            // Normal expansion
            const nodes = JSON.parse(JSON.stringify(data.nodes));
            this.packageDataToObject(data.scope_name, true, nodes);
            if (
              this.allGraphData[data.scope_name].type === 'aggregation_scope'
            ) {
              this.dealAggregationNodes(data.scope_name);
              const aggregationNode = this.allGraphData[data.scope_name];
              if (aggregationNode) {
                for (let i = 0; i < aggregationNode.childIdsList.length; i++) {
                  if (
                    aggregationNode.childIdsList[i].includes(
                        this.selectedNode.name,
                    )
                  ) {
                    aggregationNode.index = i;
                    break;
                  }
                }
              }
              if (
                this.allGraphData[data.scope_name].maxChainNum >
                this.maxChainNum
              ) {
                this.selectedNode.name = data.scope_name;
                this.allGraphData[data.scope_name].isUnfold = false;
                this.deleteNamespace(data.scope_name);
                this.$message.error(this.$t('graph.tooManyChain'));
                this.$nextTick(() => {
                  this.loading.show = false;
                });
                return;
              }
            }

            if (data.children.scope_name) {
              this.dealAutoUnfoldNamescopesData(data.children);
            } else {
              this.loading.info = this.$t('graph.searchLoading');
              this.loading.show = true;
              this.$nextTick(() => {
                setTimeout(() => {
                  this.layoutNamescope(data.scope_name, true);
                }, 200);
              });
            }
          }
        }
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
        this.initSvg(false);
        this.initGraphRectData();
      }, 500);
    },
    /**
     * Full-screen display
     */
    toggleScreen() {
      this.fullScreen = !this.fullScreen;
      setTimeout(() => {
        this.initSvg(false);
        this.initGraphRectData();
      }, 500);
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

      const downloadLink = document.createElement('a');
      downloadLink.download = 'graph.svg';
      downloadLink.style.display = 'none';
      const blob = new Blob([encodeStr], {type: 'text/html'});
      downloadLink.href = URL.createObjectURL(blob);
      document.body.appendChild(downloadLink);
      downloadLink.click();
      document.body.removeChild(downloadLink);
    },
    /**
     * Fold the legend area.
     */
    foldLegend() {
      this.showLegend = !this.showLegend;
    },
    /**
     * Control Display User Guide
     */
    showUserGuide() {
      this.guide.content = [
        this.$t('graph.guideContent11'),
        this.$t('graph.guideContent12'),
        this.$t('graph.guideContent13'),
        this.$t('graph.guideContent14'),
      ];
      this.guide.show = true;
      this.guide.step = 1;
    },
    /**
     * Close user guide
     */
    closeUserGuide() {
      this.guide.show = false;
    },
    /**
     * Show the next step
     */
    guideNext() {
      if (this.guide.step < 3) {
        this.guide.step++;
        switch (this.guide.step) {
          case 2:
            this.guide.content = [this.$t('graph.guideContent2')];
            break;
          case 3:
            this.guide.content = [this.$t('graph.guideContent3')];
            break;
          default:
            break;
        }
      } else if (this.guide.step >= 3) {
        this.guide.show = false;
      }
    },
    /**
     * jump back to train dashboard
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
  // Components imported by the page
  components: {},
};
</script>
<style>
.tooltip-container .cl-graph-sidebar-tip {
  word-break: normal;
}

.cl-graph-manage {
  height: 100%;
}
.cl-graph-manage .cl-graph-title {
  height: 50px;
  line-height: 50px;
}
.cl-graph-manage .cl-graph-title .path-message {
  display: inline-block;
  line-height: 20px;
  padding: 0px 4px 15px 4px;
  font-weight: bold;
  vertical-align: bottom;
}
.cl-graph-manage .cl-graph-title .guide {
  cursor: pointer;
  margin-left: 10px;
  display: inline-block;
  line-height: 18px;
  font-size: 12px;
}
.cl-graph-manage .cl-graph-title .guide .guide-icon {
  display: inline-block;
  width: 16px;
  height: 16px;
  vertical-align: -2.5px;
  margin-right: 4px;
  background: url("../../assets/images/guideIcon.svg");
}
.cl-graph-manage .cl-graph-title .guide:hover {
  color: #00a5a7;
}
.cl-graph-manage .cl-graph-title .guide:hover .guide-icon {
  background: url("../../assets/images/guideIconHover.svg");
}
.cl-graph-manage .graph-p32 {
  height: 100%;
  position: relative;
}
.cl-graph-manage .graph-p32 .guide-content {
  height: 100%;
  width: 100%;
  position: absolute;
  background-color: #c6c8cc;
  z-index: 9999;
}
.cl-graph-manage .graph-p32 .guide-content .step-pic {
  text-align: center;
  margin-top: 8px;
}
.cl-graph-manage .graph-p32 .guide-content .step {
  height: 100%;
  background-repeat: round;
  user-select: none;
}
.cl-graph-manage .graph-p32 .guide-content .step img {
  width: 100%;
}
.cl-graph-manage .graph-p32 .guide-content .guide-span {
  font-size: 12px;
  color: #575d6c;
  line-height: 18px;
  text-align: left;
  display: inline-block;
}
.cl-graph-manage .graph-p32 .guide-content .el-popover .el-icon-close {
  cursor: pointer;
  position: absolute;
  right: 10px;
  top: 13px;
  font-size: 20px;
}
.cl-graph-manage .graph-p32 .guide-content .el-popover .el-icon-close:hover {
  color: #00a5a7;
}
.cl-graph-manage .graph-p32 .guide-content .el-popover__title {
  font-size: 16px;
  color: #252b3a;
  line-height: 24px;
  font-weight: bold;
}
.cl-graph-manage .graph-p32 .guide-content .el-button {
  display: block;
  float: right;
  height: 28px;
  line-height: 27px;
  border-radius: 0;
  padding: 0 20px;
}
.cl-graph-manage .cl-content {
  height: calc(100% - 50px);
  overflow: auto;
}
.cl-graph-manage #graphs {
  width: 100%;
  height: 100%;
  font-size: 0;
  background: #f0f2f5;
}
.cl-graph-manage #graphs .search {
  margin-bottom: 15px;
  width: 100%;
}
.cl-graph-manage #graphs .search-wrap {
  position: relative;
}
.cl-graph-manage #graphs .search-wrap .tree-wrap {
  position: absolute;
  left: 0;
  top: 32px;
  z-index: 101;
  width: 100%;
  max-height: 224px;
  overflow: auto;
  border: 1px solid #dcdfe6;
  border-top: none;
  background: #fff;
}
.cl-graph-manage #graphs .search-wrap .tree-wrap .image-type {
  width: 20px;
  height: 10px;
  margin-right: 10px;
}
.cl-graph-manage #graphs .search-wrap .tree-wrap .el-tree > .el-tree-node {
  min-width: 100%;
  display: inline-block;
}
.cl-graph-manage #graphs .search-wrap .tree-wrap .el-tree .custom-tree-node {
  padding-right: 8px;
}
.cl-graph-manage #graphs .search-wrap .collapse_i {
  cursor: pointer;
}
.cl-graph-manage #graphs .cl-graph {
  position: relative;
  width: 100%;
  height: 100%;
  background-color: #fff;
  padding: 0 32px 10px;
  min-height: 700px;
  overflow: hidden;
}
.cl-graph-manage #graphs .cl-graph.full-screen {
  position: absolute;
  top: 0;
  bottom: 0;
  left: -280px;
  right: 0;
  width: auto;
  height: auto;
  padding: 0;
}
.cl-graph-manage #graphs .cl-graph.full-screen #sidebar .node-info-con {
  height: calc(100% - 300px);
}
.cl-graph-manage #graphs .cl-graph.full-screen .graph-container {
  width: 100%;
}
.cl-graph-manage #graphs #sidebar.right-hide {
  right: -442px;
}
.cl-graph-manage #graphs #sidebar {
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
  padding: 18px 32px 10px;
}
.cl-graph-manage #graphs #sidebar .sidebar-tooltip {
  position: absolute;
  height: 32px;
  top: 18px;
  left: 10px;
  display: flex;
  align-items: center;
  font-size: 16px;
  color: #6c7280;
}
.cl-graph-manage #graphs #sidebar div,
.cl-graph-manage #graphs #sidebar span,
.cl-graph-manage #graphs #sidebar pre {
  font-size: 14px;
}
.cl-graph-manage #graphs #sidebar #small-container {
  height: 209px;
  width: 100%;
  z-index: 100;
  border: 1px solid #e6ebf5;
  overflow: hidden;
  background-color: white;
  position: relative;
}
.cl-graph-manage #graphs #sidebar #small-container #small-resize {
  width: 100%;
  height: 100%;
  position: absolute;
  left: 0;
  top: 0;
}
.cl-graph-manage #graphs #sidebar #small-container #small-map {
  height: 100%;
  width: 100%;
  position: relative;
  padding: 0;
}
.cl-graph-manage #graphs #sidebar #small-container #inside-box {
  background-color: #5b88f1;
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
.cl-graph-manage #graphs #sidebar .title {
  padding: 20px 0;
  font-size: 14px;
  color: #333333;
}
.cl-graph-manage #graphs #sidebar .title img {
  float: right;
  margin-right: 10px;
  cursor: pointer;
}
.cl-graph-manage #graphs #sidebar .graph-controls {
  padding: 10px 20px 0 20px;
}
.cl-graph-manage #graphs #sidebar .graph-controls div {
  cursor: pointer;
  display: inline-block;
  margin-left: 20px;
}
.cl-graph-manage #graphs #sidebar .graph-controls img {
  cursor: pointer;
  vertical-align: middle;
}
.cl-graph-manage #graphs #sidebar .node-info-con ::-webkit-scrollbar-button {
  z-index: 200;
  width: 10px;
  height: 10px;
  background: #fff;
  cursor: pointer;
}
.cl-graph-manage #graphs #sidebar .node-info-con ::-webkit-scrollbar-button:horizontal:single-button:start {
  background-image: url("../../assets/images/scroll-btn-left.png");
  background-position: center;
}
.cl-graph-manage #graphs #sidebar .node-info-con ::-webkit-scrollbar-button:horizontal:single-button:end {
  background-image: url("../../assets/images/scroll-btn-right.png");
  background-position: center;
}
.cl-graph-manage #graphs #sidebar .node-info-con ::-webkit-scrollbar-button:vertical:single-button:start {
  background-image: url("../../assets/images/scroll-btn-up.png");
  background-position: center;
}
.cl-graph-manage #graphs #sidebar .node-info-con ::-webkit-scrollbar-button:vertical:single-button:end {
  background-image: url("../../assets/images/scroll-btn-down.png");
  background-position: center;
}
.cl-graph-manage #graphs #sidebar .node-info-con ::-webkit-scrollbar-thumb {
  background-color: #bac5cc;
}
.cl-graph-manage #graphs #sidebar .node-info-con ::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.cl-graph-manage #graphs #sidebar .node-info-container {
  height: calc(100% - 451px);
}
.cl-graph-manage #graphs #sidebar .node-info-container-long {
  height: calc(100% - 357px);
}
.cl-graph-manage #graphs #sidebar .node-info {
  font-size: 14px;
  padding: 0 20px;
  height: calc(100% - 54px);
  overflow: auto;
  color: #333;
  background-color: #f7faff;
}
.cl-graph-manage #graphs #sidebar .node-info .clear {
  clear: both;
}
.cl-graph-manage #graphs #sidebar .node-info .hover li:hover {
  background: #fce8b2;
}
.cl-graph-manage #graphs #sidebar .node-info .hover .control-list .dependence-title {
  line-height: 30px;
  cursor: pointer;
  font-weight: bold;
}
.cl-graph-manage #graphs #sidebar .node-info .hover .control-list .dependence-title img {
  vertical-align: middle;
  margin-right: 3px;
}
.cl-graph-manage #graphs #sidebar .node-info .hover .control-list .dependence-title.hide img {
  margin-top: -3px;
  transform: rotate(-90deg);
}
.cl-graph-manage #graphs #sidebar .node-info .hover .control-list li:hover {
  background: #fce8b2;
}
.cl-graph-manage #graphs #sidebar .node-info .hover .control-list:hover {
  background: none;
}
.cl-graph-manage #graphs #sidebar .node-info .pointer {
  cursor: pointer;
}
.cl-graph-manage #graphs #sidebar .node-info .item-content {
  max-height: calc(50% - 95px);
  overflow: auto;
}
.cl-graph-manage #graphs #sidebar .node-info .item-content li {
  min-width: 100%;
  width: max-content;
}
.cl-graph-manage #graphs #sidebar .node-info .item-min {
  min-height: 50px;
}
.cl-graph-manage #graphs #sidebar .node-info .item-min2 {
  min-height: 87px;
}
.cl-graph-manage #graphs #sidebar .node-info .items {
  line-height: 20px;
  padding: 9px 0;
}
.cl-graph-manage #graphs #sidebar .node-info .items .items-over {
  max-height: 60px;
  overflow: auto;
}
.cl-graph-manage #graphs #sidebar .node-info .items .item {
  color: #999;
}
.cl-graph-manage #graphs #sidebar .node-info .shape {
  vertical-align: top;
  width: 50px;
  word-break: break-all;
  display: inline-table;
  position: absolute;
  left: 0;
}
.cl-graph-manage #graphs #sidebar .node-info .key {
  vertical-align: top;
  width: 60px;
  word-break: break-all;
  display: inline-table;
}
.cl-graph-manage #graphs #sidebar .node-info .label {
  vertical-align: top;
  width: 70px;
  word-break: break-all;
  display: inline-block;
}
.cl-graph-manage #graphs #sidebar .node-info .value {
  vertical-align: top;
  display: inline-block;
  width: calc(100% - 70px);
  white-space: nowrap;
  overflow: auto;
}
.cl-graph-manage #graphs #sidebar .node-info .size {
  width: 310px;
  font-size: 12px;
  text-align: right;
}
.cl-graph-manage #graphs #sidebar .node-info .input {
  width: 100%;
  position: relative;
  display: inline-block;
  white-space: nowrap;
}
.cl-graph-manage #graphs #sidebar .node-info ul li {
  line-height: 20px;
}
.cl-graph-manage #graphs #sidebar .legend .legend-content {
  background-color: #f7faff;
  padding: 0 32px;
  height: 94px;
  overflow-y: auto;
}
.cl-graph-manage #graphs #sidebar .legend .legend-item {
  padding: 5px 0;
  display: inline-block;
  width: 50%;
  font-size: 14px;
  line-height: 20px;
}
.cl-graph-manage #graphs #sidebar .legend .legend-item .pic {
  width: 45px;
  text-align: center;
  display: inline-block;
  padding-left: 20px;
  vertical-align: middle;
}
.cl-graph-manage #graphs #sidebar .legend .legend-item .pic img {
  max-width: 45px;
  max-height: 15px;
  margin-left: -20px;
  vertical-align: middle;
}
.cl-graph-manage #graphs #sidebar .legend .legend-item .legend-text {
  display: inline-block;
  padding-left: 20px;
  width: calc(100% - 45px);
  vertical-align: middle;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cl-graph-manage #graphs #sidebar .legend .legend-item .legend-text:hover {
  cursor: default;
}
.cl-graph-manage #graphs #sidebar .toggle-right {
  position: absolute;
  top: calc(50% - 43px);
  left: -16px;
  width: 18px;
  height: 86px;
  cursor: pointer;
  background-image: url("../../assets/images/toggle-right-bg.png");
}
.cl-graph-manage #graphs #sidebar .icon-toggle {
  width: 6px;
  height: 9px;
  background-image: url("../../assets/images/toggle-right-icon.png");
  position: absolute;
  top: calc(50% - 4.5px);
  left: calc(50% - 3px);
}
.cl-graph-manage #graphs #sidebar .icon-toggle.icon-left {
  transform: rotateY(180deg);
}
.cl-graph-manage #graphs .operate-button-list {
  position: absolute;
  right: 0;
  top: 0;
  z-index: 100;
}
.cl-graph-manage #graphs .operate-button-list div {
  cursor: pointer;
  width: 12px;
  height: 12px;
  display: inline-block;
  margin: 5px;
}
.cl-graph-manage #graphs .operate-button-list .download-button {
  background-image: url("../../assets/images/download.png");
}
.cl-graph-manage #graphs .operate-button-list .full-screen-button {
  background-image: url("../../assets/images/full-screen.png");
}
.cl-graph-manage #graphs .graph-container.all {
  width: 100%;
}
.cl-graph-manage #graphs .graph-container .node:hover > path,
.cl-graph-manage #graphs .graph-container .node:hover > ellipse,
.cl-graph-manage #graphs .graph-container .node:hover > polygon,
.cl-graph-manage #graphs .graph-container .node:hover > rect {
  stroke-width: 2px;
}
.cl-graph-manage #graphs .graph-container .node.cluster > rect:hover {
  stroke: #8df1f2;
}
.cl-graph-manage #graphs .graph-container .selected {
  stroke: red !important;
  stroke-width: 2px;
}
.cl-graph-manage #graphs .graph-container,
.cl-graph-manage #graphs #small-map {
  font-size: 16px;
  position: relative;
  display: inline-block;
  width: calc(100% - 442px);
  height: calc(100% - 5px);
  text-align: left;
  -webkit-touch-callout: none;
  -webkit-user-select: none;
  -khtml-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;
}
.cl-graph-manage #graphs .graph-container .graph,
.cl-graph-manage #graphs #small-map .graph {
  height: 100%;
  background-color: #f7faff;
}
.cl-graph-manage #graphs .graph-container #graph0 > polygon,
.cl-graph-manage #graphs #small-map #graph0 > polygon {
  fill: transparent;
}
.cl-graph-manage #graphs .graph-container .node,
.cl-graph-manage #graphs #small-map .node {
  cursor: pointer;
}
.cl-graph-manage #graphs .graph-container .edge path,
.cl-graph-manage #graphs #small-map .edge path {
  stroke: #787878;
}
.cl-graph-manage #graphs .graph-container .edge polygon,
.cl-graph-manage #graphs #small-map .edge polygon {
  fill: #787878;
}
.cl-graph-manage #graphs .graph-container .edge.highlighted path,
.cl-graph-manage #graphs #small-map .edge.highlighted path {
  stroke: red;
}
.cl-graph-manage #graphs .graph-container .edge.highlighted polygon,
.cl-graph-manage #graphs #small-map .edge.highlighted polygon {
  stroke: red;
  fill: red;
}
.cl-graph-manage #graphs .graph-container .edge.highlighted marker path,
.cl-graph-manage #graphs #small-map .edge.highlighted marker path {
  fill: red;
}
.cl-graph-manage #graphs .graph-container .node.aggregation > polygon,
.cl-graph-manage #graphs #small-map .node.aggregation > polygon {
  stroke: #e3aa00;
  fill: #ffe794;
}
.cl-graph-manage #graphs .graph-container .node.cluster.aggregation > rect,
.cl-graph-manage #graphs #small-map .node.cluster.aggregation > rect {
  stroke: #e3aa00;
  fill: #ffe794;
  stroke-dasharray: 3, 3;
}
.cl-graph-manage #graphs .graph-container .node > polygon,
.cl-graph-manage #graphs #small-map .node > polygon {
  stroke: #00a5a7;
  fill: #8df1f2;
}
.cl-graph-manage #graphs .graph-container .node > ellipse,
.cl-graph-manage #graphs #small-map .node > ellipse {
  stroke: #4ea6e6;
  fill: #b8e0ff;
}
.cl-graph-manage #graphs .graph-container .plain > path,
.cl-graph-manage #graphs .graph-container .plain ellipse,
.cl-graph-manage #graphs #small-map .plain > path,
.cl-graph-manage #graphs #small-map .plain ellipse {
  stroke: #e37d29;
  fill: #ffd0a6;
  stroke-dasharray: 1.5, 1.5;
}
.cl-graph-manage #graphs .graph-container .edge-point ellipse,
.cl-graph-manage #graphs #small-map .edge-point ellipse {
  stroke: #a7a7a7;
  fill: #a7a7a7;
}
.cl-graph-manage #graphs .graph-container text,
.cl-graph-manage #graphs #small-map text {
  fill: black;
}
.cl-graph-manage #graphs .image-noData {
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
.cl-graph-manage #graphs .noData-text {
  margin-top: 33px;
  font-size: 18px;
}
.cl-graph-manage .cl-display-block {
  display: block;
}
.cl-graph-manage .cl-input-value {
  width: calc(100% - 70px) !important;
  margin-left: 10px !important;
}
.cl-graph-manage .cl-close-btn {
  width: 20px;
  height: 20px;
  vertical-align: -3px;
  cursor: pointer;
  display: inline-block;
}
.cl-graph-manage .cl-title-right {
  padding-right: 32px;
}

#graphTemp,
#subgraphTemp {
  position: absolute;
  bottom: 0;
  visibility: hidden;
}
</style>

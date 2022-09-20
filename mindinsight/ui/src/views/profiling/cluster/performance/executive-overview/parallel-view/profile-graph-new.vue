<!--
Copyright 2022 Huawei Technologies Co., Ltd.All Rights Reserved.

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
  <div class="profile-graph">
    <div
      class="profile-graph-tooltip"
      v-if="hoveredNodeInfo !== null"
      :style="{
        transform: `translate(${hoveredNodeInfo.x}px, ${hoveredNodeInfo.y}px)`,
      }"
    >
      <div
        class="profile-graph-tooltip-title"
        v-html="`Node ID: ${hoveredNodeInfo.node.id}`"
      ></div>
      <div class="profile-graph-tooltip-content">
        <div class="col">
          <div class="left">type:</div>
          <div class="right" v-html="hoveredNodeInfo.node.type"></div>
        </div>
        <div class="col">
          <div class="left">scope:</div>
          <div class="right">
            <div
              v-for="(scope, index) in hoveredNodeInfo.node.scope.split('/')"
              :key="'host_tooltip' + scope + index"
              v-html="`${scope}/`"
            ></div>
          </div>
        </div>
        <div class="col">
          <div class="left">inputs:</div>
          <div class="right">
            <div
              v-for="input in hoveredNodeInfo.node.input"
              :key="'host_hoveredNode_input' + input"
              v-html="
                `${input}${
                  !isNaN(input)
                    ? nodeMaps[hoveredNodeInfo.nodeGroupIndex][input].type
                    : ''
                }`
              "
            ></div>
          </div>
        </div>
        <div class="col">
          <div class="left">output:</div>
          <div class="right">
            <div
              v-for="output in hoveredNodeInfo.node.output"
              :key="'host_hoveredNode_output' + output"
              v-html="
                `${output}${
                  !isNaN(output)
                    ? nodeMaps[hoveredNodeInfo.nodeGroupIndex][output].type
                    : ''
                }`
              "
            ></div>
          </div>
        </div>
      </div>
    </div>
    <svg class="svgCanvas">
      <defs>
        <clipPath id="wrapperClipPath" class="wrapper clipPath">
          <rect class="background"></rect>
        </clipPath>
        <clipPath id="minimapClipPath" class="minimap clipPath">
          <rect class="background"></rect>
        </clipPath>
        <filter id="minimapDropShadow" width="150%" height="150%">
          <feOffset result="offOut" in="SourceGraphic" dx="1" dy="1"></feOffset>
          <feColorMatrix
            result="matrixOut"
            in="offOut"
            type="matrix"
            values="0.1 0 0 0 0 0 0.1 0 0 0 0 0 0.1 0 0 0 0 0 0.5 0"
          ></feColorMatrix>
          <feGaussianBlur
            result="blurOut"
            in="matrixOut"
            stdDeviation="10"
          ></feGaussianBlur>
          <feBlend in="SourceGraphic" in2="blurOut" mode="normal"></feBlend>
        </filter>
        <radialGradient
          id="minimapGradient"
          gradientUnits="userSpaceOnUse"
          cx="500"
          cy="500"
          r="400"
          fx="500"
          fy="500"
        >
          <stop offset="0%" stop-color="#FFFFFF"></stop>
          <stop offset="40%" stop-color="#EEEEEE"></stop>
          <stop offset="100%" stop-color="#E0E0E0"></stop>
        </radialGradient>
      </defs>
      <g class="wrapperOuter">
        <rect class="background"></rect>
        <g class="wrapperInner">
          <rect class="background"></rect>
          <g class="panCanvas">
            <svg id="profile-graph" style="width: 100%; height: 100%">
              <defs>
                <radialGradient
                  v-for="namespace in selectNamespaces"
                  :id="namespace + '_halo'"
                  :key="'host' + namespace + '_halo'"
                  x1="0"
                  x2="0"
                  y1="0"
                  y2="1"
                >
                  <stop offset="0%" :stop-color="haloColorScale(namespace)" />
                  <stop offset="100%" stop-color="rgba(255,255,255,0)" />
                </radialGradient>
                <radialGradient id="highlight_halo" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" :stop-color="'yellow'" />
                  <stop offset="100%" stop-color="rgba(255,255,255,0)" />
                </radialGradient>
              </defs>

              <g ref="graph-container" id="graph-container">
                <g
                  id="pipeline-extra-container"
                  v-if="isPipelineLayout && nodeOrder.length > 0"
                >
                  <text
                    v-for="(opNode, index) in opNodes"
                    :key="'host_extra' + index"
                    :x="bgdRectBlocks[0].x - 200"
                    :y="bgdRectBlocks[0].y + 250 * (2 * index + 1)"
                    style="font-size: 40; font-weight: bold"
                  >
                    Stage {{ index }}
                  </text>
                  <rect
                    v-for="(bgdRectBlock, index) in bgdRectBlocks"
                    :key="'host' + `${index}_bgdRectBlock`"
                    :x="bgdRectBlock.x"
                    :y="bgdRectBlock.y"
                    :width="bgdRectBlock.width"
                    :height="bgdRectBlock.height"
                    stroke-dasharray="5"
                    style="stroke: #ababab; fill: none; stroke-width: 2"
                  ></rect>
                </g>

                <g id="graph-halo-container">
                  <g
                    v-for="([namespace, nodeGroup], index) in haloInfo"
                    :key="'host_haloInfo' + namespace + index"
                  >
                    <circle
                      v-for="node in nodeGroup.filter((v) => v !== undefined)"
                      :key="'host' + node.id + 'halo' + index"
                      :cx="node.x"
                      :cy="node.y"
                      r="50"
                      :fill="`url(#${namespace}_halo)`"
                    ></circle>
                  </g>
                </g>
                <g id="graph-highlight-container">
                  <circle
                    v-for="(node, index) in selectHighlightNodes"
                    :key="'host_hightlight_' + index"
                    :cx="node.x"
                    :cy="node.y"
                    r="50"
                    :fill="`url(#highlight_halo)`"
                  ></circle>
                </g>

                <g id="graph-edge-container">
                  <g id="normal-edge-container">
                    <g
                      v-for="(normalEdgesGroup, groupIndex) in normalEdgesShow"
                      :key="'host_normalEdge_group' + groupIndex"
                    >
                      <line
                        v-for="(edge, index) in normalEdgesGroup"
                        :key="'host_normal_edge' + index"
                        :x1="edge.source.x"
                        :y1="edge.source.y"
                        :x2="edge.target.x"
                        :y2="edge.target.y"
                      ></line>
                    </g>
                  </g>
                  <g id="special-edge-container" v-show="isShowHiddenEdges">
                    <g
                      v-for="(specialEdgesGroup, groupIndex) in specialEdges"
                      :key="'host_specialEdge_group' + groupIndex"
                    >
                      <g
                        v-for="cls in Object.keys(specialEdgesGroup)"
                        :key="'host_special_edge' + cls"
                      >
                        <path
                          v-for="(edge, index) in specialEdgesGroup[cls].values"
                          :key="'host_special_path' + index"
                          :class="cls"
                          :d="
                            specialEdgesGroup[cls].path(edge.source, edge.target)
                          "
                        ></path>
                      </g>
                    </g>
                  </g>
                </g>

                <g id="graph-hovernode-edge-container">
                  <line
                    v-for="(edge, index) in hoverNodeEdges"
                    style="stroke: #cb6056"
                    :key="'host_hovernode_edge' + index"
                    :x1="edge.source.x"
                    :y1="edge.source.y"
                    :x2="edge.target.x"
                    :y2="edge.target.y"
                  ></line>
                </g>

                <g id="graph-node-container" fill="var(--font-color)">
                  <g
                    id="isomorphic-subgraph-circle-g"
                    v-for="(circle, circleIndex) in isomorphicSubgraphCircles"
                    :key="'host_isomorphic_circle' + circleIndex"
                  >
                    <ellipse
                      class="isomorphic-subgraph-circle"
                      :rx="circle.rx"
                      :ry="circle.ry"
                      :cx="circle.x"
                      :cy="circle.y"
                    />
                    <text
                      class="isomorphic-subgraph-text"
                      v-html="`x${circle.n}`"
                      :x="circle.x"
                      :y="circle.y - circle.ry + 15"
                      style="font-size: 15; font-weight: bold"
                    ></text>
                  </g>
                  <g
                    v-for="(opNodesGroup, groupIndex) in opNodesShow"
                    :key="'host_opNode' + groupIndex"
                  >
                    <g
                      v-for="node in opNodesGroup.filter(
                        (v) => v.x !== undefined
                      )"
                      :key="'host_opNode_g' + node.id"
                      @click="onNodeClick(node)"
                      @mouseover="onNodeMouseover($event, node)"
                      @mouseout="onNodeMouseout"
                      :class="clickedNodeId === node.id ? 'active' : ''"
                    >
                      <circle
                        :cx="node.x"
                        :cy="node.y"
                        :r="node.r"
                        :class="`${
                          node.instance_type
                            ? node.instance_type.toLowerCase()
                            : node.type.toLowerCase()
                        } ${
                          node.parallel_shard.length !== 0 ? ' strategy ' : ''
                        } node${node.isAggreNode ? ' aggre-node' : ''}`"
                      ></circle>
                      <circle
                        v-if="node.isAggreNode"
                        :cx="node.x + 2"
                        :cy="node.y + 2"
                        :r="node.r"
                        :class="`${
                          node.instance_type
                            ? node.instance_type.toLowerCase()
                            : node.type.toLowerCase()
                        } node${node.isAggreNode ? ' aggre-node' : ''}`"
                      ></circle>
                      <circle
                        v-if="node.isAggreNode"
                        :cx="node.x + 4"
                        :cy="node.y + 4"
                        :r="node.r"
                        :class="`${
                          node.instance_type
                            ? node.instance_type.toLowerCase()
                            : node.type.toLowerCase()
                        } node${node.isAggreNode ? ' aggre-node' : ''}`"
                      ></circle>
                      <text
                        :x="node.x - 10"
                        :y="node.y + 20"
                        v-html="`${node.id} ${node.type}`"
                      ></text>
                    </g>
                  </g>
                </g>

                <g id="parallel-strategy-container">
                  <g
                    v-for="(value, key) in parallelStrategyParas"
                    :key="'host' + `${key}_strategy_group`"
                  >
                    <g
                      v-for="(item, index) in value"
                      :key="'host' + `${key}_${index}_strategy`"
                    >
                      <g
                        v-for="(rect, index1) in item.rects"
                        :key="'host' + `${key}_${index}_${index1}_rect`"
                        :transform="`rotate(${item.theta},${item.rotateCenter[0]},${item.rotateCenter[1]})`"
                      >
                        <rect
                          :x="rect[0]"
                          :y="rect[1]"
                          :width="rect[2]"
                          :height="rect[3]"
                          :fill="item.colors[index1]"
                          stroke="white"
                          stroke-width="0.1px"
                        ></rect>
                        <text
                          dx="-1"
                          dy="1.5"
                          :transform="`matrix(0.5 0 0 0.5 ${item.textsPos[index1][0]} ${item.textsPos[index1][1]})`"
                        >
                          {{ item.texts[index1] }}
                        </text>
                      </g>
                    </g>
                  </g>
                </g>
              </g>
            </svg>
          </g>
        </g>
      </g>
      <g class="minimap">
        <g class="minipanCanvas">
          <rect class="background" id="minimap-background"></rect>
          <svg id="profile-graph" style="width: 100%; height: 100%">
            <defs>
              <radialGradient
                v-for="namespace in selectNamespaces"
                :id="namespace + '_halo'"
                :key="'mini_' + namespace + '_halo'"
                x1="0"
                x2="0"
                y1="0"
                y2="1"
              >
                <stop offset="0%" :stop-color="haloColorScale(namespace)" />
                <stop offset="100%" stop-color="rgba(255,255,255,0)" />
              </radialGradient>
            </defs>

            <g ref="graph-container" id="graph-container">
              <g
                id="pipeline-extra-container"
                v-if="isPipelineLayout && nodeOrder.length > 0"
              >
                <text
                  v-for="(opNode, index) in opNodes"
                  :key="'mini_extra_' + index"
                  :x="bgdRectBlocks[0].x - 200"
                  :y="bgdRectBlocks[0].y + 250 * (2 * index + 1)"
                  style="font-size: 40; font-weight: bold"
                >
                  Stage {{ index }}
                </text>
                <rect
                  v-for="(bgdRectBlock, index) in bgdRectBlocks"
                  :key="'mini_' + `${index}_bgdRectBlock`"
                  :x="bgdRectBlock.x"
                  :y="bgdRectBlock.y"
                  :width="bgdRectBlock.width"
                  :height="bgdRectBlock.height"
                  stroke-dasharray="5"
                  style="stroke: #ababab; fill: none; stroke-width: 2"
                ></rect>
              </g>
              <g id="graph-edge-container">
                <g id="normal-edge-container">
                  <g
                    v-for="(normalEdgesGroup, groupIndex) in normalEdgesShow"
                    :key="'host_normalEdge_group' + groupIndex"
                  >
                    <line
                      v-for="(edge, index) in normalEdgesGroup"
                      :key="'host_normal_edge' + index"
                      :x1="edge.source.x"
                      :y1="edge.source.y"
                      :x2="edge.target.x"
                      :y2="edge.target.y"
                    ></line>
                  </g>
                </g>
              </g>
              <g id="graph-node-container">
                <g
                  id="isomorphic-subgraph-circle-g"
                  v-for="(circle, circleIndex) in isomorphicSubgraphCircles"
                  :key="'mini_isomorphic_circle' + circleIndex"
                >
                  <ellipse
                    class="isomorphic-subgraph-circle"
                    :rx="circle.rx"
                    :ry="circle.ry"
                    :cx="circle.x"
                    :cy="circle.y"
                  />
                  <text
                    class="isomorphic-subgraph-text"
                    v-html="`x${circle.n}`"
                    :x="circle.x"
                    :y="circle.y - circle.ry + 15"
                    style="font-size: 15; font-weight: bold"
                  ></text>
                </g>
                <g
                  v-for="(opNodesGroup, groupIndex) in opNodes"
                  :key="'mini_opNode_group' + groupIndex"
                >
                  <g
                    v-for="node in opNodesGroup
                      .filter((v) => v.x !== undefined)"
                    :key="'mini_opNode_group_g' + node.id"
                    :class="clickedNodeId === node.id ? 'active' : ''"
                  >
                    <circle
                      :cx="node.x"
                      :cy="node.y"
                      :r="node.r * 4"
                      :class="`${
                        node.instance_type
                          ? node.instance_type.toLowerCase()
                          : node.type.toLowerCase()
                      } ${
                        node.parallel_shard.length !== 0 ? ' strategy ' : ''
                      } node${node.isAggreNode ? ' aggre-node' : ''}`"
                    ></circle>
                    <circle
                      v-if="node.isAggreNode"
                      :cx="node.x + 2"
                      :cy="node.y + 2"
                      :r="node.r"
                      :class="`${
                        node.instance_type
                          ? node.instance_type.toLowerCase()
                          : node.type.toLowerCase()
                      } node${node.isAggreNode ? ' aggre-node' : ''}`"
                    ></circle>
                    <circle
                      v-if="node.isAggreNode"
                      :cx="node.x + 4"
                      :cy="node.y + 4"
                      :r="node.r"
                      :class="`${
                        node.instance_type
                          ? node.instance_type.toLowerCase()
                          : node.type.toLowerCase()
                      } node${node.isAggreNode ? ' aggre-node' : ''}`"
                    ></circle>
                    <text
                      :x="node.x - 10"
                      :y="node.y + 20"
                      v-html="`${node.id} ${node.type}`"
                    ></text>
                  </g>
                </g>
              </g>
            </g>
          </svg>
        </g>
        <g class="frame">
          <rect class="background"></rect>
        </g>
      </g>
    </svg>
  </div>
</template>

<script>
import $store from "../store";
import {
  buildGraph,
  buildGraphOld,
  processedGraph,
  getPipelineBlockInfo,
  buildPipelinedStageInfo,
  resetTreeData,
  getStrategyInfo,
  resetSpecialNodesMap,
} from "@/js/profile-graph/build-graph.js";
import * as d3 from "d3";
import { layout } from "@/js/profile-graph/force-layout.js";
import { extractVisNodeAndEdge } from "@/js/profile-graph/graph-process.js";
import { Canvas } from "@/js/profile-graph/canvas.js";
import * as _ from "lodash";

export default {
  data() {
    return {
      selectNamespaces: [],
      nodeMaps: [],
      treeData: [],
      nodeBlocks: [],
      nodeOrder: [],
      dependNodes: {},
      bgdRectBlocks: [],
      opNodes: [],
      opNodesShow: [],
      idToIndexs: [],
      normalEdges: [],
      normalEdgesShow: [],
      specialEdges: [],
      specialEdgeTypes: [],
      showSpecialEdgeTypes: [],
      hoveredNodeInfo: null,
      isPipelineLayout: false,
      parallelStrategyRawData: null,
      parallelStrategyParas: null,
      normalEdgesBackup: [],
      extraEdges: {},
      graphData: {},
      clickedNodeId: "",
      isomorphicSubgraphCircles: [],
      canvas: null,
      hoverNodeEdges: [],
      nodeEdgesMap: {},
      selectHighlightNodes: [],
      oldHaloInfo: [],
      boxTransform: [0, 0],
    };
  },
  props: ['isShowHiddenEdges'],
  watch: {
    storeGraphData: function (val) {
      this.graphData = val;
      this.initGraph();
      this.$nextTick(() => {
        this.initMiniMap();
        this.initNodeEdgeMap();
      });
    },
    storeProfileShowSpecialEdgeTypes: function (val) {
      for (const showSpecialEdgeType of val[0]) {
        for (const specialEdgesGroup of this.specialEdges) {
          specialEdgesGroup[showSpecialEdgeType].display = false;
        }
      }
      for (const showSpecialEdgeType of val[1]) {
        for (const specialEdgesGroup of this.specialEdges) {
          specialEdgesGroup[showSpecialEdgeType].display = true;
        }
      }
    },
    storeProfileNamespaces: function (val) {
      this.oldHaloInfo = [];
      this.haloInfo.forEach(([namescope, nodeGroup], index) => {
        this.oldHaloInfo.push(namescope);
      });
      this.selectNamespaces = val;
      this.onNameScopeChanged();
    },
    storeProfileTreeData: function (val) {
      this.treeData = val;
    },
  },

  computed: {
    storeGraphData() {
      return $store.state.graphData;
    },
    storeProfileShowSpecialEdgeTypes() {
      return $store.state.profileShowSpecialEdgeTypes;
    },
    storeProfileNamespaces() {
      return $store.state.profileNamespaces;
    },
    storeProfileTreeData() {
      return $store.state.profileTreeData;
    },
    haloInfo() {
      const res = [];
      for (const namespace of this.selectNamespaces) {
        const childrenIndex = namespace.split("-");
        childrenIndex.shift();
        let selectNode = this.treeData[Number(childrenIndex[0])];
        const rankID = childrenIndex[0];
        childrenIndex.shift();
        for (const childIndex of childrenIndex) {
          selectNode = selectNode.children[Number(childIndex)];
        }
        const nodeGroup = [];
        // iterate subtree
        this.preOrder(
          selectNode,
          nodeGroup,
          this.isPipelineLayout ? rankID : 0
        );
        nodeGroup = nodeGroup.filter((v) => v !== undefined);
        nodeGroup = Array.from(new Set(nodeGroup));
        res.push([namespace, nodeGroup]);
      }
      return res;
    },
  },

  mounted() {},

  methods: {
    haloColorScale: d3.scaleOrdinal(d3.schemeAccent),
    initGraph() {
      this.fetchData();
      for (let i = 0; i < this.nodeMaps.length; i++) {
        const nodeMap = this.nodeMaps[i];
        const [normalEdgesBackup, { specialEdges, normalEdges, opNodes }] =
          extractVisNodeAndEdge(nodeMap);
        this.normalEdgesBackup.push(normalEdgesBackup);
        this.specialEdges.push(specialEdges);
        this.specialEdgeTypes = [
          ...this.specialEdgeTypes,
          ...Object.keys(specialEdges),
        ];
        this.normalEdges.push(normalEdges);
        this.opNodes.push(opNodes);
        layout(opNodes, normalEdges, nodeMap, 50);
        // move downwards
        opNodes.forEach((opNode) => {
          opNode.y += 500 * i;
        });
      }
      this.specialEdgeTypes = Array.from(new Set(this.specialEdgeTypes));
      $store.commit("setProfileSpecialEdgeTypes", this.specialEdgeTypes);

      for (const opNodes of this.opNodes) {
        const idToIndex = {};
        opNodes.forEach((opNode, index) => {
          idToIndex[opNode.id] = index;
        });
        this.idToIndexs.push(idToIndex);
      }

      if (this.isPipelineLayout) {
        this.pipelineLayout();
        this.calcStrategyPara();
      }
      const subgraphSet = new Set();
      for (const nodeGroup of this.opNodes) {
        for (const node of nodeGroup) {
          if (node.isAggreNode) {
            subgraphSet.add(node.aggreNodes);
          }
        }
      }
      for (const aggreNodes of subgraphSet) {
        let right = 0;
        let left = 100000000;
        let top = -1000000;
        let bottom = 1000000;
        for (const node of aggreNodes) {
          if (node.x > right) right = node.x;
          if (node.x < left) left = node.x;
          if (node.y > top) top = node.y;
          if (node.y < bottom) bottom = node.y;
        }
        this.isomorphicSubgraphCircles.push({
          x: (left + right) / 2,
          y: (bottom + top) / 2,
          rx: (right - left) / 2 + 40,
          ry: (top - bottom) / 2 + 40,
          // r: Math.max(right - left, top - bottom) / 2 + 15,
          n: aggreNodes[0].contain.length,
        });
      }
    },
    fetchData() {
      const res = this.graphData;
      if ("graphs" in res) {
        this.isPipelineLayout = true;
        buildPipelinedStageInfo(res.graphs);
        ({
          nodeBlocks: this.nodeBlocks,
          nodeOrder: this.nodeOrder,
          dependNodes: this.dependNodes,
        } = getPipelineBlockInfo());

        this.parallelStrategyRawData = getStrategyInfo(res.graphs);
        resetTreeData();
        resetSpecialNodesMap();
        Object.keys(res.graphs).forEach((rankID) => {
          const thisGraph = res.graphs[rankID];
          buildGraph(thisGraph);
          this.nodeMaps.push(processedGraph.nodeMap);
        });
      } else {
        this.isPipelineLayout = false;
        resetSpecialNodesMap();
        buildGraphOld(res.data);
        this.nodeMaps.push(processedGraph.nodeMap);
      }
      $store.commit("setNodeMaps", this.nodeMaps);
    },
    pipelineLayout() {
      const nodeBlockBorders = {};

      let lastDependNodeBlockEndX = undefined;
      for (let i = 0; i < this.nodeOrder.length; i++) {
        const thisNodeBlock = this.nodeOrder[i];
        const [nodeGroupIndex, startNodeID, endNodeID] =
          thisNodeBlock.split("-");
        const startNodeIndex = this.idToIndexs[nodeGroupIndex][startNodeID];
        const endNodeIndex = this.idToIndexs[nodeGroupIndex][endNodeID];

        if (lastDependNodeBlockEndX === undefined) {
          lastDependNodeBlockEndX =
            this.opNodes[nodeGroupIndex][startNodeIndex].x;
        } else {
          lastDependNodeBlockEndX = Number.MIN_VALUE;
          for (let j = 0; j < i; j++) {
            if (this.dependNodes[thisNodeBlock].includes(this.nodeOrder[j])) {
              if (
                nodeBlockBorders[this.nodeOrder[j]].rightBorder >
                lastDependNodeBlockEndX
              ) {
                lastDependNodeBlockEndX = Math.max(
                  lastDependNodeBlockEndX,
                  nodeBlockBorders[this.nodeOrder[j]].rightBorder
                );
              }
            }
          }
        }

        let minX = Number.MAX_VALUE;
        let maxX = Number.MIN_VALUE;
        for (let j = startNodeIndex; j <= endNodeIndex; j++) {
          minX = Math.min(minX, this.opNodes[nodeGroupIndex][j].x);
          maxX = Math.max(maxX, this.opNodes[nodeGroupIndex][j].x);
        }

        for (let j = startNodeIndex; j <= endNodeIndex; j++) {
          this.opNodes[nodeGroupIndex][j].x =
            lastDependNodeBlockEndX +
            (this.opNodes[nodeGroupIndex][j].x - minX);
        }

        nodeBlockBorders[thisNodeBlock] = {
          leftBorder: lastDependNodeBlockEndX,
          rightBorder: lastDependNodeBlockEndX + maxX - minX,
        };
        this.bgdRectBlocks.push({
          x: nodeBlockBorders[thisNodeBlock].leftBorder,
          y: -200 + 500 * nodeGroupIndex,
          width:
            nodeBlockBorders[thisNodeBlock].rightBorder -
            nodeBlockBorders[thisNodeBlock].leftBorder,
          height: 500,
        });
      }

      this.$forceUpdate();
    },
    calcStrategyPara() {
      this.parallelStrategyParas = {};
      const reds = d3.schemeReds[9];
      Object.keys(this.parallelStrategyRawData).forEach((key) => {
        const [nodeGroupIndex, sourceID, targetID] = key.split("-");
        const [sourceNode, targetNode] = [
          this.nodeMaps[nodeGroupIndex][sourceID],
          this.nodeMaps[nodeGroupIndex][targetID],
        ];
        if (!sourceNode || !targetNode) return;
        if (sourceNode.type === "Load" || targetNode.type === "Load") return;

        if (
          !this.normalEdgesBackup[nodeGroupIndex].includes(
            `${sourceID}-${targetID}`
          )
        ) {
          if (!(nodeGroupIndex in this.extraEdges)) {
            this.extraEdges[nodeGroupIndex] = [];
          }
          this.extraEdges[nodeGroupIndex].push([
            sourceNode.x,
            sourceNode.y,
            targetNode.x,
            targetNode.y,
            sourceNode,
            targetNode,
          ]);
        }

        if (!sourceNode.x || !sourceNode.y || !targetNode.x || !targetNode.y) {
          return;
        }
        const centerDist = Math.hypot(
          targetNode.x - sourceNode.x,
          targetNode.y - sourceNode.y
        );
        const theta = Math.asin(
          Math.abs(targetNode.y - sourceNode.y) / centerDist
        );
        const offset = 2;
        const [sourceRadius, targetRadius] = [sourceNode.r, targetNode.r];
        const rectWidth = 6;
        const rectHeight = 4;
        const rects = [];
        const colors = [];
        const textsPos = [];
        const isTargetLower = targetNode.y >= sourceNode.y;
        const isTargetRight = targetNode.x >= sourceNode.x;
        for (let i = 0; i < this.parallelStrategyRawData[key].length; i++) {
          const topLeftX =
            targetNode.x -
            targetRadius -
            offset -
            (this.parallelStrategyRawData[key].length - i) * rectWidth;
          const topLeftY = targetNode.y - rectHeight / 2;
          const textPosX = topLeftX + rectWidth / 2;
          const textPosY = targetNode.y;
          rects.push([topLeftX, topLeftY, rectWidth, rectHeight]);
          colors.push(reds[this.parallelStrategyRawData[key][i]]);
          textsPos.push([textPosX, textPosY]);
        }

        if (!(nodeGroupIndex in this.parallelStrategyParas)) {
          this.parallelStrategyParas[nodeGroupIndex] = [];
        }
        this.parallelStrategyParas[nodeGroupIndex].push({
          rects: rects,
          texts: this.parallelStrategyRawData[key],
          textsPos: textsPos,
          colors: colors,
          theta: isTargetLower
            ? isTargetRight
              ? (theta * 180) / Math.PI
              : ((Math.PI - theta) * 180) / Math.PI
            : isTargetRight
            ? (-theta * 180) / Math.PI
            : (-(Math.PI - theta) * 180) / Math.PI,
          rotateCenter: [targetNode.x, targetNode.y],
        });
      });
    },
    initMiniMap() {
      this.canvas = new Canvas(this);
      this.canvas.create(this.opNodes.length);
    },
    initNodeEdgeMap() {
      this.normalEdges.forEach((group) => {
        group.forEach((edge) => {
          const source = edge.source;
          const target = edge.target;
          if (!Object.keys(this.nodeEdgesMap).includes(source.id)) {
            this.nodeEdgesMap[source.id] = [];
          }
          this.nodeEdgesMap[source.id].push(edge);
          if (!Object.keys(this.nodeEdgesMap).includes(target.id)) {
            this.nodeEdgesMap[target.id] = [];
          }
          this.nodeEdgesMap[target.id].push(edge);
        });
      });
      this.specialEdges.forEach((group) => {
        Object.keys(group).forEach((type) => {
          group[type].values.forEach((edge) => {
            const source = edge.source;
            const target = edge.target;
            if (!Object.keys(this.nodeEdgesMap).includes(source.id)) {
              this.nodeEdgesMap[source.id] = [];
            }
            this.nodeEdgesMap[source.id].push(edge);
            if (!Object.keys(this.nodeEdgesMap).includes(target.id)) {
              this.nodeEdgesMap[target.id] = [];
            }
            this.nodeEdgesMap[target.id].push(edge);
          });
        });
      });
      Object.keys(this.extraEdges).forEach((stage) => {
        this.extraEdges[stage].forEach((edge) => {
          const source = edge[4];
          const target = edge[5];
          if (!Object.keys(this.nodeEdgesMap).includes(source.id)) {
            this.nodeEdgesMap[source.id] = [];
          }
          this.nodeEdgesMap[source.id].push({ source: source, target: target });
          if (!Object.keys(this.nodeEdgesMap).includes(target.id)) {
            this.nodeEdgesMap[target.id] = [];
          }
          this.nodeEdgesMap[target.id].push({ source: source, target: target });
        });
      });
    },
    setBoxTransform(val) {
      this.boxTransform = val;
    },
    viewboxChanged(viewbox) {
      const nodesShow = [];

      const xLeft = viewbox[0] + this.boxTransform[0];
      const xRight = viewbox[0] + viewbox[2] + this.boxTransform[0];
      this.opNodes.forEach((nodeGroup) => {
        const leftIndex = this.lower_bound(nodeGroup, xLeft);
        const rightIndex = this.upper_bound(nodeGroup, xRight);
        nodesShow.push(nodeGroup.slice(leftIndex, rightIndex));
      });
      this.opNodesShow = nodesShow;
      const currenNodes = new Set();
      const edgesShow = [];
      for (const nodes of nodesShow) {
        for (const node of nodes) {
          currenNodes.add(node);
        }
      }

      for (const edges of this.normalEdges) {
        const es = [];
        for (const normalEdge of edges) {
          if (
            currenNodes.has(normalEdge.target) ||
            currenNodes.has(normalEdge.source)
          ) {
            es.push(normalEdge);
          }
        }
        edgesShow.push(es);
      }
      this.normalEdgesShow = edgesShow; 
    },
    lower_bound(nums, target) {
      let low = 0;
      let high = nums.length - 1;
      let res = 0;
      while (low <= high) {
        const mid = Math.floor((low + high) / 2);
        if (nums[mid].x <= target) {
          res = mid;
          low = mid + 1;
        } else {
          high = mid - 1;
        }
      }
      return res;
    },
    upper_bound(nums, target) {
      if (nums[nums.length - 1].x <= target) {
        return nums.length - 1;
      }
      let left = 0;
      let right = nums.length;
      let result = 0;
      while (left < right) {
        const mid = Math.floor((left + right) / 2);
        if (nums[mid].x <= target) {
          left = mid + 1;
        } else {
          right = mid;
          result = mid;
        }
      }
      return result;
    },

    onNodeMouseover(e, node) {
      this.hoverNodeEdges = this.nodeEdgesMap[node.id];
    },
    onNodeMouseout() {
      this.hoverNodeEdges = [];
    },
    onNodeClick(node) {
      this.clickedNodeId = node.id;
      $store.commit("setSelectedGraphNode", node);
    },

    onNameScopeChanged() {
      const newHaloInfo = this.haloInfo;
      if (newHaloInfo.length != 0) {
        const viewBox = this.canvas.getViewBox();
        let minX = Number.MAX_VALUE;
        let minY = Number.MAX_VALUE;
        newHaloInfo[newHaloInfo.length - 1][1].forEach((node) => {
          if (node.x < minX) {
            minX = node.x;
            if (node.y < minY) {
              minY = node.y;
            }
          }
        });
        this.canvas.changeViewBox([minX, minY, viewBox[2], viewBox[3]], true);
      }
    },
    preOrder(tree, nodeGroup, rankID) {
      if (!tree) return;
      nodeGroup.push(this.opNodes[rankID][this.idToIndexs[rankID][tree.id]]);
      for (const child of tree.children) {
        this.preOrder(child, nodeGroup, rankID);
      }
    },
  },
};
</script>

<style>
.profile-graph {
  width: 100%;
  position: relative;
}
.special-edge-checkbox {
  position: absolute;
}

#profile-graph line {
  stroke-width: 1;
  stroke: #adadad;
}

#profile-graph text {
  font-size: 5px;
}

#profile-graph .active circle.node {
  stroke: #cb6056;
  stroke-width: 2;
}

#profile-graph circle.node {
  stroke: white;
  stroke-width: 1;
  fill: #cbcbcb;
}

#profile-graph circle.gradientaggregation {
  stroke: white;
  stroke-width: 1;
  fill: var(--allreduce-operator-color);
}

#profile-graph circle.redistribution {
  stroke: white;
  stroke-width: 1;
  fill: var(--redistribution-operator-color);
}

#profile-graph circle.strategy {
  stroke: white;
  stroke-width: 1;
  fill: var(--slice-operator-color);
}

#profile-graph circle.send {
  stroke: white;
  stroke-width: 1;
  fill: var(--send-operator-color);
}

#profile-graph circle.receive {
  stroke: white;
  stroke-width: 1;
  fill: var(--receive-operator-color);
}

#profile-graph circle.load {
  stroke-width: 0.5;
  fill: rgb(33, 29, 241);
}

#profile-graph path {
  stroke-width: 1px;
  fill: none;
}

#profile-graph path.load-edge {
  stroke: rgb(93, 213, 235);
  opacity: 0.8;
}

#profile-graph path.update-state-edge {
  stroke: rgb(126, 233, 112);
  opacity: 0.3;
}

#profile-graph path.get-next-edge {
  stroke: rgb(195, 230, 0);
  opacity: 0.8;
}

#profile-graph path.big-depend-edge {
  stroke: rgb(27, 29, 20);
  stroke-dasharray: 4;
  opacity: 0.3;
}

.profile-graph-tooltip {
  position: fixed;
  border: 1px solid #d8d8d8;
  background-color: #fff;
  z-index: 100;
  width: 260px;
  left: 0;
  top: 0;
  padding: 8px;
}

.profile-graph-tooltip .profile-graph-tooltip-title {
  text-align: center;
}

.profile-graph-tooltip .profile-graph-tooltip-content .col {
  display: flex;
  align-items: center;
  border-top: 1px solid #999;
}

.profile-graph-tooltip .profile-graph-tooltip-content .col .left {
  flex-grow: 1;
}

.profile-graph-tooltip .profile-graph-tooltip-content .col .right {
  flex-grow: 2;
  text-align: center;
}

.isomorphic-subgraph-circle {
  stroke: #ababab;
  fill: none;
  stroke-width: 2;
  stroke-dasharray: 4;
}
</style>

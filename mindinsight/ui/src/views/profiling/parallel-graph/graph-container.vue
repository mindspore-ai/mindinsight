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
  <div
    @mouseup="clickOutsideGraph"
    @mousedown="isDrag = false"
    @mousemove="isDrag = true"
    class="graph-container"
  >
    <div
      id="graph"
      class="graph"
      v-loading.fullscreen.lock="loading.show"
      element-loading-background="rgba(0, 0, 0, 0.3)"
      :element-loading-text="this.$t('trainingDashboard.loadingTip')"
    ></div>
    <svg-el-container ref="graphContainer" class="elk-graph" id="p-graph">
      <filter
        id="outline_selected_y"
        filterUnits="userSpaceOnUse"
        x="-50%"
        y="-50%"
        width="200%"
        height="200%"
        slot="marker"
      >
        <feMorphology
          result="offset"
          in="SourceGraphic"
          operator="dilate"
          radius="2"
        />
        <feColorMatrix
          color-interpolation-filters="sRGB"
          result="drop"
          in="offset"
          type="matrix"
          values="0 0 0 0 0.93
            0 0 0 0 0.56
            0 0 0 0 0.17
            0 0 0 1 0"
        />
        <feBlend in="SourceGraphic" in2="drop" mode="normal" />
      </filter>

      <filter
        id="outline_selected_g"
        filterUnits="userSpaceOnUse"
        x="-50%"
        y="-50%"
        width="200%"
        height="200%"
        slot="marker"
      >
        <feMorphology
          result="offset"
          in="SourceGraphic"
          operator="dilate"
          radius="2"
        />
        <feColorMatrix
          color-interpolation-filters="sRGB"
          result="drop"
          in="offset"
          type="matrix"
          values="0 0 0 0 0.49
            0 0 0 0 0.71
            0 0 0 0 0.49
            0 0 0 1 0"
        />
        <feBlend in="SourceGraphic" in2="drop" mode="normal" />
      </filter>

      <marker
        slot="marker"
        id="arrowhead"
        viewBox="0 0 10 10"
        refX="5"
        refY="5"
        markerUnits="userSpaceOnUse"
        markerWidth="8"
        markerHeight="6"
        orient="auto"
      >
        <path d="M -4 0 L 6.5 5 L -4 10 z" class="graph-marker-default"></path>
      </marker>
      <marker
        slot="marker"
        id="hoverArrowhead"
        viewBox="0 0 10 10"
        refX="5"
        refY="5"
        markerUnits="userSpaceOnUse"
        markerWidth="8"
        markerHeight="6"
        orient="auto"
      >
        <path d="M -4 0 L 6.5 5 L -4 10 z" class="graph-marker-hover"></path>
      </marker>
      <marker
        slot="marker"
        id="searchArrowhead"
        viewBox="0 0 10 10"
        refX="5"
        refY="5"
        markerUnits="userSpaceOnUse"
        markerWidth="8"
        markerHeight="6"
        orient="auto"
      >
        <path d="M -4 0 L 6.5 5 L -4 10 z" class="graph-marker-search"></path>
      </marker>

      <g slot="marker" class="patterns">
        <pattern
          id="data-texture"
          patternUnits="userSpaceOnUse"
          width="3"
          height="3"
        >
          <path d="M 0,1.5 l 3,0" />
        </pattern>

        <pattern
          id="model-texture"
          patternUnits="userSpaceOnUse"
          width="4"
          height="4"
        >
          <path d="M 0,4 l 4,-4 M -1,1 l 2,-2 M 3,5 l 2,-2" />
        </pattern>

        <pattern
          id="pipeline-texture"
          patternUnits="userSpaceOnUse"
          width="3"
          height="3"
        >
          <path d="M 1.5, 0 l 0, 3" />
        </pattern>

        <pattern
          id="data-pipeline-texture"
          patternUnits="userSpaceOnUse"
          width="4"
          height="4"
        >
          <path d="M 0,2 l 4,0" />
          <path d="M 2, 0 l 0, 4" />
        </pattern>
        <pattern
          id="model-pipeline-texture"
          patternUnits="userSpaceOnUse"
          width="4"
          height="4"
        >
          <path d="M 0,4 l 4,-4 M -1,1 l 2,-2 M 3,5 l 2,-2" />
          <path d="M 2, 0 l 0, 4" />
        </pattern>
        <pattern
          id="data-model-texture"
          patternUnits="userSpaceOnUse"
          width="4"
          height="4"
        >
          <path d="M 0,4 l 4,-4 M -1,1 l 2,-2 M 3,5 l 2,-2" />
          <path d="M 0,2 l 4,0" />
        </pattern>
      </g>

      <g slot="g">
        <component
          v-for="node in nodes"
          :key="node.id"
          :is="type2NodeComponent[node.type] || operatorNodeVue"
          :class="instanceType2Class(nodeAttrMap[node.id])"
          v-bind="node"
          :mouseenterListener="() => enterScopeWrapper(node)"
          :mouseleaveListener="() => leaveScopeWrapper(node)"
          @mousemove.native="mouseMoveInScope"
          @mousedown.native="mouseDownInScope"
          @mouseup.native="mouseUpInScope($event, node)"
          @dblscopenode="dbClickScope"
          @mouseenteroperatornode="mouseEnterOperatorNode"
          @mouseleaveoperatornode="mouseLeaveOperatorNode"
          @dblclickoperatornode="dbClickScope"
        />
      </g>

      <g slot="g">
        <!-- Edges -->
        <graph-edge
          :edges="edges"
          parentClass="graph-common"
          markerEndId="arrowhead"
          :opacity="edgeOpacity"
        />
        <!-- Edges(search) -->
        <graph-edge
          :edges="searchEdges"
          parentClass="graph-stroke-search"
          markerEndId="searchArrowhead"
        />
        <!-- Edges(hidden) -->
        <g slot="g">
          <g
            v-for="edge in hiddenEdges"
            :key="`${edge.id}-hidden`"
            transform="translate(7,7)"
          >
            <path :d="edge.draw" class="graph-stroke-hover no-fill"> </path>
          </g>
        </g>
        <g slot="g">
          <g v-for="edge in hiddenPolylineEdges" :key="`${edge.id}-hidden`">
            <polyline
              :points="edge.points"
              class="graph-stroke-hover no-fill"
              marker-end="url(#hoverArrowhead)"
            >
            </polyline>
          </g>
        </g>
        <!-- Edges(hover) -->
        <graph-edge
          :edges="hoverEdges"
          parentClass="graph-stroke-hover"
          markerEndId="hoverArrowhead"
        />
      </g>

      <!-- Ports -->
      <g slot="g">
        <g
          v-for="port in ports"
          :key="port.id"
          :transform="`translate(${port.x}, ${port.y})`"
          :opacity="port.opacity"
          @mouseenter="showHiddenEdges(port)"
          @mouseleave="hideHiddenEdges"
        >
          <circle cx="7.5" cy="7.5" r="5" class="graph-port-outside"> </circle>
          <circle cx="7.5" cy="7.5" r="1" class="graph-port-inside"> </circle>
        </g>
      </g>

      <template slot="g">
        <template v-for="(value, nodeId) in nodeAttrMap">
          <strategy-matrix
            v-if="visNodeMap.get(nodeId) && value.strategy !== undefined"
            :key="nodeId"
            v-bind="value"
            :x="visNodeMap.get(nodeId).x"
            :y="visNodeMap.get(nodeId).y"
            :height="visNodeMap.get(nodeId).height"
          />
        </template>
      </template>
    </svg-el-container>

    <div class="noData-content" v-show="this.noDataGraphShow">
      <div>
        <img :src="require('@/assets/images/nodata.png')"/>
      </div>
      <div class="noData-text">{{$t('public.noData')}}</div>
    </div>

    <div
      v-if="showPipelinePanel"
      class="pipeline-button"
      ref="pipeline-button"
      @click="clickPipelineBtn"
    >
      <img
        v-if="curPipelineBtn === 'PipelineOpenBtn'"
        :src="require('@/assets/images/svg/pipeline-open.svg')"
        style="user-select: none;"
      />
      <img
        v-if="curPipelineBtn === 'PipelineCloseBtn'"
        :src="require('@/assets/images/svg/pipeline-close.svg')"
        style="user-select: none;"
      />
    </div>

    <!-- Training Pipeline -->
    <div
      v-if="showPipelinePanel"
      class="training-pipeline-container"
      ref="pipeline-container"
      style="background: #fff;"
    >
      <div class="training-pipeline-title">
        {{ this.$t("profiling.trainingPipeline") }}
      </div>
      <div class="training-pipeline-legend">
        <svg width="100%" height="100%">
          <g>
            <rect
              x="191.5"
              y="8"
              width="12"
              height="12"
              :fill="pipelineReceiveRectColor"
            ></rect>
            <text x="206.5" y="19" font-size="12">Receive-op</text>
            <rect
              x="291.5"
              y="8"
              width="12"
              height="12"
              :fill="pipelineSendRectColor"
            ></rect>
            <text x="306.5" y="19" font-size="12">Send-op</text>
          </g>
        </svg>
      </div>
      <div class="training-pipeline-graph">
        <svg
          v-if="pipelineNodeInfo !== null"
          :width="getPipelineNodePosition(0, pipelineNodeInfo[0].length, 0)[0]"
          height="100%"
        >
          <defs>
            <rect
              id="send"
              :width="pipelineRectWidth"
              :height="pipelineRectWidth"
              :fill="pipelineSendRectColor"
              :style="{ cursor: 'pointer' }"
            ></rect>
            <rect
              id="receive"
              :width="pipelineRectWidth"
              :height="pipelineRectWidth"
              :fill="pipelineReceiveRectColor"
              :style="{ cursor: 'pointer' }"
            ></rect>
          </defs>
          <text
            v-for="textObj in pipelineStageText"
            :key="`${textObj.text}_pipeline_text`"
            :x="textObj.x"
            :y="textObj.y"
            font-size="12px"
          >
            {{ textObj.text }}
          </text>
          <g id="pipeline_edges">
            <path
              v-for="(edge, index) in pipelineEdgeInfo"
              :key="`${index}_pipeline_edge`"
              :d="genPipelinePath(edge)"
              :fill="pipelineArrowColor"
            ></path>
          </g>
          <g id="pipeline_nodes">
            <g
              v-for="(block, blockIndex) in pipelineNodeInfo"
              :key="`${blockIndex}_pipeline_block`"
            >
              <g
                v-if="blockIndex % 2 === 0"
                :transform="
                  `translate(${getPipelineNodePosition(1, block.length - 1, 0)
                    .map((v, i) => {
                      if (i === 0) return v + 17;
                      if (i === 1) return v - 36;
                      return v;
                    })
                    .join(',')}), rotate(90)`
                "
              >
                <foreignObject width="20" height="20">
                  <img
                    :src="require('@/assets/images/svg/link.svg')"
                    style="user-select: none;"
                  />
                </foreignObject>
              </g>
              <g
                v-for="(col, colIndex) in block"
                :key="`${colIndex}_pipeline_col`"
              >
                <g
                  v-if="colIndex % 2 === 1 && colIndex !== block.length - 1"
                  :transform="
                    `translate(${getPipelineNodePosition(
                      blockIndex,
                      colIndex,
                      Math.floor(col.length / 2)
                    )
                      .map((v, i) => {
                        if (i === 0) return v + 40;
                        if (i === 1) return v - 10;
                      })
                      .join(',')})`
                  "
                >
                  <foreignObject width="20" height="20">
                    <img
                      :src="require('@/assets/images/svg/link.svg')"
                      style="user-select: none;"
                    />
                  </foreignObject>
                </g>
                <g
                  v-for="(node, index) in col"
                  :key="`${node}_pipeline_node`"
                  @dblclick="
                    clickPipelineRect(
                      node,
                      Math.floor((colIndex + 1) / 2),
                      (blockIndex + colIndex) % 2 ? 'receive' : 'send'
                    )
                  "
                  @click="
                    clickPipelineRect(
                      node,
                      Math.floor((colIndex + 1) / 2),
                      (blockIndex + colIndex) % 2 ? 'receive' : 'send'
                    )
                  "
                  :transform="
                    `translate(${getPipelineNodePosition(
                      blockIndex,
                      colIndex,
                      index
                    ).join(',')})`
                  "
                >
                  <use
                    :xlink:href="
                      (blockIndex + colIndex) % 2 ? '#receive' : '#send'
                    "
                  ></use>
                  <text
                    :style="{
                      fill:
                        `${node}_${Math.floor((colIndex - 1) / 2) + 1}` ===
                        `${lastClickPipelineNodeID}`
                          ? 'red'
                          : 'black',
                      cursor: 'pointer',
                    }"
                    :x="
                      colIndex % 2
                        ? pipelineRectWidth + 2
                        : -pipelineRectWidth - 17
                    "
                    :y="10"
                    font-size="12px"
                  >
                    {{
                      getNodeNameFromIDAndStage(
                        node,
                        Math.floor((colIndex - 1) / 2) + 1
                      )
                    }}
                  </text>
                </g>
              </g>
            </g>
          </g>
        </svg>
      </div>
    </div>

    <!-- Right Menu -->
    <el-tooltip
      class="item"
      effect="dark"
      :content="this.$t('profiling.resetTips')"
      placement="bottom"
    >
      <el-button
        icon="el-icon-refresh"
        circle
        style="position: absolute; right: 630px; top: 35px;"
        @click="resetSVG"
        size="mini"
      ></el-button>
    </el-tooltip>
    <div class="selector-title" style="width: 120px; user-select: none;">
      {{ this.$t("profiling.parallelStrategy") }}
    </div>
    <div
      class="selector-title"
      style="width: 120px; top: 52px; user-select: none;"
    >
      {{ this.$t("profiling.rankSelector") }}
    </div>
    <div
      class="selector-title"
      style="width: 130px; top: 92px; user-select: none;"
    >
      <el-tooltip
        class="item"
        effect="dark"
        :content="this.$t('profiling.bipartiteExtractTips')"
        placement="bottom"
      >
        <i class="el-icon-info"></i>
      </el-tooltip>
      {{ this.$t("profiling.bipartiteExtractSelector") }}
    </div>
    <div class="selector-container">
      <div class="el-select" style="pointer-events: none;">
        <div class="el-input el-input--suffix">
          <input
            type="text"
            :placeholder="parallelStrategy"
            class="el-input__inner"
            style="pointer-events: none; "
          />
        </div>
      </div>
    </div>
    <div class="selector-container" style="top: 52px;">
      <el-select v-model="showRankId" @change="showRankIdChange">
        <el-option
          v-for="option in showRankIdOptions"
          :key="option.value"
          :label="option.label"
          :value="option.value"
        ></el-option>
      </el-select>
    </div>
    <div class="selector-container" style="top: 92px;">
      <el-select v-model="showNodeType" @change="showNodeTypeChange">
        <el-option
          v-for="option in showNodeTypeOptions"
          :key="option.value"
          :label="option.label"
          :value="option.value"
        ></el-option>
      </el-select>
    </div>

    <div class="graph-strategy-info">
      <div class="title">{{ this.$t("profiling.specialNodeCnt") }}</div>
      <div class="second-title" style="font-size: 10px;">
        {{ this.$t("profiling.hasStrategy") }}:
        <span style="font-weight: normal;">{{
          getSpecialNodesMap()["hasStrategy"]
            ? getSpecialNodesMap()["hasStrategy"]
            : 0
        }}</span>
      </div>
      <div class="second-title" style="font-size: 10px;">
        {{ this.$t("profiling.redistribution") }}:
        <span style="font-weight: normal;">{{
          getSpecialNodesMap()["Redistribution"]
            ? getSpecialNodesMap()["Redistribution"]
            : 0
        }}</span>
      </div>
      <div class="second-title" style="font-size: 10px;">
        {{ this.$t("profiling.gradientAggregate") }}:
        <span style="font-weight: normal;">{{
          getSpecialNodesMap()["GradientAggregation"]
            ? getSpecialNodesMap()["GradientAggregation"]
            : 0
        }}</span>
      </div>
    </div>

    <div
      class="graph-right-info menu-item"
      :style="{
        maxHeight: infoHeight,
      }"
    >
      <div class="title">{{ this.$t("profiling.nodeAttribute") }}</div>
      <template v-if="selectedNode">
        <div class="node-name" :title="selectedNode.name">
          {{ selectedNode.name }}
        </div>
        <div class="second-title">Inputs:</div>
        <div class="list">
          <div
            v-for="(item, index) in selectedNode.input"
            :key="index"
            :style="{
              'border-left': '4px solid #cccccc',
              'padding-left': '5px',
              'margin-top': '5px',
            }"
          >
            <div
              style="word-break: break-all"
              v-if="
                !notShowTypes.includes(
                  getNodeFromID(item) && getNodeFromID(item).type
                )
              "
            >
              <span style="font-weight: bold">name: </span>
              <span
                @click="clickPanelNodeID(item, 'input')"
                :style="{
                  cursor: 'pointer',
                  color:
                    `${item}_input` === lastFocusPanelNodeID
                      ? themeIndex === '0'
                        ? '#f2453d'
                        : '#ef9a9a'
                      : '',
                }"
              >
                {{
                  getNodeFromID(item) &&
                    getNodeFromID(item).name.slice(
                      getNodeFromID(item).name.lastIndexOf("/") + 1
                    )
                }}{{getNodeFromID(item) && getNodeFromID(item).type === 'const' ? ' (Const)' : ''}}
              </span>
            </div>
            <div
              v-if="
                !(
                  notShowTypes.includes(
                    getNodeFromID(item) && getNodeFromID(item).type
                  ) || getNodeFromID(item).type === 'const' || notShowTypes.includes(selectedNode.type)
                )
              "
            >
              <span style="font-weight: bold">shape: </span>
              {{
                selectedNode.input_shape ? selectedNode.input_shape[item] : ""
              }}
            </div>
            <div
              v-if="
                !(
                  notShowTypes.includes(
                    getNodeFromID(item) && getNodeFromID(item).type
                  ) || notShowTypes.includes(selectedNode.type)
                ) &&
                  _checkShardMethod(selectedNode.parallel_shard) &&
                  JSON.parse(selectedNode.parallel_shard)[index]
              "
            >
              <span style="font-weight: bold">strategy: </span>
              {{ JSON.parse(selectedNode.parallel_shard)[index] }}
            </div>
          </div>
        </div>
        <div class="second-title">Outputs:</div>
        <div class="list">
          <div
            v-for="(item, index) in selectedNode.output"
            :key="index"
            :style="{
              'border-left': '4px solid #cccccc',
              'padding-left': '5px',
              'margin-top': '5px',
            }"
          >
            <div
              style="word-break: break-all"
              v-if="
                !notShowTypes.includes(
                  getNodeFromID(item) && getNodeFromID(item).type
                )
              "
            >
              <span style="font-weight: bold">name: </span>
              <span
                @click="clickPanelNodeID(item, 'output')"
                :style="{
                  cursor: 'pointer',
                  color:
                    `${item}_output` === lastFocusPanelNodeID
                      ? themeIndex === '0'
                        ? '#f2453d'
                        : '#ef9a9a'
                      : '',
                }"
              >
                {{
                  getNodeFromID(item) &&
                    getNodeFromID(item).name.slice(
                      getNodeFromID(item).name.lastIndexOf("/") + 1
                    )
                }}
              </span>
            </div>
          </div>
        </div>
        <div class="second-title">Output_Shape:</div>
        <div class="list">
          {{ selectedNode.output_shape }}
        </div>
        <div class="second-title">Attributes:</div>
        <div class="list">
          <div v-for="(val, key) in selectedNode.attribute" :key="key">
            {{ key }}: {{ val }}
          </div>
        </div>
      </template>
      <template v-else>
        <div class="title">{{ this.$t("profiling.noneNodesTips") }}</div>
      </template>
    </div>

    <div class="graph-legend-info">
      <div class="title">{{ this.$t("graph.legend") }}</div>
      <div class="second-title" style="block">
        <svg width="20" height="20">
          <g>
            <rect width="20" height="20" rx="3" fill="rgb(0,0,0)" />
          </g>
        </svg>
        <svg width="190" height="20">
          <g>
            <text
              dx="10"
              dy="14"
              font-size="11"
              font-weight="bold"
              fill="var(--font-color)"
            >
              {{ this.$t("profiling.hasStrategy") }}
            </text>
          </g>
        </svg>
      </div>
      <div class="second-title" style="block">
        <svg width="20" height="20">
          <g>
            <rect width="20" height="20" rx="3" fill="rgb(125,181,125)" />
          </g>
        </svg>
        <svg width="190" height="20">
          <g>
            <text
              dx="10"
              dy="14"
              font-size="11"
              font-weight="bold"
              fill="var(--font-color)"
            >
              {{ this.$t("profiling.redistribution") }}
            </text>
          </g>
        </svg>
      </div>

      <div class="second-title" style="block">
        <svg width="20" height="20">
          <g>
            <rect width="20" height="20" rx="3" fill="rgb(237,142,44)" />
          </g>
        </svg>
        <svg width="190" height="20">
          <g>
            <text
              dx="10"
              dy="14"
              font-size="11"
              font-weight="bold"
              fill="var(--font-color)"
            >
              {{ this.$t("profiling.gradientAggregate") }}
            </text>
          </g>
        </svg>
      </div>
    </div>
  </div>
</template>

<script>
import elkGraph from '@/mixins/elk-graph';
import {
  getSingleNode,
  changeShowNodeType,
  changeShowRankId,
  edgeIdMap,
  getRealNodeName,
  resetFirstCntFlag,
  getSpecialNodesMap,
} from '../../../js/build-graph';
import {
  IN_PORT_SUFFIX,
  OUT_PORT_SUFFIX,
  EDGE_SEPARATOR,
  NODE_TYPE,
  NOT_SHOW_NODE_TYPE,
} from '../../../js/const';
import SvgElContainer from '@/components/svg-el-container.vue';
import scopeNode from './graph-nodes/scope-node.vue';
import operatorNodeVue from './graph-nodes/operator-node.vue';
import GraphEdge from './graph-edge.vue';
import ParallelBar from './parallel-bar.vue';
import {dataNodeMap, getEdge} from '../../../js/create-elk-graph';
import StrategyMatrix from './graph-nodes/strategy-matrix.vue';
const CONNECTED_OPACITY = 1;
const UNCONNECTED_OPACITY = 0.4;

export default {
  name: 'graph-conatiner',

  components: {
    SvgElContainer,
    GraphEdge,
    ParallelBar,
    StrategyMatrix,
  },

  mixins: [elkGraph],

  data() {
    return {
      // render different component according to node's type
      type2NodeComponent: {
        [NODE_TYPE.basic_scope]: scopeNode,
        [NODE_TYPE.name_scope]: scopeNode,
        [NODE_TYPE.aggregate_scope]: operatorNodeVue,
        [NODE_TYPE.parameter]: operatorNodeVue,
        [NODE_TYPE.const]: operatorNodeVue,
      },
      operatorNodeVue,
      bipartite: true,
      isClickOperatorNode: new Map(),
      clickTimer: null,
      infoHeight: '82px',
      defaultInfoHeight: 82,
      selectedNode: null,
      notShowTypes: Object.keys(NOT_SHOW_NODE_TYPE),

      pipelineRectWidth: 12,
      pipelineRectMargin: 2,
      pipelineStageNum: 0,

      pipelineSendRectColor: '#e9a39d',
      pipelineReceiveRectColor: '#8fc6ad',
      pipelineArrowColor: '#e4e4e4',

      isPipelineContainerShow: false,
      curPipelineBtn: 'PipelineOpenBtn',

      isDrag: false,

      lastStageID: '',
      lastClickPipelineNodeType: '',
      lastClickPipelineNodeID: '',

      lastFocusPanelNodeID: '', // focused node's id in the right panel

      themeIndex: this.$store.state.themeIndex, // Index of theme color
    };
  },

  computed: {
    /**
     * get the contents and positions of stage titles in pipelined view
     * @return {Object}
     */
    pipelineStageText() {
      const res = [];
      const y = this.getPipelineNodePosition(1, 0, 0)[1] - 8;
      for (let i = 0; i < this.pipelineStageNum; ++i) {
        let x;
        if (i === 0) {
          x = this.getPipelineNodePosition(0, 0, 0)[0] - 4;
        } else if (i === this.pipelineStageNum - 1) {
          x = this.getPipelineNodePosition(0, 2 * i - 1, 0)[0] - 4;
        } else {
          x = x = this.getPipelineNodePosition(0, 2 * i - 1, 0)[0] + 30;
        }
        res.push({
          text: `stage ${i}`,
          x,
          y,
        });
      }
      return res;
    },
  },

  methods: {
    /**
     * Get special nodes map.
     * @return {Object}
     */
    getSpecialNodesMap() {
      return getSpecialNodesMap();
    },

    /**
     * determine the css class depending on node's type
     * @param {Object} extraAttr
     * @return {String}
     */
    instanceType2Class(extraAttr) {
      if (extraAttr && extraAttr.type) {
        switch (extraAttr.type) {
          case 'GradientAggregation':
            return 'outline-y';
          default:
            return 'outline-g';
        }
      }
      return '';
    },

    /**
     * Check whether the shard method is valid
     * @param {Array|undefined} value
     * @return {boolean}
     */
    _checkShardMethod(value) {
      if (typeof value === 'string') {
        value = JSON.parse(value);
      }
      return value !== undefined && value.length > 0;
    },

    /**
     * mouse enter event handler of scope node
     * @param {Object} node
     */
    enterScopeWrapper(node) {
      if (this.selectedNode) return;
      this.enterScope(node);
    },

    /**
     * mouse leave event handler of scope node
     * @param {Object} node
     */
    leaveScopeWrapper(node) {
      if (this.selectedNode) return;
      this.leaveScope(node);
    },

    /**
     * update node info panel's height depending on the selected node
     */
    updateInfoHeight() {
      const curGraphContainerHeight = document.getElementById('p-graph')
          .clientHeight;
      const specialNodePanelHeight = 112;
      const legendPanelHeight = 114;
      const panelMargin = 8;
      const panelPadding = 12;
      const curNodeAttributePanelHeight =
        curGraphContainerHeight -
        specialNodePanelHeight -
        legendPanelHeight -
        2 * panelMargin -
        2 * panelPadding;

      if (!this.selectedNode) {
        this.infoHeight = this.defaultInfoHeight + 'px';
        return;
      }

      this.infoHeight = curNodeAttributePanelHeight + 'px';
    },

    /**
     * mouse move and down event handlers of scope node, used to distinguish between drag and click
     */
    mouseMoveInScope() {
      this.isDrag = true;
    },
    mouseDownInScope() {
      this.isDrag = false;
    },

    /**
     * mouse up event handler of scope node, used to handle single clicking
     * @param {Object} event
     * @param {Object} node
     */
    mouseUpInScope(event, node) {
      event.preventDefault();
      if (this.isDrag) return;
      // clickTimer is used to distinguish between click and dblclick
      clearTimeout(this.clickTimer);
      this.clickTimer = setTimeout(() => {
        // reset last focus node in panel
        this.lastFocusPanelNodeID = '';

        // reset last focus node in graph
        if (this.focusedNode) {
          this.focusedNode.focused = false;
        }
        if (this.selectedNode && this.selectedNode.id !== node.id) {
          this.leaveScope(this.visNodeMap.get(this.selectedNode.id));
        }
        this.enterScope(node);
        this.selectedNode = getSingleNode(node.id);
        this.updateInfoHeight();
        this.$forceUpdate();
      }, 150);
    },

    /**
     * mouse double click event handler of scope node
     * @param {Object} event
     * @param {Object} opt
     */
    async dbClickScope(event, opt) {
      clearTimeout(this.clickTimer);
      await this.doubleClickScope(event, opt);

      // reset selected node in graph
      if (this.selectedNode) {
        this.selectedNode = null;
      }

      // reset last focus node in graph
      if (this.focusedNode) {
        this.focusedNode.focused = false;
      }

      // reset last click node in pipeline panel
      this.lastStageID = this.lastClickPipelineNodeType = this.lastClickPipelineNodeID =
        '';

      // reset panel
      this.updateInfoHeight();
      this.$forceUpdate();
    },

    /**
     * mouse enter event handler of operator node
     * @param {Object} event
     * @param {String} id
     */
    mouseEnterOperatorNode(event, {id}) {
      event.stopPropagation();
      if (this.selectedNode) return;
      if (!this.isClickOperatorNode.get(id)) return;
      if (!this.visNodeMap.has(id)) {
        this.isClickOperatorNode.set(id, false);
        return;
      }
      this.hideHiddenEdges();

      this.nodes.forEach((node) => {
        node.opacity = UNCONNECTED_OPACITY;
      });
      this.ports.forEach((port) => {
        port.opacity = UNCONNECTED_OPACITY;
      });
      this.edgeOpacity = UNCONNECTED_OPACITY;

      const thisOperatorNode = getSingleNode(id);
      thisOperatorNode.input.forEach((inputID) => {
        if (!getSingleNode(inputID)) return;
        if (!this.isClickOperatorNode.get(id)) return;

        const inputNodeParent = getSingleNode(getSingleNode(inputID).parent);
        if (
          inputNodeParent &&
          inputNodeParent.type === NODE_TYPE.aggregate_scope
        ) {
          inputID = inputNodeParent.id;
        }
        if (!this.visNodeMap.has(inputID)) {
          this.isClickOperatorNode.set(id, false);
          return;
        }

        const start = this.visPortMap.get(`${inputID}${OUT_PORT_SUFFIX}`);
        const end = this.visPortMap.get(
            `${dataNodeMap.get(inputID).root}${OUT_PORT_SUFFIX}`,
        );
        if (!start || !end) return;
        start.opacity = CONNECTED_OPACITY;
        end.opacity = CONNECTED_OPACITY;
        this.hiddenEdges.push({
          id: `${inputID}${OUT_PORT_SUFFIX}${EDGE_SEPARATOR}${
            dataNodeMap.get(inputID).root
          }${OUT_PORT_SUFFIX}`,
          draw: this.calEdgeDraw([start.x, start.y], [end.x, end.y]),
        });
      });
      thisOperatorNode.output.forEach((outputID) => {
        if (!getSingleNode(outputID)) return;
        if (!this.isClickOperatorNode.get(id)) return;

        const outputNodeParent = getSingleNode(getSingleNode(outputID).parent);
        if (
          outputNodeParent &&
          outputNodeParent.type === NODE_TYPE.aggregate_scope
        ) {
          outputID = outputNodeParent.id;
        }
        if (!this.visNodeMap.has(outputID)) {
          this.isClickOperatorNode.set(id, false);
          return;
        }

        const start = this.visPortMap.get(
            `${dataNodeMap.get(outputID).root}${IN_PORT_SUFFIX}`,
        );
        const end = this.visPortMap.get(`${outputID}${IN_PORT_SUFFIX}`);
        if (!start || !end) return;
        start.opacity = CONNECTED_OPACITY;
        end.opacity = CONNECTED_OPACITY;
        this.hiddenEdges.push({
          id: `${
            dataNodeMap.get(outputID).root
          }${IN_PORT_SUFFIX}${EDGE_SEPARATOR}${outputID}${IN_PORT_SUFFIX}`,
          draw: this.calEdgeDraw([start.x, start.y], [end.x, end.y]),
        });
      });
    },

    /**
     * mouse leave event handler of operator node
     * @param {Object} event
     * @param {String} id
     */
    mouseLeaveOperatorNode(event, {id}) {
      event.stopPropagation();
      this.hideHiddenEdges();
    },

    /**
     * handler of node type selector, i.e., Graph Selector
     */
    showNodeTypeChange() {
      changeShowNodeType(this.showNodeType);
      resetFirstCntFlag();
      this.getDisplayedGraph(this.showNodeType, this.showRankId).then((res) => {
        const {width, height} = res;
        this.resetSelectStatus();
        this.resetSVG(false, width, height);
      });
    },

    /**
     * handler of rank id selector, i.e., Stage Selector
     */
    showRankIdChange() {
      changeShowRankId(this.showRankId);
      resetFirstCntFlag();
      this.getDisplayedGraph(this.showNodeType, this.showRankId).then((res) => {
        const {width, height} = res;
        this.resetSelectStatus();
        this.resetSVG(false, width, height);
      });
    },

    /**
     * get a node's info from its id
     * @param {String} id
     * @return {Object}
     */
    getNodeFromID(id) {
      return getSingleNode(id);
    },

    /**
     * get a node's real name in pipelined view from its id and stageIndex
     * @param {String} id
     * @param {String} stageIndex
     * @return {String}
     */
    getNodeNameFromIDAndStage(id, stageIndex) {
      return getRealNodeName(id, stageIndex);
    },

    /**
     * get a node's position in pipelined view from its indices
     * @param {String} firstIndex
     * @param {String} secondIndex
     * @param {String} thirdIndex
     * @return {Array}
     */
    getPipelineNodePosition(firstIndex, secondIndex, thirdIndex) {
      if (this.pipelineNodeInfo === null) return;
      const rectWidth = this.pipelineRectWidth;
      const rectMargin = 2 * this.pipelineRectMargin;
      const textWidth = 30;
      const stageBetween = 60;
      const nodeBetween = 80;
      const blockBetween = 50;
      const viewMargin = 10;
      const maxFirstBlockItemCount = this.pipelineNodeInfo[0].reduce(
          (pre, cur) => {
            if (cur.length > pre) return cur.length;
            else return pre;
          },
          0,
      );
      let x = 0;
      let y = 0;
      x += textWidth + viewMargin;
      x += Math.floor((secondIndex + 1) / 2) * stageBetween;
      x += Math.floor(secondIndex / 2) * nodeBetween;
      x += secondIndex * rectWidth;
      y += viewMargin;
      if (firstIndex === 1) {
        y += blockBetween + maxFirstBlockItemCount * (rectWidth + rectMargin);
      }
      y += thirdIndex * (rectWidth + rectMargin);
      return [x, y];
    },

    /**
     * generate pipeline edge paths
     * @param {Array} edge
     * @return {String}
     */
    genPipelinePath(edge) {
      const [start, end] = edge;
      const arrDiff = 3;
      if (end[1] > start[1]) {
        const startPos = this.getPipelineNodePosition(...start);
        startPos[0] += this.pipelineRectWidth + this.pipelineRectMargin;
        startPos[1] += arrDiff;
        const shiftStartPos = [
          startPos[0],
          startPos[1] + this.pipelineRectWidth - 2 * arrDiff,
        ];

        const endPos = this.getPipelineNodePosition(...end);
        endPos[0] -= this.pipelineRectMargin + 4;
        endPos[1] += arrDiff;

        const shiftEndPos = [
          endPos[0],
          endPos[1] + this.pipelineRectWidth - 2 * arrDiff,
        ];
        const upAnglePos = [endPos[0], endPos[1] - arrDiff];
        const downAnglePos = [endPos[0], shiftEndPos[1] + arrDiff];
        const controlPointDis = Math.abs(endPos[0] - startPos[0]) / 2;

        const startControlPoint = [startPos[0] + controlPointDis, startPos[1]];
        const endControlPoint = [endPos[0] - controlPointDis, endPos[1]];
        const shiftEndControlPoint = [
          shiftEndPos[0] - controlPointDis,
          shiftEndPos[1],
        ];
        const shiftStartControlPoint = [
          shiftStartPos[0] + controlPointDis,
          shiftStartPos[1],
        ];

        const arrowPointPos = [endPos[0] + 4, (endPos[1] + shiftEndPos[1]) / 2];
        return `M${startPos.join(' ')} C ${startControlPoint.join(
            ' ',
        )}, ${endControlPoint.join(' ')}, ${endPos.join(
            ' ',
        )} L ${upAnglePos.join(' ')} L ${arrowPointPos.join(
            ' ',
        )} L ${downAnglePos.join(' ')} L ${shiftEndPos.join(
            ' ',
        )} C ${shiftEndControlPoint.join(' ')}, ${shiftStartControlPoint.join(
            ' ',
        )}, ${shiftStartPos.join(' ')}`;
      } else {
        const startPos = this.getPipelineNodePosition(...start);
        startPos[0] += -this.pipelineRectMargin;
        startPos[1] += arrDiff;
        const shiftStartPos = [
          startPos[0],
          startPos[1] + this.pipelineRectWidth - 2 * arrDiff,
        ];
        const endPos = this.getPipelineNodePosition(...end);
        endPos[0] += this.pipelineRectWidth + this.pipelineRectMargin + 4;
        endPos[1] += arrDiff;
        const shiftEndPos = [
          endPos[0],
          endPos[1] + this.pipelineRectWidth - 2 * arrDiff,
        ];

        const controlPointDis = Math.abs(endPos[0] - startPos[0]) / 2;

        const startControlPoint = [startPos[0] - controlPointDis, startPos[1]];
        const endControlPoint = [endPos[0] + controlPointDis, endPos[1]];
        const upAnglePos = [endPos[0], endPos[1] - arrDiff];
        const downAnglePos = [endPos[0], shiftEndPos[1] + arrDiff];
        const shiftEndControlPoint = [
          shiftEndPos[0] + controlPointDis,
          shiftEndPos[1],
        ];
        const shiftStartControlPoint = [
          shiftStartPos[0] - controlPointDis,
          shiftStartPos[1],
        ];
        const arrowPointPos = [endPos[0] - 4, (endPos[1] + shiftEndPos[1]) / 2];
        return `M${startPos.join(' ')} C ${startControlPoint.join(
            ' ',
        )}, ${endControlPoint.join(' ')}, ${endPos.join(
            ' ',
        )} L ${upAnglePos.join(' ')} L ${arrowPointPos.join(
            ' ',
        )} L ${downAnglePos.join(' ')} L ${shiftEndPos.join(
            ' ',
        )} C ${shiftEndControlPoint.join(' ')}, ${shiftStartControlPoint.join(
            ' ',
        )}, ${shiftStartPos.join(' ')}`;
      }
    },

    /**
     * mouse click event handler of nodes in pipelined view
     * @param {String} nodeID
     * @param {String} stageID
     * @param {String} nodeType
     */
    async clickPipelineRect(nodeID, stageID, nodeType) {
      if (this.selectedNode?.id === nodeID) return;
      this.showRankId = stageID + '';
      changeShowRankId(this.showRankId);
      // first clear selected node in graph
      if (this.selectedNode) {
        this.leaveScope(this.visNodeMap.get(this.selectedNode.id));
      }
      if (
        stageID !== this.lastStageID ||
        nodeType !== this.lastClickPipelineNodeType
      ) {
        await this.getDisplayedGraph(this.showNodeType, this.showRankId);
      }
      await this.findNode(nodeID);
      this.lastStageID = stageID;
      this.lastClickPipelineNodeID = `${nodeID}_${stageID}`;
      this.lastClickPipelineNodeType = nodeType;

      // set selected node in graph
      this.selectedNode = getSingleNode(nodeID);
      this.enterScope(this.visNodeMap.get(nodeID));

      // reset focus status
      this.focusedNode.focused = false;
      this.focusedNode = null;

      // reset panel
      this.updateInfoHeight();
      this.$forceUpdate();
    },

    /**
     * mouse click event handler of pipelined view button, to expand/collapse pipelined view
     */
    clickPipelineBtn() {
      if (!this.isPipelineContainerShow) {
        this.$refs['pipeline-button'].style.left = '560px';
        this.$refs['pipeline-container'].style.left = '12px';
        this.curPipelineBtn = 'PipelineCloseBtn';
      } else {
        this.$refs['pipeline-button'].style.left = '30px';
        this.$refs['pipeline-container'].style.left = '-560px';
        this.curPipelineBtn = 'PipelineOpenBtn';
      }
      this.isPipelineContainerShow = !this.isPipelineContainerShow;
    },

    /**
     * reset the whole graph to the center
     */
    resetSVG(flag, width, height) {
      if (flag) {
        this.$refs.graphContainer.reset();
      } else {
        this.$refs.graphContainer.reset(false, width, height);
      }
    },

    /**
     * mouse click event handler of node ids in node info panel
     * @param {String} nodeID
     * @param {String} nodeType
     */
    async clickPanelNodeID(nodeID, nodeType) {
      const thisFocusPanelNodeID = `${nodeID}_${nodeType}`;
      if (thisFocusPanelNodeID === this.lastFocusPanelNodeID) return;
      await this.findNode(nodeID);
      this.lastFocusPanelNodeID = thisFocusPanelNodeID;
      // set selected node in graph
      if (this.selectedNode) {
        this.enterScope(this.visNodeMap.get(this.selectedNode.id));
      }
    },

    /**
     * reset node's selecting status
     */
    resetSelectStatus() {
      if (this.selectedNode) {
        this.leaveScope(this.visNodeMap.get(this.selectedNode.id));
      }
      this.selectedNode = null;

      // reset last focus node in graph
      if (this.focusedNode) {
        this.focusedNode.focused = false;
      }

      // reset last click node in pipeline panel
      this.lastStageID = this.lastClickPipelineNodeType = this.lastClickPipelineNodeID =
        '';

      // reset panel
      this.updateInfoHeight();
      this.$forceUpdate();
    },

    /**
     * mouse click event handler of outside graph, to reset node's selecting status
     * @param {Object} event
     */
    clickOutsideGraph(event) {
      if (event.target.tagName === 'svg' && !this.isDrag) {
        // click outside graph
        this.resetSelectStatus();
      }
    },
  },
};
</script>

<style>
.graph-container {
  height: 100%;
  width: 100%;
  background-color: var(--module-bg-color);
  display: flex;
  position: relative;
}

.elk-graph {
  --common-stroke-width: 1;
  --common-stroke-color: var(--common-node-stroke);
  --active-stroke-width: 2;
  --hightlight-graph-color: #fd9629;
  --click-graph-color: #f00;
  --search-graph-color: #bd39c2;
  --focused-graph-color: red;
  height: 100%;
  width: 100%;
  position: relative;
  display: grid;
}

.elk-graph .graph-common {
  stroke: var(--common-stroke-color);
  stroke-width: var(--common-stroke-width);
  transition: opacity 0.2s ease-in-out;
}

.elk-graph .graph-stroke-hover {
  stroke: var(--highlight-node-stroke-color);
  stroke-width: var(--active-stroke-width);
}

.elk-graph .graph-marker-hover {
  stroke: var(--highlight-node-stroke-color);
  fill: var(--highlight-node-stroke-color);
}

.elk-graph .graph-marker-default {
  stroke: var(--common-stroke);
  fill: var(--common-stroke);
}

.elk-graph .graph-stroke-click {
  stroke: var(--click-graph-color);
  stroke-width: var(--active-stroke-width);
}

.elk-graph .graph-marker-search {
  stroke: var(--search-graph-color);
  fill: var(--search-graph-color);
}

.elk-graph .graph-stroke-focused {
  stroke: var(--focused-node-color);
  stroke-width: var(--active-stroke-width);
}

.elk-graph .graph-scope-label {
  font-size: 14px;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  user-select: none;
  padding: 0 4px;
  fill: var(--font-color);
}
.elk-graph .graph-operator-label {
  transform: scale(0.7);
  padding: 0;
}
.elk-graph .graph-port-inside {
  fill: #000000;
}
.elk-graph .graph-port-outside {
  fill: #ffffff;
  stroke: #000000;
  stroke-miterlimit: 10;
}

.elk-graph .no-fill {
  fill: none;
}

.outline-y path,
.outline-y polyline,
.outline-y rect,
.outline-y ellipse {
  filter: url(#outline_selected_y);
}

.outline-g path,
.outline-g polyline,
.outline-g rect,
.outline-g ellipse {
  filter: url(#outline_selected_g);
}

/* Selector */
.graph-container .selector-container {
  position: absolute;
  top: 12px;
  right: 260px;
  user-select: none;
}

.strategy-title {
  position: absolute;
  line-height: 32px;
  padding-left: 15px;
  top: 12px;
  right: 260px;
  width: 217px;
  height: 32px;
  background-color: #fff;
  border: 1px solid #e4e7ed;
  user-select: none;
}

.selector-title {
  position: absolute;
  top: 12px;
  right: 488px;
  text-align: right;
  font-size: 15px;
  font-weight: 500;
  height: 32px;
  line-height: 32px;
  width: 240px;
}

/** Info */
.graph-container .graph-strategy-info {
  display: flex;
  flex-direction: column;
  position: absolute;
  top: 12px;
  right: 12px;
  height: 112px;
  padding-bottom: 6px;
  background-color: var(--attribute-panel-bg-color);
  width: 240px;
  user-select: none;
}

.graph-container .graph-right-info {
  display: flex;
  flex-direction: column;
  position: absolute;
  top: 134px;
  right: 12px;
  transition: height 0.3s;
  overflow: auto;
}

.graph-container .graph-right-info .list {
  padding: 0 12px;
  overflow: auto;
  flex-shrink: 0;
}

.graph-container .title {
  height: 36px;
  line-height: 36px;
  font-size: 15px;
  font-weight: 500;
  text-align: center;
  flex-shrink: 0;
  padding: 0 12px;
  user-select: none;
}

.graph-container .second-title {
  height: 24px;
  line-height: 24px;
  font-size: 14px;
  font-weight: 600;
  padding-left: 12px;
  flex-shrink: 0;
}

.graph-container .menu-item {
  background-color: var(--attribute-panel-bg-color);
  width: 240px;
}

.graph-legend-info {
  display: flex;
  flex-direction: column;
  position: absolute;
  bottom: 12px;
  right: 12px;
  transition: height 0.3s;
  padding-bottom: 6px;
  background-color: var(--attribute-panel-bg-color);
  width: 240px;
}

.graph-container .node-name {
  font-size: 15px;
  font-weight: 500;
  word-break: break-all;
  flex-shrink: 0;
  padding: 0 12px;
}
.elk-graph .patterns path {
  stroke-width: 1;
  shape-rendering: auto;
  stroke: #343434;
}

.training-pipeline-container {
  border: 1px solid #bebebe;
  width: 530px;
  height: 280px;
  position: absolute;
  top: 12px;
  left: -660px;
  transition: left 1s;
  z-index: 99;
}

.training-pipeline-title {
  background-color: var(--pipeline-panel-title-bg-color);
  border-bottom: 1px solid #bebebe;
  font-size: 16px;
  padding-left: 10px;
  line-height: 25px;
  height: 25px;
}

.training-pipeline-legend {
  height: 25px;
  background-color: var(--pipeline-panel-content-bg-color);
}

.training-pipeline-graph {
  background-color: var(--pipeline-panel-content-bg-color);
  position: relative;
  overflow-x: auto;
  overflow-y: hidden;
  height: calc(100% - 50px);
  z-index: 1;
}

#pipeline_edges path {
  stroke: #bbb;
}

.pipeline-button {
  position: absolute;
  width: 40px;
  height: 40px;
  top: 20px;
  left: 30px;
  transition: left 1s;
  cursor: pointer;
  z-index: 99;
}

.cls-1 {
  fill: #00a5a7;
  stroke: #00a5a7;
  stroke-linecap: round;
  stroke-miterlimit: 10;
  stroke-width: 2px;
}

.ghost {
  opacity: 0.5;
  background: #c8ebfb;
}

.flip-list-move {
  transition: transform 0.5s;
}

.no-move {
  transition: transform 0s;
}

.el-input__inner::placeholder {
  color: var(--el-input-font-color) !important;
}

.training-pipeline-container svg text {
  user-select: none;
}

.graph-container .noData-content {
  width:100%;
  height:100%;
  margin-left: -100%;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}
</style>

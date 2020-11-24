<!--
Copyright 2020 Huawei Technologies Co., Ltd.All Rights Reserved.

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
  <div class="deb-wrap">
    <div class="left-wrap"
         :class="{collapse:leftShow}">
      <div class="left"
           v-show="!leftShow">
        <div class="header">
          {{radio1==='tree' ? $t('debugger.nodeList') : $t('debugger.curHitNode')}}
          <div class="radio-tabs">
            <el-radio-group v-model="radio1"
                            size='mini'
                            @change="getWatchpointHits">
              <el-radio-button label="tree">
                <i class="el-icon-s-grid"></i>
              </el-radio-button>
              <el-radio-button label="hit">
                <i class="el-icon-s-fold"></i>
              </el-radio-button>
            </el-radio-group>
          </div>
        </div>
        <div class="content"
             v-show="radio1==='tree'">
          <div class="node-type">
            <div class="label">{{ $t('debugger.graphFile') }}</div>
            <el-select v-model="graphFiles.value"
                       @change="queryGraphByFile">
              <el-option v-for="item in graphFiles.options"
                         :key="item"
                         :value="item">
              </el-option>
            </el-select>
          </div>
          <div class="node-type">
            <div class="label">{{$t('debugger.nodeTypes')}}</div>
            <el-select v-model="nodeTypes.value"
                       @change="nodeTypesChange">
              <el-option v-for="item in nodeTypes.options"
                         :key="item"
                         :label="nodeTypes.label[item]"
                         :value="item"
                         :class="{'deb-indent': item != 'all'}">
              </el-option>
            </el-select>
          </div>
          <div class="select-wrap">
            <el-input :placeholder="$t('graph.inputNodeName')"
                      v-model="searchWord"
                      class="input-with-select"
                      @input="filterChange"
                      @keyup.enter.native="filter"
                      clearable>
            </el-input>
          </div>
          <div class="tree-wrap">
            <div class="select-all-files"
                 v-if="curWatchPointId && treeFlag">
              <el-button type="primary"
                         size="mini"
                         class="custom-btn"
                         @click="selectAllFiles(true)">{{ $t('public.selectAll') }}</el-button>
              <el-button type="primary"
                         size="mini"
                         class="custom-btn"
                         @click="selectAllFiles(false)">{{ $t('public.deselectAll') }}</el-button>
            </div>
            <tree v-show="treeFlag"
                  :props="props"
                  :load="loadNode"
                  @node-collapse="nodeCollapse"
                  @node-click="handleNodeClick"
                  node-key="name"
                  :default-checked-keys="defaultCheckedArr"
                  :expand-on-click-node="false"
                  :lazy="lazy"
                  :highlight-current="true"
                  ref="tree"
                  @check="check"
                  :show-checkbox="!!curWatchPointId">
              <span class="custom-tree-node"
                    slot-scope="{ node ,data }">
                <span :class="{const:data.type==='Const'}">
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
            </tree>
            <el-tree v-show="!treeFlag"
                     :props="defaultProps"
                     :load="loadSearchNode"
                     :lazy="true"
                     node-key="name"
                     :default-checked-keys="searchCheckedArr"
                     :expand-on-click-node="false"
                     @node-click="handleNodeClick"
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
          <div class="watch-point-wrap">
            <div class="title-wrap">
              {{$t('debugger.watchList')}}

              <div class="check-wrap">
                <i class="el-icon-circle-check"
                   :title="$t('debugger.recheck')"
                   :class="{disable: !enableRecheck}"
                   @click="recheckWatchpoint()"></i>
              </div>

              <div class="delete-wrap">
                <i class="el-icon-delete"
                   :title="$t('debugger.clearWatchpoint')"
                   :class="{disable: !watchPointArr.length}"
                   @click="deleteWatchpoint()"></i>
              </div>
              <div class="add-wrap">
                <i class="el-icon-circle-plus"
                   :title="$t('debugger.createWP')"
                   @click="addWatchPoint"></i>
              </div>
            </div>
            <div class="content-wrap">
              <ul id="watch-point-list"
                  class="list-wrap"
                  v-show="allWatchPointFlag">
                <li class="list"
                    v-for="(item,key) in watchPointArr"
                    :key="key"
                    :title="getWatchPointContent(item)">
                  <div class="name"
                       :class="{selected:item.selected}"
                       @click="selectWatchPoint(key)">
                    <div class="item-content">
                      {{getWatchPointContent(item)}}
                    </div>
                    <i class="el-icon-check"
                       v-if="item.selected"
                       @click.stop="showOrigin()"></i>
                    <i class="el-icon-close"
                       v-if="item.selected"
                       @click.stop="deleteWatchpoint(item)"></i>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
        <div class="content"
             v-show="radio1==='hit'">
          <div class="hit-list-wrap">
            <el-table :data="watchPointHits"
                      row-key="id"
                      :expand-row-keys="expandKeys">
              <el-table-column type="expand"
                               width="40">
                <template slot-scope="props">
                  <ul>
                    <li v-for="(i, index) in props.row.lists"
                        :key="index">{{i.name}}</li>
                  </ul>
                </template>
              </el-table-column>
              <el-table-column prop="name"
                               :label="$t('graph.name')">
                <template slot-scope="scope">
                  <div class="hit-item"
                       :class="{selected:scope.row.selected}"
                       @click="updateTensorValue(scope.$index)">
                    {{scope.row.graph_name}}/{{scope.row.name}}
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
        <div class="btn-wrap">
          <div class="step">
            <el-tooltip class="item"
                        effect="light"
                        :content="$t('debugger.inputTip')"
                        placement="top-start">
              <el-input v-model="step"
                        :placeholder="$t('debugger.inputStep')"
                        @input="stepChange"
                        @keyup.native.enter="control(0)">
              </el-input>
            </el-tooltip>

            <el-button type="primary"
                       size="mini"
                       class="custom-btn green"
                       :disabled="!step || metadata.state==='running' || metadata.state==='pending'"
                       @click="control(0)">{{ $t('public.sure') }}</el-button>
          </div>
          <div class="btn-two">
            <el-button size="mini"
                       class="custom-btn white"
                       :disabled="metadata.state==='running'|| metadata.state==='pending'"
                       @click="control(1)">{{$t('debugger.continue')}}</el-button>
            <el-button size="mini"
                       class="custom-btn white"
                       :disabled="metadata.state!=='running'"
                       @click="control(3)">{{$t('debugger.pause')}}</el-button>
            <el-button size="mini"
                       class="custom-btn white"
                       :disabled="metadata.state==='pending'"
                       @click="terminate">{{$t('debugger.terminate')}}</el-button>
          </div>
        </div>
      </div>
      <div class="collapse-btn"
           :class="{collapse:leftShow}"
           @click="collapseBtnClick">
      </div>
    </div>
    <div class="right"
         :class="{collapse:leftShow}">
      <div class="header">
        <span class="item">
          {{$t('debugger.clientIp') + $t('symbols.colon')}}
          <span class="content">
            {{ metadata.ip !== undefined ? metadata.ip : '--' }}
          </span>
        </span>
        <span class="item">{{$t('debugger.deviceId') + $t('symbols.colon')}}
          <span class="content">
            {{ metadata.device_name !== undefined ? metadata.device_name : '--' }}
          </span>
        </span>
        <span class="item">{{$t('debugger.currentStep') + $t('symbols.colon')}}
          <span class="content">
            {{ metadata.step !== undefined ? metadata.step : '--'}}
          </span>
        </span>
        {{ $t('debugger.stepTip')}}
      </div>
      <div class="svg-wrap"
           :class="{collapse: collapseTable}">
        <div class="graph-container">
          <div id="graph"></div>
          <div id="contextMenu">
            <ul>
              <li>{{ $t('debugger.continueTo')}}</li>
            </ul>
          </div>
        </div>
        <div class="btn-wrap">
          <el-button v-if="version==='Ascend'"
                     type="primary"
                     size="mini"
                     class="custom-btn green notShow"
                     @click="getNodeByBfs(false)">
            {{ $t('debugger.previousNode')}}
          </el-button>
          <el-button v-if="version==='GPU'"
                     type="primary"
                     size="mini"
                     class="custom-btn green"
                     :disabled="!currentNodeName"
                     :class="{disabled:!currentNodeName}"
                     @click="getCurrentNodeInfo">
            {{ $t('debugger.currentNode')}}
          </el-button>
          <el-button v-if="version==='Ascend'"
                     type="primary"
                     size="mini"
                     class="custom-btn white notShow"
                     @click="getNodeByBfs(true)">
            {{ $t('debugger.nextNode')}}
          </el-button>
          <el-button v-if="version==='GPU'"
                     type="primary"
                     size="mini"
                     class="custom-btn white"
                     @click="getNextNodeInfo">
            {{ $t('debugger.nextNode')}}
          </el-button>
        </div>
      </div>
      <div class="table-container"
           :class="{collapse: collapseTable}">
        <img :src="require('@/assets/images/all-drop-down.png')"
             v-show="collapseTable"
             @click="rightCollapse()"
             alt="" />
        <img :src="require('@/assets/images/all-uptake.png')"
             v-show="!collapseTable"
             @click="rightCollapse()"
             alt="" />

        <el-tabs v-model="tabs.activeName">
          <el-tab-pane :label="$t('debugger.tensorMsg')"
                       name="tensor">
            <div class="table-content">
              <div class="table-wrap">
                <el-table ref="singleTable"
                          :data="tableData"
                          :header-cell-style="discountHeaderStyle"
                          :span-method="objectSpanMethod"
                          :row-class-name="tableRowClassName"
                          tooltip-effect="light">
                  <el-table-column :label="$t('graph.name')">
                    <el-table-column property="type"
                                     width="80"></el-table-column>
                    <el-table-column label=""
                                     show-overflow-tooltip>
                      <template slot-scope="scope">
                        <span class="value"
                              @click="queryAllTreeData(scope.row.name,false,scope.row.graph_name)">
                          {{ scope.row.name }}
                        </span>
                      </template>
                    </el-table-column>
                  </el-table-column>
                  <el-table-column property="step"
                                   :label="$t('debugger.step')"
                                   width="80">
                  </el-table-column>
                  <el-table-column property="dtype"
                                   :label="$t('debugger.dType')"
                                   width="200">
                  </el-table-column>
                  <el-table-column property="shape"
                                   :label="$t('debugger.shape')"
                                   width="120">
                  </el-table-column>
                  <el-table-column :label="$t('debugger.value')"
                                   width="260">
                    <template slot="header">
                      <span class="center">{{ $t('debugger.value')}}</span>
                    </template>
                    <template slot-scope="scope">
                      <div class="value-wrap">
                        <el-button size="mini"
                                   type="text"
                                   v-if="scope.row.value === 'click to view'"
                                   @click="viewValueDetail(scope.row)">
                          {{ $t('debugger.view') }}
                        </el-button>
                        <span v-else
                              class="value-tip"
                              :title="isNaN(scope.row.value)?'':scope.row.value">{{ scope.row.value }}</span>
                        <el-button size="mini"
                                   type="text"
                                   :disabled="!scope.row.has_prev_step"
                                   @click="tensorComparisons(scope.row)">
                          {{ $t('debugger.compareToPre') }}
                        </el-button>
                      </div>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane :label="$t('graph.nodeInfo')"
                       name="detail">
            <div class="table-content">
              <div class="table-wrap">
                <el-table ref="nodeInfo"
                          :data="selectedNode.IOInfo"
                          :header-cell-style="discountHeaderStyle"
                          :span-method="objectSpanMethod"
                          :row-class-name="tableRowClassName"
                          tooltip-effect="light">
                  <el-table-column :label="$t('graph.name')">
                    <el-table-column property="IOType"
                                     width="80"></el-table-column>
                    <el-table-column label=""
                                     show-overflow-tooltip>
                      <template slot-scope="scope">
                        <span class="value"
                              @click="queryAllTreeData(scope.row.name,false,scope.row.graph_name)">
                          {{ scope.row.name }}
                        </span>
                      </template>
                    </el-table-column>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
    <div class="deb-con"
         v-if="tensorCompareFlag">
      <div class="deb-con-title">
        <div class="deb-con-title-left"
             :title="curRowObj.name">
          {{ curRowObj.name }}
        </div>
        <div class="deb-con-title-middle">
          MIN
          <div class="grident">0</div>
          MAX
        </div>
        <div class="deb-con-title-right">
          <div class="close-btn">
            <img src="@/assets/images/close-page.png"
                 @click="tensorCompareFlag=false;dims=null;tolerance=0;">
          </div>
        </div>

      </div>
      <div class="deb-con-slide">
        <div class="deb-con-slide-left"
             v-if="gridType === 'compare'">
          <div class="deb-slide-title">{{ $t('debugger.tolerance') }}</div>
          <div class="deb-slide-width">
            <el-slider v-model="tolerance"
                       :format-tooltip="formatTolenrance"
                       @change="tensorComparisons(curRowObj,dims)"
                       @input="toleranceInputChange()"></el-slider>
          </div>
          <div class="deb-slide-input">
            <el-input v-model="toleranceInput"
                      @input="toleranceValueChange"
                      @keyup.native.enter="tensorComparisons(curRowObj,dims)"></el-input>
          </div>
        </div>
        <div class="deb-con-slide-right">
          <el-button size="mini"
                     class="custom-btn"
                     :class="{green:gridType==='value'}"
                     @click="tabChange('value')">{{ $t('debugger.curValue') }}</el-button>
          <el-button size="mini"
                     class="custom-btn"
                     :class="{green:gridType==='compare'}"
                     :disabled="!curRowObj.has_prev_step"
                     @click="tabChange('compare')">{{ $t('debugger.compareToPre') }}</el-button>
        </div>
      </div>

      <div class="deb-con-table">
        <div class="deb-compare-wrap">
          <debuggerGridTable v-if="gridType==='value'"
                             :fullData="tensorValue"
                             :showFilterInput="showFilterInput"
                             ref="tensorValue"
                             gridType="value"
                             @martixFilterChange="tensorFilterChange($event)">
          </debuggerGridTable>
          <debuggerGridTable v-else
                             :fullData="tensorValue"
                             :showFilterInput="showFilterInput"
                             ref="tensorValue"
                             gridType="compare"
                             @martixFilterChange="tensorFilterChange($event)">
          </debuggerGridTable>
        </div>
        <div class="deb-compare-detail">
          <span>{{ $t('tensors.dimension') }} {{ curRowObj.shape }}</span>
          <div v-for="(statistics,key) in statisticsArr"
               :key="key">
            <label v-if="key===0">{{$t('debugger.curStatisticsLabel')}}<span>{{ metadata.step }}</span></label>
            <label v-if="key===1">{{$t('debugger.preStatisticsLabel')}}<span>{{ metadata.step-1 }}</span></label>
            <label v-if="key===2">{{$t('debugger.diffStatisticsLabel')}}</label>
            <span>{{ $t('debugger.max') }} {{ statistics.overall_max }}</span>
            <span>{{ $t('debugger.min') }} {{ statistics.overall_min }}</span>
            <span>{{ $t('debugger.mean') }} {{ statistics.overall_avg }}</span>
            <span>{{ $t('debugger.nan') }} {{ statistics.overall_nan_count }}</span>
            <span>{{ $t('debugger.negativeInf') }} {{ statistics.overall_neg_inf_count }}</span>
            <span>{{ $t('debugger.inf') }} {{ statistics.overall_pos_inf_count }}</span>
            <span>{{ $t('debugger.zero') }} {{ statistics.overall_zero_count }}</span>
            <span>{{ $t('debugger.negativeNum') }} {{ statistics.overall_neg_zero_count }}</span>
            <span>{{ $t('debugger.positiveNum') }} {{ statistics.overall_pos_zero_count }}</span>
          </div>
        </div>
      </div>
    </div>
    <el-dialog :title="$t('debugger.createWP')"
               :visible.sync="createWPDialogVisible"
               :show-close="false"
               :close-on-click-modal="false"
               :modal-append-to-body="false"
               class="creat-watch-point-dialog"
               width="900px">

      <div class="conditions-container">
        <div class="condition-item"
             v-for="(item, index) in createWatchPointArr"
             :key="index">
          <el-select v-model="item.collection.selectedId"
                     class="collection"
                     @change="collectionChange(item)">
            <el-option v-for="i in conditionCollections"
                       :key="i.id"
                       :label="transCondition(i.id)"
                       :value="i.id">
            </el-option>
          </el-select>
          <el-select v-model="item.condition.selectedId"
                     class="condition"
                     @change="conditionChange(item)">
            <el-option v-for="i in item.condition.options"
                       :key="i.id"
                       :label="transCondition(i.id)"
                       :value="i.id">
            </el-option>
          </el-select>

          <el-select v-model="item.param.name"
                     @change="paramChange(item)"
                     v-if="item.param.options.length"
                     class="param">
            <el-option v-for="i in item.param.options"
                       :key="i.name"
                       :label="transCondition(i.name)"
                       :value="i.name">
            </el-option>
          </el-select>

          <el-input v-model="item.param.value"
                    :placeholder="$t('scalar.placeHolderNumber')"
                    v-if="item.param.options.length &&
                                item.param.type !== 'BOOL'"
                    @input="validateParam(item)"
                    class="param-value"></el-input>
          <el-select v-model="item.param.value"
                     v-if="item.param.options.length &&
                                item.param.type === 'BOOL'"
                     class="param-value">
            <el-option :key="true"
                       label="true"
                       :value="true">
            </el-option>
            <el-option :key="false"
                       label="false"
                       :value="false">
            </el-option>
          </el-select>
        </div>
      </div>
      <span slot="footer"
            class="dialog-footer">
        <el-button type="primary"
                   size="mini"
                   class="custom-btn green"
                   :disabled="!validPram"
                   @click="createWatchPoint(true)">{{$t('public.sure')}}</el-button>
        <el-button type="primary"
                   size="mini"
                   class="custom-btn"
                   @click="createWatchPoint(false)">
          {{ $t('public.cancel') }}
        </el-button>
      </span>
    </el-dialog>

    <el-dialog :title="$t('public.notice')"
               :visible.sync="dialogVisible"
               :show-close="false"
               :close-on-click-modal="false"
               :modal-append-to-body="false"
               class="pendingTips"
               width="420px">

      <span class="dialog-icon">
        <span class="el-icon-warning"></span>
      </span>
      <span v-if="initFail"
            class="dialog-content">{{ $t('debugger.debuggerError') }}</span>
      <span v-else
            class="dialog-content">{{ $t('debugger.pendingTips') }}</span>

      <span slot="footer"
            class="dialog-footer">
        <el-button type="primary"
                   size="mini"
                   class="custom-btn green"
                   @click="toSummeryList()">{{$t('debugger.toSummeryList')}}</el-button>
      </span>
    </el-dialog>
  </div>
</template>
<script>
import {select, selectAll, zoom, dispatch} from 'd3';
import 'd3-graphviz';
import debuggerGridTable from '../../components/debugger-grid-table-simple.vue';
const d3 = {select, selectAll, zoom, dispatch};
import RequestService from '@/services/request-service';
import commonGraph from '../../mixins/common-graph.vue';
import debuggerMixin from '../../mixins/debugger-mixin.vue';
import tree from '../../components/tree.vue';

export default {
  mixins: [commonGraph, debuggerMixin],
  data() {
    return {
      leftShow: false,
      searchWord: '',
      tableData: [],
      currentRow: null,
      tipsFlag: false,
      props: {
        label: 'label',
        children: 'children',
        isLeaf: 'leaf',
      },
      defaultProps: {
        children: 'nodes',
        label: 'label',
        isLeaf: 'leaf',
      },
      curNodeData: [],
      lazy: true,
      radio1: 'tree',
      nodeTypes: {
        options: ['all', 'weight', 'activation', 'gradient'],
        label: {},
        value: 'all',
      },
      watchPointArr: [],
      allWatchPointFlag: true,
      enableRecheck: false,
      dynamicTreeData: [],
      watchPointHits: [],
      defaultCheckedArr: [],
      origialTree: [],
      conditionCollections: [],
      createWatchPointArr: [],
      createWPDialogVisible: false,
      validPram: false,
      curWatchPointId: null,
      step: '',
      metadata: {},
      searchTreeData: [],
      treeFlag: true,
      curCheckedName: '',
      isSelected: false,
      searchCheckedArr: [],
      curHalfCheckedKeys: [],
      tensorValue: [],
      loadingOption: {
        lock: true,
        text: this.$t('public.dataLoading'),
        spinner: 'el-icon-loading',
        background: 'rgba(0, 0, 0, 0.3)',
      },
      outputLength: 0,
      inputLength: 0,
      curLeafNodeName: null,

      graphFiles: {
        options: [],
        value: '',
        graphs: {},
      },
      allGraphData: {}, // Graph Original input data
      firstFloorNodes: [], // ID array of the first layer node.
      nodesCountLimit: 1500, // Maximum number of sub-nodes in a namespace.
      maxChainNum: 70,
      scaleRange: [0.001, 1000], // Graph zooms in and zooms out.
      graphviz: null,
      graphvizTemp: null,
      graph: {},
      selectedNode: {},
      svg: {},
      contextmenu: {
        point: {},
        id: 'contextMenu',
        dom: null,
      },
      code: '',
      version: 'Ascend',
      nodeName: '',
      pollInit: true,
      collapseTable: false,
      dialogVisible: false,
      initFail: false,
      isIntoView: true,
      tolerance: 0,
      tensorCompareFlag: false,
      gridType: 'compare',
      curRowObj: {},
      dims: null,
      node: null,
      resolve: null,
      toleranceInput: 0,
      showFilterInput: true,
      currentNodeName: '',
      statisticsArr: [],
      tabs: {
        activeName: 'tensor',
      },
      searchNode: null,
      searchResolve: null,
      isCurrentGraph: true, // Check whether the new and old graphs are the same.
      expandKeys: [],
      isHitIntoView: true,
      unCheckedNodeType: 'Const',
    };
  },
  components: {debuggerGridTable, tree},
  computed: {},
  mounted() {
    document.title = `${this.$t('debugger.debugger')}-MindInsight`;
    window.addEventListener(
        'resize',
        this.debounce(this.resizeCallback, 200),
        false,
    );
    this.nodeTypes.label = this.$t('debugger.nodeType');
  },
  watch: {
    'metadata.state': {
      handler(newValue, oldValue) {
        if (newValue === 'pending' && oldValue !== undefined) {
          location.reload();
        }
        if (oldValue === 'pending' && newValue === 'waiting') {
          this.loadNode(this.node, this.resolve);
        }
        if (oldValue === 'running' && newValue === 'waiting') {
          this.getWatchpointHits();
        }
        if (newValue === 'pending') {
          this.dialogVisible = true;
        } else {
          this.dialogVisible = false;
        }
      },
      deep: true,
    },
  },
  methods: {
    queryGraphByFile() {
      this.searchWord = '';
      this.nodeTypes.value = 'all';
      this.treeFlag = true;
      const params = {
        mode: 'node',
        params: {
          watch_point_id: this.curWatchPointId ? this.curWatchPointId : 0,
          graph_name: this.graphFiles.value,
        },
      };
      if (this.graphFiles.value === this.$t('debugger.all')) {
        delete params.params.graph_name;
      }
      RequestService.retrieve(params).then(
          (res) => {
            if (res.data && res.data.metadata) {
              this.dealMetadata(res.data.metadata);
            }
            if (res.data && res.data.graph) {
              const graph = res.data.graph;
              this.origialTree = res.data.graph.nodes.map((val) => {
                return {
                  label: val.name.split('/').pop(),
                  leaf:
                  val.type === 'name_scope' || val.type === 'aggregation_scope'
                    ? false
                    : true,
                  ...val,
                  showCheckbox: val.type !== this.unCheckedNodeType,
                };
              });
              this.node.childNodes = [];
              this.resolve(this.origialTree);
              // watched 0:unchecked  1:indeterminate 2:checked
              this.defaultCheckedArr = this.origialTree
                  .filter((val) => {
                    return val.watched === 2 && val.type !== this.unCheckedNodeType;
                  })
                  .map((val) => val.name);
              this.node.childNodes.forEach((val) => {
                if (val.data.watched === 1 && val.data.type !== this.unCheckedNodeType) {
                  val.indeterminate = true;
                }
                if (val.data.watched === 0) {
                  val.checked = false;
                }
                if (val.data.watched === 2 && val.data.type !== this.unCheckedNodeType) {
                  val.checked = true;
                }
              });
              this.firstFloorNodes = [];
              this.allGraphData = {};
              d3.select('#graph svg').remove();
              this.selectedNode.name = '';
              this.dealGraphData(JSON.parse(JSON.stringify(graph.nodes)));
            }
          },
          (err) => {
            this.showErrorMsg(err);
            this.resolve([]);
          },
      );
    },
    selectAllFiles(type) {
      if (
        !type &&
        !this.$refs.tree.getCheckedKeys().length &&
        !this.$refs.tree.getHalfCheckedKeys().length
      ) {
        return;
      }
      if (type && !this.node.childNodes.find((val) => val.checked === false)) {
        return;
      }
      let watchNodes = [];
      this.node.childNodes.forEach((val) => {
        if (type !== val.checked || (!type && val.indeterminate)) {
          watchNodes.push(val.data.name);
        }
        val.indeterminate = false;
        val.checked = type;

        if (val.childNodes) {
          this.dealCheckPro(val.childNodes, type);
        }
      });
      if (type) {
        watchNodes = this.$refs.tree.getCheckedKeys();
      }
      if (this.curWatchPointId) {
        const params = {
          watch_point_id: this.curWatchPointId ? this.curWatchPointId : 0,
          watch_nodes: watchNodes,
          mode: type ? 1 : 0,
          graph_name: this.graphFiles.value,
        };
        if (this.graphFiles.value === this.$t('debugger.all')) {
          delete params.graph_name;
        }
        RequestService.updateWatchpoint(params).then(
            (res) => {
              this.defaultCheckedArr = this.$refs.tree.getCheckedKeys();
            },
            (err) => {
              this.showErrorMsg(err);
            },
        );
      }
    },
    nodeTypesChange() {
      if (this.nodeTypes.value === 'all' && !this.searchWord) {
        this.treeFlag = true;
        this.node.level = 0;
        this.queryGraphByFile();
      } else {
        this.treeFlag = false;
        this.filter();
      }
    },
    /**
     * Query graph data by watchpoint id
     * @param {Number} id Wacthpoint id
     */
    queryGraphByWatchpoint(id) {
      const params = {
        mode: 'watchpoint',
        params: {watch_point_id: id, graph_name: this.graphFiles.value},
      };
      if (this.graphFiles.value === this.$t('debugger.all')) {
        delete params.params.graph_name;
      }
      RequestService.retrieve(params).then(
          (res) => {
            if (res.data && res.data.graph) {
              const graph = res.data.graph;
              this.curNodeData = graph.nodes.map((val) => {
                return {
                  label: val.name.split('/').pop(),
                  ...val,
                  showCheckbox: val.type !== this.unCheckedNodeType,
                };
              });
              this.node.childNodes = [];
              this.curWatchPointId = id;
              this.resolve(this.curNodeData);
              this.$refs.tree.getCheckedKeys().forEach((val) => {
                this.$refs.tree.setChecked(val, false);
              });
              // watched 0:unchecked  1:indeterminate 2:checked
              this.defaultCheckedArr = this.curNodeData
                  .filter((val) => {
                    return val.watched === 2 && val.type !== this.unCheckedNodeType;
                  })
                  .map((val) => val.name);
              const halfSelectArr = this.curNodeData
                  .filter((val) => {
                    return val.watched === 1 && val.type !== this.unCheckedNodeType;
                  })
                  .map((val) => val.name);
              this.node.childNodes.forEach((val) => {
                if (halfSelectArr.indexOf(val.data.name) !== -1) {
                  val.indeterminate = true;
                }
              });

              this.firstFloorNodes = [];
              this.allGraphData = {};
              d3.select('#graph svg').remove();
              this.selectedNode.name = '';
              this.dealGraphData(JSON.parse(JSON.stringify(graph.nodes)));
            }
          },
          (err) => {
            this.showErrorMsg(err);
          },
      );
    },
    /** ************************ graph **********************/

    /**
     * Get watchpoint messages
     * @param {Object} item Wacthpoint data
     * @return {String}
     */
    getWatchPointContent(item) {
      let param = '';
      if (item.params.length) {
        item.params.forEach((i, ind) => {
          const name = this.transCondition(i.name);
          if (!ind) {
            param += `${name}:${i.value}`;
          } else {
            param += `, ${name}:${i.value}`;
          }
        });
        param = `(${param})`;
      }

      const str = `${this.$t('debugger.watchPoint')} ${
        item.id
      }: ${this.transCondition(item.condition)} ${param}`;
      return str;
    },
    /** ************************ graph **********************/

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
      // The graph generated by the plug-in has a useless title and needs to be deleted.
      const title = document.querySelector('#graph g#graph0 title');
      if (title) {
        title.remove();
      }

      this.graph.dom = document.querySelector(`#graph #graph0`);
      const graphRect = this.graph.dom.getBoundingClientRect();
      let transform = '';
      if (this.graph.dom.getAttribute('transform')) {
        // transform information of graph
        transform = this.graph.dom.getAttribute('transform').split(/[(,)]/);
      } else {
        transform = ['translate', '0', '0', ' scale', '1'];
      }
      this.graph.transform = {
        k: parseFloat(transform[4]),
        x: parseFloat(transform[1]),
        y: parseFloat(transform[2]),
      };

      this.graph.minScale =
        Math.min(
            this.svg.rect.width / 2 / graphRect.width,
            this.svg.rect.height / 2 / graphRect.height,
        ) * this.graph.transform.k;

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
            this.clickEvent(target, index, nodesList, 'debugger');
          },
          false,
      );
      // namespaces Expansion or Reduction
      nodes.on(
          'dblclick',
          (target, index, nodesList) => {
            this.dblclickEvent(target, index, nodesList, 'debugger');
          },
          false,
      );
      this.initZooming('debugger');
      this.initContextMenu();

      if (this.selectedNode.name) {
        this.selectNode(true, true);
      }
    },
    /**
     * Initialize the right-click menu
     */
    initContextMenu() {
      this.contextmenu.dom = document.querySelector('#contextMenu');
      const svgDom = document.querySelector('#graph svg');
      const ignoreType = [
        'Parameter',
        'Const',
        'Depend',
        'make_tuple',
        'tuple_getitem',
        'ControlDepend',
      ];

      const dispatch = d3
          .dispatch('start', 'contextmenu')
          .on('start', (event) => {
            this.contextmenu.dom.style.display = 'none';
            this.contextmenu.point = {x: event.x, y: event.y};
          })
          .on('contextmenu', (target) => {
            const svgRect = svgDom.getBoundingClientRect();
            this.contextmenu.dom.style.left = `${
              this.contextmenu.point.x - svgRect.x
            }px`;
            this.contextmenu.dom.style.top = `${
              this.contextmenu.point.y - svgRect.y
            }px`;
            this.contextmenu.dom.style.display = 'block';

            this.selectedNode.name = target.name;
            this.selectNode(false, true);
          });

      const nodes = d3.selectAll('g.node, g.cluster');
      nodes.on(
          'contextmenu',
          (target, index, nodesList) => {
            event.preventDefault();
            const node = this.allGraphData[
                nodesList[index].id.replace('_unfold', '')
            ];
            if (node) {
              if (
                !(
                  this.version !== 'GPU' ||
                ignoreType.includes(node.type) ||
                node.type.endsWith('_scope') ||
                node.type.endsWith('Summary')
                )
              ) {
                setTimeout(() => {
                  dispatch.call('contextmenu', this, node);
                }, 10);
              }
            }
          },
          true,
      );

      document.oncontextmenu = (event) => {
        dispatch.apply('start', this, [event]);
      };

      document.onmousedown = () => {
        this.contextmenu.dom.style.display = 'none';
      };

      this.contextmenu.dom.onmousedown = () => {
        this.continueTo();
      };
    },
    /**
     * Continue to
     */
    continueTo() {
      this.watchPointHits = [];
      const params = {
        mode: 'continue',
        level: 'node',
        name: this.selectedNode.name.replace('_unfold', ''),
        graph_name: this.graphFiles.value,
      };
      if (this.graphFiles.value === this.$t('debugger.all')) {
        delete params.graph_name;
      }
      RequestService.control(params).then(
          (res) => {
            if (res && res.data) {
            }
          },
          (error) => {
            this.showErrorMsg(error);
          },
      );
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
     * Close the expanded namespace.
     * @param {String} name The name of the namespace to be closed.
     */
    deleteNamespace(name) {
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
     * To obtain graph data, initialize and expand the namespace or aggregate nodes.
     * @param {String} name Name of the current node.
     */
    queryGraphData(name) {
      const type = this.allGraphData[name]
        ? this.allGraphData[name].type
        : 'name_scope';
      const mode = name ? 'node' : 'all';
      const params = {
        mode: mode,
      };
      if (name) {
        params.params = {
          watch_point_id: this.curWatchPointId ? this.curWatchPointId : 0,
          name: name,
          node_type: type,
          single_node: false,
          graph_name: this.graphFiles.value,
        };
        if (this.graphFiles.value === this.$t('debugger.all')) {
          delete params.params.graph_name;
        }
      }
      RequestService.retrieve(params)
          .then(
              (response) => {
                if (response && response.data && response.data.graph) {
                  const graph = response.data.graph;
                  const nodes = JSON.parse(JSON.stringify(graph.nodes));
                  this.nodeExpandLinkage(nodes, name);
                  this.dealGraphData(nodes, name);
                }
              },
              (error) => {
                this.showErrorMsg(error);
              },
          )
          .catch((error) => {
          // A non-Google Chrome browser may not work properly.
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
     * Process graph data
     * @param {Object} nodes Nodes data
     * @param {String} name Node name
     */
    dealGraphData(nodes, name) {
      const namescopeChildLimit = 3500;
      const nodesCountLimit = name ? this.nodesCountLimit : namescopeChildLimit;
      const independentLayout = this.allGraphData[name]
        ? this.allGraphData[name].independent_layout
        : false;

      if (!independentLayout && nodes.length > nodesCountLimit) {
        this.$message.error(this.$t('graph.tooManyNodes'));
        this.packageDataToObject(name, false);
      } else {
        if (nodes && nodes.length) {
          this.packageDataToObject(name, true, nodes);
          // If the name is empty, it indicates the outermost layer.
          if (!name) {
            const dot = this.packageGraphData();
            this.initGraph(dot);
          } else {
            if (this.allGraphData[name].type === 'aggregation_scope') {
              this.dealAggregationNodes(name);
              if (this.allGraphData[name].maxChainNum > this.maxChainNum) {
                this.$message.error(this.$t('graph.tooManyChain'));
                this.allGraphData[name].isUnfold = true;
                this.selectedNode.name = name;
                this.deleteNamespace(name);
                return;
              }
            }
            this.allGraphData[name].isUnfold = true;
            this.selectedNode.name = `${name}_unfold`;
            this.layoutNamescope(name, true);
          }
        }
      }
    },
    /**
     * Selecting a node
     * @param {Boolean} needFocus Whether to focus on the node
     * @param {Boolean} isQueryTensor Whether to query tensorValue
     */
    selectNode(needFocus = false, isQueryTensor) {
      window.getSelection().removeAllRanges();
      d3.selectAll(
          '.node polygon, .node ellipse, .node rect, .node path',
      ).classed('selected', false);
      const path = this.selectedNode.name.split('^');
      const node = {};
      let id = path[0].replace('_unfold', '');
      this.selectedNode.name = id;
      node.data = this.allGraphData[id];
      if (node.data) {
        id = this.allGraphData[id].isUnfold ? `${id}_unfold` : id;
        node.dom = document.querySelector(`#graph g[id="${id}"]`);

        if (node.dom) {
          const needDelay = path.length > 1;
          if ((needFocus || needDelay) && node.dom) {
            this.selectNodePosition(id, needDelay);
          }

          d3.select(`#graph g[id="${id}"]`)
              .select('polygon, rect, ellipse, path')
              .classed('selected', true);

          this.highlightProxyNodes(id.replace('_unfold', ''));
          this.highLightEdges(node.data);

          this.$refs.tree.setCurrentKey(id.replace('_unfold', ''));
          if (this.isIntoView) {
            this.$nextTick(() => {
              setTimeout(() => {
                const dom = document.querySelector(
                    '.el-tree-node.is-current.is-focusable',
                );
                if (dom) {
                  dom.scrollIntoView();
                }
              }, 800);
            });
          }
          this.isIntoView = true;
          const type = this.allGraphData[path[0].replace('_unfold', '')].type;
          const ignoreType = ['name_scope', 'aggregation_scope'];
          if (
            isQueryTensor &&
            !this.selectedNode.name.includes('more...') &&
            !ignoreType.includes(type)
          ) {
            if (this.graph.timer) {
              clearTimeout(this.graph.timer);
            }
            this.graph.timer = setTimeout(() => {
              const name = path[0].replace('_unfold', '');
              if (this.graphFiles.value === this.$t('debugger.all')) {
                this.retrieveTensorHistory(
                    {name: name.replace(`${name.split('/')[0]}/`, '')},
                    name.split('/')[0],
                );
              } else {
                this.retrieveTensorHistory(
                    {
                      name,
                    },
                    this.graphFiles.value,
                );
              }
            }, 500);
          }
          if (ignoreType.includes(type)) {
            this.tableData = [];
          } else {
            if (this.graphFiles.value === this.$t('debugger.all')) {
              this.nodeName = this.selectedNode.name.replace(
                  `${this.selectedNode.name.split('/')[0]}/`,
                  '',
              );
            } else {
              this.nodeName = this.selectedNode.name;
            }
          }
        }
      }
      this.setSelectedNodeData(node.data);
      if (
        this.watchPointHits.length &&
        this.radio1 === 'hit' &&
        this.isHitIntoView
      ) {
        this.focusWatchpointHit();
      }
      this.isHitIntoView = true;
    },
    /**
     * The node information of the selected node.
     * @param {Object} selectedNode Node data
     */
    setSelectedNodeData(selectedNode = {}) {
      this.selectedNode.IOInfo = [];
      this.selectedNode.inputNum = 0;
      this.selectedNode.outputNum = 0;
      if (selectedNode.output) {
        Object.keys(selectedNode.output).forEach((key) => {
          let graphName = this.graphFiles.value;
          if (this.graphFiles.value === this.$t('debugger.all')) {
            graphName = key.split('/')[0];
            key = key.replace(`${graphName}/`, '');
          }
          const obj = {name: key, IOType: 'output', graph_name: graphName};
          this.selectedNode.IOInfo.push(obj);
          this.selectedNode.outputNum++;
        });
      }
      if (selectedNode.input) {
        Object.keys(selectedNode.input).forEach((key) => {
          let graphName = this.graphFiles.value;
          if (this.graphFiles.value === this.$t('debugger.all')) {
            graphName = key.split('/')[0];
            key = key.replace(`${graphName}/`, '');
          }
          const obj = {name: key, IOType: 'input', graph_name: graphName};
          this.selectedNode.IOInfo.push(obj);
          this.selectedNode.inputNum++;
        });
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

      const graphObj = {};
      graphObj.rect = this.graph.dom.getBoundingClientRect();
      graphObj.initWidth = graphObj.rect.width / this.graph.transform.k;
      graphObj.initHeight = graphObj.rect.height / this.graph.transform.k;

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
        screenChange.x * (this.svg.originSize.width / graphObj.initWidth);
      this.graph.transform.y -=
        screenChange.y * (this.svg.originSize.height / graphObj.initHeight);

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
    },
    /**
     * Reset graph and data
     */
    resetGraph() {
      const temp = {};
      this.firstFloorNodes.forEach((key) => {
        const node = this.allGraphData[key];
        node.isUnfold = false;
        node.children = [];
        node.size = [];
        node.html = '';
        temp[node.name] = node;
      });
      this.allGraphData = JSON.parse(JSON.stringify(temp));
      d3.select('#graph svg').remove();
      this.selectedNode.name = '';
      const dot = this.packageGraphData();
      this.initGraph(dot);
    },
    /**
     * Search for all data of a specific node and its namespace.
     * @param {Object} graphs Selected node data object
     * @param {String} name Node name
     * @param {Boolean} isQueryTensor Whether to query tensorValue
     */
    querySingleNode(graphs, name, isQueryTensor) {
      this.selectedNode.name = name;
      this.selectedNode.more = false;
      // If a node exists on the map, select the node.
      if (this.allGraphData[name]) {
        if (d3.select(`g[id="${name}"], g[id="${name}_unfold"]`).size()) {
          // If the namespace or aggregation node is expanded, you need to close it and select
          this.selectNode(true, isQueryTensor);
        } else {
          const parentId = name.substring(0, name.lastIndexOf('/'));
          if (
            this.allGraphData[parentId] &&
            this.allGraphData[parentId].isUnfold
          ) {
            const aggregationNode = this.allGraphData[parentId];
            if (aggregationNode && aggregationNode.childIdsList) {
              for (let i = 0; i < aggregationNode.childIdsList.length; i++) {
                if (aggregationNode.childIdsList[i].includes(name)) {
                  aggregationNode.index = i;
                  break;
                }
              }
            }
            this.selectedNode.name = name;
            this.layoutNamescope(parentId, true);
          }
        }
      } else {
        const data = this.findStartUnfoldNode(graphs.children);
        if (data) {
          this.dealAutoUnfoldNamescopesData(data);
        }
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
            this.querySingleNode(data, data.scope_name, true);
            this.selectNode(true, true);
            this.$message.error(this.$t('graph.tooManyNodes'));
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
                return;
              }
            }

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
     * Show error message
     * @param {Object} error Error data
     */
    showErrorMsg(error) {
      if (
        error &&
        error.response &&
        error.response.data &&
        error.response.data.error_code
      ) {
        if (this.$t('error')[`${error.response.data.error_code}`]) {
          this.$message.error(
              this.$t('error')[`${error.response.data.error_code}`],
          );
        } else {
          if (error.response.data.error_code === '5054B101') {
            // The error "The graph does not exist" should not display in front page;
            return;
          }
          this.$message.error(error.response.data.error_msg);
        }
      }
    },
    /**
     * To summery list page
     */
    toSummeryList() {
      this.dialogVisible = false;
      this.$router.push({
        path: '/summary-manage',
      });
    },
    rightCollapse() {
      this.collapseTable = !this.collapseTable;
      setTimeout(() => {
        this.initSvg(false);
      }, 500);
    },
  },
  destroyed() {
    window.removeEventListener(
        'resize',
        this.debounce(this.resizeCallback, 200),
        false,
    );
  },
};
</script>
<style lang="scss">
.deb-wrap {
  height: 100%;
  background-color: white;
  position: relative;
  overflow: hidden;
  & > div {
    float: left;
    height: 100%;
  }
  .left-wrap {
    width: 400px;
    padding-right: 25px;
    height: 100%;
    background-color: white;
    position: relative;
    transition: width 0.2s;
    -moz-transition: width 0.2s; /* Firefox 4 */
    -webkit-transition: width 0.2s; /* Safari and Chrome */
    -o-transition: width 0.2s; /* Opera */
    .left {
      height: 100%;
      background: #fff;
      box-shadow: 0 2px 2px rgba(0, 0, 0, 0.22);
      .header {
        padding: 15px;
        border-bottom: 1px solid #ebeef5;
        position: relative;
        font-weight: bold;
        .radio-tabs {
          position: absolute;
          right: 10px;
          top: 10px;
        }
      }
      .content {
        height: calc(100% - 145px);
        .node-type {
          height: 50px;
          padding: 15px 15px 0 15px;
          .label {
            display: inline-block;
            width: 80px;
          }
          .el-select {
            width: calc(100% - 80px);
          }
        }
        .select-wrap {
          padding: 10px 15px;
          font-size: 14px;
          .el-select .el-input {
            width: 100%;
          }
          .input-with-select .el-input-group__prepend {
            background-color: #fff;
          }
          .el-input--suffix .el-input__inner {
            padding-left: 5px;
            padding-right: 30px;
            font-size: 12px;
          }
        }
        .tree-wrap {
          height: calc(70% - 155px);
          overflow-y: auto;
          padding: 0 15px 15px;
          position: relative;
          z-index: 2;
          .image-type {
            width: 20px;
            height: 10px;
            margin-right: 10px;
          }
          .el-tree {
            & > .el-tree-node {
              min-width: 100%;
              display: inline-block;
            }
          }
        }
        .watch-point-wrap {
          height: 30%;
          border-top: 1px solid #ebeef5;
          .title-wrap {
            height: 30px;
            line-height: 30px;
            padding: 0 20px;
            position: relative;
            border-bottom: 1px solid #ebeef5;
            font-weight: bold;
          }
          .check-wrap {
            position: absolute;
            right: 60px;
            top: 0px;
            .el-icon-circle-check {
              color: #00a5a7;
              cursor: pointer;
              display: none;
            }
            .disable:before {
              cursor: not-allowed;
              color: #adb0b8;
            }
          }
          .delete-wrap {
            position: absolute;
            right: 35px;
            top: 0px;
            .el-icon-delete:before {
              color: #00a5a7;
              cursor: pointer;
            }
            .disable:before {
              cursor: not-allowed;
              color: #adb0b8;
            }
          }
          .add-wrap {
            position: absolute;
            right: 10px;
            top: 0px;
            .el-icon-circle-plus:before {
              color: #00a5a7;
              cursor: pointer;
            }
          }
          .content-wrap {
            padding-left: 20px;
            position: relative;
            height: calc(100% - 30px);
            .list-wrap {
              max-height: 100%;
              overflow: auto;
              padding: 10px 0;
              .list {
                margin-bottom: 10px;
                .name {
                  .item-content {
                    display: inline-block;
                    width: 310px;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                    overflow: hidden;
                  }
                }
                .name:hover {
                  cursor: pointer;
                  color: #00a5a7;
                }
                .name.selected {
                  color: #00a5a7;
                  position: relative;
                  .el-icon-close {
                    position: absolute;
                    right: 10px;
                    top: 3px;
                  }
                  .el-icon-check {
                    position: absolute;
                    right: 30px;
                    top: 3px;
                  }
                }
              }
            }
          }
        }
        .custom-tree-node {
          padding-right: 8px;
          .const {
            margin-left: 22px;
          }
        }
        .custom-tree-node.highlight {
          color: red;
        }
        .hit-list-wrap {
          height: 100%;
          overflow-y: auto;
          padding: 10px;
          .hit-item {
            word-break: break-all;
            line-height: 18px;
            padding: 10px;
            &:hover {
              cursor: pointer;
            }
          }
          .selected {
            color: #00a5a7;
          }
          .el-table__expanded-cell[class*='cell'] {
            padding: 0px 10px 0 50px;
            ul {
              background-color: #f5f7fa;
              li {
                line-height: 18px;
                padding: 10px;
                word-break: break-all;
                border-top: 1px solid white;
                border-bottom: 1px solid white;
                &:hover {
                  background-color: #ebeef5;
                }
              }
            }
          }
        }
      }
      .btn-wrap {
        padding: 10px 20px;
        border-top: 1px solid #ebeef5;
        .step {
          width: 100%;
          display: flex;
          justify-content: space-between;
          .custom-btn {
            margin-left: 10px;
          }
        }
        .btn-two {
          width: 100%;
          .custom-btn {
            height: 30px;
            margin-top: 10px;
          }
        }
        .el-button + .el-button {
          margin-left: 0px;
        }
        .el-button:not(:last-child) {
          margin-right: 10px;
        }
      }
    }
    .collapse-btn {
      position: absolute;
      right: 2px;
      width: 31px;
      height: 100px;
      top: 50%;
      margin-top: -50px;
      cursor: pointer;
      line-height: 86px;
      z-index: 1;
      text-align: center;
      background-image: url('../../assets/images/collapse-left.svg');
    }
    .collapse-btn.collapse {
      background-image: url('../../assets/images/collapse-right.svg');
    }
  }
  .left-wrap.collapse {
    width: 0px;
  }
  .right {
    width: calc(100% - 400px);
    height: 100%;
    padding-right: 20px;
    transition: width 0.2s;
    -moz-transition: width 0.2s; /* Firefox 4 */
    -webkit-transition: width 0.2s; /* Safari and Chrome */
    -o-transition: width 0.2s; /* Opera */
    .header {
      padding: 15px;
      border-bottom: 1px solid #ebeef5;
      position: relative;
      background: #fff;
      .link {
        color: #00a5a7;
      }
      .host {
        margin-left: 25px;
      }
      span.item {
        margin-right: 15px;
        .content {
          color: #00a5a7;
        }
      }
    }
    .svg-wrap {
      height: 50%;
      border-bottom: 1px solid #ebeef5;
      position: relative;
      .btn-wrap {
        position: absolute;
        top: 10px;
        right: 10px;
      }
      .graph-container {
        height: 100%;
        width: 100%;
        position: relative;
        #graph {
          height: 100%;
          background-color: #f7faff;
          .node:hover > path,
          .node:hover > ellipse,
          .node:hover > polygon,
          .node:hover > rect {
            stroke-width: 2px;
          }
          .node.cluster > rect:hover {
            stroke: #8df1f2;
          }
          .selected {
            stroke: red !important;
            stroke-width: 2px;
          }
          #graph0 > polygon {
            fill: transparent;
          }
          .node {
            cursor: pointer;
          }
          .edge {
            path {
              stroke: rgb(120, 120, 120);
            }
            polygon {
              fill: rgb(120, 120, 120);
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
            stroke: #e3aa00;
            fill: #ffe794;
          }
          .node.cluster.aggregation > rect {
            stroke: #e3aa00;
            fill: #ffe794;
            stroke-dasharray: 3, 3;
          }
          .node > polygon {
            stroke: #00a5a7;
            fill: rgb(141, 241, 242);
          }
          .node > ellipse {
            stroke: #4ea6e6;
            fill: #b8e0ff;
          }
          .plain > path,
          .plain ellipse {
            stroke: #e37d29;
            fill: #ffd0a6;
            stroke-dasharray: 1.5, 1.5;
          }
          .edge-point ellipse {
            stroke: #a7a7a7;
            fill: #a7a7a7;
          }
          text {
            fill: black;
          }
        }
        #contextMenu {
          display: none;
          position: absolute;
          min-width: 150px;
          border: 1px solid #d4d4d4;
          ul {
            background-color: #e2e2e2;
            border-radius: 2px;
            li {
              padding: 5px 18px;
              cursor: pointer;
              &:hover {
                background-color: rgb(120, 120, 120);
                color: white;
              }
            }
          }
        }
      }
    }
    .table-container {
      background: #fff;
      height: calc(50% - 60px);
      position: relative;
      img {
        position: absolute;
        right: 10px;
        top: 12px;
        cursor: pointer;
        z-index: 99;
      }
      .el-tabs.el-tabs--top {
        height: 100%;
        .el-tabs__content {
          height: calc(100% - 60px);
          .el-tab-pane {
            height: 100%;
          }
        }
      }
      .table-content {
        height: 100%;
        overflow: hidden;
        position: relative;
        .table-wrap {
          height: 100%;
          overflow-y: auto;
          .el-table .success-row {
            background: #f0f9eb;
          }
        }
        .value-wrap {
          text-align: right;
        }
        .center {
          display: inline-block;
          text-align: center;
          width: 100%;
        }
        .value {
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          cursor: pointer;
          color: #00a5a7;
          display: inline-block;
          width: 100%;
        }
        .value-tip {
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          width: 50px;
          display: inline-block;
          vertical-align: middle;
          text-align: center;
        }
        .el-table--border {
          border-right: none;
          border-left: none;
        }
        .el-table--border td {
          border-right: none;
          border-left: none;
        }
        .el-table--border th {
          border-right: none;
          border-left: none;
        }

        .el-table th > .cell {
          border-left: 1px solid #d9d8dd;
          word-break: keep-all;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .el-table-column--selection .cell {
          border-left: none !important;
        }
      }
    }
    .svg-wrap.collapse {
      height: calc(100% - 100px);
    }
    .table-container.collapse {
      height: 35px;
      .el-tabs__header {
        margin: 0;
      }
      .table-content {
        display: none;
      }
    }
  }
  .right.collapse {
    width: calc(100% - 25px);
  }
  .custom-btn {
    border: 1px solid #00a5a7;
    border-radius: 2px;
    background-color: white;
    color: #00a5a7;
  }
  .custom-btn:hover {
    background-color: #e9f7f7;
  }
  .custom-btn.green {
    background-color: #00a5a7;
    color: white;
  }
  .custom-btn.green:hover {
    background-color: #33b7b9;
  }
  .is-disabled.custom-btn {
    background-color: #f5f5f6;
    border: 1px solid #dfe1e6 !important;
    color: #adb0b8;
    &:hover {
      background-color: #f5f5f6;
    }
  }
  .notShow {
    display: none;
  }
  .conditions-container {
    .collection {
      width: 200px;
    }
    .condition {
      margin-left: 10px;
      width: 200px;
    }
    .param {
      margin-left: 10px;
      width: 200px;
    }
    .param-value {
      margin-left: 10px;
      width: 200px;
    }
  }
  .el-dialog__wrapper.pendingTips {
    position: absolute;
    .dialog-icon {
      .el-icon-warning {
        font-size: 24px;
        color: #e37d29;
        vertical-align: bottom;
      }
    }
    .el-dialog__body {
      padding: 2px 20px 32px 20px;
      .dialog-content {
        line-height: 24px;
        margin-left: 10px;
      }
    }
    .el-dialog__footer {
      text-align: center;
      padding: 10px 20px 32px;
    }
  }
  .el-dialog__wrapper.pendingTips + .v-modal {
    position: absolute;
  }
  .deb-con {
    position: absolute;
    top: 0px;
    width: 100%;
    height: 100%;
    background-color: #fff;
    z-index: 999;
    display: flex;
    flex-direction: column;

    .deb-con-title {
      height: 56px;
      line-height: 56px;
      flex-shrink: 0;
      position: relative;

      .deb-con-title-left {
        position: absolute;
        left: 32px;
        font-weight: bold;
        font-size: 16px;
        width: 50%;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .deb-con-title-middle {
        position: absolute;
        left: calc(50% + 32px);
        width: 300px;
        padding: 10px 0;
        line-height: 36px;
        .grident {
          display: inline-block;
          width: calc(100% - 70px);
          background-image: linear-gradient(
            to right,
            rgba(227, 125, 41),
            #fff,
            rgba(0, 165, 167)
          );
          text-align: center;
          color: transparent;
        }
      }
      .deb-con-title-right {
        position: absolute;
        right: 32px;

        .close-btn {
          width: 20px;
          height: 20px;
          vertical-align: -3px;
          cursor: pointer;
          display: inline-block;
          line-height: 20px;
          margin-left: 32px;
        }
      }
    }

    .deb-con-slide {
      height: 40px;
      line-height: 40px;
      flex-shrink: 0;
      position: relative;

      .deb-con-slide-left {
        position: absolute;
        left: 32px;
        display: flex;

        .deb-slide-title {
          margin-right: 20px;
        }

        .deb-slide-width {
          width: 400px;
        }
        .deb-slide-input {
          width: 100px;
          margin-left: 10px;
        }
      }
      .deb-con-slide-right {
        position: absolute;
        right: 32px;

        .custom-btn {
          border: 1px solid #00a5a7;
          border-radius: 2px;
        }
        .green {
          background-color: #00a5a7;
          color: white;
        }
        .white {
          background-color: white;
          color: #00a5a7;
        }
      }
    }

    .deb-con-table {
      margin-top: 20px;
      flex: 1;
      padding: 0 32px;
      .deb-compare-wrap {
        height: calc(100% - 120px);
      }
      .deb-compare-detail {
        height: 120px;
        overflow: auto;
        span {
          margin-right: 15px;
        }
        & > div {
          margin-top: 10px;
        }
        label {
          display: inline-block;
          min-width: 100px;
        }
      }
    }
  }
}
.deb-indent {
  padding-left: 40px;
}
#graphTemp,
#subgraphTemp {
  position: absolute;
  bottom: 0;
  visibility: hidden;
}
</style>

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
          {{$t('debugger.nodeList')}}
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
            <el-tree v-show="treeFlag"
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
                     :show-checkbox="curWatchPointId!==null">
              <span slot-scope="{ node , data}">
                <span class="custom-tree-node "
                      :class="{highlight:data.highlight}">{{ node.label }}</span>
              </span>
            </el-tree>
            <el-tree v-show="!treeFlag"
                     :data="searchTreeData"
                     :props="defaultProps"
                     node-key="name"
                     :default-checked-keys="searchCheckedArr"
                     default-expand-all
                     @node-click="handleNodeClick"
                     ref="searchTree">
            </el-tree>
          </div>
          <div class="watch-point-wrap">
            <div class="title-wrap">
              {{$t('debugger.watchList')}}
              <div class="add-wrap">
                <i class="el-icon-circle-plus"
                   @click="addWatchPoint"></i>
              </div>
            </div>
            <div class="content-wrap">
              <ul class="list-wrap"
                  v-show="allWatchPointFlag">
                <li class="list"
                    v-for="(item,key) in watchPointArr"
                    :key="key"
                    :title="$t('debugger.watchPoint') + ' ' + item.id + ': ' +
                    item.label + ' ' + item.param">
                  <div class="name"
                       :class="{selected:item.selected}"
                       @click="selectWatchPoint(key)">
                    <div class="item-content">
                      {{$t('debugger.watchPoint')}} {{item.id}}: {{item.label}} {{item.param}}
                    </div>
                    <i class="el-icon-close"
                       v-if="item.selected"
                       @click.stop="deleteWatchpoint(item)"></i>
                  </div>
                  <div v-show="!watchPointPending && key === watchPointArr.length - 1">
                    <div class="condition">
                      <el-select v-model="item.condition"
                                 :placeholder="$t('debugger.selectCondition')"
                                 @change="conditionChange(item)">
                        <el-option v-for="i in conditions.options"
                                   :key="i.value"
                                   :label="i.label"
                                   :value="i.value">
                        </el-option>
                      </el-select>
                      <el-input v-model="item.param"
                                :placeholder="$t('scalar.placeHolderNumber')"
                                v-if="conditions.hasValue.includes(item.condition)"
                                @input="validateParam(item)"
                                class="condition-param"></el-input>
                      <div class="btn-wrap">
                        <el-button type="primary"
                                   size="mini"
                                   class="custom-btn"
                                   @click="createWatchPoint(item)"
                                   :disabled="!(conditions.noValue.includes(item.condition) ||
                                   (conditions.hasValue.includes(item.condition) && validPram))">
                          {{ $t('public.sure') }}
                        </el-button>
                      </div>
                    </div>
                  </div>
                </li>
              </ul>
            </div>
          </div>
          <div class="btn-wrap">
            <div class="step">
              <el-input v-model="step"
                        :placeholder="$t('debugger.inputStep')"
                        @input="stepChange"
                        @keyup.native.enter="control(0)">
              </el-input>
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
        <div class="hit"
             v-show="radio1==='hit'">
          <div class="content">
            <div class="title">{{ $t('debugger.curHitNode') }}</div>
            <div class="hit-list-wrap">
              <div class="hit-list"
                   v-for="(item,key) in watchPointHits"
                   :key="key">
                <div>
                  <div class="node-name"
                       :class="{selected:item.selected}"
                       @click="updateTensorValue(key)">{{ item.node_name }}</div>
                  <div class="watch-points"
                       v-for="(watchpoint,index) in item.watch_points"
                       :key="index">
                    id:{{ watchpoint.id }}&nbsp;condition :{{
                      conditionMappings[watchpoint.watch_condition.condition]
                         }} {{watchpoint.watch_condition.param}}
                  </div>
                </div>
              </div>
              <div class="no-data"
                   v-if="!watchPointHits.length">
                {{ $t('public.noData') }}
              </div>
            </div>
          </div>
          <div class="btn-wrap">
            <div class="step">
              <el-input v-model="step"
                        :placeholder="$t('debugger.inputStep')"
                        @input="stepChange"
                        @keyup.native.enter="control(0)">
              </el-input>
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
                     class="custom-btn green"
                     @click="getNodeByBfs(false)">
            {{ $t('debugger.previousNode')}}
          </el-button>
          <el-button v-else
                     type="primary"
                     size="mini"
                     class="custom-btn green"
                     :disabled="!nodeName"
                     :class="{disabled:!nodeName}"
                     @click="getCurrentNodeInfo">
            {{ $t('debugger.currentNode')}}
          </el-button>
          <el-button v-if="version==='Ascend'"
                     type="primary"
                     size="mini"
                     class="custom-btn white"
                     @click="getNodeByBfs(true)">
            {{ $t('debugger.nextNode')}}
          </el-button>
          <el-button v-else
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
             @click="collapseTable=!collapseTable"
             alt="" />
        <img :src="require('@/assets/images/all-uptake.png')"
             v-show="!collapseTable"
             @click="collapseTable=!collapseTable"
             alt="" />
        <div class="table-title">{{ $t('debugger.tensorMsg')}}</div>

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
                          @click="queryAllTreeData(scope.row.name,false)">
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
      </div>
    </div>
    <div class="deb-con"
         v-if="tensorCompareFlag">
      <div class="deb-con-title">
        <div class="deb-con-title-left">
          {{ curRowObj.name }}
        </div>

        <div class="deb-con-title-right">
          <div class="close-btn">
            <img src="@/assets/images/close-page.png"
                 @click="tensorCompareFlag=false">
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
                       @change="tensorComparisons(curRowObj,dims)"></el-slider>
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
                             ref="tensorValue"
                             gridType="value"
                             @martixFilterChange="tensorFilterChange($event)">
          </debuggerGridTable>
          <debuggerGridTable v-else
                             :fullData="tensorValue"
                             ref="tensorValue"
                             gridType="compare"
                             @martixFilterChange="tensorFilterChange($event)">
          </debuggerGridTable>
        </div>
        <div class="deb-compare-detail">
          {{ $t('tensors.dimension') }} {{ curRowObj.shape }}
        </div>
      </div>
    </div>
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
import CommonProperty from '@/common/common-property.js';
import RequestService from '@/services/request-service';
import {select, selectAll, zoom, dispatch} from 'd3';
import {event as currentEvent} from 'd3-selection';
import 'd3-graphviz';
import requestService from '../../services/request-service';
import debuggerGridTable from '../../components/debuggerGridTableSimple.vue';
const d3 = {select, selectAll, zoom, dispatch};
export default {
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
      },
      curNodeData: [],
      lazy: true,
      radio1: 'tree',
      watchPointArr: [],
      allWatchPointFlag: true,
      dynamicTreeData: [],
      watchPointHits: [],
      defaultCheckedArr: [],
      watchPointPending: true,
      origialTree: [],
      conditions: {
        options: [],
        hasValue: [],
        noValue: [],
      },
      validPram: false,
      conditionMappings: {},
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
        text: 'Loading',
        spinner: 'el-icon-loading',
        background: 'rgba(0, 0, 0, 0.3)',
      },
      outputLength: 0,
      inputLength: 0,
      curLeafNodeName: null,

      allGraphData: {}, // graph Original input data
      firstFloorNodes: [], // ID array of the first layer node.
      frameSpace: 25, // Distance between the namespace border and the internal node
      nodesCountLimit: 1500, // Maximum number of sub-nodes in a namespace.
      maxChainNum: 70,
      curColorIndex: 0,
      scaleRange: [0.001, 1000], // graph zooms in and zooms out.
      totalMemory: 16777216 * 2, // Memory size of the graph plug-in
      graphviz: null,
      graphvizTemp: null,
      graph: {},
      selectedNode: {},
      svg: {},
      viewBox: {
        max: 10000,
        scale: {x: 1, y: 1},
      },
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
    };
  },
  components: {debuggerGridTable},
  computed: {},
  mounted() {
    document.title = `Debugger-MindInsight`;
    window.addEventListener('resize', this.resizeCallback, false);
    this.initCondition();
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
    /**
     * format tolenrance
     * @param {Number} value
     * @return {String}
     */
    formatTolenrance(value) {
      return `${value}%`;
    },
    /**
     * Tabs change
     * @param {String} gridType tab type
     */
    tabChange(gridType) {
      this.gridType = gridType;
      if (this.gridType === 'compare') {
        this.tensorComparisons(this.curRowObj);
      } else {
        this.viewValueDetail(this.curRowObj);
      }
    },
    /**
     * Query tensor Comparison data
     * @param { Object } row current clickd tensor value data
     * @param { Object } dims dims
     */
    tensorComparisons(row, dims) {
      this.curRowObj = row;
      this.gridType = 'compare';
      const shape = dims
        ? dims
        : JSON.stringify(
            JSON.parse(row.shape)
                .map((val, index) => {
                  if (index < 2) {
                    return ':';
                  } else {
                    return 0;
                  }
                })
                .reverse(),
        ).replace(/"/g, '');
      const params = {
        name: row.name,
        detail: 'data',
        shape,
        tolerance: this.tolerance / 100,
      };
      RequestService.tensorComparisons(params).then((res) => {
        if (res && res.data && res.data.tensor_value) {
          this.tensorCompareFlag = true;
          const tensorValue = res.data.tensor_value;
          if (
            tensorValue.diff &&
            tensorValue.diff.includes('Too large to show')
          ) {
            this.tensorValue = [];
            this.$nextTick(() => {
              this.$refs.tensorValue.showRequestErrorMessage(
                  this.$t('debugger.largeDataTip'),
                  JSON.parse(row.shape),
                  shape,
              );
            });
            return;
          }
          this.tensorValue = tensorValue.diff;
          if (
            this.tensorValue &&
            this.tensorValue instanceof Array &&
            !(this.tensorValue[0] instanceof Array)
          ) {
            this.tensorValue = [this.tensorValue];
          }
          this.$nextTick(() => {
            this.$refs.tensorValue.updateGridData(
                this.tensorValue,
                JSON.parse(row.shape),
                tensorValue.statistics,
                shape,
            );
          });
        }
      });
    },
    /**
     * Initialize the condition
     */
    initCondition() {
      this.conditionMappings = {
        INF: 'INF',
        NAN: 'NAN',
        OVERFLOW: 'OVERFLOW',
        MAX_GT: 'MAX >',
        MAX_LT: 'MAX <',
        MIN_GT: 'MIN >',
        MIN_LT: 'MIN <',
        MAX_MIN_GT: 'MAX-MIN >',
        MAX_MIN_LT: 'MAX-MIN <',
        MEAN_GT: 'MEAN >',
        MEAN_LT: 'MEAN <',
      };
      this.conditions.noValue = ['INF', 'NAN'];
      this.conditions.hasValue = [
        'MAX_GT',
        'MAX_LT',
        'MIN_GT',
        'MIN_LT',
        'MAX_MIN_GT',
        'MAX_MIN_LT',
        'MEAN_GT',
        'MEAN_LT',
      ];

      if (this.version !== 'GPU') {
        this.conditions.noValue.push('OVERFLOW');
      }

      this.conditions.options = this.conditions.noValue
          .concat(this.conditions.hasValue)
          .map((i) => {
            return {
              label: this.conditionMappings[i],
              value: i,
            };
          });
    },
    /**
     * collaspe btn click function
     */
    collapseBtnClick() {
      this.leftShow = !this.leftShow;
      setTimeout(() => {
        this.resizeCallback();
      }, 500);
    },
    /**
     * resieze Callback function
     */
    resizeCallback() {
      if (this.$refs.tensorValue) {
        this.debounce(this.$refs.tensorValue.resizeView(), 1000);
      }
    },
    /**
     * Anti-shake
     * @param { Function } fn callback function
     * @param { Number } delay delay time
     * @return { Function }
     */
    debounce(fn, delay) {
      let timer = null;
      return function() {
        if (timer) {
          clearTimeout(timer);
        }
        timer = setTimeout(fn, delay);
      };
    },
    /**
     * step input validation
     */
    stepChange() {
      if (this.step === '') {
        return;
      }
      this.step = this.step
          .toString()
          .replace(/[^\.\d]/g, '')
          .replace(/\./g, '');
      this.step = Number(this.step);
      if (this.step === 0) {
        this.step = 1;
      }
    },
    /**
     * Query current node info
     */
    getCurrentNodeInfo() {
      const params = {
        mode: 'node',
        params: {
          watch_point_id: this.curWatchPointId,
          name: this.nodeName,
          single_node: true,
          node_type: 'leaf',
        },
      };
      RequestService.retrieve(params).then(
          (res) => {
            if (res.data) {
              if (res.data.metadata) {
                this.dealMetadata(res.data.metadata);
              }
              if (res.data.graph) {
                const graph = res.data.graph;
                if (graph.children) {
                  this.dealTreeData(graph.children, this.nodeName);
                  this.defaultCheckedArr = this.$refs.tree.getCheckedKeys();
                }
                this.querySingleNode(
                    JSON.parse(JSON.stringify(res.data.graph)),
                    this.nodeName,
                    false,
                );
              }
              if (res.data.tensor_history) {
                this.tableData = res.data.tensor_history;
                this.dealTableData(this.tableData);
                this.tableData = JSON.parse(JSON.stringify(this.tableData));
              }
            }
          },
          (err) => {
            this.showErrorMsg(err);
          },
      );
    },
    /**
     * Query next node info
     */
    getNextNodeInfo() {
      this.watchPointHits = [];
      const params = {
        mode: 'continue',
        level: 'node',
        name: '',
      };
      RequestService.control(params).then(
          (res) => {},
          (err) => {
            this.showErrorMsg(err);
          },
      );
    },
    /**
     * In Ascend environment,query node info.
     * @param {Boolean} ascend previous or next
     */
    getNodeByBfs(ascend) {
      const data = this.$refs.tree.getCurrentNode();
      let name = this.$refs.tree.getCurrentKey();
      if (
        (data &&
          (data.type === 'name_scope' || data.type === 'aggregation_scope')) ||
        this.curLeafNodeName === null
      ) {
        name = this.curLeafNodeName;
      }
      const params = {ascend, name, watch_point_id: this.curWatchPointId};
      RequestService.retrieveNodeByBfs(params).then(
          (res) => {
            if (res.data && res.data.graph && res.data.name) {
              this.retrieveTensorHistory({name: res.data.name});
              const graph = res.data.graph;
              this.curLeafNodeName = res.data.name;
              this.nodeName = res.data.name;
              if (graph.children) {
                this.dealTreeData(graph.children, name);
                this.defaultCheckedArr = this.$refs.tree.getCheckedKeys();
              }
              this.querySingleNode(
                  JSON.parse(JSON.stringify(res.data.graph)),
                  res.data.name,
              );
            } else if (ascend) {
              this.$message.success(this.$t('debugger.nextNodeTip'));
            } else {
              this.$message.success(this.$t('debugger.previousNodeTip'));
            }
          },
          (err) => {
            this.showErrorMsg(err);
          },
      );
    },
    /**
     * Terminate current training
     */
    terminate() {
      this.$confirm(
          this.$t('debugger.ternimateConfirm'),
          this.$t('public.notice'),
          {
            confirmButtonText: this.$t('public.sure'),
            cancelButtonText: this.$t('public.cancel'),
            type: 'warning',
          },
      ).then(
          () => {
            this.control(2);
          },
          (err) => {
            this.showErrorMsg(err);
          },
      );
    },
    /**
     * Table row add className
     * @return { String }
     */
    tableRowClassName({row}) {
      if (row.is_hit) {
        return 'success-row';
      }
      return '';
    },
    /**
     * Table merged cells
     * @return { Object }
     */
    objectSpanMethod({row, column, rowIndex, columnIndex}) {
      if (columnIndex === 0 && this.outputLength > 0) {
        if (rowIndex === 0) {
          return {
            rowspan: this.outputLength,
            colspan: 1,
          };
        } else if (rowIndex > 0 && rowIndex < this.outputLength) {
          return {
            rowspan: 0,
            colspan: 0,
          };
        } else if (rowIndex === this.outputLength) {
          return {
            rowspan: this.inputLength,
            colspan: 1,
          };
        } else {
          return {
            rowspan: 0,
            colspan: 0,
          };
        }
      }
    },
    /**
     * Table header merged cells
     * @return { Object }
     */
    discountHeaderStyle({row, column, rowIndex, columnIndex}) {
      if (rowIndex == 1) {
        return {display: 'none'};
      }
    },
    /**
     * Handle node click
     * @param { Object } data node data
     */
    handleNodeClick(data) {
      this.isIntoView = false;
      this.selectedNode.name = data.name;
      if (this.treeFlag) {
        this.querySingleNode({}, data.name, true);
      } else {
        this.queryAllTreeData(data.name, true);
      }
    },
    /**
     * Query tensor value
     * @param { Object } data node info
     */
    retrieveTensorHistory(data) {
      const params = {
        name: data.name,
      };
      RequestService.retrieveTensorHistory(params).then(
          (res) => {
            if (res.data && res.data.metadata) {
              this.dealMetadata(res.data.metadata);
            }
            if (res.data && res.data.tensor_history) {
              this.tableData = res.data.tensor_history;
              this.dealTableData(this.tableData);
            } else {
              this.tableData = [];
            }
          },
          (err) => {
            this.showErrorMsg(err);
          },
      );
    },
    /**
     * Deal tensor history table data
     * @param {Array} arr tensor history data
     */
    dealTableData(arr) {
      const output = arr.filter((val) => val.type === 'output');
      const input = arr.filter((val) => val.type === 'input');
      this.outputLength = output.length;
      this.inputLength = input.length;
      arr.splice(0, arr.length, ...output.concat(input));
      arr.forEach((val) => {
        if (Array.isArray(val.shape)) {
          val.shape = `[${val.shape.toString()}]`;
        } else {
          if (val.shape !== undefined) {
            val.shape = val.shape + '';
          }
        }
        if (val.value === 'click to view') {
        } else {
          if (Array.isArray(val.value)) {
            val.value = `[${val.value.toString()}]`;
          } else {
            if (val.value !== undefined) {
              val.value = val.value + '';
            }
          }
        }
        if (val.dtype !== undefined) {
          val.dtype = val.dtype + '';
        }
      });
    },
    /**
     * Query tensor value or tensor comparison
     * @param {Object} data tensor value data
     */
    tensorFilterChange(data) {
      if (this.gridType === 'value') {
        this.viewValueDetail(this.curRowObj, `[${data.toString()}]`);
      } else {
        this.dims = `[${data.toString()}]`;
        this.tensorComparisons(this.curRowObj, `[${data.toString()}]`);
      }
    },
    /**
     * Query tensor value data
     * @param {Object} row current row data
     * @param { String } dims
     */
    viewValueDetail(row, dims) {
      const shape = dims
        ? dims
        : JSON.stringify(
            JSON.parse(row.shape)
                .map((val, index) => {
                  if (index < 2) {
                    return ':';
                  } else {
                    return 0;
                  }
                })
                .reverse(),
        ).replace(/"/g, '');
      this.dims = shape;
      const params = {name: row.name, detail: 'data', shape};
      const loadingInstance = this.$loading(this.loadingOption);
      RequestService.tensors(params).then(
          (res) => {
            this.gridType = 'value';
            loadingInstance.close();
            this.curRowObj = JSON.parse(JSON.stringify(row));
            this.tensorCompareFlag = true;
            if (res.data.tensor_value) {
              const value = res.data.tensor_value.value;
              if (value.includes('Too large to show')) {
                this.tensorValue = [];
                this.$nextTick(() => {
                  this.$refs.tensorValue.showRequestErrorMessage(
                      this.$t('debugger.largeDataTip'),
                      JSON.parse(row.shape),
                      shape,
                  );
                });
                return;
              }
              this.tensorValue = value instanceof Array ? value : [value];
              const status = res.data.tensor_value.statistics || {};
              this.$nextTick(() => {
                this.$refs.tensorValue.updateGridData(
                    this.tensorValue,
                    JSON.parse(row.shape),
                    status,
                    shape,
                );
              });
            }
          },
          (err) => {
            loadingInstance.close();
            this.showErrorMsg(err);
          },
      );
    },
    /**
     * Deal metadata
     * @param {Object} metadata metadata
     * @param {Boolean} isQuery wheather to query tree data
     */
    dealMetadata(metadata, isQuery = false) {
      this.metadata.pos = metadata.pos;
      if (metadata.state) {
        this.metadata.state = metadata.state;
      }
      if (metadata.node_name !== undefined && metadata.step !== undefined) {
        const nodeName = metadata.node_name;
        if (
          (nodeName !== this.nodeName && nodeName !== '') ||
          this.metadata.step !== metadata.step
        ) {
          this.nodeName = nodeName ? nodeName : this.nodeName;
          this.metadata.step = metadata.step;
          if (isQuery) {
            this.queryAllTreeData(
              nodeName ? nodeName : this.$refs.tree.getCurrentKey(),
              true,
            );
          }
        }
      }
      if (metadata.step && metadata.step > this.metadata.step) {
        this.metadata.step = metadata.step;
      }
    },
    /**
     * Long polling,update some info
     */
    pollData() {
      const params = {pos: this.metadata.pos};
      RequestService.pollData(params).then(
          (res) => {
            if (res.data) {
              if (res.data.metadata) {
                this.dealMetadata(res.data.metadata, true);
              }
              if (
                res.data.receive_tensor &&
              res.data.metadata &&
              res.data.metadata.step >= this.metadata.step &&
              res.data.receive_tensor.node_name ===
                this.$refs.tree.getCurrentKey()
              ) {
                this.retrieveTensorHistory({
                  name: res.data.receive_tensor.node_name,
                });
              }
              if (
                res.data.watch_point_hits &&
              res.data.watch_point_hits.length > 0
              ) {
                this.watchPointHits = res.data.watch_point_hits;
                this.watchPointHits.forEach((val) => {
                  val.selected = false;
                });
                this.radio1 = 'hit';
                this.$nextTick(() => {
                  this.updateTensorValue(0);
                });
              }
              if (
                res.data.tensor_history &&
              this.metadata.step <= res.data.metadata.step
              ) {
                setTimeout(() => {
                  const tableData = res.data.tensor_history;

                  if (this.tableData.length) {
                    this.tableData.forEach((val, key, arr) => {
                      tableData.forEach((value) => {
                        if (val.name === value.name) {
                          val.dtype = value.dtype;
                          val.shape = value.shape;
                          val.step = value.step;
                          val.value = value.value;
                        }
                      });
                    });
                  } else {
                    this.tableData = tableData;
                  }

                  this.dealTableData(this.tableData);
                  this.tableData = JSON.parse(JSON.stringify(this.tableData));
                }, 200);
              }
              this.pollData();
            }
          },
          (err) => {
            if (!err || (err && err.message !== 'routeJump')) {
              this.initFail = true;
              this.dialogVisible = true;
            }
          },
      );
    },
    /**
     * Step,continue,pause,terminate opesssrate
     * @param {Number} type
     */
    control(type) {
      this.watchPointHits = [];
      const params = {};
      if (type === 0) {
        if (!this.step) {
          return;
        }
        params.mode = 'continue';
        params.steps = parseInt(this.step);
      } else if (type === 1) {
        params.mode = 'continue';
        params.steps = -1;
      } else if (type === 2) {
        params.mode = 'terminate';
      } else if (type === 3) {
        params.mode = 'pause';
      }
      RequestService.control(params).then(
          (res) => {
            if (res.data && res.data.metadata) {
              const h = this.$createElement;
              this.$message({
                message: h('p', null, [
                  h('span', null, this.$t('debugger.backstageStatus')),
                  h('i', {style: 'color: teal'}, res.data.metadata.state),
                ]),
              });
              this.metadata.state = res.data.metadata.state;
            }
          },
          (err) => {
            this.showErrorMsg(err);
          },
      );
    },
    /**
     * show orginal tree
     */
    loadOriginalTree() {
      this.node.childNodes = [];
      this.curWatchPointId = null;
      this.defaultCheckedArr = [];
      this.resolve(this.origialTree);
    },
    /**
     * delete new watchpoint
     * @param {Object} item watchpoint data
     */
    deleteWatchpoint(item) {
      if (item.id) {
        this.$confirm(
            this.$t('debugger.deleteWatchpointConfirm'),
            this.$t('public.notice'),
            {
              confirmButtonText: this.$t('public.sure'),
              cancelButtonText: this.$t('public.cancel'),
              type: 'warning',
            },
        ).then(() => {
          const params = {watch_point_id: item.id};
          RequestService.deleteWatchpoint(params).then(
              (res) => {
                this.loadOriginalTree();
                this.queryWatchPoints();
                this.$message.success(this.$t('debugger.successDeleteWP'));
              },
              (err) => {
                this.showErrorMsg(err);
              },
          );
        });
      } else {
        this.curWatchPointId = null;
        this.watchPointPending = true;
        this.watchPointArr.pop();
      }
    },
    validateParam(item) {
      const reg = /^(\-|\+)?\d+(\.\d+)?$/;
      this.validPram = reg.test(item.param);
    },
    /**
     * Create new watchpoint
     * @param {Object} item watchpoint data
     */
    createWatchPoint(item) {
      if (item.condition) {
        if (item.pending) {
          const params = {
            condition: {
              condition: item.condition,
            },
            watch_nodes: this.$refs.tree.getCheckedKeys(),
          };
          if (this.conditions.hasValue.includes(item.condition)) {
            params.condition.param = parseFloat(item.param);
          }
          RequestService.createWatchpoint(params).then(
              (res) => {
                this.loadOriginalTree();
                this.queryWatchPoints();
                this.watchPointPending = true;
                this.$message.success(this.$t('debugger.successCreateWP'));
              },
              (err) => {
                this.loadOriginalTree();
                this.queryWatchPoints();
                this.watchPointPending = true;
                this.showErrorMsg(err);
              },
          );
        } else {
        }
      }
    },
    /**
     * Condition change processing
     * @param {Object} item
     */
    conditionChange(item) {
      item.label = this.conditionMappings[item.condition];
      if (this.conditions.noValue.includes(item.condition)) {
        item.param = '';
        this.validPram = false;
      }
    },
    /** Draw the tree
     * @param {Object} obj current checked obj
     */
    check(obj) {
      const node = this.$refs.tree.getNode(obj.name);
      const check = node.checked;
      if (this.treeFlag && node.childNodes) {
        this.dealCheckPro(node.childNodes, check);
      }
      if (this.curWatchPointId !== null && this.curWatchPointId !== '') {
        const checkedKeys = this.$refs.tree.getCheckedKeys();
        const watchNodes = [];
        if (this.defaultCheckedArr.length > checkedKeys.length) {
          watchNodes.push(obj.name);
        } else {
          checkedKeys.forEach((val) => {
            if (this.defaultCheckedArr.indexOf(val) === -1) {
              watchNodes.push(val);
            }
          });
        }
        const params = {
          watch_point_id: this.curWatchPointId,
          watch_nodes: watchNodes,
          mode: check ? 1 : 0,
        };
        if (this.searchWord !== '') {
          params.name = this.searchWord;
          params.watch_nodes = [obj.name];
          params.mode = check ? 1 : 0;
        }
        RequestService.updateWatchpoint(params).then(
            (res) => {
              this.defaultCheckedArr = checkedKeys;
            },
            (err) => {
              this.showErrorMsg(err);
            },
        );
      }
    },
    /** Deal tree data
     * @param {Object} childNodes tree node
     * @param { Boolean } check check status
     */
    dealCheckPro(childNodes, check) {
      childNodes.forEach((val) => {
        val.checked = check;
        if (val.childNodes) {
          this.dealCheckPro(val.childNodes, check);
        }
      });
    },
    /**
     * Add watchpoint
     */
    addWatchPoint() {
      this.searchWord = '';
      this.treeFlag = true;
      if (this.watchPointPending) {
        this.watchPointPending = false;
        this.loadOriginalTree();
        this.$refs.tree.getCheckedKeys().forEach((val) => {
          this.$refs.tree.setChecked(val, false);
        });
        this.defaultCheckedArr = [];
        this.watchPointArr.forEach((val) => {
          val.selected = false;
        });
        this.watchPointArr.push({
          selected: true,
          id: '',
          condition: '',
          label: '',
          param: '',
          pending: true,
        });
      }
      this.curWatchPointId = '';
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
     * Function to be executed after the search value changes
     */
    filterChange() {
      if (this.searchWord === '') {
        this.treeFlag = true;
        this.queryGraphByWatchpoint(this.curWatchPointId);
      }
    },
    /**
     * filter tree data by node name
     */
    filter() {
      if (this.searchWord) {
        const params = {
          name: this.searchWord,
          watch_point_id:
            this.curWatchPointId === '' ? null : this.curWatchPointId,
        };
        RequestService.search(params).then(
            (res) => {
              if (res.data && res.data.nodes) {
                this.treeFlag = false;
                this.searchTreeData = res.data.nodes;
                this.searchCheckedArr = [];
                this.dealSearchResult(this.searchTreeData);
                this.defaultCheckedArr = this.searchCheckedArr;
              }
            },
            (err) => {
              this.showErrorMsg(err);
            },
        );
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
        if (val.watched === 2) {
          this.searchCheckedArr.push(val.name);
        }
        val.label = val.name.split('/').pop();
      });
    },
    /**
     * Draw the tree
     * @param {Object} node tree root node
     * @param {Function} resolve callback function ,return next node data
     */
    loadNode(node, resolve) {
      if (node.level === 0) {
        const loadingInstance = this.$loading(this.loadingOption);
        node.childNodes = [];
        this.node = node;
        this.resolve = resolve;
        const params = {
          mode: 'all',
        };
        RequestService.retrieve(params).then(
            (res) => {
              loadingInstance.close();
              this.initFail = false;
              this.dialogVisible = false;
              if (res.data) {
                if (res.data.graph && res.data.graph.nodes) {
                  this.origialTree = res.data.graph.nodes.map((val) => {
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
                  resolve(this.origialTree);
                  this.$refs.tree.getCheckedKeys().forEach((val) => {
                    this.$refs.tree.setChecked(val, false);
                  });
                  if (this.treeFlag) {
                    this.dealGraphData(
                        JSON.parse(JSON.stringify(res.data.graph.nodes)),
                    );
                  }
                }
                if (res.data.watch_points) {
                  this.watchPointArr = res.data.watch_points.map((val) => {
                    return {
                      ...val,
                      selected: false,
                      condition: val.watch_condition.condition,
                      label: this.conditionMappings[
                          val.watch_condition.condition
                      ],
                      param: val.watch_condition.param || '',
                    };
                  });
                }
                if (res.data.metadata) {
                  this.metadata = res.data.metadata;
                  if (this.metadata.backend) {
                    this.version = this.metadata.backend;
                  }
                  this.initCondition();
                  this.nodeName = this.metadata.node_name;
                  if (this.pollInit) {
                    this.pollData();
                    this.pollInit = false;
                  }
                }
              }
            },
            (err) => {
              this.initFail = true;
              this.dialogVisible = true;
              loadingInstance.close();
            },
        );
      } else if (node.level >= 1) {
        this.isIntoView = false;
        const curHalfCheckedKeys = this.$refs.tree.getHalfCheckedKeys();
        const params = {
          mode: 'node',
          params: {
            node_type: node.data.type,
            watch_point_id: this.curWatchPointId,
            name: node.data.name,
          },
        };
        RequestService.retrieve(params).then(
            (res) => {
              if (res.data && res.data.metadata) {
                this.dealMetadata(res.data.metadata);
              }
              if (res.data && res.data.graph && res.data.graph.nodes) {
                this.curNodeData = res.data.graph.nodes.map((val) => {
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
                resolve(this.curNodeData);
                this.defaultCheckedArr = this.defaultCheckedArr.concat(
                    this.curNodeData
                        .filter((val) => {
                          return val.watched === 2;
                        })
                        .map((val) => val.name),
                );
                const halfSelectArr = this.curNodeData
                    .filter((val) => {
                      return val.watched === 1;
                    })
                    .map((val) => val.name);
                node.childNodes.forEach((val) => {
                  if (halfSelectArr.indexOf(val.data.name) !== -1) {
                    val.indeterminate = true;
                    node.indeterminate = true;
                    [
                      ...new Set(
                          curHalfCheckedKeys.concat(
                              this.$refs.tree.getHalfCheckedKeys(),
                          ),
                      ),
                    ].forEach((val) => {
                      this.$refs.tree.getNode(val).indeterminate = true;
                    });
                  }
                });
                this.selectedNode.name = node.data.name;
                if (!this.allGraphData[node.data.name].isUnfold) {
                  this.dealGraphData(
                      JSON.parse(JSON.stringify(res.data.graph.nodes)),
                      node.data.name,
                  );
                } else {
                  this.selectNode(true);
                }
              } else {
                this.selectedNode.name = node.data.name;
                this.selectNode(true);
                resolve([]);
              }
            },
            (err) => {
              this.showErrorMsg(err);
              resolve([]);
            },
        );
      }
    },
    /**
     * Show data of current selected watchpoint
     * @param {Number} key watchpoint id
     */
    selectWatchPoint(key) {
      if (!this.watchPointPending) {
        this.watchPointArr.pop();
        this.watchPointPending = true;
      }
      this.curLeafNodeName = null;
      this.curHalfCheckedKeys = [];
      this.watchPointArr.forEach((val, index) => {
        if (index === key) {
          if (val.id) {
            val.selected = true;
            this.curWatchPointId = val.id;
            if (this.searchWord === '') {
              this.queryGraphByWatchpoint(val.id);
            } else {
              this.filter();
            }
          } else {
            this.loadOriginalTree();
          }
        } else {
          if (val.selected) {
            val.selected = false;
          }
        }
      });
    },
    /**
     * Query graph data by watchpoint id
     * @param {Number} id wacthpoint id
     */
    queryGraphByWatchpoint(id) {
      const params = {
        mode: 'watchpoint',
        params: {watch_point_id: id},
      };
      RequestService.retrieve(params).then(
          (res) => {
            if (res.data && res.data.graph && res.data.graph.nodes) {
              this.curNodeData = res.data.graph.nodes.map((val) => {
                return {
                  label: val.name.split('/').pop(),
                  ...val,
                };
              });
              this.node.childNodes = [];
              this.curWatchPointId = id;
              this.resolve(this.curNodeData);
              this.$refs.tree.getCheckedKeys().forEach((val) => {
                this.$refs.tree.setChecked(val, false);
              });
              this.defaultCheckedArr = this.curNodeData
                  .filter((val) => {
                    return val.watched === 2;
                  })
                  .map((val) => val.name);
              const halfSelectArr = this.curNodeData
                  .filter((val) => {
                    return val.watched === 1;
                  })
                  .map((val) => val.name);
              this.node.childNodes.forEach((val) => {
                if (halfSelectArr.indexOf(val.data.name) !== -1) {
                  val.indeterminate = true;
                }
              });

              Object.keys(this.allGraphData).forEach((key) => {
                delete this.allGraphData[key];
              });
              d3.select('#graph svg').remove();
              this.selectedNode.name = '';
              this.dealGraphData(
                  JSON.parse(JSON.stringify(res.data.graph.nodes)),
              );
            }
          },
          (err) => {
            this.showErrorMsg(err);
          },
      );
    },
    /**
     * Query WatchPoints
     */
    queryWatchPoints() {
      const params = {
        mode: 'watchpoint',
      };
      RequestService.retrieve(params).then(
          (res) => {
            if (res.data.watch_points) {
              this.watchPointArr = res.data.watch_points.map((val) => {
                return {
                  ...val,
                  selected: false,
                  condition: val.watch_condition.condition,
                  label: this.conditionMappings[val.watch_condition.condition],
                  param: val.watch_condition.param,
                };
              });
            }
          },
          (err) => {
            this.showErrorMsg(err);
          },
      );
    },
    /**
     * Tree linkage with graph   Collapse of current node
     * @param {Obejct} name  The name of the current node
     */
    nodeCollapseLinkage(name) {
      const node = this.$refs.tree.getNode(name.replace('_unfold', ''));
      node.expanded = false;
      node.loaded = false;
      node.childNodes = [];
    },
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
        if (val.data.watched === 2) {
          val.checked = true;
        }
        if (val.data.watched === 1) {
          val.indeterminate = true;
        }
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
          const dom = document.querySelector(
              '.el-tree-node.is-current.is-focusable',
          );
          if (dom) {
            dom.scrollIntoView();
          }
        }, 800);
      });
    },
    /**
     * Query WatchpointHits
     */
    getWatchpointHits() {
      if (this.radio1 === 'hit') {
        const params = {
          mode: 'watchpoint_hit',
        };
        RequestService.retrieve(params).then(
            (res) => {
              if (res.data.metadata) {
                this.dealMetadata(res.data.metadata, false);
              }
              if (res.data && res.data.watch_point_hits) {
                this.watchPointHits = res.data.watch_point_hits;
                this.watchPointHits.forEach((val) => {
                  val.selected = false;
                });
                this.$nextTick(() => {
                  if (this.watchPointHits.length > 0) {
                    this.updateTensorValue(0);
                  }
                });
              }
            },
            (err) => {
              this.showErrorMsg(err);
            },
        );
      }
    },
    /**
     * Udpate TensrValue
     * @param {number} key The index of the node of the watchPointHits currently clicked
     */
    updateTensorValue(key) {
      const name = this.watchPointHits[key].node_name;
      const params = {
        mode: 'watchpoint_hit',
        params: {
          name,
          single_node: true,
          watch_point_id: this.curWatchPointId,
        },
      };
      this.watchPointHits.forEach((val, index) => {
        if (key === index) {
          val.selected = true;
        } else {
          val.selected = false;
        }
      });
      this.watchPointHits = JSON.parse(JSON.stringify(this.watchPointHits));
      requestService.retrieve(params).then(
          (res) => {
            if (res.data.metadata) {
              this.dealMetadata(res.data.metadata, false);
            }
            if (res.data && res.data.tensor_history) {
              this.tableData = res.data.tensor_history;
              this.dealTableData(this.tableData);
            }
            if (res.data && res.data.graph) {
              const graph = res.data.graph;
              if (graph.children) {
                this.dealTreeData(graph.children, name);
                this.defaultCheckedArr = this.$refs.tree.getCheckedKeys();
              }
              this.querySingleNode(
                  JSON.parse(JSON.stringify(res.data.graph)),
                  name,
                  false,
              );
            }
          },
          (err) => {
            this.showErrorMsg(err);
          },
      );
    },
    /**
     * Query the graph data
     * @param {String} nodeName The name of the node that needs to be query
     * @param {Boolean} isQueryTensor The name of the node that needs to be query
     */
    queryAllTreeData(nodeName, isQueryTensor) {
      const name = nodeName ? nodeName.split(':')[0] : '';
      const params = {
        mode: 'node',
        params: {
          name,
          single_node: true,
          watch_point_id: this.curWatchPointId,
        },
      };
      RequestService.retrieve(params).then(
          (res) => {
            if (res.data && res.data.metadata) {
              this.dealMetadata(res.data.metadata);
            }
            if (res.data && res.data.graph) {
              const graph = res.data.graph;
              if (graph.children) {
                this.dealTreeData(graph.children, name);
                this.defaultCheckedArr = this.$refs.tree.getCheckedKeys();
              }
              this.querySingleNode(
                  JSON.parse(JSON.stringify(res.data.graph)),
                  name,
                  isQueryTensor,
              );
            }
            if (res.data && res.data.tensor_history) {
              this.tableData = res.data.tensor_history;
              this.dealTableData(this.tableData);
            }
          },
          (err) => {
            this.showErrorMsg(err);
          },
      );
    },
    /**
     * Draw the tree
     * @param {Object} children child node
     * @param {String} name The name of the node that needs to be highlighted
     */
    dealTreeData(children, name) {
      if (children.nodes) {
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
          if (val.data.watched === 2) {
            val.checked = true;
          }
          if (val.data.watched === 1) {
            val.indeterminate = true;
          }
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
            const dom = document.querySelector(
                '.el-tree-node.is-current.is-focusable',
            );
            if (dom) {
              dom.scrollIntoView();
            }
          }, 800);
        });
      }
      if (children.children) {
        this.dealTreeData(children.children, name);
      }
    },
    /** ************************ graph **********************/
    /**
     * Initializing the graph
     * @param {String} dot dot statement encapsulated in graph data
     */
    initGraph(dot) {
      try {
        this.graphviz = d3
            .select('#graph')
            .graphviz({useWorker: false, totalMemory: this.totalMemory})
            .zoomScaleExtent(this.scaleRange)
            .dot(dot)
            .attributer(this.attributer)
            .render(() => {
              this.initSvg();
              this.afterInitGraph();
            });
      } catch (error) {
        const svg = document.querySelector('#graph svg');
        if (svg) {
          svg.remove();
        }
        this.initGraph(dot);
      }

      // Generate the dom of the submap.
      if (!d3.select('#graphTemp').size()) {
        d3.select('body').append('div').attr('id', 'graphTemp');
      }
      // Stores the dom of all the sorted subgraphs.
      if (!d3.select('#subgraphTemp').size()) {
        d3.select('body').append('div').attr('id', 'subgraphTemp');
      }
    },
    /**
     * Initialize svg
     */
    initSvg() {
      this.svg.dom = document.querySelector('#graph svg');
      this.svg.rect = this.svg.dom.getBoundingClientRect();
      const viewBoxData = this.svg.dom.getAttribute('viewBox').split(' ');
      this.viewBox.scale.x = 1;
      this.svg.originSize = {width: viewBoxData[2], height: viewBoxData[3]};
      if (viewBoxData[2] > this.viewBox.max) {
        this.viewBox.scale.x = viewBoxData[2] / this.viewBox.max;
        viewBoxData[2] = this.viewBox.max;
      }

      this.viewBox.scale.y = 1;
      if (viewBoxData[3] > this.viewBox.max) {
        this.viewBox.scale.y = viewBoxData[3] / this.viewBox.max;
        viewBoxData[3] = this.viewBox.max;
      }
      this.svg.dom.setAttribute('viewBox', viewBoxData.join(' '));
      this.svg.viewWidth = viewBoxData[2];
      this.svg.viewHeight = viewBoxData[3];
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
     * When the value of graph is too large, enlarge the value of graph.
     * Otherwise, the node cannot be clearly displayed.
     * @param {String} id Indicates the ID of the graph diagram.
     */
    fitGraph(id) {
      const graphContainer = document.getElementById(id);
      const maxShowWidth = graphContainer.offsetWidth * 1.5;
      const maxShowHeight = graphContainer.offsetHeight * 1.5;
      const graphDom = document.querySelector(`#${id} #graph0`);
      const box = graphDom.getBBox();
      let transformStr = '';
      const graphTransformData = this.getTransformData(graphDom);
      if (box.width > maxShowWidth || box.height > maxShowHeight) {
        const scale = Math.max(
            box.width / maxShowWidth / this.viewBox.scale.x,
            box.height / maxShowHeight / this.viewBox.scale.y,
        );
        const translate = {x: (box.width - maxShowWidth) / 2};

        if (!this.selectedNode.name) {
          graphTransformData.translate[0] = translate.x;
        }
        graphTransformData.scale[0] = scale;
      } else {
        graphTransformData.translate = [-box.x, -box.y];
      }
      if (id === 'graph' && this.selectedNode.more) {
        graphTransformData.scale[0] = this.graph.transform.k;
      }
      Object.keys(graphTransformData).forEach((key) => {
        transformStr += `${key}(${graphTransformData[key].join(',')}) `;
      });
      graphDom.setAttribute('transform', transformStr.trim());
    },
    /**
     * Initialization method executed after the graph rendering is complete
     */
    startApp() {
      const nodes = d3.selectAll('g.node, g.cluster');
      nodes.on(
          'click',
          (target, index, nodesList) => {
          // The target value of the element converted from the HTML attribute of the variable is null.
            const event = currentEvent;
            event.stopPropagation();
            event.preventDefault();

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
            this.selectNode(false, true);
            this.contextmenu.dom.style.display = 'none';
          },
          false,
      );
      // namespaces Expansion or Reduction
      nodes.on(
          'dblclick',
          (target, index, nodesList) => {
          // The target of the element converted from the HTML attribute of the variable is empty and
          // needs to be manually encapsulated.
            const event = currentEvent;
            event.stopPropagation();
            event.preventDefault();

            const clickNode = nodesList[index];
            const nodeId = clickNode.id;
            const nodeClass = clickNode.classList.value;
            let name = nodeId;
            this.selectedNode.more =
            name.indexOf('more...') !== -1 &&
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
              const changePage = name.includes('right') ? 1 : -1;
              const parentId = document.querySelector(`#graph g[id="${name}"]`)
                  .parentNode.id;
              name = parentId.replace('_unfold', '');
              this.allGraphData[name].index += changePage;
              this.allGraphData[name].index = Math.max(
                  0,
                  Math.min(
                      this.allGraphData[name].index,
                      this.allGraphData[name].childIdsList.length - 1,
                  ),
              );
              this.selectedNode.name = name;
            }
            if (unfoldFlag) {
              this.dealDoubleClick(name);
            } else if (this.clickScope.id) {
              this.selectedNode.name = this.clickScope.id;
            }
            this.nodeCollapseLinkage(this.selectedNode.name);
          },
          false,
      );
      this.initZooming();
      this.initContextMenu();

      if (this.selectedNode.name) {
        this.selectNode(true, true);
      }
    },
    /**
     * Initializing the graph zoom
     */
    initZooming() {
      const graphBox = this.graph.dom.getBBox();
      const padding = 4;
      const minDistance = 20;
      const pointer = {start: {x: 0, y: 0}, end: {x: 0, y: 0}};
      const zoom = d3
          .zoom()
          .on('start', () => {
            const event = currentEvent.sourceEvent;
            pointer.start.x = event.x;
            pointer.start.y = event.y;
            this.contextmenu.dom.style.display = 'none';
          })
          .on('zoom', () => {
            const event = currentEvent.sourceEvent;
            event.stopPropagation();
            event.preventDefault();

            const transformData = this.getTransformData(this.graph.dom);
            let tempStr = '';
            let change = {};
            let scale = transformData.scale[0];
            const graphRect = this.graph.dom.getBoundingClientRect();
            const transRate = graphBox.width / graphRect.width;
            if (event.type === 'mousemove') {
              pointer.end.x = event.x;
              pointer.end.y = event.y;
              let tempX = pointer.end.x - pointer.start.x;
              let tempY = pointer.end.y - pointer.start.y;
              const paddingTrans = Math.max(
                  (padding / transRate) * scale,
                  minDistance,
              );
              if (
                graphRect.left + paddingTrans + tempX >=
              this.svg.rect.left + this.svg.rect.width
              ) {
                tempX = Math.min(tempX, 0);
              }
              if (
                graphRect.left + graphRect.width - paddingTrans + tempX <=
              this.svg.rect.left
              ) {
                tempX = Math.max(tempX, 0);
              }
              if (
                graphRect.top + paddingTrans + tempY >=
              this.svg.rect.top + this.svg.rect.height
              ) {
                tempY = Math.min(tempY, 0);
              }
              if (
                graphRect.top + graphRect.height - paddingTrans + tempY <=
              this.svg.rect.top
              ) {
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
              scale =
              wheelDelta > 0
                ? transformData.scale[0] * rate
                : transformData.scale[0] / rate;

              scale = Math.max(this.scaleRange[0], scale, this.graph.minScale);
              scale = Math.min(this.scaleRange[1], scale);
              change = {
                x:
                (graphRect.x + padding / transRate - event.x) *
                transRate *
                (scale - transformData.scale[0]),
                y:
                (graphRect.bottom - padding / transRate - event.y) *
                transRate *
                (scale - transformData.scale[0]),
              };
            }

            this.graph.transform = {
              x: transformData.translate[0] + change.x,
              y: transformData.translate[1] + change.y,
              k: scale,
            };
            this.graph.transRate =
            graphRect.width / graphBox.width / this.graph.transform.k;

            tempStr =
            `translate(${this.graph.transform.x},${this.graph.transform.y}) ` +
            `scale(${this.graph.transform.k})`;
            this.graph.dom.setAttribute('transform', tempStr);
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
      };
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
     * Expand a namespace.
     * @param {String} name Nodes to be expanded or zoomed out
     * @param {Boolean} toUnfold Expand the namespace.
     */
    layoutNamescope(name, toUnfold) {
      this.$nextTick(() => {
        try {
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
        } catch (error) {
          const graphTempSvg = document.querySelector('#graphTemp svg');
          if (graphTempSvg) {
            graphTempSvg.remove();
          }
          const subGraphTempSvg = document.querySelector('#subgraphTemp svg');
          if (subGraphTempSvg) {
            subGraphTempSvg.remove();
          }

          this.dealDoubleClick(this.selectedNode.name);
        }
      });
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
          watch_point_id: this.curWatchPointId,
          name: name,
          node_type: type,
          single_node: false,
        };
      }
      RequestService.retrieve(params)
          .then(
              (response) => {
                if (
                  response &&
              response.data &&
              response.data.graph &&
              response.data.graph.nodes
                ) {
                  const nodes = JSON.parse(
                      JSON.stringify(response.data.graph.nodes),
                  );
                  if (this.treeFlag) {
                    this.nodeExpandLinkage(nodes, name);
                  }

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
     * @param {Object} nodes nodes data
     * @param {String} name node name
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
     * Process the data returned by the background interface.
     * @param {String} name Node name
     */
    dealAggregationNodes(name) {
      // A maximum of 10 subnodes can be displayed on an aggregation node.
      const aggregationNodeLimit = 10;
      const idsGroup = [];
      let maxChainNum = 1;

      this.allGraphData[name].children.forEach((key) => {
        const ids = this.getAssociatedNode(key, `${name}/`);
        if (ids.length) {
          idsGroup.push(ids);
        }
        const chainNum = this.dealChainingData(key, `${name}/`);
        maxChainNum = Math.max(...chainNum, maxChainNum);
      });

      const idsList = [];
      let temp = [];
      for (let i = 0; i < idsGroup.length; i++) {
        if (idsGroup[i].length > aggregationNodeLimit) {
          idsList.push(idsGroup[i]);
        } else {
          if (temp.length + idsGroup[i].length <= aggregationNodeLimit) {
            temp = temp.concat(idsGroup[i]);
          } else {
            if (temp.length) {
              idsList.push(temp);
              temp = [].concat(idsGroup[i]);
            }
          }
        }
        if (i === idsGroup.length - 1 && temp.length) {
          idsList.push(temp);
        }
      }

      this.allGraphData[name].childIdsList = idsList;
      this.allGraphData[name].index = 0;
      this.allGraphData[name].maxChainNum = maxChainNum;
    },
    /**
     * Process chaining data
     * @param {String} name nodes name
     * @param {String} prefix node prefix
     * @return {Number}
     */
    dealChainingData(name, prefix) {
      const node = this.allGraphData[name];
      if (!node.chained) {
        node.chained = true;
        let temp = [];
        Object.keys(node.input).forEach((key) => {
          if (key.includes(prefix)) {
            temp = temp.concat(this.dealChainingData(key, prefix));
          }
        });

        if (temp.length) {
          node.chainNum = [...new Set(temp.map((i) => i + 1))];
        }
      }
      return node.chainNum;
    },
    /**
     * Get associated node
     * @param {String} name nodes name
     * @param {String} prefix node prefix
     * @return {Number}
     */
    getAssociatedNode(name, prefix) {
      const node = this.allGraphData[name];
      let ids = [];

      if (!node.grouped) {
        node.grouped = true;
        ids.push(node.name);
        Object.keys(node.input).forEach((i) => {
          if (i.startsWith(prefix)) {
            if (!this.allGraphData[i].grouped) {
              const idsTemp = this.getAssociatedNode(i, prefix);
              ids = ids.concat(idsTemp);
            }
          }
        });
        Object.keys(node.output).forEach((i) => {
          if (i.startsWith(prefix)) {
            if (!this.allGraphData[i].grouped) {
              const idsTemp = this.getAssociatedNode(i, prefix);
              ids = ids.concat(idsTemp);
            }
          }
        });
      }

      return ids;
    },
    /**
     * Obtains the subnode data of the namespace through the namespace name.
     * @param {String} name Namespace name.
     * @return {Array} Subnode array of the namespace.
     */
    getChildNodesByName(name) {
      let nodes = [];
      if (name) {
        const node = this.allGraphData[name];
        const nameList =
          node.type === 'aggregation_scope'
            ? node.childIdsList[node.index]
            : node.children;

        nodes = nameList.map((i) => {
          return this.allGraphData[i];
        });

        if (node.type === 'aggregation_scope') {
          const idsList = node.childIdsList;

          if (idsList && idsList.length > 1) {
            if (node.index > 0) {
              let ellipsisNodesNumLeft = 0;
              for (let j = 0; j < node.index; j++) {
                ellipsisNodesNumLeft += idsList[j].length;
              }

              const ellipsisNodeL = {
                name: `${name}/left/${ellipsisNodesNumLeft} more...`,
                attr: {},
                input: {},
                output: {},
                proxy_input: {},
                proxy_output: {},
                type: '',
              };
              this.allGraphData[ellipsisNodeL.name] = ellipsisNodeL;
              nodes.unshift(ellipsisNodeL);
            }

            if (node.index < idsList.length - 1) {
              let ellipsisNodesNumRight = 0;
              for (let j = node.index + 1; j < idsList.length; j++) {
                ellipsisNodesNumRight += idsList[j].length;
              }

              const ellipsisNodeR = {
                name: `${name}/right/${ellipsisNodesNumRight} more...`,
                attr: {},
                input: {},
                output: {},
                proxy_input: {},
                proxy_output: {},
                type: '',
              };
              this.allGraphData[ellipsisNodeR.name] = ellipsisNodeR;
              nodes.push(ellipsisNodeR);
            }
          }
        }
      } else {
        nodes = this.firstFloorNodes.map((i) => {
          return this.allGraphData[i];
        });
      }

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
     * Encapsulates graph data into dot data.
     * @return {String} dot string for packing graph data
     */
    packageGraphData() {
      const nodes = this.getChildNodesByName();
      const initSetting =
        'node[style="filled";fontsize="10px"];edge[fontsize="5px";];';
      return `digraph {${initSetting}${this.packageNodes(
          nodes,
      )}${this.packageEdges(nodes)}}`;
    },
    /**
     * Encapsulates node data into dot data.
     * @param {Array} nodes Nodes of the node to be expanded.
     * @param {String} name Name of the node to be expanded.
     * @return {String} dot String that are packed into all nodes
     */
    packageNodes(nodes, name) {
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
                ? `shape="polygon";width=${node.size[0]};` +
                  `height=${node.size[1]};fixedsize=true;`
                : 'shape="octagon";'
            }];`;
        } else if (node.type === 'name_scope') {
          const fillColor = CommonProperty.graphColorArrPhg[this.curColorIndex];
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
            `label="${name}"];`;
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
     * @param {Array} nodes Nodes of the node to be expanded.
     * @param {String} name Name of the node to be expanded.
     * @return {String} dot string packaged by all edges
     */
    packageEdges(nodes, name) {
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
            if (input[key] && !input[key].independent_layout) {
              // Cannot connect to the sub-nodes in the aggregation node and cannot be directly connected to the
              // aggregation node. It can only connect to the outer namespace of the aggregation node.
              // If there is no namespace in the outer layer, you do not need to connect cables.
              // Other connections are normal.
              const source =
                this.findChildNamescope(key, name) ||
                (key ? analogNodesInputId : '');
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
          if (edge.shape.length > 1) {
            label = `tuple(${edge.shape.length} items)`;
          } else {
            const shape = edge.shape[0];
            if (shape && shape.length) {
              const flag = shape.some((i) => {
                return typeof i !== 'number';
              });
              if (flag) {
                label = `tuple(${shape.length} items)`;
              } else {
                label = `${edge.data_type} ${shape.join('×')}`;
              }
            } else if (edge.data_type) {
              label = `${edge.data_type}`;
            }
          }
        } else if (edge.data_type) {
          label = `${edge.data_type}`;
        }
      } else {
        label = `${edge.count}tensors`;
      }
      return label;
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
        fillColor = CommonProperty.graphColorArrPhg[curColorIndex];
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

      boxTemp = d3.select(`${idStr}g[id="${name}_unfold"]`).node().getBBox();
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
        const translateStr = `translate(${box.x - boxTemp.x},${
          box.y - boxTemp.y
        })`;
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
            const translateStr = `translate(${box.x - boxTemp.x},${
              box.y - boxTemp.y
            })`;
            nodeTemp.setAttribute('transform', translateStr);
            node.parentNode.appendChild(nodeTemp);
            node.remove();
          }
          const svg = document.querySelector('#graphTemp svg');
          if (svg) {
            svg.remove();
          }
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
      const nodes = this.getChildNodesByName(name);
      const nodeStr = this.packageNodes(nodes, name);
      const edgeStr = this.packageEdges(nodes, name);
      const initSetting =
        `node[style="filled";fontsize="10px";];` + `edge[fontsize="5px";];`;
      const dotStr =
        `digraph {${initSetting}label="${name.split('/').pop()}";` +
        `${nodeStr}${edgeStr}}`;
      return dotStr;
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
          .attr('class', 'edge');
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
          .attr('font-size', '5px')
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
        return {};
      }
      const transformData = node.getAttribute('transform');
      const attrObj = {};
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
              this.retrieveTensorHistory({
                name: path[0].replace('_unfold', ''),
              });
            }, 500);
          }
          if (ignoreType.includes(type)) {
            this.tableData = [];
          }
        }
      }
    },
    /**
     * Highlight proxy nodes
     * @param {String} nodeId node id
     */
    highlightProxyNodes(nodeId) {
      const proxyNodes = d3
          .selectAll('#graph g.node')
          .nodes()
          .filter((node) => {
            const id = node.id.split('^')[0].replace('_unfold', '');
            return id === nodeId;
          });
      const childTagType = ['polygon', 'ellipse', 'path', 'rect'];
      proxyNodes.forEach((i) => {
        if (i.childNodes) {
          i.childNodes.forEach((k) => {
            if (childTagType.includes(k.tagName)) {
              k.setAttribute('class', 'selected');
            }
          });
        }
      });
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
      if (name && !node.independent_layout) {
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
          subPsth = subPsth.split('/').slice(0, -1).join('/');
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
            node.grouped = false;
            node.chained = false;
            node.chainNum = [1];
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
     * Queries the first layer namespace to be expanded for a search node.
     * @param {Object} data All data of the node and the namespace to which the node belongs
     * @return {Object} First namespace to be expanded
     */
    findStartUnfoldNode(data) {
      if (data && data.scope_name) {
        if (this.allGraphData[data.scope_name].isUnfold) {
          if (
            data.nodes.some((node) => {
              return node.name === this.selectedNode.name;
            })
          ) {
            return data;
          } else {
            return this.findStartUnfoldNode(data.children);
          }
        } else {
          return data;
        }
      } else {
        return null;
      }
    },
    /**
     * Show error message
     * @param {Object} error error data
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
  },
  destroyed() {
    window.removeEventListener('resize', this.resizeCallback);
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
        height: calc(100% - 50px);
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
          height: calc(60% - 180px);
          overflow-y: auto;
          padding: 0 15px 15px;
          position: relative;
          z-index: 2;
          .el-tree {
            overflow-x: auto;
            overflow-y: hidden;
            & > .el-tree-node {
              min-width: 100%;
              display: inline-block;
            }
          }
        }
        .watch-point-wrap {
          height: 40%;
          border-top: 1px solid #ebeef5;
          border-bottom: 1px solid #ebeef5;
          .title-wrap {
            height: 30px;
            line-height: 30px;
            padding: 0 20px;
            position: relative;
            border-bottom: 1px solid #ebeef5;
            font-weight: bold;
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
                    width: 320px;
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
                    top: 0;
                  }
                }
                .condition {
                  margin: 10px 0;
                  .el-select {
                    width: 150px;
                  }
                  .condition-param {
                    width: 120px;
                    margin-left: 10px;
                  }
                  .btn-wrap {
                    display: inline-block;
                    margin-left: 10px;
                    padding: 0;
                  }
                }
              }
            }
          }
        }
        .btn-wrap {
          padding: 10px 20px 0;
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
        .custom-tree-node {
          padding-right: 8px;
        }
        .custom-tree-node.highlight {
          color: red;
        }
      }
      .hit {
        height: 100%;
        .content {
          height: calc(100% - 185px);
          padding-left: 15px;
        }
        .title {
          margin: 10px 0 30px;
        }
        .hit-list-wrap {
          height: calc(100% - 50px);
          overflow-y: auto;
          .hit-list {
            margin-bottom: 10px;
            border-bottom: 1px solid #ebeef5;
            .node-name {
              padding-left: 10px;
              line-height: 20px;
              &:hover {
                color: #00a5a7;
                cursor: pointer;
              }
            }
            .node-name.selected {
              color: #00a5a7;
            }
            .watch-points {
              padding-left: 20px;
              margin: 5px 0;
            }
          }
          .no-data {
            text-align: center;
            color: #909399;
          }
        }
        .btn-wrap {
          padding: 10px 20px 0;
          .step {
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            .custom-btn {
              margin-left: 10px;
            }
          }
          .el-button + .el-button {
            margin-bottom: 10px;
            margin-left: 0px;
          }
          .el-button:not(:last-child) {
            margin-right: 10px;
          }
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
                background-color: rgb(167, 167, 167);
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
      padding-left: 15px;
      position: relative;
      img {
        position: absolute;
        right: 10px;
        top: 20px;
        cursor: pointer;
        z-index: 99;
      }
      .table-title {
        height: 50px;
        line-height: 30px;
        padding: 10px 0;
        font-weight: bold;
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
        height: calc(100% - 50px);
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
        height: calc(100% - 50px);
      }
    }
  }
}
#graphTemp,
#subgraphTemp {
  position: absolute;
  bottom: 0;
  visibility: hidden;
}
</style>

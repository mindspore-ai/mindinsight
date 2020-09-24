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
                    <i class="el-icon-check"
                       v-if="item.selected && watchPointPending"
                       @click.stop="showOrigin()"></i>
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
import {select, selectAll, zoom, dispatch} from 'd3';
import 'd3-graphviz';
import debuggerGridTable from '../../components/debuggerGridTableSimple.vue';
const d3 = {select, selectAll, zoom, dispatch};
import RequestService from '@/services/request-service';
import commonGraph from '../../mixins/commonGraph.vue';
import debuggerMixin from '../../mixins/debuggerMixin.vue';

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
        text: this.$t('public.dataLoading'),
        spinner: 'el-icon-loading',
        background: 'rgba(0, 0, 0, 0.3)',
      },
      outputLength: 0,
      inputLength: 0,
      curLeafNodeName: null,

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
     * Query graph data by watchpoint id
     * @param {Number} id Wacthpoint id
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
              this.retrieveTensorHistory({
                name: path[0].replace('_unfold', ''),
              });
            }, 500);
          }
          if (ignoreType.includes(type)) {
            this.tableData = [];
          } else {
            this.nodeName = this.selectedNode.name;
          }
        }
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
                  .el-icon-check {
                    position: absolute;
                    right: 40px;
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
  .notShow {
    display: none;
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

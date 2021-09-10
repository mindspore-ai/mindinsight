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
  <div class="deb-wrap">
    <div class="left-wrap"
         :class="{collapse:leftShow}">
      <div class="left"
           v-show="!leftShow">
        <div class="header">
          {{radio1==='tree' ? $t('debugger.nodeList') : (
            radio1==='stack' ? $t('debugger.stackList') :
          ($t('debugger.curHitNode') + '(' + pagination.total + ')'))}}
          <div class="outdate-tip"
               v-if="hitsOutdated && radio1==='hit'">
            <el-tooltip class="item"
                        effect="light"
                        :content="$t('debugger.outdateTip')"
                        placement="top">
              <i class="el-icon-warning"></i>
            </el-tooltip>
          </div>
          <div class="radio-tabs">
            <el-radio-group v-model="radio1"
                            size='mini'
                            @change="searchWatchpointHits(true)">
              <el-radio-button label="hit">
                <i class="el-icon-s-fold"></i>
              </el-radio-button>
              <el-radio-button label="tree">
                <i class="el-icon-s-grid"></i>
              </el-radio-button>
              <el-radio-button label="stack">
                <i class="el-icon-s-unfold"></i>
              </el-radio-button>
            </el-radio-group>
          </div>
        </div>
        <div class="content"
             v-show="radio1==='tree'">
          <div class="search-conditions"
               :class="collapseConditions ? 'collapse-top':''">
            <div class="condition-title">
              {{$t('debugger.searchConditions')}}
              <div class="img-btn"
                   :class="collapseConditions ? 'collapse':''"
                   @click="collapseConditions=!collapseConditions"></div>
            </div>
            <div class="condition-container"
                 v-show="!collapseConditions">
              <div class="node-type">
                <div class="label">{{ $t('debugger.logicCard') }}</div>
                <el-select v-model="logicCard.value"
                           @change="logicCardChange"
                           :disabled="!trainId">
                  <el-option v-for="item in logicCard.options"
                             :key="item"
                             :value="item">
                  </el-option>
                </el-select>
              </div>
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
                <div class="label">{{$t('debugger.nodeName')}}</div>
                <el-input :placeholder="$t('graph.inputNodeName')"
                          v-model="searchWord"
                          :title="searchWord"
                          class="input-with-select"
                          @input="filterChange"
                          @keyup.enter.native="filter"
                          @clear="filter"
                          clearable>
                </el-input>
              </div>
              <div class="select-wrap">
                <div class="label">{{$t('debugger.stackInfo')}}</div>
                <el-input :placeholder="$t('debugger.inputStack')"
                          v-model="searchStackContent"
                          :title="searchStackContent"
                          class="input-with-select"
                          @input="filterChange"
                          @keyup.enter.native="filter"
                          @clear="filter"
                          clearable>
                </el-input>
              </div>
            </div>
          </div>

          <div class="tree-wrap"
               :class="!collapseConditions ? 'collapse':''">
            <div class="select-all-files"
                 v-if="curWatchPointId && treeFlag">
              <el-button type="primary"
                         size="mini"
                         class="custom-btn"
                         :disabled="metadata.state === state.running || metadata.state === state.sending"
                         @click="selectAllFiles(true)">{{ $t('public.selectAll') }}</el-button>
              <el-button type="primary"
                         size="mini"
                         class="custom-btn"
                         :disabled="metadata.state === state.running || metadata.state === state.sending"
                         @click="selectAllFiles(false)">{{ $t('public.deselectAll') }}</el-button>
            </div>
            <tree v-show="treeFlag"
                  :props="props"
                  :load="loadNode"
                  @node-collapse="nodeCollapse"
                  @node-click="handleNodeClick"
                  node-key="name"
                  :expand-on-click-node="false"
                  :lazy="lazy"
                  :highlight-current="true"
                  ref="tree"
                  @check="check"
                  :show-checkbox="!!curWatchPointId"
                  :disabled="treeDisabled">
              <span class="custom-tree-node"
                    slot-scope="{ node ,data }">
                <span :class="{const:data.type==='Const' && curWatchPointId}">
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
                <span class="custom-tree-node"
                      :title="node.label">{{ node.label }}</span>
              </span>
            </tree>
            <tree v-show="!treeFlag"
                  :props="defaultProps"
                  :load="loadSearchNode"
                  :lazy="true"
                  node-key="name"
                  :expand-on-click-node="false"
                  @node-click="handleNodeClick"
                  :show-checkbox="!!curWatchPointId"
                  @check="searchCheck"
                  :disabled="treeDisabled"
                  ref="searchTree">
              <span class="custom-tree-node"
                    slot-scope="{ node ,data }">
                <span :class="{const:data.type==='Const' && curWatchPointId}">
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
                <span class="custom-tree-node"
                      :title="node.label">{{ node.label }}</span>
              </span>
            </tree>
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
                   :class="{disable: !(watchPointArr.length && metadata.state !== state.running &&
                   metadata.state !== state.sending)}"
                   @click="deleteWatchpoint()"></i>
              </div>
              <div class="add-wrap">
                <i class="el-icon-circle-plus"
                   :title="$t('debugger.createWP')"
                   :class="{disable: metadata.state === state.running || metadata.state === state.sending}"
                   @click="initCondition"></i>
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
                    <i class="el-icon-check icon"
                       v-if="item.selected"
                       @click.stop="showOrigin()"></i>
                    <i class="el-icon-close icon"
                       :class="{disabled:metadata.state === state.running ||
                        metadata.state === state.sending}"
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
          <div class="node-type">
            <div class="label">{{ $t('debugger.logicCard') }}</div>
            <el-select v-model="logicCard.value"
                       :disabled="!trainId || metadata.state === state.running || metadata.state === state.sending"
                       @change="logicCardChange();searchWatchpointHits(true,true);">
              <el-option v-for="item in logicCard.options"
                         :key="item"
                         :value="item">
              </el-option>
            </el-select>
          </div>
          <div class="node-type">
            <div class="label">{{ $t('debugger.graphFile') }}</div>
            <el-select v-model="hitWpCondition.graphFile"
                       :disabled="metadata.state === state.running || metadata.state === state.sending"
                       @change="searchWatchpointHits(true,true);">
              <el-option v-for="item in graphFiles.options"
                         :key="item"
                         :value="item">
              </el-option>
            </el-select>
          </div>
          <div class="node-type">
            <div class="label">{{ $t('debugger.watchPoint') }}</div>
            <el-select v-model="hitWpCondition.watchPoint"
                       :disabled="metadata.state === state.running || metadata.state === state.sending"
                       @change="searchWatchpointHits(true,true);">
              <el-option v-for="item in hitWatchPointArr"
                         :key="item.value"
                         :label="item.label"
                         :value="item.value">
              </el-option>
            </el-select>
          </div>
          <div class="hit-list-wrap">
            <el-table class="watchpoint-table"
                      :data="watchPointHits"
                      row-key="id"
                      :expand-row-keys="expandKeys">
              <el-table-column type="expand"
                               width="40">
                <template slot-scope="props">
                  <ul>
                    <li v-for="(i, index) in props.row.lists"
                        :key="index">{{i.name}}
                      <div v-for="(j, ind) in i.params"
                           :key="ind"
                           class="param">
                        <div class="tensor-icon"></div>
                        {{j.content}}
                      </div>
                      <div class="hit-tip"
                           v-if="i.tip">
                        <i class="el-icon-warning"></i>{{i.tip}}
                      </div>
                    </li>
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
            <el-pagination class="watchpoint-page"
                           small
                           @current-change="handleCurrentChange"
                           :current-page="pagination.currentPage"
                           :page-size="pagination.pageSize"
                           :pager-count="pagination.pageCount"
                           layout="prev, pager, next, jumper"
                           :total="pagination.total"
                           v-show="pagination.total">
            </el-pagination>
          </div>
        </div>
        <div class="content"
             v-show="radio1==='stack'">
          <div class="stack-search">
            <div class="label">{{$t('debugger.stackInfo')}}</div>
            <el-input :placeholder="$t('debugger.inputStack')"
                      v-model="stacks.searchContent"
                      :title="stacks.searchContent"
                      @keyup.enter.native="queryStacks"
                      clearable
                      @clear="stackPageChange(1)">
            </el-input>
          </div>

          <div class="hit-list-wrap">
            <el-table class="watchpoint-table"
                      :data="stacks.list">
              <el-table-column type="expand">
                <template slot-scope="props">
                  <ul class="stack-info">
                    <li v-for="i in props.row.items"
                        :key="i.line_no">
                      {{i.line_no}}: {{i.code_line}}
                      <el-button type="text"
                                 class="btn"
                                 @click="stackOperator(i)">{{$t('debugger.search')}}</el-button>
                    </li>
                  </ul>
                </template>
              </el-table-column>
              <el-table-column prop="file_path"
                               :label="$t('graph.name')">
              </el-table-column>
            </el-table>
            <el-pagination class="watchpoint-page"
                           small
                           @current-change="stackPageChange"
                           :current-page="stacks.currentPage"
                           :page-size="stacks.pageSize.size"
                           :pager-count="pagination.pageCount"
                           layout="prev, pager, next, jumper"
                           :total="stacks.total"
                           v-show="stacks.total">
            </el-pagination>
          </div>
        </div>
        <div class="btn-wrap">
          <div class="step">
            <el-tooltip class="item"
                        effect="light"
                        :content="$t('debugger.inputTip',{total_step_num:metadata.total_step_num})"
                        placement="top-start">
              <el-input v-model="step"
                        :placeholder="$t('debugger.inputStep')"
                        :disabled="metadata.step === metadata.total_step_num && !!trainId"
                        @input="stepChange"
                        @keyup.native.enter="control(0)">
              </el-input>
            </el-tooltip>
            <el-button type="primary"
                       size="mini"
                       class="custom-btn green"
                       :disabled="!(step && metadata.state === state.waiting)
                       || (metadata.step === metadata.total_step_num && !!trainId)"
                       @click="control(0)">{{ $t('public.sure') }}</el-button>
          </div>
          <div class="btn-two">
            <el-button size="mini"
                       class="custom-btn white"
                       :disabled="metadata.state !== state.waiting
                       || (metadata.step === metadata.total_step_num && !!trainId)"
                       @click="control(1)">{{$t('debugger.continue')}}</el-button>
            <el-button size="mini"
                       class="custom-btn white"
                       :disabled="metadata.state !== state.running"
                       @click="control(3)">{{$t('debugger.pause')}}</el-button>
            <el-button size="mini"
                       class="custom-btn white"
                       :disabled="metadata.state === state.pending || metadata.state === state.sending"
                       @click="terminate">{{$t('debugger.terminate')}}</el-button>
          </div>
        </div>
      </div>
      <div class="collapse-btn"
           :class="[leftShow?'collapse':'',`collapse-btn-${$store.state.themeIndex}`]"
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
          <i class="el-icon-edit"
             :class="{disabled:metadata.state === state.running || metadata.state === state.sending}"
             v-if="trainId && !isShowInp"
             :title="$t('debugger.inpStepTip',{total_step_num:metadata.total_step_num})"
             @click="editStep"></i>
          <el-tooltip class="item"
                      effect="light"
                      :content="$t('debugger.inputTip',{total_step_num:metadata.total_step_num})"
                      placement="top-start"
                      v-if="trainId && isShowInp">
            <el-input v-model="newStep"
                      type="text"
                      @input="newStepChange"></el-input>
          </el-tooltip>
          <i class="el-icon-check"
             v-if="trainId && isShowInp"
             @click="saveStepValue"></i>
          <i class="el-icon-close"
             v-if="trainId && isShowInp"
             @click="isShowInp=false"></i>
          <el-tooltip class="tooltip"
                      effect="light"
                      :content="$t('debugger.stepTip') + (trainId ? $t('debugger.stepTipOffline') : '')"
                      placement="top">
            <i class="el-icon-info"></i>
          </el-tooltip>
        </span>

        <span class="item">{{$t('debugger.state') + $t('symbols.colon')}}
          <span class="content">
            <i class="el-icon-loading"
               v-show="metadata.state === state.running"></i>
            <i class="el-icon-time"
               v-show="metadata.state === state.sending"></i>
            {{ metadata.state ? $t('debugger.stateTips.' + metadata.state) : ''}}
          </span>
          <el-tooltip class="tooltip"
                      effect="light"
                      placement="right">
            <div slot="content">
              <div class="tooltip-item">
                <div class="item">
                  <span>1.</span>
                  <span>{{$t('debugger.stateInfo.waiting')}}</span>
                </div>
                <div class="item">
                  <span>2.</span>
                  <span>{{$t('debugger.stateInfo.running')}}</span>
                </div>
                <div class="item">
                  <span>3.</span>
                  <span>{{$t('debugger.stateInfo.sending')}}</span>
                </div>
                <div class="item">
                  <span>4.</span>
                  <span>{{$t('debugger.stateInfo.pending')}}</span>
                </div>
              </div>
            </div>
            <i class="el-icon-info"></i>
          </el-tooltip>
        </span>
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
          <el-button v-if="version==='GPU' && !trainId"
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
          <el-button v-if="version==='GPU' && !trainId"
                     type="primary"
                     size="mini"
                     class="custom-btn white"
                     :disabled="metadata.state === state.running ||
                     metadata.state === state.sending"
                     :class="{disabled: metadata.state === state.running ||
                     metadata.state === state.sending}"
                     @click="getNextNodeInfo">
            {{ $t('debugger.nextNode')}}
          </el-button>
        </div>
        <!-- Legend -->
        <div class="legend">
          <div class="title">
            {{ $t('graph.legend') }}
            <img :src="require('@/assets/images/all-drop-down.png')"
                 v-show="!showLegend"
                 @click="showLegend = !showLegend"
                 alt="" />
            <img :src="require('@/assets/images/all-uptake.png')"
                 v-show="showLegend"
                 @click="showLegend = !showLegend"
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

        <el-tabs v-model="tabs.activeName"
                 @tab-click="tabsChange">
          <el-tab-pane name="tensor">
            <span slot="label">
              {{$t('debugger.tensorMsg')}}
              <el-tooltip class="item"
                          effect="dark"
                          :content="$t('public.dataLoading')"
                          placement="top"
                          v-if="tableData.length && tableData.find(val=>val.value===undefined)">
                <i class="el-icon-loading"></i>
              </el-tooltip>
            </span>
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
                              @click="queryAllTreeData(scope.row.name,false,scope.row.graph_name, true)">
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
                                   :disabled="metadata.state === state.running || metadata.state === state.sending"
                                   v-if="scope.row.value === 'click to view'"
                                   @click="showTensor(scope.row,'value')">
                          {{ $t('debugger.view') }}
                        </el-button>
                        <el-button v-else
                                   class="value-tip"
                                   size="mini"
                                   type="text"
                                   :disabled="metadata.state===state.running || metadata.state === state.sending"
                                   :title="isNaN(scope.row.value)?'':scope.row.value"
                                   @click="showTensor(scope.row,'value')">
                          {{ scope.row.value }}</el-button>
                        <el-button size="mini"
                                   type="text"
                                   :disabled="metadata.state === state.running || metadata.state === state.sending ||
                                   scope.row.value === 'null' || !scope.row.value || scope.row.oversized"
                                   @click="loadTensor(scope.row)">
                          {{ $t('graph.downloadPic') }}
                        </el-button>
                        <el-button size="mini"
                                   type="text"
                                   :disabled="metadata.state===state.running || metadata.state === state.sending ||
                                  !scope.row.has_prev_step || scope.row.tensor_status==='oversize'"
                                   @click="showTensor(scope.row,'compare')">
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
                              @click="queryAllTreeData(scope.row.name,false,scope.row.graph_name, true)">
                          {{ scope.row.name }}
                        </span>
                      </template>
                    </el-table-column>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane :label="$t('debugger.stackInfo')"
                       name="stack">
            <div class="table-content">
              <ul class="stack-content">
                <li class="stack-item"
                    v-show="nodeStackContent.length"
                    v-for="(item, index) in nodeStackContent"
                    :key="index">
                  {{item.file_path ? item.file_path + ':' + item.line_no : ''}}
                  <br v-if="item.file_path">
                  {{item.code_line}}
                  <div class="operator-btns">
                    <el-button type="text"
                               v-if="item.file_path"
                               @click="stackOperator(item)">{{$t('debugger.search')}}</el-button>
                  </div>
                </li>
                <div class="noData-text"
                     v-show="!nodeStackContent.length">
                  {{$t("public.noData")}}
                </div>
              </ul>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
    <div class="deb-con"
         v-if="tensorCompareFlag">
      <debugger-tensor :row="curRowObj"
                       :formateWatchpointParams="formateWatchpointParams"
                       ref="deb-tensor"
                       @close="closeTensor"></debugger-tensor>
    </div>
    <el-dialog :title="$t('debugger.createWP')"
               :visible.sync="createWPDialogVisible"
               :show-close="false"
               :close-on-click-modal="false"
               :modal-append-to-body="false"
               class="creat-watch-point-dialog"
               width="930px">

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
                       :value="i.id"
                       :class="{'deb-indent': i.id != 'tensor_condition_collection'}">
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
                       :value="i.name"
                       v-show="i.paran_type !== 'SUPPORT_PARAM'">
            </el-option>
          </el-select>

          <el-tooltip class="item"
                      effect="light"
                      :content="$t('debugger.paramValueTip', {value: (/^(\-|\+)?\d+(\.\d+)?$/).test(item.param.value) ?
                      Number(item.param.value) : ''})"
                      placement="top">
            <el-input v-model="item.param.value"
                      :placeholder="$t('scalar.placeHolderNumber')"
                      v-show="item.param.options.length &&
                                item.param.type !== 'BOOL'"
                      @input="validateParam(item)"
                      class="param-value"></el-input>
          </el-tooltip>

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
          <div class="percent-sign"
               v-show="percentParams.includes(item.param.name)">%</div>

          <div class="inclusive-param"
               v-if="item.compositeParams.selections.length">
            <div class="item"
                 v-for="(i, index) in item.compositeParams.selections"
                 :key="index">
              {{transCondition(i.name)}}

              <el-tooltip class="item"
                          effect="light"
                          :content="$t('debugger.paramValueTip', {value:
                          (/^(\-|\+)?\d+(\.\d+)?$/).test(item.compositeParams.selections[index].value) ?
                          Number(item.compositeParams.selections[index].value) : ''})"
                          placement="top">
                <el-input v-model="item.compositeParams.selections[index].value"
                          :placeholder="$t('scalar.placeHolderNumber')"
                          v-show="i.type !== 'BOOL'"
                          @input="validateParam(item)"
                          class="param-value"></el-input>
              </el-tooltip>

              <el-select v-model="i.value"
                         v-if="i.type === 'BOOL'"
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
        </div>
      </div>
      <span slot="footer"
            class="dialog-footer">
        <div class="error-msg"
             v-show="!validPram">
          <i class="el-icon-warning"></i>
          {{$t('public.notice') + $t('symbols.colon') + paramErrorMsg}}
        </div>
        <div class="error-msg"
             v-if="createWPDialogVisible && createWatchPointArr[0].condition.selectedId === 'operator_overflow'">
          <i class="el-icon-warning"></i>
          {{$t('public.notice') + $t('symbols.colon') + $t('debugger.paramErrorMsg.watchOverflow')}}
        </div>
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
      <span v-if="noOfflineGraph"
            class="dialog-content">{{ $t('debugger.noOfflineGraphData') }}</span>
      <span v-else-if="initFail"
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

    <el-dialog :title="$t('debugger.recommendTip')"
               :visible.sync="recommendWatchPointDialog"
               :show-close="false"
               :close-on-click-modal="false"
               :modal-append-to-body="false"
               class="pendingTips"
               width="420px">

      <span class="dialog-icon">
        <span class="el-icon-warning"></span>
      </span>
      <span class="dialog-content">{{ $t('debugger.recommendDetail') }}</span>

      <span slot="footer"
            class="dialog-footer">
        <el-button type="primary"
                   size="mini"
                   class="custom-btn green"
                   @click="initRecommendWatchPoints(true)">
          {{$t('debugger.use')}}
        </el-button>
        <el-button type="primary"
                   size="mini"
                   class="custom-btn"
                   @click="initRecommendWatchPoints(false)">
          {{ $t('debugger.notUse') }}
        </el-button>
      </span>

    </el-dialog>
    <el-dialog :title="$t('public.notice')"
               :visible.sync="conflictFlag"
               :show-close="false"
               :close-on-click-modal="false"
               :modal-append-to-body="false"
               class="pendingTips"
               width="420px">

      <span class="dialog-icon">
        <span class="el-icon-warning"></span>
      </span>
      <span class="dialog-content">
        {{ $t('debugger.versionConflictTip',{msv:debuggerVersion.ms,miv:debuggerVersion.mi}) }}
      </span>
      <span slot="footer"
            class="dialog-footer">
        <el-button type="primary"
                   size="mini"
                   class="custom-btn green"
                   @click="trainId?deleteSession():control(2)">{{$t('public.sure')}}</el-button>
      </span>
    </el-dialog>

  </div>
</template>
<script>
import {select, selectAll, zoom, dispatch} from 'd3';
import 'd3-graphviz';
const d3 = {select, selectAll, zoom, dispatch};
import RequestService from '@/services/request-service';
import commonGraph from '../../mixins/common-graph.vue';
import debuggerMixin from '../../mixins/debugger-mixin.vue';
import debuggerTensor from '@/components/debugger-tensor.vue';
import tree from '../../components/tree.vue';

export default {
  mixins: [commonGraph, debuggerMixin],
  data() {
    return {
      leftShow: false,
      showLegend: true,
      searchWord: '',
      searchedWord: '',
      searchStackContent: '',
      searchedStackContent: '',
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
      logicCard: {
        options: [],
        value: '',
      },
      devices: [],
      selectedNode: {},
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
      trainId: this.$route.query.dir,
      recommendWatchPointDialog: false,
      hitsOutdated: false,
      conflictFlag: false,
      debuggerVersion: {},
      checkboxStatus: {
        unchecked: 0,
        indeterminate: 1,
        checked: 2,
        noCheckbox: -1,
      },
      percentParams: ['zero_percentage_ge', 'range_percentage_lt', 'range_percentage_gt'],
      oldState: '',
      treeDisabled: false,
      pagination: {
        currentPage: 1,
        pageSize: 10,
        pageCount: 5,
        total: 0,
      },
      state: {
        running: 'running',
        pending: 'pending',
        mismatch: 'mismatch',
        sending: 'sending',
        waiting: 'waiting',
      },
      loadingInstance: null,
      paramErrorMsg: '',
      sessionId: this.$route.query.sessionId,
      isShowInp: false,
      newStep: '',
      nodeStackContent: [],
      collapseConditions: false,
      stacks: {
        list: [],
        total: 0,
        currentPage: 1,
        pageSize: {
          options: [10, 20, 50],
          size: 10,
        },
        searchContent: '',
      },
      noOfflineGraph: false,
      hitWpCondition: {
        graphFile: '',
        watchPoint: '',
      },
      hitWatchPointArr: [],
    };
  },
  components: {debuggerTensor, tree},
  mounted() {
    document.title = `${this.$t('debugger.debugger')}-MindInsight`;
    this.nodeTypes.label = this.$t('debugger.nodeType');
    this.pageKey = 'debugger';
    if (this.trainId) {
      document.title = `${this.trainId}-${this.$t('debugger.debugger')}-MindInsight`;
      this.retrieveAll();
      this.queryStacks();
    } else {
      this.getSession();
    }
    window.addEventListener('resize', this.initSvgSize, false);
  },
  watch: {
    'metadata.state': {
      handler(newValue, oldValue) {
        if (newValue === this.state.mismatch) {
          this.conflictFlag = true;
        } else {
          this.conflictFlag = false;
        }

        if (newValue === this.state.pending) {
          if (oldValue) {
            location.reload();
          } else {
            this.dialogVisible = true;
          }
        } else {
          this.dialogVisible = false;
        }
        if (newValue === this.state.running || newValue === this.state.sending) {
          this.treeDisabled = true;
        } else {
          this.treeDisabled = false;
        }
        if (newValue === this.state.sending && oldValue) {
          this.oldState = oldValue;
        }

        if (newValue === this.state.waiting) {
          if (this.oldState === this.state.pending || oldValue === this.state.pending) {
            this.retrieveAll();
          } else if (this.oldState === this.state.running || oldValue === this.state.running) {
            this.pagination.currentPage = 1;
            this.watchPointHits = [];
            this.pagination.total = 0;
            this.searchWatchpointHits(true);
          }
        }
      },
      deep: true,
    },
    'watchPointArr': {
      handler(newValue) {
        const hitArr = newValue.map((val) => {
          return {
            label: this.getWatchPointContent(val),
            value: val.id,
          };
        });
        if (hitArr.length > 1) {
          hitArr.unshift({
            label: this.$t('debugger.all'),
            value: this.$t('debugger.all'),
          });
        }
        this.hitWpCondition.watchPoint = hitArr.length > 0 ? hitArr[0].value : '';
        this.hitWatchPointArr = hitArr;
      },
    },
  },
  methods: {
    stackOperator(stack) {
      if (!stack || !stack.file_path || !(stack.line_no || stack.line_no === 0)) {
        return;
      }
      this.searchStackContent = `${stack.file_path}:${stack.line_no}`;
      this.radio1 = 'tree';
      this.filter();
    },
    showTensor(row, type) {
      this.curRowObj = JSON.parse(JSON.stringify(row));
      this.curRowObj.type = type;
      this.curRowObj.curFileName = this.graphFiles.value;
      this.curRowObj.step = this.metadata.step;
      this.curRowObj.rank_id = this.logicCard.value;
      this.curRowObj.sessionId = this.sessionId;
      this.tensorCompareFlag = true;
    },
    closeTensor(tensor, graphName) {
      this.tensorCompareFlag = false;
      if (tensor && graphName) {
        this.queryAllTreeData(tensor, true, graphName, true);
      }
    },
    logicCardChange() {
      this.graphFiles.options = JSON.parse(
          JSON.stringify(this.devices.find((val) => val.rank_id === this.logicCard.value).graph_names),
      );
      if (this.graphFiles.options.length > 1) {
        this.graphFiles.options.unshift(this.$t('debugger.all'));
      }
      this.graphFiles.value = this.graphFiles.options[0];
      const device = this.devices.find((val) => val.rank_id === this.logicCard.value);
      this.metadata.ip = device.server_ip;
      this.metadata.device_name = device.device_id;
      if (this.nodeTypes.value === 'all' && !this.searchWord && !this.searchStackContent) {
        this.queryGraphByFile();
      } else {
        this.filter();
      }
    },
    queryGraphByFile() {
      const params = {
        mode: 'node',
        params: {
          watch_point_id: this.curWatchPointId ? this.curWatchPointId : 0,
          graph_name: this.graphFiles.value,
          rank_id: this.logicCard.value,
        },
      };
      if (this.graphFiles.value === this.$t('debugger.all')) {
        delete params.params.graph_name;
      }
      RequestService.retrieve(params, this.sessionId).then(
          (res) => {
            if (res.data && res.data.metadata) {
              this.dealMetadata(res.data.metadata);
            }
            if (res.data && res.data.graph) {
              const graph = res.data.graph;
              this.origialTree = res.data.graph.nodes.map((val) => {
                return {
                  label: val.name.split('/').pop(),
                  leaf: val.type === 'name_scope' || val.type === 'aggregation_scope' ? false : true,
                  ...val,
                  showCheckbox: val.watched !== -1,
                };
              });
              this.node.childNodes = [];
              this.resolve(this.origialTree);
              // watched 0:unchecked  1:indeterminate 2:checked -1:no checkbox
              this.defaultCheckedArr = this.origialTree
                  .filter((val) => {
                    return val.watched === this.checkboxStatus.checked;
                  })
                  .map((val) => val.name);
              this.node.childNodes.forEach((val) => {
                if (val.data.watched === this.checkboxStatus.indeterminate) {
                  val.indeterminate = true;
                }
                if (val.data.watched === this.checkboxStatus.unchecked) {
                  val.checked = false;
                }
                if (val.data.watched === this.checkboxStatus.checked) {
                  val.checked = true;
                }
              });
              this.firstFloorNodes = [];
              this.allGraphData = {};
              d3.select('#graph svg').remove();
              this.selectedNode.name = '';
              this.dealGraphData(JSON.parse(JSON.stringify(graph.nodes)));
              this.tableData = [];
            }
          },
          (err) => {
            this.showErrorMsg(err);
            this.resolve([]);
          },
      );
      this.filter();
    },
    selectAllFiles(type) {
      if (!type && !this.$refs.tree.getCheckedKeys().length && !this.$refs.tree.getHalfCheckedKeys().length) {
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
        if (type) {
          val.data.watched = this.checkboxStatus.checked;
        } else {
          val.data.watched = this.checkboxStatus.unchecked;
        }
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
          rank_id: this.logicCard.value,
        };
        if (this.graphFiles.value === this.$t('debugger.all')) {
          delete params.graph_name;
        }
        RequestService.updateWatchpoint(params, this.sessionId).then(
            (res) => {
              this.defaultCheckedArr = this.$refs.tree.getCheckedKeys();
              if (res && res.data && res.data.metadata && res.data.metadata.enable_recheck !== undefined) {
                this.enableRecheck = res.data.metadata.enable_recheck;
              }
            },
            (err) => {
              this.showErrorMsg(err);
            },
        );
      }
    },
    nodeTypesChange() {
      if (this.nodeTypes.value === 'all' && !this.searchWord && !this.searchStackContent) {
        this.treeFlag = true;
        this.node.level = 0;
        this.queryGraphByFile();
      } else {
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
        params: {
          watch_point_id: id,
          graph_name: this.graphFiles.value,
          rank_id: this.logicCard.value,
        },
      };
      if (this.graphFiles.value === this.$t('debugger.all')) {
        delete params.params.graph_name;
      }
      RequestService.retrieve(params, this.sessionId).then(
          (res) => {
            if (res.data && res.data.graph) {
              const graph = res.data.graph;
              this.origialTree = graph.nodes.map((val) => {
                return {
                  label: val.name.split('/').pop(),
                  ...val,
                  showCheckbox: val.watched !== -1,
                };
              });
              this.node.childNodes = [];
              this.curWatchPointId = id;
              this.resolve(this.origialTree);
              this.$refs.tree.getCheckedKeys().forEach((val) => {
                this.$refs.tree.setChecked(val, false);
              });
              // watched 0:unchecked  1:indeterminate 2:checked -1:no checkbox
              this.defaultCheckedArr = this.origialTree
                  .filter((val) => {
                    return val.watched === this.checkboxStatus.checked;
                  })
                  .map((val) => val.name);
              const halfSelectArr = this.origialTree
                  .filter((val) => {
                    return val.watched === this.checkboxStatus.indeterminate;
                  })
                  .map((val) => val.name);
              this.node.childNodes.forEach((val) => {
                if (halfSelectArr.indexOf(val.data.name) !== -1) {
                  val.indeterminate = true;
                }
                if (val.data.watched === this.checkboxStatus.checked) {
                  val.checked = true;
                } else if (val.data.watched === this.checkboxStatus.unchecked) {
                  val.checked = false;
                }
              });
              this.tableData = [];
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

    /**
     * Get watchpoint messages
     * @param {Object} item Wacthpoint data
     * @return {String}
     */
    getWatchPointContent(item) {
      let param = '';
      if (item.params.length) {
        param = item.params
            .map((i) => {
              const name = this.transCondition(i.name);
              const symbol = this.percentParams.includes(i.name) ? '%' : '';
              return `${name} ${i.value + symbol}`;
            })
            .join(', ');
        param = `(${param})`;
      }

      return `${this.$t('debugger.watchPoint')} ${item.id}: ${this.transCondition(item.condition)} ${param}`;
    },
    formateWatchpointParams(params = []) {
      params.forEach((i) => {
        const symbol = this.percentParams.includes(i.name) ? '%' : '';
        let content = `${this.transCondition(i.name)}: ${this.$t('debugger.setValue')} ${i.value + symbol}`;
        content +=
          i.actual_value || i.actual_value === 0
            ? `, ${this.$t('debugger.actualValue')} ${i.actual_value + symbol}`
            : '';
        i.content = content;
      });
    },
    /** ************************ graph **********************/

    /**
     * Initialization method executed after the graph rendering is complete
     */
    startApp() {
      this.initSvgSize(true);
      this.graph.dom = document.querySelector(`#graph #graph0`);
      const graphBox = this.graph.dom.getBBox();
      this.graph.size = {width: graphBox.width, height: graphBox.height};
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

      this.graph.minScale = Math.min(
          this.svg.size.width / 2 / this.graph.size.width,
          this.svg.size.height / 2 / this.graph.size.height,
      );
      this.initZooming();
      this.initContextMenu();

      if (this.selectedNode.name) {
        this.selectNode(true, true);
      }
      this.$nextTick(() => {
        this.loadingInstance.close();
      });
    },
    /**
     * Initialize the right-click menu
     */
    initContextMenu() {
      this.contextmenu.dom = document.querySelector('#contextMenu');
      const svgDom = document.querySelector('#graph svg');
      const ignoreType = ['Parameter', 'Const', 'Depend', 'make_tuple', 'tuple_getitem', 'ControlDepend'];

      const dispatch = d3
          .dispatch('start', 'contextmenu')
          .on('start', (event) => {
            this.contextmenu.dom.style.display = 'none';
            this.contextmenu.point = {x: event.x, y: event.y};
          })
          .on('contextmenu', (target) => {
            if (this.metadata.state !== this.state.waiting) {
              return;
            }
            const svgRect = svgDom.getBoundingClientRect();
            this.contextmenu.dom.style.left = `${this.contextmenu.point.x - svgRect.x}px`;
            this.contextmenu.dom.style.top = `${this.contextmenu.point.y - svgRect.y}px`;
            this.contextmenu.dom.style.display = 'block';

            this.selectedNode.name = target.name;
            this.selectNode(false, true);
          });

      const nodes = d3.selectAll('g.node, g.cluster');
      nodes.on(
          'contextmenu',
          (target, index, nodesList) => {
            event.preventDefault();
            const node = this.allGraphData[nodesList[index].id.replace('_unfold', '')];
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
      this.pagination.currentPage = 1;
      this.watchPointHits = [];
      this.pagination.total = 0;
      const params = {
        mode: 'continue',
        level: 'node',
        name: this.selectedNode.name.replace('_unfold', ''),
        graph_name: this.graphFiles.value,
        rank_id: this.logicCard.value,
      };
      if (this.graphFiles.value === this.$t('debugger.all')) {
        delete params.graph_name;
      }
      RequestService.control(params, this.sessionId).then(
          (res) => {
            if (res && res.data && res.data.metadata && res.data.metadata.enable_recheck !== undefined) {
              this.enableRecheck = res.data.metadata.enable_recheck;
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
     * @param {Boolean} expanded The expanded state of the current node
     */
    dealDoubleClick(name, expanded = false) {
      name = name.replace('_unfold', '');
      if (!(name && this.allGraphData[name])) return;
      this.loadingInstance = this.$loading(this.loadingOption);
      this.$nextTick(() => {
        // Delay is required, otherwise loading cannot be displayed
        setTimeout(() => {
          if (this.allGraphData[name].isUnfold) {
            this.selectedNode.name = name;
            this.deleteNamespace(name);
          } else if (!expanded) {
            this.queryGraphData(name);
          } else {
            this.loadingInstance.close();
          }
        }, 200);
      });
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
     * To obtain graph data, initialize and expand the namespace or aggregate nodes.
     * @param {String} name Name of the current node.
     */
    queryGraphData(name) {
      const type = this.allGraphData[name] ? this.allGraphData[name].type : 'name_scope';
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
          rank_id: this.logicCard.value,
        };
        if (this.graphFiles.value === this.$t('debugger.all')) {
          delete params.params.graph_name;
        }
      }
      RequestService.retrieve(params, this.sessionId)
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
      const independentLayout = this.allGraphData[name] ? this.allGraphData[name].independent_layout : false;

      if (!independentLayout && nodes.length > nodesCountLimit) {
        this.$message.error(this.$t('graph.tooManyNodes'));
        this.packageDataToObject(name, false);
        this.loadingInstance.close();
      } else {
        if (nodes && nodes.length) {
          this.packageDataToObject(name, true, nodes);
          // If the name is empty, it indicates the outermost layer.
          if (!name) {
            this.initGraph();
          } else {
            if (this.allGraphData[name].type === 'aggregation_scope') {
              this.dealAggregationNodes(name);
              if (this.allGraphData[name].maxChainNum > this.maxChainNum) {
                this.$message.error(this.$t('graph.tooManyChain'));
                this.allGraphData[name].isUnfold = true;
                this.selectedNode.name = name;
                this.deleteNamespace(name);
                this.loadingInstance.close();
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
      d3.selectAll('.node polygon, .node ellipse, .node rect, .node path').classed('selected', false);
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

          d3.select(`#graph g[id="${id}"]`).select('polygon, rect, ellipse, path').classed('selected', true);

          this.highlightProxyNodes(id.replace('_unfold', ''));
          this.highLightEdges(node.data);

          this.$refs.tree.setCurrentKey(id.replace('_unfold', ''));
          if (this.isIntoView) {
            this.$nextTick(() => {
              setTimeout(() => {
                const dom = document.querySelector('.el-tree-node.is-current.is-focusable');
                if (dom) {
                  dom.scrollIntoView();
                }
              }, 800);
            });
          }
          this.isIntoView = true;
          const type = this.allGraphData[path[0].replace('_unfold', '')].type;
          const ignoreType = ['name_scope', 'aggregation_scope'];
          if (isQueryTensor && !this.selectedNode.name.includes('more...') && !ignoreType.includes(type)) {
            if (this.graph.timer) {
              clearTimeout(this.graph.timer);
            }
            this.graph.timer = setTimeout(() => {
              const name = path[0].replace('_unfold', '');
              if (this.graphFiles.value === this.$t('debugger.all')) {
                this.retrieveTensorHistory({name: name.replace(`${name.split('/')[0]}/`, '')}, name.split('/')[0]);
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
              this.nodeName = this.selectedNode.name.replace(`${this.selectedNode.name.split('/')[0]}/`, '');
            } else {
              this.nodeName = this.selectedNode.name;
            }
          }
        }
      }
      if (this.tabs.activeName === 'detail') {
        this.setSelectedNodeData(node.data);
      } else if (this.tabs.activeName === 'stack') {
        this.nodeStackContent = JSON.parse(JSON.stringify(node.data.stack_info || []));
      }

      if (this.watchPointHits.length && this.radio1 === 'hit' && this.isHitIntoView) {
        if (!this.focusWatchpointHit()) {
          this.searchWatchpointHits(true);
        }
      }
      this.isHitIntoView = true;
      this.loadingInstance.close();
    },
    /**
     * The node information of the selected node.
     * @param {Object} selectedNode Node data
     */
    setSelectedNodeData(selectedNode = {}) {
      const IOInfo = [];
      this.selectedNode.inputNum = 0;
      this.selectedNode.outputNum = 0;
      if (selectedNode.output) {
        Object.keys(selectedNode.output).forEach((key) => {
          let graphName = this.graphFiles.value;
          if (this.graphFiles.value === this.$t('debugger.all')) {
            graphName = key.split('/')[0];
            key = key.replace(`${graphName}/`, '');
          }
          const obj = {
            name: key,
            IOType: 'output',
            graph_name: graphName,
            rank_id: this.logicCard.value,
          };
          IOInfo.push(obj);
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
          const obj = {
            name: key,
            IOType: 'input',
            graph_name: graphName,
            rank_id: this.logicCard.value,
          };
          IOInfo.push(obj);
          this.selectedNode.inputNum++;
        });
      }
      this.selectedNode.IOInfo = IOInfo;
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
        x: nodeRect.left + nodeRect.width / 2 - (this.svg.size.left + this.svg.size.width / 2),
        y: nodeRect.top + nodeRect.height / 2 - (this.svg.size.top + this.svg.size.height / 2),
      };

      this.graph.transform.x -= screenChange.x * (this.graph.size.width / graphObj.initWidth);
      this.graph.transform.y -= screenChange.y * (this.graph.size.height / graphObj.initHeight);

      this.graph.dom.setAttribute(
          'transform',
          `translate(${this.graph.transform.x},` + `${this.graph.transform.y}) scale(${this.graph.transform.k})`,
      );

      const transitionTime = Math.min(Math.abs(screenChange.x) * 2, Math.abs(screenChange.y) * 2, needDelay ? 800 : 0);

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
      this.initGraph();
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
          this.loadingInstance.close();
        } else {
          const parentId = name.substring(0, name.lastIndexOf('/'));
          if (this.allGraphData[parentId] && this.allGraphData[parentId].isUnfold) {
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
        if (this.allGraphData[data.scope_name] && this.allGraphData[data.scope_name].isUnfold) {
          return this.dealAutoUnfoldNamescopesData(data.children);
        } else {
          // If the namespace is a namespace and the number of subnodes exceeds the upper limit,
          // an error is reported and the namespace is selected.
          if (this.allGraphData[data.scope_name].type === 'name_scope' && data.nodes.length > this.nodesCountLimit) {
            this.selectedNode.name = data.scope_name;
            this.querySingleNode(data, data.scope_name, true);
            this.selectNode(true, true);
            this.loadingInstance.close();
            this.$message.error(this.$t('graph.tooManyNodes'));
          } else {
            // Normal expansion
            const nodes = JSON.parse(JSON.stringify(data.nodes));
            this.packageDataToObject(data.scope_name, true, nodes);
            if (this.allGraphData[data.scope_name] && this.allGraphData[data.scope_name].type === 'aggregation_scope') {
              this.dealAggregationNodes(data.scope_name);
              const aggregationNode = this.allGraphData[data.scope_name];
              if (aggregationNode) {
                for (let i = 0; i < aggregationNode.childIdsList.length; i++) {
                  if (aggregationNode.childIdsList[i].includes(this.selectedNode.name)) {
                    aggregationNode.index = i;
                    break;
                  }
                }
              }
              if (this.allGraphData[data.scope_name].maxChainNum > this.maxChainNum) {
                this.selectedNode.name = data.scope_name;
                this.allGraphData[data.scope_name].isUnfold = false;
                this.deleteNamespace(data.scope_name);
                this.loadingInstance.close();
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
      if (this.loadingInstance) {
        this.loadingInstance.close();
      }
      if (error.code === 'ECONNABORTED' && /^timeout/.test(error.message)) {
        this.$message.error(this.$t('public.timeout'));
        return;
      }
      if (error && error.response && error.response.data && error.response.data.error_code) {
        if (this.$t('error')[`${error.response.data.error_code}`]) {
          this.$message.error(this.$t('error')[`${error.response.data.error_code}`]);
        } else {
          if (error.response.data.error_code === '5054B101') {
            // The error "The graph does not exist" should not display in front page;
            return;
          }
          this.$message.error(error.response.data.error_msg);
        }
      }
    },
    tabsChange() {
      const node = this.allGraphData[this.selectedNode.name];
      if (!node) return;
      if (this.tabs.activeName === 'detail') {
        this.setSelectedNodeData(node);
      } else if (this.tabs.activeName === 'stack') {
        this.nodeStackContent = JSON.parse(JSON.stringify(node.stack_info || []));
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
      this.initSvgSize();
    },
    initSvgSize(immediate = false) {
      const setData = () => {
        const svgRect = document.querySelector('#graph svg').getBoundingClientRect();
        this.svg.size = {
          width: svgRect.width,
          height: svgRect.height,
          left: svgRect.left,
          top: svgRect.top,
        };
        this.resizeTimer = null;
      };
      if (!immediate) {
        if (this.resizeTimer) clearTimeout(this.resizeTimer);
        this.resizeTimer = setTimeout(setData, this.resizeDelay);
      } else {
        setData();
      }
    },
  },
  destroyed() {
    window.removeEventListener('resize', this.initSvgSize);
  },
};
</script>
<style>
.deb-wrap {
  height: 100%;
  background-color: var(--bg-color);
  position: relative;
  overflow: hidden;
}
.deb-wrap > div {
  float: left;
  height: 100%;
}
.deb-wrap .left-wrap {
  width: 400px;
  padding-right: 25px;
  height: 100%;
  position: relative;
  transition: width 0.2s;
  -moz-transition: width 0.2s;
  /* Firefox 4 */
  -webkit-transition: width 0.2s;
  /* Safari and Chrome */
  -o-transition: width 0.2s;
  /* Opera */
}
.deb-wrap .left-wrap .left {
  height: 100%;
  border-right: 1px solid var(--table-border-color);
  box-shadow: 0 2px 2px rgba(0, 0, 0, 0.22);
}
.deb-wrap .left-wrap .left .header {
  padding: 15px;
  border-bottom: 1px solid var(--table-border-color);
  position: relative;
  font-weight: bold;
}
.deb-wrap .left-wrap .left .header .radio-tabs {
  position: absolute;
  right: 10px;
  top: 10px;
}
.deb-wrap .left-wrap .left .header .outdate-tip {
  display: inline-block;
  margin-left: 7px;
}
.deb-wrap .left-wrap .left .header .outdate-tip .el-icon-warning {
  color: #e6a23c;
  font-size: 16px;
  cursor: pointer;
}
.deb-wrap .left-wrap .left .content {
  height: calc(100% - 145px);
}
.deb-wrap .left-wrap .left .content .search-conditions {
  height: 245px;
  position: relative;
}
.deb-wrap .left-wrap .left .content .search-conditions.collapse-top {
  height: 30px;
}
.deb-wrap .left-wrap .left .content .search-conditions .condition-title {
  height: 30px;
  line-height: 30px;
  padding: 0 20px;
  position: relative;
  border-bottom: 1px solid var(--table-border-color);
  font-weight: bold;
}
.deb-wrap .left-wrap .left .content .search-conditions .condition-title .img-btn {
  height: 20px;
  width: 20px;
  background-image: url('../../assets/images/all-drop-down.png');
  background-repeat: no-repeat;
  background-position: center;
  float: right;
  margin-top: 5px;
  cursor: pointer;
}
.deb-wrap .left-wrap .left .content .search-conditions .condition-title .img-btn.collapse {
  transform: rotate(180deg);
}

.deb-wrap .left-wrap .left .content .search-conditions .condition-container {
  border-bottom: 1px solid var(--table-border-color);
}

.deb-wrap .left-wrap .left .content .node-type,
.stack-search {
  height: 40px;
  padding: 10px 15px 0 15px;
}

.deb-wrap .left-wrap .left .content .node-type .label,
.deb-wrap .left-wrap .left .content .stack-search .label {
  display: inline-block;
  width: 80px;
}
.deb-wrap .left-wrap .left .content .node-type .el-select,
.deb-wrap .left-wrap .left .content .stack-search .el-input {
  width: calc(100% - 80px);
}
.deb-wrap .left-wrap .left .content .node-type .el-input__inner {
  height: 32px !important;
}
.deb-wrap .left-wrap .left .content .search-conditions .select-wrap {
  padding: 10px 15px;
  font-size: 14px;
}
.deb-wrap .left-wrap .left .content .search-conditions .select-wrap .label {
  display: inline-block;
  width: 80px;
}
.deb-wrap .left-wrap .left .content .search-conditions .select-wrap .el-input {
  width: calc(100% - 80px);
}
.deb-wrap .left-wrap .left .content .search-conditions .select-wrap + .select-wrap {
  padding-top: 0px;
}
.deb-wrap .left-wrap .left .content .search-conditions .select-wrap .input-with-select .el-input-group__prepend {
  background-color: #fff;
}
.deb-wrap .left-wrap .left .content .search-conditions .select-wrap .el-input--suffix .el-input__inner {
  padding-left: 5px;
  padding-right: 30px;
  font-size: 12px;
}
.deb-wrap .left-wrap .left .content .tree-wrap {
  height: calc(70% - 30px);
  overflow-y: auto;
  padding: 10px 15px 15px;
  position: relative;
  z-index: 2;
}
.deb-wrap .left-wrap .left .content .tree-wrap.collapse {
  height: calc(70% - 245px);
}

.deb-wrap .left-wrap .left .content .tree-wrap .image-type {
  width: 20px;
  height: 10px;
  margin-right: 10px;
}
.deb-wrap .left-wrap .left .content .tree-wrap .el-tree > .el-tree-node {
  min-width: 100%;
  display: inline-block;
}
.deb-wrap .left-wrap .left .content .watch-point-wrap {
  height: 30%;
  border-top: 1px solid var(--table-border-color);
}
.deb-wrap .left-wrap .left .content .watch-point-wrap .title-wrap {
  height: 30px;
  line-height: 30px;
  padding: 0 20px;
  position: relative;
  border-bottom: 1px solid var(--table-border-color);
  font-weight: bold;
}
.deb-wrap .left-wrap .left .content .watch-point-wrap .check-wrap {
  position: absolute;
  right: 60px;
  top: 0px;
}
.deb-wrap .left-wrap .left .content .watch-point-wrap .check-wrap .el-icon-circle-check {
  color: var(--theme-color);
  cursor: pointer;
}
.deb-wrap .left-wrap .left .content .watch-point-wrap .check-wrap .disable:before {
  cursor: not-allowed;
  color: #adb0b8;
}
.deb-wrap .left-wrap .left .content .watch-point-wrap .delete-wrap {
  position: absolute;
  right: 35px;
  top: 0px;
}
.deb-wrap .left-wrap .left .content .watch-point-wrap .delete-wrap .el-icon-delete:before {
  color: var(--theme-color);
  cursor: pointer;
}
.deb-wrap .left-wrap .left .content .watch-point-wrap .delete-wrap .disable:before {
  cursor: not-allowed;
  color: #adb0b8;
}
.deb-wrap .left-wrap .left .content .watch-point-wrap .add-wrap {
  position: absolute;
  right: 10px;
  top: 0px;
}
.deb-wrap .left-wrap .left .content .watch-point-wrap .add-wrap .el-icon-circle-plus:before {
  color: var(--theme-color);
  cursor: pointer;
}
.deb-wrap .left-wrap .left .content .watch-point-wrap .add-wrap .disable:before {
  cursor: not-allowed;
  color: #adb0b8;
}
.deb-wrap .left-wrap .left .content .watch-point-wrap .content-wrap {
  padding-left: 20px;
  position: relative;
  height: calc(100% - 30px);
}
.deb-wrap .left-wrap .left .content .watch-point-wrap .content-wrap .list-wrap {
  max-height: 100%;
  overflow: auto;
  padding: 10px 0;
}
.deb-wrap .left-wrap .left .content .watch-point-wrap .content-wrap .list-wrap .list {
  margin-bottom: 10px;
}
.deb-wrap .left-wrap .left .content .watch-point-wrap .content-wrap .list-wrap .list .name .item-content {
  display: inline-block;
  width: 300px;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
}
.deb-wrap .left-wrap .left .content .watch-point-wrap .content-wrap .list-wrap .list .name:hover {
  cursor: pointer;
  color: var(--theme-color);
}
.deb-wrap .left-wrap .left .content .watch-point-wrap .content-wrap .list-wrap .list .name.selected {
  color: var(--theme-color);
  position: relative;
}
.deb-wrap .left-wrap .left .content .watch-point-wrap .content-wrap .list-wrap .list .name.selected .el-icon-close {
  right: 10px;
}
.deb-wrap
  .left-wrap
  .left
  .content
  .watch-point-wrap
  .content-wrap
  .list-wrap
  .list
  .name.selected
  .el-icon-close.disabled {
  cursor: not-allowed;
  color: #adb0b8;
}
.deb-wrap .left-wrap .left .content .watch-point-wrap .content-wrap .list-wrap .list .name.selected .el-icon-check {
  right: 30px;
}
.deb-wrap .left-wrap .left .content .watch-point-wrap .content-wrap .list-wrap .list .name.selected .icon {
  position: absolute;
  top: 3px;
  border: solid 1px;
  padding: 1px;
  border-radius: 2px;
  font-size: 12px;
}
.deb-wrap .left-wrap .left .content .custom-tree-node {
  padding-right: 8px;
}
.deb-wrap .left-wrap .left .content .custom-tree-node .const {
  margin-left: 22px;
}
.deb-wrap .left-wrap .left .content .custom-tree-node.highlight {
  color: red;
}
.deb-wrap .left-wrap .left .content .hit-list-wrap {
  height: calc(100% - 40px);
  padding: 10px;
}
.deb-wrap .left-wrap .left .content .hit-list-wrap .watchpoint-table {
  max-height: calc(100% - 135px);
  overflow: auto;
  margin-top: 10px;
}
.deb-wrap .left-wrap .left .content .hit-list-wrap .watchpoint-table .stack-info > li {
  padding: 5px 50px 5px 10px !important;
  position: relative;
}
.deb-wrap .left-wrap .left .content .hit-list-wrap .watchpoint-table .stack-info > li > .btn {
  padding: 0;
  position: absolute;
  right: 10px;
  top: calc(50% - 8px);
}
.deb-wrap .left-wrap .left .content .hit-list-wrap .el-table::before {
  height: 0;
}
.deb-wrap .left-wrap .left .content .hit-list-wrap .watchpoint-page {
  padding-top: 20px;
}
.deb-wrap .left-wrap .left .content .hit-list-wrap .hit-item {
  word-break: break-all;
  line-height: 18px;
  padding: 10px;
}
.deb-wrap .left-wrap .left .content .hit-list-wrap .hit-item:hover {
  cursor: pointer;
}
.deb-wrap .left-wrap .left .content .hit-list-wrap .selected {
  color: var(--theme-color);
}
.deb-wrap .left-wrap .left .content .hit-list-wrap .el-table__expanded-cell[class*='cell'] {
  padding: 0px 10px 0 50px;
}
.deb-wrap .left-wrap .left .content .hit-list-wrap .el-table__expanded-cell[class*='cell'] ul {
  background-color: var(--el-select-dropdown-item-hover-bg-color);
}
.deb-wrap .left-wrap .left .content .hit-list-wrap .el-table__expanded-cell[class*='cell'] ul li {
  line-height: 18px;
  padding: 10px;
  word-break: break-all;
  border-top: 1px solid var(--bg-color);
  border-bottom: 1px solid var(--bg-color);
}
.deb-wrap .left-wrap .left .content .hit-list-wrap .el-table__expanded-cell[class*='cell'] ul li:hover {
  background-color: var(--table-border-color);
}
.deb-wrap .left-wrap .left .content .hit-list-wrap .el-table__expanded-cell[class*='cell'] ul li .param .tensor-icon {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 3px;
  background-color: var(--theme-color);
  margin-top: 8px;
}
.deb-wrap .left-wrap .left .content .hit-list-wrap .el-table__expanded-cell[class*='cell'] ul li .hit-tip {
  margin-top: 10px;
  font-size: 12px;
}
.deb-wrap
  .left-wrap
  .left
  .content
  .hit-list-wrap
  .el-table__expanded-cell[class*='cell']
  ul
  li
  .hit-tip
  .el-icon-warning {
  font-size: 14px;
  color: #e6a23c;
  padding-right: 4px;
}
.deb-wrap .left-wrap .left .btn-wrap {
  padding: 10px 20px;
  border-top: 1px solid var(--table-border-color);
}
.deb-wrap .left-wrap .left .btn-wrap .step {
  width: 100%;
  display: flex;
  justify-content: space-between;
}
.deb-wrap .left-wrap .left .btn-wrap .step .custom-btn {
  margin-left: 10px;
}
.deb-wrap .left-wrap .left .btn-wrap .btn-two {
  width: 100%;
}
.deb-wrap .left-wrap .left .btn-wrap .btn-two .custom-btn {
  height: 30px;
  margin-top: 10px;
}
.deb-wrap .left-wrap .left .btn-wrap .el-button + .el-button {
  margin-left: 0px;
}
.deb-wrap .left-wrap .left .btn-wrap .el-button:not(:last-child) {
  margin-right: 10px;
}
.deb-wrap .left-wrap .collapse-btn {
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
}
.deb-wrap .left-wrap .collapse-btn-0 {
  background-image: url('../../assets/images/0/collapse-left.svg');
}
.deb-wrap .left-wrap .collapse-btn-1 {
  background-image: url('../../assets/images/1/collapse-left.svg');
}
.deb-wrap .left-wrap .collapse-btn-0.collapse {
  background-image: url('../../assets/images/0/collapse-right.svg');
}
.deb-wrap .left-wrap .collapse-btn-1.collapse {
  background-image: url('../../assets/images/1/collapse-right.svg');
}
.deb-wrap .left-wrap.collapse {
  width: 0px;
}
.deb-wrap .right {
  width: calc(100% - 400px);
  height: 100%;
  padding-right: 20px;
  transition: width 0.2s;
  -moz-transition: width 0.2s;
  /* Firefox 4 */
  -webkit-transition: width 0.2s;
  /* Safari and Chrome */
  -o-transition: width 0.2s;
  /* Opera */
}
.deb-wrap .right .header {
  line-height: 51px;
  border-bottom: 1px solid var(--table-border-color);
  position: relative;
}
.deb-wrap .right .header .link {
  color: var(--theme-color);
}
.deb-wrap .right .header .host {
  margin-left: 25px;
}
.deb-wrap .right .header .item + .item {
  margin-left: 15px;
}
.deb-wrap .right .header .el-icon-edit {
  margin-left: 5px;
}
.deb-wrap .right .header .el-icon-edit.disabled::before {
  cursor: not-allowed;
  color: #adb0b8;
}
.deb-wrap .right .header i {
  font-size: 18px;
  margin: 0 2px;
  color: #00a5a7;
  cursor: pointer;
}
.deb-wrap .right .header .el-icon-close {
  color: #f56c6c;
}
.deb-wrap .right .header .el-input {
  width: 45px;
}
.deb-wrap .right .header .el-input input {
  padding: 0;
  text-align: center;
}
.deb-wrap .right .header .tooltip {
  margin-left: 5px;
  cursor: pointer;
}
.tooltip-item .item {
  display: flex;
}
.tooltip-item .item :first-child {
  width: 20px;
  flex-shrink: 0;
}
.deb-wrap .right .svg-wrap {
  height: 50%;
  border-bottom: 1px solid var(--table-border-color);
  position: relative;
}
.deb-wrap .right .svg-wrap .legend {
  width: 400px;
  position: absolute;
  bottom: 0px;
  right: 0px;
  background-color: var(--graph-legend-bg-color);
  border: 1px solid var(--table-border-color);
}
.deb-wrap .right .svg-wrap .legend .title {
  padding: 10px 0 10px 10px;
  font-size: 14px;
}
.deb-wrap .right .svg-wrap .legend .title img {
  float: right;
  margin-right: 10px;
  cursor: pointer;
}
.deb-wrap .right .svg-wrap .legend .legend-content {
  padding: 0 10px;
  border: 1px solid var(--table-border-color);
}
.deb-wrap .right .svg-wrap .legend .legend-item {
  padding: 5px 0;
  display: inline-block;
  width: 50%;
  font-size: 14px;
  line-height: 20px;
}
.deb-wrap .right .svg-wrap .legend .legend-item .pic {
  width: 45px;
  text-align: center;
  display: inline-block;
  padding-left: 20px;
  vertical-align: middle;
}
.deb-wrap .right .svg-wrap .legend .legend-item .pic img {
  max-width: 45px;
  max-height: 15px;
  margin-left: -20px;
  vertical-align: middle;
}
.deb-wrap .right .svg-wrap .legend .legend-item .legend-text {
  display: inline-block;
  padding-left: 20px;
  width: calc(100% - 45px);
  vertical-align: middle;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.deb-wrap .right .svg-wrap .legend .legend-item .legend-text:hover {
  cursor: default;
}

.deb-wrap .right .svg-wrap .btn-wrap {
  position: absolute;
  top: 10px;
  right: 10px;
}
.deb-wrap .right .svg-wrap .graph-container {
  height: 100%;
  width: 100%;
  position: relative;
}
.deb-wrap .right .svg-wrap .graph-container #graph {
  height: 100%;
  background-color: var(--graph-bg-color);
}
.deb-wrap .right .svg-wrap .graph-container #graph .node:hover > path,
.deb-wrap .right .svg-wrap .graph-container #graph .node:hover > ellipse,
.deb-wrap .right .svg-wrap .graph-container #graph .node:hover > polygon,
.deb-wrap .right .svg-wrap .graph-container #graph .node:hover > rect {
  stroke-width: 2px;
}
.deb-wrap .right .svg-wrap .graph-container #graph .node.cluster > rect:hover {
  stroke: #8df1f2;
}
.deb-wrap .right .svg-wrap .graph-container #graph .selected {
  stroke: red !important;
  stroke-width: 2px;
}
.deb-wrap .right .svg-wrap .graph-container #graph #graph0 > polygon {
  fill: transparent;
}
.deb-wrap .right .svg-wrap .graph-container #graph .node {
  cursor: pointer;
}
.deb-wrap .right .svg-wrap .graph-container #graph .edge path {
  stroke: #787878;
}
.deb-wrap .right .svg-wrap .graph-container #graph .edge polygon {
  fill: #787878;
}
.deb-wrap .right .svg-wrap .graph-container #graph .edge.highlighted path {
  stroke: red;
}
.deb-wrap .right .svg-wrap .graph-container #graph .edge.highlighted polygon {
  stroke: red;
  fill: red;
}
.deb-wrap .right .svg-wrap .graph-container #graph .edge.highlighted marker path {
  fill: red;
}
.deb-wrap .right .svg-wrap .graph-container #graph .node.aggregation > polygon {
  stroke: #e3aa00;
  fill: var(--graph-aggregation-color);
}
.deb-wrap .right .svg-wrap .graph-container #graph .node.cluster.aggregation > rect {
  stroke: #e3aa00;
  stroke-dasharray: 3, 3;
}
.deb-wrap .right .svg-wrap .graph-container #graph .node > polygon {
  stroke: var(--theme-color);
  fill: var(--graph-polygon-color);
}
.deb-wrap .right .svg-wrap .graph-container #graph .node > ellipse {
  stroke: #4ea6e6;
  fill: var(--graph-operator-color);
}
.deb-wrap .right .svg-wrap .graph-container #graph .plain > path,
.deb-wrap .right .svg-wrap .graph-container #graph .plain ellipse {
  stroke: #e6a23c;
  fill: var(--graph-plain-color);
  stroke-dasharray: 1.5, 1.5;
}
.deb-wrap .right .svg-wrap .graph-container #graph .edge-point ellipse {
  stroke: #a7a7a7;
  fill: #a7a7a7;
}
.deb-wrap .right .svg-wrap .graph-container #graph text {
  fill: var(--font-color);
}
.deb-wrap .right .svg-wrap .graph-container #contextMenu {
  display: none;
  position: absolute;
  min-width: 150px;
  border: 1px solid #d4d4d4;
}
.deb-wrap .right .svg-wrap .graph-container #contextMenu ul {
  background-color: #e2e2e2;
  border-radius: 2px;
}
.deb-wrap .right .svg-wrap .graph-container #contextMenu ul li {
  padding: 5px 18px;
  cursor: pointer;
}
.deb-wrap .right .svg-wrap .graph-container #contextMenu ul li:hover {
  background-color: #787878;
  color: white;
}
.deb-wrap .right .table-container {
  height: calc(50% - 60px);
  position: relative;
}
.deb-wrap .right .table-container > img {
  position: absolute;
  right: 10px;
  top: 12px;
  cursor: pointer;
  z-index: 99;
}
.deb-wrap .right .table-container .el-tabs.el-tabs--top {
  height: 100%;
}
.deb-wrap .right .table-container .el-tabs.el-tabs--top .el-tabs__content {
  height: calc(100% - 60px);
}
.deb-wrap .right .table-container .el-tabs.el-tabs--top .el-tabs__content .el-tab-pane {
  height: 100%;
}
.deb-wrap .right .table-container .table-content {
  height: 100%;
  overflow: hidden;
  position: relative;
}
.deb-wrap .right .table-container .table-content .stack-content {
  background-color: var(--bg-color);
  height: 100%;
  overflow: auto;
}
.deb-wrap .right .table-container .table-content .stack-content .stack-item {
  line-height: 18px;
  padding: 5px 60px 5px 10px !important;
  position: relative;
  word-break: break-all;
  border-bottom: 1px solid var(--table-border-color);
}
.deb-wrap .right .table-container .table-content .stack-content .stack-item:hover {
  background-color: var(--table-hover-color);
}
.deb-wrap .right .table-container .table-content .stack-content .operator-btns {
  position: absolute;
  right: 10px;
  top: calc(50% - 20px);
}

.deb-wrap .right .table-container .table-content .stack-content .noData-text {
  text-align: center;
  line-height: 60px;
  color: #909399;
}
.deb-wrap .right .table-container .table-content .table-wrap {
  height: 100%;
  overflow-y: auto;
}
.deb-wrap .right .table-container .table-content .table-wrap .el-table .success-row {
  background: var(--table-success-row-bg-color);
}
.deb-wrap .right .table-container .table-content .value-wrap {
  text-align: right;
}
.deb-wrap .right .table-container .table-content .center {
  display: inline-block;
  text-align: center;
  width: 100%;
}
.deb-wrap .right .table-container .table-content .value {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
  color: var(--theme-color);
  display: inline-block;
  width: 100%;
}
.deb-wrap .right .table-container .table-content .value-tip {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 50px;
  display: inline-block;
  vertical-align: middle;
  text-align: right;
}
.deb-wrap .right .table-container .table-content .el-table--border {
  border-right: none;
  border-left: none;
}
.deb-wrap .right .table-container .table-content .el-table--border td {
  border-right: none;
  border-left: none;
}
.deb-wrap .right .table-container .table-content .el-table--border th {
  border-right: none;
  border-left: none;
}
.deb-wrap .right .table-container .table-content .el-table th > .cell {
  border-left: 1px solid #d9d8dd;
  word-break: keep-all;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.deb-wrap .right .table-container .table-content .el-table-column--selection .cell {
  border-left: none !important;
}
.deb-wrap .right .svg-wrap.collapse {
  height: calc(100% - 100px);
}
.deb-wrap .right .table-container.collapse {
  height: 35px;
}
.deb-wrap .right .table-container.collapse .el-tabs__header {
  margin: 0;
}
.deb-wrap .right .table-container.collapse .table-content {
  display: none;
}
.deb-wrap .right.collapse {
  width: calc(100% - 25px);
}
.deb-wrap .custom-btn {
  border: 1px solid var(--theme-color);
  border-radius: 2px;
  background-color: var(--bg-color);
  color: var(--theme-color);
}
.deb-wrap .custom-btn:hover {
  background-color: var(--button-hover-color);
}
.deb-wrap .custom-btn.green {
  background-color: var(--theme-color);
  color: white;
}
.deb-wrap .custom-btn.green:hover {
  background-color: #33b7b9;
}
.deb-wrap .is-disabled.custom-btn {
  background-color: var(--button-disabled-bg-color);
  border: 1px solid var(--table-border-color) !important;
  color: #adb0b8;
}
.deb-wrap .is-disabled.custom-btn:hover {
  background-color: var(--button-disabled-bg-color);
}
.deb-wrap .notShow {
  display: none;
}
.deb-wrap .creat-watch-point-dialog .conditions-container .collection {
  width: 210px;
}
.deb-wrap .creat-watch-point-dialog .conditions-container .condition,
.deb-wrap .creat-watch-point-dialog .conditions-container .param,
.deb-wrap .creat-watch-point-dialog .conditions-container .param-value {
  margin-left: 10px;
  width: 210px;
}
.deb-wrap .creat-watch-point-dialog .conditions-container .percent-sign {
  display: inline-block;
  text-align: right;
  width: 20px;
}
.deb-wrap .creat-watch-point-dialog .conditions-container .inclusive-param {
  text-align: right;
}
.deb-wrap .creat-watch-point-dialog .conditions-container .inclusive-param .item {
  margin-top: 10px;
  display: inline-block;
}
.deb-wrap .creat-watch-point-dialog .conditions-container .inclusive-param .item + .item {
  margin-left: 10px;
}
.deb-wrap .creat-watch-point-dialog .error-msg {
  float: left;
}
.deb-wrap .creat-watch-point-dialog .error-msg .el-icon-warning {
  color: #e6a23c;
  font-size: 16px;
  cursor: pointer;
}
.deb-wrap .el-dialog__wrapper.pendingTips {
  position: absolute;
}
.deb-wrap .el-dialog__wrapper.pendingTips .dialog-icon .el-icon-warning {
  font-size: 24px;
  color: #e6a23c;
  vertical-align: bottom;
}
.deb-wrap .el-dialog__wrapper.pendingTips .el-dialog__body {
  padding: 2px 20px 32px 20px;
}
.deb-wrap .el-dialog__wrapper.pendingTips .el-dialog__body .dialog-content {
  line-height: 24px;
  margin-left: 10px;
}
.deb-wrap .el-dialog__wrapper.pendingTips .el-dialog__footer {
  text-align: center;
  padding: 10px 20px 32px;
}
.deb-wrap .el-dialog__wrapper.pendingTips + .v-modal {
  position: absolute;
}
.deb-wrap .deb-con {
  position: absolute;
  top: 0px;
  width: 100%;
  height: 100%;
  background-color: #fff;
  z-index: 999;
}

.deb-indent {
  padding-left: 40px;
}
</style>

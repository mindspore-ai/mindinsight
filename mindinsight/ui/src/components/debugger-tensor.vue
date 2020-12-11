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
  <div class="deb-tensor-wrap">
    <div class="deb-tensor-left"
         :class="{collapse:leftShow}">
      <div class="deb-tensor-left-content"
           v-show="!leftShow">
        <div class="left-content-title">
          <span>{{ $t('debugger.optimizationOrientation') }}</span>
        </div>
        <div class="left-advice"
             v-show="leftDataShow">
          <div class="left-content-list"
               v-for="item in tensorList"
               :key="item.id">
            <div class="detection-judgment">
              <span>{{ $t('debugger.watchPoint') }}{{item.id}}</span>
              <span>{{ $t('symbols.colon') }}</span>
              <span>{{ $parent.transCondition(item.condition) }}</span>
            </div>
            <div class="reason"
                 v-for="(ele,key) in item.params"
                 :key="key">
              <div class="tensor-icon icon-secondary"></div>
              <div class="tensor-content">{{ele.content}}</div>
            </div>
            <div class="hit-tip"
                 v-if="item.tip">
              <i class="el-icon-warning"></i>{{item.tip}}
            </div>
            <div class="tensor-advice"
                 v-if="!item.tip">
              <span>{{ $t('debugger.tuningAdvice') }}</span>
              <div class="advice-list-title">
                <div class="adviceTitle">{{ item.tuningAdviceTitle }}</div>
                <div class="advice-list">
                  <div class="advice-content"
                       v-for="(element, key) in item.tuningAdvice"
                       :key="key">{{ element }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-show="!leftDataShow"
             class="leftNoData">{{ $t('debugger.noWatchPoint') }}</div>
      </div>
      <div class="collapse-btn"
           :class="{collapse:leftShow}"
           @click="collapseBtnClick">
      </div>
    </div>
    <div class="deb-tensor-right"
         :class="{collapse:leftShow}">
      <div class="deb-con-title">
        <div class="deb-con-title-left"
             :title="curRowObj.name">
          {{ curRowObj.name }}
        </div>
        <div class="deb-con-title-right">
          <div class="close-btn">
            <img src="@/assets/images/close-page.png"
                 @click="closeTensor">
          </div>
        </div>
      </div>
      <div class="deb-compare-detail">
        <div v-for="(statistics,key) in statisticsArr"
             :key="key">
          <label v-if="key===0">
            {{gridType==='preStep'?$t('debugger.preStatisticsLabel'):$t('debugger.curStatisticsLabel')}}
            <span>{{ gridType==='preStep'?curRowObj.step-1:curRowObj.step}}</span>
          </label>
          <label v-if="key===1">{{$t('debugger.preStatisticsLabel')}}<span>{{ curRowObj.step-1 }}</span></label>
          <label v-if="key===2">{{$t('debugger.diffStatisticsLabel')}}</label>
          <span>{{ $t('debugger.max') }} {{ statistics.overall_max===undefined?'--':statistics.overall_max }}</span>
          <span>{{ $t('debugger.min') }} {{ statistics.overall_min===undefined?'--':statistics.overall_min }}</span>
          <span>{{ $t('debugger.mean') }} {{ statistics.overall_avg===undefined?'--':statistics.overall_avg }}</span>
          <span>{{ $t('debugger.nan') }}
            {{ statistics.overall_nan_count===undefined?'--':statistics.overall_nan_count }}
          </span>
          <span>{{ $t('debugger.negativeInf') }}
            {{ statistics.overall_neg_inf_count===undefined?'--':statistics.overall_neg_inf_count }}
          </span>
          <span>{{ $t('debugger.inf') }}
            {{ statistics.overall_pos_inf_count===undefined?'--': statistics.overall_pos_inf_count}}
          </span>
          <span>{{ $t('debugger.zero') }}
            {{ statistics.overall_zero_count===undefined?'--': statistics.overall_zero_count}}</span>
          <span>{{ $t('debugger.negativeNum') }}
            {{ statistics.overall_neg_zero_count===undefined?'--':statistics.overall_neg_zero_count }}</span>
          <span>{{ $t('debugger.positiveNum') }}
            {{ statistics.overall_pos_zero_count===undefined?'--':statistics.overall_pos_zero_count }}</span>
          <span>{{ $t('debugger.true') }}
            {{ statistics.overall_true_count===undefined?'--':statistics.overall_true_count }}</span>
          <span>{{ $t('debugger.false') }}
            {{ statistics.overall_false_count===undefined?'--':statistics.overall_false_count }}</span>
        </div>
      </div>
      <div class="deb-con-slide">
        <div class="deb-con-slide-right">
          <el-button size="mini"
                     class="custom-btn"
                     :class="{green:gridType==='value'}"
                     :disabled="state==='running'"
                     @click="tabChange('value')">{{ $t('debugger.curStep') }}</el-button>
          <el-button size="mini"
                     class="custom-btn"
                     :class="{green:gridType==='preStep'}"
                     :disabled="!curRowObj.has_prev_step || state==='running'"
                     @click="tabChange('preStep')">{{ $t('debugger.preStep') }}</el-button>
          <el-button size="mini"
                     class="custom-btn"
                     :class="{green:gridType==='compare'}"
                     :disabled="!curRowObj.has_prev_step || state==='running'"
                     @click="tabChange('compare')">{{ $t('debugger.compareResult') }}</el-button>
        </div>
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
        <div class="deb-con-slide-middle">
          MIN
          <div class="grident">0</div>
          MAX
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
          <debuggerGridTable v-else-if="gridType==='preStep'"
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
      </div>
      <div class="deb-graph-container">
        <div class="graph-title">
          {{$t('debugger.tensorDiagram')}}
          <span class="tip">
            <el-tooltip placement="bottom"
                        effect="light"
                        popper-class="legend-tip">
              <i class="el-icon-warning"></i>
              <div slot="content">
                <div>{{$t('debugger.selectDetail')}}</div>
                <div class="legend">
                  <div class="item">
                    {{$t('debugger.tensorTip')}}
                    <img :src="require('@/assets/images/deb-slot.png')"
                         alt="" />
                  </div>
                  <div class="item">
                    {{$t('debugger.operator')}}
                    <img :src="require('@/assets/images/deb-operator.png')"
                         alt="" />
                  </div>
                </div>
              </div>
            </el-tooltip>
          </span>
        </div>
        <div id="tensor-graph"
             class="deb-graph"
             v-if="graphShow"></div>
        <div class="nodata"
             v-else-if="!graphShow">
          {{ $t('public.noData') }}
        </div>
        <div class="deb-tensor-info">
          <div class="tensor">
            <div class="tensor-title">{{$t('debugger.tensorMsg')}}</div>
            <div class="tensor-detail">
              <span>{{ $t('graph.name') + $t('symbols.colon') }} {{ statistics.name }}</span>
              <span>{{ $t('debugger.max') }} {{ statistics.overall_max===undefined?'--':statistics.overall_max }}</span>
              <span>{{ $t('debugger.min') }} {{ statistics.overall_min===undefined?'--':statistics.overall_min }}</span>
              <span>{{ $t('debugger.mean') }}
                {{ statistics.overall_avg===undefined?'--':statistics.overall_avg }}
              </span>
              <span>{{ $t('debugger.nan') }}
                {{ statistics.overall_nan_count===undefined?'--':statistics.overall_nan_count }}
              </span>
              <span>{{ $t('debugger.negativeInf') }}
                {{ statistics.overall_neg_inf_count===undefined?'--':statistics.overall_neg_inf_count }}
              </span>
              <span>{{ $t('debugger.inf') }}
                {{ statistics.overall_pos_inf_count===undefined?'--': statistics.overall_pos_inf_count}}
              </span>
              <span>{{ $t('debugger.zero') }}
                {{ statistics.overall_zero_count===undefined?'--': statistics.overall_zero_count}}</span>
              <span>{{ $t('debugger.negativeNum') }}
                {{ statistics.overall_neg_zero_count===undefined?'--':statistics.overall_neg_zero_count }}</span>
              <span>{{ $t('debugger.positiveNum') }}
                {{ statistics.overall_pos_zero_count===undefined?'--':statistics.overall_pos_zero_count }}</span>
              <span>{{ $t('debugger.true') }}
                {{ statistics.overall_true_count===undefined?'--':statistics.overall_true_count }}</span>
              <span>{{ $t('debugger.false') }}
                {{ statistics.overall_false_count===undefined?'--':statistics.overall_false_count }}</span>
            </div>
          </div>
          <div class="watch-point">
            <div class="watchPoint-title">{{ $t('debugger.watchList') }}</div>
            <div class="point-list"
                 v-show="rightDataShow">
              <div v-for="(item,key) in watchPoints"
                   :key="key">
                <div class="watch-judgment">
                  <span>{{ $t('debugger.watchPoint') }}{{item.id}}</span>
                  <span>{{ $t('symbols.colon') }}</span>
                  <span>{{ getFormateWatchPoint(item) }}</span>
                </div>
              </div>
            </div>
            <div v-show="!rightDataShow"
                 class="leftNoData">{{ $t('debugger.noWatchPoint') }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import RequestService from '@/services/request-service';
import debuggerGridTable from './debugger-grid-table-simple.vue';
import {select, selectAll, zoom} from 'd3';
import {event as currentEvent} from 'd3-selection';
import 'd3-graphviz';
const d3 = {select, selectAll, zoom};
export default {
  mixins: [],
  components: {debuggerGridTable},
  props: {
    row: {
      type: Object,
      default: () => {},
    },
    formateWatchpointParams: Function,
  },
  data() {
    return {
      leftShow: false,
      tensorList: [],
      tuningRule: '',
      tolerance: 0,
      toleranceInput: 0,
      showFilterInput: true,
      gridType: 'compare',
      dims: null,
      statisticsArr: [],
      tensorValue: [],
      loadingOption: {
        lock: true,
        text: this.$t('public.dataLoading'),
        spinner: 'el-icon-loading',
        background: 'rgba(0, 0, 0, 0.3)',
      },
      curRowObj: this.row,

      tensorGraphData: {},
      tensorGraphviz: null,
      selectedNode: {},
      statistics: {},
      leftDataShow: true,
      rightDataShow: true,
      tuningAdvice: [],
      tuningAdviceTitle: '',
      watchPoints: [],
      callbackFun: null,
      graphShow: true,
      statisticsKeys: [
        'name',
        'overall_avg',
        'overall_count',
        'overall_max',
        'overall_min',
        'overall_nan_count',
        'overall_neg_inf_count',
        'overall_neg_zero_count',
        'overall_pos_inf_count',
        'overall_pos_zero_count',
        'overall_zero_count',
        'overall_true_count',
        'overall_false_count',
      ],
      loadingInstance: {},
      initOver: false,
    };
  },
  computed: {
    state() {
      return this.$parent.metadata.state;
    },
  },
  mounted() {
    this.$nextTick(() => {
      this.callbackFun = this.debounce(this.resizeCallback, 200);
      window.addEventListener('resize', this.callbackFun);
      this.init();
    });
  },
  methods: {
    init() {
      this.loadingInstance = this.$loading(this.loadingOption);
      this.initOver = false;
      if (this.curRowObj.type === 'value') {
        this.gridType = 'value';
        this.viewValueDetail(this.curRowObj);
      } else {
        this.gridType = 'compare';
        this.tensorComparisons(this.curRowObj);
      }
      this.getTensorGraphData(true);
      this.getTensorHitsData();
    },
    getTensorGraphData(initPage) {
      const params = {
        tensor_name: this.curRowObj.name,
        graph_name: this.curRowObj.graph_name,
      };
      RequestService.getTensorGraphData(params).then(
          (res) => {
            if (res && res.data && res.data.graph && res.data.graph.nodes && res.data.graph.nodes.length) {
              this.graphShow = true;
              const nodes = JSON.parse(JSON.stringify(res.data.graph.nodes));
              this.tensorGraphData = {};
              nodes.forEach((node) => {
                this.tensorGraphData[node.name] = {...node, type: 'node'};
                if (node.slots && node.slots.length) {
                  node.slots.forEach((slot) => {
                    const obj = {
                      ...slot,
                      name: `${node.name}:${slot.slot}`,
                      graph_name: node.graph_name,
                      type: 'slot',
                    };
                    this.tensorGraphData[obj.name] = obj;
                  });
                }
              });

              if (initPage) {
                this.selectedNode.name = this.curRowObj.name;
                const dot = this.packageData();
                this.initGraph(dot);
              } else {
                if (this.selectedNode.name) {
                  this.setNodeData();
                }
              }
            } else {
              this.graphShow = false;
              this.rightDataShow = false;
              this.statisticsKeys.forEach((key) => {
                this.statistics[key] = '--';
              });
            }
          },
          (err) => {
            this.graphShow = false;
            this.statisticsKeys.forEach((key) => {
              this.statistics[key] = '--';
            });
            this.dealLoading();
          },
      );
    },
    updateGraphData(graphName, tensorName) {
      if (graphName === this.curRowObj.graph_name && tensorName === this.curRowObj.name) {
        this.getTensorGraphData(false);
      }
    },
    getTensorHitsData() {
      const params = {
        tensor_name: this.curRowObj.name,
        graph_name: this.curRowObj.graph_name,
      };
      RequestService.tensorHitsData(params).then(
          (res) => {
            if (res && res.data && res.data.watch_points && res.data.watch_points.length) {
              this.leftDataShow = true;
              this.tensorList = res.data.watch_points.map((val) => {
                return {
                  id: val.id,
                  condition: val.watch_condition.id,
                  params: val.watch_condition.params || [],
                  selected: false,
                  tip:
                  val.error_list && val.error_list.length
                    ? val.error_list
                        .map((i) => {
                          return this.$t('debugger.checkTips')[i];
                        })
                        .join('') + this.$t('debugger.checkTips').cannotCheck
                    : '',
                };
              });

              const tensorAdvice = this.$t(`debugger.tensorTuningAdvice`);
              this.tensorList.forEach((item) => {
                const tuning = tensorAdvice[item.condition];
                if (!tuning) {
                  item.tuningAdviceTitle = this.$t(`debugger.noAdvice`);
                } else {
                  item.tuningAdviceTitle = tuning[1];
                  item.tuningAdvice = tuning[2];
                }
                this.formateWatchpointParams(item.params);
              });
            } else {
              this.leftDataShow = false;
            }
          },
          (error) => {
            this.leftDataShow = false;
            this.$parent.showErrorMsg(error);
          },
      );
    },
    getFormateWatchPoint(item) {
      let param = '';
      if (item.params && item.params.length) {
        this.formateWatchpointParams(item.params);
        param = item.params.map((i) => i.content).join('; ');
      }
      return `${this.$parent.transCondition(item.condition)} (${param})`;
    },
    packageData() {
      let nodeStr = '';
      let edgeStr = '';
      const edges = [];
      Object.keys(this.tensorGraphData).forEach((key) => {
        const node = this.tensorGraphData[key];
        if (node.type === 'node') {
          nodeStr += `<${node.name}>[id="${node.name}";label="${node.name
              .split('/')
              .pop()}";shape="ellipse";class="operator"];`;
        }
        if (node.slots && node.slots.length) {
          nodeStr += this.packageSubGraph(node);
        }

        if (node.input) {
          Object.keys(node.input).forEach((key) => {
            const list = node.input[key].slot_mapping;
            if (list && list.length) {
              list.forEach((map) => {
                if (map && map.length) {
                  edges.push({
                    source: `${key}:${map[0]}`,
                    target: `outputOf${key}_slots`,
                    count: 1,
                  });

                  edges.push({
                    source: `outputOf${key}_slots`,
                    target: `${node.name}`,
                    count: 1,
                  });
                }
              });
            }
          });
        }
      });
      this.$parent.uniqueEdges(edges);

      edges.forEach((edge) => {
        edgeStr +=
          `<${edge.source}>-><${edge.target}>[id="${edge.source}->${edge.target}";` +
          `label="${edge.count > 1 ? edge.count + 'tensor' : ''}"]`;
      });

      const initSetting = 'node[style="filled";fontsize="10px"];edge[fontsize="6px";];';
      return `digraph {compound=true;rankdir=TB;${initSetting}${nodeStr}${edgeStr}}`;
    },
    /**
     * Encapsulates the data of a subgraph.
     * @param {Array} node Node data.
     * @return {String} Dot string
     */
    packageSubGraph(node) {
      const slots = node.slots;
      const name = node.name;
      const subGraphInput = `inputOf${node.name}_slots`;
      const subGraphOutput = `outputOf${node.name}_slots`;
      let strTemp = '';
      let nodeStr = '';
      let edgeStr = '';
      const clusterName = `cluster_${name}_slots`;

      nodeStr +=
        `{rank=min;<${subGraphInput}>[shape="circle";` +
        `id="${subGraphInput}";width=0.02;fixedsize=true;` +
        `label=""]};`;
      edgeStr += `<${name}>-><${subGraphInput}>[id="${name}->${subGraphInput}";label="${slots.length}tensor"]`;

      const outputKeys = Object.keys(node.output || {});
      if (outputKeys.length) {
        nodeStr +=
          `{rank=max;<${subGraphOutput}>[shape="circle";` +
          `id="${subGraphOutput}";width=0.02;fixedsize=true;` +
          `label=""]};`;
      }

      slots.forEach((slot) => {
        const slotName = `${name}:${slot.slot}`;
        nodeStr +=
          `<${slotName}>[id="${slotName}";label="slot:${slot.slot}${this.getSlotWatchPointsAbbr(slot)}";` +
          `shape="polygon";class="slot${
            slotName === this.curRowObj.name ? ' current selected' : ''
          }";fillcolor="#c5e0b3"];`;

        edgeStr += `<${subGraphInput}>-><${slotName}>[id="${subGraphInput}->${slotName}"];`;
      });

      strTemp =
        `subgraph <${clusterName}>{style="filled";id="${name}_slots";` +
        `label="";fillcolor="#ffffff";${nodeStr}};${edgeStr}`;

      return strTemp;
    },
    getSlotWatchPointsAbbr(slot) {
      let abbrStr = '';
      if (slot && slot.watch_points && slot.watch_points.length) {
        let list = [];
        slot.watch_points.forEach((hit) => {
          if (hit.watch_condition && hit.watch_condition.abbr) {
            list.push(hit.watch_condition.abbr);
          }
        });
        list = Array.from(new Set(list));
        abbrStr = `[${list.join()}]`;
      }
      return abbrStr;
    },
    /**
     * Initializing the dataset graph
     * @param {String} dot Dot statement encapsulated in graph data
     */
    initGraph(dot) {
      try {
        this.tensorGraphviz = d3
            .select('#tensor-graph')
            .graphviz({useWorker: false})
            .dot(dot)
            .attributer(this.$parent.attributer)
            .render(this.startApp);
      } catch (error) {
        const svg = document.querySelector('#tensor-graph svg');
        if (svg) {
          svg.remove();
        }
        this.initGraph(dot);
      }
    },
    startApp() {
      setTimeout(() => {
        if (this.tensorGraphviz) {
          this.tensorGraphviz._data = null;
          this.tensorGraphviz._dictionary = null;
          this.tensorGraphviz = null;
        }
      }, 100);

      const graphDom = d3.select('#tensor-graph');
      graphDom.selectAll('title').remove();
      this.initZooming();
      this.fitGraph();

      const nodes = graphDom.selectAll('.node');
      nodes.on('click', (target, index, nodesList) => {
        const event = currentEvent;
        event.stopPropagation();
        event.preventDefault();

        this.selectedNode.name = nodesList[index].id;
        this.setNodeData();
      });

      const slots = graphDom.selectAll('.node.slot');
      slots.on('dblclick', (target, index, nodesList) => {
        const event = currentEvent;
        event.stopPropagation();
        event.preventDefault();

        const selectedNode = nodesList[index];
        if (selectedNode.id !== this.curRowObj.name) {
          const data = this.tensorGraphData[selectedNode.id];

          this.curRowObj.name = data.name;
          this.curRowObj.full_name = data.full_name;
          this.curRowObj.graph_name = data.graph_name;
          this.curRowObj.has_prev_step = data.has_prev_step;
          this.curRowObj.type = 'value';
          this.curRowObj.shape = JSON.stringify(data.shape || []);

          nodes.on('click', null);
          nodes.on('dblclick', null);
          this.resetTensor();
        }
      });

      if (this.selectedNode.name) {
        this.setNodeData();
      }
      this.$nextTick(() => {
        this.dealLoading();
      });
    },
    fitGraph() {
      const graphContainer = document.getElementById('tensor-graph');
      const graphDom = graphContainer.querySelector(`#graph0`);
      const containerRect = graphContainer.getBoundingClientRect();
      let graphRect = graphDom.getBoundingClientRect();
      const transformData = this.$parent.getTransformData(graphDom);
      const selectedNode = graphDom.querySelector(`g[id="${this.curRowObj.name}"]`);
      let nodeRect = selectedNode.getBoundingClientRect();
      const nodeBox = selectedNode.getBBox();
      const transRate = nodeBox.width / nodeRect.width;
      const paddingTop = 20;

      if (graphRect.height < containerRect.height / 2) {
        let scale = (containerRect.height - paddingTop * 2) / graphRect.height;
        graphDom.setAttribute(
            'transform',
            `translate(${transformData.translate[0]},${transformData.translate[1]}) scale(${
              scale * transformData.scale[0]
            })`,
        );

        this.$nextTick(() => {
          nodeRect = selectedNode.getBoundingClientRect();
          graphRect = graphDom.getBoundingClientRect();
          const nodeCenter = {
            x: nodeRect.x + nodeRect.width / 2,
          };
          const containerCenter = {
            x: containerRect.x + containerRect.width / 2,
          };

          let x = (containerCenter.x - nodeCenter.x) * transRate;
          let y = (containerRect.top + paddingTop - graphRect.top) * transRate;
          x = parseFloat(x.toFixed(2));
          y = parseFloat(y.toFixed(2));
          scale = parseFloat((scale * transformData.scale[0]).toFixed(2));

          graphDom.setAttribute(
              'transform',
              `translate(${transformData.translate[0] + x},${transformData.translate[1] + y}) scale(${scale})`,
          );
        });
      }
    },
    /**
     * Initializing the Zoom Function of a Graph
     */
    initZooming() {
      const svgDom = document.querySelector('#tensor-graph svg');
      const svgRect = svgDom.getBoundingClientRect();

      const graphDom = document.querySelector('#tensor-graph #graph0');
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
            if (!event) {
              return;
            }
            pointer.start.x = event.x;
            pointer.start.y = event.y;
          })
          .on('zoom', () => {
            const event = currentEvent.sourceEvent;
            if (!event) {
              return;
            }
            const transformData = this.$parent.getTransformData(graphDom);
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

              scale = Math.max(this.$parent.scaleRange[0], scale, minScale);
              scale = Math.min(this.$parent.scaleRange[1], scale);
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

      const svg = d3.select('#tensor-graph svg');
      svg.on('.zoom', null);
      svg.call(zoom);
      svg.on('dblclick.zoom', null);
      svg.on('wheel.zoom', null);

      const graph0 = d3.select('#tensor-graph #graph0');
      graph0.on('.zoom', null);
      graph0.call(zoom);
    },
    setNodeData() {
      window.getSelection().removeAllRanges();
      const selectedNode = document.querySelector(`#tensor-graph g[id="${this.selectedNode.name}"]`);
      d3.selectAll('#tensor-graph .node').classed('selected', false);
      if (selectedNode) {
        selectedNode.classList.add('selected');
      }
      d3.selectAll('#tensor-graph .edge').classed('selected', false);
      this.selectedNode = JSON.parse(JSON.stringify(this.tensorGraphData[this.selectedNode.name]));

      if (this.selectedNode.type === 'slot') {
        if (!(this.selectedNode.statistics && Object.keys(this.selectedNode.statistics).length)) {
          this.statisticsKeys.forEach((key) => {
            this.statistics[key] = '--';
          });
        } else {
          this.statistics = JSON.parse(JSON.stringify(this.selectedNode.statistics));
        }
        this.statistics.name = JSON.parse(JSON.stringify(this.selectedNode.name));

        if (this.selectedNode.watch_points && this.selectedNode.watch_points.length) {
          this.watchPoints = this.selectedNode.watch_points.map((val) => {
            return {
              id: val.id,
              condition: val.watch_condition.id,
              params: val.watch_condition.params || [],
              selected: false,
            };
          });
          this.rightDataShow = true;
        } else {
          this.rightDataShow = false;
        }
      } else {
        this.statisticsKeys.forEach((key) => {
          this.statistics[key] = '--';
        });
        this.rightDataShow = false;
        this.highLightEdges();
      }
      this.$forceUpdate();
    },
    highLightEdges() {
      const edges = [];
      const input = this.selectedNode.input || {};
      const inputKeys = Object.keys(input);
      if (inputKeys.length) {
        inputKeys.forEach((key) => {
          const mapping = input[key].slot_mapping;
          if (mapping && mapping.length) {
            mapping.forEach((map) => {
              if (map && map.length) {
                edges.push(`${key}:${map[0]}->outputOf${key}_slots`);
                edges.push(`outputOf${key}_slots->${this.selectedNode.name}`);
              }
            });
          }
        });
      }

      const slots = this.selectedNode.slots || [];
      if (slots.length) {
        edges.push(`${this.selectedNode.name}->inputOf${this.selectedNode.name}_slots`);
        slots.forEach((slot) => {
          edges.push(`inputOf${this.selectedNode.name}_slots->${this.selectedNode.name}:${slot.slot}`);
        });
      }

      edges.forEach((edge) => {
        d3.select(`#tensor-graph g[id="${edge}"]`).classed('selected', true);
      });
    },
    resetTensor() {
      const svg = document.querySelector('#tensor-graph svg');
      if (svg) {
        svg.remove();
      }

      const grideTable = this.$refs.tensorValue;
      if (grideTable) {
        grideTable.updateGridData(true, [], {}, '[0,0,:,:]');
      }

      this.tensorGraphData = {};
      this.init();
    },
    closeTensor() {
      this.$emit('close', this.selectedNode.name, this.curRowObj.graph_name);
    },
    /**
     * Collaspe btn click function
     */
    collapseBtnClick() {
      this.leftShow = !this.leftShow;
      setTimeout(() => {
        this.resizeCallback();
      }, 500);
    },
    /**
     * Resize callback function
     */
    resizeCallback() {
      this.initZooming();
      if (this.$refs.tensorValue) {
        this.$refs.tensorValue.resizeView();
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
    toleranceInputChange() {
      this.toleranceInput = this.tolerance;
    },
    toleranceValueChange(val) {
      val = val.replace(/[^0-9]+/g, '');
      if (Number(val) === 0) {
        this.toleranceInput = 0;
        this.tolerance = 0;
      }
      if (Number(val) < 0) {
        this.tolerance = 0;
        this.toleranceInput = 0;
      }
      if (Number(val) > 0) {
        if (Number(val) > 100) {
          this.tolerance = 100;
          this.toleranceInput = 100;
        } else {
          this.tolerance = Number(val);
          this.toleranceInput = Number(val);
        }
      }
    },
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
        this.tensorComparisons(this.curRowObj, this.dims);
      } else {
        this.viewValueDetail(this.curRowObj, this.dims);
      }
    },
    /**
     * Query tensor Comparison data
     * @param { Object } row current clickd tensor value data
     * @param { Object } dims dims
     */
    tensorComparisons(row, dims) {
      const shape = dims
        ? dims
        : JSON.stringify(
            JSON.parse(row.shape)
                .map((val, index) => {
                // The default parameter format of shape is that the last two digits are:. The front is all 0
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
        graph_name: row.graph_name,
      };
      RequestService.tensorComparisons(params).then(
          (res) => {
            if (res && res.data && res.data.tensor_value) {
              if (row.shape === '[]') {
                this.showFilterInput = false;
              } else {
                this.showFilterInput = true;
              }
              const tensorValue = res.data.tensor_value;
              const statistics = tensorValue.statistics || {};
              this.statisticsArr = [
                tensorValue.curr_step_statistics || {},
                tensorValue.prev_step_statistics || {},
                tensorValue.statistics || {},
              ];
              if (tensorValue.diff === 'Too large to show.') {
                this.tensorValue = [];
                this.$nextTick(() => {
                  this.$refs.tensorValue.showRequestErrorMessage(
                      this.$t('debugger.largeDataTip'),
                      JSON.parse(row.shape),
                      shape,
                      true,
                  );
                });
                this.dealLoading();
                return;
              }
              this.tensorValue = tensorValue.diff;
              if (this.tensorValue && this.tensorValue instanceof Array && !(this.tensorValue[0] instanceof Array)) {
                this.tensorValue = [this.tensorValue];
              }

              this.$nextTick(() => {
                this.$refs.tensorValue.updateGridData(this.tensorValue, JSON.parse(row.shape), statistics, shape);
              });
            }
            this.$nextTick(() => {
              this.dealLoading();
            });
          },
          (err) => {
            this.dealLoading();
          },
      );
    },
    /**
     * Query tensor value or tensor comparison
     * @param {Object} data tensor value data
     */
    tensorFilterChange(data) {
      this.dims = `[${data.toString()}]`;
      if (this.gridType === 'compare') {
        this.tensorComparisons(this.curRowObj, this.dims);
      } else {
        this.viewValueDetail(this.curRowObj, this.dims);
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
                // The default parameter format of shape is that the last two digits are:. The front is all 0
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
        graph_name: row.graph_name,
        prev: this.gridType === 'preStep' ? true : false,
      };
      RequestService.tensors(params).then(
          (res) => {
            if (row.shape === '[]') {
              this.showFilterInput = false;
            } else {
              this.showFilterInput = true;
            }
            if (res.data.tensor_value) {
              let value = res.data.tensor_value.value;
              const statistics = res.data.tensor_value.statistics || {};
              this.statisticsArr = [statistics];
              if (value === 'Too large to show.') {
                this.tensorValue = [];
                this.$nextTick(() => {
                  this.$refs.tensorValue.showRequestErrorMessage(
                      this.$t('debugger.largeDataTip'),
                      JSON.parse(row.shape),
                      shape,
                      true,
                  );
                });
                this.dealLoading();
                return;
              }
              if (value === null) {
                value = 'null';
              }
              this.tensorValue = value instanceof Array ? value : [value];
              this.$nextTick(() => {
                this.$refs.tensorValue.updateGridData(this.tensorValue, JSON.parse(row.shape), statistics, shape);
              });
            }
            this.$nextTick(() => {
              this.dealLoading();
            });
          },
          (err) => {
            this.$parent.showErrorMsg(err);
            this.dealLoading();
          },
      );
    },
    dealLoading() {
      if (!this.initOver) {
        this.initOver = true;
      } else {
        this.loadingInstance.close();
      }
    },
  },
  destroyed() {
    window.removeEventListener('resize', this.callbackFun);
  },
};
</script>
<style lang="scss">
.deb-tensor-wrap {
  height: 100%;
  background-color: white;
  position: relative;
  overflow: hidden;
  & > div {
    float: left;
    height: 100%;
  }
  .deb-tensor-left {
    width: 400px;
    padding-right: 25px;
    height: 100%;
    background-color: white;
    position: relative;
    transition: width 0.2s;
    -moz-transition: width 0.2s; /* Firefox 4 */
    -webkit-transition: width 0.2s; /* Safari and Chrome */
    -o-transition: width 0.2s; /* Opera */
    .left-content-title {
      padding-left: 15px;
      height: 50px;
      line-height: 50px;
      font-weight: bold;
    }
    .left-advice {
      overflow-y: auto;
      text-overflow: ellipsis;
      height: calc(100% - 50px);
    }
    .left-content-list {
      border-top: 1px solid #f2f2f2;
      padding-bottom: 10px;
      > div {
        padding-left: 15px;
      }
      .detection-judgment {
        height: 40px;
        line-height: 40px;
        font-weight: bold;
      }
      .hit-tip {
        padding: 10px 15px 0 15px;
        .el-icon-warning {
          font-size: 14px;
          color: #e6a23c;
          padding-right: 4px;
        }
      }
      .reason {
        display: flex;
        padding: 1px 15px;
        width: 100%;
      }
      .tensor-icon {
        width: 6px;
        height: 6px;
        border-radius: 3px;
      }
      .icon-secondary {
        background-color: #00a5a7;
        margin-top: 8px;
      }
      .tensor-content {
        padding-left: 6px;
        width: calc(100% - 12px);
      }
      .tensor-value {
        padding: 5px 2px;
        span {
          padding-right: 5px;
        }
      }
      .tensor-advice {
        width: 344px;
        background-color: #f5f7fa;
        margin-left: 15px;
        margin-top: 10px;
        padding: 10px;
        span {
          font-weight: bold;
        }
      }
      .advice-list-title {
        padding: 0px;
        padding-top: 10px;
        padding-left: 10px;
        .advice-list {
          padding-top: 5px;
        }
        .advice-icon {
          width: 6px;
          height: 6px;
          border-radius: 3px;
          background-color: #00a5a7;
          display: inline-block;
        }
        .advice-content {
          display: inline-block;
          padding: 0px 12px;
          height: 25px;
          line-height: 25px;
        }
      }
    }
    .leftNoData {
      text-align: center;
      border-top: 1px solid #f2f2f2;
      padding-top: 15px;
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
      background-image: url('../assets/images/collapse-left.svg');
    }
    .collapse-btn.collapse {
      background-image: url('../assets/images/collapse-right.svg');
    }
    .deb-tensor-left-content {
      height: 100%;
      border-right: 1px solid #ebeef5;
      overflow: auto;
    }
  }
  .deb-tensor-left.collapse {
    width: 0px;
  }
  .deb-tensor-right {
    width: calc(100% - 400px);
    height: 100%;
    transition: width 0.2s;
    -moz-transition: width 0.2s; /* Firefox 4 */
    -webkit-transition: width 0.2s; /* Safari and Chrome */
    -o-transition: width 0.2s; /* Opera */
    display: flex;
    flex-direction: column;
    .deb-con-title {
      height: 40px;
      line-height: 40px;
      flex-shrink: 0;
      position: relative;

      .deb-con-title-left {
        position: absolute;
        left: 0;
        font-weight: bold;
        font-size: 16px;
        width: calc(100% - 100px);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
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
    .deb-compare-detail {
      flex-shrink: 0;
      padding-right: 32px;
      span {
        margin-right: 10px;
        padding-left: 10px;
        border-left: 1px solid #e4e7ec;
      }
      label {
        display: inline-block;
        min-width: 123px;
        span {
          border-left: none;
        }
      }
    }
    .deb-con-slide {
      height: 40px;
      line-height: 40px;
      flex-shrink: 0;
      position: relative;
      margin: 5px 0;

      .deb-con-slide-left {
        float: left;
        display: flex;
        margin-left: 10px;

        .deb-slide-title {
          margin-right: 20px;
        }

        .deb-slide-width {
          width: 160px;
        }
        .deb-slide-input {
          width: 60px;
          margin-left: 10px;
        }
      }
      .deb-con-slide-right {
        float: left;

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
      .deb-con-slide-middle {
        position: absolute;
        right: 32px;
        width: 150px;
        padding: 10px 0;
        line-height: 15px;
        .grident {
          display: inline-block;
          width: calc(100% - 70px);
          background-image: linear-gradient(to right, rgba(227, 125, 41), #fff, rgba(0, 165, 167));
          text-align: center;
          color: transparent;
          border-radius: 10px;
        }
      }
    }

    .deb-con-table {
      flex: 1;
      flex-grow: 1;
      flex-shrink: 1;
      padding-right: 32px;
      flex-shrink: 0;
      .deb-compare-wrap {
        height: 100%;
      }
    }
    .deb-graph-container {
      flex: 1;
      flex-grow: 1;
      flex-shrink: 1;
      padding: 10px 32px 10px 0px;
      position: relative;
      display: flex;
      overflow: hidden;
      .graph-title {
        position: absolute;
        font-weight: bold;
        font-size: 14px;
        .tip {
          font-size: 16px;
          margin-left: 10px;
          cursor: pointer;
        }
      }
      .nodata {
        width: calc(100% - 375px);
        text-align: center;
        margin-top: 120px;
      }
      .deb-graph {
        width: calc(100% - 375px);
        .edge {
          path {
            stroke: rgb(120, 120, 120);
          }
          polygon {
            stroke: rgb(120, 120, 120);
            fill: rgb(120, 120, 120);
          }
        }
        .node.operator > ellipse {
          stroke: #e3aa00;
          fill: #ffe794;
        }
        .node.slot {
          & > polygon {
            stroke: #4ea6e6;
            fill: #c7f5f4;
          }
          &.current {
            & > polygon {
              stroke: #4ea6e6;
              fill: #00a5a7;
            }
            text {
              fill: white;
            }
          }
        }
        .node {
          &:hover {
            cursor: pointer;
            & > polygon,
            & > ellipse {
              stroke-width: 2px;
            }
          }
        }

        .cluster > polygon {
          stroke: #e4e7ed;
          fill: #e9fcf9;
        }
        .node.selected {
          polygon,
          ellipse {
            stroke: red !important;
            stroke-width: 2px;
          }
        }
        .edge.selected {
          path {
            stroke: red;
          }
          polygon {
            stroke: red;
            fill: red;
          }
        }
      }
      .deb-tensor-info {
        width: 375px;
        height: 100%;
        border-left: solid 2px #e4e7ed;
        padding-left: 20px;
        .tensor {
          .tensor-title {
            font-size: 14px;
            font-weight: bold;
            padding-bottom: 8px;
          }
          .tensor-detail {
            overflow: auto;
            height: calc(100% - 30px);
            span {
              display: inline-block;
              padding: 5px 0px;
              min-width: 50%;
              word-break: break-all;
            }
            ul {
              li {
                padding: 5px 10px;
                & > div {
                  display: inline-block;
                  vertical-align: top;
                  word-break: break-all;
                  line-height: 16px;
                }
                .attr-key {
                  width: 30%;
                }
                .attr-value {
                  width: 70%;
                  padding-left: 10px;
                }
                &:hover {
                  background-color: #e9fcf9;
                }
              }
            }
          }
        }
        .tensor {
          height: 50%;
          overflow: auto;
        }
        .watch-point {
          height: 50%;
          .point-list {
            height: calc(100% - 35px);
            overflow: auto;
            text-overflow: ellipsis;
          }
          .watchPoint-title {
            padding: 8px 0;
            font-size: 14px;
            font-weight: bold;
          }
          .watch-judgment {
            padding: 5px 0;
          }
        }
      }
    }
  }
  .deb-tensor-right.collapse {
    width: calc(100% - 25px);
  }
}
.legend-tip {
  .legend {
    margin-top: 10px;
    .item {
      display: inline-block;
      width: 50%;
      img {
        vertical-align: sub;
        height: 20px;
        margin-left: 10px;
      }
    }
  }
}
</style>

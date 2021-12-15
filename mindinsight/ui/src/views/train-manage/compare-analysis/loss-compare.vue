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
  <div class="mi-common-content-page">
    <!-- No data -->
    <empty v-if="!originDataArr.length"
           :state="pageState"
           :fontSize="16">
    </empty>
    <!-- Normal -->
    <div v-else
         class="loss-compare">
      <div class="mi-border-header">
        <div class="compare-run">
          <multiselectGroupComponents ref="multiselectGroupComponents"
                                      :componentsLabel="componentsLabel"
                                      :checkListArr="summaryOperateList"
                                      :isLimit="true"
                                      :limitNum="pageNum"
                                      @selectedChange="summarySelectedChanged"></multiselectGroupComponents>
        </div>
        <div class="compare-graph">
          <div class="view-title">{{$t('lossCompare.visualiation')}}</div>
          <el-radio-group class="graph-radio"
                          v-model="curGraphName"
                          fill="#00A5A7"
                          text-color="#FFFFFF"
                          size="small"
                          @change="viewGraphChange">
            <el-radio-button label='isopleth'>{{$t('lossAnalysis.isopleth')}}</el-radio-button>
            <el-radio-button label='reliefMap'>{{$t('lossAnalysis.reliefMap')}}</el-radio-button>
            <el-radio-button label='threeDiagram'>{{$t('lossAnalysis.threeDiagram')}}</el-radio-button>
          </el-radio-group>
          <div class="inline-show color-style">
            <!-- set line num -->
            <div class="inline-show"
                 v-show="curGraphName!=='threeDiagram'">
              <div class="line-num-style">{{$t('lossAnalysis.setLineNum')}}</div>
              <el-select v-model="contourSetting.contoursNumber"
                         :placeholder="$t('public.select')"
                         @change="mapLineNumChange"
                         class="inline-show color-select">
                <el-option v-for="item in lineNumoptions"
                           :key="item.value"
                           :label="item.label"
                           :value="item.value">
                </el-option>
              </el-select>
            </div>
            <div class="view-title">{{$t('lossCompare.colorMatching')}}
            </div>
            <el-select class="inline-show color-select"
                       v-model="colorValue"
                       :placeholder="$t('public.select')"
                       @change="colorChange">
              <el-option v-for="colorItem in colorOptions"
                         :key="colorItem.value"
                         :label="colorItem.label"
                         :value="colorItem.value">
              </el-option>
            </el-select>
            <div class="inline-show">{{$t('lossCompare.high')}}</div>
            <div class="inline-show color-legend-jet"
                 v-show="colorValue === 0"></div>
            <div class="inline-show color-legend-viridis"
                 v-show="colorValue === 1"></div>
            <div class="inline-show color-legend-ruBu"
                 v-show="colorValue === 2"></div>
            <div class="inline-show">{{$t('lossCompare.low')}}</div>
            <div class="conpoint inline-show"></div>
            <div class="conpoint-title inline-show">{{$t('lossCompare.conpoint')}}</div>
          </div>
          <div class="inline-show mode-select"
               v-show="curGraphName==='threeDiagram'">
            <div class="view-title">{{$t('lossCompare.compareMode')}}</div>
            <el-radio-group v-model="curModeName"
                            fill="#00A5A7"
                            text-color="#FFFFFF"
                            size="small"
                            @change="viewModeChange">
              <el-radio-button :label=0>{{$t('lossCompare.tiled')}}</el-radio-button>
              <el-radio-button :label=1>{{$t('lossCompare.superimposed')}}</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </div>
      <div class="compare-content"
           ref="compareContent">
        <!-- Data -->
        <div id="superimposedView"
             v-if="originDataArr.length"
             v-show="curGraphName==='threeDiagram' && curModeName"
             class="superimposedView">
          <div class="superimposedView-left"
               :class="{collapse:collapse}">
            <diagram3D class="mixed-chart"
                       ref="mixedDiagram3D"
                       :styleSetting="diagram3DSetting"
                       :componentConfigOptions="diagram3DMaintoolsShow"
                       :mergeGraphproperties="true"
                       :isCompareLoss="true"></diagram3D>
          </div>
          <div class="superimposedView-con">
            <div :class="[
                  `collapse-btn-${this.$store.state.themeIndex}`,
                  collapse ? 'collapse' : '',
                ]"
                 @click="clickCollapse"></div>
          </div>
          <div class="superimposedView-right"
               v-show="!collapse">
            <div class="superimposedView-right-item"
                 v-for="(sampleItem, index) in originDataArr"
                 :key="index"
                 :class="sampleItem.diagram3DSVChecked ? 'activeCheck' :
               (diagram3DSVCheckCount >= diagram3DSVCheckLimit ? 'activeDisabled' : '')"
                 :title="(!sampleItem.diagram3DSVChecked && diagram3DSVCheckCount >= diagram3DSVCheckLimit) ?
               $t('lossCompare.diagram3DSVLimitTip'): ''"
                 @click="activeCheck(sampleItem)"
                 v-show="sampleItem.show">
              <template v-if="sampleItem.hasError">
                <div class="error-message-container">
                  {{sampleItem.errorMessage}}
                </div>
              </template>
              <template v-else>
                <diagram3D :ref="'threeDiagram'+'mixed'+sampleItem.ref"
                           :oriData="sampleItem.fullData"
                           :styleSetting="diagram3DSetting"></diagram3D>
              </template>
              <div class="superimposedView-right-float">
                <i class="el-icon-check"></i>
              </div>
              <div class="chart-item-info">
                <div class="info-content">
                  <div class="w100">
                    <span class="label">{{sampleItem.label}}</span>
                  </div>
                </div>
                <div class="info-content">
                  <div>
                    <span class="label">{{$t('lossAnalysis.network')}}{{$t('symbols.colon')}}</span>
                    <span class="value">
                      [
                      <span class="res-net"
                            :title="sampleItem.info.network">{{sampleItem.info.network}}</span>
                      ]
                    </span>
                  </div>
                  <div>
                    <span class="label">{{$t('lossAnalysis.optimizer')}}{{$t('symbols.colon')}}</span>
                    <span class="value">
                      [
                      <span class="res-net"
                            :title="sampleItem.info.optimizer">{{sampleItem.info.optimizer}}</span>
                      ]</span>
                  </div>
                </div>
                <div class="info-content">
                  <div>
                    <span class="label">{{$t('lossAnalysis.learning_rate')}}{{$t('symbols.colon')}}</span>
                    <span class="value"
                          :title="sampleItem.info.learning_rate">{{sampleItem.info.learning_rate}}
                    </span>
                  </div>
                  <div v-if="!Object.keys(sampleItem.info.metric).length">
                    <span class="label">loss{{$t('symbols.colon')}}</span>
                    <span class="value"
                          :title="sampleItem.info.loss">{{sampleItem.info.loss}}
                    </span>
                  </div>
                  <div v-show="Object.keys(sampleItem.info.metric).length">
                    <span class="label">{{sampleItem.showMetric.label}}{{$t('symbols.colon')}}</span>
                    <span class="value"
                          :title="sampleItem.showMetric.value">{{sampleItem.showMetric.value}}</span>
                  </div>
                </div>
              </div>
              <div class="chart-item-mask"></div>
            </div>

          </div>
        </div>
        <div id="tiledView"
             v-if="originDataArr.length"
             v-show="curGraphName!=='threeDiagram' || !curModeName"
             class="data-content">
          <div class="sample-content"
               v-for="sampleItem in originDataArr"
               :key="sampleItem.ref"
               v-show="sampleItem.show">
            <div class="detail-container">
              <!-- components -->
              <div v-if="curGraphName === 'isopleth'||curGraphName === 'reliefMap'">
                <div class="chart-info"
                     v-show="curGraphName === 'isopleth'">
                  <div class="chartdiv-container">
                    <template v-if="sampleItem.hasError">
                      <div class="error-message-container">
                        {{sampleItem.errorMessage}}
                      </div>
                    </template>
                    <template v-else>
                      <contourMap :ref="'isopleth' + sampleItem.ref"
                                  type="contour"
                                  showConvergencePoint>
                      </contourMap>
                      <div class="chart-item-mask"
                           v-show="false"></div>
                    </template>
                  </div>
                  <div class="info-container">
                    <div class="info-title">
                      <div class="view-title inline-show">
                        {{$t('lossCompare.trainInfo')}}
                        <el-tooltip placement="right-start"
                                    effect="light">
                          <div slot="content"
                               class="tooltip-container">
                            <div class="cl-title-tip">
                              <div class="tip-part">
                                {{$t('lossCompare.trainingTip')}}
                              </div>
                            </div>
                          </div>
                          <i class="el-icon-info"></i>
                        </el-tooltip>
                      </div>
                    </div>
                    <div class="info-content">
                      <div class="w33">
                        <span class="label">{{$t('lossAnalysis.network')}}{{$t('symbols.colon')}}</span>
                        <span class="value">
                          [
                          <span class="res-net"
                                :title="sampleItem.info.network">{{sampleItem.info.network}}</span>
                          ]</span>
                      </div>
                      <div class="w33">
                        <span class="label">{{$t('lossAnalysis.optimizer')}}{{$t('symbols.colon')}}</span>
                        <span class="value">
                          [
                          <span class="res-net"
                                :title="sampleItem.info.optimizer">{{sampleItem.info.optimizer}}</span>
                          ]</span>
                      </div>
                      <div class="w33">
                        <span class="label">{{$t('lossAnalysis.learning_rate')}}{{$t('symbols.colon')}}</span>
                        <span class="value"
                              :title="sampleItem.info.learning_rate">{{sampleItem.info.learning_rate}}
                        </span>
                      </div>
                    </div>
                    <div class="info-title">
                      <div class="view-title inline-show">{{$t('lossCompare.evaluateInfo')}}</div>
                      <div class="view-more inline-show"
                           v-show="Object.keys(sampleItem.info.metric).length>3"
                           @click="showMetricDialog(sampleItem)">
                        {{$t('lossCompare.more')}}</div>
                    </div>
                    <div class="info-content">
                      <div v-if="!Object.keys(sampleItem.info.metric).length">
                        <span class="label">loss{{$t('symbols.colon')}}</span>
                        <span class="value"
                              :title="sampleItem.info.loss">{{sampleItem.info.loss}}
                        </span>
                      </div>
                      <div class="w33"
                           v-else
                           v-for="(evalKey, index) in Object.keys(sampleItem.info.metric).slice(0, 3)"
                           :key="index">
                        <span class="label">{{evalKey}}{{$t('symbols.colon')}}</span>
                        <span class="value"
                              :title="sampleItem.info.metric[evalKey]">{{sampleItem.info.metric[evalKey]}}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="chart-info"
                     v-show="curGraphName === 'reliefMap'">
                  <div class="chartdiv-container">
                    <template v-if="sampleItem.hasError">
                      <div class="error-message-container">
                        {{sampleItem.errorMessage}}
                      </div>
                    </template>
                    <template v-else>
                      <contourMap :ref="'reliefMap' + sampleItem.ref"
                                  type="topographic"
                                  showConvergencePoint>
                      </contourMap>
                      <div class="chart-item-mask"
                           v-show="false"></div>
                    </template>
                  </div>
                  <div class="info-container">
                    <div class="info-title">
                      <div class="view-title inline-show">
                        {{$t('lossCompare.trainInfo')}}
                        <el-tooltip placement="right-start"
                                    effect="light">
                          <div slot="content"
                               class="tooltip-container">
                            <div class="cl-title-tip">
                              <div class="tip-part">
                                {{$t('lossCompare.trainingTip')}}
                              </div>
                            </div>
                          </div>
                          <i class="el-icon-info"></i>
                        </el-tooltip>
                      </div>
                    </div>
                    <div class="info-content">
                      <div class="w33">
                        <span class="label">{{$t('lossAnalysis.network')}}{{$t('symbols.colon')}}</span>
                        <span class="value">
                          [
                          <span class="res-net"
                                :title="sampleItem.info.network">{{sampleItem.info.network}}</span>
                          ]</span>
                      </div>
                      <div class="w33">
                        <span class="label">{{$t('lossAnalysis.optimizer')}}{{$t('symbols.colon')}}</span>
                        <span class="value">
                          [
                          <span class="res-net"
                                :title="sampleItem.info.optimizer">{{sampleItem.info.optimizer}}</span>
                          ]
                        </span>
                      </div>
                      <div class="w33">
                        <span class="label">{{$t('lossAnalysis.learning_rate')}}{{$t('symbols.colon')}}</span>
                        <span class="value"
                              :title="sampleItem.info.learning_rate">{{sampleItem.info.learning_rate}}
                        </span>
                      </div>
                    </div>
                    <div class="info-title">
                      <div class="view-title inline-show">{{$t('lossCompare.evaluateInfo')}}</div>
                      <div class="view-more inline-show"
                           v-show="Object.keys(sampleItem.info.metric).length>3"
                           @click="showMetricDialog(sampleItem)">
                        {{$t('lossCompare.more')}}</div>
                    </div>
                    <div class="info-content">
                      <div v-if="!Object.keys(sampleItem.info.metric).length">
                        <span class="label">loss{{$t('symbols.colon')}}</span>
                        <span class="value"
                              :title="sampleItem.info.loss">{{sampleItem.info.loss}}
                        </span>
                      </div>
                      <div class="w33"
                           v-else
                           v-for="(evalKey, index) in Object.keys(sampleItem.info.metric).slice(0, 3)"
                           :key="index">
                        <span class="label">{{evalKey}}{{$t('symbols.colon')}}</span>
                        <span class="value"
                              :title="sampleItem.info.metric[evalKey]">{{sampleItem.info.metric[evalKey]}}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div class="chart-info"
                   v-show="curGraphName === 'threeDiagram'">
                <div class="chartdiv-container">
                  <template v-if="sampleItem.hasError">
                    <div class="error-message-container">
                      {{sampleItem.errorMessage}}
                    </div>
                  </template>
                  <template v-else>
                    <diagram3D :ref="'threeDiagram'+sampleItem.ref"
                               :oriData="sampleItem.fullData"
                               :componentConfigOptions="diagram3DMintoolsShow"
                               :styleSetting="diagram3DSetting"></diagram3D>
                    <div class="chart-item-mask"
                         v-show="false"></div>
                  </template>
                </div>
                <div class="info-container">
                  <div class="info-title">
                    <div class="view-title inline-show">
                      {{$t('lossCompare.trainInfo')}}
                      <el-tooltip placement="right-start"
                                  effect="light">
                        <div slot="content"
                             class="tooltip-container">
                          <div class="cl-title-tip">
                            <div class="tip-part">
                              {{$t('lossCompare.trainingTip')}}
                            </div>
                          </div>
                        </div>
                        <i class="el-icon-info"></i>
                      </el-tooltip>
                    </div>
                  </div>
                  <div class="info-content">
                    <div class="w33">
                      <span class="label">{{$t('lossAnalysis.network')}}{{$t('symbols.colon')}}</span>
                      <span class="value">
                        [
                        <span class="res-net"
                              :title="sampleItem.info.network">{{sampleItem.info.network}}</span>
                        ]</span>
                    </div>
                    <div class="w33">
                      <span class="label">{{$t('lossAnalysis.optimizer')}}{{$t('symbols.colon')}}</span>
                      <span class="value">
                        [
                        <span class="res-net"
                              :title="sampleItem.info.optimizer">{{sampleItem.info.optimizer}}</span>
                        ]</span>
                    </div>
                    <div class="w33">
                      <span class="label">{{$t('lossAnalysis.learning_rate')}}{{$t('symbols.colon')}}</span>
                      <span class="value"
                            :title="sampleItem.info.learning_rate">{{sampleItem.info.learning_rate}}
                      </span>
                    </div>
                  </div>
                  <div class="info-title">
                    <div class="view-title inline-show">{{$t('lossCompare.evaluateInfo')}}</div>
                    <div class="view-more inline-show"
                         v-show="Object.keys(sampleItem.info.metric).length>3"
                         @click="showMetricDialog(sampleItem)">
                      {{$t('lossCompare.more')}}</div>
                  </div>
                  <div class="info-content">
                    <div v-if="!Object.keys(sampleItem.info.metric).length">
                      <span class="label">loss{{$t('symbols.colon')}}</span>
                      <span class="value"
                            :title="sampleItem.info.loss">{{sampleItem.info.loss}}
                      </span>
                    </div>
                    <div class="w33"
                         v-else
                         v-for="(evalKey, index) in Object.keys(sampleItem.info.metric).slice(0, 3)"
                         :key="index">
                      <span class="label">{{evalKey}}{{$t('symbols.colon')}}</span>
                      <span class="value"
                            :title="sampleItem.info.metric[evalKey]">{{sampleItem.info.metric[evalKey]}}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="summary-title"
                 :title="sampleItem.label">{{sampleItem.label}}
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog :title="detailsDataTitle+$t('lossCompare.evaluateInfo')"
               :visible.sync="detailsDialogVisible"
               width="40%"
               :close-on-click-modal="false"
               class="details-metric-list">
      <el-table :data="detailsMetricList"
                tooltip-effect="light">
        <el-table-column width="50" />
        <el-table-column prop="key"
                         width="250"
                         label="Key">
        </el-table-column>
        <el-table-column prop="value"
                         label="Value">
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script>
import multiselectGroupComponents from '@/components/multiselect-group.vue';
import requestService from '@/services/request-service';
import commonProperty from '@/common/common-property';
import contourMap from '@/components/contour-map.vue';
import diagram3D from '@/components/diagram-3D.vue';
import elementResizeDetectorMaker from 'element-resize-detector';
import empty, { NO_DATA, LOADING_DATA } from '@/components/empty.vue';

class DataItem {
  label;
  show = false;
  ref;
  fullData = {};
  info = {
    network: '--',
    learning_rate: '--',
    optimizer: '--',
    metric: {},
    loss: '--',
  };
  showMetric = {
    label: '--',
    value: '--',
  };
  diagram3DSVNewDataFlag = true;
  diagram3DTVNewDataFlag = true;
  diagram3DSVChecked = false;
  hasError = false;
  errorMessage = '';
  constructor(trainID) {
    this.label = trainID;
    this.ref = trainID;
  }
}

export default {
  data() {
    return {
      pageState: LOADING_DATA,
      componentsLabel: {
        title: this.$t('components.summaryTitle'),
        placeholder: this.$t('components.trainFilterPlaceHolder'),
      },
      curGraphName: 'threeDiagram',
      tabs: ['threeDiagram', 'isopleth', 'reliefMap'],
      trainingJobId: this.$route.query.train_id, // ID of the current training job.
      summaryOperateList: [],
      curModeName: 0,
      originDataArr: [],
      oriDataDictionaries: {}, // Dictionary that contains all the current summary.
      curPageArr: [], // data list on the current page
      curFilterSamples: [], // List of data that meet the current filter criteria.
      multiSelectedSummaryNames: {}, // Dictionary for storing the name of the selected summarys.
      cacheStatus: 'CACHING', // cache
      pageNum: 3,
      isReloading: false, // Manually refresh
      colorValue: 0,
      colorOptions: [
        {
          value: 0,
          label: 'Jet',
        },
        {
          value: 1,
          label: 'Viridis',
        },
        {
          value: 2,
          label: 'RdBu',
        },
      ],
      collapse: false,
      // map
      diagramMapSetting: {
        showColorBar: false,
        mapColor: commonProperty.lossColorscale[0],
      },
      diagramMapBtnShow: {
        playBtnShow: false,
        downloadBtn: false,
        fitScreenBtn: true,
        fullScreenBtn: false,
        topBtnShow: true,
        noBoxSelect: false,
      },
      // 3d
      diagram3DMaintoolsShow: {
        download: true,
        fit: true,
      },
      diagram3DMintoolsShow: {
        fit: true,
        convergencePoint: true,
      },
      diagram3DSetting: {
        camera: JSON.parse(JSON.stringify(commonProperty.lossCommonStyle.camera)),
        light: JSON.parse(JSON.stringify(commonProperty.lossCommonStyle.light)),
        line: JSON.parse(JSON.stringify(commonProperty.lossCommonStyle.line)),
        opacity: JSON.parse(JSON.stringify(commonProperty.lossCommonStyle.opacity)),
        surface: {
          colorscale: JSON.parse(JSON.stringify(commonProperty.lossColorscale[0])),
        },
      },
      charResizeTimer: null,
      diagram3DSVCheckLimit: 2,
      diagram3DSVCheckCount: 0,
      eleResizeDetector: null,
      detailsDialogVisible: false,
      detailsDataTitle: '',
      detailsMetricList: {},
      lineNumoptions: [
        { value: 10, label: 10 },
        { value: 20, label: 20 },
        { value: 30, label: 30 },
      ],
      contourSetting: {
        contoursNumber: 20,
        contourColors: commonProperty.lossColorscale[0],
      },
    };
  },
  computed: {
    isReload() {
      return this.$store.state.isReload;
    },
  },
  watch: {
    isReload(newVal, oldVal) {
      if (newVal) {
        this.isReloading = true;
        this.updateAllData(false);
      }
    },
  },
  beforeDestroy() {
    try {
      this.eleResizeDetector.removeListener(this.$refs.compareContent, this.resizeCallback);
    } catch {}
  },
  destroyed() {
    this.$store.commit('setActiveTabName', '');
    if (this.isReloading) {
      this.$store.commit('setIsReload', false);
      this.isReloading = false;
    }
    if (this.charResizeTimer) {
      clearTimeout(this.charResizeTimer);
      this.charResizeTimer = null;
    }
  },
  mounted() {
    document.title = `${this.$t('summaryManage.comparePlate')}-MindInsight`;
    this.$nextTick(() => {
      this.getSummaryList();
    });
    this.eleResizeDetector = elementResizeDetectorMaker();
  },
  methods: {
    getSummaryList() {
      const params = {
        offset: 0,
        limit: 999,
      };
      requestService
        .querySummaryList(params)
        .then((res) => {
          if (res.data?.train_jobs.length <= 0) {
            this.pageState = NO_DATA;
            return;
          }
          const tempSummaryList = [];
          const dataList = [];
          const data = res.data.train_jobs;
          data.forEach((summaryObj, summaryIndex) => {
            const trainID = summaryObj.train_id;
            if (!this.oriDataDictionaries[trainID]) {
              this.oriDataDictionaries[trainID] = true;
              tempSummaryList.push({
                label: trainID,
                checked: true,
                show: true,
                ref: trainID,
              });

              if (summaryObj.cache_status === this.cacheStatus) {
                tempSummaryList.forEach((item) => {
                  if (item.label === trainID) {
                    item.loading = true;
                  }
                });
              }

              dataList.push(new DataItem(trainID));
            }
          });
          this.summaryOperateList = tempSummaryList;
          this.originDataArr = dataList;

          this.$nextTick(() => {
            this.eleResizeDetector.listenTo(this.$refs.compareContent, this.resizeCallback);
            this.multiSelectedSummaryNames = this.$refs.multiselectGroupComponents.updateSelectedDic();
            this.updateSummaryInPage();
            if (Object.keys(this.multiSelectedSummaryNames).length > 0) {
              this.trainJobsCaches();
            }
          });
        }, this.requestErrorCallback)
        .catch((e) => {
          this.$message.error(this.$t('public.dataError'));
        });
    },
    trainJobsCaches() {
      const params = {
        train_ids: Object.keys(this.multiSelectedSummaryNames),
      };
      requestService.trainJobsCaches(params);
    },

    /**
     * error
     * @param {Object} error error object
     */
    requestErrorCallback(error) {
      if (this.isReloading) {
        this.$store.commit('setIsReload', false);
        this.isReloading = false;
      }
      if (error.response && error.response.data) {
        this.clearAllData();
      }
    },
    /**
     * Clear data
     */
    clearAllData() {
      this.multiSelectedSummaryNames = {};
      this.curFilterSamples = [];
      this.summaryOperateList = [];
      this.originDataArr = [];
      this.curPageArr = [];
      this.oriDataDictionaries = {};
    },
    mapLineNumChange() {
      this.updateView();
    },
    /**
     * Update all data.
     * @param {Boolean} ignoreError whether ignore error tip
     */
    updateAllData(ignoreError) {
      const params = {
        offset: 0,
        limit: 999,
      };
      requestService
        .querySummaryList(params, ignoreError)
        .then((res) => {
          if (this.isReloading) {
            this.$store.commit('setIsReload', false);
            this.isReloading = false;
          }

          // Fault tolerance processing
          if (res.data?.train_jobs.length <= 0) {
            this.clearAllData();
            return;
          }
          const data = res.data.train_jobs;

          // Delete the data that does not exist
          const removeFlag = this.removeNonexistentData(data);

          // Check whether new data exists and add it to the page
          const addFlag = this.checkNewDataAndComplete(data);

          this.$nextTick(() => {
            this.multiSelectedSummaryNames = this.$refs.multiselectGroupComponents.updateSelectedDic();
            this.$refs.multiselectGroupComponents.$forceUpdate();

            this.updateSummaryInPage(!removeFlag && !addFlag);
            if (Object.keys(this.multiSelectedSummaryNames).length > 0) {
              this.trainJobsCaches();
            }
          });
        }, this.requestErrorCallback)
        .catch((e) => {
          this.$message.error(this.$t('public.dataError'));
        });
    },
    removeNonexistentData(oriData) {
      if (!oriData) {
        return false;
      }
      const newSummaryDictionaries = {};
      let dataRemoveFlag = false;
      oriData.forEach((summaryObj) => {
        newSummaryDictionaries[summaryObj.train_id] = true;
      });
      const oldTagListLength = this.summaryOperateList.length;
      for (let i = oldTagListLength - 1; i >= 0; i--) {
        if (!newSummaryDictionaries[this.summaryOperateList[i].label]) {
          dataRemoveFlag = true;
          delete this.oriDataDictionaries[this.summaryOperateList[i].label];
          this.summaryOperateList.splice(i, 1);
        }
      }
      const oldSampleLength = this.originDataArr.length;
      for (let i = oldSampleLength - 1; i >= 0; i--) {
        const oldSample = this.originDataArr[i];
        if (!newSummaryDictionaries[oldSample.label]) {
          dataRemoveFlag = true;
          this.originDataArr.splice(i, 1);
        }
      }
      return dataRemoveFlag;
    },
    checkNewDataAndComplete(oriData) {
      if (!oriData) {
        return false;
      }
      let dataAddFlag = false;
      oriData.forEach((summaryObj) => {
        const trainID = summaryObj.train_id;
        if (!this.oriDataDictionaries[trainID]) {
          this.oriDataDictionaries[trainID] = true;
          this.summaryOperateList.push({
            label: trainID,
            checked: true,
            show: true,
            ref: trainID,
          });
          this.originDataArr.push(new DataItem(trainID));
          if (!dataAddFlag) dataAddFlag = true;
        }
      });
      return dataAddFlag;
    },
    /**
     * The graph type is changed
     * @param {Number} val Current type
     */
    viewGraphChange(val) {
      this.$store.commit('setActiveTabName', val);
      this.updateView();
      this.$nextTick(() => {
        this.resizeCallback();
      });
    },
    /**
     * The display mode is changed
     * @param {Number} val Current mode
     */
    viewModeChange(val) {
      this.updateView();
    },
    /**
     * The color style is changed
     */
    colorChange() {
      const colors = commonProperty.lossColorscale[this.colorValue];
      this.contourSetting.contourColors = colors;
      this.diagram3DSetting.surface.colorscale = colors;
      this.restyleView();
    },
    /**
     * Update the data list based on the filtered tags
     * @param {Boolean} noPageDataNumChange No new data is added or deleted
     */
    updateSummaryInPage(noPageDataNumChange) {
      const curFilterSamples = [];
      // Obtains data subscript that meets the tag filtering conditions
      this.originDataArr.forEach((sampleItem) => {
        if (this.multiSelectedSummaryNames[sampleItem.label]) {
          curFilterSamples.push(sampleItem);
        }
      });
      this.curFilterSamples = curFilterSamples;
      // Obtains data on the current page
      this.getCurPageDataArr(noPageDataNumChange);
    },
    /**
     * The selected label is changed.
     * @param {Object} selectedItemDict Dictionary containing the selected summary
     */
    summarySelectedChanged(selectedItemDict) {
      if (!selectedItemDict) {
        return;
      }
      this.multiSelectedSummaryNames = selectedItemDict;
      if (Object.keys(this.multiSelectedSummaryNames).length > 0) {
        this.trainJobsCaches();
      }
      this.updateSummaryInPage();
    },
    /**
     * Obtains data on the current page
     * @param {Boolean} noPageDataNumChange No new data is added or deleted
     */
    getCurPageDataArr(noPageDataNumChange) {
      // Clear the previous page
      if (!noPageDataNumChange) {
        this.curPageArr.forEach((sampleItem) => {
          sampleItem.show = false;
        });
      }
      const curPageArr = [];
      for (let i = 0; i < this.pageNum && i < this.curFilterSamples.length; i++) {
        const sampleItem = this.curFilterSamples[i];
        if (sampleItem) {
          sampleItem.show = true;
          curPageArr.push(sampleItem);
        }
      }
      if (this.curGraphName === 'threeDiagram' && this.curModeName && curPageArr.length < this.curPageArr.length) {
        this.curPageArr.forEach((item) => {
          const findItem = curPageArr.find((k) => {
            return k.label === item.label;
          });
          if (findItem === undefined) {
            if (item.diagram3DSVChecked) {
              item.diagram3DSVChecked = false;
              this.diagram3DSVCheckCount--;
              setTimeout(() => {
                if (this.$refs.mixedDiagram3D) {
                  this.$refs.mixedDiagram3D.removeData(item.label);
                }
              }, 0);
            }
          }
        });
      }
      this.curPageArr = curPageArr;
      // Update the data information on the current page
      if (this.curPageArr.length) {
        this.freshCurPageData();
      }
    },
    /**
     * Refresh the data on the current page
     */
    freshCurPageData() {
      const trainIds = [];
      this.curPageArr.forEach((sampleItem) => {
        if (sampleItem.label) {
          trainIds.push(encodeURIComponent(sampleItem.label));
        }
      });

      const params = {
        train_id: trainIds.join('&'),
        type: 'final',
        metadata: true,
      };

      requestService.queryLossGraph(params).then((res) => {
        const landscapes = res.data.landscapes;
        if (!landscapes) return;

        landscapes.forEach((landscape) => {
          const sampleItem = this.curPageArr.find((item) => {
            return item.label === landscape.train_id;
          });
          if (sampleItem !== undefined) {
            if (landscape.hasOwnProperty('error_code')) {
              sampleItem.hasError = true;
              sampleItem.errorMessage = this.$t(`error.${landscape['error_code']}`);
              return;
            } else {
              sampleItem.hasError = false;
            }
            sampleItem.diagram3DSVNewDataFlag = true;
            sampleItem.diagram3DTVNewDataFlag = true;
            sampleItem.fullData = landscape;

            const { info, showMetric } = sampleItem;
            info.network = landscape.metadata.network ?? '--';
            info.optimizer = landscape.metadata.optimizer ?? '--';
            info.learning_rate = landscape.metadata.learning_rate ?? '--';
            info.metric = landscape.metadata.metric ?? {};
            info.loss = landscape.convergence_point === '' || landscape.convergence_point === null || !landscape.convergence_point instanceof Array
              ? '--' : landscape.convergence_point[2];
            const keys = Object.keys(info.metric);
            if (keys.length) {
              showMetric.label = keys[0];
              showMetric.value = info.metric[keys[0]];
            }
          }
        });
        this.updateView();
      });
    },
    /**
     *
     */
    updateView() {
      let prefix = this.curGraphName;
      if (this.curGraphName === 'threeDiagram') {
        let curNewDataKey = '';
        if (this.curModeName) {
          prefix += 'mixed';
          curNewDataKey = 'diagram3DSVNewDataFlag';
          if (this.$refs.mixedDiagram3D) {
            this.$refs.mixedDiagram3D.resize();
          }
        } else {
          curNewDataKey = 'diagram3DTVNewDataFlag';
        }
        this.curPageArr.forEach((sampleItem) => {
          if (!sampleItem.hasError) {
            const elementItem = this.$refs[prefix + sampleItem.ref];
            if (elementItem && elementItem[0]) {
              setTimeout(() => {
                elementItem[0].updateView(sampleItem[curNewDataKey]);
              }, 0);
              sampleItem[curNewDataKey] = false;
            }
          }
        });
      } else {
        this.curPageArr.forEach((sampleItem) => {
          const elementItem = this.$refs[prefix + sampleItem.ref];
          if (elementItem && elementItem[0]) {
            setTimeout(() => {
              elementItem[0].handleDataChange(sampleItem.fullData, this.contourSetting);
            }, 0);
          }
        });
      }
    },
    restyleView() {
      let prefix = this.curGraphName;
      if (this.curGraphName === 'threeDiagram' && this.curModeName) {
        prefix += 'mixed';
      }
      if (this.curGraphName === 'threeDiagram') {
        this.curPageArr.forEach((sampleItem) => {
          const elementItem = this.$refs[prefix + sampleItem.ref];
          if (elementItem && elementItem[0]) {
            elementItem[0].restyleView();
          }
        });
      } else {
        this.curPageArr.forEach((sampleItem) => {
          const elementItem = this.$refs[prefix + sampleItem.ref];
          if (elementItem && elementItem[0]) {
            setTimeout(() => {
              elementItem[0].handleContourColorsChange(this.contourSetting);
            });
          }
        });
      }
    },
    activeCheck(item) {
      if (item.hasError) {
        return;
      }
      if (item.diagram3DSVChecked) {
        item.diagram3DSVChecked = false;
        this.diagram3DSVCheckCount--;
        setTimeout(() => {
          if (this.$refs.mixedDiagram3D) {
            this.$refs.mixedDiagram3D.removeData(item.label);
          }
        }, 0);
      } else {
        if (this.diagram3DSVCheckCount >= this.diagram3DSVCheckLimit) {
          return;
        }
        item.diagram3DSVChecked = true;
        this.diagram3DSVCheckCount++;
        setTimeout(() => {
          if (this.$refs.mixedDiagram3D) {
            this.$refs.mixedDiagram3D.addData(item.fullData);
          }
        }, 0);
      }
    },
    resizeCallback() {
      if (this.charResizeTimer) {
        clearTimeout(this.charResizeTimer);
        this.charResizeTimer = null;
      }

      if (this.curGraphName === 'threeDiagram') {
        this.charResizeTimer = setTimeout(() => {
          let prefix = this.curGraphName;
          if (this.curModeName) {
            prefix += 'mixed';
            if (this.$refs.mixedDiagram3D) {
              this.$refs.mixedDiagram3D.resize();
            }
          }
          this.curPageArr.forEach((sampleItem) => {
            const elementItem = this.$refs[prefix + sampleItem.ref];
            if (elementItem && elementItem[0]) {
              elementItem[0].resize();
            }
          });
        }, 500);
      } else {
        this.charResizeTimer = setTimeout(() => {
          const prefix = this.curGraphName;
          this.curPageArr.forEach((sampleItem) => {
            const elementItem = this.$refs[prefix + sampleItem.ref];
            if (elementItem && elementItem[0]) {
              elementItem[0].resize();
            }
          });
        }, 500);
      }
    },
    clickCollapse() {
      this.collapse = !this.collapse;
      if (this.$refs.mixedDiagram3D) {
        this.$refs.mixedDiagram3D.resize();
      }
    },
    showMetricDialog(item) {
      const val = JSON.stringify(item.info.metric);
      this.detailsDialogVisible = true;
      this.detailsDataTitle = item.label;
      this.detailsMetricList = this.formateJsonString(val);
    },
    formateJsonString(str) {
      if (!str) {
        return [];
      }
      const resultArr = [];
      const dataObj = JSON.parse(str);
      const keys = Object.keys(dataObj);
      keys.forEach((key, index) => {
        const tempData = {
          id: index + 1,
          hasChildren: false,
          key: key,
          value: '',
        };
        if (typeof dataObj[key] === this.objectType && dataObj[key] !== null) {
          if (!(dataObj[key] instanceof Array)) {
            tempData.hasChildren = true;
            tempData.children = [];
            Object.keys(dataObj[key]).forEach((k, j) => {
              const item = {};
              item.key = k;
              item.value = dataObj[key][k];
              item.id = `${new Date().getTime()}` + `${this.$store.state.tableId}`;
              this.$store.commit('increaseTableId');
              tempData.children.push(item);
            });
          }
          tempData.value = JSON.stringify(dataObj[key]);
        } else {
          tempData.value = dataObj[key];
        }
        resultArr.push(tempData);
      });
      return resultArr;
    },
  },
  components: {
    multiselectGroupComponents,
    contourMap,
    diagram3D,
    empty,
  },
};
</script>
<style scoped>
.loss-compare {
  height: 100%;
  background-color: var(--bg-color);
  display: grid;
  grid-template-rows: auto 1fr;
}
.loss-compare .inline-show {
  display: inline-block;
  vertical-align: middle;
}
.loss-compare .line-num-style {
  display: inline-block;
  padding-right: 10px;
  width: 120px;
}
.loss-compare .compare-tab {
  height: 56px;
  line-height: 56px;
  padding: 5px 24px 0 24px;
  font-size: 16px;
  font-weight: bold;
}
.loss-compare .compare-tab-item {
  padding: 0 10px;
  height: 48px;
  -webkit-box-sizing: border-box;
  box-sizing: border-box;
  line-height: 48px;
  display: inline-block;
  list-style: none;
  font-size: 18px;
  color: #303133;
  position: relative;
}
.loss-compare .item-active {
  color: var(--theme-color);
  font-weight: bold;
  border-bottom: 3px solid var(--theme-color);
}
.loss-compare .compare-tab-item:hover {
  color: var(--theme-color);
  cursor: pointer;
}
.loss-compare .compare-run {
  width: 100%;
  line-height: 32px;
}
.compare-run .select-all {
  display: flex;
  align-items: center;
}
.loss-compare .compare-graph {
  width: 100%;
  height: 50px;
}
.loss-compare .compare-graph .view-title {
  display: inline-block;
  margin-right: 15px;
}
.loss-compare .compare-graph .graph-radio {
  margin-right: 64px;
}
.loss-compare .compare-graph .color-style {
  float: right;
}
.loss-compare .compare-graph .color-style .color-select {
  display: inline-block;
  width: 120px;
  margin-right: 16px;
}
.loss-compare .compare-graph .color-style .color-legend-jet {
  margin-left: 5px;
  margin-right: 5px;
  width: 150px;
  height: 30px;
  background-image: linear-gradient(to right, maroon, red, yellow, #05ffff, #003caa, #000083);
}
.loss-compare .compare-graph .color-style .color-legend-viridis {
  margin-left: 5px;
  margin-right: 5px;
  width: 150px;
  height: 30px;
  background-image: linear-gradient(to right, #fde725, #b5de2b, #1f9e89, #26838e, #3e4979, #440154);
}
.loss-compare .compare-graph .color-style .color-legend-ruBu {
  margin-left: 5px;
  margin-right: 5px;
  width: 150px;
  height: 30px;
  background-image: linear-gradient(to right, #67001f, #d6604d, #fddbc7, #d1e5f0, #4393c3, #053061);
}
.loss-compare .compare-graph .color-style .conpoint {
  margin-right: 10px;
  height: 16px;
  width: 16px;
  margin-left: 16px;
  border-radius: 50%;
  background-color: var(--conpoint-color);
}
.loss-compare .compare-content {
  flex: 1;
  overflow: hidden;
}
.loss-compare .compare-content .data-content {
  display: flex;
  height: 100%;
  width: 100%;
  flex-wrap: wrap;
  min-height: 510px;
  position: relative;
}
.loss-compare .compare-content .data-content .sample-content {
  width: 33.3%;
  height: 510px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  background-color: var(--bg-color);
  position: relative;
  padding: 32px 9px 0 9px;
}
.loss-compare .compare-content .data-content .detail-container {
  width: 100%;
  height: 485px;
}
.loss-compare .compare-content .data-content .detail-container .chartdiv-container {
  height: 350px;
  background-color: var(--module-bg-color);
  padding: 15px;
  position: relative;
}
.chartdiv-container .error-message-container {
  text-align: center;
  margin-top: 150px;
}
.superimposedView-right-item .error-message-container {
  text-align: center;
  margin-top: 90px;
}
.loss-compare .compare-content .data-content .detail-container .info-container {
  height: 130px;
  margin-top: 5px;
  background-color: var(--module-bg-color);
  padding: 5px 15px 15px 15px;
}
.loss-compare .compare-content .data-content .detail-container .info-container .info-title {
  margin-top: 10px;
}
.loss-compare .compare-content .data-content .detail-container .info-container .info-title .view-more {
  float: right;
  color: var(--theme-color);
  font-size: 12px;
  margin-top: 3px;
  cursor: pointer;
}
.loss-compare .compare-content .data-content .detail-container .info-container .info-content {
  margin-top: 2px;
}
.loss-compare .compare-content .data-content .detail-container .info-container .info-content > div {
  display: inline-block;
  padding: 0 5px;
  border-right: 1px solid var(--border-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.loss-compare .compare-content .data-content .detail-container .info-container .info-content > div .res-net {
  color: var(--theme-color);
}
.loss-compare .compare-content .data-content .detail-container .info-container .info-content > div .label {
  margin-right: 2px;
}
.loss-compare .compare-content .data-content .detail-container .info-container .info-content > div:first-child {
  padding-left: 0;
}
.loss-compare .compare-content .data-content .detail-container .info-container .info-content > div:last-child {
  border-right: none;
}
.loss-compare .compare-content .data-content .detail-container .info-container .info-content .w33 {
  width: 33.3%;
}
.loss-compare .compare-content .data-content .summary-title {
  margin-top: 10px;
  width: 100%;
  font-size: 16px;
  font-weight: 600;
  text-align: center;
}
.loss-compare .compare-content .superimposedView {
  height: 100%;
  width: 100%;
  overflow: hidden;
  display: flex;
}
.loss-compare .compare-content .superimposedView .superimposedView-left {
  flex: 1;
  margin-right: 50px;
  background: #fafbfc;
  position: relative;
  overflow: hidden;
}
.loss-compare .compare-content .superimposedView .superimposedView-left .mixed-chart {
  border: 1px solid var(--border-color);
}
.loss-compare .compare-content .superimposedView .superimposedView-con {
  width: 26px;
  display: flex;
  align-items: center;
}
.loss-compare .compare-content .superimposedView .superimposedView-con .collapse-btn-0 {
  width: 26px;
  height: 92px;
  background: url('../../../assets/images/0/collapse-left.svg');
  transform: rotate(180deg);
  cursor: pointer;
}
.loss-compare .compare-content .superimposedView .superimposedView-con .collapse-btn-1 {
  width: 26px;
  height: 92px;
  background: url('../../../assets/images/1/collapse-left.svg');
  transform: rotate(180deg);
  cursor: pointer;
}
.loss-compare .compare-content .superimposedView .superimposedView-con .collapse-btn.collapse {
  background: url('../../../assets/images/0/collapse-right.svg');
}
.loss-compare .compare-content .superimposedView .superimposedView-con .collapse-btn.collapse {
  background: url('../../../assets/images/1/collapse-right.svg');
}
.loss-compare .compare-content .superimposedView .superimposedView-right {
  height: 100%;
  width: 374px;
  flex-direction: column;
  border-left: 1px solid var(--border-color);
  padding-left: 20px;
  padding-right: 24px;
}
.loss-compare .compare-content .superimposedView .superimposedView-right .superimposedView-right-item {
  border: 1px solid var(--el-input-border-color);
  margin-bottom: 10px;
  position: relative;
  cursor: pointer;
  height: calc(33% - 10px);
}
.loss-compare .superimposedView .superimposedView-right .superimposedView-right-item .superimposedView-right-float {
  display: none;
}
.loss-compare .compare-content .superimposedView .superimposedView-right .activeCheck {
  border: 1px solid var(--theme-color);
}
.loss-compare .compare-content .superimposedView .superimposedView-right .activeCheck .superimposedView-right-float {
  position: absolute;
  display: block;
  width: 20px;
  height: 20px;
  top: 0px;
  right: 0px;
  background-color: var(--theme-color);
  color: var(--bg-color);
  line-height: 20px;
  text-align: center;
}
.loss-compare .compare-content .superimposedView .superimposedView-right .activeDisabled {
  cursor: not-allowed;
}
.loss-compare .compare-content .image-noData {
  width: 100%;
  height: 450px;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}
.loss-compare .compare-content .noData-text {
  margin-top: 33px;
  font-size: 18px;
}
.loss-compare .chart-item-mask {
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
  opacity: 0;
  z-index: 9;
}
.loss-compare .chart-item-info {
  width: 100%;
  height: 55px;
  position: absolute;
  bottom: 0;
  left: 0;
  background-color: rgba(0, 0, 0, 0.4);
  z-index: 1;
}
.loss-compare .chart-item-info .info-content > div {
  display: inline-block;
  width: 50%;
  padding: 0 5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--bg-color);
}
.loss-compare .chart-item-info .info-content > div .label,
.loss-compare .chart-item-info .info-content > div .value {
  font-size: 12px;
}
.loss-compare .chart-item-info .info-content .w100 {
  width: 100%;
}
.loss-compare ::v-deep .details-metric-list .el-table td,
.loss-compare ::v-deep .details-metric-list .el-table th.is-leaf {
  border: none;
  border-top: 1px solid var(--border-color);
}
.loss-compare ::v-deep .details-metric-list .el-table th {
  padding: 10px 0;
  border-top: 1px solid var(--border-color);
  background: #f5f7fa;
}
.loss-compare ::v-deep .details-metric-list .el-table th .cell {
  border-left: 1px solid var(--border-color);
  height: 14px;
  line-height: 14px;
}
.loss-compare ::v-deep .details-metric-list .el-table th:first-child .cell {
  border-left: none;
}
.loss-compare ::v-deep .details-metric-list .el-table th:nth-child(2),
.loss-compare ::v-deep .details-metric-list .el-table td:nth-child(2) {
  width: 30%;
}
.loss-compare ::v-deep .details-metric-list .el-table td {
  padding: 8px 0;
}
.loss-compare ::v-deep .details-metric-list .el-dialog__title {
  font-weight: bold;
}
.loss-compare ::v-deep .details-metric-list .el-dialog__body {
  max-height: 500px;
  padding-top: 10px;
  overflow: auto;
}
.loss-compare .compare-content .info-container .info-title .cl-title-tip .tip-part {
  line-height: 20px;
  word-break: normal;
}
.loss-compare .compare-content .info-container .info-title .el-icon-info {
  color: #6c7280;
}
</style>

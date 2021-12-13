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
  <div class="mi-common-full-page cl-loss-analysis">
    <div class="cl-title-top">
      {{$t('lossAnalysis.titleText')}}
      <el-tooltip placement="right-start" 
                  effect="light">
        <div slot="content" 
              class="tooltip-container">
          <div class="cl-title-tip">
            <div class="tip-part">
              {{$t('lossAnalysis.dataToolTip')}}
            </div>
          </div>
        </div>
        <i class="el-icon-info"></i>
      </el-tooltip>
      <div class="cl-close-btn"
           @click="backToManage">
        <img src="@/assets/images/close-page.png">
      </div>
    </div>
    <div class="loss-analysis-content">
      <div class="table-container">
        <el-tabs v-model="activeTab"
                 @tab-click="tabClick">
          <el-tab-pane :label="$t('lossAnalysis.isopleth')"
                       :name="CONTOUR">
            <div class="detail">
              <contourMap :ref="CONTOUR"
                          :type="CONTOUR"
                          @fullScreen="handleFullScreen"
                          showLegend
                          showAnimation
                          showFullScreen>
              </contourMap>
            </div>
          </el-tab-pane>
          <el-tab-pane :label="$t('lossAnalysis.reliefMap')"
                       :name="TOPOGRAPHIC">
            <div class="detail">
              <contourMap :ref="TOPOGRAPHIC"
                          :type="TOPOGRAPHIC"
                          @fullScreen="handleFullScreen"
                          showLegend
                          showAnimation
                          showFullScreen>
              </contourMap>
            </div>
          </el-tab-pane>
          <el-tab-pane :label="$t('lossAnalysis.threeDiagram')"
                       :name="THREED">
            <div class="detail">
              <diagram3D :oriData="oriData"
                         :over="initOver"
                         :styleSetting="diagram3DSetting"
                         :componentConfigOptions='diagramConfigOptions'
                         @viewInfoChanged="diagramViewInfoChange"
                         @toggleFullScreen="handleFullScreen"
                         :ref="THREED"></diagram3D>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <div class="right"
           v-show="!isFullScreen">
        <div class="chart-container">
          <div class="title">{{$t('lossAnalysis.stepSelection')}}</div>
          <div id="commonChart"
               class="commonChart"
               v-show="chartObj"></div>
          <div class="commonChart"
               v-show="!chartObj">
            <div class="no-data-img">
              <div class="content">
                <img :src="require('@/assets/images/nodata.png')"
                     alt="" />
                <p class='no-data-text'>
                  {{$t("public.noData")}}
                </p>
              </div>
            </div>
          </div>
          <div class="centerPoint">
            {{$t('lossAnalysis.unit') + $t('symbols.colon') + chartInfo.unit}}
          </div>

          <div class="step-select">
            <span class="step-select-info">{{$t('lossAnalysis.intervalRange')}}</span>
            <el-select v-model="steps.value"
                       :placeholder="$t('public.select')"
                       @change="stepChange">
              <el-option v-for="(item,index) in steps.options"
                         :key="index"
                         :label="item.label"
                         :value="item.label">
              </el-option>
            </el-select>
          </div>
        </div>
        <div class="chart-setting">
          <div class="title">
            {{$t('lossAnalysis.visualSettings')}}
            <span class="el-icon-refresh-right right-icon"
                  @click="configRefresh"></span>
          </div>
          <!-- Contour Map -->
          <div class="setting-detail"
               v-show="activeTab === CONTOUR">
            <div class="setting-item">
              <div class="label">{{$t('lossAnalysis.mapColorSelection')}}</div>
              <div class="content">
                <el-select v-model="contourSetting.colorsIndex"
                           @change="onContourColorsChange"
                           :placeholder="$t('public.select')">
                  <el-option v-for="item in colorOptions"
                             :key="item.label"
                             :label="item.label"
                             :value="item.value">
                  </el-option>
                </el-select>
              </div>
            </div>
            <div class="setting-item">
              <div class="label">{{$t('lossAnalysis.pathCurve')}}</div>
              <div class="content">
                <el-color-picker v-model="contourSetting.pathColor"
                                 size="mini"
                                 @change="onPathStyleChange(CONTOUR)">
                </el-color-picker>
                <div class="tip">{{$t('lossAnalysis.lineColor')}}</div>
                <el-select v-model="contourSetting.pathWidth"
                           class="line-width"
                           @change="onPathStyleChange(CONTOUR)">
                  <el-option v-for="item in lineWidthOptions"
                             :key="item"
                             :label="item"
                             :value="item">
                  </el-option>
                </el-select>
                <div class="tip">{{$t('lossAnalysis.lineWidth')}}</div>
              </div>
            </div>
            <div class="setting-item">
              <div class="line-num-title">{{$t('lossAnalysis.setLineNum')}}</div>
              <el-select v-model="contourSetting.contoursNumber"
                         :placeholder="$t('public.select')"
                         @change="onContoursNumberChange(CONTOUR)"
                         class="line-select-style">
                <el-option v-for="item in mapLineNumoptions"
                           :key="item.value"
                           :label="item.label"
                           :value="item.value">
                </el-option>
              </el-select>
            </div>
          </div>
          <!-- Topographic Map -->
          <div class="setting-detail"
               v-show="activeTab === TOPOGRAPHIC">
            <div class="setting-item">
              <div class="label">{{$t('lossAnalysis.mapColorSelection')}}</div>
              <div class="content">
                <el-select v-model="topographicSetting.colorsIndex"
                           @change="onContourColorsChange"
                           :placeholder="$t('public.select')">
                  <el-option v-for="item in colorOptions"
                             :key="item.label"
                             :label="item.label"
                             :value="item.value">
                  </el-option>
                </el-select>
              </div>
            </div>
            <div class="setting-item">
              <div class="label">{{$t('lossAnalysis.pathCurve')}}</div>
              <div class="content">
                <el-color-picker v-model="topographicSetting.pathColor"
                                 size="mini"
                                 @change="onPathStyleChange(TOPOGRAPHIC)">
                </el-color-picker>
                <div class="tip">{{$t('lossAnalysis.lineColor')}}</div>
                <el-select v-model="topographicSetting.pathWidth"
                           class="line-width"
                           @change="onPathStyleChange(TOPOGRAPHIC)">
                  <el-option v-for="item in lineWidthOptions"
                             :key="item"
                             :label="item"
                             :value="item">
                  </el-option>
                </el-select>
                <div class="tip">{{$t('lossAnalysis.lineWidth')}}</div>
              </div>
            </div>
            <div class="setting-item">
              <div class="line-num-title">{{$t('lossAnalysis.setLineNum')}}</div>
              <el-select v-model="topographicSetting.contoursNumber"
                         :placeholder="$t('public.select')"
                         @change="onContoursNumberChange(TOPOGRAPHIC)"
                         class="line-select-style">
                <el-option v-for="item in mapLineNumoptions"
                           :key="item.value"
                           :label="item.label"
                           :value="item.value">
                </el-option>
              </el-select>
            </div>
          </div>
          <!-- 3D -->
          <div class="setting-detail"
               v-show="activeTab === 'threeDiagram'">
            <div class="setting-item mini">
              <div class="label">{{$t('lossAnalysis.surfaceTransparency')}}</div>
              <div class="content">
                <div class="slider-label"></div>
                <el-slider v-model="diagram3DSetting.opacity"
                           :min="sliderOptions.startStep"
                           :max="sliderOptions.endOpacity"
                           :step="sliderOptions.commStep"
                           @input="diagramSettingChange"
                           class="slider">
                </el-slider>
                <div class="slider-value">{{diagram3DSetting.opacity}}</div>
              </div>
            </div>
            <div class="setting-item mini">
              <div class="label">{{$t('lossAnalysis.lightIntensity')}}</div>
              <div class="content">
                <div class="slider-label"></div>
                <el-slider v-model="diagram3DSetting.light.intensity"
                           :min="sliderOptions.startStep"
                           :max="sliderOptions.endIntensity"
                           :step="sliderOptions.commStep"
                           @input="diagramSettingChange"
                           class="slider">
                </el-slider>
                <div class="slider-value">{{diagram3DSetting.light.intensity}}</div>
              </div>
            </div>

            <div class="setting-item mini">
              <div class="label vertical-top">{{$t('lossAnalysis.illuminationPoint')}}</div>
              <div class="content">
                <div class="slider-label">{{$t('lossAnalysis.alpha')}}</div>
                <el-slider v-model="diagram3DSetting.light.alpha"
                           :min="sliderOptions.startAngle"
                           :max="sliderOptions.endAngle"
                           :step="sliderOptions.angleStep"
                           @input="diagramSettingChange"
                           class="slider">
                </el-slider>
                <div class="slider-value">{{diagram3DSetting.light.alpha}}</div>
                <div class="slider-label">{{$t('lossAnalysis.beta')}}</div>
                <el-slider v-model="diagram3DSetting.light.beta"
                           :min="sliderOptions.startAngle"
                           :max="sliderOptions.endAngle"
                           :step="sliderOptions.angleStep"
                           @input="diagramSettingChange"
                           class="slider">
                </el-slider>
                <div class="slider-value">{{diagram3DSetting.light.beta}}</div>
              </div>
            </div>

            <div class="setting-item mini">
              <div class="label">{{$t('lossAnalysis.cameraPosition')}}</div>
              <div class="content">
                <div class="param">x{{$t('symbols.colon') + diagramViewInfo.eye.x}}</div>
                <div class="param">y{{$t('symbols.colon') + diagramViewInfo.eye.y}}</div>
                <div class="param">z{{$t('symbols.colon') + diagramViewInfo.eye.z}}</div>
              </div>
            </div>

            <div class="setting-item mini">
              <div class="label">{{$t('lossAnalysis.cameraRotationAngle')}}</div>
              <div class="content">
                <div class="param">{{$t('lossAnalysis.alpha') +
                  $t('symbols.colon') +
                  diagramViewInfo.angle.alpha}}</div>
                <div class="param">{{$t('lossAnalysis.beta') +
                  $t('symbols.colon') +
                  diagramViewInfo.angle.beta}}</div>
                <div class="param">{{$t('lossAnalysis.distance') + $t('symbols.colon') +
                  diagramViewInfo.angle.distance}}</div>
              </div>
            </div>
            <div class="setting-item">
              <div class="label">{{$t('lossAnalysis.mapColorSelection')}}</div>
              <div class="content">
                <el-select v-model="diagram3DSetting.surface.colorScaleIndex"
                           @change="diagramSettingChange"
                           :placeholder="$t('public.select')">
                  <el-option v-for="item in colorOptions"
                             :key="item.value"
                             :label="item.label"
                             :value="item.value">
                  </el-option>
                </el-select>
              </div>
            </div>
            <div class="setting-item">
              <div class="label">{{$t('lossAnalysis.pathCurve')}}</div>
              <div class="content">
                <el-color-picker v-model="diagram3DSetting.line.color"
                                 @change="diagramSettingChange"
                                 size="mini">
                </el-color-picker>
                <div class="tip">{{$t('lossAnalysis.lineColor')}}</div>
                <el-select v-model="diagram3DSetting.line.width"
                           @change="diagramSettingChange"
                           class="line-width">
                  <el-option v-for="item in chartSetting.isopleth.lineWidth.options"
                             :key="item"
                             :label="item"
                             :value="item">
                  </el-option>
                </el-select>
                <div class="tip">{{$t('lossAnalysis.lineWidth')}}</div>
              </div>
            </div>

          </div>
        </div>
        <div class="chart-info">
          <div class="title">
            {{$t('lossAnalysis.basicTrainingInfo')}}
            <el-tooltip placement="bottom-end" 
                        effect="light">
              <div slot="content" 
                  class="tooltip-container">
                <div class="cl-title-tip">
                  <div class="tip-part">
                    {{$t('lossAnalysis.basicTrainingTip')}}
                  </div>
                </div>
              </div>
              <i class="el-icon-info"></i>
            </el-tooltip>
          </div>
          <div class="chart-info-item">
            <div class="chart-info-item-left">{{$t('lossAnalysis.network')}}{{$t('symbols.colon')}}</div>
            <div class="chart-info-item-right">{{chartInfo.network || '--'}}</div>
          </div>
          <div class="chart-info-item">
            <div class="chart-info-item-left">{{$t('lossAnalysis.optimizer')}}{{$t('symbols.colon')}}</div>
            <div class="chart-info-item-right">{{chartInfo.optimizer || '--'}}</div>
          </div>
          <div class="chart-info-item">
            <div class="chart-info-item-left">{{$t('lossAnalysis.learning_rate')}}{{$t('symbols.colon')}}</div>
            <div class="chart-info-item-right">{{isNaN(chartInfo.learning_rate) || chartInfo.learning_rate === null ? '--' : chartInfo.learning_rate}}</div>
          </div>
          <div class="chart-info-item">
            <div class="chart-info-item-left">{{$t('lossAnalysis.decomposition')}}{{$t('symbols.colon')}}</div>
            <div class="chart-info-item-right">{{chartInfo.decomposition || '--'}}</div>
          </div>
          <div class="chart-info-item">
            <div class="chart-info-item-left">{{$t('lossAnalysis.ratio')}}{{$t('symbols.colon')}}</div>
            <div class="chart-info-item-right">{{chartInfo.ratio || '--'}}</div>
          </div>
          <div class="chart-info-item">
            <div class="chart-info-item-left">{{$t('lossAnalysis.step_per_epoch')}}{{$t('symbols.colon')}}</div>
            <div class="chart-info-item-right">{{chartInfo.step_per_epoch ? chartInfo.step_per_epoch+'/1' : '--'}}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import RequestService from '../../services/request-service';
import echarts, {echartsThemeName} from '@/js/echarts';
import contourMap from '../../components/contour-map.vue';
import diagram3D from '../../components/diagram-3D.vue';
import commonProperty from '../../common/common-property';

const CONTOUR = 'contour';

const TOPOGRAPHIC = 'topographic';

const THREED = 'threeDiagram';

export default {
  data() {
    return {
      activeTab: THREED,
      CONTOUR,
      TOPOGRAPHIC,
      THREED,
      trainInfo: {
        id: '',
        path: '',
      },
      initOver: false,
      oriData: {},
      resizeTimer: null,
      colorOptions: commonProperty.colorOptions, // Color scheme options
      chartOption: {},
      chartObj: null,
      steps: {
        options: [],
        value: '',
        id: '',
      },
      chartSetting: {
        isopleth: {
          color: 'black',
          lineWidth: {
            options: [1, 2, 3, 4, 5],
            value: 1,
          },
        },
        reliefMap: {},
      },
      // Contour value
      mapContour: 'lines',
      mapTopographic: '',
      firstIsopleth: true,
      firstReliefMap: true,
      mapbtnShow: {
        playBtnShow: true,
        downloadBtn: true,
        fitScreenBtn: true,
        fullScreenBtn: true,
        // Show restore button
        topBtnShow: true,
        // Non Frameable function
        noBoxSelect: false,
      },
      pathColor: '#00a5a7',
      pathStyle: {lineColor: '#000', lineWidth: '5'},
      // Whether the gradient color and color bar of 2D contour map display settings
      mapStyle: {
        showColorBar: true,
        mapColor: commonProperty.lossColorscale[0],
      },
      // Isoline 1
      isoplethColorData: {
        colorValue: 0,
        // Path object settings
        pathColor: '#000',
        lineWidthValue: 5,
      },
      lineWidthOptions: [1, 2, 3, 4, 5],
      // Topographic map 2
      reliefMapColorData: {
        colorValue: 0,
        // Path object settings
        pathColor: '#000',
        lineWidthValue: 5,
      },
      colorscaleList: commonProperty.lossColorscale,
      // 3d
      diagramSliderChangeTimer: null,
      sliderOptions: {
        startAngle: -180,
        endAngle: 180,
        angleStep: 1,
        endOpacity: 1,
        commStep: 0.1,
        endIntensity: 2,
        startStep: 0,
        endStepMin: 1,
        endStepmid: 4,
        perStepMin: 0.01,
      },
      diagramConfigOptions: {
        cameraInfo: true,
        download: true,
        fit: true,
        fullScreen: true,
        playButton: true,
        colorBar: true,
      },
      diagram3DSetting: {
        camera: JSON.parse(
            JSON.stringify(commonProperty.lossCommonStyle.camera),
        ),
        light: JSON.parse(JSON.stringify(commonProperty.lossCommonStyle.light)),
        line: JSON.parse(JSON.stringify(commonProperty.lossCommonStyle.line)),
        opacity: JSON.parse(
            JSON.stringify(commonProperty.lossCommonStyle.opacity),
        ),
        surface: {
          colorscale: JSON.parse(
              JSON.stringify(commonProperty.lossColorscale[0]),
          ),
          colorScaleIndex: 0,
        },
      },
      diagramViewInfo: {
        eye: {
          x: commonProperty.lossCommonStyle.camera.centerX,
          y: commonProperty.lossCommonStyle.camera.centerY,
          z: commonProperty.lossCommonStyle.camera.centerZ,
        },
        angle: {
          alpha: 0,
          beta: 0,
          distance: 0,
        },
      },
      chartInfo: {
        decomposition: '',
        learning_rate: '',
        network: '',
        optimizer: '',
        ratio: '',
        unit: '',
        step_per_epoch: '',
      },
      isFullScreen: false,
      threeDiagramSetting: {
        needResize: false,
        dataChanged: false,
      },
      contourSetting: {
        needResize: false,
        dataChanged: false,
        unit: '',
        type: CONTOUR,
        pathColor: '#000000',
        pathWidth: 5,
        contoursNumber: 10,
        colorsIndex: 0,
        contourColors: commonProperty.lossColorscale[0],
      },
      topographicSetting: {
        needResize: false,
        dataChanged: false,
        unit: '',
        type: TOPOGRAPHIC,
        pathColor: '#000000',
        pathWidth: 5,
        contoursNumber: 10,
        colorsIndex: 0,
        contourColors: commonProperty.lossColorscale[0],
      },
      mapLineNumoptions: new Array(15).fill(null).map((_, index) => {
        const value = (index + 2) * 5;
        return {value, label: value};
      }),
    };
  },
  mounted() {
    const id = this.$route.query.train_id;
    if (!id) {
      this.$message.error(this.$t('trainingDashboard.invalidId'));
      document.title = `${this.$t('lossAnalysis.titleText')}-MindInsight`;
      return;
    }
    document.title = `${this.trainInfo.id}-${this.$t('lossAnalysis.titleText')}-MindInsight`;
    this.trainInfo.id = id;
    this.$nextTick(() => {
      this.init();
    });
    window.addEventListener('resize', this.resizeCallback);
  },
  destroyed() {
    window.removeEventListener('resize', this.resizeCallback);
  },
  methods: {
    init() {
      this.getEpochIntervals();
    },
    backToManage() {
      this.$router.push({
        path: '/train-manage/training-dashboard',
        query: {
          id: this.trainInfo.id,
        },
      });
    },
    /**
     * get Epoch Intervals
     */
    getEpochIntervals() {
      const id = this.trainInfo.id;
      const params = {
        train_id: id,
      };
      RequestService.queryEpochIntervals(params).then(
          (res) => {
            if (!res.data) {
              this.initOver = true;
              return;
            }
            const resArr = res.data.intervals;
            if (Array.isArray(resArr) && resArr.length) {
              resArr.forEach((item) => {
                const label = `${item.value[0]}-${item.value[1]}`;
                item.label = label;
              });

              this.steps.options = resArr;
              this.steps.value = resArr[0].label;
              this.steps.id = resArr[0].id;

              const params = {
                train_id: id,
                type: 'interval',
                metadata: true,
                interval_id: this.steps.id,
              };
              this.getDataOfLossGraph(params);
              this.initCommonChart();
            }
          },
          () => {
            this.initOver = true;
            this.steps.value = '';
            this.steps.id = '';
            this.steps.options = [];
            if (this.chartObj) {
              this.chartObj.clear();
              this.chartObj = null;
            }
            this.chartOption = {};
            this.chartInfo = {};
          },
      );
    },
    /**
     * Call the lossGraph interface to obtain topographic map and 3D map data
     * @param {Object} params Request parameter
     */
    getDataOfLossGraph(params) {
      RequestService.queryLossGraph(params).then(
          (resp) => {
            if (resp && resp.data) {
              if (resp.data.landscapes && resp.data.landscapes.length) {
                const lossdata = JSON.parse(
                    JSON.stringify(resp.data.landscapes[0]),
                );
                if (lossdata.convergence_point) {
                  lossdata.convergence_point = null;
                }
                let ratio = '';
                for (const key in lossdata.points) {
                  if (lossdata.points.hasOwnProperty(key)) {
                    ratio += lossdata.points[key].length + 'x';
                  }
                }
                ratio = ratio.slice(0, -1);
                this.oriData = lossdata;
                this.chartInfo = lossdata.metadata;
                this.chartInfo.ratio = ratio;
                const unit = lossdata.metadata.unit;
                this.contourSetting.unit = unit;
                this.topographicSetting.unit = unit;
                this.$nextTick(() => {
                  if (this.chartOption.series) {
                    this.formatMarkArea(this.chartOption.series[0]);
                    this.chartObj.setOption(this.chartOption, false);
                  }
                  this.updateTabsChart();
                });
              }
            } else {
              this.initOver = true;
            }
          },
          (error) => {
            this.oriData = {};
            this.chartInfo = {};
            this.initOver = true;
          },
      );
    },

    // ---------------------------------------------  Tabs chart about --------------------------------------------- //

    /**
     * Resizing Chart in tabs
     */
    resizeTabChart() {
      const activeRefName = this.activeTab;
      [CONTOUR, TOPOGRAPHIC, THREED].forEach((refName) => {
        if (refName === activeRefName) {
          this.$refs[activeRefName].resize();
        } else {
          this[`${refName}Setting`].needResize = true;
        }
      });
    },
    /**
     * Callback of resize event listener
     */
    resizeCallback() {
      this.resizeTimer && clearTimeout(this.resizeTimer);
      this.resizeTimer = setTimeout(() => {
        this.resizeTabChart();
        this.resizeTimer = null;
      }, 300);
    },
    handleFullScreen() {
      this.isFullScreen = !this.isFullScreen;
      this.$nextTick(() => {
        this.resizeTabChart();
      });
    },
    updateTabChart(refName) {
      const setting = this[`${refName}Setting`];
      if (refName === THREED) {
        this.$refs[refName].updateView();
      } else {
        this.$refs[refName].handleDataChange(this.oriData, setting);
      }
      setting.dataChanged = false;
    },
    updateTabsChart() {
      const activeRefName = this.activeTab;
      [CONTOUR, TOPOGRAPHIC, THREED].forEach((refName) => {
        if (refName === activeRefName) {
          this.updateTabChart(activeRefName);
        } else {
          this[`${refName}Setting`].dataChanged = true;
        }
      });
    },
    tabClick(tab) {
      const activeRefName = tab.name;
      const setting = this[`${activeRefName}Setting`];
      this.$nextTick(() => {
        if (setting.needResize) {
          this.$refs[activeRefName].resize();
          setting.needResize = false;
        }
        if (setting.dataChanged) {
          this.$nextTick(() => {
            this.updateTabChart(activeRefName);
          });
          setting.dataChanged= false;
        }
      });
    },
    onContourColorsChange(newColorIndex) {
      const refName = this.activeTab;
      const setting = this[`${refName}Setting`];
      setting.contourColors = commonProperty.lossColorscale[newColorIndex];
      this.$refs[refName].handleContourColorsChange(setting);
    },
    onPathStyleChange(refName) {
      this.$refs[refName].handlePathStyleChange(this[`${refName}Setting`]);
    },
    onContoursNumberChange(refName) {
      this.$refs[refName].handleContoursNumberChange(this[`${refName}Setting`]);
    },
    /**
     * Formatting markArea data
     * @param {Object} seriesData
     * @return {Object} seriesData
     */

    formatMarkArea(data) {
      const currentValue = this.steps.value;
      const currentValueArr = currentValue.split('-');
      const areaData = [
        [
          {
            name: this.$t('lossAnalysis.selectedInterval'),
            xAxis:
              this.chartInfo.unit === 'step'
                ? currentValueArr[0]
                : Number(currentValueArr[0]) * this.chartInfo.step_per_epoch,
          },
          {
            name: this.$t('lossAnalysis.selectedInterval'),
            xAxis:
              this.chartInfo.unit === 'step'
                ? currentValueArr[1]
                : Number(currentValueArr[1]) * this.chartInfo.step_per_epoch,
          },
        ],
      ];
      data.markArea = {
        itemStyle: {
          color: 'red',
          borderWidth: 1,
          opacity: 0.2,
        },
        data: areaData,
      };
      return data;
    },

    /**
     * Formatting Chart Data
     * @param {Object} oriData
     * @return {Object} echar option
     */

    formatChartOption(data) {
      const seriesData = [];
      const oriData = data;
      const dataObj = {
        name: this.trainInfo.id,
        data: [],
        type: 'line',
        showSymbol: false,
      };
      dataObj.data = oriData.valueData['stepData'];
      this.formatMarkArea(dataObj);
      seriesData.push(dataObj);

      const that = this;
      const tempOption = {
        legend: {
          show: false,
        },
        xAxis: {
          name: this.$t('lossAnalysis.trainingStep'),
          type: 'value',
          show: true,
          scale: true,
          nameGap: 6,
          minInterval: 1,
          axisLine: {
            lineStyle: {
              width: 2,
            },
          },
          axisLabel: {
            interval: 0,
            rotate: 90,
            formatter(value) {
              const symbol = Math.abs(value);
              if (symbol.toString().length > 6) {
                return value.toExponential(0);
              } else if (value >= 1000 || value <= -1000) {
                return parseFloat((value / 1000).toFixed(2)) + 'k';
              } else if (value > 0) {
                return value;
              } else {
                return parseFloat(value.toFixed(3));
              }
            },
          },
        },
        yAxis: {
          name: this.$t('lossAnalysis.lossValue'),
          type: 'value',
          scale: true,
          axisLine: {
            lineStyle: {
              width: 2,
            },
          },
          nameTextStyle: {
            padding: [0, 0, 7, 0]
          },
          axisLabel: {
            formatter(value) {
              const symbol = Math.abs(value);
              if (symbol.toString().length > 6) {
                return value.toExponential(4);
              } else if (value >= 1000 || value <= -1000) {
                return parseFloat((value / 1000).toFixed(2)) + 'k';
              } else if (value > 0) {
                return value;
              } else {
                return parseFloat(value.toFixed(3));
              }
            },
          },
        },
        grid: {
          top: 40,
          left: 50,
          right: 60,
          bottom: 40
        },
        animation: true,
        tooltip: {
          trigger: 'axis',
          confine: true,
          axisPointer: {
            type: 'line',
          },
          formatter(params) {
            const strhead =
              `<table class="char-tip-table" class="borderspacing3"><tr><td></td>` +
              `<td>${that.$t('scalar.charTipHeadName')}</td>` +
              `<td>${that.$t('scalar.charTipHeadValue')}</td>` +
              `<td>${that.$t('scalar.step')}</td>` +
              `</tr>`;
            let strBody = '';
            const runArr = [];
            const detialArr = [];
            let curStep = null;
            let dataCount = 0;
            params.forEach((parma) => {
              let addFlag = true;
              const curSerieOriData = oriData.valueData;

              if (curStep === null) {
                curStep = curSerieOriData.stepData[parma.dataIndex][0];
              } else {
                if (curSerieOriData.stepData[parma.dataIndex][0] === curStep) {
                  const sameRunIndex = [];
                  runArr.forEach((runName, index) => {
                    if (parma.seriesName === runName) {
                      sameRunIndex.push(index);
                    }
                  });
                  if (sameRunIndex.length) {
                    sameRunIndex.forEach((sameIndex) => {
                      if (
                        detialArr[sameIndex] &&
                        detialArr[sameIndex].value ===
                          curSerieOriData.stepData[parma.dataIndex][1]
                      ) {
                        addFlag = false;
                      }
                    });
                  }
                } else {
                  addFlag = false;
                }
              }
              if (addFlag) {
                dataCount++;
                runArr.push(parma.seriesName);
                detialArr.push({
                  value: curSerieOriData.stepData[parma.dataIndex][1],
                  step: curSerieOriData.stepData[parma.dataIndex][0],
                  dataIndex: parma.dataIndex,
                });
                strBody +=
                  `<tr><td style="border-radius:50%;width:15px;height:15px;vertical-align: middle;` +
                  `margin-right: 5px;background-color:${parma.color};` +
                  `display:inline-block;"></td><td>${parma.seriesName}</td>` +
                  `<td>${that.formatYAxisValue(
                      curSerieOriData.stepData[parma.dataIndex][1],
                  )}</td>` +
                  `<td>${curSerieOriData.stepData[parma.dataIndex][0]}</td>` +
                  `</tr>`;
              }
            });
            if (dataCount) {
              return strhead + strBody + '</table>';
            }
          },
        },
        series: seriesData,
      };

      return tempOption;
    },

    /**
     * Format the value of the Y axis
     * @param {String} value number y
     * @return {Number}
     */

    formatYAxisValue(value) {
      if (!value) {
        return value;
      }
      const symbol = Math.abs(value);
      if (symbol.toString().length > 6) {
        return value.toExponential(4);
      } else if (value > 0) {
        return value;
      } else {
        return parseFloat(value.toFixed(3));
      }
    },

    /**
     * Updating or Creating a Specified chart
     */

    updateOrCreateChart(option) {
      this.chartObj = echarts.init(document.getElementById('commonChart'), echartsThemeName);
      this.chartOption = option;
      this.$nextTick(() => {
        this.chartObj.setOption(this.chartOption, true);
        this.chartObj.resize();
      });
    },

    initCommonChart() {
      const params = {
        train_id: this.trainInfo.id,
        tag: 'loss/auto/scalar',
      };

      RequestService.getScalarsSample(params).then(
          (res) => {
            if (res && res.data) {
              const resData = res.data;
              const tempObject = {
                valueData: {
                  stepData: [],
                },
              };
              resData.metadatas.forEach((metaData) => {
                tempObject.valueData.stepData.push([
                  metaData.step,
                  metaData.value,
                ]);
              });

              const tempOriData = tempObject;
              const tempOption = this.formatChartOption(tempOriData);
              this.updateOrCreateChart(tempOption);
            }
          },
          (error) => {
            if (this.chartObj) {
              this.chartObj.clear();
              this.chartObj = null;
            }
            this.chartOption = {};
            this.chartInfo = {};
          },
      );
    },
    stepChange(val) {
      this.steps.options.some((item) => {
        if (val === item.label) {
          return (this.steps.id = item.id);
        }
      });
      if (this.chartObj) {
        const params = {
          train_id: this.trainInfo.id,
          type: 'interval',
          metadata: true,
          interval_id: this.steps.id,
        };
        this.getDataOfLossGraph(params);
      }
    },
    /**
     * Reset on the right
     */
    configRefresh() {
      const activeRefName = this.activeTab;
      if (activeRefName === THREED) {
        const lossCommonStyle = JSON.parse(JSON.stringify(commonProperty.lossCommonStyle));
        const setting = this.diagram3DSetting;
        setting.camera = lossCommonStyle.camera;
        setting.light = lossCommonStyle.light;
        setting.line = lossCommonStyle.line;
        setting.opacity = lossCommonStyle.opacity;
        setting.surface.colorScaleIndex = 0;
        setting.surface.colorscale = commonProperty.lossColorscale[0];
        const elementItem = this.$refs[THREED];
        if (elementItem) {
          elementItem.restyleView(true);
        }
      } else {
        const setting = this[`${activeRefName}Setting`];
        setting.colorsIndex = 0;
        setting.pathColor = '#000000';
        setting.pathWidth = 5;
        setting.contoursNumber = 10,
        setting.contourColors = commonProperty.lossColorscale[setting.colorsIndex];
        this.$refs[activeRefName].handleDataChange(this.oriData, setting);
      }
    },
    // -------------------------------------------------diagram3d----------------------------------
    diagramViewInfoChange(viewInfo) {
      this.diagramViewInfo = viewInfo;
    },
    diagramSettingChange() {
      if (this.diagramSliderChangeTimer) {
        clearTimeout(this.diagramSliderChangeTimer);
        this.diagramSliderChangeTimer = null;
      }
      this.diagram3DSetting.surface.colorscale =
        commonProperty.lossColorscale[
            this.diagram3DSetting.surface.colorScaleIndex
        ];
      this.diagramSliderChangeTimer = setTimeout(() => {
        const elementItem = this.$refs[THREED];
        if (elementItem) {
          elementItem.restyleView();
        }
      }, 300);
    },
  },
  components: {
    contourMap,
    diagram3D,
  },
};
</script>
<style>
.cl-loss-analysis {
  height: 100%;
}
.cl-loss-analysis .el-tabs__item {
  padding: 0 15px;
}
.cl-loss-analysis .cl-close-btn {
  width: 20px;
  height: 20px;
  cursor: pointer;
}
.cl-loss-analysis .loss-analysis-content {
  height: calc(100% - 56px);
  display: flex;
}
.cl-loss-analysis .loss-analysis-content .table-container {
  flex: 1;
  overflow: hidden;
}
.cl-loss-analysis .loss-analysis-content .table-container .el-tabs {
  height: 100%;
}
.cl-loss-analysis .loss-analysis-content .table-container .el-tabs .el-tabs__header {
  margin: 0 0 32px;
}
.cl-loss-analysis .loss-analysis-content .table-container .el-tabs .el-tabs__content {
  height: calc(100% - 72px);
}
.cl-loss-analysis .loss-analysis-content .table-container .el-tabs .el-tabs__content .el-tab-pane {
  height: 100%;
}
.cl-loss-analysis .loss-analysis-content .table-container .el-tabs .el-tabs__content .el-tab-pane .detail {
  height: 100%;
  width: 100%;
  border: 1px solid var(--border-color);
}
.cl-loss-analysis .loss-analysis-content .right {
  width: 450px;
  flex-shrink: 0;
  overflow-y: auto;
}
.cl-loss-analysis .loss-analysis-content .right .chart-container {
  height: 380px;
  padding: 0 32px 20px;
}
.cl-loss-analysis .loss-analysis-content .right .chart-container .title {
  font-size: 20px;
  font-weight: bold;
}
.cl-loss-analysis .loss-analysis-content .right .chart-container .commonChart {
  width: 100%;
  height: calc(100% - 90px);
}
.cl-loss-analysis .loss-analysis-content .right .chart-container .commonChart .no-data-img {
  background: var(--bg-color);
  height: 100%;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}
.cl-loss-analysis .loss-analysis-content .right .chart-container .commonChart .no-data-img .content {
  margin: auto;
}
.cl-loss-analysis .loss-analysis-content .right .chart-container .commonChart .no-data-img img {
  max-width: 100%;
}
.cl-loss-analysis .loss-analysis-content .right .chart-container .commonChart .no-data-img p {
  font-size: 16px;
  padding-top: 10px;
  text-align: center;
}
.cl-loss-analysis .loss-analysis-content .right .chart-container .centerPoint {
  margin-bottom: 10px;
}
.cl-loss-analysis .loss-analysis-content .right .chart-container .center-step {
  line-height: 18px;
  margin-bottom: 20px;
}
.cl-loss-analysis .loss-analysis-content .right .chart-container .center-step .circle {
  height: 12px;
  width: 12px;
  border-radius: 10px;
  background-color: red;
}
.cl-loss-analysis .loss-analysis-content .right .chart-container .center-step .operate {
  cursor: pointer;
  font-size: 16px;
}
.cl-loss-analysis .loss-analysis-content .right .chart-container .center-step .operate:hover {
  color: var(--theme-color);
}
.cl-loss-analysis .loss-analysis-content .right .chart-container .center-step > div {
  display: inline-block;
  margin-right: 20px;
}
.cl-loss-analysis .loss-analysis-content .right .chart-container .step-select .step-select-info {
  margin-right: 20px;
}
.cl-loss-analysis .loss-analysis-content .right .chart-container .step-select .el-select {
  width: 150px;
}
.cl-loss-analysis .loss-analysis-content .right .chart-setting {
  border-top: 1px dashed var(--border-color);
  padding: 20px 32px;
}
.cl-loss-analysis .loss-analysis-content .right .chart-setting .title {
  font-size: 20px;
  font-weight: bold;
}
.cl-loss-analysis .loss-analysis-content .right .chart-setting .title .right-icon {
  float: right;
  font-size: 20px;
  margin-top: 3px;
  cursor: pointer;
}
.cl-loss-analysis .loss-analysis-content .right .chart-setting .title .right-icon:hover {
  color: var(--themem-color);
}
.cl-loss-analysis .loss-analysis-content .right .chart-setting .setting-detail {
  height: calc(100% - 30px);
  overflow: auto;
}
.cl-loss-analysis .loss-analysis-content .right .chart-setting .setting-detail .setting-item {
  line-height: 32px;
  margin-top: 20px;
}
.cl-loss-analysis .loss-analysis-content .right .chart-setting .setting-detail .setting-item .line-select-style {
  width: 150px;
}
.cl-loss-analysis .loss-analysis-content .right .chart-setting .setting-detail .setting-item .line-num-title {
  display: inline-block;
  padding-right: 10px;
  width: 120px;
}
.cl-loss-analysis .loss-analysis-content .right .chart-setting .setting-detail .setting-item .label {
  display: inline-block;
  width: 90px;
  vertical-align: middle;
  font-size: 14px;
}
.cl-loss-analysis .loss-analysis-content .right .chart-setting .setting-detail .setting-item .vertical-top {
  vertical-align: top;
}
.cl-loss-analysis .loss-analysis-content .right .chart-setting .setting-detail .setting-item .content {
  display: inline-block;
  width: calc(100% - 100px);
  vertical-align: middle;
}
.cl-loss-analysis .loss-analysis-content .right .chart-setting .setting-detail .setting-item .content .color-select {
  width: 200px;
}
.cl-loss-analysis .loss-analysis-content .right .chart-setting .setting-detail .setting-item .content .color-box {
  display: inline-block;
  width: 50px;
  height: 32px;
}
.cl-loss-analysis .loss-analysis-content .right .chart-setting .setting-detail .setting-item .content .line-width {
  width: 70px;
  margin-left: 20px;
  vertical-align: top;
}
.cl-loss-analysis .loss-analysis-content .right .chart-setting .setting-detail .setting-item .content .tip {
  display: inline-block;
  margin-left: 10px;
  vertical-align: top;
  font-size: 12px;
}
.cl-loss-analysis .loss-analysis-content .right .chart-setting .setting-detail .setting-item .content .slider-label {
  display: inline-block;
  vertical-align: top;
  width: 45px;
  font-size: 12px;
}
.cl-loss-analysis .loss-analysis-content .right .chart-setting .setting-detail .setting-item .content .slider {
  width: calc(100% - 90px);
  display: inline-block;
  height: 20px;
  vertical-align: middle;
}
.cl-loss-analysis .right .chart-setting .setting-detail .setting-item .content .slider .el-slider__runway {
  margin: 8px 0;
}
.cl-loss-analysis .loss-analysis-content .right .chart-setting .setting-detail .setting-item .content .slider-value {
  display: inline-block;
  margin-left: 15px;
  vertical-align: top;
  font-size: 12px;
}
.cl-loss-analysis .loss-analysis-content .right .chart-setting .setting-detail .setting-item .content .param {
  display: inline-block;
  margin-right: 21px;
}
.cl-loss-analysis .loss-analysis-content .right .chart-setting .setting-detail .mini {
  line-height: 18px;
}
.cl-loss-analysis .loss-analysis-content .right .chart-info {
  border-top: 1px dashed var(--border-color);
  padding: 20px 32px;
}
.cl-loss-analysis .loss-analysis-content .right .chart-info .title {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 20px;
}
.cl-loss-analysis .loss-analysis-content .right .chart-info .chart-info-item {
  display: flex;
  line-height: 36px;
}
.cl-loss-analysis .loss-analysis-content .right .chart-info .chart-info-item .chart-info-item-right {
  flex: 1;
}
.cl-loss-analysis .char-tip-table td {
  padding-left: 5px;
  padding-right: 5px;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 150px;
  overflow: hidden;
}
.cl-loss-analysis .borderspacing3 {
  border-spacing: 3px;
}

.cl-loss-analysis .cl-title-top {
  height: 56px;
  line-height: 56px;
  font-size: 20px;
  font-weight: bold;
}

.cl-loss-analysis .cl-title-top .el-icon-info {
  color: #6c7280;
}

.cl-loss-analysis .cl-title-top .cl-title-tip .tip-part {
  line-height: 20px;
  word-break: normal;
}

.cl-loss-analysis .cl-close-btn {
  width: 20px;
  height: 20px;
  vertical-align: -3px;
  cursor: pointer;
  display: inline;
  float: right;
}
</style>

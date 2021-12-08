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
  <div class="cl-diagram-container">
    <empty v-if="seriesArr.length <= 1 || allEmptyData"
           :state="over ? 'noData' : isCompareLoss ? 'dataSelectTip' : 'dataLoading'"
           :fontSize="16"></empty>
    <!-- Function Area -->
    <div class="operateContainer top-operate"
         v-if="componentConfigOptions.fullScreen || componentConfigOptions.fit || componentConfigOptions.download">
      <span v-if="componentConfigOptions.fullScreen"
            class="icon-item fullscreen-icon"
            @click="toggleFullScreen"
            :title="$t('lossAnalysis.fullScreen')"></span>
      <span v-if="componentConfigOptions.fit"
            class="icon-item fit-icon"
            @click="fitScreen"
            :title="$t('lossAnalysis.fitScreen')"></span>
      <span v-if="componentConfigOptions.download"
            class="icon-item download-icon"
            @click="downloadToImage"
            :title="$t('lossAnalysis.downloadPic')"></span>
    </div>
    <!-- Draw Area -->
    <div class="chart-container"
         :class="componentConfigOptions.playButton ? 'chart-container-part' :'chart-container-full'">
      <div class="chart-item"
           :id="itemId"
           :ref="itemId"></div>
    </div>
    <!-- Play Button -->
    <div class="operateContainer bottom-operate"
         v-if="oriData.path && componentConfigOptions.playButton">
      <div @click="animateAction"
           class="animate-icon">
        <div class="play-text">
          <span class="el-icon-video-play"></span>
          {{$t('lossAnalysis.playTrackAnimation')}}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import echarts from '../js/echarts';
import 'echarts-gl';
import commonProperty from '../common/common-property';
import empty from '@/components/empty.vue';
const itemWidth = 20;
const itemHeight = 135;
const itemRight = 18;
const lineLabelSize = 20;
const axisNameGap = 30;
const standardWidth = 1400;
export default {
  components: {
    empty,
  },
  props: {
    // determine whether the component is used by compare loss module
    isCompareLoss: false,
    over: Boolean,
    oriData: {
      type: Object,
      default: () => {
        return {
          points: {
            X: [],
            Y: [],
            Z: [],
          },
        };
      },
    },
    styleSetting: {
      type: Object,
      default: () => {
        return {
          camera: commonProperty.lossCommonStyle.camera,
          light: commonProperty.lossCommonStyle.light,
          line: commonProperty.lossCommonStyle.line,
          opacity: commonProperty.lossCommonStyle.opacity,
          surface: {
            colorscale: commonProperty.lossColorscale[0],
          },
        };
      },
    },
    componentConfigOptions: {
      type: Object,
      default: () => {
        return {
          cameraInfo: false,
          download: false,
          fit: false,
          fullScreen: false,
          playButton: false,
          convergencePoint: false,
          colorBar: false,
        };
      },
    },
    //  Indicates whether different loss graph properties need to be merged
    mergeGraphproperties: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      itemId: '', // Dom id
      maxAnimateStepNum: 80, // Maximum number of animations steps
      viewMapMin: 0, // Z-axis minimum
      viewMapMax: 0, // Z-axis maximum
      chartObj: null, // Object of chart
      chartOption: {}, // Options of chart
      themeIndex: this.$store.state.themeIndex, // Index of theme color
      seriesArr: [commonProperty.emptySurfaceSeries], // Series data of chart
      // Point style of chart
      lineSymbol: {
        start: 'rect',
        end: 'triangle',
        other: 'circle',
      },
      animationTimer: null, // Timer of animation
      ANIMATION_TOTAL_TIME: 3000, // Total animation execution duration
      EMPTY_SURFACE_NAME: commonProperty.emptySurfaceSeries.name, // Name of the placeholder surface
      FIXED_SURFACE_OPACITY: 1, // Opacity of contrast mode
      // Animation-related data
      animationData: {
        pathData: [], // Data of each animation
        pointData: [], // Data of points
        pointsIndex: [], // Number of steps in which the node is located
        animationStepNum: 0, // Total animation steps
        animationStepTime: 0, // Time required for each animation step
      },
      // Check whether there is data in the comparison chart
      allEmptyData: false,
    };
  },
  created() {
    this.init();
  },
  methods: {
    /**
     * Initialize
     */
    init() {
      this.itemId = `${new Date().getTime()}` + `${this.$store.state.componentsCount}`;
      this.$store.commit('componentsNum');
    },
    /**
     * Convert the original data into the required data structure
     * @param {Object} oriData Original data
     */
    formatOriData(oriData) {
      if (!oriData.points) {
        return;
      }
      const seriesSurface = this.getSurfaceData(oriData);
      if (seriesSurface) {
        this.seriesArr.push(seriesSurface);
      }

      if (oriData.path) {
        const pathData = this.getLineData(oriData);
        if (pathData) {
          this.seriesArr.push(pathData.seriesPath, ...pathData.seriesPointArr);
        }
      } else if (
        this.componentConfigOptions.convergencePoint &&
        oriData.convergence_point &&
        oriData.convergence_point.length >= 3
      ) {
        const pointData = this.getPointData(oriData);
        this.seriesArr.push(pointData);
      }
    },
    /**
     * Convert raw data to chart option.
     * @param {Boolean} isFixedSurface Indicates where the comparison mode is used
     */
    formatChartOption(isFixedSurface) {
      let visualMapData = [];
      if (isFixedSurface) {
        visualMapData = [
          {
            min: 0,
            max: 0,
            show: false,
            seriesIndex: 0,
            inRange: {
              color: commonProperty.compareTraceColorScale[0],
            },
          },
          {
            min: 0,
            max: 0,
            show: false,
            seriesIndex: 1,
            inRange: {
              color: commonProperty.compareTraceColorScale[1],
            },
          },
        ];
      } else {
        visualMapData = [
          {
            min: this.viewMapMin,
            max: this.viewMapMax,
            precision: 3,
            text: [
              `${this.$t('lossAnalysis.lossValue')}${this.$t('symbols.colon')}${this.viewMapMax.toFixed(3)}`,
              `${this.$t('lossAnalysis.lossValue')}${this.$t('symbols.colon')}${this.viewMapMin.toFixed(3)}`,
            ],
            textStyle: {
              color: commonProperty.commonChartTheme[this.themeIndex].axisLabelColor,
            },
            seriesIndex: 1,
            right: this.getNowSize(itemRight),
            inRange: {
              color: this.styleSetting.surface.colorscale,
            },
            itemWidth: this.getNowSize(itemWidth),
            itemHeight: this.getNowSize(itemHeight),
          },
        ];
      }
      const option = {
        tooltip: {},
        backgroundColor: commonProperty.commonThemes[this.themeIndex].backgroundColor,
        visualMap: visualMapData,
        xAxis3D: {
          type: 'value',
          scale: true,
          nameTextStyle: {
            fontFamily: 'Microsoft YaHei',
            color: commonProperty.echartsTextStyle[this.themeIndex][0],
          },
          nameGap: axisNameGap,
          axisLine: {
            lineStyle: {
              color: commonProperty.commonChartTheme[this.themeIndex].axisLineColor,
            },
          },
          axisLabel: {
            textStyle: {
              color: commonProperty.commonChartTheme[this.themeIndex].axisLabelColor,
            },
          },
        },
        yAxis3D: {
          type: 'value',
          scale: true,
          nameTextStyle: {
            fontFamily: 'Microsoft YaHei',
            color: commonProperty.echartsTextStyle[this.themeIndex][0],
          },
          nameGap: axisNameGap,
          axisLine: {
            lineStyle: {
              color: commonProperty.commonChartTheme[this.themeIndex].axisLineColor,
            },
          },
          axisLabel: {
            textStyle: {
              color: commonProperty.commonChartTheme[this.themeIndex].axisLabelColor,
            },
          },
        },
        zAxis3D: {
          type: 'value',
          scale: true,

          nameTextStyle: {
            fontFamily: 'Microsoft YaHei',
            color: commonProperty.echartsTextStyle[this.themeIndex][0],
          },
          nameGap: axisNameGap,
          axisLine: {
            lineStyle: {
              color: commonProperty.commonChartTheme[this.themeIndex].axisLineColor,
            },
          },
          axisLabel: {
            textStyle: {
              color: commonProperty.commonChartTheme[this.themeIndex].axisLabelColor,
            },
          },
        },
        grid3D: {
          viewControl: {
            alpha: this.styleSetting.camera.alpha,
            beta: this.styleSetting.camera.beta,
            distance: this.styleSetting.camera.distance,
            center: [
              this.styleSetting.camera.centerX,
              this.styleSetting.camera.centerY,
              this.styleSetting.camera.centerZ,
            ],
          },
          light: {
            main: {
              alpha: this.styleSetting.light.alpha,
              beta: this.styleSetting.light.beta,
              intensity: this.styleSetting.light.intensity,
            },
          },
        },
        series: this.seriesArr,
      };
      this.chartOption = option;
    },
    /**
     * Draw chart
     */
    drawChart() {
      if (!this.chartObj) {
        const chartDom = this.$refs[this.itemId];
        if (!chartDom) {
          return;
        }
        this.chartObj = echarts.init(chartDom);
      }
      this.chartObj.setOption(this.chartOption, !this.mergeGraphproperties);
    },
    /**
     * Draw animation
     */
    drawAnimateChart() {
      if (this.chartObj) {
        this.chartObj.setOption({ series: this.chartOption.series }, false);
      }
    },
    /**
     * Graphing data comparisons
     */
    drawFixedChart() {
      if (this.chartObj) {
        this.chartObj.setOption({
          series: this.chartOption.series,
          visualMap: this.chartOption.visualMap,
        });
      }
    },
    /**
     * Obtain surface data from recognizable data
     * @param {Object} oriData Identifiable data
     * @param {Boolean} isFixedSurface Indicates where the comparison mode is used
     * @return {Object} series data of surface
     */
    getSurfaceData(oriData, isFixedSurface) {
      const loopCount = oriData.points.z.length;
      const innerLoop = oriData.points.z[0].length;

      if (!loopCount || !innerLoop) {
        return null;
      }

      const surfaceData = [];
      const xD = oriData.points.x;
      const yD = oriData.points.y;
      const zD = oriData.points.z;
      let minValue = null;
      let maxValue = null;
      for (let i = 0; i < loopCount; i++) {
        const zmin = Math.min(...zD[i]);
        const zmax = Math.max(...zD[i]);
        if (!i) {
          minValue = zmin;
          maxValue = zmax;
        } else {
          minValue = Math.min(minValue, zmin);
          maxValue = Math.max(maxValue, zmax);
        }
        for (let j = 0; j < innerLoop; j++) {
          surfaceData.push([xD[j], yD[i], zD[i][j]]);
        }
      }
      this.viewMapMin = minValue;
      this.viewMapMax = maxValue;

      const surfaceSeries = {
        type: 'surface',
        name: oriData.train_id,
        wireframe: {
          show: false,
        },
        shading: 'lambert',
        itemStyle: {
          opacity: isFixedSurface ? this.FIXED_SURFACE_OPACITY : this.styleSetting.opacity,
        },
        data: surfaceData,
      };
      return surfaceSeries;
    },
    /**
     * Obtain path data and animation data according to identifiable data
     * @param {Object} oriData Identifiable data
     * @return {Object} series data of path
     */
    getLineData(oriData) {
      const originLineData = oriData.path;
      const pathLength = oriData.path.x.length;

      if (!pathLength) {
        return null;
      }

      const pathData = [];
      const seriesPointArr = [];
      for (let k = 0; k < pathLength; k++) {
        pathData.push({
          name: `${oriData.metadata.unit}${this.$t('symbols.colon')}${originLineData.intervals[k]}`,
          value: [originLineData.x[k], originLineData.y[k], originLineData.z[k]],
        });
        let symbolType = this.lineSymbol.other;
        let symbolLabel = '';
        let labelShow = false;
        if (!k) {
          symbolType = this.lineSymbol.start;
          symbolLabel = `${this.$t('components.startText')}`;
          labelShow = true;
        } else if (k === pathLength - 1) {
          symbolType = this.lineSymbol.end;
          symbolLabel = `${this.$t('components.endText')}`;
          labelShow = true;
        }
        seriesPointArr.push({
          type: 'scatter3D',
          name: oriData.train_id,
          data: [
            {
              name: `${oriData.metadata.unit}${this.$t('symbols.colon')}${originLineData.intervals[k]}`,
              value: [originLineData.x[k], originLineData.y[k], originLineData.z[k]],
            },
          ],
          symbol: symbolType,
          symbolSize: this.styleSetting.line.width * 3,
          itemStyle: {
            color: this.styleSetting.line.color,
          },
          label: {
            show: labelShow,
            formatter: () => {
              return symbolLabel;
            },
            textStyle: {
              color: commonProperty.commonThemes[this.themeIndex].fontColor,
            },
            fontSize: this.getNowSize(lineLabelSize),
          },
        });
      }
      if (this.componentConfigOptions.playButton) {
        this.animationData.pointData = seriesPointArr;
        this.getAnimateFrames(pathData);
      }
      this.animationData.animationStepTime = this.ANIMATION_TOTAL_TIME / (this.animationData.animateStepNum - 1);
      const seriesPath = {
        type: 'line3D',
        name: oriData.train_id,
        data: pathData,
        lineStyle: {
          width: this.styleSetting.line.width,
          color: this.styleSetting.line.color,
        },
        animationDurationUpdate: this.animationData.animationStepTime,
      };
      return {
        seriesPath,
        seriesPointArr,
      };
    },
    /**
     * Obtain the convergence point data according to the identifiable data
     * @param {Object} oriData Identifiable data
     * @return {Object} Convergence point data
     */
    getPointData(oriData) {
      const pointObj = oriData.convergence_point;
      const pointData = {
        type: 'scatter3D',
        name: oriData.train_id,
        data: [pointObj],
        symbol: this.lineSymbol.other,
        symbolSize: 10,
        itemStyle: {
          color: commonProperty.compareTracePointColor[this.themeIndex].pointColor,
        },
        label: {
          show: true,
          position: 'top',
          formatter: this.$t('lossCompare.conpoint'),
          textStyle: {
            color: commonProperty.compareTracePointColor[this.themeIndex].pointColor,
          },
        },
      };
      return pointData;
    },
    /**
     * Obtain path data and animation data according to identifiable data
     */
    updateView() {
      this.seriesArr = [commonProperty.emptySurfaceSeries];
      this.formatOriData(this.oriData);
      this.formatChartOption();
      this.drawChart();
      if (this.componentConfigOptions.cameraInfo) {
        this.addViewChangeListener();
      }
    },
    /**
     * Download as PNG picture
     */
    downloadToImage() {
      if (this.chartObj) {
        const imageUrl = this.chartObj.getDataURL();
        const imageLink = document.createElement('a');
        imageLink.download = `${this.oriData.train_id ? this.oriData.train_id : '' + '-'}diagram3DImage`;
        imageLink.style.display = 'none';
        imageLink.href = imageUrl;
        document.body.appendChild(imageLink);
        imageLink.click();
        document.body.removeChild(imageLink);
      }
    },
    /**
     * Execute animation
     */
    animateAction() {
      if (this.animationTimer) {
        clearInterval(this.animationTimer);
        this.animationTimer = null;
      }
      if (this.chartOption) {
        const loopCount = this.chartOption.series.length;
        for (let i = loopCount - 1; i >= 0; i--) {
          const tempData = this.chartOption.series[i];
          if (tempData.type === 'line3D') {
            tempData.data = [];
          } else if (tempData.type === 'scatter3D') {
            if (this.oriData.path) {
              this.chartOption.series.splice(i, 1);
            }
          }
        }
        const chartOption = this.chartObj.getOption();
        const viewControlObj = this.chartOption.grid3D.viewControl;
        if (chartOption.grid3D && chartOption.grid3D[0] && chartOption.grid3D[0].viewControl) {
          const curVievControlObj = chartOption.grid3D[0].viewControl;
          viewControlObj.alpha = curVievControlObj.alpha;
          viewControlObj.beta = curVievControlObj.beta;
          viewControlObj.distance = curVievControlObj.distance;
          viewControlObj.center = curVievControlObj.center;
        }
        this.drawChart();
      } else {
        return;
      }
      let animationStep = 0;
      let curPointCount = 0;
      const totalStep = this.animationData.pathData.length;
      const pathIndex = this.chartOption.series.length - 1;
      this.animationTimer = setInterval(() => {
        if (animationStep > totalStep) {
          clearInterval(this.animationTimer);
          this.animationTimer = null;
        } else if (animationStep === totalStep) {
          curPointCount++;
          this.chartOption.series.push(...this.animationData.pointData.slice(curPointCount - 1, curPointCount));
        } else {
          if ((this.chartOption.series[pathIndex].type = 'line3D')) {
            this.chartOption.series[pathIndex].data = this.animationData.pathData[animationStep];
          }
          if (animationStep === this.animationData.pointsIndex[curPointCount]) {
            curPointCount++;
            this.chartOption.series.push(...this.animationData.pointData.slice(curPointCount - 1, curPointCount));
          }
        }
        this.drawAnimateChart();
        animationStep++;
      }, this.animationData.animationStepTime);
    },
    /**
     * Calculate basic information of Graphic Interaction
     */
    calcForViewInfo() {
      if (this.chartObj) {
        const chartOption = this.chartObj.getOption();
        if (chartOption.grid3D && chartOption.grid3D[0] && chartOption.grid3D[0].viewControl) {
          const viewControlObj = chartOption.grid3D[0].viewControl;
          const viewInfo = {
            eye: {
              x: Math.floor(viewControlObj.center[0]),
              y: Math.floor(viewControlObj.center[1]),
              z: Math.floor(viewControlObj.center[2]),
            },
            angle: {
              alpha: Math.floor(viewControlObj.alpha) % 180,
              beta: Math.floor(viewControlObj.beta) % 180,
              distance: Math.floor(viewControlObj.distance),
            },
          };
          this.$emit('viewInfoChanged', viewInfo);
        }
      }
    },
    /**
     * Redraw drawing styles
     * @param {Boolean} ifReset Reset operation
     */
    restyleView(ifReset) {
      if (!this.chartObj) {
        return;
      }
      this.$nextTick(() => {
        const settingData = this.styleSetting;
        const pointWidthBase = 3;
        if (this.chartOption) {
          this.chartOption.visualMap[0].inRange.color = this.styleSetting.surface.colorscale;
          this.chartOption.grid3D.light.main.alpha = this.styleSetting.light.alpha;
          this.chartOption.grid3D.light.main.beta = this.styleSetting.light.beta;
          this.chartOption.grid3D.light.main.intensity = this.styleSetting.light.intensity;
        } else {
          return;
        }
        const loopCount = this.chartOption.series.length;
        for (let i = 0; i < loopCount; i++) {
          const tempData = this.chartOption.series[i];
          if (tempData.type === 'surface') {
            tempData.itemStyle.opacity = settingData.opacity;
          } else if (tempData.type === 'line3D') {
            tempData.lineStyle.width = settingData.line.width;
            tempData.lineStyle.color = settingData.line.color;
          } else if (tempData.type === 'scatter3D') {
            if (this.oriData.path) {
              tempData.itemStyle.color = settingData.line.color;
              tempData.symbolSize = settingData.line.width * pointWidthBase;
            }
          }
        }
        const viewControlObj = this.chartOption.grid3D.viewControl;
        if (ifReset) {
          const cameraData = settingData.camera;
          viewControlObj.alpha = cameraData.alpha;
          viewControlObj.beta = cameraData.beta;
          viewControlObj.distance = cameraData.distance;
          viewControlObj.center = [cameraData.centerX, cameraData.centerY, cameraData.centerZ];
        } else {
          if (this.chartObj) {
            const chartOption = this.chartObj.getOption();
            if (chartOption.grid3D && chartOption.grid3D[0] && chartOption.grid3D[0].viewControl) {
              const curVievControlObj = chartOption.grid3D[0].viewControl;
              viewControlObj.alpha = curVievControlObj.alpha;
              viewControlObj.beta = curVievControlObj.beta;
              viewControlObj.distance = curVievControlObj.distance;
              viewControlObj.center = curVievControlObj.center;
            }
          }
        }
        this.drawChart();
      });
    },
    /**
     * Resize canvas
     */
    resize() {
      if (this.chartObj) {
        this.$nextTick(() => {
          this.chartObj.resize();
        });
      }
    },
    /**
     * Add view interactive listening
     */
    addViewChangeListener() {
      if (this.chartObj) {
        this.chartObj.on('finished', () => {
          this.calcForViewInfo();
        });
      }
    },
    /**
     * Adaptive screen
     */
    fitScreen() {
      if (this.chartOption) {
        const settingData = this.styleSetting;
        const viewControlObj = this.chartOption.grid3D.viewControl;
        const cameraData = settingData.camera;
        viewControlObj.alpha = cameraData.alpha;
        viewControlObj.beta = cameraData.beta;
        viewControlObj.distance = cameraData.distance;
        viewControlObj.center = [cameraData.centerX, cameraData.centerY, cameraData.centerZ];
        this.drawChart();
      }
    },
    /**
     * Add new drawing
     * @param {Object} oriData Native data for surface
     */
    addData(oriData) {
      if (!oriData.points) {
        return;
      }
      const seriesSurface = this.getSurfaceData(oriData, true);
      if (this.chartObj) {
        const seriesLength = this.seriesArr.length;
        let newSurfaceIndex = 0;

        if (seriesLength > 1) {
          for (let i = 0; i < seriesLength; i++) {
            const tempSerie = this.seriesArr[i];
            if (tempSerie.name === this.EMPTY_SURFACE_NAME) {
              this.seriesArr[i] = seriesSurface;
              newSurfaceIndex = i;
              break;
            }
          }
        } else {
          this.seriesArr.push(seriesSurface);
          newSurfaceIndex = this.seriesArr - 1;
        }
        this.chartOption.visualMap[newSurfaceIndex].max = this.viewMapMax;
        this.chartOption.visualMap[newSurfaceIndex].min = this.viewMapMin;
        this.drawFixedChart();
      } else {
        if (seriesSurface) {
          this.seriesArr.push(seriesSurface);
        } else {
          return;
        }
        this.formatChartOption(true);
        const curSurfaceIndex = this.seriesArr.length - 1;
        this.chartOption.visualMap[curSurfaceIndex].max = this.viewMapMax;
        this.chartOption.visualMap[curSurfaceIndex].min = this.viewMapMin;
        this.drawChart();
      }
      this.allEmptyData = false;
    },
    /**
     * Remove drawing
     * @param {String} dataName Name of the surface to be removed
     */
    removeData(dataName) {
      let allEmptyData = true;
      const seriesLength = this.seriesArr.length;
      for (let i = 0; i < seriesLength; i++) {
        const tempSerie = this.seriesArr[i];
        if (tempSerie.name === dataName) {
          this.seriesArr[i] = commonProperty.emptySurfaceSeries;
        } else if (tempSerie.name !== this.EMPTY_SURFACE_NAME) {
          allEmptyData = false;
        }
      }
      this.drawFixedChart();
      this.allEmptyData = allEmptyData;
    },
    /**
     * Expand / fold full screen
     */
    toggleFullScreen() {
      this.$emit('toggleFullScreen');
    },
    /**
     * Calculate high granularity path animation
     * @param {Object} lineData Data of the path
     */
    getAnimateFrames(lineData) {
      const pathData = [];
      const distenceArr = [];
      const splitArr = [];
      let totalDistence = 0;
      const pointsIndex = [];
      const loopCount = lineData.length;
      const animationLimitArr = [20, 40];
      const multipBase = 2;
      // Sets the number of animation steps based on the number of paths
      if (loopCount <= animationLimitArr[0]) {
        this.animationData.animateStepNum = loopCount * multipBase * multipBase;
      } else if (loopCount > animationLimitArr[0] && loopCount <= animationLimitArr[1]) {
        this.animationData.animateStepNum = loopCount * multipBase;
      } else {
        this.animationData.animateStepNum = this.maxAnimateStepNum;
      }
      // Obtain the length of each segment and the total length
      for (let i = 0; i < loopCount - 1; i++) {
        const tempDistence = this.calcForDistence(lineData[i].value, lineData[i + 1].value);
        distenceArr.push(tempDistence);
        totalDistence += tempDistence;
      }
      // Calculate line length per frame
      const stepDistence = totalDistence / this.animationData.animateStepNum;
      // Calculate the number of cuts between segments
      let curIndex = 0;
      pointsIndex.push(curIndex);
      for (let i = 0; i < distenceArr.length; i++) {
        let tempSplitNUm = Math.floor(distenceArr[i] / stepDistence);
        if (!tempSplitNUm) {
          tempSplitNUm = 1;
        }
        splitArr.push(tempSplitNUm);
        curIndex += tempSplitNUm;
        pointsIndex.push(curIndex);
      }
      // Generate animation for each frame
      for (let i = 0; i < loopCount - 1; i++) {
        const innerLoop = splitArr[i];
        const xd = (lineData[i + 1].value[0] - lineData[i].value[0]) / innerLoop;
        const yd = (lineData[i + 1].value[1] - lineData[i].value[1]) / innerLoop;
        const zd = (lineData[i + 1].value[2] - lineData[i].value[2]) / innerLoop;
        let curX = lineData[i].value[0];
        let curY = lineData[i].value[1];
        let curZ = lineData[i].value[2];
        const tempArr = lineData.slice(0, i + 1);
        for (let j = 0; j < innerLoop; j++) {
          curX += xd;
          curY += yd;
          curZ += zd;
          pathData.push(tempArr.concat([{ value: [curX, curY, curZ] }]));
        }
      }
      this.animationData.pathData = pathData;
      this.animationData.pointsIndex = pointsIndex;
      this.animationData.animateStepNum = pathData.length;
    },
    /**
     * Calculate the distance between two points in 3D
     * @param {Array} startPoint
     * @param {Array} endPoint
     * @return {Number} Length between two points
     */
    calcForDistence(startPoint, endPoint) {
      const xd = Math.abs(startPoint[0] - endPoint[0]);
      const yd = Math.abs(startPoint[1] - endPoint[1]);
      const zd = Math.abs(startPoint[2] - endPoint[2]);
      const baseSqrt = Math.pow(xd, 2) + Math.pow(yd, 2) + Math.pow(zd, 2);
      const baseDistence = Math.sqrt(baseSqrt);
      return baseDistence;
    },
    /**
     * Calculate the size of the drawing at the current proportion
     * @param {Number} size
     * @return {Number} current proportion size
     */
    getNowSize(size) {
      const newWidth = document.getElementById(this.itemId).clientWidth;
      const proportion = newWidth / standardWidth;
      const currentSize = size * proportion;
      return currentSize;
    },
  },
  destroyed() {
    if (this.chartObj && this.componentConfigOptions.cameraInfo) {
      this.chartObj.off('rendered');
    }
  },
};
</script>
<style>
.cl-diagram-container {
  width: 100%;
  height: 100%;
  position: relative;
}
.cl-diagram-container .no-data-img {
  background: var(--bg-color);
  text-align: center;
  height: 100%;
  width: 100%;
  position: absolute;
  z-index: 10;
  top: 0;
  display: grid;
}
.cl-diagram-container .no-data-img .content {
  margin: auto;
}
.cl-diagram-container .no-data-img img {
  max-width: 100%;
}
.cl-diagram-container .no-data-img p {
  font-size: 16px;
  padding-top: 10px;
}
.cl-diagram-container .operateContainer.top-operate {
  position: absolute;
  top: 0;
  right: 0;
  z-index: 9;
  width: auto;
}
.cl-diagram-container .operateContainer.bottom-operate {
  height: 30px;
}
.cl-diagram-container .operateContainer {
  width: 100%;
  text-align: right;
}
.cl-diagram-container .operateContainer .icon-item {
  margin: 0 10px;
  cursor: pointer;
  float: right;
  width: 24px;
  height: 24px;
}
.cl-diagram-container .operateContainer .icon-item:hover {
  border: 1px solid var(--theme-color);
}
.cl-diagram-container .operateContainer .download-icon {
  background: url('../assets/images/download.png') center no-repeat;
}
.cl-diagram-container .operateContainer .fit-icon {
  background: url('../assets/images/fit.png') center no-repeat;
}
.cl-diagram-container .operateContainer .fullscreen-icon {
  background: url('../assets/images/full-screen.png') center no-repeat;
}
.cl-diagram-container .operateContainer .animate-icon {
  cursor: pointer;
  margin-right: 20px;
}
.cl-diagram-container .operateContainer .animate-icon .play-image {
  display: inline-block;
  width: 20px;
  height: 20px;
  margin: 0 5px;
  vertical-align: middle;
}
.cl-diagram-container .operateContainer .animate-icon .play-text {
  display: inline-block;
  height: 30px;
  line-height: 30px;
}
.cl-diagram-container .chart-container {
  width: 100%;
}
.cl-diagram-container .chart-container .chart-item {
  width: 100%;
  height: 100%;
}
.cl-diagram-container .chart-container-full {
  height: 100%;
}
.cl-diagram-container .chart-container-part {
  height: calc(100% - 30px);
}
.cl-diagram-container .main-svg:first-of-type {
  background: var(--bg-color) !important;
}
</style>

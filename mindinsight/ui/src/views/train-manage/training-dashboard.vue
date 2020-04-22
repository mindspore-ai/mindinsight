<!--
Copyright 2019 Huawei Technologies Co., Ltd.All Rights Reserved.

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
  <!--dashboard -->
  <div class="cl-dashboard">
    <div class="cl-dashboard-top">
      <div class="cl-dashboard-top-title">
        {{$t('trainingDashboard.trainingDashboardTitle')}}
      </div>
    </div>
    <div class="cl-dashboard-center">
      <div class="cl-dashboard-con-up"
           :class="curPageArr.length && !wrongPlugin ? '' : 'no-data-hover'"
           @click="viewMoreScalars">
        <div class="cl-dashboard-title"> {{$t("trainingDashboard.trainingScalar")}}</div>
        <div class="cl-module">
          <div class="cl-scalar-tagName"
               v-show="curPageArr.length && !wrongPlugin">
            <div v-for="(sampleItem,index) in curPageArr"
                 :key="index"
                 :class="['tagNameLeft',index==1? 'tagNameRight':'']">
              {{sampleItem.tagName}}
            </div>
          </div>
          <div id="module-chart"
               v-show="curPageArr.length && !wrongPlugin"
               key="chart-data"></div>
          <div class="no-data-img"
               v-show="!curPageArr.length || wrongPlugin"
               key="no-chart-data">
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
            <p class='no-data-text'>
              {{$t("public.noData")}}
            </p>
          </div>
        </div>
      </div>
      <div class="cl-dashboard-con-up"
           :class="!!histogramTag && !wrongPlugin ? '' : 'no-data-hover'"
           @click="viewMoreHistogram">
        <div class="cl-dashboard-title">{{$t("histogram.titleText")}}</div>
        <div class="cl-module">
          <div class="histogram-char-container"
               v-show="!!histogramTag && !wrongPlugin">
            <div id="distribution-chart"></div>
            <div class="tag-text">{{histogramTag}}</div>
          </div>
          <div class="no-data-img"
               key="no-chart-data"
               v-show="!histogramTag || wrongPlugin">
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
            <p class='no-data-text'>
              {{$t("public.noData")}}
            </p>
          </div>
        </div>
      </div>
      <div class="cl-dashboard-con-up"
           :class="firstFloorNodes.length && !wrongPlugin ? '' : 'no-data-hover'"
           @click="jumpToGraph">
        <div class="cl-dashboard-title">
          {{$t("trainingDashboard.calculationChart")}}
        </div>
        <div class="cl-module">
          <div id="graph"
               class="graph"
               v-show="firstFloorNodes.length && !wrongPlugin"></div>
          <div class="no-data-img"
               v-show="!firstFloorNodes.length || wrongPlugin">
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
            <p class='no-data-text'>
              {{$t("public.noData")}}
            </p>
          </div>
        </div>
      </div>
      <div class="cl-dashboard-con-up"
           :class="showDatasetGraph && !wrongPlugin ? '' : 'no-data-hover'"
           @click="jumpToDataMap">
        <div class="cl-dashboard-title"> {{$t("trainingDashboard.dataMap")}}</div>
        <div class="cl-module">
          <div id="dataMapGraph"
               class="graph"
               v-show="showDatasetGraph && !wrongPlugin"></div>
          <div class="no-data-img"
               key="no-chart-data"
               v-show="!showDatasetGraph || wrongPlugin">
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
            <p class='no-data-text'>
              {{$t("public.noData")}}
            </p>
          </div>
        </div>
      </div>
      <div class="cl-dashboard-con-up"
           :class="originImageDataArr.length && !wrongPlugin ? '' : 'no-data-hover'"
           @click="linkToImage($event)">
        <div class="cl-dashboard-title">
          <div class="cl-dashboard-title-left"> {{$t("trainingDashboard.samplingData")}}</div>
          <div class="cl-dashboard-title-right title-height">
            <el-button :disabled="originImageDataArr.length <= 1"
                       type="text"
                       @click="changeImage($event)">
              <span class="el-icon-refresh"></span>{{$t("trainingDashboard.imagesampleSwitch")}}
            </el-button>
          </div>
        </div>
        <div class="cl-module">
          <div class="image-container"
               :class="originImageDataArr.length && !wrongPlugin ? '' : 'no-data-img'">
            <img class="sample-img select-disable"
                 :src="curImageShowSample.curImgUrl"
                 v-show="originImageDataArr.length && !wrongPlugin">
            <img :src="require('@/assets/images/nodata.png')"
                 alt=""
                 v-show="!originImageDataArr.length || wrongPlugin">
            <p class='no-data-text'
               v-show=" !originImageDataArr.length || wrongPlugin">
              {{$t("public.noData")}}
            </p>
          </div>
        </div>
      </div>
      <div class="cl-dashboard-con-up no-data-hover">
        <div class="comming-soon-content">
          <div class="comming-soon-container">
            <img :src="require('@/assets/images/comming-soon.png')" />
            <p class='comming-soon-text'>
              {{$t("public.stayTuned")}}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import RequestService from '@/services/request-service';
import {basePath} from '@/services/fetcher';
import CommonProperty from '@/common/common-property.js';
import {select, selectAll, format, precisionRound} from 'd3';
import 'd3-graphviz';
const d3 = {select, selectAll, format, precisionRound};
import echarts from 'echarts';
export default {
  data() {
    return {
      // training job id
      trainingJobId: '',
      defColorCount: CommonProperty.commonColorArr.length, // default color
      colorNum: 0,
      charObj: null,
      histogramObj: null,
      histogramOption: {},
      histogramData: {},
      charOption: {},
      charData: [],
      originImageDataArr: [], // List of all image data.
      curImageShowSample: {}, // Image object to be displayed.
      imageRandomLoopCount: 0,
      imageBasePath: '/v1/mindinsight/datavisual/image/single-image?', // Relative path header of the picture
      autoUpdateTimer: null, // Automatic refresh timer
      histogramTag: '', // Label of the currently displayed histogram.
      allGraphData: {}, // graph Original input data
      graphviz: null,
      firstFloorNodes: [], // ID array of the first layer node.
      curColorIndex: 0,
      totalMemory: 16777216 * 2, // Memory size of the graph plug-in
      curPageArr: [],
      allDatasetGraphData: {},
      showDatasetGraph: false,
      datasetGraphviz: {},
      reloadStopTime: 1000,
      wrongPlugin: false,
      fileTag: '',
    };
  },
  computed: {
    /**
     * Global Refresh
     * @return {Boolen}
     */
    isReload() {
      return this.$store.state.isReload;
    },
    isTimeReload() {
      return this.$store.state.isTimeReload;
    },
    timeReloadValue() {
      return this.$store.state.timeReloadValue;
    },
  },
  watch: {
    isReload(newVal) {
      if (newVal) {
        if (this.isTimeReload) {
          this.startAutoUpdate();
        }
        this.getDatavisualPlugins(true);
        this.queryDatasetGraph();
        setTimeout(() => {
          this.$store.commit('setIsReload', false);
        }, this.reloadStopTime);
      }
    },
    /**
     * Listener auto refresh
     * @param {Boolen} newVal new Value
     */
    isTimeReload(newVal) {
      if (newVal) {
        this.startAutoUpdate();
      } else {
        this.stopAutoUpdate();
      }
    },
    /**
     * Time reload
     */
    timeReloadValue() {
      if (this.isTimeReload) {
        this.startAutoUpdate();
      }
    },
  },
  /**
   * Destroyed the page
   */
  destroyed() {
    // Disable the automatic refresh function
    this.stopAutoUpdate();
    window.removeEventListener('resize', this.resizeCallback, false);
  },
  mounted() {
    this.$nextTick(() => {
      window.addEventListener('resize', this.resizeCallback, false);
      this.init();
    });
  },
  methods: {
    /**
     * The size of the view window changes.
     */
    resizeCallback() {
      if (this.charResizeTimer) {
        clearTimeout(this.charResizeTimer);
        this.charResizeTimer = null;
      }

      this.charResizeTimer = setTimeout(() => {
        if (this.charObj) {
          this.charObj.resize();
        }
        if (this.histogramObj) {
          this.histogramObj.resize();
        }
      }, 500);
    },

    /**
     * Initialization the page of dashboard
     *
     */
    init() {
      if (this.$route.query && this.$route.query.id) {
        this.trainingJobId = this.$route.query.id;
      } else {
        this.trainingJobId = '';
        this.$message.error(this.$t('trainingDashboard.invalidId'));
      }
      this.getDatavisualPlugins(true);
      if (this.isTimeReload) {
        this.startAutoUpdate();
      }
      this.queryDatasetGraph();
    },

    /**
     * Querying Training Job Visualization Plug-ins
     * @param {Boolean} fromInit boolean
     */
    getDatavisualPlugins(fromInit) {
      const params = {
        train_id: this.trainingJobId,
        manual_update: fromInit || false,
      };
      RequestService.getDatavisualPlugins(params)
          .then((res) => {
            this.wrongPlugin = false;
            if (!res || !res.data || !res.data.plugins) {
              return;
            }
            const data = res.data.plugins;
            const imageTags = data.image || [];
            const scalarTags = data.scalar || [];
            const graphIds = data.graph || [];
            if (graphIds.length) {
              this.fileTag = graphIds[0];
            }
            const histogramTags = data.histogram || [];
            this.getHistogramTag(histogramTags);
            this.dealImageData(imageTags);
            this.getScalarList(scalarTags);
            if (!this.firstFloorNodes.length && graphIds.length) {
              this.queryGraphData();
            }
          })
          .catch((error) => {
            if (
              !error.response ||
            !error.response.data ||
            !error.response.data.error_code
            ) {
              return;
            }
            if (error.response.data.error_code.toString() === '50545005') {
              this.wrongPlugin = true;
            }
          });
    },

    /**
     * Viewing more scalar information
     */
    viewMoreScalars() {
      if (!this.curPageArr.length) {
        return;
      }
      this.$router.push({
        path: '/train-manage/scalar',
        query: {
          train_id: this.trainingJobId,
        },
      });
    },
    /**
     * Viewing more histogram information
     */
    viewMoreHistogram() {
      if (!this.histogramTag) {
        return;
      }
      this.$router.push({
        path: '/train-manage/histogram',
        query: {
          train_id: this.trainingJobId,
        },
      });
    },
    /**
     * Go to data.
     */
    jumpToDataMap() {
      if (!Object.keys(this.allDatasetGraphData).length) {
        return;
      }
      this.$router.push({
        path: '/train-manage/data-map',
        query: {
          train_id: this.trainingJobId,
        },
      });
    },
    /**
     * Go to graph.
     */
    jumpToGraph() {
      if (!this.firstFloorNodes.length) {
        return;
      }
      this.$router.push({
        path: '/train-manage/graph',
        query: {
          train_id: this.trainingJobId,
        },
      });
    },
    /**
     * Start the scheduled update
     */
    startAutoUpdate() {
      // Disable the automatic refresh function
      if (this.autoUpdateTimer) {
        clearInterval(this.autoUpdateTimer);
        this.autoUpdateTimer = null;
      }
      this.autoUpdateTimer = setInterval(() => {
        this.$store.commit('clearToken');
        this.getDatavisualPlugins();
        if (!Object.keys(this.allDatasetGraphData).length) {
          this.queryDatasetGraph();
        }
      }, this.timeReloadValue * 1000);
    },
    /**
     * Stop the scheduled update
     */
    stopAutoUpdate() {
      if (this.autoUpdateTimer) {
        clearInterval(this.autoUpdateTimer);
        this.autoUpdateTimer = null;
      }
    },
    /**
     * Get scalar list
     * @param {Array} tags
     */
    getScalarList(tags) {
      if (!tags.length) {
        this.colorNum = 0;
        this.charObj = null;
        this.charOption = {};
        this.charData = [];
        this.curPageArr = [];
        return;
      }
      const params = {
        plugin_name: 'scalar',
        train_id: this.trainingJobId,
      };
      RequestService.getSingleTrainJob(params, true)
          .then((res) => {
            if (
              !res ||
            !res.data ||
            !res.data.train_jobs ||
            !res.data.train_jobs.length
            ) {
              return;
            }
            if (res.data && res.data.error_code) {
              this.$message.error(
                  `${res.data.error_code} : ${
                    this.$t('error')[res.data.error_code]
                  }`,
              );
              return;
            }
            let dataList = [];
            const tempRunList = [];
            const data = res.data.train_jobs;
            data.forEach((runObj, runObjectIndex) => {
              tempRunList.push({
                id: runObj.id,
                label: runObj.name,
              });

              runObj.tags.forEach((tagObj) => {
                let sameTagIndex = -1;
                dataList.some((imageTagItem, curIndex) => {
                  if (imageTagItem.tagName === tagObj) {
                    sameTagIndex = curIndex;
                    return true;
                  }
                });
                if (sameTagIndex === -1) {
                  dataList.push({
                    tagName: tagObj,
                    runNames: [runObj.name],
                    runId: [runObj.id],
                    colors: [],
                  });
                } else {
                  const sameTagObj = dataList[sameTagIndex];
                  sameTagObj.runNames.push(runObj.name);
                  sameTagObj.runId.push(runObj.id);
                }
              });
            });
            this.runList = tempRunList;
            if (dataList.length) {
              dataList = dataList.slice(0, 2);
              this.curPageArr = dataList;
              this.updateTagInPage();
            }
          }, this.errorScalar)
          .catch((e) => {});
    },
    /**
     * Update tag
     */
    updateTagInPage() {
      const ajaxArr = [];
      this.curPageArr.forEach((sampleObject, yIndex) => {
        const runCount = sampleObject.runId.length;
        if (runCount === 0) {
          return;
        }
        const params = {
          train_id: sampleObject.runId[0],
          tag: sampleObject.tagName,
        };

        ajaxArr.push(this.addAjax(params, yIndex));
      });

      Promise.all(ajaxArr).then((res) => {
        if (!res) {
          return;
        }
        this.charData = [];
        for (let i = 0; i < res.length; i++) {
          if (!res[i] || !res[i].data) {
            return;
          }
          const resData = res[i].data;
          const tempObject = {
            valueData: {
              stepData: [],
              absData: [],
              relativeData: [],
            },
            yAxisIndex: res[i].yIndex,
            color: CommonProperty.commonColorArr[this.colorNum]
              ? CommonProperty.commonColorArr[this.colorNum]
              : CommonProperty.commonColorArr[this.defColorCount - 1],
            tagName: res[i].params.tag,
          };
          let relativeTimeBench = 0;
          if (resData.metadatas.length) {
            relativeTimeBench = resData.metadatas[0].wall_time;
          }
          resData.metadatas.forEach((metaData) => {
            tempObject.valueData.stepData.push([metaData.step, metaData.value]);
            tempObject.valueData.absData.push([
              metaData.wall_time,
              metaData.value,
            ]);
            tempObject.valueData.relativeData.push([
              metaData.wall_time - relativeTimeBench,
              metaData.value,
            ]);
          });
          this.colorNum++;
          this.charData.push(tempObject);
        }
        this.charOption = this.formateCharOption();
        this.colorNum = 0;
        this.updateOrCreateChar();
      });
    },
    /**
     * formate smooth data
     * @param {Object} oriData Original data
     * @return {Object}
     */
    formateSmoothData(oriData) {
      if (!oriData || oriData.length < 2) {
        return oriData;
      }
      const data = JSON.parse(JSON.stringify(oriData));
      const oriDataLength = oriData.length;
      let last = 0;
      const smoothValue = 0;
      let numAccun = 0;
      const firstValue = data[0][1];
      const isAllSame = data.every((curData) => {
        return curData[1] === firstValue;
      });
      for (let i = 0; i < oriDataLength; i++) {
        const curValue = data[i][1];
        if (!isAllSame && Number.isFinite(curValue)) {
          last = last * smoothValue + (1 - smoothValue) * curValue;
          numAccun++;
          let debiasWeight = 1;
          if (smoothValue !== 1) {
            debiasWeight = 1 - Math.pow(smoothValue, numAccun);
          }
          data[i][1] = last / debiasWeight;
        }
      }
      return data;
    },
    /**
     * Updating or Creating a Specified chart
     * @param {Boolen} resetAnimate restart the animation
     */
    updateOrCreateChar(resetAnimate) {
      if (this.charObj) {
        this.charObj.setOption(this.charOption, true);
        return;
      }
      if (document.getElementById('module-chart')) {
        this.charObj = echarts.init(
            document.getElementById('module-chart'),
            null,
        );
        this.charObj.setOption(this.charOption, true);
      }
    },

    /**
     * Formatting Chart Data
     * @return {Object}
     */
    formateCharOption() {
      const seriesData = [];
      const legendData = [];

      const yAxis = [];
      this.curPageArr.forEach((sampleObject) => {
        const yAxisData = {
          type: 'value',
          scale: true,
          axisLine: {
            lineStyle: {
              color: '#E6EBF5',
              width: 2,
            },
          },
          axisLabel: {
            color: '#9EA4B3',
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
        };
        yAxis.push(yAxisData);
      });
      this.charData.forEach((tempObj, runNameIndex) => {
        const dataObj = {
          name: tempObj.tagName,
          data: [],
          type: 'line',
          showSymbol: false,
          lineStyle: {
            color: tempObj.color,
          },
          color: tempObj.color,
          yAxisIndex: tempObj.yAxisIndex,
        };

        dataObj.data = this.formateSmoothData(tempObj.valueData['stepData']);
        seriesData.push(dataObj);
        legendData.push(dataObj.name);
      });

      const tempOption = {
        legend: {
          data: legendData,
          selectedMode: false,
          icon: 'circle',
          bottom: 0,
        },
        grid: {
          top: 20,
          bottom: 66,
          left: 60,
          right: 60,
        },
        xAxis: [
          {
            type: 'value',
            show: true,
            scale: true,
            nameGap: 30,
            minInterval: 1,
            axisLine: {
              lineStyle: {
                color: '#E6EBF5',
                width: 2,
              },
            },
            axisLabel: {
              color: '#9EA4B3',
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
        ],
        yAxis: yAxis,
        animation: true,

        series: seriesData,
      };
      return tempOption;
    },

    /**
     * Adding Ajax Data
     * @param {Object} params Input parameters of the request background interface
     * @param {Number} yIndex Coordinates of the Y-axis of the echart chart.
     * @return {Object}
     */
    addAjax(params, yIndex) {
      return new Promise((resolve, reject) => {
        RequestService.getScalarsSample(params)
            .then((res) => {
              if (res) {
                res.params = params;
                res.yIndex = yIndex;
                resolve(res);
              }
            })
            .catch((error) => {
              if (error) {
                reject(error);
              }
            });
      });
    },
    /**
     * Process image data
     * @param {Array} tags
     */
    dealImageData(tags) {
      if (!tags.length) {
        this.curImageShowSample = {};
        this.originImageDataArr = [];
        return;
      }
      if (JSON.stringify(this.curImageShowSample) !== '{}') {
        if (tags.indexOf(this.curImageShowSample.tagName) !== -1) {
          this.updateImageSample();
          return;
        }
      }
      const dataList = [];
      tags.forEach((tagName) => {
        const sampleItem = {
          runId: this.trainingJobId,
          tagName: tagName,
          sampleData: [],
          curImgUrl: '',
        };
        dataList.push(sampleItem);
      });
      this.originImageDataArr = dataList;
      this.getSampleRandomly();
    },
    getHistogramTag(tagList) {
      if (!tagList) {
        return;
      }
      let histogramTag = '';
      if (!this.histogramTag || tagList.indexOf(this.histogramTag) === -1) {
        histogramTag = tagList[0] || '';
      } else {
        histogramTag = this.histogramTag;
      }
      if (!histogramTag) {
        return;
      }
      const params = {
        train_id: this.trainingJobId,
        tag: histogramTag,
      };
      // tag
      RequestService.getHistogramData(params).then((res) => {
        if (
          !res ||
          !res.data ||
          !res.data.histograms ||
          !res.data.histograms.length
        ) {
          return;
        }
        const data = res.data;
        this.histogramTag = histogramTag;
        this.histogramData = this.formOriData(data);
        const charOption = this.formatDataToChar();
        this.updateHistogramSampleData(charOption);
      });
    },
    formOriData(dataItem) {
      const chartData = [];
      dataItem.histograms.forEach((histogram, index) => {
        const chartItem = {
          wall_time: histogram.wall_time,
          step: histogram.step,
          items: [],
        };
        const chartArr = [];
        histogram.buckets.forEach((bucket) => {
          const xData = bucket[0] + bucket[1] / 2;
          const filter = chartArr.filter((k) => k[0] === xData);
          if (!filter.length) {
            chartArr.push([
              histogram.wall_time,
              histogram.step,
              xData,
              Math.floor(bucket[2]),
            ]);
          }
        });
        chartArr.sort((a, b) => a[0] - b[0]);
        if (chartArr.length) {
          const minItem = chartArr[0][2];
          const maxItem = chartArr[chartArr.length - 1][2];
          const chartAll = [
            [histogram.wall_time, histogram.step, minItem, 0],
          ].concat(chartArr, [
            [histogram.wall_time, histogram.step, maxItem, 0],
          ]);
          chartItem.items = chartAll;
          chartData.push(chartItem);
        }
      });
      return {tag: dataItem.tag, train_id: dataItem.train_id, chartData};
    },
    formatDataToChar() {
      const dataItem = this.histogramData;
      const seriesData = [];
      let maxStep = -Infinity;
      let minStep = Infinity;
      let maxX = -Infinity;
      let minX = Infinity;
      let maxZ = -Infinity;
      let minZ = Infinity;
      if (dataItem.chartData && dataItem.chartData.length) {
        dataItem.chartData.forEach((histogram) => {
          const seriesItem = [];
          maxStep = Math.max(maxStep, histogram.step);
          minStep = Math.min(minStep, histogram.step);
          histogram.items.sort((a, b) => a[0] - b[0]);
          histogram.items.forEach((bucket) => {
            seriesItem.push(bucket[2], histogram.step, bucket[3]);
            maxX = Math.max(maxX, bucket[2]);
            minX = Math.min(minX, bucket[2]);
            minZ = Math.min(minZ, bucket[3]);
            maxZ = Math.max(maxZ, bucket[3]);
          });
          seriesData.push(seriesItem);
        });
      }
      return {
        seriesData,
        maxStep,
        minStep,
        maxX,
        minX,
        maxZ,
        minZ,
      };
    },
    formatCharOption(charOption) {
      const option = {
        grid: {
          left: 15,
          top: 126,
          right: 40,
          bottom: 60,
        },
        color: ['#346E69'],
        xAxis: {
          max: charOption.maxX,
          min: charOption.minX,
          axisLine: {onZero: false},
          axisLabel: {
            fontSize: '11',
            formatter: function(value) {
              return Math.round(value * 100) / 100;
            },
          },
          splitLine: {show: false},
        },
        yAxis: {
          position: 'right',
          axisLine: {onZero: false, show: false},
          splitLine: {show: true},
          inverse: true,
          axisTick: {show: false},
          axisLabel: {
            fontSize: '11',
          },
        },
        visualMap: {
          type: 'continuous',
          show: false,
          min: charOption.minStep,
          max: charOption.maxStep,
          dimension: 1,
          range: [charOption.minStep, charOption.maxStep],
          inRange: {
            colorLightness: [0.3, 0.9],
          },
        },
        series: [
          {
            type: 'custom',
            dimensions: ['x', 'y'],
            renderItem: (params, api) => {
              const points = this.makePolyPoints(
                  params.dataIndex,
                  api.coord,
                  params.coordSys.y - 10,
                  charOption,
              );

              return {
                type: 'polyline',
                silent: true,
                shape: {
                  points,
                },
                style: api.style({
                  stroke: '#bbb',
                  lineWidth: 1,
                }),
              };
            },
            data: charOption.seriesData,
          },
        ],
      };
      return option;
    },
    /**
     * update sample data
     * @param {Object} charOption data
     */
    updateHistogramSampleData(charOption) {
      this.histogramOption = this.formatCharOption(charOption);
      setTimeout(() => {
        if (!this.histogramObj) {
          this.histogramObj = echarts.init(
              document.getElementById('distribution-chart'),
              null,
          );
        }
        this.histogramObj.setOption(this.histogramOption, true);
      }, 100);
    },
    getValue(seriesData, dataIndex, i) {
      return seriesData[dataIndex][i];
    },
    makePolyPoints(dataIndex, getCoord, yValueMapHeight, charOption) {
      const points = [];
      const rawData = charOption.seriesData;
      const maxZ = charOption.maxZ;
      const minZ = charOption.minZ;
      for (let i = 0; i < rawData[dataIndex].length; ) {
        const x = this.getValue(rawData, dataIndex, i++);
        const y = this.getValue(rawData, dataIndex, i++);
        const z = this.getValue(rawData, dataIndex, i++);
        const pt = getCoord([x, y]);
        // linear map in z axis
        pt[1] -= ((z - minZ) / (maxZ - minZ)) * yValueMapHeight;
        points.push(pt);
      }
      return points;
    },
    /**
     * errorScalar
     * @param {Object} error Error Object
     */
    errorScalar(error) {
      if (error.response && error.response.data) {
        this.scalarClearAllData();
      } else {
        if (
          !(error.code === 'ECONNABORTED' && /^timeout/.test(error.message))
        ) {
          // Clear Display Data
          this.scalarClearAllData();
        }
      }
    },
    /**
     * Clears the scalar data.
     */
    scalarClearAllData() {
      this.colorNum = 0;
      this.charObj = null;
      this.curPageArr = [];
      this.charOption = {};
      this.charData = [];
    },

    /**
     * Obtain a picture randomly.
     */
    getSampleRandomly() {
      if (this.originImageDataArr.length) {
        if (this.originImageDataArr.length > 1) {
          const sampleIndex = Math.floor(
              Math.random() * this.originImageDataArr.length,
          );
          const curSample = this.originImageDataArr[sampleIndex];
          if (
            curSample.tagName !== this.curImageShowSample.tagName ||
            this.imageRandomLoopCount >= 15
          ) {
            this.curImageShowSample = curSample;
            this.imageRandomLoopCount = 0;
          } else {
            this.imageRandomLoopCount++;
            this.getSampleRandomly();
            return;
          }
        } else {
          this.imageRandomLoopCount = 0;
          this.curImageShowSample = this.originImageDataArr[0];
        }
      } else {
        this.imageRandomLoopCount = 0;
        this.curImageShowSample = {};
      }
      // Updating Image Data
      this.updateImageSample();
    },

    /**
     * Updating Image Data.
     */
    updateImageSample() {
      if (JSON.stringify(this.curImageShowSample) === '{}') {
        return;
      }
      const sampleItem = this.curImageShowSample;
      const params = {
        train_id: sampleItem.runId,
        tag: sampleItem.tagName,
      };
      RequestService.getImageMetadatas(params)
          .then(
              (res) => {
                if (!res || !res.data || !res.data.metadatas) {
                  return;
                }
                if (
                  sampleItem.runId !== this.curImageShowSample.runId ||
              sampleItem.tagName !== this.curImageShowSample.tagName
                ) {
                  return;
                }
                // Processes image data
                const tempData = res.data.metadatas;
                sampleItem.sampleData = tempData;
                // Initialize the current step information
                if (sampleItem.sampleData.length) {
                  const sampleIndex = sampleItem.sampleData.length - 1;
                  const sampleStep = sampleItem.sampleData[sampleIndex].step;
                  const sampleWallTime =
                sampleItem.sampleData[sampleIndex].wall_time;
                  sampleItem.curImgUrl =
                `${basePath}${this.imageBasePath}` +
                `train_id=${sampleItem.runId}&tag=${sampleItem.tagName}` +
                `&step=${sampleStep}&wt=${sampleWallTime}`;
                } else {
                  this.curImageShowSample = {};
                }
              },
              (err) => {
                this.curImageShowSample = {};
              },
          )
          .catch((e) => {
            this.$message.error(this.$t('public.dataError'));
          });
    },

    /**
     * The image page is displayed.
     * @param {Object} event
     */
    linkToImage(event) {
      if (!this.originImageDataArr.length) {
        return;
      }
      if (this.originImageDataArr.length === 1) {
        const bool = event.path.some((dom) => {
          if (dom.className) {
            return dom.className.indexOf('el-button') !== -1;
          }
        });
        if (bool) {
          return;
        }
      }
      this.$router.push({
        path: '/train-manage/image',
        query: {
          id: this.trainingJobId,
        },
      });
    },

    /**
     * Change a picture.
     * @param {Object} event Native event event
     */
    changeImage(event) {
      event.stopPropagation();
      event.preventDefault();
      this.getSampleRandomly();
    },
    // Sampling data end
    /**
     * Initializing the graph
     * @param {String} dot dot statement encapsulated in graph data
     */
    initGraph(dot) {
      this.graphviz = d3
          .select('#graph')
          .graphviz({useWorker: false, totalMemory: this.totalMemory})
          .dot(dot)
          .attributer(this.attributer)
          .render(() => {
            if (d3.select('#graph svg')) {
              d3.select('#graph svg').on('.zoom', null);
            }
            d3.selectAll('#graph title').remove();
            setTimeout(() => {
              this.graphviz._data = null;
              this.graphviz._dictionary = null;
              this.graphviz = null;
            }, 200);
          });
    },
    /**
     * To obtain graph data, initialize and expand the namespace or aggregate nodes.
     */
    queryGraphData() {
      const params = {
        train_id: this.trainingJobId,
        type: 'name_scope',
        tag: this.fileTag,
      };
      RequestService.queryGraphData(params)
          .then(
              (response) => {
                if (response && response.data && response.data.nodes) {
                  const nodes = response.data.nodes;
                  if (nodes && nodes.length) {
                    this.packageDataToObject(nodes);
                    const dot = this.packageGraphData();
                    this.initGraph(dot);
                  }
                }
              },
              (error) => {},
          )
          .catch((e) => {});
    },
    /**
     * Processes its own and corresponding child node data when expanding or closing namespaces.
     * @param {Array} nodes Node array
     */
    packageDataToObject(nodes) {
      this.allGraphData = {};
      this.firstFloorNodes = [];
      nodes.forEach((node) => {
        this.allGraphData[node.name] = node;
        this.firstFloorNodes.push(node.name);
      });
    },
    /**
     * Obtains the subnode data of the namespace through the namespace name.
     * @return {Array} Subnode array of the namespace.
     */
    getChildNodesByName() {
      const nameList = this.firstFloorNodes;
      const nodes = nameList.map((i) => {
        return this.allGraphData[i];
      });
      return nodes;
    },
    /**
     * Encapsulates graph data into dot data.
     * @return {String} dot string for packing graph data
     */
    packageGraphData() {
      const initSetting =
        'node[style="filled";fontsize="10px"];edge[fontsize="6px";];';
      return `digraph {${initSetting}${this.packageNodes()}${this.packageEdges()}}`;
    },
    /**
     * Encapsulates node data into dot data.
     * @return {String} dot String that are packed into all nodes
     */
    packageNodes() {
      const nodes = this.getChildNodesByName();
      let tempStr = '';
      nodes.forEach((node) => {
        const name = node.name.split('/').pop();
        // Different types of nodes are generated for different data types.
        if (node.type === 'polymeric_scope') {
          tempStr +=
            `<${node.name}>[id="${node.name}";shape="octagon";` +
            `label="${name}";class="polymeric"];`;
        } else if (node.type === 'name_scope') {
          const fillColor = CommonProperty.graphColorArr[this.curColorIndex];
          this.curColorIndex = this.curColorIndex % 4;
          this.curColorIndex++;
          tempStr +=
            `<${node.name}>[id="${node.name}";fillcolor="${fillColor}";` +
            `shape="polygon";label="${name}";class="cluster"];`;
        } else if (node.type === 'Const') {
          tempStr +=
            `<${node.name}>[id="${node.name}";label="${name}\n\n\n";` +
            `shape="circle";width="0.14";height="0.14";fixedsize=true;];`;
        } else {
          tempStr +=
            `<${node.name}>[id="${node.name}";shape="ellipse";` +
            `label="${name}";];`;
        }
        // A maximum of five virtual nodes can be displayed. Other virtual nodes are displayed in XXXmore.
        // The ID of the omitted aggregation node is analogNodesInput||analogNodeOutput^nodeId.
        // After the namespace or aggregation node is expanded, the virtual node does not need to be displayed.
        let keys = Object.keys(node.polymeric_input || {});
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

        keys = Object.keys(node.polymeric_output || {});
        source = node.name;
        for (let i = 0; i < Math.min(5, keys.length); i++) {
          target = keys[i];
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
      });
      return tempStr;
    },
    /**
     * Encapsulates node data into dot data.
     * @return {String} dot string packaged by all edges
     */
    packageEdges() {
      const nodes = this.getChildNodesByName();
      let tempStr = '';
      const edges = [];
      nodes.forEach((node) => {
        const input = node.input || {};
        const keyList = Object.keys(input);
        keyList.forEach((key) => {
          if (input[key]) {
            // Cannot connect to the sub-nodes in the aggregation node and
            // cannot be directly connected to the aggregation node.
            // It can only connect to the outer namespace of the aggregation node.
            // If there is no namespace in the outer layer,
            // you do not need to connect cables. Other connections are normal.
            const temp =
              input[key].scope === 'polymeric_scope'
                ? key.substring(0, key.lastIndexOf('/'))
                : key;
            const source = temp.split('/')[0];
            const target =
              node.type === 'polymeric_scope' || node.polymeric_scope_name
                ? `${node.name.substring(0, node.name.lastIndexOf('/'))}`
                : node.name;
            // The namespace is not nested.
            if (
              source &&
              target &&
              !target.includes(source) &&
              !source.includes(target)
            ) {
              const obj = {
                source: source,
                target: target,
                shape: input[key].shape,
                edge_type: input[key].edge_type,
                count: 1,
              };
              edges.push(obj);
            }
          }
        });

        let keys = Object.keys(node.polymeric_input || {});
        for (let i = 0; i < Math.min(5, keys.length); i++) {
          const target = node.name;
          const source = keys[i];
          const obj = {
            source: `${source}^${target}`,
            target: target,
            shape: [],
            edge_type:
              node.type !== 'polymeric_scope' && !node.polymeric_scope_name
                ? 'polymeric'
                : '',
            count: 1,
          };
          edges.push(obj);
        }
        if (keys.length > 5) {
          const obj = {
            source: `analogNodesInput^${node.name}`,
            target: node.name,
            shape: [],
            edge_type:
              node.type !== 'polymeric_scope' && !node.polymeric_scope_name
                ? 'polymeric'
                : '',
            count: 1,
          };
          edges.push(obj);
        }

        keys = Object.keys(node.polymeric_output || {});
        for (let i = 0; i < Math.min(5, keys.length); i++) {
          const source = node.name;
          const target = keys[i];
          const obj = {
            source: source,
            target: `${target}^${source}`,
            shape: [],
            edge_type:
              node.type !== 'polymeric_scope' && !node.polymeric_scope_name
                ? 'polymeric'
                : '',
            count: 1,
          };
          edges.push(obj);
        }
        if (keys.length > 5) {
          const obj = {
            source: node.name,
            target: `analogNodesOutput^${node.name}`,
            shape: [],
            edge_type:
              node.type !== 'polymeric_scope' && !node.polymeric_scope_name
                ? 'polymeric'
                : '',
            count: 1,
          };
          edges.push(obj);
        }
      });

      this.uniqueEdges(edges);
      edges.forEach((edge) => {
        tempStr +=
          `<${edge.source}>-><${edge.target}>[id="${edge.source}->` +
          `${edge.target}";label="${this.getEdgeLabel(edge)}";` +
          `${edge.edge_type === 'control' ? 'style=dashed' : ''}];`;
      });
      return tempStr;
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
          const flag = edge.shape.some((i) => {
            return typeof i !== 'number';
          });
          if (flag) {
            label = `tuple(${edge.shape.length} items)`;
          } else {
            label = edge.shape.join('x');
          }
        }
      } else {
        label = `${edge.count}tensors`;
      }
      return label;
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

    /** ******************************** dataMap *****************************/
    /**
     * To obtain dataset graph data.
     */
    queryDatasetGraph() {
      const params = {
        train_id: this.trainingJobId,
      };
      RequestService.queryDatasetGraph(params)
          .then(
              (res) => {
                if (
                  res &&
              res.data &&
              res.data.dataset_graph &&
              Object.keys(res.data.dataset_graph).length
                ) {
                  const data = JSON.parse(JSON.stringify(res.data.dataset_graph));
                  this.dealDatasetGraph(data);
                  if (Object.keys(this.allDatasetGraphData).length) {
                    const dot = this.packageDatasetGraph();
                    this.initDatasetGraph(dot);
                  }
                }
              },
              (err) => {},
          )
          .catch((e) => {});
    },
    /**
     * Processing dataset Graph Data
     * @param {Object} data Data of the dataset graph
     * @param {String} parentKey Key value of the parent-level data.
     * @param {Number} index Index of a node.
     */
    dealDatasetGraph(data, parentKey = '', index = 0) {
      if (!data) {
        return;
      }
      const key = `${parentKey ? parentKey + '/' : ''}${data.op_type ||
        ''}_${index}`;
      const obj = {
        key: key,
        id: '',
      };
      Object.keys(data).forEach((k) => {
        {
          if (k !== 'children') {
            obj[k] = JSON.parse(JSON.stringify(data[k]));
          } else {
            obj.children = [];
            if (data.children && data.children.length) {
              data.children.forEach((data, ind) => {
                obj.children.push(`${obj.key}/${data.op_type}_${ind}`);
                this.dealDatasetGraph(data, obj.key, ind);
              });
            }
          }
        }
      });
      this.allDatasetGraphData[key] = obj;
    },
    /**
     * Encapsulates dataset graph data into dot data.
     * @return {String} dot string for packing dataset graph data
     */
    packageDatasetGraph() {
      const nodeType = [
        'BatchDataset',
        'ShuffleDataset',
        'RepeatDataset',
        'MapDataset',
      ];
      let nodeStr = '';
      let edgeStr = '';
      Object.keys(this.allDatasetGraphData).forEach((key) => {
        const node = this.allDatasetGraphData[key];
        if (node.op_type === 'MapDataset') {
          nodeStr += this.packageSubGraph(key);
        } else {
          node.id = key;
          nodeStr +=
            `<${node.key}>[id="${node.key}";label="${node.op_type}";` +
            `class=${
              nodeType.includes(node.op_type) ? node.op_type : 'CreatDataset'
            };shape=rect;fillcolor="#9cc3e5";];`;
        }
      });

      Object.keys(this.allDatasetGraphData).forEach((key) => {
        const node = this.allDatasetGraphData[key];
        node.children.forEach((k) => {
          const child = this.allDatasetGraphData[k];
          edgeStr += `<${child.id}>-><${node.id}>[${
            child.op_type === 'MapDataset'
              ? `ltail=<cluster_${child.key}>;`
              : ''
          }${
            node.op_type === 'MapDataset' ? `lhead=<cluster_${node.key}>;` : ''
          }];`;
        });
      });
      const initSetting =
        'node[style="filled";fontsize="10px"];edge[fontsize="6px";];';
      return `digraph {compound=true;rankdir=LR;${initSetting}${nodeStr}${edgeStr}}`;
    },

    /**
     * Encapsulates the data of a subgraph.
     * @param {String} key Key value of a node.
     * @return {String} dot string
     */
    packageSubGraph(key) {
      const node = this.allDatasetGraphData[key];
      let strTemp = '';
      if (node.operations && node.operations.length) {
        let nodeStr = '';
        node.operations.forEach((op, ind) => {
          const id = `${node.key}/${op.tensor_op_name}_${ind}`;
          op.key = id;
          nodeStr += `<${id}>[id="${id}";class=Operator;label="${op.tensor_op_name}";fillcolor="#c5e0b3"];`;
          if (!node.id) {
            node.id = id;
          }
        });
        strTemp +=
          `subgraph <cluster_${key}>{style="filled";id="${key}";` +
          `label="${node.op_type}";fillcolor="#9cc3e5";${nodeStr}};`;
      }
      return strTemp;
    },
    /**
     * Initializing the dataset graph
     * @param {String} dot dot statement encapsulated in dataset graph data
     */
    initDatasetGraph(dot) {
      this.datasetGraphviz = d3
          .select('#dataMapGraph')
          .graphviz({useWorker: false, totalMemory: this.totalMemory})
          .dot(dot)
          .attributer((datum, index, nodes) => {
            if (datum.tag === 'svg') {
              const width = '100%';
              const height = '100%';
              datum.attributes.width = width;
              datum.attributes.height = height;
            }
          })
          .render(this.afterinitDatasetGraph);
    },
    /**
     * Process other data after the dataset graph is initialized.
     */
    afterinitDatasetGraph() {
      this.showDatasetGraph = true;
      if (d3.select('#dataMapGraph svg')) {
        d3.select('#dataMapGraph svg').on('.zoom', null);
      }
      setTimeout(() => {
        if (this.datasetGraphviz) {
          this.datasetGraphviz._data = null;
          this.datasetGraphviz._dictionary = null;
          this.datasetGraphviz = null;
        }
      }, 100);
      d3.select('#dataMapGraph')
          .selectAll('title')
          .remove();
    },
  },
};
</script>
<style lang="scss" >
.cl-dashboard {
  height: 100%;
  overflow-y: auto;
  width: 100%;
  overflow: hidden;
  .cl-dashboard-top {
    width: 100%;
    padding-left: 32px;
    padding-right: 20px;
    height: 56px;
    vertical-align: middle;
    background: #ffffff;
    .cl-dashboard-top-title {
      float: left;
      color: #000000;
      font-weight: bold;
      font-size: 20px;
      line-height: 20px;
      padding: 18px 0;
    }
  }
  .cl-dashboard-center {
    width: calc(100% + 2px);
    margin: -1px;
    margin-top: 2px;
    height: calc(100% - 58px);
  }
  .title-height {
    height: 30px;
    line-height: 30px;
  }
  .cl-dashboard-title {
    font-size: 20px;
    color: #000000;
    line-height: 20px;
    font-weight: bold;
    margin-bottom: 1vw;
    height: 20px;
    display: flex;

    .cl-dashboard-title-left {
      font-size: 20px;
      color: #000000;
      line-height: 20px;
      font-weight: bold;
      flex: 1;
    }

    .cl-dashboard-title-right {
      height: 30px;
      flex: 1;
      overflow: hidden;
      text-align: right;
      .el-button {
        padding: 0px;
      }
    }
  }

  .cl-dashboard-con-up {
    background-color: #fff;
    padding: 1.6vw;
    cursor: pointer;
    overflow: hidden;
    height: calc(50% - 2px);
    width: calc(33.3% - 2px);
    margin: 1px;
    float: left;
  }

  .cl-module {
    height: calc(100% - 35px);
    overflow: hidden;

    .select-disable {
      -moz-user-select: none; /*Firefox*/
      -webkit-user-select: none; /*webkitbrowser*/
      -ms-user-select: none; /*IE10*/
      -khtml-user-select: none; /*Early browser*/
      user-select: none;
    }

    .cl-scalar-tagName {
      height: 22px;
      font-size: 14px;
      color: #333;
      z-index: 999;
      line-height: 22px;
      display: flex;
      font-weight: 600;
      .tagNameLeft {
        text-align: left;
        width: 49%;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .tagNameRight {
        text-align: right;
      }
    }

    .graph {
      height: 100%;
      background-color: #fff;
      #graph0 > polygon {
        fill: transparent;
      }
      .edge {
        path {
          stroke: rgb(167, 167, 167);
        }
        polygon {
          fill: rgb(167, 167, 167);
        }
      }

      .node.polymeric > polygon {
        stroke: #fdca5a;
        fill: #ffe8b5;
      }
      .node.cluster.polymeric > rect {
        stroke: #fdca5a;
        fill: #fff2d4;
        stroke-dasharray: 3, 3;
      }

      .node > polygon {
        stroke: #f45c5e;
        fill: #ffba99;
      }
      .node > ellipse {
        stroke: #58a4e0;
        fill: #d1ebff;
      }
      .plain > path,
      .plain ellipse {
        stroke: #56b077;
        fill: #c1f5d5;
        stroke-dasharray: 1.5, 1.5;
      }
    }

    .image-container {
      width: 100%;
      height: 100%;
      .sample-img {
        object-fit: contain;
        width: 100%;
        height: 100%;
      }
    }
  }

  .comming-soon-content {
    width: 100%;
    height: 100%;
    text-align: center;
    .comming-soon-container {
      position: relative;
      top: calc(50% - 88px);
      .comming-soon-text {
        color: #000000;
        font-size: 16px;
      }
    }
  }

  .no-data-hover {
    cursor: not-allowed;
  }

  .no-data-img {
    background: #fff;
    text-align: center;
    height: 100%;
    padding-top: 50px;
    img {
      max-width: 100%;
    }
    p {
      font-size: 16px;
      padding-top: 10px;
    }
  }
  // Public Style End

  #module-chart {
    height: calc(100% - 22px);
    canvas {
      cursor: pointer;
    }
  }
  #distribution-chart {
    height: calc(100% - 19px);
    canvas {
      cursor: pointer;
    }
  }
  .histogram-char-container {
    height: 100%;
    width: 100%;
    cursor: pointer;
    .tag-text {
      font-size: 12px;
      font-weight: 400;
      text-align: center;
    }
  }

  #dataMapGraph {
    .CreatDataset > polygon,
    .Operator > ellipse {
      stroke: #58a4e0;
      fill: #d1ebff;
    }
    .cluster > polygon {
      fill: #c1f5d5;
      stroke: #56b077;
    }
    .RepeatDataset > polygon {
      stroke: #fdca5a;
      fill: #fff2d4;
    }
    .ShuffleDataset > polygon {
      stroke: #f79666;
      fill: #fed78e;
    }
    .BatchDataset > polygon {
      stroke: #fa8e5a;
      fill: #ffcfb8;
    }
    .edge {
      path {
        stroke: rgb(167, 167, 167);
      }
      polygon {
        fill: rgb(167, 167, 167);
        stroke: rgb(167, 167, 167);
      }
    }
  }
}
</style>

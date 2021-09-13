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
  <div class="cl-compare-manage">

    <div class="compare-bk">
      <div class="cl-title cl-compare-title"
           v-show="originDataArr.length>0">
        <div class="cl-title-left">
          {{$t("summaryManage.comparePlate")}}</div>
      </div>

      <!--Operation area -->
      <div class="cl-eval-operate-content"
           v-show="originDataArr.length>0">

        <!--Summary select-->
        <div class="cl-eval-operate-component">
          <multiSelectGroupComponents ref="summaryGroup"
                                      :checkListArr="summaryOperateList"
                                      :isLimit="true"
                                      :limitNum="5"
                                      @selectedChange="summarySelectedChanged"
                                      :componentsLabel="componentsLabel.summary"></multiSelectGroupComponents>
        </div>

        <!--Tag select-->
        <div class="cl-eval-operate-component">
          <multiSelectGroupComponents ref="tagsGroup"
                                      :checkListArr="tagOperateList"
                                      @selectedChange="tagSelectedChanged"
                                      :componentsLabel="componentsLabel.tag"></multiSelectGroupComponents>
        </div>

      </div>
      <!-- Slider -->
      <div class="cl-eval-slider-operate-content"
           v-show="originDataArr.length>0">
        <div class="xaxis-title">{{$t('scalar.xAxisTitle')}}</div>
        <el-radio-group v-model="curAxisName"
                        fill="#00A5A7"
                        text-color="#FFFFFF"
                        size="small "
                        @change="timeTypeChange">
          <el-radio-button :label="$t('scalar.step')">
            {{$t('scalar.step')}}
          </el-radio-button>
          <el-radio-button :label="$t('scalar.relativeTime')">
            {{$t('scalar.relativeTime') + $t('symbols.leftbracket') + 's' + $t('symbols.rightbracket')}}
          </el-radio-button>
          <el-radio-button :label="$t('scalar.absoluteTime')">
            {{$t('scalar.absoluteTime')}}
          </el-radio-button>
        </el-radio-group>
        <div class="xaxis-title">{{$t('scalar.smoothness')}}</div>
        <el-slider v-model="smoothValue"
                   :step="0.01"
                   :max="0.99"
                   @input="updataInputValue"></el-slider>

        <el-input v-model="smoothValueNumber"
                  class="w60"
                  @input="smoothValueChange"
                  @blur="smoothValueBlur"></el-input>
      </div>
      <!-- Content display -->
      <div class="cl-eval-show-data-content"
           ref="miDataShoeContent">
        <!-- No data -->
        <div class="image-noData"
             v-if="!originDataArr.length">
          <div>
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
          </div>
          <div v-if="initOver"
               class="noData-text">{{$t('public.noData')}}</div>
          <div v-else
               class="noData-text">{{$t("public.dataLoading")}}</div>
        </div>
        <!-- Data -->
        <div class="data-content"
             v-if="originDataArr.length">
          <div class="sample-content"
               v-for="sampleItem in originDataArr"
               :key="sampleItem.domId"
               :class="sampleItem.fullScreen?'char-full-screen':''"
               :id="'view'+sampleItem.domId"
               v-show="sampleItem.show">
            <!-- Charts -->
            <div class="chars-container">
              <div class="char-item-content"
                   :id="sampleItem.domId"></div>
            </div>
            <!-- Tag name -->
            <div class="tag-name"
                 :title="sampleItem.tagName">{{sampleItem.tagName}}
              <el-tooltip v-if="sampleItem.invalidData"
                          class="item"
                          effect="dark"
                          :content="$t('scalar.invalidData')"
                          placement="top">
                <i class="el-icon-warning"></i>
              </el-tooltip>
            </div>
          </div>
        </div>
        <!-- page -->

      </div>
      <div class="pagination-content"
           v-if="originDataArr.length">
        <el-pagination @current-change="currentPageChange"
                       :current-page="pageIndex + 1"
                       :page-size="pageNum"
                       layout="total, prev, pager, next, jumper"
                       :total="curFilterSamples.length">
        </el-pagination>

      </div>

    </div>

  </div>
</template>
<script>
import echarts, {echartsThemeName} from '../../js/echarts';
import RequestService from '../../services/request-service';
import CommonProperty from '../../common/common-property';
import multiSelectGroupComponents from '../../components/multiselect-group.vue';
import autoUpdate from '../../mixins/auto-update.vue';

export default {
  mixins: [autoUpdate],
  data() {
    return {
      componentsLabel: {
        summary: {
          title: this.$t('components.summaryTitle'),
          placeholder: this.$t('components.trainFilterPlaceHolder'),
        },
        tag: {
          title: this.$t('components.tagSelectTitle'),
          placeholder: this.$t('components.tagFilterPlaceHolder'),
        },
      },
      firstNum: 0, // First num
      isActive: 0, // Horizontal axis selected value
      initOver: false, // Indicates whether the initialization is complete
      charResizeTimer: null, // Delay after the window size is changed
      multiSelectedSummaryNames: {}, // Selected summary name
      multiSelectedTagNames: {}, // Selected tag name
      curFilterSamples: [], // Chart subscript
      summaryOperateList: [], // Array selected by summary
      tagOperateList: [], // Array selected by tag
      smoothValue: 0, // Initial smoothness of the slider
      smoothValueNumber: 0,
      smoothSliderValueTimer: null, // Smoothness slider timer
      // Number of predefined colors
      defColorCount: CommonProperty.commonColorArr[this.$store.state.themeIndex].length,
      curAvlColorIndexArr: [], // Color subscript
      DomIdIndex: 0, // DomId num
      originDataArr: [], // Original data
      oriDataDictionaries: {}, // Dictionary that contains all the current tags
      curPageArr: [], // Data of the current page
      pageIndex: 0, // Current page number
      pageNum: 6, // Number of records per page
      backendString: 'comparePlate', // Background layer suffix
      curBenchX: 'stepData', // Front axle reference
      curAxisName: this.$t('scalar.step'), // Current chart tip
      axisBenchChangeTimer: null, // Horizontal axis reference switching timing
      themeIndex: this.$store.state.themeIndex,
    };
  },

  destroyed() {
    // Remove the size of a window and change the listener
    window.removeEventListener('resize', this.resizeCallback);

    // Remove axisBench value change timing
    if (this.axisBenchChangeTimer) {
      clearTimeout(this.axisBenchChangeTimer);
      this.axisBenchChangeTimer = null;
    }

    // Remove slider value change timing
    if (this.smoothSliderValueTimer) {
      clearTimeout(this.smoothSliderValueTimer);
      this.smoothSliderValueTimer = null;
    }

    // Remove Chart Calculation Delay
    if (this.charResizeTimer) {
      clearTimeout(this.charResizeTimer);
      this.charResizeTimer = null;
    }

    this.originDataArr.forEach((sampleObject) => {
      if (sampleObject.dataZoomYTimer) {
        clearTimeout(sampleObject.dataZoomYTimer);
      }
      if (sampleObject.dataZoomXTimer) {
        clearTimeout(sampleObject.dataZoomXTimer);
      }
    });
  },
  mounted() {
    document.title = `${this.$t('summaryManage.comparePlate')}-MindInsight`;
    this.$nextTick(() => {
      // Adding a listener
      window.addEventListener('resize', this.resizeCallback, false);

      // Initialize available colors
      this.initAvlColorArr();

      // Initializing data
      this.getScalarsList();

      this.firstNum = 1;

      // Auto refresh
      if (this.isTimeReload) {
        this.autoUpdateSamples();
      }
    });
  },
  methods: {
    /**
     * Obtain the tag and summary list
     */
    getScalarsList() {
      const params = {};
      params.offset = 0;
      params.limit = 999;

      RequestService.querySummaryList(params)
          .then((res) => {
          // Error
            if (!res || !res.data || !res.data.train_jobs || !res.data.train_jobs.length) {
              this.initOver = true;
              return;
            }
            const tempSummaryList = [];
            const tempTagList = [];
            const dataList = [];
            const data = res.data.train_jobs.filter((item) => {
              return item.summary_files > 0;
            });
            if (!data.length) {
              this.initOver = true;
              return;
            }
            data.forEach((summaryObj, summaryIndex) => {
              const colorIndex = this.curAvlColorIndexArr.length
              ? this.curAvlColorIndexArr.shift()
              : this.defColorCount - 1;
              const summaryNmeColor = CommonProperty.commonColorArr[this.$store.state.themeIndex][colorIndex];

              tempSummaryList.push({
                label: summaryObj.train_id,
                checked: true,
                show: true,
                color: summaryNmeColor,
                colorIndex: colorIndex,
              });

              tempSummaryList.forEach((item) => {
                if (item.label === summaryObj.train_id) {
                  item.loading = summaryObj.cache_status;
                }
              });

              summaryObj.plugins.scalar.forEach((tagObj) => {
              // Tag with the same name exists

                let sameTagIndex = -1;
                dataList.some((tagItem, curIndex) => {
                  if (tagItem.tagName === tagObj) {
                    sameTagIndex = curIndex;
                    return true;
                  }
                });

                if (!this.oriDataDictionaries[tagObj]) {
                // Add the tag list
                  this.oriDataDictionaries[tagObj] = true;
                  tempTagList.push({
                    label: tagObj,
                    checked: true,
                    show: true,
                  });

                  const sampleIndex = dataList.length;

                  // Adding chart data
                  dataList.push({
                    tagName: tagObj,
                    summaryNames: [summaryObj.train_id],
                    colors: [summaryNmeColor],
                    show: false,
                    updateFlag: false,
                    dataRemove: false,
                    fullScreen: false,
                    sampleIndex: sampleIndex,
                    domId: 'prDom' + this.DomIdIndex,
                    charData: {
                      oriData: [],
                      charOption: {},
                    },
                    zoomData: [null, null],
                    zoomDataX: [null, null],
                    zoomDataYTimer: null,
                    zoomDataXTimer: null,
                    charObj: null,
                  });

                  this.DomIdIndex++;
                } else {
                  const sameTagObj = dataList[sameTagIndex];
                  sameTagObj.summaryNames.push(summaryObj.train_id);
                  sameTagObj.colors.push(summaryNmeColor);
                }
              });
            });
            this.summaryOperateList = tempSummaryList;

            this.tagOperateList = tempTagList;
            if (dataList.length === 1) {
              dataList[0].fullScreen = true;
            }
            this.originDataArr = dataList;
            this.initOver = true;

            this.$nextTick(() => {
              this.multiSelectedTagNames = this.$refs.tagsGroup.updateSelectedDic();
              this.multiSelectedSummaryNames = this.$refs.summaryGroup.updateSelectedDic();
              this.updateTagInPage();
              this.resizeCallback();
              if (Object.keys(this.multiSelectedSummaryNames).length > 0) {
                this.trainJobsCaches();
              }
            });
          })
          .catch((e) => {
            this.requestErrorCallback(e);
          });
    },

    trainJobsCaches() {
      const params = {};
      params.train_ids = Object.keys(this.multiSelectedSummaryNames);
      RequestService.trainJobsCaches(params);
    },

    /**
     * Obtains data on a specified page
     * @param {Boolean} noPageIndexChange // The page number does not change
     */

    getCurPageDataArr(noPageIndexChange) {
      if (!noPageIndexChange) {
        this.curPageArr.forEach((sampleItem) => {
          sampleItem.show = false;
        });
      }

      const startIndex = this.pageIndex * this.pageNum;
      const endIndex = startIndex + this.pageNum;
      const curPageArr = [];

      for (let i = startIndex; i < endIndex; i++) {
        const sampleItem = this.curFilterSamples[i];
        if (sampleItem) {
          sampleItem.updateFlag = true;
          sampleItem.show = true;
          curPageArr.push(sampleItem);
        }
      }
      this.curPageArr = curPageArr;
      this.updateCurPageSamples();
    },

    /**
     * Load the data on the current page
     */

    updateCurPageSamples() {
      this.curPageArr.forEach((sampleObject) => {
        if (!sampleObject) {
          return;
        }
        sampleObject.updateFlag = true;
        const sampleIndex = sampleObject.sampleIndex;
        const summaryCount = sampleObject.summaryNames.length;
        if (summaryCount === 0) {
          return;
        }

        const params = {
          train_id: '',
          tag: sampleObject.tagName,
        };

        for (let i = 0; i < summaryCount; i++) {
          if (i === summaryCount - 1) {
            params.train_id += encodeURIComponent(sampleObject.summaryNames[i]);
          } else {
            params.train_id += encodeURIComponent(sampleObject.summaryNames[i]) + '&';
          }
        }

        RequestService.getSummarySample(params)
            .then((res) => {
              if (sampleObject.charObj) {
                sampleObject.charObj.showLoading();
              }
              let scalarIndex = 0;
              let hasInvalidData = false;
              if (!res || !res.data || !res.data.scalars) {
                return;
              }
              const resData = res.data.scalars;
              resData.forEach((scalarItem) => {
                const tempObject = {
                  valueData: {
                    stepData: [],
                    absData: [],
                    relativeData: [],
                  },
                  logData: {
                    stepData: [],
                    absData: [],
                    relativeData: [],
                  },
                };
                let relativeTimeBench = 0;
                if (scalarItem.values.length) {
                  relativeTimeBench = scalarItem.values[0].wall_time;
                }
                // Initializing chart data
                scalarItem.values.forEach((metaData) => {
                  if (metaData.value === null && !hasInvalidData) {
                    hasInvalidData = true;
                  }

                  tempObject.valueData.stepData.push([metaData.step, metaData.value]);
                  tempObject.valueData.absData.push([metaData.wall_time, metaData.value]);
                  tempObject.valueData.relativeData.push([metaData.wall_time - relativeTimeBench, metaData.value]);
                  const logValue = metaData.value >= 0 ? metaData.value : '';
                  tempObject.logData.stepData.push([metaData.step, logValue]);
                  tempObject.logData.absData.push([metaData.wall_time, logValue]);
                  tempObject.logData.relativeData.push([metaData.wall_time - relativeTimeBench, logValue]);
                });

                sampleObject.charData.oriData[scalarIndex] = tempObject;
                scalarIndex++;
              });

              if (hasInvalidData) {
                this.$set(this.originDataArr[sampleIndex], 'invalidData', true);
              }
              sampleObject.charData.charOption = this.formateCharOption(sampleIndex);

              this.$nextTick(() => {
                if (sampleObject.charObj) {
                  sampleObject.charObj.hideLoading();
                }

                // Draw chart
                this.updateOrCreateChar(sampleIndex);
              });
            })
            .catch((error) => {});
      });
    },

    /**
     * Formatting chart data
     * @param {Number} sampleIndex Chart subscript
     * @return {Object} Echar option
     */

    formateCharOption(sampleIndex) {
      const sampleObject = this.originDataArr[sampleIndex];
      if (!sampleObject) {
        return;
      }
      let returnFlag = false;
      const seriesData = [];
      const legendSelectData = {};
      const oriData = sampleObject.charData.oriData;
      const legendData = [];

      sampleObject.summaryNames.forEach((summaryName, summaryIndex) => {
        const curBackName = summaryName + this.backendString;
        const dataObj = {
          name: summaryName,
          data: [],
          type: 'line',
          showSymbol: false,
          color: sampleObject.colors[summaryIndex],
        };
        const dataObjBackend = {
          name: curBackName,
          data: [],
          type: 'line',
          smooth: 0,
          symbol: 'none',
          lineStyle: {
            color: sampleObject.colors[summaryIndex],
            opacity: 0.2,
          },
        };

        const curOriData = oriData[summaryIndex];

        if (curOriData) {
          if (sampleObject.log) {
            dataObj.data = this.formateSmoothData(curOriData.logData[this.curBenchX]);
            dataObjBackend.data = curOriData.logData[this.curBenchX];
          } else {
            dataObj.data = this.formateSmoothData(curOriData.valueData[this.curBenchX]);
            dataObjBackend.data = curOriData.valueData[this.curBenchX];
          }
        } else {
          returnFlag = true;
        }
        if (this.multiSelectedSummaryNames[summaryName]) {
          legendSelectData[summaryName] = true;
          legendSelectData[curBackName] = true;
        } else {
          legendSelectData[summaryName] = false;
          legendSelectData[curBackName] = false;
        }
        const onePoint = 1;
        if (dataObj.data.length === onePoint) {
          dataObj.showSymbol = true;
        }
        seriesData.push(dataObj, dataObjBackend);
      });
      if (returnFlag) {
        return;
      }
      const that = this;
      const fullScreenFun = this.toggleFullScreen;
      const yAxisFun = this.yAxisScale;
      const tempOption = {
        legend: {
          show: false,
          data: legendData,
          selected: legendSelectData,
        },
        xAxis: {
          type: 'value',
          show: true,
          scale: true,
          nameGap: 30,
          minInterval: this.isActive === 0 ? 1 : 0,
          axisLabel: {
            interval: 0,
            formatter: (value) => {
              if (sampleObject.zoomDataXTimer) {
                clearTimeout(sampleObject.zoomDataXTimer);
                sampleObject.zoomDataXTimer = setTimeout(() => {
                  sampleObject.zoomDataXTimer = null;
                  this.calIfOnePoint(sampleObject);
                }, 50);
                if (value < sampleObject.zoomDataX[0]) {
                  sampleObject.zoomDataX[0] = value;
                } else if (sampleObject.zoomDataX[1] < value) {
                  sampleObject.zoomDataX[1] = value;
                }
              } else {
                sampleObject.zoomDataX = [value, value];
                sampleObject.zoomDataXTimer = setTimeout(() => {
                  sampleObject.zoomDataXTimer = null;
                }, 50);
              }
              if (that.isActive === 2) {
                // absolute
                if (sampleObject.fullScreen) {
                  const date = new Date(value * 1000);
                  const dateTime = date.toTimeString().split(' ')[0];
                  const dateYear = date.toDateString();
                  return dateTime + '\n' + dateYear;
                } else {
                  return '';
                }
              } else if (that.isActive === 1) {
                // relative
                if (value < 1 && value.toString().length > 6) {
                  return value.toFixed(3);
                } else if (value.toString().length > 6) {
                  return value.toExponential(0);
                } else {
                  return value;
                }
              } else {
                // step
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
              }
            },
          },
        },
        yAxis: {
          type: sampleObject.log ? 'log' : 'value',
          scale: true,
          logBase: 10,
          axisLabel: {
            formatter: (value) => {
              if (sampleObject.zoomDataYTimer) {
                clearTimeout(sampleObject.zoomDataYTimer);
                sampleObject.zoomDataYTimer = setTimeout(() => {
                  sampleObject.zoomDataYTimer = null;
                  this.calIfOnePoint(sampleObject);
                }, 50);
                if (value < sampleObject.zoomData[0]) {
                  sampleObject.zoomData[0] = value;
                } else if (sampleObject.zoomData[1] < value) {
                  sampleObject.zoomData[1] = value;
                }
              } else {
                sampleObject.zoomData = [value, value];
                sampleObject.zoomDataYTimer = setTimeout(() => {
                  sampleObject.zoomDataYTimer = null;
                }, 50);
              }
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
          left: 80,
          right: sampleObject.fullScreen ? 80 : 10,
        },
        dataZoom: [
          {
            show: false,
            yAxisIndex: 0,
            filterMode: 'none',
          },
        ],
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'line',
          },
          position: (point, params, dom, rect, size) => {
            const curDom = document.getElementById(sampleObject.domId);
            if (!curDom) {
              return {left: 0, bottom: '100%'};
            }
            if (sampleObject.fullScreen) {
              if (point[0] + size.contentSize[0] <= size.viewSize[0]) {
                return {left: point[0], bottom: '10%'};
              } else {
                return {right: size.viewSize[0] - point[0], bottom: '10%'};
              }
            } else {
              const parentNode = curDom.parentNode;
              if (!parentNode) {
                return {left: 0, bottom: '100%'};
              }
              if (parentNode.offsetLeft > size.contentSize[0]) {
                return {right: '100%', bottom: 0};
              } else {
                return {left: '100%', bottom: 0};
              }
            }
          },
          formatter: (params) => {
            const unit = 's';
            const strhead =
              `<table class="char-tip-table" class="borderspacing3"><tr><td></td>` +
              `<td>${this.$t('scalar.charTipHeadName')}</td>` +
              `<td>${this.$t('scalar.charSmoothedValue')}</td>` +
              `<td>${this.$t('scalar.charTipHeadValue')}</td>` +
              `<td>${this.$t('scalar.step')}</td>` +
              `<td>${this.$t('scalar.relativeTime')}</td>` +
              `<td>${this.$t('scalar.absoluteTime')}</td>` +
              `</tr>`;
            let strBody = '';
            const summaryArr = [];
            const detialArr = [];
            let curStep = null;
            let dataCount = 0;
            params.forEach((parma) => {
              if (parma.componentIndex % 2 === 0) {
                let addFlag = true;
                const curIndex = parseInt(parma.componentIndex / 2);
                let curSerieOriData;
                if (sampleObject.log) {
                  curSerieOriData = oriData[curIndex].logData;
                } else {
                  curSerieOriData = oriData[curIndex].valueData;
                }
                if (curStep === null) {
                  curStep = curSerieOriData.stepData[parma.dataIndex][0];
                } else {
                  if (curSerieOriData.stepData[parma.dataIndex][0] === curStep) {
                    const sameSummaryIndex = [];
                    summaryArr.forEach((summaryName, index) => {
                      if (parma.seriesName === summaryName) {
                        sameSummaryIndex.push(index);
                      }
                    });
                    if (sameSummaryIndex.length) {
                      sameSummaryIndex.forEach((sameIndex) => {
                        if (
                          detialArr[sameIndex] &&
                          detialArr[sameIndex].value === curSerieOriData.stepData[parma.dataIndex][1] &&
                          detialArr[sameIndex].wallTime === curSerieOriData.absData[parma.dataIndex][0]
                        ) {
                          addFlag = false;
                        }
                      });
                    }
                  } else {
                    addFlag = false;
                  }
                }
                if (
                  addFlag &&
                  parma.value[1] &&
                  parma.value[1] >= sampleObject.zoomData[0] &&
                  parma.value[1] <= sampleObject.zoomData[1]
                ) {
                  dataCount++;
                  summaryArr.push(parma.seriesName);
                  detialArr.push({
                    value: curSerieOriData.stepData[parma.dataIndex][1],
                    step: curSerieOriData.stepData[parma.dataIndex][0],
                    wallTime: curSerieOriData.absData[parma.dataIndex][0],
                    dataIndex: parma.dataIndex,
                  });
                  strBody +=
                    `<tr><td style="border-radius:50%;width:15px;height:15px;vertical-align: middle;` +
                    `margin-right: 5px;background-color:${sampleObject.colors[curIndex]};` +
                    `display:inline-block;"></td><td>${parma.seriesName}</td>` +
                    `<td>${this.formateYaxisValue(parma.value[1])}</td>` +
                    `<td>${this.formateYaxisValue(curSerieOriData.stepData[parma.dataIndex][1])}</td>` +
                    `<td>${curSerieOriData.stepData[parma.dataIndex][0]}</td>` +
                    `<td>${curSerieOriData.relativeData[parma.dataIndex][0].toFixed(3)}${unit}</td>` +
                    `<td>${this.dealrelativeTime(
                        new Date(curSerieOriData.absData[parma.dataIndex][0] * 1000).toString(),
                    )}</td>` +
                    `</tr>`;
                }
              }
            });
            if (dataCount) {
              return strhead + strBody + '</table>';
            }
          },
        },
        toolbox: {
          top: 20,

          emphasis: {
            iconStyle: {
              textPosition: 'top',
              textAlign: 'right',
              borderColor: '#00A5A7',
            },
          },
          // Toolbox
          feature: {
            // FullScreen
            myToolFullScreen: {
              show: true,
              title: this.$t('scalar.fullScreen'),
              iconStyle: {
                borderColor: sampleObject.fullScreen ? '#00A5A7' : '#6D7278',
              },
              icon: CommonProperty.fullScreenIcon[this.$store.state.themeIndex],
              onclick() {
                fullScreenFun(sampleIndex);
              },
            },
            myTool2: {
              show: true,
              title: this.$t('scalar.toggleYaxisScale'),
              iconStyle: {
                borderColor: sampleObject.log ? '#00A5A7' : '#6D7278',
              },
              icon:
                'path://M0 150 c0 -18 7 -20 85 -20 78 0 85 2 85 20 0 18 -7 20 -85 20 -78 0 -85 -2 ' +
                '-85 -20z M0 95 c0 -12 16 -15 85 -15 69 0 85 3 85 15 0 12 -16 15 -85 15 -69 0 -85 ' +
                '-3 -85 -15z M0 50 c0 -6 35 -10 85 -10 50 0 85 4 85 10 0 6 -35 10 -85 10 -50 0 -85' +
                `-4 -85 -10z`,
              onclick(ExtendedClass, ExtensionAPI, toolName, event) {
                yAxisFun(sampleIndex);
              },
            },

            // Selection and rollback
            dataZoom: {
              textStyle: false,
              title: {
                zoom: this.$t('scalar.openOrCloseSelection'),
                back: this.$t('scalar.stepBack'),
              },
              show: true,
            },

            // Restore
            restore: {
              title: this.$t('scalar.restore'),
            },
          },
        },
        series: seriesData,
      };
      return tempOption;
    },

    /**
     * Updating or creating a specified chart
     * @param {Number} sampleIndex Chart subscript
     */

    updateOrCreateChar(sampleIndex) {
      const sampleObject = this.originDataArr[sampleIndex];

      if (!sampleObject) {
        return;
      }
      if (sampleObject.charObj) {
        // Updating chart option
        if (sampleObject.updateFlag) {
          sampleObject.charObj.setOption(sampleObject.charData.charOption, sampleObject.dataRemove);
          sampleObject.updateFlag = false;
          sampleObject.dataRemove = false;
        }
      } else {
        // Create chart
        sampleObject.charObj = echarts.init(document.getElementById(sampleObject.domId), echartsThemeName);
        sampleObject.charObj.setOption(sampleObject.charData.charOption, true);
      }
    },

    /**
     * The logic of keep showSymbol right
     * @param {Object} sampleObject Chart object
     */
    calIfOnePoint(sampleObject) {
      if (!sampleObject.dataZoomYTimer && !sampleObject.dataZoomXTimer) {
        // Format is finished
        const selected = Object.keys(this.multiSelectedSummaryNames);
        const [xStart, xEnd] = sampleObject.zoomDataX;
        const [yStart, yEnd] = sampleObject.zoomData;
        const series = sampleObject.charData.charOption.series;
        const onePoint = 1;
        series.forEach((data) => {
          if (selected.includes(data.name)) {
            let count = 0;
            for (let i = 0; i < data.data.length; i++) {
              const [xValue, yValue] = data.data[i];
              if (this.calIfExist(xStart, xEnd, yStart, yEnd, xValue, yValue)) {
                count++;
              }
              if (count > onePoint) {
                break;
              }
            }
            // Keep showSymbol right
            if (count === onePoint) {
              if (!data.showSymbol) {
                data.showSymbol = true;
                this.$nextTick(() => {
                  sampleObject.charObj.setOption({
                    series: series,
                  });
                });
              }
            } else {
              if (data.showSymbol) {
                data.showSymbol = false;
                this.$nextTick(() => {
                  sampleObject.charObj.setOption({
                    series: series,
                  });
                });
              }
            }
          }
        });
      }
    },

    /**
     * The logic of cal if point in zoom area
     * @param {Number} xStart
     * @param {Number} xEnd
     * @param {Number} yStart
     * @param {Number} yEnd
     * @param {Number} xValue
     * @param {Number} yValue
     * @return {Boolean}
     */
    calIfExist(xStart, xEnd, yStart, yEnd, xValue, yValue) {
      const newYStart = this.losePrecision(yStart, false);
      const newYEnd = this.losePrecision(yEnd, true);
      const xExist = xStart <= xValue && xValue <= xEnd;
      const yEyist = newYStart <= yValue && yValue <= newYEnd;
      return xExist && yEyist;
    },

    /**
     * The logic of lose precision
     * @param {Number} number
     * @param {Boolean} ifCeil
     * @return {Number}
     */
    losePrecision(number, ifCeil) {
      try {
        const [, decimal] = number.toString().split('.');
        if (!decimal) {
          return number;
        }
        const decimalLength = decimal.length;
        // 10: use to move decimal point
        const param = Math.pow(10, decimalLength - 1);
        if (ifCeil) {
          number = Math.ceil(number * param);
        } else {
          number = Math.floor(number * param);
        }
        return number / param;
      } catch {
        return number;
      }
    },

    /**
     * Enabling/Disabling full screen
     * @param {Number} sampleIndex Chart subscript
     */

    toggleFullScreen(sampleIndex) {
      const sampleObject = this.originDataArr[sampleIndex];
      if (!sampleObject) {
        return;
      }

      // Background color of the refresh button
      sampleObject.fullScreen = !sampleObject.fullScreen;
      if (sampleObject.fullScreen) {
        sampleObject.charData.charOption.toolbox.feature.myToolFullScreen.iconStyle.borderColor = '#00A5A7';
        sampleObject.charData.charOption.grid.right = 80;
      } else {
        sampleObject.charData.charOption.toolbox.feature.myToolFullScreen.iconStyle.borderColor = '#6D7278';
        sampleObject.charData.charOption.grid.right = 10;
      }
      sampleObject.updateFlag = true;

      // Refresh icon display
      this.updateOrCreateChar(sampleIndex);
      setTimeout(() => {
        sampleObject.charObj.resize();

        document.getElementById('view' + sampleObject.domId).scrollIntoView();
      }, 0);
    },

    /**
     * Update chart by tag
     * @param {Boolean} noPageDataNumChange No new data is added or deleted
     */

    updateTagInPage(noPageDataNumChange) {
      const curFilterSamples = [];
      this.originDataArr.forEach((sampleItem) => {
        if (this.multiSelectedTagNames[sampleItem.tagName]) {
          curFilterSamples.push(sampleItem);
        }
      });
      this.curFilterSamples = curFilterSamples;
      this.getCurPageDataArr(noPageDataNumChange);
    },

    /**
     *
     * The time display type is changed
     */

    timeTypeChange(val) {
      if (this.axisBenchChangeTimer) {
        clearTimeout(this.axisBenchChangeTimer);
        this.axisBenchChangeTimer = null;
      }
      switch (val) {
        case this.$t('scalar.step'):
          this.curBenchX = 'stepData';
          this.curAxisName = this.$t('scalar.step');
          this.isActive = 0;
          break;
        case this.$t('scalar.relativeTime'):
          this.curBenchX = 'relativeData';
          this.curAxisName = this.$t('scalar.relativeTime');
          this.isActive = 1;
          break;
        case this.$t('scalar.absoluteTime'):
          this.curBenchX = 'absData';
          this.curAxisName = this.$t('scalar.absoluteTime');
          this.isActive = 2;
          break;
        default:
          this.curBenchX = 'stepData';
          this.curAxisName = this.$t('scalar.step');
          this.isActive = 0;
          break;
      }
      this.axisBenchChangeTimer = setTimeout(() => {
        // Update the horizontal benchmark of the default data
        this.curPageArr.forEach((sampleObject) => {
          if (sampleObject.charObj) {
            sampleObject.charData.oriData.forEach((originData, index) => {
              const series = sampleObject.charData.charOption.series;
              if (sampleObject.log) {
                series[index * 2].data = this.formateSmoothData(
                    sampleObject.charData.oriData[index].logData[this.curBenchX],
                );
                series[index * 2 + 1].data = sampleObject.charData.oriData[index].logData[this.curBenchX];
              } else {
                series[index * 2].data = this.formateSmoothData(
                    sampleObject.charData.oriData[index].valueData[this.curBenchX],
                );
                series[index * 2 + 1].data = sampleObject.charData.oriData[index].valueData[this.curBenchX];
              }
            });

            sampleObject.charData.charOption.xAxis.minInterval = this.isActive === 0 ? 1 : 0;
            sampleObject.updateFlag = true;
            sampleObject.charObj.clear();
            this.updateOrCreateChar(sampleObject.sampleIndex);
          }
        });
      }, 500);
    },

    /**
     * Page number change event
     * @param {Number} pageIndex (1~n)
     */

    currentPageChange(pageIndex) {
      this.pageIndex = pageIndex - 1;

      // Load the data on the current page
      this.getCurPageDataArr();
    },

    /**
     * The selected label is changed
     * @param {Object} selectItemDict Dictionary containing the selected tags
     */

    tagSelectedChanged(selectedItemDict) {
      if (!selectedItemDict) {
        return;
      }
      this.multiSelectedTagNames = selectedItemDict;
      // Reset to the first page
      this.pageIndex = 0;
      this.updateTagInPage();
    },

    /**
     * The selected label is changed
     * @param {Object} selectedItemDict Dictionary containing the selected summary
     */

    summarySelectedChanged(selectedItemDict) {
      if (!selectedItemDict) {
        return;
      }
      this.multiSelectedSummaryNames = selectedItemDict;
      if (this.isTimeReload) {
        this.autoUpdateSamples();
      }
      if (Object.keys(this.multiSelectedSummaryNames).length > 0) {
        this.trainJobsCaches();
      }
      this.updateSummary();
    },

    /**
     * Update chart by summary
     */
    updateSummary() {
      // Update the data display area
      this.originDataArr.forEach((sampleObject) => {
        if (sampleObject.charObj) {
          sampleObject.updateFlag = true;
          sampleObject.summaryNames.forEach((summaryName) => {
            const sampleSelect = sampleObject.charData.charOption.legend.selected;
            if (!sampleSelect) {
              return;
            }
            if (this.multiSelectedSummaryNames[summaryName]) {
              sampleSelect[summaryName] = true;
              sampleSelect[summaryName + this.backendString] = true;
            } else {
              sampleSelect[summaryName] = false;
              sampleSelect[summaryName + this.backendString] = false;
            }
          });
        }
      });

      setTimeout(() => {
        // Refresh the current page chart
        this.curPageArr.forEach((sampleObject) => {
          this.updateOrCreateChar(sampleObject.sampleIndex);
        });
      }, 0);
    },

    /**
     *Window resize
     */

    resizeCallback() {
      if (this.isTimeReload) {
        this.autoUpdateSamples();
      }
      if (this.charResizeTimer) {
        clearTimeout(this.charResizeTimer);
        this.charResizeTimer = null;
      }

      this.charResizeTimer = setTimeout(() => {
        this.curPageArr.forEach((sampleItem) => {
          if (sampleItem.charObj) {
            sampleItem.charObj.resize();
          }
        });
      }, 500);
    },

    /**
     * Initialize the color array
     */

    initAvlColorArr() {
      const length = this.defColorCount;
      for (let i = 0; i < length; i++) {
        this.curAvlColorIndexArr.push(i);
      }
    },

    /**
     * Clear data
     */

    clearAllData() {
      this.summaryOperateList.forEach((summaryItem) => {
        this.curAvlColorIndexArr.unshift(summaryItem.colorIndex);
      });
      this.multiSelectedSummaryNames = {};
      this.multiSelectedTagNames = {};
      this.curFilterSamples = [];
      this.tagOperateList = [];
      this.pageIndex = 0;
      this.originDataArr = [];
      this.oriDataDictionaries = {};
      this.curPageArr = [];
    },

    /**
     * Error
     * @param {Object} error Error object
     */

    requestErrorCallback(error) {
      if (!this.initOver) {
        this.initOver = true;
      }
      if (this.isReloading) {
        this.$store.commit('setIsReload', false);
        this.isReloading = false;
      }
      this.clearAllData();
    },

    /**
     * Delete the data that does not exist
     * @param {Object} oriData Original summary and tag data
     */

    removeNonexistentData(oriData) {
      if (!oriData) {
        return false;
      }
      const summaryList = []; // Summary list
      const tagList = []; // Tag list
      const oriSummaryList = []; // Original list
      let dataRemoveFlag = false;
      // Obtains the current tag and summary list
      oriData.forEach((summaryObj, summaryIndex) => {
        oriSummaryList.push(summaryObj.train_id);
        summaryObj.plugins.scalar.forEach((tagObj) => {
          let sameTagIndex = tagList.indexOf(tagObj);
          if (sameTagIndex === -1) {
            sameTagIndex = tagList.length;
            tagList.push(tagObj);
            summaryList[sameTagIndex] = [summaryObj.train_id];
          } else {
            summaryList[sameTagIndex].push(summaryObj.train_id);
          }
        });
      });

      // Delete the summary that does not exist
      const oldSummaryListLength = this.summaryOperateList.length;
      for (let i = oldSummaryListLength - 1; i >= 0; i--) {
        if (oriSummaryList.indexOf(this.summaryOperateList[i].label) === -1) {
          const removeSummaryObj = this.summaryOperateList.splice(i, 1);
          this.curAvlColorIndexArr.unshift(removeSummaryObj[0].colorIndex);
        }
      }

      // Delete the tag that does not exist
      const oldTagListLength = this.tagOperateList.length;
      for (let i = oldTagListLength - 1; i >= 0; i--) {
        if (tagList.indexOf(this.tagOperateList[i].label) === -1) {
          dataRemoveFlag = true;
          this.tagOperateList.splice(i, 1);
        }
      }

      // Except the old data in the chart
      const oldSampleLength = this.originDataArr.length;

      for (let i = oldSampleLength - 1; i >= 0; i--) {
        const oldSample = this.originDataArr[i];

        const sameTagIndex = tagList.indexOf(oldSample.tagName);
        if (sameTagIndex === -1) {
          this.originDataArr.splice(i, 1);
          dataRemoveFlag = true;
          const loopLength = this.originDataArr.length;
          for (let loopStart = i; loopStart < loopLength; loopStart++) {
            if (this.originDataArr[loopStart]) {
              this.originDataArr[loopStart].sampleIndex = loopStart;
            }
          }
        } else {
          const oldSummaryLength = oldSample.summaryNames.length;
          for (let j = oldSummaryLength - 1; j >= 0; j--) {
            const sameSummaryIndex = summaryList[sameTagIndex].indexOf(oldSample.summaryNames[j]);
            if (sameSummaryIndex === -1) {
              oldSample.summaryNames.splice(j, 1);
              oldSample.colors.splice(j, 1);
              oldSample.charData.oriData.splice(j, 1);

              oldSample.dataRemove = true;
            }
          }
        }
      }

      return dataRemoveFlag;
    },

    /**
     * Check and add new data
     * @param {Object} oriData Original summary and tag data
     */

    checkNewDataAndComplete(oriData) {
      if (!oriData) {
        return false;
      }
      let dataAddFlag = false;
      oriData.forEach((summaryObj) => {
        let sameSummaryIndex = -1;
        this.summaryOperateList.some((summaryItem, summaryIndex) => {
          if (summaryItem.label === summaryObj.train_id) {
            sameSummaryIndex = summaryIndex;
            return true;
          }
        });

        let summaryColor;

        if (sameSummaryIndex === -1) {
          const colorIndex = this.curAvlColorIndexArr.length
            ? this.curAvlColorIndexArr.shift()
            : this.defColorCount - 1;
          summaryColor = CommonProperty.commonColorArr[this.$store.state.themeIndex][colorIndex];
          this.summaryOperateList.push({
            label: summaryObj.train_id,
            checked: true,
            show: false,
            color: summaryColor,
            colorIndex: colorIndex,
          });
        } else {
          summaryColor = this.summaryOperateList[sameSummaryIndex].color;
        }

        this.summaryOperateList.forEach((item) => {
          if (item.label === summaryObj.train_id) {
            item.loading = summaryObj.cache_status;
          }
        });

        summaryObj.plugins.scalar.forEach((tagObj) => {
          let sameTagIndex = -1;
          this.tagOperateList.some((tagItem, tagIndex) => {
            if (tagItem.label === tagObj) {
              sameTagIndex = tagIndex;
              return true;
            }
          });
          if (sameTagIndex === -1) {
            this.tagOperateList.push({
              label: tagObj,
              checked: true,
              show: false,
            });
            const sampleIndex = this.originDataArr.length;
            dataAddFlag = true;
            this.originDataArr.push({
              tagName: tagObj,
              summaryNames: [summaryObj.train_id],
              colors: [summaryColor],
              show: false,
              updateFlag: false,
              dataRemove: false,
              fullScreen: false,
              sampleIndex: sampleIndex,
              domId: 'prDom' + this.DomIdIndex,
              charData: {
                oriData: [],
                charOption: {},
              },
              zoomData: [null, null],
              zoomDataX: [null, null],
              zoomDataYTimer: null,
              zoomDataXTimer: null,
              charObj: null,
            });
            this.DomIdIndex++;
          } else {
            const sameSampleObj = this.originDataArr[sameTagIndex];
            if (sameSampleObj && sameSampleObj.summaryNames.indexOf(summaryObj.train_id) === -1) {
              sameSampleObj.summaryNames.push(summaryObj.train_id);
              sameSampleObj.colors.push(summaryColor);
            }
          }
        });
      });

      return dataAddFlag;
    },

    /**
     * Updating all data
     * @param {Boolean} ignoreError Whether ignore error tip
     */

    updateAllData(ignoreError) {
      const params = {};
      params.offset = 0;
      params.limit = 999;
      RequestService.querySummaryList(params, ignoreError)
          .then((res) => {
            if (this.isReloading) {
              this.$store.commit('setIsReload', false);
              this.isReloading = false;
            }

            // Fault tolerance processing
            if (!res || !res.data || !res.data.train_jobs || !res.data.train_jobs.length) {
              if (res.toString() === 'false') {
                return;
              }

              this.clearAllData();
              return;
            }
            const data = res.data.train_jobs.filter((item) => {
              return item.summary_files > 0;
            });
            if (!data.length) {
              this.clearAllData();
              return;
            }

            // Delete the data that does not exist
            const tagRemoveFlag = this.removeNonexistentData(data);

            // Check whether new data exists and add it to the page
            const tagAddFlag = this.checkNewDataAndComplete(data);

            this.$nextTick(() => {
              this.multiSelectedTagNames = this.$refs.tagsGroup.updateSelectedDic();
              this.multiSelectedSummaryNames = this.$refs.summaryGroup.updateSelectedDic();
              this.$refs.summaryGroup.$forceUpdate();
              this.$refs.tagsGroup.$forceUpdate();

              this.updateTagInPage(!tagRemoveFlag && !tagAddFlag);
              this.resizeCallback();
              if (Object.keys(this.multiSelectedSummaryNames).length > 0) {
                this.trainJobsCaches();
              }
            });
          }, this.requestErrorCallback)
          .catch((e) => {
            this.$message.error(this.$t('public.dataError'));
          });
    },

    /**
     * Enable automatic refresh
     */

    autoUpdateSamples() {
      if (this.autoUpdateTimer) {
        clearInterval(this.autoUpdateTimer);
        this.autoUpdateTimer = null;
      }
      this.autoUpdateTimer = setInterval(() => {
        this.$store.commit('clearToken');
        this.updateAllData(true);
      }, this.timeReloadValue * 1000);
    },

    /**
     * Disable automatic refresh
     */

    stopUpdateSamples() {
      if (this.autoUpdateTimer) {
        clearInterval(this.autoUpdateTimer);
        this.autoUpdateTimer = null;
      }
    },

    /**
     * Updata smoothness
     * @param {String} value Slide value
     */

    updataInputValue(val) {
      if (this.firstNum === 0) {
        return;
      }
      this.smoothValueNumber = Number(val);
      if (this.smoothSliderValueTimer) {
        clearTimeout(this.smoothSliderValueTimer);
        this.smoothSliderValueTimer = null;
      }
      this.smoothSliderValueTimer = setTimeout(() => {
        // Change the smoothness
        this.setCharLineSmooth();
      }, 500);
    },

    smoothValueChange(val) {
      if (!isNaN(val)) {
        if (Number(val) === 0) {
          this.smoothValue = 0;
        }
        if (Number(val) < 0) {
          this.smoothValue = 0;
          this.smoothValueNumber = 0;
        }
        if (Number(val) > 0) {
          if (Number(val) > 0.99) {
            this.smoothValue = 0.99;
            this.smoothValueNumber = 0.99;
          } else {
            this.smoothValue = Number(val);
          }
        }
      }
    },

    smoothValueBlur() {
      this.smoothValueNumber = this.smoothValue;
    },

    /**
     * Format absolute time
     * @param {String} time String
     * @return {string} Str
     */

    dealrelativeTime(time) {
      const arr = time.split(' ');
      const str = arr[0] + ' ' + arr[1] + ' ' + arr[2] + ',' + ' ' + arr[4];
      return str;
    },

    /**
     * Setting the smoothness
     */

    setCharLineSmooth() {
      if (this.curPageArr.length < 1) {
        return;
      }

      // Update the smoothness of initialized data
      this.curPageArr.forEach((sampleObject) => {
        if (sampleObject.charObj) {
          const log = sampleObject.log;
          sampleObject.charData.charOption.series.forEach((singleItem, index) => {
            if (index % 2 === 0) {
              if (log) {
                singleItem.data = this.formateSmoothData(
                    sampleObject.charData.oriData[index / 2].logData[this.curBenchX],
                );
              } else {
                singleItem.data = this.formateSmoothData(
                    sampleObject.charData.oriData[index / 2].valueData[this.curBenchX],
                );
              }
            }
          });
          sampleObject.updateFlag = true;
          this.updateOrCreateChar(sampleObject.sampleIndex);
        }
      });
    },

    /**
     * Format smooth data
     * @param {Object} oriData
     * @return {Object} Data
     */

    formateSmoothData(oriData) {
      if (!oriData || oriData.length < 2) {
        return oriData;
      }
      const data = JSON.parse(JSON.stringify(oriData));
      const oriDataLength = oriData.length;
      let last = 0;
      const smoothValue = this.smoothValue;
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
     * Format the value of the Y axis
     * @param {String} value Number y
     * @return {Number}
     */

    formateYaxisValue(value) {
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
     * YAxis scale
     * @param {Number} sampleIndex Number
     */

    yAxisScale(sampleIndex) {
      const sampleObject = this.originDataArr[sampleIndex];
      if (!sampleObject) {
        return;
      }
      const log = !sampleObject.log;
      if (log) {
        sampleObject.charData.charOption.toolbox.feature.myTool2.iconStyle.borderColor = '#00A5A7';
        sampleObject.charData.charOption.yAxis.type = 'log';
      } else {
        sampleObject.charData.charOption.yAxis.type = 'value';
        sampleObject.charData.charOption.toolbox.feature.myTool2.iconStyle.borderColor = '#666';
      }
      sampleObject.charData.oriData.forEach((originData, index) => {
        const series = sampleObject.charData.charOption.series;
        if (log) {
          series[index * 2].data = this.formateSmoothData(
              sampleObject.charData.oriData[index].logData[this.curBenchX],
          );
          series[index * 2 + 1].data = sampleObject.charData.oriData[index].logData[this.curBenchX];
        } else {
          series[index * 2].data = this.formateSmoothData(
              sampleObject.charData.oriData[index].valueData[this.curBenchX],
          );
          series[index * 2 + 1].data = sampleObject.charData.oriData[index].valueData[this.curBenchX];
        }
      });
      sampleObject.log = log;
      sampleObject.updateFlag = true;
      sampleObject.charObj.clear();

      this.updateOrCreateChar(sampleIndex);
    },

    /**
     * Jump back to train dashboard
     */

    jumpToSummary() {
      this.$router.push({
        path: '/summary-manage',
      });
    },
  },
  components: {
    multiSelectGroupComponents,
  },
};
</script>
<style>
.cl-compare-manage {
  height: 100%;
}
.cl-compare-manage .w60 {
  width: 60px;
  margin-left: 20px;
}
.cl-compare-manage .borderspacing3 {
  border-spacing: 3px;
}
.cl-compare-manage .compare-bk {
  height: 100%;
  background-color: var(--bg-color);
  display: flex;
  flex-direction: column;
}
.cl-compare-manage .compare-bk .cl-compare-title {
  height: 56px;
  line-height: 56px;
}
.cl-compare-manage .select-all {
  flex-shrink: 0;
  cursor: pointer;
}
.cl-compare-manage .cl-eval-operate-content {
  width: 100%;
  padding: 0px 32px 22px 32px;
}
.cl-compare-manage .cl-eval-operate-content .cl-eval-operate-component {
  margin-top: 8px;
}
.cl-compare-manage .cl-eval-slider-operate-content {
  padding: 0 32px 21px 32px;
  display: flex;
  align-items: center;
  border-bottom: 2px solid var(--item-split-line-color);
}
.cl-compare-manage .cl-eval-slider-operate-content .xaxis-title {
  font-size: 14px;
  line-height: 14px;
  vertical-align: middle;
  margin-right: 16px;
  flex-shrink: 0;
}
.cl-compare-manage .cl-eval-slider-operate-content .el-radio-group {
  margin-right: 64px;
  flex-shrink: 0;
}
.cl-compare-manage .cl-eval-slider-operate-content .el-select {
  width: 163px;
  margin-right: 16px;
  flex-shrink: 0;
}
.cl-compare-manage .cl-eval-slider-operate-content .el-slider {
  width: 400px;
  flex-shrink: 0;
}
.cl-compare-manage .cl-eval-slider-operate-content .el-slider .el-input.el-input--small {
  width: 60px;
}
.cl-compare-manage .cl-eval-slider-operate-content .el-slider .el-input-number .el-input__inner {
  padding-left: 0px;
  padding-right: 0px;
}
.cl-compare-manage .cl-eval-slider-operate-content .el-slider .el-input-number--small .el-input-number__increase {
  display: none;
}
.cl-compare-manage .cl-eval-slider-operate-content .el-slider .el-input-number--small .el-input-number__decrease {
  display: none;
}
.cl-compare-manage .cl-eval-show-data-content {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-wrap: wrap;
  padding-right: 10px;
}
.cl-compare-manage .cl-eval-show-data-content .data-content {
  display: flex;
  height: 100%;
  width: 100%;
  flex-wrap: wrap;
  min-height: 400px;
}
.cl-compare-manage .cl-eval-show-data-content .data-content .sample-content {
  width: 33.3%;
  height: 400px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.cl-compare-manage .cl-eval-show-data-content .data-content .char-full-screen {
  width: 100%;
  height: 400px;
}
.cl-compare-manage .cl-eval-show-data-content .chars-container {
  flex: 1;
  padding: 0 15px 0 15px;
  position: relative;
  background-color: var(--bg-color);
  border: 1px solid var(--echarts-border-color);
  border-radius: 4px;
  margin: 15px 20px;
}
.cl-compare-manage .cl-eval-show-data-content .tag-name {
  color: var(--font-color);
  font-size: 16px;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 600;
  text-align: center;
}
.cl-compare-manage .cl-eval-show-data-content .tag-name i {
  color: #e6a23c;
}
.cl-compare-manage .cl-eval-show-data-content .char-item-content {
  width: 100%;
  height: 100%;
}
.cl-compare-manage .cl-eval-show-data-content .char-tip-table td {
  padding-left: 5px;
  padding-right: 5px;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 150px;
  overflow: hidden;
}
.cl-compare-manage .cl-eval-show-data-content .image-noData {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}
.cl-compare-manage .cl-eval-show-data-content .noData-text {
  margin-top: 33px;
  font-size: 18px;
}
.cl-compare-manage .pagination-content {
  text-align: right;
  padding: 24px 32px;
}
.cl-compare-manage .mr24 {
  margin-right: 24px;
}
.cl-compare-manage .select-disable {
  -moz-user-select: none;
  /*Firefox*/
  -webkit-user-select: none;
  /*Webkit*/
  -ms-user-select: none;
  /*IE10*/
  -khtml-user-select: none;
  user-select: none;
}
.cl-compare-manage .cl-close-btn {
  width: 20px;
  height: 20px;
  vertical-align: -3px;
  cursor: pointer;
  display: inline-block;
  line-height: 20px;
  margin-left: 32px;
}

.tooltip-show-content {
  max-width: 50%;
}

.cl-title-right {
  padding-right: 20px;
}
</style>

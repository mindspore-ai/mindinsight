<!--
Copyright 2019-2021 Huawei Technologies Co., Ltd.All Rights Reserved.

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
  <div class="cl-scalar-manage">
    <div class="scalar-bk">
      <div class="cl-title cl-scalar-title"
           v-show="originDataArr.length>0">
        <div class="cl-title-left">{{$t("scalar.titleText")}}
          <div class="path-message">
            <span>{{$t('symbols.leftbracket')}}</span>
            <span>{{$t('trainingDashboard.summaryDirPath')}}</span>
            <span>{{summaryPath}}</span>
            <span>{{$t('symbols.rightbracket')}}</span>
          </div>
        </div>
        <div class="cl-title-right">
          <ScalarButton class="scalar-btn"
                        :right="scalarCompare"
                        @compareClick='compareClick'
                        :initOver="initOver"></ScalarButton>
          <div class="cl-close-btn"
               @click="jumpToTrainDashboard">
            <img src="@/assets/images/close-page.png">
          </div>
        </div>
      </div>

      <!--Operation area -->
      <div class="cl-eval-operate-content"
           v-show="!compare && originDataArr.length>0">
        <multiselectGroupComponents ref="multiselectGroupComponents"
                                    :checkListArr="tagOperateList"
                                    @selectedChange="tagSelectedChanged"></multiselectGroupComponents>
      </div>
      <!-- Slider -->
      <div class="cl-eval-slider-operate-content"
           v-show="!compare && originDataArr.length>0">
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
           ref="miDataShoeContent"
           v-show="!compare">
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

            <div class="chartThreshold">
              <div class="chartThresholdLeft"
                   :title="sampleItem.pieceStr">{{$t("scalar.currentThreshold")}}：{{sampleItem.pieceStr || "-"}}</div>
              <div class="chartThresholdRight">
                <span @click="setThreshold(sampleItem)"
                      v-if="!thresholdLocal
                || !thresholdLocal[decodeTrainingJobId]
                || !thresholdLocal[decodeTrainingJobId][sampleItem.tagName]">
                  {{$t("scalar.setThreshold")}}</span>
                <span v-else
                      @click="delThreshold(sampleItem)">{{$t("scalar.deleteThreshold")}}</span>
              </div>
            </div>
            <!-- Tag name -->
            <div class="tag-name">{{sampleItem.tagName}}
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
           v-if="!compare && originDataArr.length">
        <el-pagination @current-change="currentPageChange"
                       :current-page="pageIndex + 1"
                       :page-size="pageNum"
                       layout="total, prev, pager, next, jumper"
                       :total="curFilterSamples.length">
        </el-pagination>

      </div>
      <ScalarCompare :tagPropsList="tagPropsList"
                     :initOver="initOver"
                     :propsList="propsList"
                     :compare="compare"
                     v-show="compare"></ScalarCompare>

    </div>

    <el-dialog :title="$t('scalar.setThreshold')"
               :visible.sync="thresholdDialogVisible"
               :close-on-click-modal="false"
               @close="thresholdCancel"
               width="1000px">
      <div class="thresholdAll">
        <div class="thresholdItem fs16">{{$t('scalar.currentTag')}}：</div>
        <div class="thresholdItemWidth">
          <el-tooltip class="item"
                      effect="dark"
                      :content="currentTagName"
                      placement="top">
            <span>{{currentTagName}}</span>
          </el-tooltip>
        </div>
      </div>

      <div class="thresholdAll">
        <div class="thresholdItem fs16">{{$t('scalar.filterCriteria')}}：</div>
        <div class="thresholdItem">
          <el-select v-model="thresholdValue[0].filterCondition"
                     class="smallSelect">
            <el-option v-for="filterItem in filterOptions"
                       :key="filterItem.value"
                       :label="filterItem.label"
                       :value="filterItem.value">
            </el-option>
          </el-select>
        </div>
        <div class="thresholdItem">
          <el-input v-model="thresholdValue[0].value"
                    :placeholder="$t('scalar.placeHolderThreshold')"
                    class="smallInput"
                    clearable></el-input>
        </div>
        <div class="thresholdItem">
          <el-select v-model="thresholdRelational"
                     :placeholder="$t('public.select')"
                     @change="relationalChange"
                     clearable
                     class="smallSelectTwo">
            <el-option :label="$t('scalar.or')"
                       :value="$t('scalar.or')">
            </el-option>
            <el-option :label="$t('scalar.and')"
                       :value="$t('scalar.and')">
            </el-option>
          </el-select>
        </div>
        <div class="thresholdItem"
             v-show="thresholdRelational">
          <el-select v-model="thresholdValue[1].filterCondition"
                     class="smallSelect">
            <el-option v-for="filterItem in filterOptions"
                       :key="filterItem.value"
                       :label="filterItem.label"
                       :value="filterItem.value">
            </el-option>
          </el-select>
        </div>
        <div class="thresholdItem"
             v-show="thresholdRelational">
          <el-input v-model="thresholdValue[1].value"
                    :placeholder="$t('scalar.placeHolderThreshold')"
                    class="smallInput"
                    clearable></el-input>
        </div>
        <div class="thresholdItem thresholdError">{{thresholdErrorMsg}}</div>
      </div>

      <div class="thresholdAll">
        <div class="thresholdItem fs16">{{$t('scalar.applyAllSelectTag')}}</div>
        <div class="thresholdItem">
          <el-switch v-model="thresholdSwitch"></el-switch>
        </div>
      </div>

      <span slot="footer"
            class="dialog-footer">
        <el-button @click="thresholdCancel"
                   size="mini">{{$t('public.cancel')}}</el-button>
        <el-button type="primary"
                   @click="thresholdCommit"
                   size="mini">{{$t('public.sure')}}</el-button>
      </span>
    </el-dialog>

    <el-dialog :title="$t('scalar.info')"
               :visible.sync="delThresholdVisible"
               custom-class="delDialog"
               :close-on-click-modal="false"
               @close="delThresholdCancel"
               top="35vh"
               width="425px">
      <div class="delThresholdItem">
        <span class="delThresholdIcon el-icon-warning"></span>
        <span class="delThresholdInfo">{{$t('scalar.isDelete')}}</span>
      </div>
      <div class="delThresholdItem">
        <span class="delThresholdIcon">
          <el-switch v-model="delThresholdSwitch"></el-switch>
        </span>
        <span class="delThresholdInfo">{{$t('scalar.applyAllSelectTag')}}</span>
      </div>
      <span slot="footer"
            class="dialog-footer">
        <el-button @click="delThresholdCancel"
                   size="mini">{{$t('public.cancel')}}</el-button>
        <el-button type="primary"
                   @click="delThresholdCommit"
                   size="mini">{{$t('public.sure')}}</el-button>
      </span>
    </el-dialog>

  </div>
</template>
<script>
import ScalarButton from './scalar-button';
import echarts from '../../js/echarts';
import RequestService from '../../services/request-service';
import CommonProperty from '../../common/common-property';
import ScalarCompare from './scalar-compare';
import multiselectGroupComponents from '../../components/multiselect-group.vue';
import autoUpdate from '../../mixins/auto-update.vue';
import threshold from '../../mixins/threshold.vue';


export default {
  mixins: [threshold, autoUpdate],
  data() {
    return {
      firstNum: 0, // First time
      isActive: 0, // Horizontal axis selected value
      initOver: false, // Indicates whether the initialization is complete
      charResizeTimer: null, // Delay after the window size is changed
      multiSelectedTagNames: {}, // Selected tag name
      curFilterSamples: [], // List of chart that meet the current filter criteria
      tagOperateList: [], // Array selected by tag
      tagPropsList: [], // Tag props
      propsList: [], // DataList props
      smoothValue: 0, // Initial smoothness of the slider
      smoothValueNumber: 0,
      smoothSliderValueTimer: null, // Smoothness slider timer
      DomIdIndex: 0, // DomId num
      originDataArr: [], // Original data
      oriDataDictionaries: {}, // Dictionary that contains all the current tags
      curPageArr: [], // Data of the current page
      pageIndex: 0, // Current page number
      pageNum: 6, // Number of records per page
      backendString: 'scalarBackend', // Background layer suffix
      curBenchX: 'stepData', // Front axle reference
      curAxisName: this.$t('scalar.step'), // Current chart tip
      axisBenchChangeTimer: null, // Horizontal axis reference switching timing
      yAxisScaleTimer: null, // yAxis scale timer
      compare: false, // Comparison Page
      scalarCompare: this.$t('scalar')['comparison'],
      trainingJobId: this.$route.query.train_id, // ID of the current training job
      summaryPath: this.$route.query.summaryPath,
      decodeTrainingJobId: '',
    };
  },

  destroyed() {
    // Remove the size of a window and change the listener
    window.removeEventListener('resize', this.resizeCallback);

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

    if (this.axisBenchChangeTimer) {
      clearTimeout(this.axisBenchChangeTimer);
      this.axisBenchChangeTimer = null;
    }
    if (this.yAxisScaleTimer) {
      clearTimeout(this.yAxisScaleTimer);
      this.yAxisScaleTimer = null;
    }
  },
  mounted() {
    if (!this.$route.query || !this.$route.query.train_id) {
      this.$message.error(this.$t('trainingDashboard.invalidId'));
      document.title = `${this.$t('scalar.titleText')}-MindInsight`;
      return;
    }
    document.title = `${decodeURIComponent(
        this.$route.query.train_id,
    )}-${this.$t('scalar.titleText')}-MindInsight`;
    // Adding a Listener
    window.addEventListener('resize', this.resizeCallback, false);
    // Dom ready
    this.$nextTick(() => {
      // Initializing Data
      this.getScalarsList();

      this.firstNum = 1;

      this.decodeTrainingJobId = decodeURIComponent(this.trainingJobId);

      this.getCache();

      // Auto refresh
      if (this.isTimeReload) {
        this.autoUpdateSamples();
      }
    });
  },
  methods: {
    /**
     * Obtain the tag and run list.
     */

    getScalarsList() {
      const params = {
        plugin_name: 'scalar',
        train_id: this.trainingJobId,
      };
      RequestService.getSingleTrainJob(params, false)
          .then((res) => {
          // Error
            if (
              !res ||
            !res.data ||
            !res.data.train_jobs ||
            !res.data.train_jobs.length
            ) {
              this.initOver = true;
              return;
            }
            const tempTagList = [];
            const dataList = [];
            const propsList = [];
            const data = res.data.train_jobs[0];
            const runNmeColor = CommonProperty.commonColorArr[0];
            data.tags.forEach((tagObj) => {
              if (!this.oriDataDictionaries[tagObj]) {
                this.oriDataDictionaries[tagObj] = true;
                // Add the tag list
                tempTagList.push({
                  label: tagObj,
                  checked: true,
                  show: true,
                });
                const sampleIndex = dataList.length;
                // Adding chart data
                dataList.push({
                  tagName: tagObj,
                  runNames: data.name,
                  colors: runNmeColor,
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
                  zoomDataTimer: null,
                  charObj: null,
                  invalidData: false,
                });

                propsList.push({
                  tagName: tagObj,
                  runNames: data.name,
                  colors: '',
                });
                this.DomIdIndex++;
              }
            });
            this.tagOperateList = tempTagList;
            this.tagPropsList = JSON.parse(JSON.stringify(tempTagList));
            if (dataList.length === 1) {
              dataList[0].fullScreen = true;
            }
            this.originDataArr = dataList;
            this.propsList = propsList;
            this.initOver = true;

            this.$nextTick(() => {
              this.multiSelectedTagNames = this.$refs.multiselectGroupComponents.updateSelectedDic();
              // Obtains data on the current page
              this.updateTagInPage();
              this.resizeCallback();
            });
          }, this.requestErrorCallback)
          .catch((e) => {
            this.initOver = true;
            this.$message.error(this.$t('public.dataError'));
          });
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
        const sampleIndex = sampleObject.sampleIndex;
        if (!sampleObject) {
          return;
        }
        sampleObject.updateFlag = true;

        const params = {
          train_id: this.trainingJobId,
          tag: sampleObject.tagName,
        };

        RequestService.getScalarsSample(params)
            .then((res) => {
            // Error
              if (!res || !res.data || !res.data.metadatas) {
              // Canceled
                if (res.toString() === 'false') {
                  return;
                }
                if (sampleObject.charObj) {
                  sampleObject.charObj.clear();
                  sampleObject.onePoint = false;
                }
                return;
              }
              let hasInvalidData = false;

              if (sampleObject.charObj) {
                sampleObject.charObj.showLoading();
              }

              const resData = res.data;

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
              if (resData.metadatas.length) {
                relativeTimeBench = resData.metadatas[0].wall_time;
              }

              const mathData = [];
              // Initializing chart data
              resData.metadatas.forEach((metaData) => {
                if (metaData.value === null && !hasInvalidData) {
                  hasInvalidData = true;
                }
                if (!isNaN(metaData.value) && metaData.value !== null) {
                  mathData.push(metaData.value);
                }
                tempObject.valueData.stepData.push([
                  metaData.step,
                  metaData.value,
                ]);
                tempObject.valueData.absData.push([
                  metaData.wall_time,
                  metaData.value,
                ]);
                tempObject.valueData.relativeData.push([
                  metaData.wall_time - relativeTimeBench,
                  metaData.value,
                ]);
                // Values less than 0 have no logarithm
                // Set empty string and echart does not render
                const logValue = metaData.value > 0 ? metaData.value : '';
                tempObject.logData.stepData.push([metaData.step, logValue]);
                tempObject.logData.absData.push([metaData.wall_time, logValue]);
                tempObject.logData.relativeData.push([
                  metaData.wall_time - relativeTimeBench,
                  logValue,
                ]);
              });

              // Numerical range
              const filtersData = mathData.filter((item) => {
              // Values less than 0 have no logarithm
                return item > 0;
              });
              const maxData = Math.max(...filtersData);
              const minData = Math.min(...filtersData);
              sampleObject.max = maxData;
              if (maxData === minData) {
                sampleObject.isEqual = true;
              } else {
                sampleObject.isEqual = false;
              }

              sampleObject.charData.oriData[0] = tempObject;

              if (hasInvalidData) {
                this.$set(sampleObject, 'invalidData', true);
              } else {
                this.$set(sampleObject, 'invalidData', false);
              }

              sampleObject.charData.charOption = this.formateCharOption(
                  sampleIndex,
              );
              const tempOption = sampleObject.charData.charOption;
              if (
                tempOption.series[0].data.length === 1 ||
              sampleObject.onePoint
              ) {
                tempOption.series[0].showSymbol = true;
              } else {
                tempOption.series[0].showSymbol = false;
              }

              this.$forceUpdate();

              this.$nextTick(() => {
                if (sampleObject.charObj) {
                  sampleObject.charObj.hideLoading();
                }
                // Draw chart
                if (!this.compare) {
                  this.updateOrCreateChar(sampleIndex, true);
                }
              });
            })
            .catch((e) => {
              if (sampleObject.charObj) {
                sampleObject.charObj.clear();
              }
            });
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
      const oriData = sampleObject.charData.oriData;
      const runName = sampleObject.runNames;
      const curBackName = runName + this.backendString;
      const dataObj = {
        name: runName,
        data: [],
        type: 'line',
        showSymbol: false,
        lineStyle: {
          color: sampleObject.colors,
        },
        markLine: [],
      };
      const dataObjBackend = {
        name: curBackName,
        data: [],
        type: 'line',
        smooth: 0,
        symbol: 'none',
        lineStyle: {
          color: sampleObject.colors,
          opacity: 0.2,
        },
      };
      const curOriData = oriData[0];

      if (curOriData) {
        if (sampleObject.log) {
          dataObj.data = this.formateSmoothData(
              curOriData.logData[this.curBenchX],
          );
          dataObjBackend.data = curOriData.logData[this.curBenchX];
        } else {
          dataObj.data = this.formateSmoothData(
              curOriData.valueData[this.curBenchX],
          );
          dataObjBackend.data = curOriData.valueData[this.curBenchX];
        }
      } else {
        returnFlag = true;
      }

      seriesData.push(dataObj, dataObjBackend);
      if (returnFlag) {
        return;
      }
      const that = this;
      const fullScreenFun = this.toggleFullScreen;
      const yAxisFun = this.yAxisScale;
      const tempOption = {
        legend: {
          show: false,
        },
        xAxis: {
          type: 'value',
          show: true,
          scale: true,
          nameGap: 30,
          minInterval: this.isActive === 0 ? 1 : 0,
          axisLine: {
            lineStyle: {
              color: '#E6EBF5',
              width: 2,
            },
          },
          axisLabel: {
            color: '#9EA4B3',
            interval: 0,
            formatter(value) {
              if (that.isActive === 2) {
                if (sampleObject.fullScreen) {
                  const date = new Date(value * 1000);
                  const dateTime = date.toTimeString().split(' ')[0];
                  const dateYear = date.toDateString();
                  return dateTime + '\n' + dateYear;
                } else {
                  return '';
                }
              } else if (that.isActive === 1) {
                if (value < 1 && value.toString().length > 6) {
                  return value.toFixed(3);
                } else if (value.toString().length > 6) {
                  return value.toExponential(0);
                } else {
                  return value;
                }
              } else {
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
          // Logbase for very small values,default 10
          logBase: sampleObject.max < 1 && sampleObject.isEqual ? 0.1 : 10,
          inverse:
            sampleObject.log && sampleObject.max < 1 && sampleObject.isEqual
              ? true
              : false,
          axisLine: {
            lineStyle: {
              color: '#E6EBF5',
              width: 2,
            },
          },
          axisLabel: {
            color: '#9EA4B3',
            formatter(value) {
              if (sampleObject.zoomDataTimer) {
                clearTimeout(sampleObject.zoomDataTimer);
                sampleObject.zoomDataTimer = setTimeout(() => {
                  sampleObject.zoomDataTimer = null;
                }, 50);
                if (value < sampleObject.zoomData[0]) {
                  sampleObject.zoomData[0] = value;
                } else if (sampleObject.zoomData[1] < value) {
                  sampleObject.zoomData[1] = value;
                }
              } else {
                sampleObject.zoomData = [value, value];
                sampleObject.zoomDataTimer = setTimeout(() => {
                  sampleObject.zoomDataTimer = null;
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
          right: sampleObject.fullScreen ? 80 : 50,
        },
        animation: true,
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
          backgroundColor: 'rgba(50, 50, 50, 0.7)',
          borderWidth: 0,
          textStyle: {
            color: '#fff',
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
          formatter(params) {
            const unit = 's';
            const strhead =
              `<table class="char-tip-table" class="borderspacing3"><tr><td></td>` +
              `<td>${that.$t('scalar.charTipHeadName')}</td>` +
              `<td>${that.$t('scalar.charSmoothedValue')}</td>` +
              `<td>${that.$t('scalar.charTipHeadValue')}</td>` +
              `<td>${that.$t('scalar.step')}</td>` +
              `<td>${that.$t('scalar.relativeTime')}</td>` +
              `<td>${that.$t('scalar.absoluteTime')}</td>` +
              `</tr>`;
            let strBody = '';
            const runArr = [];
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
                  if (
                    curSerieOriData.stepData[parma.dataIndex][0] === curStep
                  ) {
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
                            curSerieOriData.stepData[parma.dataIndex][1] &&
                          detialArr[sameIndex].wallTime ===
                            curSerieOriData.absData[parma.dataIndex][0]
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
                  Math.ceil(parma.value[1] * 1000) / 1000 >=
                    sampleObject.zoomData[0] &&
                  Math.floor(parma.value[1] * 1000) / 1000 <=
                    sampleObject.zoomData[1]
                ) {
                  dataCount++;
                  runArr.push(parma.seriesName);
                  detialArr.push({
                    value: curSerieOriData.stepData[parma.dataIndex][1],
                    step: curSerieOriData.stepData[parma.dataIndex][0],
                    wallTime: curSerieOriData.absData[parma.dataIndex][0],
                    dataIndex: parma.dataIndex,
                  });
                  strBody +=
                    `<tr><td style="border-radius:50%;width:15px;height:15px;vertical-align: middle;` +
                    `margin-right: 5px;background-color:${
                      parma.color === that.thresholdColor &&
                      sampleObject.charData.charOption.visualMap
                        ? that.thresholdColor
                        : sampleObject.colors
                    };` +
                    `display:inline-block;"></td><td>${parma.seriesName}</td>` +
                    `<td>${that.formateYaxisValue(parma.value[1])}</td>` +
                    `<td>${that.formateYaxisValue(
                        curSerieOriData.stepData[parma.dataIndex][1],
                    )}</td>` +
                    `<td>${curSerieOriData.stepData[parma.dataIndex][0]}</td>` +
                    `<td>${curSerieOriData.relativeData[
                        parma.dataIndex
                    ][0].toFixed(3)}${unit}</td>` +
                    `<td>${that.dealrelativeTime(
                        new Date(
                            curSerieOriData.absData[parma.dataIndex][0] * 1000,
                        ).toString(),
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
              icon: CommonProperty.fullScreenIcon,
              onclick() {
                fullScreenFun(sampleIndex);
              },
            },
            myTool2: {
              show: true,
              title:
                sampleObject.max <= 0
                  ? this.$t('scalar.noLog')
                  : this.$t('scalar.toggleYaxisScale'),
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
     * @param {Boolean} isSetVisualMap IsSetVisualMap
     */

    updateOrCreateChar(sampleIndex, isSetVisualMap) {
      const sampleObject = this.originDataArr[sampleIndex];
      if (!sampleObject) {
        return;
      }
      if (sampleObject.charObj) {
        // Updating chart option
        if (sampleObject.updateFlag) {
          sampleObject.charObj.setOption(
              sampleObject.charData.charOption,
              sampleObject.dataRemove,
          );
          sampleObject.updateFlag = false;
          sampleObject.dataRemove = false;
        }
      } else {
        // Create chart
        sampleObject.charObj = echarts.init(
            document.getElementById(sampleObject.domId),
            null,
        );
        sampleObject.charObj.setOption(sampleObject.charData.charOption, true);
        this.setOnePoint(sampleObject);
        this.setRestore(sampleObject);
      }
      if (isSetVisualMap) {
        this.updateVisualMap(sampleObject);
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
        sampleObject.charData.charOption.toolbox.feature.myToolFullScreen.iconStyle.borderColor =
          '#00A5A7';
        sampleObject.charData.charOption.grid.right = 80;
      } else {
        sampleObject.charData.charOption.toolbox.feature.myToolFullScreen.iconStyle.borderColor =
          '#6D7278';
        sampleObject.charData.charOption.grid.right = 50;
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
      // Obtains the chart subscript
      this.originDataArr.forEach((sampleItem) => {
        if (this.multiSelectedTagNames[sampleItem.tagName]) {
          curFilterSamples.push(sampleItem);
        }
      });
      this.curFilterSamples = curFilterSamples;
      // Obtains data on the current page
      this.getCurPageDataArr(noPageDataNumChange);
    },

    /**
     *
     * The time display type is changed
     */

    timeTypeChange(val) {
      if (this.isTimeReload) {
        this.autoUpdateSamples();
      }
      if (this.axisBenchChangeTimer) {
        clearTimeout(this.axisBenchChangeTimer);
        this.axisBenchChangeTimer = null;
      }
      this.axisBenchChangeTimer = setTimeout(() => {
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
        // Update the horizontal benchmark of the default data
        this.curPageArr.forEach((sampleObject) => {
          if (sampleObject.charObj) {
            sampleObject.charData.oriData.forEach((originData, index) => {
              const seriesData = sampleObject.charData.charOption.series;
              const oriIndexData = sampleObject.charData.oriData[index];
              if (sampleObject.log) {
                seriesData[index * 2].data = this.formateSmoothData(
                    oriIndexData.logData[this.curBenchX],
                );
                seriesData[index * 2 + 1].data =
                  oriIndexData.logData[this.curBenchX];
              } else {
                seriesData[index * 2].data = this.formateSmoothData(
                    oriIndexData.valueData[this.curBenchX],
                );
                seriesData[index * 2 + 1].data =
                  oriIndexData.valueData[this.curBenchX];
              }
            });

            const optionxAxis = sampleObject.charData.charOption.xAxis;
            const seriesData = sampleObject.charData.charOption.series[0];
            optionxAxis.minInterval = this.isActive === 0 ? 1 : 0;
            sampleObject.updateFlag = true;
            sampleObject.charObj.clear();

            if (seriesData.data.length === 1) {
              seriesData.showSymbol = true;
              sampleObject.onePoint = true;
            } else {
              seriesData.showSymbol = false;
              sampleObject.onePoint = false;
            }
            this.updateOrCreateChar(sampleObject.sampleIndex, true);
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
     * @param {Object} selectedItemDict Dictionary containing the selected tags
     */

    tagSelectedChanged(selectedItemDict) {
      if (!selectedItemDict) {
        return;
      }
      if (this.isTimeReload) {
        this.autoUpdateSamples();
      }
      this.multiSelectedTagNames = selectedItemDict;
      // Reset to the first page
      this.pageIndex = 0;
      this.updateTagInPage();
    },

    /**
     *Window resize
     */

    resizeCallback() {
      if (!this.compare) {
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
      }
    },

    /**
     * Clear data
     */

    clearAllData() {
      this.multiSelectedTagNames = {};
      this.curFilterSamples = [];
      this.tagOperateList = [];
      this.pageIndex = 0;
      this.originDataArr = [];
      this.oriDataDictionaries = {};
      this.curPageArr = [];
      this.tagPropsList = [];
      this.propsList = [];
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
      if (error.response && error.response.data) {
        this.clearAllData();
      } else {
        if (
          !(error.code === 'ECONNABORTED' && /^timeout/.test(error.message))
        ) {
          // Clear data
          this.clearAllData();
        }
      }
    },

    /**
     * Delete the data that does not exist
     * @param {Object} oriData Original run and tag data
     */

    removeNonexistentData(oriData) {
      if (!oriData) {
        return false;
      }
      const newTagDictionaries = {}; // Index of the tag in the new data
      let dataRemoveFlag = false;
      oriData.tags.forEach((tagName) => {
        newTagDictionaries[tagName] = true;
      });
      // Delete the tag that does not exist
      const oldTagListLength = this.tagOperateList.length;
      for (let i = oldTagListLength - 1; i >= 0; i--) {
        if (!newTagDictionaries[this.tagOperateList[i].label]) {
          dataRemoveFlag = true;
          delete this.oriDataDictionaries[this.tagOperateList[i].label];
          this.tagOperateList.splice(i, 1);
        }
      }

      // Except the old data in the chart
      const oldSampleLength = this.originDataArr.length;

      for (let i = oldSampleLength - 1; i >= 0; i--) {
        const oldSample = this.originDataArr[i];
        if (!newTagDictionaries[oldSample.tagName]) {
          dataRemoveFlag = true;
          this.originDataArr.splice(i, 1);
        }
      }
      return dataRemoveFlag;
    },

    /**
     * Check and add new data
     * @param {Object} oriData Original run and tag data
     */

    checkNewDataAndComplete(oriData) {
      if (!oriData) {
        return false;
      }
      let dataAddFlag = false;
      const runColor = CommonProperty.commonColorArr[0];
      oriData.tags.forEach((tagObj) => {
        if (!this.oriDataDictionaries[tagObj]) {
          this.oriDataDictionaries[tagObj] = true;
          this.tagOperateList.push({
            label: tagObj,
            checked: true,
            show: false,
          });
          const sampleIndex = this.originDataArr.length;
          dataAddFlag = true;
          this.originDataArr.push({
            tagName: tagObj,
            runNames: oriData.name,
            colors: runColor,
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
            zoomDataTimer: null,
            charObj: null,
          });
          this.DomIdIndex++;
        }
      });
      return dataAddFlag;
    },

    /**
     * Update all data
     * @param {Boolean} ignoreError Whether ignore error tip
     */

    updateAllData(ignoreError) {
      const params = {
        plugin_name: 'scalar',
        train_id: this.trainingJobId,
      };
      RequestService.getSingleTrainJob(params, ignoreError)
          .then((res) => {
            if (this.isReloading) {
              this.$store.commit('setIsReload', false);
              this.isReloading = false;
            }

            // Fault tolerance processing
            if (!res || !res.data) {
              return;
            } else if (!res.data.train_jobs || !res.data.train_jobs.length) {
              this.clearAllData();
              return;
            }
            const data = res.data.train_jobs[0];
            // Delete the data that does not exist
            const tagRemoveFlag = this.removeNonexistentData(data);

            // Check whether new data exists and add it to the page
            const tagAddFlag = this.checkNewDataAndComplete(data);

            this.$nextTick(() => {
              this.multiSelectedTagNames = this.$refs.multiselectGroupComponents.updateSelectedDic();
              this.updateTagInPage(!tagRemoveFlag && !tagAddFlag);
              this.resizeCallback();
            });

            const tempTagList = [];
            const propsList = [];
            // Initial chart data
            data.tags.forEach((tagObj) => {
            // Check whether the tag with the same name exists
              tempTagList.push({
                label: tagObj,
                checked: true,
                show: true,
              });

              // Add the tag list
              propsList.push({
                tagName: tagObj,
                runNames: data.name,
                colors: '',
              });
            });
            this.tagPropsList = tempTagList;
            this.propsList = propsList;
          }, this.requestErrorCallback)
          .catch((e) => {
            this.$message.error(this.$t('public.dataError'));
          });
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
     * Format absolute Time
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

      if (this.isTimeReload) {
        this.autoUpdateSamples();
      }

      // Update the smoothness of initialized data
      this.curPageArr.forEach((sampleObject) => {
        if (sampleObject.charObj) {
          const log = sampleObject.log;
          sampleObject.charData.charOption.series.forEach((singleItem, index) => {
            if (index % 2 === 0) {
              if (log) {
                singleItem.data = this.formateSmoothData(
                    sampleObject.charData.oriData[index / 2].logData[
                        this.curBenchX
                    ],
                );
              } else {
                singleItem.data = this.formateSmoothData(
                    sampleObject.charData.oriData[index / 2].valueData[
                        this.curBenchX
                    ],
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
     * @param {String} value number y
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
     * YAxis Scale
     * @param {Number} sampleIndex Number
     */

    yAxisScale(sampleIndex) {
      if (this.isTimeReload) {
        this.autoUpdateSamples();
      }
      if (this.yAxisScaleTimer) {
        clearTimeout(this.yAxisScaleTimer);
        this.yAxisScaleTimer = null;
      }
      const sampleObject = this.originDataArr[sampleIndex];
      if (!sampleObject) {
        return;
      }
      // There is no logarithm of 0 and negative numbers
      if (sampleObject.max <= 0) {
        return;
      }
      this.yAxisScaleTimer = setTimeout(() => {
        const tempOption = sampleObject.charData.charOption;
        const tempOriData = sampleObject.charData.oriData;
        const log = !sampleObject.log;
        if (log) {
          tempOption.toolbox.feature.myTool2.iconStyle.borderColor = '#00A5A7';
          tempOption.yAxis.type = 'log';
          // Logarithmic axis scale ascending, maximum scale 1
          if (sampleObject.max < 1 && sampleObject.isEqual) {
            tempOption.yAxis.inverse = true;
          }
        } else {
          tempOption.yAxis.type = 'value';
          tempOption.toolbox.feature.myTool2.iconStyle.borderColor = '#666';
          tempOption.yAxis.inverse = false;
        }
        tempOriData.forEach((originData, index) => {
          if (log) {
            tempOption.series[index * 2].data = this.formateSmoothData(
                tempOriData[index].logData[this.curBenchX],
            );
            tempOption.series[index * 2 + 1].data =
              tempOriData[index].logData[this.curBenchX];
          } else {
            tempOption.series[index * 2].data = this.formateSmoothData(
                tempOriData[index].valueData[this.curBenchX],
            );
            tempOption.series[index * 2 + 1].data =
              tempOriData[index].valueData[this.curBenchX];
          }
        });
        sampleObject.log = log;
        sampleObject.updateFlag = true;
        sampleObject.charObj.clear();

        const dataObj = tempOption.series[0];

        // One point
        if (dataObj.data.length === 1) {
          tempOption.series[0].showSymbol = true;
          sampleObject.onePoint = true;
        } else {
          tempOption.series[0].showSymbol = false;
          sampleObject.onePoint = false;
        }
        if (
          tempOption.visualMap &&
          tempOption.visualMap['pieces'] &&
          tempOption.visualMap['pieces'].length > 0
        ) {
          tempOption.visualMap = null;
          tempOption.series[0].markLine = null;
          sampleObject.charObj.setOption(tempOption, true);
          this.updateVisualMap(sampleObject);
        } else {
          this.updateOrCreateChar(sampleIndex);
        }
      }, 500);
    },

    /**
     * Scalar synthesis
     */

    compareClick() {
      this.compare = !this.compare;
      if (this.compare) {
        this.scalarCompare = this.$t('scalar.compareCancel');
        this.$bus.$emit('updateTag');
      } else {
        this.scalarCompare = this.$t('scalar.comparison');

        this.curPageArr.forEach((sampleObject) => {
          // Draw chart
          if (!sampleObject.charObj) {
            this.updateOrCreateChar(sampleObject.sampleIndex);
          }
        });

        this.$nextTick(() => {
          this.resizeCallback();
        });
      }
    },

    /**
     * Jump back to train dashboard
     */

    jumpToTrainDashboard() {
      this.$router.push({
        path: '/train-manage/training-dashboard',
        query: {
          id: this.trainingJobId,
        },
      });
    },
  },
  components: {
    ScalarButton,
    ScalarCompare,
    multiselectGroupComponents,
  },
};
</script>
<style>
.cl-scalar-manage {
  height: 100%;
}
.cl-scalar-manage .el-dialog {
  border-radius: 4px;
}
.cl-scalar-manage .el-dialog__header {
  padding: 15px 15px 10px;
  font-size: 14px;
}
.cl-scalar-manage .el-dialog__header .el-dialog__title {
  font-size: 14px;
}
.cl-scalar-manage .el-dialog__body {
  padding: 10px 15px;
}
.cl-scalar-manage .el-dialog__footer {
  padding: 5px 15px 10px;
}
.cl-scalar-manage .w60 {
  width: 60px;
  margin-left: 20px;
}
.cl-scalar-manage .w261 {
  width: 261px;
}
.cl-scalar-manage .smallSelect {
  width: 80px;
}
.cl-scalar-manage .smallSelectTwo {
  width: 100px;
}
.cl-scalar-manage .smallInput {
  width: 120px;
}
.cl-scalar-manage .scalar-btn {
  height: 32px;
  line-height: 32px;
  padding: 0 20px;
  color: #00a5a7;
  border: 1px solid #00a5a7;
  border-radius: 2px;
}
.cl-scalar-manage .borderspacing3 {
  border-spacing: 3px;
}
.cl-scalar-manage .scalar-bk {
  height: 100%;
  background-color: #fff;
  display: flex;
  flex-direction: column;
}
.cl-scalar-manage .scalar-bk .path-message {
  display: inline-block;
  line-height: 20px;
  padding: 0px 4px 15px 4px;
  font-weight: bold;
  vertical-align: bottom;
}
.cl-scalar-manage .scalar-bk .cl-scalar-title {
  height: 56px;
  line-height: 56px;
}
.cl-scalar-manage .select-all {
  flex-shrink: 0;
  cursor: pointer;
}
.cl-scalar-manage .cl-eval-operate-content {
  width: 100%;
  padding: 8px 32px 22px 32px;
  background: #ffffff;
}
.cl-scalar-manage .cl-eval-operate-content .tag-select-content {
  display: flex;
  align-items: center;
}
.cl-scalar-manage .cl-eval-operate-content .tag-select-content .title {
  flex-shrink: 0;
}
.cl-scalar-manage .cl-eval-operate-content .tag-select-content .select-item-content {
  display: flex;
  height: 16px;
  flex-wrap: wrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cl-scalar-manage .cl-eval-operate-content .tag-select-content .run-select-content-open {
  flex: 1;
  text-align: right;
  font-size: 14px;
  color: #00a5a7;
  cursor: pointer;
  min-width: 60px;
}
.cl-scalar-manage .cl-eval-operate-content .run-select-content-all {
  max-height: 150px;
  padding-left: 72px;
  overflow-x: hidden;
  display: flex;
  flex-wrap: wrap;
}
.cl-scalar-manage .cl-eval-operate-content .run-select-content-all .label-item {
  line-height: 14px;
}
.cl-scalar-manage .cl-eval-operate-content .run-select-content-all .select-item {
  height: 25px;
  margin-top: 25px;
}
.cl-scalar-manage .cl-eval-operate-content .select-item {
  margin-right: 20px;
  flex-shrink: 0;
  margin-bottom: 1px;
  cursor: pointer;
}
.cl-scalar-manage .cl-eval-operate-content .select-item .label-item {
  width: 100px;
  display: block;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
  text-align: left;
}
.cl-scalar-manage .cl-eval-operate-content .multiCheckBox-border {
  width: 16px;
  height: 16px;
  display: block;
  margin-right: 20px;
  cursor: pointer;
  float: left;
}
.cl-scalar-manage .cl-eval-operate-content .checkbox-checked {
  background-image: url("../../assets/images/mult-select.png");
}
.cl-scalar-manage .cl-eval-operate-content .checkbox-unchecked {
  background-image: url("../../assets/images/mult-unselect.png");
}
.cl-scalar-manage .cl-eval-operate-content .checkbox-disabled {
  opacity: 0.2;
}
.cl-scalar-manage .cl-eval-operate-content .label-item {
  font-size: 14px;
  line-height: 14px;
  vertical-align: middle;
}
.cl-scalar-manage .cl-eval-operate-content .label-item .el-tooltip {
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
  text-align: left;
  height: 16px;
}
.cl-scalar-manage .cl-eval-operate-content .label-item span {
  font-size: 14px;
  line-height: 14px;
  display: block;
}
.cl-scalar-manage .cl-eval-slider-operate-content {
  background: #ffffff;
  padding: 0 32px 21px 32px;
  display: flex;
  align-items: center;
  border-bottom: 2px solid #e6ebf5;
}
.cl-scalar-manage .cl-eval-slider-operate-content .xaxis-title {
  font-size: 14px;
  line-height: 14px;
  vertical-align: middle;
  margin-right: 16px;
  flex-shrink: 0;
}
.cl-scalar-manage .cl-eval-slider-operate-content .el-radio-group {
  margin-right: 64px;
  flex-shrink: 0;
}
.cl-scalar-manage .cl-eval-slider-operate-content .el-select {
  width: 163px;
  margin-right: 16px;
  flex-shrink: 0;
}
.cl-scalar-manage .cl-eval-slider-operate-content .el-slider {
  width: 400px;
  flex-shrink: 0;
}
.cl-scalar-manage .cl-eval-slider-operate-content .el-slider .el-input.el-input--small {
  width: 60px;
}
.cl-scalar-manage .cl-eval-slider-operate-content .el-slider .el-input-number .el-input__inner {
  padding-left: 0px;
  padding-right: 0px;
}
.cl-scalar-manage .cl-eval-slider-operate-content .el-slider .el-input-number--small .el-input-number__increase {
  display: none;
}
.cl-scalar-manage .cl-eval-slider-operate-content .el-slider .el-input-number--small .el-input-number__decrease {
  display: none;
}
.cl-scalar-manage .cl-eval-show-data-content {
  background: #fff;
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-wrap: wrap;
  padding-right: 10px;
}
.cl-scalar-manage .cl-eval-show-data-content .data-content {
  display: flex;
  height: 100%;
  width: 100%;
  flex-wrap: wrap;
  min-height: 400px;
  padding-left: 20px;
}
.cl-scalar-manage .cl-eval-show-data-content .data-content .sample-content {
  width: 33.3%;
  height: 400px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  padding-right: 20px;
  margin-top: 20px;
}
.cl-scalar-manage .cl-eval-show-data-content .data-content .char-full-screen {
  width: 100%;
  height: 400px;
}
.cl-scalar-manage .cl-eval-show-data-content .chars-container {
  flex: 1;
  position: relative;
  background-color: #edf0f5;
  padding: 5px;
}
.cl-scalar-manage .cl-eval-show-data-content .chartThreshold {
  height: 40px;
  background-color: #edf0f5;
  border-top: 1px solid #fff;
  display: flex;
  line-height: 40px;
}
.cl-scalar-manage .cl-eval-show-data-content .chartThreshold .chartThresholdLeft {
  flex: 1;
  text-align: left;
  padding-left: 5px;
  font-size: 14px;
  color: #6c7280;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cl-scalar-manage .cl-eval-show-data-content .chartThreshold .chartThresholdRight {
  width: 120px;
  text-align: right;
  padding-right: 10px;
  font-size: 12px;
  color: #00a5a7;
  flex-shrink: 0;
}
.cl-scalar-manage .cl-eval-show-data-content .chartThreshold .chartThresholdRight span {
  cursor: pointer;
  width: auto;
  height: 39px;
  display: inline-block;
}
.cl-scalar-manage .cl-eval-show-data-content .tag-name {
  color: #333;
  font-size: 16px;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 600;
  text-align: center;
  margin-top: 10px;
}
.cl-scalar-manage .cl-eval-show-data-content .tag-name i {
  color: #e6a23c;
}
.cl-scalar-manage .cl-eval-show-data-content .char-item-content {
  width: 100%;
  height: 100%;
  background-color: #fff;
}
.cl-scalar-manage .cl-eval-show-data-content .char-tip-table td {
  padding-left: 5px;
  padding-right: 5px;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 150px;
  overflow: hidden;
}
.cl-scalar-manage .cl-eval-show-data-content .image-noData {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}
.cl-scalar-manage .cl-eval-show-data-content .noData-text {
  margin-top: 33px;
  font-size: 18px;
}
.cl-scalar-manage .pagination-content {
  text-align: right;
  padding: 24px 32px;
}
.cl-scalar-manage .mr24 {
  margin-right: 24px;
}
.cl-scalar-manage .select-disable {
  -moz-user-select: none;
  /*Firefox*/
  -webkit-user-select: none;
  /*Webkit*/
  -ms-user-select: none;
  /*IE10*/
  -khtml-user-select: none;
  user-select: none;
}
.cl-scalar-manage .cl-close-btn {
  width: 20px;
  height: 20px;
  vertical-align: -3px;
  cursor: pointer;
  display: inline-block;
  line-height: 20px;
  margin-left: 32px;
}
.cl-scalar-manage .thresholdAll {
  display: flex;
  line-height: 32px;
  margin-bottom: 10px;
}
.cl-scalar-manage .thresholdAll .thresholdItem {
  margin-right: 10px;
}
.cl-scalar-manage .thresholdAll .thresholdItemWidth {
  width: 500px;
  height: 32px;
  margin-right: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cl-scalar-manage .thresholdError {
  color: #f56c6c;
  text-align: center;
}
.cl-scalar-manage .fs16 {
  font-size: 14px;
  color: #6c7280;
  width: 180px;
}

.tooltip-show-content {
  max-width: 50%;
}
.cl-title-right {
  padding-right: 20px;
}

.delDialog .delThresholdItem {
  display: flex;
  margin-bottom: 10px;
}

.delDialog .delThresholdIcon {
  color: #e6a23c;
  font-size: 24px;
  width: 40px;
  margin-right: 10px;
}

.delDialog .delThresholdInfo {
  line-height: 24px;
  height: 24px;
}
</style>

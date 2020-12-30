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
  <div class="cl-tensor-manage">
    <div class="tensor-bk">
      <!-- Title area -->
      <div class="cl-title cl-tensor-title">
        <div class="cl-title-left">{{$t('tensors.titleText')}}
          <div class="path-message">
            <span>{{$t('symbols.leftbracket')}}</span>
            <span>{{$t('trainingDashboard.summaryDirPath')}}</span>
            <span>{{summaryPath}}</span>
            <span>{{$t('symbols.rightbracket')}}</span>
          </div>
        </div>
        <div class="cl-title-right">
          <div class="cl-close-btn"
               @click="jumpToTrainDashboard">
            <img src="@/assets/images/close-page.png" />
          </div>
        </div>
      </div>
      <!-- List item operation area -->
      <div class="cl-tensor-operate-content">
        <multiselectGroupComponents ref="multiselectGroupComponents"
                                    :checkListArr="tagList"
                                    @selectedChange="tagSelectedChanged"></multiselectGroupComponents>
      </div>
      <!-- Area for selecting a view type -->
      <div class="cl-tensor-view-type-select-content">
        <div class="view-title">{{$t('tensors.viewTypeTitle')}}</div>
        <el-radio-group v-model="curDataType"
                        fill="#00A5A7"
                        text-color="#FFFFFF"
                        size="small"
                        @change="dataTypeChange">
          <el-radio-button :label="0">{{$t('tensors.chartViewType')}}</el-radio-button>
          <el-radio-button :label="1">{{$t('tensors.histogramViewType')}}</el-radio-button>
        </el-radio-group>
        <div class="view-title"
             v-if="!!curDataType">{{$t('histogram.viewType')}}
        </div>
        <el-radio-group v-model="curViewName"
                        v-if="!!curDataType"
                        fill="#00A5A7"
                        text-color="#FFFFFF"
                        size="small"
                        @change="viewTypeChange">
          <el-radio-button :label="0">{{$t('histogram.overlay')}}</el-radio-button>
          <el-radio-button :label="1">{{$t('histogram.offset')}}</el-radio-button>
        </el-radio-group>
        <div class="view-title"
             v-if="!!curViewName && !!curDataType">
          {{$t('histogram.xAxisTitle')}}
        </div>
        <el-radio-group v-model="curAxisName"
                        fill="#00A5A7"
                        text-color="#FFFFFF"
                        size="small"
                        v-if="!!curDataType && !!curViewName"
                        :disabled="curViewName === 0"
                        @change="timeTypeChange">
          <el-radio-button :label="0">{{$t('histogram.step')}}</el-radio-button>
          <el-radio-button :label="1">{{$t('histogram.relativeTime')}}</el-radio-button>
          <el-radio-button :label="2">{{$t('histogram.absoluteTime')}}</el-radio-button>
        </el-radio-group>
      </div>
      <!-- Content display area -->
      <div class="cl-show-data-content">
        <!-- No data -->
        <div class="image-noData"
             v-if="!originDataArr.length">
          <div>
            <img :src="require('@/assets/images/nodata.png')" />
          </div>
          <div v-if="initOver"
               class="noData-text">{{$t('public.noData')}}</div>
          <div v-else
               class="noData-text">{{$t("public.dataLoading")}}</div>
        </div>
        <!-- Data -->
        <div class="data-content"
             v-if="!!originDataArr.length">
          <div id="echartTip"
               v-show="chartTipFlag">
            <table class="char-tip-table borderspacing3">
              <tr>
                <td>{{$t('histogram.centerValue')}}</td>
                <td>{{$t('histogram.step')}}</td>
                <td>{{$t('histogram.relativeTime')}}</td>
                <td>{{$t('histogram.absoluteTime')}}</td>
              </tr>
              <tr id="tipTr"></tr>
            </table>
          </div>
          <div class="sample-content"
               v-for="sampleItem in originDataArr"
               :key="sampleItem.ref"
               :class="sampleItem.fullScreen ? 'char-full-screen' : ''"
               v-show="sampleItem.show">
            <div class="chars-container">
              <!-- Components -->
              <gridTableComponents v-if="!curDataType"
                                   :ref="sampleItem.ref"
                                   :fullScreen="sampleItem.fullScreen"
                                   @martixFilterChange="filterChange($event, sampleItem)"
                                   @toggleFullScreen="toggleFullScreen(sampleItem)"
                                   :columnLimitNum="columnLimitNum"
                                   :fullData="sampleItem.curData"></gridTableComponents>
              <histogramUntil v-else
                              :ref="sampleItem.ref"
                              :fullScreen="sampleItem.fullScreen"
                              @chartTipFlagChange="chartTipFlagChange"
                              @toggleFullScreen="toggleFullScreen(sampleItem)"
                              :viewName="curViewName"
                              :axisName="curAxisName"
                              :fullData="sampleItem.curData"></histogramUntil>
              <div class="loading-cover"
                   v-if="sampleItem.showLoading">
                <i class="el-icon-loading"></i></div>
            </div>
            <!-- Information display area -->
            <div class="sample-data-show"
                 v-if="!curDataType">
              <div class="tensor-demension"
                   :title="sampleItem.curDims">
                {{$t('tensors.dimension')}}
                <span>{{sampleItem.curDims}}</span>
              </div>
              <div class="tensor-type"
                   :title="sampleItem.curDataType">
                {{$t('tensors.tensorType')}} {{sampleItem.curDataType}}
              </div>
              <!-- Current step information -->
              <div class="sample-operate-info select-disable">
                <span class="step-info"
                      :title="sampleItem.curStep">{{$t('images.step')}}{{sampleItem.curStep}}</span>
                <span class="time-info"
                      :title="sampleItem.curTime">{{sampleItem.curTime}}</span>
              </div>
              <el-slider class="step-slider"
                         v-model="sampleItem.sliderValue"
                         :step="1"
                         :max="sampleItem.totalStepNum"
                         @input="sliderChange(sampleItem.sliderValue, sampleItem)"
                         :show-tooltip="false"
                         :disabled="sampleItem.totalStepNum === 0">
              </el-slider>
            </div>
            <div class="tag-title"
                 :title="sampleItem.tagName">{{sampleItem.tagName}}
            </div>
          </div>
        </div>
      </div>
      <!-- Page number area -->
      <div class="pagination-content"
           v-if="originDataArr.length">
        <el-pagination @current-change="currentPageChange"
                       :current-page="pageIndex + 1"
                       :page-sizes="pageSizes"
                       :page-size="pageNum"
                       layout="total, prev, pager, next, jumper"
                       :total="curFilterSamples.length">
        </el-pagination>
      </div>
    </div>
  </div>
</template>

<script>
import multiselectGroupComponents from '../../components/multiselect-group.vue';
import gridTableComponents from '../../components/grid-table-simple';
import histogramUntil from '../../components/histogram-unit';
import RequestService from '../../services/request-service';
import autoUpdate from '../../mixins/auto-update.vue';
export default {
  mixins: [autoUpdate],
  data() {
    return {
      tagList: [], // Tag list.
      trainingJobId: this.$route.query.train_id, // ID of the current training job.
      summaryPath: this.$route.query.summaryPath,
      originDataArr: [], // List of all data.
      initOver: false, // Indicates whether the initialization is complete.
      curFullTagDic: {}, // Dictionary that contains all the current tags.
      multiSelectedTagNames: {}, // Dictionary for storing the name of the selected tags.
      curFilterSamples: [], // List of data that meet the current filter criteria.
      curPageArr: [], // Data list on the current page.
      pageIndex: 0, // Current page number.
      pageSizes: [6], // The number of records on each page is optional.
      pageNum: 6, // Number of records on each page.
      dataTypeChangeTimer: null, // View switching timer
      viewNameChangeTimer: null, // ViewName switching timer
      axisNameChangeTimer: null, // Vertical axis switching timer
      curDataType: 0, // Current data type
      curViewName: 1, // Current histogram view type
      curAxisName: 0, // Current histogran axis type
      chartTipFlag: false, // Wheather to display tips of the histogram
      columnLimitNum: 1000, // Maximum number of columns is 1000
    };
  },
  computed: {},
  components: {
    multiselectGroupComponents,
    gridTableComponents,
    histogramUntil,
  },
  watch: {},
  destroyed() {
    window.removeEventListener('resize', this.resizeCallback);

    // Cancel the delay
    this.originDataArr.forEach((sampleItem) => {
      if (sampleItem.sliderChangeTimer) {
        clearTimeout(sampleItem.sliderChangeTimer);
        sampleItem.sliderChangeTimer = null;
      }
    });
    if (this.charResizeTimer) {
      clearTimeout(this.charResizeTimer);
      this.charResizeTimer = null;
    }
    if (this.dataTypeChangeTimer) {
      clearTimeout(this.dataTypeChangeTimer);
      this.dataTypeChangeTimer = null;
    }
    if (this.viewNameChangeTimer) {
      clearTimeout(this.viewNameChangeTimer);
      this.viewNameChangeTimer = null;
    }
    if (this.axisNameChangeTimer) {
      clearTimeout(this.axisNameChangeTimer);
      this.axisNameChangeTimer = null;
    }
  },
  mounted() {
    this.init();
    window.addEventListener('resize', this.resizeCallback, false);
  },
  methods: {
    /**
     * Callback after the window size is changed
     */
    resizeCallback() {
      if (this.charResizeTimer) {
        clearTimeout(this.charResizeTimer);
        this.charResizeTimer = null;
      }
      this.charResizeTimer = setTimeout(() => {
        this.curPageArr.forEach((sampleItem) => {
          const elementItem = this.$refs[sampleItem.ref];
          if (elementItem) {
            elementItem[0].resizeView();
          }
        });
      }, 500);
    },
    /**
     * Initialize
     */
    init() {
      this.getOriginData();
      if (this.isTimeReload) {
        this.autoUpdateSamples();
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
    /**
     * Obtains original data.
     */
    getOriginData() {
      const params = {
        plugin_name: 'tensor',
        train_id: this.trainingJobId,
      };
      RequestService.getSingleTrainJob(params)
          .then((res) => {
            if (
              !res ||
            !res.data ||
            !res.data.train_jobs ||
            !res.data.train_jobs.length
            ) {
              this.initOver = true;
              return;
            }
            const data = res.data.train_jobs[0];
            if (!data.tags) {
              return;
            }
            const tagList = [];
            const dataList = [];
            data.tags.forEach((tagName, tagIndex) => {
              if (!this.curFullTagDic[tagName]) {
                this.curFullTagDic[tagName] = true;
                tagList.push({
                  label: tagName,
                  checked: true,
                  show: true,
                });
                dataList.push({
                  tagName: tagName,
                  summaryName: this.trainingJobId,
                  show: false,
                  showLoading: false,
                  sliderValue: 0,
                  newDataFlag: true,
                  totalStepNum: 0,
                  curStep: '',
                  curTime: '',
                  curDims: '',
                  curDataType: '',
                  fullScreen: false,
                  ref: tagName,
                  sliderChangeTimer: null,
                  curData: [],
                  formateData: [],
                  fullData: [],
                  filterStr: '',
                  curMartixShowSliderValue: 0,
                });
              }
            });
            if (dataList.length === 1) {
              dataList[0].fullScreen = true;
            }
            this.tagList = tagList;
            this.originDataArr = dataList;
            this.$nextTick(() => {
              this.multiSelectedTagNames = this.$refs.multiselectGroupComponents.updateSelectedDic();
              this.initOver = true;
              this.updateTagInPage();
            });
          }, this.requestErrorCallback)
          .catch((e) => {
            this.initOver = true;
            this.$message.error(this.$t('public.dataError'));
          });
    },
    /**
     * Table dimension change callback
     * @param {Array} data Dimension array after change
     * @param {Object} sampleItem The object that is being operated
     */
    filterChange(data, sampleItem) {
      sampleItem.showLoading = true;
      sampleItem.filterStr = `[${data.toString()}]`;
      sampleItem.newDataFlag = true;
      this.freshtMartixData(sampleItem);
    },
    /**
     * The selected label is changed.
     * @param {Object} selectedItemDict Dictionary containing the selected tags
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
     * Page number change event
     * @param {Number} pageIndex Changed page number
     */
    currentPageChange(pageIndex) {
      this.pageIndex = pageIndex - 1;
      // Load the data on the current page
      this.getCurPageDataArr();
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
          if (this.curDataType === 1 && this.curViewName === 1) {
            const elementItem = this.$refs[sampleItem.ref];
            if (elementItem) {
              elementItem[0].clearZrData();
            }
          }
        });
      }
      // This interface is used to obtain the current page group and hide the current page group.
      const startIndex = this.pageIndex * this.pageNum;
      const endIndex = startIndex + this.pageNum;
      const curPageArr = [];
      for (let i = startIndex; i < endIndex; i++) {
        const sampleItem = this.curFilterSamples[i];
        if (sampleItem) {
          sampleItem.show = true;
          curPageArr.push(sampleItem);
        }
      }
      this.curPageArr = curPageArr;
      // Update the data information on the current page
      this.freshCurPageData();
    },
    /**
     * Refresh the data on the current page
     * @param {Boolean} isFromTypeChange
     */
    freshCurPageData(isFromTypeChange) {
      this.curPageArr.forEach((sampleItem, index) => {
        if (!sampleItem || !sampleItem.tagName) {
          return;
        }
        const dataType = this.curDataType;
        if (dataType) {
          this.getHistogramData(sampleItem);
        } else {
          sampleItem.newDataFlag = !!isFromTypeChange || sampleItem.newDataFlag;
          this.getMartixData(sampleItem);
        }
      });
    },
    /**
     * Initialize the current dimension selection
     * @param {Array} array Array containing the current number of dimensions
     * @return {Object} Current dimension selection
     */
    initFilterStr(array) {
      if (!array) {
        return [];
      }
      const countLinit = array.length - 2;
      const tempArr = [];
      for (let i = 0; i < array.length; i++) {
        tempArr.push(i >= countLinit ? ':' : '0');
      }
      if (tempArr.length) {
        const lastIndex = tempArr.length - 1;
        const lastFilter = tempArr[lastIndex];
        if (lastFilter && array[lastIndex] > this.columnLimitNum) {
          tempArr[lastIndex] = `0:${this.columnLimitNum}`;
        }
      }
      return `[${tempArr.toString()}]`;
    },
    /**
     * Obtains histogram data
     * @param {Object} sampleItem The object that is being operated
     */
    getHistogramData(sampleItem) {
      const params = {
        train_id: this.trainingJobId,
        tag: sampleItem.tagName,
        detail: 'histogram',
      };
      RequestService.getTensorsSample(params).then(
          (res) => {
            sampleItem.showLoading = false;
            if (!res || !res.data || !this.curDataType) {
              return;
            }
            if (!res.data.tensors || !res.data.tensors.length) {
              return;
            }
            const resData = JSON.parse(JSON.stringify(res.data.tensors[0]));
            sampleItem.summaryName = resData.train_id;
            // sampleItem.fullData = resData;
            sampleItem.curData = this.formHistogramOriData(resData);
            this.$nextTick(() => {
              const elementItem = this.$refs[sampleItem.ref];
              if (elementItem) {
                elementItem[0].updateHistogramData();
              }
            });
          },
          (e) => {
            this.freshDataErrorCallback(e, sampleItem, false);
          },
      );
    },
    /**
     * Obtain table data
     * @param {Object} sampleItem The object that is being operated
     */
    getMartixData(sampleItem) {
      const params = {
        train_id: this.trainingJobId,
        tag: sampleItem.tagName,
        detail: 'stats',
      };
      RequestService.getTensorsSample(params).then(
          (res) => {
            if (!res || !res.data || this.curDataType) {
              sampleItem.showLoading = false;
              return;
            }
            if (!res.data.tensors.length) {
              sampleItem.showLoading = false;
              return;
            }
            const resData = JSON.parse(JSON.stringify(res.data.tensors[0]));
            sampleItem.summaryName = resData.train_id;
            if (!resData.values.length) {
              sampleItem.fullData = [];
              sampleItem.formateData = [];
              sampleItem.curData = [];
              sampleItem.curTime = '';
              sampleItem.curDims = '';
              sampleItem.curDataType = '';
              sampleItem.curStep = '';
              sampleItem.sliderValue = 0;
              sampleItem.totalStepNum = 0;
              this.clearMartixData(sampleItem);
              sampleItem.showLoading = false;
              return;
            }
            const oldTotalStepNum = sampleItem.totalStepNum;
            sampleItem.totalStepNum = resData.values.length - 1;
            if (sampleItem.sliderValue === oldTotalStepNum) {
              sampleItem.sliderValue = sampleItem.totalStepNum;
            }
            if (sampleItem.sliderValue > sampleItem.totalStepNum) {
              sampleItem.sliderValue = sampleItem.totalStepNum;
            }
            sampleItem.fullData = resData.values;
            sampleItem.formateData = sampleItem.fullData[sampleItem.sliderValue];
            const oldStep = sampleItem.curStep;
            sampleItem.curStep = sampleItem.formateData.step;
            if (!sampleItem.filterStr) {
              sampleItem.filterStr = this.initFilterStr(
                  sampleItem.formateData.value.dims,
              );
              sampleItem.newDataFlag = true;
            }
            if (sampleItem.curStep !== oldStep) {
              sampleItem.newDataFlag = true;
            }
            sampleItem.curTime = this.dealrelativeTime(
                new Date(sampleItem.formateData.wall_time * 1000).toString(),
            );
            sampleItem.curDataType = sampleItem.formateData.value.data_type;
            sampleItem.curDims = JSON.stringify(
                sampleItem.formateData.value.dims,
            );
            this.freshtMartixData(sampleItem);
          },
          () => {
            sampleItem.fullData = [];
            sampleItem.formateData = [];
            sampleItem.curData = [];
            sampleItem.curTime = '';
            sampleItem.curDims = '';
            sampleItem.curDataType = '';
            sampleItem.curStep = '';
            sampleItem.sliderValue = 0;
            sampleItem.totalStepNum = 0;
            this.clearMartixData(sampleItem);
            sampleItem.showLoading = false;
          },
      );
    },
    /**
     * Refresh table display
     * @param {Object} sampleItem The object that is being operated
     */
    freshtMartixData(sampleItem) {
      const params = {
        train_id: this.trainingJobId,
        tag: sampleItem.tagName,
        detail: 'data',
        step: sampleItem.curStep,
        dims: encodeURIComponent(sampleItem.filterStr),
      };
      sampleItem.curMartixShowSliderValue = sampleItem.sliderValue;
      RequestService.getTensorsSample(params).then(
          (res) => {
            sampleItem.showLoading = false;
            if (!res || !res.data || this.curDataType) {
              return;
            }
            if (!res.data.tensors.length) {
              return;
            }
            const resData = res.data.tensors[0];
            const curStepData = resData.values[0];
            let statistics = {};
            if (curStepData) {
              sampleItem.curData =
              curStepData.value.data instanceof Array
                ? curStepData.value.data
                : [curStepData.value.data];
              statistics = curStepData.value.statistics;
            } else {
              sampleItem.curData = [[]];
            }
            let elementItem = null;
            this.$nextTick(() => {
              elementItem = this.$refs[sampleItem.ref];
              if (elementItem) {
                elementItem[0].updateGridData(
                    sampleItem.newDataFlag,
                    curStepData.value.dims,
                    statistics,
                    sampleItem.filterStr,
                );
              }
              sampleItem.newDataFlag = false;
            });
          },
          (e) => {
            this.freshDataErrorCallback(e, sampleItem, true);
          },
      );
    },
    /**
     * callback of fresh data
     * @param {Object} errorData The error object
     * @param {Object} sampleItem The object that is being operated
     * @param {Boolean} isMartix Martix data
     */
    freshDataErrorCallback(errorData, sampleItem, isMartix) {
      let showLimitError = false;
      let errorMsg = '';
      if (
        errorData.response &&
            errorData.response.data &&
            errorData.response.data.error_code &&
            (errorData.response.data.error_code.toString() === '50545013' ||
              errorData.response.data.error_code.toString() === '50545014' ||
              errorData.response.data.error_code.toString() === '50545016')
      ) {
        showLimitError = true;
        errorMsg = this.$t('error')[errorData.response.data.error_code];
      }
      if (isMartix) {
        this.clearMartixData(sampleItem, showLimitError, errorMsg);
      } else {
        this.$nextTick(() => {
          const elementItem = this.$refs[sampleItem.ref];
          if (elementItem) {
            elementItem[0].showRequestErrorMessage(errorMsg);
          }
        });
      }
      sampleItem.showLoading = false;
    },
    /**
     * Clear table display
     * @param {Object} sampleItem The object that is being operated
     * @param {Boolean} showLimitError Display request error message
     * @param {String} errorMsg Error message
     */
    clearMartixData(sampleItem, showLimitError, errorMsg) {
      sampleItem.curData = [];
      sampleItem.newDataFlag = true;
      let elementItem = null;
      this.$nextTick(() => {
        elementItem = this.$refs[sampleItem.ref];
        if (elementItem) {
          if (showLimitError) {
            elementItem[0].showRequestErrorMessage(
                errorMsg,
                sampleItem.formateData.value.dims,
                sampleItem.filterStr,
            );
          } else {
            elementItem[0].updateGridData();
          }
        }
      });
    },
    /**
     * The dataType display type is changed
     */
    dataTypeChange() {
      if (this.dataTypeChangeTimer) {
        clearTimeout(this.dataTypeChangeTimer);
        this.dataTypeChangeTimer = null;
      }
      this.dataTypeChangeTimer = setTimeout(() => {
        this.freshCurPageData(true);
      }, 500);
    },
    /**
     * The time display type is changed
     * @param {Number} val Current mode
     */
    timeTypeChange(val) {
      if (this.axisNameChangeTimer) {
        clearTimeout(this.axisNameChangeTimer);
        this.axisNameChangeTimer = null;
      }
      this.axisNameChangeTimer = setTimeout(() => {
        this.curPageArr.forEach((sampleItem) => {
          const elementItem = this.$refs[sampleItem.ref];
          if (elementItem) {
            elementItem[0].updateHistogramData();
          }
        });
      }, 500);
    },
    /**
     * The view display type is changed
     * @param {Number} val Current mode
     */
    viewTypeChange(val) {
      if (this.viewNameChangeTimer) {
        clearTimeout(this.viewNameChangeTimer);
        this.viewNameChangeTimer = null;
      }
      this.viewNameChangeTimer = setTimeout(() => {
        this.curPageArr.forEach((sampleItem) => {
          const elementItem = this.$refs[sampleItem.ref];
          if (elementItem) {
            elementItem[0].updateHistogramData();
          }
        });
      }, 200);
    },
    /**
     * Formate absolute time
     * @param {String} time Time string
     * @return {String} String Formatted time
     */
    dealrelativeTime(time) {
      const arr = time.split(' ');
      const str = `${arr[0]} ${arr[1]} ${arr[2]}, ${arr[4]}`;
      return str;
    },
    /**
     * Update the data list based on the filtered tags
     * @param {Boolean} noPageDataNumChange No new data is added or deleted
     */
    updateTagInPage(noPageDataNumChange) {
      const curFilterSamples = [];
      // Obtains data subscript that meets the tag filtering conditions
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
     * Clear data
     */
    clearAllData() {
      if (this.curDataType === 1 && this.curViewName === 1) {
        this.originDataArr.forEach((sampleItem) => {
          const elementItem = this.$refs[sampleItem.ref];
          if (elementItem) {
            elementItem[0].clearZrData();
          }
        });
      }
      this.tagList = [];
      this.originDataArr = [];
      this.curFullTagDic = {};
      this.multiSelectedTagNames = {};
      this.curFilterSamples = [];
      this.pageIndex = 0;
      this.curPageArr = [];
      this.$nextTick(() => {
        this.$refs.multiselectGroupComponents.updateSelectedDic();
      });
    },
    /**
     * error
     * @param {Object} error error object
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
     * Update all data.
     * @param {Boolean} ignoreError Whether ignore error tip.
     */
    updateAllData(ignoreError) {
      const params = {
        plugin_name: 'tensor',
        train_id: this.trainingJobId,
      };
      RequestService.getSingleTrainJob(params, ignoreError)
          .then((res) => {
            if (this.isReloading) {
              this.$store.commit('setIsReload', false);
              this.isReloading = false;
            }
            // Fault tolerance processing
            if (
              !res ||
            !res.data ||
            !res.data.train_jobs ||
            !res.data.train_jobs.length ||
            !res.data.train_jobs[0].tags
            ) {
              this.clearAllData();
              return;
            }
            const data = res.data.train_jobs[0];
            // Remove data that does not exist.
            const dataRemoveFlag = this.removeNoneExistentData(data);
            // Add new data.
            const dataAddFlag = this.checkNewDataAndComplete(data);
            this.$nextTick(() => {
              this.multiSelectedTagNames = this.$refs.multiselectGroupComponents.updateSelectedDic();
              this.updateTagInPage(!dataAddFlag && !dataRemoveFlag);
            });
          }, this.requestErrorCallback)
          .catch((e) => {
            this.$message.error(this.$t('public.dataError'));
          });
    },
    /**
     * Delete the data that does not exist
     * @param {Object} oriData Raw data with tags
     * @return {Boolean} Indicates whether data is removed.
     */
    removeNoneExistentData(oriData) {
      if (!oriData || !oriData.tags) {
        return false;
      }
      const newTagDictionaries = {};
      let dataRemoveFlag = false;
      // Obtains the current tag list
      oriData.tags.forEach((tagName) => {
        newTagDictionaries[tagName] = true;
      });
      // Delete data that do not exist in the operation bar
      const oldTagListLength = this.tagList.length;
      for (let i = oldTagListLength - 1; i >= 0; i--) {
        if (!newTagDictionaries[this.tagList[i].label]) {
          dataRemoveFlag = true;
          delete this.curFullTagDic[this.tagList[i].label];
          this.tagList.splice(i, 1);
        }
      }
      // Delete the data corresponding to the tag that does not exist.
      const oldSampleLength = this.originDataArr.length;
      for (let i = oldSampleLength - 1; i >= 0; i--) {
        if (!newTagDictionaries[this.originDataArr[i].tagName]) {
          dataRemoveFlag = true;
          this.originDataArr.splice(i, 1);
        }
      }
      return dataRemoveFlag;
    },
    /**
     * Check and add new data
     * @param {Object} oriData Raw data with tags
     * @return {Boolean} Check whether new data is added
     */
    checkNewDataAndComplete(oriData) {
      if (!oriData || !oriData.tags) {
        return false;
      }
      let dataAddFlag = false;
      oriData.tags.forEach((tagName) => {
        if (!this.curFullTagDic[tagName]) {
          this.tagList.push({
            label: tagName,
            checked: true,
            show: false,
          });
          this.originDataArr.push({
            tagName: tagName,
            summaryName: this.trainingJobId,
            show: false,
            showLoading: false,
            sliderValue: 0,
            newDataFlag: true,
            totalStepNum: 0,
            curStep: '',
            curTime: '',
            curDims: '',
            curDataType: '',
            fullScreen: false,
            ref: tagName,
            sliderChangeTimer: null,
            curData: [],
            formateData: [],
            fullData: [],
            filterStr: '',
            curMartixShowSliderValue: 0,
          });
          this.curFullTagDic[tagName] = true;
          dataAddFlag = true;
        }
      });
      return dataAddFlag;
    },
    /**
     * Expand/Collapse in full Screen
     * @param {Object} sampleItem The object that is being operated
     */
    toggleFullScreen(sampleItem) {
      if (!sampleItem) {
        return;
      }
      sampleItem.fullScreen = !sampleItem.fullScreen;
      this.$nextTick(() => {
        const elementItem = this.$refs[sampleItem.ref];
        if (elementItem) {
          elementItem[0].resizeView();
          elementItem[0].$el.scrollIntoView();
        }
      });
    },
    /**
     * Callback after the step slider changes
     * @param {Number} sliderValue Changed slider value
     * @param {Object} sampleItem The object that is being operated
     */
    sliderChange(sliderValue, sampleItem) {
      if (sampleItem.sliderChangeTimer) {
        clearTimeout(sampleItem.sliderChangeTimer);
        sampleItem.sliderChangeTimer = null;
      }
      if (!sampleItem.fullData || !sampleItem.fullData[sliderValue]) {
        return;
      }
      sampleItem.newDataFlag = true;
      sampleItem.formateData = sampleItem.fullData[sliderValue];
      sampleItem.curStep = sampleItem.formateData.step;
      sampleItem.curTime = this.dealrelativeTime(
          new Date(sampleItem.formateData.wall_time * 1000).toString(),
      );
      sampleItem.curDataType = sampleItem.formateData.value.data_type;
      sampleItem.curDims = JSON.stringify(sampleItem.formateData.value.dims);
      if (sampleItem.curMartixShowSliderValue === sliderValue) {
        return;
      }
      sampleItem.sliderChangeTimer = setTimeout(() => {
        sampleItem.showLoading = true;
        this.freshtMartixData(sampleItem);
      }, 500);
    },
    /**
     * Converts the original data formate to a histogram-recognizable formate
     * @param {Object} resData Original data
     * @return {Object} Formatted data
     */
    formHistogramOriData(resData) {
      const formateData = [];
      const histogramArr = resData.values || [];
      const wallTimeInit = histogramArr.length ? histogramArr[0].wall_time : 0;
      histogramArr.forEach((histogram, index) => {
        const step = histogram.step.toString();
        const chartItem = {
          wall_time: histogram.wall_time,
          relative_time: histogram.wall_time - wallTimeInit,
          step: step,
          items: [],
        };
        const chartArr = [];
        histogram.value.histogram_buckets.forEach((bucket) => {
          const xData = bucket[0] + bucket[1] / 2;
          const filter = chartArr.filter((k) => k[0] === xData);
          if (!filter.length) {
            chartArr.push([
              histogram.wall_time,
              step,
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
            [histogram.wall_time, step, minItem, 0],
          ].concat(chartArr, [[histogram.wall_time, step, maxItem, 0]]);
          chartItem.items = chartAll;
          formateData.push(chartItem);
        }
      });
      return formateData;
    },
    /**
     * Histogram display/hidden change of tip
     * @param {Boolean} value Show tip
     */
    chartTipFlagChange(value) {
      this.chartTipFlag = value;
    },
  },
};
</script>
<style lang="scss">
.cl-tensor-manage {
  height: 100%;
  .tensor-bk {
    height: 100%;
    background-color: #fff;
    display: flex;
    flex-direction: column;
    .cl-tensor-title {
      height: 56px;
      line-height: 56px;
      .path-message {
        display: inline-block;
        line-height: 20px;
        padding: 0px 4px 15px 4px;
        font-weight: bold;
        vertical-align: bottom;
      }
      .cl-close-btn {
        width: 20px;
        height: 20px;
        vertical-align: -3px;
        cursor: pointer;
        display: inline-block;
      }
    }
    .cl-tensor-operate-content {
      width: 100%;
      padding: 8px 32px 22px 32px;
      background: #ffffff;
    }
    .cl-tensor-view-type-select-content {
      background: #ffffff;
      padding: 0 32px 21px 32px;
      height: 58px;
      display: flex;
      align-items: center;
      border-bottom: 2px solid #e6ebf5;
      .view-title {
        font-size: 14px;
        line-height: 14px;
        vertical-align: middle;
        margin-right: 16px;
        flex-shrink: 0;
      }
      .el-radio-group {
        margin-right: 64px;
        flex-shrink: 0;
      }
    }
    .cl-show-data-content {
      background: #ffffff;
      padding: 0 23px;
      flex: 1;
      overflow: auto;
      .data-content {
        display: flex;
        height: 100%;
        width: 100%;
        flex-wrap: wrap;
        min-height: 400px;
        position: relative;
        .sample-content {
          width: 33.3%;
          height: 600px;
          display: flex;
          flex-direction: column;
          flex-shrink: 0;
          background-color: #fff;
          position: relative;
          padding: 32px 9px 0 9px;
        }
        .char-full-screen {
          width: 100%;
          height: 600px;
        }
        .chars-container {
          flex: 1;
          padding: 10px 15px 0 15px;
          position: relative;
          background: #f0f3fa;
          overflow-x: hidden;
          .loading-cover {
            width: 100%;
            height: 100%;
            z-index: 9;
            position: absolute;
            top: 0;
            left: 0;
            display: flex;
            background: white;
            opacity: 0.5;
            align-items: center;
            justify-content: center;
          }
        }
        .sample-data-show {
          padding: 32px 16px;
          text-overflow: ellipsis;
          white-space: nowrap;
          overflow: hidden;
          background-color: #f0f3fa;
          margin-top: 1px;
          .tensor-demension,
          .tensor-type {
            font-size: 14px;
            line-height: 20px;
            text-overflow: ellipsis;
            white-space: nowrap;
            overflow: hidden;
            span {
              color: #00a5a7;
            }
          }
          .sample-operate-info {
            width: 100%;
            min-height: 24px;
            vertical-align: middle;
            line-height: 20px;
            margin-top: 24px;
            color: #000000;
            position: relative;
            text-overflow: ellipsis;
            white-space: nowrap;
            overflow: hidden;
            span {
              max-width: 100%;
              text-overflow: ellipsis;
              white-space: nowrap;
              overflow: hidden;
            }
            .step-info {
              left: 0;
              font-size: 14px;
            }
            .time-info {
              right: 0;
              float: right;
              font-size: 14px;
            }
          }
          .step-slider {
            margin-top: 10px;
          }
        }
        .tag-title {
          margin-top: 10px;
          width: 100%;
          font-size: 16px;
          font-weight: 600;
          text-align: center;
        }
      }
    }
    .pagination-content {
      padding: 24px 32px;
      text-align: right;
    }
    // No data available.
    .image-noData {
      // Set the width and white on the right.
      width: 100%;
      height: 100%;
      display: flex;
      justify-content: center;
      align-items: center;
      flex-direction: column;
    }
  }
  .content {
    position: relative;
  }

  #echart {
    width: 500px;
    height: 500px;
    border: 1px solid black;
    position: relative;
  }

  #echartTip {
    position: absolute;
    padding: 5px;
    z-index: 9999;
    font-size: 14px;
    font-family: 'Microsoft YaHei';
    background-color: rgba(50, 50, 50, 0.7);
    border: 0;
    border-radius: 4px;
    color: #fff;
  }

  .char-tip-table td {
    padding-left: 5px;
    padding-right: 5px;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 150px;
    overflow: hidden;
  }

  .borderspacing3 {
    border-spacing: 3px;
  }
}
</style>

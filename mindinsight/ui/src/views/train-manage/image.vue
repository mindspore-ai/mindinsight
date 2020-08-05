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
  <div class="cl-image-manage">
    <div class="image-bk">
      <div class="cl-title cl-image-title">
        <div class="cl-title-left">{{$t('images.titleText')}}</div>
        <div class="cl-title-right">
          <div class="cl-close-btn"
               @click="jumpToTrainDashboard">
            <img src="@/assets/images/close-page.png">
          </div>
        </div>
      </div>
      <!-- Selecting an operation area -->
      <div class="cl-img-operate-content">
        <multiselectGroupComponents ref="multiselectGroupComponents"
                             :checkListArr="tagOperateList"
                             @selectedChange="tagSelectedChanged"></multiselectGroupComponents>
      </div>
      <!-- Sliding block area -->
      <div class="cl-img-slider-operate-content">
        <span class="setBright-text">{{$t('images.setBright')}}</span>
        <span class="slider-content">
          <el-slider v-model="brightness"></el-slider>
        </span>
        <el-button class="reset-btn"
                   size="small"
                   @click="brightness = 50"
                   :disabled="brightness===50"
                   :class="brightness===50?'button-disable':'' ">{{$t('public.reset')}}</el-button>
        <span class="setContrast-text">{{$t('images.setContrast')}}</span>
        <span class="slider-content">
          <el-slider v-model="contrast"></el-slider>
        </span>
        <el-button class="reset-btn"
                   size="small"
                   @click="contrast = 50"
                   :disabled="contrast===50"
                   :class="contrast===50?'button-disable':'' ">{{$t('public.reset')}}</el-button>
      </div>
      <!-- Content display area -->
      <div class="cl-img-show-data-content">
        <!-- No data is displayed. -->
        <div class="image-noData"
             v-if="!originDataArr.length">
          <div>
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
          </div>
          <div v-if="initOver"
               class="noData-text">{{$t("public.noData")}}</div>
          <div v-else
               class="noData-text">{{$t("public.dataLoading")}}</div>
        </div>
        <!-- Data is displayed -->
        <div class="data-content"
             v-if="originDataArr.length">
          <div class="sample-content"
               :class="sampleItem.fullScreen ? 'content-full-screen': 'content-common'"
               v-for="(sampleItem,sampleIndex) in originDataArr"
               :key="sampleIndex"
               v-show="sampleItem.curPageShow">
            <!-- Image container -->
            <div class="image-container"
                 @click="sampleToggleFullScreen($event, sampleItem)">
              <!-- Image -->
              <img class="sample-img select-disable"
                   :src='sampleItem.curImgUrl'
                   :width='sampleItem.fullScreen ? sampleItem.curImageSize[0] : "100%"'
                   :height='sampleItem.fullScreen ? sampleItem.curImageSize[1] : "359px"'
                   :style='{filter:`brightness(${brightness/50}) contrast(${contrast/50})`,
                          "-webkit-filter": `brightness(${brightness/50}) contrast(${contrast/50})`}'>
            </div>
            <!-- Information display area -->
            <div class="sample-data-show">
              <div class="tag-title"
                   :title="sampleItem.tagName">{{sampleItem.tagName}}</div>
              <div class="summary-title"
                   :title="sampleItem.summaryName">{{sampleItem.summaryName}}</div>
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
                         :max='sampleItem.totalStepNum'
                         @input='sliderChange(sampleItem.sliderValue,sampleItem)'
                         :show-tooltip='false'
                         :disabled="sampleItem.totalStepNum===0">
              </el-slider>
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
import multiselectGroupComponents from '../../components/multiselectGroup.vue';
import RequestService from '../../services/request-service';
import {basePath} from '@/services/fetcher';
export default {
  data() {
    return {
      initOver: false, // Indicates whether the initialization is complete.
      autoUpdateTimer: null, // Automatic refresh timer
      brightness: 50, // Brightness
      contrast: 50, // Contrast
      trainingJobId: this.$route.query.train_id, // ID of the current training job
      multiSelectedTagNames: {}, // Dictionary for storing the name of the selected tags
      curFilterSamples: [], // List of images that meet the current filter criteria
      tagOperateList: [], // Tag list
      originDataArr: [], // List of all image data.
      oriDataDictionaries: {}, // Dictionary that contains all the current tags.
      curPageArr: [], // Image data list on the current page
      pageIndex: 0, // Current page number
      pageSizes: [8, 16, 24], // The number of records on each page is optional
      pageNum: 8, // Number of records on each page
      isReloading: false, // Manually refresh
      imageBasePath: '/v1/mindinsight/datavisual/image/single-image?', // Relative path header of the picture
    };
  },
  computed: {
    /**
     * Global refresh switch
     * @return {Boolean}
     */
    isReload() {
      return this.$store.state.isReload;
    },
    /**
     * Automatic refresh switch
     * @return {Boolean}
     */
    isTimeReload() {
      return this.$store.state.isTimeReload;
    },
    /**
     * Automatic refresh value
     * @return {Boolean}
     */
    timeReloadValue() {
      return this.$store.state.timeReloadValue;
    },
  },
  watch: {
    /**
     * Global refresh switch Listener
     * @param {Boolean} newVal Value After Change
     * @param {Boolean} oldVal Value Before Change
     */
    isReload(newVal, oldVal) {
      if (newVal) {
        this.isReloading = true;
        // Automatic refresh and retiming
        if (this.isTimeReload) {
          this.autoUpdateSamples();
        }
        this.updateAllData(false);
      }
    },
    /**
     * Automatic refresh switch Listener
     * @param {Boolean} newVal Value After Change
     * @param {Boolean} oldVal Value Before Change
     */
    isTimeReload(newVal, oldVal) {
      if (newVal) {
        // Enable automatic refresh
        this.autoUpdateSamples();
      } else {
        // Disable automatic refresh
        this.stopUpdateSamples();
      }
    },
    /**
     * The refresh time is changed.
     */
    timeReloadValue() {
      this.autoUpdateSamples();
    },
  },
  destroyed() {
    // Disable the automatic refresh function
    if (this.autoUpdateTimer) {
      clearInterval(this.autoUpdateTimer);
      this.autoUpdateTimer = null;
    }
    // Stop Refreshing
    if (this.isReloading) {
      this.$store.commit('setIsReload', false);
      this.isReloading = false;
    }
  },
  mounted() {
    if (!this.$route.query || !this.$route.query.train_id) {
      this.$message.error(this.$t('trainingDashboard.invalidId'));
      document.title = this.$t('images.titleText') + '-MindInsight';
      return;
    }
    document.title = decodeURIComponent(this.$route.query.train_id) +'-' + this.$t('images.titleText') +
      '-MindInsight';
    this.getTagList();
    // Automatic refresh
    if (this.isTimeReload) {
      this.autoUpdateSamples();
    }
  },

  methods: {
    /**
     * Initialize the training log and tag list
     */
    getTagList() {
      const params = {
        plugin_name: 'image',
        train_id: this.trainingJobId,
      };
      RequestService.getSingleTrainJob(params, false)
          .then((res) => {
            if (!res || !res.data || !res.data.train_jobs) {
              this.initOver = true;
              return;
            }
            const data = res.data.train_jobs[0];
            if (!data.tags) {
              return;
            }
            const tempTagList = [];
            const dataList = [];
            data.tags.forEach((tagName) => {
              if (!this.oriDataDictionaries[tagName]) {
                this.oriDataDictionaries[tagName] = true;
                tempTagList.push({
                  label: tagName,
                  checked: true,
                  show: true,
                });
                dataList.push({
                  summaryId: data.id,
                  summaryName: data.name,
                  tagName: tagName,
                  sampleData: [],
                  curPageShow: false,
                  sliderValue: 0,
                  fullScreen: false,
                  totalStepNum: 0,
                  curStep: '',
                  curImgUrl: '',
                  curTime: '',
                  curImageSize: [0, 0],
                });
              }
            });
            // Initialize the assignment tag list, and image list
            this.tagOperateList = tempTagList;
            this.originDataArr = dataList;
            this.initOver = true;

            this.$nextTick(() => {
              this.multiSelectedTagNames = this.$refs.multiselectGroupComponents.updateSelectedDic();
              // Obtains data on the current page
              this.updateTagInPage();
            });
          }, this.requestErrorCallback)
          .catch((e) => {
            this.$message.error(this.$t('public.dataError'));
          });
    },
    /**
     * Obtains data on the current page
     * @param {Boolean} noPageDataNumChange No new data is added or deleted
     */
    getCurPageDataArr(noPageDataNumChange) {
      // Clear the previous page
      if (!noPageDataNumChange) {
        this.curPageArr.forEach((sampleItem) => {
          sampleItem.curPageShow = false;
        });
      }
      // This interface is used to obtain the current page group and hide the current page group.
      const startIndex = this.pageIndex * this.pageNum;
      const endIndex = startIndex + this.pageNum;
      const curPageArr = [];
      for (let i = startIndex; i < endIndex; i++) {
        const sampleItem = this.curFilterSamples[i];
        if (sampleItem) {
          sampleItem.curPageShow = true;
          curPageArr.push(sampleItem);
        }
      }
      this.curPageArr = curPageArr;
      // Update the image information on the current page
      this.updateCurPageSamples();
    },
    /**
     * Update the image information on the current page
     */
    updateCurPageSamples() {
      this.curPageArr.forEach((sampleItem) => {
        const params = {
          train_id: sampleItem.summaryId,
          tag: sampleItem.tagName,
        };
        RequestService.getImageMetadatas(params)
            .then(
                (res) => {
                  if (!res || !res.data || !res.data.metadatas) {
                    return;
                  }
                  // Processes image data
                  const tempData = res.data.metadatas;
                  sampleItem.sampleData = tempData;
                  const oldTotalStepNum = sampleItem.totalStepNum;
                  if (tempData.length) {
                    sampleItem.totalStepNum = tempData.length - 1;
                  } else {
                    sampleItem.totalStepNum = 0;
                    sampleItem.sliderValue = 0;
                    sampleItem.curStep = '';
                    sampleItem.curImgUrl = '';
                    sampleItem.curTime = '';
                    return;
                  }
                  if (sampleItem.sliderValue === oldTotalStepNum) {
                    sampleItem.sliderValue = sampleItem.totalStepNum;
                  }
                  if (sampleItem.sliderValue > sampleItem.totalStepNum) {
                    sampleItem.sliderValue = sampleItem.totalStepNum;
                  }
                  const curSampleData =
                sampleItem.sampleData[sampleItem.sliderValue];
                  // Initialize the current step information
                  if (curSampleData) {
                    sampleItem.curStep = curSampleData.step;
                    sampleItem.curImgUrl =
                  `${basePath}${this.imageBasePath}train_id=${sampleItem.summaryId}` +
                  `&tag=${sampleItem.tagName}&step=${curSampleData.step}&wt=${curSampleData.wall_time}`;
                    sampleItem.curTime = this.dealrelativeTime(new Date(
                        curSampleData.wall_time * 1000,
                    ).toString());
                    sampleItem.curImageSize = [
                      curSampleData.width,
                      curSampleData.height,
                    ];
                  }
                  this.$forceUpdate();
                },
                (e) => {
                  sampleItem.totalStepNum = 0;
                  sampleItem.sliderValue = 0;
                  sampleItem.curStep = '';
                  sampleItem.curImgUrl = '';
                  sampleItem.curTime = '';
                },
            )
            .catch((e) => {});
      });
    },
    /**
     * Image step value change event
     * @param {Number} sliderValue Current slider value
     * @param {Object} sampleItem Current picture object.
     */
    sliderChange(sliderValue, sampleItem) {
      if (
        (!sliderValue && sliderValue !== 0) ||
        !sampleItem ||
        !sampleItem.sampleData ||
        !sampleItem.sampleData[sliderValue]
      ) {
        return;
      }
      const curStepData = sampleItem.sampleData[sliderValue];
      sampleItem.curStep = curStepData.step;
      sampleItem.curImgUrl =
        `${basePath}${this.imageBasePath}train_id=${sampleItem.summaryId}` +
        `&tag=${sampleItem.tagName}&step=${curStepData.step}&wt=${curStepData.wall_time}`;
      sampleItem.curTime = this.dealrelativeTime(new Date(
          curStepData.wall_time * 1000,
      ).toString());
      sampleItem.curImageSize = [curStepData.width, curStepData.height];
    },
    /**
     * Image click event
     * @param {Object} event Native event event
     * @param {Object} sampleItem Current picture data object.
     */
    sampleToggleFullScreen(event, sampleItem) {
      if (!event || !sampleItem) {
        return;
      }
      event.stopPropagation();
      event.preventDefault();
      sampleItem.fullScreen = !sampleItem.fullScreen;
      this.$forceUpdate();
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
     * The selected label is changed
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
     * Update the image list based on the filtered tags
     * @param {Boolean} noPageDataNumChange No new data is added or deleted
     */
    updateTagInPage(noPageDataNumChange) {
      const curFilterSamples = [];
      // Obtains the image data subscript that meets the tag filtering conditions
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
     * Clear data.
     */
    clearAllData() {
      this.multiSelectedTagNames = {};
      this.curFilterSamples = [];
      this.tagOperateList = [];
      this.originDataArr = [];
      this.oriDataDictionaries = {};
      this.curPageArr = [];
      this.pageIndex = 0;
    },
    /**
     * Request error handling
     * @param {Object} error Error Object
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
          // Clear Display Data
          this.clearAllData();
        }
      }
    },

    /**
     * Delete the data that does not exist
     * @param {Object} oriData Raw data with training logs and tags
     * @return {Boolean} Indicates whether image data is removed.
     */
    removeNonexistentData(oriData) {
      if (!oriData) {
        return false;
      }
      const newTagDictionaries = {}; // Index of the tag in the new data
      let dataRemoveFlag = false;
      // Obtains the current tag list
      oriData.tags.forEach((tagName) => {
        newTagDictionaries[tagName] = true;
      });
      // Delete the tags that do not exist in the operation bar
      const oldTagListLength = this.tagOperateList.length;
      for (let i = oldTagListLength - 1; i >= 0; i--) {
        if (!newTagDictionaries[this.tagOperateList[i].label]) {
          dataRemoveFlag = true;
          delete this.oriDataDictionaries[this.tagOperateList[i].label];
          this.tagOperateList.splice(i, 1);
        }
      }
      // Delete the old data from the image list and update the dictionary
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
     * @param {Object} oriData Raw data with training logs and tags
     * @return {Boolean} Check whether new image data is added
     */
    checkNewDataAndComplete(oriData) {
      if (!oriData) {
        return false;
      }
      // Add New Data
      let dataAddFlag = false;
      oriData.tags.forEach((tagName) => {
        if (!this.oriDataDictionaries[tagName]) {
          this.oriDataDictionaries[tagName] = true;
          this.tagOperateList.push({
            label: tagName,
            checked: true,
            show: false,
          });
          this.originDataArr.push({
            summaryId: oriData.id,
            summaryName: oriData.name,
            tagName: tagName,
            sampleData: [],
            curPageShow: false,
            sliderValue: 0,
            fullScreen: false,
            totalStepNum: 0,
            curStep: '',
            curImgUrl: '',
            curTime: '',
            curImageSize: [0, 0],
          });
          dataAddFlag = true;
        }
      });
      return dataAddFlag;
    },
    /**
     * Update all data.
     * @param {Boolean} ignoreError whether ignore error tip
     */
    updateAllData(ignoreError) {
      const params = {
        plugin_name: 'image',
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
            const oriData = res.data.train_jobs[0];
            // Delete the data that does not exist.
            const dataRemoveFlag = this.removeNonexistentData(oriData);
            // Check whether new data exists and add it
            const dataAddFlag = this.checkNewDataAndComplete(oriData);
            this.$nextTick(() => {
              this.multiSelectedTagNames = this.$refs.multiselectGroupComponents.updateSelectedDic();
              this.updateTagInPage(!dataRemoveFlag && !dataAddFlag);
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
    // jump back to train dashboard
    jumpToTrainDashboard() {
      this.$router.push({
        path: '/train-manage/training-dashboard',
        query: {
          id: this.trainingJobId,
        },
      });
    },
    /**
     * Format Absolute Time
     * @param {String} time string
     * @return {string} str
     */

    dealrelativeTime(time) {
      const arr = time.split(' ');
      const str = arr[0] + ' ' + arr[1] + ' ' + arr[2] + ',' + ' ' + arr[4];
      return str;
    },
  },
  components: {
    multiselectGroupComponents,
  },
};
</script>
<style lang="scss" scoped>
.cl-image-manage {
  height: 100%;
  .image-bk {
    height: 100%;
    background-color: #fff;
    display: flex;
    flex-direction: column;

    .cl-image-title {
      height: 56px;
      line-height: 56px;
    }
  }
  .title {
    font-size: 14px;
    vertical-align: middle;
    flex-shrink: 0;
  }
  .select-all {
    cursor: pointer;
    flex-shrink: 0;
  }
  .cl-img-operate-content {
    width: 100%;
    padding: 8px 32px 22px 32px;
    background: #ffffff;
  }
  .cl-img-slider-operate-content {
    background: #ffffff;
    padding: 0 32px 22px 32px;
    display: flex;
    align-items: center;
    border-bottom: 2px solid #e6ebf5;
    .button-disable {
      color: rgb(128, 210, 211) !important;
      border: 1px solid rgb(128, 210, 211) !important;
    }
    .setBright-text,
    .setContrast-text {
      font-size: 14px;
      line-height: 14px;
      color: #282b33;
      margin-right: 14px;
    }
    .setContrast-text {
      margin-left: 48px;
    }
    .slider-content {
      width: 403px;
      margin-right: 19px;
    }
    .reset-btn {
      width: 96px;
      border-radius: 2px;
      color: #00a5a7;
      border: 1px solid #00a5a7;
      font-size: 14px;
      line-height: 20px;
      padding-top: 4px;
      padding-bottom: 5px;
    }
  }
  .cl-img-show-data-content {
    background: #ffffff;
    padding: 0 23px;
    flex: 1;
    overflow: auto;
    .data-content {
      display: flex;
      width: 100%;
      flex-wrap: wrap;
      min-height: 470px;
      .content-common {
        width: calc(25% - 18px);
        max-width: 500px;
      }
      .content-full-screen {
        max-width: 100%;
      }
      .sample-content {
        min-width: 250px;
        min-height: 359px;
        margin-right: 9px;
        margin-left: 9px;
        margin-top: 32px;
        display: flex;
        flex-direction: column;
        flex-shrink: 0;
        .image-container {
          position: relative;
          cursor: pointer;
          width: 100%;
          min-height: 359px;
          overflow-x: auto;
          .sample-img {
            object-fit: contain;
            background: #f0f3fa;
          }
        }
        .sample-data-show {
          padding: 32px 16px;
          text-overflow: ellipsis;
          white-space: nowrap;
          overflow: hidden;
          background-color: #f0f3fa;
          .tag-title,
          .summary-title {
            font-size: 14px;
            line-height: 20px;
            text-overflow: ellipsis;
            white-space: nowrap;
            overflow: hidden;
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
      }
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
  .pagination-content {
    padding: 24px 32px;
    text-align: right;
  }
  .mr24 {
    margin-right: 24px;
  }
  .select-disable {
    -moz-user-select: none; /*Firefox*/
    -webkit-user-select: none; /*webkitbrowser*/
    -ms-user-select: none; /*IE10*/
    -khtml-user-select: none; /*Early browser*/
    user-select: none;
  }
  .el-slider__bar {
    background-color: #6c92fa;
  }
  .el-slider__button {
    border-color: #6c92fa;
  }
  .noData-text {
    margin-top: 33px;
    font-size: 18px;
  }

  .tooltip-show-content {
    max-width: 50%;
  }
  // Pagination selected
  .el-pager li.active {
    background: #00a5a7;
    color: #ffffff;
  }
  // Arrow on the previous or next page
  .el-pagination .btn-prev,
  .el-pagination .btn-next {
    background: #e6ebf5;
    .el-icon {
      color: #b8becc;
    }
  }
  .search-input-item {
    width: 261px;
  }
  .cl-close-btn {
    width: 20px;
    height: 20px;
    vertical-align: -3px;
    cursor: pointer;
    display: inline-block;
  }
}
</style>

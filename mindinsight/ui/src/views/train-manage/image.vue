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
  <div class="cl-image-manage">
    <div class="image-bk">
      <div class="cl-title cl-image-title">
        <div class="cl-title-left">{{$t('images.titleText')}}
          <el-tooltip placement="right-start"
                      effect="light">
            <div slot="content"
                 class="tooltip-container">
              <div class="cl-title-tip">
                <div class="tip-part">
                  {{$t('images.titleTip')}}
                </div>
              </div>
            </div>
            <i class="el-icon-info"></i>
          </el-tooltip>
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
              <div v-if="sampleItem.showErrMsg"
                   class="error-message-container select-disable"
                   :style='{width:sampleItem.fullScreen ? sampleItem.curImageSize[0]+"px" : "100%",
                          height: sampleItem.fullScreen ? sampleItem.curImageSize[1]+"px" : "356px"}'>
                <div>{{sampleItem.errMsg}}</div>
              </div>
              <!-- Image -->
              <img class="sample-img select-disable"
                   v-else
                   :src='sampleItem.curImgUrl'
                   :width='sampleItem.fullScreen ? sampleItem.curImageSize[0] : "100%"'
                   :height='sampleItem.fullScreen ? sampleItem.curImageSize[1] : "356px"'
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
import multiselectGroupComponents from '../../components/multiselect-group.vue';
import RequestService from '../../services/request-service';
import { basePath, transCode } from '@/services/fetcher';
import autoUpdate from '../../mixins/auto-update.vue';
export default {
  mixins: [autoUpdate],
  data() {
    return {
      initOver: false, // Indicates whether the initialization is complete.
      brightness: 50, // Brightness
      contrast: 50, // Contrast
      trainingJobId: this.$route.query.train_id, // ID of the current training job
      summaryPath: this.$route.query.summaryPath,
      multiSelectedTagNames: {}, // Dictionary for storing the name of the selected tags
      curFilterSamples: [], // List of images that meet the current filter criteria
      tagOperateList: [], // Tag list
      originDataArr: [], // List of all image data.
      oriDataDictionaries: {}, // Dictionary that contains all the current tags.
      curPageArr: [], // Image data list on the current page
      pageIndex: 0, // Current page number
      pageSizes: [8, 16, 24], // The number of records on each page is optional
      pageNum: 8, // Number of records on each page
      imageBasePath: 'v1/mindinsight/datavisual/image/single-image?', // Relative path header of the picture
    };
  },
  computed: {},
  watch: {},
  destroyed() {},
  mounted() {
    if (!this.$route.query || !this.$route.query.train_id) {
      this.$message.error(this.$t('trainingDashboard.invalidId'));
      document.title = this.$t('images.titleText') + '-MindInsight';
      return;
    }
    document.title = this.$route.query.train_id + '-' + this.$t('images.titleText') + '-MindInsight';
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
                showErrMsg: false,
                errMsg: '',
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
              const curSampleData = sampleItem.sampleData[sampleItem.sliderValue];
              // Initialize the current step information
              if (curSampleData) {
                sampleItem.curStep = curSampleData.step;
                const params = {
                  train_id: sampleItem.summaryId,
                  tag: sampleItem.tagName,
                  step: curSampleData.step,
                  wt: curSampleData.wall_time,
                };
                this.getImageData(params, sampleItem);
                sampleItem.curTime = this.dealrelativeTime(new Date(curSampleData.wall_time * 1000).toString());
                sampleItem.curImageSize = [curSampleData.width, curSampleData.height];
              }
              this.$forceUpdate();
            },
            (e) => {
              sampleItem.totalStepNum = 0;
              sampleItem.sliderValue = 0;
              sampleItem.curStep = '';
              sampleItem.curImgUrl = '';
              sampleItem.curTime = '';
            }
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
      const params = {
        train_id: sampleItem.summaryId,
        tag: sampleItem.tagName,
        step: curStepData.step,
        wt: curStepData.wall_time,
      };
      this.getImageData(params, sampleItem);
      sampleItem.curTime = this.dealrelativeTime(new Date(curStepData.wall_time * 1000).toString());
      sampleItem.curImageSize = [curStepData.width, curStepData.height];
    },
    /**
     * Get image data
     * @param {Object} params Current params
     * @param {Object} sampleItem Current picture object.
     */
    getImageData(params, sampleItem) {
      RequestService.getImageData(params).then(
        (res) => {
          sampleItem.showErrMsg = false;
          sampleItem.curImgUrl =
            `${basePath}${this.imageBasePath}train_id=${transCode(sampleItem.summaryId)}` +
            `&tag=${transCode(sampleItem.tagName)}&step=${params.step}&wt=${params.wt}`;
        },
        (e) => {
          if (e.response && e.response.data && e.response.data.error_code) {
            sampleItem.curImgUrl = '';
            sampleItem.showErrMsg = true;
            if (e.response.data.error_code === '5054500D') {
              sampleItem.errMsg = this.$t('images.imageErrorTip');
            } else {
              sampleItem.errMsg = this.$t('error')[e.response.data.error_code];
            }
          }
        }
      );
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
        if (!(error.code === 'ECONNABORTED' && /^timeout/.test(error.message))) {
          // Clear display Data
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
            showErrMsg: false,
            errMsg: '',
          });
          dataAddFlag = true;
        }
      });
      return dataAddFlag;
    },
    /**
     * Update all data.
     * @param {Boolean} ignoreError Whether ignore error tip
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
    // Jump back to train dashboard
    jumpToTrainDashboard() {
      this.$router.push({
        path: '/train-manage/training-dashboard',
        query: {
          id: this.trainingJobId,
        },
      });
    },
    /**
     * Format absolute Time
     * @param {String} time String
     * @return {string}
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
<style scoped>
.cl-image-manage {
  height: 100%;
}
.cl-image-manage .image-bk {
  height: 100%;
  background-color: var(--bg-color);
  display: flex;
  flex-direction: column;
}
.cl-image-manage .image-bk .cl-image-title {
  height: 56px;
  line-height: 56px;
}
.cl-image-manage .image-bk .cl-image-title .path-message {
  display: inline-block;
  line-height: 20px;
  padding: 0px 4px 15px 4px;
  font-weight: bold;
  vertical-align: bottom;
}
.cl-image-manage .image-bk .cl-image-title .cl-title-tip {
  padding: 10px;
}
.cl-image-manage .image-bk .cl-image-title .cl-title-tip .tip-part {
  line-height: 20px;
  word-break: normal;
}
.cl-image-manage .image-bk .cl-image-title .el-icon-info {
  color: #6c7280;
}
.cl-image-manage .title {
  font-size: 14px;
  vertical-align: middle;
  flex-shrink: 0;
}
.cl-image-manage .select-all {
  cursor: pointer;
  flex-shrink: 0;
}
.cl-image-manage .cl-img-operate-content {
  width: 100%;
  padding: 8px 32px 22px 32px;
  background: var(--bg-color);
}
.cl-image-manage .cl-img-slider-operate-content {
  background: var(--bg-color);
  padding: 0 32px 22px 32px;
  display: flex;
  align-items: center;
  border-bottom: 2px solid var(--item-split-line-color);
}
.cl-image-manage .cl-img-slider-operate-content .button-disable {
  color: #80d2d3 !important;
  background-color: var(--button-disabled-bg-color);
  border: 1px solid var(--table-border-color) !important;
}
.cl-image-manage .cl-img-slider-operate-content .button-disable:hover {
  background-color: var(--button-disabled-bg-color);
}
.cl-image-manage .cl-img-slider-operate-content .setBright-text,
.cl-image-manage .cl-img-slider-operate-content .setContrast-text {
  font-size: 14px;
  line-height: 14px;
  color: var(--font-color);
  margin-right: 14px;
}
.cl-image-manage .cl-img-slider-operate-content .setContrast-text {
  margin-left: 48px;
}
.cl-image-manage .cl-img-slider-operate-content .slider-content {
  width: 403px;
  margin-right: 19px;
}
.cl-image-manage .cl-img-slider-operate-content .reset-btn {
  width: 96px;
  border-radius: 2px;
  background-color: var(--bg-color);
  color: var(--theme-color);
  border: 1px solid var(--theme-color);
  font-size: 14px;
  line-height: 20px;
  padding-top: 4px;
  padding-bottom: 5px;
}
.cl-image-manage .cl-img-slider-operate-content .reset-btn:hover {
  background-color: var(--button-hover-color);
}
.cl-image-manage .cl-img-show-data-content {
  background: var(--bg-color);
  padding: 0 23px;
  flex: 1;
  overflow: auto;
}
.cl-image-manage .cl-img-show-data-content .data-content {
  display: flex;
  width: 100%;
  flex-wrap: wrap;
  min-height: 470px;
}
.cl-image-manage .cl-img-show-data-content .data-content .content-common {
  width: calc(25% - 18px);
  max-width: 500px;
}
.cl-image-manage .cl-img-show-data-content .data-content .content-full-screen {
  max-width: 100%;
}
.cl-image-manage .cl-img-show-data-content .data-content .sample-content {
  min-width: 250px;
  min-height: 359px;
  margin-right: 9px;
  margin-left: 9px;
  margin-top: 32px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.cl-image-manage .cl-img-show-data-content .data-content .sample-content .image-container {
  position: relative;
  cursor: pointer;
  width: 100%;
  min-height: 359px;
  overflow-x: auto;
}
.cl-image-manage .cl-img-show-data-content .data-content .sample-content .image-container .sample-img {
  object-fit: contain;
  background: var(--image-sample-bg-color);
}
.cl-image-manage .cl-img-show-data-content .data-content .sample-content .image-container .error-message-container {
  height: 100%;
  display: flex;
  background-color: var(--image-sample-bg-color);
}
.cl-image-manage
  .cl-img-show-data-content
  .data-content
  .sample-content
  .image-container
  .error-message-container
  div {
  margin: auto;
}
.cl-image-manage .cl-img-show-data-content .data-content .sample-content .sample-data-show {
  padding: 32px 16px;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
  background-color: var(--image-sample-bg-color);
  margin-top: 3px;
}
.cl-image-manage .cl-img-show-data-content .data-content .sample-content .sample-data-show .tag-title,
.cl-image-manage .cl-img-show-data-content .data-content .sample-content .sample-data-show .summary-title {
  font-size: 14px;
  line-height: 20px;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
}
.cl-image-manage .cl-img-show-data-content .data-content .sample-content .sample-data-show .sample-operate-info {
  width: 100%;
  min-height: 24px;
  vertical-align: middle;
  line-height: 20px;
  margin-top: 24px;
  color: var(--font-color);
  position: relative;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
}
.cl-image-manage .cl-img-show-data-content .data-content .sample-content .sample-data-show .sample-operate-info span {
  max-width: 100%;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
}
.cl-image-manage
  .cl-img-show-data-content
  .data-content
  .sample-content
  .sample-data-show
  .sample-operate-info
  .step-info {
  left: 0;
  font-size: 14px;
}
.cl-image-manage
  .cl-img-show-data-content
  .data-content
  .sample-content
  .sample-data-show
  .sample-operate-info
  .time-info {
  right: 0;
  float: right;
  font-size: 14px;
}
.cl-image-manage .cl-img-show-data-content .data-content .sample-content .sample-data-show .step-slider {
  margin-top: 10px;
}
.cl-image-manage .cl-img-show-data-content .data-content .sample-content ::-webkit-scrollbar-button {
  z-index: 200;
  width: 10px;
  height: 10px;
  background: #fff;
  cursor: pointer;
}
.cl-image-manage
  .cl-img-show-data-content
  .data-content
  .sample-content
  ::-webkit-scrollbar-button:horizontal:single-button:start {
  background-image: url('../../assets/images/scroll-btn-left.png');
  background-position: center;
}
.cl-image-manage
  .cl-img-show-data-content
  .data-content
  .sample-content
  ::-webkit-scrollbar-button:horizontal:single-button:end {
  background-image: url('../../assets/images/scroll-btn-right.png');
  background-position: center;
}
.cl-image-manage
  .cl-img-show-data-content
  .data-content
  .sample-content
  ::-webkit-scrollbar-button:vertical:single-button:start {
  background-image: url('../../assets/images/scroll-btn-up.png');
  background-position: center;
}
.cl-image-manage
  .cl-img-show-data-content
  .data-content
  .sample-content
  ::-webkit-scrollbar-button:vertical:single-button:end {
  background-image: url('../../assets/images/scroll-btn-down.png');
  background-position: center;
}
.cl-image-manage .cl-img-show-data-content .data-content .sample-content ::-webkit-scrollbar-thumb {
  background-color: #bac5cc;
}
.cl-image-manage .cl-img-show-data-content .data-content .sample-content ::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}
.cl-image-manage .cl-img-show-data-content .image-noData {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}
.cl-image-manage .pagination-content {
  padding: 24px 32px;
  text-align: right;
}
.cl-image-manage .mr24 {
  margin-right: 24px;
}
.cl-image-manage .select-disable {
  -moz-user-select: none;
  /*Firefox*/
  -webkit-user-select: none;
  /*webkitbrowser*/
  -ms-user-select: none;
  /*IE10*/
  -khtml-user-select: none;
  /*Early browser*/
  user-select: none;
}
.cl-image-manage .el-slider__bar {
  background-color: #6c92fa;
}
.cl-image-manage .el-slider__button {
  border-color: #6c92fa;
}
.cl-image-manage .noData-text {
  margin-top: 33px;
  font-size: 18px;
}
.cl-image-manage .tooltip-show-content {
  max-width: 50%;
}
.cl-image-manage .el-pager li.active {
  background: #00a5a7;
  color: #ffffff;
}
.cl-image-manage .el-pagination .btn-prev,
.cl-image-manage .el-pagination .btn-next {
  background: #e6ebf5;
}
.cl-image-manage .el-pagination .btn-prev .el-icon,
.cl-image-manage .el-pagination .btn-next .el-icon {
  color: #b8becc;
}
.cl-image-manage .search-input-item {
  width: 290px;
}
.cl-image-manage .cl-close-btn {
  width: 20px;
  height: 20px;
  vertical-align: -3px;
  cursor: pointer;
  display: inline-block;
}
</style>

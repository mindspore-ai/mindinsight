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
        <!-- Select tag -->
        <div class="tag-select-content">
          <div class="title mr24">{{$t("images.tagSelectTitle")}}</div>
          <!-- Select All -->
          <div class="select-all mr24"
               @click="tagSelectAll">
            <span class="multiCheckBox-border multi-check-border"
                  :class="tagOperateSelectAll ? 'checkbox-checked' : 'checkbox-unchecked'"></span>
            <span class="label-item select-disable">{{$t('images.selectAll')}}</span>
          </div>
          <!-- Tag search box -->
          <el-input class="search-input-item"
                    v-model="tagInput"
                    @input="filterByTagName"
                    v-if="headTagFullScreen"
                    :placeholder="$t('public.tagFilterPlaceHolder')"></el-input>
          <!-- Tag List -->
          <div class="select-item-content"
               v-if="!headTagFullScreen"
               ref="tagSelectItemContent">
            <div class="select-item"
                 v-for="(tagItem, tagIndex) in tagOperateList"
                 :key="tagIndex"
                 @click="tagItemClick(tagItem)"
                 v-show="tagItem.show">
              <span class="multiCheckBox-border multi-check-border"
                    :class="tagItem.checked ? 'checkbox-checked' : 'checkbox-unchecked'"></span>
              <span class="label-item">
                <el-tooltip effect="dark"
                            popper-class="tooltip-show-content"
                            :content="tagItem.label"
                            placement="top">
                  <span class="select-disable">{{tagItem.label}}</span>
                </el-tooltip>
              </span>
            </div>
          </div>
          <!-- Tag expansion/collapse button -->
          <div class="run-select-content-open select-disable"
               @click="toggleHeadTagFullScreen"
               v-if="tagOverRowFlag || tagInput"
               v-show="!headTagFullScreen">{{$t("images.open")}}</div>
          <div class="run-select-content-open select-disable"
               @click="toggleHeadTagFullScreen"
               v-if="tagOverRowFlag || headTagFullScreen"
               v-show="headTagFullScreen">{{$t("images.close")}}</div>
        </div>
        <div class="run-select-content-all"
             v-if="headTagFullScreen">
          <div class="select-item"
               v-for="(tagItem, tagIndex) in tagOperateList"
               :key="tagIndex"
               @click="tagItemClick(tagItem)"
               v-show="tagItem.show">
            <span class="multiCheckBox-border multi-check-border"
                  :class="tagItem.checked ? 'checkbox-checked' : 'checkbox-unchecked'"></span>
            <span class="label-item">
              <el-tooltip effect="dark"
                          popper-class="tooltip-show-content"
                          :content="tagItem.label"
                          placement="top">
                <span class="select-disable">{{tagItem.label}}</span>
              </el-tooltip>
            </span>
          </div>
        </div>
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
      <div class="cl-img-show-data-content"
           ref="miDataShoeContent">
        <!-- No data is displayed. -->
        <div class="image-noData"
             v-if="initOver && originDataArr.length === 0">
          <div>
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
          </div>
          <div class="noData-text">{{$t("public.noData")}}</div>
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
              <div class="run-title"
                   :title="sampleItem.runName">{{sampleItem.runName}}</div>
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
        <el-pagination @size-change="pageSizeChange"
                       @current-change="currentPageChange"
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
import RequestService from '../../services/request-service';
import {basePath} from '@/services/fetcher';
export default {
  data() {
    return {
      initOver: false, // Indicates whether the initialization is complete.
      autoUpdateTimer: null, // Automatic refresh timer
      tagInput: '', // Regular input value of the training tag
      valiableTagInput: '', // Last valid input for tag retrieval.
      brightness: 50, // Brightness
      contrast: 50, // Contrast
      trainingJobId: this.$route.query.id, // ID of the current training job
      tagInputTimer: '', // Timer for filtering training tags
      multiSelectedRunNames: {}, // Dictionary for storing the name of the selected training logs
      multiSelectedTagNames: {}, // Dictionary for storing the name of the selected tags
      curFilterSamples: [], // List of images that meet the current filter criteria
      headTagFullScreen: false, // Indicates whether to expand the tag selection list.
      tagOperateSelectAll: true, // Indicates whether to select all tags
      runOperateList: [], // Training log list
      tagOperateList: [], // Tag list
      originDataArr: [], // List of all image data.
      oriDataDictionaries: {}, // Dictionary for storing training logs and tag relationships
      curPageArr: [], // Image data list on the current page
      pageIndex: 0, // Current page number
      pageSizes: [8, 16, 24], // The number of records on each page is optional
      pageNum: 8, // Number of records on each page
      tagOverRowFlag: false, // Check whether the tag list contains more than one line
      perSelectItemMarginBottom: 1, // Outer margin of the bottom of each selection box
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
        this.updateAllData();
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
    timeReloadValue(newVal) {
      this.autoUpdateSamples();
    },
  },
  destroyed() {
    // Remove the listener of the label input box
    if (this.tagInputTimer) {
      clearTimeout(this.tagInputTimer);
      this.tagInputTimer = null;
    }
    // Disable the automatic refresh function
    if (this.autoUpdateTimer) {
      clearInterval(this.autoUpdateTimer);
      this.autoUpdateTimer = null;
    }
    // Remove the listener of window size change
    window.removeEventListener('resize', this.resizeCallback);
  },
  mounted() {
    this.getCharMainContentwidth();
    this.getTagAndRunList();
  },

  methods: {
    /**
     * Initialize the training log and tag list
     */
    getTagAndRunList() {
      const params = {
        plugin_name: 'image',
        train_id: this.trainingJobId,
      };
      RequestService.getSingleTrainJob(params)
          .then((res) => {
            if (!res || !res.data || !res.data.train_jobs) {
              this.initOver = true;
              return;
            }
            const data = res.data.train_jobs;
            const tempRunList = [];
            const tempTagList = [];
            const dataList = [];
            data.forEach((runObj, runObjIndex) => {
            // Add to Training Log List
              tempRunList.push({
                label: runObj.name,
                checked: true,
                show: true,
              });
              this.multiSelectedRunNames[runObj.name] = true;
              runObj.tags.forEach((tagName) => {
              // Check whether a label with the same name exists
                if (!this.oriDataDictionaries[tagName]) {
                // The new tag information is added to the dictionary
                  this.oriDataDictionaries[tagName] = {};
                  // Add to Tag List
                  tempTagList.push({
                    label: tagName,
                    checked: true,
                    show: true,
                  });
                  this.multiSelectedTagNames[tagName] = true;
                }
                this.oriDataDictionaries[tagName][runObj.name] = true;
                // Add to the original data list
                const sampleItem = {
                  runId: runObj.id,
                  runName: runObj.name,
                  tagName: tagName,
                  sampleData: [],
                  tagShow: true,
                  runShow: true,
                  curPageShow: false,
                  sliderValue: 0,
                  fullScreen: false,
                  totalStepNum: 0,
                  curStep: '',
                  curImgUrl: '',
                  curTime: '',
                  curImageSize: [0, 0],
                };
                dataList.push(sampleItem);
                this.curFilterSamples.push(sampleItem);
              });
            });
            // Initialize the assignment training log list, tag list, and image list
            this.runOperateList = tempRunList;
            this.tagOperateList = tempTagList;
            this.originDataArr = dataList;
            this.initOver = true;

            this.$nextTick(() => {
              this.resizeCallback();
            });

            // Obtains data on the current page
            this.getCurPageDataArr();

            // Automatic refresh
            if (this.isTimeReload) {
              this.autoUpdateSamples();
            }
          }, this.requestErrorCallback)
          .catch((e) => {
            this.$message.error(this.$t('public.dataError'));
          });
    },
    /**
     * Obtains data on the current page
     * @param {Boolwn} noPageDataNumChange No new data is added or deleted
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
          train_id: sampleItem.runId,
          tag: sampleItem.tagName,
        };
        RequestService.getImageMetadatas(params)
            .then((res) => {
              if (!res || !res.data || !res.data.metadatas) {
                return;
              }
              // Processes image data
              const tempData = res.data.metadatas;
              sampleItem.sampleData = tempData;
              const oldTotalStepNum = sampleItem.totalStepNum;
              sampleItem.totalStepNum = tempData.length - 1;
              if (sampleItem.sliderValue === oldTotalStepNum) {
                sampleItem.sliderValue = sampleItem.totalStepNum;
              }
              const curSampleData = sampleItem.sampleData[sampleItem.sliderValue];
              // Initialize the current step information
              if (curSampleData) {
                sampleItem.curStep = curSampleData.step;
                sampleItem.curImgUrl =
                `${basePath}${this.imageBasePath}train_id=${sampleItem.runId}` +
                `&tag=${sampleItem.tagName}&step=${curSampleData.step}&wt=${curSampleData.wall_time}`;
                sampleItem.curTime = new Date(
                    curSampleData.wall_time * 1000,
                ).toLocaleString();
                sampleItem.curImageSize = [
                  curSampleData.width,
                  curSampleData.height,
                ];
              }
              this.$forceUpdate();
            })
            .catch((e) => {});
      });
    },
    /**
     * Listens to and obtains the width of the table container in the content area
     */
    getCharMainContentwidth() {
      // Add the resize listener.
      window.addEventListener('resize', this.resizeCallback, false);
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
        `${basePath}${this.imageBasePath}train_id=${sampleItem.runId}` +
        `&tag=${sampleItem.tagName}&step=${curStepData.step}&wt=${curStepData.wall_time}`;
      sampleItem.curTime = new Date(
          curStepData.wall_time * 1000,
      ).toLocaleString();
      sampleItem.curImageSize = [curStepData.width, curStepData.height];
    },
    /**
     * The callback of window size changes listener
     */
    resizeCallback() {
      // Calculating the Display of the Expand Folding Button
      const tagSelectItemContent = this.$refs.tagSelectItemContent;
      if (tagSelectItemContent) {
        this.tagOverRowFlag =
          tagSelectItemContent.clientHeight <
          tagSelectItemContent.scrollHeight - this.perSelectItemMarginBottom;
      }
    },
    /**
     * Expand or collapse the list of tag items
     */
    toggleHeadTagFullScreen() {
      this.headTagFullScreen = !this.headTagFullScreen;
      if (!this.headTagFullScreen) {
        this.$nextTick(() => {
          this.resizeCallback();
        });
      }
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
     * The number of pages displayed on each page is changed
     * @param {Number} value Number of pages after modification
     */
    pageSizeChange(value) {
      this.pageNum = value;
      this.pageIndex = 0;
      this.getCurPageDataArr();
    },
    /**
     * Click event of the tag selection button
     */
    tagSelectAll() {
      this.tagOperateSelectAll = !this.tagOperateSelectAll;
      this.multiSelectedTagNames = {};
      // Setting the status of tag items
      if (this.tagOperateSelectAll) {
        this.tagOperateList.forEach((tagItem) => {
          if (tagItem.show) {
            tagItem.checked = true;
            this.multiSelectedTagNames[tagItem.label] = true;
          }
        });
      } else {
        this.tagOperateList.forEach((tagItem) => {
          if (tagItem.show) {
            tagItem.checked = false;
          }
        });
      }
      // Update the image list based on the selected status of the tag.
      this.updateTagInPage();
    },
    /**
     * Tag Filter
     */
    filterByTagName() {
      if (this.tagInputTimer) {
        clearTimeout(this.tagInputTimer);
        this.tagInputTimer = null;
      }
      this.tagInputTimer = setTimeout(() => {
        let reg;
        try {
          reg = new RegExp(this.tagInput);
        } catch (e) {
          this.$message.warning(this.$t('public.regIllegal'));
          return;
        }
        this.valiableTagInput = this.tagInput;
        this.multiSelectedTagNames = {};
        let tagSelectAll = true;
        // Filter the tags that do not meet the conditions in the operation bar and hide them
        this.tagOperateList.forEach((tagItem) => {
          if (reg.test(tagItem.label)) {
            tagItem.show = true;
            if (tagItem.checked) {
              this.multiSelectedTagNames[tagItem.label] = true;
            } else {
              tagSelectAll = false;
            }
          } else {
            tagItem.show = false;
          }
        });
        // Update the selected status of the Select All button
        this.tagOperateSelectAll = tagSelectAll;
        // Update the image list based on the selected status of the tag.
        this.updateTagInPage();
      }, 200);
    },
    /**
     * Tag item click event
     * @param {Object} tagItem Current tag item object
     */
    tagItemClick(tagItem) {
      if (!tagItem) {
        return;
      }
      tagItem.checked = !tagItem.checked;
      // Refreshes the selected status of the current label option
      if (tagItem.checked) {
        this.multiSelectedTagNames[tagItem.label] = true;
      } else {
        if (this.multiSelectedTagNames[tagItem.label]) {
          delete this.multiSelectedTagNames[tagItem.label];
        }
      }
      // Update the selected status of the Select All button
      let tagSellectAll = true;
      this.tagOperateList.some((curTagItem) => {
        if (curTagItem.show && !curTagItem.checked) {
          tagSellectAll = false;
          return true;
        }
      });
      this.tagOperateSelectAll = tagSellectAll;
      // Update the image list based on the selected status of the tag.
      this.updateTagInPage();
    },
    /**
     * Update the image list based on the filtered tags
     */
    updateTagInPage() {
      // Reset to the first page
      this.pageIndex = 0;
      const curFilterSamples = [];
      // Obtains the image data subscript that meets the tag filtering conditions
      this.originDataArr.forEach((sampleItem) => {
        if (this.multiSelectedTagNames[sampleItem.tagName]) {
          sampleItem.tagShow = true;
          if (sampleItem.runShow) {
            curFilterSamples.push(sampleItem);
          }
        } else {
          sampleItem.tagShow = false;
        }
      });
      this.curFilterSamples = curFilterSamples;
      // Obtains data on the current page
      this.getCurPageDataArr();
    },
    /**
     * Clear data.
     */
    clearAllData() {
      this.multiSelectedRunNames = {};
      this.multiSelectedTagNames = {};
      this.curFilterSamples = [];
      this.tagOperateSelectAll = true;
      this.runOperateList = [];
      this.tagOperateList = [];
      this.originDataArr = [];
      this.oriDataDictionaries = {};
      this.curPageArr = [];
      this.pageIndex = 0;
      this.tagOverRowFlag = false;
      this.headTagFullScreen = false;
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
      const newRunDictionaries = {}; // Index of the training log in the new data.
      const newTagDictionaries = {}; // Index of the tag in the new data
      let dataRemoveFlag = false;
      // Obtains the current training log and tag list
      oriData.forEach((runObj, runIndex) => {
        newRunDictionaries[runObj.name] = true;
        runObj.tags.forEach((tagName) => {
          if (newTagDictionaries[tagName]) {
            newTagDictionaries[tagName][runObj.name] = true;
          } else {
            newTagDictionaries[tagName] = {};
            newTagDictionaries[tagName][runObj.name] = true;
          }
        });
      });
      // Delete training logs that do not exist in the operation bar
      const oldRunListLength = this.runOperateList.length;
      for (let i = oldRunListLength - 1; i >= 0; i--) {
        if (!newRunDictionaries[this.runOperateList[i].label]) {
          dataRemoveFlag = true;
          this.runOperateList.splice(i, 1);
        }
      }
      // Delete the tags that do not exist in the operation bar
      const oldTagListLength = this.tagOperateList.length;
      for (let i = oldTagListLength - 1; i >= 0; i--) {
        if (!newTagDictionaries[this.tagOperateList[i].label]) {
          dataRemoveFlag = true;
          this.tagOperateList.splice(i, 1);
        }
      }
      // Delete the old data from the image list and update the dictionary
      const oldSampleLength = this.originDataArr.length;
      for (let i = oldSampleLength - 1; i >= 0; i--) {
        const oldSample = this.originDataArr[i];

        if (!newTagDictionaries[oldSample.tagName]) {
          delete this.oriDataDictionaries[oldSample.tagName];
          this.originDataArr.splice(i, 1);
          dataRemoveFlag = true;
        } else if (!newTagDictionaries[oldSample.tagName][oldSample.runName]) {
          delete this.oriDataDictionaries[oldSample.tagName][oldSample.runName];
          this.originDataArr.splice(i, 1);
          dataRemoveFlag = true;
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
      const runDictionaries = {};
      const tagDictionaries = {};
      // Generate the current training log dictionary
      this.runOperateList.forEach((runItem) => {
        runDictionaries[runItem.label] = true;
      });
      // Generate the current tag dictionary
      this.tagOperateList.forEach((tagItem) => {
        tagDictionaries[tagItem.label] = true;
      });

      // Add New Data
      let dataAddFlag = false;
      oriData.forEach((runObj) => {
        // Add training logs in the operation bar
        if (!runDictionaries[runObj.name]) {
          this.runOperateList.push({
            label: runObj.name,
            checked: true,
            show: false,
          });
          runDictionaries[runObj.name] = true;
          dataAddFlag = true;
        }

        runObj.tags.forEach((tagName) => {
          // Adding a tag to the operation bar
          if (!tagDictionaries[tagName]) {
            this.tagOperateList.push({
              label: tagName,
              checked: true,
              show: false,
            });
            tagDictionaries[tagName] = true;
            dataAddFlag = true;
          }

          // Add Image Information
          let newSampleFlag = false;
          if (this.oriDataDictionaries[tagName]) {
            if (!this.oriDataDictionaries[tagName][runObj.name]) {
              newSampleFlag = true;
              this.oriDataDictionaries[tagName][runObj.name] = true;
            }
          } else {
            newSampleFlag = true;
            this.oriDataDictionaries[tagName] = {};
            this.oriDataDictionaries[tagName][runObj.name] = true;
          }
          // Add image information to all data array
          if (newSampleFlag) {
            dataAddFlag = true;
            this.originDataArr.push({
              runId: runObj.id,
              runName: runObj.name,
              tagName: tagName,
              sampleData: [],
              tagShow: false,
              runShow: true,
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
      });
      return dataAddFlag;
    },
    /**
     * Update the training log and tag selection status and select all status,
     * and obtain the list of images that meet the search criteria
     */
    updateRunAndTagSelectStateAndFilterResult() {
      this.multiSelectedRunNames = {};
      this.multiSelectedTagNames = {};
      // Update the selection status and selection status of training logs
      this.runOperateList.forEach((runItem) => {
        runItem.show = true;
        this.multiSelectedRunNames[runItem.label] = true;
      });
      // Update the tag selection status and select all status
      let tagReg;
      try {
        tagReg = new RegExp(this.tagInput);
      } catch (e) {
        tagReg = new RegExp(this.valiableTagInput);
      }
      let tagSelectAll = true;
      this.tagOperateList.forEach((tagItem) => {
        if (tagReg.test(tagItem.label)) {
          tagItem.show = true;
          if (tagItem.checked) {
            this.multiSelectedTagNames[tagItem.label] = true;
          } else {
            tagSelectAll = false;
          }
        } else {
          tagItem.show = false;
        }
      });
      this.tagOperateSelectAll = tagSelectAll;
      // Update the list of images that meet the filter criteria
      const curFilterSamples = [];
      this.originDataArr.forEach((sampleItem) => {
        sampleItem.runShow = true;
        // Filter tag
        if (this.multiSelectedTagNames[sampleItem.tagName]) {
          sampleItem.tagShow = true;
        } else {
          sampleItem.tagShow = false;
        }
        // whether all filter criteria are met.
        if (sampleItem.tagShow && sampleItem.runShow) {
          curFilterSamples.push(sampleItem);
        }
      });
      this.curFilterSamples = curFilterSamples;
    },
    /**
     * Update all data.
     */
    updateAllData() {
      const params = {
        plugin_name: 'image',
        train_id: this.trainingJobId,
      };
      RequestService.getSingleTrainJob(params)
          .then((res) => {
            if (this.isReloading) {
              this.$store.commit('setIsReload', false);
              this.isReloading = false;
            }
            // Fault tolerance processing
            if (!res || !res.data) {
              return;
            } else if (!res.data.train_jobs) {
              this.clearAllData();
              return;
            }
            const oriData = res.data.train_jobs;
            // Delete the data that does not exist.
            const dataRemoveFlag = this.removeNonexistentData(oriData);
            // Check whether new data exists and add it
            const dataAddFlag = this.checkNewDataAndComplete(oriData);
            this.$nextTick(() => {
              this.resizeCallback();
            });
            // Update the training log and tag selection status and select all status,
            // and obtain the list of images that meet the search criteria
            this.updateRunAndTagSelectStateAndFilterResult();
            // Obtains data on the current page
            this.getCurPageDataArr(!dataRemoveFlag && !dataAddFlag);
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
        this.updateAllData();
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
  },
  // Component titlebar
  components: {},
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
    width: 84px;
  }
  .select-all {
    cursor: pointer;
    flex-shrink: 0;
  }
  .cl-img-operate-content {
    width: 100%;
    padding: 8px 32px 22px 32px;
    background: #ffffff;
    .tag-select-content {
      display: flex;
      align-items: center;

      .select-item-content {
        display: flex;
        height: 16px;
        flex-wrap: wrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .run-select-content-open {
        flex: 1;
        text-align: right;
        font-size: 14px;
        color: #00a5a7;
        cursor: pointer;
        min-width: 60px;
      }
    }
    .run-select-content-all {
      max-height: 150px;
      padding-left: 72px;
      overflow-x: hidden;
      display: flex;
      flex-wrap: wrap;
      .label-item {
        line-height: 14px;
      }
      .select-item {
        height: 25px;
        margin-top: 25px;
      }
    }
    .select-item {
      margin-right: 20px;
      flex-shrink: 0;
      margin-bottom: 1px;
      cursor: pointer;
      .label-item {
        width: 100px;
        display: block;
        text-overflow: ellipsis;
        white-space: nowrap;
        overflow: hidden;
        text-align: left;
      }
    }
    .multiCheckBox-border {
      width: 16px;
      height: 16px;
      display: block;
      margin-right: 20px;
      cursor: pointer;
      float: left;
    }
    .checkbox-checked {
      background-image: url('../../assets/images/mult-select.png');
    }
    .checkbox-unchecked {
      background-image: url('../../assets/images/mult-unselect.png');
    }
    .label-item {
      font-size: 14px;
      line-height: 14px;
      vertical-align: middle;
      .el-tooltip {
        text-overflow: ellipsis;
        white-space: nowrap;
        overflow: hidden;
        text-align: left;
        height: 16px;
      }
      span {
        font-size: 14px;
        line-height: 14px;
        display: block;
      }
    }
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
          .run-title {
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
      height: 450px;
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

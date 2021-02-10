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
  <div class="cl-hoc">
    <div class="cl-hoc-container">
      <div class="cl-hoc-title cl-hoc-tip-container">
        {{$t('explain.coverfactualInterpretation')}}
        <el-tooltip placement="right-start"
                    effect="light">
          <div slot="content"
               class="tooltip-container">
            <div class="tip-text">
              {{$t('explain.hocTitleTip')}}
            </div>
          </div>
          <i class="el-icon-info"></i>
        </el-tooltip>
      </div>
      <div class="cl-hoc-con">
        <div class="cl-hoc-left">
          <!-- Top Bar -->
          <div class="cl-left-top-container">
            <div class="hoc-title-container left-title">
              {{$t('explain.imageList')}}
            </div>
            <!-- Selecting a hoc image -->
            <div class="hoc-filter-container cl-hoc-tip-container">
              <div class="title-text">
                {{$t('explain.tag')}}
                <el-tooltip placement="bottom-start"
                    effect="light">
                  <div slot="content"
                      class="tooltip-container">
                    {{ $t('explain.labelTip') }}
                  </div>
                  <i class="el-icon-info"></i>
                </el-tooltip>
              </div>
              <div class="select-options">
                <el-select v-model="curFilterLabel"
                           :placeholder="$t('public.select')"
                           @change="filterLabelChange"
                           size="small">
                  <el-option v-for="item in labelLlist"
                             :key="item.label"
                             :label="item.label"
                             :value="item.label"></el-option>
                </el-select>
              </div>
            </div>
            <div class="hoc-filter-container">
              <div class="title-text">{{$t('explain.imgSort')}}</div>
              <div class="select-options">
                <el-select v-model="pageData.sortName"
                           :placeholder="$t('public.select')"
                           size="small">
                  <el-option v-for="item in sortOption"
                             :key="item.value"
                             :label="item.label"
                             :value="item.value"></el-option>
                </el-select>
              </div>
            </div>
          </div>
          <!-- Thumbnail bar -->
          <div class="cl-left-middle-container">
            <div class="cl-left-thumb"
                 v-if="!pageData.totalNum || !initOver">
              <!-- No data -->
              <div class="image-noData">
                <div>
                  <img :src="require('@/assets/images/nodata.png')"
                       alt="" />
                </div>
                <div v-if="initOver"
                     class="noData-text">{{$t("public.noData")}}</div>
                <div v-else
                     class="noData-text">{{$t("public.dataLoading")}}</div>
              </div>
            </div>
            <div class="cl-left-thumb"
                 v-else>
              <div class="cl-left-thumb-item"
                   v-for="(data, index) in fullData"
                   :key="data.id"
                   :class="index === curSelectedDataIndex ? 'active' : ''"
                   @click="dataSelect(index)">
                <img :src="formateUrl(data.image)">
              </div>
            </div>
            <!-- pagination -->
            <div class="cl-left-page">
              <el-pagination layout="prev, pager ,next, jumper"
                             :total="pageData.totalNum"
                             :current-page="pageData.curPage"
                             :pager-count="5"
                             :page-size="pageData.pageSize"
                             @current-change="pageChange"></el-pagination>
            </div>
          </div>
        </div>
        <div class="cl-hoc-right">
          <div class="cl-right-top">
            <div class="cl-right-top-item left-item">
              <!-- Original image label selection bar -->
              <div class="cl-right-title">
                <div class="hoc-title-container ori-image-title">
                  {{$t('explain.originalPicture')}}
                </div>
                <div class="ori-tag-select-container">
                  <div class="ori-select-title"
                       :title="$t('explain.forecastTagPosibility')">
                    {{$t('explain.forecastTagPosibility')}}
                  </div>
                  <div class="cl-left-options">
                    <el-select v-model="curImageData.selectedLabel"
                               :placeholder="$t('public.select')"
                               size="small"
                               @change="selectLableChange">
                      <el-option v-for="item in curImageData.labels"
                                 :key="item.value"
                                 :label="item.label"
                                 :value="item.value"></el-option>
                    </el-select>
                  </div>
                </div>
              </div>
              <!-- Original image -->
              <div class="ori-image-container">
                <img v-if="curImageData.src"
                     :src="formateUrl(curImageData.src)">
                <div class="image-noData"
                     v-else>
                  <div>
                    <img :src="require('@/assets/images/nodata.png')"
                         alt="" />
                  </div>
                  <div v-if="initOver"
                       class="noData-text">{{$t("public.noData")}}</div>
                  <div v-else
                       class="noData-text">{{$t("public.dataLoading")}}</div>
                </div>
              </div>
            </div>
            <div class="cl-right-top-item">
              <div class="cl-right-title">
                <div class="hoc-title-container">{{$t('explain.viewExplanation')}}</div>
                <div class="cl-right-title-silde">
                  <div class="cl-right-title-label cl-hoc-tip-container">
                    {{ $t('explain.minConfidence') }}
                    <el-tooltip placement="bottom-start"
                                effect="light">
                      <div slot="content">
                        {{ $t('explain.hocMinConfidenceTip') }}
                      </div>
                      <i class="el-icon-info"></i>
                    </el-tooltip>
                    <span>{{ $t('symbols.colon') }}</span>
                    <span>{{ minConfidence }}</span>
                  </div>
                </div>
              </div>
              <div class="cl-right-con">
                <div class="img-container">
                  <img v-if="curImageData.curSampleData.hoc_layers && curImageData.curSampleData.hoc_layers.length"
                       :src="formateUrl(curImageData.curSampleData.hoc_layers[curImageData.imageIndex].outcome)"
                       alt="">
                  <div class="image-noData"
                       v-else>
                    <div>
                      <img :src="require('@/assets/images/nodata.png')"
                           alt="" />
                    </div>
                    <div v-if="initOver"
                         class="noData-text">{{$t("public.noData")}}</div>
                    <div v-else
                         class="noData-text">{{$t("public.dataLoading")}}</div>
                  </div>
                </div>
                <div class="image-title"
                     v-if="curImageData.curSampleData.hoc_layers && curImageData.curSampleData.hoc_layers.length">
                  {{curImageData.curSampleData.label}}
                  {{$t('symbols.leftbracket')}}
                  {{curImageData.curSampleData.hoc_layers[curImageData.imageIndex].confidence.toFixed(3)}}
                  {{$t('symbols.rightbracket')}}
                </div>
              </div>
            </div>
          </div>
          <div class="cl-right-footer"
               ref="foot">
            <div class="cl-right-footer-info hoc-title-container">
              {{$t('explain.maskingProcess')}}
            </div>
            <div class="cl-right-footer-con">
              <div class="cl-right-arrowCon"
                   ref="sampleContainer">
                <div class="cl-right-footer-marquee"
                     v-if="curImageData.curSampleData.hoc_layers && curImageData.curSampleData.hoc_layers.length">
                  <div class="cl-right-footer-item"
                       v-for="(sample, index) in curImageData.curSampleData.hoc_layers"
                       :key="index">
                    <div class="cl-right-footer-image"
                         :style="{width: (widthBase * 2) + 'px'}"
                         @click="jumpImage(index)">
                      <div class="image-container"
                           :class="[curImageData.imageIndex===index ? 'itemActive':'']">
                        <img :src="formateUrl(sample.outcome)"
                             alt="">
                      </div>
                      <div class="cl-right-footer-title">
                        {{curImageData.curSampleData.label}}
                        {{$t('symbols.leftbracket')}}
                        {{sample.confidence.toFixed(3)}}
                        {{$t('symbols.rightbracket')}}
                      </div>
                    </div>
                    <div class="cl-right-footer-arrow"
                         :style="{width: widthBase + 'px'}"
                         v-if="index!==curImageData.curSampleData.hoc_layers.length-1">
                      <i class="el-icon-right"></i>
                    </div>
                  </div>
                </div>
                <!-- No data -->
                <div class="image-noData"
                     v-else>
                  <div>
                    <img :src="require('@/assets/images/nodata.png')"
                         alt="" />
                  </div>
                  <div v-if="initOver"
                       class="noData-text">{{$t("public.noData")}}</div>
                  <div v-else
                       class="noData-text">{{$t("public.dataLoading")}}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
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
      trainId: this.$route.query.id, // Train id
      initOver: false, // Initialization completion flag
      // Sorting mode
      sortOption: [
        {
          label: 'confidence',
          value: 'confidence',
        },
      ],
      // Pagination data
      pageData: {
        curPage: 1,
        totalNum: 0,
        pageSize: 24,
        pageSizes: [24],
        sortName: 'confidence',
        sortType: 'descending',
      },
      // Prediction tag of the current image
      labelLlist: [],
      // All tags
      emptyLabelSelect: {
        id: -1,
        label: this.$t('public.all'),
      },
      curFilterLabel: this.$t('public.all'), // Current filter label
      resizeTimer: null, // Timer for changing the window size
      widthBase: 150, // Foundation width
      textHeight: 30, // Text height
      partBase: 2, // Number of basic block
      minConfidence: '', // Probability threshold
      fullData: [], // Full data on current page
      curSelectedDataIndex: 0, // Current selected data subscript
      // Information about the selected data
      curImageData: {
        src: '',
        labels: [],
        selectedLabel: '',
        oriData: {},
        imageIndex: 0,
        curSampleData: {},
      },
      dataWaitTimer: null, // No data available timer
      // Status of metaData request
      status: {
        pendding: 'PENDING',
        loading: 'LOADING',
        loaded: 'LOADED',
        stop: 'STOP',
      },
    };
  },
  computed: {},
  watch: {},
  created() {
    this.getMetaData();
  },
  mounted() {
    if (!this.trainId) {
      this.$message.error(this.$t('trainingDashboard.invalidId'));
      document.title = `${this.$t(
          'explain.conterfactualInterpretation',
      )}-MindInsight`;
      return;
    }
    document.title = `${this.$t(
        'explain.conterfactualInterpretation',
    )}-MindInsight`;

    window.addEventListener('resize', this.resizeCallback, false);
    this.$nextTick(() => {
      this.resizeCallback();
    });
  },
  destroyed() {
    // Remove the listener of window size change
    window.removeEventListener('resize', this.resizeCallback);
    // Remove timer
    if (this.dataWaitTimer) {
      clearTimeout(this.dataWaitTimer);
      this.dataWaitTimer = null;
    }
  },
  methods: {
    /**
     * Obtains explanation job meta information
     */
    getMetaData() {
      const params = {
        train_id: this.trainId,
      };
      RequestService.queryTrainInfo(params).then(
          (res) => {
            if (
              !res ||
            !res.data ||
            !res.data.classes ||
            !res.data.saliency
            ) {
              this.initOver = true;
              return;
            }
            const status = res.data.status;
            // IF status is not loaded, delay 500ms and request again
            const delayTime = 500;
            if (status !== this.status.loaded) {
              if (this.dataWaitTimer) {
                clearTimeout(this.dataWaitTimer);
                this.dataWaitTimer = null;
              }
              this.dataWaitTimer = setTimeout(() => {
                this.getMetaData();
              }, delayTime);
            } else {
              this.labelLlist = [this.emptyLabelSelect].concat(res.data.classes);
              this.minConfidence = res.data.saliency.min_confidence;
              this.getHOCData();
            }
          }, () => {
            this.initOver = true;
          },
      );
    },

    /**
     * Obtains HOC data
     */
    getHOCData() {
      const params = {
        train_id: this.trainId,
        limit: this.pageData.pageSize,
        offset: this.pageData.curPage - 1,
        sorted_name: this.pageData.sortName,
        sorted_type: this.pageData.sortType,
      };
      if (this.curFilterLabel !== this.$t('public.all')) {
        params.labels = [this.curFilterLabel];
      }
      RequestService.queryHOCData(params).then(
          (res) => {
            this.initOver = true;
            if (!res || !res.data) {
              this.pageData.totalNum = 0;
              this.resetIniitData();
              return;
            }
            this.pageData.totalNum = res.data.count;
            this.fullData = res.data.samples;
            this.curSelectedDataIndex = 0;
            this.formateCurrentHOCData();
          },
          () => {
            this.pageData.totalNum = 0;
            this.initOver = true;
            this.resetIniitData();
          },
      );
    },
    /**
     * Initializes and loads selected HOC data
     */
    formateCurrentHOCData() {
      const curData = this.fullData[this.curSelectedDataIndex];
      if (!curData) {
        this.resetIniitData();
        return;
      }
      const labelOptions = [];
      curData.inferences.forEach((inference, index) => {
        const label = `${inference.label}${this.$t(
            'symbols.leftbracket',
        )}${inference.confidence.toFixed(3)}${this.$t('symbols.rightbracket')}`;
        labelOptions.push({
          label: label,
          value: index,
        });
      });
      this.curImageData.src = curData.image;
      this.curImageData.labels = labelOptions;
      this.curImageData.oriData = curData;
      if (labelOptions.length) {
        this.curImageData.selectedLabel = labelOptions[0].value;
        this.curImageData.curSampleData = this.curImageData.oriData.inferences[
            this.curImageData.selectedLabel
        ];
      } else {
        this.curImageData.selectedLabel = '';
        this.curImageData.curSampleData = {};
      }
      if (
        this.curImageData.curSampleData.hoc_layers &&
        this.curImageData.curSampleData.hoc_layers.length
      ) {
        this.curImageData.imageIndex =
          this.curImageData.curSampleData.hoc_layers.length - 1;
      } else {
        this.curImageData.imageIndex = 0;
      }
    },

    /**
     * Page number change
     * @param {Number} page Page number after change
     */
    pageChange(page) {
      this.pageData.curPage = page;
      this.getHOCData();
    },

    /**
     * Selected data change
     * @param {Number} index Selected data subscript
     */
    dataSelect(index) {
      this.curSelectedDataIndex = index;
      this.formateCurrentHOCData();
    },

    /**
     * The images label is changed
     * @param {Number} value Selected label subscript
     */
    selectLableChange(value) {
      this.curImageData.selectedLabel = value;
      this.curImageData.curSampleData = this.curImageData.oriData.inferences[
          value
      ];
      if (
        this.curImageData.curSampleData.hoc_layers &&
        this.curImageData.curSampleData.hoc_layers.length
      ) {
        this.curImageData.imageIndex =
          this.curImageData.curSampleData.hoc_layers.length - 1;
      } else {
        this.curImageData.imageIndex = 0;
      }
    },

    /**
     *Jump image
     * @param {Number} index Selected image subscript
     */
    jumpImage(index) {
      this.curImageData.imageIndex = index;
    },

    /**
     * Resize callback
     */
    resizeCallback() {
      if (this.resizeTimer) {
        clearTimeout(this.resizeTimer);
        this.resizeTimer = null;
      }
      this.resizeTimer = setTimeout(() => {
        const sampleContainer = this.$refs.sampleContainer;
        if (sampleContainer) {
          this.widthBase =
            (sampleContainer.clientHeight - this.textHeight) / this.partBase;
        }
      }, 300);
    },
    /**
     * Concatenate a valid URL
     * @param {String} url
     * @return {String} Concatenated character string
     */
    formateUrl(url) {
      if (!url) {
        return '';
      }
      const newURL = `${basePath}${url}&date=${new Date().getTime()}`;
      return newURL.replace(/(?<!:)\/\//g, '/');
    },
    /**
     * Filter label change
     */
    filterLabelChange() {
      this.pageData.curPage = 1;
      this.getHOCData();
    },
    /**
     * Reset initial data
     */
    resetIniitData() {
      this.curImageData = {
        src: '',
        labels: [],
        selectedLabel: '',
        oriData: {},
        imageIndex: 0,
        curSampleData: {},
      };
    },
  },
};
</script>
<style>
.cl-hoc {
  height: 100%;
  background-color: #fff;
}
.cl-hoc .no-image-tip {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}
.cl-hoc .image-noData {
  height: 100%;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}
.cl-hoc .image-noData .noData-text {
  margin-top: 33px;
  font-size: 18px;
}
.cl-hoc .hoc-title-container {
  font-size: 16px;
  font-weight: bold;
  line-height: 21px;
}
.cl-hoc .cl-hoc-container {
  height: 100%;
  padding: 0 32px 14px 32px;
}
.cl-hoc .cl-hoc-container .cl-hoc-tip-container .el-icon-info {
  color: #6c7280;
}
.cl-hoc .cl-hoc-title {
  height: 56px;
  font-size: 20px;
  font-weight: bold;
  line-height: 56px;
}
.cl-hoc .cl-hoc-title .tooltip-container .tip-text {
  padding: 10px;
}
.cl-hoc .cl-hoc-title .tooltip-container .tip-text .tip-title {
  font-size: 16px;
  font-weight: bold;
}
.cl-hoc .cl-hoc-title .tooltip-container .tip-text .tip-part {
  line-height: 20px;
  word-break: normal;
}
.cl-hoc .cl-hoc-con {
  height: calc(100% - 55px);
  overflow-y: auto;
  display: flex;
}
.cl-hoc .cl-hoc-con .cl-hoc-left {
  width: 440px;
  background-color: #edf0f5;
  margin-right: 20px;
  flex-shrink: 0;
  padding: 20px 24px;
  height: 100%;
}
.cl-hoc .cl-hoc-con .cl-hoc-left .cl-left-top-container .left-title {
  margin-bottom: 20px;
}
.cl-hoc .cl-hoc-con .cl-hoc-left .cl-left-top-container .hoc-filter-container {
  display: flex;
  line-height: 32px;
  margin-bottom: 12px;
}
.cl-hoc
  .cl-hoc-con
  .cl-hoc-left
  .cl-left-top-container
  .hoc-filter-container
  .title-text {
  width: 100px;
  flex: 1;
}
.cl-hoc .cl-hoc-con .cl-hoc-left .cl-left-middle-container {
  display: flex;
  flex-direction: column;
  height: calc(100% - 131px);
}
.cl-hoc .cl-hoc-con .cl-hoc-left .cl-left-thumb {
  flex: 1;
  display: flex;
  background-color: #fff;
  flex-wrap: wrap;
  overflow: hidden;
  align-content: flex-start;
}
.cl-hoc .cl-hoc-con .cl-hoc-left .cl-left-thumb .cl-left-thumb-item {
  width: calc(25% - 10px);
  height: calc(16.6% - 10px);
  margin: 5px;
  overflow: hidden;
  cursor: pointer;
}
.cl-hoc .cl-hoc-con .cl-hoc-left .cl-left-thumb .cl-left-thumb-item img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.cl-hoc .cl-hoc-con .cl-hoc-left .cl-left-thumb .active,
.cl-hoc .cl-hoc-con .cl-hoc-left .cl-left-thumb .cl-left-thumb-item:hover {
  border: solid 1px #00a5a7;
}
.cl-hoc .cl-hoc-con .cl-hoc-left .cl-left-page {
  padding: 0 10px;
  flex-shrink: 0;
  background-color: #fff;
  text-align: right;
}
.cl-hoc .cl-hoc-con .cl-hoc-left .cl-left-page .el-pagination {
  border-top: solid 1px #ccc;
}
.cl-hoc .cl-hoc-con .cl-hoc-right {
  overflow: hidden;
  flex: 1;
}
.cl-hoc .cl-hoc-con .cl-hoc-right .cl-right-top {
  height: 60%;
  display: flex;
}
.cl-hoc .cl-hoc-con .cl-hoc-right .cl-right-top .left-item {
  margin-right: 20px;
}
.cl-hoc .cl-hoc-con .cl-hoc-right .cl-right-top .cl-right-top-item {
  width: calc(50% - 10px);
  padding: 20px 24px;
  height: 100%;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
}
.cl-hoc
  .cl-hoc-con
  .cl-hoc-right
  .cl-right-top
  .cl-right-top-item
  .cl-right-title {
  padding-bottom: 12px;
}
.cl-hoc
  .cl-hoc-con
  .cl-hoc-right
  .cl-right-top
  .cl-right-top-item
  .cl-right-title
  .ori-image-title {
  margin-bottom: 6px;
}
.cl-hoc
  .cl-hoc-con
  .cl-hoc-right
  .cl-right-top
  .cl-right-top-item
  .cl-right-title
  .ori-tag-select-container {
  display: flex;
  font-size: 14px;
  line-height: 32px;
}
.cl-hoc
  .cl-hoc-con
  .cl-hoc-right
  .cl-right-top
  .cl-right-top-item
  .cl-right-title
  .ori-tag-select-container
  .ori-select-title {
  flex: 1;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
  padding-right: 10px;
}
.cl-hoc
  .cl-hoc-con
  .cl-hoc-right
  .cl-right-top
  .cl-right-top-item
  .cl-right-title
  .cl-right-title-silde {
  display: flex;
  margin-top: 12px;
}
.cl-hoc
  .cl-hoc-con
  .cl-hoc-right
  .cl-right-top
  .cl-right-top-item
  .cl-right-title
  .cl-right-title-silde
  .cl-right-title-label {
  font-size: 14px;
  color: #333333;
}
.cl-hoc
  .cl-hoc-con
  .cl-hoc-right
  .cl-right-top
  .cl-right-top-item
  .ori-image-container {
  height: calc(100% - 100px);
}
.cl-hoc
  .cl-hoc-con
  .cl-hoc-right
  .cl-right-top
  .cl-right-top-item
  .ori-image-container
  img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.cl-hoc .cl-hoc-con .cl-hoc-right .cl-right-con {
  height: calc(100% - 63px);
  position: relative;
}
.cl-hoc .cl-hoc-con .cl-hoc-right .cl-right-con .img-container {
  height: calc(100% - 28px);
}
.cl-hoc .cl-hoc-con .cl-hoc-right .cl-right-con .img-container img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.cl-hoc .cl-hoc-con .cl-hoc-right .cl-right-con .image-title {
  width: 100%;
  margin-top: 12px;
  text-align: center;
  line-height: 16px;
}
.cl-hoc .cl-hoc-con .cl-hoc-right .cl-right-footer {
  height: calc(40% - 20px);
  overflow: hidden;
  margin-top: 20px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  padding: 20px 24px 24px 24px;
}
.cl-hoc .cl-hoc-con .cl-hoc-right .cl-right-footer .cl-right-footer-info {
  height: 40px;
}
.cl-hoc .cl-hoc-con .cl-hoc-right .cl-right-footer .cl-right-footer-con {
  height: calc(100% - 40px);
  display: flex;
  overflow: hidden;
}
.cl-hoc
  .cl-hoc-con
  .cl-hoc-right
  .cl-right-footer
  .cl-right-footer-con
  .cl-right-arrowCon {
  height: 100%;
  width: 100%;
  overflow: hidden;
  justify-content: center;
  display: flex;
}
.cl-hoc
  .cl-hoc-con
  .cl-hoc-right
  .cl-right-footer
  .cl-right-footer-con
  .cl-right-footer-marquee {
  display: flex;
  max-width: 100%;
  height: 100%;
  overflow-x: auto;
}
.cl-hoc
  .cl-hoc-con
  .cl-hoc-right
  .cl-right-footer
  .cl-right-footer-con
  .cl-right-footer-item {
  width: auto;
  height: 100%;
  display: flex;
  position: relative;
}
.cl-hoc
  .cl-hoc-con
  .cl-hoc-right
  .cl-right-footer
  .cl-right-footer-con
  .cl-right-footer-item
  .cl-right-footer-image {
  cursor: pointer;
  float: left;
  width: 220px;
  height: 100%;
  position: relative;
  overflow: hidden;
}
.cl-hoc
  .cl-hoc-con
  .cl-hoc-right
  .cl-right-footer
  .cl-right-footer-con
  .cl-right-footer-item
  .cl-right-footer-image
  .image-container {
  width: 100%;
  height: calc(100% - 30px);
}
.cl-hoc
  .cl-hoc-con
  .cl-hoc-right
  .cl-right-footer
  .cl-right-footer-con
  .cl-right-footer-item
  .cl-right-footer-image
  .image-container
  img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.cl-hoc
  .cl-hoc-con
  .cl-hoc-right
  .cl-right-footer
  .cl-right-footer-con
  .cl-right-footer-item
  .cl-right-footer-title {
  width: 220px;
  height: 30px;
  line-height: 30px;
  text-align: center;
}
.cl-hoc
  .cl-hoc-con
  .cl-hoc-right
  .cl-right-footer
  .cl-right-footer-con
  .cl-right-footer-item
  .cl-right-footer-arrow {
  float: left;
  width: 110px;
  height: 100%;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}
.cl-hoc
  .cl-hoc-con
  .cl-hoc-right
  .cl-right-footer
  .cl-right-footer-con
  .cl-right-footer-item
  .cl-right-footer-arrow
  i {
  font-size: 40px;
  color: #dcdfe6;
}
.cl-hoc
  .cl-hoc-con
  .cl-hoc-right
  .cl-right-footer
  .cl-right-footer-con
  .itemActive {
  border: 1px solid #00a5a7;
}
</style>

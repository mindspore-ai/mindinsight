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
  <div class="cl-saliency-map">
    <!-- Page Title -->
    <div class="cl-saliency-map-title">
      {{$t('explain.title')}}
      <el-tooltip placement="right-start"
                  effect="light">
        <div slot="content"
             class="tooltip-container">
          <div class="cl-saliency-map-tip">
            <div class="tip-title">
              {{$t('explain.mainTipTitle')}}
            </div>
            <div class="tip-part">
              {{$t('explain.mainTipPartOne')}}
            </div>
            <div class="tip-part">
              {{$t('explain.mainTipPartTwo')}}
            </div>
            <div class="tip-part">
              {{$t('explain.mainTipPartThree')}}
            </div>
            <a :href="$t('explain.mainTipPartFour')"
               target="_blank">
              {{$t('explain.mainTipPartFour')}}
            </a>
          </div>
        </div>
        <i class="el-icon-info"></i>
      </el-tooltip>
    </div>
    <!-- Explanation Method -->
    <div class="cl-saliency-map-methods">
      <!-- Explainer Checkbox -->
      <select-group :checkboxes="allExplainers"
                    @updateCheckedList="updateSelectedExplainers"
                    :title="$t('explain.explainMethod')">
        <span class="methods-action"
              @click="goMetric">{{$t('explain.viewScore')}}</span>
      </select-group>
    </div>
    <!-- Parameters Fetch -->
    <div class="cl-saliency-map-condition">
      <div class="condition-left">
        <div class="condition-item line-title">
          {{ $t('explain.tag') }}
          <el-tooltip placement="bottom-start"
                      effect="light">
            <div slot="content"
                 class="tooltip-container">
                {{$t('explain.tagTip')}}
            </div>
            <i class="el-icon-info"></i>
          </el-tooltip>
        </div>
        <!-- Truth Labels -->
        <div class="condition-item search-select">
          <search-select multiple
                         plain
                         :source="truthLabels"
                         @selectedUpdate="updateSelected"
                         @selectEnter="fetch">
          </search-select>
        </div>
        <!-- Button -->
        <div class="condition-item">
          <el-button type="primary"
                     class="condition-button"
                     @click="fetch">{{ $t('explain.fetch') }}</el-button>
        </div>
        <!-- Min Confidence -->
        <div class="condition-item">
          {{ $t('explain.minConfidence')}}
          <el-tooltip placement="bottom-start"
                      effect="light"
                      popper-class="confidence-tooltip">
            <div slot="content"
                 class="tooltip-container">
              {{$t('explain.minConfidenceTip')}}
            </div>
            <i class="el-icon-info"></i>
          </el-tooltip>
          {{$t('symbols.colon')}}
          {{minConfidence}}
        </div>
      </div>
      <div class="condition-right">
        <!-- Sorted Name -->
        <div class="condition-item">
          <span class="item-children">{{$t('explain.imgSort')}}</span>
          <el-select v-model="sortedName"
                     @change="sortedNameChange"
                     popper-class="saliency-map-selector">
            <el-option v-for="name of sortedNames"
                       :key="name.label"
                       :label="name.label"
                       :value="name.value">
            </el-option>
          </el-select>
        </div>
        <!-- Open Superpose -->
        <div class="condition-item">
          <span class="item-children">{{
            $t('explain.superposeImg')
          }}</span>
          <el-switch v-model="ifSuperpose"
                     active-color="#00a5a7"></el-switch>
        </div>
      </div>
    </div>
    <!-- Data Table -->
    <div class="cl-saliency-map-table">
      <div class="table-nodata"
           v-if="ifTableLoading">
        <img :src="require('@/assets/images/nodata.png')"
             alt="">
        <span class="nodata-text"
              v-if="!ifError">
          {{ $t('public.dataLoading') }}
        </span>
        <span class="nodata-text"
              v-else>
          {{ $t('public.noData') }}
        </span>
      </div>
      <div class="table-data"
           v-else>
        <el-table :data="tableData"
                  border
                  height="100%"
                  :span-method="mergeTable"
                  :empty-text="$t('explain.noData')">
          <!-- Original Picture Column-->
          <el-table-column :label="$t('explain.originalPicture')"
                           width="270"
                           class-name="pic-cell"
                           :resizable="false">
            <template slot-scope="scope">
              <img :src="getImgURL(scope.row.image)" />
            </template>
          </el-table-column>
          <!-- Forecast Tag Column-->
          <el-table-column width="260"
                           class-name="tag-cell"
                           :resizable="false">
            <!-- Tag Tip -->
            <template slot="header">
              <span>
                {{ $t('explain.forecastTag') }}
                <el-tooltip placement="right-start"
                            effect="light"
                            popper-class="table-tooltip">
                  <div slot="content"
                       class="tooltip-container">
                    <div class="cl-saliency-map-tip tag-tip">
                      <div class="tip-item tip-title">
                        {{$t('explain.forecastTagTip')}}
                      </div>
                      <div class="tip-item">
                        <img :src="require('@/assets/images/explain-tp.svg')"
                             class="tip-icon">
                        {{$t('symbols.colon')}}
                        {{$t('explain.TP')}}
                      </div>
                      <div class="tip-item">
                        <img :src="require('@/assets/images/explain-fn.svg')"
                             class="tip-icon">
                        {{$t('symbols.colon')}}
                        {{$t('explain.FN')}}
                      </div>
                      <div class="tip-item">
                        <img :src="require('@/assets/images/explain-fp.svg')"
                             class="tip-icon">
                        {{$t('symbols.colon')}}
                        {{$t('explain.FP')}}
                      </div>
                      <div class="tip-item">
                        <img :src="require('@/assets/images/explain-tn.svg')"
                             class="tip-icon">
                        {{$t('symbols.colon')}}
                        {{$t('explain.TN')}}
                      </div>
                    </div>
                  </div>
                  <i class="el-icon-info"></i>
                </el-tooltip>
              </span>
            </template>
            <template slot-scope="scope">
              <div class="table-forecast-tag">
                <!--Tag Title-->
                <div class="tag-title-false">
                  <div></div>
                  <div>{{$t('explain.tag')}}</div>
                  <div>{{$t('explain.confidence')}}</div>
                </div>
                <!--Tag content-->
                <div class="tag-content">
                  <div v-for="(tag, index) in scope.row.inferences"
                       :key="tag.label"
                       class="tag-content-item tag-content-item-false"
                       :class="{
                        'tag-active': index === scope.row.activeLabelIndex,
                        'tag-tp': tag.type === 'tp',
                        'tag-fn': tag.type === 'fn',
                        'tag-fp': tag.type === 'fp'
                      }"
                       @click="changeActiveLabel(scope.row, index)">
                    <div></div>
                    <div class="content-label"
                         :title="tag.label">{{tag.label}}</div>
                    <div>{{tag.confidence.toFixed(3)}}</div>
                  </div>
                </div>
              </div>
            </template>
          </el-table-column>
          <!-- Selected Methods Column-->
          <el-table-column v-for="explainer in selectedExplainers"
                           :key="explainer"
                           :label="explainer"
                           class-name="canvas-cell"
                           :resizable="false">
            <template slot="header">
              <span :title="explainer">{{explainer}}</span>
            </template>
            <template slot-scope="scope">
              <superpose-img v-if="scope.row.inferences[scope.row.activeLabelIndex][explainer]"
                             containerSize="250"
                             :backgroundImg="getImgURL(scope.row.image)"
                             :targetImg="getImgURL(scope.row.inferences[scope.row.activeLabelIndex][explainer])"
                             :ifSuperpose="ifSuperpose"
                             @click.native="showImgDiglog(scope.row, explainer)">
              </superpose-img>
            </template>
          </el-table-column>
          <!-- None selected explainer Column-->
          <el-table-column v-if="selectedExplainers.length === 0"
                           label=""
                           class-name="no-method-cell">
            <template>
              <div class="table-nodata">
                <img :src="require('@/assets/images/nodata.png')"
                     alt="">
                <span class="nodata-text">
                  {{$t('explain.noExplainer')}}
                </span>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
    <!-- Pagination -->
    <div class="cl-saliency-map-pagination">
      <el-pagination @current-change="currentPageChange"
                     @size-change="pageSizeChange"
                     :current-page.sync="pageInfo.currentPage"
                     :page-sizes="[2, 5, 10]"
                     :page-size.sync="pageInfo.pageSize"
                     layout="total, sizes, prev, pager, next, jumper"
                     :total="pageInfo.total"
                     v-show="!ifError"></el-pagination>
    </div>
    <!-- Show Img Dialog -->
    <el-dialog :title="imageDetails.title"
               :visible.sync="imageDetails.imgShow"
               v-if="imageDetails.imgShow"
               top="100px"
               width="560px">
      <div class="detail-container">
        <superpose-img containerSize="500"
                       :backgroundImg="imageDetails.imgUrl"
                       :targetImg="imageDetails.targetUrl"
                       :ifSuperpose="ifSuperpose">
        </superpose-img>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import selectGroup from '../../components/select-group';
import superposeImg from '../../components/superpose-img';
import searchSelect from '../../components/search-select';
import requestService from '../../services/request-service.js';
import {basePath} from '@/services/fetcher';

export default {
  components: {
    selectGroup,
    superposeImg,
    searchSelect,
  },
  data() {
    return {
      trainID: '', // The id of the train
      selectedExplainers: [], // The selected explainer methods
      allExplainers: [], // The list of all explainer method
      imageDetails: {
        title: '',
        imgUrl: '',
        targetUrl: '',
        imgShow: false,
      }, // The object of show img dialog
      ifSuperpose: false, // If open the superpose function
      ifTableLoading: true, // If the table waiting for the data
      ifError: false, // If request error
      minConfidence: 0, // The min confidence
      tableData: null, // The table data
      selectedTruthLabels: [], // The selected truth labels
      truthLabels: [], // The list of all truth labels
      // truthLabelsTemp: [], // The list of all truth labels
      sortedName: 'confidence', // The sorted Name of sort
      sortedNames: [
        {
          label: this.$t('explain.byProbability'),
          value: 'confidence',
        },
      ], // The list of all sorted Name
      sortedType: 'descending', // The default sorted type
      pageInfo: {
        currentPage: 1,
        pageSize: 2,
        total: 0,
      }, // The object of pagination information
      tableHeight: 0, // The height of table to fix the table header
      queryParameters: null, // The complete parameters of query table information, have pagination information
      labelReady: false, // If the truth labels are ready
      pageChangeDelay: 200, // The time interval used to prevent the violent clicks of changing current page
    };
  },
  computed: {
    // The basic parameters of query table information, have none pagination information
    baseQueryParameters() {
      return {
        train_id: this.trainID,
        labels: this.selectedTruthLabels,
        explainer: this.selectedExplainers,
        sorted_name: this.sortedName,
      };
    },
  },
  methods: {
    /**
     * The logic of update selected explainers
     * @param {Object} newVal The updated list
     */
    updateSelectedExplainers(newVal) {
      this.selectedExplainers = newVal;
    },
    /**
     * The logic of update selected truth labels
     * @param {Object} newVal The updated list
     */
    updateSelected(newVal) {
      this.selectedTruthLabels = newVal;
    },
    /**
     * Get the complete url of image
     * @param {string} url The path url
     * @return {string} The complete url of image
     */
    getImgURL(url) {
      const newURL = `${basePath}${url}&date=${new Date().getTime()}`;
      return newURL.replace(/(?<!:)\/\//g, '/');
    },
    /**
     * The logic of query page information by non-default parameters
     */
    fetch() {
      this.pageInfo.currentPage = 1;
      this.updateTable(this.baseQueryParameters, {
        limit: this.pageInfo.pageSize,
        offset: this.pageInfo.currentPage - 1,
      });
    },
    /**
     * The logic that is executed when the page size changed
     * @param {number} val The new page size
     */
    pageSizeChange(val) {
      this.pageInfo.currentPage = 1;
      this.queryParameters.offset = this.pageInfo.currentPage - 1;
      this.queryParameters.limit = val;
      this.queryPageInfo(this.queryParameters);
    },
    /**
     * The logic that is executed when the current page number changed
     * @param {number} val The current page number
     */
    currentPageChange(val) {
      clearTimeout(this.pageChangeTimer);
      this.pageChangeTimer = setTimeout(() => {
        this.queryParameters.offset = val - 1;
        this.queryPageInfo(this.queryParameters);
        this.pageChangeTimer = null;
      }, this.pageChangeDelay);
    },
    /**
     * The logic that is executed when the sorted name changed
     * @param {string} val The sorted name now
     */
    sortedNameChange(val) {
      this.queryParameters.sorted_name = val;
      this.pageInfo.currentPage = 1;
      this.queryParameters.offset = this.pageInfo.currentPage - 1;
      this.queryPageInfo(this.queryParameters);
    },
    /**
     * The logic of click the explainer method canvas
     * @param {Object} rowObj The object of table row in element-ui table
     * @param {string} title The title of the dialog
     */
    showImgDiglog(rowObj, title) {
      this.imageDetails.title = title;
      this.imageDetails.imgUrl = this.getImgURL(rowObj.image);
      this.imageDetails.targetUrl = this.getImgURL(
          rowObj.inferences[rowObj.activeLabelIndex][title],
      );
      this.imageDetails.imgShow = true;
    },
    /**
     * Request basic information of train
     * @param {Object} params Parameters of the request basic information of train interface
     * @return {Object}
     */
    queryTrainInfo(params) {
      return new Promise((resolve, reject) => {
        requestService
            .queryTrainInfo(params)
            .then(
                (res) => {
                  if (res && res.data) {
                    if (res.data.saliency) {
                      this.minConfidence = res.data.saliency.min_confidence
                    ? res.data.saliency.min_confidence
                    : '--';
                      this.allExplainers = this.arrayToCheckBox(
                          res.data.saliency.explainers,
                      );
                    }
                    if (res.data.classes) {
                      const truthLabels = [];
                      for (let i = 0; i < res.data.classes.length; i++) {
                        truthLabels.push(res.data.classes[i].label);
                      }
                      this.truthLabels = truthLabels;
                    }
                  }
                  resolve(true);
                },
                (error) => {
                  reject(error);
                },
            )
            .catch((error) => {
              reject(error);
            });
      });
    },
    /**
     * The complete logic of table update when any condition changed
     * @param {Object} params The main parameters
     * @param {Object} supParams The supplymentary parameters
     */
    updateTable(params, supParams) {
      const paramsTemp = JSON.parse(JSON.stringify(params));
      for (const attr in paramsTemp) {
        if ({}.hasOwnProperty.call(paramsTemp, attr)) {
          if (
            paramsTemp[attr] === null ||
            paramsTemp[attr] === undefined ||
            // Some array has no element in does not mean query when it empty
            (Array.isArray(paramsTemp[attr]) &&
              paramsTemp[attr].length === 0 &&
              attr !== 'explainer')
          ) {
            Reflect.deleteProperty(paramsTemp, attr);
          }
        }
      }
      Object.assign(paramsTemp, supParams);
      this.queryPageInfo(paramsTemp);
    },
    /**
     * Request page table information
     * @param {Object} params Parameters of the request page information interface
     */
    queryPageInfo(params) {
      params.train_id = decodeURIComponent(params.train_id);
      this.queryParameters = params;
      requestService
          .queryPageInfo(params)
          .then(
              (res) => {
                // Make sure the offset of response is equal to offset of request
                if (params.offset === this.queryParameters.offset) {
                  if (res && res.data && res.data.samples) {
                    if (this.minConfidence === '--') {
                      this.tableData = this.processTableData(res.data.samples, false);
                      this.pageInfo.total =
                  res.data.count !== undefined ? res.data.count : 0;
                    } else {
                      this.tableData = this.processTableData(
                          res.data.samples,
                          this.minConfidence,
                      );
                      this.pageInfo.total =
                  res.data.count !== undefined ? res.data.count : 0;
                    }
                  } else {
                    this.pageInfo.total = 0;
                  }
                  this.ifError = false;
                  this.ifTableLoading = false;
                }
              },
              (error) => {
                this.ifError = true;
                this.ifTableLoading = true;
              },
          )
          .catch((e) => {
            this.ifError = true;
            this.ifTableLoading = true;
          });
    },
    /**
     * Process the original table data
     * @param {Object} samples The original table data
     * @param {number | boolean} minConfidence The min confindence
     * If min confidence is lost, replace with type except number, such as 'false', 'null'
     * @return {Object} The processed table data
     */
    processTableData(samples, minConfidence) {
      for (let i = 0; i < samples.length; i++) {
        samples[i].activeLabelIndex = 0;
        if (samples[i].inferences) {
          for (let j = 0; j < samples[i].inferences.length; j++) {
            if (
              typeof minConfidence === 'number' &&
              typeof samples[i].inferences[j].confidence === 'number'
            ) {
              // Model Inference Result
              const MIR =
                samples[i].inferences[j].confidence * 100 >=
                minConfidence * 100;
              let labelValid;
              // The label if valid, judged by whether it exists in the truth labels
              if (samples[i].labels && samples[i].inferences[j].label) {
                labelValid =
                  samples[i].labels.indexOf(samples[i].inferences[j].label) >=
                  0;
              } else {
                labelValid = false;
              }
              if (MIR) {
                if (labelValid) {
                  samples[i].inferences[j].type = 'tp';
                } else {
                  samples[i].inferences[j].type = 'fp';
                }
              } else {
                if (labelValid) {
                  samples[i].inferences[j].type = 'fn';
                } else {
                  samples[i].inferences[j].type = 'tn';
                }
              }
            } else {
              samples[i].inferences[j].type = 'none';
            }
            // Defined the attr{key: explainer, value: overlay} out the saliencies
            // Can provide some convenience for some table operation
            if (samples[i].inferences[j].saliency_maps) {
              const saliencies = samples[i].inferences[j].saliency_maps;
              for (let k = 0; k < saliencies.length; k++) {
                const explainer = saliencies[k].explainer;
                const overlay = saliencies[k].overlay;
                samples[i].inferences[j][explainer] = overlay;
              }
            }
          }
        }
      }
      return samples;
    },
    /**
     * Transform the array of string to array of checkbox
     * Class Checkbox { label: string, checked: boolean }
     * @param {Array<string>} arrayTemp The target array
     * @return {Array<Checkbox>} The result array
     */
    arrayToCheckBox(arrayTemp) {
      if (!Array.isArray(arrayTemp)) {
        return [];
      }
      if (arrayTemp.length === 0 || typeof arrayTemp[0] !== 'string') {
        return [];
      }
      const res = arrayTemp.map((item) => {
        return {
          label: item,
          checked: true,
        };
      });
      return res;
    },
    /**
     * Change the active label index in table row object by click
     * @param {Object} row The row object of element-ui table
     * @param {number} index The click item index
     */
    changeActiveLabel(row, index) {
      row.activeLabelIndex = index;
    },
    /**
     * Merge the table column of explainer when there is none selected explainer
     * @param {Object} params The specified object in element-ui table api
     * @return {Array<number>} Means [rowSpan, colSpan]
     */
    mergeTable({row, column, rowIndex, columnIndex}) {
      if (this.selectedExplainers.length === 0) {
        if (columnIndex === 2) {
          // Merge the column which should has explainer but none now
          return [this.pageInfo.pageSize, 1];
        }
      } else {
        // Do nothing
        return [1, 1];
      }
    },
    /**
     * Go to the metric page
     */
    goMetric() {
      this.$router.push({
        path: '/explain/xai-metric',
        query: {id: this.trainID},
      });
    },
  },
  created() {
    if (!this.$route.query.id) {
      this.$message.error(this.$t('trainingDashboard.invalidId'));
      this.ifError = true;
      return;
    }
    this.trainID = this.$route.query.id;
    const params = {
      train_id: this.trainID,
    };
    this.queryTrainInfo(params)
        .then(
            (res) => {
              this.updateTable(this.baseQueryParameters, {
                limit: this.pageInfo.pageSize,
                offset: this.pageInfo.currentPage - 1,
              });
            },
            (error) => {
              this.ifError = true;
            },
        )
        .catch((e) => {
          this.ifError = true;
        });
  },
  mounted() {
    // Change the page title
    if (this.$route.query.id) {
      document.title = `${decodeURIComponent(this.$route.query.id)}-${this.$t(
          'explain.title',
      )}-MindInsight`;
    } else {
      document.title = `${this.$t('explain.title')}-MindInsight`;
    }
  },
};
</script>

<style>
.saliency-map-selector .selected {
  font-weight: normal;
}

.cl-saliency-map .el-icon-info {
  color: #6c7280;
}
.cl-saliency-map .el-checkbox__input {
  border-radius: 0px;
  height: 16px;
  width: 16px;
}
.cl-saliency-map .el-checkbox__input .el-checkbox__inner {
  border-radius: 0px;
}
.cl-saliency-map .el-checkbox__label {
  color: #333333 !important;
}
.cl-saliency-map .cl-saliency-map-table .table-data .el-table__body .pic-cell .cell {
  text-overflow: clip;
}
.cl-saliency-map .cl-saliency-map-table .table-data .el-table__body .pic-cell .cell img {
  height: 250px;
  width: 250px;
  object-fit: contain;
}
.cl-saliency-map .cl-saliency-map-table .table-data .el-table__body .canvas-cell img {
  cursor: pointer;
}
.cl-saliency-map .cl-saliency-map-table .table-data .el-table__body .cell {
  height: 270px;
  padding: 10px;
}

.table-tooltip {
  max-width: 650px;
}

.el-tooltip__popper .tooltip-container .cl-saliency-map-tip {
  padding: 10px;
}
.el-tooltip__popper .tooltip-container .cl-saliency-map-tip .tip-title {
  font-size: 16px;
  font-weight: bold;
}
.el-tooltip__popper .tooltip-container .cl-saliency-map-tip .tip-part {
  line-height: 20px;
  word-break: normal;
}
.el-tooltip__popper .tooltip-container .tag-tip .tip-item {
  margin-bottom: 10px;
  font-size: 12px;
  color: #575d6c;
  white-space: nowrap;
  display: flex;
  align-items: center;
}
.el-tooltip__popper .tooltip-container .tag-tip .tip-item .tip-icon {
  margin-right: 4px;
}
.el-tooltip__popper .tooltip-container .tag-tip .tip-item:last-of-type {
  margin-bottom: 0px;
}
.el-tooltip__popper .tooltip-container .tag-tip .tip-title {
  color: #333333;
}
</style>
<style scoped>
.cl-saliency-map {
  height: 100%;
  box-sizing: border-box;
  background-color: #ffffff;
  display: flex;
  flex-direction: column;
}
.cl-saliency-map .cl-saliency-map-title {
  display: flex;
  align-items: center;
  height: 56px;
  padding: 0 32px;
  font-size: 20px;
  color: #282b33;
  letter-spacing: -0.86px;
  font-weight: bold;
}
.cl-saliency-map .cl-saliency-map-title .el-icon-info {
  margin-left: 12px;
}
.cl-saliency-map .line-title {
  font-size: 14px;
  width: 100px;
  min-width: 100px;
  margin-right: 0px !important;
}
.cl-saliency-map .cl-saliency-map-methods {
  padding: 8px 32px 12px 32px;
}
.cl-saliency-map .cl-saliency-map-methods .methods-action {
  cursor: pointer;
  font-size: 14px;
  color: #00a5a7;
  text-decoration: underline;
}
.cl-saliency-map .cl-saliency-map-condition {
  padding: 0px 32px 21px 32px;
  height: 58px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e6ebf5;
}
.cl-saliency-map .cl-saliency-map-condition .condition-left {
  height: 100%;
  display: flex;
  align-items: center;
}
.cl-saliency-map .cl-saliency-map-condition .condition-left .condition-item {
  margin-right: 16px;
  height: 100%;
  display: flex;
  align-items: center;
}
.cl-saliency-map .cl-saliency-map-condition .condition-left .condition-item .condition-button {
  padding: 7px 15px;
  border-radius: 2px;
  border: 1px solid #00a5a7;
}
.cl-saliency-map .cl-saliency-map-condition .condition-left .condition-item .el-icon-info {
  margin-right: 4px;
  margin-left: 2px;
}
.cl-saliency-map .cl-saliency-map-condition .condition-left .search-select {
  width: 200px;
  height: 32px;
}
.cl-saliency-map .cl-saliency-map-condition .condition-right {
  display: flex;
  align-items: center;
}
.cl-saliency-map .cl-saliency-map-condition .condition-right .condition-item {
  margin-right: 24px;
  display: flex;
  align-items: center;
}
.cl-saliency-map .cl-saliency-map-condition .condition-right .condition-item .item-children {
  margin-right: 12px;
}
.cl-saliency-map .cl-saliency-map-condition .condition-right .condition-item:last-of-type {
  margin-right: 0px;
}
.cl-saliency-map .cl-saliency-map-table {
  padding: 21px 32px 0 32px;
  flex-grow: 1;
  overflow: hidden;
}
.cl-saliency-map .cl-saliency-map-table .table-nodata {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}
.cl-saliency-map .cl-saliency-map-table .table-nodata .nodata-text {
  margin-top: 16px;
  font-size: 16px;
}
.cl-saliency-map .cl-saliency-map-table .table-data {
  height: 100%;
}
.cl-saliency-map .cl-saliency-map-table .table-data .table-forecast-tag {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.cl-saliency-map .cl-saliency-map-table .table-data .table-forecast-tag .center {
  text-align: center;
}
.cl-saliency-map .cl-saliency-map-table .table-data .table-forecast-tag div,
.cl-saliency-map .cl-saliency-map-table .table-data .table-forecast-tag span {
  font-size: 12px;
}
.cl-saliency-map .cl-saliency-map-table .table-data .table-forecast-tag .tag-title-true {
  display: grid;
  grid-template-columns: 35% 35% 30%;
}
.cl-saliency-map .cl-saliency-map-table .table-data .table-forecast-tag .tag-title-true .first {
  padding-left: 12px;
}
.cl-saliency-map .cl-saliency-map-table .table-data .table-forecast-tag .tag-title-false {
  display: grid;
  grid-template-columns: 20% 40% 40%;
}
.cl-saliency-map .cl-saliency-map-table .table-data .table-forecast-tag .tag-content {
  flex-grow: 1;
  overflow-y: scroll;
}
.cl-saliency-map .cl-saliency-map-table .table-data .table-forecast-tag .tag-content::-webkit-scrollbar {
  width: 0px;
  height: 0px;
}
.cl-saliency-map .cl-saliency-map-table .table-data .table-forecast-tag .tag-content .tag-content-item {
  background-repeat: no-repeat;
  background-position: 2px 0px;
  box-sizing: border-box;
  cursor: pointer;
  height: 48px;
  border: 1px solid #d9ecff;
  background-color: #f5fbfb;
  border-radius: 3px;
  margin-bottom: 6px;
}
.cl-saliency-map .cl-saliency-map-table .table-data .table-forecast-tag .tag-content .tag-content-item .first {
  padding-left: 10px;
  background-color: rgba(0, 0, 0, 0) !important;
}
.cl-saliency-map .cl-saliency-map-table .table-data .table-forecast-tag .tag-content .tag-content-item .more-action {
  cursor: pointer;
  text-decoration: underline;
}
.cl-saliency-map .cl-saliency-map-table .table-data .table-forecast-tag .tag-content .tag-content-item .content-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cl-saliency-map .cl-saliency-map-table .table-data .table-forecast-tag .tag-content .tag-content-item-true {
  display: grid;
  grid-template-columns: 35% 35% 30%;
  align-items: center;
}
.cl-saliency-map .cl-saliency-map-table .table-data .table-forecast-tag .tag-content .tag-content-item-false {
  display: grid;
  grid-template-columns: 20% 40% 40%;
  align-items: center;
}
.cl-saliency-map .cl-saliency-map-table .table-data .table-forecast-tag .tag-content .tag-active {
  background-color: #00a5a7;
  color: #ffffff;
}
.cl-saliency-map .cl-saliency-map-table .table-data .table-forecast-tag .tag-content :hover {
  background-color: #00a5a7;
  color: #ffffff;
}
.cl-saliency-map .cl-saliency-map-table .table-data .table-forecast-tag .tag-content .tag-tp {
  background-image: url("../../assets/images/explain-tp.svg");
}
.cl-saliency-map .cl-saliency-map-table .table-data .table-forecast-tag .tag-content .tag-fn {
  background-image: url("../../assets/images/explain-fn.svg");
}
.cl-saliency-map .cl-saliency-map-table .table-data .table-forecast-tag .tag-content .tag-fp {
  background-image: url("../../assets/images/explain-fp.svg");
}
.cl-saliency-map .cl-saliency-map-table .table-data .table-forecast-tag .tag-content .tag-tn {
  background-image: url("../../assets/images/explain-tn.svg");
}
.cl-saliency-map .cl-saliency-map-pagination {
  padding: 0 32px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.detail-container {
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>

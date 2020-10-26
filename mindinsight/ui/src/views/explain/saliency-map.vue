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
                      <a :href="$t('explain.mainTipPartFour')" target="_blank">
                        {{$t('explain.mainTipPartFour')}}
                      </a>
                    </div>
                  </div>
                  <i class="el-icon-info"></i>
                </el-tooltip>
    </div>
    <!-- Explanation Method -->
    <div class="cl-saliency-map-methods">
      <div class="line-title methods-left">{{$t('explain.explainMethod')}}</div>
      <!-- Explainer Checkbox -->
      <div class="methods-right">
        <el-checkbox name="type"
                     v-for="explainer in allExplainers"
                     :key="explainer.label"
                     :label="explainer.label"
                     v-model="explainer.checked"
                     class="methods-item"></el-checkbox>
        <span class="methods-action"
              @click="goMetric">{{$t('explain.viewScore')}}</span>
      </div>
    </div>
    <!-- Parameters Fetch -->
    <div class="cl-saliency-map-condition">
      <div class="condition-left">
        <div class="condition-item line-title">{{ $t('explain.tag') }}</div>
        <!-- Truth Labels -->
        <div class="condition-item">
          <el-select v-model="selectedTruthLabels"
                     :placeholder="$t('public.select')"
                     multiple
                     filterable
                     collapse-tags>
            <el-option v-for="label in truthLabels"
                       :key="label"
                       :label="label"
                       :value="label"></el-option>
          </el-select>
        </div>
        <!-- Button -->
        <div class="condition-item">
          <el-button type="primary"
                     class="condition-button"
                     @click="fetch">{{ $t('explain.fetch') }}</el-button>
        </div>
        <div class="condition-item">
          {{ $t('explain.minConfidence') + $t('symbols.colon')}}{{minConfidence}}</div>
      </div>
      <div class="condition-right">
        <!-- Sorted Name -->
        <div class="condition-item">
          <span class="item-children">{{$t('explain.imgSort')}}</span>
          <el-select v-model="sortedName"
                      @change="sortedNameChange">
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
        <span class="nodata-text">
          {{ $t('public.dataLoading') }}
        </span>
      </div>
      <div class="table-data"
           v-else>
        <el-table :data="tableData"
                  border
                  :height="tableHeight"
                  :span-method="mergeTable">
          <!-- Original Picture Column-->
          <el-table-column :label="$t('explain.originalPicture')"
                            width="270"
                           class-name="pic-cell"
                           :resizable="false">
            <template slot-scope="scope">
              <img :src="getImgURL(scope.row.image)"/>
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
                            effect="light">
                  <div slot="content"
                       class="tooltip-container">
                    <div class="cl-saliency-map-tip tag-tip">
                      <div class="tip-left">
                        <i class="el-icon-info"></i>
                      </div>
                      <div class="tip-right">
                        <div class="tip-item tip-title">
                          {{$t('explain.forecastTagTip')}}
                        </div>
                        <div class="tip-item">
                          <img :src="require('@/assets/images/explain-tp.svg')"
                               alt="">
                          <img :src="require('@/assets/images/explain-fn.svg')"
                               alt="">
                          <img :src="require('@/assets/images/explain-fp.svg')"
                               alt="">
                          <img :src="require('@/assets/images/explain-tn.svg')"
                               alt="">
                        </div>
                        <div class="tip-item">{{$t('explain.TP')}}</div>
                        <div class="tip-item">{{$t('explain.FN')}}</div>
                        <div class="tip-item">{{$t('explain.FP')}}</div>
                        <div class="tip-item">{{$t('explain.TN')}}</div>
                      </div>
                    </div>
                  </div>
                  <i class="el-icon-info"></i>
                </el-tooltip>
              </span>
            </template>
            <template slot-scope="scope">
              <div class="table-forecast-tag" v-if="uncertaintyEnabled">
                <!-- Tag Title -->
                <div class="tag-title">
                  <div class="first">{{ $t('explain.tag') }}</div>
                  <div>{{ $t('explain.confidenceRange') }}</div>
                  <div class="center">{{ $t('explain.uncertainty') }}</div>
                </div>
                <!-- Tag content -->
                <div class="tag-content">
                  <div v-for="(tag, index) in scope.row.inferences"
                       :key="tag.label"
                       class="tag-content-item tag-content-item-true"
                       :class="{
                    'tag-active': index == scope.row.activeLabelIndex,
                    'tag-tp': tag.type == 'tp',
                    'tag-fn': tag.type == 'fn',
                    'tag-fp': tag.type == 'fp'
                  }"
                       @click="changeActiveLabel(scope.row, index)">
                    <div class="first">{{ tag.label }}</div>
                    <div>
                      <div>{{ tag.confidence.toFixed(3) }}</div>
                      <div>{{
                        Math.floor(tag.confidence_itl95[0] * 100) / 100 +
                          '-' +
                          Math.ceil(tag.confidence_itl95[1] * 100) / 100
                      }}</div>
                    </div>
                    <div class="center">
                      <span @click="showSimilarDialog(scope.row, tag)">
                        {{ tag.confidence_var.toFixed(2) }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              <div class="table-forecast-tag" v-else>
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
                        'tag-active': index == scope.row.activeLabelIndex,
                        'tag-tp': tag.type == 'tp',
                        'tag-fn': tag.type == 'fn',
                        'tag-fp': tag.type == 'fp'
                      }"
                      @click="changeActiveLabel(scope.row, index)">
                      <div></div>
                      <div>{{tag.label}}</div>
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
              <SuperpostImgComponent v-if="scope.row.inferences[scope.row.activeLabelIndex][explainer]"
                                     containerSize="250"
                                     :backgroundImg="getImgURL(scope.row.image)"
                                     :targetImg="getImgURL(scope.row.inferences[scope.row.activeLabelIndex][explainer])"
                                     :ifSuperpose="ifSuperpose"
                                     @click.native="showImgDiglog(scope.row, explainer)">
              </SuperpostImgComponent>
            </template>
          </el-table-column>
          <!-- None selected explainer Column-->
          <el-table-column v-if="selectedExplainers.length == 0"
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
                         :total="pageInfo.total"></el-pagination>
    </div>
    <!-- The dialog of nine similar pictures -->
    <el-dialog :title="$t('explain.ninePictures')"
               :visible.sync="similarDialog.visible"
               v-if="similarDialog.visible"
               top="50px"
               width="660px"
               @close="dialogClose">
      <div class="cl-saliency-map-dialog">
        <div class="dialog-text">
          <div class="dot"></div>
          <div class="text">{{ $t('explain.theMeaningOfBorderColor') }}</div>
        </div>
        <div class="dialog-text">
          <div class="dot"></div>
          <div class="text">{{ $t('explain.theMeaningOfEightPicture') }}</div>
        </div>
        <div class="dialog-label">
          {{$t('explain.tagAndLegend') + $t('symbols.colon')}}
          <span class="label-item">{{ similarDialog.label }}</span>
        </div>
        <div class="dialog-grid-container">
          <div class="dialog-grid"
               v-if="!similarDialog.loading">
            <div class="grid-item"
                 v-for="dialogItem in similarDialog.around"
                 :key="dialogItem.image"
                 :style="{'backgroundColor': dialogItem.color}">
              <img :src="getImgURL(dialogItem.image)" alt="">
            </div>
            <div class="grid-item grid-center">
              <img :src="getImgURL(similarDialog.center.image)" alt="">
            </div>
          </div>
          <div class="dialog-grid"
               v-else
               v-loading="true">
            <div class="grid-item"
                 v-for="index in 9"
                 :key="index">
            </div>
          </div>
        </div>
      </div>

    </el-dialog>
    <el-dialog :title="imageDetails.title"
               :visible.sync="imageDetails.imgShow"
               v-if="imageDetails.imgShow"
               top="100px"
               width="560px">
      <div class="detail-container">
        <SuperpostImgComponent containerSize="500"
                               :backgroundImg="imageDetails.imgUrl"
                               :targetImg="imageDetails.targetUrl"
                               :ifSuperpose="ifSuperpose">
        </SuperpostImgComponent>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import SuperpostImgComponent from '../../components/superposeImg';
import requestService from '../../services/request-service.js';
import {basePath} from '@/services/fetcher';

export default {
  components: {
    SuperpostImgComponent,
  },
  data() {
    return {
      trainID: this.$route.query.id, // The id of the train
      selectedExplainers: [], // The selected explainer methods
      allExplainers: [], // The list of all explainer method
      similarDialog: {
        visible: false,
        loading: true,
        around: [], // The eight img around
        center: null, // The center image
        label: null,
      }, // The object of similar dialog
      ifSuperpose: false, // If open the superpose function
      ifTableLoading: true, // If the table waiting for the data
      minConfidence: 0, // The min confidence
      tableData: null, // The table data
      selectedTruthLabels: [], // The selected truth labels
      truthLabels: [], // The list of all truth labels
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
      uncertaintyEnabled: null, // If open the uncertainty api
      tableHeight: 0, // The height of table to fixed the table header
      imageDetails: {
        title: '',
        imgUrl: '',
        targetUrl: '',
        imgShow: false,
      }, // The object of click canvas dialog
      queryParameters: null, // The complete parameters of query table information, have pagination information
      ifCalHeight: {
        mounted: false,
        serviced: false,
      }, // The Effectiveness of calculate the height of table, when the doms and the explainer checkboxs are ready
    };
  },
  computed: {
    // The basic parameters of query table information, have none pagination information
    baseQueryParameters() {
      return {
        train_id: decodeURIComponent(this.trainID),
        labels: this.selectedTruthLabels,
        explainer: this.selectedExplainers,
        sorted_name: this.sortedName,
      };
    },
  },
  methods: {
    /**
     * The logic of close the similar dialog
     */
    dialogClose() {
      this.similarDialog.visible = false;
      this.similarDialog.data = {};
      this.similarDialog.loading = true;
    },
    /**
     * The logic of open the similar dialog
     * @param {Object} row The table row object
     * @param {Object} tag The tag object iterate from the inferences in row object
     */
    showSimilarDialog(row, tag) {
      this.similarDialog.label = tag.label;
      const params = {
        train_id: decodeURIComponent(this.trainID),
        sample_id: row.id,
        label: tag.label,
        limit: 8,
      };
      requestService.querySimilarPic(params)
          .then(
              (res) => {
                this.similarDialog.center = res.data.query_sample;
                this.similarDialog.around = this.calBackgroundColor(res.data.similar_samples);
                this.similarDialog.loading = false;
              },
          );
      this.similarDialog.visible = true;
    },
    /**
     * The logic of calculate the background alpha of similar image
     * @param {Object} samples The list of similar image
     * @return {Object} The list of similar image with backgroundColor value
     */
    calBackgroundColor(samples) {
      // Do not have the Correspondence between image and alpha, just test
      for (let i = 0; i < samples.length; i++) {
        samples[i].color = `rgba(00, 165, 167, ${samples[i].confidence})`;
      }
      return samples;
    },
    /**
     * Get the complete url of image
     * @param {string} url The path url
     * @return {string} The complete url of image
     */
    getImgURL(url) {
      return `${basePath}${url}&date=${new Date().getTime()}`;
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
      this.queryParameters.offset = val- 1;
      this.queryPageInfo(this.queryParameters);
    },
    /**
     * The logic that is executed when the sorted name changed
     * @param {string} val The sorted name now
     */
    sortedNameChange(val) {
      if (val !== null) {
        this.queryParameters.sorted_name = val;
      } else {
        Reflect.deleteProperty(this.queryParameters, 'sorted_name');
      }
      this.pageInfo.currentPage = 1;
      this.queryParameters.offset = this.pageInfo.currentPage - 1;
      this.queryPageInfo(this.queryParameters);
    },
    /**
     * Request basic inforamtion of train
     * @param {Object} params Parameters of the request basic inforamtion of train interface
     * @return {Object}
     */
    queryTrainInfo(params) {
      return new Promise((resolve, reject) => {
        requestService.queryTrainInfo(params)
            .then(
                (res) => {
                  if (res && res.data) {
                    this.pageInfo.total = res.data.sample_count ? res.data.sample_count : 0;
                    if (res.data.saliency) {
                      this.minConfidence = res.data.saliency.min_confidence ? res.data.saliency.min_confidence : '--';
                      this.allExplainers = this.arrayToCheckBox(res.data.saliency.explainers);
                    }
                    if (res.data.classes) {
                      const truthLabels = [];
                      for (let i = 0; i < res.data.classes.length; i++) {
                        truthLabels.push(res.data.classes[i].label);
                      }
                      this.truthLabels = truthLabels;
                    }
                    if (res.data.uncertainty) {
                      this.uncertaintyEnabled = res.data.uncertainty.enabled ? true : false;
                    }
                  }
                  this.ifCalHeight.serviced = true; // The explainer checkboxs are ready
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
     * The complete logic of table update when any condiiton changed
     * @param {Object} params The main parameters
     * @param {Object} supParams The supplymentary parameters
     */
    updateTable(params, supParams) {
      const paramsTemp = JSON.parse(JSON.stringify(params));
      for (const attr in paramsTemp) {
        if ({}.hasOwnProperty.call(paramsTemp, attr)) {
          if (paramsTemp[attr] === null ||
              paramsTemp[attr] === undefined ||
              // Some array has no element in does not mean query when it empty
              (Array.isArray(paramsTemp[attr]) && paramsTemp[attr].length === 0 && attr !== 'explainer')) {
            Reflect.deleteProperty(paramsTemp, attr);
          }
        }
      };
      Object.assign(paramsTemp, supParams);
      this.queryPageInfo(paramsTemp);
    },
    /**
     * Request page table information
     * @param {Object} params Parameters of the request page information interface
     */
    queryPageInfo(params) {
      this.queryParameters = params;
      requestService.queryPageInfo(params)
          .then(
              (res) => {
                if (res && res.data && res.data.samples) {
                  if (this.minConfidence === '--') {
                    this.tableData = this.processTableData(res.data.samples, false);
                    this.pageInfo.total = res.data.count !== undefined ? res.data.count : 0;
                  } else {
                    this.tableData = this.processTableData(res.data.samples, this.minConfidence);
                    this.pageInfo.total = res.data.count !== undefined ? res.data.count : 0;
                  }
                } else {
                  this.pageInfo.total = 0;
                }
                this.ifError = false;
                this.ifTableLoading = false;
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
      for (let i =0; i < samples.length; i++) {
        samples[i].activeLabelIndex = 0;
        if (samples[i].inferences) {
          for (let j = 0; j < samples[i].inferences.length; j++) {
            if (typeof minConfidence === 'number' &&
                typeof samples[i].inferences[j].confidence === 'number') {
              // Model Inference Result
              const MIR = samples[i].inferences[j].confidence * 100 >= minConfidence * 100;
              let labelValid;
              // The label if valid, judged by whether it exists in the truth labels
              if (samples[i].labels && samples[i].inferences[j].label) {
                labelValid = samples[i].labels.indexOf(samples[i].inferences[j].label) >= 0;
              } else {
                labelValid = false;
              }
              let result = '';
              if (MIR === labelValid) {
                result += 't';
              } else {
                result += 'f';
              }
              if (MIR) {
                result += 'p';
              } else {
                result += 'n';
              }
              samples[i].inferences[j].type = result;
            } else {
              samples[i].inferences[j].type = 'none';
            }
            // Defined the attr{key: explainer, value: overlay} out the saliencies
            // Can provide some convenience for some table operation
            if (samples[i].inferences[j].saliency_maps) {
              const saliencies = samples[i].inferences[j].saliency_maps;
              for (let k = 0; k < saliencies.length; k++ ) {
                const explainer = saliencies[k].explainer;
                const overlay = saliencies[k].overlay;
                samples[i].inferences[j][explainer] = overlay;
              };
            };
          };
        };
      };
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
      if (arrayTemp.length === 0 || (typeof arrayTemp[0] !== 'string')) {
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
        };
      } else {
        // Do nothing
        return [1, 1];
      };
    },
    /**
     * Calculate the height of table to let the table header fixed
     */
    calTableHeight() {
      const table = document.getElementsByClassName('cl-saliency-map-table')[0];
      if (table !== undefined || table !== null) {
        this.$nextTick(() => {
          const height = table.clientHeight;
          this.tableHeight = height - 21;// The table container padding-top
        });
      };
      window.onresize = (() => {
        const height = table.clientHeight;
        this.tableHeight = height - 21;
      });
    },
    /**
     * Go to the metric page
     */
    goMetric() {
      this.$router.push({
        path: '/explain/xai-metric',
        query: {id: this.$route.query.id},
      });
    },
  },
  watch: {
    // The watcher of allExplainer to get the selectedExplainers
    allExplainers: {
      handler() {
        const selectedExplainers = [];
        for (let i = 0; i < this.allExplainers.length; i++) {
          if (this.allExplainers[i].checked) {
            selectedExplainers.push(this.allExplainers[i].label);
          }
        }
        this.selectedExplainers = selectedExplainers;
      },
      deep: true,
    },
    // The watcher of ifCalHeight to calculate the table height at the right time
    ifCalHeight: {
      handler() {
        if (this.ifCalHeight.serviced && this.ifCalHeight.mounted) {
          this.calTableHeight();
        }
      },
      deep: true,
    },
  },
  created() {
    const params = {
      train_id: decodeURIComponent(this.trainID),
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
              this.ifCalHeight.serviced = true;
              this.ifTableLoading = false;
            },
        )
        .catch((e) => {
          this.ifCalHeight.serviced = true;
          this.ifTableLoading = false;
        });
  },
  mounted() {
    this.ifCalHeight.mounted = true; // The doms are ready
    // Change the page title
    if (this.$route.query.id) {
      document.title = `${decodeURIComponent(this.$route.query.id)}-${this.$t(
          'explain.title',
      )}-MindInsight`;
    } else {
      document.title = `${this.$t('explain.title')}-MindInsight`;
    }
  },
  beforeDestroy() {
    window.onresize = null;
  },
};
</script>

<style lang="scss">
.cl-saliency-map {
  .el-icon-info {
    color: #6c7280;
  }
  .cl-saliency-map-table {
    .table-data {
      .el-table__body{
        .pic-cell{
          .cell{
            text-overflow: clip;
            & img{
              height: 250px;
              width: 250px;
              object-fit: contain;
            }
          }
        }
        .canvas-cell{
          & img {
            cursor: pointer;
          }
        }
        .cell{
          height: 270px;
          padding: 10px;
        }
      }
    }
  }
}
.el-tooltip__popper{
  .tooltip-container {
    .cl-saliency-map-tip{
      padding: 10px;
      .tip-title{
        font-size:16px;
        font-weight: bold;
      }
      .tip-part{
        line-height: 20px;
      }
    }
    .tag-tip {
      display: flex;
      .tip-left{
        height: 100%;
        margin-right: 8px;
        .el-icon-info{
          color: #6c7280;
        }
      }
      .tip-right{
        height: 100%;
        .tip-item{
          margin-bottom: 10px;
          font-size: 12px;
          color: #575D6C;
        }
        .tip-item:last-of-type{
          margin-bottom: 0px;
        }
        .tip-title{
          color: #333333;
        }
      }
    }
  }
}
</style>
<style lang="scss" scoped>
$horizontalPadding: 32px;
$titleHeight: 56px;
$titlePadding: 0 $horizontalPadding;
$methodsPadding: 8px $horizontalPadding 12px $horizontalPadding;
$methodsLineHeight: 19px;
$conditionHeight: 58px;
$conditionPadding: 0px $horizontalPadding 21px $horizontalPadding;
$tablePadding: 21px $horizontalPadding 0 $horizontalPadding;
$paginationHeight: 60px;
$paginationPadding: 0 $horizontalPadding;
$tagFontSize: 12px;
.cl-saliency-map {
  height: 100%;
  width: 100%;
  box-sizing: border-box;
  background-color: #ffffff;
  display: flex;
  flex-direction: column;
  .cl-saliency-map-title {
    display: flex;
    align-items: center;
    height: $titleHeight;
    padding: $titlePadding;
    font-size: 20px;
    color: #282b33;
    letter-spacing: -0.86px;
    font-weight: bold;
    .el-icon-info {
      margin-left: 12px;
    }
  }
  .line-title{
    font-size: 14px;
    width: 100px;
    min-width: 100px;
    margin-right: 0px !important;
  }
  .cl-saliency-map-methods {
    padding: $methodsPadding;
    display: flex;
    .methods-right {
      display: flex;
      flex-wrap: wrap;
      line-height: $methodsLineHeight;
      .methods-item{
        padding-bottom: 10px;
      }
      .methods-item:last-of-type {
        margin-right: 32px;
      }
      .methods-action {
        cursor: pointer;
        font-size: 14px;
        color: #00a5a7;
        text-decoration: underline;
      }
    }
  }
  .cl-saliency-map-condition {
    padding: $conditionPadding;
    height: $conditionHeight;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid #e6ebf5;
    .condition-left {
      height: 100%;
      display: flex;
      align-items: flex-start;
      .condition-item {
        margin-right: 16px;
        height: 100%;
        display: flex;
        align-items: center;
        .condition-button {
          padding: 7px 15px;
          border-radius: 2px;
          border: 1px solid #00a5a7;
        }
      }
    }
    .condition-right {
      display: flex;
      align-items: center;
      .condition-item {
        margin-right: 24px;
        display: flex;
        align-items: center;
        .item-children {
          margin-right: 12px;
        }
      }
      & .condition-item:last-of-type {
        margin-right: 0px;
      }
    }
  }
  .cl-saliency-map-table {
    padding: $tablePadding;
    flex-grow: 1;
    overflow: hidden;
    .table-nodata {
      height: 100%;
      width: 100%;
      display: flex;
      justify-content: center;
      align-items: center;
      flex-direction: column;
      .nodata-text{
        margin-top:16px;
        font-size:16px;
      }
    }
    .table-data {
      height: 100%;
      width: 100%;
      .table-forecast-tag {
        height: 100%;
        width: 100%;
        display: flex;
        flex-direction: column;
        .center {
          text-align: center;
        }
        & div, span {
          font-size: $tagFontSize;
        }
        .tag-title {
          display: grid;
          grid-template-columns: 35% 35% 30%;
          .first {
            padding-left: 12px;
          }
        }
        .tag-title-false{
          display: grid;
          grid-template-columns: 20% 40% 40%;
        }
        .tag-content {
          flex-grow: 1;
          overflow-y: scroll;
          &::-webkit-scrollbar {
            width: 0px;
            height: 0px;
          }
          .tag-content-item {
            background-repeat: no-repeat;
            background-position: 2px 0px;
            box-sizing: border-box;
            cursor: pointer;
            height: 48px;
            border: 1px solid #d9ecff;
            background-color: #f5fbfb;
            border-radius: 3px;
            margin-bottom: 6px;
            .first {
              padding-left: 10px;
              background-color: rgba(0,0,0,0) !important;
            }
            .more-action {
              color: #409eff;
              cursor: pointer;
              text-decoration: underline;
            }
          }
          .tag-content-item-true{
            display: grid;
            grid-template-columns: 35% 35% 30%;
            align-items: center;
          }
          .tag-content-item-false{
            display: grid;
            grid-template-columns: 20% 40% 40%;
            align-items: center;
          }
          .tag-active {
            background-color: #00a5a7;
            color: #ffffff;
          }
          & :hover {
            background-color: #00a5a7;
            color: #ffffff;
          }
          .tag-tp{
            background-image: url('../../assets/images/explain-tp.svg');
          }
          .tag-fn{
            background-image: url('../../assets/images/explain-fn.svg');
          }
          .tag-fp{
            background-image: url('../../assets/images/explain-fp.svg');
          }
          .tag-tn{
            background-image: url('../../assets/images/explain-tn.svg');
          }
        }
      }
    }
  }
  .cl-saliency-map-pagination {
    padding: $paginationPadding;
    height: $paginationHeight;
    display: flex;
    align-items: center;
    justify-content: flex-end;
  }
}
.cl-saliency-map-dialog {
  .dialog-text{
    display: flex;
    .text{
      line-height: 22px;
    }
    .dot{
      margin: 7px;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background-color: #00a5a7;
    }
  }
  .dialog-label {
    .label-item{
      font-size: 12px;
      display: inline-block;
      background-color: #F5FBFB;
      border: #dcdfe6 1px solid;
      border-radius: 3px;
      padding: 4px 10px;
    }
  }
  .dialog-grid-container {
    width: 620px;
    height: 620px;
    .dialog-loading {
      width: 100%;
      height: 100%;
    }
    .dialog-grid {
      width: 100%;
      height: 100%;
      display: grid;
      grid-template-columns: repeat(3, 200px);
      grid-template-rows: repeat(3, 200px);
      gap: 10px;
      .grid-item {
        height: 100%;
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        & img {
          object-fit: cover;
          width: 90%;
          height: 90%;
        }
      }
      .grid-center {
        background-color: rgba(00, 165, 167, 1);
        grid-column: 2;
        grid-row: 2;
      }
    }
  }
}
.detail-container {
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>

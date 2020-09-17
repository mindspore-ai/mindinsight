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
  <div class="cl-model-traceback">
    <div class="traceback-tab">
      <div class="traceback-tab-item item-active">{{$t("summaryManage.modelTraceback")}}</div>
      <div class="traceback-tab-item"
           @click="jumpToDataTraceback()">{{$t("summaryManage.dataTraceback")}}</div>
    </div>
    <div id="model-traceback-con">
      <div v-if="loading"
           class="no-data-page">
        <div class="no-data-img">
          <img :src="require('@/assets/images/nodata.png')"
               alt="" />
          <p class="no-data-text">{{$t("public.dataLoading")}}</p>
        </div>
      </div>

      <div class="cl-model-left"
           :class="{collapse:collapse}"
           v-show="!loading && !errorData">
        <div class="left-chart-container"
             v-show="!collapse && !errorData">
          <div class="left-title">
            <div class="title-style">{{$t('modelTraceback.optimizationObject')}}
            </div>
            <div class="pie-select-style">
              <el-select v-model="targetValue"
                         class="left-select"
                         @change="targetSelectChange()">
                <el-option v-for="item in targetOptions"
                           :key="item.value"
                           :label="item.label"
                           :value="item.value">
                </el-option>
              </el-select>
            </div>
          </div>
          <!-- pie chart -->
          <div class="pie-module-container">
            <div class="title-container">
              <div class="pie-title">{{$t('modelTraceback.targetDistribution')}}</div>
            </div>
            <div id="pie-chart">
            </div>
          </div>
          <!-- bar -->
          <div class="bar-module-container">
            <div class="bar-title-container">
              <div class="bar-title"> {{$t('modelTraceback.parameterImportance')}}</div>
              <div class="inline-block-set bar-select">
                <!-- Parameter importance drop-down box -->
                <el-select v-model="selectedBarArray"
                           multiple
                           collapse-tags
                           @change="selectedBarNameListChange"
                           :placeholder="$t('public.select')"
                           @focus="selectinputFocus('left')">
                  <div class="select-input-button">
                    <div class="select-inner-input">
                      <el-input v-model="barKeyWord"
                                @input="myfilter('left')"
                                :placeholder="$t('public.search')"></el-input>
                    </div>
                    <button type="text"
                            @click="barAllSelect"
                            class="select-all-button"
                            :class="[selectedAllBar ? 'checked-color' : 'button-text',
                            (baseOptions.length > searchOptions.length)||!canSelected.length ? 'btn-disabled' : '']"
                            :disabled="(baseOptions.length > searchOptions.length)||!canSelected.length">
                      {{$t('public.selectAll')}}
                    </button>
                    <button type="text"
                            @click="barDeselectAll"
                            class="deselect-all-button"
                            :class="[!selectedAllBar ? 'checked-color' : 'button-text',
                            (baseOptions.length > searchOptions.length)||!canSelected.length ? 'btn-disabled' : '']"
                            :disabled="(baseOptions.length > searchOptions.length)||!canSelected.length">
                      {{$t('public.deselectAll')}}
                    </button>
                  </div>
                  <el-option-group v-for="group in barNameList"
                                   :key="group.label"
                                   :label="group.label">
                    <el-option v-for="item in group.options"
                               :key="item.value"
                               :label="item.label"
                               :value="item.value"
                               :disabled="item.disabled||item.unselected"
                               :title="item.message ? item.message : item.disabled ?
                               $t('modelTraceback.mustExist') : ''">
                    </el-option>
                  </el-option-group>
                </el-select>
              </div>
            </div>
            <div id="bar-chart"></div>
          </div>
          <!-- scatter -->
          <div class="scatter-container">
            <div class="scatter-title-container">
              <div>
                {{$t('modelTraceback.optimizationTitle')}}
                <el-tooltip class="item"
                            effect="light"
                            placement="top-start">
                  <div slot="content"
                       class="tooltip-container">
                    {{$t('modelTraceback.targetTips')}}
                  </div>
                  <i class="el-icon-info"></i>
                </el-tooltip>
              </div>
              <div class="right-view">
                <div class="view-big"
                     @click="viewLargeImage"
                     :disabled="viewBigBtnDisabled"
                     :class="[viewBigBtnDisabled ? 'btn-disabled' : '']"
                     :title="$t('modelTraceback.viewBigImage')">
                </div>
              </div>
            </div>
            <div class="left-scatters-container">
              <Scatter ref="smallScatter"
                       :data="scatterChartData"
                       :yTitle="yTitle"
                       :xTitle="xTitle"
                       :tooltipsData="tooltipsData"
                       :showTooltip="false">
              </Scatter>
            </div>
          </div>
        </div>
        <div class="collapse-btn"
             :class="{collapse:collapse}"
             @click="collapseLeft()">
        </div>
      </div>
      <!-- Model traceability right column  -->
      <div class="cl-model-right"
           v-if="!loading"
           :class="{collapse:collapse}">
        <div class="top-area"
             v-show="!noData && showEchartPic && !loading">
          <div class="select-box"
               v-if="!noData &&
             (!summaryDirList || (summaryDirList && summaryDirList.length))">
            <div v-show="showTable && !noData"
                 class="select-container">
              <!-- multiple collapse-tags -->
              <div class="display-column"> {{$t('modelTraceback.displayColumn')}}</div>
              <div class="inline-block-set">
                <el-select v-model="selectArrayValue"
                           multiple
                           collapse-tags
                           @change="selectValueChange"
                           :placeholder="$t('public.select')"
                           @focus="selectinputFocus">
                  <div class="select-input-button">
                    <div class="select-inner-input">
                      <el-input v-model="keyWord"
                                @input="myfilter"
                                :placeholder="$t('public.search')"></el-input>
                    </div>
                    <button type="text"
                            @click="allSelect"
                            class="select-all-button"
                            :class="[selectCheckAll ? 'checked-color' : 'button-text',
                            rightAllOptions.length > showOptions.length ? 'btn-disabled' : '']"
                            :disabled="rightAllOptions.length > showOptions.length">
                      {{$t('public.selectAll')}}
                    </button>
                    <button type="text"
                            @click="deselectAll"
                            class="deselect-all-button"
                            :class="[!selectCheckAll ? 'checked-color' : 'button-text',
                            rightAllOptions.length > showOptions.length ? 'btn-disabled' : '']"
                            :disabled="rightAllOptions.length > showOptions.length">
                      {{$t('public.deselectAll')}}
                    </button>
                  </div>
                  <el-option-group v-for="group in checkOptions"
                                   :key="group.label"
                                   :label="group.label">
                    <el-option v-for="item in group.options"
                               :key="item.value"
                               :label="item.label"
                               :value="item.value"
                               :disabled="item.disabled"
                               :title="item.disabled ? $t('modelTraceback.mustExist') : ''">
                    </el-option>
                  </el-option-group>
                </el-select>
              </div>
              <div class="label-legend"
                   v-if="haveCustomizedParams">
                <div>[U]: {{$t('modelTraceback.userDefined')}}</div>
                <div>[M]: {{$t('modelTraceback.metric')}}</div>
              </div>
            </div>
          </div>
        </div>
        <div id="echart"
             v-show="!noData && showEchartPic && !loading">
        </div>
        <div class="btns-container"
             v-show="showTable && !noData">
          <el-button type="primary"
                     size="mini"
                     @click="showSelectedModelData"
                     :disabled="disabledFilterBtnModel"
                     class="disabled-btn-color"
                     :class="[!disabledFilterBtnModel ? 'abled-btn-color' : '']"
                     plain>{{$t('modelTraceback.showSelected')}}</el-button>
          <el-button type="primary"
                     size="mini"
                     @click="hideSelectedModelRows"
                     :disabled="disabledHideBtnModel"
                     class="disabled-btn-color"
                     :class="[!disabledHideBtnModel ? 'abled-btn-color' : '']"
                     plain>{{$t('modelTraceback.hideSelected')}}</el-button>
          <el-button type="primary"
                     size="mini"
                     class="custom-btn"
                     @click="showAllDatafun"
                     plain>
            {{ $t('modelTraceback.showAllData') }}
          </el-button>
        </div>
        <div class="table-container"
             v-show="showTable && !noData">
          <div class="disabled-checked"
               v-show="!table.data.length"></div>
          <el-table ref="table"
                    :data="table.data"
                    tooltip-effect="light"
                    height="calc(100% - 30px)"
                    @selection-change="selectionChange"
                    @sort-change="sortChange"
                    row-key="summary_dir">
            <el-table-column type="selection"
                             width="55"
                             :reserve-selection="true"
                             v-show="showTable && !noData">
            </el-table-column>

            <!--metric table column-->
            <el-table-column :label="$t('modelTraceback.metricLabel')"
                             align="center"
                             v-if="metricList.length">
              <el-table-column v-for="key in metricList"
                               :key="key"
                               :prop="key"
                               :label="table.columnOptions[key].label.substring(3)"
                               show-overflow-tooltip
                               min-width="120"
                               sortable="custom">
                <template slot="header"
                          slot-scope="scope">
                  <div class="custom-label"
                       :title="scope.column.label">
                    {{scope.column.label}}
                  </div>
                </template>
                <template slot-scope="scope">
                  <span>{{formatNumber(key,scope.row[key])}}</span>
                </template>
              </el-table-column>
            </el-table-column>

            <!--user Defined table column-->
            <el-table-column :label="$t('modelTraceback.userDefinedLabel')"
                             align="center"
                             v-if="userDefinedList.length">
              <el-table-column v-for="key in userDefinedList"
                               :key="key"
                               :prop="key"
                               :label="table.columnOptions[key].label.substring(3)"
                               show-overflow-tooltip
                               min-width="120"
                               sortable="custom">
                <template slot="header"
                          slot-scope="scope">
                  <div class="custom-label"
                       :title="scope.column.label">
                    {{scope.column.label}}
                  </div>
                </template>
                <template slot-scope="scope">
                  <span>{{formatNumber(key,scope.row[key])}}</span>
                </template>
              </el-table-column>
            </el-table-column>

            <!--hyper List table column-->
            <el-table-column :label="$t('modelTraceback.hyperLabel')"
                             align="center"
                             v-if="hyperList.length">
              <el-table-column v-for="key in hyperList"
                               :key="key"
                               :prop="key"
                               :label="table.columnOptions[key].label"
                               show-overflow-tooltip
                               min-width="154"
                               sortable="custom">
                <template slot="header"
                          slot-scope="scope">
                  <div class="custom-label"
                       :title="scope.column.label">
                    {{scope.column.label}}
                  </div>
                </template>
                <template slot-scope="scope">
                  <span>{{formatNumber(key, scope.row[key])}}</span>
                </template>
              </el-table-column>
            </el-table-column>
            <!--other column-->
            <el-table-column v-for="key in table.otherColumn"
                             :key="key"
                             :prop="key"
                             :label="table.columnOptions[key].label"
                             :fixed="table.columnOptions[key].label === text ? true : false"
                             show-overflow-tooltip
                             min-width="150"
                             sortable="custom">
              <template slot="header"
                        slot-scope="scope">
                <div class="custom-label"
                     :title="scope.column.label">
                  {{ scope.column.label }}
                </div>
              </template>
              <template slot-scope="scope">
                <a v-if="key === 'summary_dir'"
                   @click="jumpToTrainDashboard(scope.row[key])">{{ scope.row[key] }}</a>
                <span v-else>{{ formatNumber(key, scope.row[key]) }}</span>
              </template>
            </el-table-column>
            <!-- remark column -->
            <el-table-column fixed="right"
                             width="260">
              <template slot="header">
                <div>
                  <div class="label-text">{{$t('public.remark')}}</div>
                  <div class="remark-tip">{{$t('modelTraceback.remarkTips')}}</div>
                </div>
              </template>
              <template slot-scope="scope">
                <div class="edit-text-container"
                     v-show="scope.row.editShow">{{scope.row.remark}}</div>
                <div class="inline-block-set">
                  <i class="el-icon-edit"
                     @click="editRemarks(scope.row)"
                     v-show="scope.row.editShow"></i>
                  <el-input type="text"
                            v-model="scope.row.remark"
                            v-show="!scope.row.editShow"
                            :placeholder="$t('public.enter')"
                            class="remark-input-style"></el-input>
                  <i class="el-icon-check"
                     @click="saveRemarksValue(scope.row)"
                     v-show="!scope.row.editShow"></i>
                  <i class="el-icon-close"
                     @click="cancelRemarksValue(scope.row)"
                     v-show="!scope.row.editShow"></i>
                  <div class="validation-error"
                       v-show="scope.row.isError">
                    {{$t('modelTraceback.remarkValidation')}}
                  </div>
                </div>
              </template>
            </el-table-column>
            <!-- tag -->
            <el-table-column label="tag"
                             fixed="right"
                             prop="tag"
                             sortable="custom">
              <template slot-scope="scope">
                <div @click="showAllIcon(scope.row, scope, $event)"
                     class="tag-icon-container">
                  <img v-if="scope.row.tag"
                       :class="'img' + scope.$index"
                       :src="require('@/assets/images/icon' + scope.row.tag + '.svg')">
                  <img v-else
                       :class="'img' + scope.$index"
                       :src="require('@/assets/images/icon-down.svg')">
                </div>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-container">
            <el-pagination @current-change="pagination.pageChange"
                           :current-page="pagination.currentPage"
                           :page-size="pagination.pageSize"
                           :layout="pagination.layout"
                           :total="pagination.total">
            </el-pagination>
          </div>
        </div>
        <div v-if="noData"
             class="no-data-page">
          <div class="no-data-img"
               :class="{'set-height-class':(summaryDirList && !summaryDirList.length)}">
            <img :src="require('@/assets/images/nodata.png')"
                 alt />
            <p class="no-data-text"
               v-show="(!summaryDirList || (summaryDirList && summaryDirList.length)) &&
               (!hideTableIdList||(hideTableIdList&&!hideTableIdList.length))">
              {{ $t('public.noData') }}</p>
            <div v-show="(hideTableIdList && hideTableIdList.length) && !summaryDirList">
              <p class="no-data-text">{{ $t('modelTraceback.allHide') }}</p>
              <p class="no-data-text">
                <el-button type="primary"
                           size="mini"
                           class="custom-btn"
                           @click="showAllDatafun"
                           plain>
                  {{ $t('modelTraceback.showAllData') }}
                </el-button>
              </p>
            </div>
            <div v-show="summaryDirList && !summaryDirList.length">
              <p class="no-data-text">{{ $t('modelTraceback.noDataFound') }}</p>
              <p class="no-data-text">
                <el-button type="primary"
                           size="mini"
                           class="custom-btn"
                           @click="showAllDatafun"
                           plain>
                  {{ $t('modelTraceback.showAllData') }}
                </el-button>
              </p>
            </div>
          </div>
        </div>
      </div>
      <!-- tag dialog -->
      <div v-show="tagDialogShow"
           id="tag-dialog"
           class="icon-dialog">
        <div>
          <div class="icon-image-container">
            <div class="icon-image"
                 v-for="item in imageList"
                 :key="item.number"
                 :class="[tagScope.row && item.number === tagScope.row.tag ? 'icon-border':'']"
                 @click="iconValueChange(tagScope.row, item.number, $event)">
              <img :src="item.iconAdd">
            </div>
          </div>
          <div class="btn-container-margin">
            <div class="tag-button-container">
              <el-button type="primary"
                         size="mini"
                         class="custom-btn"
                         @click="iconChangeSave(tagScope)"
                         plain>
                {{$t('public.sure')}}
              </el-button>
            </div>
            <div class="tag-button-container">
              <el-button type="primary"
                         size="mini"
                         class="custom-btn"
                         @click="clearIcon(tagScope, $event)"
                         plain>
                {{$t('public.clear')}}
              </el-button>
            </div>
            <div class="tag-button-container">
              <el-button type="primary"
                         size="mini"
                         class="custom-btn"
                         @click="cancelChangeIcon(tagScope.row)"
                         plain>
                {{$t('public.cancel')}}
              </el-button>
            </div>
          </div>
        </div>
      </div>
      <!-- echart dialog -->
      <div v-show="echartDialogVisible">
        <el-dialog :title="$t('modelTraceback.optimizationTitle')"
                   :visible.sync="echartDialogVisible"
                   width="50%"
                   :close-on-click-modal="false"
                   class="echart-data-list">
          <div class="dialog-scatter">
            <Scatter ref="dialogScatter"
                     :data="largeScatterChartData"
                     :yTitle="yTitle"
                     :xTitle="xTitle"
                     :tooltipsData="tooltipsData"
                     :showTooltip="true">
            </Scatter>
          </div>
        </el-dialog>
      </div>
    </div>
  </div>
</template>
<script>
import RequestService from '../../services/request-service';
import CommonProperty from '@/common/common-property.js';
import Echarts from 'echarts';
import Scatter from '@/components/scatter';

export default {
  props: {},
  watch: {},
  data() {
    return {
      // left data
      searchOptions: [],
      baseOptions: [],
      // Expand and collapse the left column
      collapse: false,
      showLeftChart: null,
      // pie chart
      myPieChart: undefined,
      // bar chart
      myBarChart: undefined,
      // Check whether the big scatter icon can be clicked
      viewBigBtnDisabled: false,
      // Options that can be selected in the multiple selection drop-down box on the left
      canSelected: [],
      targetValue: '',
      targetOptions: [],
      targetLabel: '',
      targetData: [],
      scatterData: [],
      pieLegendData: [],
      pieSeriesData: [],
      barYAxisData: [],
      barSeriesData: [],
      scatterChartData: [],
      largeScatterChartData: [],
      // Scatter chart tips data
      tooltipsData: [],
      // The content of the bar graph drop-down box
      barNameList: [],
      // All values of the drop-down box initially saved
      baseSelectOptions: [],
      // Whether to select all the drop-down boxes of the histogram
      selectedAllBar: false,
      // Selected select bar name
      selectBarNameList: [],
      // input key word
      barKeyWord: '',
      // List of selected bars
      selectedBarArray: [],
      // List of all bars
      allBararr: [],
      yTitle: '',
      xTitle: '',
      // bar datazoom scroll bar settings
      barStart: 100,
      barEnd: 0,
      tooltipsBarData: [],
      echartDialogVisible: false,

      // right data
      rightAllOptions: [],
      showOptions: [],
      // Filter button disabled
      disabledFilterBtnModel: true,
      // Hide button disabled
      disabledHideBtnModel: true,
      // List of IDs that need to be hidden
      hideTableIdList: [],
      sortChangeTimer: null,
      tagDialogShow: false,
      errorData: true,
      tagScope: {},
      iconValue: 0,
      imageList: [],
      // Select all
      selectCheckAll: true,
      delayTime: 500,
      showEchartPic: true,
      beforeEditValue: '',
      keyWord: '',
      basearr: [],
      labelObj: {metric: '', userDefined: ''},
      userOptions: [],
      metricOptions: [],
      hyperOptions: [],
      otherTypeOptions: [],
      checkOptions: [],
      selectArrayValue: [],
      // metric list
      metricList: [],
      userDefinedList: [],
      hyperList: [],
      summaryList: [],
      table: {},
      summaryDirList: undefined,
      text: this.$t('modelTraceback.summaryPath'),
      keysOfStringValue: [], // All keys whose values are character strings
      keysOfIntValue: [], // All keys whose values are int
      keysOfMixed: [],
      keysOfListType: [],
      echart: {
        chart: null,
        allData: [],
        brushData: [],
        showData: [],
      },
      pagination: {
        currentPage: 1,
        pageSize: 8,
        total: 0,
        layout: 'total, prev, pager, next, jumper',
        pageChange: {},
      },
      chartFilter: {}, // chart filter condition
      tableFilter: {lineage_type: {in: ['model']}}, // table filter condition
      sortInfo: {},
      showTable: false,
      noData: false,
      loading: true,
      haveCustomizedParams: false,
      replaceStr: {
        metric: 'metric/',
        userDefined: 'user_defined/',
      },
      valueType: {
        int: 'int',
        str: 'str',
        mixed: 'mixed',
        list: 'list',
        category: 'category',
        model_size: 'model_size',
        dataset_mark: 'dataset_mark',
      },
      valueName: {
        userDefined: 'userDefined',
        metric: 'metric',
        UserDefined: 'UserDefined',
        Metric: 'Metric',
      },
      labelValue: {
        loss: 'loss',
        batch_size: 'batch_size',
        epoch: 'epoch',
        learning_rate: 'learning_rate',
      },
    };
  },
  computed: {},
  mounted() {
    this.setInitListValue();
    this.setTableTagImage();
    document.title = `${this.$t('summaryManage.modelTraceback')}-MindInsight`;
    document.addEventListener('click', this.blurFloat, true);
    this.$store.commit('setSelectedBarList', []);
    this.getStoreList();
    this.pagination.pageChange = (page) => {
      this.pagination.currentPage = page;
      this.queryLineagesData(false);
    };
    this.$nextTick(() => {
      this.init();
    });
  },
  methods: {
    // Set the image display of the tag
    setTableTagImage() {
      this.imageList = [];
      for (let i = 1; i <= 10; i++) {
        const obj = {};
        obj.number = i;
        obj.iconAdd = require('@/assets/images/icon' + obj.number + '.svg');
        this.imageList.push(obj);
      }
    },
    /** ***  left code***/
    /**
     * open or close left  column
     */
    collapseLeft() {
      this.collapse = !this.collapse;
      if (this.showLeftChart) {
        clearTimeout(this.showLeftChart);
        this.showLeftChart = null;
      }
      this.showLeftChart = setTimeout(() => {
        this.resizeChart();
      }, 50);
    },

    /**
     * Call the left side to optimize the target interface to obtain data
     * @param {Object} params
     */
    initLeftColumnData(params) {
      this.getTargetsData(params);
    },
    /**
     * Call the left side to optimize the target interface to obtain data
     * @param {Object} params
     */
    getTargetsData(params) {
      this.targetOptions = [];
      RequestService.queryTargetsData(params)
          .then(
              (resp) => {
                if (
                  resp &&
              resp.data &&
              resp.data.targets &&
              resp.data.targets.length
                ) {
                  this.targetData = JSON.parse(JSON.stringify(resp.data.targets));
                  this.scatterData = JSON.parse(JSON.stringify(resp.data));
                  let targetName = '';
                  for (let i = 0; i < this.targetData.length; i++) {
                    const obj = {};
                    targetName = this.targetData[i].name;
                    obj.value = targetName;
                    obj.label = targetName;
                    this.targetOptions.push(obj);
                  }
                  this.targetValue = this.targetData[0].name;
                  this.targetLabel = this.targetData[0].name;
                  this.setTargetsData(0);
                  this.$nextTick(() => {
                    setTimeout(() => {
                      this.setChartOfPie();
                      this.setChartOfBar();
                    }, this.delayTime);
                  });
                } else {
                  this.leftChartNoData();
                }
              },
              (error) => {
                this.leftChartNoData();
              },
          )
          .catch(() => {
            this.leftChartNoData();
          });
    },
    /**
     * No data on echart on the left
     */
    leftChartNoData() {
      this.viewBigBtnDisabled = true;
      this.targetValue = '';
      this.targetOptions = [];
      this.selectedBarArray = [];
      this.barNameList = [];
      this.baseSelectOptions = [];
      // Clear pie charts, bar chart and scatter charts
      if (this.myPieChart) {
        this.myPieChart.clear();
      }
      if (this.myBarChart) {
        this.myBarChart.clear();
      }
      if (this.$refs.smallScatter) {
        this.$refs.smallScatter.clearScatter();
      }
    },
    /**
     * Single selection drop-down box on the left
     */
    targetSelectChange() {
      const length = this.targetOptions.length;
      let index = 0;
      for (let i = 0; i < length; i++) {
        if (this.targetValue === this.targetOptions[i].value) {
          this.targetLabel = this.targetOptions[i].label;
          index = i;
        }
      }
      this.setTargetsData(index);
      this.$nextTick(() => {
        this.setChartOfPie();
        this.setChartOfBar();
      });
    },
    /**
     * The method of changing the value of the multi-select drop-down box of the histogram
     */
    selectedBarNameListChange() {
      // Setting the bar selection
      const list = [];
      this.baseSelectOptions.forEach((item) => {
        item.options.forEach((option) => {
          list.push(option.label);
        });
      });
      if (list.length > this.selectedBarArray.length) {
        this.selectedAllBar = false;
      } else {
        this.selectedAllBar = true;
      }
      this.selectedSetBarData();
    },
    // Select all bar options
    barAllSelect() {
      if (this.selectedAllBar) {
        return;
      }
      this.selectedBarArray = [];
      this.barNameList.forEach((item) => {
        item.options.forEach((option) => {
          if (!option.unselected) {
            this.selectedBarArray.push(option.label);
          }
        });
      });
      this.selectedAllBar = !this.selectedAllBar;
      this.selectedSetBarData();
    },

    // Bar unselect all
    barDeselectAll() {
      this.selectedBarArray = [];
      this.barNameList.forEach((item) => {
        item.options.forEach((option) => {
          if (option.disabled && !option.unselected) {
            this.selectedBarArray.push(option.label);
          }
        });
      });
      this.selectedAllBar = false;
      this.selectedSetBarData();
    },

    viewLargeImage() {
      if (this.scatterChartData.length && !this.viewBigBtnDisabled) {
        this.echartDialogVisible = true;
        this.$nextTick(() => {
          this.largeScatterChartData = this.scatterChartData;
          this.$refs.dialogScatter.resizeCallback();
        });
      }
    },

    sortBy(field) {
      return function(a, b) {
        return a[field] - b[field];
      };
    },
    setNumberType(value) {
      const num = 1000000;
      if (value < num) {
        return Math.round(value * Math.pow(10, 4)) / Math.pow(10, 4);
      } else {
        return value.toExponential(4);
      }
    },

    setTargetsData(index) {
      const pieHBuckets = this.targetData[index].buckets;
      this.pieLegendData = [];
      this.pieSeriesData = [];
      // data of pie
      for (let i = 0; i < pieHBuckets.length; i++) {
        const objData = {};
        let preNum = pieHBuckets[i][0];
        let numSum = undefined;
        preNum = Math.round(preNum * Math.pow(10, 4)) / Math.pow(10, 4);
        if (i < pieHBuckets.length - 1) {
          numSum =
            Math.round(pieHBuckets[i + 1][0] * Math.pow(10, 4)) /
            Math.pow(10, 4);
        } else {
          let nextNumber = pieHBuckets[i][1];
          nextNumber =
            Math.round(nextNumber * Math.pow(10, 4)) / Math.pow(10, 4);
          numSum = preNum + nextNumber;
          numSum = Math.round(numSum * Math.pow(10, 4)) / Math.pow(10, 4);
        }
        const minNegativeNum = -10000;
        const maxNegativeNum = -0.0001;
        const minPositiveNum = 0.0001;
        const maxPositiveNum = 10000;
        if (
          ((preNum > maxPositiveNum || preNum < minPositiveNum) &&
            preNum > 0) ||
          ((preNum < minNegativeNum || preNum > maxNegativeNum) && preNum < 0)
        ) {
          preNum = preNum.toExponential(2);
        }
        if (
          ((numSum > maxPositiveNum || numSum < minPositiveNum) &&
            numSum > 0) ||
          ((numSum < minNegativeNum || numSum > maxNegativeNum) && numSum < 0)
        ) {
          numSum = numSum.toExponential(2);
        }
        const numSumString = preNum + '~' + numSum;
        this.pieLegendData.push(numSumString);
        objData.value = pieHBuckets[i][2];
        objData.name = numSumString;
        this.pieSeriesData.push(objData);
      }
      this.setBarSelectOptionData(index);
    },

    setBarSelectOptionData(index) {
      const barHyper = [];
      const tempData = this.targetData[index].hyper_parameters;
      const unrecognizedParams = this.scatterData.metadata.unrecognized_params;
      let arrayTotal = [];
      if (unrecognizedParams && unrecognizedParams.length) {
        arrayTotal = unrecognizedParams.concat(tempData);
      } else {
        arrayTotal = tempData;
      }
      tempData.forEach((item) => {
        if (!item.unselected) {
          if (item.name.startsWith('[U]')) {
            barHyper.unshift(item);
          } else {
            barHyper.push(item);
          }
        }
      });
      barHyper.sort(this.sortBy('importance'));
      this.selectedBarArray = [];
      const mustSelectOptions = [];
      const otherListOptions = [];
      const selectBar = [];
      // Options that can be selected
      this.canSelected = [];
      arrayTotal.forEach((item) => {
        if (item.name.startsWith('[U]')) {
          if (!item.unselected) {
            this.canSelected.push(item);
            otherListOptions.unshift({
              value: item.name,
              label: item.name,
              disabled: item.unselected ? true : false,
              unselected: item.unselected ? item.unselected : undefined,
              message: item.reason_code
                ? this.$t('modelTraceback.reasonCode')[
                    item.reason_code.toString()
                ]
                : '',
            });
          } else {
            otherListOptions.push({
              value: item.name,
              label: item.name,
              disabled: item.unselected ? true : false,
              unselected: item.unselected ? item.unselected : undefined,
              message: item.reason_code
                ? this.$t('modelTraceback.reasonCode')[
                    item.reason_code.toString()
                ]
                : '',
            });
          }
        } else {
          if (!item.unselected) {
            selectBar.push(item.name);
            mustSelectOptions.unshift({
              value: item.name,
              label: item.name,
              disabled: true,
              unselected: item.unselected ? item.unselected : undefined,
              message: item.reason_code
                ? this.$t('modelTraceback.reasonCode')[
                    item.reason_code.toString()
                ]
                : '',
            });
          } else {
            mustSelectOptions.push({
              value: item.name,
              label: item.name,
              disabled: true,
              unselected: item.unselected ? item.unselected : undefined,
              message: item.reason_code
                ? this.$t('modelTraceback.reasonCode')[
                    item.reason_code.toString()
                ]
                : '',
            });
          }
        }
      });
      this.selectedBarArray = selectBar;
      this.barNameList = [];
      this.baseSelectOptions = [];
      const nameObjMust = {
        label: this.$t('modelTraceback.mustOptions'),
        options: mustSelectOptions,
      };
      const nameObjOther = {
        label: this.$t('modelTraceback.customOptions'),
        options: otherListOptions,
      };
      this.baseOptions = mustSelectOptions.concat(otherListOptions);
      this.searchOptions = this.baseOptions;
      // The displayed bar drop-down box content
      this.barNameList.push(nameObjMust, nameObjOther);
      // Save all the contents of the drop-down box
      this.baseSelectOptions.push(nameObjMust, nameObjOther);
      this.barYAxisData = [];
      this.barSeriesData = [];
      for (let i = 0; i < barHyper.length; i++) {
        const name = barHyper[i].name;
        let importanceValue = barHyper[i].importance;
        const smallNum = 0.0001;
        if (importanceValue < smallNum && importanceValue > 0) {
          importanceValue = importanceValue.toExponential(4);
        } else {
          importanceValue =
            Math.round(importanceValue * Math.pow(10, 4)) / Math.pow(10, 4);
        }
        if (!barHyper[i].name.startsWith('[U]')) {
          this.barYAxisData.push(name);
          this.barSeriesData.push(importanceValue);
        }
      }
      this.selectedAllBar =
        barHyper.length > this.barYAxisData.length ? false : true;
    },

    setChartOfPie() {
      if (!this.myPieChart) {
        this.myPieChart = Echarts.init(document.getElementById('pie-chart'));
      }
      const pieOption = {
        grid: {
          y2: 0,
          y: 0,
          containLabel: true,
        },
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/> {b} : {c} ({d}%)',
        },
        legend: {
          data: this.pieLegendData,
          selectedMode: false,
          icon: 'circle',
          itemWidth: 10,
          itemHeight: 10,
          itemGap: 10,
          orient: 'vertical',
          left: 'left',
          top: 'bottom',
        },
        color: ['#6c91fb', '#7cdc9f', '#fc8b5d', '#f1689b', '#ab74ff'],
        series: [
          {
            name: this.targetLabel,
            type: 'pie',
            radius: '65%',
            center: ['65%', '50%'],
            label: {
              normal: {
                show: false,
                positionL: 'inner',
              },
            },
            data: this.pieSeriesData,
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)',
              },
            },
          },
        ],
      };
      this.$nextTick(() => {
        this.myPieChart.setOption(pieOption);
      });
    },

    setChartOfBar() {
      if (!this.barSeriesData.length) {
        this.viewBigBtnDisabled = true;
      }
      if (this.barSeriesData.length === 0 && this.myBarChart) {
        this.myBarChart.clear();
        this.$refs.smallScatter.clearScatter();
        return;
      }
      this.viewBigBtnDisabled = false;
      this.xTitle = this.barYAxisData[this.barYAxisData.length - 1];
      // Set up a scatter chart
      this.setChartOfScatters();
      if (!this.myBarChart) {
        this.myBarChart = Echarts.init(document.getElementById('bar-chart'));
      }
      const barOption = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow',
          },
          formatter: (val) => {
            this.tooltipsBarData = val;
            const maxTooltipLen = 30;
            let name = val[0].name;
            name = name.replace(/</g, '< ');
            const breakCount = Math.ceil(name.length / maxTooltipLen);
            let str = '';
            for (let i = 0; i < breakCount; i++) {
              const temp = name.substr(i * maxTooltipLen, maxTooltipLen);
              str += str ? '<br/>' + temp : temp;
            }
            const res =
              '<p>' +
              str +
              '</p><p>' +
              this.$t('modelTraceback.parameterImportance') +
              ':' +
              '&nbsp;&nbsp;' +
              val[0].value +
              '</p>';
            return res;
          },
        },
        xAxis: [{type: 'value'}],
        yAxis: [
          {
            type: 'category',
            axisTick: {show: false},
            data: this.barYAxisData,
            axisLabel: {
              formatter: function(params) {
                const maxLength = 13;
                if (params.length > maxLength) {
                  return params.substring(0, maxLength) + '...';
                } else {
                  return params;
                }
              },
              textStyle: {
                color: (params) => {
                  const textColor =
                    params === this.xTitle ? '#cc5b58' : 'black';
                  return textColor;
                },
              },
            },
          },
        ],
        series: [
          {
            name: this.$t('modelTraceback.parameterImportance'),
            type: 'bar',
            barGap: 0,
            barWidth: 10,
            data: this.barSeriesData,
            itemStyle: {
              normal: {
                color: (params) => {
                  // Determine the selected name to change the color setting of the column
                  if (params.name === this.xTitle) {
                    return '#cc5b58';
                  } else {
                    return '#6c92fa';
                  }
                },
              },
            },
          },
        ],
        grid: {
          x: 88,
          y: 30,
          x2: 50,
          y2: 30,
        },
        dataZoom: [
          {
            show: this.barYAxisData.length > 15 ? true : false,
            type: 'slider',
            yAxisIndex: 0,
            width: '30px',
            start: 100, // The starting percentage of the data frame range
            end: this.barYAxisData.length > 15 ? 40 : 0, // The end percentage of the data frame range
            showDetail: false,
          },
        ],
      };
      this.barEnd = this.barYAxisData.length > 15 ? 40 : 0;
      this.barStart = 100;
      this.$nextTick(() => {
        this.myBarChart.setOption(barOption);
      });
      this.myBarChart.on('datazoom', (params) => {
        this.barStart = params.start;
        this.barEnd = params.end;
      });
      this.myBarChart.getZr().on('click', (params) => {
        this.xTitle = this.tooltipsBarData[0].name;
        barOption.dataZoom = [
          {
            show: this.barYAxisData.length > 15 ? true : false,
            type: 'slider',
            yAxisIndex: 0,
            width: '30px',
            start: this.barStart,
            end: this.barEnd,
          },
        ];
        barOption.yAxis = [
          {
            type: 'category',
            axisTick: {show: false},
            data: this.barYAxisData,
          },
        ];
        barOption.series = [
          {
            type: 'bar',
            barWidth: 10,
            data: this.barSeriesData,
            itemStyle: {
              normal: {
                color: (params) => {
                  // Determine the selected name to change the color setting of the column
                  if (params.name === this.xTitle) {
                    return '#cc5b58';
                  } else {
                    return '#6c92fa';
                  }
                },
              },
            },
          },
        ];
        this.$nextTick(() => {
          this.myBarChart.setOption(barOption);
        });
        // Draw a scatter chart after click
        this.setChartOfScatters();
      });
    },

    /**
     * set data of scatters echart
     */
    setChartOfScatters() {
      this.yTitle = this.targetLabel;
      let xvalue = [];
      let yvalue = [];
      this.tooltipsData = [];
      const hyper = this.scatterData.metadata.possible_hyper_parameters;
      for (let m = 0; m < hyper.length; m++) {
        if (hyper[m].name === this.xTitle) {
          xvalue = hyper[m].data;
        }
      }
      for (let k = 0; k < this.scatterData.targets.length; k++) {
        if (this.scatterData.targets[k].name === this.yTitle) {
          yvalue = this.scatterData.targets[k].data;
        }
      }
      const arrayTemp = [];
      for (let i = 0; i < xvalue.length; i++) {
        if ((xvalue[i] || xvalue[i] === 0) && (yvalue[i] || yvalue[i] === 0)) {
          arrayTemp.push([xvalue[i], yvalue[i]]);
          const obj = {train_id: this.scatterData.metadata['train_ids'][i]};
          obj[this.xTitle] = xvalue[i];
          obj[this.yTitle] = yvalue[i];
          this.tooltipsData.push(obj);
        }
      }
      this.scatterChartData = arrayTemp;
    },

    /** ***********right column*********** **/
    /**
     * Initialization
     */
    init() {
      this.table = {
        columnOptions: {
          train_dataset_path: {
            label: this.$t('modelTraceback.trainSetPath'),
            required: true,
          },
          test_dataset_path: {
            label: this.$t('modelTraceback.testSetPath'),
            required: true,
          },
          loss: {
            label: this.labelValue.loss,
            required: true,
          },
          network: {
            label: this.$t('modelTraceback.network'),
            required: true,
          },
          optimizer: {
            label: this.$t('modelTraceback.optimizer'),
            required: true,
          },
          train_dataset_count: {
            label: this.$t('modelTraceback.trainingSampleNum'),
            required: false,
          },
          test_dataset_count: {
            label: this.$t('modelTraceback.testSampleNum'),
            required: false,
          },
          learning_rate: {
            label: this.$t('modelTraceback.learningRate'),
            required: false,
          },
          epoch: {
            label: this.labelValue.epoch,
            required: false,
          },
          batch_size: {
            label: this.labelValue.batch_size,
            required: false,
          },
          device_num: {
            label: this.$t('modelTraceback.deviceNum'),
            required: false,
          },
          model_size: {
            label: this.$t('modelTraceback.modelSize'),
            required: false,
          },
          loss_function: {
            label: this.$t('modelTraceback.lossFunc'),
            required: false,
          },
        }, // All options of the column in the table
        otherColumn: [], // Table Column
        mandatoryColumn: [], // Mandatory Table Column
        optionalColumn: [], // Optional Table Column
        data: [],
        // no checked list
        optionsNotInCheckbox: [
          'summary_dir',
          'train_dataset_path',
          'test_dataset_path',
        ],
        optionsNotInEchart: [
          'summary_dir',
          'train_dataset_path',
          'test_dataset_path',
        ],
        optionsNotInTable: ['dataset_mark'],
        selectedColumn: [],
        selectAll: false, // Whether to select all columns
        indeterminate: false,
      };
      this.keysOfMixed = [];
      this.keysOfListType = [];

      this.userOptions = [];
      this.metricOptions = [];
      // metric list
      this.metricList = [];
      // User-defined list
      this.userDefinedList = [];
      // hyper list
      this.hyperList = [];
      this.summaryList = [];
      this.hyperOptions = [];
      this.otherTypeOptions = [];
      this.checkOptions = [];
      this.basearr = [];
      this.selectArrayValue = [];
      this.queryLineagesData(true);
    },

    /**
     * Querying All Model Version Information
     * @param {Boolean} allData Indicates whether to query all data
     */
    queryLineagesData(allData) {
      const params = {
        body: {},
      };
      const tempParam = {
        sorted_name: this.sortInfo.sorted_name,
        sorted_type: this.sortInfo.sorted_type,
      };
      // List id to be hidden
      this.hideTableIdList = this.$store.state.hideTableIdList;
      this.summaryDirList = this.$store.state.summaryDirList;
      // Need to pass in the request parameters of the hidden list id
      if (this.summaryDirList || this.hideTableIdList) {
        this.tableFilter.summary_dir = {
          in: this.summaryDirList,
          not_in: this.hideTableIdList,
        };
      } else {
        this.tableFilter.summary_dir = undefined;
      }

      if (!allData) {
        tempParam.limit = this.pagination.pageSize;
        tempParam.offset = this.pagination.currentPage - 1;
        params.body = Object.assign(
            params.body,
            this.chartFilter,
            tempParam,
            this.tableFilter,
        );
      } else {
        params.body = Object.assign(params.body, this.tableFilter);
      }
      // 1.Retrieve the data interface request in the left column (non-table page turning)
      if (allData) {
        this.initLeftColumnData(params);
      }
      RequestService.queryLineagesData(params)
          .then(
              (res) => {
                this.loading = false;
                if (res && res.data && res.data.object) {
                  this.errorData = false;
                  const listTemp = this.setDataOfModel(res.data.object);
                  const list = JSON.parse(JSON.stringify(listTemp));
                  if (allData) {
                    this.setInitListValue();
                    let customized = {};
                    if (res.data.customized) {
                      customized = JSON.parse(JSON.stringify(res.data.customized));
                      const customizedKeys = Object.keys(customized);
                      if (customizedKeys.length) {
                        customizedKeys.forEach((i) => {
                          if (customized[i].type === this.valueType.int) {
                            this.keysOfIntValue.push(i);
                          } else if (customized[i].type === this.valueType.str) {
                            this.keysOfStringValue.push(i);
                          } else if (customized[i].type === this.valueType.mixed) {
                            // list of type mixed
                            this.keysOfMixed.push(i);
                            this.keysOfStringValue.push(i);
                          } else if (customized[i].type === this.valueType.list) {
                            this.keysOfListType.push(i);
                            this.keysOfStringValue.push(i);
                          }
                          if (i.startsWith(this.replaceStr.userDefined)) {
                            this.labelObj.userDefined = this.valueName.userDefined;
                            customized[i].label = customized[i].label.replace(
                                this.replaceStr.userDefined,
                                '[U]',
                            );
                            const userDefinedObject = {value: '', label: ''};
                            userDefinedObject.value = customized[i].label;
                            userDefinedObject.label = customized[i].label;
                            this.userOptions.push(userDefinedObject);
                          } else if (i.startsWith(this.replaceStr.metric)) {
                            customized[i].label = customized[i].label.replace(
                                this.replaceStr.metric,
                                '[M]',
                            );
                            this.labelObj.metric = this.valueName.metric;
                            const metricObject = {value: '', label: ''};
                            metricObject.value = customized[i].label;
                            metricObject.label = customized[i].label;
                            metricObject.disabled = true;
                            this.metricOptions.push(metricObject);
                          }
                        });
                        this.haveCustomizedParams = true;
                      }
                      this.checkOptions = [
                        {
                          label: '',
                          options: [
                            {
                              value: this.$t('modelTraceback.dataProcess'),
                              label: this.$t('modelTraceback.dataProcess'),
                              disabled: true,
                            },
                          ],
                        },
                      ];
                      this.basearr = [
                        {
                          label: '',
                          options: [
                            {
                              value: this.$t('modelTraceback.dataProcess'),
                              label: this.$t('modelTraceback.dataProcess'),
                              disabled: true,
                            },
                          ],
                        },
                      ];
                      if (this.labelObj.metric) {
                        const metricTemp = {
                          label: this.valueName.Metric,
                          options: this.metricOptions,
                        };
                        this.checkOptions.push(metricTemp);
                        this.basearr.push(metricTemp);
                      }
                      if (this.labelObj.userDefined) {
                        const userTemp = {
                          label: this.valueName.UserDefined,
                          options: this.userOptions,
                        };
                        this.checkOptions.push(userTemp);
                        this.basearr.push(userTemp);
                      }
                      Object.keys(this.table.columnOptions).forEach((item) => {
                        if (
                          item !== this.labelValue.epoch &&
                      item !== this.labelValue.learning_rate &&
                      item !== this.labelValue.batch_size
                        ) {
                          const haveItem = this.table.optionsNotInCheckbox.includes(
                              item,
                          );
                          if (!haveItem) {
                            const otherType = {value: '', label: ''};
                            otherType.value = this.table.columnOptions[item].label;
                            otherType.label = this.table.columnOptions[item].label;
                            if (
                              otherType.value === this.labelValue.loss ||
                          otherType.value ===
                            this.$t('modelTraceback.network') ||
                          otherType.value ===
                            this.$t('modelTraceback.optimizer')
                            ) {
                              otherType.disabled = true;
                            }
                            this.otherTypeOptions.push(otherType);
                          }
                        } else {
                          const hyperObject = {value: '', label: ''};
                          hyperObject.value = this.table.columnOptions[item].label;
                          hyperObject.label = this.table.columnOptions[item].label;
                          this.hyperOptions.push(hyperObject);
                        }
                      });
                      if (this.hyperOptions.length) {
                        const hyperTemp = {
                          label: this.$t('modelTraceback.hyperLabel'),
                          options: this.hyperOptions,
                        };
                        this.checkOptions.push(hyperTemp);
                        this.basearr.push(hyperTemp);
                      }
                      if (this.otherTypeOptions.length) {
                        const otherTemp = {
                          label: this.$t('modelTraceback.otherLabel'),
                          options: this.otherTypeOptions,
                        };
                        this.checkOptions.push(otherTemp);
                        this.basearr.push(otherTemp);
                      }
                    }
                    let tempOptions = [];
                    this.checkOptions.forEach((item) => {
                      tempOptions = tempOptions.concat(item.options);
                      item.options.forEach((option) => {
                        this.selectArrayValue.push(option.label);
                      });
                    });
                    this.showOptions = tempOptions;
                    // select all options
                    this.rightAllOptions = tempOptions;
                    this.table.columnOptions = Object.assign(
                        {
                          summary_dir: {
                            label: this.$t('modelTraceback.summaryPath'),
                            required: true,
                          },
                          dataset_mark: {
                            label: this.$t('modelTraceback.dataProcess'),
                            required: true,
                          },
                        },
                        customized,
                        this.table.columnOptions,
                    );
                    this.$store.commit('customizedColumnOptions', customized);

                    this.noData = !res.data.object.length;
                    this.showEchartPic = !!res.data.object.length;
                    this.echart.allData = list;
                    this.echart.brushData = list;
                    this.echart.showData = this.echart.brushData;
                    Object.keys(this.table.columnOptions).forEach((i) => {
                      this.table.columnOptions[i].selected = true;
                      const flag = list.some((val) => {
                        return val[i] || val[i] === 0;
                      });
                      if (!flag) {
                        let index = this.table.optionsNotInCheckbox.indexOf(i);
                        if (index >= 0) {
                          this.table.optionsNotInCheckbox.splice(index, 1);
                        }
                        index = this.table.optionsNotInEchart.indexOf(i);
                        if (index >= 0) {
                          this.table.optionsNotInEchart.splice(index, 1);
                        }
                        index = this.table.optionsNotInTable.indexOf(i);
                        if (index >= 0) {
                          this.table.optionsNotInTable.splice(index, 1);
                        }

                        delete this.table.columnOptions[i];
                      }
                    });
                    this.initColumm();
                    this.$nextTick(() => {
                      this.resizeChart();
                      this.initChart();
                    });

                    const tempList = list.slice(0, this.pagination.pageSize);
                    this.table.data = tempList;
                  } else {
                    const tempList = list.slice(0, this.pagination.pageSize);
                    this.table.data = tempList;
                  }

                  this.pagination.total = res.data.count || 0;
                } else {
                  this.errorData = true;
                  this.noData = allData;
                  this.showEchartPic = !allData;
                }
              },
              (error) => {
                this.errorData = true;
                this.loading = false;
                if (allData) {
                  this.noData = allData;
                  this.showEchartPic = !allData;
                }
              },
          )
          .catch(() => {
            this.errorData = true;
            this.loading = false;
            this.noData = true;
          });
    },
    /**
     * Selected data in the table
     * @param {Array} data
     * @return {Array}
     */
    setDataOfModel(data = []) {
      const modelLineageList = [];
      data.forEach((item) => {
        if (item.model_lineage) {
          item.model_lineage.editShow = true;
          item.model_lineage.isError = false;
          item.model_lineage.summary_dir = item.summary_dir;
          item.model_lineage.remark = item.added_info.remark
            ? item.added_info.remark
            : '';
          item.model_lineage.tag = item.added_info.tag
            ? item.added_info.tag
            : 0;
          const modelData = JSON.parse(JSON.stringify(item.model_lineage));
          const byteNum = 1024;
          modelData.model_size = parseFloat(
              ((modelData.model_size || 0) / byteNum / byteNum).toFixed(2),
          );
          const keys = Object.keys(modelData.metric || {});
          if (keys.length) {
            keys.forEach((key) => {
              if (modelData.metric[key] || modelData.metric[key] === 0) {
                const temp = this.replaceStr.metric + key;
                modelData[temp] = modelData.metric[key];
              }
            });
            delete modelData.metric;
          }
          const udkeys = Object.keys(modelData.user_defined || {});
          if (udkeys.length) {
            udkeys.forEach((key) => {
              if (
                modelData.user_defined[key] ||
                modelData.user_defined[key] === 0
              ) {
                const temp = this.replaceStr.userDefined + key;
                modelData[temp] = modelData.user_defined[key];
              }
            });
            delete modelData.user_defined;
          }
          modelLineageList.push(modelData);
        }
      });
      return modelLineageList;
    },
    setInitListValue() {
      this.keysOfStringValue = [
        'summary_dir',
        'network',
        'optimizer',
        'loss_function',
        'train_dataset_path',
        'test_dataset_path',
        'dataset_mark',
      ]; // All keys whose values are character strings
      this.keysOfIntValue = [
        'train_dataset_count',
        'test_dataset_count',
        'epoch',
        'batch_size',
        'device_num',
      ]; // All keys whose values are int
      this.keysOfMixed = [];
      this.keysOfListType = [];
    },
    /**
     * Column initialization
     */
    initColumm() {
      this.metricList = [];
      this.userDefinedList = [];
      // hyper list
      this.hyperList = [];
      this.summaryList = [];
      this.table.mandatoryColumn = Object.keys(this.table.columnOptions).filter(
          (i) => {
            return this.table.columnOptions[i].required;
          },
      );
      this.table.optionalColumn = Object.keys(this.table.columnOptions).filter(
          (i) => {
            return !this.table.columnOptions[i].required;
          },
      );
      const columnList = Object.keys(this.table.columnOptions).filter((i) => {
        return (
          !this.table.optionsNotInTable.includes(i) &&
          this.table.columnOptions[i].selected
        );
      });
      const metricArray = [];
      const userDefinedArray = [];
      const columnArray = [];
      const hyperArray = [];
      columnList.forEach((item) => {
        if (item.indexOf('metric/') === 0) {
          metricArray.push(item);
        } else if (item.indexOf('user_defined/') === 0) {
          userDefinedArray.push(item);
        } else if (
          item === this.labelValue.epoch ||
          item === this.labelValue.batch_size ||
          item === this.labelValue.learning_rate
        ) {
          hyperArray.push(item);
        } else {
          columnArray.push(item);
        }
      });
      this.showTable = true;
      this.table.otherColumn = columnArray;
      this.metricList = metricArray;
      this.userDefinedList = userDefinedArray;
      // hyper list
      this.hyperList = hyperArray;

      this.table.selectedColumn = this.table.optionalColumn;
      this.table.selectAll = true;
      this.showTable = true;
      this.$nextTick(() => {
        this.$refs.table.doLayout();
      });
    },

    /**
     * Initializing the Eechart
     */
    initChart() {
      const chartAxis = Object.keys(this.table.columnOptions).filter((i) => {
        return (
          this.table.columnOptions[i].selected &&
          !this.table.optionsNotInEchart.includes(i)
        );
      });
      const data = [];
      this.echart.showData.forEach((i, index) => {
        let item = {};
        item = {
          lineStyle: {
            normal: {
              color: CommonProperty.commonColorArr[index % 10],
            },
          },
          value: [],
        };

        chartAxis.forEach((key) => {
          if (
            (i[key] || i[key] === 0) &&
            this.keysOfMixed &&
            this.keysOfMixed.length &&
            this.keysOfMixed.includes(key)
          ) {
            item.value.push(i[key].toString());
          } else {
            item.value.push(i[key]);
          }
        });
        data.push(item);
      });

      const parallelAxis = [];
      chartAxis.forEach((key, index) => {
        const obj = {dim: index, scale: true, id: key};
        obj.name = this.table.columnOptions[key].label;
        if (this.keysOfStringValue.includes(key)) {
          const values = {};
          this.echart.showData.forEach((i) => {
            if (i[key] || i[key] === 0) {
              values[i[key].toString()] = i[key].toString();
            }
          });
          obj.type = this.valueType.category;
          obj.data = Object.keys(values);
          if (key === this.valueType.dataset_mark) {
            obj.axisLabel = {
              show: false,
            };
          } else {
            obj.axisLabel = {
              formatter: function(val) {
                const strs = val.split('');
                let str = '';
                if (val.length > 100) {
                  return val.substring(0, 12) + '...';
                } else {
                  if (chartAxis.length < 10) {
                    for (let i = 0, s = ''; (s = strs[i++]); ) {
                      str += s;
                      if (!(i % 16)) {
                        str += '\n';
                      }
                    }
                  } else {
                    for (let i = 0, s = ''; (s = strs[i++]); ) {
                      str += s;
                      if (!(i % 12)) {
                        str += '\n';
                      }
                    }
                  }
                  return str;
                }
              },
            };
          }
        }
        if (this.keysOfIntValue.includes(key)) {
          obj.minInterval = 1;
        }
        parallelAxis.push(obj);
      });

      const echartOption = {
        backgroundColor: 'white',
        parallelAxis: parallelAxis,
        tooltip: {
          trigger: 'axis',
        },
        parallel: {
          top: 25,
          left: 70,
          right: 100,
          bottom: 10,
          parallelAxisDefault: {
            type: 'value',
            nameLocation: 'end',
            nameGap: 6,
            nameTextStyle: {
              color: '#000000',
              fontSize: 14,
            },
            axisLine: {
              lineStyle: {
                color: '#6D7278',
              },
            },
            axisTick: {
              lineStyle: {
                color: '#6D7278',
              },
            },
            axisLabel: {
              textStyle: {
                fontSize: 10,
                color: '#6C7280',
              },
            },
            areaSelectStyle: {
              width: 40,
            },
            tooltip: {
              show: true,
            },
            realtime: false,
          },
        },
        series: {
          type: 'parallel',
          lineStyle: {
            normal: {
              width: 1,
              opacity: 1,
            },
          },
          data: data,
        },
      };

      if (this.echart.chart) {
        this.echart.chart.off('axisareaselected', null);
        window.removeEventListener('resize', this.resizeChart, false);
      } else {
        this.echart.chart = Echarts.init(document.querySelector('#echart'));
      }
      this.echart.chart.setOption(echartOption, true);
      window.addEventListener('resize', this.resizeChart, false);
      this.chartEventsListen(parallelAxis);
    },
    /**
     * Model traceability parallel coordinate system echart frame selection operation monitoring
     * @param {Object} parallelAxis
     */
    chartEventsListen(parallelAxis) {
      this.echart.chart.on('axisareaselected', (params) => {
        const key = params.parallelAxisId;
        if (
          (this.keysOfMixed &&
            this.keysOfMixed.length &&
            this.keysOfMixed.includes(key)) ||
          this.keysOfListType.includes(key)
        ) {
          if (this.keysOfListType.includes(key)) {
            this.$message.error(this.$t('modelTraceback.notSupportSelected'));
          } else {
            this.$message.error(this.$t('modelTraceback.mixedItemMessage'));
          }
          this.$nextTick(() => {
            this.initChart();
          });
          return;
        }
        const list = this.$store.state.selectedBarList || [];
        const selectedAxisId = params.parallelAxisId;
        if (list.length) {
          list.forEach((item, index) => {
            if (item === selectedAxisId) {
              list.splice(index, 1);
            }
          });
        }
        list.push(selectedAxisId);
        this.$store.commit('setSelectedBarList', list);

        let range = params.intervals[0] || [];
        const [axisData] = parallelAxis.filter((i) => {
          return i.id === key;
        });
        const lineLength = 2;
        if (axisData && range.length === lineLength) {
          if (axisData && axisData.id === this.valueType.model_size) {
            const byteNum = 1024;
            range = [
              parseInt(range[0] * byteNum * byteNum, 0),
              parseInt(range[1] * byteNum * byteNum, 0),
            ];
          }
          if (axisData.type === this.valueType.category) {
            const rangeData = {};
            for (let i = range[0]; i <= range[1]; i++) {
              rangeData[axisData.data[i]] = axisData.data[i];
            }
            const rangeDataKey = Object.keys(rangeData);
            this.chartFilter[key] = {
              in: rangeDataKey,
            };
          } else {
            if (this.keysOfIntValue.includes(key)) {
              range[1] = Math.floor(range[1]);
              range[0] = Math.ceil(range[0]);
            }
            this.chartFilter[key] = {
              le: range[1],
              ge: range[0],
            };
          }
          const filterParams = {};
          filterParams.body = Object.assign(
              {},
              this.chartFilter,
              this.tableFilter,
          );
          const tableParams = {};
          tableParams.body = Object.assign(
              {},
              this.chartFilter,
              this.tableFilter,
              this.sortInfo,
          );
          // Call the target interface, and pass in the frame selection parameters
          this.initLeftColumnData(filterParams);
          RequestService.queryLineagesData(filterParams)
              .then(
                  (res) => {
                    if (res && res.data && res.data.object) {
                      this.errorData = false;
                      if (res.data.object.length) {
                        let customized = {};
                        customized = JSON.parse(
                            JSON.stringify(res.data.customized),
                        );
                        const customizedKeys = Object.keys(customized);
                        if (customizedKeys.length) {
                          this.setInitListValue();
                          customizedKeys.forEach((i) => {
                            if (customized[i].type === this.valueType.int) {
                              this.keysOfIntValue.push(i);
                            } else if (customized[i].type === this.valueType.str) {
                              this.keysOfStringValue.push(i);
                            } else if (
                              customized[i].type === this.valueType.mixed
                            ) {
                              // list of type mixed
                              this.keysOfMixed.push(i);
                              this.keysOfStringValue.push(i);
                            }
                          });
                        }

                        const list = this.setDataOfModel(res.data.object);
                        if (!list.length) {
                          this.noData = true;
                          this.showEchartPic = false;
                          // After the echart box is selected, it is empty, and an empty data array needs to be saved
                          this.summaryDirList = [];
                          this.$store.commit('setSummaryDirList', []);
                          return;
                        }
                        const summaryDirList = list.map((i) => i.summary_dir);
                        this.$store.commit('setSummaryDirList', summaryDirList);
                        this.echart.showData = this.echart.brushData = list;
                        this.$nextTick(() => {
                          this.initChart();
                        });
                        this.getTableList(tableParams);
                      } else {
                        // After the echart box is selected, it is empty, and an empty data array needs to be saved
                        this.summaryDirList = [];
                        this.$store.commit('setSummaryDirList', []);
                        this.noData = true;
                        this.showEchartPic = false;
                      }
                    } else {
                      this.errorData = true;
                    }
                  },
                  (error) => {
                    this.errorData = true;
                  },
              )
              .catch(() => {
                this.errorData = true;
              });
        }
      });
    },
    /**
     * Get table data
     * @param {Object} tableParams
     */
    getTableList(tableParams) {
      RequestService.queryLineagesData(tableParams)
          .then(
              (res) => {
                if (res && res.data && res.data.object) {
                  this.errorData = false;
                  if (res.data.object.length) {
                    const list = this.setDataOfModel(res.data.object);
                    const tempList = list.slice(0, this.pagination.pageSize);
                    this.table.data = tempList;
                    this.pagination.currentPage = 1;
                    this.pagination.total = this.echart.brushData.length;
                    this.$refs.table.clearSelection();
                  }
                } else {
                  this.errorData = true;
                }
              },
              (error) => {
                this.errorData = true;
              },
          )
          .catch(() => {
            this.errorData = true;
          });
    },
    /**
     * Resetting the Eechart
     */
    showAllDatafun() {
      this.summaryDirList = undefined;
      // The hidden list is set to undefined
      this.hideTableIdList = undefined;
      // Set the saved hidden list to undefined;
      this.$store.commit('setHideTableIdList', undefined);
      this.$store.commit('setSummaryDirList', undefined);
      this.$store.commit('setSelectedBarList', []);
      this.noData = false;
      this.showTable = false;
      this.selectCheckAll = true;
      this.chartFilter = {};
      this.tableFilter.summary_dir = undefined;
      this.sortInfo = {};
      this.pagination.currentPage = 1;
      this.echart.allData = [];
      if (this.echart.chart) {
        this.echart.chart.clear();
      }
      this.init();
      this.$refs.table.clearSelection();
    },
    // Set tag style
    blurFloat(event) {
      const domArr = document.querySelectorAll('.icon-dialog');
      const path = event.path || (event.composedPath && event.composedPath());
      const isActiveDom = path.some((item) => {
        return item.className === 'icon-dialog';
      });
      if (!isActiveDom) {
        this.removeIconBorder();
        domArr.forEach((item) => {
          item.style.display = 'none';
        });
        this.tagDialogShow = false;
      }
    },
    /**
     * Display of the icon dialog box
     * @param {Object} row
     * @param {Object} scope
     * @param {Object} event
     */
    showAllIcon(row, scope, event) {
      this.iconValue = row.tag >= 0 ? row.tag : 0;
      this.tagScope = scope;
      if (this.tagDialogShow) {
        this.tagDialogShow = false;
        this.removeIconBorder();
        return;
      }
      this.addIconBorder(row);
      this.tagDialogShow = true;
      const dialogHeight = 130;
      const ev = window.event || event;
      document.getElementById('tag-dialog').style.top =
        ev.clientY - dialogHeight + 'px';
    },

    /**
     * Add icon border style
     * @param {Object} row
     */
    addIconBorder(row) {
      const iconImage = document.querySelectorAll('.icon-image');
      iconImage.forEach((item, index) => {
        if (index + 1 === row.tag) {
          item.classList.add('icon-border');
        }
      });
    },

    /**
     * Remove  icon border style
     */
    removeIconBorder() {
      const classArr = document.querySelectorAll('.icon-border');
      if (classArr.length) {
        classArr.forEach((item) => {
          item.classList.remove('icon-border');
        });
      }
    },

    /**
     * icon value change
     * @param {Object} row
     * @param {Number} num
     *  @param {Object} event
     */
    iconValueChange(row, num, event) {
      const path = event.path || (event.composedPath && event.composedPath());
      const classWrap = path.find((item) => {
        return item.className === 'icon-dialog';
      });
      const classArr = classWrap.querySelectorAll('.icon-border');
      classArr.forEach((item) => {
        item.classList.remove('icon-border');
      });
      const htmDom = path.find((item) => {
        return item.nodeName === 'DIV';
      });
      htmDom.classList.add('icon-border');
      this.iconValue = num;
    },
    /**
     * Save the modification of the icon.
     * @param {Object} scope
     */
    iconChangeSave(scope) {
      this.tagDialogShow = false;
      if (scope.row.tag === this.iconValue || this.iconValue === 0) {
        return;
      }
      this.tagScope.row.tag = this.iconValue;
      const imgDom = document.querySelectorAll('.img' + scope.$index);
      imgDom.forEach((item) => {
        item.src = require('@/assets/images/icon' + this.iconValue + '.svg');
      });
      this.$forceUpdate();
      const params = {
        train_id: scope.row.summary_dir,
        body: {
          tag: this.tagScope.row.tag,
        },
      };
      this.putChangeToLineagesData(params);
    },

    /**
     * clear icon
     * @param {Object} scope
     * @param {Object} event
     */
    clearIcon(scope, event) {
      const path = event.path || (event.composedPath && event.composedPath());
      const classWrap = path.find((item) => {
        return item.className === 'icon-dialog';
      });
      const classArr = classWrap.querySelectorAll('.icon-border');
      classArr.forEach((item) => {
        item.classList.remove('icon-border');
      });
      this.tagDialogShow = false;
      this.iconValue = 0;
      this.tagScope.row.tag = 0;
      const imgDom = document.querySelectorAll('.img' + scope.$index);
      imgDom.forEach((item) => {
        item.src = require('@/assets/images/icon-down.svg');
      });
      const params = {
        train_id: scope.row.summary_dir,
        body: {
          tag: 0,
        },
      };
      this.putChangeToLineagesData(params);
    },
    /**
     * cancel save
     * @param {Object} row
     */
    cancelChangeIcon(row) {
      this.removeIconBorder();
      this.addIconBorder(row);
      this.tagDialogShow = false;
    },

    /**
     * Select all
     */
    allSelect() {
      if (this.selectCheckAll) {
        return;
      }
      this.selectArrayValue = [];
      this.checkOptions.forEach((item) => {
        item.options.forEach((option) => {
          this.selectArrayValue.push(option.label);
        });
      });
      this.selectCheckAll = !this.selectCheckAll;
      let allList = [];
      const listA = [this.$t('modelTraceback.summaryPath')];
      allList = this.selectArrayValue.concat(listA);
      //  Set selected of the column data in the table to false;
      Object.keys(this.table.columnOptions).filter((i) => {
        this.table.columnOptions[i].selected = false;
      });
      allList.forEach((item) => {
        Object.keys(this.table.columnOptions).filter((i) => {
          const labelValue = this.table.columnOptions[i].label;
          if (labelValue === item) {
            this.table.columnOptions[i].selected = true;
          }
        });
      });
      this.initColumm();
      this.$nextTick(() => {
        this.initChart();
        this.$refs.table.doLayout();
      });
    },
    /**
     * deselect all
     */
    deselectAll() {
      this.selectArrayValue = [];
      this.checkOptions.forEach((item) => {
        item.options.forEach((option) => {
          if (option.disabled) {
            this.selectArrayValue.push(option.label);
          }
        });
      });
      this.selectCheckAll = false;
      let allList = [];
      const listA = [this.$t('modelTraceback.summaryPath')];
      allList = this.selectArrayValue.concat(listA);
      // Set selected to false for these columns in the table.
      Object.keys(this.table.columnOptions).filter((i) => {
        this.table.columnOptions[i].selected = false;
      });
      allList.forEach((item) => {
        Object.keys(this.table.columnOptions).filter((i) => {
          const labelValue = this.table.columnOptions[i].label;
          if (labelValue === item) {
            this.table.columnOptions[i].selected = true;
          }
        });
      });
      this.initChart();
      this.initColumm();
    },
    /**
     * Edit remarks
     * @param {Object} row
     */
    editRemarks(row) {
      row.editShow = false;
      row.isError = false;
      this.beforeEditValue = row.remark;
    },

    /**
     * Save remarks
     * @param {Object} row
     */
    saveRemarksValue(row) {
      const tagValidation = new RegExp('^[a-zA-Z0-9\u4e00-\u9fa5_.-]{1,128}$');
      const result = row.remark.length ? tagValidation.test(row.remark) : true;
      if (result) {
        row.isError = false;
        row.editShow = true;
        const params = {
          train_id: row.summary_dir,
          body: {
            remark: row.remark,
          },
        };
        this.putChangeToLineagesData(params);
      } else {
        row.isError = true;
      }
    },

    /**
     * Cancel save editing
     * @param {Object} row
     */
    cancelRemarksValue(row) {
      row.editShow = true;
      row.remark = this.beforeEditValue;
      row.isError = false;
    },

    /**
     *After the remark or tag is modified, invoke the interface and save the modification.
     * @param {Object} params
     */
    putChangeToLineagesData(params) {
      RequestService.putLineagesData(params)
          .then(
              (res) => {
                if (res) {
                  this.$message.success(this.$t('modelTraceback.changeSuccess'));
                }
              },
              (error) => {},
          )
          .catch(() => {});
    },
    /**
     * The method for the drop-down box to get the focus operation.
     *  @param {String} val
     */
    selectinputFocus(val) {
      if (val === 'left') {
        // Parameter importance drop-down box
        this.barKeyWord = '';
        this.searchOptions = this.baseOptions;
        this.barNameList = this.baseSelectOptions;
      } else {
        // Model traceability drop-down box on the right
        this.keyWord = '';
        this.checkOptions = this.basearr;
        this.showOptions = this.rightAllOptions;
      }
    },
    /**
     * Input search filtering in the select module.
     *  @param {String} val
     */
    myfilter(val) {
      if (val === 'left') {
        // Parameter importance drop-down box
        const queryString = this.barKeyWord;
        const restaurants = this.baseSelectOptions;
        const results = queryString
          ? this.createFilter(queryString, restaurants)
          : restaurants;
        this.barNameList = results;
        this.searchOptions = [];
        let list = [];
        results.forEach((item) => {
          list = list.concat(item.options);
        });
        this.searchOptions = list;
      } else {
        // Model traceability drop-down box on the right
        const queryString = this.keyWord;
        const restaurants = this.basearr;
        const results = queryString
          ? this.createFilter(queryString, restaurants)
          : restaurants;
        this.checkOptions = results;
        this.showOptions = [];
        let list = [];
        results.forEach((item) => {
          list = list.concat(item.options);
        });
        this.showOptions = list;
      }
    },

    /**
     *Input search filtering in the select module.
     * @param {String} queryString
     * @param {Array} restaurants
     * @return {Array}
     */
    createFilter(queryString, restaurants) {
      const list = [];
      restaurants.forEach((item) => {
        const object = {};
        const options = [];
        if (item.options) {
          item.options.forEach((item) => {
            if (
              item.label.toLowerCase().indexOf(queryString.toLowerCase()) >= 0
            ) {
              const tempObj = {};
              tempObj.label = item.label;
              tempObj.value = item.value;
              tempObj.disabled = item.disabled;
              options.push(tempObj);
            }
          });
        }
        if (options.length > 0) {
          object.label = item.label;
          object.options = options;
          list.push(object);
        }
      });
      return list;
    },

    getStoreList() {
      // Get hidden list
      this.hideTableIdList = this.$store.state.hideTableIdList;
      this.summaryDirList = this.$store.state.summaryDirList;
      if (this.summaryDirList || this.hideTableIdList) {
        this.tableFilter.summary_dir = {
          in: this.summaryDirList,
          not_in: this.hideTableIdList,
        };
      } else {
        this.tableFilter.summary_dir = undefined;
      }
    },

    /**
     * Selected data in the table
     * @param {Array} list Selected data in the table
     */
    selectionChange(list = []) {
      const summaryDirFilter = [];
      list.forEach((i) => {
        summaryDirFilter.push(i.summary_dir);
      });
      this.selectRowIdList = summaryDirFilter;
      if (summaryDirFilter.length) {
        this.disabledFilterBtnModel = false;
        this.disabledHideBtnModel = false;
      } else {
        this.disabledFilterBtnModel = true;
        this.disabledHideBtnModel = true;
      }
    },
    showSelectedModelData() {
      // Only need to pass in the filter data list when filtering the table
      this.tableFilter.summary_dir = {
        in: this.selectRowIdList,
      };
      this.$store.commit('setSummaryDirList', this.selectRowIdList);
      this.selectArrayValue = [];
      this.checkOptions = [];
      this.basearr = [];
      this.$refs.table.clearSelection();
      // The page needs to be initialized to 1
      this.pagination.currentPage = 1;
      this.init();
    },
    // Hide button, hide selected item
    hideSelectedModelRows() {
      this.hideTableIdList = this.$store.state.hideTableIdList;
      this.summaryDirList = this.$store.state.summaryDirList;
      // Set hidden data
      if (this.hideTableIdList) {
        this.hideTableIdList = this.hideTableIdList.concat(
            this.selectRowIdList,
        );
      } else {
        this.hideTableIdList = this.selectRowIdList;
      }
      // There must be hidden list data
      this.tableFilter.summary_dir = {
        in: this.summaryDirList,
        not_in: this.hideTableIdList,
      };
      this.$store.commit('setHideTableIdList', this.hideTableIdList);
      this.selectArrayValue = [];
      this.checkOptions = [];
      this.basearr = [];
      this.$refs.table.clearSelection();
      // The page needs to be initialized to 1
      this.pagination.currentPage = 1;
      this.init();
    },

    /**
     * Selected data in the table
     */
    selectValueChange() {
      const list = [];
      this.basearr.forEach((item) => {
        item.options.forEach((option) => {
          list.push(option.label);
        });
      });
      if (list.length > this.selectArrayValue.length) {
        this.selectCheckAll = false;
      } else {
        this.selectCheckAll = true;
      }
      let allList = [];
      const listA = [this.$t('modelTraceback.summaryPath')];
      allList = this.selectArrayValue.concat(listA);
      Object.keys(this.table.columnOptions).filter((i) => {
        this.table.columnOptions[i].selected = false;
      });
      allList.forEach((item) => {
        Object.keys(this.table.columnOptions).filter((i) => {
          const labelValue = this.table.columnOptions[i].label;
          if (labelValue === item) {
            this.table.columnOptions[i].selected = true;
          }
        });
      });
      this.$nextTick(() => {
        this.initChart();
      });
      this.initColumm();
    },

    selectedSetBarData() {
      // Set the y-axis coordinate
      const barHyper = [];
      for (let i = 0; i < this.targetData.length; i++) {
        if (this.targetData[i].name === this.yTitle) {
          this.targetData[i].hyper_parameters.forEach((item) => {
            if (!item.unselected) {
              if (item.name.startsWith('[U]')) {
                barHyper.unshift(item);
              } else {
                barHyper.push(item);
              }
            }
          });
        }
      }
      barHyper.sort(this.sortBy('importance'));
      this.barYAxisData = [];
      this.barSeriesData = [];
      for (let j = 0; j < barHyper.length; j++) {
        const name = barHyper[j].name;
        let importanceValue = barHyper[j].importance;
        if (importanceValue < 0.0001 && importanceValue > 0) {
          importanceValue = importanceValue.toExponential(4);
        } else {
          importanceValue =
            Math.round(importanceValue * Math.pow(10, 4)) / Math.pow(10, 4);
        }
        if (this.selectedBarArray.includes(name)) {
          this.barYAxisData.push(name);
          this.barSeriesData.push(importanceValue);
        }
      }
      this.selectedAllBar =
        barHyper.length > this.barYAxisData.length ? false : true;
      this.$nextTick(() => {
        this.setChartOfBar();
      });
    },

    /**
     * Sort data in the table
     * @param {Object} column current column
     */
    sortChange(column) {
      if (this.sortChangeTimer) {
        clearTimeout(this.sortChangeTimer);
        this.sortChangeTimer = null;
      }
      this.sortChangeTimer = setTimeout(() => {
        this.sortInfo.sorted_name = column.prop;
        this.sortInfo.sorted_type = column.order;
        this.getStoreList();
        const tempParam = {
          limit: this.pagination.pageSize,
          offset: 0,
          sorted_name: this.sortInfo.sorted_name,
          sorted_type: this.sortInfo.sorted_type,
        };
        const params = {};
        params.body = Object.assign(
            {},
            tempParam,
            this.tableFilter,
            this.chartFilter || {},
        );
        RequestService.queryLineagesData(params)
            .then(
                (res) => {
                  if (res && res.data && res.data.object) {
                    this.errorData = false;
                    const list = this.setDataOfModel(res.data.object);
                    const tempList = list.slice(0, this.pagination.pageSize);
                    this.table.data = tempList;
                    this.pagination.total = res.data.count || 0;
                    this.pagination.currentPage = 1;
                  } else {
                    this.errorData = true;
                  }
                },
                (error) => {
                  this.errorData = true;
                },
            )
            .catch(() => {
              this.errorData = true;
            });
      }, this.delayTime);
    },

    /**
     * Jump to the training dashboard
     * @param {String} id
     */
    jumpToTrainDashboard(id) {
      const trainId = encodeURIComponent(id);
      const routeUrl = this.$router.resolve({
        path: '/train-manage/training-dashboard',
        query: {id: trainId},
      });
      window.open(routeUrl.href, '_blank');
    },
    /**
     * Jump to DataTraceback
     */
    jumpToDataTraceback() {
      this.$router.push({
        path: '/data-traceback',
      });
    },
    /**
     * Keep the number with n decimal places.
     * @param {Number} num
     * @param {Number} pow Number of decimal places
     * @return {Number}
     */
    toFixedFun(num, pow) {
      if (isNaN(num) || isNaN(pow) || !num || !pow) {
        return num;
      }
      return Math.round(num * Math.pow(10, pow)) / Math.pow(10, pow);
    },
    /**
     * Formatting Data
     * @param {String} key
     * @param {String} value
     * @return {Object}
     */
    formatNumber(key, value) {
      if (isNaN(value) || !value) {
        return value;
      } else {
        const numDigits = 4;
        if (key === this.labelValue.learning_rate) {
          let temp = value.toPrecision(numDigits);
          let row = 0;
          while (temp < 1) {
            temp = temp * 10;
            row += 1;
          }
          temp = this.toFixedFun(temp, numDigits);
          return `${temp}${row ? `e-${row}` : ''}`;
        } else if (key === this.valueType.model_size) {
          return value + 'MB';
        } else {
          const num = 1000;
          if (value < num) {
            return (
              Math.round(value * Math.pow(10, numDigits)) /
              Math.pow(10, numDigits)
            );
          } else {
            const reg = /(?=(\B)(\d{3})+$)/g;
            return (value + '').replace(reg, ',');
          }
        }
      }
    },
    /**
     * Resizing Chart
     */
    resizeChart() {
      if (
        document.getElementById('echart') &&
        document.getElementById('echart').style.display !== 'none' &&
        this.echart &&
        this.echart.chart
      ) {
        this.$nextTick(() => {
          this.echart.chart.resize();
        });
      }
    },
  },
  /**
   * Destroy the page
   */
  destroyed() {
    this.myPieChart = null;
    this.myBarChart = null;
    this.sortChangeTimer = null;
    if (this.echart.chart) {
      window.removeEventListener('resize', this.resizeChart, false);
      this.echart.chart.clear();
      this.echart.chart = null;
    }
    document.removeEventListener('resize', this.blurFloat);
  },
  components: {
    Scatter,
  },
};
</script>
<style lang="scss">
.cl-model-traceback {
  height: 100%;
  background-color: #fff;
}
// Set the maximum width of the drop-down box
.el-select-dropdown {
  max-width: 300px;
}
.el-select__tags {
  overflow: hidden;
}
.traceback-tab {
  height: 51px;
  line-height: 56px;
  padding: 0 24px;
  border-bottom: 1px solid rgba($color: #000000, $alpha: 0.1);
}
.traceback-tab-item {
  padding: 0 10px;
  height: 48px;
  -webkit-box-sizing: border-box;
  box-sizing: border-box;
  line-height: 48px;
  display: inline-block;
  list-style: none;
  font-size: 17px;
  color: #303133;
  position: relative;
}
.item-active {
  color: #00a5a7;
  font-weight: bold;
  border-bottom: 3px solid rgba($color: #00a5a7, $alpha: 1);
}
.traceback-tab-item:hover {
  color: #00a5a7;
  cursor: pointer;
}
.label-text {
  line-height: 20px !important;
  padding-top: 20px;
  display: block !important;
}
.remark-tip {
  line-height: 20px !important;
  font-size: 12px;
  white-space: pre-wrap !important;
  color: gray;
  display: block !important;
}
.el-color-dropdown__main-wrapper,
.el-color-dropdown__value,
.el-color-alpha-slider {
  display: none;
}
.el-tag.el-tag--info .el-tag__close {
  color: #fff;
}
.select-inner-input {
  width: calc(100% - 130px);
  margin: 2px 4px;
  display: inline-block;
}
.select-input-button {
  position: relative;
}
.el-select-group__title {
  font-size: 14px;
  font-weight: 700;
}
.el-select-dropdown__item.selected {
  font-weight: 400;
}
.checked-color {
  color: #00a5a7 !important;
}
.el-tag.el-tag--info .el-tag__close {
  display: none;
}
.btn-disabled {
  cursor: not-allowed !important;
}
.select-all-button {
  padding: 4px 0;
  display: inline-block;
  position: absolute;
  right: 80px;
  padding: 5px;
  height: 32px;
  border: none;
  background: none;
}
.deselect-all-button {
  padding: 4px 0;
  display: inline-block;
  position: absolute;
  right: 10px;
  padding: 5px;
  height: 32px;
  border: none;
  background: none;
}

#model-traceback-con {
  display: flex;
  height: calc(100% - 51px);
  overflow-y: auto;
  position: relative;
  background: #fff;
  .no-data-page {
    display: flex;
    width: 100%;
    flex: 1;
    justify-content: center;
    align-items: center;
    .set-height-class {
      height: 282px !important;
    }
    .no-data-img {
      background: #fff;
      text-align: center;
      height: 200px;
      width: 310px;
      margin: auto;
      img {
        max-width: 100%;
      }
    }
    .no-data-text {
      font-size: 16px;
      padding-top: 15px;
      text-align: center;
    }
  }
  .echart-data-list {
    .dialog-scatter {
      width: 100%;
      height: 100%;
    }
    .el-dialog__title {
      font-weight: bold;
    }
    .el-dialog__body {
      height: 500px;
      padding-top: 0px;
      margin-bottom: 20px;
      overflow: auto;
      .details-data-title {
        margin-bottom: 20px;
      }
    }
  }
  .el-table th.gutter {
    display: table-cell !important;
  }
  .icon-border {
    border: 1px solid #00a5a7 !important;
  }
  #tag-dialog {
    z-index: 999;
    border: 1px solid #d6c9c9;
    position: fixed;
    width: 326px;
    height: 120px;
    background-color: #efebeb;
    right: 106px;
    border-radius: 4px;
  }
  .custom-btn {
    border: 1px solid #00a5a7;
    border-radius: 2px;
    background-color: white;
    color: #00a5a7;
  }
  .custom-btn:hover {
    color: #00a5a7;
    background: #e9f7f7;
  }
  .disabled-btn-color {
    border-radius: 2px;
    background-color: #f5f5f6;
    border: 1px solid #dfe1e6;
    color: #adb0b8;
  }
  .abled-btn-color {
    border: 1px solid #00a5a7;
    color: #00a5a7;
    background: white;
  }
  .abled-btn-color:hover {
    color: #00a5a7;
    background: #e9f7f7;
  }
  .icon-image {
    display: inline-block;
    padding: 4px;
    height: 30px;
    width: 30px;
    border: 1px solid transparent;
  }
  .icon-image-container {
    margin: 16px 10px 18px;
  }
  .edit-text-container {
    display: inline-block;
    max-width: 140px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .btn-container-margin {
    margin: 0 10%;
  }
  .tag-button-container {
    display: inline-block;
    width: 33.3%;
    text-align: center;
  }
  .btns-container {
    padding: 6px 32px 4px;
  }
  .table-container .el-icon-edit {
    margin-left: 5px;
  }
  .table-container i {
    font-size: 18px;
    margin: 0 2px;
    color: #00a5a7;
    cursor: pointer;
  }
  .table-container .el-icon-close {
    color: #f56c6c;
  }
  .table-container .validation-error {
    color: #ff0000;
  }
  .select-container {
    padding: 10px 0;
    position: relative;
    display: flex;
  }
  .display-column {
    display: inline-block;
    padding-right: 6px;
    height: 32px;
    line-height: 32px;
  }
  .inline-block-set {
    display: inline-block;
  }
  .remark-input-style {
    width: 140px;
  }
  .tag-icon-container {
    width: 21px;
    height: 21px;
    border: 1px solid #e6e6e6;
    cursor: pointer;
    border-radius: 2px;
  }
  .button-text {
    color: #606266 !important;
  }
  // left module
  .cl-model-left {
    width: 400px;
    background: #edf0f5;
    overflow-y: auto;
    margin: 6px 0px 10px 32px;
    padding: 10px 16px;
    .left-chart-container {
      height: 100%;
      min-height: 774px;
    }
    .left-title {
      height: 30px;
      display: flex;
      .pie-select-style {
        flex: 1;
      }
      .left-select {
        width: 180px;
        .el-select > .el-input {
          width: 180px !important;
        }
      }
    }
    .title-style {
      font-size: 16px;
      flex: 1;
      font-weight: bold;
      line-height: 30px;
      .el-icon-refresh-right {
        font-size: 20px;
        vertical-align: middle;
        cursor: pointer;
      }
    }

    .pie-title {
      margin-right: 110px;
      height: 20px;
      line-height: 20px;
      font-weight: bold;
    }
    .title-container {
      margin-bottom: 10px;
      display: flex;
      .tooltip-container {
        line-height: 20px;
        padding: 10px;
      }
    }
    .pie-module-container {
      padding: 10px 0 0px;
      height: 250px;
      #pie-chart {
        width: 368px;
        height: 200px;
      }
    }
    .bar-module-container {
      height: 270px;
      border-bottom: 1px solid #b9bcc1;
      border-top: 1px solid #b9bcc1;
      padding: 10px 0;
      .bar-select {
        display: flex;
        flex: 1.35;
        .el-select {
          max-width: 240px;
        }
      }
      .bar-title-container {
        display: flex;
      }
      .bar-title {
        font-weight: bold;
        flex: 1;
        height: 32px;
        line-height: 32px;
      }
      #bar-chart {
        width: 368px;
        height: 220px;
      }
    }
    .scatter-container {
      height: calc(100% - 20px - 250px - 270px);
      padding-top: 10px;
      .scatter-title-container {
        display: flex;
        font-weight: bold;
        flex-direction: row;
        width: 100%;
        .right-view {
          position: relative;
          flex: 1;
        }
        .el-icon-info {
          font-size: 16px;
          margin-left: 5px;
          color: #6c7280;
        }
        .view-big {
          position: absolute;
          right: 10px;
          width: 12px;
          height: 12px;
          cursor: pointer;
          background-image: url('../../assets/images/full-screen.png');
        }
      }
    }
    .left-scatters-container {
      overflow: auto;
      width: 100%;
      height: calc(100% - 32px);
    }
    .collapse-btn {
      position: absolute;
      width: 31px;
      height: 100px;
      top: 50%;
      left: 423px;
      margin-top: -50px;
      cursor: pointer;
      line-height: 86px;
      z-index: 1999;
      text-align: center;
      background-image: url('../../assets/images/collapse-left.svg');
    }
    .collapse-btn.collapse {
      left: -10px;
      background-image: url('../../assets/images/collapse-right.svg');
    }
  }
  .cl-model-right.collapse {
    width: 100% !important;
  }
  .cl-model-left.collapse {
    width: 0;
    padding: 0px;
  }
  .cl-model-right {
    display: flex;
    flex-direction: column;
    width: 100%;
    flex: 1;
    width: calc(100% - 400px);
    background-color: #fff;
    -webkit-box-shadow: 0 1px 0 0 rgba(200, 200, 200, 0.5);
    box-shadow: 0 1px 0 0 rgba(200, 200, 200, 0.5);
    overflow: hidden;
    // select
    .el-select > .el-input {
      min-width: 280px !important;
      max-width: 500px !important;
    }
    .top-area {
      margin: 0px 32px 6px;
      display: flex;
      justify-content: flex-end;
      .select-box {
        height: 46px;
        flex-grow: 1;
        .label-legend {
          height: 19px;
          margin-bottom: 4px;
          display: inline-block;
          position: absolute;
          right: 30px;
          height: 32px;
          line-height: 32px;
          div {
            display: inline-block;
            font-size: 12px;
          }
          div + div {
            margin-left: 30px;
          }
        }
      }
    }
    #echart {
      height: 31%;
      padding: 0 12px;
    }
    .echart-no-data {
      height: 31%;
      padding: 0 12px;
      width: 100%;
    }
    .table-container {
      background-color: white;
      height: calc(67% - 78px);
      padding: 6px 32px 0px;
      position: relative;
      .disabled-checked {
        position: absolute;
        top: 9px;
        left: 0px;
        z-index: 1000;
        width: 87px;
        height: 66px;
        cursor: not-allowed;
      }
      .custom-label {
        max-width: calc(100% - 25px);
        padding: 0;
        vertical-align: middle;
      }
      a {
        cursor: pointer;
      }
      .el-pagination {
        float: right;
        margin-right: 32px;
        bottom: 10px;
      }
      .pagination-container {
        height: 40px;
      }
    }
  }
}
</style>

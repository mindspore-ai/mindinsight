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
            <div class="title-style">{{$t('modelTraceback.optimizationObject')}}</div>
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
            <div id="pie-chart"></div>
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
                                :placeholder="$t('public.search')"
                                ref="barKeyInput"></el-input>
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
                  <div slot="empty">
                    <div class="select-input-button empty-container">
                      <div class="select-inner-input">
                        <el-input v-model="barKeyWord"
                                  @input="myfilter('left')"
                                  :placeholder="$t('public.search')"
                                  ref="barKeyEmptyInput"></el-input>
                      </div>
                      <button type="text"
                              class="select-all-button"
                              disabled>
                        {{$t('public.selectAll')}}
                      </button>
                      <button type="text"
                              class="deselect-all-button"
                              disabled>
                        {{$t('public.deselectAll')}}
                      </button>
                      <div class="search-no-data">{{$t('public.emptyData')}}</div>
                    </div>
                  </div>
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
                            placement="top">
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
            <div class="left-scatters-container" v-show="!viewBigBtnDisabled">
              <Scatter ref="smallScatter"
                       :data="scatterChartData"
                       :yTitle="yTitle"
                       :xTitle="xTitle"
                       :tooltipsData="tooltipsData"
                       :showTooltip="true">
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
                                :placeholder="$t('public.search')"
                                ref="keyInput"></el-input>
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
                  <div slot="empty">
                    <div class="select-input-button empty-container">
                      <div class="select-inner-input">
                        <el-input v-model="keyWord"
                                  @input="myfilter"
                                  :placeholder="$t('public.search')"
                                  ref="keyEmptyInput"></el-input>
                      </div>
                      <button type="text"
                              class="select-all-button"
                              disabled>
                        {{$t('public.selectAll')}}
                      </button>
                      <button type="text"
                              @click="deselectAll"
                              class="deselect-all-button"
                              disabled>
                        {{$t('public.deselectAll')}}
                      </button>
                      <div class="search-no-data">{{$t('public.emptyData')}}</div>
                    </div>
                  </div>
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
             v-show="!noData && showEchartPic && !loading"></div>
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
                             :show-overflow-tooltip="table.columnOptions[key].label === text ? false : true"
                             :min-width="table.columnOptions[key].label === text ? 250 : 150"
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
                     v-show="scope.row.editShow"
                     :title="scope.row.remark">{{scope.row.remark}}</div>
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
                           @size-change="pagination.currentPagesizeChange"
                           :current-page="pagination.currentPage"
                           :page-size="pagination.pageSize"
                           :page-sizes="pagination.pageSizes"
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
               (!hideTableIdList || (hideTableIdList&&!hideTableIdList.length))">
              {{ $t('public.noData') }}</p>
            <div v-show="(hideTableIdList && hideTableIdList.length) &&
            (!summaryDirList || (summaryDirList && summaryDirList.length))">
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
import modelDataFun from '../../mixins/model-data.vue';

export default {
  mixins: [modelDataFun],
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
      barOption: {},
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
      currentBarData: {},
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
      tooltipsBarName: '',
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
        pageSize: 10,
        pageSizes: [10, 20, 50],
        total: 0,
        layout: 'total, sizes, prev, pager, next, jumper',
        pageChange: {},
        currentPagesizeChange: {},
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
    this.setTableColumnData();
    this.getStoreList();
    this.pagination.pageChange = (page) => {
      this.pagination.currentPage = page;
      this.queryLineagesData(false);
    };
    this.pagination.currentPagesizeChange = (pageSize) => {
      this.pagination.pageSize = pageSize;
      this.queryLineagesData(false);
    };
    this.$nextTick(() => {
      this.init();
    });
  },
  methods: {
    /**
     * Initialization
     */
    init() {
      this.queryLineagesData(true);
    },

    /** ***  left code***/

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

    /** ***********right column*********** **/

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
                    this.setTableColumnData();
                    this.setSelectOptionsData();
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
                    this.table.data = list.slice(0, this.pagination.pageSize);
                  } else {
                    this.table.data = list.slice(0, this.pagination.pageSize);
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
    /**
     * Column initialization
     */
    initColumm() {
      this.metricList = [];
      this.userDefinedList = [];
      // hyper list
      this.hyperList = [];
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
                    this.table.data = list.slice(0, this.pagination.pageSize);
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
     * Deselect all
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
              barHyper.unshift(item);
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
        const minRange = 1.0e-10;
        const smallerData = 0.0001;
        if (importanceValue < minRange && importanceValue > 0) {
          importanceValue = 0;
        } else if (importanceValue < smallerData && importanceValue > 0) {
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
                    this.table.data = list.slice(0, this.pagination.pageSize);
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
  },
  /**
   * Destroy the page
   */
  destroyed() {
    if (this.myPieChart) {
      this.myPieChart.clear();
      this.myPieChart = null;
    }

    if (this.myBarChart) {
      this.myBarChart.off('datazoom');
      this.myBarChart.off('click');
      if (this.myBarChart.getZr()) {
        this.myBarChart.getZr().off('click');
      }
      this.myBarChart.off('mouseover');
      this.myBarChart.off('mouseout');
      this.myBarChart.clear();
      this.myBarChart = null;
    }

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
<style>
.cl-model-traceback {
  height: 100%;
  background-color: #fff;
}

.el-select-dropdown {
  max-width: 300px;
}
.el-select-dropdown li.is-disabled {
  color: #c0c4cc !important;
}

.el-select__tags {
  overflow: hidden;
}

.traceback-tab {
  height: 51px;
  line-height: 56px;
  padding: 0 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
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
  border-bottom: 3px solid #00a5a7;
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
  min-width: 78px;
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

.empty-container {
  padding-top: 6px;
}

.search-no-data {
  padding: 10px 0;
  margin: 0;
  text-align: center;
  color: #999;
  font-size: 14px;
}

#model-traceback-con {
  display: flex;
  height: calc(100% - 51px);
  overflow-y: auto;
  position: relative;
  background: #fff;
}
#model-traceback-con .no-data-page {
  display: flex;
  width: 100%;
  flex: 1;
  justify-content: center;
  align-items: center;
}
#model-traceback-con .no-data-page .set-height-class {
  height: 282px !important;
}
#model-traceback-con .no-data-page .no-data-img {
  background: #fff;
  text-align: center;
  height: 200px;
  width: 310px;
  margin: auto;
}
#model-traceback-con .no-data-page .no-data-img img {
  max-width: 100%;
}
#model-traceback-con .no-data-page .no-data-text {
  font-size: 16px;
  padding-top: 15px;
  text-align: center;
}
#model-traceback-con .echart-data-list .dialog-scatter {
  width: 100%;
  height: 100%;
}
#model-traceback-con .echart-data-list .el-dialog__title {
  font-weight: bold;
}
#model-traceback-con .echart-data-list .el-dialog__body {
  height: 500px;
  padding-top: 0px;
  margin-bottom: 20px;
  overflow: auto;
}
#model-traceback-con .echart-data-list .el-dialog__body .details-data-title {
  margin-bottom: 20px;
}
#model-traceback-con .el-table th.gutter {
  display: table-cell !important;
}
#model-traceback-con .icon-border {
  border: 1px solid #00a5a7 !important;
}
#model-traceback-con #tag-dialog {
  z-index: 999;
  border: 1px solid #d6c9c9;
  position: fixed;
  width: 326px;
  height: 120px;
  background-color: #efebeb;
  right: 106px;
  border-radius: 4px;
}
#model-traceback-con .custom-btn {
  border: 1px solid #00a5a7;
  border-radius: 2px;
  background-color: white;
  color: #00a5a7;
}
#model-traceback-con .custom-btn:hover {
  color: #00a5a7;
  background: #e9f7f7;
}
#model-traceback-con .disabled-btn-color {
  border-radius: 2px;
  background-color: #f5f5f6;
  border: 1px solid #dfe1e6;
  color: #adb0b8;
}
#model-traceback-con .abled-btn-color {
  border: 1px solid #00a5a7;
  color: #00a5a7;
  background: white;
}
#model-traceback-con .abled-btn-color:hover {
  color: #00a5a7;
  background: #e9f7f7;
}
#model-traceback-con .icon-image {
  display: inline-block;
  padding: 4px;
  height: 30px;
  width: 30px;
  border: 1px solid transparent;
}
#model-traceback-con .icon-image-container {
  margin: 16px 10px 18px;
}
#model-traceback-con .edit-text-container {
  display: inline-block;
  max-width: 190px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: bottom;
}
#model-traceback-con .btn-container-margin {
  margin: 0 10%;
}
#model-traceback-con .tag-button-container {
  display: inline-block;
  width: 33.3%;
  text-align: center;
}
#model-traceback-con .btns-container {
  padding: 6px 32px 4px;
}
#model-traceback-con .table-container .el-icon-edit {
  margin-left: 5px;
}
#model-traceback-con .table-container i {
  font-size: 18px;
  margin: 0 2px;
  color: #00a5a7;
  cursor: pointer;
}
#model-traceback-con .table-container .el-icon-close {
  color: #f56c6c;
}
#model-traceback-con .table-container .validation-error {
  color: #ff0000;
}
#model-traceback-con .select-container {
  padding: 10px 0;
  position: relative;
  display: flex;
}
#model-traceback-con .display-column {
  display: inline-block;
  padding-right: 6px;
  height: 32px;
  line-height: 32px;
}
#model-traceback-con .inline-block-set {
  display: inline-block;
}
#model-traceback-con .remark-input-style {
  width: 190px;
}
#model-traceback-con .tag-icon-container {
  width: 21px;
  height: 21px;
  border: 1px solid #e6e6e6;
  cursor: pointer;
  border-radius: 2px;
}
#model-traceback-con .button-text {
  color: #606266 !important;
}
#model-traceback-con .cl-model-left {
  width: 400px;
  background: #edf0f5;
  overflow-y: auto;
  margin: 6px 0px 10px 32px;
  padding: 10px 16px;
}
#model-traceback-con .cl-model-left .left-chart-container {
  height: 100%;
  min-height: 774px;
}
#model-traceback-con .cl-model-left .left-title {
  height: 30px;
  display: flex;
}
#model-traceback-con .cl-model-left .left-title .pie-select-style {
  flex: 1;
}
#model-traceback-con .cl-model-left .left-title .left-select {
  width: 180px;
}
#model-traceback-con .cl-model-left .left-title .left-select .el-select > .el-input {
  width: 180px !important;
}
#model-traceback-con .cl-model-left .title-style {
  font-size: 16px;
  flex: 1;
  font-weight: bold;
  line-height: 30px;
}
#model-traceback-con .cl-model-left .title-style .el-icon-refresh-right {
  font-size: 20px;
  vertical-align: middle;
  cursor: pointer;
}
#model-traceback-con .cl-model-left .pie-title {
  margin-right: 110px;
  height: 20px;
  line-height: 20px;
  font-weight: bold;
}
#model-traceback-con .cl-model-left .title-container {
  margin-bottom: 10px;
  display: flex;
}
#model-traceback-con .cl-model-left .title-container .tooltip-container {
  line-height: 20px;
  padding: 10px;
}
#model-traceback-con .cl-model-left .pie-module-container {
  padding: 10px 0 0px;
  height: 250px;
}
#model-traceback-con .cl-model-left .pie-module-container #pie-chart {
  width: 368px;
  height: 200px;
}
#model-traceback-con .cl-model-left .bar-module-container {
  height: 270px;
  border-bottom: 1px solid #b9bcc1;
  border-top: 1px solid #b9bcc1;
  padding: 10px 0;
  overflow: hidden;
}
#model-traceback-con .cl-model-left .bar-module-container .bar-select {
  display: flex;
  flex: 1.35;
}
#model-traceback-con .cl-model-left .bar-module-container .bar-select .el-select {
  max-width: 240px;
}
#model-traceback-con .cl-model-left .bar-module-container .bar-title-container {
  display: flex;
}
#model-traceback-con .cl-model-left .bar-module-container .bar-title {
  font-weight: bold;
  flex: 1;
  height: 32px;
  line-height: 32px;
}
#model-traceback-con .cl-model-left .bar-module-container #bar-chart {
  width: 368px;
  height: 220px;
}
#model-traceback-con .cl-model-left .scatter-container {
  height: calc(100% - 20px - 250px - 270px);
  padding-top: 10px;
}
#model-traceback-con .cl-model-left .scatter-container .scatter-title-container {
  display: flex;
  font-weight: bold;
  flex-direction: row;
  width: 100%;
}
#model-traceback-con .cl-model-left .scatter-container .scatter-title-container .right-view {
  position: relative;
  flex: 1;
}
#model-traceback-con .cl-model-left .scatter-container .scatter-title-container .el-icon-info {
  font-size: 16px;
  margin-left: 5px;
  color: #6c7280;
}
#model-traceback-con .cl-model-left .scatter-container .scatter-title-container .view-big {
  position: absolute;
  right: 10px;
  width: 12px;
  height: 12px;
  cursor: pointer;
  background-image: url("../../assets/images/full-screen.png");
}
#model-traceback-con .cl-model-left .left-scatters-container {
  overflow: hidden;
  width: 100%;
  height: calc(100% - 32px);
}
#model-traceback-con .cl-model-left .collapse-btn {
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
  background-image: url("../../assets/images/collapse-left.svg");
}
#model-traceback-con .cl-model-left .collapse-btn.collapse {
  left: -10px;
  background-image: url("../../assets/images/collapse-right.svg");
}
#model-traceback-con .cl-model-right.collapse {
  width: 100% !important;
}
#model-traceback-con .cl-model-left.collapse {
  width: 0;
  padding: 0px;
}
#model-traceback-con .cl-model-right {
  display: flex;
  flex-direction: column;
  width: 100%;
  flex: 1;
  width: calc(100% - 400px);
  background-color: #fff;
  -webkit-box-shadow: 0 1px 0 0 rgba(200, 200, 200, 0.5);
  box-shadow: 0 1px 0 0 rgba(200, 200, 200, 0.5);
  overflow: hidden;
}
#model-traceback-con .cl-model-right .select-container .el-select > .el-input {
  min-width: 280px !important;
  max-width: 500px !important;
}
#model-traceback-con .cl-model-right .top-area {
  margin: 0px 32px 6px;
  display: flex;
  justify-content: flex-end;
}
#model-traceback-con .cl-model-right .top-area .select-box {
  height: 46px;
  flex-grow: 1;
}
#model-traceback-con .cl-model-right .top-area .select-box .label-legend {
  height: 19px;
  margin-bottom: 4px;
  display: inline-block;
  position: absolute;
  right: 30px;
  height: 32px;
  line-height: 32px;
}
#model-traceback-con .cl-model-right .top-area .select-box .label-legend div {
  display: inline-block;
  font-size: 12px;
}
#model-traceback-con .cl-model-right .top-area .select-box .label-legend div + div {
  margin-left: 30px;
}
#model-traceback-con .cl-model-right #echart {
  height: 31%;
  padding: 0 12px;
}
#model-traceback-con .cl-model-right .echart-no-data {
  height: 31%;
  padding: 0 12px;
  width: 100%;
}
#model-traceback-con .cl-model-right .table-container {
  background-color: white;
  height: calc(67% - 78px);
  padding: 6px 32px 0px;
  position: relative;
}
#model-traceback-con .cl-model-right .table-container .disabled-checked {
  position: absolute;
  top: 9px;
  left: 0px;
  z-index: 1000;
  width: 87px;
  height: 66px;
  cursor: not-allowed;
}
#model-traceback-con .cl-model-right .table-container .custom-label {
  max-width: calc(100% - 25px);
  padding: 0;
  vertical-align: middle;
}
#model-traceback-con .cl-model-right .table-container a {
  cursor: pointer;
}
#model-traceback-con .cl-model-right .table-container .el-pagination {
  float: right;
  margin-right: 32px;
  bottom: 10px;
}
#model-traceback-con .cl-model-right .table-container .pagination-container {
  height: 40px;
}

.tooltip-msg {
  white-space: normal;
  word-break: break-all;
  max-width: 250px;
}
</style>

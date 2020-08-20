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
  <div id="cl-data-traceback">
    <div v-if="loading"
         class="no-data-page">
      <div class="no-data-img">
        <img :src="require('@/assets/images/nodata.png')"
             alt="" />
        <p class="no-data-text">{{$t("public.dataLoading")}}</p>
      </div>
    </div>
    <div class="cl-data-right"
         v-if="!loading">
      <!-- select area -->
      <div class="data-checkbox-area"
           v-show="!errorData&&!(!totalSeries.length&&pagination.total)">
        <div class="select-container"
             v-show="totalSeries && totalSeries.length &&
              (!summaryDirList || (summaryDirList && summaryDirList.length))">
          <div class="display-column">
            {{$t('modelTraceback.displayColumn')}}
          </div>
          <div class="inline-block-set">
            <!-- multiple collapse-tags -->
            <el-select v-model="selectArrayValue"
                       multiple
                       collapse-tags
                       @change="selectValueChange"
                       :placeholder="$t('public.select')"
                       @focus="selectinputFocus">
              <div class="select-input-button">
                <div class="select-inner-input">
                  <el-input v-model="keyWord"
                            v-on:input="myfilter"
                            :placeholder="$t('public.search')">
                  </el-input>
                </div>
                <button type="text"
                        @click="allSelect"
                        class="select-all-button"
                        :class="[selectCheckAll ? 'checked-color' : 'button-text',
                           basearr.length > checkOptions.length ? 'btn-disabled' : '']"
                        :disabled="basearr.length > checkOptions.length">
                  {{ $t('public.selectAll')}}
                </button>
                <button type="text"
                        @click="deselectAll"
                        class="deselect-all-button"
                        :class="[!selectCheckAll ? 'checked-color' : 'button-text',
                           basearr.length > checkOptions.length ? 'btn-disabled' : '']"
                        :disabled="basearr.length > checkOptions.length">
                  {{ $t('public.deselectAll')}}
                </button>
              </div>
              <el-option v-for="item in checkOptions"
                         :key="item.value"
                         :label="item.label"
                         :value="item.value"
                         :disabled="item.disabled"
                         :title="item.disabled ? $t('modelTraceback.mustExist') : ''">
              </el-option>
            </el-select>
          </div>
        </div>
        <!-- show all data button -->
        <div class="btns">
          <el-button class="reset-btn custom-btn"
                     @click="echartShowAllData"
                     type="primary"
                     size="mini"
                     plain
                     v-show="(summaryDirList && !summaryDirList.length)||(totalSeries && totalSeries.length)">
            {{ $t('modelTraceback.showAllData') }}
          </el-button>
        </div>
      </div>
      <!-- echart drawing area -->
      <div id="data-echart"
           v-show="showEchartPic && !echartNoData"></div>
      <div class="echart-nodata-container"
           v-show="!showEchartPic && showTable && !(summaryDirList && !summaryDirList.length)">
      </div>
      <div class="btns-container"
           v-show="!echartNoData && showTable">
        <el-button type="primary"
                   size="mini"
                   class="custom-btn"
                   @click="hiddenRecords"
                   plain>
          {{ $t('modelTraceback.hide')}}
        </el-button>
        <el-button type="primary"
                   size="mini"
                   class="custom-btn"
                   @click="unhideRecords"
                   plain>
          {{$t('modelTraceback.unhide')}}
        </el-button>
      </div>
      <!-- table area -->
      <div class="table-container"
           v-show="!echartNoData && showTable">
        <el-table ref="table"
                  :data="table.data"
                  tooltip-effect="light"
                  height="calc(100% - 40px)"
                  row-key="summary_dir"
                  @selection-change="handleSelectionChange"
                  @sort-change="tableSortChange">
          <el-table-column type="selection"
                           width="55"
                           :reserve-selection="true"
                           v-show="!echartNoData && showTable">
          </el-table-column>
          <el-table-column v-for="key in table.column"
                           :key="key"
                           :prop="key"
                           :label="table.columnOptions[key].label"
                           :sortable="sortArray.includes(table.columnOptions[key].label) ? 'custom' : false"
                           :fixed="table.columnOptions[key].label === text ? true : false"
                           min-width="200"
                           show-overflow-tooltip>
            <template slot="header"
                      slot-scope="scope">
              <div class="custom-label"
                   :title="scope.column.label">
                {{scope.column.label}}
              </div>
            </template>
            <template slot-scope="scope">
              <span class="icon-container"
                    v-show="table.columnOptions[key].label === text">
                <el-tooltip effect="light"
                            :content="$t('dataTraceback.dataTraceTips')"
                            placement="top"
                            v-show="scope.row.children">
                  <i class="el-icon-warning"></i>
                </el-tooltip>
              </span>
              <span @click="jumpToTrainDashboard(scope.row[key])"
                    v-if="table.columnOptions[key].label === text"
                    class="href-color">
                {{ scope.row[key] }}
              </span>
              <span v-else
                    @click="showDialogData(scope.row[key], scope)"
                    class="click-span">
                {{formatNumber(key, scope.row[key]) }}
              </span>
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
              <!-- The system determines whether to display the pen icon and
              text box based on the values of editShow -->
              <div class="edit-text-container"
                   v-show="scope.row.editShow">{{ scope.row.remark }}</div>
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
                  {{ $t('modelTraceback.remarkValidation')}}
                </div>
              </div>
            </template>
          </el-table-column>
          <!-- tag column -->
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
          <el-pagination @current-change="handleCurrentChange"
                         :current-page="pagination.currentPage"
                         :page-size="pagination.pageSize"
                         :layout="pagination.layout"
                         :total="pagination.total">
          </el-pagination>
          <div class="hide-count"
               v-show="recordsNumber-showNumber">
            {{ $t('modelTraceback.totalHide').replace(`{n}`, (recordsNumber-showNumber))}}
          </div>
          <div class="clear"></div>
        </div>
      </div>
      <div v-show="nodata"
           class="no-data-page">
        <div class="no-data-img"
             :class="{'set-height-class':(summaryDirList && !summaryDirList.length)}">
          <img :src="require('@/assets/images/nodata.png')"
               alt="" />
          <p class="no-data-text"
             v-show="!summaryDirList || (summaryDirList && summaryDirList.length) && !lineagedata.serData">
            {{ $t('public.noData') }}
          </p>
          <div v-show="echartNoData && (lineagedata.serData && !!lineagedata.serData.length)">
            <p class="no-data-text">{{ $t('dataTraceback.noDataFound') }}</p>
          </div>
          <div v-show="summaryDirList && !summaryDirList.length">
            <p class="no-data-text">{{ $t('dataTraceback.noDataFound') }}</p>
            <p class="no-data-text">
              {{ $t('dataTraceback.click') }}
              <b> {{ $t('modelTraceback.showAllDataBtn') }}</b>
              {{ $t('dataTraceback.viewAllData') }}
            </p>
          </div>
        </div>
      </div>
    </div>
    <div v-if="detailsDialogVisible">
      <el-dialog :title="rowName"
                 :visible.sync="detailsDialogVisible"
                 width="50%"
                 :close-on-click-modal="false"
                 class="details-data-list">
        <div class="details-data-title">{{ detailsDataTitle }}</div>
        <el-table :data="detailsDataList"
                  row-key="id"
                  lazy
                  tooltip-effect="light"
                  :load="loadDataListChildren"
                  :tree-props="{ children: 'children', hasChildren: 'hasChildren' }">
          <el-table-column width="50" />
          <el-table-column prop="key"
                           width="180"
                           label="Key">
          </el-table-column>
          <el-table-column prop="value"
                           show-overflow-tooltip
                           label="Value">
            <template slot-scope="scope">
              {{ scope.row.value }}
            </template>
          </el-table-column>
        </el-table>
      </el-dialog>
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
               :class="[tagScope.row && item.number === tagScope.row.tag ? 'icon-border' : '']"
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
              {{ $t('public.sure')}}
            </el-button>
          </div>
          <div class="tag-button-container">
            <el-button type="primary"
                       size="mini"
                       class="custom-btn"
                       @click="clearIcon(tagScope,$event)"
                       plain>
              {{ $t('public.clear')}}
            </el-button>
          </div>
          <div class="tag-button-container">
            <el-button type="primary"
                       size="mini"
                       class="custom-btn"
                       @click="cancelChangeIcon(tagScope.row)"
                       plain>
              {{ $t('public.cancel')}}
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import RequestService from '../../services/request-service';
import CommonProperty from '@/common/common-property.js';
import Echarts from 'echarts';
export default {
  data() {
    return {
      tableSortTimer: null,
      showAllTimer: null,
      unhideTimer: null,
      loading: true,
      errorData: true,
      tagDialogShow: false,
      nodata: false,
      tagScope: {},
      iconValue: 0,
      // icon list of tag
      imageList: [],
      selectCheckAll: true,
      initOver: false, // Page initialization completed.
      dataCheckedSummary: [],
      selectedBarList: [],
      // The selected summarydir list to hide.
      hidenDirChecked: [],
      showTable: false,
      hideRecord: false,
      // Whether to display the echart
      showEchartPic: true,
      checkOptions: [],
      basearr: [],
      sortInfo: {},
      keyWord: '',
      // Number of data records returned by the interface.
      recordsNumber: 0,
      // Number of displayed records.
      showNumber: 0,
      delayTime: 500,
      selectArrayValue: [],
      customizedColumnOptions: [],
      // Set the type of customized
      customizedTypeObject: [],
      // Value of the vertical axis query interface brought by model source tracing
      modelObjectArray: [],
      summaryDirList: undefined,
      // Table filter condition
      tableFilter: {},
      echartNoData: true,
      // Encapsulate the data returned by the background interface.
      lineagedata: {},
      // Create an array of the type and filter the mandatory options from the array.
      createType: {
        StorageDataset: true,
        ImageFolderDataset: true,
        ImageFolderDatasetV2: true,
        MnistDataset: true,
        MindDataset: true,
        GeneratorDataset: true,
        TFRecordDataset: true,
        ManifestDataset: true,
        Cifar10Dataset: true,
        Cifar100Dataset: true,
        Schema: true,
        VOCDataset: true,
      },
      // echart parallel line coordinate system
      parallelEchart: null,
      deviceNum: 'device_num',
      shuffleTitle: 'Shuffle',
      repeatTitle: 'Repeat',
      categoryType: 'category',
      objectType: 'object',
      type: {
        batch: 'BatchDataset',
        shuffle: 'ShuffleDataset',
        repeat: 'RepeatDataset',
        mapData: 'MapDataset',
      },
      batchNode: 'Batch',
      echart: {
        brushData: [],
        // Data of echart  need to be displayed
        showData: [],
      },
      text: this.$t('modelTraceback.summaryPath'),
      // Selected option
      checkedSeries: [],
      // fixed option
      fixedSeries: [],
      // other option can be selected
      noFixedSeries: [],
      // Array of all options
      totalSeries: [],
      // Page data
      pagination: {
        currentPage: 1,
        pageSize: 8,
        total: 0,
        layout: 'total, prev, pager, next, jumper',
      },
      // Summary path column
      dirPathList: ['summary_dir'],
      // Options that support sorting
      sortArray: [
        this.$t('modelTraceback.summaryPath'),
        'loss',
        this.$t('modelTraceback.network'),
        this.$t('modelTraceback.optimizer'),
        this.$t('modelTraceback.trainingSampleNum'),
        this.$t('modelTraceback.testSampleNum'),
        this.$t('modelTraceback.learningRate'),
        'epoch',
        'batch_size',
        this.$t('modelTraceback.deviceNum'),
        this.$t('modelTraceback.modelSize'),
        this.$t('modelTraceback.lossFunc'),
      ],
      numberTypeIdList: [
        'train_dataset_count',
        'test_dataset_count',
        'epoch',
        'batch_size',
        'model_size',
        'loss',
        'learning_rate',
        'device_num',
      ],
      valueType: {
        float: 'float',
        int: 'int',
        string: 'string',
        model_size: 'model_size',
        learning_rate: 'learning_rate',
        dataset_mark: 'dataset_mark',
      },
      table: {
        columnOptions: {
          summary_dir: {
            label: this.$t('modelTraceback.summaryPath'),
            required: true,
          },
          dataset_mark: {
            label: this.$t('modelTraceback.dataProcess'),
          },
          model_size: {
            label: this.$t('modelTraceback.modelSize'),
          },
          network: {
            label: this.$t('modelTraceback.network'),
          },
          loss: {
            label: 'loss',
          },
          optimizer: {
            label: this.$t('modelTraceback.optimizer'),
          },
          train_dataset_count: {
            label: this.$t('modelTraceback.trainingSampleNum'),
          },
          test_dataset_count: {
            label: this.$t('modelTraceback.testSampleNum'),
          },
          learning_rate: {
            label: this.$t('modelTraceback.learningRate'),
          },
          epoch: {
            label: 'epoch',
          },
          batch_size: {
            label: 'batch_size',
          },
          device_num: {
            label: this.$t('modelTraceback.deviceNum'),
          },
          loss_function: {
            label: this.$t('modelTraceback.lossFunc'),
          },
        },
        // All options of the column in the table
        column: [],
        // Data of the table
        data: [],
      },

      tempFormateData: {},
      detailsDialogVisible: false,
      detailsDataTitle: '',
      detailsDataList: [],
      rowName: this.$t('dataTraceback.details'),
      replaceStr: {
        metric: 'metric/',
        userDefined: 'user_defined/',
      },
    };
  },
  computed: {},
  mounted() {
    this.imageList = [];
    for (let i = 1; i <= 10; i++) {
      const obj = {};
      obj.number = i;
      obj.iconAdd = require('@/assets/images/icon' + obj.number + '.svg');
      this.imageList.push(obj);
    }
    document.title = `${this.$t('summaryManage.dataTraceback')}-MindInsight`;
    document.addEventListener('click', this.blurFloat, true);
    this.$nextTick(() => {
      this.init();
    });
  },
  methods: {
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
      this.tagScope = scope;
      this.iconValue = row.tag >= 0 ? row.tag : 0;
      if (this.tagDialogShow) {
        this.tagDialogShow = false;
        this.removeIconBorder();
        return;
      }
      this.addIconBorder(row);
      this.tagDialogShow = true;
      const ev = window.event || event;
      document.getElementById('tag-dialog').style.top = ev.clientY - 130 + 'px';
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
     *  icon value change
     * @param {Object} row
     * @param {Number} num
     * @param {Object} event
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
     * Save the modification of the icon
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
      this.tagDialogShow = false;
    },

    /**
     * Cancel Save
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
        this.selectArrayValue.push(item.value);
      });

      this.selectCheckAll = !this.selectCheckAll;
      this.$nextTick(() => {
        this.initChart();
      });
      const list = [];
      this.checkOptions.forEach((item) => {
        this.selectArrayValue.forEach((i) => {
          if (i === item.value) {
            list.push(i);
          }
        });
      });

      if (this.selectedBarList) {
        const resultArray = this.hideDataMarkTableData();
        this.table.column = this.dirPathList.concat(resultArray, list);
      } else {
        this.table.column = this.dirPathList.concat(list);
      }
    },

    /**
     * deselect all
     */
    deselectAll() {
      this.selectArrayValue = [];
      this.checkOptions.forEach((item) => {
        if (item.disabled) {
          this.selectArrayValue.push(item.value);
        }
      });
      this.selectCheckAll = false;
      this.$nextTick(() => {
        this.initChart();
      });
      const list = [];
      this.checkOptions.forEach((item) => {
        this.selectArrayValue.forEach((i) => {
          if (i === item.value) {
            list.push(i);
          }
        });
      });
      if (this.selectedBarList) {
        const resultArray = this.hideDataMarkTableData();
        this.table.column = this.dirPathList.concat(resultArray, list);
      } else {
        this.table.column = this.dirPathList.concat(list);
      }
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
     * Cancel Save Editing
     * @param {Object} row
     */
    cancelRemarksValue(row) {
      row.editShow = true;
      row.remark = this.beforeEditValue;
      row.isError = false;
    },

    /**
     * After the remark or tag is modified,invoke the interface and save the modification
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
     * Hidden records
     */
    hiddenRecords() {
      this.hideRecord = true;
      if (this.dataCheckedSummary.length) {
        this.dataCheckedSummary.forEach((i) => {
          this.hidenDirChecked.push(i.summary_dir);
        });
      }
      this.$store.commit('setHidenDirChecked', this.hidenDirChecked);
      if (this.hidenDirChecked.length) {
        const tempEchartData = this.echart.brushData.slice();
        this.hidenDirChecked.forEach((dir) => {
          tempEchartData.forEach((item, index) => {
            if (item.summary_dir === dir) {
              tempEchartData.splice(index, 1);
            }
          });
        });
        const tableTemp = this.table.data.slice();
        this.hidenDirChecked.forEach((dir) => {
          tableTemp.forEach((item, index) => {
            if (item.summary_dir === dir) {
              tableTemp.splice(index, 1);
            }
          });
        });
        this.dataCheckedSummary = [];
        this.table.data = tableTemp;
        this.showNumber = tableTemp.length;
        this.echart.showData = tempEchartData;
        this.$refs.table.clearSelection();
        if (this.echart.showData.length > 0) {
          this.$nextTick(() => {
            this.initChart();
          });
        } else {
          this.showEchartPic = false;
        }
      }
      this.hideRecord = false;
    },

    /**
     * Unhide
     */
    unhideRecords() {
      if (this.unhideTimer) {
        clearTimeout(this.unhideTimer);
        this.unhideTimer = null;
      }
      this.unhideTimer = setTimeout(() => {
        this.showEchartPic = true;
        this.$refs.table.clearSelection();
        if (this.parallelEchart) {
          this.parallelEchart.clear();
        }
        this.$store.commit('setHidenDirChecked', []);
        if (this.hidenDirChecked.length) {
          this.checkedSummary = [];
          this.hidenDirChecked = [];
        }
        this.checkOptions = [];
        this.selectArrayValue = [];
        this.basearr = [];
        const params = {
          body: {},
        };
        const tempParam = {
          sorted_name: this.sortInfo.sorted_name,
          sorted_type: this.sortInfo.sorted_type,
        };
        this.summaryDirList = this.$store.state.summaryDirList;
        this.tableFilter.summary_dir = {
          in: this.summaryDirList,
        };
        params.body = Object.assign(
            params.body,
            this.chartFilter,
            tempParam,
            this.tableFilter,
        );
        this.queryLineagesData(params);
      }, this.delayTime);
    },
    /**
     * Input search filtering in the select module
     */
    myfilter() {
      const queryString = this.keyWord;
      const restaurants = this.basearr;
      const results = queryString
        ? this.createFilter(queryString, restaurants)
        : restaurants;
      this.checkOptions = results;
    },

    /**
     * Input search filtering in the select module
     * @param {String} queryString
     * @param {Array} restaurants
     * @return {Array}
     */
    createFilter(queryString, restaurants) {
      const list = [];
      restaurants.forEach((item) => {
        const object = {};
        if (
          item &&
          item.label.toLowerCase().indexOf(queryString.toLowerCase()) >= 0
        ) {
          object.label = item.label;
          object.value = item.value;
          object.disabled = item.disabled;
          list.push(object);
        }
      });
      return list;
    },

    selectinputFocus() {
      // the text box is restored to empty
      this.keyWord = '';
      this.checkOptions = this.basearr;
    },

    /**
     * Selected data in the table
     */
    selectValueChange() {
      const templist = [];
      this.basearr.forEach((item) => {
        templist.push(item.label);
      });
      if (templist.length > this.selectArrayValue.length) {
        this.selectCheckAll = false;
      } else {
        this.selectCheckAll = true;
      }
      this.$nextTick(() => {
        this.initChart();
      });
      const list = [];
      this.basearr.forEach((item) => {
        this.selectArrayValue.forEach((i) => {
          if (i === item.value) {
            list.push(i);
          }
        });
      });

      if (this.selectedBarList) {
        const resultArray = this.hideDataMarkTableData();
        this.table.column = this.dirPathList.concat(resultArray, list);
      } else {
        this.table.column = this.dirPathList.concat(list);
      }
    },

    /**
     * init
     */
    init() {
      this.customizedColumnOptions =
        this.$store.state.customizedColumnOptions || [];
      this.table.columnOptions = Object.assign(
          this.table.columnOptions,
          this.customizedColumnOptions,
      );
      // Obtain the value of summary_dir from the store,
      this.summaryDirList = this.$store.state.summaryDirList;
      this.selectedBarList = this.$store.state.selectedBarList;
      if (this.selectedBarList && this.selectedBarList.length) {
        this.tableFilter = {};
      } else {
        this.tableFilter.lineage_type = {in: ['dataset']};
      }
      const params = {};
      if (this.summaryDirList) {
        this.tableFilter.summary_dir = {in: this.summaryDirList};
      } else {
        this.tableFilter.summary_dir = undefined;
      }
      params.body = Object.assign({}, this.tableFilter);
      this.queryLineagesData(params);
    },

    /*
     * Initialize the echart diagram.
     */
    initChart() {
      const parallelAxis = [];
      const selectedBarList = this.$store.state.selectedBarList;
      const data = [];
      const arrayTemp = [];
      if (selectedBarList && selectedBarList.length) {
        selectedBarList.forEach((item) => {
          const value = this.customizedTypeObject[item];
          const obj = {
            name: this.table.columnOptions[item].label,
            id: item,
            checked: true,
          };
          if (value && value.type === this.valueType.float) {
            obj.type = this.valueType.float;
          } else if (value && value.type === this.valueType.int) {
            obj.type = this.valueType.int;
          }
          arrayTemp.push(obj);
        });
      }
      const list = [];
      this.basearr.forEach((item) => {
        this.selectArrayValue.forEach((i) => {
          if (i === item.value) {
            const obj = {};
            obj.id = item.value;
            obj.name = item.label;
            list.push(obj);
          }
        });
      });
      const totalBarArray = arrayTemp.concat(list);
      this.echart.showData.forEach((val, i) => {
        let item = {};
        item = {
          lineStyle: {
            normal: {
              color: CommonProperty.commonColorArr[i % 10],
            },
          },
          value: [],
        };
        totalBarArray.forEach((obj) => {
          item.value.push(val[obj.id]);
        });
        data.push(item);
      });

      totalBarArray.forEach((content, i) => {
        const obj = {dim: i, name: content.name, id: content.id};
        if (
          content.name === this.repeatTitle ||
          content.name === this.shuffleTitle ||
          content.id === this.deviceNum ||
          (content.type && content.type === this.valueType.int)
        ) {
          obj.scale = true;
          obj.minInterval = 1;
          this.setColorOfSelectedBar(selectedBarList, obj);
        } else if (
          this.numberTypeIdList.includes(content.id) ||
          (content.type && content.type === this.valueType.float)
        ) {
          obj.scale = true;
          this.setColorOfSelectedBar(selectedBarList, obj);
        } else {
          // String type
          obj.type = this.categoryType;
          obj.axisLabel = {
            show: false,
          };
          this.setColorOfSelectedBar(selectedBarList, obj);
          if (content.id === this.valueType.dataset_mark) {
            obj.axisLabel = {
              show: false,
            };
          }
          const values = {};
          this.echart.showData.forEach((i) => {
            if (i[content.id] || i[content.id] === 0) {
              values[i[content.id]] = '';
            }
          });
          obj.data = Object.keys(values);
        }
        parallelAxis.push(obj);
      });

      const option = {
        backgroundColor: 'white',
        parallelAxis: parallelAxis,
        tooltip: {
          trigger: 'axis',
        },
        parallel: {
          top: 30,
          left: 90,
          right: 100,
          bottom: 12,
          parallelAxisDefault: {
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
            width: 1,
            opacity: 1,
          },
          data: data,
        },
      };
      if (this.parallelEchart) {
        this.parallelEchart.off('axisareaselected', null);
        window.removeEventListener('resize', this.resizeChart, false);
      } else {
        this.parallelEchart = Echarts.init(
            document.querySelector('#data-echart'),
        );
      }
      this.parallelEchart.setOption(option, true);
      window.addEventListener('resize', this.resizeChart, false);
      this.chartEventsListen(parallelAxis);
    },
    chartEventsListen(parallelAxis) {
      this.parallelEchart.on('axisareaselected', (params) => {
        this.recordsNumber = 0;
        this.showNumber = 0;
        const key = params.parallelAxisId;
        const range = params.intervals[0] || [];
        const [axisData] = parallelAxis.filter((i) => {
          return i.id === key;
        });
        if (axisData && range.length === 2) {
          if (axisData.type === this.categoryType) {
            const selectedAxisKeys = axisData.data.slice(
                range[0],
                range[1] + 1,
            );
            this.echart.brushData = this.echart.showData.filter((i) => {
              return selectedAxisKeys.includes(i[key]);
            });
          } else {
            this.echart.brushData = this.echart.showData.filter((i) => {
              return i[key] >= range[0] && i[key] <= range[1];
            });
          }
          const tempList = this.echart.brushData;
          const summaryList = [];
          tempList.forEach((item) => {
            summaryList.push(item.summary_dir);
          });
          // The summaryList value could not be saved in the destroy state.
          this.dataCheckedSummary = [];
          this.$store.commit('setSummaryDirList', summaryList);
          this.tableFilter.summary_dir = {in: summaryList};
          if (!tempList.length) {
            this.summaryDirList = [];
            this.lineagedata.serData = undefined;
            this.showTable = false;
            this.nodata = true;
            this.echartNoData = true;
          } else {
            this.echart.showData = this.echart.brushData;
            this.$nextTick(() => {
              this.initChart();
            });
            this.pagination.currentPage = 1;
            this.pagination.total = this.echart.brushData.length;
            this.table.data = this.echart.brushData.slice(
                (this.pagination.currentPage - 1) * this.pagination.pageSize,
                this.pagination.currentPage * this.pagination.pageSize,
            );
            const tableLength = this.table.data.length;
            this.recordsNumber = tableLength;
            this.showNumber = tableLength;
            this.showTable = true;
          }
        }
      });
    },
    /**
     * Set the color of the model tracing axis.
     * @param {Array} selectedBarList
     * @param {Object} obj
     */
    setColorOfSelectedBar(selectedBarList, obj) {
      if (selectedBarList && obj.dim < selectedBarList.length) {
        obj.nameTextStyle = {
          color: '#00a5a7',
        };
        obj.axisLabel = {
          show: true,
          textStyle: {
            color: '#00a5a7',
          },
          formatter: function(val) {
            if (typeof val !== 'string') {
              return val;
            }
            const strs = val.split('');
            let str = '';
            const maxStringLength = 100;
            const showStringLength = 12;
            if (val.length > maxStringLength) {
              return val.substring(0, showStringLength) + '...';
            } else {
              for (let i = 0, s = ''; (s = strs[i++]); ) {
                str += s;
                if (!(i % showStringLength)) {
                  str += '\n';
                }
              }
              return str;
            }
          },
        };
        obj.axisLine = {
          show: true,
          lineStyle: {
            color: '#00a5a7',
          },
        };
      } else {
        // Text color
        obj.nameTextStyle = {
          color: 'black',
        };
      }
    },

    /**
     * jump to train dashboard
     * @param {String} val
     */
    jumpToTrainDashboard(val) {
      const trainId = encodeURIComponent(val);
      const routeUrl = this.$router.resolve({
        path: '/train-manage/training-dashboard',
        query: {id: trainId},
      });
      window.open(routeUrl.href, '_blank');
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
        if (key === this.valueType.learning_rate) {
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
     * The detailed information is displayed in the dialog box.
     * @param {String} val
     * @param {Object} scope
     */
    showDialogData(val, scope) {
      const emptyObjectStr = '{}';
      if (typeof val !== this.valueType.string || val === emptyObjectStr) {
        return;
      } else {
        const isJson = this.isJSON(val);
        if (!isJson) {
          return;
        }
      }
      this.rowName = `${scope.column.label}${this.$t('dataTraceback.details')}`;
      this.detailsDialogVisible = true;
      this.detailsDataTitle = scope.row.summary_dir;
      this.detailsDataList = this.formateJsonString(val);
    },

    /**
     * Checks whether the value is a JSON character string.
     *  @param {String} val
     * @return {Boolean}
     */
    isJSON(val) {
      try {
        JSON.parse(val);
        return true;
      } catch (e) {
        return false;
      }
    },

    /**
     * set object value
     * @param {Array} array
     * @param {boolean} booleanValue
     */
    setObjectValue(array, booleanValue) {
      array.forEach((val) => {
        const obj = {};
        obj.label = val.name;
        obj.required = booleanValue;
        this.table.columnOptions[val.id] = obj;
      });
    },

    /**
     * get data of table
     * @param {Object} params
     */
    queryTableLineagesData(params) {
      RequestService.queryLineagesData(params)
          .then(
              (res) => {
                if (!res || !res.data) {
                  this.nodata = true;
                  return;
                }
                this.nodata = false;
                this.errorData = false;
                this.lineagedata = this.formateOriginData(res.data);
                const serData = this.lineagedata.serData;
                this.table.data = JSON.parse(JSON.stringify(serData));
              },
              (error) => {
                this.errorData = true;
                this.nodata = true;
              },
          )
          .catch(() => {
            this.errorData = true;
            this.nodata = true;
          });
    },

    /**
     * Method of invoking the interface
     * @param {Object} params
     */
    queryLineagesData(params) {
      RequestService.queryLineagesData(params)
          .then(
              (res) => {
                this.initOver = true;
                this.loading = false;
                this.echartNoData = false;
                if (!res || !res.data) {
                  this.nodata = true;
                  return;
                }
                this.nodata = false;
                this.errorData = false;
                this.customizedTypeObject = res.data.customized;
                let keys = Object.keys(this.customizedTypeObject);
                if (keys.length) {
                  keys = keys.map((i) => {
                    if (i.startsWith(this.replaceStr.userDefined)) {
                      return i.replace(this.replaceStr.userDefined, '[U]');
                    } else if (i.startsWith(this.replaceStr.metric)) {
                      return i.replace(this.replaceStr.metric, '[M]');
                    }
                  });
                  this.sortArray = this.sortArray.concat(keys);
                }
                // Model source tracing filtering parameters
                this.selectedBarList = this.$store.state.selectedBarList;
                if (this.selectedBarList && this.selectedBarList.length) {
                  const tempList = JSON.parse(JSON.stringify(res.data.object));
                  const list = [];
                  const metricKeys = {};
                  tempList.forEach((item) => {
                    if (item.model_lineage) {
                      const modelData = JSON.parse(
                          JSON.stringify(item.model_lineage),
                      );
                      modelData.model_size = parseFloat(
                          ((modelData.model_size || 0) / 1024 / 1024).toFixed(2),
                      );
                      const keys = Object.keys(modelData.metric || {});
                      if (keys.length) {
                        keys.forEach((key) => {
                          if (
                            modelData.metric[key] ||
                        modelData.metric[key] === 0
                          ) {
                            const temp = this.replaceStr.metric + key;
                            metricKeys[temp] = key;
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
                      list.push(modelData);
                    }
                  });
                  this.modelObjectArray = [];
                  for (let i = 0; i < list.length; i++) {
                    const modelObject = {};
                    for (let j = 0; j < this.selectedBarList.length; j++) {
                      const tempObject = list[i];
                      const key = this.selectedBarList[j];
                      modelObject[key] = tempObject[key];
                    }
                    this.modelObjectArray.push(modelObject);
                  }
                }

                this.fixedSeries = [];
                this.noFixedSeries = [];
                this.checkedSeries = [];
                this.lineagedata = this.formateOriginData(res.data);
                this.totalSeries = this.lineagedata.fullNodeList;
                if (!this.totalSeries.length) {
                  this.echartNoData = true;
                  this.nodata = true;
                } else {
                  this.nodata = false;
                }
                this.totalSeries.forEach((nodeItem) => {
                  if (this.createType[nodeItem.name]) {
                    nodeItem.checked = true;
                    this.fixedSeries.push(nodeItem);
                  } else {
                    nodeItem.checked = false;
                    this.noFixedSeries.push(nodeItem);
                  }
                });
                this.noFixedSeries.forEach((item) => {
                  item.checked = true;
                });
                this.getCheckedSerList();
                if (this.fixedSeries.length) {
                  this.setObjectValue(this.fixedSeries, true);
                }
                if (this.noFixedSeries.length) {
                  this.setObjectValue(this.noFixedSeries, false);
                }
                const list1 = this.fixedSeries.concat(this.noFixedSeries);
                list1.forEach((item, index) => {
                  this.checkOptions[index] = {};
                  this.basearr[index] = {};
                  this.checkOptions[index].label = item.name;
                  this.checkOptions[index].value = item.id;
                  if (this.createType[item.name]) {
                    this.checkOptions[index].disabled = true;
                    this.basearr[index].disabled = true;
                  }
                  this.basearr[index].label = item.name;
                  this.basearr[index].value = item.id;
                });
                this.checkOptions.forEach((item) => {
                  this.selectArrayValue.push(item.value);
                });
                this.hidenDirChecked = this.$store.state.hidenDirChecked || [];
                this.echart.brushData = this.lineagedata.serData;
                if (this.hidenDirChecked.length) {
                  const listdada = this.lineagedata.serData.slice();
                  this.hidenDirChecked.forEach((item) => {
                    listdada.forEach((i, index) => {
                      if (i.summary_dir === item) {
                        listdada.splice(index, 1);
                      }
                    });
                  });
                  if (listdada.length) {
                    this.showEchartPic = true;
                  } else {
                    this.showEchartPic = false;
                  }
                  this.echart.showData = listdada;
                } else {
                  this.echart.showData = this.echart.brushData;
                  this.showEchartPic = true;
                }
                this.resizeChart();
                this.setEchartValue();
                this.$nextTick(() => {
                  this.initChart();
                });
                // Total number of pages in the table
                this.pagination.total = res.data.count;
                // Data encapsulation of the table
                let data = [];
                data = this.setTableData();
                this.table.data = data;
                this.showTable = true;
                if (this.selectedBarList) {
                  const resultArray = this.hideDataMarkTableData();
                  this.table.column = this.dirPathList.concat(
                      resultArray,
                      this.checkedSeries.map((i) => i.id),
                  );
                } else {
                  this.table.column = this.dirPathList.concat(
                      this.checkedSeries.map((i) => i.id),
                  );
                }
              },
              (error) => {
                this.loading = false;
                this.initOver = true;
                this.showEchartPic = false;
                this.errorData = true;
                this.nodata = true;
              },
          )
          .catch(() => {
            this.loading = false;
            this.initOver = true;
            this.showEchartPic = false;
            this.errorData = true;
            this.nodata = true;
          });
    },

    /**
     *  Gets the selected items and updates the select all state.
     */
    getCheckedSerList() {
      this.checkedSeries = [];
      this.totalSeries.forEach((nodeItem) => {
        if (nodeItem.checked) {
          this.checkedSeries.push(nodeItem);
        }
      });
    },

    /**
     *  The window size changes. Resizing Chart
     */
    resizeChart() {
      if (
        document.getElementById('data-echart') &&
        document.getElementById('data-echart').style.display !== 'none' &&
        this.parallelEchart
      ) {
        this.parallelEchart.resize();
      }
    },

    /**
     * reset echart data.Show all data
     */
    echartShowAllData() {
      // The first page is displayed.
      this.nodata = false;
      if (this.showAllTimer) {
        clearTimeout(this.showAllTimer);
        this.showAllTimer = null;
      }
      this.showAllTimer = setTimeout(() => {
        this.initOver = false;
        this.echartNoData = false;
        this.showEchartPic = true;
        this.selectCheckAll = true;
        // checkOptions initializate to an empty array
        this.checkOptions = [];
        this.selectArrayValue = [];
        this.basearr = [];
        this.pagination.currentPage = 1;
        this.$store.commit('setSummaryDirList', undefined);
        this.$store.commit('setSelectedBarList', []);
        if (this.parallelEchart) {
          this.parallelEchart.clear();
        }
        this.$refs.table.clearSelection();
        this.init();
      }, this.delayTime);
    },

    /**
     * The table column data is deleted from the data processing result.
     * @return {Array}
     */
    hideDataMarkTableData() {
      const result = [];
      this.selectedBarList.forEach((item) => {
        if (item !== this.valueType.dataset_mark) {
          result.push(item);
        }
      });
      return result;
    },

    /**
     * Selected rows of tables
     * @param {Object} val
     */
    handleSelectionChange(val) {
      // summary_dir cannot be stored here.If it is not selected ,it cannot be stroed correctly.
      if (this.hideRecord) {
        return;
      }
      this.dataCheckedSummary = val;
      if (val.length) {
        this.echart.showData = val;
      } else {
        this.echart.showData = this.echart.brushData;
      }
      this.$nextTick(() => {
        this.initChart();
      });
    },

    setEchartValue() {
      if (this.modelObjectArray.length) {
        const list = this.echart.showData;
        for (let i = 0; i < list.length; i++) {
          const temp = this.modelObjectArray[i];
          this.echart.showData[i] = Object.assign(
              this.echart.showData[i],
              temp,
          );
        }
      }
    },

    /**
     * Sort by path parameter
     * @param {Object} data
     */
    tableSortChange(data) {
      if (this.tableSortTimer) {
        clearTimeout(this.tableSortTimer);
        this.tableSortTimer = null;
      }
      this.tableSortTimer = setTimeout(() => {
        this.sortInfo.sorted_name = data.prop;
        this.sortInfo.sorted_type = data.order;
        const params = {};
        const tempParam = {
          sorted_name: data.prop,
          sorted_type: data.order,
        };
        this.checkOptions = [];
        this.selectArrayValue = [];
        this.basearr = [];
        this.pagination.currentPage = 1;
        this.summaryDirList = this.$store.state.summaryDirList;
        if (this.summaryDirList) {
          this.tableFilter.summary_dir = {in: this.summaryDirList};
        } else {
          this.tableFilter.summary_dir = undefined;
        }
        params.body = Object.assign({}, tempParam, this.tableFilter);
        this.queryLineagesData(params);
      }, this.delayTime);
    },

    /**
     * Setting Table Data
     * @param {Number} val
     */
    handleCurrentChange(val) {
      this.pagination.currentPage = val;
      const data = this.setTableData();
      const summaryDirList = [];
      data.forEach((item) => {
        summaryDirList.push(item.summary_dir);
      });
      const params = {
        body: {},
      };
      const tempParam = {
        sorted_name: this.sortInfo.sorted_name,
        sorted_type: this.sortInfo.sorted_type,
      };
      this.tableFilter.summary_dir = {
        in: summaryDirList,
      };
      params.body = Object.assign(
          params.body,
          this.chartFilter,
          tempParam,
          this.tableFilter,
      );
      this.queryTableLineagesData(params);
    },

    /**
     * Setting Table Data
     * @return {Array}
     */
    setTableData() {
      let data = [];
      // Table data encapsulation
      const pathData = JSON.parse(JSON.stringify(this.echart.brushData));
      // Obtain table data based on the page number and number of records.
      data = pathData.slice(
          (this.pagination.currentPage - 1) * this.pagination.pageSize,
          this.pagination.currentPage * this.pagination.pageSize,
      );
      this.recordsNumber = data.length;
      if (this.hidenDirChecked.length) {
        this.hidenDirChecked.forEach((dir) => {
          data.forEach((item, index) => {
            if (item.summary_dir === dir) {
              data.splice(index, 1);
            }
          });
        });
      }
      this.showNumber = data.length;
      return data;
    },

    /**
     * Chart data encapsulation
     * @param {Object} data
     * @return {Object}
     */
    formateOriginData(data) {
      if (!data || !data.object) {
        return {};
      }
      // Preliminarily filter the required data from the original data and form a unified format.
      const objectDataArr = [];
      data.object.forEach((object) => {
        this.tempFormateData = {
          nodeList: [],
          children: false,
          summary_dir: object.summary_dir,
          remark: object.added_info.remark ? object.added_info.remark : '',
          tag: object.added_info.tag,
        };
        if (JSON.stringify(object.dataset_graph) !== '{}') {
          this.getSingleRunData(object.dataset_graph);
        }
        objectDataArr.push(JSON.parse(JSON.stringify(this.tempFormateData)));
      });
      // The data in the unified format is combined by category.
      const fullNodeList = [];
      const tempDic = {};
      objectDataArr.forEach((objectData) => {
        if (fullNodeList.length) {
          let startIndex = 0;
          let tempNodeListMap = fullNodeList.map((nodeObj) => nodeObj.name);
          objectData.nodeList.forEach((nodeItem) => {
            const tempIndex = tempNodeListMap.indexOf(
                nodeItem.name,
                startIndex,
            );
            if (tempIndex === -1) {
              if (!tempDic[nodeItem.name]) {
                tempDic[nodeItem.name] = 0;
              }
              tempDic[nodeItem.name]++;
              let tempId = '';
              const createKey = Object.keys(this.createType);
              if (createKey.includes(nodeItem.name)) {
                tempId = nodeItem.name;
              } else {
                tempId = `${nodeItem.name}${tempDic[nodeItem.name]}`;
              }
              fullNodeList.splice(startIndex, 0, {
                name: nodeItem.name,
                id: tempId,
              });
              nodeItem.id = tempId;
              startIndex++;
              tempNodeListMap = fullNodeList.map((nodeObj) => nodeObj.name);
            } else {
              nodeItem.id = fullNodeList[tempIndex].id;
              startIndex = tempIndex + 1;
            }
          });
        } else {
          objectData.nodeList.forEach((nodeItem) => {
            if (!tempDic[nodeItem.name]) {
              tempDic[nodeItem.name] = 0;
            }
            tempDic[nodeItem.name]++;
            const createKey = Object.keys(this.createType);
            if (createKey.includes(nodeItem.name)) {
              fullNodeList.push({
                name: nodeItem.name,
                id: nodeItem.name,
              });
              nodeItem.id = nodeItem.name;
            } else {
              fullNodeList.push({
                name: nodeItem.name,
                id: `${nodeItem.name}${tempDic[nodeItem.name]}`,
              });
              nodeItem.id = `${nodeItem.name}${tempDic[nodeItem.name]}`;
            }
          });
        }
      });
      // Obtain the value of run on each coordinate.
      const serData = [];
      objectDataArr.forEach((objectData) => {
        const curDataObj = {};
        objectData.nodeList.forEach((nodeItem) => {
          curDataObj[nodeItem.id] = nodeItem.value;
        });
        curDataObj.children = objectData.children;
        curDataObj.summary_dir = objectData.summary_dir;

        // set remark value
        curDataObj.remark = objectData.remark;
        // set tag value
        curDataObj.tag = objectData.tag;
        // set remark icon is show
        curDataObj.editShow = true;
        curDataObj.isError = false;
        serData.push(curDataObj);
      });
      const formateData = {
        fullNodeList: fullNodeList,
        serData: serData,
      };
      return formateData;
    },

    /**
     * Get single run data
     * @param {Object} nodeObj
     */
    getSingleRunData(nodeObj) {
      if (nodeObj.children && nodeObj.children.length) {
        if (nodeObj.children.length > 1) {
          this.tempFormateData.children = true;
        }
        this.getSingleRunData(nodeObj.children[0]);
      }
      let nodeType = nodeObj.op_type;
      let nodeName = '';
      let nodeValue = '';

      if (nodeType === this.type.batch) {
        nodeName = this.batchNode;
        nodeValue = `batch_size:${nodeObj.batch_size},drop_remainder:${nodeObj.drop_remainder}`;
      } else if (nodeType === this.type.shuffle) {
        nodeName = this.shuffleTitle;
        nodeValue = nodeObj.buffer_size;
      } else if (nodeType === this.type.repeat) {
        nodeValue = nodeObj.count;
        nodeName = this.repeatTitle;
      } else if (nodeType === this.type.mapData) {
        const nodeOptions = nodeObj.operations;
        nodeType = nodeOptions.forEach((nodeOption) => {
          nodeName = `Map_${nodeOption.tensor_op_name}`;
          delete nodeOption.tensor_op_module;
          delete nodeOption.tensor_op_name;
          nodeValue = JSON.stringify(nodeOption);
          this.tempFormateData.nodeList.push({
            name: nodeName,
            id: ``,
            value: nodeValue,
          });
        });
      } else {
        nodeValue = JSON.stringify(nodeObj);
        nodeName = nodeType;
      }
      if (nodeObj.op_type !== this.type.mapData) {
        this.tempFormateData.nodeList.push({
          name: nodeName,
          id: ``,
          value: nodeValue,
        });
      }
    },
    /**
     * Converts JSON strings.
     * @param {String} str
     * @return {Array}
     */
    formateJsonString(str) {
      if (!str) {
        return [];
      }
      const resultArr = [];
      const dataObj = JSON.parse(str);
      const keys = Object.keys(dataObj);
      keys.forEach((key, index) => {
        const tempData = {
          id: index + 1,
          hasChildren: false,
          key: key,
          value: '',
        };
        if (dataObj[key] === null) {
          tempData.value = 'None';
        } else if (
          typeof dataObj[key] === this.objectType &&
          dataObj[key] !== null
        ) {
          if (!(dataObj[key] instanceof Array)) {
            tempData.hasChildren = true;
            tempData.children = [];
            Object.keys(dataObj[key]).forEach((k, j) => {
              const item = {};
              item.key = k;
              if (dataObj[key][k] === null) {
                item.value = 'None';
              } else {
                item.value = dataObj[key][k];
              }
              item.id =
                `${new Date().getTime()}` + `${this.$store.state.tableId}`;
              this.$store.commit('increaseTableId');
              tempData.children.push(item);
            });
          }
          tempData.value = JSON.stringify(dataObj[key]);
        } else {
          tempData.value = dataObj[key];
        }
        resultArr.push(tempData);
      });
      return resultArr;
    },
    loadDataListChildren(tree, treeNode, resolve) {
      setTimeout(() => {
        resolve(tree.children);
      });
    },
  },

  /**
   * Destroy the page
   */
  destroyed() {
    this.tableSortTimer = null;
    this.showAllTimer = null;
    this.unhideTimer = null;
    if (this.dataCheckedSummary && this.dataCheckedSummary.length) {
      const summaryDirList = [];
      this.dataCheckedSummary.forEach((item) => {
        summaryDirList.push(item.summary_dir);
      });
      this.$store.commit('setSummaryDirList', summaryDirList);
    }
    if (this.parallelEchart) {
      window.removeEventListener('resize', this.resizeChart, false);
      this.parallelEchart.clear();
      this.parallelEchart = null;
    }
  },
  components: {},
};
</script>
<style lang="scss">
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
.select-inner-input {
  width: calc(100% - 140px);
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
.btn-disabled {
  cursor: not-allowed !important;
}
#cl-data-traceback {
  display: flex;
  height: 100%;
  overflow-y: auto;
  position: relative;
  background: #fff;
  .el-select > .el-input {
    width: 280px !important;
    max-width: 500px !important;
  }
  .el-table th.is-leaf {
    background: #f5f7fa;
  }
  .el-table td,
  .el-table th.is-leaf {
    border: 1px solid #ebeef5;
  }
  .inline-block-set {
    display: inline-block;
  }
  .icon-border {
    border: 1px solid #00a5a7 !important;
  }
  .btn-container-margin {
    margin: 0 10%;
  }
  .tag-button-container {
    display: inline-block;
    width: 33.3%;
    text-align: center;
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
  .tag-icon-container {
    width: 21px;
    height: 21px;
    border: 1px solid #e6e6e6;
    cursor: pointer;
    border-radius: 2px;
  }
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
      p {
        font-size: 16px;
        padding-top: 10px;
      }
    }
    .no-data-text {
      font-size: 16px;
      padding-top: 10px;
    }
  }
  .edit-text-container {
    display: inline-block;
    max-width: 140px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .btns-container {
    padding: 14px 32px 4px;
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
  .display-column {
    display: inline-block;
    padding-right: 6px;
  }
  .remark-input-style {
    width: 140px;
  }
  .cl-data-right {
    display: flex;
    flex-direction: column;
    flex: 1;
    background-color: #fff;
    -webkit-box-shadow: 0 1px 0 0 rgba(200, 200, 200, 0.5);
    box-shadow: 0 1px 0 0 rgba(200, 200, 200, 0.5);
    overflow: hidden;

    .data-checkbox-area {
      margin: 24px 32px 12px;
      height: 46px;
      display: flex;
      justify-content: flex-end;
      .select-container {
        padding-top: 10px;
        height: 46px;
        flex-grow: 1;
      }
      .btns {
        margin-left: 20px;
        padding-top: 12px;
        height: 46px;
      }
    }
    #data-echart {
      height: 32%;
      width: 100%;
      padding: 0 12px;
    }
    .echart-nodata-container {
      height: 32%;
      width: 100%;
    }
    .table-container {
      background-color: white;
      height: calc(68% - 130px);
      padding: 6px 32px;
      position: relative;
      .custom-label {
        max-width: calc(100% - 25px);
        padding: 0;
        vertical-align: middle;
      }
      .el-icon-warning {
        font-size: 16px;
      }
      .icon-container {
        padding-right: 5px;
        width: 20px;
      }
      .href-color {
        cursor: pointer;
        color: #3399ff;
      }
      .click-span {
        cursor: pointer;
      }
      .clear {
        clear: both;
      }
      .hide-count {
        height: 32px;
        line-height: 32px;
        color: red;
        float: right;
        margin-right: 10px;
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
  .el-dialog {
    min-width: 500px;
    padding-bottom: 30px;
  }
  .details-data-list {
    .el-table td,
    .el-table th.is-leaf {
      border: none;
      border-top: 1px solid #ebeef5;
    }
    .el-table {
      th {
        padding: 10px 0;
        border-top: 1px solid #ebeef5;
        .cell {
          border-left: 1px solid #d9d8dd;
          height: 14px;
          line-height: 14px;
        }
      }
      th:first-child {
        .cell {
          border-left: none;
        }
      }
      th:nth-child(2),
      td:nth-child(2) {
        max-width: 30%;
      }
      td {
        padding: 8px 0;
      }
    }
    .el-table__row--level-0 td:first-child:after {
      width: 20px;
      height: 1px;
      background: #ebeef5;
      z-index: 11;
      position: absolute;
      left: 0;
      bottom: -1px;
      content: '';
      display: block;
    }
    .el-table__row--level-1 {
      td {
        padding: 4px 0;
        position: relative;
      }
      td:first-child::before {
        width: 42px;
        background: #f0fdfd;
        border-right: 2px #00a5a7 solid;
        z-index: 10;
        position: absolute;
        left: 0;
        top: -1px;
        bottom: 0px;
        content: '';
        display: block;
      }
    }

    .el-table__row--level-1:first-child {
      td:first-child::before {
        bottom: 0;
      }
    }
    .el-dialog__title {
      font-weight: bold;
    }
    .el-dialog__body {
      max-height: 500px;
      padding-top: 10px;
      padding-bottom: 0px;
      overflow: auto;
      .details-data-title {
        margin-bottom: 20px;
      }
    }
  }
}
</style>

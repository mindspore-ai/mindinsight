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
  <div class="cl-histogram-manage">
    <div class="histogram-bk">
      <!-- Title area -->
      <div class="cl-title cl-histogram-title">
        <div class="cl-title-left">{{$t('histogram.titleText')}}
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
      <div class="cl-histogram-operate-content">
        <multiselectGroupComponents ref="multiselectGroupComponents"
                                    :checkListArr="tagList"
                                    @selectedChange="tagSelectedChanged"></multiselectGroupComponents>
      </div>
      <!-- Area for selecting a view type -->
      <div class="cl-histogram-view-type-select-content">
        <div class="view-title">{{$t('histogram.viewType')}}</div>
        <el-radio-group v-model="curViewName"
                        fill="#00A5A7"
                        text-color="#FFFFFF"
                        size="small"
                        @change="viewTypeChange">
          <el-radio-button :label=0>{{$t('histogram.overlay')}}</el-radio-button>
          <el-radio-button :label=1>{{$t('histogram.offset')}}</el-radio-button>
        </el-radio-group>
        <div class="view-title"
             v-if="!!curViewName">{{$t('histogram.xAxisTitle')}}</div>
        <el-radio-group v-model="curAxisName"
                        fill="#00A5A7"
                        text-color="#FFFFFF"
                        size="small"
                        v-if="!!curViewName"
                        :disabled="curViewName === 0"
                        @change="timeTypeChange">
          <el-radio-button :label=0>
            {{$t('histogram.step')}}
          </el-radio-button>
          <el-radio-button :label=1>
            {{$t('histogram.relativeTime') + $t('symbols.leftbracket') + 's' + $t('symbols.rightbracket')}}
          </el-radio-button>
          <el-radio-button :label=2>
            {{$t('histogram.absoluteTime')}}
          </el-radio-button>
        </el-radio-group>
      </div>
      <!-- Content display area -->
      <div class="cl-histogram-show-data-content">
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
               :key="sampleItem.domId"
               :class="sampleItem.fullScreen?'char-full-screen':''"
               v-show="sampleItem.show">
            <div class="chars-container">
              <div class="char-item-content"
                   :id="sampleItem.domId"></div>
              <div class="tag-title"
                   :title="sampleItem.tagName">{{sampleItem.tagName}}</div>
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
import CommonProperty from '../../common/common-property';
import echarts from 'echarts';
import {format, precisionRound} from 'd3';
import autoUpdate from '../../mixins/auto-update.vue';
const d3 = {format, precisionRound};
export default {
  mixins: [autoUpdate],
  data() {
    return {
      tagList: [], // Tag list.
      trainingJobId: this.$route.query.train_id, // ID of the current training job.
      summaryPath: this.$route.query.summaryPath,
      originDataArr: [], // List of all data.
      initOver: false, // Indicates whether the initialization is complete.
      curAxisName: 0, // Current time type.
      curViewName: 1, // Current view type.
      curFullTagDic: {}, // Dictionary that contains all the current tags.
      multiSelectedTagNames: {}, // Dictionary for storing the name of the selected tags.
      curFilterSamples: [], // List of data that meet the current filter criteria.
      curPageArr: [], // Data list on the current page.
      pageIndex: 0, // Current page number.
      pageSizes: [6], // The number of records on each page is optional.
      pageNum: 6, // Number of records on each page.
      zrDrawElement: {hoverDots: []},
      chartTipFlag: false,
      charResizeTimer: null,
      changeAxisTimer: null,
      changeViewTimer: null,
    };
  },
  computed: {},
  components: {
    multiselectGroupComponents,
  },
  watch: {},
  destroyed() {
    window.removeEventListener('resize', this.resizeCallback);
    if (this.curPageArr.length) {
      this.curPageArr.forEach((item) => {
        this.clearZrData(item);
      });
    }
    if (this.changeAxisTimer) {
      clearTimeout(this.changeAxisTimer);
      this.changeAxisTimer = null;
    }
    if (this.changeViewTimer) {
      clearTimeout(this.changeViewTimer);
      this.changeViewTimer = null;
    }
  },
  mounted() {
    this.init();
    window.addEventListener('resize', this.resizeCallback, false);
  },
  methods: {
    resizeCallback() {
      if (this.charResizeTimer) {
        clearTimeout(this.charResizeTimer);
        this.charResizeTimer = null;
      }

      this.charResizeTimer = setTimeout(() => {
        this.curPageArr.forEach((sampleItem) => {
          if (sampleItem.charObj) {
            sampleItem.charObj.resize();
          }
        });
      }, 500);
    },
    /**
     * Initialize
     */
    init() {
      if (!this.$route.query || !this.$route.query.train_id) {
        this.$message.error(this.$t('trainingDashboard.invalidId'));
        document.title = this.$t('histogram.titleText') + '-MindInsight';
        return;
      }
      document.title =
        decodeURIComponent(this.$route.query.train_id) +
        '-' +
        this.$t('histogram.titleText') +
        '-MindInsight';
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
        plugin_name: 'histogram',
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
            data.tags.forEach((tagName) => {
              if (!this.curFullTagDic[tagName]) {
                this.curFullTagDic[tagName] = true;
                tagList.push({
                  label: tagName,
                  checked: true,
                  show: true,
                });
                dataList.push({
                  tagName: tagName,
                  zr: null,
                  show: false,
                  fullScreen: false,
                  domId: `${tagName}`,
                  oriData: {},
                  charOption: {},
                  chartData: [],
                  charObj: null,
                });
              }
            });
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
          this.clearZrData(sampleItem);
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
    freshCurPageData() {
      this.curPageArr.forEach((item, index) => {
        if (!item || !item.tagName) {
          return;
        }
        const params = {
          train_id: this.trainingJobId,
          tag: item.tagName,
        };
        RequestService.getHistogramData(params).then((res) => {
          if (!res || !res.data) {
            return;
          }
          const data = JSON.parse(JSON.stringify(res.data));
          item.chartData = this.formOriData(data);
          this.formatDataToChar(item);
          this.updateSampleData(item);
          this.sampleEventBind(item);
        });
      });
    },
    /**
     * The time display type is changed
     * @param {Number} val Current mode
     */
    timeTypeChange(val) {
      if (this.changeAxisTimer) {
        clearTimeout(this.changeAxisTimer);
        this.changeAxisTimer = null;
      }
      this.changeAxisTimer = setTimeout(() => {
        this.curPageArr.forEach((item) => {
          this.updateSampleData(item);
        });
      }, 500);
    },
    /**
     * The view display type is changed
     * @param {Number} val Current mode
     */
    viewTypeChange(val) {
      if (this.changeViewTimer) {
        clearTimeout(this.changeViewTimer);
        this.changeViewTimer = null;
      }
      this.changeViewTimer = setTimeout(() => {
        this.curPageArr.forEach((item) => {
          this.formatDataToChar(item);
          this.updateSampleData(item);
        });
      }, 200);
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
      this.originDataArr.forEach((item) => {
        this.clearZrData(item);
      });
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
     * Error callback
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
     * @param {Boolean} ignoreError whether ignore error tip.
     */
    updateAllData(ignoreError) {
      const params = {
        plugin_name: 'histogram',
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
          this.clearZrData(this.originDataArr[i]);
          this.originDataArr[i].charObj.clear();
          this.originDataArr.splice(i, 1);
        }
      }
      this.originDataArr.forEach((item, index) => {
        item.sampleIndex = index;
      });
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
            zr: null,
            show: false,
            fullScreen: false,
            domId: `${tagName}`,
            oriData: {},
            charOption: {},
            chartData: [],
            charObj: null,
          });
          this.curFullTagDic[tagName] = true;
          dataAddFlag = true;
        }
      });
      return dataAddFlag;
    },
    /**
     * Update sample data
     * @param {Object} sampleObject sampleObject
     */
    updateSampleData(sampleObject) {
      sampleObject.charOption = this.formatCharOption(sampleObject);
      if (!sampleObject.charObj) {
        sampleObject.charObj = echarts.init(
            document.getElementById(sampleObject.domId),
            null,
        );
      }
      this.removeTooltip(sampleObject);
      sampleObject.charObj.setOption(sampleObject.charOption, true);
    },
    sampleEventBind(sampleObject) {
      if (!sampleObject.zr) {
        sampleObject.zr = sampleObject.charObj.getZr();
        sampleObject.zr.off('mouseout', 'mousemove');
        sampleObject.zr.on('mouseout', (e) => {
          this.removeTooltip(sampleObject);
          this.chartTipFlag = false;
        });
        sampleObject.zr.on('mousemove', (e) => {
          this.removeTooltip(sampleObject);
          this.mousemoveEvent(sampleObject, e);
        });
      }
    },
    mousemoveEvent(sampleObject, e) {
      const unit = 's';
      const nearestIndex = this.findNearestValue(sampleObject, [
        e.offsetX,
        e.offsetY,
      ]);
      if (
        nearestIndex &&
        nearestIndex.yIndex !== null &&
        nearestIndex.binIndex !== null
      ) {
        const {binIndex, yIndex} = nearestIndex;
        const chartData = sampleObject.chartData;
        const hoveredItem = chartData[yIndex];
        const p = Math.max(0, d3.precisionRound(0.01, 1.01) - 1);
        const yValueFormat = d3.format(`.${p}e`);
        const gridRect = sampleObject.charObj
            .getModel()
            .getComponent('grid', 0)
            .coordinateSystem.getRect();
        const gridRectY = gridRect.y - 10;
        let linePoints = [];
        if (!hoveredItem || !hoveredItem.items[binIndex]) {
          return;
        }
        if (!this.chartTipFlag) {
          this.chartTipFlag = true;
        }
        if (this.curViewName === 1 && yIndex !== null) {
          linePoints = this.makePolyPoints(
              yIndex,
              this.getCoord,
              gridRectY,
              sampleObject,
          );
        } else if (this.curViewName === 0 && hoveredItem.items) {
          hoveredItem.items.forEach((item) => {
            linePoints.push(this.getCoord([item[2], item[3]], sampleObject));
          });
        }

        this.zrDrawElement.hoverLine = new echarts.graphic.Polyline({
          silent: true,
          shape: {
            points: linePoints.slice(1, -1),
          },
          z: 999,
        });
        sampleObject.zr.add(this.zrDrawElement.hoverLine);

        this.zrDrawElement.tooltip = new echarts.graphic.Text({});
        let itemX;
        const x = hoveredItem.items[binIndex][2];
        let z = 0;
        chartData.forEach((dataItem, index) => {
          const y = dataItem.step;
          const pt = this.getCoord([x, y], sampleObject);
          if (index === yIndex) {
            z = hoveredItem.items[binIndex][3];
          } else {
            const items = dataItem.items;
            for (let k = 1; k < items.length - 1; k++) {
              const nextX = items[k + 1][2];
              const nextZ = items[k + 1][3];
              if (items[k][2] === x) {
                z = items[k][3];
                break;
              } else if (items[k][2] < x && nextX > x) {
                const proportionX = (x - items[k][2]) / (nextX - items[k][2]);
                z = (nextZ - items[k][3]) * proportionX + items[k][3];
                break;
              }
            }
          }
          itemX = pt[0];
          const circleOption = {
            z: 1000,
          };
          if (this.curViewName === 1) {
            pt[1] -=
              ((z - sampleObject.oriData.minZ) /
                (sampleObject.oriData.maxZ - sampleObject.oriData.minZ)) *
              gridRectY;
            circleOption.shape = {
              cx: itemX,
              cy: pt[1],
              r: 1.5,
            };
          } else {
            circleOption.shape = {
              cx: 0,
              cy: 0,
              r: 1.5,
            };
            circleOption.position = sampleObject.charObj.convertToPixel(
                'grid',
                [x, z],
            );
          }
          const dot = new echarts.graphic.Circle(circleOption);
          sampleObject.zr.add(dot);
          this.zrDrawElement.hoverDots.push(dot);
        });
        this.zrDrawElement.tooltip = new echarts.graphic.Text({});

        let htmlStr = '';
        const hoveredAxis = hoveredItem.items[binIndex][3];
        htmlStr = `<td>${
          hoveredAxis.toString().length >= 6
            ? yValueFormat(hoveredAxis)
            : hoveredAxis
        }</td><td style="text-align:center;">${this.formateNUmber(
            hoveredItem.step,
        )}</td><td>${this.formateNUmber(
            hoveredItem.relative_time.toFixed(0),
        )}${unit}</td><td>${this.dealrelativeTime(
            new Date(hoveredItem.wall_time * 1000).toString(),
        )}</td>`;
        const dom = document.querySelector('#tipTr');
        dom.innerHTML = htmlStr;
        if (!sampleObject.fullScreen) {
          const chartWidth = document.getElementById(sampleObject.domId)
              .parentNode.parentNode.clientWidth;
          const chartHeight = document.getElementById(sampleObject.domId)
              .parentNode.parentNode.clientHeight;
          const left = document.getElementById(sampleObject.domId).parentNode
              .parentNode.offsetLeft;
          const top = document.getElementById(sampleObject.domId).parentNode
              .parentNode.offsetTop;
          const echartTip = document.querySelector('#echartTip');
          echartTip.style.top = `${top + chartHeight - 60}px`;
          if (left > echartTip.clientWidth) {
            echartTip.style.left = `${left - echartTip.clientWidth}px`;
          } else {
            echartTip.style.left = `${left + chartWidth}px`;
          }
        } else {
          const width = document.querySelector('#echartTip').clientWidth;
          const height = document.querySelector('#echartTip').clientHeight;
          const screenWidth = document.body.scrollWidth;
          const screenHeight = document.body.scrollHeight;
          const scrollTop = document.querySelector(
              '.cl-histogram-show-data-content',
          ).scrollTop;
          const offsetTop = document.querySelector(
              '.cl-histogram-show-data-content',
          ).offsetTop;
          if (height + e.event.y + 20 > screenHeight && screenHeight > height) {
            document.querySelector('#echartTip').style.top = `${
              e.event.y + scrollTop - height - 20 - offsetTop
            }px`;
          } else {
            document.querySelector('#echartTip').style.top = `${
              e.event.y + scrollTop + 20 - offsetTop
            }px`;
          }
          // Blank area on the right of the chart is 80
          if (width + e.event.x + 80 > screenWidth && screenWidth > width) {
            document.querySelector('#echartTip').style.left = `${
              e.event.x - width - 20
            }px`;
          } else {
            document.querySelector('#echartTip').style.left = `${
              e.event.x + 20
            }px`;
          }
        }

        this.zrDrawElement.tooltipX = new echarts.graphic.Text({
          position: [itemX, gridRect.y + gridRect.height],
          style: {
            text:
              x.toString().length >= 6
                ? x.toExponential(3)
                : Math.round(x * 1000) / 1000,
            textFill: '#fff',
            textAlign: 'center',
            fontSize: 12,
            textBackgroundColor: '#333',
            textBorderWidth: 2,
            textPadding: [5, 7],
            rich: {},
          },
          z: 2000,
        });
        sampleObject.zr.add(this.zrDrawElement.tooltipX);
        if (this.curViewName === 1 && linePoints && linePoints.length) {
          let text = '';
          if (yIndex !== null) {
            text = this.yAxisFormatter(sampleObject, hoveredItem.step);
          }
          this.zrDrawElement.tooltipY = new echarts.graphic.Text({
            position: [
              gridRect.x + gridRect.width,
              linePoints[linePoints.length - 1][1],
            ],
            style: {
              text: text,
              textFill: '#fff',
              textVerticalAlign: 'middle',
              fontSize: 12,
              textBackgroundColor: '#333',
              textBorderWidth: 2,
              textPadding: [5, 7],
              rich: {},
            },
            z: 2000,
          });
          sampleObject.zr.add(this.zrDrawElement.tooltipY);
        }
      }
    },
    /**
     * Get convert point
     * @param {Array} pt Value
     * @param {Object} sampleObject SampleObject
     * @return {Array}
     */
    getCoord(pt, sampleObject) {
      return sampleObject.charObj.convertToPixel('grid', pt);
    },
    /**
     * Find nearest value
     * @param {Object} sampleObject SampleObject
     * @param {Array} eventPoint Value
     * @return {Object}
     */
    findNearestValue(sampleObject, eventPoint) {
      if (
        !eventPoint ||
        !eventPoint.length ||
        !sampleObject ||
        !sampleObject.charObj ||
        !sampleObject.oriData
      ) {
        return;
      }
      const value = sampleObject.charObj.convertFromPixel('grid', eventPoint);
      if (!value || !value.length) {
        return;
      }
      let binIndex = null;
      let yIndex = null;
      let nearestX = Infinity;
      let nearestY = -Infinity;
      let nearestYData = Infinity;
      const gridRect = sampleObject.charObj
          .getModel()
          .getComponent('grid', 0)
          .coordinateSystem.getRect();
      const gridRectY = gridRect.y - 10;
      const x = value[0];
      sampleObject.chartData.forEach((dataItem, i) => {
        let distY;
        let yAxis;
        for (let k = 0; k < dataItem.items.length - 1; k++) {
          const item = dataItem.items[k];
          const itemNext = dataItem.items[k + 1];
          const nextX = itemNext[2];
          const nextZ = itemNext[3];
          if (item.length >= 4) {
            if (item[2] < x && nextX >= x) {
              const proportionX = (x - item[2]) / (nextX - item[2]);
              yAxis = (nextZ - item[3]) * proportionX + item[3];
              distY = Math.abs(value[1] - yAxis);
              break;
            }
          }
        }
        if (this.curViewName === 0 && distY < nearestYData) {
          nearestYData = distY;
          yIndex = i;
        } else if (this.curViewName === 1) {
          const pt = this.getCoord([x, dataItem.step], sampleObject);
          const ptStep = pt[1];
          pt[1] -=
            ((yAxis - sampleObject.oriData.minZ) /
              (sampleObject.oriData.maxZ - sampleObject.oriData.minZ)) *
            gridRectY;
          if (
            eventPoint[1] > pt[1] &&
            eventPoint[1] < ptStep &&
            ptStep > nearestY
          ) {
            nearestY = ptStep;
            yIndex = i;
          }
        }
      });
      if (yIndex === null && this.curViewName === 1) {
        sampleObject.chartData.forEach((item, index) => {
          if (index >= value[1]) {
            yIndex = yIndex === null ? index : Math.min(yIndex, index);
          }
        });
      }
      if (yIndex !== null) {
        const yData = sampleObject.chartData[yIndex].items;
        yData.forEach((ele, index) => {
          const distX = Math.abs(ele[2] - value[0]);
          if (distX < nearestX) {
            nearestX = distX;
            binIndex = index;
          }
        });
        binIndex =
          binIndex === 0
            ? 1
            : binIndex === yData.length - 1
            ? yData.length - 2
            : binIndex;
      }
      return {
        binIndex,
        yIndex,
      };
    },
    dealrelativeTime(time) {
      const arr = time.split(' ');
      const str = arr[0] + ' ' + arr[1] + ' ' + arr[2] + ',' + ' ' + arr[4];
      return str;
    },
    clearZrData(sampleObject) {
      if (sampleObject && sampleObject.zr) {
        this.removeTooltip(sampleObject);
        sampleObject.zr.off('mouseout', 'mousemove');
        sampleObject.zr = null;
      }
    },
    /**
     * Remove tooltip
     * @param {Number} sampleObject SampleObject
     */
    removeTooltip(sampleObject) {
      if (sampleObject && sampleObject.zr) {
        if (this.zrDrawElement.hoverDots) {
          this.zrDrawElement.hoverDots.forEach((dot) =>
            sampleObject.zr.remove(dot),
          );
        }
        if (this.zrDrawElement.hoverLine) {
          sampleObject.zr.remove(this.zrDrawElement.hoverLine);
        }
        if (this.zrDrawElement.tooltip) {
          sampleObject.zr.remove(this.zrDrawElement.tooltip);
        }
        if (this.zrDrawElement.tooltipY) {
          sampleObject.zr.remove(this.zrDrawElement.tooltipY);
        }
        if (this.zrDrawElement.tooltipX) {
          sampleObject.zr.remove(this.zrDrawElement.tooltipX);
        }
      }
    },
    getValue(seriesData, dataIndex, i) {
      return seriesData[dataIndex][i];
    },
    makePolyPoints(dataIndex, getCoord, yValueMapHeight, sampleObject) {
      const points = [];
      const rawData = sampleObject.oriData.seriesData;
      const maxZ = sampleObject.oriData.maxZ;
      const minZ = sampleObject.oriData.minZ;
      for (let i = 0; i < rawData[dataIndex].length; ) {
        const x = this.getValue(rawData, dataIndex, i++);
        const y = this.getValue(rawData, dataIndex, i++);
        const z = this.getValue(rawData, dataIndex, i++);
        const pt = getCoord([x, y], sampleObject);
        // Linear map in z axis
        if (maxZ !== minZ) {
          pt[1] -= ((z - minZ) / (maxZ - minZ)) * yValueMapHeight;
        }
        points.push(pt);
      }
      return points;
    },
    formOriData(dataItem) {
      const chartData = [];
      const wallTimeInit = dataItem.histograms.length
        ? dataItem.histograms[0].wall_time
        : 0;
      dataItem.histograms.forEach((histogram, index) => {
        const step = histogram.step.toString();
        const chartItem = {
          wall_time: histogram.wall_time,
          relative_time: histogram.wall_time - wallTimeInit,
          step: step,
          items: [],
        };
        const chartArr = [];
        histogram.buckets.forEach((bucket) => {
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
          chartData.push(chartItem);
        }
      });
      return chartData;
    },
    formatDataToChar(item) {
      const chartData = item.chartData;
      const seriesData = [];
      let maxX = -Infinity;
      let minX = Infinity;
      let maxZ = -Infinity;
      let minZ = Infinity;
      const gridData = [];
      if (chartData && chartData.length) {
        chartData.forEach((histogram) => {
          const seriesItem = [];
          gridData.push(histogram.step);
          histogram.items.forEach((bucket) => {
            if (this.curViewName === 0) {
              seriesItem.push([bucket[2], bucket[3]]);
            } else if (this.curViewName === 1) {
              seriesItem.push(bucket[2], histogram.step, bucket[3]);
            }
            maxX = Math.max(maxX, bucket[2]);
            minX = Math.min(minX, bucket[2]);
            minZ = Math.min(minZ, bucket[3]);
            maxZ = Math.max(maxZ, bucket[3]);
          });
          seriesData.push(seriesItem);
        });
      }
      item.oriData = {
        seriesData,
        maxX,
        minX,
        maxZ,
        minZ,
        gridData,
      };
    },
    formatCharOption(sampleObject) {
      const colorMin = '#346E69';
      const colorMax = '#EBFFFD';
      const oriData = sampleObject.oriData;
      const colorArr = this.getGrientColor(
          colorMin,
          colorMax,
          oriData.seriesData.length,
      );
      const fullScreenFun = this.toggleFullScreen;
      const curAxisName = this.curAxisName;
      const that = this;
      const option = {
        grid: {
          left: 40,
          top: 60,
          right: 80,
          bottom: 60,
        },
        xAxis: {
          max: oriData.maxX,
          min: oriData.minX,
          axisLine: {onZero: false},
          axisLabel: {
            fontSize: '11',
            formatter: function(value) {
              return that.formateNUmber(value);
            },
          },
          splitLine: {show: false},
        },
        yAxis: {
          position: 'right',
          axisLine: {onZero: false, show: false},
          splitLine: {show: true},
          axisTick: {show: false},
          boundaryGap: false,
          axisLabel: {
            fontSize: '11',
            formatter: function(value) {
              return that.formateNUmber(value);
            },
          },
        },
        toolbox: {
          top: 20,
          right: 20,
          emphasis: {
            iconStyle: {
              textPosition: 'top',
              borderColor: '#00A5A7',
            },
          },
          // toolbox
          feature: {
            // fullScreen
            myToolFullScreen: {
              show: true,
              title: this.$t('histogram.fullScreen'),
              iconStyle: {
                borderColor: sampleObject.fullScreen ? '#00A5A7' : '#6D7278',
              },
              icon: CommonProperty.fullScreenIcon,
              onclick() {
                fullScreenFun(sampleObject);
              },
            },
          },
        },
      };
      if (this.curViewName === 1) {
        const seriesData = [];
        oriData.seriesData.forEach((item, dataIndex) => {
          const dataItem = {
            name: item[1],
            value: item,
            itemStyle: {
              color: colorArr[dataIndex],
            },
          };
          seriesData.push(dataItem);
        });
        option.series = [
          {
            type: 'custom',
            dimensions: ['x', 'y'],
            renderItem: (params, api) => {
              const points = this.makePolyPoints(
                  params.dataIndex,
                  api.coord,
                  params.coordSys.y - 10,
                  sampleObject,
              );

              return {
                type: 'polyline',
                z2: params.dataIndex,
                silent: true,
                shape: {
                  points,
                },
                style: api.style({
                  stroke: '#bbb',
                  lineWidth: 1,
                }),
              };
            },
            data: seriesData,
          },
        ];
        option.yAxis.data = oriData.gridData;
        option.yAxis.type = 'category';
        option.grid.top = 126;
        if (curAxisName === 2 && sampleObject.fullScreen) {
          option.grid.right = 140;
        }
        option.yAxis.inverse = true;
        option.yAxis.axisLabel.formatter = function(value) {
          return that.yAxisFormatter(sampleObject, value);
        };
      } else if (this.curViewName === 0) {
        option.color = colorArr;
        option.series = [];
        oriData.seriesData.forEach((k) => {
          option.series.push({
            type: 'line',
            symbol: 'none',
            lineStyle: {
              width: 1,
            },
            data: k.slice(1, -1),
          });
        });
      }
      return option;
    },
    yAxisFormatter(sampleObject, value) {
      let data = '';
      const filter = sampleObject.chartData.filter((k) => k.step === value);
      if (filter.length) {
        if (this.curAxisName === 2) {
          data = sampleObject.fullScreen
            ? this.dealrelativeTime(
                new Date(filter[0].wall_time * 1000).toString(),
            )
            : [];
        } else if (this.curAxisName === 1) {
          data = this.formateNUmber(filter[0].relative_time.toFixed(0));
        } else {
          data = this.formateNUmber(filter[0].step);
        }
      }
      return data;
    },
    /**
     * Format time display
     * @param {Number} value
     * @return {Number} Formatted number
     */
    formateNUmber(value) {
      value = Number(value);
      if (value.toString().length > 6) {
        return value.toExponential(3);
      } else {
        return Math.round(value * 1000) / 1000;
      }
    },
    formatColor(str) {
      if (!str) {
        return;
      }
      const colorReg = /^([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/;
      let colorStr = str.toLowerCase().slice(1);
      if (colorReg.test(colorStr)) {
        let colorStrNew = '';
        if (colorStr.length === 3) {
          for (let i = 0; i < 3; i++) {
            colorStrNew += colorStrNew
                .slice(i, i + 1)
                .concat(colorStrNew.slice(i, i + 1));
          }
          colorStr = colorStrNew;
        }
        const colorFormat = [];
        for (let i = 0; i < 6; i += 2) {
          colorFormat.push(parseInt(`0x${colorStr.slice(i, i + 2)}`));
        }
        return colorFormat;
      } else {
        return colorStr;
      }
    },
    formatColorToHex(rgb) {
      const regRgb = /^(rgb|RGB)/g;
      if (regRgb.test(rgb)) {
        const colorSplit = rgb.replace(/(?:(|)|rgb|RGB)*/g, '').split(',');
        let hexStr = '';
        for (let i = 0; i < colorSplit.length; i++) {
          let hexItem = Number(colorSplit[i]).toString(16);
          hexItem = hexItem < 10 ? `0${hexItem}` : hexItem;
          if (hexItem === '0') {
            hexItem += hexItem;
          }
          hexStr += hexItem;
        }
        if (hexStr.length !== 6) {
          hexStr = rgb;
        }
        return hexStr;
      }
    },
    getGrientColor(startColor, endColor, step) {
      const startRgb = this.formatColor(startColor);
      const endRgb = this.formatColor(endColor);
      const gapRgbR = (endRgb[0] - startRgb[0]) / step;
      const gapRgbG = (endRgb[1] - startRgb[1]) / step;
      const gapRgbB = (endRgb[2] - startRgb[2]) / step;
      const colorResult = [];
      for (let i = 0; i < step; i++) {
        const sR = parseInt(gapRgbR * i + startRgb[0]);
        const sG = parseInt(gapRgbG * i + startRgb[1]);
        const sB = parseInt(gapRgbB * i + startRgb[2]);
        const hex = this.formatColorToHex(`rgb(${sR},${sG},${sB})`);
        colorResult.push(hex);
      }
      return colorResult;
    },
    toggleFullScreen(sampleObject) {
      if (!sampleObject) {
        return;
      }
      this.removeTooltip(sampleObject);
      sampleObject.fullScreen = !sampleObject.fullScreen;
      if (sampleObject.fullScreen) {
        if (this.curAxisName === 2) {
          sampleObject.charOption.grid.right = 140;
        }
        sampleObject.charOption.toolbox.feature.myToolFullScreen.iconStyle.borderColor =
          '#00A5A7';
      } else {
        sampleObject.charOption.grid.right = 80;
        sampleObject.charOption.toolbox.feature.myToolFullScreen.iconStyle.borderColor =
          '#6D7278';
      }
      setTimeout(() => {
        sampleObject.charObj.setOption(sampleObject.charOption);
        sampleObject.charObj.resize();
        document.getElementById(sampleObject.domId).scrollIntoView();
      }, 0);
    },
  },
};
</script>
<style>
.cl-histogram-manage {
  height: 100%;
}
.cl-histogram-manage .histogram-bk {
  height: 100%;
  background-color: #fff;
  display: flex;
  flex-direction: column;
}
.cl-histogram-manage .histogram-bk .cl-histogram-title {
  height: 56px;
  line-height: 56px;
}
.cl-histogram-manage .histogram-bk .cl-histogram-title .path-message {
  display: inline-block;
  line-height: 20px;
  padding: 0px 4px 15px 4px;
  font-weight: bold;
  vertical-align: bottom;
}
.cl-histogram-manage .histogram-bk .cl-histogram-title .cl-close-btn {
  width: 20px;
  height: 20px;
  vertical-align: -3px;
  cursor: pointer;
  display: inline-block;
}
.cl-histogram-manage .histogram-bk .cl-histogram-operate-content {
  width: 100%;
  padding: 8px 32px 22px 32px;
  background: #ffffff;
}
.cl-histogram-manage .histogram-bk .cl-histogram-view-type-select-content {
  background: #ffffff;
  padding: 0 32px 21px 32px;
  height: 58px;
  display: flex;
  align-items: center;
  border-bottom: 2px solid #e6ebf5;
}
.cl-histogram-manage .histogram-bk .cl-histogram-view-type-select-content .view-title {
  font-size: 14px;
  line-height: 14px;
  vertical-align: middle;
  margin-right: 16px;
  flex-shrink: 0;
}
.cl-histogram-manage .histogram-bk .cl-histogram-view-type-select-content .el-radio-group {
  margin-right: 64px;
  flex-shrink: 0;
}
.cl-histogram-manage .histogram-bk .cl-histogram-show-data-content {
  background: #ffffff;
  padding: 0 23px;
  flex: 1;
  overflow: auto;
}
.cl-histogram-manage .histogram-bk .cl-histogram-show-data-content .data-content {
  display: flex;
  height: 100%;
  width: 100%;
  flex-wrap: wrap;
  min-height: 400px;
  position: relative;
}
.cl-histogram-manage .histogram-bk .cl-histogram-show-data-content .data-content .sample-content {
  width: 33.3%;
  height: 400px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  background-color: #fff;
  position: relative;
}
.cl-histogram-manage .histogram-bk .cl-histogram-show-data-content .data-content .char-full-screen {
  width: 100%;
  height: 400px;
}
.cl-histogram-manage .histogram-bk .cl-histogram-show-data-content .data-content .chars-container {
  flex: 1;
  padding: 0 15px 0 15px;
  position: relative;
}
.cl-histogram-manage .histogram-bk .cl-histogram-show-data-content .data-content .chars-container .char-item-content {
  width: 100%;
  height: calc(100% - 26px);
}
.cl-histogram-manage .histogram-bk .cl-histogram-show-data-content .data-content .chars-container .tag-title {
  width: 100%;
  font-size: 16px;
  font-weight: 600;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
}
.cl-histogram-manage .histogram-bk .pagination-content {
  padding: 24px 32px;
  text-align: right;
}
.cl-histogram-manage .histogram-bk .image-noData {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}
.cl-histogram-manage .content {
  position: relative;
}
.cl-histogram-manage #echart {
  width: 500px;
  height: 500px;
  border: 1px solid black;
  position: relative;
}
.cl-histogram-manage #echartTip {
  position: absolute;
  padding: 5px;
  z-index: 9999;
  font-size: 14px;
  font-family: "Microsoft YaHei";
  background-color: rgba(50, 50, 50, 0.7);
  border: 0;
  border-radius: 4px;
  color: #fff;
}
.cl-histogram-manage .char-tip-table td {
  padding-left: 5px;
  padding-right: 5px;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 150px;
  overflow: hidden;
}
.cl-histogram-manage .borderspacing3 {
  border-spacing: 3px;
}
</style>

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
  <div class="cl-xai">
    <div class="cl-xai-title">
      <div class="cl-xai-title-left">{{$t('metric.scoreSystem')}}
        <el-tooltip effect="light"
                    class="item"
                    placement="top-start">
          <div slot="content"
               class="tooltip-container">
            <div class="tooltip-style">
              <div class="tooltip-title">{{$t('metric.scoreSystemtooltipOne')}}</div>
              <div class="tooltip-content">{{$t('metric.scoreSystemtooltiptwo')}}</div><br />
              <div class="tooltip-title">{{$t('metric.scoreSystemtooltipthree')}}</div>
              <div class="tooltip-content">{{$t('metric.scoreSystemtooltipfour')}}</div>
              <div class="tooltip-content">{{$t('metric.scoreSystemtooltipfive')}}</div>
            </div>
          </div>
          <i class="el-icon-info"></i>
        </el-tooltip>
      </div>
      <div class="cl-xai-title-right">
        <div class="cl-close-btn"
             @click="jumpToSaliencyMap">
          <img src="@/assets/images/close-page.png">
        </div>
      </div>

    </div>
    <el-tabs v-model="tabType">

      <el-tab-pane name="overall">
        <span slot="label">
          {{$t('metric.comprehensive')}}
          <el-tooltip effect="light"
                      class="item"
                      placement="top-start">
            <div slot="content"
                 class="tooltip-container">
              {{$t('metric.comprehensiveTooltip')}}
            </div>
            <i class="el-icon-info"></i>
          </el-tooltip>
        </span>
      </el-tab-pane>

      <el-tab-pane name="detail">
        <span slot="label">
          {{$t('metric.classify')}}
          <el-tooltip effect="light"
                      class="item"
                      placement="top-start">
            <div slot="content"
                 class="tooltip-container">
              {{$t('metric.classifyTooltip')}}
            </div>
            <i class="el-icon-info"></i>
          </el-tooltip>
        </span>
      </el-tab-pane>
    </el-tabs>

    <div class="cl-xai-con comprehensiveEvaluation"
         ref="xaiCon"
         v-show="tabType==='overall' && !isNoData">
      <el-table :data="evaluationTableData"
                border
                header-row-class-name="evaluation-table-header"
                show-summary
                :summary-method="getSummaries"
                :sum-text="$t('metric.compositeScore')"
                ref="sortTable">
        <el-table-column prop="metric"
                         :label="$t('metric.metric')"
                         width="180"
                         class-name="firstColumn"
                         fixed
                         :resizable="false">
        </el-table-column>
        <el-table-column prop="weight"
                         :label="$t('metric.weightAllocatgion')"
                         width="180"
                         :class-name="!resultShow ? 'resultFalse':''"
                         fixed
                         :resizable="false">
          <template slot-scope="scope">
            <el-input-number v-model="scope.row.weight"
                             controls-position="right"
                             @change="weightChange"
                             :min="0"
                             :max="1"
                             :precision="2"
                             size="small"
                             :step="0.01"></el-input-number>
          </template>
        </el-table-column>
        <el-table-column v-for="(item,index) in tableHead"
                         :key="index"
                         :prop="item"
                         sortable
                         min-width="120"
                         :resizable="false">
          <template slot="header">
            <div :title="item"
                 class="thTooltip">{{item}}</div>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <div class="cl-xai-con"
         v-show="tabType==='detail' && !isNoData">
      <div class="classify-container">
        <!-- Single method and multi metrics-->
        <div class="half-item left-item">
          <div class="operate-container">
            <div class="container-name">{{$t("metric.singleMethod")}}</div>
            <div class="select-see">
              <span class="see-methods">{{$t("metric.seeInterpretation")}}</span>
              <span class="slectMethod">{{multiMetricForm.selectedMethods}}</span>
              <span class="see-methods">{{$t('metric.showGrade')}}</span>
            </div>
            <div>
              <span class="select-name">{{$t('metric.interpretation')}}</span>
              <span>
                <el-select v-model="multiMetricForm.selectedMethods"
                           :placeholder="$t('metric.interpretation')"
                           @change="getSingalMethodChartData">
                  <el-option v-for="(item, index) in classifyAllMethods"
                             :key="index"
                             :value="item"
                             :label="item"></el-option>
                </el-select>
              </span>
            </div>
            <div class="methods-show">
              <span class="show-name">{{$t('metric.measurement')}}</span>
              <span>
                <el-checkbox-group v-model="multiMetricForm.selectedMetrics"
                                   @change="getSingalMethodChartData">
                  <el-checkbox v-for="(item, index) in classifyAllMetrics"
                               :key="index"
                               :value="item"
                               :label="item"></el-checkbox>
                </el-checkbox-group>
              </span>
            </div>
          </div>
          <div class="chart-container">
            <benchmark-bar-chart v-bind:barData="multiMetricData"
                                 v-bind:resizeFlag="resizeFlag"></benchmark-bar-chart>
          </div>
        </div>
        <!-- Single metric and multi methods -->
        <div class="half-item right-itemm">
          <div class="operate-container">
            <div class="container-name">{{$t("metric.multiMethod")}}</div>
            <div class="select-see">
              <span class="see-methods">{{$t("metric.seeMeasurement")}}</span>
              <span class="slectMethod">{{multiMethodForm.selectedMetrics}}
              </span>
              <span class="see-methods">{{$t('metric.showGrade')}}</span>
            </div>
            <div>
              <span class="select-name">{{$t('metric.measurement')}}</span>
              <span>
                <el-select v-model="multiMethodForm.selectedMetrics"
                           :placeholder="$t('metric.measurement')"
                           @change="getSingalMetricChartData">
                  <el-option v-for="(item, index) in classifyAllMetrics"
                             :key="index"
                             :value="item"
                             :label="item"></el-option>
                </el-select>
              </span>
            </div>
            <div class="methods-show">
              <span class="show-name">{{$t('metric.interpretation')}}</span>
              <span>
                <el-checkbox-group v-model="multiMethodForm.selectedMethods"
                                   @change="getSingalMetricChartData">
                  <el-checkbox v-for="(item, index) in classifyAllMethods"
                               :key="index"
                               :value="item"
                               :label="item"></el-checkbox>
                </el-checkbox-group>
              </span>
            </div>
          </div>
          <div class="chart-container">
            <benchmark-bar-chart v-bind:barData="multiMethodData"
                                 v-bind:resizeFlag="resizeFlag"
                                 theme="light"></benchmark-bar-chart>
          </div>
        </div>
      </div>
    </div>
    <!-- No data -->
    <div class="cl-xai-con"
         v-show="isNoData">
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

  </div>
</template>

<script>
import BenchmarkBarChart from '@/components/benchmarkBarChart';
import RequestService from '../../services/request-service';

export default {
  components: {
    BenchmarkBarChart,
  },
  data() {
    return {
      trainId: this.$route.query.id, // Train id
      tabType: 'overall',
      tableHead: [], // Table head
      evaluationTableData: [], // Evaluation table data
      tableParam: {}, // Table param
      resultShow: true, // Result show
      isNoData: true, // Is no data
      initOver: false, // Initialization completion flag
      fullDict: {}, // Full data dictionary
      classifyAllMethods: [], // all explain methods
      // The currently selected exlpain method and all selected metrics
      multiMetricForm: {
        selectedMethods: null,
        selectedMetrics: [],
      },
      // Chart data of current single method
      multiMetricData: {
        legend: [],
        yAxis: [],
        series: [],
      },

      classifyAllMetrics: [], // all explain metrics
      // The currently selected metric and all selected exlpain methods
      multiMethodForm: {
        selectedMethods: [],
        selectedMetrics: null,
      },
      // Chart data of current single metric
      multiMethodData: {
        legend: [],
        yAxis: [],
        series: [],
      },
      allLabels: [], // all labels
      resizeFlag: false, // Chart drawing area change sign
      resizeTimer: null, // Chart redraw delay indicator
    };
  },
  watch: {
    // Listen to the current tab
    tabType(val) {
      if (val === 'detail') {
        this.$nextTick(() => {
          this.resizeFlag = !this.resizeFlag;
        });
      }
    },
  },
  destroyed() {
    // Cancel delay and monitor
    if (this.resizeTimer) {
      clearTimeout(this.resizeTimer);
      this.resizeTimer = null;
    }
    window.removeEventListener('resize', this.resizeCallback);
  },
  mounted() {
    if (!this.trainId) {
      this.$message.error(this.$t('trainingDashboard.invalidId'));
      document.title = `${this.$t('metric.scoreSystem')}-MindInsight`;
      return;
    }
    document.title = `${this.$t('metric.scoreSystem')}-MindInsight`;
    this.getEvaluationData();
    window.addEventListener('resize', this.resizeCallback, false);
  },

  methods: {
    /**
     * Jump back to train dashboard
     */
    jumpToSaliencyMap() {
      this.$router.push({
        path: '/explain/saliency-map',
        query: {
          id: this.trainId,
        },
      });
    },

    /**
     * Init evaluation table
     * @param {Object} res Original data
     */
    initEvaluationTable(res) {
      if (res && res.explainer_scores && res.explainer_scores.length > 0) {
        const tableData = [];
        const resData = res.explainer_scores[0].evaluations;
        let score = 0;

        resData.forEach((item, index) => {
          const data = {};
          res.explainer_scores.forEach((v, i) => {
            data.metric = item.metric;
            data[v.explainer] = v.evaluations[index].score;
          });

          const resDataLength = resData.length;
          if (index < resDataLength - 1) {
            data.weight = Math.floor((1 / resDataLength) * 100) / 100;
            score += Math.floor((1 / resDataLength) * 100) / 100;
          } else {
            score = 1 - score;
            data.weight = score;
          }
          tableData.push(data);
        });

        const tableHead = [];
        Object.keys(tableData[0]).forEach((item) => {
          if (item !== 'metric' && item !== 'weight') {
            tableHead.push(item);
          }
        });
        this.evaluationTableData = tableData;
        this.tableHead = tableHead;
      }
    },

    /**
     * Weight change
     */
    weightChange() {
      this.getSummaries(this.tableParam);
    },

    /**
     * Get summaries
     * @param {Object} param params
     * @return {Object} Summaries data
     */
    getSummaries(param) {
      this.tableParam = param;
      const {columns, data} = param;

      if (!this.evaluationTableData.length) {
        return [];
      }

      const sums = [];
      columns.forEach((column, index) => {
        const values = data.map((item) => Number(item[column.property]));

        if (index === 0) {
          sums[index] = this.$t('metric.compositeScore');
        } else if (index === 1) {
          sums[index] = 0;
          values.forEach((value) => {
            sums[index] += value;
          });

          if (sums[index] !== 1) {
            this.resultShow = false;
            sums[index] = this.$t('metric.weightSum');
          } else {
            this.resultShow = true;
          }
        } else {
          if (this.resultShow) {
            sums[index] = 0;
            values.forEach((value, i) => {
              const tableData = this.$refs.sortTable.tableData;
              sums[index] += value * tableData[i].weight;
            });
            sums[index] = Math.floor(sums[index] * 100) / 100;
          } else {
            sums[index] = '-';
          }
        }
      });

      return sums;
    },

    /**
     * Get evaluation data
     */
    getEvaluationData() {
      const params = {
        train_id: decodeURIComponent(this.trainId),
      };
      RequestService.getEvaluation(params).then(
          (res) => {
            this.initOver = true;
            if (res && res.data) {
              const resData = JSON.parse(JSON.stringify(res.data));
              if (
                resData.explainer_scores.length &&
              resData.explainer_scores[0].evaluations.length
              ) {
                this.isNoData = false;
                this.initEvaluationTable(resData);
                this.initializeClassifyData(resData);
              } else {
                this.isNoData = true;
              }
            }
          },
          (err) => {
            this.initOver = true;
          },
      );
    },

    /**
     * Initialize classification evaluation data
     * @param {Object} oriData Original data
     */
    initializeClassifyData(oriData) {
      if (!oriData || !oriData.explainer_scores) {
        this.clearCllassifyCommonData();
        return;
      }
      const fullDataDict = {};
      const classifyAllMethods = [];
      const classifyAllMetrics = [];
      const metricsDic = {};
      const labelDic = {};
      const allLabels = [];
      // Simplify data to dictionary
      oriData.explainer_scores.forEach((explainerScore) => {
        const curMethod = explainerScore.explainer;
        if (!fullDataDict[curMethod]) {
          classifyAllMethods.push(curMethod);
          fullDataDict[curMethod] = {};
          explainerScore.class_scores.forEach((classScore) => {
            const curLabel = classScore.label;
            if (!labelDic[curLabel]) {
              labelDic[curLabel] = true;
              allLabels.push(curLabel);
            }
            if (!fullDataDict[curMethod][curLabel]) {
              fullDataDict[curMethod][curLabel] = {};
              classScore.evaluations.forEach((evaluation) => {
                fullDataDict[curMethod][curLabel][evaluation.metric] =
                  evaluation.score;
                if (!metricsDic[evaluation.metric]) {
                  metricsDic[evaluation.metric] = true;
                  classifyAllMetrics.push(evaluation.metric);
                }
              });
            }
          });
        }
      });
      this.fullDict = fullDataDict;
      this.classifyAllMethods = classifyAllMethods;
      this.classifyAllMetrics = classifyAllMetrics;
      this.multiMetricForm.selectedMetrics = classifyAllMetrics;
      this.multiMethodForm.selectedMethods = classifyAllMethods;
      this.allLabels = allLabels;
      if (classifyAllMethods.length) {
        this.multiMetricForm.selectedMethods = classifyAllMethods[0];
      }
      if (classifyAllMetrics.length) {
        this.multiMethodForm.selectedMetrics = classifyAllMetrics[0];
      }
      // Get single explain method chart data
      this.getSingalMethodChartData();
      // Get single metric chart data
      this.getSingalMetricChartData();
    },
    /**
     * Get single explain method chart data
     */
    getSingalMethodChartData() {
      const tempData = this.fullDict[this.multiMetricForm.selectedMethods];
      const series = [];
      this.multiMetricForm.selectedMetrics.forEach((metric) => {
        const tempSerData = {
          name: metric,
          values: [],
        };
        this.allLabels.forEach((label) => {
          if (tempData && tempData[label] && tempData[label][metric]) {
            tempSerData.values.push(tempData[label][metric]);
          } else {
            tempSerData.values.push(0);
          }
        });
        series.push(tempSerData);
      });
      this.multiMetricData = {
        legend: this.multiMetricForm.selectedMetrics,
        yAxis: this.allLabels,
        series: series,
      };
    },
    /**
     * Get single metric chart data
     */
    getSingalMetricChartData() {
      const tempMetric = this.multiMethodForm.selectedMetrics;
      const series = [];
      this.multiMethodForm.selectedMethods.forEach((method) => {
        const tempData = this.fullDict[method];
        const tempSerData = {
          name: method,
          values: [],
        };
        this.allLabels.forEach((label) => {
          if (tempData && tempData[label] && tempData[label][tempMetric]) {
            tempSerData.values.push(tempData[label][tempMetric]);
          } else {
            tempSerData.values.push(0);
          }
        });
        series.push(tempSerData);
      });
      this.multiMethodData = {
        legend: this.multiMethodForm.selectedMethods,
        yAxis: this.allLabels,
        series: series,
      };
    },
    /**
     * Clear commmon data
     */
    clearCllassifyCommonData() {
      this.fullDataDict = {};
      this.classifyAllMethods = [];
      this.multiMetricForm = {
        selectedMethods: null,
        selectedMetrics: [],
      };
      this.multiMetricData = {
        legend: [],
        yAxis: [],
        series: [],
      };
      this.classifyAllMetrics = [];
      this.multiMethodForm = {
        selectedMethods: [],
        selectedMetrics: null,
      };
      this.multiMethodData = {
        legend: [],
        yAxis: [],
        series: [],
      };
      this.allLabels = [];
    },
    /**
     * Callback of window size change
     */
    resizeCallback() {
      if (this.resizeTimer) {
        clearTimeout(this.resizeTimer);
        this.resizeTimer = null;
      }
      this.resizeTimer = setTimeout(() => {
        this.resizeFlag = !this.resizeFlag;
      }, 500);
    },
  },
};
</script>

<style lang="scss">
.cl-xai {
  height: 100%;
  background-color: #fff;
  padding: 0px 32px;
  padding-bottom: 32px;
  display: flex;
  flex-direction: column;

  .cl-xai-title {
    height: 56px;
    line-height: 56px;
    display: flex;
    overflow: hidden;
    flex-direction: 0;

    .cl-xai-title-left {
      flex: 1;
      font-size: 20px;
      font-weight: bold;
      letter-spacing: -0.86px;

      i {
        color: #6c7280;
        margin-left: 12px;
      }
    }

    .cl-xai-title-right {
      flex: 1;
      text-align: right;

      .cl-close-btn {
        width: 20px;
        height: 20px;
        vertical-align: -3px;
        cursor: pointer;
        display: inline-block;
        line-height: 20px;
        margin-left: 32px;
      }
    }
  }
  .el-tabs__active-bar {
    width: 76px !important;
  }
  .el-tabs__item:nth-child(2) {
    margin-right: 10px !important;
  }
  .el-tabs__item:last-child {
    margin-left: 10px !important;
  }
  .is-active:nth-child(2) {
    margin-right: 10px !important;
  }
  .is-active:last-child {
    margin-left: 10px !important;
  }
  .el-tabs__active-bar {
    width: 0px !important;
    height: 0px !important;
  }
  .el-tabs__item {
    font-size: 14px;
    color: #303133;
    height: 40px !important;
    line-height: 36px !important;
    padding: 0px !important;
    span {
      font-weight: 500 !important;
      font-size: 14px;
      color: #303133;
    }
    span:hover {
      color: #00a5a7;
      i {
        color: #00a5a7;
      }
    }
    i {
      color: #6c7280;
      font-size: 14px;
    }
  }
  .el-tabs__item.is-active {
    color: #00a5a7;
    border-bottom: 2px solid #00a5a7;

    span {
      color: #00a5a7;
      font-weight: 700 !important;
      font-size: 14px;
    }
    i {
      color: #00a5a7;
      font-size: 14px;
    }
  }

  .el-tabs__header {
    margin: 0px;
  }

  .cl-xai-con {
    flex: 1;
  }

  .comprehensiveEvaluation {
    padding: 25px 0;

    .resultFalse {
      color: #f00 !important;
    }

    .firstColumn {
      color: #00a5a7;
    }

    .thTooltip {
      max-width: calc(100% - 25px);
      padding: 0px;
      vertical-align: middle;
      overflow: hidden;
    }
    .evaluation-table-header {
      th {
        background: #f5f7fa;
      }
    }
  }

  .image-noData {
    // Set the width and white on the right.
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
    .noData-text {
      margin-top: 33px;
      font-size: 18px;
    }
  }

  .classify-container {
    height: 100%;

    .left-item {
      padding-right: 10px;
    }
    .right-itemm {
      padding-left: 10px;
    }
    .half-item {
      width: 50%;
      float: left;
      height: 100%;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      .operate-container {
        width: 100%;
        .container-name {
          font-size: 16px;
          font-weight: 700;
          padding: 15px 0px;
        }
        .select-see {
          padding-bottom: 10px;
        }
        .see-methods {
          font-size: 13px;
          // font-weight: bold;
        }
        .select-name {
          display: inline-block;
          padding-right: 10px;
        }
      }
      .chart-container {
        flex: 1;
        overflow: hidden;
      }
      .methods-show {
        padding: 10px 0px;
        .show-name {
          display: inline-block;
          margin-right: 10px;
          padding-bottom: 10px;
        }
        div {
          display: inline;
        }
      }
    }
  }

  .classify {
    border-right: solid 1px #ddd;
  }
  .slectMethod {
    color: darkmagenta;
  }

  .el-select {
    height: 32px;
    width: 217px;
  }
  .el-input__inner {
    height: 32px;
    line-height: 32px;
    padding: 0px 15px;
  }
}
.el-tooltip__popper {
  .tooltip-container {
    .tooltip-style {
      .tooltip-title {
        font-size: 16px !important;
        font-weight: bold;
        color: #333333;
      }
      .tooltip-content {
        line-height: 20px;
      }
    }
  }
}
</style>

<!--
Copyright 2021-2022 Huawei Technologies Co., Ltd.All Rights Reserved.

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
  <div class="operator-shape-step">
    <div class="shape-step">
      <span class="shape-step-title">
        {{$t('profiling.operatorShapeDetail')}}
        <el-tooltip class="item" 
                    effect="light" 
                    placement="right-end">
          <div slot="content" class="tooltip-container">
            <div>{{$t('profiling.operatorShapeTip')}}</div>
          </div>
          <span class="el-icon-info"></span>
        </el-tooltip>
      </span>
    </div>
    <div class="operator-shape-option">
      <div class="operator-shape-select">
        <span class="operator-filter-title">{{$t('profiling.operatorFilterTitle')}}</span>
        <el-select class="operator-detail-select" 
                   v-model="topOperatorValue"
                   @remove-tag="operatorRemove"
                   :collapse-tags="true"
                   multiple
                   filterable 
                   :placeholder="selectTip">
          <el-option
            v-for="(item, index) in topOperatorArr"
            :key="index"
            :label="item.name"
            disabled
            :value="item.name">
            <el-checkbox :key="item.name" 
                         v-model="item.check" 
                         @change="operatorChange(item.name)">{{item.name}}</el-checkbox>
          </el-option>
        </el-select>
      </div>
    </div>
    <div class="operator-shape-detail">
      <div class="operator-shape-title">{{$t('profiling.operatorShapeTitle')}}</div>
      <div class="operator-shape-chart" id="operatorShapeDetailChart">
      </div>
      <div class="image-noData" v-if="svg.noData">
        <div>
            <img :src="require('@/assets/images/nodata.png')" 
                 alt="" />
            <p v-show="svg.noData">{{$t('public.noData')}}</p>
        </div>
      </div>
    </div>
    <div v-if="showDialogModel" class="operator-shape-dialog">
      <el-dialog
          :title="operatorShapeTilte"
          :visible.sync="showDialogModel"
          width="50%"
          :close-on-click-modal="false"
          class="details-data-list">
        <el-table :data="modelShapeData"
                  row-key="id"
                  lazy
                  tooltip-effect="light">
          <el-table-column property="name"
                           label="OperatorName"
                           width="200">
          </el-table-column>
          <el-table-column property="step"
                           label="Step"
                           width="100">
          </el-table-column>
          <el-table-column property="value"
                           label="OperatorShape">
            <template slot-scope="scope">
              {{scope.row.value}}
            </template>
          </el-table-column>
        </el-table>
      </el-dialog>
    </div>
  </div>
</template>

<script>
import echarts, {echartsThemeName} from '@/js/echarts';
import RequestService from '@/services/request-service';
export default {
  props: {
    rankID: String,
  },
  data() {
    return {
      trainInfo: {
        id: this.$route.query.id,
        path: this.$route.query.path,
        dir: this.$route.query.dir,
      },
      operatorOptions: {
        dataZoom: [{
          type: 'slider',
          show: true,
          start: 0,
          end: 100,
        }],
        tooltip: {
          trigger: 'axis',
          formatter: null,
          confine: true,
        },
        legend: {
          right: 70,
          top: 8,
          data: [],
        },
        color: ['#c23531', '#2f4554', '#61a0a8'],
        xAxis: {
          type: 'category',
          name: 'step',
          data: [],
        },
        yAxis: {
          type: 'value',
          name: this.$t('profiling.timeConsume') + '(s)',
        },
        series: []
      },
      topOperatorValue: [],
      topOperatorArr: [],
      showDialogModel: false,
      modelShapeData: null,
      svg: {
        noData: false,
      },
      selectTip: this.$t('public.select'),
      operatorShapeTitle: this.$t('profiling.operatorShapeTitle'),
    }
  },
  mounted() {
      this.$nextTick(() => {
        this.getOperatorShape();
      })
  },
  methods: {
    /**
     * init operator shape info by request dynamic shape api
     */
    getOperatorShape() {
      const params = {
        dir: this.trainInfo.path,
        device_id: this.rankID,
      }
      let series = [];
      let legend = [];
      let details = [];
      RequestService.queryDynamicShape(params).then(
        (res) => {
          if (res && res.data) {
            this.svg.noData = false;
            let data = res.data;
            let op_type_arr = data.op_type;
            let count_num = 0;
            Object.keys(op_type_arr).forEach((val) => {
              let operatorInfo = data[val];
              operatorInfo.forEach((item) => {
                let operatorName = Object.keys(item).length > 0 ? Object.keys(item)[0] : null;
                let operatorInfo = Object.values(item).length > 0 ? Object.values(item)[0].op_exe_time : [];
                let operatorShape = Object.values(item).length > 0 ? Object.values(item)[0].op_shape : [];
                let sig = false;
                let content = null;
                // init top of three operator info
                if (count_num < 3) {
                  sig = true;
                  const item = {
                    type: 'line',
                    name: operatorName,
                    data: operatorInfo,
                    smooth: true,
                    showSymbol: false,
                  }
                  series.push(item);
                  legend.push(operatorName);
                  content = {
                    name: operatorName,
                    check: sig,
                    data: operatorInfo,
                    detail: operatorShape,
                  }
                } else {
                  sig = false;
                  content = {
                    name: operatorName,
                    check: sig,
                    data: operatorInfo,
                    detail: operatorShape,
                  }
                }
                count_num++;
                details.push(content);
              })
            })
          }
          this.operatorOptions.xAxis.data = series[0].data.map((_v, i) => i + 1);
          this.operatorOptions.series = series;
          this.operatorOptions.legend.data = legend;
          this.topOperatorArr = details;
          let chartObj = echarts.init(document.getElementById('operatorShapeDetailChart'), echartsThemeName);
          this.operatorOptions.tooltip.formatter = (params) => {
            return this.formatChartTip(params);
          }
          this.$nextTick(() => {
            chartObj.setOption(this.operatorOptions, true);
            chartObj.on('click', this.showOperatorDetail);
            this.addDefaultShape(this.topOperatorArr);
          })
        }
      ).catch(() => {
        this.svg.noData = true;
      })
    },
    /**
     * format the chart
     * @param {object} params html dom object
     */
    formatChartTip(params) {
      const tipInnerHTML = [];
      if (params && params.length) {
        const colorArray = ['#c23531', '#2f4554', '#61a0a8'];
        const index = params[0].dataIndex + 1;
        tipInnerHTML.push(`step: ${index}`);
        params.forEach((item, idx) => {
          tipInnerHTML.push(
            `<span class="define-chart-tip" style="background-color:${colorArray[idx]};"></span>` +
            `${item.seriesName}: <span style="margin: 0 6px;">${item.data}</span>`
          );
        });
      }
      return tipInnerHTML.join('<br>');
    },
    /**
     * selector remove the operator by name
     * @param {String} opName operator name
     */
    operatorRemove(opName) {
      if (opName == 'all') {
        this.topOperatorArr.forEach((elm) => {
          elm.check = false;
        })
      } else {
        this.topOperatorArr.forEach((elm) => {
          if (elm.name == opName) {
            elm.check = !elm.check;
            this.drawChart();
          }
        })
      }
    },
    /**
     * init the default shape data
     * @param {Array} details the operator shape data
     */
    addDefaultShape(details) {
      // get top of three operator shape data
      let topThreeArr = details.slice(0, 3);
      topThreeArr.forEach((item) => {
        if (item.check) {
          this.topOperatorValue.push(item.name);
        }
      })
    },
    /**
     * operator select change
     * @param {String} val operator name
     */
    operatorChange(val) {
      if (this.topOperatorValue.indexOf(val) == -1) {
        this.topOperatorValue.push(val);
      } else {
        this.topOperatorValue.forEach((ele) => {
          if (ele == val) {
            this.topOperatorValue.splice(this.topOperatorValue.indexOf(val), 1);
          }
        })
      }
      this.drawChart();
    },
    /**
     * init the operator chart
     */
    drawChart() {
      let series = [];
      let legend = [];
      this.topOperatorArr.forEach((obj) => {
        const check = obj.check;
        if (check) {
          const item = {
            type: 'line',
            name: obj.name,
            data: obj.data,
            smooth: true,
            showSymbol: false,
          }
          series.push(item);
          legend.push(obj.name);
        }
      })
      this.operatorOptions.series = series;
      this.operatorOptions.legend.data = legend;
      let chartObj = echarts.init(document.getElementById('operatorShapeDetailChart'), echartsThemeName);
      this.$nextTick(() => {
        chartObj.setOption(this.operatorOptions, true);
      })
    },
    /**
     * show operator shape detail by click the pointer of echarts 
     * @param {Object} params html dom object
     */
    showOperatorDetail(params) {
      this.showDialogModel = !this.showDialogModel;
      const dataIndex = params.dataIndex;
      this.modelShapeData = [];
      this.topOperatorArr.forEach((item) => {
        if (item.check) {
          const shapeInfoDetail = item.detail[dataIndex];
          const name = item.name;
          const step = dataIndex + 1;
          this.modelShapeData.push({name: name, step: step, value: shapeInfoDetail})
        }
      });
    },
  }
}
</script>
<style>
.operator-shape-step {
  width: 100%;
  height: 100%;
}

.operator-shape-step .shape-step {
  margin: 20px 0;
}

.operator-shape-step .operator-shape-option {
  line-height: 25px;
  height: 25px;
  margin: 0 auto;
  text-align: center;
}

.operator-shape-step .operator-shape-option .operator-filter-title {
  color: #00A5A7;
  margin: 0 10px;
}

.operator-shape-step .operator-shape-select .operator-detail-select {
  border-radius: 10%;
  width: 20%;
  line-height: 30px;
  height: 30px;
  margin: 0 auto;
}

.operator-shape-step .shape-step .shape-step-title {
  height: 40px;
  line-height: 40px;
  font-size: 16px;
  font-weight: bold;
  display: flex;
}

.operator-shape-step .shape-step .shape-step-title .el-icon-info {
  line-height: 40px;
  margin: 0 5px;
}

.operator-shape-step .shape-step .item {
  margin-right: 10px;
  font-size: 20px;
  color: #6c7280;
  cursor: pointer;
}

.operator-shape-step .shape-step .el-input {
  width: 30%;
  margin: 0 50px;
}

.operator-shape-step .shape-step .shape-step-right {
  margin-left: 35px;
}

.operator-shape-step .operator-shape-detail {
  display: flex;
  width: 100%;
  margin: 50px 0;
  height: calc(100% - 200px);
  border: 1px solid var(--border-color);
  flex-grow: 1;
  flex-direction: column;
  overflow-x: auto;
  overflow-y: auto;
}

#operatorShapeDetailChart {
  height: 80%;
  width: 100%
}

.operator-shape-step .operator-shape-title {
  height: 20px;
  font-size: 15px;
  font-weight: bold;
  margin-top: 12px;
  padding: 16px;
}

.define-chart-tip {
display: inline-block;
  margin-right: 5px;
  width: 10px;
  height: 10px;
}

.operator-shape-step .operator-shape-dialog .el-dialog {
  position: relative;
  top: 14%;
  height: 42%;
  overflow-y: auto;
}

.operator-shape-step .image-noData {
  width: 100%;
  height: calc(100% - 10px);
  display: flex;
  justify-content: top;
  align-items: center;
  flex-direction: column;
}

.operator-shape-step .image-noData p {
  font-size: 16px;
  padding-top: 10px;
  text-align: center;
}
</style>
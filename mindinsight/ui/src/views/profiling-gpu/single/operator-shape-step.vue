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
                   v-model="topOperatorValueGPU"
                   @remove-tag="operatorRemoveGPU"
                   :collapse-tags="true"
                   multiple
                   filterable
                   :placeholder="selectTip">
          <el-option
            v-for="(item, index) in topOperatorArr"
            :key="index"
            :label="item.name.length > 20 ? item.name.substring(0, 20) + '...' : item.name"
            disabled
            :value="item.name">
            <el-checkbox :key="item.name"
                         v-model="item.check"
                         :title="item.name"
                         :disabled="checkSig"
                         @change="operatorChangeGPU(item)">
              {{item.name.length > 18 ? item.name.substring(0, 18) + "..." : item.name}}
            </el-checkbox>
          </el-option>
        </el-select>
        <el-radio-group class="operator-type-select" v-model="operatorStatisticType"
                        @change="coreTableChange"
                        fill="#00A5A7"
                        text-color="#FFFFFF"
                        size="small">
          <el-radio-button label="0">operator</el-radio-button>
          <el-radio-button label="1">kernel</el-radio-button>
        </el-radio-group>
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
          :title="operatorShapeTitle"
          :visible.sync="showDialogModel"
          width="50%"
          :close-on-click-modal="false"
          class="details-data-list">
        <el-table :data="modelShapeData"
                  row-key="id"
                  height="300"
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

    <div style="height: 100%">
      <div class="cl-search-box">
        <label>Steps:</label>
        <el-input style="width: 170px;"
                v-model="searchByStepInput"
                  clearable
                  :placeholder = "this.step.label"
                  @clear="searchOpCoreList"
                  @keyup.enter.native="searchOpCoreList">
        </el-input>
        <el-input v-model="searchByTypeInput"
                  :placeholder="  this.$t('operator.searchByType') +
                                  this.$t('symbols.leftbracket') +
                                  this.$t('public.caseMode') +
                                  this.$t('symbols.rightbracket')"
                  clearable
                  @clear="searchOpCoreList"
                  @keyup.enter.native="searchOpCoreList">
        </el-input>
        <el-button @click="searchOpCoreList"
                   :disabled="false">
          {{$t('public.sure')}}
        </el-button>
      </div>
      <el-table :data="opAllTypeList.opDetailList"
                stripe
                tooltip-effect="light"
                border style="width: calc(100% - 20px)"
                :height=" isHeterogeneous ? 'calc(80% - 80px)' :'calc(100% - 80px)' "
                @sort-change="(...args)=>{coreDetailSortChange(opAllTypeList, ...args)}"
                default-expand-all >
        <el-table-column v-if="onType === 'gpu_op_type_info'" v-for="(item,$index) in opAllTypeList.opDetailCol"
                         :property="item"
                         :label="item"
                         :key="$index"
                         :sortable="(item === 'step' || item === 'op_side' ||  item === 'op_shape' ) ? false : 'custom'">
        </el-table-column>
        <el-table-column v-if="onType === 'gpu_cuda_type_info'"  v-for="(item,$index) in opAllTypeList.opDetailCol"
                         :property="item"
                         :label="item"
                         :key="$index"
                         :sortable="(item === 'step' || item === 'block_dim' ||  item === 'grid_dim' ) ? false : 'custom'">
        </el-table-column>
      </el-table>
      <el-pagination
                     v-if="opAllTypeList.opDetailList.length"
                     :current-page="opAllTypeList.opDetailPage.offset + 1"
                     :page-size="opAllTypeList.opDetailPage.limit"
                     :page-sizes="[10, 20, 50]"
                     style="height: 80px;"
                     @current-change="(...args)=>{opDetailPageChange(opAllTypeList, ...args)}"
                     @size-change="(...args)=>{opDetailPageSizeChange(opAllTypeList, ...args)}"
                     layout="total, sizes, prev, pager, next, jumper"
                     :total="opAllTypeList.pageTotal">
      </el-pagination>
    </div>
  </div>

</template>

<script>
import echarts, {echartsThemeName} from '@/js/echarts';
import RequestService from '@/services/request-service';
import CommonProperty from '@/common/common-property';
import {isInteger} from '@/js/utils';
export default {
  props: {
    rankID: String,
    showHelp: Boolean,
  },
  watch:{
    rankID:{
      immediate:true,
      handler(val){
        if(isInteger(val)){
          this.svg.initOver = false;// display  Data Loading
          this.initData();
        }else{
          if (val === '') {
            this.svg.noData = true;
            this.svg.initOver = true; // display no Data
          }
        }
      }
    },
    showHelp:{
      handler(newValue){
          if (!this.newValue) {
            this.newValue.resize();
          }
      }
    },
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
          formatter:function(name){
            return name.length > 12 ?name.substr(0,12)+"...":name;
          },
          tooltip:{
            show:true,
            trigger:'axis'
          },
          padding: [0, 0, 0, 120],
          type: 'scroll',
        },
        color: CommonProperty.dynamicLineColor,
        xAxis: {
          type: 'category',
          name: 'step',
          data: [],
        },
        yAxis: {
          type: 'value',
          name: this.$t('profiling.timeConsume') + '(ms)',
        },
        series: []
      },
      topOperatorValue: [],
      topOperatorValueGPU:[],
      topOperatorArr: [],
      showDialogModel: false,
      modelShapeData: null,
      svg: {
        noData: false,
      },
      selectTip: this.$t('public.select'),
      operatorShapeTitle: this.$t('profiling.operatorShapeTitle'),
      chartObj: null,
      checkSig: false,
      filterCondition:{
        displayOnType:[]
      },
      onType:'gpu_op_type_info',
      operatorStatisticType:0,
      opAllTypeList: {
        opDetailCol: [], //表格中的表头
        opDetailList: [],//表格的数据列表
        pageTotal: 0,
        opDetailPage: {
          offset: 0,
          limit: 10,
        },
        op_filter_condition: {},
        op_sort_condition: {},
      }, // table data of all operator details
      searchByTypeInput: '', // search by ai core type name
      searchByStepInput:'', // search by step
      deviceId: this.rankID,
      step:{
        max:0,
        label:this.$t('profiling.stepInput')
      },
      isHeterogeneous:false
    }
  },
  created() {
    Object.getPrototypeOf(this.$options.components).ElSelect.options.methods.handleFocus = (event) => {};
  },
  mounted() {
    window.addEventListener('resize', this.resizeEchart, false);
    setTimeout(() => {
      this.$bus.$on('collapse', () => {
        this.resizeEchart();
      });
    }, 500);
  },
  methods: {
    /**
     *
     * init  data
     */
    initData(){
      this.$nextTick(() => {
        this.initGpuOperatorShape(this.opAllTypeList,false);
        this.getTableOperatorList(this.opAllTypeList, false);//init table data
        window.addEventListener('resize', this.resizeCallback, false);
        setTimeout(() => {
          this.$bus.$on('collapse', this.resizeEchart);
        }, 300)
      })
    },
    coreTableChange(){
      this.onType = this.operatorStatisticType == 0? "gpu_op_type_info" : "gpu_cuda_type_info";
      this.topOperatorValueGPU =[];
      this.initGpuOperatorShape(this.opAllTypeList,false);
      this.getTableOperatorList(this.opAllTypeList, false);
    },
    /**
     *
     * init table data
     */
    getTableOperatorList(row,isSort){
      const params = {};
      params.params = {
      };
      params.body = {
        dir:this.trainInfo.path,
        device_type: "gpu",
        op_type: this.onType,
        device_id: this.rankID,
        filter_condition: row.op_filter_condition,
        sort_condition: row.op_sort_condition,
        group_condition: row.opDetailPage,
      };
      RequestService.queryDynamicShapeGPU(params).then((res) => {
        if(res && res.data){
          // Format table data and construct it into the format required by the table
          this.getFormatterDetailData(row, res.data.dynamic_info);
        }
      });
    },

    /**
     *
     * init
     */
    initGpuOperatorShape(row,isSort){
      const params = {}
      params.params={
      };
      params.body= {
        dir:this.trainInfo.path,
        device_type: "gpu",
        op_type: this.onType,
        device_id:this.rankID,
        filter_condition:
          {
            step_filter: ["1"],
          },
      };
      let details = [];//
      RequestService.queryDynamicShapeGPU(params).then(
              (res) => {
                if (res && res.data) {
                  this.svg.noData = false;
                  let data = res.data.dynamic_info; // Timeline and tabular data
                  let op_type_arr = data.all_type; //operator type
                  this.isHeterogeneous = res.data.graph_info.is_heterogeneous;
                  //Add an array to the bound drop-down box
                  op_type_arr.forEach((operatorName) => {
                    let content = null;
                    content ={
                          name: operatorName,
                          check: false,
                          data: [],
                        };
                    details.push(content);
                      });
                  this.topOperatorArr = details;
                  // data to be plotted
                  let ssChart = [];
                  this.topOperatorArr.slice(0,3).forEach(
                          elem => ssChart.push(elem.name)
                  );
                  this.checkSig = false;
                  this.topOperatorValueGPU = ssChart;
                  this.getGpuOperatorShape(this.opAllTypeList, false);
                }
              }
      );

    },
    /**
     *
     * init gpu operator shape info by request dynamic shape api
     */
    getGpuOperatorShape(row,isSort){
      const params = {}
      params.params={
      };
      params.body= {
        dir:this.trainInfo.path,
        device_type: "gpu",
        op_type: this.onType,
        device_id: this.rankID,
        filter_condition:
                {
                  dispaly_op_type: this.topOperatorValueGPU,
                },
      }
      let details = [];//
      let series = [];
      let legend = [];
      RequestService.queryDynamicShapeGPU(params).then(
              (res) => {
                if (res && res.data) {
                  this.svg.noData = false;
                  this.svg.initOver = false;
                  let data = res.data.dynamic_info;
                  let op_type_arr = data.all_type;
                  let filter_type = data.filter_type;
                  let count_num = 0;
                  op_type_arr.forEach((operatorName) => {
                    let content = null;
                    let sig = false;
                    if(params.body.filter_condition.dispaly_op_type.includes(operatorName)){
                      sig = true;
                      content ={
                        name: operatorName,
                        check: sig,
                        data: filter_type[operatorName],
                      };
                      const item = {
                        type: 'line',
                        name: operatorName,
                        data: filter_type[operatorName],
                        smooth: true,
                        showSymbol: false,
                      };
                      this.step.max = filter_type[operatorName].length;
                      this.step.label = this.step.label.replace('{max}', this.step.max);
                      series.push(item);
                      legend.push(item.name);
                      count_num++;
                    }else {
                      sig = false;
                      content ={
                        name: operatorName,
                        check: sig,
                        data: [],
                      }
                    }
                    details.push(content)
                  }
                  );
                  // this.getFormatterDetailData(row,isSort);
                }
                this.operatorOptions.xAxis.data = series[0].data.map((_v, i) => i + 1);
                this.operatorOptions.series = series;
                this.operatorOptions.legend.data = legend;
                this.topOperatorArr = details;
                if(!this.chartObj)
                    this.chartObj = echarts.init(document.getElementById('operatorShapeDetailChart'), echartsThemeName);
                this.operatorOptions.tooltip.formatter = (params) => {
                  return this.formatChartTip(params);
                };
                this.$nextTick(() => {
                  this.chartObj.setOption(this.operatorOptions, true);
                })
                this.resizeEchart();
              }
      ).catch(() => {
      })
    },
    /**
     * operator select change
     * @param {String} val operator name
     */
    operatorChangeGPU(item) {
      if (item.check && this.topOperatorValueGPU.indexOf(item.name) == -1) {
        this.topOperatorValueGPU.push(item.name);
      } else if(!item.check){
        this.topOperatorValueGPU.forEach((elm, idx) => {
          if (elm == item.name) {
            this.topOperatorValueGPU.splice(idx, 1)
          }
        })
      }
      if(this.topOperatorValueGPU && this.topOperatorValueGPU.length){ // not null
        this.filterCondition.displayOnType = this.topOperatorValueGPU;
        this.getGpuOperatorShape();
      }else {
        this.operatorOptions.series = [];
        this.operatorOptions.legend.data = [];
      }
      this.drawChart();
      if (this.topOperatorValueGPU.length > 9) {
        this.checkSig = true;
      }
      this.resizeEchart();
    },
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
          this.chartObj = echarts.init(document.getElementById('operatorShapeDetailChart'), echartsThemeName);
          this.operatorOptions.tooltip.formatter = (params) => {
            return this.formatChartTip(params);
          };
          this.$nextTick(() => {
            this.chartObj.setOption(this.operatorOptions, true);
          })
        }
      ).catch(() => {
      })
    },

    /**
     * format the chart
     * @param {object} params html dom object
     */
    formatChartTip(params) {
      const tipInnerHTML = [];
      if (params && params.length) {
        const colorArray = CommonProperty.dynamicLineColor;
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
    operatorRemoveGPU(opName) {
      this.topOperatorArr.forEach((elm) => {
        if (elm.name == opName) {
          elm.check = !elm.check;
          this.drawChart();
        }
      })
      if (this.topOperatorValueGPU.length <= 9) {
        this.checkSig = false;
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
          this.topOperatorValueGPU.push(item.name);
        }
      })
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
      this.chartObj = echarts.init(document.getElementById('operatorShapeDetailChart'), echartsThemeName);
      this.$nextTick(() => {
        this.chartObj.setOption(this.operatorOptions, true);
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
    /**
     * Window resize
     */
    resizeCallback() {
      if (this.chartObj) {
        this.chartObj.resize();
      }
    },
    /**
     * echart resize
     */
    resizeEchart() {
      if (this.chartObj) {
        setTimeout(() => {
          this.chartObj.resize();
        }, 100);
      }
    },

    /**
     * Show operator info deteail
     * @param {Object} cellData cell data
     * @param {Object} column column
     */
    showInfoDetail(cellData, column) {
      if (column.property !== 'op_info' || !cellData || !cellData.op_info) {
        return;
      }
      this.showDialogData(cellData.op_info, column);
    },

    /**
     * Core detail sort
     * @param {Object} row table cell
     * @param {Object} column table cell
     */
    coreDetailSortChange(row, column) {
      row.op_sort_condition = {
        name: column.prop,
        type: column.order,
      };
      row.opDetailPage.offset = 0;
      this.getTableOperatorList(row, false);
    },
    /**
     *  formatter
     */
    getFormatterDetailData(row, detailsDataList) {
      row.opDetailList = [];
      row.opDetailCol = detailsDataList.col_name; // table header
      row.pageTotal = detailsDataList.size; //table data sum
      if (detailsDataList.object) {
        detailsDataList.object.forEach((k) => {
          const data = {};
          detailsDataList.col_name.forEach((item, index) => {
            if (item === 'step') {
              data[item] = JSON.stringify(k[index]);
            } else {
              data[item] = k[index];
            }

            if(item === 'op_shape'){
              data[item] = data[item].join(',').split();
            }
          });
          row.opDetailList.push(data);
        });
      }
    },
    /**
     * Operator detail list page change
     * @param {Object} row table cell
     * @param {Number} pageIndex current page
     */
    opDetailPageChange(row, pageIndex) {
      row.opDetailPage.offset = pageIndex - 1;
      this.getTableOperatorList(row, false);
    },
    /**
     * Operator detail list page size change
     * @param {Object} row table cell
     * @param {Number} pageSize current page size
     */
    opDetailPageSizeChange(row, pageSize) {
      row.opDetailPage.offset = 0;
      row.opDetailPage.limit = pageSize;
      this.getTableOperatorList(row, false);
    },
    searchOpCoreList(){
      // if (this.coreStatisticType) {
        if(this.searchByStepInput > this.step.max)
          this.$message.error(this.$t('profiling.inputError').replace('{max}', this.step.max));

      this.opAllTypeList.op_filter_condition = {};
        if (this.searchByTypeInput) {
          this.opAllTypeList.op_filter_condition['op_type']={
            partial_match_str_in: [this.searchByTypeInput.trim()],
          }
        }
        if(this.searchByStepInput){
          this.opAllTypeList.op_filter_condition['step_filter']=[this.searchByStepInput.trim()];
        }
      if(!this.searchByTypeInput && !this.searchByStepInput){
          this.opAllTypeList.op_filter_condition = {};
        }
        this.opAllTypeList.opDetailPage.offset = 0;
        this.getTableOperatorList(this.opAllTypeList, false);
      }
  },
  /**
   * Object destroyed
   */
  destroyed() {
    // Remove the listener of window size change
    window.removeEventListener('resize', this.resizeCallback);
    this.$bus.$off('collapse');
    if (this.chartObj) {
      this.chartObj.off('mouseover');
      this.chartObj.off('mouseout');
    }
  },

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
  width: 35%;
  line-height: 30px;
  height: 40px;
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
  width: calc(100% - 20px);
  margin: 50px 0;
  height: calc(100% - 150px);
  border: 1px solid var(--border-color);
  flex-grow: 1;
  flex-direction: column;
  overflow-x: auto;
  overflow-y: auto;
}

#operatorShapeDetailChart {
  height: 80%;
  width: 100%;
  margin: 0 auto;
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
  overflow-y: hidden;
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
.cl-search-box {
  float: right;
  margin-bottom: 10px;
  margin-right: 20px;
}
.cl-search-box .el-input {
  width: 300px;
  margin-right: 50px;
}
.operator-type-select {
  padding-left: 40px;
}
</style>

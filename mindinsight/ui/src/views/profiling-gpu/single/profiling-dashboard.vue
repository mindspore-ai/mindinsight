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
  <div class="pro-router-wrap">
    <div class="pro-router-left">
      <!-- Step trace area -->
      <div v-show="!isHeterogeneous" class="step-trace">
        <div class="title-wrap">
          <div class="title" v-show="!svg.noData && !isHeterogeneous ">{{ $t('profiling.stepTrace') }}</div>
          <div class="view-detail" v-if="isDynamic">
            <button @click="viewDetail('step-trace-dynamic')"
                    :disabled="svg.noData && svg.data.length === 0"
                    :class="{disabled:svg.noData && svg.data.length === 0}">{{ $t('profiling.viewDetail') }}
              <i class="el-icon-d-arrow-right"></i></button>
            <!--{disabled:svg.noData && svg.data.length === 0}-->
          </div>
          <div class="view-detail" v-else>
            <button @click="viewDetail('step-trace')"
                    :disabled="svg.noData && svg.data.length === 0"
                    :class="{disabled:svg.noData && svg.data.length === 0}">{{ $t('profiling.viewDetail') }}
              <i class="el-icon-d-arrow-right"></i></button>
          </div>

          <!-- Step trace description -->
          <div class="tip-icon">
            <el-tooltip placement="bottom"
                        effect="light">
              <div slot="content"
                   class="tooltip-container">
                <div class="pro-dash-tooltip">
                  <div class="font-size-style">{{$t("profiling.features")}}</div>
                  <div>{{$t('profiling.iterationInfo')}}</div>
                  <div>
                    <span class="font-style">{{$t('profiling.queueInfo')}}&nbsp;</span>
                    <span>{{$t('profiling.iterationGapInfo')}}</span>
                  </div>
                  <div>
                    <span class="font-style">{{$t('profiling.fpbpTitle')}}&nbsp;</span>
                    <span>{{$t('profiling.fpbpInfo')}}</span>
                  </div>
                  <div>
                    <span class="font-style">{{$t('profiling.iterativeTailingTitle')}}&nbsp;</span>
                    <span>{{$t('profiling.iterativeTailingInfo')}}</span>
                  </div>
                  <br />
                  <div class="font-size-style">{{$t('profiling.statistics')}}</div>
                  <div>{{$t('profiling.totalTime')}}
                    <span>{{totalTime}}{{$t('profiling.millisecond')}}</span>
                  </div>
                  <div>{{$t('profiling.totalSteps')}}<span>{{totalSteps}}</span></div>
                  <div>{{$t('profiling.iterationGapTimeRatio')}}<span>{{iterationIntervalPercent}}</span></div>
                  <div v-if="fpBpPercent">{{$t('profiling.fpbpTimeRatio')}}<span>{{fpBpPercent}}</span></div>
                  <div v-else>{{$t('profiling.fpTimeRatio')}}<span>{{fpPercent}}</span></div>
                  <div v-if="tailPercent">
                    {{$t('profiling.iterativeTailingTimeRatio')}}
                    <span>{{tailPercent}}</span>
                  </div>
                </div>
              </div>
              <i class="el-icon-info"></i>
            </el-tooltip>
          </div>
        </div>
        <!-- Step trace SVG container -->
        <div class="trace-container">
          <div id="trace"
               class="training-trace"
               :style="{height: svg.totalHeight + 'px'}">
            <svg version="1.1"
                 xmlns="http://www.w3.org/2000/svg"
                 height="100%"
                 width="100%">
              <defs>
                <marker id="marker_end"
                        refX="5"
                        refY="4"
                        markerWidth="10"
                        markerHeight="8"
                        orient="auto">
                  <path d="M1,1 L1,7 L9,4 z"
                        fill="#6c7280"
                        stroke="#6c7280"></path>
                </marker>
                <marker id="marker_start"
                        refX="5"
                        refY="4"
                        markerWidth="10"
                        markerHeight="8"
                        orient="auto">
                  <path d="M9,1 L9,7 L1,4 z"
                        fill="#6c7280"
                        stroke="#6c7280"></path>
                </marker>
              </defs>
            </svg>
          </div>
          <div class="image-noData"
               v-if="svg.noData">
            <div>
              <img :src="require('@/assets/images/nodata.png')"
                   alt="" />
            </div>
            <p v-show="!isHeterogeneous && !svg.initOver">{{$t("public.dataLoading")}}</p>
            <p v-show="!isDynamic && svg.initOver">{{isHeterogeneous?$t("profiling.isHeterogeneous"):$t("public.noStepStraceData")}}</p>
          </div>
        </div>
      </div>
      <!--Operator Detail-->
      <div v-show="isHeterogeneous" class="operator-detail">
        <div class="title-wrap">
          <div class="title"> {{$t('profiling.operatorShapeDetail')}}</div>
          <div class="view-detail" v-if="isDynamic">
            <button @click="viewDetail('step-trace-dynamic')"
                    :class="">{{ $t('profiling.viewDetail') }}
              <i class="el-icon-d-arrow-right"></i></button>
            <!--{disabled:svg.noData && svg.data.length === 0}-->
          </div>
          <div class="view-detail" v-else>
            <button @click="viewDetail('step-trace')"
                    :disabled="svg.noData && svg.data.length === 0"
                    :class="{disabled:svg.noData && svg.data.length === 0}"> {{ $t('profiling.viewDetail') }}
              <i class="el-icon-d-arrow-right"></i></button>
          </div>
          <!-- Step trace description -->
          <div class="tip-icon">
            <el-tooltip placement="bottom"
                        effect="light">
              <div slot="content"
                   class="tooltip-container">
                <div class="pro-dash-tooltip">
                  <div class="font-size-style">{{$t("profiling.features")}}</div>
                  <div>{{$t('profiling.gpuOpeatorFeatures')}}</div>
                </div>
              </div>
              <i class="el-icon-info"></i>
            </el-tooltip>
          </div>
        </div>

        <div v-if="isDynamic" class="operator-shape-option">
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
        <div v-show="isDynamic" class="operator-shape-detail" >
          <div class="operator-shape-chart" id="operatorShapeDetailChart">
          </div>
        </div>
        <div class="image-noData"
             v-if="svg.noData">
          <div>
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
          </div>
          <p v-show="isHeterogeneous && !svg.initOver">{{$t("public.dataLoading")}}</p>
          <!--static，display no isHeterogeneous data-->
          <p v-show="!isDynamic && svg.initOver">{{isHeterogeneous?$t("profiling.isHeterogeneous"):$t("public.noData")}}
          </p>
        </div>
      </div>
      <!-- Process summary display area -->
      <div class="minddata">
        <div class="title-wrap">
          <div class="title">{{ $t('profiling.mindData') }}</div>
          <div class="view-detail">
            <button @click="viewDetail('data-process')"
                    :disabled="processSummary.noData"
                    :class="{disabled:processSummary.noData}">
              {{ $t('profiling.viewDetail') }}
              <i class="el-icon-d-arrow-right"></i></button>
          </div>
          <div class="tip-icon">
            <el-tooltip placement="bottom"
                        effect="light">
              <div slot="content"
                   class="tooltip-container">
                <div class="pro-dash-tooltip">
                  <div class="font-size-style">{{$t("profiling.features")}}</div>
                  <div>{{$t('profilingGPU.dataProcess')}}</div>
                  <div>{{$t('profilingGPU.dataProcessInfo')}}</div>
                  <div>{{$t('profilingGPU.analysisOne')}}</div>
                  <div>{{$t('profilingGPU.analysisTwo')}}</div>
                  <div v-show="deviceInfoShow || queueInfoShow">{{$t('profiling.higherAnalysis')}}</div>
                  <br />
                  <div v-show="deviceInfoShow || queueInfoShow"
                       class="font-size-style">{{$t('profiling.statistics')}}</div>
                  <div v-show="queueInfoShow">{{$t('profilingGPU.chipInfo')}}
                    <span>{{processSummary.get_next.empty}} / {{processSummary.get_next.total}}</span>
                  </div>
                  <div v-show="deviceInfoShow">
                    <div>{{$t('profiling.hostIsEmpty')}}
                      <span>{{processSummary.device.empty}} / {{processSummary.device.total}}</span>
                    </div>
                    <div>{{$t('profiling.hostIsFull')}}
                      <span>{{processSummary.device.full}} / {{processSummary.device.total}}</span>
                    </div>
                  </div>

                </div>
              </div>
              <i class="el-icon-info"></i>
            </el-tooltip>
          </div>
        </div>
        <div class="pipeline-container"
             v-show="!processSummary.noData">
          <div class="cell-container data-process">
            <div class="title">
              {{$t('profiling.pipeline')}}
            </div>
          </div>

          <div class="queue-container">
            <div class="img">
              <div class="edge">
                <img src="@/assets/images/data-flow.png"
                     alt="" />
              </div>
              <div class="icon">
                <img src="@/assets/images/queue.svg"
                     alt=""
                     clickKey="connector_queue" />
              </div>
              <div class="edge">
                <img src="@/assets/images/data-flow.png"
                     alt="" />
              </div>
            </div>
            <div class="title">{{$t('profiling.connectorQuene')}}</div>
            <div class="description">
              <div class="item"
                   v-if="processSummary.device.empty || processSummary.device.empty === 0">
                {{$t('profiling.queueTip2')}}
                <span class="num">
                  {{processSummary.device.empty}} / {{processSummary.device.total}}
                </span>
              </div>
              <div class="item"
                   v-if="processSummary.device.full || processSummary.device.full === 0">
                {{$t('profiling.queueTip1')}}
                <span class="num">
                  {{processSummary.device.full}} / {{processSummary.device.total}}
                </span>
              </div>
            </div>
          </div>

          <div class="cell-container device_queue_op"
               clickKey="device_queue_op">
            <div class="title">
              {{$t('profiling.deviceQueueOp')}}
            </div>
          </div>

          <div class="queue-container"
               v-if="processSummary.count === processSummary.maxCount">
            <div class="img">
              <div class="edge">
                <img src="@/assets/images/data-flow.png"
                     alt="" />
              </div>
              <div class="icon">
                <img src="@/assets/images/queue.svg"
                     clickKey="data_queue"
                     alt="" />
              </div>
              <div class="edge">
                <img src="@/assets/images/data-flow.png"
                     alt="" />
              </div>
            </div>
            <div class="title">{{$t('profiling.dataQueue')}}</div>
            <div class="description">
              <div class="item"
                   v-if="processSummary.get_next.empty || processSummary.get_next.empty === 0">
                {{$t('profiling.queueTip2')}}
                <span class="num">
                  {{processSummary.get_next.empty}} / {{processSummary.get_next.total}}
                </span>
              </div>
              <div class="item"
                   v-if="processSummary.get_next.full || processSummary.get_next.full === 0">
                {{$t('profiling.queueTip1')}}
                <span class="num">
                  {{processSummary.get_next.full}} / {{processSummary.get_next.total}}
                </span>
              </div>
            </div>
          </div>

          <div class="cell-container get-next"
               clickKey="get_next"
               v-if="processSummary.count === processSummary.maxCount">
            <div class="title">
              {{$t('profiling.getData')}}
            </div>
          </div>
        </div>
        <div class="image-noData"
             v-if="processSummary.noData">
          <div>
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
          </div>
          <p v-show="!processSummary.initOver">{{$t("public.dataLoading")}}</p>
          <p v-show="processSummary.initOver">{{$t("public.noData")}}</p>
        </div>
      </div>
    </div>
    <!-- Operator information display area -->
    <div class="pro-router-right">
      <div class="op-time-consume">
        <div class="title-wrap">
          <div class="title">{{ $t('profiling.rankOfOperator') }}</div>
          <div class="view-detail">
            <button @click="viewDetail('operator')"
                    :disabled="pieChart.noData && pieChart.data.length === 0"
                    :class="{disabled:pieChart.noData && pieChart.data.length === 0}">{{ $t('profiling.viewDetail') }}
              <i class="el-icon-d-arrow-right"></i></button>
          </div>
        </div>
        <div class="image-noData"
             v-if="pieChart.noData">
          <div>
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
          </div>
          <p v-show="!pieChart.initOver">{{$t("public.dataLoading")}}</p>
          <p v-show="pieChart.initOver">{{$t("public.noData")}}</p>
        </div>

        <div class="op-time-content">
          <div id="pieChart"
               class="pie-chart"
               v-if="pieChart.data.length"></div>
          <!-- Operator time consumption top5 -->
          <div class="time-list"
               v-if="pieChart.data.length">
            <ul>
              <li v-for="(item, index) in pieChart.topN"
                  :key="index"
                  class="item">
                <span class="index"
                      :style="{'background-color': pieChart.colorList[index]}">{{index + 1}}</span>
                <span class="name">{{item.name}}</span>
                <span class="num">{{item.frequency + $t('profiling.times')}}</span>
                <span class="time">
                  <span class="bar"
                        :style="{width: item.time / pieChart.topN[0].time * 100 + '%'}"></span>
                  <span class="value">{{item.time + $t('profiling.gpuunit')}}</span>
                </span>
              </li>
            </ul>
          </div>
        </div>
      </div>
      <!-- Time line display area -->
      <div class="time-line">
        <div class="title-wrap">
          <div class="title">{{ $t('profiling.timeLine') }}</div>
          <div class="view-detail">
            <button @click="queryTimeline"
                    v-show="!timeLine.waiting"
                    :disabled="timeLine.disable"
                    :class="{disabled:timeLine.disable}">{{ $t('profiling.downloadTimeline') }}
            </button>
            <div class="el-icon-loading loading-icon"
                 v-show="timeLine.waiting"></div>
          </div>
          <div class="tip-icon">
            <el-tooltip placement="bottom"
                        effect="light">
              <div slot="content"
                   class="tooltip-container">
                <div class="pro-dash-tooltip">
                  <div class="font-size-style">{{$t("profiling.features")}}</div>
                  <div class="font-style">{{$t("profiling.timelineTips.title1")}}</div>
                  <div>{{$t("profiling.timelineTips.content12")}}</div>
                  <div>{{$t("profiling.timelineTips.content13")}}</div>
                  <div>{{$t("profiling.timelineTips.content14")}}</div>
                  <br>
                  <div class="font-style">{{$t("profiling.timelineTips.title2")}}</div>
                  <div>
                    {{$t("profiling.timelineTips.content21.part1")}}
                    <b>{{$t("profiling.timelineTips.content21.part2")}}</b>
                    {{$t("profiling.timelineTips.content21.part3")}}
                  </div>
                  <div>{{$t("profiling.timelineTips.content22")}}</div>
                  <div>
                    {{$t("profiling.timelineTips.content23.part1")}}
                    <b>{{$t("profiling.timelineTips.content23.part2")}}</b>
                    {{$t("profiling.timelineTips.content23.part3")}}
                    <b>{{$t("profiling.timelineTips.content23.part4")}}</b>
                    {{$t("profiling.timelineTips.content23.part5")}}
                    <b>{{$t("profiling.timelineTips.content23.part6")}}</b>
                    {{$t("profiling.timelineTips.content23.part7")}}
                  </div>
                  <br>
                  <div class="font-style">{{$t("profiling.timelineTips.title3")}}</div>
                  <div>{{$t("profiling.timelineTips.content31")}}</div>
                  <div>{{$t("profiling.timelineTips.content32")}}</div>
                  <br>
                  <div class="font-style">{{$t("profiling.timelineTips.title4")}}</div>
                  <div>{{$t("profiling.timelineTips.content41")}}</div>
                  <div class="indent">{{$t("profiling.timelineTips.content42")}}</div>
                  <div class="indent">{{$t("profiling.timelineTips.content43")}}</div>
                  <div class="indent">{{$t("profiling.timelineTips.content44")}}</div>
                  <div>{{$t("profiling.timelineTips.content45")}}</div>
                  <div>{{$t("profiling.timelineTips.content46")}}</div>
                  <div>{{$t("profiling.timelineTips.content47")}}</div>
                  <div>{{$t("profiling.timelineTips.content48")}}</div>
                  <div class="indent">{{$t("profiling.timelineTips.content49")}}</div>
                  <div class="indent">{{$t("profiling.timelineTips.content410")}}</div>
                  <div class="indent">{{$t("profiling.timelineTips.content411")}}</div>
                  <div class="indent">{{$t("profiling.timelineTips.content412")}}</div>
                </div>
              </div>
              <i class="el-icon-info"></i>
            </el-tooltip>
          </div>
        </div>
        <!-- Time line detail  -->
        <div class="timeline-info"
             v-if="!timelineInfo.noData">
          <div class="info-line">
            <span>{{$t('profiling.scopeNameNum')}}</span><span>
              <el-select v-model="timelineInfo.scopeNameNum"
                         :placeholder="$t('public.select')"
                         class="scope-name">
                <el-option v-for="item in timelineInfo.scopeNameNumArr"
                           :key="item.value"
                           :label="item.label"
                           :value="item.value">
                </el-option>
              </el-select>
            </span>
          </div>
          <div class="info-line">
            <span>{{$t('profiling.opTotalTime')}}</span><span>{{timelineInfo.totalTime}}ms</span>
          </div>
          <div class="info-line">
            <span>{{$t('profiling.streamNum')}}</span><span>{{timelineInfo.streamNum}}</span>
          </div>
          <div class="info-line">
            <span>{{$t('profiling.opNum')}}</span><span>{{timelineInfo.opNum}}</span>
          </div>
          <div class="info-line">
            <span>{{$t('profiling.opTimes')}}</span><span>{{timelineInfo.opTimes}}{{$t('profiling.times')}}</span>
          </div>
        </div>
        <div class="image-noData"
             v-if="timelineInfo.noData">
          <div>
            <img :src="require('@/assets/images/nodata.png')"
                 alt="" />
          </div>
          <p v-show="!timelineInfo.initOver">{{$t("public.dataLoading")}}</p>
          <p v-show="timelineInfo.initOver">{{$t("public.noData")}}</p>
        </div>

      </div>
    </div>
  </div>
</template>
<script>
import echarts ,{echartsThemeName}from '@/js/echarts';
import RequestService from '@/services/request-service';
import CommonProperty from '@/common/common-property';
export default {
  data() {
    return {
      trainingJobId: this.$route.query.id, // Training job id
      summaryPath: this.$route.query.dir, // Summary path data
      relativePath: this.$route.query.path, // Relative path of summary log
      currentCard: '', // current device card
      queueInfoShow: false, // Whether to show queue information
      deviceInfoShow: false, // Whether to show device information
      fpBpPercent: '--', // Ratio of time consumed by forward and backward propagation
      fpPercent: '--', // Ratio of time consumed by forward propagation
      iterationIntervalPercent: '--', // Ratio of time consumed by step interval
      totalSteps: '--',
      totalTime: '--',
      tailPercent: '--', // Ratio of time consumed by step tail
      // graphMode:this.$route.query.graphMode,
      isDynamic:this.$route.query.graphMode === 'dynamic' ? true : false, // dynamic

      svg: {
        // Step trace svg information
        data: [], // Data of svg
        svgPadding: 20, // Padding of svg
        totalWidth: 0, // Total width of svg
        totalTime: 0,
        cellHeight: 40,
        cellPadding: 0,
        rowPadding: 20,
        rowMargin: 10,
        totalHeight: 0,
        markerPadding: 4,
        minRate: 0.1, // Minimum time share threshold of non wrapping display
        minTime: 0, // Minimum time for non wrapping display
        minWidth: 1, // Minimum width of graphics in SVG
        fontSize: 12,
        textMargin: 21, // The minimum margin of the text from the border
        namespaceURI: 'http://www.w3.org/2000/svg', // XML namespace
        resizeTimer: null, // Response delay of resize event
        colors: {
          // Colors of different types of data presentation
          iteration_interval: [
            CommonProperty.stepTraceThemes[this.$store.state.themeIndex].reactIterationIntervalStroke,
            CommonProperty.stepTraceThemes[this.$store.state.themeIndex].reactIterationIntervalFill,
          ],
          fp_and_bp: [
            CommonProperty.stepTraceThemes[this.$store.state.themeIndex].reactFpAndBpstroke,
            CommonProperty.stepTraceThemes[this.$store.state.themeIndex].reactFpAndBpFill,
          ],
          tail: [
            CommonProperty.stepTraceThemes[this.$store.state.themeIndex].reactTailStroke,
            CommonProperty.stepTraceThemes[this.$store.state.themeIndex].reactTailFill,
          ],
          stream_parallel: ['#01a5a7', '#cceded'],
        },
        noData: true,
        initOver: false,
      },
      processSummary: {
        // Data of process summary
        noData: true,
        count: 6,
        maxCount: 6,
        device: {
          empty: 0, // Number of empty devices
          full: 0, // Number of full devices
          total: 0, // Total number of devices
        },
        get_next: {
          empty: 0,
          full: 0,
          total: 0,
        },
        initOver: false, // Is initialization complete
      },
      pieChart: {
        // Pie graph information of operators
        chartDom: null,
        data: [],
        noData: true,
        topN: [],
        colorList: CommonProperty.pieColorArr[this.$store.state.themeIndex],
        initOver: false, // Is initialization complete
      },
      timeLine: {
        // Time line data
        data: null,
        waiting: false, // Is it waiting for interface return
        disable: true,
      },
      timelineInfo: {
        // Time line information
        totalTime: 0,
        streamNum: 0,
        opNum: 0, // Number of operators
        opTimes: 0, // Operator time consuming
        noData: true,
        initOver: false, // Is initialization complete
        scopeNameNum: '',
        scopeNameNumArr: [],
      },
      themeIndex: this.$store.state.themeIndex,
      isHeterogeneous: false,
      operatorOptions: { // operator
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
            trigger:'axis',
            formatter:null
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
      selectTip: this.$t('public.select'),
      onType:'gpu_op_type_info',
      operatorStatisticType:0,
      checkSig: false,
      chartObj: null,
      filterCondition:{
        displayOnType:[]
      },
      step:{
        max:0,
        label:this.$t('profiling.stepInputTip')
      },
    };
  },
  mounted() {
    setTimeout(() => {
      this.$bus.$on('collapse', this.resizeTrace);
      this.$bus.$on('collapse', this.resizeEchart);

    }, 500);
  },
  watch: {
    // Monitor current card information
    '$parent.curDashboardInfo': {
      handler(newValue, oldValue) {
        if (newValue.curCardNum === '') {
          this.svg.noData = true;
          this.svg.initOver = true;
          this.pieChart.noData = true;
          this.pieChart.initOver = true;
          this.processSummary.initOver = true;
          this.timelineInfo.initOver = true;
          this.timeLine.waiting = false;
        }
        if (newValue.query.dir && newValue.query.id && newValue.query.path && newValue.curCardNum) {
          this.summaryPath = newValue.query.dir;
          this.trainingJobId = newValue.query.id;
          this.relativePath = newValue.query.path;
          this.currentCard = newValue.curCardNum;
          if (this.trainingJobId) {
            document.title = `${this.trainingJobId}-${this.$t('profiling.profilingDashboard')}-MindInsight`;
          } else {
            document.title = `${this.$t('profiling.profilingDashboard')}-MindInsight`;
          }
          this.svg.initOver = false;
          this.pieChart.initOver = false;
          this.processSummary.initOver = false;
          this.timelineInfo.initOver = false;
          this.init();
        }
      },
      deep: true,
      immediate: true,
    },
  },
  methods: {
    /**
     * Initialization function
     */
    init() {
      this.queryTimelineInfo();
      this.initPieChart();
      this.getProccessSummary();
      // this.queryTrainingTrace();
      if(this.isDynamic){
        this.$nextTick(() => {
          this.initDynamicShape();
          this.initGpuOperatorShape();
          window.addEventListener('resize', this.resizeCallback, false);
          window.addEventListener('resize', this.resizeEchart, false);
        })
      }else{
        this.queryTrainingTrace();
      }
      // initial data
      window.addEventListener('resize', this.resizeTrace, false);
      window.addEventListener('resize', this.resizeEchart, false);
    },
    /**
     * Get the data of process summary
     */
    getProccessSummary() {
      const params = {
        train_id: this.trainingJobId,
        profile: this.summaryPath,
        device_id: this.currentCard,
      };
      RequestService.queryProcessSummary(params).then((resp) => {
        this.processSummary.initOver = true;
        if (resp && resp.data) {
          const data = JSON.parse(JSON.stringify(resp.data));
          this.processSummary.count = Object.keys(data).length;
          this.dealProcess(data);
        } else {
          this.dealProcess(null);
          this.processSummary.initOver = true;
        }
      });
    },
    /**
     * Set the data of process
     * @param {Object} data The data of process
     */
    dealProcess(data) {
      this.processSummary.device = {
        empty: 0,
        full: 0,
        total: 0,
      };
      this.processSummary.get_next = {
        empty: 0,
        full: 0,
        total: 0,
      };
      this.processSummary.noData = true;

      if (data && Object.keys(data).length) {
        if (data.device_queue_info && data.device_queue_info.summary) {
          this.deviceInfoShow = true;
          this.processSummary.device = {
            empty: data.device_queue_info.summary.empty_batch_count,
            full: data.device_queue_info.summary.total_batch - data.device_queue_info.summary.empty_batch_count,
            total: data.device_queue_info.summary.total_batch,
          };
        }
        if (data.get_next_queue_info && data.get_next_queue_info.summary) {
          this.queueInfoShow = true;
          this.processSummary.get_next = {
            empty: data.get_next_queue_info.summary.empty_batch_count,
            full: data.get_next_queue_info.summary.total_batch - data.get_next_queue_info.summary.empty_batch_count,
            total: data.get_next_queue_info.summary.total_batch,
          };
        }
        this.processSummary.noData = false;
      }
    },
    /**
     * Router link
     * @param { String } path  router path
     */
    viewDetail(path) {
      this.$router.push({
        path,
        query: {
          id: this.trainingJobId,
          dir: this.summaryPath,
          path: this.relativePath,
          graphMode:this.$route.query.graphMode
        },
      });
    },
    /**
     * Chart setOption
     */
    setPieOption() {
      const option = {};
      option.tooltip = {
        trigger: 'item',
        formatter: (params) => {
          return `${params.data.name}<br>${params.marker}${params.percent}%`;
        },
        confine: true,
        extraCssText: 'white-space:normal; word-break:break-word;',
      };
      option.series = [
        {
          type: 'pie',
          center: ['50%', '50%'],
          data: this.pieChart.data,
          radius: '80%',
          label: {
            normal: {
              show: false,
              positionL: 'inner',
            },
          },
          itemStyle: {
            normal: {
              color: (params) => {
                return CommonProperty.pieColorArr[this.$store.state.themeIndex][params.dataIndex];
              },
            },
          },
        },
      ];
      this.$nextTick(() => {
        const dom = document.getElementById('pieChart');
        if (dom) {
          this.pieChart.chartDom = echarts.init(dom, null);
        } else {
          if (this.pieChart.chartDom) {
            this.pieChart.chartDom.clear();
          }
          return;
        }
        this.pieChart.chartDom.setOption(option, true);
        this.pieChart.chartDom.resize();
      }, 10);
    },
    /**
     * Init chart
     */
    initPieChart() {
      const params = {};
      params.params = {
        profile: this.summaryPath,
        train_id: this.trainingJobId,
      };
      params.body = {
        op_type: 'gpu_op_type',
        device_id: this.currentCard,
        filter_condition: {},
        sort_condition: {
          name: 'avg_time',
          type: 'descending',
        },
      };
      RequestService.getProfilerOpData(params)
        .then((res) => {
          this.pieChart.initOver = true;
          if (res && res.data) {
            if (res.data.object) {
              this.pieChart.data = [];
              res.data.object.forEach((item) => {
                if (this.pieChart.data && this.pieChart.data.length < 5) {
                  this.pieChart.data.push({
                    name: item[0],
                    value: item[4],
                    frequency: item[1],
                    percent: item[3],
                  });
                } else {
                  if (!this.pieChart.data[5]) {
                    this.pieChart.data[5] = {
                      name: 'Other',
                      value: 0,
                      percent: 0,
                    };
                  }
                  this.pieChart.data[5].value += item[4];
                  this.pieChart.data[5].percent += item[3];
                }
              });
              this.setPieOption();
              this.pieChart.noData = !!!this.pieChart.data.length;
              this.pieChart.topN = this.pieChart.data.slice(0, Math.min(this.pieChart.data.length, 5)).map((i) => {
                return {
                  name: i.name,
                  time: i.value,
                  frequency: i.frequency,
                };
              });
            }
          }
        })
        .catch(() => {
          this.pieChart.data = [];
          this.pieChart.noData = true;
          this.pieChart.initOver = true;
        });
    },
    /**
     * Query the data of time line
     */
    queryTimelineInfo() {
      const params = {
        dir: this.relativePath,
        device_id: this.currentCard,
        device_type: 'gpu',
      };
      RequestService.queryTimelineInfo(params)
        .then((res) => {
          this.timelineInfo.initOver = true;
          if (res && res.data) {
            this.timelineInfo.noData = false;

            this.timelineInfo.totalTime =
              this.toFixedFun(res.data.total_time, 4) || (res.data.total_time === 0 ? 0 : '--');
            this.timelineInfo.streamNum = res.data.num_of_streams || (res.data.num_of_streams === 0 ? 0 : '--');
            this.timelineInfo.opNum = res.data.num_of_ops || (res.data.num_of_ops === 0 ? 0 : '--');
            this.timelineInfo.opTimes = res.data.op_exe_times || (res.data.op_exe_times === 0 ? 0 : '--');
            if (res.data.max_scope_name_num >= 0) {
              this.timelineInfo.scopeNameNum = res.data.max_scope_name_num;
              this.timelineInfo.scopeNameNumArr = Array(res.data.max_scope_name_num + 1)
                .fill()
                .map((value, key) => {
                  return {
                    label: key,
                    value: key,
                  };
                });
              this.timeLine.disable = false;
            } else {
              this.timeLine.disable = true;
            }
          } else {
            this.timelineInfo.noData = true;
            this.timeLine.disable = true;
          }
        })
        .catch(() => {
          this.timelineInfo.noData = true;
          this.timelineInfo.initOver = true;
          this.timeLine.disable = true;
        });
    },
    queryTimeline() {
      this.timeLine.waiting = true;
      this.timeLine.disable = true;
      const params = {
        dir: this.relativePath,
        device_id: this.currentCard,
        device_type: 'gpu',
        scope_name_num: this.timelineInfo.scopeNameNum,
      };
      RequestService.queryTimeline(params)
        .then((res) => {
          this.timeLine.waiting = false;
          this.timeLine.disable = false;
          if (res && res.data && res.data.length) {
            this.timeLine.data = JSON.stringify(res.data);
            this.downloadTimelineFile();
          }
        })
        .catch(() => {
          this.timeLine.waiting = false;
        });
    },
    /**
     * Download timeline data file
     */
    downloadTimelineFile() {
      const downloadLink = document.createElement('a');
      downloadLink.download = this.getDocName();
      downloadLink.style.display = 'none';
      const blob = new Blob([this.timeLine.data]);
      downloadLink.href = URL.createObjectURL(blob);
      document.body.appendChild(downloadLink);
      downloadLink.click();
      document.body.removeChild(downloadLink);
    },
    /**
     * Generate a download file name
     * @return {String}
     */
    getDocName() {
      const dealNumber = (value) => {
        const prefix = value < 10 ? '0' : '';
        return prefix + value;
      };
      const replacedPrefix = './';
      let dir = this.summaryPath;
      if (dir === replacedPrefix) dir = ' ';
      if (dir.startsWith(replacedPrefix)) dir = dir.replace(replacedPrefix, '');
      const date = new Date();
      const year = date.getFullYear();
      const mouth = dealNumber(date.getMonth() + 1);
      const day = dealNumber(date.getDate());
      const hour = dealNumber(date.getHours());
      const minute = dealNumber(date.getMinutes());
      const second = dealNumber(date.getSeconds());
      const millisecond = date.getMilliseconds();
      const timestamp = `${year}${mouth}${day}${hour}${minute}${second}${millisecond}`;
      return `timeline_${dir}_${this.currentCard}_scope-num-${this.timelineInfo.scopeNameNum}_${timestamp}.json`;
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
     * init dynamic shape info by request dynamic shape api
     */
    initDynamicShape(){
      const params = {};
      params.params={
      };
      params.body= {
        dir:this.relativePath,
        type : 0,
        device_type: "gpu",
        op_type: "gpu_op_type_info",
        device_id: this.currentCard,
        filter_condition:
                {
                  op_type: {partial_match_str_in: []},
                  dispaly_op_type: [],
                  step_filter: ["1"],
                },
      };
      RequestService.queryDynamicShapeGPU(params).then(
              (res) => {
                this.svg.initOver = true;
                this.svg.noData = false;
                this.isHeterogeneous = res.data.graph_info.is_heterogeneous;
                if (res && res.data && res.data.graph_info.training_trace_graph && res.data.graph_info.training_trace_graph.length) {
                  this.removeTrace();
                  this.$nextTick(() => {
                    this.packageTraceData(JSON.parse(JSON.stringify(res.data.graph_info.training_trace_graph)));
                  });

                  // Set the display information in tip
                  if (res.data.graph_info.summary) {
                    this.fpBpPercent = res.data.graph_info.summary.fp_and_bp_percent;
                    this.fpPercent = res.data.graph_info.summary.fp_percent;
                    this.iterationIntervalPercent = res.data.graph_info.summary.iteration_interval_percent;
                    this.totalSteps = res.data.graph_info.summary.total_steps;
                    this.totalTime = res.data.graph_info.summary.total_time;
                    this.tailPercent = res.data.graph_info.summary.tail_percent;
                  } else {
                    this.fpBpPercent = '--';
                    this.iterationIntervalPercent = '--';
                    this.totalSteps = '--';
                    this.totalTime = '--';
                    this.tailPercent = '--';
                  }
                } else {
                  this.svg.totalHeight = 0;
                  // this.svg.noData = true;
                  this.svg.data = [];
                  this.svg.initOver = true;
                  this.removeTrace();
                }
              },
              (error) => {
                this.svg.totalHeight = 0;
                this.svg.noData = true;
                this.svg.data = [];
                this.svg.initOver = true;
                this.removeTrace();
                this.fpBpPercent = '--';
                this.iterationIntervalPercent = '--';
                this.totalSteps = '--';
                this.totalTime = '--';
                this.tailPercent = '--';
                this.isHeterogeneous = false;
              }
      )
    },
    /**
     * Get the data of training trace
     */
    queryTrainingTrace() {
      const params = {
        dir: this.relativePath,
        type: 0,
        device_id: this.currentCard,
      };
      RequestService.queryTrainingTrace(params).then(
        (res) => {
          this.isHeterogeneous = res.data.is_heterogeneous;
          if (res && res.data && res.data.training_trace_graph && res.data.training_trace_graph.length) {
            this.svg.noData = false;
            this.svg.initOver = true;
            this.removeTrace();
            this.$nextTick(() => {
              this.packageTraceData(JSON.parse(JSON.stringify(res.data.training_trace_graph)));
            });

            // Set the display information in tip
            if (res.data.summary) {
              this.fpBpPercent = res.data.summary.fp_and_bp_percent;
              this.fpPercent = res.data.summary.fp_percent;
              this.iterationIntervalPercent = res.data.summary.iteration_interval_percent;
              this.totalSteps = res.data.summary.total_steps;
              this.totalTime = res.data.summary.total_time;
              this.tailPercent = res.data.summary.tail_percent;
            } else {
              this.fpBpPercent = '--';
              this.iterationIntervalPercent = '--';
              this.totalSteps = '--';
              this.totalTime = '--';
              this.tailPercent = '--';
            }
          } else {
            this.svg.totalHeight = 0;
            this.svg.noData = true;
            this.svg.data = [];
            this.svg.initOver = true;
            this.removeTrace();
          }
        },
        (error) => {
          this.svg.totalHeight = 0;
          this.svg.noData = true;
          this.svg.data = [];
          this.svg.initOver = true;
          this.removeTrace();
          this.fpBpPercent = '--';
          this.iterationIntervalPercent = '--';
          this.totalSteps = '--';
          this.totalTime = '--';
          this.tailPercent = '--';
          this.isHeterogeneous = false;
        }
      );
    },
    /**
     * Encapsulating the data of training trace
     * @param {Object} traceGraph Data of training trace
     */
    packageTraceData(traceGraph) {
      this.svg.totalTime = 0;
      this.svg.minTime = 0;
      this.svg.totalHeight = 0;
      const data = [];

      if (traceGraph && traceGraph[0] && traceGraph[0][0]) {
        this.svg.totalTime = traceGraph[0][0].duration;
        this.svg.minTime = this.svg.minRate * this.svg.totalTime;

        // If there is data less than the minimum time in each row,
        // the data in each row is divided into several rows
        traceGraph.forEach((row, index) => {
          const rowObj = {
            rowCount: 0,
            data: [],
            height: 0,
            startY: this.svg.totalHeight,
          };
          let obj = [];
          for (let i = 0; i < row.length; i++) {
            if (row[i].duration < this.svg.minTime) {
              if (obj.length) {
                rowObj.data.push(obj);
                obj = [];
                rowObj.rowCount++;
              }
              rowObj.data.push([row[i]]);
              rowObj.rowCount++;
            } else {
              obj.push(row[i]);
            }

            if (i === row.length - 1 && obj.length) {
              rowObj.data.push(obj);
              obj = [];
              rowObj.rowCount++;
            }
          }
          rowObj.height =
            rowObj.rowCount * this.svg.cellHeight +
            (rowObj.rowCount - 1) * this.svg.cellPadding +
            (index ? this.svg.rowPadding * 2 : 0);

          this.svg.totalHeight += rowObj.height + this.svg.rowMargin;
          data.push(rowObj);
        });

        this.svg.totalHeight += this.svg.rowPadding;
        this.svg.data = JSON.parse(JSON.stringify(data));

        this.$nextTick(() => {
          this.dealTraceData();
        });
      }
    },
    /**
     * Processing the data of training trace, Control data generation svg
     */
    dealTraceData() {
      const traceDom = document.querySelector('#trace');
      if (traceDom) {
        this.svg.totalWidth = traceDom.offsetWidth - this.svg.svgPadding * 2;

        if (this.svg.data[0] && this.svg.data[0].data.length) {
          const svg = traceDom.querySelector('svg');
          if (this.svg.totalTime) {
            this.svg.data.forEach((item, index) => {
              let itemDom = {};
              if (index) {
                itemDom = this.createMultipleRowContainer(item);
              } else {
                itemDom = this.createRowContainer(item.data, item.startY);
              }
              svg.appendChild(itemDom);
            });
          }
        } else {
          this.removeTrace();
        }
      }
    },
    /**
     * Generate a container with multiple rows
     * @param {Object} item Multi row data
     * @return {Object} Generated DOM object
     */
    createMultipleRowContainer(item) {
      const rectContainer = document.createElementNS(this.svg.namespaceURI, 'g');
      rectContainer.setAttribute('class', 'container');

      const rect = document.createElementNS(this.svg.namespaceURI, 'rect');
      rect.setAttribute('x', this.svg.svgPadding);
      rect.setAttribute('y', item.startY + this.svg.rowPadding);
      rect.setAttribute('height', item.height);
      rect.setAttribute('width', this.svg.totalWidth);
      rect.setAttribute(
        'style',
        `fill:${CommonProperty.stepTraceThemes[this.$store.state.themeIndex].reactContainerFill};stroke:${
          CommonProperty.stepTraceThemes[this.$store.state.themeIndex].reactContainerStroke
        };stroke-width:1`
      );
      rectContainer.appendChild(rect);

      const temp = this.createRowContainer(item.data, item.startY + this.svg.rowPadding);
      rectContainer.appendChild(temp);
      return rectContainer;
    },
    /**
     * DOM for generating a single SVG image
     * @param {Object} data Data of single SVG image
     * @param {Number} startY Start y position of box
     * @return {Object}
     */
    createRowContainer(data, startY) {
      const g = document.createElementNS(this.svg.namespaceURI, 'g');

      data.forEach((row, index) => {
        const y = startY + this.svg.rowPadding + index * (this.svg.cellPadding + this.svg.cellHeight);
        row.forEach((i) => {
          if (i.duration) {
            let temp;
            if (i.name) {
              temp = this.createRect(i, y);
              g.insertBefore(temp, g.querySelector('g'));
            } else {
              temp = this.createArrow(i, y);
              g.appendChild(temp);
            }
          }
        });
      });
      return g;
    },
    /**
     * Create a box DOM from the data
     * @param {Object} data Data of single SVG image
     * @param {Number} startY Start y position of box
     * @return {Object}
     */
    createRect(data, startY) {
      const color =
        data.name && this.svg.colors[data.name] ? this.svg.colors[data.name] : this.svg.colors.stream_parallel;
      // Start x position of box
      const x1 = (data.start / this.svg.totalTime) * this.svg.totalWidth + this.svg.svgPadding;
      // The width of the box
      const width = Math.max(this.svg.minWidth, (data.duration / this.svg.totalTime) * this.svg.totalWidth);

      // Contents of the box
      let name = '';
      switch (data.name) {
        case 'iteration_interval':
          name = this.$t('profiling.iterationGap');
          break;
        case 'fp_and_bp':
          name = this.$t('profiling.deviceQueueOpTip');
          break;
        case 'fp':
          name = this.$t('profiling.deviceQueueOpFpTip');
          break;
        case 'tail':
          name = this.$t('profiling.iterationTail');
          break;
        default:
          name = data.name;
          break;
      }

      const textContent = `${name}: ${this.toFixedFun(data.duration, 4)}ms`;
      const textWidth = this.getTextWidth(textContent);
      const normalSize = data.duration >= this.svg.minTime;

      const g = document.createElementNS(this.svg.namespaceURI, 'g');
      g.setAttribute('class', 'rect');

      const rect = document.createElementNS(this.svg.namespaceURI, 'rect');
      rect.setAttribute('x', x1);
      rect.setAttribute('y', startY);
      rect.setAttribute('height', this.svg.cellHeight);
      rect.setAttribute('width', width);
      rect.setAttribute('style', `fill:${color[1]};stroke:${color[0]};`);

      const foreignObject = document.createElementNS(this.svg.namespaceURI, 'foreignObject');
      foreignObject.textContent = textContent;
      foreignObject.setAttribute(
        'x',
        normalSize
          ? x1
          : Math.min(
              this.svg.svgPadding * 2 + this.svg.totalWidth - textWidth - this.svg.textMargin,
              Math.max(this.svg.textMargin, x1 + width / 2 - textWidth / 2)
            )
      );

      foreignObject.setAttribute('y', startY);
      foreignObject.setAttribute('height', this.svg.cellHeight);
      foreignObject.setAttribute('width', width);
      foreignObject.setAttribute('style', `color:${color[0]}`);
      foreignObject.setAttribute('class', `content${normalSize ? '' : ' content-mini'}`);

      const title = document.createElementNS(this.svg.namespaceURI, 'title');
      title.textContent = textContent;

      g.appendChild(rect);
      g.appendChild(foreignObject);
      g.appendChild(title);
      return g;
    },
    /**
     * Create a arrow DOM from the data
     * @param {Object} data Data of single SVG image
     * @param {Number} startY Start y position of arrow
     * @return {Object}
     */
    createArrow(data, startY) {
      const width = (data.duration / this.svg.totalTime) * this.svg.totalWidth;
      const x1 = (data.start / this.svg.totalTime) * this.svg.totalWidth + this.svg.svgPadding;
      const centerY = startY + this.svg.cellHeight / 2;

      const g = document.createElementNS(this.svg.namespaceURI, 'g');
      g.setAttribute('class', 'arrow');

      const line = document.createElementNS(this.svg.namespaceURI, 'line');
      line.setAttribute('y1', centerY);
      line.setAttribute('y2', centerY);
      line.setAttribute('style', 'stroke:#6c7280;stroke-width:1');
      if (width > this.svg.markerPadding) {
        line.setAttribute('x1', x1 + this.svg.markerPadding);
        line.setAttribute('x2', x1 + width - this.svg.markerPadding);
        line.setAttribute('marker-end', 'url(#marker_end)');
        line.setAttribute('marker-start', 'url(#marker_start)');
      } else {
        line.setAttribute('x1', x1);
        line.setAttribute('x2', x1 + width);
      }

      const text = document.createElementNS(this.svg.namespaceURI, 'text');
      text.textContent = `${
        data.duration === this.svg.totalTime ? this.$t('profiling.approximateTime') : ''
      }${this.toFixedFun(data.duration, 4)}ms`;
      const textWidth = text.textContent ? this.getTextWidth(text.textContent) : 0;
      // The position of the text cannot go beyond the border of the SVG
      text.setAttribute(
        'x',
        Math.min(
          this.svg.svgPadding * 2 + this.svg.totalWidth - textWidth - this.svg.textMargin,
          Math.max(this.svg.textMargin, width / 2 + x1 - textWidth / 2)
        )
      );
      text.setAttribute('y', centerY - this.svg.fontSize / 2);
      text.setAttribute('font-size', this.svg.fontSize);
      text.setAttribute('fill', CommonProperty.stepTraceThemes[this.themeIndex].reactFontColor);

      const startLine = document.createElementNS(this.svg.namespaceURI, 'line');
      startLine.setAttribute('x1', x1);
      startLine.setAttribute('y1', startY);
      startLine.setAttribute('x2', x1);
      startLine.setAttribute('y2', startY + this.svg.cellHeight);
      startLine.setAttribute('style', 'stroke:#6c7280;stroke-width:1');
      g.appendChild(startLine);

      const endLine = document.createElementNS(this.svg.namespaceURI, 'line');
      endLine.setAttribute('x1', x1 + width);
      endLine.setAttribute('y1', startY);
      endLine.setAttribute('x2', x1 + width);
      endLine.setAttribute('y2', startY + this.svg.cellHeight);
      endLine.setAttribute('style', 'stroke:#6c7280;stroke-width:1');
      g.appendChild(endLine);
      g.appendChild(line);
      g.appendChild(text);
      return g;
    },
    /**
     * Gets the width of a string
     * @param {String} text
     * @return {Number}
     */
    getTextWidth(text) {
      const body = document.querySelector('body');
      const temp = document.createElement('span');
      temp.style['font-size'] = '12px';
      temp.textContent = text;
      body.appendChild(temp);
      const textWidth = temp.offsetWidth;
      body.removeChild(temp);
      return textWidth;
    },
    /**
     * Remove SVG DOM from page
     */
    removeTrace() {
      const svgDom = document.querySelector('#trace svg');
      if (svgDom) {
        const gDoms = svgDom.children;
        if (gDoms) {
          for (let i = 0; i < gDoms.length; i++) {
            if (gDoms[i].nodeName === 'g') {
              svgDom.removeChild(gDoms[i--]);
            }
          }
        }
      }
    },
    /**
     * Respond to the reset event and update the page display
     */
    resizeTrace() {
      if (this.svg.resizeTimer) {
        clearTimeout(this.svg.resizeTimer);
      }
      this.svg.resizeTimer = setTimeout(() => {
        this.removeTrace();
        this.dealTraceData();
        this.svg.resizeTimer = null;
      }, 500);
    },

    /**
     *  switcher
     */
    coreTableChange(){
      this.onType = this.operatorStatisticType == 0? "gpu_op_type_info" : "gpu_cuda_type_info";
      this.topOperatorValueGPU =[];
      this.initGpuOperatorShape(); // default 3
    },
    initGpuOperatorShape(){
      const params = {}
      params.params={
      };
      params.body= {
        dir:this.relativePath,
        device_id: this.currentCard,
        device_type: "gpu",
        op_type: this.onType,
        filter_condition:
                {
                  op_type: {partial_match_str_in: []},
                  step_filter: ["1"],
                },
      };
      let details = [];//
      let series = [];
      let legend = [];
      let ssChart = [];
      RequestService.queryDynamicShapeGPU(params).then(
              (res) => {
                if (res && res.data) {
                  this.svg.noData = false;
                  this.svg.initOver = true;
                  let data = res.data.dynamic_info;
                  let op_type_arr = data.all_type;
                  let filter_type = data.filter_type;
                  this.isHeterogeneous = res.data.graph_info.is_heterogeneous;
                  let cc = Object.keys(filter_type);
                  op_type_arr.forEach((operatorName) => {
                    let content = null;
                    let sig = false;
                    if(cc.includes(operatorName)){
                      sig = true;
                      content = {
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
                      series.push(item);
                      legend.push(item.name);
                      ssChart.push(operatorName);
                    }else{
                      sig = false;
                      content ={
                        name: operatorName,
                        check: sig,
                        data: [],
                      }
                    }
                    details.push(content);
                  });
                }
                this.checkSig = false;
                this.topOperatorValueGPU = ssChart;  // default 3
                this.operatorOptions.xAxis.data = series[0].data.map((_v, i) => i + 1);
                this.operatorOptions.series = series;
                this.operatorOptions.legend.data = legend;
                this.topOperatorArr = details;
                if(this.isHeterogeneous){
                  this.$nextTick(() => {
                    if(!this.chartObj)
                      this.chartObj = echarts.init(document.getElementById('operatorShapeDetailChart'), echartsThemeName);
                    this.chartObj.setOption(this.operatorOptions, true);
                  });
                }
                this.operatorOptions.tooltip.formatter = (params) => {
                  return this.formatChartTip(params);
                };
                this.operatorOptions.legend.tooltip.formatter = (params) =>{
                  return this.formatLegendTip(params);
                };
                // search
                this.resizeEchart();
              }
      );

    },
    /**
     *
     * init gpu operator shape info by request dynamic shape api
     */
    getGpuOperatorShape(){
      const params = {}
      params.params={
      };
      params.body= {
        dir:this.relativePath,
        device_id: this.currentCard,
        device_type: "gpu",
        op_type: this.onType,
        filter_condition:
                {
                  op_type:{
                    "partial_match_str_in": []
                  },
                  dispaly_op_type: this.topOperatorValueGPU,
                },
      };
      let details = [];//
      let series = [];
      let legend = [];
      RequestService.queryDynamicShapeGPU(params).then(
              (res) => {
                if (res && res.data) {
                  this.svg.noData = false;
                  this.svg.initOver = true;
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
                //
                this.operatorOptions.xAxis.data = series[0].data.map((_v, i) => i + 1);
                this.operatorOptions.series = series;
                this.operatorOptions.legend.data = legend;
                this.topOperatorArr = details;
                if(!this.chartObj)
                  this.chartObj = echarts.init(document.getElementById('operatorShapeDetailChart'), echartsThemeName);
                this.operatorOptions.tooltip.formatter = (params) => {
                  return this.formatChartTip(params);
                };
                this.operatorOptions.legend.tooltip.formatter = (params) =>{
                  return this.formatLegendTip(params);
                };
                // search
                this.$nextTick(() => {
                  this.chartObj.setOption(this.operatorOptions, true);
                  this.drawChart();
                });
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
      let length = this.topOperatorValueGPU.length;
      if (item.check && this.topOperatorValueGPU.indexOf(item.name) == -1) {
        this.topOperatorValueGPU.push(item.name);
      } else if(!item.check){
        this.topOperatorValueGPU.forEach((elm, idx) => {
          if (elm == item.name) {
            this.topOperatorValueGPU.splice(idx, 1)
          }
        })
      }
      if(this.topOperatorValueGPU && this.topOperatorValueGPU.length && length < this.topOperatorValueGPU.length){ // not null
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
     * echart resize
     */
    resizeEchart() {
      if (this.chartObj) {
        setTimeout(() => {
          this.chartObj.resize();
        }, 200);
      }
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
                `<div class="formatter-shape" >
               <span class="formatter-image" style="background-color:${item.color};"></span>
               <span  class="formatter-text">${item.seriesName}&nbsp;:&nbsp;${item.data}</span></div> `
          );
        });
      }
      return tipInnerHTML.join('<br>');
    },
    /**
     * format the formatLegendTip
     * @param {object} params html dom object
     */
    formatLegendTip(params){
      const tipInnerHTML = [];
      tipInnerHTML.push(
              `<div class="formatter-shape" >
             <span  class="formatter-text">${params.name}</span></div> `
      );
      return tipInnerHTML.join('<br>');
    },
    /**
     * Window resize
     */
    resizeCallback() {
      if (this.chartObj) {
        this.chartObj.resize();
      }
    },
  },
  destroyed() {
    window.removeEventListener('resize', this.resizeTrace, false);
    this.$bus.$off('collapse');
  },
};
</script>
<style>
.el-tooltip-popper {
  max-width: 500px;
}

.tooltip-container .pro-dash-tooltip {
  line-height: 20px;
  padding: 10px;
}
.tooltip-container .pro-dash-tooltip .font-style {
  font-weight: bold;
}
.tooltip-container .pro-dash-tooltip .font-size-style {
  font-weight: bold;
  font-size: 16px;
}
.tooltip-container .pro-dash-tooltip .indent {
  padding-left: 30px;
}
.pro-router-wrap {
  height: 100%;
}
.pro-router-wrap > div {
  float: left;
  height: 100%;
}
.pro-router-wrap > div > div {
  border: 1px solid var(--border-color);
  border-radius: 1px;
}
.pro-router-wrap > div .title-wrap {
  padding: 15px;
}
.pro-router-wrap > div .title-wrap .title {
  float: left;
  font-weight: bold;
  font-size: 18px;
  max-width: 300px;
}
.pro-router-wrap > div .title-wrap .tip-icon {
  float: right;
  margin-right: 10px;
  font-size: 20px;
  color: #6c7280;
}
.pro-router-wrap > div .title-wrap .tip-icon .el-icon-warning {
  cursor: pointer;
}
.pro-router-wrap > div .title-wrap .tip-icon .el-icon-warning:hover::before {
  color: var(--theme-color);
}
.pro-router-wrap > div .title-wrap .view-detail {
  float: right;
  cursor: pointer;
  font-size: 12px;
  height: 24px;
  line-height: 24px;
}
.pro-router-wrap > div .title-wrap .view-detail a {
  color: var(--theme-color) !important;
  padding-right: 6px;
}
.pro-router-wrap > div .title-wrap .view-detail button {
  color: var(--theme-color);
  border: none;
  background-color: var(--bg-color);
  cursor: pointer;
}
.pro-router-wrap > div .title-wrap .view-detail button.disabled {
  cursor: not-allowed;
  color: var(--button-disabled-font-color);
}
.pro-router-wrap > div .title-wrap::after {
  content: '';
  clear: both;
  display: block;
}
.pro-router-wrap > div .loading-icon {
  margin-left: 5px;
}
.pro-router-wrap > div .coming-soon-content {
  height: calc(100% - 50px);
  position: relative;
}
.pro-router-wrap > div .coming-soon-content .coming-soon-container {
  text-align: center;
  position: absolute;
  top: 50%;
  left: 50%;
  border-radius: 5px;
  -webkit-transform: translate(-50%, -50%);
  -moz-transform: translate(-50%, -50%);
  transform: translate(-50%, -50%);
}
.pro-router-wrap > div .coming-soon-content .coming-soon-text {
  font-size: 16px;
}
.pro-router-wrap .pro-router-left {
  width: calc(100% - 400px);
  padding-right: 15px;
}
.pro-router-wrap .pro-router-left .step-trace {
  height: calc(100% - 275px);
  margin-bottom: 15px;
}
.pro-router-wrap .pro-router-left .step-trace .trace-container {
  width: 100%;
  height: calc(100% - 54px);
  overflow: auto;
}
.pro-router-wrap .pro-router-left .step-trace .trace-container .training-trace {
  position: relative;
  height: 0;
}
.pro-router-wrap .pro-router-left .step-trace .trace-container .training-trace .content {
  overflow: hidden;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  line-height: 40px;
}
.pro-router-wrap .pro-router-left .step-trace .trace-container .training-trace .content-mini {
  overflow: visible;
}
.pro-router-wrap .pro-router-left .minddata {
  height: 260px;
}
.pro-router-wrap .pro-router-left .minddata .pipeline-container {
  width: 100%;
  padding: 0 20px;
  height: calc(100% - 52px);
  display: flex;
  font-size: 0;
  align-items: baseline;
}
.pro-router-wrap .pro-router-left .minddata .pipeline-container .cell-container {
  width: 20%;
  min-width: 110px;
  padding: 20px 0;
  border: 2px solid transparent;
}
.pro-router-wrap .pro-router-left .minddata .pipeline-container .cell-container .title {
  font-size: 14px;
  line-height: 20px;
  padding: 0 0 0 10px;
  font-weight: bold;
}
.pro-router-wrap .pro-router-left .minddata .pipeline-container .data-process {
  background-color: var(--data-process-color);
}
.pro-router-wrap .pro-router-left .minddata .pipeline-container .data-process .title {
  border-left: 2px solid var(--data-process-title-color);
}
.pro-router-wrap .pro-router-left .minddata .pipeline-container .device_queue_op {
  background-color: var(--device-queue-op-color);
}
.pro-router-wrap .pro-router-left .minddata .pipeline-container .device_queue_op .title {
  border-left: 2px solid var(--device-queue-op-title-color);
}
.pro-router-wrap .pro-router-left .minddata .pipeline-container .get-next {
  background-color: var(--get-next-color);
}
.pro-router-wrap .pro-router-left .minddata .pipeline-container .get-next .title {
  border-left: 2px solid var(--get-next-title-color);
}
.pro-router-wrap .pro-router-left .minddata .pipeline-container .queue-container {
  width: 20%;
  position: relative;
}
.pro-router-wrap .pro-router-left .minddata .pipeline-container .queue-container .img {
  width: 100%;
  height: 24px;
  margin-top: 30px;
}
.pro-router-wrap .pro-router-left .minddata .pipeline-container .queue-container .img .edge {
  width: calc(50% - 40px);
  display: inline-block;
  vertical-align: middle;
}
.pro-router-wrap .pro-router-left .minddata .pipeline-container .queue-container .img .edge img {
  width: 100%;
}
.pro-router-wrap .pro-router-left .minddata .pipeline-container .queue-container .img .icon {
  padding: 0 20px;
  display: inline-block;
  vertical-align: middle;
}
.pro-router-wrap .pro-router-left .minddata .pipeline-container .queue-container .img .icon img {
  padding: 3px;
  border: 2px solid transparent;
}
.pro-router-wrap .pro-router-left .minddata .pipeline-container .queue-container .title {
  text-align: center;
  font-size: 14px;
  margin-top: 10px;
  font-weight: bold;
}
.pro-router-wrap .pro-router-left .minddata .pipeline-container .queue-container .description {
  position: absolute;
  font-size: 12px;
  line-height: 12px;
  white-space: nowrap;
  overflow: visible;
  width: 100%;
  min-width: 100px;
  text-align: center;
  margin-top: 30px;
}
.pro-router-wrap .pro-router-left .minddata .pipeline-container .queue-container .description .item {
  font-size: 12px;
  line-height: 16px;
  white-space: normal;
  overflow: visible;
}
.pro-router-wrap .pro-router-left .minddata .pipeline-container .queue-container .description .item .num {
  white-space: nowrap;
  color: var(--data-process-queue-num-color);
}
.pro-router-wrap .pro-router-right {
  width: 400px;
}
.pro-router-wrap .pro-router-right .op-time-consume {
  height: calc(100% - 275px);
  margin-bottom: 15px;
}
.pro-router-wrap .pro-router-right .op-time-consume .time-list {
  height: calc(40% - 52px);
}
.pro-router-wrap .pro-router-right .op-time-consume .time-list .item {
  height: 25px;
  line-height: 25px;
  padding: 0 20px;
}
.pro-router-wrap .pro-router-right .op-time-consume .time-list .item > span {
  display: inline-block;
  height: 100%;
  vertical-align: middle;
}
.pro-router-wrap .pro-router-right .op-time-consume .time-list .item .index {
  color: white;
  background-color: #6c92fa;
  width: 20px;
  height: 20px;
  border-radius: 20px;
  text-align: center;
  vertical-align: middle;
  line-height: 20px;
}
.pro-router-wrap .pro-router-right .op-time-consume .time-list .item .name {
  margin-left: 10px;
  width: calc(50% - 30px);
  text-overflow: ellipsis;
  overflow: hidden;
}
.pro-router-wrap .pro-router-right .op-time-consume .time-list .item .num {
  width: 20%;
}
.pro-router-wrap .pro-router-right .op-time-consume .time-list .item .time {
  width: 30%;
  position: relative;
}
.pro-router-wrap .pro-router-right .op-time-consume .time-list .item .time span {
  display: inline-block;
  position: absolute;
  left: 0;
  height: 20px;
}
.pro-router-wrap .pro-router-right .op-time-consume .time-list .item .time .bar {
  background-color: var(--operator-bar-bg-color);
  top: 2px;
}
.pro-router-wrap .pro-router-right .op-time-consume .time-list .item .time .value {
  line-height: 25px;
  height: 25px;
}
.pro-router-wrap .pro-router-right .time-line {
  height: 260px;
}
.pro-router-wrap .pro-router-right .time-line .timeline-info {
  width: 100%;
  height: calc(100% - 54px);
  padding-left: 36px;
}
.pro-router-wrap .pro-router-right .time-line .info-line {
  line-height: 30px;
}
.pro-router-wrap .pro-router-right .time-line .info-line .scope-name {
  width: 100px;
}
.pro-router-wrap .op-time-content {
  height: calc(100% - 72px);
  overflow: auto;
}
.pro-router-wrap .pie-chart {
  width: 100%;
  height: 260px;
  overflow: hidden;
}
.pro-router-wrap .image-noData {
  width: 100%;
  height: calc(100% - 52px);
  min-height: 194px;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}
.pro-router-wrap .image-noData p {
  font-size: 16px;
  padding-top: 10px;
}
.pro-router-wrap .pro-router-left .operator-detail{
  width: 100%;
  height: calc(100% - 275px);
  margin-bottom: 15px;
  overflow: auto;
}
.pro-router-wrap .pro-router-left .operator-shape-option{
  line-height: 25px;
  height: 25px;
  margin: 0 auto;
  text-align: center;
}
.pro-router-wrap .pro-router-left .operator-shape-option .operator-filter-title {
  color: #00A5A7;
  margin: 0 10px;
}
.pro-router-left .operator-shape-select .operator-detail-select {
  border-radius: 10%;
  width: 42%;
  line-height: 30px;
  height: 40px;
  margin: 0 auto;
}
#operatorShapeDetailChart{
  width: 100%;
  height: 80%;
  margin: 0 auto;
  min-height: 200px;
  min-width: 120px
}
.define-chart-tip {
  display: inline-block;
  margin-right: 5px;
  width: 10px;
  height: 10px;
}
.operator-shape-detail{
  width: calc(100% - 20px);
  margin: 50px 0;
  height: calc(100% - 130px);
}
.operator-type-select{
  padding-left: 40px;
}
.el-radio-group .el-radio-button--small .el-radio-button__inner {
  height: 30px;
  width: 80px;
  font-size: 14px;
  line-height: 10px;
}
.formatter-shape {
  position: relative;
  display:inline-block;
  padding:0px;
  margin:0px;
}
.formatter-shape .formatter-image{
  display: inline-block;
  position: absolute;
  top: 5px;
  margin-right: 5px;
  width: 10px;
  height: 10px;
 }
.formatter-shape .formatter-text{
  display:inline-block;
  width:100%;
  padding-left: 10px;
  overflow-wrap:break-word;
  white-space: normal;
  word-wrap: break-word;
  font-size:14px;
  font-weight:400;
  margin-left:2px;
}
.el-select-dropdown {
  z-index: 999 !important;
}
</style>

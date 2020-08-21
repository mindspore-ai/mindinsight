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
  <div class="cl-hardware-visual">
    <div class="cl-hardware-content"
         v-if="!(chipTableData.length === 0 && cpuList.length===0)">
      <div class="cl-hardware-top"
           v-if="chipTableData.length">
        <div class="cl-hardware-left">
          <div class="cl-sub-title"
               v-if="chipTableData.length">
            {{$t('hardwareVisual.processor')}}
          </div>
          <div class="cl-chip-wrap">
            <el-table v-if="chipTableData.length"
                      :data="chipTableData"
                      width="100%"
                      height="100%"
                      :row-class-name="tableRowClassName">
              <el-table-column width="120">
                <template slot="header">
                  <span class="cl-text-center">
                    {{ $t('hardwareVisual.name') }}
                    <el-tooltip class="item"
                                effect="light"
                                :content="$t('hardwareVisual.chipNameTip')"
                                placement="top-start">
                      <i class="el-icon-info"></i>
                    </el-tooltip>
                  </span>
                </template>
                <template slot-scope="scope">
                  <span class="cl-text-center">{{ scope.row.chip_name }}</span>
                </template>
              </el-table-column>
              <el-table-column width="80">
                <template slot="header">
                  <span class="cl-text-center">
                    {{ $t('hardwareVisual.npu') }}
                    <el-tooltip class="item"
                                effect="light"
                                :content="$t('hardwareVisual.deviceIdTip')"
                                placement="top-start">
                      <i class="el-icon-info"></i>
                    </el-tooltip>
                  </span>
                </template>
                <template slot-scope="scope">
                  <span class="cl-text-center">{{ scope.row.device_id }}</span>
                </template>
              </el-table-column>
              <el-table-column width="110">
                <template slot="header">
                  <span class="cl-text-center">
                    {{ $t('hardwareVisual.available') }}
                    <el-tooltip class="item"
                                effect="light"
                                :content="$t('hardwareVisual.availableTip')"
                                placement="top-start">
                      <i class="el-icon-info"></i>
                    </el-tooltip>
                  </span>
                </template>
                <template slot-scope="scope">
                  <span class="cl-text-center">
                    <i class="el-icon-success"
                       v-if="scope.row.available"
                       :title="$t('hardwareVisual.availableFree')"></i>
                    <i class="available-fail"
                       :title="$t('hardwareVisual.availableBusy')"
                       v-else></i>
                  </span>
                </template>
              </el-table-column>
              <el-table-column width="100">
                <template slot="header">
                  <span class="cl-text-center">
                    {{ $t('hardwareVisual.health') }}
                    <el-tooltip class="item"
                                effect="light"
                                :content="$t('hardwareVisual.healthTip')"
                                placement="top-start">
                      <i class="el-icon-info"></i>
                    </el-tooltip>
                  </span>
                </template>
                <template slot-scope="scope">
                  <span class="cl-text-center">
                    <i class="el-icon-success"
                       v-if="scope.row.health===0"
                       :title="$t('hardwareVisual.normal')"></i>
                    <i class="el-icon-warning normal"
                       v-if="scope.row.health===1"
                       :title="$t('hardwareVisual.generalWarn')"></i>
                    <i class="el-icon-warning important"
                       v-if="scope.row.health===2"
                       :title="$t('hardwareVisual.importantWarn')"></i>
                    <i class="el-icon-warning emergency"
                       v-if="scope.row.health===3"
                       :title="$t('hardwareVisual.emergencyWarn')"></i>
                    <i class="el-icon-remove"
                       v-if="scope.row.health=== 0xffffffff"
                       :title="$t('hardwareVisual.noChip')"></i>
                  </span>
                </template>
              </el-table-column>
              <el-table-column width="130">
                <template slot="header">
                  <span class="cl-text-center">
                    {{ $t('hardwareVisual.ipAddress') }}
                    <el-tooltip class="item"
                                effect="light"
                                :content="$t('hardwareVisual.ipTip')"
                                placement="top-start">
                      <i class="el-icon-info"></i>
                    </el-tooltip>
                  </span>
                </template>
                <template slot-scope="scope">
                  <span class="cl-text-center">{{ scope.row.ip_address }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="aicore">
                <template slot="header">
                   {{ $t('hardwareVisual.aiCore') }}
                  <el-tooltip class="item"
                              effect="light"
                              :content="$t('hardwareVisual.aicoreTip')"
                              placement="top-start">
                    <i class="el-icon-info"></i>
                  </el-tooltip>
                </template>
                <template slot-scope="scope">
                  <div class="core-wrap">
                    <el-progress :percentage="scope.row.aicore_rate===-1?0:scope.row.aicore_rate"
                                 :format="format(scope.row.aicore_rate)"></el-progress>
                  </div>
                </template>

              </el-table-column>
              <el-table-column prop="hbm_usage"
                               min-width="100">
                <template slot="header">
                  {{ $t('hardwareVisual.hbmUsage') }}
                  <el-tooltip class="item"
                              effect="light"
                              :content="$t('hardwareVisual.hbmTip')"
                              placement="top-start">
                    <i class="el-icon-info"></i>
                  </el-tooltip>
                </template>
                <template slot-scope="scope">
                  <div class="hbs-wrap">
                    <el-progress :percentage="scope.row.hbm_info.memory_size?
                    parseInt(scope.row.hbm_info.memory_usage/scope.row.hbm_info.memory_size*100):0"
                                 :format="formatHbm(scope.row.hbm_info)"></el-progress>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="power">
                <template slot="header">
                  {{ $t('hardwareVisual.power') }}
                  <el-tooltip class="item"
                              effect="light"
                              :content="$t('hardwareVisual.powerTip')"
                              placement="top-start">
                    <i class="el-icon-info"></i>
                  </el-tooltip>
                </template>
                <template slot-scope="scope">
                  <div class="power-wrap">
                    <div class="power"
                         :style="{width:`${scope.row.power/powerMax*100}%`}">{{scope.row.power}}</div>
                  </div>
                </template>

              </el-table-column>
              <el-table-column prop="temp"
                               width="150">
                <template slot="header">
                 {{ $t('hardwareVisual.temp') }}
                  <el-tooltip class="item"
                              effect="light"
                              :content="$t('hardwareVisual.temperatureTip')"
                              placement="top-start">
                    <i class="el-icon-info"></i>
                  </el-tooltip>
                </template>
                <template slot-scope="scope">
                  <div class="temp-wrap">
                    <div class="circle"
                         :class="{zero:!scope.row.temperature}"></div>
                    <div class="process-wrap">
                      <div class="process-cover"
                           :style="{width:temperatureMax?scope.row.temperature/temperatureMax*100+'%':0}"></div>
                    </div>
                    <span>{{scope.row.temperature}}</span>
                  </div>
                </template>
              </el-table-column>
            </el-table>
            <div class="image-noData"
                 v-if="chipTableData.length === 0">
              <div>
                <img :src="require('@/assets/images/nodata.png')"
                     alt="" />
              </div>
              <p>{{$t("hardwareVisual.noNpuInfo")}}</p>
            </div>
          </div>
        </div>
      </div>
      <div class="cl-hardware-bottom"
           :class="{noNpu:!chipTableData.length}">
        <div class="cl-hardware-left">
          <div class="cl-sub-title">
            CPU
          </div>
          <div class="cl-cpu-wrap">
            <div class="cpu-items">
              <div class="cpu-item"
                   v-for="(item,key) in cpuList"
                   :key="key">
                <div class="cpu"
                     :class="{selected:item.selected}"
                     :style="{backgroundColor:item.idle!==undefined?
                     `rgba(250,152,65,${(100-item.idle).toFixed(2)/100}`:'#ccc'}"
                     :title="item.idle!==undefined?`Core ${key}`:''"
                     @click="viewPerCpuInfo(key)">
                  {{ item.idle!==undefined?(100-item.idle).toFixed(2):'' }}
                </div>
              </div>
            </div>
            <div class="cpu-detail">
              <div class="all-cpu-info">
                <span>{{$t('hardwareVisual.allCpu')}}</span>
                <div class="info-item"
                     v-for="(item,index) in overallCpuInfo"
                     :key="index">
                  <el-tooltip class="item"
                              effect="light"
                              :content="item.tips"
                              placement="top-start">
                    <span>
                      <span class="label">{{item.label}}</span>
                      <span class="value">{{`${item.value}%`}}</span>
                    </span>
                  </el-tooltip>
                </div>
              </div>
              <div class="selected-cpu-info"
                   v-if="selectedCpuIndex!==null">
                <span>{{$t('hardwareVisual.selectedCpu')}}</span>
                <div class="info-item"
                     v-for="(item,index) in selectedCpuInfo"
                     :key="index">
                  <el-tooltip class="item"
                              effect="light"
                              :content="item.tips"
                              placement="top-start">
                    <span>
                      <span class="label">{{item.label}}</span>
                      <span class="value">{{`${item.value}%`}}</span>
                    </span>
                  </el-tooltip>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="cl-hardware-right">
          <div class="cl-sub-title ram">
            {{$t('hardwareVisual.ram')}}
          </div>
          <div class="cl-ram-wrap">
            <div class="virtual-wrap">
              <div id="virtual"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="image-noData"
         v-if="chipTableData.length === 0 && cpuList.length===0">
      <div>
        <img :src="require('@/assets/images/nodata.png')"
             alt="" />
      </div>
      <p>{{initOver?$t("public.noData"):$t('public.dataLoading')}}</p>
    </div>
  </div>
</template>

<script>
import echarts from 'echarts';
import RequestService from '../../services/request-service';
export default {
  data() {
    return {
      chipTableData: [],
      powerMax: null,
      temperatureMax: null,
      virtualChart: {
        id: 'virtual',
        chartDom: null,
        data: [],
        legend: [],
        totalValue: null,
      },
      defaultCpuNum: 96,
      cpuList: [],
      overallCpuInfo: [],
      selectedCpuInfo: [],
      selectedCpuIndex: null,
      pieColorArr: ['#5e7ce0', '#ccc', '#a6dd82'],
      autoUpdateTimer: null, // Automatic refresh timer
      isReloading: false, // Manually refresh
      legendSelected: {},
      initOver: false,
      mark: false,
    };
  },
  computed: {
    /**
     * Global refresh switch
     * @return {Boolean}
     */
    isReload() {
      return this.$store.state.isReload;
    },
    /**
     * Automatic hardware refresh switch
     * @return {Boolean}
     */
    isHardwareTimeReload() {
      return this.$store.state.isHardwareTimeReload;
    },
    /**
     * Automatic hardware refresh value
     * @return {Boolean}
     */
    hardwareTimeReloadValue() {
      return this.$store.state.hardwareTimeReloadValue;
    },
  },
  watch: {
    /**
     * Global refresh switch Listener
     * @param {Boolean} newVal Value After Change
     * @param {Boolean} oldVal Value Before Change
     */
    isReload(newVal, oldVal) {
      if (newVal) {
        this.isReloading = true;
        if (this.isHardwareTimeReload) {
          this.autoUpdateSamples();
        }
        this.init();
      }
    },
    /**
     * Automatic refresh switch Listener
     * @param {Boolean} newVal Value After Change
     * @param {Boolean} oldVal Value Before Change
     */
    isHardwareTimeReload(newVal, oldVal) {
      if (newVal) {
        this.autoUpdateSamples();
      } else {
        this.stopUpdateSamples();
      }
    },
    /**
     * The refresh time is changed.
     */
    hardwareTimeReloadValue() {
      this.autoUpdateSamples();
    },
  },
  destroyed() {
    // Disable the automatic refresh function
    if (this.autoUpdateTimer) {
      clearInterval(this.autoUpdateTimer);
      this.autoUpdateTimer = null;
    }
    // Stop Refreshing
    if (this.isReloading) {
      this.$store.commit('setIsReload', false);
      this.isReloading = false;
    }
  },
  mounted() {
    document.title = this.$t('summaryManage.hardwareVisual') + '-MindInsight';
    // Automatic refresh
    if (this.isHardwareTimeReload) {
      this.autoUpdateSamples();
    }
    this.init();
  },

  methods: {
    /**
     * Initialization data
     */
    init() {
      this.mark = false;
      RequestService.getMetricsData().then(
          (res) => {
            this.mark = true;
            this.initOver = true;
            if (this.isReloading) {
              this.$store.commit('setIsReload', false);
              this.isReloading = false;
            }
            if (res && res.data) {
              this.chipTableData = res.data.npu || [];
              if (this.chipTableData.length === 0) {
                this.defaultCpuNum = 192;
              }
              this.powerMax =
              Math.max(...this.chipTableData.map((val) => val.power)) * 1.2;
              this.temperatureMax =
              Math.max(...this.chipTableData.map((val) => val.temperature)) *
              1.2;
              // 1.2 In order to Demonstrated effect
              if (res.data.memory && res.data.memory.virtual) {
                this.dealChartData(this.virtualChart, res.data.memory.virtual);
                this.setOption(this.virtualChart);
              }
              if (res.data.cpu) {
                const overall = res.data.cpu.overall || {};
                this.overallCpuInfo = Object.keys(overall).map((val) => {
                  return {
                    label: val,
                    value: overall[val],
                  };
                });
                this.addtips(this.overallCpuInfo);
                this.cpuList = (res.data.cpu.percpu || []).map((val) => {
                  return {...val, selected: false};
                });
                while (this.cpuList.length < this.defaultCpuNum) {
                  this.cpuList.push({});
                }
                if (this.selectedCpuIndex !== null) {
                  this.viewPerCpuInfo(this.selectedCpuIndex);
                } else {
                  this.selectedCpuInfo = [];
                }
                this.$nextTick(() => {
                  const doms = document.querySelectorAll('.fail-row');
                  if (doms) {
                    for (let i = 0; i < doms.length; i++) {
                      doms[i].setAttribute(
                          'title',
                          this.$t('hardwareVisual.failQueryChip'),
                      );
                    }
                  }
                });
              }
            }
          },
          (err) => {
            this.mark = true;
            this.chipTableData = [];
            this.cpuList = [];
            this.initOver = true;
            if (this.isReloading) {
              this.$store.commit('setIsReload', false);
              this.isReloading = false;
            }
          },
      );
    },
    tableRowClassName({row, rowIndex}) {
      if (!row.success) {
        return 'fail-row';
      }
      return '';
    },
    /**
     * add tips
     * @param {Array} arr cpu Info
     */
    addtips(arr) {
      arr.forEach((val) => {
        switch (val.label) {
          case 'user':
            val.tips = this.$t('hardwareVisual.cpuUserTip');
            break;
          case 'nice':
            val.tips = this.$t('hardwareVisual.cpuNiceTip');
            break;
          case 'system':
            val.tips = this.$t('hardwareVisual.cpuSystemTip');
            break;
          case 'idle':
            val.tips = this.$t('hardwareVisual.cpuIdleTip');
            break;
          case 'iowait':
            val.tips = this.$t('hardwareVisual.cpuIowaitTip');
            break;
          case 'irq':
            val.tips = this.$t('hardwareVisual.cpuIrqTip');
            break;
          case 'softirq':
            val.tips = this.$t('hardwareVisual.cpuSoftirqTip');
            break;
          case 'steal':
            val.tips = this.$t('hardwareVisual.cpuStealTip');
            break;
          case 'guest':
            val.tips = this.$t('hardwareVisual.cpuGuestTip');
            break;
          case 'guest_nice':
            val.tips = this.$t('hardwareVisual.cpuGuestniceTip');
            break;
          case 'interrupt':
            val.tips = this.$t('hardwareVisual.cpuInterruptTip');
            break;
          case 'dpc':
            val.tips = this.$t('hardwareVisual.cpuDpcTip');
            break;
        }
      });
    },
    /**
     * View the information of each cpu
     * @param {Number} index index
     */
    viewPerCpuInfo(index) {
      this.cpuList.forEach((val, key) => {
        if (val.idle !== undefined) {
          if (index === key) {
            this.selectedCpuIndex = key;
            val.selected = !val.selected;
            if (val.selected) {
              this.selectedCpuInfo = Object.keys(this.cpuList[index]).map(
                  (val) => {
                    return {
                      label: val,
                      value: this.cpuList[index][val],
                    };
                  },
              );
              this.selectedCpuInfo.pop();
            } else {
              this.selectedCpuIndex = null;
              this.selectedCpuInfo = [];
            }
          } else {
            if (this.cpuList[index].idle !== undefined) {
              val.selected = false;
            }
          }
        }
      });
      this.addtips(this.selectedCpuInfo);
    },
    /**
     * Handling pie chart data
     * @param {Object} chart chart obejct
     * @param {Object} data chart data
     */
    dealChartData(chart, data) {
      if (data.others === 0) {
        chart.legend = ['used', 'available'];
        this.pieColorArr = ['#5e7ce0', '#a6dd82'];
      } else {
        chart.legend = ['used', 'others', 'available'];
        this.pieColorArr = ['#5e7ce0', '#ccc', '#a6dd82'];
      }
      chart.data = chart.legend.map((val) => {
        return {
          value: data[val],
          name: val,
        };
      });
      chart.totalValue = 0;
      chart.data.forEach((val) => {
        chart.totalValue += val.value;
      });
    },
    /**
     * Data unit conversion
     * @param {Number} n chart obejct
     * @param {Boolean} type format type
     * @return {String}
     */
    bytesHuman(n, type) {
      const symbols = 'KMG'
          .split('')
          .map((symbol, index) => [symbol, 1 << ((index + 1) * 10)]);
      for (const [symbol, prefix] of symbols.reverse()) {
        if (n >= prefix) {
          if (type) {
            return `${n}(${(n / prefix).toFixed(1)}${symbol})`;
          } else {
            return `${(n / prefix).toFixed(1)}${symbol}`;
          }
        }
      }
      return `${n}`;
    },
    format(percentage, item) {
      return () => {
        return percentage === -1
          ? this.$t('hardwareVisual.faliQuery')
          : `${percentage}`;
      };
    },
    formatHbm(hbmInfo) {
      return function() {
        return `${hbmInfo.memory_usage}/${hbmInfo.memory_size}`;
      };
    },
    /**
     * Enable automatic hardware refresh
     */
    autoUpdateSamples() {
      if (this.autoUpdateTimer) {
        clearInterval(this.autoUpdateTimer);
        this.autoUpdateTimer = null;
      }
      this.autoUpdateTimer = setInterval(() => {
        if (this.mark) {
          this.$store.commit('clearToken');
          this.init();
        }
      }, this.hardwareTimeReloadValue * 1000);
    },
    /**
     * Disable automatic refresh
     */
    stopUpdateSamples() {
      if (this.autoUpdateTimer) {
        clearInterval(this.autoUpdateTimer);
        this.autoUpdateTimer = null;
      }
    },
    setOption(chart) {
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: (params) => {
            return `${params.name}<br>
            ${params.marker}${this.bytesHuman(params.value, true)}`;
          },
          confine: true,
        },
        legend: {
          orient: 'vertical',
          left: '50%',
          top: '35%',
          icon: 'circle',
          data: chart.legend,
          formatter: (params) => {
            let legendStr = '';
            for (let i = 0; i < chart.data.length; i++) {
              if (chart.data[i].name === params) {
                const name = chart.data[i].name;
                legendStr = `{a|${this.bytesHuman(
                    chart.data[i].value,
                    true,
                )}}\n{b|${name}}`;
              }
            }
            return legendStr;
          },
          selected: this.legendSelected,
          textStyle: {
            rich: {
              a: {
                fontSize: 14,
              },
              b: {
                color: '#aeb2bf',
              },
            },
          },
        },
        series: [
          {
            name: '',
            center: ['25%', '50%'],
            type: 'pie',
            radius: this.chipTableData.length ? ['40%', '60%'] : ['30%', '40%'],
            avoidLabelOverlap: false,
            label: {
              show: true,
              formatter: () => {
                return `{a|${this.bytesHuman(chart.totalValue)}}{b|All}`;
              },
              position: 'center',
              textStyle: {
                rich: {
                  a: {
                    fontSize: 20,
                    color: '#000',
                  },
                  b: {
                    color: '#aeb2bf',
                  },
                },
              },
            },
            labelLine: {
              show: false,
            },
            data: chart.data,
            itemStyle: {
              normal: {
                color: (params) => {
                  return this.pieColorArr[params.dataIndex];
                },
              },
            },
          },
        ],
      };
      this.$nextTick(() => {
        const cpuDom = document.getElementById(chart.id);
        if (cpuDom) {
          chart.chartDom = echarts.init(cpuDom, null);
          chart.chartDom.setOption(option, true);
          chart.chartDom.resize();
          chart.chartDom.on('legendselectchanged', (obj) => {
            this.legendSelected = obj.selected;
          });
        }
      });
    },
  },
};
</script>
<style lang="scss" >
.cl-hardware-visual {
  height: 100%;
  background-color: #fff;

  .cl-hardware-content {
    height: 100%;
    padding: 0 24px 24px 24px;
    .cl-hardware-top {
      height: calc(100% - 372px);
      padding-top: 16px;
      & > div {
        width: 100%;
        .cl-text-center {
          display: inline-block;
          text-align: center;
          width: 100%;
        }
        .el-table::before {
          height: 0px;
        }
      }
    }
    .cl-hardware-bottom {
      height: 360px;
      .cl-hardware-left {
        width: calc(100% - 466px);
        margin-right: 16px;
      }
      .cl-hardware-right {
        width: 450px;
      }
    }
    & > div {
      height: calc(50% - 8px);
      margin-bottom: 16px;
      & > div {
        float: left;
        height: 100%;
        border: 1px solid #eee;
        border-radius: 4px;
        padding: 16px;
        .cl-sub-title {
          font-weight: bold;
          font-size: 16px;
          margin-bottom: 15px;
        }
        .cl-sub-title.ram {
          margin-bottom: 10px;
        }
        .cl-chip-wrap {
          height: calc(100% - 36px);
          overflow: auto;
          .available-fail {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 12px;
            background-image: url('../../assets/images/occupy.svg');
            background-size: 100% 100%;
          }
          .el-icon-success:before {
            color: #57d7ac;
          }
          .el-icon-error:before {
            color: #e37783;
          }
          .el-icon-warning.normal:before {
            color: #6f81e4;
          }
          .el-icon-warning.important:before {
            color: #faa048;
          }
          .el-icon-warning.emergency:before {
            color: #f06281;
          }
          .el-icon-remove:before {
            color: #8b8e95;
          }
          .temp-wrap {
            .circle {
              width: 10px;
              height: 10px;
              border-radius: 5px;
              background: #ffaa00;
              display: inline-block;
              position: absolute;
              left: 1px;
              top: 50%;
              margin-top: -4px;
            }
            .circle.zero {
              background: #e6ebf5;
            }
            .process-wrap {
              background: #e6ebf5;
              width: calc(100% - 50px);
              height: 6px;
              display: inline-block;
              border-top-right-radius: 50px;
              border-bottom-right-radius: 50px;
              margin-right: 5px;
              .process-cover {
                height: 6px;
                border-top-right-radius: 50px;
                border-bottom-right-radius: 50px;
                background: #ff5100;
                background-image: linear-gradient(to right, #ffaa00, #ff5100);
              }
            }
          }
          .hbs-wrap {
            .el-progress-bar {
              padding-right: 140px;
              margin-right: -145px;
            }
          }
          .core-wrap {
            .el-progress-bar {
              padding-right: 80px;
              margin-right: -85px;
            }
          }
          .power {
            background: #e5f6f6;
            padding-left: 10px;
          }
        }
        .cl-ram-wrap {
          height: calc(100% - 36px);
          .virtual-wrap {
            height: 100%;
            overflow: auto;
            #virtual {
              height: 100%;
              overflow: hidden;
            }
          }
        }
        .cl-disk-wrap {
          height: calc(100% - 36px);
          overflow: auto;
        }
        .cl-cpu-wrap {
          height: 201px;
          .cpu-items {
            height: 100%;
            overflow: auto;
            background: url('../../assets/images/cpu-bg.svg') repeat;
            padding: 3px 0 0 3px;
            .cpu-item {
              float: left;
              width: calc(6.25% - 3px);
              height: 30px;
              text-align: center;
              background: #fff;
              margin-right: 3px;
              margin-bottom: 3px;
              cursor: pointer;
              .cpu {
                height: 100%;
                line-height: 30px;
              }
              .cpu.selected {
                line-height: 30px;
                outline: 3px solid #00a5a7;
              }
            }
          }
          .cpu-detail {
            & > div {
              margin-top: 10px;
              & > span {
                margin-right: 5px;
                color: #b2b4bb;
              }
              & > div {
                display: inline-block;
                padding: 0 7px;
                border-right: 1px solid #ccc;
                &:last-child {
                  border-right: none;
                }
                .label {
                  margin-right: 5px;
                  cursor: pointer;
                }
                .value {
                  display: inline-block;
                  width: 40px;
                  text-align: right;
                  cursor: pointer;
                }
              }
            }
          }
        }
      }
    }
    .cl-hardware-bottom.noNpu {
      padding-top: 16px;
      height: 570px;
      .cl-cpu-wrap {
        height: 399px;
      }
    }
    .el-table thead tr {
      background: #f0f3fa;
    }
    .el-table th.is-leaf .cell {
      border-left: 1px solid #d4d9e6;
    }
    .el-table th.is-leaf:first-child .cell {
      border-left: none;
    }
    .el-pagination {
      margin: 7px 0;
      float: right;
    }
  }
  .el-table th {
    height: 32px;
  }
  .image-noData {
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
    p {
      font-size: 16px;
      padding-top: 10px;
    }
  }
  .el-icon-info:before {
    color: #6c7280;
  }
  .el-table .fail-row {
    opacity: 0.24;
    filter: grayscale(1);
  }
}
</style>

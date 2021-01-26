<!--
Copyright 2019-2021 Huawei Technologies Co., Ltd.All Rights Reserved.

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
  <div class="compareFlex">
    <!-- Operation area -->
    <div class="cl-eval-operate-content">
      <!-- Tag select -->
      <div class="tag-select-content">
        <div class="title mr24">{{$t("scalar.tagSelectTitle")}}</div>
        <!-- Tag search -->
        <el-input class="w261"
                  v-model="tagInput"
                  @input="filterByTagName"
                  v-if="headTagFullScreen"
                  :placeholder="$t('public.tagFilterPlaceHolder')"></el-input>
        <!-- Tag list -->
        <div class="select-item-content"
             v-if="!headTagFullScreen"
             ref="tagSelectItemContent">
          <div v-for="(tagItem, tagIndex) in tagList"
               :key="tagIndex"
               @click="tagItemClick(tagItem)"
               v-show="tagItem.show"
               :class="[tagItem.disabled ? 'checkbox-disabled':'','select-item']">
            <span class="multiCheckBox-border multi-check-border"
                  :class="tagItem.checked ? 'checkbox-checked' : 'checkbox-unchecked'"></span>
            <span class="label-item">
              <el-tooltip effect="dark"
                          :content="tagItem.label"
                          placement="top">
                <span class="select-disable">{{tagItem.label}}</span>
              </el-tooltip>
            </span>
          </div>
        </div>
        <!-- Tag expand/collapse -->
        <div class="run-select-content-open"
             @click="toggleHeadTagFullScreen"
             v-if="tagOverRowFlag || tagInput"
             v-show="!headTagFullScreen">{{$t("scalar.open")}}</div>
        <div class="run-select-content-open"
             @click="toggleHeadTagFullScreen"
             v-if="tagOverRowFlag || headTagFullScreen"
             v-show="headTagFullScreen">{{$t("scalar.close")}}</div>
      </div>
      <div class="run-select-content-all"
           v-if="headTagFullScreen">
        <div v-for="(tagItem, tagIndex) in tagList"
             :key="tagIndex"
             @click="tagItemClick(tagItem)"
             v-show="tagItem.show"
             :class="[tagItem.disabled ? 'checkbox-disabled':'','select-item']">
          <span class="multiCheckBox-border multi-check-border"
                :class="tagItem.checked ? 'checkbox-checked' : 'checkbox-unchecked'"></span>
          <span class="label-item">
            <el-tooltip effect="dark"
                        :content="tagItem.label"
                        placement="top">
              <span class="select-disable">{{tagItem.label}}</span>
            </el-tooltip>
          </span>
        </div>
      </div>
    </div>
    <!-- Slider -->
    <div class="cl-eval-slider-operate-content">
      <div class="xaxis-title">{{$t('scalar.xAxisTitle')}}</div>
      <el-radio-group v-model="curAxisName"
                      fill="#00A5A7"
                      text-color="#FFFFFF"
                      size="small "
                      @change="timeTypeChange">
          <el-radio-button :label="$t('scalar.step')">
            {{$t('scalar.step')}}
          </el-radio-button>
          <el-radio-button :label="$t('scalar.relativeTime')">
            {{$t('scalar.relativeTime') + $t('symbols.leftbracket') + 's' + $t('symbols.rightbracket')}}
          </el-radio-button>
          <el-radio-button :label="$t('scalar.absoluteTime')">
            {{$t('scalar.absoluteTime')}}
          </el-radio-button>
      </el-radio-group>
      <div class="xaxis-title">{{$t('scalar.smoothness')}}</div>
      <el-slider v-model="smoothValue"
                 :step="0.01"
                 :max="0.99"
                 @input="updataInputValue"></el-slider>

                 <el-input v-model="smoothValueNumber"
                   class="w60"
                   @input="smoothValueChange"
                   @blur="smoothValueBlur"
                   ></el-input>
    </div>
    <!-- Content display -->
    <div class="cl-eval-show-data-content"
         ref="miDataShoeContent">
      <!-- No data -->
      <div class="image-noData"
           v-show="initOk && dataList.length === 0">
        <div>
          <img :src="require('@/assets/images/nodata.png')"
               alt="" />
        </div>
        <div class="noData-text">{{$t("public.noData")}}</div>
      </div>
      <!-- Data -->
      <div class="data-contentCompare"
           v-show="dataList.length>0">
        <div class="data-contentCompare-title">{{$t('scalar.comparison')}}</div>
        <div class="data-contentCompare-content">
          <div class="data-contentCompare-tagName">
            <div v-for="(sampleItem,index) in curPageArr"
                 :key="index"
                 :class="['tagNameLeft',index==1? 'tagNameRight':'']">
              {{sampleItem.tagName}}
            </div>
          </div>
          <div class="data-contentCompare-chart"
               id="compareChart"
               ref="mindChart"></div>

        </div>
      </div>
    </div>
  </div>
</template>
<script>
import RequestService from '../../services/request-service';
import CommonProperty from '../../common/common-property';
import echarts from 'echarts';

export default {
  props: {
    tagPropsList: Array, // Prop tagList
    initOver: Boolean, // Prop initOver
    propsList: Array, // Prop list
    compare: Boolean, // Prop isCompare
  },
  data() {
    return {
      trainingJobId: '',
      // Number of predefined colors
      defColorCount: CommonProperty.commonColorArr.length, // Default colors num
      colorNum: 0, // Number of colors
      isActive: 0, // Horizontal axis selected value
      tagList: [], // Tag list
      dataList: [], // DataList
      initOk: false, // IsInit
      tagInput: '', // Tag input value
      tagInputTimer: '', // Tag filtering timing
      charResizeTimer: null, // Delay after the window size is changed
      multiSelectedTagNames: {}, // Selected tag name
      curFilterTagIndexArr: [], // Chart subscript
      curPageArr: [], // Data of the current page
      headTagFullScreen: false, // Indicates whether tag is expanded
      curBenchX: 'stepData', // Front axle reference
      curAxisName: this.$t('scalar.step'), // Current chart tip
      smoothValue: 0, // Initial smoothness of the slider
      smoothValueNumber: 0,
      smoothSliderValueTimer: null, // Smoothness slider timer
      axisBenchChangeTimer: null, // Horizontal axis reference switching timing
      backendString: 'scalarBackend', // Background layer suffix
      charObj: null, // Chart object
      charOption: {}, // Option of chart
      charData: [], // Data of chart
      isCompare: false, // IsCompare
      tagOverRowFlag: false, // The value of tag is greater than one line
      perSelectItemMarginBottom: 1, // Bottom of each selection box
    };
  },
  computed: {},
  watch: {
    initOver(newValue, oldValue) {
      if (newValue) {
        this.initOk = true;
      }
    },
    tagPropsList: {
      handler(newValue, oldValue) {
        if (newValue && newValue.length > 0) {
          this.multiSelectedTagNames = {};
          const tagArr = JSON.parse(JSON.stringify(newValue));
          if (this.tagList.length > 0) {
            tagArr.forEach((propsObj) => {
              propsObj.checked = false;
            });
            tagArr.forEach((propsObj) => {
              this.tagList.forEach((item) => {
                if (propsObj.label === item.label) {
                  propsObj.checked = item.checked;
                  propsObj.show = item.show;
                  if (item.disabled) {
                    propsObj.disabled = true;
                  }
                }
              });
            });

            tagArr.forEach((propsObj) => {
              if (propsObj.checked) {
                this.multiSelectedTagNames[propsObj.label] = true;
              }
            });

            if (Object.keys(this.multiSelectedTagNames).length === 2) {
              tagArr.forEach((item, index) => {
                if (!this.multiSelectedTagNames[item.label]) {
                  item.checked = false;
                  item.disabled = true;
                }
              });
            } else {
              tagArr.forEach((item, index) => {
                if (item.disabled) {
                  delete item.disabled;
                }
              });
            }
          } else {
            tagArr.forEach((item, index) => {
              if (index < 2) {
                this.multiSelectedTagNames[item.label] = true;
              } else {
                item.checked = false;
                item.disabled = true;
              }
            });
          }
          this.tagList = tagArr;
        } else {
          this.tagList = [];
          this.multiSelectedTagNames = {};
        }
      },
      deep: true,
    },
    propsList: {
      handler(newValue, oldValue) {
        if (newValue && newValue.length > 0) {
          this.dataList = JSON.parse(JSON.stringify(newValue));
          if (this.isCompare) {
            this.updateTagInPage();
          }
        } else {
          this.dataList = [];
        }
      },
      deep: true,
    },

    compare(newValue, oldValue) {
      if (newValue) {
        this.isCompare = true;
        this.$nextTick(() => {
          this.resizeCallback();
        });
      } else {
        this.isCompare = false;
      }
    },
  },
  destroyed() {
    this.$bus.$off('updateTag');
  },
  mounted() {
    window.addEventListener('resize', this.resizeCallback, false);

    if (this.$route.query && this.$route.query.train_id) {
      this.trainingJobId = this.$route.query.train_id;
    } else {
      this.trainingJobId = '';
      this.$message.error(this.$t('trainingDashboard.invalidId'));
      return;
    }

    this.$bus.$on('updateTag', (val) => {
      // Update chart by tag
      this.updateTagInPage();
    });
  },
  methods: {
    /**
     *Window resize
     */

    resizeCallback() {
      if (this.isCompare) {
        const tagSelectItemContent = this.$refs.tagSelectItemContent;
        if (tagSelectItemContent) {
          this.tagOverRowFlag =
            tagSelectItemContent.clientHeight <
            tagSelectItemContent.scrollHeight - this.perSelectItemMarginBottom;
        }
        this.charResizeTimer = setTimeout(() => {
          if (this.charObj) {
            this.charObj.resize();
          }
        }, 500);
      }
    },
    /**
     * Tag filtering
     */

    filterByTagName() {
      if (this.tagInputTimer) {
        clearTimeout(this.tagInputTimer);
        this.tagInputTimer = null;
      }
      this.tagInputTimer = setTimeout(() => {
        let reg;
        try {
          reg = new RegExp(this.tagInput);
        } catch (e) {
          this.$message.warning(this.$t('public.regIllegal'));
          return;
        }
        this.tagList.forEach((tagItem) => {
          if (reg.test(tagItem.label)) {
            tagItem.show = true;
            if (tagItem.checked) {
              this.multiSelectedTagNames[tagItem.label] = true;
            }
          } else {
            tagItem.show = false;
          }
        });
        // Update Chart by tag
        this.updateTagInPage();
      }, 500);
    },

    /**
     *
     * Tag click
     * @param {Object} tagItem Current tag
     */
    tagItemClick(tagItem) {
      if (!tagItem) {
        return;
      }
      if (Object.keys(this.multiSelectedTagNames).length === 0) {
        tagItem.checked = true;
        this.multiSelectedTagNames[tagItem.label] = true;
        this.updateTagInPage();
        return;
      }
      if (Object.keys(this.multiSelectedTagNames).length === 1) {
        if (this.multiSelectedTagNames[tagItem.label]) {
          tagItem.checked = false;
          delete this.multiSelectedTagNames[tagItem.label];
          this.updateTagInPage();
        } else {
          tagItem.checked = true;
          this.multiSelectedTagNames[tagItem.label] = true;
          this.tagList.forEach((item, index) => {
            if (!this.multiSelectedTagNames[item.label]) {
              item.checked = false;
              item.disabled = true;
            }
          });
          this.updateTagInPage();
        }
        return;
      }

      if (Object.keys(this.multiSelectedTagNames).length === 2) {
        if (this.multiSelectedTagNames[tagItem.label]) {
          tagItem.checked = false;
          delete this.multiSelectedTagNames[tagItem.label];
          this.tagList.forEach((item, index) => {
            if (item.disabled) {
              delete item.disabled;
            }
          });

          this.updateTagInPage();
        }
        return;
      }
    },

    /**
     * Expand or collapse the run list
     */

    toggleHeadTagFullScreen() {
      this.headTagFullScreen = !this.headTagFullScreen;
      if (!this.headTagFullScreen) {
        this.resizeCallback();
      }
    },

    /**
     * The time display type is changed
     * @param {String} val Radio group value
     */

    timeTypeChange(val) {
      if (this.axisBenchChangeTimer) {
        clearTimeout(this.axisBenchChangeTimer);
        this.axisBenchChangeTimer = null;
      }
      switch (val) {
        case this.$t('scalar.step'):
          this.curBenchX = 'stepData';
          this.curAxisName = this.$t('scalar.step');
          this.isActive = 0;
          break;
        case this.$t('scalar.relativeTime'):
          this.curBenchX = 'relativeData';
          this.curAxisName = this.$t('scalar.relativeTime');
          this.isActive = 1;
          break;
        case this.$t('scalar.absoluteTime'):
          this.curBenchX = 'absData';
          this.curAxisName = this.$t('scalar.absoluteTime');
          this.isActive = 2;
          break;
        default:
          this.curBenchX = 'stepData';
          this.curAxisName = this.$t('scalar.step');
          this.isActive = 0;
          break;
      }
      this.axisBenchChangeTimer = setTimeout(() => {
        if (
          this.charObj &&
          Object.keys(this.multiSelectedTagNames).length > 0
        ) {
          this.charData.forEach((originData, index) => {
            this.charOption.series[index * 2].data = this.formateSmoothData(
                this.charData[index].valueData[this.curBenchX],
            );
            this.charOption.series[index * 2 + 1].data = this.charData[
                index
            ].valueData[this.curBenchX];
          });
          this.charOption.xAxis[0].minInterval = this.isActive === 0 ? 1 : 0;

          this.updateOrCreateChar();
        }
      }, 500);
    },

    /**
     * updata smoothness
     */

    updataInputValue(val) {
      this.smoothValueNumber = Number(val);
      if (this.smoothSliderValueTimer) {
        clearTimeout(this.smoothSliderValueTimer);
        this.smoothSliderValueTimer = null;
      }
      if (Object.keys(this.multiSelectedTagNames).length > 0) {
        this.smoothSliderValueTimer = setTimeout(() => {
          // Change the smoothness
          this.setCharLineSmooth();
        }, 500);
      }
    },

    smoothValueChange(val) {
      if (!isNaN(val)) {
        if (Number(val) === 0) {
          this.smoothValue = 0;
        }
        if (Number(val) < 0) {
          this.smoothValue = 0;
          this.smoothValueNumber = 0;
        }
        if (Number(val) > 0) {
          if (Number(val) > 0.99) {
            this.smoothValue = 0.99;
            this.smoothValueNumber = 0.99;
          } else {
            this.smoothValue = Number(val);
          }
        }
      }
    },

    smoothValueBlur() {
      this.smoothValueNumber = this.smoothValue;
    },

    /**
     * Setting the smoothness
     */

    setCharLineSmooth() {
      // Update the smoothness of initialized data
      if (this.charObj) {
        if (this.charOption.series && this.charOption.series.length > 0) {
          this.charOption.series.forEach((serie, index) => {
            if (index % 2 === 0) {
              serie.data = this.formateSmoothData(
                  this.charData[index / 2].valueData[this.curBenchX],
              );
            }
          });
        }
        this.updateOrCreateChar();
      }
    },

    /**
     * Obtains data on a specified page
     *
     */

    getCurDataArr() {
      const curPageArr = [];
      for (let i = 0; i < this.curFilterTagIndexArr.length; i++) {
        const sampleIndex = this.curFilterTagIndexArr[i];
        if (sampleIndex !== undefined && this.dataList[sampleIndex]) {
          curPageArr.push(this.dataList[sampleIndex]);
        }
      }
      this.curPageArr = curPageArr;
      this.freshCurPageData();
    },

    /**
     * Clear data
     */

    clearAll() {
      if (this.charObj) {
        this.charObj.clear();
      }
      this.colorNum = 0;
      this.charData = [];
      this.charOption = {};
      this.curPageArr = [];
      this.multiSelectedTagNames = {};
    },

    /**
     * Update chart by tag
     */

    updateTagInPage() {
      const curFilterTagIndexArr = [];
      if (this.dataList.length > 0) {
        if (Object.keys(this.multiSelectedTagNames).length > 0) {
          // Obtains the chart subscript
          this.dataList.forEach((sampleObject, sampleIndex) => {
            if (this.multiSelectedTagNames[sampleObject.tagName]) {
              curFilterTagIndexArr.push(sampleIndex);
            }
          });
          this.curFilterTagIndexArr = curFilterTagIndexArr;
          this.getCurDataArr();
        } else {
          this.clearAll();
        }
      } else {
        this.clearAll();
      }
    },

    /**
     * Load the data on the current page
     */

    freshCurPageData() {
      this.charData = [];
      this.colorNum = 0;

      const ajaxArr = [];

      if (this.curPageArr.length > 0) {
        this.curPageArr.forEach((sampleObject, yIndex) => {
          const params = {
            train_id: this.trainingJobId,
            tag: sampleObject.tagName,
          };
          ajaxArr.push(this.addAjax(params, yIndex));
        });

        Promise.all(ajaxArr.map(function(promiseItem) {
          return promiseItem.catch(function(err) {
            return err;
          });
        }))
            .then((res) => {
              if (!res) {
                return;
              }
              this.curPageArr.forEach((sampleObject, yIndex) => {
                sampleObject.colors=
                  CommonProperty.commonColorArr[this.colorNum]
                    ? CommonProperty.commonColorArr[this.colorNum]
                    : CommonProperty.commonColorArr[this.defColorCount - 1];
                this.colorNum++;
              });
              this.colorNum = 0;
              for (let i = 0; i < res.length; i++) {
                if (!res[i] || !res[i].data) {
                  return;
                }

                const resData = res[i].data;
                const tempObject = {
                  valueData: {
                    stepData: [],
                    absData: [],
                    relativeData: [],
                  },
                  yAxisIndex: res[i].yIndex,
                  color: CommonProperty.commonColorArr[this.colorNum]
                  ? CommonProperty.commonColorArr[this.colorNum]
                  : CommonProperty.commonColorArr[this.defColorCount - 1],
                  runName: this.trainingJobId,
                  curBackName: this.trainingJobId + this.backendString,
                  tagName: res[i].params.tag,
                };
                let relativeTimeBench = 0;
                if (resData.metadatas.length) {
                  relativeTimeBench = resData.metadatas[0].wall_time;
                }
                // Initializing chart Data
                resData.metadatas.forEach((metaData) => {
                  tempObject.valueData.stepData.push([
                    metaData.step,
                    metaData.value,
                  ]);
                  tempObject.valueData.absData.push([
                    metaData.wall_time,
                    metaData.value,
                  ]);
                  tempObject.valueData.relativeData.push([
                    metaData.wall_time - relativeTimeBench,
                    metaData.value,
                  ]);
                });
                this.colorNum++;
                this.charData.push(tempObject);
              }

              this.charOption = this.formateCharOption();

              // Draw a chart
              if (this.isCompare) {
                this.updateOrCreateChar();
              }
            })
            .catch((error) => {});
      }
    },


    /**
     * Add request
     * @param {Object} params
     * @param {Number} yIndex
     * @return {Object} Response or error
     */

    addAjax(params, yIndex) {
      return new Promise((resolve, reject) => {
        RequestService.getScalarsSample(params)
            .then((res) => {
              if (res) {
                res.params = params;
                res.yIndex = yIndex;
                resolve(res);
              }
            })
            .catch((error) => {
              if (error) {
                reject(error);
              }
            });
      });
    },

    /**
     * Formatting chart data
     */

    formateCharOption() {
      const _this = this;
      const seriesData = [];
      const yAxis = [];

      this.curPageArr.forEach((sampleObject) => {
        const yAxisData = {
          type: 'value',
          scale: true,
          axisLine: {
            lineStyle: {
              color: '#E6EBF5',
              width: 2,
            },
          },
          axisLabel: {
            color: '#9EA4B3',
            formatter(value) {
              const symbol = Math.abs(value);
              if (symbol.toString().length > 6) {
                return value.toExponential(4);
              } else if (value >= 1000 || value <= -1000) {
                return parseFloat((value / 1000).toFixed(2)) + 'k';
              } else if (value > 0) {
                return value;
              } else {
                return parseFloat(value.toFixed(3));
              }
            },
          },
        };

        yAxis.push(yAxisData);
      });
      this.charData.forEach((tempObj, runNameIndex) => {
        const dataObj = {
          name: tempObj.runName + '@' + tempObj.tagName,
          data: [],
          type: 'line',
          showSymbol: false,
          lineStyle: {
            color: tempObj.color,
          },
          color: tempObj.color,
          yAxisIndex: tempObj.yAxisIndex,
        };
        const dataObjBackend = {
          name: tempObj.runName + '@' + tempObj.tagName + this.backendString,
          data: [],
          type: 'line',
          smooth: 0,
          symbol: 'none',
          lineStyle: {
            color: tempObj.color,
            opacity: 0.2,
          },
          color: tempObj.color,
          yAxisIndex: tempObj.yAxisIndex,
        };
        dataObj.data = this.formateSmoothData(
            tempObj.valueData[this.curBenchX],
        );
        dataObjBackend.data = tempObj.valueData[this.curBenchX];
        seriesData.push(dataObj, dataObjBackend);
      });

      const tempOption = {
        legend: {
          show: false,
        },
        grid: {
          left: 80,
          right: 80,
        },
        xAxis: [
          {
            type: 'value',
            show: true,
            scale: true,
            nameGap: 30,
            minInterval: this.isActive === 0 ? 1 : 0,
            axisLine: {
              lineStyle: {
                color: '#E6EBF5',
                width: 2,
              },
            },
            axisLabel: {
              color: '#9EA4B3',
              interval: 0,
              formatter(value) {
                if (_this.isActive === 2) {
                  const date = new Date(value * 1000);
                  const dateTime = date.toTimeString().split(' ')[0];
                  const dateYear = date.toDateString();
                  return dateTime + '\n' + dateYear;
                } else if (_this.isActive === 1) {
                  if (value < 1 && value.toString().length > 6) {
                    return value.toFixed(3);
                  } else if (value.toString().length > 6) {
                    return value.toExponential(0);
                  } else {
                    return value;
                  }
                } else {
                  const symbol = Math.abs(value);
                  if (symbol.toString().length > 6) {
                    return value.toExponential(0);
                  } else if (value >= 1000 || value <= -1000) {
                    return parseFloat((value / 1000).toFixed(2)) + 'k';
                  } else if (value > 0) {
                    return value;
                  } else {
                    return parseFloat(value.toFixed(3));
                  }
                }
              },
            },
          },
        ],
        yAxis: yAxis,
        animation: true,
        tooltip: {
          trigger: 'axis',
          confine: true,
          axisPointer: {
            type: 'line',
          },
          formatter(params) {
            const unit = 's';
            const strhead =
              '<table class="char-tip-table" class="borderspacing3"><tr><td></td><td>' +
              _this.$t('scalar.charTipHeadName') +
              '</td><td>' +
              _this.$t('scalar.charTipTagName') +
              '</td><td>' +
              _this.$t('scalar.charSmoothedValue') +
              '</td><td>' +
              _this.$t('scalar.charTipHeadValue') +
              '</td><td>' +
              _this.$t('scalar.step') +
              '</td><td>' +
              _this.$t('scalar.relativeTime') +
              '</td><td>' +
              _this.$t('scalar.absoluteTime') +
              '</td></tr>';
            let strBody = '';
            const runArr=[];
            const detialArr=[];
            let curStep=null;
            let dataCount = 0;
            params.forEach((parma) => {
              if (parma.componentIndex % 2 === 0) {
                let addFlag=true;
                const curIndex = parseInt(parma.componentIndex / 2);
                const curSerieOriData=_this.charData[curIndex]
                 ? _this.charData[curIndex].valueData
                 : null;

                if (!curSerieOriData) {
                  return;
                }
                if (curStep===null) {
                  curStep=curSerieOriData.stepData[parma.dataIndex][0];
                } else {
                  if (
                    curSerieOriData.stepData[parma.dataIndex][0]===curStep
                  ) {
                    const sameRunIndex=[];
                    runArr.forEach((runName, index)=>{
                      if (parma.seriesName === runName) {
                        sameRunIndex.push(index);
                      }
                    });
                    if (sameRunIndex.length) {
                      sameRunIndex.forEach((sameIndex) => {
                        if (
                          detialArr[sameIndex] &&
                          detialArr[sameIndex].value ===
                            curSerieOriData.stepData[parma.dataIndex][1] &&
                          detialArr[sameIndex].wallTime ===
                            curSerieOriData.absData[parma.dataIndex][0]
                        ) {
                          addFlag = false;
                        }
                      });
                    }
                  } else {
                    addFlag = false;
                  }
                }

                if (addFlag) {
                  dataCount++;
                  runArr.push(parma.seriesName);
                  detialArr.push({
                    value: curSerieOriData.stepData[parma.dataIndex][1],
                    step: curSerieOriData.stepData[parma.dataIndex][0],
                    wallTime: curSerieOriData.absData[parma.dataIndex][0],
                    dataIndex: parma.dataIndex,
                  });
                  strBody +=
                    `<td style="border-radius:50%;width:15px;height:15px;vertical-align: middle;` +
                    `margin-right: 5px;background-color:` +
                    parma.color +
                    `;display:inline-block;"></td>
                  <td>` +
                    parma.seriesName.split('@')[0] +
                    `</td>
                     <td>` +
                    parma.seriesName.split('@')[1] +
                    `</td>
                  <td>` +
                    _this.formateYaxisValue(parma.value[1]) +
                    `</td>
                  <td>` +
                    _this.formateYaxisValue(
                        curSerieOriData.stepData[parma.dataIndex][1],
                    ) +
                    `</td>
                  <td>` +
                    curSerieOriData.stepData[parma.dataIndex][0] +
                    `</td><td>` +
                    curSerieOriData.relativeData[parma.dataIndex][0].toFixed(
                        3,
                    ) +
                    unit +
                    `</td><td>` +
                    _this.dealrelativeTime(
                        new Date(
                            curSerieOriData.absData[parma.dataIndex][0] * 1000,
                        ).toString(),
                    ) +
                    `</td>
                </tr>`;
                }
              }
            });
            if (dataCount) {
              return strhead + strBody + '</table>';
            }
          },
        },
        series: seriesData,
      };
      return tempOption;
    },

    /**
     * Format smooth data
     * @param {String} oriData
     */

    formateSmoothData(oriData) {
      if (!oriData || oriData.length < 2) {
        return oriData;
      }
      const data = JSON.parse(JSON.stringify(oriData));
      const oriDataLength = oriData.length;
      let last = 0;
      const smoothValue = this.smoothValue;
      let numAccun = 0;
      const firstValue = data[0][1];
      const isAllSame = data.every((curData) => {
        return curData[1] === firstValue;
      });
      for (let i = 0; i < oriDataLength; i++) {
        const curValue = data[i][1];
        if (!isAllSame && Number.isFinite(curValue)) {
          last = last * smoothValue + (1 - smoothValue) * curValue;
          numAccun++;
          let debiasWeight = 1;
          if (smoothValue !== 1) {
            debiasWeight = 1 - Math.pow(smoothValue, numAccun);
          }
          data[i][1] = last / debiasWeight;
        }
      }
      return data;
    },

    /**
     * Updating or creating a specified chart
     * @param {Boolean} resetAnimate Restart the animation
     */

    updateOrCreateChar(resetAnimate) {
      if (this.charObj) {
        if (resetAnimate) {
          this.charOption.animation = false;
        } else {
          this.charOption.animation = true;
        }
        this.charObj.setOption(this.charOption, true);
        return;
      }
      this.charObj = echarts.init(
          document.getElementById('compareChart'),
          null,
      );
      this.charObj.setOption(this.charOption, true);
    },

    /**
     * Format the value of the y axis
     * @param {String} value Number y
     * @return {Number}
     */

    formateYaxisValue(value) {
      if (!value) {
        return value;
      }
      const symbol = Math.abs(value);
      if (symbol.toString().length > 6) {
        return value.toExponential(4);
      } else if (value > 0) {
        return value;
      } else {
        return parseFloat(value.toFixed(3));
      }
    },

    /**
     * Format absolute time
     * @param {String} time String
     * @return String
     */

    dealrelativeTime(time) {
      const arr = time.split(' ');
      const str = arr[0] + ' ' + arr[1] + ' ' + arr[2] + ',' + ' ' + arr[4];
      return str;
    },
  },
  destroyed() {
    // Remove the size of a window and change the listener
    window.removeEventListener('resize', this.resizeCallback);

    // Remove slider value change timing
    if (this.smoothSliderValueTimer) {
      clearTimeout(this.smoothSliderValueTimer);
      this.smoothSliderValueTimer = null;
    }
    // Delete the response delay of removing the tag input box
    if (this.tagInputTimer) {
      clearTimeout(this.tagInputTimer);
      this.tagInputTimer = null;
    }
    // Remove chart calculation delay
    if (this.charResizeTimer) {
      clearTimeout(this.charResizeTimer);
      this.charResizeTimer = null;
    }
  },
  components: {},
};
</script>
<style>
.compareFlex {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.data-contentCompare {
  width: 100%;
  background: #fff;
}

.data-contentCompare-title {
  padding-top: 32px;
  padding-left: 32px;
  font-size: 16px;
  color: #333333;
  font-weight: 600;
}

.data-contentCompare-content {
  padding: 0 32px;
}
.data-contentCompare-content .data-contentCompare-tagName {
  height: 22px;
  font-size: 14px;
  color: #333;
  z-index: 999;
  line-height: 22px;
  display: flex;
  margin-top: 36px;
  font-weight: 600;
}
.data-contentCompare-content .data-contentCompare-tagName .tagNameLeft {
  text-align: left;
  width: 49%;
  overflow: hidden;
  text-overflow: ellipsis;
}
.data-contentCompare-content .data-contentCompare-tagName .tagNameRight {
  text-align: right;
}
.data-contentCompare-content .data-contentCompare-chart {
  height: 570px;
  margin-top: -36px;
}
</style>

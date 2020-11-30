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

<script>
export default {
  data() {
    return {
      thresholdDialogVisible: false,
      delThresholdVisible: false,
      currentTagName: '',
      currentSample: {},
      thresholdErrorMsg: '',
      thresholdRelational: '',
      thresholdValue: [
        {filterCondition: this.$t('scalar.lessThan'), value: ''},
        {filterCondition: this.$t('scalar.lessThan'), value: ''},
      ],
      filterOptions: [
        {
          value: this.$t('scalar.lessThan'),
          label: this.$t('scalar.lessThan'),
        },
        {
          value: this.$t('scalar.greaterThan'),
          label: this.$t('scalar.greaterThan'),
        },
      ],
      thresholdLocal: null,
      thresholdSwitch: false,
      delThresholdSwitch: false,
      thresholdColor: '#f00',
    };
  },
  methods: {
    /**
     * Get localStorge
     */

    getCache() {
      if (localStorage.getItem('thresholdCache')) {
        try {
          this.thresholdLocal = JSON.parse(
              localStorage.getItem('thresholdCache'),
          );
          this.clearCache();
        } catch (e) {
          localStorage.removeItem('thresholdCache');
          this.thresholdLocal = {};
        }
      } else {
        this.thresholdLocal = {};
      }
    },

    /**
     * Clear localStorge
     */

    clearCache() {
      if (
        this.thresholdLocal &&
        this.thresholdLocal[this.decodeTrainingJobId]
      ) {
        if (
          Object.keys(this.thresholdLocal[this.decodeTrainingJobId]).length ===
          0
        ) {
          delete this.thresholdLocal[this.decodeTrainingJobId];
          localStorage.setItem(
              'thresholdCache',
              JSON.stringify(this.thresholdLocal),
          );
        }
      }
    },

    /**
     * Set one point style
     * @param {Object} sampleObject
     */

    setOnePoint(sampleObject) {
      const that = this;
      sampleObject.charObj.on('datazoom', function(params) {
        const xAxisObject = params.batch[0];
        const yAxisObject = params.batch[1];
        const charData = sampleObject.charData.charOption.series[0].data;
        const tempCharOption = sampleObject.charData.charOption;
        // one point
        if (charData.length === 1) {
          sampleObject.onePoint = true;
          tempCharOption.series[0].showSymbol = true;
          sampleObject.charObj.setOption(tempCharOption, false);
          return;
        }
        let filtetArr = [];
        for (let i = 0; i < charData.length; i++) {
          if (
            Math.ceil(charData[i][0] * 10000) / 10000 >=
              xAxisObject.startValue &&
            Math.floor(charData[i][0] * 10000) / 10000 <=
              xAxisObject.endValue &&
            Math.ceil(charData[i][1] * 10000) / 10000 >=
              yAxisObject.startValue &&
            Math.floor(charData[i][1] * 10000) / 10000 <= yAxisObject.endValue
          ) {
            filtetArr.push(charData[i]);
            if (filtetArr.length > 1) {
              filtetArr = [];
              break;
            }
          }
        }
        if (filtetArr.length === 1) {
          sampleObject.onePoint = true;
          tempCharOption.series[0].showSymbol = true;
        } else {
          sampleObject.onePoint = false;
          tempCharOption.series[0].showSymbol = false;
        }

        if (
          tempCharOption.visualMap &&
          tempCharOption.visualMap['pieces'] &&
          tempCharOption.visualMap['pieces'].length > 0
        ) {
          tempCharOption.visualMap = null;
          tempCharOption.series[0].markLine = null;
          that.updateVisualMap(sampleObject);
        } else {
          sampleObject.charObj.setOption(tempCharOption, false);
        }
      });
    },

    /**
     * Set restore
     * @param {Object} sampleObject
     */

    setRestore(sampleObject) {
      const that = this;
      sampleObject.charObj.on('restore', function(params) {
        const charData = sampleObject.charData.charOption.series[0].data;
        const tempCharOption = sampleObject.charData.charOption;

        // One point
        if (charData.length === 1) {
          sampleObject.onePoint = true;
          tempCharOption.series[0].showSymbol = true;
          sampleObject.charObj.setOption(tempCharOption, false);
          return;
        }
        sampleObject.onePoint = false;
        tempCharOption.series[0].showSymbol = false;
        if (
          tempCharOption.visualMap &&
          tempCharOption.visualMap['pieces'] &&
          tempCharOption.visualMap['pieces'].length > 0
        ) {
          tempCharOption.visualMap = null;
          tempCharOption.series[0].markLine = null;
          that.updateVisualMap(sampleObject);
        } else {
          sampleObject.charObj.setOption(tempCharOption, false);
        }
      });
    },

    /**
     * Update visualMap
     * @param {Object} sampleObject
     */

    updateVisualMap(sampleObject) {
      this.getCache();
      if (
        this.thresholdLocal &&
        this.thresholdLocal[this.decodeTrainingJobId] &&
        this.thresholdLocal[this.decodeTrainingJobId][sampleObject.tagName]
      ) {
        const tempStorgeArr = JSON.parse(
            JSON.stringify(
                this.thresholdLocal[this.decodeTrainingJobId][sampleObject.tagName],
            ),
        );
        let pieceStr = '';
        pieceStr = this.formatePieceStr(tempStorgeArr);
        sampleObject.pieceStr = pieceStr;

        tempStorgeArr.forEach((item) => {
          item.color = this.thresholdColor;
        });

        if (sampleObject.charObj) {
          this.setVisualMap(sampleObject, tempStorgeArr);
        }
      } else {
        sampleObject.pieceStr = '';
        sampleObject.charData.charOption.series[0].markLine = null;
      }
    },

    /**
     * Set threshold
     * @param {Object} sampleItem sampleItem
     */

    setThreshold(sampleItem) {
      this.stopUpdateSamples();
      this.getCache();
      if (
        this.thresholdLocal &&
        this.thresholdLocal[this.decodeTrainingJobId] &&
        this.thresholdLocal[this.decodeTrainingJobId][sampleItem.tagName]
      ) {
        delete this.thresholdLocal[this.decodeTrainingJobId][
            sampleItem.tagName
        ];
      }
      this.currentTagName = sampleItem.tagName;
      this.currentSample = sampleItem;
      this.thresholdDialogVisible = true;
    },

    /**
     * Delete threshold
     * @param {Object} sampleItem sampleItem
     */

    delThreshold(sampleItem) {
      this.stopUpdateSamples();
      this.currentTagName = sampleItem.tagName;
      this.currentSample = sampleItem;
      this.delThresholdVisible = true;
    },

    /**
     * Threshold validate
     */

    thresholdValidate() {
      let isValidate = true;

      const valueFirst = this.thresholdValue[0].value;
      const valueSec = this.thresholdValue[1].value;
      const filterConditionFirst = this.thresholdValue[0].filterCondition;
      const filterConditionSec = this.thresholdValue[1].filterCondition;

      if (!this.thresholdRelational) {
        if (!valueFirst) {
          this.thresholdErrorMsg = this.$t('scalar.placeHolderThreshold');
          isValidate = false;
        } else if (valueFirst.indexOf(' ') > -1) {
          this.thresholdErrorMsg = this.$t('scalar.noSpace');
          isValidate = false;
        } else if (isNaN(valueFirst) || valueFirst.indexOf('Infinity') > -1) {
          this.thresholdErrorMsg = this.$t('scalar.placeHolderNumber');
          isValidate = false;
        }
      } else {
        if (filterConditionFirst === filterConditionSec) {
          this.thresholdErrorMsg = this.$t('scalar.sameCompare');
          isValidate = false;
        } else if (!valueFirst || !valueSec) {
          this.thresholdErrorMsg = this.$t('scalar.placeHolderThreshold');
          isValidate = false;
        } else if (valueFirst.indexOf(' ') > -1 || valueSec.indexOf(' ') > -1) {
          this.thresholdErrorMsg = this.$t('scalar.noSpace');
          isValidate = false;
        } else if (valueFirst === valueSec) {
          this.thresholdErrorMsg = this.$t('scalar.unreasonable');
          isValidate = false;
        } else if (isNaN(valueFirst) || isNaN(valueSec)) {
          this.thresholdErrorMsg = this.$t('scalar.placeHolderNumber');
          isValidate = false;
        } else if (
          valueFirst.indexOf('Infinity') > -1 ||
          valueSec.indexOf('Infinity') > -1
        ) {
          this.thresholdErrorMsg = this.$t('scalar.placeHolderNumber');
          isValidate = false;
        } else {
          if (this.thresholdRelational === this.$t('scalar.or')) {
            if (
              filterConditionFirst === this.$t('scalar.greaterThan') &&
              Number(valueFirst) < Number(valueSec)
            ) {
              this.thresholdErrorMsg = this.$t('scalar.unreasonable');
              isValidate = false;
            } else if (
              filterConditionFirst === this.$t('scalar.lessThan') &&
              Number(valueFirst) > Number(valueSec)
            ) {
              this.thresholdErrorMsg = this.$t('scalar.unreasonable');
              isValidate = false;
            }
          }
          if (this.thresholdRelational === this.$t('scalar.and')) {
            if (
              filterConditionFirst === this.$t('scalar.greaterThan') &&
              Number(valueFirst) > Number(valueSec)
            ) {
              this.thresholdErrorMsg = this.$t('scalar.unreasonable');
              isValidate = false;
            } else if (
              filterConditionFirst === this.$t('scalar.lessThan') &&
              Number(valueFirst) < Number(valueSec)
            ) {
              this.thresholdErrorMsg = this.$t('scalar.unreasonable');
              isValidate = false;
            }
          }
        }
      }
      return isValidate;
    },

    /**
     * Set visualMap
     * @param {Object} sampleObject SampleObject
     * @param {Array} chartPieces ChartPieces
     */

    setVisualMap(sampleObject, chartPieces) {
      // Empty array
      if (chartPieces.length === 0) {
        return;
      }
      const markLineData = [];
      chartPieces.forEach((item) => {
        if (!isNaN(item.lt)) {
          const markLineDataItem = {};
          markLineDataItem.yAxis = item.lt;
          markLineData.push(markLineDataItem);
        }
        if (!isNaN(item.gt)) {
          const markLineDataItem = {};
          markLineDataItem.yAxis = item.gt;
          markLineData.push(markLineDataItem);
        }
      });
      const tempCharOption = sampleObject.charData.charOption;

      let chartPiecesTemp = JSON.parse(JSON.stringify(chartPieces));
      chartPiecesTemp.forEach((item) => {
        item.color = this.thresholdColor;
      });

      // One filter condition
      if (chartPiecesTemp.length === 1) {
        if (
          !isNaN(chartPiecesTemp[0]['lt']) &&
          isNaN(chartPiecesTemp[0]['gt'])
        ) {
          if (chartPiecesTemp[0]['lt'] <= sampleObject.zoomData[0]) {
            chartPiecesTemp = [];
          } else if (
            chartPiecesTemp[0]['lt'] < sampleObject.zoomData[1] &&
            chartPiecesTemp[0]['lt'] > sampleObject.zoomData[0]
          ) {
            chartPiecesTemp[0]['gt'] = sampleObject.zoomData[0];
          } else if (chartPiecesTemp[0]['lt'] >= sampleObject.zoomData[1]) {
            chartPiecesTemp[0]['lt'] = sampleObject.zoomData[1];
            chartPiecesTemp[0]['gt'] = sampleObject.zoomData[0];
          }
        } else if (
          !isNaN(chartPiecesTemp[0]['gt']) &&
          isNaN(chartPiecesTemp[0]['lt'])
        ) {
          if (chartPiecesTemp[0]['gt'] >= sampleObject.zoomData[1]) {
            chartPiecesTemp = [];
          } else if (
            chartPiecesTemp[0]['gt'] > sampleObject.zoomData[0] &&
            chartPiecesTemp[0]['gt'] < sampleObject.zoomData[1]
          ) {
            chartPiecesTemp[0]['lt'] = sampleObject.zoomData[1];
          } else if (chartPiecesTemp[0]['gt'] <= sampleObject.zoomData[0]) {
            chartPiecesTemp[0]['lt'] = sampleObject.zoomData[1];
            chartPiecesTemp[0]['gt'] = sampleObject.zoomData[0];
          }
        } else if (
          !isNaN(chartPiecesTemp[0]['lt']) &&
          !isNaN(chartPiecesTemp[0]['gt'])
        ) {
          if (chartPiecesTemp[0]['gt'] >= sampleObject.zoomData[1]) {
            chartPiecesTemp = [];
          } else {
            if (chartPiecesTemp[0]['gt'] <= sampleObject.zoomData[0]) {
              chartPiecesTemp[0]['gt'] = sampleObject.zoomData[0];
            }
            if (chartPiecesTemp[0]['lt'] >= sampleObject.zoomData[1]) {
              chartPiecesTemp[0]['lt'] = sampleObject.zoomData[1];
            }
            if (chartPiecesTemp[0]['lt'] <= sampleObject.zoomData[0]) {
              chartPiecesTemp = [];
            }
          }
        }
      }

      // Two filter condition
      if (chartPiecesTemp.length === 2) {
        const relationalArr = [];
        relationalArr[0] = chartPiecesTemp[0].lt || chartPiecesTemp[1].lt || 0;
        relationalArr[1] = chartPiecesTemp[0].gt || chartPiecesTemp[1].gt || 0;
        if (
          relationalArr[0] >= sampleObject.zoomData[1] ||
          relationalArr[1] <= sampleObject.zoomData[0]
        ) {
          chartPiecesTemp = [
            {
              gt: sampleObject.zoomData[0],
              lt: sampleObject.zoomData[1],
              color: this.thresholdColor,
            },
          ];
        } else {
          if (relationalArr[0] <= sampleObject.zoomData[0]) {
            if (!isNaN(chartPiecesTemp[0].lt)) {
              chartPiecesTemp[0].lt = sampleObject.zoomData[0];
            } else {
              chartPiecesTemp[1].lt = sampleObject.zoomData[0];
            }
          }
          if (relationalArr[1] >= sampleObject.zoomData[1]) {
            if (!isNaN(chartPiecesTemp[0].gt)) {
              chartPiecesTemp[0].gt = sampleObject.zoomData[1];
            } else {
              chartPiecesTemp[1].gt = sampleObject.zoomData[1];
            }
          }
        }
      }
      if (chartPiecesTemp.length > 0) {
        tempCharOption.series[0].lineStyle['color'] = null;
        tempCharOption.visualMap = {};
        tempCharOption.visualMap['show'] = false;
        tempCharOption.visualMap['pieces'] = chartPiecesTemp;
        tempCharOption.visualMap['outOfRange'] = {
          color: sampleObject.colors,
        };
        tempCharOption.series[0]['markLine'] = {
          precision: 5,
          silent: true,
          data: markLineData,
        };

        sampleObject.charObj.setOption(tempCharOption, false);
      } else {
        tempCharOption.series[0].lineStyle['color'] = sampleObject.colors;
        sampleObject.charObj.setOption(tempCharOption, false);
      }
    },

    /**
     * Formate pieceStr
     * @param {Array} piecesArr PiecesArr
     * @return {String}
     */

    formatePieceStr(piecesArr) {
      // Empty array
      if (piecesArr.length === 0) {
        return;
      }
      piecesArr.forEach((item) => {
        if (item.lt) {
          item.lt = Number(item.lt.toFixed(5));
        }
        if (item.gt) {
          item.gt = Number(item.gt.toFixed(5));
        }
      });
      let pieceStr;
      // Only one filter condition
      if (piecesArr.length === 1) {
        if (!isNaN(piecesArr[0].gt) && !isNaN(piecesArr[0].lt)) {
          pieceStr = `(${piecesArr[0].gt},${piecesArr[0].lt})`;
        } else if (!isNaN(piecesArr[0].gt) && isNaN(piecesArr[0].lt)) {
          pieceStr = `(${piecesArr[0].gt},Infinity)`;
        } else if (!isNaN(piecesArr[0].lt) && isNaN(piecesArr[0].gt)) {
          pieceStr = `(-Infinity,${piecesArr[0].lt})`;
        }
      }
      //  Two filter condition
      if (piecesArr.length === 2) {
        if (!isNaN(piecesArr[0].lt) && !isNaN(piecesArr[1].gt)) {
          pieceStr = `(-Infinity,${piecesArr[0].lt}),(${piecesArr[1].gt},Infinity)`;
        } else if (!isNaN(piecesArr[0].gt) && !isNaN(piecesArr[1].lt)) {
          pieceStr = `(-Infinity,${piecesArr[1].lt}),(${piecesArr[0].gt},Infinity)`;
        }
      }
      return pieceStr;
    },

    /**
     * Threshold commit
     */

    thresholdCommit() {
      const isValidate = this.thresholdValidate();

      if (isValidate) {
        const chartPieces = [];
        if (this.thresholdValue[0].value && this.thresholdValue[1].value) {
          if (this.thresholdRelational === this.$t('scalar.or')) {
            this.thresholdValue.forEach((item) => {
              const chartPiecesData = {};
              if (item.filterCondition === this.$t('scalar.greaterThan')) {
                chartPiecesData.gt = Number(item.value);
                chartPieces.push(chartPiecesData);
              } else {
                chartPiecesData.lt = Number(item.value);
                chartPieces.push(chartPiecesData);
              }
            });
          } else {
            const tempArr = [];
            const chartPiecesData = {};
            this.thresholdValue.forEach((item) => {
              tempArr.push(item.value);
            });

            if (Number(tempArr[0]) > Number(tempArr[1])) {
              chartPiecesData.gt = Number(tempArr[1]);
              chartPiecesData.lt = Number(tempArr[0]);
              chartPieces.push(chartPiecesData);
            } else {
              chartPiecesData.gt = Number(tempArr[0]);
              chartPiecesData.lt = Number(tempArr[1]);
              chartPieces.push(chartPiecesData);
            }
          }
        } else {
          this.thresholdValue.forEach((item) => {
            const chartPiecesData = {};
            if (!item.value) {
              return;
            } else if (item.filterCondition === this.$t('scalar.greaterThan')) {
              chartPiecesData.gt = Number(item.value);
              chartPieces.push(chartPiecesData);
            } else if (item.filterCondition === this.$t('scalar.lessThan')) {
              chartPiecesData.lt = Number(item.value);
              chartPieces.push(chartPiecesData);
            }
          });
        }

        let pieceStr = '';
        pieceStr = this.formatePieceStr(chartPieces);

        if (!this.thresholdLocal) {
          this.thresholdLocal = {};
        }
        if (!this.thresholdLocal[this.decodeTrainingJobId]) {
          this.thresholdLocal[this.decodeTrainingJobId] = {};
        }

        const chartPiecesTemp = JSON.parse(JSON.stringify(chartPieces));

        chartPiecesTemp.forEach((item) => {
          item.color = this.thresholdColor;
        });

        if (this.thresholdSwitch) {
          this.originDataArr.forEach((sampleObject) => {
            if (this.multiSelectedTagNames[sampleObject.tagName]) {
              this.thresholdLocal[this.decodeTrainingJobId][
                  sampleObject.tagName
              ] = chartPieces;
              sampleObject.pieceStr = pieceStr;

              if (sampleObject.charObj) {
                this.setVisualMap(sampleObject, chartPieces);
              }
            }
          });
        } else {
          this.thresholdLocal[this.decodeTrainingJobId][
              this.currentTagName
          ] = chartPieces;
          this.currentSample.pieceStr = pieceStr;
          this.setVisualMap(this.currentSample, chartPieces);
        }
        localStorage.setItem(
            'thresholdCache',
            JSON.stringify(this.thresholdLocal),
        );

        this.thresholdDialogVisible = false;
      }
    },

    /**
     * Relational change
     */

    relationalChange(val) {
      if (!val) {
        this.thresholdValue[1].value = '';
        this.thresholdErrorMsg = '';
        this.thresholdValue[1].filterCondition = this.$t('scalar.lessThan');
      }
    },

    /**
     * Threshold cancel
     */

    thresholdCancel() {
      this.thresholdValue[0].value = '';
      this.thresholdValue[1].value = '';
      this.thresholdErrorMsg = '';
      this.currentTagName = '';
      this.currentSample = {};
      this.thresholdSwitch = false;
      this.thresholdRelational = '';
      this.thresholdValue[1].filterCondition = this.$t('scalar.lessThan');
      this.thresholdDialogVisible = false;
      if (this.isTimeReload) {
        this.autoUpdateSamples();
      }
    },

    /**
     * Delete threshold cancel
     */

    delThresholdCancel() {
      this.currentTagName = '';
      this.currentSample = {};
      this.delThresholdSwitch = false;
      this.delThresholdVisible = false;
      if (this.isTimeReload) {
        this.autoUpdateSamples();
      }
    },

    /**
     * Delete threshold commit
     */

    delThresholdCommit() {
      this.getCache();
      if (this.delThresholdSwitch) {
        this.originDataArr.forEach((sampleObject) => {
          if (this.multiSelectedTagNames[sampleObject.tagName]) {
            if (
              this.thresholdLocal &&
              this.thresholdLocal[this.decodeTrainingJobId] &&
              this.thresholdLocal[this.decodeTrainingJobId][
                  sampleObject.tagName
              ]
            ) {
              delete this.thresholdLocal[this.decodeTrainingJobId][
                  sampleObject.tagName
              ];
              sampleObject.pieceStr = '';
              const tempCharOption = sampleObject.charData.charOption;
              if (
                tempCharOption.visualMap &&
                tempCharOption.visualMap['pieces'] &&
                tempCharOption.visualMap['pieces'].length > 0
              ) {
                tempCharOption.visualMap = null;
                tempCharOption.series[0].markLine = null;
                tempCharOption.series[0].lineStyle['color'] =
                  sampleObject.colors;
              }
              if (sampleObject.charObj) {
                sampleObject.charObj.setOption(tempCharOption, false);
              }
            }
          }
        });
      } else {
        if (
          this.thresholdLocal &&
          this.thresholdLocal[this.decodeTrainingJobId] &&
          this.thresholdLocal[this.decodeTrainingJobId][this.currentTagName]
        ) {
          delete this.thresholdLocal[this.decodeTrainingJobId][
              this.currentTagName
          ];
          this.currentSample.pieceStr = '';
          const tempCharOption = this.currentSample.charData.charOption;
          if (
            tempCharOption.visualMap &&
            tempCharOption.visualMap['pieces'] &&
            tempCharOption.visualMap['pieces'].length > 0
          ) {
            tempCharOption.visualMap = null;
            tempCharOption.series[0].markLine = null;
            tempCharOption.series[0].lineStyle[
                'color'
            ] = this.currentSample.colors;
          }
          this.currentSample.charObj.setOption(tempCharOption, false);
        }
      }
      this.clearCache();
      localStorage.setItem(
          'thresholdCache',
          JSON.stringify(this.thresholdLocal),
      );
      this.delThresholdVisible = false;
    },
  },
};
</script>

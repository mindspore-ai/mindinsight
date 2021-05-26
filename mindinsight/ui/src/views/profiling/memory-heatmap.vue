<!--
Copyright 2021 Huawei Technologies Co., Ltd.All Rights Reserved.

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
  <div class="cl-memory-heatmap">
    <div class="cl-cluster-title">
      <div class="cl-cluster-title-left">
        {{$t("profilingCluster.memoryHeatMapTitle")}}
        <el-tooltip placement="right-start"
                    effect="light">
        <div slot="content"
             class="heatmap-tooltip-container">
          <div class="cl-memory-heatmap-tip">
            <div class="tip-title">
              {{$t("profilingCluster.mainTipTitle")}}
            </div>
            <div class="tip-part">
              {{$t("profilingCluster.mainTipPartOne")}}
            </div>
            <div class="tip-part">
              {{$t("profilingCluster.mainTipPartTwo")}}
            </div>
            <div class="tip-part">
              {{$t("profilingCluster.mainTipPartThree")}}
            </div>
            <div class="tip-part">
              {{$t("profilingCluster.mainTipPartFour")}}
            </div>
          </div>
        </div>
        <i class="el-icon-info"></i>
      </el-tooltip>
      </div>
      <div class="path-message">
        <span>{{$t('symbols.leftbracket')}}</span>
        <span>{{$t('trainingDashboard.summaryDirPath')}}</span>
        <span>{{summaryPath}}</span>
        <span>{{$t('symbols.rightbracket')}}</span>
      </div>
    </div>
    <div class="content">
      <div class="legend-content">
        <div class="legend-item"
             v-for="(item, itemIndex) in colorArr"
             :key="itemIndex">
          <div class="color-item">
            <div :style="{background: item.background}"></div>
          </div>
          <div class="value-item">{{`≥${item.range}`}}</div>
        </div>
      </div>
      <p>{{$t('profilingCluster.granuLarity')+$t('symbols.colon')}}</p>
      <el-select v-model="granuLarity"
                 class="select-granuLarity"
                 @change="getColorValue">
        <el-option v-for="(item, index) in granuLarityList"
                   :key="index"
                   :value="item.label"
                   :label="item.label">
        </el-option>
      </el-select>
    </div>
    <div class="heatmap-content">
      <div class="heatmap-item"
           v-for="(item, itemIndex) in memoryHeatmapDataList"
           :key="itemIndex"
           :class="{'mt0': itemIndex < colNum}">
        <div class="detail-content" :class="{'center': item.showCenter}">
          <div class="device-item"
               v-for="(deviceItem, deviceItemIndex) in item.data"
               :key="deviceItemIndex">
            <div class="color-item">
              <el-tooltip placement="top">
                <div slot="content">
                  <div>
                    {{$t('profilingCluster.rankID') + $t('symbols.colon') + deviceItem.rankId}}
                    <br>
                    {{$t('profilingCluster.peakMem') + $t('symbols.colon') + deviceItem.peakMem.toFixed(3)
                     + $t('unit.KiB')}}
                    <br>
                    {{$t('profilingCluster.capaCity') + $t('symbols.colon') + deviceItem.capacity
                     + $t('unit.GiB')}}
                  </div>
                </div>
                <div :style="{background:deviceItem.background}"
                     @click="jumpToMemory(deviceItem, item.hostIp)"></div>
              </el-tooltip>
            </div>
            <div class="info-item">
              {{$t('profilingCluster.deviceId') + deviceItem.deviceId}}
            </div>
          </div>
        </div>
        <div class="info-content">
          {{$t('profilingCluster.host') + item.hostIp}}
        </div>
      </div>
    </div>
    <!-- outer Page -->
    <div class="pagination-content">
    </div>
    <img src="@/assets/images/close-page.png"
         class="cl-cluster-close"
         @click="backToDashboard">
  </div>
</template>
<script>
import RequestService from '../../services/request-service';
import Color from '../../common/common-property';
export default {
  props: {},
  data() {
    return {
      summaryPath: decodeURIComponent(this.$route.query.path),
      trainingJobId: this.$route.query.id, // ID of the current training job
      summaryDir: this.$route.query.dir,
      memoryHeatmapInitOver: false, // init Heat map
      memoryHeatmapDataList: [], // Heat map data
      colNum: 4, // column number
      granuLarityList: [], // Array of granularity
      granuLarity: '0.1', // granuLarity value
      colorArr: [], // Array of color index
    };
  },
  watch: {},
  computed: {},
  created() {
    this.granuLarityList = [
      {label: '0.1', value: '0.1'},
      {label: '0.05', value: '0.05'},
      {label: '0.02', value: '0.02'},
    ];
    this.getColorValue();
  },
  mounted() {
    if (this.trainingJobId) {
      document.title = `${this.summaryPath}-${this.$t('profilingCluster.memoryHeatMapTitle')}-MindInsight`;
      this.getHeatMapData();
    } else {
      document.title = `${this.$t('profilingCluster.memoryHeatMapTitle')}-MindInsight`;
      this.trainingJobId = '';
      this.memoryHeatmapInitOver = true;
      this.$message.error(this.$t('trainingDashboard.invalidId'));
    }
  },
  methods: {
    /**
     * Get the color value
     */
    getColorValue() {
      this.colorArr = [];
      this.index = 0;
      const colorDepth = Color.clusterHeatmapColorArr;
      const colorLength = 1 / this.granuLarity / (colorDepth.length - 1);
      // 1: Used to calculate decimal places length
      const fixedLength = this.granuLarity.length - (this.granuLarity.indexOf('.') + 1);
      for (let i = 0; i < colorDepth.length - 1; i++) {
        for (let j = 0; j < colorLength; j++) {
          this.colorArr.push({
            background: this.getGrientColor(colorDepth[i], colorDepth[i + 1], colorLength)[j],
            range: (this.index * this.granuLarity).toFixed(fixedLength),
          });
          this.index++;
        }
      }
      if (this.memoryHeatmapDataList.length) {
        this.changeBackground();
      }
    },
    /**
     * Obtain heat map data
     */
    getHeatMapData() {
      const params = {
        train_id: this.trainingJobId,
      };
      RequestService.getClusterPeakMemory(params)
          .then((res) => {
            if (!res || !res.data) {
              this.memoryHeatmapInitOver = true;
              return;
            }
            const resData = res.data;
            const heatmapDataMap = {};
            const heatmapDataArr = [];
            // Merge host ip
            resData.forEach((data) => {
              let arrayIndex;
              if (heatmapDataMap[data.host_ip] === undefined) {
                // New host_ip
                arrayIndex = heatmapDataArr.push({
                  hostIp: data.host_ip,
                  data: [],
                  showCenter: true,
                }) - 1;
                heatmapDataMap[data.host_ip] = arrayIndex;
              } else {
                // Exist host_ip
                arrayIndex = heatmapDataMap[data.host_ip];
              }
              const deviceId = data.device_id;
              const factorFromGiBToKiB = 1024 * 1024; // 1024: Transform GiB to KiB
              const capacityInKiB = data.capacity * factorFromGiBToKiB;
              heatmapDataArr[arrayIndex].data[deviceId] = {
                deviceId,
                rankId: data.rank_id,
                peakMem: data.peak_mem,
                capacity: data.capacity,
                peakRatio: data.peak_mem / capacityInKiB,
                background: '',
              };
            });
            heatmapDataArr.forEach((data) => {
              // Avoid device_id incoherent
              data.data = data.data.filter((item) => {
                return item !== undefined;
              });
              if (data.data.length > this.colNum) {
                data.showCenter = false;
              }
            });
            this.memoryHeatmapDataList = heatmapDataArr;
            this.changeBackground();
          })
          .catch(() => {
            this.memoryHeatmapInitOver = true;
          });
    },
    /**
     * Calculate gradient color
     * @param {String} startColor
     * @param {String} endColor
     * @param {Number} step
     * @return {Array} Array of gradient color
     */
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
    /**
     * Converts a color string to recognizable format
     * @param {String} str Color string
     * @return {Array} Value of RGB
     */
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
            colorStrNew += colorStrNew.slice(i, i + 1).concat(colorStrNew.slice(i, i + 1));
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
    /**
     * Converts rgb color string to hex
     * @param {String} rgb Rgb color
     * @return {String} Hex color
     */
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
    /**
     * page turn memory
     * @param {Object} item Jump parameters
     * @param {String} hostIP host ip
     */
    jumpToMemory(item, hostIP) {
      this.$router.push({
        path: '/profiling/memory-detail',
        query: {
          dir: 'profiler',
          id: `${this.trainingJobId}/cluster_profiler/${hostIP}`,
          path: `${this.summaryPath}/cluster_profiler/${hostIP}`,
          cardNum: item.deviceId,
          deviceid: item.deviceId,
          activeName: this.$route.query.activeName,
        },
      });
    },
    /**
     * Change Color
     */
    changeBackground() {
      // Factor used to avoid JS floating point number question
      const factor = 1000000;
      const maxPeakRatio = 1;
      this.memoryHeatmapDataList.forEach((data) => {
        data.data.forEach((item) => {
          if (item.peakRatio !== maxPeakRatio) {
            const colorIndex = Math.floor((item.peakRatio * factor) / (+this.granuLarity * factor));
            item.background = this.colorArr[colorIndex].background;
          } else {
            item.background = this.colorArr[this.colorArr.length - 1].background;
          }
        });
      });
    },
    /**
     * Back to cluster dashboard
     */
    backToDashboard() {
      this.$router.push({
        path: '/cluster-dashboard',
        query: {
          dir: this.summaryDir,
          id: this.trainingJobId,
          path: this.summaryPath,
          activeName: this.$route.query.activeName,
        },
      });
    },
  },
};
</script>
<style scoped>
.cl-memory-heatmap {
  height: 100%;
  width: 100%;
  padding: 0 32px 24px 32px;
  background: #fff;
}
.cl-memory-heatmap .cl-cluster-title {
  height: 56px;
  line-height: 56px;
  position: relative;
  flex-shrink: 0;
}
.cl-memory-heatmap .el-icon-info {
  color: #6c7280;
}
.el-tooltip__popper .heatmap-tooltip-container .cl-memory-heatmap-tip {
  padding: 10px;
}
.el-tooltip__popper .heatmap-tooltip-container .cl-memory-heatmap-tip .tip-title {
  font-size: 16px;
  font-weight: bold;
  padding: 0px 0px 3px 0px;
}
.el-tooltip__popper .heatmap-tooltip-container .tag-tip .tip-title {
  color: #333333;
}
.el-tooltip__popper .heatmap-tooltip-container .cl-memory-heatmap-tip .tip-part {
  line-height: 20px;
  word-break: normal;
}
.cl-memory-heatmap .cl-cluster-title .cl-cluster-title-left {
  display: inline-block;
  font-size: 20px;
  font-weight: bold;
  left: 0;
}
.cl-memory-heatmap .cl-cluster-title .path-message {
  display: inline-block;
  line-height: 20px;
  padding: 18px 0;
  font-weight: bold;
  margin-left: 5px;
}
.cl-memory-heatmap .cl-cluster-close {
  object-fit: none;
  position: absolute;
  cursor: pointer;
  top: 82px;
  right: 24px;
}
.cl-memory-heatmap .content {
  position: absolute;
  display: flex;
  margin-top: -5px;
  width: 150px;
  right: 35px;
  line-height: 56px;
}
.cl-memory-heatmap .content p {
  line-height: 56px;
}
.cl-memory-heatmap .content .select-granuLarity {
  width: 104px;
}
.cl-memory-heatmap .content {
  position: relative;
  margin-left: 30px;
  width: 100%;
  margin-top: 3px;
  border-bottom: solid 1px #e6ebf5;
  padding: 8px 0px;
}
.cl-memory-heatmap .content .legend-content {
  position: relative;
  margin-top: 3px;
  width: calc(100% - 150px);
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-start;
}
.content .legend-content .legend-item {
  width: 26px;
  height: 56px;
  padding: 5px 0;
  margin-left: 12px;
}
.content .legend-content .legend-item .color-item {
  width: 100%;
  margin-left: 3px;
  padding: 0 1px;
  height: calc(100% - 20px);
}
.content .legend-content .legend-item .color-item div {
  position: relative;
  margin-top: 5px;
  width: 100%;
  height: 100%;
  border: solid 1px #e6ebf5;
}
.content .legend-content .legend-item .value-item {
  margin-top: -21px;
}
.cl-memory-heatmap .heatmap-content {
  height: calc(100% - 132px);
  overflow-y: auto;
  display: flex;
  flex-wrap: wrap;
  margin-top: 20px;
}
.cl-memory-heatmap .heatmap-content .heatmap-item {
  width: 25%;
  height: 260px;
  padding: 0 10px;
  margin-top: 20px;
  flex-shrink: 0;
}
.cl-memory-heatmap .heatmap-content .heatmap-item.mt0 {
  margin-top: 0;
}
.cl-memory-heatmap .heatmap-content .heatmap-item .detail-content {
  height: calc(100% - 28px);
  background: #e6ebf5;
  display: flex;
  flex-wrap: wrap;
  overflow-y: auto;
  padding-bottom: 10px;
  border-radius: 6px;
}
.cl-memory-heatmap .heatmap-content .heatmap-item .detail-content.center {
  justify-content: center;
  align-items: center;
}
.heatmap-content .heatmap-item .detail-content .device-item {
  flex-shrink: 0;
  width: 25%;
  height: 50%;
  padding: 5px;
}
.heatmap-item .detail-content .device-item .color-item {
  width: 100%;
  height: calc(100% - 23px);
  padding: 0 10px;
  display: block;
  position: relative;
}
.heatmap-item .detail-content .device-item .color-item div {
  max-height: 100%;
  height: 50px;
  width: 24px;
  bottom: 0;
  left: 50%;
  margin-left: -12px;
  position: absolute;
  cursor: pointer;
}
.heatmap-item .detail-content .device-item .info-item {
  margin-top: 4px;
  text-align: center;
}
.cl-memory-heatmap .heatmap-content .heatmap-item .info-content {
  margin-top: 10px;
  font-size: 16px;
  color: #333;
  font-weight: 600;
  text-align: center;
}
</style>

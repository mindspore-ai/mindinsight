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
    <div class="profiling-content-title">
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
    <div class="content">
      <div class="legend-content">
        <div class="legend-item"
             v-for="(item, itemIndex) in colorArr"
             :key="itemIndex">
          <div class="color-item"
               :style="{background: item.background}">
          </div>
          <span class="text-item">≥{{item.range}}</span>
        </div>
      </div>
      <div>
        <span>{{$t('profilingCluster.granuLarity')}} </span>
        <el-select v-model="granuLarity"
                   class="select-granuLarity"
                   @change="getColorValue">
          <el-option v-for="(item, index) in granuLarityList"
                     :key="index"
                     :value="item.value"
                     :label="item.label">
          </el-option>
        </el-select>
      </div>
    </div>
    <div class="heatmap-content">
      <div class="heatmap-item"
           v-for="deviceItem in memoryHeatmapDataList"
           :key="deviceItem.rankID">
        <el-tooltip placement="top">
          <div slot="content">
            <div>
              {{$t('profilingCluster.peakMem') + $t('symbols.colon') + deviceItem.peakMem
                + $t('unit.GiB')}}
              <br>
              {{$t('profilingCluster.capaCity') + $t('symbols.colon') + deviceItem.capacity
                + $t('unit.GiB')}}
              <br>
              {{$t('profilingCluster.maximumPeakRatio') + $t('symbols.colon') + deviceItem.peakRatio}}
            </div>
          </div>
          <div class="color-item"
               :style="{background: deviceItem.background}"
               @click="jumpToMemory(deviceItem.rankID)"></div>
        </el-tooltip>
        {{$t('profilingCluster.rankID') + deviceItem.rankID}}
      </div>
    </div>
  </div>
</template>
<script>
import RequestService from '@/services/request-service';
import Color from '@/common/common-property';
import { getGradientColor } from '@/js/utils';
export default {
  props: {},
  data() {
    return {
      trainInfo: {
        id: this.$route.query.id,
        path: this.$route.query.path,
        dir: this.$route.query.dir,
      },
      memoryHeatmapInitOver: false, // init Heat map
      memoryHeatmapDataList: [], // Heat map data
      granuLarityList: [], // Array of granularity
      granuLarity: '0.1', // GranuLarity value
      colorArr: [], // Array of color index
    };
  },
  created() {
    this.granuLarityList = [
      { label: '0.1', value: '0.1' },
      { label: '0.05', value: '0.05' },
      { label: '0.02', value: '0.02' },
    ];
    this.getColorValue();
  },
  mounted() {
    const id = this.trainInfo.id;
    if (id) {
      document.title = `${id}-${this.$t('profilingCluster.memoryHeatMapTitle')}-MindInsight`;
      this.getHeatMapData();
    } else {
      document.title = `${this.$t('profilingCluster.memoryHeatMapTitle')}-MindInsight`;
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
            background: getGradientColor(colorDepth[i], colorDepth[i + 1], colorLength)[j],
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
        train_id: this.trainInfo.id,
      };
      RequestService.getClusterPeakMemory(params)
        .then((res) => {
          if (!res.data) {
            this.memoryHeatmapInitOver = true;
            return;
          }
          const heatmapDataset = [];
          res.data.forEach((data) => {
            const { capacity } = data;
            heatmapDataset.push({
              rankID: data.rank_id,
              peakMem: Number(Math.floor(data.peak_mem * 1000) / 1000),
              capacity,
              peakRatio: Number(Math.floor((data.peak_mem / capacity) * 1000) / 1000),
              background: '',
            });
          });
          this.memoryHeatmapDataList = heatmapDataset.sort((a, b) => a.rankID - b.rankID);
          this.changeBackground();
        })
        .catch(() => {
          this.memoryHeatmapInitOver = true;
        });
    },
    /**
     * Page turn memory
     * @param {Object} rankID Jump parameters
     */
    jumpToMemory(rankID) {
      this.$router.push({
        path: '/profiling/single/memory-utilization',
        query: Object.assign(this.trainInfo, { rankID }),
      });
    },
    /**
     * Change Color
     */
    changeBackground() {
      const maxPeakRatio = 1;
      this.memoryHeatmapDataList.forEach((item) => {
        if (item.peakRatio !== maxPeakRatio) {
          const colorIndex = Math.floor(item.peakRatio / +this.granuLarity);
          item.background = this.colorArr[colorIndex].background;
        } else {
          item.background = this.colorArr[this.colorArr.length - 1].background;
        }
      });
    },
  },
};
</script>
<style scoped>
.cl-memory-heatmap {
  height: 100%;
  width: 100%;
  background: var(--bg-color);
  display: flex;
  flex-direction: column;
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
.cl-memory-heatmap .content {
  display: grid;
  grid-template-columns: 1fr auto;
  width: 100%;
  border-bottom: solid 1px var(--border-color);
  padding: 8px 0px;
}
.cl-memory-heatmap .content .select-granuLarity {
  width: 100px;
}
.cl-memory-heatmap .content .legend-content {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding-left: 4px;
}
.content .legend-content .legend-item {
  position: relative;
  height: 36px;
}
.content .legend-content .legend-item .color-item {
  width: 24px;
  height: 24px;
  border: solid 1px #e6ebf5;
}
.content .legend-content .legend-item .text-item {
  top: 24px;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}
.cl-memory-heatmap .heatmap-content {
  flex-grow: 1;
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  overflow-y: auto;
}
.heatmap-content .heatmap-item {
  height: 200px;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  gap: 10px;
}
.heatmap-content .heatmap-item .color-item {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  cursor: pointer;
}
</style>

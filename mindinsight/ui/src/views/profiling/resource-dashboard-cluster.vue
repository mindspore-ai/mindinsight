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
  <div class="cl-memory-heatmap-dasnhoard">
    <div class="dashboard-item">
      <div class="title-item">
        <div class="title-text">
          {{$t('profilingCluster.memoryHeatMapTitle')}}
        </div>
        <div class="detail-link"
             :class="{disabled:!memoryHeatmapInitOver || !memoryHeatmapDataList.length}">
          <button :disabled="!memoryHeatmapInitOver || !memoryHeatmapDataList.length"
                  @click="jumpToMemoryHeatmap">
            {{$t('profiling.viewDetail')}}
            <i class="el-icon-d-arrow-right"></i>
          </button>
        </div>
      </div>
      <div class="content-item">
        <div class="noData-content"
             v-show="!memoryHeatmapInitOver || !memoryHeatmapDataList.length">
          <div>
            <img :src="require('@/assets/images/nodata.png')" />
          </div>
          <div v-if="memoryHeatmapInitOver && !memoryHeatmapDataList.length"
               class="noData-text">{{$t("public.noData")}}</div>
          <div v-else
               class="noData-text">{{$t("public.dataLoading")}}</div>
        </div>
        <div class="dashboard-chart-content"
             v-show="memoryHeatmapDataList.length && memoryHeatmapInitOver">
          <div class="legend-content">
            <div class="legend-item"
                 v-for="(item, itemIndex) in legendArr"
                 :key="itemIndex">
              <div class="color-item">
                <div :style="{backgroundColor: item.backgroundColor}"></div>
              </div>
              <div class="value-item">{{item.info}}</div>
            </div>
          </div>
          <div class="heatmap-content">
            <div class="heatmap-item"
                 v-for="(item, itemIndex) in memoryHeatmapDataList"
                 :key="itemIndex"
                 :class="{'mt0': itemIndex < colNum}">
              <div class="detail-content">
                <div class="device-item"
                     v-for="(deviceItem, deviceItemIndex) in item.data"
                     :key="deviceItemIndex">
                  <div class="color-item">
                    <el-tooltip placement="top">
                      <div slot="content">
                        <div>
                          {{$t('profilingCluster.rankID') + $t('symbols.colon') + deviceItem.rankId}}
                        </div>
                      </div>
                      <div :style="{backgroundColor: deviceItem.backgroundColor}"></div>
                    </el-tooltip>
                  </div>
                  <div class="info-item">
                    {{$t('profilingCluster.deviceId') + deviceItem.deviceId}}
                  </div>
                </div>
              </div>
              <div class="info-content">
                {{item.hostIp}}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import RequestService from '../../services/request-service';
import Color from '../../common/common-property';
export default {
  props: {
    activeName: {
      type: String,
      default: '',
    },
  },
  data() {
    return {
      summaryPath: this.$route.query.path, // Path of the current training job
      trainingJobId: this.$route.query.id, // ID of the current training job
      summaryDir: this.$route.query.dir, // Dir of the current training job
      memoryHeatmapInitOver: false, // The page state
      memoryHeatmapDataList: [], // The heatmap daata
      legendArr: [], // Legend
      legendArrLength: 10, // Length of legend
      colNum: 4, // Column num of heatmap
      granularity: 0.1, // Granularity
    };
  },
  mounted() {
    this.initLegendArr();
    this.getHeatMapData();
  },
  methods: {
    /**
     * The logic of jump to heatmap page
     */
    jumpToMemoryHeatmap() {
      this.$router.push({
        path: '/memory-heatmap',
        query: {
          dir: this.summaryDir,
          id: this.trainingJobId,
          path: this.summaryPath,
          activeName: this.activeName,
        },
      });
    },
    /**
     * The logic of init heatmap legend
     */
    initLegendArr() {
      const tempArr = [];
      const colorArr = Color.clusterHeatmapDashboardColorArr;
      for (let i = 0; i < colorArr.length; i++) {
        tempArr.push({
          backgroundColor: colorArr[i],
          info: `≥0.${i}`,
        });
      }
      this.legendArr = tempArr;
    },
    /**
     * The logic of get heatmap data
     */
    getHeatMapData() {
      const params = {
        train_id: this.trainingJobId,
      };
      RequestService.getClusterPeakMemory(params).then((res) => {
        if (!res || !res.data) {
          this.memoryHeatmapInitOver = true;
          return;
        }
        const resData = res.data;
        const heatmapDataDic = {};
        const HeatmapDataArr = [];
        resData.forEach((heatmap) => {
          let dataIndex = heatmapDataDic[heatmap.host_ip];
          if (isNaN(dataIndex)) {
            dataIndex = HeatmapDataArr.length;
            heatmapDataDic[heatmap.host_ip] = dataIndex;
            HeatmapDataArr.push({
              hostIp: heatmap.host_ip,
              data: [],
            });
          }
          // Factor used to avoid JS floating point number question
          const factor = 100;
          const index = Math.floor(((heatmap.peak_mem / heatmap.capacity) * factor) / (this.granularity * factor));
          HeatmapDataArr[dataIndex].data.push({
            deviceId: heatmap.device_id,
            rankId: heatmap.rank_id,
            peakMem: heatmap.peak_mem,
            capacity: heatmap.capacity,
            backgroundColor: this.legendArr[index].backgroundColor,
          });
        });
        this.memoryHeatmapDataList = this.sortByDeviceId(HeatmapDataArr);
        this.memoryHeatmapInitOver = true;
      });
    },
    /**
     * The logic of sort data by device ID
     * @param {Array} oriData
     * @return {Array}
     */
    sortByDeviceId(oriData) {
      if (!oriData) {
        return [];
      }
      oriData.forEach((hostData) => {
        hostData.data.sort((a, b) => {
          return a.deviceId - b.deviceId;
        });
      });
      return oriData;
    },
  },
};
</script>
<style scoped>
.cl-memory-heatmap-dasnhoard {
  height: 100%;
  width: 100%;
}
.cl-memory-heatmap-dasnhoard .dashboard-item {
  width: 100%;
  height: 100%;
  padding: 15px;
  border: solid 1px #d9d9d9;
  border-radius: 4px;
  min-height: 284px;
}
.cl-memory-heatmap-dasnhoard .dashboard-item .title-item {
  display: flex;
  height: 24px;
}
.cl-memory-heatmap-dasnhoard .dashboard-item .title-item .title-text {
  flex: 1;
  font-size: 18px;
  font-weight: bold;
  line-height: 24px;
}
.cl-memory-heatmap-dasnhoard .dashboard-item .title-item .detail-link {
  cursor: pointer;
  font-size: 12px;
  height: 18px;
  line-height: 12px;
  padding-top: 2px;
}
.cl-memory-heatmap-dasnhoard .dashboard-item .title-item .detail-link a {
  color: #00a5a7;
  padding-right: 6px;
}
.cl-memory-heatmap-dasnhoard .dashboard-item .title-item .detail-link button {
  color: #00a5a7;
  border: none;
  background-color: #fff;
  cursor: pointer;
}
.cl-memory-heatmap-dasnhoard .dashboard-item .title-item .detail-link.disabled button {
  color: #c0c4cc;
  cursor: not-allowed;
}
.cl-memory-heatmap-dasnhoard .dashboard-item .content-item {
  height: calc(100% - 44px);
  margin-top: 20px;
}
.cl-memory-heatmap-dasnhoard .dashboard-item .content-item .dashboard-chart-content {
  width: 100%;
  height: 100%;
}
.cl-memory-heatmap-dasnhoard .margin-item {
  margin-top: 20px;
}
.cl-memory-heatmap-dasnhoard .noData-content {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}
.cl-memory-heatmap-dasnhoard .noData-content p,
.cl-memory-heatmap-dasnhoard .noData-content .noData-text {
  font-size: 16px;
}
.legend-content {
  height: 56px;
  border-bottom: solid 1px #e6ebf5;
  display: flex;
  justify-content: flex-end;
}
.legend-content .legend-item {
  width: 26px;
  height: 100%;
  padding: 5px 0;
  margin-left: 10px;
}
.legend-content .legend-item .color-item {
  width: 100%;
  padding: 0 6px;
  height: calc(100% - 20px);
}
.legend-content .legend-item .color-item div {
  width: 100%;
  height: 100%;
  border: solid 1px #e6ebf5;
}
.legend-content .legend-item .value-item {
  margin-top: 4px;
}
.heatmap-content {
  height: calc(100% - 132px);
  overflow-y: auto;
  display: flex;
  flex-wrap: wrap;
  margin-top: 20px;
}
.heatmap-content .heatmap-item {
  width: 25%;
  height: 260px;
  padding: 0 10px;
  margin-top: 20px;
  flex-shrink: 0;
}
.heatmap-content .heatmap-item.mt0 {
  margin-top: 0;
}
.heatmap-content .heatmap-item .detail-content {
  height: calc(100% - 28px);
  background: #e6ebf5;
  display: flex;
  flex-wrap: wrap;
  overflow-y: auto;
  padding-bottom: 10px;
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
}
.heatmap-item .detail-content .device-item .info-item {
  margin-top: 4px;
  text-align: center;
}
.heatmap-content .heatmap-item .info-content {
  margin-top: 10px;
  font-size: 16px;
  color: #333;
  font-weight: 600;
  text-align: center;
}
</style>

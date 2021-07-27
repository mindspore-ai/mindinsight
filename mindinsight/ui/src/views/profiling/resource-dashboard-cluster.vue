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
      <div class="cluster-wrap">
        <div class="title-item">
          <div class="title-text">
            {{$t('profilingCluster.memoryHeatMapTitle')}}
          </div>
          <div class="detail-link"
               :class="{disabled:!memoryHeatmapInitOver || !memoryHeatmapDataList.length}">
            <button :disabled="!memoryHeatmapInitOver || !memoryHeatmapDataList.length"
                    @click="jumpToHeatmapDetail('/memory-heatmap')">
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
            <div class="heatmap-content">
              <div class="heatmap-item"
                   v-for="(item, itemIndex) in memoryHeatmapDataList"
                   :key="itemIndex"
                   :class="{'mt0': itemIndex < colNum}">
                <div class="detail-content"
                     :class="{'center': item.showCenter}">
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
                          + $t('unit.GiB')}}
                            <br>
                            {{$t('profilingCluster.capaCity') + $t('symbols.colon') + deviceItem.capacity
                          + $t('unit.GiB')}}
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
                  {{$t('profilingCluster.host') + item.hostIp}}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="cluster-wrap">
        <div class="title-item">
          <div class="title-text">
            {{$t('profilingCluster.flopsHeatMapTitle')}}
          </div>
          <div class="detail-link"
               :class="{disabled:!flopsHeatmapInitOver || !flopsHeatmapDataList.length}">
            <button :disabled="!flopsHeatmapInitOver || !flopsHeatmapDataList.length"
                    @click="jumpToHeatmapDetail('/flops-heatmap')">
              {{$t('profiling.viewDetail')}}
              <i class="el-icon-d-arrow-right"></i>
            </button>
          </div>
        </div>
        <div class="content-item">
          <div class="noData-content"
               v-show="!flopsHeatmapInitOver || !flopsHeatmapDataList.length">
            <div>
              <img :src="require('@/assets/images/nodata.png')" />
            </div>
            <div v-if="flopsHeatmapInitOver && !flopsHeatmapDataList.length"
                 class="noData-text">{{$t("public.noData")}}</div>
            <div v-else
                 class="noData-text">{{$t("public.dataLoading")}}</div>
          </div>
          <div class="dashboard-chart-content"
               v-show="flopsHeatmapDataList.length && flopsHeatmapInitOver">
            <div class="heatmap-content">
              <div class="heatmap-item"
                   v-for="(item, itemIndex) in flopsHeatmapDataList"
                   :key="itemIndex"
                   :class="{'mt0': itemIndex < colNum}">
                <div class="detail-content"
                     :class="{'center': item.showCenter}">
                  <div class="device-item"
                       v-for="(deviceItem, deviceItemIndex) in item.data"
                       :key="deviceItemIndex">
                    <div class="color-item">
                      <el-tooltip placement="top">
                        <div slot="content">
                          <div>
                            {{$t('profilingCluster.rankID') + $t('symbols.colon') + deviceItem.rankId}}
                            <br>
                            FLOPs{{$t('symbols.colon')+deviceItem.flops}}M
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
                  {{$t('profilingCluster.host') + item.hostIp}}
                </div>
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
      memoryHeatmapInitOver: false, // The memory heatmap state
      memoryHeatmapDataList: [], // The memory heatmap data
      flopsHeatmapInitOver: false, // The flops heatmap state
      flopsHeatmapDataList: [], // The flops heatmap data
      legendArr: [], // Legend
      legendArrLength: 10, // Length of legend
      colNum: 4, // Column num of heatmap
      granularity: 0.1, // Granularity
    };
  },
  mounted() {
    this.initLegendArr();
    this.getMemoryHeatMapData();
    this.getFlopsHeatMapData();
  },
  methods: {
    /**
     * The logic of jump to heatmap page
     * @param {String} path The router path
     */
    jumpToHeatmapDetail(path) {
      this.$router.push({
        path,
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
     * The logic of get flops heatmap data
     */
    getFlopsHeatMapData() {
      const params = {
        train_id: this.trainingJobId,
      };
      RequestService.getClusterFlops(params)
          .then((res) => {
            if (!res || !res.data) {
              this.flopsHeatmapInitOver = true;
              return;
            }
            const resData = res.data;
            const heatmapDataDic = {};
            const heatmapDataArr = [];
            resData.forEach((heatmap) => {
              let arrayIndex;
              if (heatmapDataDic[heatmap.host_ip] === undefined) {
                arrayIndex =
                heatmapDataArr.push({
                  hostIp: heatmap.host_ip,
                  data: [],
                  center: false,
                }) - 1;
                heatmapDataDic[heatmap.host_ip] = arrayIndex;
              } else {
                arrayIndex = heatmapDataDic[heatmap.host_ip];
              }
              // Factor used to avoid JS floating point number question
              const factor = 100;
              const index = Math.floor((heatmap.FLOPs_norm * factor) / (this.granularity * factor));
              heatmapDataArr[arrayIndex].data.push({
                deviceId: heatmap.device_id,
                rankId: heatmap.rank_id,
                flops: heatmap.FLOPs,
                backgroundColor: this.legendArr[heatmap.FLOPs_norm === 1 ? index - 1 : index].backgroundColor,
              });
            });
            heatmapDataArr.forEach((data) => {
              if (data.data.length > this.colNum) {
                data.showCenter = false;
              }
            });
            this.flopsHeatmapDataList = heatmapDataArr;
            this.flopsHeatmapDataList =
            this.flopsHeatmapDataList.length > this.colNum
              ? this.flopsHeatmapDataList.slice(0, this.colNum)
              : this.flopsHeatmapDataList;
            this.flopsHeatmapInitOver = true;
          })
          .catch(() => {
            this.flopsHeatmapInitOver = true;
          });
    },
    /**
     * The logic of get memory heatmap data
     */
    getMemoryHeatMapData() {
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
            resData.forEach((data) => {
              let arrayIndex;
              if (heatmapDataMap[data.host_ip] === undefined) {
              // New host_ip
                arrayIndex =
                heatmapDataArr.push({
                  hostIp: data.host_ip,
                  data: [],
                  showCenter: true,
                }) - 1;
                heatmapDataMap[data.host_ip] = arrayIndex;
              } else {
              // Exist host_ip
                arrayIndex = heatmapDataMap[data.host_ip];
              }
              const capacity = data.capacity;
              const index = Math.floor(data.peak_mem / capacity / this.granularity);
              const deviceId = data.device_id;
              heatmapDataArr[arrayIndex].data[deviceId] = {
                deviceId,
                rankId: data.rank_id,
                peakMem: data.peak_mem,
                capacity,
                backgroundColor: this.legendArr[index]
                ? this.legendArr[index].backgroundColor
                : this.legendArr.slice(-1).backgroundColor,
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
            this.memoryHeatmapDataList =
            this.memoryHeatmapDataList.length > this.colNum
              ? this.memoryHeatmapDataList.slice(0, this.colNum)
              : this.memoryHeatmapDataList;
            this.memoryHeatmapInitOver = true;
          })
          .catch(() => {
            this.memoryHeatmapInitOver = true;
          });
    },
  },
};
</script>
<style scoped>
.cl-memory-heatmap-dasnhoard {
  height: 100%;
  width: 100%;
  background: var(--bg-color);
}
.cl-memory-heatmap-dasnhoard .dashboard-item {
  width: 100%;
  height: 100%;
  padding: 15px;
  border: solid 1px var(--border-color);
  border-radius: 4px;
  min-height: 284px;
}
.cluster-wrap {
  height: calc(50% - 28px);
  border-top: 1px solid var(--item-split-line-color);
}
.cl-memory-heatmap-dasnhoard .dashboard-item .title-item {
  display: flex;
  height: 24px;
  margin-top: 5px;
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
  height: 100%;
  display: flex;
  align-items: center;
}
.cl-memory-heatmap-dasnhoard .dashboard-item .title-item .detail-link a {
  color: var(--theme-color);
  padding-right: 6px;
}
.cl-memory-heatmap-dasnhoard .dashboard-item .title-item .detail-link button {
  color: var(--theme-color);
  border: none;
  background-color: var(--bg-color);
  cursor: pointer;
  padding: 0;
}
.cl-memory-heatmap-dasnhoard .dashboard-item .title-item .detail-link.disabled button {
  color: var(--button-disabled-font-color);
  cursor: not-allowed;
}
.cl-memory-heatmap-dasnhoard .dashboard-item .content-item {
  height: calc(100% - 49px);
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
  display: flex;
  justify-content: flex-start;
}
.legend-content .legend-item {
  width: 26px;
  height: 100%;
  padding: 5px 0;
  margin-left: 10px;
}
.legend-content .legend-item .color-item {
  width: 100%;
  padding: 0 1px;
  height: calc(100% - 19px);
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
  height: calc(100% - 29px);
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
  background: var(--heatmap-content-color);
  display: flex;
  flex-wrap: wrap;
  overflow-y: auto;
  padding-bottom: 10px;
  border-radius: 6px;
}
.heatmap-content .heatmap-item .detail-content.center {
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
}
.heatmap-item .detail-content .device-item .info-item {
  margin-top: 4px;
  text-align: center;
}
.heatmap-content .heatmap-item .info-content {
  margin-top: 10px;
  font-size: 16px;
  color: var(--font-color);
  font-weight: 600;
  text-align: center;
}
</style>

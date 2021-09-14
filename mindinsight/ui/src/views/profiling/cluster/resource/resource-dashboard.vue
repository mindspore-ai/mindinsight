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
               :class="{disabled:isHeterogeneous || !memoryHeatmapInitOver || !memoryHeatmapDataList.length}">
            <button :disabled="isHeterogeneous || !memoryHeatmapInitOver || !memoryHeatmapDataList.length"
                    @click="viewDetail('memory-heatmap')">
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
            <div v-if="isHeterogeneous"
                 class="noData-text">{{$t("profiling.isHeterogeneous")}}</div>
            <div v-else-if="memoryHeatmapInitOver && !memoryHeatmapDataList.length"
                 class="noData-text">{{$t("public.noData")}}</div>
            <div v-else
                 class="noData-text">{{$t("public.dataLoading")}}</div>
          </div>
          <div class="dashboard-chart-content"
               v-show="memoryHeatmapDataList.length && memoryHeatmapInitOver">
             <div class="heatmap-content">
                <div class="heatmap-item"
                      v-for="deviceItem in memoryHeatmapDataList"
                      :key="deviceItem.rankID">
                  <el-tooltip placement="top">
                    <div slot="content">
                      <div>
                        {{$t('profilingCluster.peakMem') + $t('symbols.colon') + deviceItem.peakMem.toFixed(3)
                          + $t('unit.GiB')}}
                        <br>
                        {{$t('profilingCluster.capaCity') + $t('symbols.colon') + deviceItem.capacity
                          + $t('unit.GiB')}}
                      </div>
                    </div>
                    <div class="color-item"
                          :style="{backgroundColor: deviceItem.backgroundColor}"></div>
                  </el-tooltip>
                  {{$t('profilingCluster.rankID') + deviceItem.rankID}}
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
                    @click="viewDetail('flops-heatmap')">
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
                  v-for="deviceItem in flopsHeatmapDataList"
                  :key="deviceItem.rankID">
                <el-tooltip placement="top">
                  <div slot="content">
                    <div>
                      FLOPs{{$t('symbols.colon') + deviceItem.flops}}M
                    </div>
                  </div>
                  <div class="color-item"
                      :style="{backgroundColor: deviceItem.backgroundColor}"></div>
                </el-tooltip>
                {{$t('profilingCluster.rankID') + deviceItem.rankID}}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import RequestService from '@/services/request-service';
import Color from '@/common/common-property';
export default {
  data() {
    return {
      trainInfo: {
        id: this.$route.query.id,
        dir: this.$route.query.dir,
        path: this.$route.query.path,
      },
      memoryHeatmapInitOver: false, // The memory heatmap state
      memoryHeatmapDataList: [], // The memory heatmap data
      flopsHeatmapInitOver: false, // The flops heatmap state
      flopsHeatmapDataList: [], // The flops heatmap data
      legendArr: [], // Legend
      num: 8, // num of heatmap
      legendArrLength: 10, // Length of legend
      granularity: 0.1, // Granularity
      isHeterogeneous: false,
    };
  },
  mounted() {
    this.initLegendArr();
    this.getMemoryHeatMapData();
    this.getFlopsHeatMapData();
  },
  methods: {
    viewDetail(path) {
      this.$emit('viewDetail', path);
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
        train_id: this.trainInfo.id,
      };
      RequestService.getClusterFlops(params)
          .then((res) => {
            if (!res || !res.data) {
              this.flopsHeatmapInitOver = true;
              return;
            }
            const heatmapDataset = [];
            res.data.forEach((data) => {
              const index = Math.floor(data.FLOPs_norm / this.granularity);
              heatmapDataset.push({
                rankID: data.rank_id,
                flops: data.FLOPs,
                backgroundColor: this.legendArr[data.FLOPs_norm === 1 ? index - 1 : index].backgroundColor,
              });
            });
            this.flopsHeatmapDataList = heatmapDataset.sort((a, b) => a.rankID - b.rankID);
            this.flopsHeatmapDataList =
            this.flopsHeatmapDataList.length > this.num
              ? this.flopsHeatmapDataList.slice(0, this.num)
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
        train_id: this.trainInfo.id,
      };
      RequestService.getClusterPeakMemory(params)
          .then((res) => {
            if (typeof res.data === 'object' && res.data.is_heterogeneous) {
              this.isHeterogeneous = true;
              this.memoryHeatmapInitOver = true;
              return;
            }
            if (!res || !res.data) {
              this.memoryHeatmapInitOver = true;
              return;
            }
            const heatmapDataset = [];
            res.data.forEach((data) => {
              const index = Math.floor(data.peak_mem / data.capacity / this.granularity);
              const {capacity} = data;
              const peakMem = data.peak_mem;
              heatmapDataset.push({
                rankID: data.rank_id,
                peakMem,
                capacity,
                backgroundColor: this.legendArr[index]
                ? this.legendArr[index].backgroundColor
                : this.legendArr.slice(-1).backgroundColor,
              });
            });
            this.memoryHeatmapDataList = heatmapDataset.sort((a, b) => a.rankID - b.rankID);
            this.memoryHeatmapDataList =
            this.memoryHeatmapDataList.length > this.num
              ? this.memoryHeatmapDataList.slice(0, this.num)
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
  font-size: 16px;
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
  flex-grow: 1;
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  overflow-y: auto;
}
.heatmap-content .heatmap-item {
  height: 120px;
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

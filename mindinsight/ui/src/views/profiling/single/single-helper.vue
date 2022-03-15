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
  <div class="helper">
    <div class="cur-card">
      <label>{{$t('profiling.rankID')}}</label>
      <el-select v-model="rankID"
                 class="card-select"
                 :placeholder="$t('public.select')"
                 @change="rankIDChanged">
        <el-option v-for="item in rankIDList"
                   :key="item"
                   :label="item"
                   :value="item">
        </el-option>
      </el-select>
    </div>
    <div class="helper-title">
      {{$t("profiling.smartHelper")}}
    </div>
    <div class="suggested-title">{{$t("profiling.suggestions")}}</div>
    <div id="helper-tips"></div>
  </div>
</template>

<script>
import RequestService from '@/services/request-service';
import { isInteger } from '@/js/utils';
export default {
  props: {
    defaultRankID: [Number, String],
  },
  data() {
    return {
      trainInfo: {
        id: this.$route.query.id,
        path: this.$route.query.path,
        dir: this.$route.query.dir,
      },
      rankID: null,
      rankIDList: [],
      tipsArrayList: [
        'step_trace-iter_interval',
        'minddata_pipeline-general',
        'minddata_pipeline-dataset_op',
        'minddata_pipeline-generator_op',
        'minddata_pipeline-map_op',
        'minddata_pipeline-batch_op',
        'minddata_cpu_utilization',
        'minddata_device_queue_rate',
      ],
      moreParameter: ['minddata_device_queue', 'minddata_get_next_queue', 'device_queue_warning'],
      helperUrl: '',
    };
  },
  mounted() {
    this.initRankIDList().then((res) => {
      this.rankIDChanged();
      if (res) this.getDataOfProfileHelper();
    });
  },
  created() {
    const isPynative = this.$route.query.mode === 'pynative';
    this.helperUrl = isPynative? 'pynativeUrl': 'url';
  },
  methods: {
    /**
     * On rankID changed
     */
    rankIDChanged() {
      this.$emit('change', this.rankID);
    },
    /**
     * Init rankID list
     * @return {Promise}
     */
    initRankIDList() {
      return new Promise((resolve) => {
        const params = {
          profile: this.trainInfo.dir,
          train_id: this.trainInfo.id,
        };
        RequestService.getProfilerDeviceData(params)
          .then(
            (res) => {
              if (Object.keys(res.data).length > 0) {
                this.rankIDList = res.data.device_list.sort((a, b) => +a - +b);
                this.rankID = isInteger(this.defaultRankID) ? this.defaultRankID + '' : this.rankIDList[0];
                resolve(true);
              } else {
                this.rankIDList = [];
                this.rankID = '';
                resolve(false);
              }
            },
            () => {
              this.rankIDList = [];
              this.rankID = '';
              resolve(false);
            }
          )
          .catch(() => {
            this.rankIDList = [];
            this.rankID = '';
            resolve(false);
          });
      });
    },
    /**
     * Get profile helper data
     */
    getDataOfProfileHelper() {
      const params = {
        train_id: this.trainInfo.id,
        profile: this.trainInfo.dir,
        device_id: this.rankID,
      };
      RequestService.queryDataOfProfileHelper(params)
        .then((res) => {
          if (res && res.data) {
            const innerHTMLs = [];
            Object.keys(res.data).forEach((item) => {
              if (!this.tipsArrayList.includes(item) && !this.moreParameter.includes(item) && res.data[item]) {
                this.$t(`profiling`)[item] = res.data[item];
              }
              if (item.endsWith('type_label')) {
                innerHTMLs.push(
                  `<div class="suggested-items-style">
                         <div class="helper-icon"></div>
                         <div class="helper-container-title">
                           ${this.$t(`profiling`)[item].desc}
                         </div>
                       </div>`
                );
              } else if (this.tipsArrayList.includes(item)) {
                let content = '';
                if (item === 'minddata_device_queue_rate') {
                  if (res.data[item].empty_rate > res.data[item].empty_warning_threshold) {
                    content = this.$t(`profiling.${item}.empty_rate`, res.data[item]);
                  } else {
                    content = this.$t(`profiling.${item}.empty_warning_threshold`, res.data[item]);
                  }
                } else {
                  content = `${this.$t(`profiling`)[item].desc}`.replace(`{n1}`, res.data[item][0]);
                }
                innerHTMLs.push(
                  `<div class="content-style">
                         <div class="content-icon el-icon-caret-right"></div>
                         <div class="helper-content-style">${content}</div>
                       </div>`
                );
              } else if (item === 'minddata_device_queue') {
                const [queueStart, queueEnd] = res.data['minddata_device_queue'];
                const deviceEmpty = queueStart >= 0 ? queueStart : '--';
                const deviceTotal = queueEnd >= 0 ? queueEnd : '--';
                const content = `${this.$t(`profiling`)[item].desc}`
                  .replace(`{n1}`, `<span class="nowrap-style"> ${deviceEmpty}</span>`)
                  .replace(`{n2}`, `<span class="nowrap-style"> ${deviceTotal}</span>`)
                  .replace(`{n3}`, `<span class="nowrap-style"> ${deviceTotal - deviceEmpty}</span>`)
                  .replace(`{n4}`, `<span class="nowrap-style"> ${deviceTotal}</span>`);
                innerHTMLs.push(
                  `<div class="content-style">
                         <div class="content-icon el-icon-caret-right"></div>
                         <div class="helper-content-style">${content}</div>
                       </div>`
                );
              } else if (item === 'minddata_get_next_queue') {
                const [queueStart, queueEnd] = res.data['minddata_get_next_queue'];
                const getNextEmpty = queueStart >= 0 ? queueStart : '--';
                const getNextTotal = queueEnd >= 0 ? queueEnd : '--';
                const content = `${this.$t(`profiling`)[item].desc}`
                  .replace(`{n1}`, `<span class="nowrap-style"> ${getNextEmpty}</span>`)
                  .replace(`{n2}`, `<span class="nowrap-style"> ${getNextTotal}</span>`)
                  .replace(`{n3}`, `<span class="nowrap-style"> ${getNextTotal - getNextEmpty}</span>`)
                  .replace(`{n4}`, `<span class="nowrap-style"> ${getNextTotal}</span>`);
                innerHTMLs.push(
                  `<div class="content-style">
                         <div class="content-icon el-icon-caret-right"></div>
                         <div class="helper-content-style">${content}</div>
                       </div>`
                );
              } else if (item === 'device_queue_warning' && res.data[item].length) {
                const content = `${this.$t(`profiling`)[item].desc}`;
                innerHTMLs.push(
                  `<div class="content-style">
                         <div class="content-icon el-icon-caret-right"></div>
                         <div class="helper-content-style">${content}</div>
                       </div>`
                );
              } else if (this.$t(`profiling`)[item].anchor) {
                if (this.$t(`profiling`)[item].anchor.length === 1) {
                  innerHTMLs.push(
                    `<div class="content-style">
                           <div class="content-icon el-icon-caret-right"></div>
                           <div class="helper-content-style">
                             <a target="_blank" href="${this.$t(`profiling`)[item][this.helperUrl][0]}">
                               ${this.$t(`profiling`)[item].desc}
                             </a>
                           </div>
                         </div>`
                  );
                } else {
                  const anchorList = this.$t(`profiling`)[item].anchor;
                  let anchorContent = this.$t(`profiling`)[item].desc;
                  for (let i = 0; i < anchorList.length; i++) {
                    const desc = anchorContent.relpace(
                      anchorList[i],
                      `<a target="_blank" href="${this.$t(`profiling`)[item][this.helperUrl][i]}">
                      ${anchorList[i]}</a>`
                    );
                    anchorContent = desc;
                  }
                  innerHTMLs.push(
                    `<div class="content-style">
                           <div class="content-icon el-icon-caret-right"></div>
                           <div class="helper-content-style">${anchorContent}</div>
                         </div>`
                  );
                }
              } else {
                innerHTMLs.push(
                  `<div class="content-style">
                         ${this.$t(`profiling`)[item].desc}
                       </div>`
                );
              }
              const helper = document.getElementById('helper-tips');
              if (helper) helper.innerHTML = innerHTMLs.join('');
            });
          }
        })
        .catch(() => {});
    },
  },
};
</script>

<style>
.helper {
  box-sizing: border-box;
  padding: 32px;
  padding-top: 20px;
  height: 100%;
  overflow-y: auto;
  background: var(--module-bg-color);
  word-wrap: break-word;
}
.helper .nowrap-style {
  white-space: nowrap;
}
.helper .cur-card {
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-color);
}
.helper .cur-card .card-select {
  width: calc(100% - 120px);
}
.helper .cur-card > label {
  margin-right: 14px;
}
.helper .helper-title {
  font-size: 18px;
  font-weight: bold;
  margin: 24px 0;
}
.helper .helper-title .el-icon-rank {
  float: right;
  cursor: pointer;
}
.helper .helper-container-title {
  display: inline-block;
  padding: 0 6px;
}
.helper .helper-icon {
  display: inline-block;
  width: 6px;
  height: 6px;
  margin-top: 6px;
  border-radius: 3px;
  background-color: var(--theme-color);
}
.helper .suggested-title {
  font-weight: bold;
  margin-bottom: 20px;
  font-size: 16px;
}
.helper .link-title {
  cursor: pointer;
}
.helper .container-bottom {
  margin-bottom: 16px;
}
.helper .suggested-items-style {
  display: flex;
  font-weight: bold;
  margin-bottom: 6px;
  margin-top: 10px;
}
.helper .helper-content-style {
  margin-left: 6px;
  line-height: 20px;
  word-break: break-all;
  text-overflow: ellipsis;
  overflow: hidden;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 8;
}
.helper .content-icon {
  color: var(--theme-color);
  padding-top: 3px;
}
.helper .content-style {
  display: flex;
}
</style>

/**
 * Copyright 2019 Huawei Technologies Co., Ltd.All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
import axios from './fetcher';

export default {
  // query dataset graph data
  queryDatasetGraph(params) {
    return axios({
      method: 'get',
      url: 'v1/mindinsight/datasets/dataset_graph',
      params: params,
    });
  },

  // NEW API for model and data source tracing
  queryLineagesData(params) {
    return axios({
      method: 'post',
      url: 'v1/mindinsight/lineagemgr/lineages',
      data: params.body,
    });
  },
  // API for model and data source tracing
  putLineagesData(params) {
    return axios({
      method: 'put',
      url: 'v1/mindinsight/lineagemgr/lineages?train_id=' + params.train_id,
      data: params.body,
    });
  },

  // query summary list
  querySummaryList(params, isIgnoreError) {
    return axios({
      method: 'get',
      url: 'v1/mindinsight/datavisual/train-jobs',
      params: params,
      headers: {
        ignoreError: isIgnoreError,
      },
    });
  },

  // query scalar sample
  getScalarsSample(params) {
    return axios({
      method: 'get',
      url: 'v1/mindinsight/datavisual/scalar/metadata',
      params: params,
      headers: {
        ignoreError: true,
      },
    });
  },

  // query tensors sample
  getTensorsSample(params) {
    return axios({
      method: 'get',
      url: 'v1/mindinsight/datavisual/tensors',
      params: params,
      headers: {
        ignoreError: true,
      },
    });
  },

  // query graph data
  queryGraphData(params) {
    return axios({
      method: 'get',
      url: 'v1/mindinsight/datavisual/graphs/nodes',
      params: params,
    });
  },

  // search graph node
  searchNodesNames(params) {
    return axios({
      method: 'get',
      url: 'v1/mindinsight/datavisual/graphs/nodes/names',
      params: params,
    });
  },

  // query the level of the node from the first layer based on node name
  querySingleNode(params) {
    return axios({
      method: 'get',
      url: 'v1/mindinsight/datavisual/graphs/single-node',
      params: params,
    });
  },

  // query single train job list(image/scalar/graph)
  getSingleTrainJob(params, isIgnoreError) {
    return axios({
      method: 'get',
      url: 'v1/mindinsight/datavisual/single-job',
      params: params,
      headers: {
        ignoreError: isIgnoreError,
      },
    });
  },

  // set caches
  trainJobsCaches(params) {
    return axios({
      method: 'post',
      url: 'v1/mindinsight/datavisual/train-job-caches',
      data: params,
    });
  },

  // query metedata
  getSummarySample(params) {
    const trainIdsStr = params.train_id;
    const trainIdsArr = trainIdsStr.split('&');
    let requestStr = '';
    trainIdsArr.forEach((item) => {
      if (item) {
        requestStr += `train_id=${encodeURIComponent(item)}&`;
      }
    });
    requestStr += `tag=${params.tag}`;
    return axios({
      method: 'get',
      url: `v1/mindinsight/datavisual/scalars?${requestStr}`,
    });
  },

  // query image meta data
  getImageMetadatas(params) {
    return axios({
      method: 'get',
      url: 'v1/mindinsight/datavisual/image/metadata',
      params: params,
      headers: {
        ignoreError: true,
      },
    });
  },

  // query training job visualization plugins
  getDatavisualPlugins(params) {
    return axios({
      method: 'get',
      url: 'v1/mindinsight/datavisual/plugins',
      params: params,
    });
  },
  getHistogramData(params) {
    return axios({
      method: 'get',
      url: 'v1/mindinsight/datavisual/histograms',
      params: params,
    });
  },
  getProfilerDeviceData(params) {
    return axios({
      method: 'get',
      url: 'v1/mindinsight/profile/devices',
      params: params,
    });
  },
  getProfilerOpData(params) {
    return axios({
      method: 'post',
      url: 'v1/mindinsight/profile/ops/search',
      params: params.params,
      data: params.body,
      headers: {
        ignoreError: true,
      },
    });
  },
  // get data of helper
  queryDataOfProfileHelper(params) {
    return axios({
      method: 'get',
      url: 'v1/mindinsight/profile/summary/propose',
      params: params,
    });
  },
  // query training trace
  queryTrainingTrace(params) {
    return axios({
      method: 'get',
      url: 'v1/mindinsight/profile/training-trace/graph',
      params: params,
      headers: {
        ignoreError: true,
      },
    });
  },
  targetTimeInfo(params) {
    return axios({
      method: 'get',
      url: 'v1/mindinsight/profile/training-trace/target-time-info',
      params: params,
      headers: {
        ignoreError: true,
      },
    });
  },
  queryTimeline(params) {
    return axios({
      method: 'get',
      url: 'v1/mindinsight/profile/timeline',
      params: params,
      headers: {
        ignoreError: true,
      },
    });
  },
  queryTimlineInfo(params) {
    return axios({
      method: 'get',
      url: 'v1/mindinsight/profile/timeline-summary',
      params: params,
      headers: {
        ignoreError: true,
      },
    });
  },
  queryOpQueue(params) {
    return axios({
      method: 'post',
      url: 'v1/mindinsight/profile/minddata-pipeline/op-queue',
      params: params.params,
      data: params.body,
      headers: {
        ignoreError: true,
      },
    });
  },
  queryQueue(params) {
    return axios({
      method: 'get',
      url: 'v1/mindinsight/profile/minddata-pipeline/queue',
      params: params,
      headers: {
        ignoreError: true,
      },
    });
  },
  queryProcessSummary(params) {
    return axios({
      method: 'get',
      url: 'v1/mindinsight/profile/process_summary',
      params: params,
      headers: {
        ignoreError: true,
      },
    });
  },
  queueInfo(params) {
    return axios({
      method: 'get',
      url: 'v1/mindinsight/profile/queue_info',
      params: params,
      headers: {
        ignoreError: true,
      },
    });
  },
  minddataOp(params) {
    return axios({
      method: 'get',
      url: 'v1/mindinsight/profile/minddata_op',
      params: params,
      headers: {
        ignoreError: true,
      },
    });
  },
  getMetricsData() {
    return axios({
      method: 'get',
      url: 'v1/mindinsight/resource_monitor/current/metrics',
      headers: {
        ignoreError: true,
      },
    });
  },
};

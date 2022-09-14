/**
 * Copyright 2019-2022 Huawei Technologies Co., Ltd.All Rights Reserved.
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
 import { transCode } from './fetcher';

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
       url: 'v1/mindinsight/lineagemgr/lineages?train_id=' + transCode(params.train_id),
       data: params.body,
     });
   },

   queryTargetsData(params) {
     return axios({
       method: 'post',
       url: `v1/mindinsight/optimizer/targets/search`,
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
     const trainIds = params.train_id;
     let requestStr = '';
     trainIds.forEach((item) => {
       if (item) {
         requestStr += `train_id=${transCode(item)}&`;
       }
     });
     requestStr += `tag=${transCode(params.tag)}`;
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

   // query image data
   getImageData(params) {
     return axios({
       method: 'get',
       url: 'v1/mindinsight/datavisual/image/single-image',
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
   // get data of cluster helper
   queryDataOfProfileClusterHelper(params) {
     return axios({
       method: 'get',
       url: 'v1/mindinsight/profile/summary/cluster-propose',
       params: params,
       timeout: 1000 * 240,
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
   queryTimelineInfo(params) {
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
   getGraphData(params) {
     return axios({
       method: 'get',
       url: 'v1/mindinsight/profile/parallel-strategy/graphs',
       params: params,
       headers: {
         ignoreError: true,
       },
     });
   },
   // debugger
   getSession(params) {
     return axios({
       method: 'post',
       url: 'v1/mindinsight/debugger/sessions',
       data: params,
     });
   },
   deleteSession(sessionId) {
     return axios({
       method: 'post',
       url: `v1/mindinsight/debugger/sessions/${sessionId}/delete`,
     });
   },
   checkSessions() {
     return axios({
       method: 'get',
       url: `v1/mindinsight/debugger/sessions`,
     });
   },
   pollData(params, sessionId) {
     return axios({
       method: 'get',
       url: `v1/mindinsight/debugger/sessions/${sessionId}/poll-data`,
       params: params,
       headers: {
         ignoreError: true,
       },
       timeout: 0,
     });
   },
   retrieve(params, sessionId) {
     return axios({
       method: 'post',
       url: `v1/mindinsight/debugger/sessions/${sessionId}/retrieve`,
       data: params,
     });
   },
   createWatchpoint(params, sessionId) {
     return axios({
       method: 'post',
       url: `v1/mindinsight/debugger/sessions/${sessionId}/create-watchpoint`,
       data: params,
     });
   },
   updateWatchpoint(params, sessionId) {
     return axios({
       method: 'post',
       url: `v1/mindinsight/debugger/sessions/${sessionId}/update-watchpoint`,
       data: params,
     });
   },
   deleteWatchpoint(params, sessionId) {
     return axios({
       method: 'post',
       url: `v1/mindinsight/debugger/sessions/${sessionId}/delete-watchpoint`,
       data: params,
     });
   },
   control(params, sessionId) {
     return axios({
       method: 'post',
       url: `v1/mindinsight/debugger/sessions/${sessionId}/control`,
       data: params,
     });
   },
   search(params, sessionId) {
     return axios({
       method: 'get',
       url: `v1/mindinsight/debugger/sessions/${sessionId}/search`,
       params: params,
     });
   },
   retrieveNodeByBfs(params) {
     return axios({
       method: 'get',
       url: 'v1/mindinsight/debugger/retrieve_node_by_bfs',
       params: params,
     });
   },
   tensorComparisons(params, sessionId) {
     return axios({
       method: 'get',
       url: `v1/mindinsight/debugger/sessions/${sessionId}/tensor-comparisons`,
       params: params,
     });
   },
   tensors(params, sessionId) {
     return axios({
       method: 'get',
       url: `v1/mindinsight/debugger/sessions/${sessionId}/tensors`,
       params: params,
     });
   },
   retrieveTensorHistory(params, sessionId) {
     return axios({
       method: 'post',
       url: `v1/mindinsight/debugger/sessions/${sessionId}/tensor-history`,
       data: params,
     });
   },
   queryConditions(sessionId) {
     return axios({
       method: 'get',
       url: `v1/mindinsight/debugger/sessions/${sessionId}/condition-collections`,
     });
   },
   recheckWatchPoints(sessionId) {
     return axios({
       method: 'post',
       url: `v1/mindinsight/debugger/sessions/${sessionId}/recheck`,
     });
   },
   searchWatchpointHits(params, sessionId) {
     return axios({
       method: 'post',
       url: `v1/mindinsight/debugger/sessions/${sessionId}/search-watchpoint-hits`,
       data: params,
     });
   },
   queryStackList(params, sessionId) {
     return axios({
       method: 'get',
       url: `v1/mindinsight/debugger/sessions/${sessionId}/stacks`,
       params,
     });
   },
   loadTensor(params, sessionId) {
     return axios({
       method: 'post',
       url: `v1/mindinsight/debugger/sessions/${sessionId}/tensor-files/load`,
       data: params,
     });
   },
   getGraphRuns(sessionId, rankId) {
     return axios({
       method: 'get',
       url: `v1/mindinsight/debugger/sessions/${sessionId}/ranks/${rankId}/graph-runs`,
     });
   },
   // explain list
   getExplainList(params) {
     return axios({
       method: 'get',
       url: 'v1/mindinsight/explainer/explain-jobs',
       params: params,
     });
   },
   // Explain query train base information
   queryTrainInfo(params) {
     return axios({
       method: 'get',
       url: 'v1/mindinsight/explainer/explain-job',
       params: params,
     });
   },
   // Explain query page table information
   queryPageInfo(params) {
     return axios({
       method: 'post',
       url: 'v1/mindinsight/explainer/saliency',
       data: params,
     });
   },

   getEvaluation(params) {
     return axios({
       method: 'get',
       url: 'v1/mindinsight/explainer/evaluation',
       params: params,
     });
   },
   queryHOCData(params) {
     return axios({
       method: 'post',
       url: 'v1/mindinsight/explainer/hoc',
       data: params,
     });
   },
   tensorHitsData(params, sessionId) {
     return axios({
       method: 'get',
       url: `v1/mindinsight/debugger/sessions/${sessionId}/tensor-hits`,
       params: params,
     });
   },
   getTensorGraphData(params, sessionId) {
     return axios({
       method: 'get',
       url: `v1/mindinsight/debugger/sessions/${sessionId}/tensor-graphs`,
       params: params,
     });
   },
   getCpuUtilization(params) {
     return axios({
       method: 'post',
       url: 'v1/mindinsight/profile/minddata-cpu-utilization-summary',
       params: params.params,
       data: params.body,
     });
   },
   setRecommendWatchPoints(params, sessionId) {
     return axios({
       method: 'post',
       url: `v1/mindinsight/debugger/sessions/${sessionId}/set-recommended-watch-points`,
       data: params,
     });
   },
   // memory-datail apis
   queryMemorySummary(params) {
     return axios({
       method: 'get',
       url: 'v1/mindinsight/profile/memory-summary',
       params: params,
     });
   },
   queryMemoryGraphics(params) {
     return axios({
       method: 'get',
       url: 'v1/mindinsight/profile/memory-graphics',
       params: params,
     });
   },
   queryMemoryBreakdowns(params) {
     return axios({
       method: 'get',
       url: 'v1/mindinsight/profile/memory-breakdowns',
       params: params,
     });
   },
   getClusterInfo(params) {
     return axios({
       method: 'post',
       params: params.params,
       data: params.body,
       url: 'v1/mindinsight/profile/cluster-step-trace-summary',
     });
   },
   getCommInfo(params) {
     return axios({
       method: 'post',
       params: params.params,
       data: params.body,
       url: 'v1/mindinsight/profile/search-cluster-communication',
     });
   },
   getLinkInfo(params) {
     return axios({
       method: 'post',
       params: params.params,
       data: params.body,
       url: 'v1/mindinsight/profile/search-cluster-link',
     });
   },
   getClusterPeakMemory(params) {
     return axios({
       method: 'get',
       params: params,
       url: 'v1/mindinsight/profile/cluster-peak-memory',
     });
   },
   getFlopsSummary(params) {
     return axios({
       method: 'get',
       params: params,
       url: 'v1/mindinsight/profile/flops-summary',
     });
   },
   getClusterFlops(params) {
     return axios({
       method: 'get',
       params: params,
       url: 'v1/mindinsight/profile/cluster-flops',
     });
   },
   getFlopsScope(params) {
     return axios({
       method: 'get',
       params: params,
       url: 'v1/mindinsight/profile/flops-scope',
     });
   },
   queryLossGraph(params) {
     const trainIds = params.train_id;
     let requestStr = '';
     if (Array.isArray(trainIds)) {
       trainIds.forEach((item) => {
         if (item) {
           requestStr += `train_id=${(transCode(item))}&`;
         }
       });
     } else {
       requestStr += `train_id=${(transCode(trainIds))}&`;
     }
     requestStr += `type=${params.type}`;
     if (params.metadata || params.metadata === false) {
       requestStr += `&metadata=${params.metadata}`;
     }
     if (params.interval_id || params.interval_id === 0) {
       requestStr += `&interval_id=${params.interval_id}`;
     }
     return axios({
       method: 'get',
       url: `v1/mindinsight/datavisual/landscape/landscapes?${requestStr}`,
     });
   },
   queryEpochIntervals(params) {
     return axios({
       method: 'get',
       url: 'v1/mindinsight/datavisual/landscape/intervals',
       params: params,
     });
   },
  // query operator dynamic shape detail
  queryDynamicShape(params) {
    return axios({
      method: 'post',
      url: 'v1/mindinsight/profile/dynamic-shape-detail',
      params: params,
      headers: {
        ignoreError: true,
      }
    });
  },
  // query all graph nodes data
  queryAllGraphNodesData(params) {
    return axios({
      method: 'get',
      url: 'v1/mindinsight/datavisual/graphs/nodes/all',
      params: params,
    });
  },
  getGraphs(trainId) {
    return axios({
      method: "get",
      url: "v1/mindinsight/profile/parallel-strategy/graphs",
      params: { train_id: trainId },
      headers: {
        ignoreError: true,
      },
      timeout: 1000 * 240,
    });
  },
  getTimeLineData(trainId, stepNum) {
    return axios({
      method: "get",
      url: "v1/mindinsight/profile/marey-graph/timeline",
      params: { train_id: trainId, step: stepNum, device_type: "ascend" },
      headers: {
        ignoreError: true,
      },
      timeout: 1000 * 240,
    });
  },
  getOverviewTime(trainId) {
    return axios({
      method: "get",
      url: "v1/mindinsight/profile/marey-graph/overview-time",
      params: { train_id: trainId, device_type: "ascend" },
      headers: {
        ignoreError: true,
      },
      timeout: 1000 * 240,
    });
  },
  getCommunicationGraph(trainId) {
    return axios({
      method: "get",
      url: "v1/mindinsight/profile/communication-data",
      params: { train_id: trainId },
      headers: {
        ignoreError: true,
      },
      timeout: 1000 * 240,
    });
  },

  getFLOPsData(trainId) {
    return axios({
      method: "get",
      url: "v1/mindinsight/profile/marey-graph/flops-data",
      params: { train_id: trainId },
      headers: {
        ignoreError: true,
      },
      timeout: 1000 * 240,
    });
  },
  getMemoryData(trainId) {
    return axios({
      method: "get",
      url: "v1/mindinsight/profile/marey-graph/memory-data",
      params: { train_id: trainId, device_type: "ascend" },
      headers: {
        ignoreError: true,
      },
      timeout: 1000 * 240,
    });
  },
  getScopeMap(params) {
    return axios({
      method: "get",
      url: "/v1/mindinsight/profile/marey-graph/scopemap",
      params: params,
      headers: {
        ignoreError: true,
      },
      timeout: 1000 * 240,
    });
  },
   // query operator gpu dynamic shape detail
   queryDynamicShapeGPU(params) {
     return axios({
       method: 'post',
       url: 'v1/mindinsight/profile/dynamic-shape-detail',
       params: params.params,
       data: params.body,
       headers: {
         ignoreError: true,
       }
     });
   },
};

/**
 * Copyright 2019-2021 Huawei Technologies Co., Ltd.All Rights Reserved.
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
import Vue from 'vue';
import Router from 'vue-router';
Vue.use(Router);
const VueRouterPush = Router.prototype.push;
Router.prototype.push = function push(to) {
  return VueRouterPush.call(this, to).catch((err) => err);
};

export default new Router({
  base: process.env.BASE_URL,
  routes: [
    // 404 matching
    {
      path: '*',
      redirect: '/summary-manage',
    },
    {
      path: '/',
      component: () => import('./views/train-manage/summary-manage.vue'),
      redirect: '/summary-manage',
    },
    {
      path: '/summary-manage',
      component: () => import('./views/train-manage/summary-manage.vue'),
    },
    {
      path: '/train-manage/training-dashboard',
      component: () => import('./views/train-manage/training-dashboard.vue'),
    },
    {
      path: '/train-manage/scalar',
      component: () => import('./views/train-manage/scalar.vue'),
    },
    {
      path: '/train-manage/image',
      component: () => import('./views/train-manage/image.vue'),
    },
    {
      path: '/train-manage/histogram',
      component: () => import('./views/train-manage/histogram.vue'),
    },
    {
      path: '/train-manage/tensor',
      component: () => import('./views/train-manage/tensor.vue'),
    },
    {
      path: '/train-manage/graph',
      component: () => import('./views/train-manage/graph.vue'),
    },
    {
      path: '/train-manage/data-map',
      component: () => import('./views/train-manage/data-map.vue'),
    },
    {
      path: '/train-manage/loss-analysis',
      component: () => import('./views/train-manage/loss-analysis.vue'),
    },
    {
      path: '/model-traceback',
      component: () => import('./views/train-manage/model-traceback.vue'),
    },
    {
      path: '/data-traceback',
      component: () => import('./views/train-manage/data-traceback.vue'),
    },
    {
      path: '/compare-analysis',
      component: () => import('./views/train-manage/compare-analysis/compare-dashboard.vue'),
      redirect: '/compare-analysis/scalar',
      children: [
        {
          path: 'scalar',
          component: () => import('./views/train-manage/compare-analysis/scalar-compare.vue'),
        },
        {
          path: 'loss',
          component: () => import('./views/train-manage/compare-analysis/loss-compare.vue'),
        },
      ],
    },
    {
      path: '/profiling-cpu',
      component: () => import('./views/profiling-cpu/profiling-dashboard.vue'),
      redirect: '/profiling-cpu/performance-dashboard',
      children: [
        {
          path: 'performance-dashboard',
          component: () => import('./views/profiling-cpu/performance-dashboard.vue'),
        },
        {
          path: 'resource-dashboard',
          component: () => import('./views/profiling-cpu/resource-dashboard.vue'),
        },
        {
          path: 'operator',
          component: () => import('./views/profiling-cpu/operator.vue'),
        },
      ],
    },
    // add single and cluster tab for profiling of gpu
    {
      path: '/profiling-gpu',
      component: () => import('./views/profiling-gpu/profiling-gpu-dashboard.vue'),
      redirect: '/profiling-gpu/single',
      children: [
        {
          path: 'single',
          component: () => import('./views/profiling-gpu/single/profiling.vue'),
          redirect: '/profiling-gpu/single/profiling-dashboard',
          children: [
            {
              path: 'profiling-dashboard',
              component: () => import('./views/profiling-gpu/single/profiling-dashboard.vue'),
            },
            {
              path: 'data-process',
              component: () => import('./views/profiling/single/performance/data-process.vue'),
            },
            {
              path: 'operator',
              component: () => import('./views/profiling-gpu/single/operator.vue'),
            },
            {
              path: 'resource-utilization',
              component: () => import('./views/profiling-gpu/single/resource-utilization.vue'),
            },
            {
              path: 'step-trace',
              component: () => import('./views/profiling/single/performance/step-trace.vue'),
            },
            {
              path: 'cpu-detail',
              component: () => import('./views/profiling/single/resource/cpu-utilization.vue'),
            },
          ]
        },
        {
          path: 'cluster',
          component: () => import('./views/profiling-gpu/cluster/cluster-dashboard.vue'),
          redirect: '/profiling-gpu/cluster/performance',
          children: [
            {
              path: 'performance',
              component: () => import('./views/profiling-gpu/cluster/performance-dashboard.vue'),
            },
            {
              path: 'step-trace',
              component: () => import('./views/profiling-gpu/cluster/step-trace.vue')
            },
          ]
        }
      ],
    },
    {
      path: '/debugger',
      component: () => import('./views/debugger/debugger.vue'),
    },
    {
      path: '/offline-debugger',
      component: () => import('./views/debugger/debugger.vue'),
    },
    {
      path: '/explain',
      component: () => import('./views/explain/summary-list.vue'),
    },
    {
      path: '/explain/saliency-map',
      component: () => import('./views/explain/saliency-map.vue'),
    },
    {
      path: '/explain/conterfactual-interpretation',
      component: () => import('./views/explain/conterfactual-interpretation.vue'),
    },
    {
      path: '/explain/xai-metric',
      component: () => import('./views/explain/xai-metric.vue'),
    },
    {
      path: '/profiling',
      component: () => import('./views/profiling/profiling-dashboard.vue'),
      redirect: '/profiling/single',
      children: [
        {
          path: 'single',
          component: () => import('./views/profiling/single/single-dashboard.vue'),
          redirect: '/profiling/single/performance',
          children: [
            // Dashboard
            {
              path: 'performance',
              component: () => import('./views/profiling/single/performance/performance-dashboard.vue'),
            },
            {
              path: 'resource',
              component: () => import('./views/profiling/single/resource/resource-dashboard.vue'),
            },
            // Performance Details
            {
              path: 'step-trace',
              component: () => import('./views/profiling/single/performance/step-trace.vue'),
            },
            {
              path: 'data-process',
              component: () => import('./views/profiling/single/performance/data-process.vue'),
            },
            {
              path: 'operator',
              component: () => import('./views/profiling/single/performance/operator.vue'),
            },
            // Resource Details
            {
              path: 'cpu-utilization',
              component: () => import('./views/profiling/single/resource/cpu-utilization.vue'),
            },
            {
              path: 'memory-utilization',
              component: () => import('./views/profiling/single/resource/memory-utilization.vue'),
            },
          ],
        },
        {
          path: 'cluster',
          component: () => import('./views/profiling/cluster/cluster-dashboard.vue'),
          redirect: '/profiling/cluster/performance',
          children: [
            // Dashboard
            {
              path: 'performance',
              component: () => import('./views/profiling/cluster/performance/performance-dashboard.vue'),
            },
            {
              path: 'resource',
              component: () => import('./views/profiling/cluster/resource/resource-dashboard.vue'),
            },
            {
              path: 'strategy',
              component: () => import('./views/profiling/parallel-graph/graph-container.vue'),
            },
            // Performance Details
            {
              path: 'step-trace',
              component: () => import('./views/profiling/cluster/performance/step-trace.vue'),
            },
            {
              path: 'communication',
              component: () => import('./views/profiling/cluster/performance/communication.vue'),
            },
            // Resource Details
            {
              path: 'flops-heatmap',
              component: () => import('./views/profiling/cluster/resource/flops-heatmap.vue'),
            },
            {
              path: 'memory-heatmap',
              component: () => import('./views/profiling/cluster/resource/memory-heatmap.vue'),
            },
          ],
        },
      ],
    },
  ],
});

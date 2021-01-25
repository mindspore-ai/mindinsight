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
      path: '/model-traceback',
      component: () => import('./views/train-manage/model-traceback.vue'),
    },
    {
      path: '/data-traceback',
      component: () => import('./views/train-manage/data-traceback.vue'),
    },
    {
      path: '/compare-plate',
      component: () => import('./views/train-manage/compare-plate.vue'),
    },
    {
      path: '/profiling',
      component: () => import('./views/profiling/profiling.vue'),
      redirect: '/profiling/profiling-dashboard',
      children: [
        {
          path: 'profiling-dashboard',
          component: () => import('./views/profiling/profiling-dashboard.vue'),
        },
        {
          path: 'step-trace',
          component: () => import('./views/profiling/step-trace.vue'),
        },
        {
          path: 'operator',
          component: () => import('./views/profiling/operator.vue'),
        },
        {
          path: 'data-process',
          component: () => import('./views/profiling/data-process.vue'),
        },
        {
          path: 'memory-detail',
          component: () => import('./views/profiling/memory-detail.vue'),
        },
      ],
    },
    {
      path: '/profiling-gpu',
      component: () => import('./views/profiling-gpu/profiling.vue'),
      redirect: '/profiling-gpu/profiling-dashboard',
      children: [
        {
          path: 'profiling-dashboard',
          component: () =>
            import('./views/profiling-gpu/profiling-dashboard.vue'),
        },
        {
          path: 'data-process',
          component: () => import('./views/profiling/data-process.vue'),
        },
        {
          path: 'operator',
          component: () => import('./views/profiling-gpu/operator.vue'),
        },
        {
          path: 'step-trace',
          component: () => import('./views/profiling/step-trace.vue'),
        },
      ],
    },
    {
      path: '/debugger',
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
      component: () =>
        import('./views/explain/conterfactual-interpretation.vue'),
    },
    {
      path: '/explain/xai-metric',
      component: () => import('./views/explain/xai-metric.vue'),
    },
  ],
});

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
import Vue from 'vue';
import App from './app.vue';
import router from './router';
import store from './store';

import ElementUI from 'element-ui';
import './assets/css/element.css';
import './assets/css/reset.scss';
import i18n from './i18n';
import $ from 'jquery';
import locale from 'element-ui/lib/locale/lang/en';
import localezh from 'element-ui/lib/locale/lang/zh-CN';

if (
  localStorage.getItem('milang') &&
  localStorage.getItem('milang') !== 'zh-cn'
) {
  Vue.use(ElementUI, {locale});
} else {
  Vue.use(ElementUI, {localezh});
}
window.$ = window.jQuery = $;

Vue.prototype.$bus = new Vue();

// Route interception
router.beforeEach((to, from, next) => {
  // cancel request
  if (from.path !== '/') {
    store.commit('clearToken');
  }

  // deter refresh
  store.commit('setIsReload', false);
  next();
});
router.onError((error) => {
  Vue.prototype.$message.error(i18n.messages[i18n.locale].public.netWorkError);
});

// forbidden showing production tip
Vue.config.productionTip = false;

/**
 * Check the browser version
 * @return {Boolen}
 */
function isBrowserSupport() {
  const isChrome = navigator.userAgent.toLowerCase().match(/chrome/);
  const isEdge = navigator.userAgent.toLowerCase().match(/edge/);

  if (!isChrome || isEdge) {
    return true;
  } else {
    const arr = navigator.userAgent.split(' ');
    let chromeVersion = '';
    for (let i = 0; i < arr.length; i++) {
      if (/chrome/i.test(arr[i])) chromeVersion = arr[i];
    }
    chromeVersion = Number(chromeVersion.split('/')[1].split('.')[0]);
    if (chromeVersion < 65) {
      return true;
    }
    return false;
  }
}

window.onload = function(e) {
  if (isBrowserSupport()) {
    Vue.prototype.$warmBrowser = true;
  }
  // Instantiation
  setTimeout(() => {
    new Vue({
      router,
      store,
      i18n,
      render: (h) => h(App),
    }).$mount('#app');
  }, 100);
};

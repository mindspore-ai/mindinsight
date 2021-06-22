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
import App from './app.vue';
import router from './router';
import store from './store';

import ElementUI from 'element-ui';
import './assets/css/element.css';
import './assets/css/reset.css';
import './assets/css/theme-config.css';
import i18n from './i18n';
import $ from 'jquery';
import locale from 'element-ui/lib/locale/lang/en';
import localezh from 'element-ui/lib/locale/lang/zh-CN';
import {basePath} from '@/services/fetcher';
import CommonProperty from './common/common-property';

let language = window.localStorage.getItem('milang');
const languageList = ['zh-cn', 'en-us'];
if (!language) {
  let tempLang = navigator.language || navigator.userLanguage;
  tempLang = tempLang.substr(0, 2);
  if (tempLang === 'zh') {
    language = languageList[0];
  } else {
    language = languageList[1];
  }
  window.localStorage.setItem('milang', language);
} else {
  if (!languageList.includes(language)) {
    // set English if no default language
    language = languageList[1];
    window.localStorage.setItem('milang', language);
  }
}
store.commit('setLanguage', language);

if (language !== languageList[0]) {
  Vue.use(ElementUI, {locale});
} else {
  Vue.use(ElementUI, {localezh});
}
window.$ = window.jQuery = $;

Vue.prototype.$bus = new Vue();

// theme color
let themeIndex = localStorage.getItem('miTheme');
if (!['0', '1'].includes(themeIndex)) {
  themeIndex = '0';
}
store.commit('setThemeIndex', themeIndex);
initThemeColor(themeIndex);

// Route interception
router.beforeEach((to, from, next) => {
  if (!window.enableDebugger && to.path === '/debugger') {
    next('/');
    return;
  }
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
 * @return {Boolean}
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
/**
 * Instantiate App
 */
function appInstantiation() {
  setTimeout(() => {
    new Vue({
      router,
      store,
      i18n,
      render: (h) => h(App),
    }).$mount('#app');
  }, 100);
}
/**
 * Init theme color
 * @param {String} colorIndex color index
 */
function initThemeColor(colorIndex) {
  let colorArr = [];
  if (!colorIndex) {
    colorArr = CommonProperty.themes['0'];
  } else {
    colorArr = CommonProperty.themes[colorIndex];
  }
  setThemeColor(colorArr);
}
/**
 * Set theme color
 * @param {Array} colorArr color arr
 */
function setThemeColor(colorArr) {
  if (colorArr.length) {
    for (let i = 0; i < colorArr.length; i++) {
      const tempItem = colorArr[i];
      document.documentElement.style.setProperty(tempItem.key, tempItem.value);
    }
  }
}

window.enableDebugger = true;
window.onload = function(e) {
  if (isBrowserSupport()) {
    Vue.prototype.$warmBrowser = true;
  }
  $.ajax({
    url: `${basePath}v1/mindinsight/ui-config`,
    type: 'GET',
    dataType: 'json',
    success: (data) => {
      if (data) {
        window.enableDebugger = data.enable_debugger;
      }
      appInstantiation();
    },
    error: () => {
      appInstantiation();
    },
  });
};

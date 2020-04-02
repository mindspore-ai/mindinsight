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
import router from '@/router';
import store from '@/store';
import i18n from '@/i18n';
import axios from 'axios';
import Vue from 'vue';

export {default} from 'axios';
export const basePath = location.origin;

axios.defaults.timeout = 30000;
axios.defaults.baseURL = basePath;
axios.interceptors.request.use(
    function(config) {
      config.headers['Pragma'] = 'no-cache';
      config.headers['Cache-Control'] = 'no-cache,no-store,must-revalidate';
      config.cancelToken = new axios.CancelToken((cancel) => {
        store.commit('pushToken', {
          cancelToken: cancel,
        });
      });
      return config;
    },
    function(error) {
      return Promise.reject(error);
    },
);

// Add a response interceptor
axios.interceptors.response.use(
    function(response) {
      return response;
    },
    function(error) {
      const errorData = i18n.messages[i18n.locale].error;

      // error returned by backend
      if (error.response && error.response.data && error.response.data.error_code) {
        if (error.response.data.error_code.toString() === '50540005' ||
        error.response.data.error_code.toString() === '50545006') {
          if (error.config.headers.ignoreError ||
            router.currentRoute.path === '/train-manage/training-dashboard') {
            return Promise.reject(error);
          }
        } else if ( error.response.data.error_code.toString() === '50542216' &&
        router.currentRoute.path === '/train-manage/training-dashboard') {
          return Promise.reject(error);
        }
        if (errorData[error.response.data.error_code]) {
          Vue.prototype.$message.error(errorData[error.response.data.error_code]);
        }
        return Promise.reject(error);
      } else {
      // error returned by browser
        if (error.code === 'ECONNABORTED' && /^timeout/.test(error.message)) {
          if (error.config.headers.ignoreError) {
            return Promise.reject(error);
          }
          // timeout processing
          Vue.prototype.$message.error(i18n.messages[i18n.locale].public.timeout);
          return Promise.reject(error);
        } else if (error.message === 'routeJump') {
        // route jump
          return false;
        } else {
        // show network error
          Vue.prototype.$message.error(
              i18n.messages[i18n.locale].public.netWorkError,
          );
          return Promise.reject(error);
        }
      }
      store.commit('setIsReload', false);
    },
);

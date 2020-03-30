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
const path = require('path');

/**
 * @param {String} dir
 * @return {String}
 */
function resolve(dir) {
  return path.join(__dirname, dir);
}

module.exports = {
  publicPath: process.env.NODE_ENV === 'production' ? './' : '/',
  outputDir: 'dist',
  assetsDir: 'static',

  // map
  productionSourceMap: false,

  configureWebpack: {
    devtool: 'source-map',
  },

  chainWebpack: (config) => {
    config.resolve.alias.set('@', resolve('src'));

    config.plugins.delete('preload');
    config.plugins.delete('prefetch');
    config.module
        .rule('element-ui')
        .test(/element-ui.src.*?js$/)
        .use('babel')
        .loader('babel-loader')
        .end();
  },

  devServer: {
    port: 8086,
    disableHostCheck: true,
  },

  pluginOptions: {
    i18n: {
      locale: 'zh-cn',
      fallbackLocale: 'zh-cn',
      localeDir: 'locales',
      enableInSFC: true,
    },
  },
  css: {
    loaderOptions: {
      sass: {
        prependData: `
          @import "@/assets/css/variable.scss";
        `,
      },
    },
  },
};

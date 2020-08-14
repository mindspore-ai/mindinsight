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
import VueI18n from 'vue-i18n';

Vue.use(VueI18n);

/**
 * return language package
 * @return {object}
 */
function loadLocaleMessages() {
  const locales = require.context('./locales', true, /[A-Za-z0-9-_,\s]+\.json$/i);

  const messages = {};
  locales.keys().forEach((key) => {
    const matched = key.match(/([A-Za-z0-9-_]+)\./i);
    if (matched && matched.length > 1) {
      const locale = matched[1];
      messages[locale] = locales(key);
    }
  });
  return messages;
}

/* load default language pack */
const languageList = ['zh-cn', 'en-us'];
const langStorge = window.localStorage.getItem('milang');
let langflag;
// Check language by default
if (langStorge && languageList.includes(langStorge)) {
  langflag = langStorge;
} else {
  // set Chinese if no default language
  langflag = languageList[0];
  window.localStorage.setItem('milang', langflag);
}

export default new VueI18n({
  locale: langflag,
  fallbackLocale: langflag,
  messages: loadLocaleMessages(),
});

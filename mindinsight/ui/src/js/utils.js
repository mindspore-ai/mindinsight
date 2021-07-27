/**
 * Copyright 2021 Huawei Technologies Co., Ltd.All Rights Reserved.
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

/**
 * The function of keep decimal places when the length of decimal digit is greater than param 'length'
 * @param {number | string} number
 * @param {number} length
 * @return {string} String with fixed decimal places
 */
export function keepDecimalPlaces(number, length) {
  if (typeof number !== 'number') {
    number = parseFloat(number);
  }
  if (isNaN(number)) {
    return 'NaN';
  }
  const numberStr = number + '';
  const decimalPointIndex = numberStr.indexOf('.');
  // Not float or the length of decimal digit is not greater than param 'length'
  return decimalPointIndex < 0 || numberStr.length - decimalPointIndex - 1 <= length
    ? numberStr
    : number.toFixed(length);
}

/**
 * The function of judge whether the target is an integer
 * @param {string | number} target
 * @return {boolean} If target is integer number
 */
export function isInteger(target) {
  if (Number.isInteger(target)) {
    return true;
  }
  if (typeof target !== 'string') {
    return false;
  }
  const numberTarget = +target;
  return numberTarget + '' === target && Number.isInteger(numberTarget);
}

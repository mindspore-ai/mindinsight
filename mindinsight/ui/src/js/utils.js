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
 * Calculate gradient color
 * @param {String} startColor
 * @param {String} endColor
 * @param {Number} step
 * @return {Array} Array of gradient color
 */
export function getGradientColor(startColor, endColor, step) {
  if (!startColor.toLowerCase().includes('rgb')) {
    startColor = formatHexColorToRgb(startColor);
  }
  if (!endColor.toLowerCase().includes('rgb')) {
    endColor = formatHexColorToRgb(endColor);
  }
  const [startRed, startGreen, startBlue] = startColor.match(/[0-9]\d*/g);
  const [endRed, endGreen, endBlue] = endColor.match(/[0-9]\d*/g);
  const gapRgbR = (+endRed - (+startRed)) / step;
  const gapRgbG = (+endGreen - (+startGreen)) / step;
  const gapRgbB = (+endBlue - (+startBlue)) / step;
  const colorResult = [startColor];
  for (let i = 1; i < step; i++) {
    const sR = parseInt(gapRgbR * i + (+startRed));
    const sG = parseInt(gapRgbG * i + (+startGreen));
    const sB = parseInt(gapRgbB * i + (+startBlue));
    colorResult.push(`rgb(${sR},${sG},${sB})`);
  }
  return colorResult;
}

/**
 * Converts a color string to recognizable format
 * @param {String} str Color string
 * @return {Array} Value of RGB
 */
export function formatHexColorToRgb(str) {
  const hex = 16;
  if (str.length === 4) {
    // Example: #000
    return `rgb(${
      parseInt(str[1] + str[1], hex)}, ${parseInt(str[2] + str[2], hex)}, ${parseInt(str[3] + str[3], hex)
    })`;
  } else {
    // Example: #000000
    return `rgb(${
      parseInt(str[1] + str[2], hex)}, ${parseInt(str[3] + str[4], hex)}, ${parseInt(str[5] + str[6], hex)
    })`;
  }
}

/**
 * Converts rgb color string to hex
 * @param {String} rgb Rgb color
 * @return {String} Hex color
 */
export function formatRgbColorToHex(rgb) {
  const [red, green, blue] = rgb.match(/[0-9]\d*/g);
  // 16: RGB color conversion to hexadecimal
  return `#${(+red).toString(16)}${(+green).toString(16)}${(+blue).toString(16)}`;
}

/**
 * The function to keep decimal places when the length of decimal digit is greater than param 'length'
 * @param {number | string} number
 * @param {number} length
 * @return {string}
 */
export function keepDecimalPlaces(number, length) {
  if (typeof number !== 'number') number = parseFloat(number);
  if (isNaN(number)) return 'NaN';
  const numberStr = number + '';
  const decimalPointIndex = numberStr.indexOf('.');
  // Not float or the length of decimal digit is not greater than param 'length'
  return decimalPointIndex < 0 || numberStr.length - decimalPointIndex - 1 <= length
    ? numberStr
    : number.toFixed(length);
}

/**
 * The function to judge whether the target is an integer
 * @param {string | number} target
 * @return {boolean}
 */
export function isInteger(target) {
  if (Number.isInteger(target)) return true;
  if (typeof target !== 'string') return false;
  const numberTarget = +target;
  return numberTarget + '' === target && Number.isInteger(numberTarget);
}


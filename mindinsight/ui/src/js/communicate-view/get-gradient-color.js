/**
 * Copyright 2022 Huawei Technologies Co., Ltd.All Rights Reserved.
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
 * Get the color corresponding to the value in the gradient color card
 * @param {String} startColor start of the gradient color card(like "#ffffff")
 * @param {String} endColor end of the gradient color card
 * @param {Number} minValue value corresponding to startColor
 * @param {Number} maxValue value corresponding to endColor
 * @param {Number} value target value to get the corresponding color
 * @return {String} color like "#ffffff"
 */
export function gradientColor(startColor, endColor, minValue, maxValue, value) {
  var startR = parseInt(startColor.substring(1, 3), 16);
  var startG = parseInt(startColor.substring(3, 5), 16);
  var startB = parseInt(startColor.substring(5), 16);

  var endR = parseInt(endColor.substring(1, 3), 16);
  var endG = parseInt(endColor.substring(3, 5), 16);
  var endB = parseInt(endColor.substring(5), 16);
  var sR = Math.round(
    ((value - minValue) / (maxValue - minValue)) * (endR - startR) + startR
  );
  var sG = Math.round(
    ((value - minValue) / (maxValue - minValue)) * (endG - startG) + startG
  );
  var sB = Math.round(
    ((value - minValue) / (maxValue - minValue)) * (endB - startB) + startB
  );

  return "#" + sR.toString(16) + sG.toString(16) + sB.toString(16);
}

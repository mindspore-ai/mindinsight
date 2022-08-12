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
 * @param {Array} data
 * @param {Number} threshold
 * @return {Array}
 */
function mergeNearbyRects(data, threshold) {
  const mergedData = [data[0]];
  for (let i = 1; i < data.length; i++) {
    const pre = mergedData[mergedData.length - 1];
    const cur = data[i];

    const {x1: a1, x2: a2, y: aY, type: aType} = pre;
    const {x1: b1, x2: b2, y: bY, type: bType} = cur;
    // skip different type、stage
    if (
      aY === bY &&
      checkSegment(a1, a2, b1, b2, threshold) &&
      aType === bType
    ) {
      pre.x1 = Math.min(a1, b1);
      pre.x2 = Math.max(a2, b2);
      pre.op = pre.op + '\n'+cur.op;
      mergedData[mergedData.length - 1] = pre;
    } else {
      mergedData.push(cur);
    }
  }

  return mergedData;
}

/**
 * @param {*} data
 * @param {*} threshold
 * @return {Array}
 */
function mergeNearbyGap(data, threshold) {
  const mergedData = [data[0]];

  for (let i = 1; i < data.length; i++) {
    const pre = mergedData[mergedData.length - 1];
    const cur = data[i];

    if (checkGapConnected(pre, cur, threshold)) {
      pre.x1 = Math.min(pre.x1, cur.x1);
      pre.x2 = Math.max(pre.x2, cur.x2);
      pre.x3 = Math.min(pre.x3, cur.x3),
      pre.x4 = Math.max(pre.x4, cur.x4);
      pre.op = pre.op + ','+cur.op;
      mergedData[mergedData.length - 1] = pre;
    } else {
      mergedData.push(cur);
    }
  }

  return mergedData;
}

/**
 * @param {*} a1
 * @param {*} a2
 * @param {*} b1
 * @param {*} b2
 * @param {*} threshold
 * @return {boolean}
 */
function checkSegment(a1, a2, b1, b2, threshold) {
  if (
    Math.max(a1, b1) < Math.min(a2, b2) ||
    (b1 > a2 && b1 - a2 <= threshold) ||
    (a1 > b2 && a1 - b2 <= threshold)
  ) {
    return true;
  } else {
    return false;
  }
}

/**
 * @param {Object} a
 * @param {Object} b
 * @param {number} threshold
 * @return {boolean}
 */
function checkGapConnected(a, b, threshold) {
  if (a.type !== b.type) {
    return false;
  }

  const {x1: a1, x2: a2, y1: aY1, y2: aY2, x3: a3, x4: a4} = a;
  const {x1: b1, x2: b2, y1: bY1, y2: bY2, x3: b3, x4: b4} = b;

  if (aY1 !== bY1 || aY2 !== bY2) {
    return false;
  }

  if (checkSegment(a1, a2, b1, b2, threshold) && checkSegment(a3, a4, b3, b4, threshold)) {
    return true;
  } else {
    return false;
  }
}


export {
  mergeNearbyRects,
  mergeNearbyGap,
};

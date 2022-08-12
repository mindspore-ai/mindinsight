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
function index(d) {
  return d.index;
}

function find(nodeById, nodeId) {
  const node = nodeById.get(nodeId);
  if (!node) throw new Error('node not found: ' + nodeId);
  return node;
}

export default function(links) {
  const id = index;
  const strength = defaultStrength;
  let strengths;
  const distance = () => 30;
  let distances;
  let nodes;
  let count;
  let bias;
  let random;
  const iterations = 1;

  if (links == null) links = [];

  function defaultStrength(link) {
    return 1 / Math.min(count[link.source.index], count[link.target.index]);
  }

  function force(alpha) {
    for (let k = 0, n = links.length; k < iterations; ++k) {
      for (let i = 0, link, source, target, x, y, b; i < n; ++i) {
        (link = links[i]), (source = link.source), (target = link.target);
        // console.log(target.x);
        x = target.x + target.vx - source.x - source.vx;
        y = target.y + target.vy - source.y - source.vy;
        let xdiff = x - distances[i];
        const timeDiff = Number(target.order) - Number(source.order);
        if (xdiff > 0) {
          // x = 0
          x = (xdiff * alpha * strengths[i]) / Math.pow(timeDiff, 2);
        } else {
          if (xdiff > -20) xdiff = -20;
          x = xdiff * Math.pow(timeDiff, 2) * alpha * strengths[i];
        }
        x = x > 100 ? 100 : x;
        x = x < -100 ? -100 : x;
        const ydiff = y;
        y = ydiff * alpha * strengths[i];
        y = y > 100 ? 100 : y;
        y = y < -100 ? -100 : y;
        target.vx -= x;
        target.vy -= y;
        source.vx += x;
        source.vy += y;
      }
    }
  }

  function initialize() {
    if (!nodes) return;

    let i;
    const n = nodes.length;
    const m = links.length;
    const nodeById = new Map(nodes.map((d, i) => [id(d, i, nodes), d]));
    let link;

    for (i = 0, count = new Array(n); i < m; ++i) {
      (link = links[i]), (link.index = i);
      if (typeof link.source !== 'object') {
        link.source = find(nodeById, link.source);
      }
      if (typeof link.target !== 'object') {
        link.target = find(nodeById, link.target);
      }
      count[link.source.index] = (count[link.source.index] || 0) + 1;
      count[link.target.index] = (count[link.target.index] || 0) + 1;
    }

    for (i = 0, bias = new Array(m); i < m; ++i) {
      (link = links[i]),
      (bias[i] =
          count[link.source.index] /
          (count[link.source.index] + count[link.target.index]));
    }

    (strengths = new Array(m)), initializeStrength();
    (distances = new Array(m)), initializeDistance();
  }

  function initializeStrength() {
    if (!nodes) return;

    for (let i = 0, n = links.length; i < n; ++i) {
      strengths[i] = +strength(links[i], i, links);
    }
  }

  function initializeDistance() {
    if (!nodes) return;

    for (let i = 0, n = links.length; i < n; ++i) {
      distances[i] = +distance(links[i], i, links);
      const link = links[i];
      const {source, target} = link;
      if (
        (source.type === 'Conv2D' && target.type === 'ReLU') ||
        (source.type === 'ReLU' && target.type === 'MaxPool')
      ) {
        distances[i] = 1;
        strengths[i] = 5;
      }
    }
  }

  force.initialize = function(_nodes, _random) {
    nodes = _nodes;
    random = _random;
    initialize();
  };

  return force;
}

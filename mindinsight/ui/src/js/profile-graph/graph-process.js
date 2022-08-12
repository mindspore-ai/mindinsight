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
import {specialEdgesDef} from '@/js/profile-graph/edge-process.js';

const BIG_PRIMITIVE = 10000019;

export function extractVisNodeAndEdge(nodeMap) {
  const {allEdges, opNodes} = _getNodeAndEdgeFromNodeMap(nodeMap);
  const {specialEdges, normalEdges, normalEdgesBackup} = _getNormalEdgeAndSpecialEdge(allEdges, nodeMap);

  const newData = _stackIsomorphicSubgraph(specialEdges, normalEdges, opNodes, nodeMap);

  return [normalEdgesBackup, newData];
}

function _getNodeAndEdgeFromNodeMap(nodeMap) {
  const allEdges = [];
  const opNodes = Object.values(nodeMap);
  const idToIndex = {};
  opNodes.forEach((v, i) => {
    idToIndex[v.id] = i;
  });
  opNodes.forEach((v, i) => {
    v.input.forEach((preId) => {
      if (nodeMap[preId]) {
        allEdges.push({
          source: opNodes[idToIndex[preId]],
          target: opNodes[idToIndex[v.id]],
          iterations: 5,
        });
      }
    });
  });
  return {allEdges, opNodes};
}


function _getNormalEdgeAndSpecialEdge(allEdges, nodeMap) {
  const normalEdges = [];
  const normalEdgesBackup = [];
  const specialEdges = {};
  specialEdgesDef.forEach((v) => {
    specialEdges[v.class] = {
      values: [],
      display: v.defaultDisplay,
      path: v.path,
    };
  });

  for (const edge of allEdges) {
    const {source, target} = edge;
    const [sNode, tNode] = [source, target];
    const isNormalEdge = true;
    for (const def of specialEdgesDef) {
      if (def.condition(sNode, tNode, nodeMap)) {
        isNormalEdge = false;
        specialEdges[def.class].values.push(edge);
        break;
      }
    }
    if (isNormalEdge) {
      normalEdges.push(edge);
      normalEdgesBackup.push(`${edge.source.id}-${edge.target.id}`);
    }
  }
  return {normalEdges, normalEdgesBackup, specialEdges};
}


function _stackIsomorphicSubgraph(specialEdges, normalEdges, opNodes, nodeMap) {
  const subgraphs = _subgraphDetect(normalEdges, opNodes);
  const isomorphicSubgraphs = _detectIsomorphicSubgraphs(subgraphs);
  const newData = _aggreSubgraphs(specialEdges, normalEdges, opNodes, isomorphicSubgraphs, nodeMap);
  return newData;
}

function _aggreSubgraphs(specialEdges, normalEdges, opNodes, isomorphicSubgraphs, nodeMap) {
  const obj2index = new Map();
  opNodes.forEach((v, i) => {
    obj2index.set(v, i);
  });
  const templateNodes = new Set();
  const node2aggreNode = new Map();
  for (const subgraphs of isomorphicSubgraphs) {
    const aggreNodes = [];

    subgraphs.forEach((subgraph, i) => {
      if (i === 0) {
        Array.from(subgraph).forEach((node, j) => {
          const aggreNode = Object.assign({}, node);
          aggreNode.id = aggreNode.id + '_aggre';
          aggreNodes.push(aggreNode);
          opNodes[obj2index.get(node)] = aggreNode;
          aggreNode.isAggreNode = true;
          aggreNode.aggreNodes = aggreNodes;
          aggreNode.contain = [node];
          node2aggreNode.set(node, aggreNode);
          templateNodes.add(node);
          nodeMap[aggreNode.id] = aggreNode;
        });
      } else {
        Array.from(subgraph).forEach((node, j) => {
          const aggreNode = aggreNodes[j];
          aggreNode.contain.push(node);
          node2aggreNode.set(node, aggreNode);
        });
      }
    });
  }
  const nodeToDelete = new Set(node2aggreNode.keys());
  const normalEdgesToDelete = new Set();
  for (const edge of normalEdges) {
    if (templateNodes.has(edge.source)) {
      edge.source = node2aggreNode.get(edge.source);
      edge.target = node2aggreNode.get(edge.target);
    } else if (nodeToDelete.has(edge.source) || nodeToDelete.has(edge.target)) {
      normalEdgesToDelete.add(edge);
    }
  }

  for (const edges of Object.values(specialEdges)) {
    const spEdgeToDelate = new Set();
    for (const e of edges.values) {
      if (nodeToDelete.has(e.target) || nodeToDelete.has(e.source)) {
        spEdgeToDelate.add(e);
      }
    }
    edges.values = edges.values.filter((v) => !spEdgeToDelate.has(v));
  }

  opNodes = opNodes.filter((v) => !nodeToDelete.has(v));
  normalEdges = normalEdges.filter((v) => !nodeToDelete.has(v));

  return {specialEdges, normalEdges, opNodes};
}

function _subgraphDetect(normalEdges, opNodes) {
  const subgraphs = [];
  const unvisitedNodes = new Set(opNodes);
  const undirectedEdges = new Map();
  for (const normalEdge of normalEdges) {
    if (undirectedEdges.has(normalEdge.source)) {
      undirectedEdges.get(normalEdge.source).push(normalEdge.target);
    } else {
      undirectedEdges.set(normalEdge.source, [normalEdge.target]);
    }
    if (undirectedEdges.has(normalEdge.target)) {
      undirectedEdges.get(normalEdge.target).push(normalEdge.source);
    } else {
      undirectedEdges.set(normalEdge.target, [normalEdge.source]);
    }
  }

  while (unvisitedNodes.size > 0) {
    const subgraph = new Set();
    let node = Array.from(unvisitedNodes)[0];
    unvisitedNodes.delete(node);
    subgraph.add(node);
    const stack = [node];
    while (stack.length) {
      node = stack.pop();
      if (undirectedEdges.has(node)) {
        for (const next of undirectedEdges.get(node)) {
          if (unvisitedNodes.has(next)) {
            unvisitedNodes.delete(next);
            subgraph.add(next);
            stack.push(next);
          }
        }
      }
    }
    if (subgraph.size > 1) {
      subgraphs.push(subgraph);
    }
  }
  return subgraphs;
}

function _detectIsomorphicSubgraphs(subgraphs) {
  const hashMap = {};
  const REPEAT_THRESHOLD = 5;
  for (const subgraph of subgraphs) {
    const hash = _genHashForSubgraph(subgraph);
    if (hashMap[hash]) {
      hashMap[hash].push(subgraph);
    } else {
      hashMap[hash] = [subgraph];
    }
  }
  return Object.values(hashMap).filter((v) => v.length >= REPEAT_THRESHOLD);
}

function _genHashForSubgraph(subgraph) {
  let hash = 0;
  for (const node of Array.from(subgraph)) {
    hash += _genHash(node.type);
    hash %= BIG_PRIMITIVE;
  }
  return hash;
}

function _genHash(str) {
  let hash = 5381;
  str = str || '';

  for (let i = 0, len = str.length; i < len; ++i) {
    hash += (hash << 5) + str.charCodeAt(i);
  }
  const ret = hash & 0x7fffffff;
  return ret;
}

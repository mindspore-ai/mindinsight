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
import {
  INSERTED_ATTR,
  NODE_TYPE,
  EDGE_SEPARATOR,
} from './const';
import {showNodeType} from './build-graph';

// communication oeperator
const COMM_LIST = new Set([
  'AllReduce',
  'AllGather',
  'AllToAll',
  'ReduceScatter',
]);
let processedGraph = {};

/**
 * Construct communication and computation bipartite.
 * @param {Object} nodeMap nodeMap
 * @param {Object} cutEdges edges to cut
 * @return {Object}
 */
function processBipartite(nodeMap, cutEdges = null) {
  Object.keys(nodeMap).forEach((nodeid) => {
    const node = nodeMap[nodeid];
    if (COMM_LIST.has(node.type) && node.scope.startsWith(showNodeType)) {
      // Traverse from the comm node as the source node
      let v = [];
      const preNxtNodeDict = {
        pre: new Set(),
        nxt: new Set(),
      };
      let q = [nodeid];
      v[nodeid] = true;
      while (q.length) {
        const cur = q.shift();
        const curNode = nodeMap[cur];
        for (const nxtId of curNode.input) {
          // find nodes backward
          if (cutEdges.has(nxtId + EDGE_SEPARATOR + cur) || !nodeMap[nxtId]) continue;
          if (!v[nxtId]) {
            preNxtNodeDict['pre'].add(nxtId);
            v[nxtId] = true;
            q.push(nxtId);
          }
        }
      }
      v = [];
      q = [nodeid];
      v[nodeid] = true;
      while (q.length) {
        const cur = q.shift();
        const curNode = nodeMap[cur];
        for (const nxtId of curNode.output) {
          // find nodes forward
          if (cutEdges.has(cur + EDGE_SEPARATOR + nxtId)) continue;
          if (!v[nxtId]) {
            preNxtNodeDict['nxt'].add(nxtId);
            v[nxtId] = true;
            q.push(nxtId);
          }
        }
      }
      v = [];
      q = [];
      for (const id of preNxtNodeDict['pre']) {
        if (
          COMM_LIST.has(nodeMap[id].type) &&
            nodeMap[id].scope.startsWith(showNodeType)
        ) {
          continue;
        }
        v[id] = true;
        q.push(id);
      }
      while (q.length) {
        const cur = q.shift();
        const curNode = nodeMap[cur];
        for (const nxtId of curNode.output) {
          if (cutEdges.has(cur + EDGE_SEPARATOR + nxtId)) continue;
          if (
            COMM_LIST.has(nodeMap[nxtId].type) &&
              nodeMap[nxtId].scope.startsWith(showNodeType)
          ) {
            continue;
          }
          if (!v[nxtId]) {
            if (preNxtNodeDict['nxt'].has(nxtId)) {
              cutEdges.add(cur + EDGE_SEPARATOR + nxtId); // cut the cross-comm edges
            } else {
              v[nxtId] = true;
              q.push(nxtId);
            }
          }
        }
        for (const nxtId of curNode.input) {
          if (cutEdges.has(nxtId + EDGE_SEPARATOR + cur)) continue;
          if (
            !nodeMap[nxtId] ||
              (COMM_LIST.has(nodeMap[nxtId].type) &&
                nodeMap[nxtId].scope.startsWith(showNodeType))
          ) {
            continue;
          }
          if (!v[nxtId]) {
            if (preNxtNodeDict['nxt'].has(nxtId)) {
              cutEdges.add(cur + EDGE_SEPARATOR + nxtId); // cut the cross-comm edges
            } else {
              v[nxtId] = true;
              q.push(nxtId);
            }
          }
        }
      }
    }
  });
  const v = [];
  const components = [];
  for (const key in nodeMap) {
    if (nodeMap.hasOwnProperty(key)) {
      const node = nodeMap[key];
      if (
        !isNaN(key) &&
        !v[key] &&
        !(COMM_LIST.has(node.type) && node.scope.startsWith(showNodeType))
      ) {
        const curConnectedComponent = [];
        curConnectedComponent.push(key);
        v[key] = true;
        const queue = [key];
        while (queue.length) {
          const cur = queue.shift();
          for (const nid of nodeMap[cur].output) {
            if (cutEdges.has(cur + EDGE_SEPARATOR + nid)) continue;
            if (
              !v[nid] &&
              !(
                COMM_LIST.has(nodeMap[nid].type) &&
                nodeMap[nid].scope.startsWith(showNodeType)
              )
            ) {
              curConnectedComponent.push(nid);
              queue.push(nid);
              v[nid] = true;
            }
          }
          for (const nid of nodeMap[cur].input) {
            if (!nodeMap[nid]) continue;
            if (cutEdges.has(nid + EDGE_SEPARATOR + cur)) continue;
            if (
              !v[nid] &&
              !(
                COMM_LIST.has(nodeMap[nid].type) &&
                nodeMap[nid].scope.startsWith(showNodeType)
              )
            ) {
              curConnectedComponent.push(nid);
              queue.push(nid);
              v[nid] = true;
            }
          }
        }
        components.push(curConnectedComponent);
      }
    }
  }
  return {components: components, cutEdges: cutEdges};
}

/**
 * get the product of all elements in an array
 * @param {Array<Number>} arr
 * @return {Number}
 */
function getProduct(arr) {
  return arr.reduce((prev, cur) => prev * cur);
}

/**
 * check whether the shard method is valid
 * @param {Array|undefined} value
 * @return {boolean}
 */
function _checkShardMethod(value) {
  return value !== undefined && value.length > 0;
}

const _nodesExtraAttributesMap = {};

/**
 * Class representing extra attributes
 */
class ExtraAttr {
  /**
   * constructor
   * @param {Object} node
   * @param {String} type
   */
  constructor(node, type) {
    if (this[type]) {
      this[type](node);
    }
  }

  /**
   * assign the type of the node
   * @param {Object} node
   */
  instanceType(node) {
    this.type = node[INSERTED_ATTR.instance_type];
  }

  /**
   * get data for strategy matrix
   * @param {Object} node
   */
  shardStrategy(node) {
    const {nodeMap} = processedGraph;
    let shard = node[INSERTED_ATTR.parallel_shard];
    if (typeof shard === 'string') {
      shard = JSON.parse(shard);
    }
    this.strategy = shard
        .map((arr, i) => {
          const input = node.input[i];
          if (!arr.length) return null; // skip when the matrix is empty
          if (getProduct(arr) === 1) return null; // skip when only one piece
          // ignore const and parameters
          if (nodeMap[input] === undefined) return null;

          return {
            strategy: arr,
            name: input,
          };
        })
        .filter((d) => d !== null);
  }
  /**
   * change strategy array to string.
   * @return {string}
   */
  getStrategy() {
    return this.strategy.map(({strategy}) => strategy.join(','));
  }
}

/**
 * handle displayed attributes
 * @param {string} nodeId
 */
function handleDisplayedAttr(nodeId) {
  const {nodeMap, root} = processedGraph;
  const node = nodeMap[nodeId] || root;

  const nodeSet = new Set();

  const nodeStack = [node];
  while (nodeStack.length > 0) {
    const curNode = nodeStack.pop();

    // ignore basic nodes
    if (curNode.type in NODE_TYPE || nodeId===undefined) {
      for (const childId of curNode.children) {
        const childNode = nodeMap[childId];

        if (childNode.expanded === true) {
          nodeStack.push(childNode);
        } else if (
          NODE_TYPE[childNode.type] === undefined &&
          _checkShardMethod(childNode[INSERTED_ATTR.parallel_shard])
        ) {
          // ignore compound nodes not been expanded
          nodeSet.add(childId);
        }

        if (childNode[INSERTED_ATTR.instance_type]&&childNode[INSERTED_ATTR.instance_type]!=='') {
          _nodesExtraAttributesMap[childId] = new ExtraAttr(childNode, 'instanceType');
        }
      }
    }
  }

  nodeSet.forEach((childId) => {
    _nodesExtraAttributesMap[childId] = new ExtraAttr(nodeMap[childId], 'shardStrategy');
  });
}

/**
 * using BFS as the searching algorithm in the residual graph
 * @param {Object} residualAllNodes nodes in the residual graph
 * @param {Object} residualAllEdges edges in the residual graph
 * @param {Number} source source
 * @param {Number} target target
 * @param {Array} parent store path
 * @return {Boolean} whether found a path from source to target
 */
function bfsInResidualGraph(residualAllNodes, residualAllEdges, source, target, parent) {
  const maxIterateCnt = 10;

  const isVisit = new Map();
  for (const residualNode of residualAllNodes) {
    isVisit.set(residualNode, false);
  }

  let curIterateCnt = 0;
  const queue = [];
  queue.push(source);
  isVisit.set(source, true);
  parent[source] = -1;

  while (queue.length !== 0) {
    if (curIterateCnt > maxIterateCnt && !isVisit.get(target)) {
      return false;
    }

    const top = queue[0];
    queue.shift();

    for (const residualNode of residualAllNodes) {
      if (!isVisit.get(residualNode) && residualAllEdges[top] && residualAllEdges[top][residualNode] > 0) {
        queue.push(residualNode);
        parent[residualNode] = top;
        isVisit.set(residualNode, true);
      }
    }

    curIterateCnt++;
  }

  return isVisit.get(target);
}

/**
 * the Ford-Fulkerson Algorithm
 * @param {Object} curAllNodes nodes
 * @param {Object} curAllEdges edges
 * @param {Number} source source
 * @param {Number} target target
 * @param {Object} nodeMap graph data
 * @return {Object} last residual graph and edge type set
 */
function fordFulkerson(curAllNodes, curAllEdges, source, target) {
  const residualAllNodes = curAllNodes;
  const residualAllEdges = JSON.parse(JSON.stringify(curAllEdges));

  const parent = {};
  curAllNodes.forEach((curNode) => {
    parent[curNode] = -1;
  });

  while (bfsInResidualGraph(residualAllNodes, residualAllEdges, source, target, parent)) {
    let pathFlow = Number.MAX_VALUE;
    for (let i = target; i !== source; i = parent[i]) {
      pathFlow = Math.min(pathFlow, residualAllEdges[parent[i]][i]);
    }

    for (let i = target; i !== source; i = parent[i]) {
      residualAllEdges[parent[i]][i] -= pathFlow;
      if (residualAllEdges[parent[i]][i] === 0) {
        delete residualAllEdges[parent[i]][i];
      }
      if (!(parent[i] in residualAllEdges[i])) {
        residualAllEdges[i][parent[i]] = 0;
      }
      residualAllEdges[i][parent[i]] += pathFlow;
    }
  }

  return {
    lastResidualEdges: residualAllEdges,
  };
}

/**
 * calculate minimum cut
 * @param {Number} source source node
 * @param {Number} target target node
 * @param {Object} residualAllNodes nodes in the final residual graph
 * @param {Object} residualAllEdges edges in the final residual graph
 * @param {Object} originAllEdges edges in the original graph
 * @return {Set} edges to cut
 */
function findCutEdges(source, target, residualAllNodes, residualAllEdges, originAllEdges) {
  const isVisit = new Map();
  for (const residualNode of residualAllNodes) {
    isVisit.set(residualNode, false);
  }

  const queue = [];
  queue.push(source);
  isVisit.set(source, true);

  const cutEdges = new Set();
  const firstNodeSet = new Set();
  const secondNodeSet = new Set();

  firstNodeSet.add(source);
  secondNodeSet.add(target);

  while (queue.length !== 0) {
    const top = queue[0];
    queue.shift();
    Object.keys(residualAllEdges[top]).forEach((id) => {
      if (!isVisit.get(id)) {
        firstNodeSet.add(id);
        queue.push(id);
        isVisit.set(id, true);
      }
    });
  }

  for (const node of residualAllNodes) {
    if (!firstNodeSet.has(node)) {
      secondNodeSet.add(node);
    }
  }

  for (const fromNode of firstNodeSet) {
    if (fromNode == source || fromNode == target) {
      continue;
    }
    Object.keys(originAllEdges[fromNode]).forEach((toNode) => {
      if (toNode == source || toNode == target) {
        return;
      }
      if (secondNodeSet.has(toNode)) {
        cutEdges.add(`${fromNode}->${toNode}`);
      }
    });
  }

  return cutEdges;
}

/**
 * using BFS to find all connected nodes
 * @param {Number} commNodeID communication node id
 * @param {Object} allNodes all nodes
 * @param {Object} nodeMap graph data
 * @return {Object} pre and next nodes
 */
function findRelateNodes(commNodeID, allNodes, nodeMap) {
  const maxIterateCnt = 5;

  const preNodes = new Set();
  const nextNodes = new Set();

  // find pre nodes
  let isVisit = new Map();
  for (const node of allNodes) {
    isVisit.set(node, false);
  }

  let curIterateCnt = 0;
  let queue = [];
  queue.push(commNodeID);
  isVisit.set(commNodeID, true);

  while (queue.length !== 0 && curIterateCnt <= maxIterateCnt) {
    const top = queue[0];
    queue.pop();

    nodeMap[top].input.forEach((inputID) => {
      if (!isVisit.get(inputID) && !isNaN(inputID) && !COMM_LIST.has(nodeMap[inputID].type)) {
        queue.push(inputID);
        preNodes.add(inputID);
        isVisit.set(inputID, true);
      }
    });

    curIterateCnt++;
  }

  // find next nodes
  isVisit = new Map();
  for (const node of allNodes) {
    isVisit.set(node, false);
  }
  curIterateCnt = 0;
  queue = [];
  queue.push(commNodeID);
  isVisit.set(commNodeID, true);

  while (queue.length !== 0 && curIterateCnt <= maxIterateCnt) {
    const top = queue[0];
    queue.pop();

    nodeMap[top].output.forEach((outputID) => {
      if (!isVisit.get(outputID) && !isNaN(outputID) && !COMM_LIST.has(nodeMap[outputID].type)) {
        queue.push(outputID);
        nextNodes.add(outputID);
        isVisit.set(outputID, true);
      }
    });

    curIterateCnt++;
  }

  return {
    preNodes: preNodes,
    nextNodes: nextNodes,
  };
}

/**
 * calculate minimum cut
 * @param {Object} nodeMap Graph data.
 * @return {Object} edges to cut
 */
function calcMinCut(nodeMap) {
  const allEdges = {};
  const allNodes = new Set();
  const commNodes = [];

  Object.keys(nodeMap).forEach((key) => {
    const node = nodeMap[key];
    if (isNaN(key)) {
      return;
    }
    if (COMM_LIST.has(node.type) && node.scope.indexOf(showNodeType) === 0) {
      commNodes.push(key);
      return;
    } else {
      allNodes.add(key);
      allEdges[key] = {};
    }
    node.input.forEach((inputID) => {
      const inputNode = nodeMap[inputID];
      if (!isNaN(inputID) && !COMM_LIST.has(inputNode.type)) {
        allNodes.add(inputID);
        if (!(inputID in allEdges)) {
          allEdges[inputID] = {};
        }
        allEdges[inputID][key] = 1;
      }
    });
    node.output.forEach((outputID) => {
      const outputNode = nodeMap[outputID];
      if (!isNaN(outputID) && !COMM_LIST.has(outputNode.type)) {
        allNodes.add(outputID);
        allEdges[key][outputID] = 1;
      }
    });
  });

  const MaxDepth = 5; // max depth of foreign structure
  const classifiedDict = {};
  const topoToCutEdgesDict = {};

  commNodes.forEach((id) => {
    const preTypeDict = {};
    const nxtTypeDict = {};

    let levDict = {};
    levDict[id] = 0;

    let q = [id];
    const nodesList = [parseInt(id)]; // sorted nodes for matching

    while (q.length) {
      const cur = q.shift();
      const curNode = nodeMap[cur];
      for (const preId of curNode.input) {
        if (!isNaN(preId) && !levDict.hasOwnProperty(preId) && levDict[cur] < MaxDepth) {
          const nxtNode = nodeMap[preId];
          levDict[preId] = levDict[cur] + 1;
          q.push(preId);
          nodesList.push(parseInt(preId));
          if (!preTypeDict.hasOwnProperty(nxtNode.type)) preTypeDict[nxtNode.type] = 1;
          else preTypeDict[nxtNode.type] = preTypeDict[nxtNode.type] + 1;
        }
      }
    }

    q = [id];
    levDict = {};
    levDict[id] = 0;

    while (q.length) {
      const cur = q.shift();
      const curNode = nodeMap[cur];
      for (const nxtId of curNode.output) {
        if (!isNaN(nxtId) && !levDict.hasOwnProperty(nxtId) && levDict[cur] < MaxDepth) {
          const nxtNode = nodeMap[nxtId];
          levDict[nxtId] = levDict[cur] + 1;
          q.push(nxtId);
          nodesList.push(parseInt(nxtId));
          if (!nxtTypeDict.hasOwnProperty(nxtNode.type)) nxtTypeDict[nxtNode.type] = 1;
          else nxtTypeDict[nxtNode.type] = nxtTypeDict[nxtNode.type] + 1;
        }
      }
    }
    const commTypeKey = JSON.stringify(preTypeDict) + JSON.stringify(nxtTypeDict);
    classifiedDict[id] = {};
    classifiedDict[id]['topo'] = commTypeKey;
    classifiedDict[id]['nodes'] = nodesList.sort((a, b) => a - b);
  });


  const cutEdges = new Set();
  commNodes.forEach((id) => {
    const curTopo = classifiedDict[id]['topo'];
    if (topoToCutEdgesDict.hasOwnProperty(curTopo)) { // has cutting methods
      const curCutEdgesIdx = topoToCutEdgesDict[curTopo];
      for (const edge of curCutEdgesIdx) {
        const src = classifiedDict[id]['nodes'][edge[0]];
        const tg = classifiedDict[id]['nodes'][edge[1]];
        cutEdges.add(src + EDGE_SEPARATOR + tg);
      }
      return;
    }
    const {preNodes, nextNodes} = findRelateNodes(id, allNodes, nodeMap);
    const source = '-1';
    const target = '-2';
    const curAllNodes = allNodes;
    const curAllEdges = allEdges;
    curAllNodes.add(source);
    curAllNodes.add(target);
    curAllEdges[source] = {};
    curAllEdges[target] = {};

    preNodes.forEach((preID) => {
      curAllEdges[source][preID] = 10000;
    });
    nextNodes.forEach((nextID) => {
      if (!(nextID in curAllEdges)) {
        curAllEdges[nextID] = {};
      }
      curAllEdges[nextID][target] = 10000;
    });

    const residualAllNodes = curAllNodes;
    const residualAllEdges = JSON.parse(JSON.stringify(curAllEdges));
    const {lastResidualEdges} = fordFulkerson(residualAllNodes, residualAllEdges, source, target);

    const curCutEdges = findCutEdges(source, target, residualAllNodes, lastResidualEdges, curAllEdges);
    topoToCutEdgesDict[curTopo] = [];
    for (const edge of curCutEdges) {
      cutEdges.add(edge);
      const srcIdx = classifiedDict[id]['nodes'].indexOf(parseInt(edge.split(EDGE_SEPARATOR)[0]));
      const tgIdx = classifiedDict[id]['nodes'].indexOf(parseInt(edge.split(EDGE_SEPARATOR)[1]));
      topoToCutEdgesDict[curTopo].push([srcIdx, tgIdx]);
    }
  });

  return {
    cutEdges: cutEdges,
  };
}

const optimizer = {
  /**
   * @param {Object} graphData processedGraph
   */
  init: (graphData) => {
    processedGraph = graphData;
  },

  optimizeNode: (id) => {
    handleDisplayedAttr(id);
  },

  attrNodeMap: _nodesExtraAttributesMap,
};

export {
  optimizer as bipartiteGraphOptimzer,
  processBipartite,
  calcMinCut,
};

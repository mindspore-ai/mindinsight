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
  bipartiteGraphOptimzer,
  processBipartite,
  calcMinCut,
} from './bipartite-graph-optimizer';
import {
  NODE_TYPE,
  SCOPE_SEPARATOR,
  INSERTED_ATTR,
  MIN_COUNT_OF_NODE_STACK,
  SCOPE_AGGREGATOR,
} from './const';

import {genHash, _checkShardMethod} from './util';

let processedGraph = {
  nodeMap: {},
  parameterMap: {},
  constMap: {},
  root: {},
};


let nameScopeIds = [];
const minimumCutMode = true;
let insertedAttr = [];
let delNodesSet;
let firstCntFlag = true;

let rawGraphData = null; // raw graph data

const COMM_LIST = new Set([
  'AllReduce',
  'AllGather',
  'AllToAll',
  'ReduceScatter',
]);

export let showNodeType = ''; // graph selector label
export let showRankId = ''; // rank selector label
export let instanceTypeFlag = false;

const topScopeSet = new Set();
let pipelinedStageInfo = {};
let pipelineNodeInfo = [[], []];
let pipelineEdgeInfo = [];

export const edgeIdMap = {};
let specialNodesMap = {};

/**
 * Reset data.
 */
function _resetData() {
  instanceTypeFlag = false;
  nameScopeIds = [];
  processedGraph = {
    nodeMap: {},
    parameterMap: {},
    constMap: {},
    root: {},
  };
}

/**
 * Creating a basic node.
 * @param {Object} node Node data
 * @return {Object}
 */
function _createBasicNode(node) {
  const attribute = {};
  Object.keys(node.attr).forEach((key) => (attribute[key] = node.attr[key]));

  return {
    id: node.node_id,
    name: node.name,
    label: node.name.split(SCOPE_SEPARATOR).pop(),
    type: node.type,
    attribute,
    parent: node.scope,
    children: [],
    input: node.input || [],
    output: [],
    outputType: node.outputType || {},
    parameters: {},
    consts: {},
    scope: node.scope,
    ...insertedAttr.reduce((acc, key) => ((acc[key] = node[key]), acc), {}),
    output_shape: node.output_shape,
  };
}

/**
 * Creating a name scope.
 * @param {String} name Name of name scope.
 * @return {Object}
 */
function _createNameScope(name) {
  let parent = '';
  const arr = name.split(SCOPE_SEPARATOR);
  if (arr.length > 1) {
    parent = arr.slice(0, -1).join(SCOPE_SEPARATOR);
  }
  const curNameList = name.split(SCOPE_SEPARATOR).pop().split(SCOPE_AGGREGATOR);
  const oriNameList = name.split(/[+]|[/]/);
  const newScopeHierarchy = [];
  const newScopeHierarchyOri = [oriNameList[0]];
  for (let i = 0; i < curNameList.length; i++) {
    const sc = curNameList[i];
    const idx = sc.lastIndexOf('_');
    if (sc[0] == 'C') newScopeHierarchy.push(sc);
    else newScopeHierarchy.push(sc.substr(0, idx));
  }
  for (let i = 1; i < oriNameList.length; i++) {
    const sc = oriNameList[i];
    const idx = sc.lastIndexOf('_');
    newScopeHierarchyOri.push(sc.substr(0, idx));
  }

  const curName = newScopeHierarchy.join(SCOPE_SEPARATOR);
  newScopeHierarchyOri.shift();
  const oriName = newScopeHierarchyOri.join(SCOPE_SEPARATOR);

  return {
    id: name,
    name: oriName,
    label: curName,
    type: NODE_TYPE.name_scope,
    parent,
    children: [],
    input: [],
    output: [],
    expanded: false,
    stacked: false,
    scope: parent,
    specialNodesCnt: {},
  };
}

/**
 * Creating a aggregate scope.
 * @param {String} name Name of aggregate scope.
 * @return {Object}
 */
function _createAggregateScope(name) {
  let parent = '';
  const arr = name.split(SCOPE_SEPARATOR);
  if (arr.length > 1) {
    parent = arr.slice(0, -1).join(SCOPE_SEPARATOR);
  }
  return {
    id: name,
    name: name,
    label: name.split(SCOPE_SEPARATOR).pop(),
    type: NODE_TYPE.aggregate_scope,
    parent,
    children: [],
    input: [],
    output: [],
    expanded: false,
    stacked: true,
    scope: parent,
  };
}

/**
 * Creating a parameter node.
 * @param {Object} param Parameter node data.
 * @return {Object}
 */
function _createParameter(param) {
  return {
    id: param.node_id,
    name: param.name,
    type: NODE_TYPE.parameter,
    parent: '',
    value: param.attr || {},
  };
}

/**
 * Creating a const node.
 * @param {Object} con Const node data.
 * @return {Object}
 */
function _createConst(con) {
  return {
    id: con.node_id,
    name: con.name,
    type: NODE_TYPE.const,
    parent: '',
  };
}

/**
 * Create a trie node.
 * @param {Object} key
 */
function TrieNode(key) {
  this.key = key;
  this.children = [];
  this.refNodes = [];
}

/**
 * Insert a node to the trie.
 * @param {Object} insertNode the initial node to be inserted
 * @param {String} scopeString the scope string of the initial node
 * @param {Object} root the root of the trie
 */
function _insertTrieNode(insertNode, scopeString, root) {
  if (scopeString === '' || !scopeString) return;

  const scopes = scopeString.split(SCOPE_SEPARATOR);
  const children = root.children;
  let hasSuffixChild = null;
  for (let i = 0; i < children.length; i++) {
    if (children[i].key === scopes[0]) {
      hasSuffixChild = children[i];
      children[i].refNodes.push(insertNode);
      break;
    }
  }

  if (hasSuffixChild) {
    _insertTrieNode(
        insertNode,
        scopes.splice(1).join(SCOPE_SEPARATOR),
        hasSuffixChild,
    );
  } else {
    if (children.length === 0) {
      const newNode = new TrieNode(scopes[0]);
      newNode.refNodes.push(insertNode);
      children.push(newNode);
      _insertTrieNode(
          insertNode,
          scopes.splice(1).join(SCOPE_SEPARATOR),
          newNode,
      );
    } else {
      let validPosition = 0;
      for (let j = 0; j < children.length; j++) {
        if (children[j].key < scopes[0]) {
          validPosition++;
        }
      }
      const newNode = new TrieNode(scopes[0]);
      newNode.refNodes.push(insertNode);
      children.splice(validPosition, 0, newNode);
      _insertTrieNode(
          insertNode,
          scopes.splice(1).join(SCOPE_SEPARATOR),
          newNode,
      );
    }
  }
}

/**
 * Compress the trie.
 * @param {Object} node the root node of the trie
 */
function _compressTrie(node) {
  for (let i = 0; i < node.children.length; i++) {
    _compressTrie(node.children[i]);
  }
  const queue = [];
  queue.unshift(node);
  while (queue.length !== 0) {
    const top = queue[queue.length - 1];
    queue.pop();
    if (top.children.length === 1 && top.children[0].children.length !== 0) {
      // only one child, compress
      top.refNodes.forEach((refNode) => {
        refNode.scope = refNode.scope.replace(
            `${top.key}/${top.children[0].key}`,
            `${top.key}+${top.children[0].key}`,
        );
        refNode.parent = refNode.parent.replace(
            `${top.key}/${top.children[0].key}`,
            `${top.key}+${top.children[0].key}`,
        );
      });
      top.key += '+' + top.children[0].key;
      top.children = top.children[0].children;
    }
    for (let i = 0; i < top.children.length; i++) {
      queue.unshift(top.children[i]);
    }
  }
}

/**
 * Finding exist name scope of node.
 * @param {String} id Node id.
 * @return {String}
 */
function _findExistNameScope(id) {
  const {nodeMap} = processedGraph;
  let currentNode = nodeMap[id];
  if (!currentNode.parent) return id;
  let target = id;
  let parent = nodeMap[currentNode.parent];
  while (currentNode.parent) {
    if (!parent.expanded) {
      target = parent.id;
    }
    currentNode = parent;
    parent = nodeMap[currentNode.parent];
  }
  return target;
}

/**
 * Finding top name scope of node.
 * @param {String} id Node id.
 * @return {String}
 */
function _findTopScope(id) {
  const {nodeMap} = processedGraph;

  let currentNode = nodeMap[id];
  if (!currentNode.parent) return id;
  let parent = nodeMap[currentNode.parent];
  while (currentNode.parent) {
    currentNode = parent;
    parent = nodeMap[currentNode.parent];
  }
  return currentNode;
}

/**
 * Delete certain nodes {Load}, {UpdateState, MakeTuple, TupleGetItem, Depend}.
 * These types of nodes are not the focus of analysis, deleting them helps reduce visual clutter.
 * With equal to or less than 1 input or output nodes.
 * @param {Object} nodeMap node map.
 */
function _delTrivialNodes(nodeMap) {
  delNodesSet = new Set();
  Object.values(nodeMap).forEach((basicNode) => {
    if (basicNode.type === 'UpdateState' || basicNode.type === 'MakeTuple'
    || basicNode.type === 'TupleGetItem' || basicNode.type === 'Load' || basicNode.type === 'Depend') {
      let inputCnt = 0;
      let outputCnt = 0;
      const inputNodes = [];
      const outputNodes = [];
      for (const id of basicNode.input) {
        if (!isNaN(id)) {
          inputCnt++;
          inputNodes.push(id);
        }
      }
      for (const id of basicNode.output) {
        if (!isNaN(id)) {
          outputCnt++;
          outputNodes.push(id);
        }
      }
      if (inputCnt === 0) {
        for (const id of basicNode.output) {
          if (!isNaN(id)) {
            const curOutputNode = nodeMap[id];
            if (_checkShardMethod(curOutputNode.parallel_shard)) return;
            const targetNodeIdx = curOutputNode.input.indexOf(basicNode.id);
            curOutputNode.input.splice(targetNodeIdx, 1);
          }
        }
        delNodesSet.add(basicNode.id);
        delete nodeMap[basicNode.id];
      } else if (outputCnt === 0) {
        for (const id of basicNode.input) {
          if (!isNaN(id)) {
            const curInputNode = nodeMap[id];
            const targetNodeIdx = curInputNode.output.indexOf(basicNode.id);
            curInputNode.output.splice(targetNodeIdx, 1);
          }
        }
        delNodesSet.add(basicNode.id);
        delete nodeMap[basicNode.id];
      } else if (outputCnt === 1) {
        const nxtNode = nodeMap[outputNodes[0]];
        if (_checkShardMethod(nxtNode.parallel_shard)) return;
        for (const id of basicNode.input) {
          if (!isNaN(id)) {
            const preNode = nodeMap[id];
            const targetNodeIdx = preNode.output.indexOf(basicNode.id);
            preNode.output.splice(targetNodeIdx, 1, outputNodes[0]);
          }
        }
        const targetNodeIdx = nxtNode.input.indexOf(basicNode.id);
        nxtNode.input.splice(targetNodeIdx, 1);
        nxtNode.input.push(...basicNode.input);

        delNodesSet.add(basicNode.id);
        delete nodeMap[basicNode.id];
      } else if (inputCnt === 1) {
        for (const id of basicNode.output) {
          if (!isNaN(id)) {
            const nxtNode = nodeMap[id];
            if (_checkShardMethod(nxtNode.parallel_shard)) return;
            const targetNodeIdx = nxtNode.input.indexOf(basicNode.id);
            nxtNode.input.splice(targetNodeIdx, 1, inputNodes[0]);
          }
        }
        const preNode = nodeMap[inputNodes[0]];
        const targetNodeIdx = preNode.output.indexOf(basicNode.id);
        preNode.output.splice(targetNodeIdx, 1);
        preNode.output.push(...basicNode.output);
        delNodesSet.add(basicNode.id);
        delete nodeMap[basicNode.id];
      }
    }
  });
}

/**
 * build top scope set
 * @param {Object} data Graph data.
 * @return {Set} topScopeSet
 */
function _buildTopScopeSet(data) {
  // filter communication nodes
  for (const sNode of data.op_nodes) {
    if (sNode && Object.keys(sNode).length) {
      topScopeSet.add(sNode.scope.split(SCOPE_SEPARATOR)[0]);
    }
  }
  showNodeType = topScopeSet.values().next().value;
  return topScopeSet;
}

/**
 * Processing nodes data, statistics const and parameter nodes.
 * Construct bipartite graph, do namescope aggregation.
 * @param {Object} data Graph data.
 */
function _processNodesParallel(data) {
  const nodes = data.op_nodes || [];
  const {parameter_nodes: parameterNodes, const_nodes: constNodes} = data;
  const {nodeMap, parameterMap, constMap} = processedGraph;
  // save the IDs of all existing namespaces
  const nameScopeSet = new Set();
  for (const param of parameterNodes) {
    parameterMap[param.node_id] = _createParameter(param);
  }

  for (const con of constNodes) {
    constMap[con.node_id] = _createConst(con);
  }

  let commNodesCnt = 0;
  for (const sNode of nodes) {
    if (COMM_LIST.has(sNode.type) && sNode.scope.startsWith(showNodeType)) {
      commNodesCnt++;
    }
  }
  // for nodes cnt > 5000 and comm nodes cnt > 30, we only extract comm nodes with special type
  if (nodes.length > 5000 && commNodesCnt > 30) instanceTypeFlag = true;

  // nodeMap
  for (const sNode of nodes) {
    if (sNode && Object.keys(sNode).length) {
      const node = _createBasicNode(sNode);
      if (COMM_LIST.has(node.type) && node.scope.startsWith(showNodeType) && (!instanceTypeFlag || node.instance_type !== '')) {
        sNode.parent = '';
        sNode.scope = '';
      }
      nodeMap[node.id] = node;
    }
  }

  // output & input_shape
  Object.values(nodeMap).forEach((basicNode) => {
    const inputs = basicNode.input;
    basicNode.input_shape = {};
    for (const inputId of inputs) {
      const source =
        nodeMap[inputId] || parameterMap[inputId] || constMap[inputId];
      if (
        !source ||
        source.type === NODE_TYPE.parameter ||
        source.type === NODE_TYPE.const
      ) {
        continue;
      }
      source.output.push(basicNode.id);
    }
  });


  let bipartiteRes;
  if (minimumCutMode) {
    const {cutEdges} = calcMinCut(nodeMap);
    bipartiteRes = processBipartite(nodeMap, cutEdges);
  } else {
    bipartiteRes = processBipartite(nodeMap);
  }

  const components = bipartiteRes['components'];
  const bits = components.length.toString().length;

  Object.keys(components).forEach((nid) => {
    const curComponent = components[nid];
    for (const sid of curComponent) {
      const id = parseInt(sid) - 1;
      let scopes = nodes[id].scope;
      const names = scopes
          .split(SCOPE_SEPARATOR)
          .map((nameId) => nameId + '_' + nid);
      scopes = names.join(SCOPE_SEPARATOR);
      scopes = 'Computation_' + nid.padStart(bits, '0') + SCOPE_SEPARATOR + scopes;
      nodes[id].scope = scopes;
      nodes[id].parent = scopes;
    }
  });

  const trie = new TrieNode(null);
  for (const sNode of nodes) {
    _insertTrieNode(
        sNode,
        `${sNode.scope}/${
          sNode.name.split(SCOPE_SEPARATOR)[
              sNode.name.split(SCOPE_SEPARATOR).length - 1
          ]
        }`,
        trie,
    );
  }
  _compressTrie(trie); // compress the namescope with only one child
  _delTrivialNodes(nodeMap); // delete trivial nodes
  // output & input_shape
  Object.values(nodeMap).forEach((basicNode) => {
    const inputs = basicNode.input;
    basicNode.input_shape = {};
    for (const inputId of inputs) {
      const source =
        nodeMap[inputId] || parameterMap[inputId] || constMap[inputId];
      if (
        !source ||
        source.type === NODE_TYPE.parameter ||
        source.type === NODE_TYPE.const
      ) {
        continue;
      }
      basicNode.input_shape[inputId] = source.output_shape;
    }
  });
  for (const sNode of nodes) {
    if (sNode && Object.keys(sNode).length && !delNodesSet.has(sNode.node_id)) {
      if (sNode.scope && !nameScopeSet.has(sNode.scope)) {
        let iterator = sNode.scope.split(SCOPE_SEPARATOR);
        do {
          const name = iterator.join(SCOPE_SEPARATOR);
          if (nameScopeSet.has(name)) {
            iterator = [];
          } else {
            nameScopeSet.add(name);
            iterator.pop();
          }
        } while (iterator.length);
      }

      nodeMap[sNode.node_id].scope = sNode.scope;
      nodeMap[sNode.node_id].parent = sNode.scope;
    }
  }


  nameScopeIds = Array.from(nameScopeSet).sort(); // to ensure the child's namescope constructed after the father's
}

/**
 * Creating all name scope nodes.
 */
function _processNameScope() {
  processedGraph.root = {id: 'root', children: [], stacked: false};
  const {nodeMap, root} = processedGraph;

  for (const id of nameScopeIds) {
    const nameScope = _createNameScope(id);
    nodeMap[id] = nameScope;
    const parent = nameScope.parent ? nodeMap[nameScope.parent] : root;
    parent.children.push(id);
  }
}

/**
 * Get special nodes cnt of the entire graph
 */
function _processNodesGlobalCnt() {
  specialNodesMap = {};
  const {nodeMap} = processedGraph;
  Object.keys(nodeMap).forEach((id) => {
    if (isNaN(id)) return;
    const node = nodeMap[id];
    if (_checkShardMethod(node.parallel_shard)) {
      if (specialNodesMap.hasOwnProperty('hasStrategy')) {
        specialNodesMap['hasStrategy']++;
      } else {
        specialNodesMap['hasStrategy'] = 1;
      }
    }
    if (node.instance_type !== undefined) {
      if (specialNodesMap.hasOwnProperty(node.instance_type)) {
        specialNodesMap[node.instance_type]++;
      } else {
        specialNodesMap[node.instance_type] = 1;
      }
    }
  });
}

/**
 * reset firstCntFlag
 */
function resetFirstCntFlag() {
  firstCntFlag = true;
}

/**
 * reset pipeline and special nodes cnt data
 */
function resetData() {
  specialNodesMap = {};
  pipelinedStageInfo = {};
  pipelineNodeInfo = [[], []];
  pipelineEdgeInfo = [];
}

/**
 * Get special nodes cnt of all namescopes
 */
function _processNodesCnt() {
  if (firstCntFlag) {
    _processNodesGlobalCnt();
    firstCntFlag = false;
  }

  const {nodeMap} = processedGraph;
  Object.keys(nodeMap).forEach((id) => {
    if (isNaN(id)) return;
    const node = nodeMap[id];
    const iterator = node.scope.split(SCOPE_SEPARATOR);

    if (!node.parent) return;
    do {
      const name = iterator.join(SCOPE_SEPARATOR);
      const scopeNode = nodeMap[name];
      if (_checkShardMethod(node.parallel_shard)) {
        if (scopeNode.specialNodesCnt.hasOwnProperty('hasStrategy')) {
          scopeNode.specialNodesCnt['hasStrategy']++;
        } else {
          scopeNode.specialNodesCnt['hasStrategy'] = 1;
        }
      }
      if (node.instance_type !== undefined) {
        if (scopeNode.specialNodesCnt.hasOwnProperty(node.instance_type)) {
          scopeNode.specialNodesCnt[node.instance_type]++;
        } else {
          scopeNode.specialNodesCnt[node.instance_type] = 1;
        }
      }
      iterator.pop();
    } while (iterator.length);
  });
}

/**
 * Filter input and output information.
 * @param {Object} data Input or output information.
 * @param {String} filterKey Name scope name.
 * @return {Object}
 */
function _filterIOData(data, filterKey) {
  const obj = {};
  const {nodeMap} = processedGraph;
  for (const key of Object.keys(data)) {
    const temp = data[key];
    if (nodeMap[temp].scope.startsWith(filterKey + SCOPE_SEPARATOR)) continue;
    obj[key] = temp;
  }
  return obj;
}

/**
 * Collect statistics on input and output of all nodes and
 * then the input and output of all name scopes.
 */
function _processHierarchy() {
  const {nodeMap, parameterMap, constMap, root} = processedGraph;
  const nodes = Object.values(nodeMap);
  const usedAuxiliaryNodes = {parameter: {}, const: {}};

  // record the input and output of all nodes
  for (const node of nodes) {
    if (node.type === NODE_TYPE.name_scope) continue;
    const parent = node.parent ? nodeMap[node.parent] : root;
    parent.children.push(node.id);

    for (const inputId of node.input) {
      const source =
        nodeMap[inputId] || parameterMap[inputId] || constMap[inputId];
      if (!source) continue;
      if (
        source.type === NODE_TYPE.parameter ||
        source.type === NODE_TYPE.const
      ) {
        source.parent = parent.id;
        node[source.type + 's'][source.id] = source;
        usedAuxiliaryNodes[source.type][source.id] = source;
      } else {
        if (
          node.parent &&
          !source.scope.startsWith(node.parent)
        ) {
          nodeMap[node.parent].input.push(inputId);
        }
        if (
          source.parent &&
          !node.scope.startsWith(source.parent)
        ) {
          nodeMap[source.parent].output.push(node.id);
        }
      }
    }
  }
  processedGraph.parameterMap = usedAuxiliaryNodes.parameter;
  processedGraph.constMap = usedAuxiliaryNodes.const;

  // record the input and output of namescopes
  for (let len = nameScopeIds.length - 1, i = len; i >= 0; i--) {
    const id = nameScopeIds[i];
    const nameScope = nodeMap[id];
    nameScope.children = Array.from(new Set(nameScope.children));
    nameScope.input = Array.from(new Set(nameScope.input));
    nameScope.output = Array.from(new Set(nameScope.output));

    if (!nameScope.parent) continue;
    const parent = nodeMap[nameScope.parent];
    parent.input = parent.input.concat(
        Object.values(_filterIOData(nameScope.input, parent.id)),
    );
    parent.output = parent.output.concat(
        Object.values(_filterIOData(nameScope.output, parent.id)),
    );
  }
}

/**
 * Processing all data.
 * @param {Object} data All graph data
 */
function _processSourceData(data) {
  insertedAttr = Object.values(INSERTED_ATTR);
  _processNodesParallel(data);
  _processNameScope();
  _processNodesCnt();
  _processHierarchy();
}

/**
 * Generates a hash value of a node.
 * @param {Object} node
 * @param {Object} nodeMap Map of all nodes.
 * @param {Object} parameterMap Map of all parameter nodes.
 * @param {Object} constMap Map of all const nodes.
 * @return {Number}
 */
function _getNodeHash(node, nodeMap, parameterMap, constMap) {
  let hash = 0;
  const bigPrimitive = 10000019;
  const genHashValues = [node.parent, node.type];
  const attrs = {
    input: node.input,
    output: node.output,
  };

  for (const attr of Object.keys(attrs)) {
    const ids = attrs[attr];
    for (const id of ids) {
      if (isNaN(id)) continue;
      genHashValues.push(
          attr + '-' + (nodeMap[id] || parameterMap[id] || constMap[id]).type,
      );
    }
    genHashValues.push(attr + '-' + ids.length);
  }

  for (const str of genHashValues) {
    hash = (hash + genHash(str)) % bigPrimitive;
  }
  return hash;
}

/**
 * Stack nodes with the same hash value.
 * @param {Object} nameScope Name scope data.
 * @param {Object} nodeHashMap Map of hash values of all child nodes.
 * @param {Object} nodeMap Map of all nodes.
 */
function _stackSimilarNodes(nameScope, nodeHashMap, nodeMap) {
  let count = 1;
  const children = new Set(nameScope.children);
  nodeHashMap.forEach((value) => {
    const stackSize = value.set.size;
    if (stackSize >= MIN_COUNT_OF_NODE_STACK) {
      const name = `${nameScope.id}/${value.type}[${stackSize}]_${count++}`;
      const stackNode = _createAggregateScope(name);
      const ids = Array.from(value.set);
      stackNode.children = ids;
      nodeMap[stackNode.id] = stackNode;
      children.add(stackNode.id);

      for (const id of ids) {
        const node = nodeMap[id];
        node.parent = name;
        children.delete(node.id);
        stackNode.input = stackNode.input.concat(node.input);
        stackNode.output = stackNode.output.concat(node.output);
      }
      stackNode.input = [...new Set(stackNode.input)];
      stackNode.output = [...new Set(stackNode.output)];
    }
  });
  nameScope.stacked = true;
  nameScope.children = Array.from(children);
}

/**
 * Optimizing the subnodes of a name scope.
 * @param {String} id Id of name scope.
 */
function _optimizeNodes(id) {
  const {nodeMap, parameterMap, constMap, root} = processedGraph;
  const nameScope = nodeMap[id] || root;
  bipartiteGraphOptimzer.optimizeNode(id);
  if (
    nameScope.stacked ||
    nameScope.children.length < MIN_COUNT_OF_NODE_STACK
  ) {
    nameScope.stacked = true;
    return;
  }
  const nodeHashMap = new Map();
  for (const child of nameScope.children) {
    const node = nodeMap[child];
    if (node.type in NODE_TYPE) continue;
    if (COMM_LIST.has(node.type)) { // do not stack comm nodes
      continue;
    }
    const nodeHash = _getNodeHash(node, nodeMap, parameterMap, constMap);
    let nodeHashSet = nodeHashMap.get(nodeHash);
    if (nodeHashSet) {
      nodeHashSet.set.add(child);
    } else {
      nodeHashSet = {type: node.type, set: new Set()};
      nodeHashSet.set.add(child);
      nodeHashMap.set(nodeHash, nodeHashSet);
    }
  }

  _stackSimilarNodes(nameScope, nodeHashMap, nodeMap);
}

/**
 * Process the nodes data to be displayed.
 * @return {Object}
 */
function _produceVisGraph() {
  const {nodeMap, root} = processedGraph;
  const visNodes = [];
  const edges = [];
  const edgesMap = new Map();
  let iterator = [].concat(root.children);
  while (iterator.length) {
    const node = nodeMap[iterator[0]];
    visNodes.push(node);

    iterator.shift();
    if (node.expanded) {
      iterator = iterator.concat(node.children);
    } else {
      const inputIds = node.input;
      for (const id of inputIds) {
        if (isNaN(id)) continue;
        const source = _findExistNameScope(id);
        if (source === node.id) continue;
        if (
          nodeMap[source].type in NODE_TYPE &&
          nodeMap[node.id].type in NODE_TYPE &&
          nodeMap[node.id].id.indexOf(SCOPE_SEPARATOR) === -1 &&
          nodeMap[source].id.indexOf(SCOPE_SEPARATOR) === -1 &&
          nodeMap[node.id].id.split('_')[
              nodeMap[node.id].id.split('_').length - 1
          ] !==
            nodeMap[source].id.split('_')[
                nodeMap[source].id.split('_').length - 1
            ]
        ) {
          continue;
        }
        const key = `${source}->${node.id}`;
        const value = (edgesMap.get(key) || 0) + 1;
        edgesMap.set(key, value);
        edgeIdMap[id + '->' + node.id] = key;
      }
    }
  }

  const edgesWithOutline = [];
  for (const [key, value] of edgesMap) {
    const ids = key.split('->');
    edges.push({
      source: ids[0],
      target: ids[1],
      count: value,
    });
  }
  return {
    visNodes,
    edges,
    edgesWithOutline,
    nodeAttrMap: bipartiteGraphOptimzer.attrNodeMap,
  };
}

/**
 * Search node by name.
 * @param {String} name Node name.
 * @return {Object}
 */
function searchNode(name) {
  name = name + '';
  if (!name) return null;
  const {nodeMap} = processedGraph;

  const ids = new Set();
  const nodes = {};
  for (const node of Object.values(nodeMap)) {
    if (!node.node_id.includes(name)) continue;
    let scopeId;
    let currentId;
    if (node.type in NODE_TYPE) {
      scopeId = currentId = node.id;
    } else {
      ids.add(node.id);
      nodes[node.id] = {
        id: node.id,
        name: node.node_id,
        type: node.type,
        parent: node.parent,
      };
      currentId = node.id;
      scopeId = node.parent;
    }

    while (scopeId) {
      if (ids.has(scopeId)) {
        if (currentId !== scopeId) {
          nodes[scopeId].children.push(currentId);
        }
        scopeId = null;
      } else {
        const scope = nodeMap[scopeId];
        const scopeTemp = {
          id: scopeId,
          name: scope.node_id,
          type: scope.type,
          parent: scope.parent,
          children: [],
        };
        if (currentId !== scopeId) {
          scopeTemp.children.push(currentId);
        }
        nodes[scopeId] = scopeTemp;
        ids.add(scopeId);

        currentId = scopeId;
        scopeId = scope.parent;
      }
    }
  }
  return JSON.parse(JSON.stringify(nodes));
}

/**
 * Query a single node.
 * @param {String} id Node id.
 * @return {Object}
 */
function querySingleNode(id) {
  const {nodeMap} = processedGraph;
  let node = nodeMap[id];
  if (!node) return null;

  while (node.parent) {
    const parent = nodeMap[node.parent];
    if (parent.type === NODE_TYPE.aggregate_scope) {
      node = parent;
      continue;
    }
    if (!parent.expanded) parent.expanded = true;
    if (!parent.stacked) _optimizeNodes(parent.id);
    node = parent;
  }

  const visGraph = _produceVisGraph();
  return visGraph;
}

/**
 * Get a single node.
 * @param {String} id Node id.
 * @return {Object}
 */
function getSingleNode(id) {
  const {nodeMap, constMap, parameterMap} = processedGraph;
  return nodeMap[id] || constMap[id] || parameterMap[id];
}

/**
 * Get send/receive nodes' real names
 * @param {String} nodeID node id.
 * @param {String} stageIndex stage index.
 * @return {String}
 */
function getRealNodeName(nodeID, stageIndex) {
  const nodeName = rawGraphData[stageIndex]['op_nodes'][nodeID - 1]?.name;
  const index = nodeName.lastIndexOf('op');
  return nodeName.substring(index + 2);
}

/**
 * Change top comm nodes.
 * @param {String} newType top comm nodes type.
 */
function changeShowNodeType(newType) {
  showNodeType = newType;
}

/**
 * Change top comm nodes.
 * @param {String} newId new rankId.
 */
function changeShowRankId(newId) {
  showRankId = newId;
}

/**
 * Modify name scope expansion status.
 * @param {String} id Name scope id.
 * @return {Object}
 */
function toggleExpanded(id) {
  const nameScope = processedGraph.nodeMap[id];
  if (!nameScope) return;
  nameScope.expanded = !nameScope.expanded;
  let optimizeId = id;

  let children = [].concat(nameScope.children);
  let child = processedGraph.nodeMap[children[0]];
  while (
    nameScope.expanded &&
    children.length === 1 &&
    child.type === NODE_TYPE.name_scope
  ) {
    child.expanded = true;
    optimizeId = child.id;
    children = [].concat(child.children);
    child = processedGraph.nodeMap[children[0]];
  }

  _optimizeNodes(optimizeId);

  const visGraph = _produceVisGraph();
  return visGraph;
}

/**
 * Build Pipeline stage info for training pipeline panel.
 * @param {Object} data All graph data
 * @return {Object}
 *  nodeInfo represents the operator: a three-level array [][][],
 *  the first level takes values 0 and 1, which respectively represents whether the operator is in l-r or r-l area;
 *  the second level is the column number;
 *  the third level is the line number. The elements in the array are operator IDs.
 *
 *  edgeInfo represents the edge: [[start, end]],
 *  start and end are arrays consisiting of the coordinates of the operator and the index of nodeInfo.
 */
function buildPipelinedStageInfo(data) {
  pipelinedStageInfo = {};
  pipelineNodeInfo = [[], []];
  pipelineEdgeInfo = [];
  rawGraphData = data;
  for (const rankID of Object.keys(data)) {
    const opNodes = data[rankID]['op_nodes'];
    for (const opNode of opNodes) {
      if (opNode.type === 'Send' || opNode.type === 'Receive') {
        const thisStr =
          opNode.type === 'Send'
            ? `${rankID}-${opNode.attr.dest_rank}`
            : `${opNode.attr.src_rank}-${rankID}`;
        if (!(thisStr in pipelinedStageInfo)) {
          pipelinedStageInfo[thisStr] = {};
        }
        if (!(opNode.attr.sr_tag in pipelinedStageInfo[thisStr])) {
          pipelinedStageInfo[thisStr][opNode.attr.sr_tag] = [];
        }
        if (opNode.type === 'Send') {
          pipelinedStageInfo[thisStr][opNode.attr.sr_tag].unshift(
              opNode.node_id,
          );
        } else {
          pipelinedStageInfo[thisStr][opNode.attr.sr_tag].push(opNode.node_id);
        }
      }
    }
  }

  for (const key of Object.keys(pipelinedStageInfo)) {
    const stageInfo = pipelinedStageInfo[key];
    const [startStage, endStage] = key.split('-').map((v) => Number(v));
    let firstIndex; let startSecondIndex; let endSecondIndex;
    if (startStage < endStage) {
      firstIndex = 0;
      startSecondIndex = (startStage) * 2;
      endSecondIndex = (endStage) * 2 - 1;
    } else {
      firstIndex = 1;
      startSecondIndex = (startStage) * 2 - 1;
      endSecondIndex = (endStage) * 2;
    }
    if (pipelineNodeInfo[firstIndex][startSecondIndex] === undefined) {
      pipelineNodeInfo[firstIndex][startSecondIndex] = [];
    }
    if (pipelineNodeInfo[firstIndex][endSecondIndex] === undefined) {
      pipelineNodeInfo[firstIndex][endSecondIndex] = [];
    }
    for (const [startNodeId, endNodeId] of Object.values(stageInfo)) {
      if (endNodeId === undefined) {
        return {err: 'build failed.'};
      }
      pipelineNodeInfo[firstIndex][startSecondIndex].push(startNodeId);
      pipelineNodeInfo[firstIndex][endSecondIndex].push(endNodeId);
      pipelineEdgeInfo.push([
        [firstIndex, startSecondIndex, pipelineNodeInfo[firstIndex][startSecondIndex].length - 1],
        [firstIndex, endSecondIndex, pipelineNodeInfo[firstIndex][endSecondIndex].length - 1],
      ]);
    }
  }
  if (!pipelineEdgeInfo.length) {
    return {err: 'no pipeline data.'};
  }
  return {
    pipelinedStageInfo,
    pipelineNodeInfo,
    pipelineEdgeInfo,
  };
}

/**
 * Get special nodes map.
 * @return {Object}
 */
function getSpecialNodesMap() {
  return specialNodesMap;
}

/**
 * Build graph data.
 * @param {Object} data All graph data
 * @return {Object}
 */
function buildGraph(data) {
  _resetData();
  _processSourceData(data);
  bipartiteGraphOptimzer.init(processedGraph);
  _optimizeNodes();
  const visGraph = _produceVisGraph();
  return visGraph;
}

export {
  buildGraph,
  toggleExpanded,
  searchNode,
  querySingleNode,
  getSingleNode,
  changeShowNodeType,
  changeShowRankId,
  buildPipelinedStageInfo,
  _findTopScope,
  _findExistNameScope,
  getRealNodeName,
  resetFirstCntFlag,
  resetData,
  _buildTopScopeSet,
  getSpecialNodesMap,
};

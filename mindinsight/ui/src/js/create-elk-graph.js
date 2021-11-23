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
  NODE_TYPE,
  SCOPE_SEPARATOR,
  EDGE_SEPARATOR,
  IN_PORT_SUFFIX,
  OUT_PORT_SUFFIX,
} from './const';
import {ElkDataNode, ElkRootNode, ElkEdge, ElkNode, ElkPort} from './elk-class';

let moduleEdge;

export const dataNodeMap = new Map();

const rootSet = new Set();

let curEdgesWithOutline = new Set();

let _nodeAttrMap = {};

/**
 * The function to create data
 * @param {Object} data
 * @param {Boolean} isFirst
 * @param {Number} themeIndex
 * @return {Array}
 */
export function createElkGraph(data, isFirst, themeIndex) {
  // Prepare dataNodeMap and rootSet
  const {visNodes, edges, edgesWithOutline, nodeAttrMap} = data;
  curEdgesWithOutline = new Set(edgesWithOutline);
  _nodeAttrMap = nodeAttrMap;
  dataNodeMap.clear();
  if (isFirst) rootSet.clear();
  // Prepare dataNodeMap and rootSet
  visNodes.forEach((visNode) => {
    if (isFirst) {
      rootSet.add(visNode.id);
      visNode.root = '';
    } else {
      visNode.root = visNode.parent === '' ? '' : getScopeRoot(visNode.parent);
    }
    dataNodeMap.set(visNode.id, new ElkDataNode(visNode));
  });
  if (isFirst) {
    moduleEdge = Array.from(edges);
  } else {
    edges.push(...moduleEdge);
  }
  const elkGraph = new ElkRootNode([], [], themeIndex);
  createNodesEdges(edges);
  for (const node of dataNodeMap.values()) {
    if (!node.parent) {
      // From the children of root node
      if (node.type === NODE_TYPE.name_scope) {
        node.type = NODE_TYPE.basic_scope;
      }
      createElkNode(elkGraph, node);
    }
  }
  return elkGraph;
}
/**
 * The function to get the strategy matrix height
 * @param {ExtraAttr} extraAttr
 * @return {Number}
 */
function _getStrategyHeight(extraAttr) {
  if (!extraAttr || !extraAttr.strategy) return 0;

  return extraAttr.strategy.length * 8 * 2;
}

/**
 * The function to create elk node
 * @param {ElkRootNode} root
 * @param {ElkDataNode} node
 */
function createElkNode(root, node) {
  const isScope = [
    NODE_TYPE.basic_scope,
    NODE_TYPE.name_scope,
  ].includes(node.type);
  const checkShow = [
    NODE_TYPE.basic_scope,
  ].includes(node.type);
  root.children.push(
      new ElkNode({
        id: node.id,
        label: node.label,
        name: node.name,
        type: node.type,
        specialNodesCnt: node.specialNodesCnt,
        expanded: node.expanded,
        width: isScope ? 120 : 40,
        height: isScope ? 80 : 16 + _getStrategyHeight(_nodeAttrMap[node.id]),
        ports: [
          new ElkPort(
              node.id,
              true,
          checkShow ? !node.input.length : !node.hiddenEdges.input.size,
          ),
          new ElkPort(
              node.id,
              false,
          checkShow ? !node.output.length : !node.hiddenEdges.output.size,
          ),
        ],
      }),
  );
  if (node.edges.size) {
    node.edges.forEach((value, id) => {
      const elkEdge = new ElkEdge(id, value.sources, value.targets);
      if (curEdgesWithOutline.has(id)) {
        elkEdge.outline = true;
      }
      root.edges.push(elkEdge);
    });
  }
  if (node.expanded) {
    node.children.forEach((child) => {
      createElkNode(
          root.children[root.children.length - 1],
          dataNodeMap.get(child),
      );
    });
  }
}

/**
 * The function to get root of scope
 * @param {String} parent
 * @return {String} root
 */
function getScopeRoot(parent) {
  const rootIterator = rootSet.values();
  let root = rootIterator.next();
  while (!root.done && !parent.startsWith(root.value)) {
    root = rootIterator.next();
  }
  return root.value;
}

/**
 * The function to create nodes targets
 * @param {Array} edges
 */
function createNodesEdges(edges) {
  edges.forEach((edge) => {
    createNodeEdges(edge.source, edge.target);
  });
}
/**
 * The function to get edge id when hovering strategy matrix
 * @param {String} source
 * @param {String} target
 * @return {null | String | Array<String>} edgeId
 */
export function getEdge(source, target) {
  if (
    dataNodeMap.get(source) === undefined ||
    dataNodeMap.get(target) === undefined
  ) {
    return null;
  }
  const sourceParent = dataNodeMap.get(source).parent;
  const targetParent = dataNodeMap.get(target).parent;
  if (sourceParent !== targetParent) {
    // Different name scope
    const sourceParentList = sourceParent.split(SCOPE_SEPARATOR);
    const targetParentList = targetParent.split(SCOPE_SEPARATOR);
    if (sourceParentList[0] === targetParentList[0]) {
      // Same basic scope
      return createThroughScopeEdges(
          source,
          target,
          sourceParentList,
          targetParentList,
      );
    } else {
      return 'HIDDEN';
    }
  } else {
    // Same name scope
    return createNormalEdges(source, target);
  }
}

/**
 * The function to create node edges
 * @param {String} source
 * @param {String} target
 */
function createNodeEdges(source, target) {
  const edgeId = getEdge(source, target);
  if (edgeId === 'HIDDEN') {
    dataNodeMap.get(source).hiddenEdges.output.add(target);
    dataNodeMap.get(target).hiddenEdges.input.add(source);
  } else if (edgeId) {
    if (typeof edgeId === 'string') {
      addEdge(source, target, edgeId);
    } else {
      addEdges(source, target, edgeId);
    }
  }
}

/**
 * The function to create edges of two node when two nodes have same root scope but different parent
 * @param {String} source ID of source
 * @param {String} target ID of target
 * @param {Array<String>} sourceParentList source parent
 * @param {Array<String>} targetParentList target parent
 * @return {Array<String>} ID of edges of two node
 */
function createThroughScopeEdges(
    source,
    target,
    sourceParentList,
    targetParentList,
) {
  const publicScopeList = getPublicScopeList(
      sourceParentList,
      targetParentList,
  );
  const level = publicScopeList.length + 1;
  const edges = [];
  if (sourceParentList.length === publicScopeList.length) {
    const targetStart = targetParentList.slice(0, level).join(SCOPE_SEPARATOR);
    edges.push(createNormalEdges(source, targetStart));
    edges.push(...createInputEdges(targetStart, target));
  } else if (targetParentList.length === publicScopeList.length) {
    const sourceEnd = sourceParentList.slice(0, level).join(SCOPE_SEPARATOR);
    edges.push(createNormalEdges(sourceEnd, target));
    edges.push(...createOutputEdges(source, sourceEnd));
  } else {
    const targetStart = targetParentList.slice(0, level).join(SCOPE_SEPARATOR);
    const sourceEnd = sourceParentList.slice(0, level).join(SCOPE_SEPARATOR);
    edges.push(createNormalEdges(sourceEnd, targetStart));
    edges.push(...createOutputEdges(source, sourceEnd));
    edges.push(...createInputEdges(targetStart, target));
  }
  return edges;
}

/**
 * The function to create edges from start to end in input direction
 * @param {Array<String>} start
 * @param {Array<String>} end
 * @return {Array<String>} ID of edges
 */
function createInputEdges(start, end) {
  const edges = [];
  let endTemp = end;
  do {
    const source = `${dataNodeMap.get(endTemp).parent}${IN_PORT_SUFFIX}`;
    const target = `${endTemp}${IN_PORT_SUFFIX}`;
    const ID = `${dataNodeMap.get(endTemp).parent}${EDGE_SEPARATOR}${endTemp}`;
    dataNodeMap.get(endTemp).edges.set(ID, {
      sources: [source],
      targets: [target],
    });
    edges.push(ID);
    endTemp = dataNodeMap.get(endTemp).parent;
  } while (start !== endTemp);
  return edges;
}

/**
 * The function to create edges from start to end in output direction
 * @param {Array<String>} start
 * @param {Array<String>} end
 * @return {Array<String>} ID of edges
 */
function createOutputEdges(start, end) {
  const edges = [];
  let startTemp = start;
  do {
    const source = `${startTemp}${OUT_PORT_SUFFIX}`;
    const target = `${dataNodeMap.get(startTemp).parent}${OUT_PORT_SUFFIX}`;
    const ID = `${startTemp}${EDGE_SEPARATOR}${
      dataNodeMap.get(startTemp).parent
    }`;
    dataNodeMap.get(startTemp).edges.set(ID, {
      sources: [source],
      targets: [target],
    });
    edges.push(ID);
    startTemp = dataNodeMap.get(startTemp).parent;
  } while (startTemp !== end);
  return edges;
}

/**
 * The function to add edge IDs
 * @param {String} source
 * @param {String} target
 * @param {Array<String>} IDs
 */
function addEdges(source, target, IDs) {
  IDs.forEach((ID) => {
    addEdge(source, target, ID);
  });
}

/**
 * The function to add edge ID
 * @param {String} source
 * @param {String} target
 * @param {String} ID
 */
function addEdge(source, target, ID) {
  dataNodeMap.get(source).hoverEdges.add(ID);
  dataNodeMap.get(target).hoverEdges.add(ID);
  if (!dataNodeMap.get(source).next.has(target)) {
    dataNodeMap.get(source).next.set(target, new Set());
  }
  dataNodeMap
      .get(source)
      .next.get(target)
      .add(ID);
}

/**
 * The function to get public parent scope of two scope
 * @param {Array<String>} sourceParentList
 * @param {Array<String>} targetParentList
 * @return {Array<String>} publicScopeList
 */
function getPublicScopeList(sourceParentList, targetParentList) {
  const publicScopeList = [];
  for (let i = 0; i < sourceParentList.length; i++) {
    if (sourceParentList[i] === targetParentList[i]) {
      publicScopeList.push(sourceParentList[i]);
    }
  }
  return publicScopeList;
}

/**
 * The function to create normal targets
 * @param {String} start
 * @param {String} end
 * @return {Array<String>} ID
 */
function createNormalEdges(start, end) {
  const source = `${start}${OUT_PORT_SUFFIX}`;
  const target = `${end}${IN_PORT_SUFFIX}`;
  const ID = `${start}${EDGE_SEPARATOR}${end}`;
  dataNodeMap.get(start).edges.set(ID, {
    sources: [source],
    targets: [target],
  });
  return ID;
}

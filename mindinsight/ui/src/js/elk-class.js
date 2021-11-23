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
  DisplayedGraph,
  DisplayedNode,
  DisplayedEdge,
  DisplayedMap,
} from './displayed-class';
import {
  NODE_TYPE,
  OUT_PORT_SUFFIX,
  IN_PORT_SUFFIX,
  INPUT,
  OUTPUT,
} from './const';
import {labelOptions, childrenOptions} from './config';
import CommonProperty from '@/common/common-property';

/**
 * The class of ElkDataNode
 */
export class ElkDataNode {
  /**
   * The constructor of ElkDataNode
   * @param {Object} object
   */
  constructor({
    id,
    name,
    label,
    type,
    layerType,
    children,
    parent,
    root,
    scope,
    expanded,
    stacked,
    input,
    output,
    specialNodesCnt,
  }) {
    this.id = id;
    this.label = label;
    this.name = name;
    this.type = type;
    this.layerType = layerType;
    this.children = children;
    this.parent = parent;
    this.root = root;
    this.scope = scope;
    this.expanded = expanded;
    this.stacked = stacked;
    this.edges = new Map();
    this.next = new Map();
    this.input = input;
    this.output = output;
    this.hoverEdges = new Set();
    this.hiddenEdges = {
      [INPUT]: new Set(),
      [OUTPUT]: new Set(),
    };
    this.specialNodesCnt = specialNodesCnt;
  }
}

/**
 * The class of ElkRootNode
 */
export class ElkRootNode {
  /**
   * The constructor of ELKBasicNode
   * @param {Array<ElkNode>} children
   * @param {Array<ElkEdge>} edges
   * @param {Number} themeIndex
   */
  constructor(children, edges, themeIndex) {
    this.id = 'root';
    this.children = children;
    this.edges = edges;
    this.getDisplayedGraph = () => {
      const getFillColor = ({type, layerType, children}) => {
        const themeArray = CommonProperty.themes[themeIndex];
        if (
          [
            NODE_TYPE.basic_scope,
            NODE_TYPE.name_scope,
          ].includes(type)
        ) {
          if (children.length) {
            let re = '';
            themeArray.forEach((item) => {
              if (item.key === '--expanded-node-fill') re += item.value;
            });
            return re;
          } else {
            let re = '';
            themeArray.forEach((item) => {
              if (item.key === '--unexpanded-node-fill') re += item.value;
            });
            return re;
          }
        } else {
          let re = '';
          themeArray.forEach((item) => {
            if (item.key === '--unexpanded-node-fill') re += item.value;
          });
          return re;
        }
      };
      const result = new DisplayedGraph();
      const map = new DisplayedMap();
      const transition = new Map();
      if (this.x === undefined) return result;
      const flatten = (target, result) => {
        if (target.edges) {
          target.edges.forEach((edge) => {
            if (edge.sections) {
              let points = '';
              const data = edge.sections[0];
              points += `${(data.startPoint.x +=
                target.x)},${(data.startPoint.y += target.y)} `;
              if (data.bendPoints) {
                data.bendPoints.forEach((point) => {
                  points += `${(point.x += target.x)},${(point.y +=
                    target.y)} `;
                });
              }
              points += `${(data.endPoint.x += target.x)},${(data.endPoint.y +=
                target.y)}`;
              const newEdge = new DisplayedEdge(edge.id, points, edge.outline);
              map.visEdgeMap.set(edge.id, newEdge);
              result.edges.push(newEdge);
            }
          });
          if (target.children.length) {
            target.children.forEach((child) => {
              child.x += target.x;
              child.y += target.y;
              child.fill = getFillColor(child);
              const node = new DisplayedNode(child);
              result.nodes.push(node);
              map.visNodeMap.set(node.id, node);
              // Transition
              if (
                [NODE_TYPE.basic_scope, NODE_TYPE.name_scope].includes(
                    node.type,
                )
              ) {
                transition.set(child.id, {
                  x: node.x,
                  y: node.y,
                  width: node.width,
                  height: node.height,
                });
              }
              child.ports.forEach((p) => {
                if (!p.isHidden) {
                  if (child.type === NODE_TYPE.basic_scope) {
                    if (p.x !== 0) p.x -= 15;
                    p.x += child.x;
                  } else {
                    p.x =
                      p.x +
                      child.x -
                      7.5;
                  }
                  p.y =
                    child.type === NODE_TYPE.name_scope
                      ? p.y + child.y - child.height / 2
                      : p.y + child.y - 7.5;
                  p.opacity = 1;
                  result.ports.push(p);
                  map.visPortMap.set(p.id, p);
                }
              });
              if (child.children.length) {
                flatten(child, result);
              }
            });
          }
        }
      };
      flatten(this, result);
      return new FlattenedGraph(result, map, transition);
    };
  }
}

/**
 * The class of FlattenedGraph
 */
export class FlattenedGraph {
  /**
   * The constructor of FlattenedGraph
   * @param {Array} array
   * @param {Map} map
   * @param {Map} transition
   */
  constructor(array, map, transition) {
    this.array = array;
    this.map = map;
    this.transition = transition;
  }
}

/**
 * The class of ELKNode
 */
export class ElkNode {
  /**
   * The constructor of ELKNode
   * @param {Object} ELKNode
   */
  constructor({
    id,
    type,
    layerType,
    label,
    name,
    width,
    height,
    ports,
    rects,
    specialNodesCnt,
    expanded,
  }) {
    this.id = id;
    this.type = type;
    this.layerType = layerType;
    this.width = width;
    this.height = height;
    this.ports = ports;
    this.children = [];
    this.edges = [];
    this.label = label;
    this.name = name;
    this.labels = [
      {
        layoutOptions: labelOptions,
        height: 10,
      },
    ];
    this.layoutOptions = Object.assign({}, childrenOptions, {
      'nodeSize.minimum': `[${width}, ${height}]`,
    });
    this.rects = rects;
    this.specialNodesCnt = specialNodesCnt;
    this.expanded = expanded;
  }
}

/**
 * The class of ElkEdge
 */
export class ElkEdge {
  /**
   * The constructor of ElkEdge
   * @param {String} id
   * @param {Array} sources
   * @param {Array} targets
   */
  constructor(id, sources, targets) {
    this.id = id;
    this.sources = sources;
    this.targets = targets;
  }
}

/**
 * The class of ElkPort
 */
export class ElkPort {
  /**
   * The constructor of ElkPort
   * @param {String} owner
   * @param {Boolean} isInput
   * @param {Boolean} isHidden
   */
  constructor(owner, isInput, isHidden) {
    this.id = `${owner}${isInput ? IN_PORT_SUFFIX : OUT_PORT_SUFFIX}`;
    this.owner = owner;
    this.isInput = isInput;
    this.isHidden = isHidden;
    this.properties = isInput
      ? {'port.side': 'WEST'}
      : {'port.side': 'EAST'};
  }
}

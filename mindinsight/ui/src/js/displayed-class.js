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
 * The class of DisplayedGraph
 */
export class DisplayedGraph {
  /**
   * The constructor of DisplayedGraph
   */
  constructor() {
    this.nodes = [];
    this.edges = [];
    this.ports = [];
  }
}

/**
 * The class of DisplayedMap
 */
export class DisplayedMap {
  /**
   * The constructor of DisplayedMap
   */
  constructor() {
    this.visNodeMap = new Map();
    this.visEdgeMap = new Map();
    this.visPortMap = new Map();
  }
}

/**
 * The class of DisplayedEdge
 */
export class DisplayedEdge {
  /**
   * The constructor of DisplayedEdge
   * @param {String} id
   * @param {String} points
   * @param {Boolean} outline
   */
  constructor(id, points, outline) {
    this.id = id;
    this.points = points;
    this.selected = false;
    this.outline = outline;
  }
}

/**
 * The class of DisplayedNode
 */
export class DisplayedNode {
  /**
   * The constructor of DisplayedNode
   * @param {Object} Object
   */
  constructor({id, x, y, width, height, type, label, name, fill, specialNodesCnt, expanded}) {
    this.id = id;
    this.x = x;
    this.y = y;
    this.width = width;
    this.height = height;
    this.type = type;
    this.label = label;
    this.name = name;
    this.click = false;
    this.hover = false;
    this.selected = false;
    this.opacity = 1;
    this.fill = fill ? fill : '#ffffff';
    this.specialNodesCnt = specialNodesCnt;
    this.expanded = expanded;
  }
}

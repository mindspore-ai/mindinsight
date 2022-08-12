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
import * as d3 from "d3";
import { gradientColor } from "@/js/communicate-view/get-gradient-color.js";
import { Lasso } from "@/js/communicate-view/lasso.js";
import { Matrix } from "@/js/communicate-view/matrix.js";
import * as _ from "lodash";
/**
 * The function to create communication graph
 * @param {Number} w weight of the graph
 * @param {Number} h height of the graph
 * @param {Object} father parent dom of the graph
 * @return
 */
export function Graph(w, h, father) {
  this.w = w;
  this.h = h;
  this.nodes = [];
  this.links = [];
  this.currNodes = [];
  this.currLinks = [];
  this.min_ratio = 1;
  this.max_ratio = 0;
  this.inputNodes = [];
  this.inputLinks = [];
  this.forceNodes = [];
  this.forceLinks = [];
  this.netNodes = [];
  this.netLinks = [];
  this.staticNodes = [];
  this.staticLinks = [];
  this.matrix_size = w * 0.8; // 设置矩阵的宽
  this.father = father;
}

/**
 * The function to change the size of the matrix
 * @param {Number} newsize
 * @return
 */
Graph.prototype.setMatrixSize = function (newsize) {
  if (newsize != 0) {
    this.matrix_size = newsize;
  } else {
    this.matrix_size = this.w * 0.5;
  }
};

/**
 * The function to init communication graph
 * @param {Array} links
 * @param {Array} nodes
 * @return
 */
Graph.prototype.init = function (links, nodes) {
  this.nodes = nodes;
  this.links = links;
  d3.selectAll("#networklayer").remove();
  this.layer = d3.select("#force");
  this.svg = d3.select("#mainsvg");
  initDefs(this.svg);
  var minR = 1,
    maxR = 0;
  this.nodes.forEach((d) => {
    d.time_ratio = d.c_cost / (d.c_cost + d.w_cost);
    d.showable = true;
    minR = Math.min(d.time_ratio, minR);
    maxR = Math.max(d.time_ratio, maxR);
  });
  this.min_ratio = minR;
  this.max_ratio = maxR;

  this.renderNet();
};
Graph.prototype.selectOpname = "";
Graph.prototype.setSelectOpname = function (op) {
  this.father.setSelectErrorOp(op);
};
Graph.prototype.getMatrixSize = function () {
  return this.matrix_size;
};

/**
 * The function to render communication graph in the svg dom
 * @return
 */
Graph.prototype.renderNet = function () {
  this.layer.select("#networklayer").remove();
  d3.select("#mainsvg > g.matrix-label").remove();
  var network = this.layer.append("g").attr("id", "networklayer");
  var forceLinks = _.cloneDeep(this.links);
  var forceNodes = _.cloneDeep(this.nodes);
  d3.selectAll("#matrix > *").remove();

  var simulation = d3
    .forceSimulation()
    .force(
      "link",
      d3
        .forceLink()
        .id(function (d) {
          return d.id;
        })
        .distance(function (d) {
          return 150;
        })
    )
    .force("charge", d3.forceManyBody())
    .force("center", d3.forceCenter(this.w / 2, this.h / 2));
  // .force("x", d3.forceX(this.w))
  // .force("y", d3.forceY(this.h));

  simulation.nodes(forceNodes).on("tick", (d) => {
    forceNodes.forEach((n) => {
      if (n.x < 50) {
        n.x = 50;
      }
      if (n.x > this.w - 50) {
        n.x = this.w - 50;
      }
      if (n.y < 50) {
        n.y = 50;
      }
      if (n.y > this.h - 20) {
        n.y = this.h - 20;
      }
    });
    handleTick(node, link, label);
  });
  simulation.force("link").links(forceLinks);
  var link = initLinks(forceLinks, network);
  var node = initNodes(
    forceNodes,
    network,
    this.min_ratio,
    this.max_ratio,
    simulation
  );
  var label = initLabels(forceNodes, network);
  window.lasso = new Lasso();
  window.lasso.bind();
};

/**
 * Executed when the node graph is perturbed by force
 * @param {Object} node d3 selection of nodes
 * @param {Object} link d3 selection of links
 * @param {Object} label d3 selection of labels
 * @return
 */
function handleTick(node, link, label) {
  link.attr("d", function (d) {
    var x1 = d.source.x,
      x2 = d.target.x,
      y1 = d.source.y,
      y2 = d.target.y;

    var dx = x2 - x1,
      dy = y2 - y1,
      dr = Math.sqrt(dx * dx + dy * dy),
      // Defaults for normal edge.
      drx = dr,
      dry = dr,
      xRotation = 0, // degrees
      largeArc = 0, // 1 or 0
      sweep = 1; // 1 or 0

    // Self edge.
    if (x1 === x2 && y1 === y2) {
      xRotation = 45;
      largeArc = 1;
      drx = 20;
      dry = 20;
      x2 = x2 + 1;
      y2 = y2 + 1;
    }

    return (
      "M" +
      x1 +
      "," +
      y1 +
      "A" +
      drx +
      "," +
      dry +
      " " +
      xRotation +
      "," +
      largeArc +
      "," +
      sweep +
      " " +
      x2 +
      "," +
      y2
    );
  });
  label
    .attr("x", function (d) {
      return d.x + 10;
    })
    .attr("y", function (d) {
      return d.y + 3;
    });
  node
    .attr("cx", function (d) {
      return d.x;
    })
    .attr("cy", function (d) {
      return d.y;
    });
}

/**
 * Function to init label dom
 * @param {Array} nodesData
 * @param {Object} network communication graph dom
 * @return
 */
function initLabels(nodesData, network) {
  network.select(".labels").remove();
  var label = network
    .append("g")
    .attr("class", "labels")
    .selectAll("text")
    .data(nodesData)
    .enter()
    .append("text")
    .attr("class", "label")
    .attr("id", function (d) {
      return "l" + d.id;
    })
    .text(function (d) {
      if (d.showable) {
        return d.label;
      } else {
        return "";
      }
    });
  return label;
}
/**
 * Function to init nodes dom
 * @param {Array} nodesData
 * @param {Object} network communication graph dom
 * @param {Number} minR min value
 * @param {Number} maxR max value
 * @param {Object} simulation simulation of d3 force
 * @param {Boolean} draggable whether the node can be dragged
 * @return
 */
function initNodes(
  nodesData,
  network,
  minR,
  maxR,
  simulation,
  draggable = true
) {
  network.select(".nodes").remove();

  var node = network
    .append("g")
    .attr("class", "nodes")
    .selectAll("circle")
    .data(nodesData)
    .enter()
    .append("circle")
    .attr("visibility", function (d) {
      if (!d.showable) {
        return "hidden";
      } else {
        return "visible";
      }
    })
    .attr("r", function (d) {
      return Math.abs(Math.log(d.c_cost + d.w_cost));
    })
    .attr("id", function (d) {
      return d.id;
    })
    .style("fill", function (d) {
      return gradientColor("#fbe7d5", "#e6882e", minR, maxR, d.time_ratio);
    })
    .attr("pointer-events", "all")
    .on("mouseenter", function (d) {
      d3.select(this).attr("stroke", "red");
    })
    .on("mouseleave", function (d) {
      d3.select(this).attr("stroke", "none");
    });
  if (draggable) {
    node.call(
      d3
        .drag()
        .on("start", function (d) {
          if (d.showable) {
            if (!d3.event.active) simulation.alphaTarget(0.1).restart();
            d.fx = d.x;
            d.fy = d.y;
          }
        })
        .on("drag", function (d) {
          if (d.showable) {
            d.fx = d3.event.x;
            d.fy = d3.event.y;
          }
        })
        .on("end", function (d) {
          if (d.showable) {
            if (!d3.event.active) simulation.alphaTarget(0);
          }
        })
    );
  }

  return node;
}

/**
 * Function to init links dom
 * @param {Array} linksData
 * @param {Object} network communication graph dom
 * @return
 */
function initLinks(linksData, network) {
  network.select(".links").remove();
  var link = network
    .append("g")
    .attr("class", "links")
    .attr("id", "links")
    .selectAll("path")
    .data(linksData)
    .enter()
    .append("path")
    .style("fill", "none")
    .style("stroke", function (d) {
      if (d.link_type == "SDMA") return "#cecfd1";
      else return "#a1a1a1";
    })
    .attr("stroke-width", function (d) {
      return 1;
    })
    .attr("marker-end", function (d) {
      if (d.link_type == "SDMA") return "url(#arrowSDMA)";
      else return "url(#arrowOther)";
    })
    .attr("pointer-events", "all")
    .style("cursor", "pointer");

  return link;
}

function initDefs(svg) {
  var defs = svg.append("defs");
  var arrowMarkerSDMA = defs
    .append("marker")
    .attr("id", "arrowSDMA")
    .attr("markerUnits", "strokeWidth")
    .attr("markerWidth", "8")
    .attr("markerHeight", "8")
    .attr("viewBox", "0 0 12 12")
    .attr("refX", "13")
    .attr("refY", "6")
    .attr("orient", "auto");
  var arrow_path = "M2,2 L10,6 L2,10 L4,6 L2,2";
  arrowMarkerSDMA.append("path").attr("d", arrow_path).attr("fill", "#cecfd1");

  var arrowMarkerOther = defs
    .append("marker")
    .attr("id", "arrowOther")
    .attr("markerUnits", "strokeWidth")
    .attr("markerWidth", "8")
    .attr("markerHeight", "8")
    .attr("viewBox", "0 0 12 12")
    .attr("refX", "13")
    .attr("refY", "6")
    .attr("orient", "auto");
  var arrow_path = "M2,2 L10,6 L2,10 L4,6 L2,2";
  arrowMarkerOther.append("path").attr("d", arrow_path).attr("fill", "#a1a1a1");
}
/**
 * Function to get links data
 * @return {Array}
 */
Graph.prototype.getLinks = function () {
  return this.links;
};
/**
 * Function to get nodes data
 * @param {Array} nameList device id of target node
 * @return {Object} nodes data
 */
Graph.prototype.getNodesData = function (nameList) {
  var resData = {};
  this.nodes.forEach((node) => {
    if (nameList.includes(node.id)) {
      resData[node.id] = { c_cost: node.c_cost, w_cost: node.w_cost };
    }
  });
  return resData;
};

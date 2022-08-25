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

export function Minimap(store) {
  this.width = 0;
  this.height = 0;
  this.svgWidth = 0;
  this.svgHeight = 0;
  this.heightScale = 0;
  this.widthScale = 0;
  this.lastTransform = { k: 1, x: 0, y: 0 };
  this.transform = [0, 0, 1];
  this.store = store;
}

Minimap.prototype.create = function () {
  var nodes = d3.select(".svgCanvas>.minimap").selectAll("circle");
  var minX = 10000,
    maxX = -10000;

  nodes._groups[0].forEach((d) => {
    minX = Math.min(minX, d.getBBox().x);
    maxX = Math.max(maxX, d.getBBox().x);
  });

  this.svgHeight =
    document.getElementsByClassName("strategy-view")[0].clientHeight;
  //  -
  // document.getElementsByClassName("view-header")[0].clientHeight;
  this.svgWidth =
    document.getElementsByClassName("profile-graph")[0].clientWidth;
  this.width = this.svgWidth;
  this.height = this.svgHeight * 0.1;
  this.bigWidth = d3
    .select(".wrapperInner")
    .select("#profile-graph")
    .attr("width");
  var bigHeight = d3
    .select(".wrapperInner")
    .select("#profile-graph")
    .attr("height");
  this.store.setMiniBox(this.bigWidth, bigHeight);

  var container = d3.select(".svgCanvas>.minimap");
  container.attr("clip-path", "url(#minimapClipPath)");

  container.attr(
    "transform",
    "translate(0," + (this.svgHeight - this.height) + ")"
  );

  container
    .select(".background")
    .attr("height", this.height)
    .attr("width", this.width)
    .style("fill", "var(--bg-color)")
    .style("stroke", "gray");
  var box = container.select("#graph-container").node().getBBox();
  this.widthScale = this.width / (maxX - minX);
  this.heightScale = this.height / box.height;
  this.widthScale = Math.min(this.widthScale, this.heightScale);
  this.store.setMiniScale(this.widthScale);
  container
    .select("#graph-container")
    .attr(
      "transform",
      "scale(" +
        this.widthScale +
        ")" +
        "translate(" +
        -box.x +
        "," +
        -box.y +
        ")"
    );
  this.generateFrame();
};

Minimap.prototype.generateFrame = function () {
  var frame = d3.select(".minimap>.frame");
  var window = frame.select(".background");
  window
    .attr("width", this.width)
    .attr("height", this.svgHeight * 0.9)
    .style("stroke", "#111111")
    .style("fill-opacity", "0.2")
    .style("fill", "var(--font-color)")
    .style("filter", "url(#minimapDropShadow)")
    .style("cursor", "move")
    .attr("transform", "scale(" + this.widthScale + ")");

  var frameEl = document.getElementsByClassName("frame")[0];
  var minimapEl = document.getElementById("minimap-background");
  minimapEl.onwheel = (e) => {
    this.transform = this.store.getTransform();
    let delta = e.wheelDelta && (e.wheelDelta > 0 ? 1 : -1);
    if (delta > 0) {
      this.transform[2] = this.transform[2] * 1.1;
    } else if (delta < 0) {
      this.transform[2] = this.transform[2] / 1.1;
    }
    frame.attr(
      "transform",
      "translate(" +
        [this.transform[0], this.transform[1]].join(" ") +
        ")" +
        "scale(" +
        this.transform[2] +
        ")"
    );
    this.store.changeMinimap(this.transform);
  };
  frameEl.onwheel = (e) => {
    this.transform = this.store.getTransform();
    let delta = e.wheelDelta && (e.wheelDelta > 0 ? 1 : -1);
    if (delta > 0) {
      this.transform[2] = this.transform[2] * 1.1;
    } else if (delta < 0) {
      this.transform[2] = this.transform[2] / 1.1;
    }
    frame.attr(
      "transform",
      "translate(" +
        [this.transform[0], this.transform[1]].join(" ") +
        ")" +
        "scale(" +
        this.transform[2] +
        ")"
    );
    this.store.changeMinimap(this.transform);
  };
  var offsetX, offsetY;
  var dragging = false;
  frameEl.onmousedown = (e) => {
    dragging = true;
    offsetX = e.offsetX;
    offsetY = e.offsetY;
  };
  frameEl.onmouseup = (e) => {
    if (dragging) {
      this.transform = this.store.getTransform();
      this.transform[0] = this.transform[0] + (e.offsetX - offsetX);
      this.transform[1] = this.transform[1] + (e.offsetY - offsetY);

      frame.attr(
        "transform",
        "translate(" +
          [this.transform[0], this.transform[1]].join(" ") +
          ")" +
          "scale(" +
          this.transform[2] +
          ")"
      );
      this.store.changeMinimap(this.transform);
      dragging = false;
    }
  };
  frameEl.onmouseleave = (e) => {
    if (dragging) {
      this.transform = this.store.getTransform();
      this.transform[0] = this.transform[0] + (e.offsetX - offsetX);
      this.transform[1] = this.transform[1] + (e.offsetY - offsetY);

      frame.attr(
        "transform",
        "translate(" +
          [this.transform[0], this.transform[1]].join(" ") +
          ")" +
          "scale(" +
          this.transform[2] +
          ")"
      );
      this.store.changeMinimap(this.transform);
      dragging = false;
    }
  };
  frameEl.onmousemove = (e) => {
    if (dragging) {
      var tmpT = [0, 0, this.transform[2]];
      tmpT[0] = this.transform[0] + (e.offsetX - offsetX);
      tmpT[1] = this.transform[1] + (e.offsetY - offsetY);

      frame.attr(
        "transform",
        "translate(" +
          [tmpT[0], tmpT[1]].join(" ") +
          ")" +
          "scale(" +
          tmpT[2] +
          ")"
      );
    }
  };
};

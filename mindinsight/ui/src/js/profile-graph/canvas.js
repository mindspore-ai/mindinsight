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
import { Minimap } from "@/js/profile-graph/minimap.js";
import { Store } from "@/js/profile-graph/store.js";
export function Canvas(father) {
  this.width = 0;
  this.height = 0;
  this.wrapperBorder = 0;
  this.minimap = null;
  this.minimapPadding = 0;
  this.minimapScale = 0.25;
  this.svgHeight = 0;
  this.svgWidth = 0;
  this.zoom = null;
  this.viewBox = [0, 0, 0, 0];
  this.lastTransform = { k: 1, x: 0, y: 0 };
  this.store = new Store(this, father);
  this.father = father;
}

Canvas.prototype.create = function (stageNum) {
  this.svgHeight =
    document.getElementsByClassName("strategy-view")[0].clientHeight;
  this.svgWidth =
    document.getElementsByClassName("profile-graph")[0].clientWidth;
  this.width = this.svgWidth;
  this.height = this.svgHeight * 0.9;

  var svg = d3.select(".svgCanvas");
  svg
    .attr("width", this.svgWidth)
    .attr("height", this.svgHeight)
    .style("overflow", "hidden");

  this.generateDefs();

  var outerWrapper = d3.select(".svgCanvas").select(".wrapperOuter");
  outerWrapper.attr("transform", "translate(0," + this.minimapPadding + ")");
  outerWrapper
    .select(".background")
    .attr("width", this.width + 2 * this.wrapperBorder)
    .attr("height", this.height + 2 * this.wrapperBorder)
    .style("fill", "var(--bg-color)");

  var innerWrapper = outerWrapper.select(".wrapperInner");
  innerWrapper
    .attr("clip-path", "url(#wrapperClipPath)")
    .attr(
      "transform",
      "translate(" + this.wrapperBorder + "," + this.wrapperBorder + ")"
    );

  innerWrapper
    .select(".background")
    .attr("width", this.width)
    .attr("height", this.height)
    .style("fill", "var(--bg-color)")
    .style("cursor", "move");

  var panCanvas = innerWrapper.select(".panCanvas");
  panCanvas.style("cursor", "move");

  var box = innerWrapper.select("#graph-container").node().getBBox();

  innerWrapper
    .select("#graph-container")
    .attr("transform", "translate(" + -box.x + "," + -box.y + ")");
  this.father.setBoxTransform([box.x, box.y]);

  var scale = stageNum >= 2 ? (500 * 2) / this.height : 500 / this.height;
  innerWrapper
    .select("#profile-graph")
    .attr("viewBox", "0 0 " + this.width * scale + " " + this.height * scale)
    .attr("height", this.height)
    .attr("width", this.width);

  this.viewBox = innerWrapper
    .select("#profile-graph")
    .attr("viewBox")
    .split(" ")
    .map((d) => Number(d));

  var minimap = new Minimap(this.store);
  minimap.create();
  this.father.viewboxChanged(this.viewBox);
  this.store.setViewBox(this.viewBox);
  this.store.changeViewBox(this.viewBox);

  var innerEl = document.getElementsByClassName("wrapperInner")[0];
  innerEl.onwheel = (e) => {
    let delta = e.wheelDelta && (e.wheelDelta > 0 ? 1 : -1);
    this.viewBox = this.store.getViewBox();
    if (delta > 0) {
      this.viewBox[2] = this.viewBox[2] / 1.1;
      this.viewBox[3] = this.viewBox[3] / 1.1;
    } else if (delta < 0) {
      this.viewBox[2] = this.viewBox[2] * 1.1;
      this.viewBox[3] = this.viewBox[3] * 1.1;
    }
    innerWrapper
      .select("#profile-graph")
      .attr("viewBox", this.viewBox.join(" "));
    this.father.viewboxChanged(this.viewBox);
    this.store.changeViewBox(this.viewBox);
  };
  var offsetX, offsetY;
  var dragging = false;
  innerEl.onmousedown = (e) => {
    dragging = true;
    offsetX = e.offsetX;
    offsetY = e.offsetY;
  };
  innerEl.onmouseup = (e) => {
    if (dragging) {
      this.viewBox = this.store.getViewBox();
      this.viewBox[0] = this.viewBox[0] - e.offsetX + offsetX;
      this.viewBox[1] = this.viewBox[1] - e.offsetY + offsetY;
      offsetX = e.offsetX;
      offsetY = e.offsetY;
      this.father.viewboxChanged(this.viewBox);
      this.changeViewBox(this.viewBox, true);
      dragging = false;
    }
  };
};

Canvas.prototype.getViewBox = function () {
  return this.viewBox;
};

Canvas.prototype.changeViewBox = function (newViewBox, changeMinimap) {
  this.viewBox = newViewBox;
  d3.select(".svgCanvas")
    .select(".wrapperOuter")
    .select(".wrapperInner")
    .select("#profile-graph")
    .attr("viewBox", this.viewBox.join(" "));
  if (changeMinimap == true) {
    this.father.viewboxChanged(this.viewBox);
    this.store.changeViewBox(this.viewBox);
  }
};

Canvas.prototype.generateDefs = function () {
  var svgDefs = d3.select(".svgCanvas").select("defs");

  svgDefs
    .select("#wrapperClipPath > rect")
    .attr("width", this.width)
    .attr("height", this.height);

  svgDefs
    .select("#minimapClipPath > rect")
    .attr("width", this.width)
    .attr("height", this.svgHeight * 0.1);
};

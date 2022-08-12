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
export function Store(canvas, father) {
  this.viewBox = [0, 0, 0, 0];
  this.miniTransform = [0, 0, 1];
  this.miniScale = 1;
  this.miniWidth = 0;
  this.miniHeight = 0;
  this.canvas = canvas;
  this.father = father;
}
Store.prototype.setMiniScale = function (scale) {
  this.miniScale = scale;
};
Store.prototype.setMiniBox = function (width, height) {
  this.miniWidth = width;
  this.miniHeight = height;
};
Store.prototype.setViewBox = function (viewBox) {
  this.viewBox = viewBox;
};
Store.prototype.setMiniTransform = function (transform) {
  this.miniTransform = transform;
};
Store.prototype.changeViewBox = function (viewBox) {
  this.viewBox = viewBox;

  var frame = d3.select(".minimap>.frame");
  var xtrans = viewBox[0] * this.miniScale;
  var ytrans = viewBox[1] * this.miniScale;
  var s = viewBox[2] / this.miniWidth;
  frame.attr(
    "transform",
    "translate(" + xtrans + " " + ytrans + ")" + "scale(" + s + ")"
  );
  this.miniTransform = [xtrans, ytrans, s];
};
Store.prototype.changeMinimap = function (transform) {
  this.miniTransform = transform;
  var viewBox = [0, 0, 0, 0];
  viewBox[0] = transform[0] / this.miniScale;
  viewBox[1] = transform[1] / this.miniScale;
  viewBox[2] = transform[2] * this.miniWidth;
  viewBox[3] = transform[2] * this.miniHeight;
  this.viewBox = viewBox;
  this.father.viewboxChanged(viewBox);
  this.canvas.changeViewBox(this.viewBox, false);
};

Store.prototype.getViewBox = function () {
  return this.viewBox;
};

Store.prototype.getTransform = function () {
  // console.log(this.miniTransform);
  return this.miniTransform;
};

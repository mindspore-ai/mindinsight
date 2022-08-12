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
import { lasso } from "d3-lasso";
import { Matrix } from "@/js/communicate-view/matrix.js";

/**
 * Function to init lasso
 * @return
 */
export function Lasso() {
  d3.select(".lasso").remove();
  this.circles = d3.selectAll("circle");
  this.svg = d3.select("#mainsvg");
  global.d3 = d3;
  this.lasso = lasso();
}

/**
 * Function to bind lasso on graph
 * @return
 */
Lasso.prototype.bind = function () {
  var lasso = this.lasso
    .closePathSelect(true)
    .closePathDistance(100)
    .items(this.circles)
    .targetArea(this.svg)
    .on("end", function () {
      var selected = lasso.selectedItems()["_groups"][0];
      var nodeList = [];
      selected.forEach(function (d) {
        var id = d3.select(d).attr("id");
        nodeList.push(id);
      });
      if (!nodeList.length) return;
      nodeList = nodeList.sort(
        (a, b) =>
          Number(a.replace("device", "")) - Number(b.replace("device", ""))
      );
      if (nodeList.length) {
        var m = new Matrix();
        m.create(nodeList);
      }
      d3.selectAll("#force > *").style("display", "none");
      d3.selectAll("#path > *").style("display", "none");
    });
  this.svg.call(this.lasso);
};
/**
 * Function to unbind lasso on graph
 * @return
 */
Lasso.prototype.unbind = function () {
  d3.select(".lasso").remove();
};

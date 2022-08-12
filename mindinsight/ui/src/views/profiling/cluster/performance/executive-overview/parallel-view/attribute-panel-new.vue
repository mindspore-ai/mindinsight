<!--
Copyright 2022 Huawei Technologies Co., Ltd.All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
<style scope>
.attribute-panel-container {
  position: absolute;
  top: 50px;
  right: 10px;
  width: 300px;
  background: #fafafa;
}
#attribute-collapse .lee-collapse-item .itemtab {
  background: #ececec;
  padding: 0 10px;
  height: 30px;
  border-radius: 4px;
}
#attribute-collapse .lee-collapse-item .itemcontent {
  padding-bottom: 10px;
}
#attribute-collapse .lee-collapse-item .itemcontentw {
  padding: 0 10px;
  border: none;
  max-height: 190px;
  overflow-y: scroll;
}
#attribute-collapse .lee-collapse-item:first-child .itemcontentw {
  max-height: 100px;
}
#attribute-collapse .lee-collapse {
  border-radius: 4px;
}
#attribute-collapse .lee-collapse-item {
  border-bottom: 1px solid #fff;
}
.second-title {
  height: 24px;
  line-height: 24px;
  font-size: 14px;
  font-weight: 600;
  -ms-flex-negative: 0;
  flex-shrink: 0;
}
.third-title {
  height: 24px;
  line-height: 24px;
  font-size: 14px;
  font-weight: 500;
  -ms-flex-negative: 0;
  flex-shrink: 0;
}
.graph-strategy-info {
  padding-top: 5px;
}

#write blockquote {
  margin-bottom: 4px;
  margin-top: 4px;
  padding: 4px 8px 4px 8px;
  font-size: 0.9em;
  background: none;
  border-left: 3px solid #aaa;
  /* color: #6a737d; */
  overflow: auto;
  -webkit-overflow-scrolling: touch;
}
#write blockquote p {
  line-height: 26px;
}
</style>

<script>
import $store from "../store";
import { LeeCollapse, LeeCollapseItem } from "leevueplugin";
import { getSpecialNodesMap } from "@/js/profile-graph/build-graph.js";

export default {
  components: {
    LeeCollapse,
    LeeCollapseItem,
  },
  data() {
    return {
      expname: ["1"],
      selectedNode: null,
      nodeMaps: [],
      nodeGroupIndex: "",
      specialNodesMap: {},
    };
  },
  watch: {
    storeSelectedGraphNode: function (val) {
      // console.log(this.nodeMaps);
      // console.log(val[0], val[1]);
      this.selectedNode = val;
      // this.selectedNode.input_shape = val[1];
      var strategyStr = this.selectedNode.parallel_shard;
      strategyStr = strategyStr.slice(1, strategyStr.length - 1);
      var pos = strategyStr.indexOf("[");
      var p1 = [],
        p2 = [];
      while (pos > -1) {
        p1.push(pos);
        pos = strategyStr.indexOf("[", pos + 1);
      }
      pos = strategyStr.indexOf("]");
      while (pos > -1) {
        p2.push(pos);
        pos = strategyStr.indexOf("]", pos + 1);
      }
      // console.log(strategyStr.slice(p1[0], p2[0] + 1));
      this.selectedNode.input_strategy = [];
      for (var i = 0; i < p1.length; i++) {
        this.selectedNode.input_strategy.push(
          strategyStr.slice(p1[i], p2[i] + 1)
        );
      }

      // var leftCIndex=strategyStr.
      // this.selectedNode.input_strategy = this.selectedNode.parallel_shard.split;
      this.nodeGroupIndex = Math.floor((this.selectedNode.y + 200) / 500);
      this.expname = ["1", "2"];
      // console.log(this.selectedNode);
      this.selectedNode.input_shape = [];
      this.selectedNode.input_name = [];
      this.selectedNode.input.forEach((input) => {
        if (Object.keys(this.nodeMaps[this.nodeGroupIndex]).includes(input)) {
          this.selectedNode.input_shape.push(
            '[ "' +
              this.nodeMaps[this.nodeGroupIndex][input].output_shape.join(
                '", "'
              ) +
              '" ]'
          );
          var input_name =
            this.nodeMaps[this.nodeGroupIndex][input].name.split("/");
          input_name = input_name[input_name.length - 1];
          this.selectedNode.input_name.push(input_name);
        } else {
          this.selectedNode.input_name.push(input + "(Const)");
          this.selectedNode.input_shape.push(undefined);
        }
      });
      // console.log(getSpecialNodesMap())
    },
    storeNodeMaps: function (val) {
      this.nodeMaps = val;
      // console.log(this.nodeMaps);
      this.specialNodesMap = getSpecialNodesMap();
    },
  },
  computed: {
    storeSelectedGraphNode() {
      return $store.state.selectedGraphNode;
    },
    storeNodeMaps() {
      return $store.state.nodeMaps;
    },
  },
  methods: {
    handleChange(val) {
      // console.log(val);
    },
    getSpecialNodesMap() {
      return getSpecialNodesMap();
    },
  },
};
</script>

<template>
  <div class="attribute-panel-container" id="attribute-collapse">
    <LeeCollapse v-model="expname" @change="handleChange">
      <LeeCollapseItem title="Special operator statiatics" name="1">
        <div class="graph-strategy-info">
          <div class="second-title" style="font-size: 10px">
            {{ this.$t("profiling.hasStrategy") }}:
            <span style="font-weight: normal">{{
              specialNodesMap["hasStrategy"]
                ? specialNodesMap["hasStrategy"]
                : 0
            }}</span>
          </div>
          <div class="second-title" style="font-size: 10px">
            {{ this.$t("profiling.redistribution") }}:
            <span style="font-weight: normal">{{
              specialNodesMap["Redistribution"]
                ? specialNodesMap["Redistribution"]
                : 0
            }}</span>
          </div>
          <div class="second-title" style="font-size: 10px">
            {{ this.$t("profiling.gradientAggregate") }}:
            <span style="font-weight: normal">{{
              specialNodesMap["GradientAggregation"]
                ? specialNodesMap["GradientAggregation"]
                : 0
            }}</span>
          </div>
        </div>
      </LeeCollapseItem>
      <LeeCollapseItem title="Node attributes" name="2">
        <div class="attribute-tooltip" v-if="selectedNode !== null">
          <div
            class="second-title"
            v-html="`Node ID: ${selectedNode.id}`"
          ></div>
          <div class="attribute-tooltip-content">
            <div class="col">
              <div class="left second-title">type:</div>
              <div class="right" v-html="selectedNode.type"></div>
            </div>
            <div class="col">
              <div class="left second-title">name:</div>
              <div
                class="right"
                v-html="selectedNode.name.split('/').slice(-1)[0]"
              ></div>
            </div>
            <div class="col">
              <div class="left second-title">scope:</div>
              <div class="right">
                <div
                  v-for="(scope, index) in selectedNode.scope.split('/')"
                  :key="scope + index"
                  v-html="`${scope}/`"
                  style="word-break: break-all"
                ></div>
              </div>
            </div>
            <div class="col">
              <div class="left second-title">inputs:</div>
              <div class="right">
                <div
                  id="write"
                  v-for="(input, index) in selectedNode.input"
                  :key="'attr_' + input"
                >
                  <blockquote>
                    <div class="third-title">
                      name:<span
                        style="font-weight: normal"
                        v-html="`${selectedNode.input_name[index]}`"
                      ></span>
                    </div>
                    <div class="third-title">
                      shape:<span
                        style="font-weight: normal"
                        v-html="`${selectedNode.input_shape[index]}`"
                      ></span>
                    </div>
                    <div class="third-title">
                      strategy:<span
                        style="font-weight: normal"
                        v-html="`${selectedNode.input_strategy[index]}`"
                      ></span>
                    </div>
                  </blockquote>
                </div>
              </div>
            </div>
            <div class="col">
              <div class="left second-title">output:</div>
              <div class="right">
                <div
                  v-for="output in selectedNode.output"
                  :key="output"
                  v-html="
                    `${output} - ${
                      !isNaN(output)
                        ? nodeMaps[nodeGroupIndex][output].type
                        : ''
                    }`
                  "
                ></div>
              </div>
            </div>
          </div>
        </div>
      </LeeCollapseItem>
    </LeeCollapse>
  </div>
</template>

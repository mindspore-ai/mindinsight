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
import Vue from "vue";
import Vuex from "vuex";

Vue.use(Vuex);

export default new Vuex.Store({
  state: {
    graphData: {},
    nodeMaps: [],
    profileSpecialEdgeTypes: [],
    selectedGraphNode: null,
    profileTreeData: [],
    profileShowSpecialEdgeTypes: [],
    stepNum: 1,
    opNameMap: null,
    profileNamespaces: [],
    overviewData: {},
    communicateNodes: {},
  },
  mutations: {
    setGraphData: (state, data) => {
      state.graphData = data;
    },
    setNodeMaps(state, val) {
      state.nodeMaps = val;
    },
    setProfileSpecialEdgeTypes(state, val) {
      state.profileSpecialEdgeTypes = val;
    },
    // profile->attribute
    setSelectedGraphNode(state, val) {
      state.selectedGraphNode = val;
    },
    //configure
    setProfileTreeData(state, val) {
      state.profileTreeData = val;
    },
    //configure->profile hidden edge
    setProfileShowSpecialEdgeTypes(state, val) {
      state.profileShowSpecialEdgeTypes = val;
    },
    // configure->profile select nameScope
    setProfileNamespaces(state, val) {
      state.profileNamespaces = val;
    },
    // marey
    setStepNum(state, val) {
      state.stepNum = val;
    },
    setOpNameMap(state, val) {
      state.opNameMap = val;
    },
    setOverviewData(state, val) {
      state.overviewData = val;
    },
    setCommunicateNodes(state, val) {
      state.communicateNodes = val;
    },
  },
});

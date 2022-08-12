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
export const specialEdgesDef = [
  {
    class: 'update-state-edge',
    condition: isUpdateStateBigEdge,
    path: (sNode, tNode) => `M${sNode.x} ${sNode.y} Q${(sNode.x + tNode.x) / 2} 1000 ${tNode.x} ${tNode.y}`,
    defaultDisplay: false,
  }, {
    class: 'activation-gradient-edges',
    condition: isActivationBigEdge,
    path: (sNode, tNode) => `M${sNode.x} ${sNode.y} Q${(sNode.x + tNode.x) / 2} 1000 ${tNode.x} ${tNode.y}`,
    defaultDisplay: false,
  }, {
    class: 'load-edge',
    condition: isLoadEdge,
    path: (sNode, tNode) => {
      if (sNode.type === 'Load') {
        return `M${sNode.x} ${sNode.y} Q${tNode.x} ${sNode.y} ${tNode.x} ${tNode.y}`;
      }
      return `M${sNode.x} ${sNode.y} Q${sNode.x} ${tNode.y} ${tNode.x} ${tNode.y}`;
    },
    defaultDisplay: false,
  }, {
    class: 'big-depend-edge',
    condition: isBigDependEdge,
    path: (sNode, tNode) => `M${sNode.x} ${sNode.y} Q${(sNode.x + tNode.x) / 2} ${tNode.y + 100} ${tNode.x} ${tNode.y}`,
    defaultDisplay: false,
  }, {
    class: 'get-next-edge',
    condition: isGetNextEdge,
    path: (sNode, tNode) => `M${sNode.x} ${sNode.y} Q${tNode.x} ${sNode.y} ${tNode.x} ${tNode.y}`,
    defaultDisplay: false,
  }, {
    class: 'big-from-syncbatchnorm-edge',
    condition: isBigFromSyncBatchNormGradEdge,
    path: (sNode, tNode) => null,
    defaultDisplay: false,
  }, {
    class: 'big-hub-node-edge',
    condition: isBigHubNodeEdge,
    path: (sNode, tNode) => null,
    defaultDisplay: false,
  }, {
    class: 'other-big-edge',
    condition: isBigEdge,
    path: (sNode, tNode) => null,
    defaultDisplay: false,
  },

];

function isBigEdge(source, target) {
  return _isBigEdge(source, target);
}

export function isUpdateStateBigEdge(source, target) {
  if (source.type === 'UpdateState' && target.type === 'UpdateState') {
    return true;
  }
  if (source.type !== 'UpdateState' && target.type !== 'UpdateState') {
    return false;
  }
  if (Math.abs(Number(source.id) - Number(target.id)) > 20) {
    return true;
  }
  return false;
}

export function isLoadEdge(source, target) {
  if (source.type === 'Load' || target.type === 'Load') {
    return true;
  }
  return false;
}

export function isGetNextEdge(source, target) {
  if (source.type === 'GetNext') {
    return true;
  }
  return false;
}

const gradientPairs = {
  Conv2DBackpropFilter: 'Conv2D',
  Conv2DBackpropInput: 'Conv2D',
  SyncBatchNormGrad: 'SyncBatchNorm',
  MaxPoolGrad: 'MaxPool',
  ReluGrad: 'ReLU',
  gradGather: 'Gather',
  LayerNormGrad: 'LayerNorm',
  DropoutGrad: 'Dropout',
  gradMatMul: 'MatMul',
  gradBatchMatMul: 'BatchMatMul',
  gradSoftmax: 'Softmax',
  GeLUGrad: 'GeLU',
  TanhGrad: 'Tanh',
};

const gradOps = new Set(Object.keys(gradientPairs));
export function isActivationBigEdge(source, target, nodeMap) {
  if (!_isBigEdge(source, target)) return false;
  if (gradientPairs[target.type] === source.type) {
    return true;
  }
  if (gradientPairs[target.scope.split('/').pop()] === source.type) {
    return true;
  }
  if (gradOps.has(target.type)) {
    for (const outputId of source.output) {
      if (nodeMap[outputId]?.type === gradientPairs[target.type]) {
        return true;
      }
    }
  }
  if (gradOps.has(target.scope.split('/').pop())) {
    for (const outputId of source.output) {
      if (
        nodeMap[outputId]?.type === gradientPairs[target.scope.split('/').pop()]
      ) {
        return true;
      }
    }
  }

  return false;
}

export function isBigDependEdge(source, target) {
  return _isBigEdge(source, target);
}

function _isBigEdge(source, target) {
  if (Math.abs(Number(source.id) - Number(target.id)) > 7) {
    return true;
  }
}

export function isBigFromSyncBatchNormGradEdge(source, target) {
  if (source.type === 'SyncBatchNormGrad' && target.type === 'AssignAdd') {
    return true;
  } else if (
    source.type === 'SyncBatchNormGrad' &&
    target.type === 'Conv2DBackpropFilter'
  ) {
    return true;
  }
  return false;
}

export function isBigHubNodeEdge(source, target) {
  if (!_isBigEdge(source, target)) {
    return false;
  }
  if (source.output.length > 10 || target.input.length > 10) {
    return true;
  }
  return false;
}

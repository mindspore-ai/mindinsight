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
export const childrenOptions = {
  'algorithm': 'layered',
  'portConstraints': 'FIXED_SIDE',
  'contentAlignment': '[H_CENTER, V_CENTER]',
};

export const labelOptions = {
  'nodeLabels.placement': '[H_CENTER, V_TOP, INSIDE]',
};

export const layoutOptions = {
  'algorithm': 'layered',
  // Node placement strategy
  // NETWORK_SIMPLEX like floating down
  'org.eclipse.elk.layered.nodePlacement.strategy': 'NETWORK_SIMPLEX',
  // Orthogonal style
  'org.eclipse.elk.layered.nodePlacement.favorStraightEdges': 'true',
  'org.eclipse.elk.layered.crossingMinimization.strategy': 'LAYER_SWEEP',
  // Port relative position
  'org.eclipse.elk.portAlignment.east': 'CENTER',
  'org.eclipse.elk.portAlignment.west': 'CENTER',
  // interactive mode
  'org.eclipse.elk.interactive': 'true',
  // Horizontal space of nodes in same layer
  'spacing.nodeNodeBetweenLayers': '50.0',
  // Vertical space of nodes in same layer
  // 'spacing.nodeNode': '20.0',
  // Horizontal space of node and edge in same layer
  'spacing.edgeNodeBetweenLayers': '20.0',
  // Vertical space of node and edge in same layer
  // 'spacing.edgeNode': '20.0',
  'nodeSize.constraints': 'MINIMUM_SIZE',
};

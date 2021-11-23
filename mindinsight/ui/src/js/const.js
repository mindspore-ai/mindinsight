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
export const IN_PORT_SUFFIX = '-in-port';

export const OUT_PORT_SUFFIX = '-out-port';

export const SCOPE_SEPARATOR = '/';

export const SCOPE_AGGREGATOR = '+';

export const EDGE_SEPARATOR = '->';

export const EXAMPLE_SEPERATOR = ':';

export const NODE_TYPE = {
  basic_scope: 'basic_scope',
  name_scope: 'name_scope',
  aggregate_scope: 'aggregate_scope',
  parameter: 'parameter',
  const: 'const',
  comm: 'communication',
};

// attributes to insert
export const INSERTED_ATTR = {
  'parallel_shard': 'parallel_shard',
  'parallel_group': 'parallel_group',
  'parallel_group_rank': 'parallel_group_rank',
  'instance_type': 'instance_type',
};

export const INPUT = 'input';

export const OUTPUT = 'output';

export const MIN_COUNT_OF_NODE_STACK = 10;

export const COLOR = {
  expanded: '#fff5e6',
  unexpanded: '#ffffff',
};

export const GRAPH_STYLE = `.no-fill {fill: none;}
.graph-action {height: 40px;width: 100%;display: flex;align-items: center;}
.graph-container {height: calc(100% - 40px);width: 100%;position: relative;}
.graph-common {stroke: #000000;stroke-width: 1;}
.graph-scope-label {font-size: 14px;text-align: center;overflow: hidden;text-overflow: ellipsis;user-select: none;}
.graph-operator-label {transform: scale(0.7);}
.graph-port-inside {fill: #000000;}
.graph-port-outside {fill: #ffffff;stroke: #000000;stroke-miterlimit: 10;}`;

export const MARKER = `<marker slot="marker" id="arrowhead" viewBox="0 0 10 10" 
refX="5" refY="5" markerUnits="userSpaceOnUse" markerWidth="8" markerHeight="6" orient="auto">
<path d="M -4 0 L 6.5 5 L -4 10 z"></path></marker>`;

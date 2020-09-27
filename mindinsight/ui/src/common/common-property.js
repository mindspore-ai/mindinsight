/**
 * Copyright 2019 Huawei Technologies Co., Ltd.All Rights Reserved.
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
export default {
  pieColorArr: [
    '#6C92FA',
    '#6CBFFF',
    '#4EDED2',
    '#7ADFA0',
    '#A6DD82',
    '#F6DF66',
    '#FDCA5A',
    '#FA8E5A',
    '#F45C5E',
    '#F3689A',
    '#A97AF8',
    '#3D58A6',
    '#3673A3',
    '#2C9990',
    '#469965',
    '#68994D',
    '#A89636',
    '#A8812C',
    '#A6542D',
    '#A34142',
    '#664EA3',
  ],
  commonColorArr: [
    '#00A5A7',
    '#6C92FA',
    '#FA8E5A',
    '#A6DD82',
    '#6CBFFF',
    '#F45C5E',
    '#F6DF66',
    '#4EDED2',
    '#F3689A',
    '#FDCA5A',
    '#7ADFA0',
    '#4C6BC2',
    '#C2663A',
    '#7EB05D',
    '#468BC2',
    '#BF5254',
    '#C2AE44',
    '#33B0A6',
    '#BA456F',
    '#C49939',
    '#56B077',
    '#A1BAFF',
    '#FFBA99',
    '#C7EDAD',
    '#9ED5FF',
    '#FA9698',
    '#FAEB9D',
    '#8CEDE5',
    '#F79CBC',
    '#FFDE96',
    '#A8EDC2',
    '#25386E',
    '#8A4321',
    '#59823D',
    '#285C85',
    '#873233',
    '#8F7E29',
    '#1E827A',
    '#822849',
    '#8C6A20',
    '#388252',
    '#DCFCE8',
    '#FFE4D6',
    '#D2FCF9',
    '#FFF2D4',
    '#D1EBFF',
    '#FFF9D9',
    '#D4DFFF',
    '#FCD2E1',
    '#E9FCDC',
    '#FFD1D2',
  ],
  // define graph color array
  graphColorArrPhg: ['#F5FBFB', '#EDF9F9', '#DEF5F5', '#C9F5F5'],
  // define fullscreen icon
  fullScreenIcon:
    'path://M432.45,595.444c0,2.177-4.661,6.82-11.305,6.82c-6.475,' +
    '0-11.306-4.567-11.306-6.82s4.852-6.812,11.306-6.812C427.841,' +
    '588.632,432.452,593.191,432.45,595.444L432.45,595.444z M421.155,' +
    '589.876c-3.009,0-5.448,2.495-5.448,5.572s2.439,5.572,5.448,' +
    '5.572c3.01,0,5.449-2.495,5.449-5.572C426.604,592.371,424.165,' +
    '589.876,421.155,589.876L421.155,589.876z M421.146,591.891c-1.916,' +
    '0-3.47,1.589-3.47,3.549c0,1.959,1.554,3.548,3.47,3.548s3.469-1.589,' +
    '3.469-3.548C424.614,593.479,423.062,591.891,421.146,591.891L421.146,591.891zM421.146,591.891',
  // define svg style for graph download
  graphDownloadStyle:
    '<style>.graph {margin: 20px;width: calc(100% - 40px);height: calc(100% - 40px);' +
    'border: 1px solid #e6ebf5;}.selected {stroke: red !important;stroke-width: 2px;}' +
    '.node {cursor: pointer;}.node:hover > path,.node:hover > ellipse,' +
    '.node:hover > polygon,.node:hover > rect {stroke-width: 2px;}' +
    '.edge path {stroke: rgb(120, 120, 120);}.edge polygon {fill: rgb(120, 120, 120);}' +
    '.node.aggregation > polygon {stroke: #e3aa00;fill: #ffe794;}.node.cluster.aggregation > ' +
    'rect {stroke: #e3aa00;fill: #ffe794;stroke-dasharray: 3, 3;}' +
    '.node.cluster > rect:hover {stroke: #8df1f2;}.node > polygon {stroke: #00a5a7;fill: rgb(141,241,242);}' +
    '.node > ellipse {stroke: #4ea6e6;fill: #b8e0ff;}.node > path {stroke: #e37d29;fill: #ffd0a6;' +
    'stroke-dasharray: 3, 3;}' +
    '.hide {visibility: hidden;}.show {visibility: visible;}' +
    '.edgePoint ellipse{stroke:#a7a7a7;' +
    'fill:#a7a7a7;}text {fill: black;}' +
    '.edge.highlighted path {stroke: red;}.edge.highlighted polygon {' +
    'stroke: red;fill: red;}' +
    '.edge.highlighted marker path {fill: red;}</style>',
  dataMapDownloadStyle: '<style> #graph0 > polygon { fill: transparent; }' +
    '.node, .cluster { cursor: pointer; }' +
    '.selected { polygon, ellipse { stroke: red !important; stroke-width: 2px; } }' +
    '.CreatDataset > polygon, .Operator > ellipse { stroke: #4ea6e6; fill: #b8e0ff; }' +
    '.cluster > polygon { fill: #8df1f2; stroke: #00a5a7; }' +
    '.RepeatDataset > polygon { stroke: #fdca5a; fill: #fff2d4; }' +
    '.ShuffleDataset > polygon { stroke: #e37d29; fill: #ffd0a6; }' +
    '.BatchDataset > polygon { stroke: #de504e; fill: #ffbcba; }' +
    '.edge { path { stroke: rgb(167, 167, 167); }' +
    'polygon { fill: rgb(167, 167, 167); stroke: rgb(167, 167, 167); } }</style>',
};

<!--
Copyright 2020-2021 Huawei Technologies Co., Ltd.All Rights Reserved.

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
<script>
import CommonProperty from '@/common/common-property.js';
import {select, selectAll, zoom} from 'd3';
import {event as currentEvent} from 'd3-selection';
import 'd3-graphviz';
const d3 = {select, selectAll, zoom};
export default {
  data() {
    return {
      clickScope: {}, // Information about the node that is clicked for the first time.
      frameSpace: 25, // Distance between the namespace border and the internal node
      curColorIndex: 0,
      totalMemory: 16777216 * 2, // Memory size of the graph plug-in
      viewBox: {
        max: 10000,
        scale: {x: 1, y: 1},
      },
    };
  },
  methods: {
    /**
     * Initializing the click event
     * @param {Object} target The target of the click event
     * @param {Number} index Index of the target
     * @param {Array} nodesList List of nodes on the page
     * @param {String} pageKey Page identification mark
     */
    clickEvent(target, index, nodesList, pageKey) {
      // The target value of the element converted from the HTML attribute of the variable is null.
      const event = currentEvent;
      event.stopPropagation();
      event.preventDefault();

      const clickNode = nodesList[index];
      const nodeId = clickNode.id;
      const nodeClass = clickNode.classList.value;
      setTimeout(() => {
        this.clickScope = {
          id: nodeId,
          class: nodeClass,
        };
      }, 10);
      setTimeout(() => {
        this.clickScope = {};
      }, 1000);
      this.selectedNode.name = nodeId;
      if (pageKey === 'graph') {
        this.selectNode(false);
      } else if (pageKey === 'debugger') {
        this.selectNode(false, true);
        this.contextmenu.dom.style.display = 'none';
      }
    },
    /**
     * Initializing the click event
     * @param {Object} target The target of the click event
     * @param {Number} index Index of the target
     * @param {Array} nodesList List of nodes on the page
     * @param {String} pageKey Page identification mark
     */
    dblclickEvent(target, index, nodesList, pageKey) {
      // The target of the element converted from the HTML attribute of the variable is empty and
      // needs to be manually encapsulated.
      const event = currentEvent;
      event.stopPropagation();
      event.preventDefault();

      const clickNode = nodesList[index];
      const nodeId = clickNode.id;
      const nodeClass = clickNode.classList.value;
      let name = nodeId;
      this.selectedNode.more =
        name.indexOf('more...') !== -1 &&
        document
            .querySelector(`#graph g[id="${name}"]`)
            .attributes.class.value.indexOf('plain') === -1;

      const unfoldFlag =
        (nodeClass.includes('aggregation') ||
          nodeClass.includes('cluster') ||
          this.selectedNode.more) &&
        (!this.clickScope.id ||
          (this.clickScope.id && nodeId === this.clickScope.id));

      if (this.selectedNode.more) {
        const changePage = name.includes('right') ? 1 : -1;
        const parentId = document.querySelector(`#graph g[id="${name}"]`)
            .parentNode.id;
        name = parentId.replace('_unfold', '');
        this.allGraphData[name].index += changePage;
        this.allGraphData[name].index = Math.max(
            0,
            Math.min(
                this.allGraphData[name].index,
                this.allGraphData[name].childIdsList.length - 1,
            ),
        );
        this.selectedNode.name = name;
      }
      if (unfoldFlag) {
        this.dealDoubleClick(name);
      } else if (this.clickScope.id) {
        this.selectedNode.name = this.clickScope.id;
        if (pageKey === 'graph') {
          this.selectNode(false);
        }
      }
      this.nodeCollapseLinkage(this.selectedNode.name);
    },
    /**
     * Tree linkage with graph
     * Collapse of current node
     * @param {Object} name  The name of the current node
     */
    nodeCollapseLinkage(name) {
      const node = this.$refs.tree.getNode(name.replace('_unfold', ''));
      if (node) {
        node.expanded = false;
        node.loaded = false;
        node.childNodes = [];
      }
    },
    /**
     * Initializing the graph
     * @param {String} dot Dot statement encapsulated in graph data
     */
    initGraph(dot) {
      try {
        this.graphviz = d3
            .select('#graph')
            .graphviz({useWorker: false, totalMemory: this.totalMemory})
            .zoomScaleExtent(this.scaleRange)
            .dot(dot)
            .attributer(this.attributer)
            .render(() => {
              this.initSvg(true);
              this.afterInitGraph();
            });
      } catch (error) {
        const svg = document.querySelector('#graph svg');
        if (svg) {
          svg.remove();
        }
        this.initGraph(dot);
      }

      // Generate the dom of the submap.
      if (!d3.select('#graphTemp').size()) {
        d3.select('body').append('div').attr('id', 'graphTemp');
      }
      // Stores the dom of all the sorted subgraphs.
      if (!d3.select('#subgraphTemp').size()) {
        d3.select('body').append('div').attr('id', 'subgraphTemp');
      }
    },
    /**
     * Initialize svg
     * @param {Bealoon} setSize Weather to set svg origin width and height
     */
    initSvg(setSize) {
      this.svg.dom = document.querySelector('#graph svg');
      this.svg.rect = this.svg.dom.getBoundingClientRect();
      const viewBoxData = this.svg.dom.getAttribute('viewBox').split(' ');
      this.viewBox.scale.x = 1;
      if (setSize) {
        this.svg.originSize = {width: viewBoxData[2], height: viewBoxData[3]};
      }
      if (viewBoxData[2] > this.viewBox.max) {
        this.viewBox.scale.x = viewBoxData[2] / this.viewBox.max;
        viewBoxData[2] = this.viewBox.max;
      }

      this.viewBox.scale.y = 1;
      if (viewBoxData[3] > this.viewBox.max) {
        this.viewBox.scale.y = viewBoxData[3] / this.viewBox.max;
        viewBoxData[3] = this.viewBox.max;
      }
      this.svg.dom.setAttribute('viewBox', viewBoxData.join(' '));
      this.svg.viewWidth = viewBoxData[2];
      this.svg.viewHeight = viewBoxData[3];
    },
    /**
     * Initializing the graph zoom
     * @param {String} pageKey
     */
    initZooming(pageKey) {
      const graphBox = this.graph.dom.getBBox();
      const padding = 4;
      const minDistance = 20;
      const pointer = {start: {x: 0, y: 0}, end: {x: 0, y: 0}};
      const zoom = d3
          .zoom()
          .on('start', () => {
            const event = currentEvent.sourceEvent;
            pointer.start.x = event.x;
            pointer.start.y = event.y;
            if (pageKey === 'debugger') {
              this.contextmenu.dom.style.display = 'none';
            }
          })
          .on('zoom', () => {
            const event = currentEvent.sourceEvent;
            event.stopPropagation();
            event.preventDefault();

            const transformData = this.getTransformData(this.graph.dom);
            let tempStr = '';
            let change = {};
            let scale = transformData.scale[0];
            const graphRect = this.graph.dom.getBoundingClientRect();
            const transRate = graphBox.width / graphRect.width;
            if (event.type === 'mousemove') {
              pointer.end.x = event.x;
              pointer.end.y = event.y;
              let tempX = pointer.end.x - pointer.start.x;
              let tempY = pointer.end.y - pointer.start.y;
              const paddingTrans = Math.max(
                  (padding / transRate) / scale,
                  minDistance,
              );
              if (
                graphRect.left + paddingTrans + tempX >=
              this.svg.rect.left + this.svg.rect.width
              ) {
                tempX = Math.min(tempX, 0);
              }
              if (
                graphRect.left + graphRect.width - paddingTrans + tempX <=
              this.svg.rect.left
              ) {
                tempX = Math.max(tempX, 0);
              }
              if (
                graphRect.top + paddingTrans + tempY >=
              this.svg.rect.top + this.svg.rect.height
              ) {
                tempY = Math.min(tempY, 0);
              }
              if (
                graphRect.top + graphRect.height - paddingTrans + tempY <=
              this.svg.rect.top
              ) {
                tempY = Math.max(tempY, 0);
              }

              change = {
                x: tempX * transRate * scale,
                y: tempY * transRate * scale,
              };
              pointer.start.x = pointer.end.x;
              pointer.start.y = pointer.end.y;
            } else if (event.type === 'wheel') {
              const wheelDelta = -event.deltaY;
              const rate = 1.2;
              scale =
              wheelDelta > 0
                ? transformData.scale[0] * rate
                : transformData.scale[0] / rate;

              scale = Math.max(this.scaleRange[0], scale, this.graph.minScale);
              scale = Math.min(this.scaleRange[1], scale);
              change = {
                x:
                (graphRect.x + padding / transRate - event.x) *
                transRate *
                (scale - transformData.scale[0]),
                y:
                (graphRect.bottom - padding / transRate - event.y) *
                transRate *
                (scale - transformData.scale[0]),
              };
            }

            this.graph.transform = {
              x: transformData.translate[0] + change.x,
              y: transformData.translate[1] + change.y,
              k: scale,
            };
            this.graph.transRate =
            graphRect.width / graphBox.width / this.graph.transform.k;

            tempStr =
            `translate(${this.graph.transform.x},${this.graph.transform.y}) ` +
            `scale(${this.graph.transform.k})`;
            this.graph.dom.setAttribute('transform', tempStr);
            if (pageKey === 'graph') {
              this.setInsideBoxData();
            }
          });

      const svg = d3.select('#graph svg');
      svg.on('.zoom', null);
      svg.call(zoom);
      svg.on('dblclick.zoom', null);
      svg.on('wheel.zoom', null);

      const graph0 = d3.select('#graph #graph0');
      graph0.on('.zoom', null);
      graph0.call(zoom);
    },
    /**
     * Default method of the graph rendering adjustment. Set the node format.
     * @param {Object} datum Object of the current rendering element.
     * @param {Number} index Indicates the subscript of the current rendering element.
     * @param {Array} nodes An array encapsulated with the current rendering element.
     */
    attributer(datum, index, nodes) {
      const isChild =
        datum.tag === 'ellipse' ||
        datum.tag === 'circle' ||
        (datum.tag === 'polygon' && datum.attributes.stroke !== 'transparent');
      if (datum.tag === 'svg') {
        const width = '100%';
        const height = '100%';
        datum.attributes.width = width;
        datum.attributes.height = height;
      } else if (isChild) {
        datum.attributes.stroke = 'rgb(120, 120, 120)';
      }
    },
    /**
     * When the value of graph is too large, enlarge the value of graph.
     * Otherwise, the node cannot be clearly displayed.
     * @param {String} id Indicates the ID of the graph diagram.
     */
    fitGraph(id) {
      const graph = document.getElementById(id);
      const maxShowWidth = graph.offsetWidth * 1.5;
      const maxShowHeight = graph.offsetHeight * 1.5;
      const graphDom = document.querySelector(`#${id} #graph0`);
      const box = graphDom.getBBox();
      let transformStr = '';
      const graphTransformData = this.getTransformData(graphDom);
      if (box.width > maxShowWidth || box.height > maxShowHeight) {
        const scale = Math.max(
            box.width / maxShowWidth / this.viewBox.scale.x,
            box.height / maxShowHeight / this.viewBox.scale.y,
        );
        const translate = {x: (box.width - maxShowWidth) / 2};

        if (!this.selectedNode.name) {
          graphTransformData.translate[0] = translate.x;
        }
        graphTransformData.scale[0] = scale;
      } else {
        graphTransformData.translate = [-box.x, -box.y];
      }
      if (id === 'graph' && this.selectedNode.more) {
        graphTransformData.scale[0] = this.graph.transform.k;
      }
      Object.keys(graphTransformData).forEach((key) => {
        transformStr += `${key}(${graphTransformData[key].join(',')}) `;
      });
      graphDom.setAttribute('transform', transformStr.trim());
    },
    /**
     * Expand a namespace.
     * @param {String} name Nodes to be expanded or zoomed out
     * @param {Boolean} toUnfold Expand the namespace.
     */
    layoutNamescope(name, toUnfold) {
      this.$nextTick(() => {
        try {
          const dotStr = this.packageNamescope(name);
          this.graphvizTemp = d3
              .select('#graphTemp')
              .graphviz({useWorker: false, totalMemory: this.totalMemory})
              .dot(dotStr)
              .zoomScaleExtent(this.scaleRange)
              .attributer((datum, index, nodes) => {
                if (
                  datum.tag === 'polygon' &&
                datum.attributes.stroke !== 'transparent'
                ) {
                  datum.attributes.stroke = 'rgb(120, 120, 120)';
                }
              })
              .render(() => {
                this.fitGraph('graphTemp');
                this.dealNamescopeTempGraph(name);
              });
        } catch (error) {
          const graphTempSvg = document.querySelector('#graphTemp svg');
          if (graphTempSvg) {
            graphTempSvg.remove();
          }
          const subGraphTempSvg = document.querySelector('#subgraphTemp svg');
          if (subGraphTempSvg) {
            subGraphTempSvg.remove();
          }

          this.dealDoubleClick(this.selectedNode.name);
        }
      });
    },
    /**
     * Process the data returned by the background interface.
     * @param {String} name Node name
     */
    dealAggregationNodes(name) {
      // A maximum of 10 subnodes can be displayed on an aggregation node.
      const aggregationNodeLimit = 10;
      const idsGroup = [];
      let maxChainNum = 1;

      this.allGraphData[name].children.forEach((key) => {
        const ids = this.getAssociatedNode(key, `${name}/`);
        if (ids.length) {
          idsGroup.push(ids);
        }
        const chainNum = this.dealChainingData(key, `${name}/`);
        maxChainNum = Math.max(...chainNum, maxChainNum);
      });

      const idsList = [];
      let temp = [];
      for (let i = 0; i < idsGroup.length; i++) {
        if (idsGroup[i].length > aggregationNodeLimit) {
          idsList.push(idsGroup[i]);
        } else {
          if (temp.length + idsGroup[i].length <= aggregationNodeLimit) {
            temp = temp.concat(idsGroup[i]);
          } else {
            if (temp.length) {
              idsList.push(temp);
              temp = [].concat(idsGroup[i]);
            }
          }
        }
        if (i === idsGroup.length - 1 && temp.length) {
          idsList.push(temp);
        }
      }

      this.allGraphData[name].childIdsList = idsList;
      this.allGraphData[name].index = 0;
      this.allGraphData[name].maxChainNum = maxChainNum;
    },
    /**
     * Process chaining data
     * @param {String} name Nodes name
     * @param {String} prefix Node prefix
     * @return {Number}
     */
    dealChainingData(name, prefix) {
      const node = this.allGraphData[name];
      if (!node.chained) {
        node.chained = true;
        let temp = [];
        Object.keys(node.input).forEach((key) => {
          if (key.includes(prefix)) {
            temp = temp.concat(this.dealChainingData(key, prefix));
          }
        });

        if (temp.length) {
          node.chainNum = [...new Set(temp.map((i) => i + 1))];
        }
      }
      return node.chainNum;
    },
    /**
     * Get associated node
     * @param {String} name Nodes name
     * @param {String} prefix Node prefix
     * @return {Number}
     */
    getAssociatedNode(name, prefix) {
      const node = this.allGraphData[name];
      let ids = [];

      if (!node.grouped) {
        node.grouped = true;
        ids.push(node.name);
        Object.keys(node.input).forEach((i) => {
          if (i.startsWith(prefix)) {
            if (!this.allGraphData[i].grouped) {
              const idsTemp = this.getAssociatedNode(i, prefix);
              ids = ids.concat(idsTemp);
            }
          }
        });
        Object.keys(node.output).forEach((i) => {
          if (i.startsWith(prefix)) {
            if (!this.allGraphData[i].grouped) {
              const idsTemp = this.getAssociatedNode(i, prefix);
              ids = ids.concat(idsTemp);
            }
          }
        });
      }

      return ids;
    },
    /**
     * Encapsulates graph data into dot data.
     * @return {String} Dot String for packing graph data
     */
    packageGraphData() {
      const nodes = this.getChildNodesByName();
      const initSetting =
        'node[style="filled";fontsize="10px"];edge[fontsize="5px";];';
      return `digraph {${initSetting}${this.packageNodes(
          nodes,
      )}${this.packageEdges(nodes)}}`;
    },
    /**
     * Encapsulates node data into dot data.
     * @param {Array} nodes Nodes of the node to be expanded.
     * @param {String} name Name of the node to be expanded.
     * @return {String} Dot String that are packed into all nodes
     */
    packageNodes(nodes, name) {
      let tempStr = '';
      nodes.forEach((node) => {
        const name = node.name.split('/').pop();
        // Different types of nodes are generated for different data types.
        if (node.type === 'aggregation_scope') {
          tempStr +=
            `<${node.name}>[id="${node.name}";` +
            `label="${name}";class="aggregation";` +
            `${
              node.isUnfold
                ? `shape="polygon";width=${node.size[0]};` +
                  `height=${node.size[1]};fixedsize=true;`
                : 'shape="octagon";'
            }];`;
        } else if (node.type === 'name_scope') {
          const fillColor = CommonProperty.graphColorArrPhg[this.curColorIndex];
          this.curColorIndex = this.curColorIndex % 4;
          this.curColorIndex++;
          tempStr +=
            `<${node.name}>[id="${node.name}";fillcolor="${fillColor}";` +
            `shape="polygon";label="${name}";class="cluster";` +
            `${
              node.isUnfold
                ? `width=${node.size[0]};height=${node.size[1]};fixedsize=true;`
                : ''
            }];`;
        } else if (node.type === 'Const') {
          tempStr +=
            `<${node.name}>[id="${node.name}";label="${name}\n\n\n";` +
            `shape="circle";width="0.14";height="0.14";fixedsize=true;];`;
        } else {
          tempStr +=
            `<${node.name}>[id="${node.name}";shape="ellipse";` +
            `label="${name}"];`;
        }
        // A maximum of five virtual nodes can be displayed. Other virtual nodes are displayed in XXXmore.
        // The ID of the omitted aggregation node is analogNodesInput||analogNodeOutput^nodeId.
        // After the namespace or aggregation node is expanded, the virtual node does not need to be displayed.
        if (!this.allGraphData[node.name].isUnfold) {
          let keys = Object.keys(node.proxy_input || {});
          let target = node.name;
          let source = '';
          let isConst = false;
          for (let i = 0; i < Math.min(5, keys.length); i++) {
            source = keys[i];
            isConst = !!(
              this.allGraphData[keys[i]] &&
              this.allGraphData[keys[i]].type === 'Const'
            );
            const nodeStr = isConst
              ? `shape="circle";width="0.14";height="0.14";fixedsize=true;` +
                `label="${source.split('/').pop()}\n\n\n";`
              : `shape="Mrecord";label="${source.split('/').pop()}";`;

            tempStr +=
              `<${source}^${target}>[id="${source}^${target}";` +
              `${nodeStr}class="plain"];`;
          }
          if (keys.length > 5) {
            tempStr +=
              `<analogNodesInput^${target}>[id="analogNodesInput^` +
              `${target}";label="${keys.length - 5} more...";shape="Mrecord";` +
              `class="plain";];`;
          }

          keys = Object.keys(node.proxy_output || {});
          source = node.name;
          for (let i = 0; i < Math.min(5, keys.length); i++) {
            target = keys[i];
            isConst = !!(
              this.allGraphData[keys[i]] &&
              this.allGraphData[keys[i]].type === 'Const'
            );
            const nodeStr = isConst
              ? `shape="circle";width="0.14";height="0.14";fixedsize=true;` +
                `label="${target.split('/').pop()}\n\n\n";`
              : `shape="Mrecord";label="${target.split('/').pop()}";`;

            tempStr +=
              `<${target}^${source}>[id="${target}^${source}";` +
              `${nodeStr}class="plain";];`;
          }
          if (keys.length > 5) {
            tempStr +=
              `<analogNodesOutput^${source}>[id="analogNodesOutput^` +
              `${source}";shape="Mrecord";label="${keys.length - 5} more...";` +
              `class="plain";];`;
          }
        }
      });
      return tempStr;
    },
    /**
     * Encapsulates node data into dot data.
     * @param {Array} nodes Nodes of the node to be expanded.
     * @param {String} name Name of the node to be expanded.
     * @return {String} Dot String packaged by all edges
     */
    packageEdges(nodes, name) {
      let tempStr = '';
      const edges = [];
      // Construct the input and output virtual nodes and optimize the connection.
      const analogNodesInputId = `analogNodesInputOf${name}`;
      const analogNodesOutputId = `analogNodesOutputOf${name}`;
      let needAnalogInput = false;
      let needAnalogOutput = false;
      const unfoldIndependentScope = name
        ? this.allGraphData[name].independent_layout
        : false;
      nodes.forEach((node) => {
        // No input cable is required for the aggregation node and nodes in the aggregation node without namescoope.
        // When only aggregation nodes are encapsulated, input cables do not need to be considered.
        if (!unfoldIndependentScope) {
          const input = node.input || {};
          const keys = Object.keys(input);
          keys.forEach((key) => {
            if (input[key] && !input[key].independent_layout) {
              // Cannot connect to the sub-nodes in the aggregation node and cannot be directly connected to the
              // aggregation node. It can only connect to the outer namespace of the aggregation node.
              // If there is no namespace in the outer layer, you do not need to connect cables.
              // Other connections are normal.
              const source =
                this.findChildNamescope(key, name) ||
                (key ? analogNodesInputId : '');
              let target = node.name;
              if (node.independent_layout) {
                const list = node.name.split('/');
                list.splice(list.length - 2, 2);
                target = `${list.join('/')}_unfold`;
              }
              // The namespace is not nested.
              if (
                source &&
                target &&
                !target.includes(source.replace('_unfold', '') + '/') &&
                !source.includes(target.replace('_unfold', '') + '/')
              ) {
                if (!name || (name && source.startsWith(`${name}/`))) {
                  const obj = {
                    source: source,
                    target: target,
                    shape: input[key].shape,
                    edge_type: input[key].edge_type,
                    data_type: input[key].data_type,
                    count: 1,
                  };
                  edges.push(obj);
                } else {
                  // If it is connected to the outside of the namespace,
                  // it is connected to the virtual input and output node of the namespace.
                  // The connection line of the aggregation node is connected to the namespace of the aggregation node.
                  // If the namespace to be opened is to be opened, you need to delete it.
                  if (target.replace('_unfold', '') !== name) {
                    const obj = {
                      source: analogNodesInputId,
                      target: target,
                      shape: input[key].shape,
                      edge_type: input[key].edge_type,
                      data_type: input[key].data_type,
                      count: 1,
                    };
                    edges.push(obj);
                    needAnalogInput = true;
                  }
                }
              }
            }
          });
          // When the namespace is opened,
          // the line connected to the namespace is connected to the virtual input and output node of the namespace.
          // The aggregation node and its subnodes do not need to consider the situation where the output is connected
          // to the virtual output node.
          if (!node.independent_layout) {
            Object.keys(node.output || {}).forEach((key) => {
              if (!node.output[key].independent_layout) {
                const source = node.name;
                const target =
                  this.findChildNamescope(key, name) || analogNodesOutputId;
                if (source && target) {
                  if (
                    name &&
                    !target.startsWith(`${name}/`) &&
                    source !== name
                  ) {
                    const obj = {
                      source: source,
                      target: analogNodesOutputId,
                      shape: node.output[key].shape,
                      edge_type: node.output[key].edge_type,
                      data_type: node.output[key].data_type,
                      count: 1,
                    };
                    edges.push(obj);
                    needAnalogOutput = true;
                  }
                }
              }
            });
          }
        }
        // Virtual node data
        // The expanded namespace or aggregation node does not need to display virtual nodes.
        if (!this.allGraphData[node.name].isUnfold) {
          let keys = Object.keys(node.proxy_input || {});
          for (let i = 0; i < Math.min(5, keys.length); i++) {
            const target = node.name;
            const source = keys[i];
            const obj = {
              source: `${source}^${target}`,
              target: target,
              shape: node.proxy_input[keys[i]].shape,
              edge_type: node.proxy_input[keys[i]].edge_type,
              data_type: node.proxy_input[keys[i]].data_type,
              count: 1,
            };
            edges.push(obj);
          }
          if (keys.length > 5) {
            const obj = {
              source: `analogNodesInput^${node.name}`,
              target: node.name,
              shape: [],
              edge_type: '',
              data_type: '',
              count: 1,
            };
            edges.push(obj);
          }

          keys = Object.keys(node.proxy_output || {});
          for (let i = 0; i < Math.min(5, keys.length); i++) {
            const source = node.name;
            const target = keys[i];
            const obj = {
              source: source,
              target: `${target}^${source}`,
              shape: node.proxy_output[keys[i]].shape,
              edge_type: node.proxy_output[keys[i]].edge_type,
              data_type: node.proxy_output[keys[i]].data_type,
              count: 1,
            };
            edges.push(obj);
          }
          if (keys.length > 5) {
            const obj = {
              source: node.name,
              target: `analogNodesOutput^${node.name}`,
              shape: [],
              edge_type: '',
              data_type: '',
              count: 1,
            };
            edges.push(obj);
          }
        }
      });

      // Add the virtual input/output node. The aggregation node does not need to be configured.
      if (name && !this.allGraphData[name].independent_layout) {
        if (needAnalogInput) {
          tempStr +=
            `{rank=min;<${analogNodesInputId}>[shape="circle";` +
            `id="${analogNodesInputId}";fixedsize=true;width=0.02;label="";` +
            `class="edge-point"]};`;
        }
        if (needAnalogOutput) {
          tempStr +=
            `{rank=max;<${analogNodesOutputId}>[shape="circle";` +
            `id="${analogNodesOutputId}";width=0.02;fixedsize=true;` +
            `label="";class="edge-point"]};`;
        }
      }

      this.uniqueEdges(edges);
      edges.forEach((edge) => {
        const suffix = edge.edge_type === 'control' ? '_control' : '';
        tempStr +=
          `<${edge.source}>-><${edge.target}>[id="${edge.source}->` +
          `${edge.target}${suffix}";label="${this.getEdgeLabel(edge)}";` +
          `${edge.edge_type === 'control' ? 'style=dashed' : ''}];`;
      });
      return tempStr;
    },
    /**
     * Obtain the label of the edge
     * @param {Object} edge Edge Object
     * @return {String} Edge label
     */
    getEdgeLabel(edge) {
      // The label is not displayed on the control edge
      if (edge.edge_type === 'control') {
        return '';
      }
      let label = '';
      if (!edge.count || edge.count === 1) {
        if (edge.shape && edge.shape.length) {
          if (edge.shape.length > 1) {
            label = `tuple(${edge.shape.length} items)`;
          } else {
            const shape = edge.shape[0];
            if (shape && shape.length) {
              const flag = shape.some((i) => {
                return typeof i !== 'number';
              });
              if (flag) {
                label = `tuple(${shape.length} items)`;
              } else {
                label = `${edge.data_type} ${shape.join('×')}`;
              }
            } else if (edge.data_type) {
              label = `${edge.data_type}`;
            }
          }
        } else if (edge.data_type) {
          label = `${edge.data_type}`;
        }
      } else {
        label = `${edge.count}tensors`;
      }
      return label;
    },
    /**
     * Obtains the subnode data of the namespace through the namespace name.
     * @param {String} name Namespace name.
     * @return {Array} Subnode array of the namespace.
     */
    getChildNodesByName(name) {
      let nodes = [];
      if (name) {
        const node = this.allGraphData[name];
        const nameList =
          node.type === 'aggregation_scope'
            ? node.childIdsList[node.index]
            : node.children;

        nodes = nameList.map((i) => {
          return this.allGraphData[i];
        });

        if (node.type === 'aggregation_scope') {
          const idsList = node.childIdsList;

          if (idsList && idsList.length > 1) {
            if (node.index > 0) {
              let ellipsisNodesNumLeft = 0;
              for (let j = 0; j < node.index; j++) {
                ellipsisNodesNumLeft += idsList[j].length;
              }

              const ellipsisNodeL = {
                name: `${name}/left/${ellipsisNodesNumLeft} more...`,
                attr: {},
                input: {},
                output: {},
                proxy_input: {},
                proxy_output: {},
                type: '',
              };
              this.allGraphData[ellipsisNodeL.name] = ellipsisNodeL;
              nodes.unshift(ellipsisNodeL);
            }

            if (node.index < idsList.length - 1) {
              let ellipsisNodesNumRight = 0;
              for (let j = node.index + 1; j < idsList.length; j++) {
                ellipsisNodesNumRight += idsList[j].length;
              }

              const ellipsisNodeR = {
                name: `${name}/right/${ellipsisNodesNumRight} more...`,
                attr: {},
                input: {},
                output: {},
                proxy_input: {},
                proxy_output: {},
                type: '',
              };
              this.allGraphData[ellipsisNodeR.name] = ellipsisNodeR;
              nodes.push(ellipsisNodeR);
            }
          }
        }
      } else {
        nodes = this.firstFloorNodes.map((i) => {
          return this.allGraphData[i];
        });
      }

      return nodes;
    },
    /**
     * Find the node path that exists in the current namescoope through the node path.
     * @param {String} name Target node name
     * @param {String} namescope Namespace Name
     * @return {String} Namespace node of the namespace.
     */
    findChildNamescope(name, namescope) {
      if (!namescope) {
        return name.split('/')[0];
      } else {
        if (name.startsWith(namescope)) {
          const length = namescope.split('/').length;
          return name
              .split('/')
              .slice(0, length + 1)
              .join('/');
        } else {
          return null;
        }
      }
    },
    /**
     * Multiple edges with the same source and target are combined into one.
     * @param {Array} edges Array of edge data.
     */
    uniqueEdges(edges) {
      for (let i = 0; i < edges.length - 1; i++) {
        for (let j = i + 1; j < edges.length; j++) {
          const isSame =
            edges[i].source === edges[j].source &&
            edges[i].target === edges[j].target &&
            edges[i].edge_type === edges[j].edge_type;
          if (isSame) {
            edges[i].count += edges[j].count;
            edges.splice(j--, 1);
          }
        }
      }
    },
    /**
     * 1. Encapsulating the namespace generated by the graphTemp dom
     * 2. Replace the corresponding node in graphTemp with the existing namespace node in subgraphTemp.
     * 3. Move the namespace dom generated in graphTemp to subgraphTemp for storage.
     * 4. Use graphTemp to generate the dom of the new namespace.
     * @param {String} name Name of the namespace to be expanded.
     */
    dealNamescopeTempGraph(name) {
      const type = this.allGraphData[name].type;
      const classText =
        type === 'aggregation_scope'
          ? 'node cluster aggregation'
          : 'node cluster';
      const idStr = '#graphTemp #graph0 ';
      let fillColor = type === 'aggregation_scope' ? '#fff2d4' : '#ffe4d6';
      const curColorIndex = (name.split('/').length - 1) % 4;
      if (type === 'name_scope') {
        fillColor = CommonProperty.graphColorArrPhg[curColorIndex];
      }

      const graphTemp = d3.select(idStr).node();
      let boxTemp = graphTemp.getBBox();

      // Create a namespace node and add it to graphTemp.
      const g = d3
          .select(idStr)
          .insert('g')
          .attr('id', `${name}_unfold`)
          .attr('class', classText)
          .attr('style', `fill:${fillColor};`);
      g.append('title').text(name);
      g.node().appendChild(
          d3
              .select('#graphTemp #graph0>text')
              .attr('y', boxTemp.y - 10)
              .node(),
      );
      // Move all the subnodes of the namespace to the created namespace node.
      Array.prototype.forEach.call(
          document.querySelector(idStr).querySelectorAll('g'),
          (node) => {
            if (node.id !== g.node().id) {
            // The title of all virtual nodes needs to be reset.
              if (Array.prototype.includes.call(node.classList, 'plain')) {
                const title = node.querySelector('title');
                title.textContent = title.textContent.split('^')[0];
              }
              node.setAttribute('transform', 'translate(0,0)');
              g.node().appendChild(node);
            }
          },
      );
      // Add a rectangle to the created namespace node as the border of the namespace.
      g.insert('rect', 'title')
          .attr('style', `fill:${fillColor};`)
          .attr('stroke', 'rgb(167, 167, 167)')
          .attr('x', g.node().getBBox().x - this.frameSpace)
          .attr('y', g.node().getBBox().y - this.frameSpace)
          .attr('width', g.node().getBBox().width + this.frameSpace * 2)
          .attr('height', g.node().getBBox().height + this.frameSpace * 2);

      boxTemp = d3.select(`${idStr}g[id="${name}_unfold"]`).node().getBBox();
      // After the namespace dom is successfully encapsulated, set the related data of the data object.
      this.allGraphData[name].isUnfold = true;
      this.allGraphData[name].size = [boxTemp.width / 72, boxTemp.height / 72];

      if (d3.select(`#subgraphTemp svg`).size()) {
        // Migrate the dom file in subgraph to the new namescope file.
        const nodeTemp = document.querySelector('#subgraphTemp #graph0 g');
        const name = nodeTemp.id.replace('_unfold', '');
        const node = document.querySelector(`#graphTemp g[id="${name}"]`);
        const box = node.getBBox();
        const boxTemp = nodeTemp.getBBox();
        const translateStr = `translate(${box.x - boxTemp.x},${
          box.y - boxTemp.y
        })`;
        nodeTemp.setAttribute('transform', translateStr);
        node.parentNode.appendChild(nodeTemp);
        document.querySelector('#subgraphTemp svg').remove();
        node.remove();
      }
      // Delete unnecessary g nodes from graphTemp.
      const domList = document.querySelector('#graphTemp #graph0').children;
      for (let i = 0; i < domList.length; i++) {
        if (domList[i].id !== `${name}_unfold`) {
          domList[i--].remove();
        }
      }

      this.generateIOBus(name);
      // Move the DOM station in graphTemp to subgraph, and then graphTemp continue to lay out the outer graph.
      document
          .querySelector('#subgraphTemp')
          .appendChild(document.querySelector('#graphTemp svg'));
      this.transplantChildrenDom(name);
      this.layoutController(name);
    },
    /**
     * Move the namespace dom generated in graphTemp to subgraphTemp for storage.
     * @param {String} name Name of the namespace to be expanded.
     */
    transplantChildrenDom(name) {
      let nameList = [];
      let idStr = '#subgraphTemp ';
      if (name) {
        nameList = this.allGraphData[name].children;
      } else {
        idStr = '#graph ';
        nameList = this.firstFloorNodes;
      }
      nameList.forEach((i) => {
        const nodeData = this.allGraphData[i];
        const flag =
          (nodeData.type === 'name_scope' ||
            nodeData.type === 'aggregation_scope') &&
          nodeData.isUnfold;
        if (flag) {
          // Place the dom character string in graphTemp and then move it to the corresponding node of subgraphTemp.
          document.querySelector('#graphTemp').innerHTML = nodeData.html;
          const node = document.querySelector(`${idStr}g[id="${i}"]`);
          const nodeTemp = document.querySelector(
              `#graphTemp #graph0 g[id="${i}_unfold"]`,
          );
          if (node && nodeTemp) {
            const box = node.getBBox();
            const boxTemp = nodeTemp.getBBox();
            const translateStr = `translate(${box.x - boxTemp.x},${
              box.y - boxTemp.y
            })`;
            nodeTemp.setAttribute('transform', translateStr);
            node.parentNode.appendChild(nodeTemp);
            node.remove();
          }
          const svg = document.querySelector('#graphTemp svg');
          if (svg) {
            svg.remove();
          }
        }
      });
      if (name) {
        this.allGraphData[name].html = document.querySelector(
            `#subgraphTemp svg`,
        ).outerHTML;
      }
    },
    /**
     * Add the input and output buses of the namespace.
     * @param {String} name Name of the namespace to be expanded.
     */
    generateIOBus(name) {
      if (d3.select(`#graphTemp g[id="analogNodesInputOf${name}"]`).size()) {
        this.generateEdge(
            {source: `${name}_unfold`, target: `analogNodesInputOf${name}`},
            name,
            'input',
        );
      }
      if (d3.select(`#graphTemp g[id="analogNodesOutputOf${name}"]`).size()) {
        this.generateEdge(
            {source: `analogNodesOutputOf${name}`, target: `${name}_unfold`},
            name,
            'output',
        );
      }
    },
    /**
     * Encapsulates the data of the namespace to be expanded.
     * @param {String} name Name of the namespace to be expanded.
     * @return {String} Dot String that is used to package the data of the namespace.
     */
    packageNamescope(name) {
      const nodes = this.getChildNodesByName(name);
      const nodeStr = this.packageNodes(nodes, name);
      const edgeStr = this.packageEdges(nodes, name);
      const initSetting =
        `node[style="filled";fontsize="10px";];` + `edge[fontsize="5px";];`;
      const dotStr =
        `digraph {${initSetting}label="${name.split('/').pop()}";` +
        `${nodeStr}${edgeStr}}`;
      return dotStr;
    },
    /**
     * Generate a edge in graph.
     * @param {Object} edge Edge data
     * @param {String} name Namespace to which the edge belongs.
     * @param {String} port Indicates the input/output type of a edge.
     */
    generateEdge(edge, name, port) {
      const points = this.getEdgePoints(edge, port);
      const text = this.getEdgeLabel(edge);
      const g = d3
          .select(`#graphTemp g#graph0${name ? ` g[id="${name}_unfold"]` : ''}`)
          .append('g')
          .attr(
              'id',
              `${edge.source.replace('_unfold', '')}->${edge.target.replace(
                  '_unfold',
                  '',
              )}`,
          )
          .attr('class', 'edge');
      g.append('title').text(text);
      // Because the edges need to be highlighted, marker requires one side of each side.
      const marker = g.append(`marker`);
      marker
          .attr('id', `${name + port}marker`)
          .attr('refX', 6)
          .attr('refY', 3)
          .attr('markerWidth', 8)
          .attr('markerHeight', 6)
          .attr('orient', 'auto');
      marker
          .append('path')
          .attr('d', 'M1,1 L1,5 L6,3 z')
          .attr('fill', 'rgb(120, 120, 120)')
          .attr('stroke', 'rgb(120, 120, 120)');
      g.append('path')
          .attr('stroke', 'rgb(167, 167, 167)')
          .attr('stroke-width', 1)
          .attr(
              'stroke-dasharray',
              `${edge.edge_type === 'control' ? '5,2' : '0'}`,
          )
          .attr('marker-end', `url(#${name + port}marker)`)
          .attr(
              'd',
              `M${points[0].x},${points[0].y}L${points[1].x},${points[1].y}`,
          );
      g.append('text')
          .attr('text-anchor', 'middle')
          .attr('font-family', 'Times,serif')
          .attr('font-size', '5px')
          .attr('fill', '#000000')
          .attr('x', (points[0].x + points[1].x) / 2)
          .attr('y', (points[0].y + points[1].y) / 2)
          .text(text);
    },
    /**
     * Obtain the location data of the source and target edges.
     * @param {Object} edge Edge data
     * @param {String} port Indicates the input/output type of a edge.
     * @return {Array} Coordinate array of the start point and end point of the edge.
     */
    getEdgePoints(edge, port) {
      const source = d3
          .select(`#graphTemp g[id="${edge.source}"]`)
          .node()
          .getBBox();
      const target = d3
          .select(`#graphTemp g[id="${edge.target}"]`)
          .node()
          .getBBox();
      source.points = this.getBoxPoints(source);
      target.points = this.getBoxPoints(target);
      // The input bus is at the top of the namespace, and the output bus is at the bottom of the namespace.
      if (port === 'input') {
        return [source.points.top, target.points.top];
      } else {
        return [source.points.bottom, target.points.bottom];
      }
    },
    /**
     * Obtains the coordinates of the top and button in the node box.
     * @param {Object} box Edge data
     * @return {Object} Object that contains the top and bottom coordinates of the box.
     */
    getBoxPoints(box) {
      const points = {
        top: {
          x: box.x + box.width / 2,
          y: box.y,
        },
        bottom: {
          x: box.x + box.width / 2,
          y: box.y + box.height,
        },
      };
      return points;
    },
    /**
     * Obtains the transform data of a node.
     * @param {Object} node Node dom data
     * @return {Object} Transform data of a node
     */
    getTransformData(node) {
      if (!node) {
        return {};
      }
      const transformData = node.getAttribute('transform');
      const attrObj = {};
      if (transformData) {
        const lists = transformData.trim().split(' ');
        lists.forEach((item) => {
          item = item.trim();
          if (item) {
            const index1 = item.indexOf('(');
            const index2 = item.indexOf(')');
            const params = item
                .substring(index1 + 1, index2)
                .split(',')
                .map((i) => {
                  return parseFloat(i) || 0;
                });
            attrObj[item.substring(0, index1)] = params;
          }
        });
      }
      return attrObj;
    },
    /**
     * Highlight proxy nodes
     * @param {String} nodeId Node id
     */
    highlightProxyNodes(nodeId) {
      const proxyNodes = d3
          .selectAll('#graph g.node')
          .nodes()
          .filter((node) => {
            const id = node.id.split('^')[0].replace('_unfold', '');
            return id === nodeId;
          });
      const childTagType = ['polygon', 'ellipse', 'path', 'rect'];
      proxyNodes.forEach((i) => {
        if (i.childNodes) {
          i.childNodes.forEach((k) => {
            if (childTagType.includes(k.tagName)) {
              k.setAttribute('class', 'selected');
            }
          });
        }
      });
    },
    /**
     * Highlight the input and output cables related to the selected node.
     * @param {Object} node Data of the selected node
     */
    highLightEdges(node) {
      // Click an operator or namespace to highlight the connection between the operator or namespace and the node and
      // virtual node.
      // Click the aggregation node or its subnodes to highlight the connection between the node and the virtual
      // node and the connection between the namespace and other nodes.
      const edges = {};
      const input = node.input || {};
      const output = node.output || {};
      const name = this.findExsitNode(node.name);
      // Connects to the edge of the actual node.
      if (name && !node.independent_layout) {
        Object.keys(input).forEach((key) => {
          const source = this.findExsitNode(key);
          if (source) {
            edges[`${source}->${name}`] = {
              source: source,
              target: name,
              edge_type: input[key].edge_type || '',
            };
          }
        });
        Object.keys(output).forEach((key) => {
          const target = this.findExsitNode(key);
          if (target) {
            edges[`${name}->${target}`] = {
              source: name,
              target: target,
              edge_type: output[key].edge_type || '',
            };
          }
        });
      }

      if (!node.isUnfold) {
        // Connects to the edge of a virtual node.
        let keys = Object.keys(node.proxy_input || {});
        for (let i = 0; i < Math.min(5, keys.length); i++) {
          const nameTemp = `${keys[i]}^${node.name}`;
          edges[`${nameTemp}->${node.name}`] = {
            source: nameTemp,
            target: node.name,
            edge_type: node.proxy_input[keys[i]].edge_type || '',
          };
        }
        if (keys.length > 5) {
          const nameTemp = `analogNodesInput^${node.name}`;
          edges[`${nameTemp}->${node.name}`] = {
            source: nameTemp,
            target: node.name,
            edge_type: '',
          };
        }
        keys = Object.keys(node.proxy_output || {});
        for (let i = 0; i < Math.min(5, keys.length); i++) {
          const nameTemp = `${keys[i]}^${node.name}`;
          edges[`${node.name}->${nameTemp}`] = {
            source: node.name,
            target: nameTemp,
            edge_type: node.proxy_output[keys[i]].edge_type || '',
          };
        }
        if (keys.length > 5) {
          const nameTemp = `analogNodesOutput^${node.name}`;
          edges[`${node.name}->${nameTemp}`] = {
            source: node.name,
            target: nameTemp,
            edge_type: '',
          };
        }
      }

      // The line of the virtual node does not need to be managed.
      const edgesList = {};
      Object.keys(edges).forEach((key) => {
        if (key.includes('^')) {
          edgesList[key] = edges[key];
        } else {
          const suffix = edges[key].edge_type === 'control' ? '_control' : '';
          const [source, target] = key.split('->');
          const list = [];
          const sourceList = source.split('/');
          const targetList = target.split('/');
          const lengthMin = Math.min(sourceList.length, targetList.length);
          let commonIndex = -1;
          // Find the same prefix.
          for (let i = 0; i < lengthMin; i++) {
            if (
              sourceList.slice(0, i + 1).join('/') ===
              targetList.slice(0, i + 1).join('/')
            ) {
              commonIndex = i;
            }
          }
          // To split the side into several sections
          for (let i = commonIndex + 2; i < sourceList.length; i++) {
            const source = sourceList.slice(0, i + 1).join('/');
            const target = sourceList.slice(0, i).join('/');
            list.push(`${source}->analogNodesOutputOf${target}${suffix}`);
            list.push(`analogNodesOutputOf${target}->${target}`);
          }
          list.push(
              `${sourceList.slice(0, commonIndex + 2).join('/')}->` +
              `${targetList.slice(0, commonIndex + 2).join('/')}${suffix}`,
          );
          for (let i = commonIndex + 2; i < targetList.length; i++) {
            const source = targetList.slice(0, i).join('/');
            const target = targetList.slice(0, i + 1).join('/');
            list.push(`${source}->analogNodesInputOf${source}`);
            list.push(`analogNodesInputOf${source}->${target}${suffix}`);
          }
          // Deduplication and encapsulation of data
          for (let i = 0; i < list.length; i++) {
            const [sourceTemp, targetTemp] = list[i].split('->');
            // Remove the situation where the aggregation node and node are in the same namespace.
            if (
              !(
                sourceTemp.startsWith(targetTemp + '/') ||
                targetTemp.startsWith(sourceTemp + '/')
              )
            ) {
              edgesList[`${sourceTemp}->${targetTemp}`] = {
                source: sourceTemp,
                target: targetTemp,
                edge_type: edges[key].edge_type,
              };
            }
          }
        }
      });

      d3.selectAll('#graph g.edge').classed('highlighted', false);
      Object.keys(edgesList).forEach((key) => {
        d3.select(`#graph g[id="${key}"]`).classed('highlighted', true);
      });
    },
    /**
     * Find the existing namespace based on the node name.
     * @param {String} name Data of the selected node
     * @return {String} Find the existing node by name.
     */
    findExsitNode(name) {
      let subPsth = '';
      const paths = name.split('/');
      for (let i = paths.length; i > 0; i--) {
        const path = paths.slice(0, i).join('/');
        if (this.allGraphData[path]) {
          subPsth = path;
          break;
        }
      }
      if (subPsth && this.allGraphData[subPsth]) {
        // The virtual node and its subnodes need to return their namespaces.
        if (this.allGraphData[subPsth].independent_layout) {
          subPsth = subPsth.split('/').slice(0, -1).join('/');
        }
      }
      return subPsth;
    },
    /**
     * Processes its own and corresponding child node data when expanding or closing namespaces.
     * @param {String} name Data of the selected node
     * @param {Boolean} toUnfold Expand or Not
     * @param {Array} nodes Node array
     */
    packageDataToObject(name, toUnfold, nodes) {
      // If there is no name, it indicates the first layer.
      if (!name) {
        this.allGraphData = {};
        this.firstFloorNodes = [];
        nodes.forEach((node) => {
          node.isUnfold = false;
          node.children = [];
          node.size = [];
          node.html = '';
          this.allGraphData[node.name] = node;
          this.firstFloorNodes.push(node.name);
        });
      } else {
        // Expand the namespace and encapsulate its child node data.
        if (toUnfold) {
          this.allGraphData[name].isUnfold = true;
          nodes.forEach((node) => {
            node.isUnfold = false;
            node.children = [];
            node.size = [];
            node.html = '';
            node.grouped = false;
            node.chained = false;
            node.chainNum = [1];
            this.allGraphData[node.name] = node;
            this.allGraphData[name].children.push(node.name);
          });
        } else {
          // Close the namespace and delete all child node data.
          const allChildren = Object.keys(this.allGraphData).filter((key) => {
            return key.startsWith(`${name}/`);
          });
          allChildren.forEach((key) => {
            delete this.allGraphData[key];
          });

          this.allGraphData[name].isUnfold = false;
          this.allGraphData[name].children = [];
          this.allGraphData[name].size = [];
          this.allGraphData[name].html = '';
        }
      }
    },
    /**
     * Queries the first layer namespace to be expanded for a search node.
     * @param {Object} data All data of the node and the namespace to which the node belongs
     * @return {Object} First namespace to be expanded
     */
    findStartUnfoldNode(data) {
      if (data && data.scope_name) {
        if (this.allGraphData[data.scope_name].isUnfold) {
          if (
            data.nodes.some((node) => {
              return node.name === this.selectedNode.name;
            })
          ) {
            return data;
          } else {
            return this.findStartUnfoldNode(data.children);
          }
        } else {
          return data;
        }
      } else {
        return null;
      }
    },
  },
};
</script>

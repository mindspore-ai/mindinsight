<!--
Copyright 2021 Huawei Technologies Co., Ltd.All Rights Reserved.

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
export default {
  /**
   * The logic of transform object to string in 'dot' form
   * @param {Object} object
   * @return {String}
   */
  objectToDot(object) {
    const keys = Object.keys(object);
    let attrTemp = '';
    let nodesTemp = '';
    let subTemp = '';
    let arrowsTemp = '';
    let mixTemp = '';
    for (let i = 0; i < keys.length; i++) {
      switch (keys[i]) {
        case 'nodes':
          const tempArray = this.nodesToDot(object[keys[i]]);
          nodesTemp = tempArray[0];
          arrowsTemp += tempArray[1];
          break;
        case 'mix':
          const mixTempArray = this.mixToDot(object[keys[i]]);
          mixTemp = mixTempArray[0];
          arrowsTemp += mixTempArray[1];
          break;
        case 'subgraph':
          const subTempArray = this.subToDot(object[keys[i]]);
          subTemp = subTempArray[0];
          arrowsTemp += subTempArray[1];
          break;
        default:
          attrTemp += this.attrToDot(object[keys[i]], keys[i]);
          break;
      }
    }
    const dotTemp = `digraph {${attrTemp}${nodesTemp}${subTemp}${mixTemp}${arrowsTemp}}`;
    return dotTemp;
  },
  /**
   * The logic of transform object.subgraph to string in 'dot' form
   * @param {Object} subgraph
   * @return {String}
   */
  subToDot(subgraph) {
    let subTemp = '';
    let arrowTemp = '';
    for (let i = 0; i < subgraph.length; i++) {
      subTemp += `subgraph <${subgraph[i].name}>{`;
      const keys = Object.keys(subgraph[i]);
      for (let j = 0; j < keys.length; j++) {
        switch (keys[j]) {
          case 'name':
            break;
          case 'nodes':
            const tempArray = this.nodesToDot(subgraph[i].nodes);
            subTemp += tempArray[0];
            arrowTemp += tempArray[1];
            break;
          case 'next':
            arrowTemp += this.nextToDot(subgraph[i].next, subgraph[i].name);
            break;
          default:
            subTemp += `${keys[j]}="${subgraph[i][keys[j]]}";`;
        }
      }
      subTemp += '};';
    }
    return [subTemp, arrowTemp];
  },
  /**
   * The logic of transform 'next' of single item in object.nodes to string in 'dot' form
   * @param {Object} object
   * @param {Object} start
   * @return {String}
   */
  nextToDot(object, start) {
    let arrowTemp = '';
    if (Array.isArray(object)) {
      for (let i = 0; i < object.length; i++) {
        const keys = Object.keys(object[i]);
        arrowTemp += `<${start}>-><${object[i].name}>[`;
        for (let j = 0; j < keys.length; j++) {
          if (keys[j] !== 'name') {
            if (object[i][keys[j]][0] === '<') {
              arrowTemp += `${keys[j]}=${object[i][keys[j]]};`;
            } else {
              arrowTemp += `${keys[j]}="${object[i][keys[j]]}";`;
            }
          }
        }
        arrowTemp += '];';
      }
    } else {
      const keys = Object.keys(object);
      arrowTemp += `<${start}>-><${object.name}>[`;
      for (let i = 0; i < keys.length; i++) {
        if (keys[i] !== 'name') {
          if (object[keys[i]][0] === '<') {
            arrowTemp += `${keys[i]}=${object[keys[i]]};`;
          } else {
            arrowTemp += `${keys[i]}="${object[keys[i]]}";`;
          }
        }
      }
      arrowTemp += '];';
    }
    return arrowTemp;
  },
  /**
   * The logic of transform object.attr to string in 'dot' form
   * @param {Object} object
   * @param {String} title
   * @return {String}
   */
  attrToDot(object, title) {
    const keys = Object.keys(object);
    if (keys.length === 0) {
      return;
    }
    if (title === 'total') {
      let nodeTemp = '';
      for (let i = 0; i < keys.length; i++) {
        nodeTemp += `${keys[i]}="${object[keys[i]]}";`;
      }
      return nodeTemp;
    } else {
      let nodeTemp = `${title}[`;
      for (let i = 0; i < keys.length; i++) {
        nodeTemp += `${keys[i]}="${object[keys[i]]}";`;
      }
      return `${nodeTemp}];`;
    }
  },
  /**
   * The logic of transform object.nodes to string in 'dot' form
   * @param {Array} nodes
   * @return {Array<string>}
   */
  nodesToDot(nodes) {
    let nodesTemp = '';
    let arrowsTemp = '';
    for (let i = 0; i < nodes.length; i++) {
      const tempArray = this.nodeToDot(nodes[i]);
      nodesTemp += tempArray[0];
      arrowsTemp += tempArray[1];
    }
    return [nodesTemp, arrowsTemp];
  },
  /**
   * The logic of transform object.mix to string in 'dot' form
   * @param {Array} mix
   * @return {Array<string>}
   */
  mixToDot(mix) {
    let nodesTemp = '';
    let arrowsTemp = '';
    for (let i = 0; i < mix.length; i++) {
      const keys = Object.keys(mix[i]);
      let attrTemp = '';
      let nodeTemp = '';
      for (let j = 0; j < keys.length; j++) {
        if (keys[j] === 'nodes') {
          const tempArray = this.nodesToDot(mix[i].nodes);
          nodeTemp += tempArray[0];
          arrowsTemp += tempArray[1];
        } else {
          attrTemp += `${keys[j]}="${mix[i][keys[j]]}";`;
        }
      }
      nodesTemp += `{${attrTemp}${nodeTemp}};`;
    }
    return [nodesTemp, arrowsTemp];
  },
  /**
   * The logic of transform single item in object.nodes to string in 'dot' form
   * @param {String} node
   * @return {Array<string>}
   */
  nodeToDot(node) {
    let nodeTemp = `<${node.name}>[`;
    let arrowTemp = '';
    const keys = Object.keys(node);
    for (let i = 0; i < keys.length; i++) {
      switch (keys[i]) {
        case 'name':
          break;
        case 'next':
          arrowTemp += this.nextToDot(node.next, node.name);
          break;
        default:
          nodeTemp += `${keys[i]}="${node[keys[i]]}";`;
          break;
      }
    }
    nodeTemp += '];';
    return [nodeTemp, arrowTemp];
  },
};
</script>

<script>
import ELK from 'elkjs/lib/elk.bundled';
import {layoutOptions} from '../js/config';
import {
  buildGraph,
  toggleExpanded,
  getTopScopeSet,
  buildPipelinedStageInfo,
  querySingleNode,
  _findTopScope,
  _findExistNameScope,
  getSingleNode,
} from '../js/build-graph';
import {createElkGraph, dataNodeMap} from '../js/create-elk-graph';
import {
  IN_PORT_SUFFIX,
  OUT_PORT_SUFFIX,
  EDGE_SEPARATOR,
  NODE_TYPE,
  INPUT,
  OUTPUT,
  SCOPE_SEPARATOR,
} from '../js/const';
import RequestService from '@/services/request-service';

const CONNECTED_OPACITY = 1;
const UNCONNECTED_OPACITY = 0.4;

export default {
  data() {
    return {
      trainInfo: {
        id: this.$route.query.id,
        path: this.$route.query.path,
        dir: this.$route.query.dir,
      },
      elk: null,
      // ELKGraph data
      nodes: [],
      edges: [],
      ports: [],
      searchEdges: [],
      hoverEdges: [],
      hiddenEdges: [],
      hiddenPolylineEdges: [],
      focusedNode: null,
      // Map of ELKGraph data
      visPortMap: null,
      visEdgeMap: null,
      visNodeMap: null,
      // {Map<string, ExtraAttr>} nodeAttrMap
      nodeAttrMap: {},
      // settings
      option: {
        layoutOptions,
      },
      timer: null,
      bipartite: false,
      synchronizeTransitionDelay: 100,
      pathSearch: {
        active: false,
        start: null,
        end: null,
      },
      // Work for graph transition (only scope)
      previousNodeState: new Map(),
      nodeType: NODE_TYPE,
      // state
      doubleClickScopeEffective: true,
      lastClickNode: null,
      edgeOpacity: CONNECTED_OPACITY,

      focusExpandedMode: false,

      showNodeType: '',
      showNodeTypeOptions: [],

      showRankId: '',
      showRankIdOptions: [],

      parallelStrategy: '',

      pipelinedStageInfo: null,
      pipelineNodeInfo: null,
      pipelineEdgeInfo: null,
      lastStackedParentID: '',
      loading: {
        show: true,
        info: "",
      },
    };
  },

  created() {
    this.elk = new ELK();
  },
  mounted() {
    this.getDisplayedGraph();
  },
  destroyed() {
    this.timer && clearInterval(this.timer);
  },
  methods: {
    // The logic of get displayedGraph
    async getDisplayedGraph(
        showNodeType = null,
        showRankId = null,
    ) {
      const params = {
        profile: this.trainInfo.dir,
        train_id: this.trainInfo.id,
      };
      const fetch = () => {
        RequestService.getGraphData(params)
          .catch(err => {
            this.loading.show = false;
            clearInterval(this.timer);
            throw err;
          })
          .then(res => res.data)
          .then(async (res) => {
            if (res.status === "loading" || res.status === "pending") { // continue loading
              return;
            } else if(res.status === "finish") {
              const {graphs, metadata} = res;
              // pipelined stage
              const {
                pipelinedStageInfo,
                pipelineNodeInfo,
                pipelineEdgeInfo,
              } = buildPipelinedStageInfo(graphs);
              this.pipelinedStageInfo = pipelinedStageInfo;
              this.pipelineNodeInfo = pipelineNodeInfo;
              this.pipelineEdgeInfo = pipelineEdgeInfo;
              // rank selector
              let stageCnt = 0;
              this.showRankIdOptions = Object.keys(graphs).map((key) => {
                const ranks = graphs[key].rank_ids;
                stageCnt += 1;
                return {
                  value: key,
                  label: 'Stage ' + stageCnt + ': ' + JSON.stringify(ranks),
                };
              });
              if (!showRankId) showRankId = 0;
              const visGraph = buildGraph(
                  graphs[showRankId],
                  this.bipartite,
              );
              const topScopeSet = getTopScopeSet();
              this.showNodeTypeOptions = [];
              for (const topScope of topScopeSet) {
                let label;
                if (topScope.indexOf('Recompute') != -1) {
                  label = this.$t('profiling.recomputeGraph');
                } else if (topScope.indexOf('Gradients') != -1) {
                  label = this.$t('profiling.backwardGraph');
                } else if (topScope.indexOf('Default') != -1) {
                  label = this.$t('profiling.forwardGraph');
                }
                this.showNodeTypeOptions.push({
                  value: topScope,
                  label: label,
                });
              }
              this.showNodeType = showNodeType || this.showNodeTypeOptions[0].label;
              this.showRankId = showRankId || this.showRankIdOptions[0].value;
              this.parallelStrategy = metadata.parallel_type;
              const elkGraph = createElkGraph(visGraph, true, this.$store.state.themeIndex);
              await this.elk.layout(elkGraph, this.option).then((res) => {
                this.processDisplayedGraph(res.getDisplayedGraph());
                this.nodeAttrMap = visGraph.nodeAttrMap;
              });
              this.loading.show = false;
              clearInterval(this.timer);
            }
          })
        return fetch;
      };

      this.timer = setInterval(fetch(), 3000);
    },

    /**
     * The logic of process flattenedGraph
     * @param {FlattenedGraph} flattenedGraph
     */
    processDisplayedGraph(flattenedGraph) {
      Object.assign(this, flattenedGraph.array, flattenedGraph.map);
      // NOTE remove transition
    },
    /**
     * The logic of mouse enter DOM of node
     * @param {DisplayedNode} node
     */
    enterScope(node) {
      if (!node) return;
      const hoverEdges = [];
      dataNodeMap.get(node.id).hoverEdges.forEach((id) => {
        if (this.visEdgeMap.has(id)) {
          hoverEdges.push(this.visEdgeMap.get(id));
        }
      });
      this.hoverEdges = hoverEdges;
      node.hover = true;
    },
    /**
     * The logic of mouse leave DOM of node
     * @param {DisplayedNode} node
     */
    leaveScope(node) {
      this.hoverEdges = [];
      node.hover = false;
    },

    /**
     * The logic of mouse double click DOM of node
     * @param {HTMLEvent} event
     * @param {DisplayedNode} node
     */
    async doubleClickScope(event, node) {
      event.stopPropagation();
      if (!this.doubleClickScopeEffective) return;
      this.doubleClickScopeEffective = false;
      this.hoverEdges = [];
      this.resetPathSearch();

      const visGraph = toggleExpanded(node.id);
      await this.updateVisGraph(visGraph);
    },

    async updateVisGraph(visGraph) {
      const elkGraph = createElkGraph(visGraph, false, this.$store.state.themeIndex);

      await this.elk.layout(elkGraph, this.option).then((res) => {
        this.processDisplayedGraph(res.getDisplayedGraph());
        this.lastClickNode = null;
        this.doubleClickScopeEffective = true;
        this.nodeAttrMap = visGraph.nodeAttrMap;
      });
    },

    /**
     * The logic of reset path search info
     */
    resetPathSearch() {
      if (this.pathSearch.start) {
        this.pathSearch.start.selected = false;
        this.pathSearch.start = null;
      }
      if (this.pathSearch.end) {
        this.pathSearch.end.selected = false;
        this.pathSearch.end = null;
      }
      this.searchEdges = [];
    },

    /**
     * The logic of show hidden edges that displayed when mouse hover on any port except ports of root scope
     * @param {ElkPort} port
     * @param {String} strategyTarget only show the edge between port and strategyTarget
     */
    showHiddenEdges(port, strategyTarget) {
      const root = dataNodeMap.get(port.owner).root;
      if (!root) return;
      if (!strategyTarget) {
        this.nodes.forEach((node) => {
          node.opacity = UNCONNECTED_OPACITY;
        });
        this.ports.forEach((port) => {
          port.opacity = UNCONNECTED_OPACITY;
        });
      }
      this.edgeOpacity = UNCONNECTED_OPACITY;
      const hiddenEdges = [];
      const hiddenPolylineEdges = [];
      const targetRootSet = new Set();
      // Keep source and source root port opacity
      this.visNodeMap.get(root).opacity = this.visNodeMap.get(port.owner).opacity = CONNECTED_OPACITY;
      // Add 'source -> source root' hiddenEdges

      const partEdges = this.createHiddenEdge(port.owner, port.isInput);
      partEdges && hiddenEdges.push(partEdges);
      dataNodeMap.get(port.owner)[port.isInput ? INPUT : OUTPUT].forEach((nodeId) => {
        if (isNaN(nodeId)) return;
        nodeId = _findExistNameScope(nodeId);
        // to construct cross-comm edges
        if (!isNaN(nodeId) || nodeId.indexOf(SCOPE_SEPARATOR) !== -1) {
          // operator or scopenode to construct hidden edges
          const outputNode = dataNodeMap.get(nodeId);
          if (
            outputNode &&
            dataNodeMap.get(port.owner).parent.split(SCOPE_SEPARATOR)[0] !==
              outputNode.parent.split(SCOPE_SEPARATOR)[0] &&
            outputNode.parent.length !== 0
          ) {
            // OutputNode/InputNode under different scope node && is not comm node
            const outputPartEdges = this.createHiddenEdge(nodeId, !port.isInput);
            hiddenEdges.push(outputPartEdges);
          }
        }
      });
      dataNodeMap.get(port.owner).hiddenEdges[port.isInput ? INPUT : OUTPUT].forEach((edge) => {
        const targetRoot = dataNodeMap.get(edge).root === '' ? edge : dataNodeMap.get(edge).root;
        if (targetRoot) {
          // the parent of comm nodes is empty string
          if (!targetRootSet.has(targetRoot)) {
            targetRootSet.add(targetRoot);
            // Keep target root port opacity
            if (targetRoot.length !== 0) this.visNodeMap.get(targetRoot).opacity = CONNECTED_OPACITY;
          }
          // Keep target port opacity
          this.visNodeMap.get(edge).opacity = CONNECTED_OPACITY;
        }
      });
      // Add 'source root -> target root' polyline and cross comm edges
      targetRootSet.forEach((target) => {
        if (strategyTarget !== undefined && target !== strategyTarget) return;
        // dataNodeMap.get(target).parent === ""
        const edgeTemp = port.isInput ? `${target}${EDGE_SEPARATOR}${root}` : `${root}${EDGE_SEPARATOR}${target}`;
        if (this.visEdgeMap.has(edgeTemp)) {
          hiddenPolylineEdges.push(this.visEdgeMap.get(edgeTemp));
        } else {
          const topScopePort = _findTopScope(port.owner);
          const suffix = port.isInput ? IN_PORT_SUFFIX : OUT_PORT_SUFFIX;
          const anotherSuffix = port.isInput ? OUT_PORT_SUFFIX : IN_PORT_SUFFIX;
          const start = this.visPortMap.get(`${topScopePort.id}${suffix}`);
          const end = this.visPortMap.get(`${target}${anotherSuffix}`);
          if (start === undefined || end === undefined) return;
          start.opacity = CONNECTED_OPACITY;
          end.opacity = CONNECTED_OPACITY;
          hiddenEdges.push({
            id: `${port.owner}${suffix}${EDGE_SEPARATOR}${target}${anotherSuffix}`,
            draw: this.calEdgeDraw([start.x, start.y], [end.x, end.y]),
          });
        }
      });

      this.hiddenEdges = hiddenEdges;
      this.hiddenPolylineEdges = hiddenPolylineEdges;
    },
    /**
     * The logic of create draw of polyline by two array which stores value of point's x and y
     * @param {String} id ID of port owner
     * @param {Boolean} isInput port type
     * @return {String} draw
     */
    createHiddenEdge(id, isInput) {
      const suffix = isInput ? IN_PORT_SUFFIX : OUT_PORT_SUFFIX;
      const rootPort = `${dataNodeMap.get(id).root}${suffix}`;
      const start = this.visPortMap.get(`${id}${suffix}`);
      const end =
        this.visPortMap.get(rootPort) ||
        this.visPortMap.get(
            `${
            dataNodeMap.get(dataNodeMap.get(id).root)
              ? dataNodeMap.get(dataNodeMap.get(id).root).root
              : dataNodeMap.get(id).root
            }${suffix}`, // the root of the comm node is itself
        );
      if (start === undefined || end === undefined) return;
      start.opacity = CONNECTED_OPACITY;
      end.opacity = CONNECTED_OPACITY;
      return {
        id: `${id}${suffix}${EDGE_SEPARATOR}${rootPort}`,
        draw: this.calEdgeDraw([start.x, start.y], [end.x, end.y]),
      };
    },
    /**
     * The logic of create draw of polyline by two array which stores value of point's x and y
     * @param {Array} start
     * @param {Array} end
     * @return {String} draw
     */
    calEdgeDraw(start, end) {
      if (start[0] > end[0]) [start, end] = [end, start];
      const control1 = [start[0] + (end[0] - start[0]) / 3, start[1]];
      const control2 = [end[0] - (end[0] - start[0]) / 3, end[1]];
      return `
        M ${start[0]} ${start[1]},
        C ${control1[0]} ${control1[1]},
          ${control2[0]} ${control2[1]},
          ${end[0]} ${end[1]}`;
    },
    /**
     * The logic of hide hidden edges that only displayed when mouse hover on any port
     */
    hideHiddenEdges() {
      this.nodes.forEach((node) => {
        node.opacity = 1;
      });
      this.ports.forEach((port) => {
        port.opacity = 1;
      });
      this.edgeOpacity = 1;
      this.hiddenEdges = [];
      this.hiddenPolylineEdges = [];
    },
    /**
     * The logic of find a certain node
     * @param {String} id
     */
    async findNode(id) {
      if (this.focusedNode && id === this.focusedNode.id) return;

      if (this.visNodeMap.has(id)) {
        this.focusNode(this.visNodeMap.get(id));
        return;
      }

      const visGraph = querySingleNode(id);
      if (!visGraph) return;

      // whether this node is stacked
      const nodeParentID = getSingleNode(id).parent;
      let isStacked = false;
      if (nodeParentID.indexOf('[') !== -1) {
        isStacked = true;
      }

      const elkGraph = createElkGraph(visGraph, false, this.$store.state.themeIndex);
      await this.elk.layout(elkGraph, this.option).then((res) => {
        this.processDisplayedGraph(res.getDisplayedGraph());
        if (isStacked) {
          this.focusNode(this.visNodeMap.get(nodeParentID));
          this.lastStackedParentID = nodeParentID;
        } else {
          this.focusNode(this.visNodeMap.get(id));
        }
      });
    },
    /**
     * The logic of focus a certain node
     * @param {Object} node
     */
    focusNode(node) {
      if (!node) return;
      if (this.focusedNode) {
        this.focusedNode.focused = false;
      }
      const {width, height} = getComputedStyle(this.$refs.graphContainer.$vnode.elm);
      const scale = this.$refs.graphContainer.scale;
      this.$refs.graphContainer.moveTo(
          parseInt(width) / 2 - (node.x + node.width / 2) * scale,
          parseInt(height) / 2 - (node.y + node.height / 2) * scale,
      );
      node.focused = true;
      this.focusedNode = node;
      this.$forceUpdate();
    },
  },
};
</script>

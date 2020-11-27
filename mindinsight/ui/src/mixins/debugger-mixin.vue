<script>
import RequestService from '@/services/request-service';
import {select, selectAll, zoom, dispatch} from 'd3';
import 'd3-graphviz';
const d3 = {select, selectAll, zoom, dispatch};
export default {
  data() {
    return {
      conditionRulesMap: this.$t('debugger.tensorTuningRule'),
    };
  },
  methods: {
    showOrigin() {
      this.loadOriginalTree();
      this.queryWatchPoints();
    },
    /**
     * Initialize the condition
     */
    initCondition() {
      RequestService.queryConditions(this.trainId).then((res) => {
        if (res && res.data) {
          this.conditionCollections = res.data;
        }
      });
    },
    transCondition(str) {
      if (!str) {
        return '';
      }
      let temp;
      if (this.conditionRulesMap[str]) {
        temp = this.conditionRulesMap[str];
      } else if (str.endsWith('_lt')) {
        temp = str.replace(/_lt$/, ' <');
      } else if (str.endsWith('_gt')) {
        temp = str.replace(/_gt$/, ' >');
      } else if (str.endsWith('_ge')) {
        temp = str.replace(/_ge$/, ' >=');
      } else {
        temp = str;
      }

      if (temp.includes('max_min')) {
        temp = temp.replace('max_min', 'max-min');
      }
      return temp;
    },
    /**
     * Collaspe btn click function
     */
    collapseBtnClick() {
      this.leftShow = !this.leftShow;
      setTimeout(() => {
        this.resizeCallback();
      }, 500);
    },
    /**
     * Step input validation
     */
    stepChange() {
      if (this.step === '') {
        return;
      }
      const maxStep = 2147483648;
      this.step = this.step
          .toString()
          .replace(/[^\.\d]/g, '')
          .replace(/\./g, '');
      this.step = Number(this.step);
      if (this.step === 0) {
        this.step = 1;
      }
      if (this.step >= maxStep) {
        this.step = maxStep - 1;
      }
    },
    /**
     * Query current node info
     */
    getCurrentNodeInfo() {
      let name = this.currentNodeName;
      const params = {
        mode: 'node',
        params: {
          watch_point_id: this.curWatchPointId ? this.curWatchPointId : 0,
          name,
          single_node: true,
          node_type: 'leaf',
        },
      };
      if (this.graphFiles.value === this.$t('debugger.all')) {
        name = `${this.metadata.graph_name}/${this.currentNodeName}`;
        params.params.name = name;
      } else {
        if (this.metadata.graph_name !== this.graphFiles.value) {
          this.graphFiles.value = this.metadata.graph_name;
          this.isCurrentGraph = false;
        }
        params.params.graph_name = this.graphFiles.value;
      }
      RequestService.retrieve(params).then(
          (res) => {
            if (res.data) {
              if (res.data.metadata) {
                this.dealMetadata(res.data.metadata);
              }
              if (res.data.graph) {
                const graph = res.data.graph;
                if (graph.nodes && !this.isCurrentGraph) {
                  this.node.childNodes = [];
                  this.origialTree = graph.nodes.map((val) => {
                    return {
                      label: val.name.split('/').pop(),
                      leaf: val.type === 'name_scope' || val.type === 'aggregation_scope' ? false : true,
                      ...val,
                      showCheckbox: val.watched !== -1,
                    };
                  });
                  this.resolve(this.origialTree);
                  // watched 0:unchecked  1:indeterminate 2:checked -1:no checkbox
                  this.node.childNodes.forEach((val) => {
                    if (val.data.watched === this.checkboxStatus.checked) {
                      val.checked = true;
                    }
                    if (val.data.watched === this.checkboxStatus.indeterminate) {
                      val.indeterminate = true;
                    }
                  });
                  this.isCurrentGraph = true;
                  this.firstFloorNodes = [];
                  this.allGraphData = {};
                  d3.select('#graph svg').remove();
                  this.selectedNode.name = '';
                  this.packageDataToObject('', true, JSON.parse(JSON.stringify(graph.nodes)));
                  this.querySingleNode(JSON.parse(JSON.stringify(graph)), name, true);
                } else {
                  this.querySingleNode(JSON.parse(JSON.stringify(graph)), name, true);
                }
                if (graph.children) {
                  this.dealTreeData(graph.children, name);
                  this.defaultCheckedArr = this.$refs.tree.getCheckedKeys();
                }
              }
            }
          },
          (err) => {
            this.showErrorMsg(err);
          },
      );
    },
    /**
     * Query next node info
     */
    getNextNodeInfo() {
      this.watchPointHits = [];
      const params = {
        mode: 'continue',
        level: 'node',
        name: '',
        graph_name: this.graphFiles.value,
      };
      if (this.graphFiles.value === this.$t('debugger.all')) {
        delete params.graph_name;
      }
      RequestService.control(params).then(
          (res) => {},
          (err) => {
            this.showErrorMsg(err);
          },
      );
    },
    /**
     * In Ascend environment,query node info.
     * @param {Boolean} ascend previous or next
     */
    getNodeByBfs(ascend) {
      const data = this.$refs.tree.getCurrentNode();
      let name = this.$refs.tree.getCurrentKey();
      if (
        (data && (data.type === 'name_scope' || data.type === 'aggregation_scope')) ||
        this.curLeafNodeName === null
      ) {
        name = this.curLeafNodeName;
      }
      const params = {
        ascend,
        name,
        watch_point_id: this.curWatchPointId ? this.curWatchPointId : 0,
        graph_name: this.graphFiles.value,
      };
      if (this.graphFiles.value === this.$t('debugger.all')) {
        delete params.graph_name;
      }
      RequestService.retrieveNodeByBfs(params).then(
          (res) => {
            if (res.data && res.data.graph && res.data.name) {
              this.retrieveTensorHistory({name: res.data.name});
              const graph = res.data.graph;
              this.curLeafNodeName = res.data.name;
              this.nodeName = res.data.name;
              if (graph.children) {
                this.dealTreeData(graph.children, name);
                this.defaultCheckedArr = this.$refs.tree.getCheckedKeys();
              }
              this.querySingleNode(JSON.parse(JSON.stringify(graph)), res.data.name);
            } else if (ascend) {
              this.$message.success(this.$t('debugger.nextNodeTip'));
            } else {
              this.$message.success(this.$t('debugger.previousNodeTip'));
            }
          },
          (err) => {
            this.showErrorMsg(err);
          },
      );
    },
    /**
     * Terminate current training
     */
    terminate() {
      this.$confirm(this.$t('debugger.ternimateConfirm'), this.$t('public.notice'), {
        confirmButtonText: this.$t('public.sure'),
        cancelButtonText: this.$t('public.cancel'),
        type: 'warning',
      }).then(
          () => {
            this.control(2);
          },
          (err) => {
            this.showErrorMsg(err);
          },
      );
    },
    /**
     * Table row add className
     * @return { String }
     */
    tableRowClassName({row}) {
      if (row.is_hit) {
        return 'success-row';
      }
      return '';
    },
    /**
     * Table merged cells
     * @return { Object }
     */
    objectSpanMethod({row, column, rowIndex, columnIndex}) {
      let inputLength = 0;
      let outputLength = 0;
      if (this.tabs.activeName === 'tensor') {
        inputLength = this.inputLength;
        outputLength = this.outputLength;
      } else {
        inputLength = this.selectedNode.inputNum;
        outputLength = this.selectedNode.outputNum;
      }
      if (columnIndex === 0 && outputLength > 0) {
        if (rowIndex === 0) {
          return {
            rowspan: outputLength,
            colspan: 1,
          };
        } else if (rowIndex > 0 && rowIndex < outputLength) {
          return {
            rowspan: 0,
            colspan: 0,
          };
        } else if (rowIndex === outputLength) {
          return {
            rowspan: inputLength,
            colspan: 1,
          };
        } else {
          return {
            rowspan: 0,
            colspan: 0,
          };
        }
      }
    },
    /**
     * Table header merged cells
     * @return { Object }
     */
    discountHeaderStyle({row, column, rowIndex, columnIndex}) {
      if (rowIndex === 1) {
        return {display: 'none'};
      }
    },
    /**
     * Handle node click
     * @param { Object } data node data
     */
    handleNodeClick(data) {
      this.isIntoView = false;
      this.selectedNode.name = data.name;
      if (this.treeFlag) {
        this.querySingleNode({}, data.name, true);
      } else {
        if (this.graphFiles.value === this.$t('debugger.all')) {
          if (data.name.includes('/')) {
            const graphName = data.name.split('/')[0];
            this.queryAllTreeData(data.name.replace(`${graphName}/`, ''), true, graphName);
          } else {
            this.queryAllTreeData(data.name, true, data.name);
          }
        } else {
          this.queryAllTreeData(data.name, true, this.graphFiles.value);
        }
      }
    },
    /**
     * Query tensor value
     * @param { Object } data node info
     * @param { String } graphName Graph name
     */
    retrieveTensorHistory(data, graphName) {
      const params = {
        name: data.name,
      };
      if (this.graphFiles.value === this.$t('debugger.all')) {
        params.name = `${graphName}/${data.name}`;
      } else {
        params.graph_name = graphName;
      }
      RequestService.retrieveTensorHistory(params).then(
          (res) => {
            if (res.data && res.data.metadata) {
              this.dealMetadata(res.data.metadata);
            }
            if (data.name === this.nodeName) {
              if (res.data && res.data.tensor_history) {
                this.tableData = res.data.tensor_history;
                this.dealTableData(this.tableData);
              } else {
                this.tableData = [];
              }
            }
          },
          (err) => {
            this.showErrorMsg(err);
          },
      );
    },
    /**
     * Deal tensor history table data
     * @param {Array} arr tensor history data
     */
    dealTableData(arr) {
      const output = arr.filter((val) => val.type === 'output');
      const input = arr.filter((val) => val.type === 'input');
      this.outputLength = output.length;
      this.inputLength = input.length;
      arr.splice(0, arr.length, ...output.concat(input));
      arr.forEach((val) => {
        if (Array.isArray(val.shape)) {
          val.shape = `[${val.shape.toString()}]`;
        } else {
          if (val.shape !== undefined) {
            val.shape = val.shape + '';
          }
        }
        if (val.value === 'click to view') {
        } else {
          if (Array.isArray(val.value)) {
            val.value = `[${val.value.toString()}]`;
          } else {
            if (val.value !== undefined) {
              val.value = val.value + '';
            }
          }
        }
        if (val.dtype !== undefined) {
          val.dtype = val.dtype + '';
        }
      });
    },
    /**
     * Deal metadata
     * @param {Object} metadata metadata
     * @param {Boolean} isQuery wheather to query tree data
     */
    dealMetadata(metadata) {
      if (
        metadata.graph_name &&
        metadata.graph_name !== this.graphFiles.value &&
        this.graphFiles.value !== this.$t('debugger.all')
      ) {
        this.graphFiles.value = metadata.graph_name;
        this.isCurrentGraph = false;
      }
      this.metadata.pos = metadata.pos;
      this.enableRecheck = metadata.enable_recheck;
      if (metadata.state) {
        this.metadata.state = metadata.state;
      }
      if (metadata.debugger_version) {
        this.debuggerVersion = metadata.debugger_version;
      }
      if (metadata.node_name !== undefined && metadata.step !== undefined) {
        const nodeName = metadata.node_name;
        if ((nodeName !== this.currentNodeName && nodeName !== '') || this.metadata.step !== metadata.step) {
          this.nodeName = nodeName ? nodeName : this.nodeName;
          this.currentNodeName = nodeName ? nodeName : this.currentNodeName;
          this.metadata.step = metadata.step;
          this.metadata.graph_name = metadata.graph_name ? metadata.graph_name : this.metadata.graph_name;
          let graphName = this.graphFiles.value === this.$t('debugger.all') ? '' : this.graphFiles.value;
          if (this.graphFiles.value === this.$t('debugger.all') && this.selectedNode.name) {
            graphName = this.selectedNode.name.split('/')[0];
          }
          if (metadata.graph_name) {
            graphName = metadata.graph_name;
          }
          if (this.nodeName) {
            this.queryAllTreeData(this.nodeName, true, graphName);
          }
        }
      }
      if (metadata.step && metadata.step > this.metadata.step) {
        this.metadata.step = metadata.step;
      }

      if (metadata.graph_name && metadata.tensor_name && this.tensorCompareFlag) {
        const debTensor = this.$refs['deb-tensor'];
        if (debTensor) {
          debTensor.updateGraphData(metadata.graph_name, metadata.tensor_name);
        }
      }
    },
    /**
     * Long polling,update some info
     */
    pollData() {
      const params = {
        pos: this.metadata.pos,
        graph_name: this.graphFiles.value,
      };
      if (this.graphFiles.value === this.$t('debugger.all')) {
        delete params.graph_name;
      }
      RequestService.pollData(params).then(
          (res) => {
            if (res.data) {
              if (res.data.metadata) {
                this.dealMetadata(res.data.metadata);
              }
              let name = null;
              if (this.$refs.tree && this.$refs.tree.getCurrentKey()) {
                name = this.$refs.tree.getCurrentKey();
              }
              let graphName = this.graphFiles.value;
              if (
                res.data.receive_tensor &&
              res.data.metadata &&
              res.data.metadata.step >= this.metadata.step &&
              res.data.receive_tensor.node_name === name
              ) {
                if (this.graphFiles.value === this.$t('debugger.all')) {
                  graphName = name.split('/')[0];
                  name = name.replace(`${graphName}/`, '');
                }
                this.retrieveTensorHistory(
                    {
                      name,
                    },
                    graphName,
                );
              }
              if (res.data.watch_point_hits && res.data.watch_point_hits.length > 0) {
                this.radio1 = 'hit';
                this.getWatchpointHits();
              }
              this.pollData();
            }
          },
          (err) => {
            if (!err || (err && err.message !== 'routeJump')) {
              this.initFail = true;
              this.dialogVisible = true;
            }
          },
      );
    },
    /**
     * Step,continue,pause,terminate opesssrate
     * @param {Number} type
     */
    control(type) {
      if (type !== 3) {
        this.watchPointHits = [];
      }
      const params = {};
      if (type === 0) {
        if (!this.step) {
          return;
        }
        params.mode = 'continue';
        params.steps = parseInt(this.step);
      } else if (type === 1) {
        params.mode = 'continue';
        params.steps = -1;
      } else if (type === 2) {
        params.mode = 'terminate';
      } else if (type === 3) {
        params.mode = 'pause';
      }
      RequestService.control(params).then(
          (res) => {
            if (res.data && res.data.metadata) {
              const h = this.$createElement;
              this.$message({
                message: h('p', null, [
                  h('span', null, this.$t('debugger.backstageStatus')),
                  h('i', {style: 'color: teal'}, res.data.metadata.state),
                ]),
              });
              this.metadata.state = res.data.metadata.state;
            }
          },
          (err) => {
            this.showErrorMsg(err);
          },
      );
    },
    /**
     * Show orginal tree
     */
    loadOriginalTree() {
      this.node.childNodes = [];
      this.curWatchPointId = null;
      this.defaultCheckedArr = [];
      this.resolve(JSON.parse(JSON.stringify(this.origialTree)));
      this.resetGraph();
    },
    recheckWatchpoint() {
      RequestService.recheckWatchPoints().then(
          (res) => {
            if (res && res.data && res.data.metadata) {
              this.enableRecheck = res.data.metadata.enable_recheck;
            }
            this.$message.success(this.$t('debugger.recheckSuccess'));
          },
          (err) => {},
      );
    },
    /**
     * Add watchpoint
     */
    addWatchPoint() {
      this.createWatchPointArr = [];
      this.createWatchPointArr.push({
        collection: {
          selectedId: this.conditionCollections[0].id,
        },
        condition: {
          selectedId: '',
          options: [],
        },
        param: {
          options: [],
          name: '',
          value: '',
          type: '',
        },
        compositeParams: {
          options: [],
          selections: [],
        },
      });
      this.collectionChange(this.createWatchPointArr[0]);
      this.createWPDialogVisible = true;
      this.curWatchPointId = null;
    },
    /**
     * Delete new watchpoint
     * @param {Object} item watchpoint data
     */
    deleteWatchpoint(item) {
      if (!this.watchPointArr.length) {
        return;
      }
      if ((item && item.id) || !item) {
        const msg = item ? this.$t('debugger.deleteWatchpointConfirm') : this.$t('debugger.clearWatchpointConfirm');
        this.$confirm(msg, this.$t('public.notice'), {
          confirmButtonText: this.$t('public.sure'),
          cancelButtonText: this.$t('public.cancel'),
          type: 'warning',
        }).then(() => {
          const params = {watch_point_id: item ? item.id : null};
          RequestService.deleteWatchpoint(params).then(
              (res) => {
                if (!item) {
                  this.curWatchPointId = null;
                  this.watchPointArr = [];
                }
                this.loadOriginalTree();
                this.queryWatchPoints();
                this.$message.success(this.$t('debugger.successDeleteWP'));
                if (res && res.data && res.data.metadata) {
                  this.enableRecheck = res.data.metadata.enable_recheck;
                }
                this.curWatchPointId = null;
              },
              (err) => {
                this.showErrorMsg(err);
              },
          );
        });
      } else {
        this.curWatchPointId = null;
      }
    },
    validateParam(item) {
      this.$forceUpdate();
      const reg = /^(\-|\+)?\d+(\.\d+)?$/;
      this.validPram = reg.test(item.param.value);
      item.compositeParams.selections.forEach((i) => {
        this.validPram = this.validPram && reg.test(i.value);
      });
    },
    /**
     * Create new watchpoint
     * @param {Boolean} creatFlag Whether create watchpoint
     */
    createWatchPoint(creatFlag) {
      if (creatFlag) {
        const item = this.createWatchPointArr[0];
        const params = {
          condition: {
            id: item.condition.selectedId,
            params: [],
          },
          watch_nodes: [],
          graph_name: this.graphFiles.value,
        };
        if (this.graphFiles.value === this.$t('debugger.all')) {
          delete params.graph_name;
        }

        if (item.param.options.length) {
          params.condition.params = [
            {
              name: item.param.name,
              value: item.param.type === 'BOOL' ? Boolean(item.param.value) : Number(item.param.value),
            },
          ];
        }
        if (item.compositeParams.selections.length) {
          item.compositeParams.selections.forEach((i) => {
            params.condition.params.push({
              name: i.name,
              value: i.type === 'BOOL' ? Boolean(i.value) : Number(i.value),
            });
          });
        }
        RequestService.createWatchpoint(params).then(
            (res) => {
              this.createWatchPointArr = [];
              this.createWPDialogVisible = false;
              this.$message.success(this.$t('debugger.successCreateWP'));
              if (res && res.data && res.data.metadata) {
                this.enableRecheck = res.data.metadata.enable_recheck;
              }

              this.queryWatchPoints(true);
            },
            (err) => {
              this.loadOriginalTree();
              this.queryWatchPoints();
              this.showErrorMsg(err);
            },
        );
      } else {
        this.createWatchPointArr = [];
        this.createWPDialogVisible = false;
      }
    },
    /**
     * Collection change processing
     * @param {Object} item
     */
    collectionChange(item) {
      const collection = this.conditionCollections.filter((i) => {
        return i.id === item.collection.selectedId;
      })[0];

      if (collection.conditions && collection.conditions.length) {
        item.condition.options = collection.conditions;
        item.condition.selectedId = item.condition.options[0].id;
        this.conditionChange(item);
      } else {
        item.condition.options = [];
        item.condition.selectedId = '';

        item.param.options = [];
        item.param.name = '';
        item.param.type = '';
        item.param.value = '';
        this.validPram = false;
      }
    },
    /**
     * Condition change processing
     * @param {Object} item
     */
    conditionChange(item) {
      const condition = item.condition.options.filter((i) => {
        return i.id === item.condition.selectedId;
      })[0];

      if (condition.parameters && condition.parameters.length) {
        item.param.options = condition.parameters.filter((i) => {
          return i.param_type !== 'SUPPORT_PARAM';
        });

        item.compositeParams.options = condition.parameters.filter((i) => {
          return i.param_type === 'SUPPORT_PARAM';
        });

        item.param.name = item.param.options[0].name;
        this.paramChange(item);
      } else {
        item.param.options = [];
        item.param.name = '';
        item.param.type = '';
        item.param.value = '';
        this.validPram = true;

        item.compositeParams.options = [];
        item.compositeParams.selections = [];
      }
    },
    /**
     * Parameter change processing
     * @param {Object} item
     */
    paramChange(item) {
      const param = item.param.options.filter((i) => {
        return i.name === item.param.name;
      })[0];

      if (param.required_params && param.required_params.length) {
        item.compositeParams.selections = item.compositeParams.options.filter((i) => {
          return param.required_params.includes(i.name);
        });
        item.compositeParams.selections.forEach((i) => {
          i.value = i.type === 'BOOL' ? true : '';
        });
      } else {
        item.compositeParams.selections = [];
      }

      item.param.type = param.type;
      item.param.value = '';
      this.validPram = false;
      if (item.param.type === 'BOOL') {
        item.param.value = true;
        this.validPram = true;
      }
    },
    /** Draw the tree
     * @param {Object} obj Current checked obj
     */
    check(obj) {
      const node = this.$refs.tree.getNode(obj.name);
      const check = node.checked;
      if (this.treeFlag && node.childNodes) {
        this.dealCheckPro(node.childNodes, node.indeterminate || check);
      }
      if (this.curWatchPointId) {
        this.$refs.tree.getCheckedKeys().forEach((val) => {
          const node = this.$refs.tree.getNode(val);
          if (node.data.watched === this.checkboxStatus.noCheckbox) {
            node.checked = false;
          }
        });
        const checkedKeys = this.$refs.tree.getCheckedKeys();
        const watchNodes = [];
        if (this.defaultCheckedArr.length === checkedKeys.length) {
          return;
        } else if (this.defaultCheckedArr.length > checkedKeys.length) {
          watchNodes.push(obj.name);
        } else {
          checkedKeys.forEach((val) => {
            if (this.defaultCheckedArr.indexOf(val) === -1) {
              watchNodes.push(val);
            }
          });
        }
        const params = {
          watch_point_id: this.curWatchPointId ? this.curWatchPointId : 0,
          watch_nodes: watchNodes,
          mode: node.indeterminate || check ? 1 : 0,
          graph_name: this.graphFiles.value,
        };
        if (this.graphFiles.value === this.$t('debugger.all')) {
          delete params.graph_name;
        }
        if (this.searchWord !== '') {
          params.name = this.searchWord;
          params.watch_nodes = [obj.name];
          params.mode = check ? 1 : 0;
        }
        RequestService.updateWatchpoint(params).then(
            (res) => {
              this.defaultCheckedArr = checkedKeys;
              this.enableRecheck = res.data.metadata.enable_recheck;
              this.$nextTick(() => {
                if (node.indeterminate) {
                  node.checked = true;
                  node.indeterminate = false;
                }
                if (check) {
                  this.dealParentNode(node);
                }
              });
            },
            (err) => {
              this.showErrorMsg(err);
            },
        );
      }
    },
    dealParentNode(node) {
      const parent = node.parent;
      if (
        parent &&
        !parent.childNodes.filter((val) => val.data.watched !== -1).find((val) => val.checked === false)
      ) {
        parent.checked = true;
        parent.indeterminate = false;
        this.dealParentNode(parent);
      }
    },
    searchCheck(obj) {
      const node = this.$refs.searchTree.getNode(obj.name);
      const check = node.checked;
      if (node.childNodes) {
        this.dealCheckPro(node.childNodes, node.indeterminate || check);
      }
      const checkedKeys = this.$refs.searchTree.getCheckedKeys();
      const watchNodes = [];
      if (this.searchCheckedArr.length === checkedKeys.length) {
        return;
      } else if (this.searchCheckedArr.length > checkedKeys.length) {
        watchNodes.push(obj.name);
      } else {
        checkedKeys.forEach((val) => {
          if (this.searchCheckedArr.indexOf(val) === -1) {
            watchNodes.push(val);
          }
        });
      }
      const params = {
        watch_point_id: this.curWatchPointId ? this.curWatchPointId : 0,
        watch_nodes: watchNodes,
        mode: check ? 1 : 0,
        graph_name: this.graphFiles.value,
        search_pattern: {name: this.searchedWord},
      };
      if (this.graphFiles.value === this.$t('debugger.all')) {
        delete params.graph_name;
      }
      if (this.nodeTypes.value !== 'all') {
        params.search_pattern.node_category = this.nodeTypes.value;
      }
      RequestService.updateWatchpoint(params).then(
          (res) => {
            this.searchCheckedArr = checkedKeys;
            this.enableRecheck = res.data.metadata.enable_recheck;
            this.$nextTick(() => {
              if (node.indeterminate) {
                node.checked = true;
                node.indeterminate = false;
              }
              if (check) {
                this.dealParentNode(node);
              }
            });
          },
          (err) => {
            this.showErrorMsg(err);
          },
      );
    },
    /** Deal tree data
     * @param {Object} childNodes tree node
     * @param { Boolean } check check status
     */
    dealCheckPro(childNodes, check) {
      childNodes.forEach((val) => {
        val.indeterminate = false;
        if (val.data.watched !== -1) {
          val.checked = check;
        } else {
          val.checked = false;
        }
        if (val.childNodes) {
          this.dealCheckPro(val.childNodes, check);
        }
      });
    },
    /**
     * Collapse node
     * @param {Object} _
     * @param {Object} node node data
     */
    nodeCollapse(_, node) {
      node.loaded = false;
      node.childNodes = [];
      if (this.treeFlag) {
        this.dealDoubleClick(node.data.name);
      }
    },
    /**
     * Function to be executed after the search value changes
     */
    filterChange() {
      if (this.searchWord === '' && this.nodeTypes.value === 'all') {
        this.treeFlag = true;
        this.$nextTick(() => {
          setTimeout(() => {
            const dom = document.querySelector('.el-tree-node.is-current.is-focusable');
            if (dom) {
              dom.scrollIntoView();
            }
          }, 800);
        });
      }
    },
    /**
     * Filter tree data by node name
     */
    filter() {
      this.treeFlag = this.searchWord === '' && this.nodeTypes.value === 'all';
      if (this.searchWord || this.nodeTypes.value !== 'all') {
        this.searchedWord = this.searchWord;
        const params = {
          name: this.searchWord,
          watch_point_id: this.curWatchPointId ? this.curWatchPointId : 0,
          graph_name: this.graphFiles.value,
        };
        if (this.graphFiles.value === this.$t('debugger.all')) {
          delete params.graph_name;
        }
        if (this.nodeTypes.value !== 'all') {
          params.node_category = this.nodeTypes.value;
        }
        RequestService.search(params).then(
            (res) => {
              if (res.data && res.data.nodes) {
                this.searchTreeData = res.data.nodes;
                this.searchHalfCheckedArr = [];
                this.searchCheckedArr = [];
                this.dealSearchResult(this.searchTreeData);
                this.searchNode.childNodes = [];
                const data = res.data.nodes.map((val) => {
                  return {
                    label: val.name.split('/').pop(),
                    ...val,
                    showCheckbox: val.watched !== -1,
                  };
                });
                const currentData = JSON.parse(JSON.stringify(data));
                currentData.forEach((val) => {
                  val.nodes = [];
                });
                this.searchResolve(currentData);
                // watched 0:unchecked  1:indeterminate 2:checked -1:no checkbox
                this.searchNode.childNodes.forEach((val) => {
                  if (val.data.watched === this.checkboxStatus.indeterminate) {
                    val.indeterminate = true;
                  }
                  if (val.data.watched === this.checkboxStatus.checked) {
                    val.checked = true;
                  }
                  if (val.data.watched === this.checkboxStatus.unchecked) {
                    val.checked = false;
                  }
                });
                data.forEach((val, key) => {
                  if (val.nodes && val.nodes.length) {
                    val.nodes.forEach((value) => {
                      value.parentName = val.name;
                    });
                    this.dealSearchTreeData(val.nodes);
                  }
                });
                this.searchHalfCheckedArr.forEach((val) => {
                  this.$refs.searchTree.getNode(val).indeterminate = true;
                });
              }
            },
            (err) => {
              this.showErrorMsg(err);
            },
        );
      }
    },
    dealSearchTreeData(children) {
      children.forEach((val) => {
        const node = this.$refs.searchTree.getNode(val.parentName);
        val.label = val.name.split('/').pop();
        val.leaf = val.type === 'name_scope' || val.type === 'aggregation_scope' ? false : true;
        val.showCheckbox = val.watched !== -1;
        this.$refs.searchTree.append(val, node);
        node.expanded = true;
        // watched 0:unchecked  1:indeterminate 2:checked -1:no checkbox
        node.childNodes.forEach((value) => {
          if (value.data.watched === this.checkboxStatus.indeterminate) {
            value.indeterminate = true;
          }
          if (value.data.watched === this.checkboxStatus.checked) {
            value.checked = true;
          }
          if (value.data.watched === this.checkboxStatus.unchecked) {
            value.checked = false;
          }
        });
        if (val.nodes && val.nodes.length) {
          val.nodes.forEach((value) => {
            value.parentName = val.name;
          });
          this.dealSearchTreeData(val.nodes);
        }
      });
    },
    /**
     * Deal search data
     * @param {Array} arr search tree data
     */
    dealSearchResult(arr) {
      arr.forEach((val) => {
        if (val.nodes) {
          this.dealSearchResult(val.nodes);
        }
        // watched 0:unchecked  1:indeterminate 2:checked -1:no checkbox
        if (val.watched === this.checkboxStatus.checked) {
          this.searchCheckedArr.push(val.name);
        }
        val.label = val.name.split('/').pop();
      });
    },
    /**
     * Draw the tree
     * @param {Object} node tree root node
     * @param {Function} resolve callback function ,return next node data
     */
    loadNode(node, resolve) {
      if (node.level === 0) {
        const loadingInstance = this.$loading(this.loadingOption);
        node.childNodes = [];
        if (!this.node && !this.resolve) {
          this.node = node;
          this.resolve = resolve;
        }
        const params = {
          mode: 'all',
        };
        RequestService.retrieve(params).then(
            (res) => {
              loadingInstance.close();
              this.initFail = false;
              this.dialogVisible = false;
              if (res.data) {
                if (res.data.graph && res.data.graph.nodes) {
                  this.graphFiles.options = res.data.graph.graph_names || [];
                  if (this.graphFiles.options.length > 1) {
                    this.graphFiles.options.unshift(this.$t('debugger.all'));
                  }
                  this.graphFiles.value = this.graphFiles.options[0];
                  this.origialTree = res.data.graph.nodes.map((val) => {
                    return {
                      label: val.name.split('/').pop(),
                      leaf: val.type === 'name_scope' || val.type === 'aggregation_scope' ? false : true,
                      ...val,
                    };
                  });
                  resolve(this.origialTree);
                  this.dealGraphData(JSON.parse(JSON.stringify(res.data.graph.nodes)));
                }
                if (res.data.watch_points) {
                  this.watchPointArr = res.data.watch_points.map((val) => {
                    return {
                      id: val.id,
                      condition: val.watch_condition.id,
                      params: val.watch_condition.params || [],
                      selected: false,
                    };
                  });
                }
                if (res.data.metadata) {
                  if (res.data.metadata.debugger_version) {
                    this.debuggerVersion = res.data.metadata.debugger_version;
                  }
                  this.metadata = res.data.metadata;
                  this.enableRecheck = res.data.metadata.enable_recheck;
                  if (this.metadata.backend) {
                    this.version = this.metadata.backend;
                  }
                  this.trainId = encodeURIComponent(res.data.metadata.ip);
                  if (this.trainId) {
                    this.initCondition();
                  }
                  if (!res.data.metadata.recommendation_confirmed && this.trainId) {
                    this.recommendWatchPointDialog = true;
                  }

                  this.nodeName = this.metadata.node_name;
                  this.currentNodeName = this.nodeName;
                  if (this.pollInit) {
                    this.pollData();
                    this.pollInit = false;
                  }
                }
              }
            },
            (err) => {
              this.initFail = true;
              this.dialogVisible = true;
              loadingInstance.close();
            },
        );
      } else if (node.level >= 1) {
        this.isIntoView = false;
        const curHalfCheckedKeys = this.$refs.tree.getHalfCheckedKeys();
        const params = {
          mode: 'node',
          params: {
            node_type: node.data.type,
            watch_point_id: this.curWatchPointId ? this.curWatchPointId : 0,
            name: node.data.name,
            graph_name: this.graphFiles.value,
          },
        };
        if (this.graphFiles.value === this.$t('debugger.all')) {
          delete params.params.graph_name;
        }
        RequestService.retrieve(params).then(
            (res) => {
              if (res.data && res.data.metadata) {
                this.dealMetadata(res.data.metadata);
              }
              if (res.data && res.data.graph) {
                const graph = res.data.graph;
                this.curNodeData = graph.nodes.map((val) => {
                  return {
                    label: val.name.split('/').pop(),
                    leaf: val.type === 'name_scope' || val.type === 'aggregation_scope' ? false : true,
                    ...val,
                    showCheckbox: val.watched !== -1,
                  };
                });
                resolve(this.curNodeData);
                // watched 0:unchecked  1:indeterminate 2:checked -1:no checkbox
                this.defaultCheckedArr = this.defaultCheckedArr.concat(
                    this.curNodeData
                        .filter((val) => {
                          return val.watched === this.checkboxStatus.checked;
                        })
                        .map((val) => val.name),
                );
                const halfSelectArr = this.curNodeData
                    .filter((val) => {
                      return val.watched === this.checkboxStatus.indeterminate;
                    })
                    .map((val) => val.name);
                node.childNodes.forEach((val) => {
                  if (halfSelectArr.indexOf(val.data.name) !== -1) {
                    val.indeterminate = true;
                    node.indeterminate = true;
                  }
                });
                [...new Set(curHalfCheckedKeys.concat(this.$refs.tree.getHalfCheckedKeys()))].forEach((val) => {
                  this.$refs.tree.getNode(val).indeterminate = true;
                });
                this.selectedNode.name = node.data.name;
                if (!this.allGraphData[node.data.name].isUnfold) {
                  this.dealGraphData(JSON.parse(JSON.stringify(graph.nodes)), node.data.name);
                } else {
                  this.selectNode(true);
                }
              } else {
                this.selectedNode.name = node.data.name;
                this.selectNode(true);
                resolve([]);
              }
            },
            (err) => {
              this.showErrorMsg(err);
              resolve([]);
            },
        );
      }
    },
    /**
     * Draw the tree
     * @param {Object} node tree root node
     * @param {Function} resolve callback function ,return next node data
     */
    loadSearchNode(node, resolve) {
      if (node.level === 0) {
        node.childNodes = [];
        if (!this.searchNode && !this.searchResolve) {
          this.searchNode = node;
          this.searchResolve = resolve;
        }
      } else if (node.level >= 1) {
        const curHalfCheckedKeys = this.$refs.searchTree.getHalfCheckedKeys();
        if (node.childNodes && node.childNodes.length) {
          node.expanded = true;
          node.loaded = true;
          node.loading = false;
          return;
        }
        const params = {
          mode: 'node',
          params: {
            node_type: node.data.type,
            watch_point_id: this.curWatchPointId ? this.curWatchPointId : 0,
            name: node.data.name,
            graph_name: this.graphFiles.value,
          },
        };
        if (this.graphFiles.value === this.$t('debugger.all')) {
          delete params.params.graph_name;
        }
        RequestService.retrieve(params).then((res) => {
          if (res.data && res.data.metadata) {
            this.dealMetadata(res.data.metadata);
          }
          if (res.data && res.data.graph && res.data.graph.nodes) {
            this.curNodeData = res.data.graph.nodes.map((val) => {
              return {
                label: val.name.split('/').pop(),
                leaf: val.type === 'name_scope' || val.type === 'aggregation_scope' ? false : true,
                ...val,
                showCheckbox: val.watched !== -1,
              };
            });
            resolve(this.curNodeData);
            this.searchCheckedArr = this.searchCheckedArr.concat(
                this.curNodeData
                    .filter((val) => {
                      return val.watched === this.checkboxStatus.checked;
                    })
                    .map((val) => val.name),
            );
            // watched 0:unchecked  1:indeterminate 2:checked -1:no checkbox
            const halfSelectArr = this.curNodeData
                .filter((val) => {
                  return val.watched === this.checkboxStatus.indeterminate;
                })
                .map((val) => val.name);
            node.childNodes.forEach((val) => {
              if (val.data.watched === this.checkboxStatus.checked) {
                val.checked = true;
              }
              if (halfSelectArr.indexOf(val.data.name) !== -1) {
                val.indeterminate = true;
                node.indeterminate = true;
              }
            });
            [...new Set(curHalfCheckedKeys.concat(this.$refs.searchTree.getHalfCheckedKeys()))].forEach((val) => {
              this.$refs.searchTree.getNode(val).indeterminate = true;
            });
          }
        });
      }
    },
    initRecommendWatchPoints(value) {
      this.recommendWatchPointDialog = false;
      const params = {
        trainId: this.trainId,
        body: {
          requestBody: {
            set_recommended: value,
          },
        },
      };
      RequestService.setRecommendWatchPoints(params).then((res) => {
        if (res && res.data) {
          if (value) {
            this.queryWatchPoints(false);
          }
        }
      });
    },
    /**
     * Show data of current selected watchpoint
     * @param {Number} key watchpoint id
     */
    selectWatchPoint(key) {
      this.curLeafNodeName = null;
      this.curHalfCheckedKeys = [];
      this.watchPointArr.forEach((val, index) => {
        if (index === key) {
          if (val.id) {
            val.selected = true;
            this.curWatchPointId = val.id;
            if (this.searchWord === '' && this.nodeTypes.value === 'all') {
              this.queryGraphByWatchpoint(val.id);
            } else {
              this.filter();
            }
          } else {
            this.loadOriginalTree();
          }
        } else {
          if (val.selected) {
            val.selected = false;
          }
        }
      });
    },
    /**
     * Query WatchPoints
     * @param {Boolean} focusLast
     */
    queryWatchPoints(focusLast) {
      const params = {
        mode: 'watchpoint',
        graph_name: this.graphFiles.value,
      };
      if (this.graphFiles.value === this.$t('debugger.all')) {
        delete params.graph_name;
      }
      RequestService.retrieve(params).then(
          (res) => {
            if (res.data.watch_points) {
              this.watchPointArr = res.data.watch_points.map((val) => {
                return {
                  id: val.id,
                  condition: val.watch_condition.id,
                  params: val.watch_condition.params || [],
                  selected: false,
                };
              });

              if (focusLast) {
                this.selectWatchPoint(this.watchPointArr.length - 1);
                this.$nextTick(() => {
                  const newWatchPointDom = document.querySelector('#watch-point-list>li:last-child');
                  if (newWatchPointDom) {
                    newWatchPointDom.scrollIntoView();
                  }
                });
              }
            }
          },
          (err) => {
            this.showErrorMsg(err);
          },
      );
    },
    /**
     * Tree linkage with graph  Expand of current node
     * @param {Obejct} nodes Data of children of current node
     * @param {Obejct} name  The name of the current node
     */
    nodeExpandLinkage(nodes, name) {
      const curNodeData = nodes.map((val) => {
        return {
          label: val.name.split('/').pop(),
          ...val,
          showCheckbox: val.watched !== -1,
        };
      });
      const node = this.$refs.tree.getNode(name);
      curNodeData.forEach((val) => {
        this.$refs.tree.append(val, name);
      });
      // watched 0:unchecked  1:indeterminate 2:checked -1:no checkbox
      node.childNodes.forEach((val) => {
        if (node.checked && !node.childNodes.find((val) => val.data.watched !== 2) && val.data.watched !== -1) {
          val.checked = true;
        }
        if (val.data.watched === this.checkboxStatus.checked) {
          val.checked = true;
        }
        if (val.data.watched === this.checkboxStatus.indeterminate) {
          val.indeterminate = true;
        }
        if (val.data.type !== 'name_scope' && val.data.type !== 'aggregation_scope') {
          val.isLeaf = true;
        }
      });
      node.expanded = true;
      node.loading = false;
      this.$refs.tree.setCurrentKey(name);
      this.defaultCheckedArr = this.$refs.tree.getCheckedKeys();
      this.$nextTick(() => {
        if (
          node.indeterminate &&
          !node.childNodes.filter((val) => val.data.watched !== -1).find((val) => val.checked === false)
        ) {
          node.indeterminate = false;
          node.checked = true;
          this.dealParentNode(node);
        }
        setTimeout(() => {
          const dom = document.querySelector('.el-tree-node.is-current.is-focusable');
          if (dom) {
            dom.scrollIntoView();
          }
        }, 800);
      });
    },
    /**
     * Query WatchpointHits
     */
    getWatchpointHits() {
      if (this.radio1 === 'hit') {
        const params = {
          mode: 'watchpoint_hit',
          graph_name: this.graphFiles.value,
        };
        if (this.graphFiles.value === this.$t('debugger.all')) {
          delete params.graph_name;
        }
        RequestService.retrieve(params).then(
            (res) => {
              if (res.data.metadata) {
                this.dealMetadata(res.data.metadata);
              }
              if (res.data && res.data.watch_point_hits) {
                this.hitsOutdated = res.data.outdated;
                this.dealWatchpointHits(res.data.watch_point_hits);
              }
            },
            (err) => {
              this.showErrorMsg(err);
            },
        );
      } else {
        this.$nextTick(() => {
          setTimeout(() => {
            const dom = document.querySelector('.el-tree-node.is-current.is-focusable');
            if (dom) {
              dom.scrollIntoView();
            }
          }, 200);
        });
      }
    },
    dealWatchpointHits(data) {
      this.watchPointHits = [];
      const tipsMapping = {1: 'NAN', 2: 'INF', 3: 'NAN, INF'};
      if (data && data.length) {
        data.forEach((hit) => {
          const obj = {
            name: hit.node_name,
            lists: [],
            selected: false,
            id: hit.node_name,
            graph_name: hit.graph_name,
          };
          if (hit.tensors && hit.tensors.length) {
            hit.tensors.forEach((i) => {
              const tensorName = `slot: ${i.slot}, `;
              if (i.watch_points && i.watch_points.length) {
                i.watch_points.forEach((j, key) => {
                  let item = `${tensorName} Watch Point Id: ${j.id}, `;
                  if (j.watch_condition) {
                    item += ` ${this.transCondition(j.watch_condition.id)}`;
                    const param = (j.watch_condition.params || [])
                        .map((k) =>
                        k.actual_value === undefined || k.actual_value === null
                          ? `${this.transCondition(k.name)}: ${this.$t('debugger.setValue')}:${k.value}`
                          : `${this.transCondition(k.name)}: ${this.$t('debugger.setValue')}:${k.value}, ${this.$t(
                              'debugger.actualValue',
                          )}:${k.actual_value}`,
                        )
                        .join(', ');
                    if (param) {
                      item += ` (${param})`;
                    }
                  }
                  obj.lists.push({
                    name: item,
                    id: `${key}${hit.node_name}`,
                    tip: j.error_code ? this.$t('debugger.checkTips', {msg: tipsMapping[j.error_code]}) : '',
                  });
                });
              }
            });
          }
          this.watchPointHits.push(obj);
        });
        this.focusWatchpointHit();
      }
    },
    focusWatchpointHit() {
      if (this.selectedNode.name) {
        let selectedNodeName = this.selectedNode.name;
        if (this.graphFiles.value === this.$t('debugger.all')) {
          selectedNodeName = selectedNodeName.replace(`${selectedNodeName.split('/')[0]}/`, '');
        }
        this.expandKeys = [];
        this.watchPointHits.forEach((val) => {
          if (val.name === selectedNodeName) {
            val.selected = true;
            this.expandKeys.push(val.id);
          } else {
            val.selected = false;
          }
        });
        this.$nextTick(() => {
          setTimeout(() => {
            const dom = document.querySelector('.hit-item.selected');
            if (dom) {
              dom.scrollIntoView();
            }
          }, 200);
        });
      }
    },
    /**
     * Update tensor value
     * @param {number} key The index of the node of the watchPointHits currently clicked
     */
    updateTensorValue(key) {
      const currentHit = this.watchPointHits[key];
      const name = currentHit.name;
      const temName = this.nodeName;
      this.nodeName = name;
      this.isHitIntoView = false;
      const params = {
        mode: 'watchpoint_hit',
        params: {
          name,
          single_node: true,
          watch_point_id: this.curWatchPointId ? this.curWatchPointId : 0,
          graph_name: currentHit.graph_name,
        },
      };
      if (this.graphFiles.value === this.$t('debugger.all')) {
        delete params.params.graph_name;
        params.params.name = `${currentHit.graph_name}/${name}`;
      }
      this.watchPointHits.forEach((val, index) => {
        if (key === index) {
          val.selected = true;
        } else {
          val.selected = false;
        }
      });
      this.watchPointHits = JSON.parse(JSON.stringify(this.watchPointHits));
      RequestService.retrieve(params).then(
          (res) => {
            if (res.data.metadata) {
              this.dealMetadata(res.data.metadata);
            }
            this.retrieveTensorHistory({name: this.nodeName}, currentHit.graph_name);
            if (res.data && res.data.graph) {
              const graph = res.data.graph;

              if (
                this.graphFiles.value !== currentHit.graph_name &&
              this.graphFiles.value !== this.$t('debugger.all')
              ) {
                this.graphFiles.value = currentHit.graph_name;
                this.resetAllData(graph, params.params.name);
              } else {
                this.querySingleNode(JSON.parse(JSON.stringify(graph)), params.params.name, true);
              }
              if (graph.children) {
                this.dealTreeData(graph.children, name);
                this.defaultCheckedArr = this.$refs.tree.getCheckedKeys();
              }
            }
          },
          (err) => {
            this.showErrorMsg(err);
            this.nodeName = temName;
          },
      );
    },
    /**
     * Query the graph data
     * @param {String} nodeName The name of the node that needs to be query
     * @param {Boolean} isQueryTensor The name of the node that needs to be query
     * @param {String} graphName Graph file name
     */
    queryAllTreeData(nodeName, isQueryTensor, graphName) {
      let name = nodeName ? nodeName.split(':')[0] : '';
      const params = {
        mode: 'node',
        params: {
          name,
          single_node: true,
          watch_point_id: this.curWatchPointId ? this.curWatchPointId : 0,
        },
      };
      if (this.graphFiles.value === this.$t('debugger.all') && graphName && name) {
        if (name !== graphName) {
          name = `${graphName}/${name}`;
          params.params.name = name;
        }
      } else {
        params.params.graph_name = graphName;
      }
      RequestService.retrieve(params).then(
          (res) => {
            if (res.data && res.data.metadata) {
              this.dealMetadata(res.data.metadata);
            }
            if (res.data && res.data.graph) {
              const graph = res.data.graph;
              if (graph.nodes && !this.isCurrentGraph) {
                this.resetAllData(graph, name);
                this.isCurrentGraph = true;
              } else {
                this.querySingleNode(JSON.parse(JSON.stringify(graph)), name, true);
              }
              if (graph.children) {
                this.dealTreeData(graph.children, name);
                this.defaultCheckedArr = this.$refs.tree.getCheckedKeys();
              }
            }
          },
          (err) => {
            this.showErrorMsg(err);
          },
      );
    },
    /**
     * Draw the tree
     * @param {Object} children child node
     * @param {String} name The name of the node that needs to be highlighted
     */
    dealTreeData(children, name) {
      if (children.nodes) {
        const data = children.nodes.map((val) => {
          return {
            label: val.name.split('/').pop(),
            ...val,
            showCheckbox: val.watched !== -1,
          };
        });
        data.forEach((val) => {
          const node = this.$refs.tree.getNode(children.scope_name);
          if (node.childNodes) {
            if (node.childNodes.map((value) => value.data.name).indexOf(val.name) === -1) {
              this.$refs.tree.append(val, node);
            }
          } else {
            this.$refs.tree.append(val, node);
          }
        });
        const node = this.$refs.tree.getNode(children.scope_name);
        // watched 0:unchecked  1:indeterminate 2:checked -1:no checkbox
        node.childNodes.forEach((val) => {
          if (val.data.watched === this.checkboxStatus.checked) {
            val.checked = true;
          }
          if (val.data.watched === this.checkboxStatus.indeterminate) {
            val.indeterminate = true;
          }
          if (val.data.type !== 'name_scope' && val.data.type !== 'aggregation_scope') {
            val.isLeaf = true;
          }
        });
        node.expanded = true;
        node.loading = false;
      } else {
        this.$refs.tree.setCurrentKey(name);
        this.$nextTick(() => {
          setTimeout(() => {
            const dom = document.querySelector('.el-tree-node.is-current.is-focusable');
            if (dom) {
              dom.scrollIntoView();
            }
          }, 800);
        });
      }
      if (children.children) {
        this.dealTreeData(children.children, name);
      }
    },
    resetAllData(graph, name) {
      this.node.childNodes = [];
      this.origialTree = graph.nodes.map((val) => {
        return {
          label: val.name.split('/').pop(),
          leaf: val.type === 'name_scope' || val.type === 'aggregation_scope' ? false : true,
          ...val,
          showCheckbox: val.watched !== -1,
        };
      });
      this.resolve(this.origialTree);
      // watched 0:unchecked  1:indeterminate 2:checked -1:no checkbox
      this.node.childNodes.forEach((val) => {
        if (val.data.watched === this.checkboxStatus.checked) {
          val.checked = true;
        }
        if (val.data.watched === this.checkboxStatus.indeterminate) {
          val.indeterminate = true;
        }
      });
      this.firstFloorNodes = [];
      this.allGraphData = {};
      d3.select('#graph svg').remove();
      this.packageDataToObject('', true, JSON.parse(JSON.stringify(graph.nodes)));
      if (name) {
        this.querySingleNode(JSON.parse(JSON.stringify(graph)), name, true);
      } else {
        this.resetGraph();
      }
    },
  },
};
</script>

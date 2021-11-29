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
import RequestService from '@/services/request-service';
import { basePath } from '@/services/fetcher';
import { select, selectAll, zoom, dispatch } from 'd3';
import 'd3-graphviz';
const d3 = { select, selectAll, zoom, dispatch };
export default {
  data() {
    return {
      conditionRulesMap: this.$t('debugger.tensorTuningRule'),
      downloadedTensor: {},
      maxFileSize: [2, 'GB'],
    };
  },
  methods: {
    editStep() {
      if (this.metadata.state === this.state.running || this.metadata.state === this.state.sending) {
        return;
      }
      this.isShowInp = true;
      this.newStep = this.metadata.step;
    },
    newStepChange(val) {
      if (val === '') {
        return;
      }
      val = val.replace(/[^0-9]+/g, '');
      if (Number(val) <= this.metadata.total_step_num) {
        this.newStep = Number(val);
      } else {
        this.newStep = this.metadata.total_step_num;
      }
    },
    saveStepValue() {
      this.isShowInp = false;
      if (this.newStep === '' || this.newStep === this.metadata.step) {
        return;
      }
      this.metadata.step = this.newStep;
      const params = {
        mode: 'reset',
        level: 'step',
        steps: this.metadata.step,
        graph_name: this.graphFiles.value,
        rank_id: this.logicCard.value,
      };
      if (this.graphFiles.value === this.$t('debugger.all')) {
        delete params.graph_name;
      }
      RequestService.control(params, this.sessionId).then(
        (res) => {
          if (res && res.data && res.data.metadata && res.data.metadata.enable_recheck !== undefined) {
            this.enableRecheck = res.data.metadata.enable_recheck;
          }
          if (res.data.metadata?.state) {
            this.metadata.state = res.data.metadata.state;
          }
          this.queryTensorHistory();
          if (this.radio1 === 'hit') {
            this.searchWatchpointHits(true);
          }
        },
        (err) => {
          this.showErrorMsg(err);
        }
      );
    },
    getSession() {
      const params = {
        dump_dir: null,
        session_type: 'ONLINE',
      };
      RequestService.getSession(params).then((res) => {
        if (res) {
          this.sessionId = res.data;
          this.retrieveAll();
          this.queryStacks();
        }
      });
    },
    deleteSession() {
      RequestService.deleteSession(this.sessionId).then((res) => {
        this.$router.push({
          path: '/summary-manage',
        });
      });
    },
    handleCurrentChange(page) {
      this.pagination.currentPage = page;
      this.searchWatchpointHits(false);
    },
    showOrigin() {
      this.loadOriginalTree();
      this.queryWatchPoints();
    },
    /**
     * Initialize the condition
     */
    initCondition() {
      if (this.metadata.state === this.state.running || this.metadata.state === this.state.sending) {
        return;
      }
      RequestService.queryConditions(this.sessionId).then((res) => {
        if (res && res.data) {
          this.conditionCollections = res.data;
          this.addWatchPoint();
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
      this.initSvgSize();
    },
    /**
     * Step input validation
     */
    stepChange() {
      if (this.step === '') {
        return;
      }
      const maxStep = this.metadata.total_step_num;
      this.step = this.step
        .toString()
        .replace(/[^\.\d]/g, '')
        .replace(/\./g, '');
      this.step = Number(this.step);
      if (this.step === 0) {
        this.step = 1;
      }
      if (this.step >= maxStep) {
        this.step = maxStep;
      }
    },
    /**
     * Query current node info
     */
    getCurrentNodeInfo() {
      this.loadingInstance = this.$loading(this.loadingOption);
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
      RequestService.retrieve(params, this.sessionId).then(
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
          this.loadingInstance.close();
        },
        (err) => {
          this.showErrorMsg(err);
          this.loadingInstance.close();
        }
      );
    },
    /**
     * Query next node info
     */
    getNextNodeInfo() {
      this.loadingInstance = this.$loading(this.loadingOption);
      this.pagination.currentPage = 1;
      this.watchPointHits = [];
      this.pagination.total = 0;
      const params = {
        mode: 'continue',
        level: 'node',
        name: '',
        graph_name: this.graphFiles.value,
        rank_id: this.logicCard.value,
      };
      if (this.graphFiles.value === this.$t('debugger.all')) {
        delete params.graph_name;
      }
      RequestService.control(params, this.sessionId).then(
        (res) => {},
        (err) => {
          this.showErrorMsg(err);
        }
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
            this.retrieveTensorHistory({ name: res.data.name });
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
        }
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
          if (this.trainId) {
            this.deleteSession();
          } else {
            this.control(2);
          }
        },
        (err) => {
          this.showErrorMsg(err);
        }
      );
    },
    /**
     * Table row add className
     * @return { String }
     */
    tableRowClassName({ row }) {
      if (row.is_hit) {
        return 'success-row';
      }
      return '';
    },
    /**
     * Table merged cells
     * @return { Object }
     */
    objectSpanMethod({ row, column, rowIndex, columnIndex }) {
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
    discountHeaderStyle({ row, column, rowIndex, columnIndex }) {
      if (rowIndex === 1) {
        return { display: 'none' };
      }
    },
    /**
     * Handle node click
     * @param { Object } data node data
     */
    handleNodeClick(data) {
      this.isIntoView = false;
      this.selectedNode.name = data.name;
      if (this.treeFlag && this.allGraphData[data.name]) {
        this.querySingleNode({}, data.name, true);
      } else {
        if (this.graphFiles.value === this.$t('debugger.all')) {
          if (data.name.includes('/')) {
            const graphName = data.name.split('/')[0];
            this.queryAllTreeData(data.name.replace(`${graphName}/`, ''), true, graphName, true);
          } else {
            this.queryAllTreeData(data.name, true, data.name, true);
          }
        } else {
          this.queryAllTreeData(data.name, true, this.graphFiles.value, true);
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
        rank_id: this.logicCard.value,
      };
      if (this.graphFiles.value === this.$t('debugger.all')) {
        params.name = `${graphName}/${data.name}`;
      } else {
        params.graph_name = graphName;
      }
      RequestService.retrieveTensorHistory(params, this.sessionId).then(
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
        }
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
        if (val.bytes) {
          const [value, unit] = this.fileSizeConversion(val.bytes);
          val.oversized = unit === this.maxFileSize[1] && value > this.maxFileSize[0];
        }
      });
    },
    /**
     * Deal metadata
     * @param {Object} metadata metadata
     * @param {Boolean} isQuery whether to query tree data
     */
    dealMetadata(metadata) {
      if (metadata.graph_name 
          && metadata.graph_name !== this.metadata.graph_name 
          && this.graphFiles.value !== this.$t('debugger.all')     
      ) {
        this.graphFiles.value = metadata.graph_name;
        this.isCurrentGraph = false;
      }
      if (metadata.graph_name 
          && metadata.step !== undefined 
          && metadata.step !== this.metadata.step 
          && metadata.graph_name === this.metadata.graph_name 
          && this.graphFiles.value !== metadata.graph_name 
          && this.graphFiles.value !== this.$t('debugger.all')    
      ) {
        this.graphFiles.value = metadata.graph_name;
        this.isCurrentGraph = false;
        this.queryGraphByFile();
      }
      this.metadata.pos = metadata.pos;
      if (metadata.enable_recheck !== undefined) {
        this.enableRecheck = metadata.enable_recheck;
      }
      const temState = this.metadata.state;
      if (metadata.state) {
        this.metadata.state = metadata.state;
      }
      if (metadata.debugger_version) {
        this.debuggerVersion = metadata.debugger_version;
      }
      if (metadata.node_name !== undefined && metadata.step !== undefined) {
        const nodeName = metadata.node_name;
        if (
          (nodeName !== this.currentNodeName && nodeName !== '') ||
          this.metadata.step !== metadata.step ||
          (this.metadata.state === this.state.waiting &&
            (temState === this.state.sending || temState === this.state.running))
        ) {
          if (nodeName) {
            if (this.metadata.state !== this.state.running) {
              this.nodeName = nodeName;
            }
            this.currentNodeName = nodeName;
          }
          this.metadata.step = metadata.step;

          let graphName = this.graphFiles.value === this.$t('debugger.all') ? '' : this.graphFiles.value;
          if (this.graphFiles.value === this.$t('debugger.all') && this.selectedNode.name) {
            graphName = this.selectedNode.name.split('/')[0];
          }
          if (metadata.graph_name) {
            this.metadata.graph_name = metadata.graph_name;
            graphName = metadata.graph_name;
          }

          if (nodeName && this.metadata.state !== this.state.running) {
            if (this.selectedNode.name) {
              if (nodeName === this.selectedNode.name) {
                this.queryTensorHistory();
              } else {
                this.queryAllTreeData(nodeName, true, graphName);
              }
            } else {
              this.queryAllTreeData(nodeName, true, graphName);
            }
          } else {
            if (this.selectedNode.name) {
              this.queryTensorHistory();
            }
          }
        } else {
          this.loadingInstance.close();
        }
      }
      if (metadata.step && metadata.step > this.metadata.step) {
        this.metadata.step = metadata.step;
      }
    },
    /**
     * Update tensor history by current selected node
     */
    queryTensorHistory() {
      if (this.selectedNode.name) {
        const path = this.selectedNode.name.split('^');
        const id = path[0].replace('_unfold', '');
        if (!(id && this.allGraphData[id])) return;
        const type = this.allGraphData[id].type;
        const ignoreType = ['name_scope', 'aggregation_scope'];
        if (!this.selectedNode.name.includes('more...') && !ignoreType.includes(type)) {
          const name = path[0].replace('_unfold', '');
          if (this.graphFiles.value === this.$t('debugger.all')) {
            this.retrieveTensorHistory({ name: name.replace(`${name.split('/')[0]}/`, '') }, name.split('/')[0]);
          } else {
            this.retrieveTensorHistory(
              {
                name,
              },
              this.graphFiles.value
            );
          }
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
        rank_id: this.logicCard.value,
      };
      if (this.graphFiles.value === this.$t('debugger.all')) {
        delete params.graph_name;
      }
      RequestService.pollData(params, this.sessionId).then(
        (res) => {
          if (res.data) {
            if (res.data.metadata) {
              this.dealMetadata(res.data.metadata);
            }
            if(res.data.graph?.graph_names?.length){
              let graphNames = res.data.graph.graph_names.filter(val=>!this.graphFiles.options.includes(val));
              graphNames.filter(val=>!this.graphFiles.options.includes(val))
              this.$message.success(this.$t('debugger.newGraphName', { graphNames }));
              setTimeout(() => {
                location.reload();
              }, 2000);
            }
            let name = null;
            if (this.selectedNode.name) {
              name = this.selectedNode.name.replace('_unfold', '');
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
                graphName
              );
            }
            if (res.data.receive_watchpoint_hits) {
              this.radio1 = 'hit';
              this.pagination.currentPage = 1;
              this.watchPointHits = [];
              this.pagination.total = 0;
              this.searchWatchpointHits(true);
            }

            if (
              res.data.receive_tensor &&
              res.data.receive_tensor.graph_name &&
              res.data.receive_tensor.tensor_name &&
              this.tensorCompareFlag
            ) {
              const debTensor = this.$refs['deb-tensor'];
              if (debTensor) {
                if (res.data.receive_tensor.level === 'stats') {
                  debTensor.updateGraphData(res.data.receive_tensor.graph_name, res.data.receive_tensor.tensor_name);
                } else if (res.data.receive_tensor.level === undefined) {
                  debTensor.tabChange(debTensor.gridType);
                }
              }
            }

            if (res.data.tensor_file) {
              if (this.downloadedTensor.name === res.data.node_name) {
                this.downloadTensor();
              } else {
                this.downloadedTensor.name = res.data.node_name;
              }
            }
            this.pollData();
          }
        },
        (err) => {
          if (!err || (err && err.message !== 'routeJump')) {
            this.initFail = true;
            this.dialogVisible = true;
          }
        }
      );
    },
    /**
     * Step,continue,pause,terminate opesssrate
     * @param {Number} type
     */
    control(type) {
      if (type !== 3) {
        this.pagination.currentPage = 1;
        this.watchPointHits = [];
        this.pagination.total = 0;
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
      RequestService.control(params, this.sessionId).then(
        (res) => {
          if (res.data && res.data.metadata) {
            setTimeout(() => {
              let msg = '';
              if (this.metadata.state === this.state.sending) {
                msg = this.$t('debugger.stateMsg.sending');
              } else if (this.metadata.state === this.state.running) {
                msg = this.$t('debugger.stateMsg.running');
              } else {
                msg = `${this.$t('debugger.backstageStatus')}${this.metadata.state}`;
              }
              this.$message.success(msg);
            }, 500);

            this.metadata.state = res.data.metadata.state;
            if (res.data.metadata.enable_recheck !== undefined) {
              this.enableRecheck = res.data.metadata.enable_recheck;
            }
          }
        },
        (err) => {
          this.showErrorMsg(err);
        }
      );
    },
    /**
     * Show original tree
     */
    loadOriginalTree() {
      this.node.childNodes = [];
      this.curWatchPointId = null;
      this.defaultCheckedArr = [];
      this.resolve(JSON.parse(JSON.stringify(this.origialTree)));
      this.resetGraph();
      this.tabledata = [];
    },
    recheckWatchpoint() {
      if (!this.enableRecheck) {
        return;
      }
      RequestService.recheckWatchPoints(this.sessionId).then(
        (res) => {
          if (res && res.data && res.data.metadata) {
            if (res.data.metadata.enable_recheck !== undefined) {
              this.enableRecheck = res.data.metadata.enable_recheck;
              this.pagination.currentPage = 1;
              this.watchPointHits = [];
              this.pagination.total = 0;
            }
            if (res.data.metadata.state) {
              this.metadata.state = res.data.metadata.state;
            }
          }
          this.$message.success(this.$t('debugger.recheckSuccess'));
        },
        (err) => {}
      );
    },
    /**
     * Add watchpoint
     */
    addWatchPoint() {
      this.paramErrorMsg = this.$t('debugger.paramErrorMsg.errorType');
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
    },
    /**
     * Delete new watchpoint
     * @param {Object} item watchpoint data
     */
    deleteWatchpoint(item) {
      if (
        !this.watchPointArr.length ||
        this.metadata.state === this.state.running ||
        this.metadata.state === this.state.sending
      ) {
        return;
      }
      if ((item && item.id) || !item) {
        const msg = item ? this.$t('debugger.deleteWatchpointConfirm') : this.$t('debugger.clearWatchpointConfirm');
        this.$confirm(msg, this.$t('public.notice'), {
          confirmButtonText: this.$t('public.sure'),
          cancelButtonText: this.$t('public.cancel'),
          type: 'warning',
        }).then(() => {
          const params = { watch_point_id: item ? item.id : null };
          RequestService.deleteWatchpoint(params, this.sessionId).then(
            (res) => {
              if (!item) {
                this.curWatchPointId = null;
                this.watchPointArr = [];
              }
              this.loadOriginalTree();
              this.queryWatchPoints();
              this.$message.success(this.$t('debugger.successDeleteWP'));
              if (res && res.data && res.data.metadata && res.data.metadata.enable_recheck !== undefined) {
                this.enableRecheck = res.data.metadata.enable_recheck;
              }
              this.curWatchPointId = null;
            },
            (err) => {
              this.showErrorMsg(err);
            }
          );
        });
      } else {
        this.curWatchPointId = null;
      }
    },
    validateParam(item) {
      const reg = /^(\-|\+)?\d+(\.\d+)?$/;
      this.validPram = reg.test(item.param.value);
      item.compositeParams.selections.forEach((i) => {
        this.validPram = this.validPram && reg.test(i.value);
      });
      if (!this.validPram) {
        this.paramErrorMsg = this.$t('debugger.paramErrorMsg.errorType');
      } else {
        this.paramErrorMsg = '';
        const inputValue = parseFloat(item.param.value);

        const absParams = [
          'abs_mean_gt',
          'abs_mean_lt',
          'rtol',
          'abs_mean_update_ratio_gt',
          'abs_mean_update_ratio_lt',
        ];
        if (absParams.includes(item.param.name) && inputValue < 0) {
          this.validPram = false;
          this.paramErrorMsg = this.$t('debugger.paramErrorMsg.nonnegative');
        }

        const positiveParams = ['max_min_lt', 'max_min_gt'];
        if (positiveParams.includes(item.param.name) && inputValue <= 0) {
          this.validPram = false;
          this.paramErrorMsg = this.$t('debugger.paramErrorMsg.allPositive');
        }

        if (this.percentParams.includes(item.param.name)) {
          const percentRange = { min: 0, max: 100 };
          if (inputValue < percentRange.min || inputValue > percentRange.max) {
            this.validPram = false;
            this.paramErrorMsg = this.$t('debugger.paramErrorMsg.percentError');
          }
        }

        if (this.validPram && item.compositeParams.selections.length) {
          const rangeKey = ['range_start_inclusive', 'range_end_inclusive'];
          const rangeStart = item.compositeParams.selections.filter((i) => {
            return i.name === rangeKey[0];
          });
          const rangeEnd = item.compositeParams.selections.filter((i) => {
            return i.name === rangeKey[1];
          });
          if (rangeStart.length && rangeEnd.length) {
            const start = parseFloat(rangeStart[0].value);
            const end = parseFloat(rangeEnd[0].value);
            if (start > end) {
              this.validPram = false;
              this.paramErrorMsg = this.$t('debugger.paramErrorMsg.rangeError');
            }
          }
        }
      }
      this.$forceUpdate();
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
          rank_id: this.logicCard.value,
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
        RequestService.createWatchpoint(params, this.sessionId).then(
          (res) => {
            this.createWatchPointArr = [];
            this.createWPDialogVisible = false;
            this.$message.success(this.$t('debugger.successCreateWP'));
            if (res && res.data && res.data.metadata && res.data.metadata.enable_recheck !== undefined) {
              this.enableRecheck = res.data.metadata.enable_recheck;
            }

            this.queryWatchPoints(true);
          },
          (err) => {
            this.loadOriginalTree();
            this.queryWatchPoints();
            this.showErrorMsg(err);
          }
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
        this.paramErrorMsg = this.$t('debugger.paramErrorMsg.errorType');
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
      this.paramErrorMsg = this.$t('debugger.paramErrorMsg.errorType');
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
      if (check) {
        node.data.watched = this.checkboxStatus.checked;
      } else {
        node.data.watched = this.checkboxStatus.unchecked;
      }
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
        this.$nextTick(() => {
          if (node.indeterminate) {
            node.checked = true;
            node.indeterminate = false;
          }
          if (check) {
            this.dealParentNode(node);
          }
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
            rank_id: this.logicCard.value,
          };
          if (this.graphFiles.value === this.$t('debugger.all')) {
            delete params.graph_name;
          }
          RequestService.updateWatchpoint(params, this.sessionId).then(
            (res) => {
              this.defaultCheckedArr = checkedKeys;
              if (res && res.data && res.data.metadata && res.data.metadata.enable_recheck !== undefined) {
                this.enableRecheck = res.data.metadata.enable_recheck;
              }
            },
            (err) => {
              this.showErrorMsg(err);
            }
          );
        });
      }
    },
    dealParentNode(node) {
      const parent = node.parent;
      if (parent && !parent.childNodes.filter((val) => val.data.watched !== -1).find((val) => val.checked === false)) {
        parent.checked = true;
        parent.indeterminate = false;
        this.dealParentNode(parent);
      }
    },
    searchCheck(obj) {
      const node = this.$refs.searchTree.getNode(obj.name);
      const check = node.checked;
      if (check) {
        node.data.watched = this.checkboxStatus.checked;
      } else {
        node.data.watched = this.checkboxStatus.unchecked;
      }
      if (node.childNodes) {
        this.dealCheckPro(node.childNodes, node.indeterminate || check);
      }
      this.$nextTick(() => {
        if (node.indeterminate) {
          node.checked = true;
          node.indeterminate = false;
        }
        if (check) {
          this.dealParentNode(node);
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
          rank_id: this.logicCard.value,
          search_pattern: { name: this.searchedWord },
        };
        if (this.graphFiles.value === this.$t('debugger.all')) {
          delete params.graph_name;
        }
        if (this.nodeTypes.value !== 'all') {
          params.search_pattern.node_category = this.nodeTypes.value;
        }
        RequestService.updateWatchpoint(params, this.sessionId).then(
          (res) => {
            this.searchCheckedArr = checkedKeys;
            if (res && res.data && res.data.metadata && res.data.metadata.enable_recheck !== undefined) {
              this.enableRecheck = res.data.metadata.enable_recheck;
            }
          },
          (err) => {
            this.showErrorMsg(err);
          }
        );
      });
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
          if (check) {
            val.data.watched = this.checkboxStatus.checked;
          } else {
            val.data.watched = this.checkboxStatus.unchecked;
          }
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
        this.dealDoubleClick(node.data.name, node.expanded);
      }
    },
    /**
     * Function to be executed after the search value changes
     */
    filterChange() {
      if (this.searchWord === '' && this.nodeTypes.value === 'all' && this.searchStackContent === '') {
        if (this.curWatchPointId) {
          this.queryGraphByWatchpoint(this.curWatchPointId);
        }
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
      this.searchWord = this.searchWord.trim();
      this.searchStackContent = this.searchStackContent.trim();
      this.treeFlag = this.searchWord === '' && this.nodeTypes.value === 'all' && this.searchStackContent === '';
      if (this.searchWord || this.nodeTypes.value !== 'all' || this.searchStackContent) {
        this.searchedWord = this.searchWord;
        this.searchedStackContent = this.searchStackContent;
        const params = {
          name: this.searchWord,
          watch_point_id: this.curWatchPointId ? this.curWatchPointId : 0,
          graph_name: this.graphFiles.value,
          rank_id: this.logicCard.value,
          stack_info_key_word: encodeURIComponent(this.searchStackContent),
        };
        if (this.graphFiles.value === this.$t('debugger.all')) {
          delete params.graph_name;
        }
        if (this.nodeTypes.value !== 'all') {
          params.node_category = this.nodeTypes.value;
        }
        const loadingInstance = this.$loading(this.loadingOption);
        RequestService.search(params, this.sessionId).then(
          (res) => {
            loadingInstance.close();
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
            loadingInstance.close();
            this.showErrorMsg(err);
          }
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
    retrieveAll() {
      this.loadingInstance = this.$loading(this.loadingOption);
      const params = {
        mode: 'all',
      };
      RequestService.retrieve(params, this.sessionId).then(
        (res) => {
          this.initFail = false;
          this.dialogVisible = false;
          if (res.data) {
            if (res.data.graph && res.data.graph.nodes) {
              this.origialTree = res.data.graph.nodes.map((val) => {
                return {
                  label: val.name.split('/').pop(),
                  leaf: val.type === 'name_scope' || val.type === 'aggregation_scope' ? false : true,
                  ...val,
                };
              });
              this.resolve(this.origialTree);
              this.dealGraphData(JSON.parse(JSON.stringify(res.data.graph.nodes)));
            } else if (res.data.metadata && res.data.metadata.state === this.state.waiting) {
              if (this.trainId) {
                this.noOfflineGraph = true;
              }
              this.loadingInstance.close();
              this.dialogVisible = true;
              return;
            }
            if (res.data.devices && res.data.devices.length) {
              this.devices = res.data.devices;
              this.logicCard.value = this.devices[0].rank_id;
              this.graphFiles.options = JSON.parse(JSON.stringify(this.devices[0].graph_names));
              if (this.graphFiles.options.length > 1) {
                this.graphFiles.options.unshift(this.$t('debugger.all'));
              }
              this.graphFiles.value = this.graphFiles.options[0];
              if(this.trainId){
                this.getGraphRuns();
              }             
              if (res.data.metadata 
                  && res.data.metadata.state === this.state.waiting 
                  && this.trainId 
                  && !this.graphFiles.value
              ) {
                this.noOfflineGraphName = true;
                this.dialogVisible = true;
                return;
              }
              this.hitWpCondition.graphFile = this.graphFiles.options[0];
              this.logicCard.options = this.devices.map((val) => val.rank_id);
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
              if (!this.trainId) {
                this.metadata.total_step_num = 2147483647;
              }
              if (res && res.data && res.data.metadata && res.data.metadata.enable_recheck !== undefined) {
                this.enableRecheck = res.data.metadata.enable_recheck;
              }
              if (this.metadata.backend) {
                this.version = this.metadata.backend;
              }
              if (!res.data.metadata.recommendation_confirmed && this.metadata.state === this.state.waiting) {
                this.recommendWatchPointDialog = true;
              }

              this.nodeName = this.metadata.node_name;
              this.currentNodeName = this.nodeName;
              if (this.metadata.state === this.state.pending || this.metadata.state === this.state.mismatch) {
                this.loadingInstance.close();
              }
              if (this.pollInit) {
                this.pollData();
                this.pollInit = false;
              }
              if (this.devices && this.devices.length) {
                this.metadata.ip = this.devices[0].server_ip;
                this.metadata.device_name = this.devices[0].device_id;
              }
            }
          }
        },
        (err) => {
          this.initFail = true;
          this.dialogVisible = true;
          this.loadingInstance.close();
          this.showErrorMsg(err);
        }
      );
    },
    /**
     * Draw the tree
     * @param {Object} node tree root node
     * @param {Function} resolve callback function ,return next node data
     */
    loadNode(node, resolve) {
      if (node.level === 0) {
        node.childNodes = [];
        if (!this.node && !this.resolve) {
          this.node = node;
          this.resolve = resolve;
        }
        resolve([]);
      } else if (node.level >= 1) {
        this.loadingInstance = this.$loading(this.loadingOption);
        this.isIntoView = false;
        const curHalfCheckedKeys = this.$refs.tree.getHalfCheckedKeys();
        const params = {
          mode: 'node',
          params: {
            node_type: node.data.type,
            watch_point_id: this.curWatchPointId ? this.curWatchPointId : 0,
            name: node.data.name,
            graph_name: this.graphFiles.value,
            rank_id: this.logicCard.value,
          },
        };
        if (this.graphFiles.value === this.$t('debugger.all')) {
          delete params.params.graph_name;
        }
        RequestService.retrieve(params, this.sessionId).then(
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
              if (this.curNodeData.length > this.nodesCountLimit) {
                this.$message.error(this.$t('graph.tooManyNodes'));
                this.loadingInstance.close();
                node.loading = false;
                return;
              }
              resolve(this.curNodeData);
              // watched 0:unchecked  1:indeterminate 2:checked -1:no checkbox
              this.defaultCheckedArr = this.defaultCheckedArr.concat(
                this.curNodeData
                  .filter((val) => {
                    return val.watched === this.checkboxStatus.checked;
                  })
                  .map((val) => val.name)
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
                if (val.data.watched === this.checkboxStatus.checked) {
                  val.checked = true;
                } else if (val.data.watched === this.checkboxStatus.unchecked) {
                  val.checked = false;
                }
              });
              [...new Set(curHalfCheckedKeys.concat(this.$refs.tree.getHalfCheckedKeys()))].forEach((val) => {
                this.$refs.tree.getNode(val).indeterminate = true;
              });
              this.selectedNode.name = node.data.name;
              if (this.allGraphData[node.data.name] && !this.allGraphData[node.data.name].isUnfold) {
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
          }
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
            rank_id: this.logicCard.value,
          },
        };
        if (this.graphFiles.value === this.$t('debugger.all')) {
          delete params.params.graph_name;
        }
        RequestService.retrieve(params, this.sessionId).then((res) => {
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
                .map((val) => val.name)
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
        requestBody: {
          set_recommended: value,
        },
      };
      RequestService.setRecommendWatchPoints(params, this.sessionId).then((res) => {
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
            this.queryGraphByWatchpoint(val.id);
            if (this.searchWord !== '' || this.nodeTypes.value !== 'all' || this.searchStackContent !== '') {
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
        rank_id: this.logicCard.value,
      };
      if (this.graphFiles.value === this.$t('debugger.all')) {
        delete params.graph_name;
      }
      RequestService.retrieve(params, this.sessionId).then(
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
        }
      );
    },
    /**
     * Tree linkage with graph  Expand of current node
     * @param {Object} nodes Data of children of current node
     * @param {Object} name  The name of the current node
     */
    nodeExpandLinkage(nodes, name) {
      if (nodes.length > this.nodesCountLimit) {
        return;
      }
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
     * @param {Boolean} type  true: search watchpointhits false:query watchpointhits
     * @param {Boolean} resetOffset  true: reset pagination offset
     */
    searchWatchpointHits(type, resetOffset = false) {
      if (this.radio1 === 'hit') {
        const params = {};
        const condition = {
          rank_id: this.logicCard.value,
        };
        if (this.hitWpCondition.graphFile !== this.$t('debugger.all')) {
          condition.graph_id = this.hitWpCondition.graphFile;
        }
        if (this.hitWpCondition.watchPoint !== this.$t('debugger.all')) {
          condition.watchpoint_id = this.hitWpCondition.watchPoint;
        }
        if (type) {
          if (this.selectedNode.name) {
            if (this.graphFiles.value === this.$t('debugger.all')) {
              const arr = this.selectedNode.name.split('/');
              condition.focused_node = {
                node_name: arr[1] ? this.selectedNode.name.replace(`${arr[0]}/`, '') : arr[0],
                graph_name: arr[0],
              };
            } else {
              condition.focused_node = {
                node_name: this.selectedNode.name,
                graph_name: this.graphFiles.value,
              };
            }
          } else {
            condition.offset = this.pagination.currentPage - 1;
          }
        } else {
          condition.offset = this.pagination.currentPage - 1;
        }
        condition.limit = this.pagination.pageSize;
        if (resetOffset) condition.offset = 0;
        params.group_condition = condition;
        RequestService.searchWatchpointHits(params, this.sessionId).then(
          (res) => {
            if (res.data.metadata) {
              this.dealMetadata(res.data.metadata);
            }
            this.hitsOutdated = res.data.outdated;
            if (res.data && res.data.watch_point_hits) {
              this.watchPointHits = [];
              this.pagination.total = res.data.total;
              this.pagination.currentPage = res.data.offset + 1;
              this.dealWatchpointHits(res.data.watch_point_hits);
            } else {
              if (condition.node_name) {
                if (this.watchPointHits.length > 0) {
                  this.watchPointHits.forEach((val) => {
                    val.selected = false;
                  });
                } else {
                  this.searchWatchpointHits(false);
                }
              } else {
                this.pagination.currentPage = 1;
                this.watchPointHits = [];
                this.pagination.total = 0;
              }
            }
          },
          (err) => {
            this.showErrorMsg(err);
          }
        );
      } else if (this.radio1 === 'tree') {
        this.$nextTick(() => {
          setTimeout(() => {
            const dom = document.querySelector('.el-tree-node.is-current.is-focusable');
            if (dom) {
              dom.scrollIntoView();
            }
          }, 200);
        });
      } else if (this.radio1 === 'stack') {
        if (!this.stacks.list.length) {
          this.stacks.currentPage = 1;
          this.queryStacks();
        }
      }
    },
    dealWatchpointHits(data) {
      if (data && data.length) {
        data.forEach((hit) => {
          const obj = {
            name: hit.node_name,
            lists: [],
            selected: false,
            id: hit.node_name,
            graph_name: hit.graph_name,
            rank_id: this.logicCard.value,
          };
          if (hit.tensors && hit.tensors.length) {
            hit.tensors.forEach((i) => {
              const tensorName = `slot: ${i.slot}, `;
              if (i.watch_points && i.watch_points.length) {
                i.watch_points.forEach((j, key) => {
                  let item = `${tensorName}${this.$t('debugger.watchPoint')} ${j.id}, `;
                  let params = [];
                  if (j.watch_condition) {
                    item += ` ${this.transCondition(j.watch_condition.id)}`;
                    this.formateWatchpointParams(j.watch_condition.params || []);
                    params = JSON.parse(JSON.stringify(j.watch_condition.params));
                  }
                  obj.lists.push({
                    name: item,
                    params,
                    id: `${key}${hit.node_name}`,
                    tip:
                      j.error_list && j.error_list.length
                        ? j.error_list
                            .map((i) => {
                              return this.$t('debugger.checkTips')[i];
                            })
                            .join('') + this.$t('debugger.checkTips').cannotCheck
                        : '',
                  });
                });
              }
            });
          }
          this.watchPointHits.push(obj);
        });
        this.focusWatchpointHit();
      } else {
        this.pagination.currentPage = 1;
        this.watchPointHits = [];
        this.pagination.total = 0;
      }
    },
    focusWatchpointHit() {
      if (this.selectedNode.name) {
        let selectedNodeName = this.selectedNode.name;
        if (this.graphFiles.value !== this.$t('debugger.all')) {
          selectedNodeName = `${this.graphFiles.value}/${selectedNodeName}`;
        }
        this.expandKeys = [];
        let focused = false;
        this.watchPointHits.forEach((val) => {
          if (`${val.graph_name}/${val.name}` === selectedNodeName) {
            val.selected = true;
            focused = true;
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
        return focused;
      }
    },
    /**
     * Update tensor value
     * @param {number} key The index of the node of the watchPointHits currently clicked
     */
    updateTensorValue(key) {
      this.loadingInstance = this.$loading(this.loadingOption);
      const currentHit = this.watchPointHits[key];
      const name = currentHit.name;
      const temName = this.nodeName;
      this.nodeName = name;
      this.isHitIntoView = false;
      const params = {
        mode: 'node',
        params: {
          name,
          single_node: true,
          watch_point_id: this.curWatchPointId ? this.curWatchPointId : 0,
          graph_name: currentHit.graph_name,
          rank_id: this.logicCard.value,
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
      RequestService.retrieve(params, this.sessionId).then(
        (res) => {
          if (res.data.metadata) {
            this.dealMetadata(res.data.metadata);
          }
          this.retrieveTensorHistory({ name: this.nodeName }, currentHit.graph_name);
          if (res.data && res.data.graph) {
            const graph = res.data.graph;

            if (this.graphFiles.value !== currentHit.graph_name && this.graphFiles.value !== this.$t('debugger.all')) {
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
        }
      );
    },
    /**
     * Query the graph data
     * @param {String} nodeName The name of the node that needs to be query
     * @param {Boolean} isQueryTensor The name of the node that needs to be query
     * @param {String} graphName Graph file name
     * @param {Boolean} needLoading Whether to display loading
     */
    queryAllTreeData(nodeName, isQueryTensor, graphName, needLoading) {
      if (needLoading) {
        this.loadingInstance = this.$loading(this.loadingOption);
      }
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
      RequestService.retrieve(params, this.sessionId).then(
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
        }
      );
    },
    /**
     * Draw the tree
     * @param {Object} children child node
     * @param {String} name The name of the node that needs to be highlighted
     */
    dealTreeData(children, name) {
      if (children.nodes) {
        if (
          (children.nodes.length > this.nodesCountLimit &&
            this.$refs.tree.getNode(children.scope_name).data.type === 'name_scope') ||
          this.allGraphData[children.scope_name].maxChainNum > this.maxChainNum
        ) {
          return;
        }
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
    stackPageChange(page) {
      this.stacks.currentPage = page;
      this.queryStacks();
    },
    queryStacks() {
      this.stacks.searchContent = this.stacks.searchContent.trim();
      const param = {
        offset: this.stacks.currentPage - 1,
        limit: this.stacks.pageSize.size,
        key_word: encodeURIComponent(this.stacks.searchContent),
      };
      RequestService.queryStackList(param, this.sessionId).then(
        (res) => {
          if (res && res.data && res.data.stack_infos) {
            this.stacks.total = res.data.total;
            this.stacks.currentPage = res.data.offset + 1;
            this.stacks.list = JSON.parse(JSON.stringify(res.data.stack_infos));
          } else {
            this.stacks.currentPage = 1;
            this.stacks.total = 0;
            this.stacks.list = [];
          }
        },
        (error) => {
          this.stacks.currentPage = 1;
          this.stacks.total = 0;
          this.stacks.list = [];
          this.showErrorMsg(error);
        }
      );
    },
    loadTensor(tensor, prev = false) {
      const param = {
        name: tensor.name,
        rank_id: this.logicCard.value,
        graph_name: tensor.graph_name,
        prev: prev + '',
      };
      RequestService.loadTensor(param, this.sessionId).then(
        (res) => {
          if (res && res.data && res.data.node_name) {
            const fileSize = this.fileSizeConversion(tensor.bytes);
            this.$message(this.$t('debugger.downloadTip', { fileSize: fileSize.join('') }));
            this.downloadedTensor.graph_name = tensor.graph_name;
            this.downloadedTensor.prev = prev;

            if (this.downloadedTensor.name === res.data.node_name) {
              this.downloadTensor();
            } else {
              this.downloadedTensor.name = res.data.node_name;
            }
          }
        },
        (err) => {
          this.showErrorMsg(err);
          this.downloadedTensor = {};
        }
      );
    },
    downloadTensor() {
      const url =
        basePath +
        `v1/mindinsight/debugger/sessions/${this.sessionId}/tensor-files/download?` +
        `name=${this.downloadedTensor.name}&rank_id=${this.logicCard.value}&` +
        `graph_name=${this.downloadedTensor.graph_name}&prev=${this.downloadedTensor.prev}`;
      const a = document.createElement('a');
      a.download = '';
      a.href = url;
      a.rel = 'noopener noreferrer';
      a.target = '_blank';
      a.click();
      this.downloadedTensor = {};
    },
    fileSizeConversion(value = 0, unit = 'bytes') {
      const units = ['bytes', 'KB', 'MB', 'GB'];
      let index = units.indexOf(unit);
      if (value < 0 || index === -1) return [value, unit];

      const ratio = 1024;
      while (value >= ratio && index < units.length - 1) {
        value = value / ratio;
        index++;
      }

      value = parseFloat(value.toFixed(2));
      return [value, units[index]];
    },
  },
};
</script>

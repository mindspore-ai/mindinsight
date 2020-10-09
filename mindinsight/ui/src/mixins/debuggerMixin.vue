<script>
import RequestService from '@/services/request-service';
export default {
  methods: {
    toleranceInputChange() {
      this.toleranceInput = this.tolerance;
    },
    toleranceValueChange(val) {
      val = val.replace(/[^0-9]+/g, '');
      if (Number(val) === 0) {
        this.toleranceInput = 0;
        this.tolerance = 0;
      }
      if (Number(val) < 0) {
        this.tolerance = 0;
        this.toleranceInput = 0;
      }
      if (Number(val) > 0) {
        if (Number(val) > 100) {
          this.tolerance = 100;
          this.toleranceInput = 100;
        } else {
          this.tolerance = Number(val);
          this.toleranceInput = Number(val);
        }
      }
    },
    showOrigin() {
      this.watchPointPending = true;
      this.loadOriginalTree();
      this.queryWatchPoints();
    },
    /**
     * Format tolenrance
     * @param {Number} value
     * @return {String}
     */
    formatTolenrance(value) {
      return `${value}%`;
    },
    /**
     * Tabs change
     * @param {String} gridType tab type
     */
    tabChange(gridType) {
      this.gridType = gridType;
      if (this.gridType === 'compare') {
        this.tensorComparisons(this.curRowObj, this.dims);
      } else {
        this.viewValueDetail(this.curRowObj, this.dims);
      }
    },
    /**
     * Query tensor Comparison data
     * @param { Object } row current clickd tensor value data
     * @param { Object } dims dims
     */
    tensorComparisons(row, dims) {
      this.curRowObj = row;
      const shape = dims
        ? dims
        : JSON.stringify(
            JSON.parse(row.shape)
                .map((val, index) => {
                  if (index < 2) {
                    return ':';
                  } else {
                    return 0;
                  }
                })
                .reverse(),
        ).replace(/"/g, '');
      const params = {
        name: row.name,
        detail: 'data',
        shape,
        tolerance: this.tolerance / 100,
      };
      const loadingInstance = this.$loading(this.loadingOption);
      RequestService.tensorComparisons(params).then(
          (res) => {
            loadingInstance.close();
            if (res && res.data && res.data.tensor_value) {
              this.tensorCompareFlag = true;
              this.gridType = 'compare';
              if (row.shape === '[]') {
                this.showFilterInput = false;
              } else {
                this.showFilterInput = true;
              }
              const tensorValue = res.data.tensor_value;
              if (tensorValue.diff === 'Too large to show.') {
                this.tensorValue = [];
                this.$nextTick(() => {
                  this.$refs.tensorValue.showRequestErrorMessage(
                      this.$t('debugger.largeDataTip'),
                      JSON.parse(row.shape),
                      shape,
                      true,
                  );
                });
                return;
              }
              this.tensorValue = tensorValue.diff;
              if (
                this.tensorValue &&
              this.tensorValue instanceof Array &&
              !(this.tensorValue[0] instanceof Array)
              ) {
                this.tensorValue = [this.tensorValue];
              }
              this.$nextTick(() => {
                this.$refs.tensorValue.updateGridData(
                    this.tensorValue,
                    JSON.parse(row.shape),
                    tensorValue.statistics,
                    shape,
                );
              });
            }
          },
          (err) => {
            loadingInstance.close();
          },
      );
    },
    /**
     * Initialize the condition
     */
    initCondition() {
      this.conditionMappings = {
        INF: 'INF',
        NAN: 'NAN',
        OVERFLOW: 'OVERFLOW',
        MAX_GT: 'MAX >',
        MAX_LT: 'MAX <',
        MIN_GT: 'MIN >',
        MIN_LT: 'MIN <',
        MAX_MIN_GT: 'MAX-MIN >',
        MAX_MIN_LT: 'MAX-MIN <',
        MEAN_GT: 'MEAN >',
        MEAN_LT: 'MEAN <',
      };
      this.conditions.noValue = ['INF'];
      this.conditions.hasValue = [
        'MAX_GT',
        'MAX_LT',
        'MIN_GT',
        'MIN_LT',
        'MAX_MIN_GT',
        'MAX_MIN_LT',
        'MEAN_GT',
        'MEAN_LT',
      ];

      if (this.version === 'GPU') {
        this.conditions.noValue.push('NAN');
      } else {
        this.conditions.noValue.push('OVERFLOW');
      }

      this.conditions.options = this.conditions.noValue
          .concat(this.conditions.hasValue)
          .map((i) => {
            return {
              label: this.conditionMappings[i],
              value: i,
            };
          });
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
     * Resize callback function
     */
    resizeCallback() {
      if (this.$refs.tensorValue) {
        this.debounce(this.$refs.tensorValue.resizeView(), 1000);
      }
    },
    /**
     * Anti-shake
     * @param { Function } fn callback function
     * @param { Number } delay delay time
     * @return { Function }
     */
    debounce(fn, delay) {
      let timer = null;
      return function() {
        if (timer) {
          clearTimeout(timer);
        }
        timer = setTimeout(fn, delay);
      };
    },
    /**
     * Step input validation
     */
    stepChange() {
      if (this.step === '') {
        return;
      }
      this.step = this.step
          .toString()
          .replace(/[^\.\d]/g, '')
          .replace(/\./g, '');
      this.step = Number(this.step);
      if (this.step === 0) {
        this.step = 1;
      }
    },
    /**
     * Query current node info
     */
    getCurrentNodeInfo() {
      const params = {
        mode: 'node',
        params: {
          watch_point_id: this.curWatchPointId ? this.curWatchPointId : 0,
          name: this.currentNodeName,
          single_node: true,
          node_type: 'leaf',
        },
      };
      RequestService.retrieve(params).then(
          (res) => {
            if (res.data) {
              if (res.data.metadata) {
                this.dealMetadata(res.data.metadata);
              }
              if (res.data.graph) {
                const graph = res.data.graph;
                if (graph.children) {
                  this.dealTreeData(graph.children, this.currentNodeName);
                  this.defaultCheckedArr = this.$refs.tree.getCheckedKeys();
                }
                this.querySingleNode(
                    JSON.parse(JSON.stringify(res.data.graph)),
                    this.currentNodeName,
                    false,
                );
              }
            }
          },
          (err) => {
            this.showErrorMsg(err);
          },
      );
      this.retrieveTensorHistory({name: this.nodeName});
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
      };
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
        (data &&
          (data.type === 'name_scope' || data.type === 'aggregation_scope')) ||
        this.curLeafNodeName === null
      ) {
        name = this.curLeafNodeName;
      }
      const params = {
        ascend,
        name,
        watch_point_id: this.curWatchPointId ? this.curWatchPointId : 0,
      };
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
              this.querySingleNode(
                  JSON.parse(JSON.stringify(res.data.graph)),
                  res.data.name,
              );
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
      this.$confirm(
          this.$t('debugger.ternimateConfirm'),
          this.$t('public.notice'),
          {
            confirmButtonText: this.$t('public.sure'),
            cancelButtonText: this.$t('public.cancel'),
            type: 'warning',
          },
      ).then(
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
      if (columnIndex === 0 && this.outputLength > 0) {
        if (rowIndex === 0) {
          return {
            rowspan: this.outputLength,
            colspan: 1,
          };
        } else if (rowIndex > 0 && rowIndex < this.outputLength) {
          return {
            rowspan: 0,
            colspan: 0,
          };
        } else if (rowIndex === this.outputLength) {
          return {
            rowspan: this.inputLength,
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
        this.queryAllTreeData(data.name, true);
      }
    },
    /**
     * Query tensor value
     * @param { Object } data node info
     */
    retrieveTensorHistory(data) {
      const params = {
        name: data.name,
      };
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
     * Query tensor value or tensor comparison
     * @param {Object} data tensor value data
     */
    tensorFilterChange(data) {
      this.dims = `[${data.toString()}]`;
      if (this.gridType === 'value') {
        this.viewValueDetail(this.curRowObj, this.dims);
      } else {
        this.tensorComparisons(this.curRowObj, this.dims);
      }
    },
    /**
     * Query tensor value data
     * @param {Object} row current row data
     * @param { String } dims
     */
    viewValueDetail(row, dims) {
      const shape = dims
        ? dims
        : JSON.stringify(
            JSON.parse(row.shape)
                .map((val, index) => {
                  if (index < 2) {
                    return ':';
                  } else {
                    return 0;
                  }
                })
                .reverse(),
        ).replace(/"/g, '');
      const params = {name: row.name, detail: 'data', shape};
      const loadingInstance = this.$loading(this.loadingOption);
      RequestService.tensors(params).then(
          (res) => {
            this.gridType = 'value';
            loadingInstance.close();
            this.curRowObj = JSON.parse(JSON.stringify(row));
            this.tensorCompareFlag = true;
            if (row.shape === '[]') {
              this.showFilterInput = false;
            } else {
              this.showFilterInput = true;
            }
            if (res.data.tensor_value) {
              const value = res.data.tensor_value.value;
              if (value === 'Too large to show.') {
                this.tensorValue = [];
                this.$nextTick(() => {
                  this.$refs.tensorValue.showRequestErrorMessage(
                      this.$t('debugger.largeDataTip'),
                      JSON.parse(row.shape),
                      shape,
                      true,
                  );
                });
                return;
              }
              this.tensorValue = value instanceof Array ? value : [value];
              const status = res.data.tensor_value.statistics || {};
              this.$nextTick(() => {
                this.$refs.tensorValue.updateGridData(
                    this.tensorValue,
                    JSON.parse(row.shape),
                    status,
                    shape,
                );
              });
            }
          },
          (err) => {
            loadingInstance.close();
            this.showErrorMsg(err);
          },
      );
    },
    /**
     * Deal metadata
     * @param {Object} metadata metadata
     * @param {Boolean} isQuery wheather to query tree data
     */
    dealMetadata(metadata) {
      this.metadata.pos = metadata.pos;
      if (metadata.state) {
        this.metadata.state = metadata.state;
      }
      if (metadata.node_name !== undefined && metadata.step !== undefined) {
        const nodeName = metadata.node_name;
        if (
          (nodeName !== this.currentNodeName && nodeName !== '') ||
          this.metadata.step !== metadata.step
        ) {
          this.nodeName = nodeName ? nodeName : this.nodeName;
          this.currentNodeName = nodeName ? nodeName : this.currentNodeName;
          this.metadata.step = metadata.step;
          this.queryAllTreeData(this.nodeName, true);
        }
      }
      if (metadata.step && metadata.step > this.metadata.step) {
        this.metadata.step = metadata.step;
      }
    },
    /**
     * Long polling,update some info
     */
    pollData() {
      const params = {pos: this.metadata.pos};
      RequestService.pollData(params).then(
          (res) => {
            if (res.data) {
              if (res.data.metadata) {
                this.dealMetadata(res.data.metadata);
              }
              if (
                res.data.receive_tensor &&
              res.data.metadata &&
              res.data.metadata.step >= this.metadata.step &&
              res.data.receive_tensor.node_name === this.nodeName
              ) {
                this.retrieveTensorHistory({
                  name: res.data.receive_tensor.node_name,
                });
              }
              if (
                res.data.watch_point_hits &&
              res.data.watch_point_hits.length > 0
              ) {
                this.watchPointHits = res.data.watch_point_hits;
                this.watchPointHits.forEach((val) => {
                  val.selected = false;
                });
                this.radio1 = 'hit';
                this.$nextTick(() => {
                  this.updateTensorValue(0);
                });
              }
              if (
                res.data.tensor_history &&
              this.metadata.step <= res.data.metadata.step
              ) {
                setTimeout(() => {
                  const tableData = res.data.tensor_history;

                  if (this.tableData.length) {
                    this.tableData.forEach((val, key, arr) => {
                      tableData.forEach((value) => {
                        if (val.name === value.name) {
                          val.dtype = value.dtype;
                          val.shape = value.shape;
                          val.step = value.step;
                          val.value = value.value;
                        }
                      });
                    });
                  } else {
                    this.tableData = tableData;
                  }

                  this.dealTableData(this.tableData);
                  this.tableData = JSON.parse(JSON.stringify(this.tableData));
                }, 200);
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
    /**
     * Delete new watchpoint
     * @param {Object} item watchpoint data
     */
    deleteWatchpoint(item) {
      if (item.id) {
        this.$confirm(
            this.$t('debugger.deleteWatchpointConfirm'),
            this.$t('public.notice'),
            {
              confirmButtonText: this.$t('public.sure'),
              cancelButtonText: this.$t('public.cancel'),
              type: 'warning',
            },
        ).then(() => {
          const params = {watch_point_id: item.id};
          RequestService.deleteWatchpoint(params).then(
              (res) => {
                this.loadOriginalTree();
                this.queryWatchPoints();
                this.$message.success(this.$t('debugger.successDeleteWP'));
              },
              (err) => {
                this.showErrorMsg(err);
              },
          );
        });
      } else {
        this.curWatchPointId = null;
        this.watchPointPending = true;
        this.watchPointArr.pop();
      }
    },
    validateParam(item) {
      const reg = /^(\-|\+)?\d+(\.\d+)?$/;
      this.validPram = reg.test(item.param);
    },
    /**
     * Create new watchpoint
     * @param {Object} item watchpoint data
     */
    createWatchPoint(item) {
      if (item.condition) {
        if (item.pending) {
          const params = {
            condition: {
              condition: item.condition,
            },
            watch_nodes: this.$refs.tree.getCheckedKeys(),
          };
          if (this.conditions.hasValue.includes(item.condition)) {
            params.condition.param = parseFloat(item.param);
          }
          RequestService.createWatchpoint(params).then(
              (res) => {
                this.loadOriginalTree();
                this.queryWatchPoints();
                this.watchPointPending = true;
                this.$message.success(this.$t('debugger.successCreateWP'));
              },
              (err) => {
                this.loadOriginalTree();
                this.queryWatchPoints();
                this.watchPointPending = true;
                this.showErrorMsg(err);
              },
          );
        } else {
        }
      }
    },
    /**
     * Condition change processing
     * @param {Object} item
     */
    conditionChange(item) {
      item.label = this.conditionMappings[item.condition];
      if (this.conditions.noValue.includes(item.condition)) {
        item.param = '';
        this.validPram = false;
      }
    },
    /** Draw the tree
     * @param {Object} obj current checked obj
     */
    check(obj) {
      const node = this.$refs.tree.getNode(obj.name);
      const check = node.checked;
      if (this.treeFlag && node.childNodes) {
        this.dealCheckPro(node.childNodes, check);
      }
      if (this.curWatchPointId !== null && this.curWatchPointId !== '') {
        const checkedKeys = this.$refs.tree.getCheckedKeys();
        const watchNodes = [];
        if (this.defaultCheckedArr.length > checkedKeys.length) {
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
          mode: check ? 1 : 0,
        };
        if (this.searchWord !== '') {
          params.name = this.searchWord;
          params.watch_nodes = [obj.name];
          params.mode = check ? 1 : 0;
        }
        RequestService.updateWatchpoint(params).then(
            (res) => {
              this.defaultCheckedArr = checkedKeys;
            },
            (err) => {
              this.showErrorMsg(err);
            },
        );
      }
    },
    /** Deal tree data
     * @param {Object} childNodes tree node
     * @param { Boolean } check check status
     */
    dealCheckPro(childNodes, check) {
      childNodes.forEach((val) => {
        val.checked = check;
        if (val.childNodes) {
          this.dealCheckPro(val.childNodes, check);
        }
      });
    },
    /**
     * Add watchpoint
     */
    addWatchPoint() {
      this.searchWord = '';
      this.treeFlag = true;
      if (this.watchPointPending) {
        this.watchPointPending = false;
        this.loadOriginalTree();
        this.$refs.tree.getCheckedKeys().forEach((val) => {
          this.$refs.tree.setChecked(val, false);
        });
        this.defaultCheckedArr = [];
        this.watchPointArr.forEach((val) => {
          val.selected = false;
        });
        this.watchPointArr.push({
          selected: true,
          id: '',
          condition: '',
          label: '',
          param: '',
          pending: true,
        });
      }
      this.curWatchPointId = '';
    },
    /**
     * Collapse node
     * @param {Object} _
     * @param {Object} node node data
     */
    nodeCollapse(_, node) {
      node.loaded = false;
      if (this.treeFlag) {
        this.dealDoubleClick(node.data.name);
      }
    },
    /**
     * Function to be executed after the search value changes
     */
    filterChange() {
      if (this.searchWord === '') {
        this.treeFlag = true;
        this.queryGraphByWatchpoint(this.curWatchPointId);
      }
    },
    /**
     * Filter tree data by node name
     */
    filter() {
      if (this.searchWord) {
        const params = {
          name: this.searchWord,
          watch_point_id: this.curWatchPointId ? this.curWatchPointId : 0,
        };
        RequestService.search(params).then(
            (res) => {
              if (res.data && res.data.nodes) {
                this.treeFlag = false;
                this.searchTreeData = res.data.nodes;
                this.searchCheckedArr = [];
                this.dealSearchResult(this.searchTreeData);
                this.defaultCheckedArr = this.searchCheckedArr;
              }
            },
            (err) => {
              this.showErrorMsg(err);
            },
        );
      }
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
        if (val.watched === 2) {
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
                  this.origialTree = res.data.graph.nodes.map((val) => {
                    return {
                      label: val.name.split('/').pop(),
                      leaf:
                      val.type === 'name_scope' ||
                      val.type === 'aggregation_scope'
                        ? false
                        : true,
                      ...val,
                    };
                  });
                  resolve(JSON.parse(JSON.stringify(this.origialTree)));
                  this.$refs.tree.getCheckedKeys().forEach((val) => {
                    this.$refs.tree.setChecked(val, false);
                  });
                  if (this.treeFlag) {
                    this.dealGraphData(
                        JSON.parse(JSON.stringify(res.data.graph.nodes)),
                    );
                  }
                }
                if (res.data.watch_points) {
                  this.watchPointArr = res.data.watch_points.map((val) => {
                    return {
                      ...val,
                      selected: false,
                      condition: val.watch_condition.condition,
                      label: this.conditionMappings[
                          val.watch_condition.condition
                      ],
                      param:
                      val.watch_condition.param ||
                      (val.watch_condition.param === 0 ? 0 : ''),
                    };
                  });
                }
                if (res.data.metadata) {
                  this.metadata = res.data.metadata;
                  if (this.metadata.backend) {
                    this.version = this.metadata.backend;
                  }
                  this.initCondition();
                  this.nodeName = this.metadata.node_name;
                  this.currentNodeName = this.metadata.node_name;
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
          },
        };
        RequestService.retrieve(params).then(
            (res) => {
              if (res.data && res.data.metadata) {
                this.dealMetadata(res.data.metadata);
              }
              if (res.data && res.data.graph && res.data.graph.nodes) {
                this.curNodeData = res.data.graph.nodes.map((val) => {
                  return {
                    label: val.name.split('/').pop(),
                    leaf:
                    val.type === 'name_scope' ||
                    val.type === 'aggregation_scope'
                      ? false
                      : true,
                    ...val,
                  };
                });
                resolve(this.curNodeData);
                this.defaultCheckedArr = this.defaultCheckedArr.concat(
                    this.curNodeData
                        .filter((val) => {
                          return val.watched === 2;
                        })
                        .map((val) => val.name),
                );
                const halfSelectArr = this.curNodeData
                    .filter((val) => {
                      return val.watched === 1;
                    })
                    .map((val) => val.name);
                node.childNodes.forEach((val) => {
                  if (halfSelectArr.indexOf(val.data.name) !== -1) {
                    val.indeterminate = true;
                    node.indeterminate = true;
                    [
                      ...new Set(
                          curHalfCheckedKeys.concat(
                              this.$refs.tree.getHalfCheckedKeys(),
                          ),
                      ),
                    ].forEach((val) => {
                      this.$refs.tree.getNode(val).indeterminate = true;
                    });
                  }
                });
                this.selectedNode.name = node.data.name;
                if (!this.allGraphData[node.data.name].isUnfold) {
                  this.dealGraphData(
                      JSON.parse(JSON.stringify(res.data.graph.nodes)),
                      node.data.name,
                  );
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
     * Show data of current selected watchpoint
     * @param {Number} key watchpoint id
     */
    selectWatchPoint(key) {
      if (!this.watchPointPending) {
        return;
      }
      this.curLeafNodeName = null;
      this.curHalfCheckedKeys = [];
      this.watchPointArr.forEach((val, index) => {
        if (index === key) {
          if (val.id) {
            val.selected = true;
            this.curWatchPointId = val.id;
            if (this.searchWord === '') {
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
     */
    queryWatchPoints() {
      const params = {
        mode: 'watchpoint',
      };
      RequestService.retrieve(params).then(
          (res) => {
            if (res.data.watch_points) {
              this.watchPointArr = res.data.watch_points.map((val) => {
                return {
                  ...val,
                  selected: false,
                  condition: val.watch_condition.condition,
                  label: this.conditionMappings[val.watch_condition.condition],
                  param:
                  val.watch_condition.param ||
                  (val.watch_condition.param === 0 ? 0 : ''),
                };
              });
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
        };
      });
      const node = this.$refs.tree.getNode(name);
      curNodeData.forEach((val) => {
        this.$refs.tree.append(val, name);
      });
      node.childNodes.forEach((val) => {
        if (node.checked) {
          val.checked = true;
        }
        if (val.data.watched === 2) {
          val.checked = true;
        }
        if (val.data.watched === 1) {
          val.indeterminate = true;
        }
        if (
          val.data.type !== 'name_scope' &&
          val.data.type !== 'aggregation_scope'
        ) {
          val.isLeaf = true;
        }
      });
      node.expanded = true;
      node.loading = false;
      this.$refs.tree.setCurrentKey(name);
      this.$nextTick(() => {
        setTimeout(() => {
          const dom = document.querySelector(
              '.el-tree-node.is-current.is-focusable',
          );
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
        };
        RequestService.retrieve(params).then(
            (res) => {
              if (res.data.metadata) {
                this.dealMetadata(res.data.metadata);
              }
              if (res.data && res.data.watch_point_hits) {
                this.watchPointHits = res.data.watch_point_hits;
                this.watchPointHits.forEach((val) => {
                  val.selected = false;
                });
                this.$nextTick(() => {
                  if (this.watchPointHits.length > 0) {
                    this.updateTensorValue(0);
                  }
                });
              }
            },
            (err) => {
              this.showErrorMsg(err);
            },
        );
      }
    },
    /**
     * Update tensor value
     * @param {number} key The index of the node of the watchPointHits currently clicked
     */
    updateTensorValue(key) {
      const name = this.watchPointHits[key].node_name;
      const temName = this.nodeName;
      this.nodeName = name;
      const params = {
        mode: 'watchpoint_hit',
        params: {
          name,
          single_node: true,
          watch_point_id: this.curWatchPointId ? this.curWatchPointId : 0,
        },
      };
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
            this.retrieveTensorHistory({name: this.nodeName});
            if (res.data && res.data.graph) {
              const graph = res.data.graph;
              if (graph.children) {
                this.dealTreeData(graph.children, name);
                this.defaultCheckedArr = this.$refs.tree.getCheckedKeys();
              }
              this.querySingleNode(
                  JSON.parse(JSON.stringify(res.data.graph)),
                  name,
                  false,
              );
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
     */
    queryAllTreeData(nodeName, isQueryTensor) {
      const name = nodeName ? nodeName.split(':')[0] : '';
      const params = {
        mode: 'node',
        params: {
          name,
          single_node: true,
          watch_point_id: this.curWatchPointId ? this.curWatchPointId : 0,
        },
      };
      RequestService.retrieve(params).then(
          (res) => {
            if (res.data && res.data.metadata) {
              this.dealMetadata(res.data.metadata);
            }
            if (res.data && res.data.graph) {
              const graph = res.data.graph;
              if (graph.children) {
                this.dealTreeData(graph.children, name);
                this.defaultCheckedArr = this.$refs.tree.getCheckedKeys();
              }
              this.querySingleNode(
                  JSON.parse(JSON.stringify(res.data.graph)),
                  name,
                  isQueryTensor,
              );
            }
            if (res.data && res.data.tensor_history) {
              this.tableData = res.data.tensor_history;
              this.dealTableData(this.tableData);
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
          };
        });
        data.forEach((val) => {
          const node = this.$refs.tree.getNode(children.scope_name);
          if (node.childNodes) {
            if (
              node.childNodes
                  .map((value) => value.data.name)
                  .indexOf(val.name) === -1
            ) {
              this.$refs.tree.append(val, node);
            }
          } else {
            this.$refs.tree.append(val, node);
          }
        });
        const node = this.$refs.tree.getNode(children.scope_name);
        node.childNodes.forEach((val) => {
          if (val.data.watched === 2) {
            val.checked = true;
          }
          if (val.data.watched === 1) {
            val.indeterminate = true;
          }
          if (
            val.data.type !== 'name_scope' &&
            val.data.type !== 'aggregation_scope'
          ) {
            val.isLeaf = true;
          }
        });
        node.expanded = true;
        node.loading = false;
      } else {
        this.$refs.tree.setCurrentKey(name);
        this.$nextTick(() => {
          setTimeout(() => {
            const dom = document.querySelector(
                '.el-tree-node.is-current.is-focusable',
            );
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
  },
};
</script>

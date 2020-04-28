## MindInsight

# Release 0.2.0-alpha

## Major Features and Improvements
* Parameter distribution graph (Histogram).
Now you can use [`HistogramSummary`](https://www.mindspore.cn/api/zh-CN/master/api/python/mindspore/mindspore.ops.operations.html#mindspore.ops.operations.HistogramSummary) and MindInsight to record and visualize distribution info of tensors. See our [tutorial](https://www.mindspore.cn/tutorial/zh-CN/master/advanced_use/visualization_tutorials.html) for details.
* Lineage support Custom information
* GPU support
* Model and dataset tracking linkage support

## Bugfixes 
* Fix graph bug when node name is empty.([#I1EQ5H](https://gitee.com/mindspore/mindinsight/issues/I1EQ5H?from=project-issue))
* Fix sha256 checksum missing bug.([#I1EHVK](https://gitee.com/mindspore/mindinsight/issues/I1EHVK?from=project-issue))
* Fix start/stop command exit-code incorrect.([#I1EY3F](https://gitee.com/mindspore/mindinsight/issues/I1EY3F?from=project-issue))
* Reduce cyclomatic complexity of list_summary_directories.
([#I1DANB](https://gitee.com/mindspore/mindinsight/issues/I1DANB?from=project-issue))
* Fix unsafe functions and duplication files and redundant codes.([#I1DDGF]https://gitee.com/mindspore/mindinsight/issues/I1DDGF?from=project-issue))

## Thanks to our Contributors
Thanks goes to these wonderful people:

Ye Huang, Weifeng Huang, Zhenzhong Kou, Pengting Luo, Hongzhang Li, Yongxiong Liang, Gongchang Ou, Hui Pan, Luyu Qiu, Junyan Qin, Kai Wen, Weining Wang, Yifan Xia, Yunshu Zhang, Ting Zhao

Contributions of any kind are welcome!

# Release 0.1.0-alpha

* Training process observation
   * Provides and displays training process information, including computational graphs and training process indicators.

* Training result tracing
   * Provides functions of tracing and visualizing model training parameter information, including filtering and sorting of training data, model accuracy and training hyperparameters.

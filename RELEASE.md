## MindInsight

# Release 0.2.0-alpha

## Major Features and Improvements
* Parameter distribution graph (Histogram).
Now you can use [`HistogramSummary`](https://www.mindspore.cn/api/zh-CN/master/api/python/mindspore/mindspore.ops.operations.html#mindspore.ops.operations.HistogramSummary) and MindInsight to record and visualize distribution info of tensors. See our [tutorial](https://www.mindspore.cn/tutorial/zh-CN/master/advanced_use/visualization_tutorials.html) for details.
* Lineage support Custom information
* GPU support
* Model and dataset tracking linkage support

## Bugfixes 
* Reduce cyclomatic complexity of `list_summary_directories` ([!11](https://gitee.com/mindspore/mindinsight/pulls/11)).
* Fix unsafe functions and duplication files and redundant codes ([!14](https://gitee.com/mindspore/mindinsight/pulls/14)).
* Fix sha256 checksum missing bug ([!24](https://gitee.com/mindspore/mindinsight/pulls/24)).
* Fix graph bug when node name is empty ([!34](https://gitee.com/mindspore/mindinsight/pulls/34)).
* Fix start/stop command exit-code incorrect ([!44](https://gitee.com/mindspore/mindinsight/pulls/44)).

## Thanks to our Contributors
Thanks goes to these wonderful people:

Ye Huang, Weifeng Huang, Zhenzhong Kou, Pengting Luo, Hongzhang Li, Yongxiong Liang, Gongchang Ou, Hui Pan, Luyu Qiu, Junyan Qin, Kai Wen, Weining Wang, Yifan Xia, Yunshu Zhang, Ting Zhao

Contributions of any kind are welcome!

# Release 0.1.0-alpha

* Training process observation
   * Provides and displays training process information, including computational graphs and training process indicators.

* Training result tracing
   * Provides functions of tracing and visualizing model training parameter information, including filtering and sorting of training data, model accuracy and training hyperparameters.

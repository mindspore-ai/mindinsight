## MindInsight

# Release 0.3.0-alpha

## Major Features and Improvements
* Profiling
    * Provide easy to use apis for profiling start/stop and profiling data analyse (on Ascend only).
    * Provide operators performance display and analysis on MindInsight UI.
* Large scale network computation graph visualization.
* Optimize summary record implementation and improve its performance.
* Improve lineage usability
    * Optimize lineage display and enrich tabular operation.
    * Decouple lineage callback from `SummaryRecord`.
* Support scalar compare of multiple runs.
* Scripts conversion from other frameworks
    * Support for converting PyTorch scripts within TorchVision to MindSpore scripts automatically.
    
## Bugfixes
* Fix pb files loaded problem when files are modified at the same time ([!53](https://gitee.com/mindspore/mindinsight/pulls/53)).
* Fix load data thread stuck in `LineageCacheItemUpdater` ([!114](https://gitee.com/mindspore/mindinsight/pulls/114)).
* Fix samples from previous steps erased due to tags size too large problem ([!86](https://gitee.com/mindspore/mindinsight/pulls/86)).
* Fix image and histogram event package error ([!1143](https://gitee.com/mindspore/mindspore/pulls/1143)).
* Equally distribute histogram ignoring actual step number to avoid large white space ([!66](https://gitee.com/mindspore/mindinsight/pulls/66)).

## Thanks to our Contributors
Thanks goes to these wonderful people:

Chao Chen, Congli Gao, Ye Huang, Weifeng Huang, Zhenzhong Kou, Hongzhang Li, Longfei Li, Yongxiong Liang, Pengting Luo, Yanming Miao, Gongchang Ou, Yongxiu Qu, Hui Pan, Luyu Qiu, Junyan Qin, Kai Wen, Weining Wang, Yue Wang, Zhuanke Wu, Yifan Xia, Weibiao Yu, Ximiao Yu, Ting Zhao, Jianfeng Zhu.

Contributions of any kind are welcome!

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
* Fix start/stop command error code incorrect ([!44](https://gitee.com/mindspore/mindinsight/pulls/44)).

## Thanks to our Contributors
Thanks goes to these wonderful people:

Ye Huang, Weifeng Huang, Zhenzhong Kou, Pengting Luo, Hongzhang Li, Yongxiong Liang, Gongchang Ou, Hui Pan, Luyu Qiu, Junyan Qin, Kai Wen, Weining Wang, Yifan Xia, Yunshu Zhang, Ting Zhao

Contributions of any kind are welcome!

# Release 0.1.0-alpha

* Training process observation
   * Provides and displays training process information, including computational graphs and training process indicators.

* Training result tracing
   * Provides functions of tracing and visualizing model training parameter information, including filtering and sorting of training data, model accuracy and training hyperparameters.

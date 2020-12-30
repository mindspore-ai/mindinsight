# MindInsight 1.1.0 Release Notes

## Major Features and Improvements

### Precision tuning framework

* Support useful checks on weights, activations, gradients and tensors, such as:
    * check unchanged weight
    * check weight change above threshold
    * check activation range
    * check gradient vanishing
    * check tensor overflow
* Support rechecking with new watch points on the same data.
* Newly designed tensor view with fix suggestions and tensor context to quickly locate root cause of problems.
* Support recommending watch points to find common precision problems.
* Support debugger on multigraph network.

### Profiler

* Support GPU step trace profiling.
* Support GPU minddata profiling.

### MindConverter

* Support TensorFlow model definition script to MindSpore for CV field.
* Conversion capability of PyTorch is enhanced.

### Model Explanation

Provide explanations and their benchmarks for image classification deep CNN models.

* Support 6 explanation methods: Gradient, Deconvolution, GuidedBackprop, GradCAM, RISE, Occlusion
* Support 4 benchmark methods: Localization, Faithfulness, Class Sensitivity, Robustness
* Provide a high-level API (ImageClassificationRunner) for users to execute explanation methods and benchmark methods and store the results easily.

## API Change

### Improvements

#### Command Line Interface

* `--enable_debugger`: Support both 1 and True ([!1051](https://gitee.com/mindspore/mindinsight/pulls/1051))
* `ENABLE_MS_DEBUGGER`: Support both 1 and True ([!10199](https://gitee.com/mindspore/mindspore/pulls/10199))
* `parse_summary`: Add parse_summary function to convert summary file to image file and csv file ([!774](https://gitee.com/mindspore/mindinsight/pulls/774))

## Bugfixes

### Profiler

* Fix paser framework file error if the profiling data of one op is saved separately to two files.([!7824](https://gitee.com/mindspore/mindspore/pulls/7824))

### Model Explanation

* Add reset_offset when CRCLengthError and CRCError happen([!955](https://gitee.com/mindspore/mindinsight/pulls/955))
* FIx the bug which ignore the sample_event when sample_id == 0.([!968](https://gitee.com/mindspore/mindinsight/pulls/968))

## Thanks to our Contributors

Thanks goes to these wonderful people:

Congli Gao, Jianfeng Zhu, Zhenzhong Kou, Longfei Li, Yongxiong Liang, Chongming Liu, Pengting Luo, Yanming Miao, Gongchang Ou, Yongxiu Qu, Luyu Qiu, Kai Wen, Yue Wang, Lihua Ye, Ximiao Yu, Yunshu Zhang, Ning Ma, Yihui Zhang, Shuide Wang, Hong Sheng, Ran Mo, Zhaohong Guo, Hui Pan, Weining Wang, Weifeng Huang, Yifan Xia, Chen Cao, Ngaifai Ng, Xiaohui Li, Yi Yang, Luyu Qiu, Yunpeng Wang, Yuhan Shi, Yanxi Wei.

Contributions of any kind are welcome!

# MindInsight 1.0.0 Release Notes

## Major Features and Improvements

* Release MindSpore Debugger.
* MindConverter ability is enhanced, supporting scripts generation based on PyTorch model.
* Support training hyper-parameter importance visualization.
* Support GPU timeline.

## Bugfixes

* Optimize aicpu display method. ([!595](https://gitee.com/mindspore/mindinsight/pulls/595/files))
* Add the summary loading switch mechanism. ([!601](https://gitee.com/mindspore/mindinsight/pulls/601/files))
* Detect a summary dir having summary files or not. ([!632](https://gitee.com/mindspore/mindinsight/pulls/632/files))

## Thanks to our Contributors

Thanks goes to these wonderful people:

Congli Gao, Jianfeng Zhu, Zhenzhong Kou, Hongzhang Li, Longfei Li, Yongxiong Liang, Chongming Liu, Pengting Luo, Yanming Miao, Gongchang Ou, Yongxiu Qu, Luyu Qiu, Kai Wen, Yue Wang, Lihua Ye, Ximiao Yu, Yunshu Zhang, Ning Ma, Yihui Zhang, Shuide Wang, Hong Sheng, Ran Mo, Zhaohong Guo, Hui Pan, Junyan Qin, Weining Wang, Weifeng Huang, Yifan Xia.

Contributions of any kind are welcome!

# MindInsight 0.7.0-beta Release Notes

## Major Features and Improvements

* Optimize node name display in computation graph.
* MindSpore Profiler supports network training with GPU operators.
* MindWizard generates classic network scripts according to user preference.
* Web UI supports language internationalization, including both Chinese and English.

## Bugfixes

* Optimize UI page initialization to handle timeout requests. ([!503](https://gitee.com/mindspore/mindinsight/pulls/503))
* Fix the line break problem when the profiling file number is too long. ([!532](https://gitee.com/mindspore/mindinsight/pulls/532))

## Thanks to our Contributors

Thanks goes to these wonderful people:

Congli Gao, Weifeng Huang, Zhenzhong Kou, Hongzhang Li, Longfei Li, Yongxiong Liang, Chongming Liu, Pengting Luo, Yanming Miao, Gongchang Ou, Yongxiu Qu, Hui Pan, Luyu Qiu, Junyan Qin, Kai Wen, Weining Wang, Yue Wang, Zhuanke Wu, Yifan Xia, Lihua Ye, Weibiao Yu, Ximiao Yu, Yunshu Zhang, Ting Zhao, Jianfeng Zhu, Ning Ma, Yihui Zhang, Shuide Wang, Hong Sheng, Lin Pan, Ran Mo.

Contributions of any kind are welcome!

# MindInsight 0.6.0-beta Release Notes

## Major Features and Improvements

* Provide monitoring capabilities for each of Ascend AI processor and other hardware resources, including CPU and memory.
* Visualization of weight, gradient and other tensor data in model training.
    * Provide tabular from presentation of tensor data.
    * Provide histogram to show the distribution of tensor data and its change over time.

## Bugfixes

* UI fix for the error message display mode of the tensor during real-time training. ([!465](https://gitee.com/mindspore/mindinsight/pulls/465))
* The summary file size is larger than max_file_size. ([!3481](https://gitee.com/mindspore/dashboard/projects/mindspore/mindspore/pulls/3481))
* Fix real-time training error when disk is full. ([!3058](https://gitee.com/mindspore/mindspore/pulls/3058))

## Thanks to our Contributors

Thanks goes to these wonderful people:

Congli Gao, Weifeng Huang, Zhenzhong Kou, Hongzhang Li, Longfei Li, Yongxiong Liang, Chongming Liu, Pengting Luo, Yanming Miao, Gongchang Ou, Yongxiu Qu, Hui Pan, Luyu Qiu, Junyan Qin, Kai Wen, Weining Wang, Yue Wang, Zhuanke Wu, Yifan Xia, Lihua Ye, Weibiao Yu, Ximiao Yu, Yunshu Zhang, Ting Zhao, Jianfeng Zhu, Ning Ma, Yihui Zhang, Shuide Wang.

Contributions of any kind are welcome!

# MindInsight 0.5.0-beta Release Notes

## Major Features and Improvements

* MindSpore Profiler
    * Provide performance analyse tool for the input data pipeline.
    * Provide timeline analyse tool, which can show the detail of the streams/tasks.
    * Provide a tool to visualize the step trace information, which can be used to analyse the general performance of the neural network in each phase.
    * Provide profiling guides for the users to find the performance bottlenecks quickly.
* CPU summary operations support for CPU summary data.
* Over threshold warn support in scalar training dashboard.
* Provide more user-friendly callback function for visualization
    * Provide unified callback `SummaryCollector` to log most commonly visualization event.
    * Discard the original visualization callback `SummaryStep`, `TrainLineage` and `EvalLineage`.
    * `SummaryRecord` provide new API `add_value` to collect data into cache for summary persistence.
    * `SummaryRecord` provide new API `set_mode` to distinguish summary persistence mode at different stages.  
* MindConverter supports conversion of more operators and networks, and improves its ease of use.

## Bugfixes

* Fix FileNotFound exception by adding robust check for summary watcher ([!281](https://gitee.com/mindspore/mindinsight/pulls/281)).
* UI fix operator table sort jump problem ([!283](https://gitee.com/mindspore/mindinsight/pulls/283)).
* Dataset serializer return schema json str when schema type is `mindspore.dataset.engine.Schema` ([!2185](https://gitee.com/mindspore/mindspore/pulls/2185)).

## Thanks to our Contributors

Thanks goes to these wonderful people:

Chao Chen, Congli Gao, Ye Huang, Weifeng Huang, Zhenzhong Kou, Hongzhang Li, Longfei Li, Yongxiong Liang, Chongming Liu, Pengting Luo, Yanming Miao, Gongchang Ou, Yongxiu Qu, Hui Pan, Luyu Qiu, Junyan Qin, Kai Wen, Weining Wang, Yue Wang, Zhuanke Wu, Yifan Xia, Lihua Ye, Weibiao Yu, Ximiao Yu, Yunshu Zhang, Ting Zhao, Jianfeng Zhu.

Contributions of any kind are welcome!

# MindInsight 0.3.0-alpha Release Notes

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

# MindInsight 0.2.0-alpha Release Notes

## Major Features and Improvements

* Parameter distribution graph (Histogram).

    Now you can use [`HistogramSummary`](https://www.mindspore.cn/doc/api_python/en/master/mindspore/mindspore.ops.html#mindspore.ops.HistogramSummary) and MindInsight to record and visualize distribution info of tensors. See our [tutorial](https://www.mindspore.cn/tutorial/training/en/master/advanced_use/visualization_tutorials.html).

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

# MindInsight 0.1.0-alpha Release Notes

* Training process observation
    * Provides and displays training process information, including computational graphs and training process indicators.

* Training result tracing
    * Provides functions of tracing and visualizing model training parameter information, including filtering and sorting of training data, model accuracy and training hyperparameters.

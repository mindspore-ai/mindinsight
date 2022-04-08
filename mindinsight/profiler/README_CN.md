# Profiler 介绍

[View English](./README.md)

## 概述

MindSpore Profiler是为用户进行模型开发提供的分析工具，可以更直观地展现网络模型各维度的性能信息，为用户提供易用、丰富的性能分析功能，帮助用户快速定位网络中性能问题。

Profiler目前支持Ascend、GPU和集群的图模式以及Ascend的Pynative模式。用户可以通过Profiler分析以下数据：

- 训练性能
    - 迭代轨迹
    - 算子性能
    - 计算量
    - 数据准备性能
    - Timeline
- 资源利用
    - CPU利用率
    - 内存使用情况
- 策略感知
    - 计算图探索
    - 算子策略矩阵
    - 流水线并行视图
    - 算子堆叠与边隐藏

> 在不同模式不同环境下，Profiler支持展示的数据并不一致。具体详情参考官方文档。

## 操作流程

- 准备训练脚本，并在训练脚本中调用性能调试接口，接着运行训练脚本。
- 启动MindInsight，并通过启动参数指定summary-base-dir目录(summary-base-dir是Profiler所创建目录的父目录)，例如训练时Profiler创建的文件夹绝对路径为`/home/user/code/data`，则summary-base-dir设为`/home/user/code`。启动成功后，根据IP和端口访问可视化界面，默认访问地址为 `http://127.0.0.1:8080`。
- 在训练列表找到对应训练，点击性能分析，即可在页面中查看训练性能数据。

## 使用详情

MindSpore Profiler的使用详情，请参考<https://www.mindspore.cn/mindinsight/docs/zh-CN/master/performance_profiling.html>。
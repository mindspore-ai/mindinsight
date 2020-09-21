# Debugger 介绍

[View English](./README.md)

## Debugger概述

MindSpore Debugger是为图模式训练提供的调试工具，可以用来查看并分析计算图节点的中间结果。

在MindSpore图模式的训练过程中，用户无法从Python层获取到计算图中间节点的结果，使得训练调试变得很困难。使用MindSpore Debugger，用户可以：

- 在MindInsight UI结合计算图，查看图节点的输出结果；
- 设置条件断点，监测训练异常情况（比如Nan/Inf），在异常发生时追踪错误原因；
- 查看权重等参数的变化情况。

## 操作流程

- 以Debugger模式启动MindInsight，配置相关环境变量;
- 训练开始，在MindInsight Debugger UI设置条件断点，监测节点的输出值；
- 在MindInsight Debugger UI分析训练执行情况。

## Debugger使用方法

MindSpore Debugger的使用方法，请参考<https://www.mindspore.cn/tutorial/training/zh-CN/master/advanced_use/debugger.html>。
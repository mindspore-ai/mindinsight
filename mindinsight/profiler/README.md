# Profiler Introduction

[查看中文](./README_CN.md)

## Overview

MindSpore Profiler is a analyzing tool for users to develop models. It can more intuitively display the performance information of various dimensions of the network model, and provide users with easy-to-use and rich performance analysis functions to help users quickly locate performance problems in the network.

Profiler currently supports Graph mode for Ascend, GPU and Cluster and PyNative mode for Ascend. Users can analyze the following data through Profiler:

- Training Performance
    - Step Trace
    - Operator Performance
    - Calculation Quantity
    - Data Preparation Performance
    - Timeline
- Resource Utilization
    - CPU Utilization
    - Memory Analysis
- Strategy Perception
    - Graph Exploration Module
    - Operator Strategy Matrix
    - Training Pipeline
    - Operator Stacking and Edge Hiding

> In different modes and different environments, the data displayed by Profiler is inconsistent. For details, refer to the official documentation.

## Operation Process

- Prepare a training script, add profiler APIs in the training script
  and run the training script.
- Start MindInsight and specify the summary-base-dir using startup
  parameters, note that summary-base-dir is the parent directory of the
  directory created by Profiler. For example, the directory created by
  Profiler is ``/home/user/code/data/``, the summary-base-dir should be
  ``/home/user/code``. After MindInsight is started, access the
  visualization page based on the IP address and port number. The
  default access IP address is ``http://127.0.0.1:8080``.
- Find the training in the list, click the performance profiling link
  and view the data on the web page.

## Usage Details

For the usage details of MindSpore Profiler, please refer to <https://www.mindspore.cn/mindinsight/docs/zh-CN/master/performance_profiling.html>.

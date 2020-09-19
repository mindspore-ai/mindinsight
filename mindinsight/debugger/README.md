# Debugger Introduction

[查看中文](./README_CN.md)

## Overview

MindSpore Debugger is a debugging tool for training in `Graph Mode`. It can be applied to visualize and analyze the intermediate computation results of the computational graph.

In `Graph Mode` training, the computation results of intermediate nodes in the computational graph can not be acquired from python layer, which makes it difficult for users to do the debugging. By applying MindSpore Debugger, users can:

- Visualize the computational graph on the UI and analyze the output of the graph node;
- Set conditional breakpoint to monitor training exceptions (such as Nan/Inf), if the condition (Nan/Inf etc.) is met, users can track the cause of the bug when an exception occurs;
- Visualize and analyze the change of parameters, such as weights.   

## Operation Process

- Launch MindInsight in debugger mode, and set Debugger environment variables for the training;
- At the beginning of the training, set conditional breakpoints to monitor the outputs of the graph nodes;
- Analyze the training progress on MindInsight Debugger UI. 

## Debugger Instructions

For the details of how to use MindSpore Debugger, please refer to <https://www.mindspore.cn/tutorial/training/en/master/advanced_use/debugger.html>.

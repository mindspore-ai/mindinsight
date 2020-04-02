# Introduction













MindInsight provides MindSpore with easy-to-use debugging and tuning capabilities. It 
enables users to visualize the experiments. The features of MindInsight are as follows.

- Visualization of training process: 

    Provide visualization of training process information, 
such as computation graph, training process metrics, etc.

- Traceability of training result: 

    Provide visualization of model parameters information, 
such as training data, model accuracy, etc.


# Index

- [More about MindInsight](#more-about-mindinsight)
- [Installation](#installation)
- [QuickStart](#quickstart)
- [Docs](#docs)
- [Community](#community)
- [Contributing](#contributing)
- [Release Notes](#release-notes)
- [License](#license)

# More about MindInsight

The architecture diagram of MindInsight is illustrated as follows:


![MindInsight Architecture](docs/arch.png)


## Summary log file

The summary log file consists of a series of operation events. Each event contains 
the necessary data for visualization.

MindSpore uses the Callback mechanism to record graph, scalar, image and model 
information into summary log file. 

- The scalar and image is recorded by Summary operator.

- The computation graph is recorded by SummaryRecord after it was compiled.

- The model parameters is recorded by TrainLineage or EvalLineage.

MindInsight provides the capability to analyze summary log files and visualize 
relative information.

## Visualization

MindInsight provides users with a full-process visualized GUI during 
AI development, in order to help model developers to improve the model 
precision efficiently.

MindInsight has the following visualization capabilities:

### Graph visualization

The GUI of MindInsight displays the structure of neural network, the data flow and control 
flow of each operator during the entire training process.

### Scalar visualization

The GUI of MindInsight displays the change tendency of a specific scalar during the entire 
training process, such as loss value and accuracy rate of each iteration. 

Two scalar curves can be combined and displayed in one chart. 

### Image visualization

The GUI of MindInsight displays both original images and enhanced images during the entire 
training process.

### Model lineage visualization

The GUI of MindInsight displays the parameters and metrics of all models, such as the 
learning rate, the number of samples and the loss function of each model.

### Dataset Graph visualization

The GUI of MindInsight displays the pipeline of dataset processing and augmentation.

### Dataset Lineage visualization

The GUI of MindInsight displays the parameters and operations of the dataset processing and augmentation.

# Installation

See [Install MindInsight](https://www.mindspore.cn/install/en).

# QuickStart

See [guidance](https://www.mindspore.cn/tutorial/en/0.1.0-alpha/advanced_use/visualization_tutorials.html)

# Docs

See [API Reference](https://www.mindspore.cn/api/en/master/index.html) 

# Community

- [MindSpore Slack](https://join.slack.com/t/mindspore/shared_invite/enQtOTcwMTIxMDI3NjM0LTNkMWM2MzI5NjIyZWU5ZWQ5M2EwMTQ5MWNiYzMxOGM4OWFhZjI4M2E5OGI2YTg3ODU1ODE2Njg1MThiNWI3YmQ) - Communication platform for developers.

# Contributing

Welcome contributions. See our [Contributor Wiki](https://gitee.com/mindspore/mindspore/blob/master/CONTRIBUTING.md) for more details.

# Release Notes

The release notes, see our [RELEASE](RELEASE.md).

# License

[Apache License 2.0](LICENSE)

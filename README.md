# MindInsight

<!-- TOC -->

- [Introduction](#introduction)
- [Installation](#installation)
    - [System Environment Information Confirmation](#system-environment-information-confirmation)
    - [Installation Methods](#installation-methods)
        - [Installation by pip](#installation-by-pip)
        - [Installation by Source Code](#installation-by-source-code)
            - [Downloading Source Code from Gitee](#downloading-source-code-from-gitee)
            - [Compiling MindInsight](#compiling-mindInsight)
    - [Installation Verification](#installation-verification)
- [Quick Start](#quick-start)
- [Docs](#docs)
- [Community](#community)
    - [Governance](#governance)
    - [Communication](#communication)
- [Vulkan Vision](#vulkan-vision)
- [Contributing](#contributing)
- [Release Notes](#release-notes)
- [License](#license)

<!-- /TOC -->

[简体中文](./README_CN.md)

## Introduction

MindInsight provides MindSpore with easy-to-use debugging and tuning capabilities. During the training, data such as scalar, tensor, image, computational graph, model hyper parameter and training’s execution time can be recorded in the file for viewing and analysis through the visual page of MindInsight.

![MindInsight Architecture](docs/arch.png)

Click to view the [MindInsight design document](https://www.mindspore.cn/doc/note/en/master/design/mindinsight.html), learn more about the design.
Click to view the [Tutorial documentation](https://www.mindspore.cn/tutorial/training/en/master/advanced_use/visualization_tutorials.html) learn more about the MindInsight tutorial.

## Installation

### System Environment Information Confirmation

- The hardware platform is Ascend or GPU.
- Confirm that [Python](https://www.python.org/ftp/python/3.7.5/Python-3.7.5.tgz) 3.7.5 is installed.
- The versions of MindInsight and MindSpore must be consistent.
- If you use source code to compile and install, the following dependencies also need to be installed:
    - Confirm that [CMake](https://cmake.org/download/) 3.14.1 or later is installed.
    - Confirm that [GCC](https://gcc.gnu.org/releases.html) 7.3.0 is installed.
    - Confirm that [node.js](https://nodejs.org/en/download/) 10.19.0 or later is installed.
    - Confirm that [wheel](https://pypi.org/project/wheel/) 0.32.0 or later is installed.
    - Confirm that [pybind11](https://pypi.org/project/pybind11/) 2.4.3 or later is installed.
- All other dependencies are included in [requirements.txt](https://gitee.com/mindspore/mindinsight/blob/master/requirements.txt).

### Installation Methods

You can install MindInsight either by pip or by source code.

#### Installation by pip

```bash
pip install https://ms-release.obs.cn-north-4.myhuaweicloud.com/{version}/MindInsight/ascend/{system}/mindinsight-{version}-cp37-cp37m-linux_{arch}.whl --trusted-host ms-release.obs.cn-north-4.myhuaweicloud.com -i https://pypi.tuna.tsinghua.edu.cn/simple
```

> - When the network is connected, dependency items are automatically downloaded during .whl package installation. (For details about other dependency items, see [requirements.txt](https://gitee.com/mindspore/mindinsight/blob/master/requirements.txt)). In other cases, you need to manually install dependency items.  
> - `{version}` denotes the version of MindInsight. For example, when you are downloading MindSpore 1.0.1, `{version}` should be 1.0.1.  
> - `{arch}` denotes the system architecture. For example, the Linux system you are using is x86 architecture 64-bit, `{arch}` should be `x86_64`. If the system is ARM architecture 64-bit, then it should be `aarch64`.  
> - `{system}` denotes the system version. For example, if you are using EulerOS ARM architecture, `{system}` should be `euleros_aarch64`. Currently, the following systems are supported by Ascend: `euleros_aarch64`/`centos_aarch64`/`centos_x86`/`ubuntu_aarch64`/`ubuntu_x86`. `ubuntu_x86` is supported by GPU.

#### Installation by Source Code

##### Downloading Source Code from Gitee

```bash
git clone https://gitee.com/mindspore/mindinsight.git
```

##### Compiling MindInsight

You can choose any of the following installation methods:

1. Run the following command in the root directory of the source code:

    ```bash
    cd mindinsight
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    python setup.py install
    ```

2. Build the `whl` package for installation.

    Enter the root directory of the source code, first execute the MindInsight compilation script in the `build` directory, and then execute the command to install the `whl` package generated in the `output` directory.

    ```bash
    cd mindinsight
    bash build/build.sh
    pip install output/mindinsight-{version}-cp37-cp37m-linux_{arch}.whl -i https://pypi.tuna.tsinghua.edu.cn/simple
    ```

### Installation Verification

Execute the following command:

```bash
mindinsight start
```

If it prompts the following information, the installation is successful:

```bash
Web address: http://127.0.0.1:8080
service start state: success
```

## Quick Start

Before using MindInsight, the data in the training process should be recorded. When starting MindInsight, the directory of the saved data should be specified. After successful startup, the data can be viewed through the web page. Here is a brief introduction to recording training data, as well as starting and stopping MindInsight.

[SummaryCollector](https://www.mindspore.cn/doc/api_python/en/master/mindspore/mindspore.train.html#mindspore.train.callback.SummaryCollector) is the interface MindSpore provides for a quick and easy collection of common data about computational graphs, loss values, learning rates, parameter weights, and so on. Below is an example of using `SummaryCollector` for data collection, specifying the directory where the data is stored in `./summary_dir`.

```python
...

from mindspore.train.callback import SummaryCollector
summary_collector = SummaryCollector(summary_dir='./summary_dir')
model.train(epoch=1, ds_train, callbacks=[summary_collector])
```

For more ways to record visual data, see the [MindInsight Tutorial](https://www.mindspore.cn/tutorial/training/en/master/advanced_use/visualization_tutorials.html).

After you've collected the data, when you launch MindInsight, specify the directory in which the data has been stored.

```bash
mindinsight start --summary-base-dir ./summary_dir
```

After successful startup, visit `http://127.0.0.1:8080` through the browser to view the web page.

Command of stopping the MindInsight service:

```bash
mindinsight stop
```

## Docs

More details about installation guide, tutorials and APIs, please see the
[User Documentation](https://gitee.com/mindspore/docs).

## Community

### Governance

Check out how MindSpore Open Governance [works](https://gitee.com/mindspore/community/blob/master/governance.md).

### Communication

- [MindSpore Slack](https://join.slack.com/t/mindspore/shared_invite/zt-dgk65rli-3ex4xvS4wHX7UDmsQmfu8w) - Communication platform for developers.
- IRC channel at `#mindspore` (only for meeting minutes logging purpose)
- Video Conferencing: TBD
- Mailing-list: <https://mailweb.mindspore.cn/postorius/lists>

## Vulkan Vision

Vulkan Vision(V-Vision) provides an unprecedented level of detail into the execution of Vulkan applications through dynamic instrumentation. V-Vision supports analyzing AI workloads implemented using the a compute pipeline as well as traditional raster and ray-tracing Vulkan applications. To use V-Vision please refer to the [build instructions](https://gitee.com/mindspore/mindspore/ecosystem_tools/VulkanVision/README.md).

## Contributing

Welcome contributions. See our [Contributor Wiki](https://gitee.com/mindspore/mindspore/blob/master/CONTRIBUTING.md) for more details.

## Release Notes

The release notes, see our [RELEASE](RELEASE.md).

## License

[Apache License 2.0](LICENSE)

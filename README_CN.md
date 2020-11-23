# MindInsight
<!-- TOC -->

- [MindInsight介绍](#mindinsight介绍)
- [安装](#安装)
    - [确认系统环境信息](#确认系统环境信息)
    - [安装方式](#安装方式)
        - [pip安装](#pip安装)
        - [源码编译安装](#源码编译安装)
            - [从代码仓下载源码](#从代码仓下载源码)
            - [编译安装MindInsight](#编译安装mindinsight)
    - [验证是否成功安装](#验证是否成功安装)
- [快速入门](#快速入门)
- [文档](#文档)
- [社区](#社区)
    - [治理](#治理)
    - [交流](#交流)
- [贡献](#贡献)
- [版本说明](#版本说明)
- [许可证](#许可证)

<!-- /TOC -->

[View English](./README.md)

## MindInsight介绍

MindInsight为MindSpore提供了简单易用的调优调试能力。在训练过程中，可以将标量、张量、图像、计算图、模型超参、训练耗时等数据记录到文件中，通过MindInsight可视化页面进行查看及分析。

![MindInsight Architecture](docs/arch.png)

点击查看[设计文档](https://www.mindspore.cn/doc/note/zh-CN/master/design/overall.html)，了解更多设计详情。
点击查看[教程文档](https://www.mindspore.cn/tutorial/training/zh-CN/master/advanced_use/visualization_tutorials.html)，了解更多MindInsight教程。

## 安装

### 确认系统环境信息

- 硬件平台为Ascend或GPU。  
- 确认安装[Python](https://www.python.org/ftp/python/3.7.5/Python-3.7.5.tgz) 3.7.5版本。
- MindInsight与MindSpore的版本需保持一致。
- 若采用源码编译安装，还需确认安装以下依赖。
    - 确认安装[CMake](https://cmake.org/download/) 3.14.1及以上版本。
    - 确认安装[GCC](https://gcc.gnu.org/releases.html) 7.3.0版本。
    - 确认安装[node.js](https://nodejs.org/en/download/) 10.19.0及以上版本。
    - 确认安装[wheel](https://pypi.org/project/wheel/) 0.32.0及以上版本。
    - 确认安装[pybind11](https://pypi.org/project/pybind11/) 2.4.3及以上版本。
- 其他依赖参见[requirements.txt](https://gitee.com/mindspore/mindinsight/blob/master/requirements.txt)。

### 安装方式

可以采用pip安装或者源码编译安装两种方式。

#### pip安装

```bash
pip install https://ms-release.obs.cn-north-4.myhuaweicloud.com/{version}/MindInsight/ascend/{system}/mindinsight-{version}-cp37-cp37m-linux_{arch}.whl --trusted-host ms-release.obs.cn-north-4.myhuaweicloud.com -i https://mirrors.huaweicloud.com/repository/pypi/simple
```

> - 在联网状态下，安装whl包时会自动下载MindSpore安装包的依赖项（依赖项详情参见[requirements.txt](https://gitee.com/mindspore/mindinsight/blob/master/requirements.txt)），其余情况需自行安装。  
> - `{version}`表示MindInsight版本号，例如下载1.0.1版本MindInsight时，`{version}`应写为1.0.1。  
> - `{arch}`表示系统架构，例如使用的Linux系统是x86架构64位时，`{arch}`应写为`x86_64`。如果系统是ARM架构64位，则写为`aarch64`。  
> - `{system}`表示系统版本，例如使用的欧拉系统ARM架构，`{system}`应写为`euleros_aarch64`，目前Ascend版本可支持以下系统`euleros_aarch64`/`centos_aarch64`/`centos_x86`/`ubuntu_aarch64`/`ubuntu_x86`；GPU版本可支持以下系统`ubuntu_x86`。

#### 源码编译安装

##### 从代码仓下载源码

```bash
git clone https://gitee.com/mindspore/mindinsight.git
```

##### 编译安装MindInsight

可选择以下任意一种安装方式：

1. 在源码根目录下执行如下命令。

    ```bash
    cd mindinsight
    pip install -r requirements.txt -i https://mirrors.huaweicloud.com/repository/pypi/simple
    python setup.py install
    ```

2. 构建`whl`包进行安装。

    进入源码的根目录，先执行`build`目录下的MindInsight编译脚本，再执行命令安装`output`目录下生成的`whl`包。

    ```bash
    cd mindinsight
    bash build/build.sh
    pip install output/mindinsight-{version}-cp37-cp37m-linux_{arch}.whl -i https://mirrors.huaweicloud.com/repository/pypi/simple
    ```

### 验证是否成功安装

执行如下命令：

```bash
mindinsight start
```

如果出现下列提示，说明安装成功：

```bash
Web address: http://127.0.0.1:8080
service start state: success
```

## 快速入门

使用MindInsight前，需要先将训练过程中的数据记录下来，启动MindInsight时，指定所保存的数据的位置，启动成功后，
即可通过可视化页面查看数据。下面将简单介绍记录训练过程数据，以及启动、停止MindInsight服务。

[SummaryCollector](https://www.mindspore.cn/doc/api_python/zh-CN/master/mindspore/mindspore.train.html#mindspore.train.callback.SummaryCollector)是MindSpore提供的快速简易地收集一些常见信息的接口，收集的信息包括计算图、损失值、学习率、参数权重等。
下面是使用 `SummaryCollector` 进行数据收集的示例，其中指定存放数据的目录为 `./summary_dir`。

```python
...

from mindspore.train.callback import SummaryCollector
summary_collector = SummaryCollector(summary_dir='./summary_dir')
model.train(epoch=1, ds_train, callbacks=[summary_collector])
```

更多记录可视化数据的方法，请点击查看[MindInsight使用教程](https://www.mindspore.cn/tutorial/training/zh-CN/master/advanced_use/visualization_tutorials.html)。

收集好数据后，启动MindInsight时指定存放数据的目录。

```bash
mindinsight start --summary-base-dir ./summary_dir
```

启动成功后，通过浏览器访问 `http://127.0.0.1:8080`，查看可视化页面。

停止MindInsight服务的命令：

```bash
mindinsight stop
```

## 文档

有关安装指南、教程和API的更多详细信息，请参阅[用户文档](https://gitee.com/mindspore/docs)。

## 社区

### 治理

查看MindSpore如何进行[开放治理](https://gitee.com/mindspore/community/blob/master/governance.md)。

### 交流

- [MindSpore Slack](https://join.slack.com/t/mindspore/shared_invite/zt-dgk65rli-3ex4xvS4wHX7UDmsQmfu8w) 开发者交流平台。
- `#mindspore`IRC频道（仅用于会议记录）
- 视频会议：待定
- 邮件列表：<https://mailweb.mindspore.cn/postorius/lists>

## 贡献

欢迎参与贡献。更多详情，请参阅我们的[贡献者Wiki](https://gitee.com/mindspore/mindspore/blob/master/CONTRIBUTING.md)。

## 版本说明

版本说明请参阅[RELEASE](RELEASE.md)。

## 许可证

[Apache License 2.0](LICENSE)

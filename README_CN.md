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

点击查看[MindInsight设计文档](https://www.mindspore.cn/mindinsight/docs/zh-CN/master/training_visual_design.html)，了解更多设计详情。
点击查看[教程文档](https://www.mindspore.cn/mindinsight/docs/zh-CN/master/index.html)，了解更多MindInsight教程。

## 安装

### 确认系统环境信息

- 硬件平台支持Ascend，GPU和CPU。
- 确认安装[Python](https://www.python.org/ftp/python/3.7.5/Python-3.7.5.tgz) 3.7.5版本。
- MindInsight与MindSpore的版本需保持一致。
- 若采用源码编译安装，还需确认安装以下依赖。
    - 确认安装[node.js](https://nodejs.org/en/download/) 10.19.0及以上版本。
    - 确认安装[wheel](https://pypi.org/project/wheel/) 0.32.0及以上版本。
- 其他依赖参见[requirements.txt](https://gitee.com/mindspore/mindinsight/blob/master/requirements.txt)。

### 安装方式

可以采用pip安装或者源码编译安装两种方式。

#### pip安装

安装PyPI上的版本:

```bash
pip install mindinsight
```

安装自定义版本:

```bash
pip install https://ms-release.obs.cn-north-4.myhuaweicloud.com/{version}/MindInsight/any/mindinsight-{version}-py3-none-any.whl --trusted-host ms-release.obs.cn-north-4.myhuaweicloud.com -i https://pypi.tuna.tsinghua.edu.cn/simple
```

> - 在联网状态下，安装whl包时会自动下载MindInsight安装包的依赖项（依赖项详情参见[requirements.txt](https://gitee.com/mindspore/mindinsight/blob/master/requirements.txt)），其余情况需自行安装。
> - `{version}`表示MindInsight版本号，例如下载1.3.0版本MindInsight时，`{version}`应写为1.3.0。
> - MindInsight支持使用x86 64位或ARM 64位架构的Linux发行版系统。

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
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    python setup.py install
    ```

2. 构建`whl`包进行安装。

    进入源码的根目录，先执行`build`目录下的MindInsight编译脚本，再执行命令安装`output`目录下生成的`whl`包。

    ```bash
    cd mindinsight
    bash build/build.sh
    pip install output/mindinsight-{version}-py3-none-any.whl -i https://pypi.tuna.tsinghua.edu.cn/simple
    ```

### 验证是否成功安装

执行如下命令：

```bash
mindinsight start [--port PORT]
```

*注：--port 参数默认值为8080*

如果出现下列提示，说明安装成功：

```bash
Web address: http://127.0.0.1:8080
service start state: success
```

## 快速入门

使用MindInsight前，需要先将训练过程中的数据记录下来，启动MindInsight时，指定所保存的数据的位置，启动成功后，
即可通过可视化页面查看数据。下面将简单介绍记录训练过程数据，以及启动、停止MindInsight服务。

[SummaryCollector](https://www.mindspore.cn/docs/zh-CN/r1.7/api_python/mindspore.train.html#mindspore.train.callback.SummaryCollector)是MindSpore提供的快速简易地收集一些常见信息的接口，收集的信息包括计算图、损失值、学习率、参数权重等。
下面是使用 `SummaryCollector` 进行数据收集的示例，其中指定存放数据的目录为 `./summary_dir`。

```python
...

from mindspore.train.callback import SummaryCollector
summary_collector = SummaryCollector(summary_dir='./summary_dir')
model.train(epoch=1, ds_train, callbacks=[summary_collector])
```

更多记录可视化数据的方法，请点击查看[MindInsight使用教程](https://www.mindspore.cn/mindinsight/docs/zh-CN/master/index.html)。

收集好数据后，启动MindInsight时指定存放数据的目录。

```bash
mindinsight start --summary-base-dir ./summary_dir [--port PORT]
```

*注：--port 参数默认值为8080*

启动成功后，通过浏览器访问 `http://127.0.0.1:8080`，查看可视化页面。

停止MindInsight服务的命令：

```bash
mindinsight stop [--port PORT]
```

*注：--port 参数默认值为8080，停止指定端口服务*

更多MindInsight命令行参数使用方法，请点击查看[MindInsight命令行简介](https://www.mindspore.cn/mindinsight/docs/zh-CN/r1.5/mindinsight_commands.html)。

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

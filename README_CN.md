[View English](./README.md)

- [介绍](#介绍)
- [安装](#安装)
- [快速入门](#快速入门)
- [文档](#文档)
- [社区](#社区)
    - [治理](#治理)
    - [交流](#交流)
- [贡献](#贡献)
- [版本说明](#版本说明)
- [许可证](#许可证)

## 介绍
MindInsight为MindSpore提供了简单易用的调优调试能力。在训练过程中，可以将标量、张量、图像、计算图、模型超参、训练耗时等数据记录到文件中，通过MindInsight可视化页面进行查看及分析。

![MindInsight Architecture](docs/arch.png)

点击查看[设计文档](https://www.mindspore.cn/docs/zh-CN/r0.7/design.html)，了解更多设计详情。
点击查看[教程文档](https://www.mindspore.cn/tutorial/zh-CN/r0.7/advanced_use/visualization_tutorials.html)，了解更多MindInsight教程。

## 安装
请从[MindSpore下载页面](https://www.mindspore.cn/versions)下载并安装whl包。

```
pip install -U mindinsight-{version}-cp37-cp37m-linux_{arch}.whl
```

更多MindInsight的安装方法，请点击[安装教程](https://www.mindspore.cn/install/)中的MindInsight章节进行查看。

## 快速入门
使用MindInsight前，需要先将训练过程中的数据记录下来，启动MindInsight时，指定所保存的数据的位置，启动成功后，
即可通过可视化页面查看数据。下面将简单介绍记录训练过程数据，以及启动、停止MindInsight服务。

[SummaryCollector](https://www.mindspore.cn/api/zh-CN/r0.7/api/python/mindspore/mindspore.train.html?highlight=summarycollector#mindspore.train.callback.SummaryCollector)是MindSpore提供的快速简易地收集一些常见信息的接口，收集的信息包括计算图、损失值、学习率、参数权重等。
下面是使用 `SummaryCollector` 进行数据收集的示例，其中指定存放数据的目录为 `./summary_dir`。
```
...

from mindspore.train.callback import SummaryCollector
summary_collector = SummaryCollector(summary_dir='./summary_dir')
model.train(epoch=1, ds_train, callbacks=[summary_collector])
```

更多记录可视化数据的方法，请点击查看[MindInsight使用教程](https://www.mindspore.cn/tutorial/zh-CN/r0.7/advanced_use/visualization_tutorials.html)。

收集好数据后，启动MindInsight时指定存放数据的目录。
```
mindinsight start --summary-base-dir ./summary_dir
```

启动成功后，通过浏览器访问 `http://127.0.0.1:8080`，查看可视化页面。

停止MindInsight服务的命令：
```
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
欢迎参与贡献。更多详情，请参阅我们的[贡献者Wiki](https://gitee.com/mindspore/mindspore/blob/r0.7/CONTRIBUTING.md)。

## 版本说明
版本说明请参阅[RELEASE](RELEASE.md)。

## 许可证
[Apache License 2.0](LICENSE)

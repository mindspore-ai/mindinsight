[简体中文](./README_CN.md)

- [Introduction ](#introduction)
- [Installation](#installation)
- [QuickStart](#quick-start)
- [Docs](#docs)
- [Community](#community)
    - [Governance](#governance)
    - [Communication](#communication)
- [Contributing](#contributing)
- [Release Notes](#release-notes)
- [License](#license)

## Introduction
MindInsight provides MindSpore with easy-to-use debugging and tuning capabilities. During the training, data such as scalar, tensor, image, computational graph, model hyper parameter and training’s execution time can be recorded in the file for viewing and analysis through the visual page of MindInsight.

![MindInsight Architecture](docs/arch.png)

Click to view the [Design document](https://www.mindspore.cn/doc/note/en/master/design.html) (visit [Design document](https://www.mindspore.cn/docs/en/master/design.html) before Sep. 24)，learn more about the design.
Click to view the [Tutorial documentation](https://www.mindspore.cn/tutorial/training/en/master/advanced_use/visualization_tutorials.html) (visit [Tutorial documentation](https://www.mindspore.cn/tutorial/en/master/advanced_use/visualization_tutorials.html) before Sep. 24) learn more about the MindInsight tutorial.

## Installation
Download whl package from [MindSpore download page](https://www.mindspore.cn/versions/en), and install the package.

```
pip install -U mindinsight-{version}-cp37-cp37m-linux_{arch}.whl
```

For more details on how to install MindInsight, click on the MindInsight section of the [installation tutorial](https://www.mindspore.cn/install/en).

## Quick Start
Before using MindInsight, the data in the training process should be recorded. When starting MindInsight, the directory of the saved data should be specified. After successful startup, the data can be viewed through the web page. Here is a brief introduction to recording training data, as well as starting and stopping MindInsight.

[SummaryCollector](https://www.mindspore.cn/doc/api_python/en/master/mindspore/mindspore.train.html#mindspore.train.callback.SummaryCollector) (visit [SummaryCollector](https://www.mindspore.cn/api/en/master/api/python/mindspore/mindspore.train.html#mindspore.train.callback.SummaryCollector) before Sep. 24) is the interface MindSpore provides for a quick and easy collection of common data about computational graphs, loss values, learning rates, parameter weights, and so on. Below is an example of using `SummaryCollector` for data collection, specifying the directory where the data is stored in `./summary_dir`.
```
...

from mindspore.train.callback import SummaryCollector
summary_collector = SummaryCollector(summary_dir='./summary_dir')
model.train(epoch=1, ds_train, callbacks=[summary_collector])
```

For more ways to record visual data, see the [MindInsight Tutorial](https://www.mindspore.cn/tutorial/training/en/master/advanced_use/visualization_tutorials.html) (visit [MindInsight Tutorial](https://www.mindspore.cn/tutorial/en/master/advanced_use/visualization_tutorials.html) before Sep. 24).

After you've collected the data, when you launch MindInsight, specify the directory in which the data has been stored.
```
mindinsight start --summary-base-dir ./summary_dir
```

After successful startup, visit `http://127.0.0.1:8080` through the browser to view the web page.

Command of stopping the MindInsight service:
```
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

## Contributing
Welcome contributions. See our [Contributor Wiki](https://gitee.com/mindspore/mindspore/blob/master/CONTRIBUTING.md) for
more details.

## Release Notes
The release notes, see our [RELEASE](RELEASE.md).

## License
[Apache License 2.0](LICENSE)


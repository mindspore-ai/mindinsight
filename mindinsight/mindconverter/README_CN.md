# MindConverter 文档

[View English](./README.md)

## 介绍

MindConverter是一款用于将PyTorch脚本转换到MindSpore脚本的工具。结合转换报告的信息，用户只需对转换后的脚本进行微小的改动，即可快速将PyTorch框架的模型迁移到MindSpore。

## 安装

此工具是MindInsight的一部分，安装MindInsight即可使用此工具，无需其他操作。

## 命令行用法

```buildoutcfg
mindconverter [-h] [--version] --in_file IN_FILE [--output OUTPUT]
              [--report REPORT]

optional arguments:
  -h, --help         show this help message and exit
  --version          show program's version number and exit
  --in_file IN_FILE  Specify path for script file.
  --output OUTPUT    Specify path for converted script file directory. Default
                     is output directory in the current working directory.
  --report REPORT    Specify report directory. Default is the current working
                     directorys
```

## 示例

有如下一系列PyTorch模型的脚本，
```buildoutcfg
~$ ls
models
~$ ls models
lenet.py resnet.py vgg.py
```

转换lenet.py这个脚本，
```buildoutcfg
~$ mindconverter --in_file models/lenet.py
```

可以看到生成了一个转换报告，输出了一个转换后的MindSpore脚本。
```buildoutcfg
~$ ls
lenet_report.txt models output
~$ ls output
lenet.py
```

执行该示例时，请确认分别将[models/lenet.py](../../tests/st/func/mindconverter/data/lenet_script.py)和[output/lenet.py](../../tests/st/func/mindconverter/data/lenet_converted.py)作为输入和输出。
由于工具转换并非100%完美，若转换后的脚本存在问题，建议用户参考转换报告对其进行修正。

## 不支持的情形1

部分类和方法目前无法转换：
* 使用```torch.Tensor```的```shape```，```ndim```和```dtype```成员
* ```torch.nn.AdaptiveXXXPoolXd```和```torch.nn.functional.adaptive_XXX_poolXd()```
* ```torch.nn.functional.Dropout```
* ```torch.unsqueeze()```和```torch.Tensor.unsqueeze()```
* ```torch.chunk()```和```torch.Tensor.chunk()```

## 不支持的情形2

继承的父类是nn.Module的子类。

例如：(如下代码片段摘自torchvision.models.mobilenet)
```python
from torch import nn

class ConvBNReLU(nn.Sequential):
    def __init__(self, in_planes, out_planes, kernel_size=3, stride=1, groups=1):
        padding = (kernel_size - 1) // 2
        super(ConvBNReLU, self).__init__(
            nn.Conv2d(in_planes, out_planes, kernel_size, stride, padding, groups=groups, bias=False),
            nn.BatchNorm2d(out_planes),
            nn.ReLU6(inplace=True)
        )
```

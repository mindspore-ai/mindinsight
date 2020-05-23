### Introduction

MindConverter is a tool that converting PyTorch scripts to MindSpore scripts. With minial manual editing and the guidance from conversion reports, users may easily migrate their model from PyTorch framework to MindSpore.



### System Requirements

* PyTorch v1.5.0
* MindSpore v0.2.0

### Installation

This tool is part of MindInsight and accessible to users after installing MindInsight, no extra installation is needed.

### Commandline Usage
Set the model scripts directory as the PYTHONPATH environment variable first: 
```buildoutcfg
export PYTHONPATH=<model scripts dir>
```

mindconverter commandline usage:
```buildoutcfg
mindconverter [-h] [--version] --in_file IN_FILE [--output OUTPUT]
              [--report REPORT]

MindConverter CLI entry point (version: 0.2.0)

optional arguments:
  -h, --help         show this help message and exit
  --version          show program's version number and exit
  --in_file IN_FILE  Specify path for script file.
  --output OUTPUT    Specify path for converted script file directory. Default
                     is output directory in the current working directory.
  --report REPORT    Specify report directory. Default is the current working
                     directorys
```

Usage example:
```buildoutcfg
export PYTHONPATH=~/my_pt_proj/models
mindconverter --in_file lenet.py
```

Since the conversion is not 100% flawless, we encourage users to checkout the reports when fixing issues of the converted scripts.


### Unsupported Situation #1
Classes and functions that can't be converted:
* The use of shape, ndim and dtype member of torch.Tensor.
* torch.nn.AdaptiveXXXPoolXd and torch.nn.functional.adaptive_XXX_poolXd()
* torch.nn.functional.Dropout
* torch.unsqueeze() and torch.Tensor.unsqueeze()
* torch.chunk() and torch.Tensor.chunk()

### Unsupported Situation #2

Subclassing from the subclasses of nn.Module

e.g. (code snip from torchvision,models.mobilenet)

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

### Unsupported Situation #3

Unconventional import naming

e.g.
```python
import torch.nn as mm
```
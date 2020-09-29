# MindWizard 文档

[View English](./README.md)

## 介绍

MindWizard是一款快速生成经典网络脚本的工具。工具根据用户选择，组合模型、超参、数据集等网络参数，自动生成目标网络脚本，生成的网络脚本可以在Ascend或GPU等环境上进行训练和评估。

## 安装

此工具是MindInsight的一部分，安装MindInsight即可使用此工具，无需其他操作。

## 命令行用法

```buildoutcfg
mindwizard [-h] [--version] name
positional arguments:
  name        Specify the new project name.
optional arguments:
  -h, --help  show this help message and exit
  --version   show program's version number and exit
```

## 生成网络脚本工程

用户运行mindwizard，根据提示回答以下问题：

1. 请选择网络（LeNet / AlexNet / ResNet50 / ...）

    1.1. 请选择损失函数（SoftmaxCrossEntropyWithLogits / ...）
    
    缺省值: SoftmaxCrossEntropyWithLogits
    
    1.2. 请选择优化器（Adam / Momentum / SGD ...）
    
    缺省值: Momentum

2. 请选择数据集（MNIST / Cifar10 / ImageNet / ...）

缺省值: MNIST or ImageNet

生成脚本后，用户可执行训练和评估，详细介绍可参考网络脚本工程中的README。

## 网络脚本工程结构

```shell
project
 |- script
 |   |- run_standalone_train.sh     # 单卡训练脚本
 |   |- run_distribute_train.sh     # 多卡训练脚本
 |   |- run_eval.sh                 # 评估脚本
 |   |- ...
 |- src
 |   |- config.py                   # 参数配置
 |   |- dataset.py                  # 数据集处理
 |   |- lenet.py/resent.py/...      # 网络定义
 |   |- ...
 |- eval.py                         # 网络评估
 |- train.py                        # 网络训练
 |- README.md
```

## 示例

生成LeNet脚本工程。

```buildoutcfg
$ mindwizard project

>>> Please select a network:
   1: alexnet
   2: lenet
   3: resnet50
 : 2
Your choice is lenet.
>>> Please select a loss function:
   1: SoftmaxCrossEntropyWithLogits
 [1]: 1
Your choice is SoftmaxCrossEntropyWithLogits.
>>> Please select an optimizer:
   1: Adam
   2: Momentum
   3: SGD
 [2]: 2
Your choice is Momentum.
>>> Please select a dataset:
   1: MNIST
 [1]: 1
Your choice is MNIST.

project is generated in $PWD/project

$ cd $PWD/project/scripts
```

### 训练

多卡训练

```
# Ascend
Usage: bash run_distribute_train.sh [RANK_TABLE_FILE] [DATASET_PATH] [PRETRAINED_CKPT_PATH](optional)

# GPU
Usage: bash run_distribute_train_gpu.sh [DATASET_PATH] [PRETRAINED_CKPT_PATH](optional)
```

单卡训练

```
# Ascend
Usage: bash run_standalone_train.sh [DATASET_PATH] [PRETRAINED_CKPT_PATH](optional)

# GPU 
Usage: bash run_standalone_train_gpu.sh [DATASET_PATH] [PRETRAINED_CKPT_PATH](optional)
```

### 评估

```
# Ascend
Usage: bash run_eval.sh [DATASET_PATH] [CHECKPOINT_PATH]

# GPU
Usage: bash run_eval_gpu.sh [DATASET_PATH] [CHECKPOINT_PATH]
```

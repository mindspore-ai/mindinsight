# MindWizard Documentation

[查看中文](./README_CN.md)

## Introduction

MindWizard is a tool for quickly generating classic network scripts. It collects user preference on the combination of network parameters, such models, hyperparameters and datasets, then automatically generates target network scripts. The generated scripts can be used for training and evaluation in the Ascend or GPU environment.

## Installation

This tool is part of MindInsight and accessible to users after installing MindInsight, no extra installation is needed.

## Commandline Usage

```buildoutcfg
mindwizard [-h] [--version] name
positional arguments:
  name        Specify the new project name.
optional arguments:
  -h, --help  show this help message and exit
  --version   show program's version number and exit
```

## Generating Network Project

Run the mindwizard command and answer the following questions as prompted：

1. Select a network（LeNet / AlexNet / ResNet50 / ...）

    1.1. Select a Loss Function（SoftmaxCrossEntropyWithLogits / ...）
    
    Default: SoftmaxCrossEntropyWithLogits

    1.2. Select a Optimizer（Adam / Momentum / SGD ...）
    
    Default: Momentum

2. Select a Dataset（MNIST / Cifar10 / ImageNet / ...）

Default: MNIST or ImageNet

After the project is generated, user can perform training and evaluation. For details, see README in the network project.

## Network Project Structure

```shell
project
 |- script
 |   |- run_standalone_train.sh     # launch standalone training
 |   |- run_distribute_train.sh     # launch distributed training
 |   |- run_eval.sh                 # launch evaluation
 |   |- ...
 |- src
 |   |- config.py                   # parameter configuration
 |   |- dataset.py                  # data preprocessing
 |   |- lenet.py/resent.py/...      # network definition
 |   |- ...
 |- eval.py                         # evaluate network
 |- train.py                        # train network
 |- README.md
```

## Example

Generate LeNet project.

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

### Training

Distributed training

```
# Ascend
Usage: bash run_distribute_train.sh [RANK_TABLE_FILE] [DATASET_PATH] [PRETRAINED_CKPT_PATH](optional)

# GPU
Usage: bash run_distribute_train_gpu.sh [DATASET_PATH] [PRETRAINED_CKPT_PATH](optional)
```

Standalone training

```
# Ascend
Usage: bash run_standalone_train.sh [DATASET_PATH] [PRETRAINED_CKPT_PATH](optional)

# GPU 
Usage: bash run_standalone_train_gpu.sh [DATASET_PATH] [PRETRAINED_CKPT_PATH](optional)
```

### Evaluation

```
# Ascend
Usage: bash run_eval.sh [DATASET_PATH] [CHECKPOINT_PATH]

# GPU
Usage: bash run_eval_gpu.sh [DATASET_PATH] [CHECKPOINT_PATH]
```

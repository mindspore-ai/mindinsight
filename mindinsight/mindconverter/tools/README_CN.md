# 工具使用教程

[Switch to English version](./README.md)

<!-- TOC -->

- [工具使用教程](#工具使用教程)
    - [权重名修正工具](#权重名修正工具)
        - [概述](#概述)
        - [使用方法](#使用方法)
        - [使用示例](#使用示例)
        - [约束限制](#约束限制)

<!-- /TOC -->

## 权重名修正工具

### 概述

所需的依赖

```text
MindSpore>=1.2
```

对于由MindConverter转换生成的MindSpore脚本，用户可能会依照自己的需求对脚本中的类名、变量名进行修改，以增加网络脚本的可读性。但是这些修改有可能会导致加载权重信息时，因为无法找到对应的权重名称，而加载失败。该[权重名修正工具](./fix_checkpoint_file.py)用于将脚本中修改后的内容统一修改到权重文件中，生成可以用于新脚本的权重文件。

### 使用方法

```bash
usage: fix_checkpoint_file.py [-h] [--fixed_ckpt_file FIXED_CKPT_FILE]
                              source_py_file source_ckpt_file fixed_py_file

Fix weight name in CheckPoint file.

positional arguments:
  source_py_file        source model script file
  source_ckpt_file      source_checkpoint file
  fixed_py_file         fixed model script file  

optional arguments:
  -h, --help            show this help message and exit
  --fixed_ckpt_file FIXED_CKPT_FILE
                        Optional, the output path of fixed checkpoint file.
                        Default output file is saved in the current working
                        directory, with the same name as `fixed_py_file`.
```

### 使用示例

假设原始网络脚本为`xxx/model.py`，原始权重文件为`xxx/model.ckpt`，修改后的网络脚本为`xxx/fixed_model.py`，生成的新权重文件为`xxx/fixed_model.ckpt`。

则运行命令为：

```bash
python -m mindinsight.mindconverter.tools.fix_checkpoint_file xxx/model.py xxx/model.ckpt xxx/fixed_model.py --fixed_ckpt_file xxx/fixed_model
```

如果显示结果如下，则说明转换完成：

```text
Saved new checkpoint file to xxx/fixed_model.ckpt.
```

### 约束限制

1. 该工具仅适用于：在MindConverter的图模式下（通过--model_file迁移）迁移生成的MindSpore网络脚本和权重文件。
2. 该工具仅适用于修改变量名，类名的场景中，不适用于修改网络结构、脚本结构（新增或删除算子定义）的应用场景。
3. 该工具依赖MindSpore，需要确保正确安装MindSpore。

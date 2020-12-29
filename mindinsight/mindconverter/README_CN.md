# MindConverter教程

[Switch to English version](./README.md)

<!-- TOC -->

- [MindConverter教程](#mindconverter教程)
    - [概述](#概述)
    - [安装](#安装)
    - [用法](#用法)
        - [PyTorch模型脚本迁移](#pytorch模型脚本迁移)
        - [TensorFlow模型脚本迁移](#tensorflow模型脚本迁移)
    - [使用场景](#使用场景)
    - [使用示例](#使用示例)
        - [基于AST的脚本转换示例](#基于ast的脚本转换示例)
        - [基于图结构的脚本生成示例](#基于图结构的脚本生成示例)
            - [PyTorch模型脚本生成示例](#pytorch模型脚本生成示例)
            - [TensorFlow模型脚本生成示例](#tensorflow模型脚本生成示例)
    - [注意事项](#注意事项)
    - [AST方案不支持场景](#ast方案不支持场景)
        - [场景1](#场景1)
        - [场景2](#场景2)
    - [三方库依赖](#三方库依赖)
    - [常见问题](#常见问题)
    - [附录](#附录)
        - [TensorFlow Pb模型导出](#tensorflow-pb模型导出)
        - [MindConverter错误码速查表](#mindconverter错误码速查表)

<!-- /TOC -->

## 概述

MindConverter是一款用于将PyTorch、TensorFlow脚本转换到MindSpore脚本的工具。结合转换报告的信息，用户只需对转换后的脚本进行微小的改动，即可快速将PyTorch、TensorFlow框架的模型脚本迁移到MindSpore。

## 安装

此工具为MindInsight的子模块，安装MindInsight后，即可使用MindConverter，MindInsight安装请参考该[安装文档](https://www.mindspore.cn/install/)。

## 用法

MindConverter提供命令行（Command-line interface, CLI）的使用方式，命令如下。

```bash
usage: mindconverter [-h] [--version] [--in_file IN_FILE]
                     [--model_file MODEL_FILE] [--shape SHAPE]
                     [--input_nodes INPUT_NODES] [--output_nodes OUTPUT_NODES]
                     [--output OUTPUT] [--report REPORT]
                     [--project_path PROJECT_PATH]

optional arguments:
  -h, --help            show this help message and exit
  --version             show program version number and exit
  --in_file IN_FILE     Specify path for script file to use AST schema to do
                        script conversation.
  --model_file MODEL_FILE
                        PyTorch .pth or TensorFlow .pb model file path to use
                        graph based schema to do script generation. When
                        `--in_file` and `--model_file` are both provided, use
                        AST schema as default.
  --shape SHAPE         Optional, expected input tensor shape of
                        `--model_file`. It is required when use graph based
                        schema. Usage: --shape 1,3,244,244
  --input_nodes INPUT_NODES
                        Optional, input node(s) name of `--model_file`. It is
                        required when use TensorFlow model. Usage:
                        --input_nodes input_1:0,input_2:0
  --output_nodes OUTPUT_NODES
                        Optional, output node(s) name of `--model_file`. It is
                        required when use TensorFlow model. Usage:
                        --output_nodes output_1:0,output_2:0
  --output OUTPUT       Optional, specify path for converted script file
                        directory. Default output directory is `output` folder
                        in the current working directory.
  --report REPORT       Optional, specify report directory. Default is
                        converted script directory.
  --project_path PROJECT_PATH
                        Optional, PyTorch scripts project path. If PyTorch
                        project is not in PYTHONPATH, please assign
                        `--project_path` when use graph based schema. Usage:
                        --project_path ~/script_file/
```

### PyTorch模型脚本迁移

#### MindConverter提供两种PyTorch模型脚本迁移方案：

1. **基于抽象语法树(Abstract syntax tree, AST)的脚本转换**：指定`--in_file`的值，将使用基于AST的脚本转换方案；
2. **基于图结构的脚本生成**：指定`--model_file`与`--shape`将使用基于图结构的脚本生成方案。

> 若同时指定了`--in_file`，`--model_file`将默认使用AST方案进行脚本迁移。

当使用基于图结构的脚本生成方案时，要求必须指定`--shape`的值；当使用基于AST的脚本转换方案时，`--shape`会被忽略。

其中，`--output`与`--report`参数可省略。若省略，MindConverter将在当前工作目录（Working directory）下自动创建`output`目录，将生成的脚本、转换报告输出至该目录。

另外，当使用基于图结构的脚本生成方案时，请确保原PyTorch项目已在Python包搜索路径中，可通过CLI进入Python交互式命令行，通过import的方式判断是否已满足；若未加入，可通过`--project_path`
命令手动将项目路径传入，以确保MindConverter可引用到原PyTorch脚本。

> 假设用户项目目录为`/home/user/project/model_training`，用户可通过如下命令手动将项目添加至包搜索路径中：`export PYTHONPATH=/home/user/project/model_training:$PYTHONPATH`；
> 此处MindConverter需要引用原PyTorch脚本，是因为PyTorch模型反向序列化过程中会引用原脚本。

### TensorFlow模型脚本迁移

**MindConverter提供基于图结构的脚本生成方案**：指定`--model_file`、`--shape`、`--input_nodes`、`--output_nodes`进行脚本迁移。

> AST方案不支持TensorFlow模型脚本迁移，TensorFlow脚本迁移仅支持基于图结构的方案。

## 使用场景

MindConverter提供两种技术方案，以应对不同脚本迁移场景：

1. 用户希望迁移后脚本保持原脚本结构（包括变量、函数、类命名等与原脚本保持一致）；
2. 用户希望迁移后脚本保持较高的转换率，尽量少的修改、甚至不需要修改，即可实现迁移后模型脚本的执行。

对于上述第一种场景，推荐用户使用基于AST的方案进行转换（AST方案仅支持PyTorch脚本转换），AST方案通过对原PyTorch脚本的抽象语法树进行解析、编辑，将其替换为MindSpore的抽象语法树，再利用抽象语法树生成代码。理论上，AST方案支持任意模型脚本迁移，但语法树解析操作受原脚本用户编码风格影响，可能导致同一模型的不同脚本最终的转换率存在一定差异。

对于上述第二种场景，推荐用户使用基于图结构的脚本生成方案，计算图作为一种标准的模型描述语言，可以消除用户代码风格多样导致的脚本转换率不稳定的问题。在已支持算子的情况下，该方案可提供优于AST方案的转换率。

目前已基于典型图像分类网络对图结构的脚本转换方案进行测试。

> 1. 基于图结构的脚本生成方案，目前仅支持单输入、单输出模型，对于多输入模型暂不支持；
> 2. 基于图结构的脚本生成方案，由于要加载PyTorch、TensorFlow模型，会导致转换后网络中Dropout算子丢失，需要用户手动补齐；
> 3. 基于图结构的脚本生成方案持续优化中。

支持的模型列表（如下模型已基于x86 Ubuntu发行版，PyTorch 1.4.0(TorchVision 0.5)以及TensorFlow 1.15.0测试通过）:

|  模型  | PyTorch脚本 | TensorFlow脚本 | 备注 |
| :----: | :----: | :----: | :----: |
| ResNet18 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | 暂未测试 |  |
| ResNet34 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | 暂未测试 |  |
| ResNet50 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet.py) |  |
| ResNet50V2 | 暂未测试 | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet_v2.py) |  |
| ResNet101 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet.py) |  |
| ResNet101V2 | 暂未测试 | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet_v2.py) |  |
| ResNet152 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet.py) |  |
| ResNet152V2 | 暂未测试 | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet_v2.py) |  |
| Wide ResNet50 2 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | 暂未测试 | |
| Wide ResNet101 2 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | 暂未测试 | |
| VGG11/11BN | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | 暂未测试 |  |
| VGG13/13BN | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | 暂未测试 |  |
| VGG16 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/vgg16.py) |  |
| VGG16BN | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | 暂未测试 |  |
| VGG19 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/vgg19.py) |  |
| VGG19BN | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | 暂未测试 |  |
| AlexNet | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/alexnet.py) | 暂未测试 |  |
| GoogLeNet | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/googlenet.py) | 暂未测试 |  |
| Xception | 暂未测试 | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/xception.py) |  |
| InceptionV3 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/inception.py) | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/inception_v3.py) |  |
| InceptionResNetV2 | 暂未测试 | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/inception_resnet_v2.py) |  |
| MobileNetV1 | 暂未测试 | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/mobilenet.py) |  |
| MobileNetV2 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/mobilenet.py) | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/mobilenet_v2.py) |  |
| MNASNet | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/mnasnet.py) | 暂未测试 | |
| SqueezeNet | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/squeezenet.py) | 暂未测试 | |
| DenseNet121/169/201 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/densenet.py) | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/densenet.py) |  |
| DenseNet161 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/densenet.py) | 暂未测试 | |
| NASNetMobile/Large | 暂未测试 | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/nasnet.py) |  |
| EfficientNetB0~B7 | [脚本链接](https://github.com/lukemelas/EfficientNet-PyTorch) | [TF1.5脚本链接](https://github.com/tensorflow/tpu/tree/master/models/official/efficientnet) [TF2.3脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/efficientnet.py) |  |
| Unet | [脚本链接](https://github.com/milesial/Pytorch-UNet) | [脚本链接](https://github.com/zhixuhao/unet) | 由于算子`mindspore.ops.ResizeBilinear`在GPU上暂未实现，所以当运行在GPU设备上时，算子`mindspore.ops.ResizeBilinear`需要被替换为算子`mindspore.ops.ResizeNearestNeighbor` |

## 使用示例

### 基于AST的脚本转换示例

若用户希望使用基于AST的方案进行脚本迁移，假设原PyTorch脚本路径为`/home/user/model.py`，希望将脚本输出至`/home/user/output`，转换报告输出至`/home/user/output/report`
，则脚本转换命令为：

```bash
mindconverter --in_file /home/user/model.py \
              --output /home/user/output \
              --report /home/user/output/report
```

转换报告中，对于未转换的代码行形式为如下，其中x,
y指明的是原PyTorch脚本中代码的行、列号。对于未成功转换的算子，可参考[MindSporeAPI映射查询功能](https://www.mindspore.cn/doc/note/zh-CN/master/index.html#operator_api)
手动对代码进行迁移。对于工具无法迁移的算子，会保留原脚本中的代码。

```text
line x:y: [UnConvert] 'operator' didn't convert. ...
```

转换报告示例如下所示：

```text
 [Start Convert]
 [Insert] 'import mindspore.ops.operations as P' is inserted to the converted file.
 line 1:0: [Convert] 'import torch' is converted to 'import mindspore'.
 ...
 line 157:23: [UnConvert] 'nn.AdaptiveAvgPool2d' didn't convert. Maybe could convert to mindspore.ops.operations.ReduceMean.
 ...
 [Convert Over]
```

对于部分未成功转换的算子，报告中会提供修改建议，如`line 157:23`，MindConverter建议将`torch.nn.AdaptiveAvgPool2d`
替换为`mindspore.ops.operations.ReduceMean`。

### 基于图结构的脚本生成示例

#### PyTorch模型脚本生成示例

若用户已将PyTorch模型保存为.pth格式，假设模型绝对路径为`/home/user/model.pth`，该模型期望的输入shape为(1, 3, 224, 224)
，原PyTorch脚本位于`/home/user/project/model_training`，希望将脚本输出至`/home/user/output`，转换报告输出至`/home/user/output/report`，则脚本生成命令为：

```bash
mindconverter --model_file /home/user/model.pth --shape 1,3,224,224 \
              --output /home/user/output \
              --report /home/user/output/report \
              --project_path /home/user/project/model_training
```

执行该命令，MindSpore代码文件、转换报告生成至相应目录。

基于图结构的脚本生成方案产生的转换报告格式与AST方案相同。然而，由于基于图结构方案属于生成式方法，转换过程中未参考原PyTorch脚本，因此生成的转换报告中涉及的代码行、列号均指生成后脚本。

另外对于未成功转换的算子，在代码中会相应的标识该节点输入、输出Tensor的shape（以`input_shape`, `output_shape`
标识），便于用户手动修改。以Reshape算子为例（暂不支持Reshape），将生成如下代码：

```python
class Classifier(nn.Cell):

    def __init__(self):
        super(Classifier, self).__init__()
        ...
        self.reshape = onnx.Reshape(input_shape=(1, 1280, 1, 1),
                                    output_shape=(1, 1280))
        ...

    def construct(self, x):
        ...
        # Suppose input of `reshape` is x.
        reshape_output = self.reshape(x)
        ...

```

通过`input_shape`、`output_shape`参数，用户可以十分便捷地完成算子替换，替换结果如下：

```python
from mindspore.ops import operations as P

...


class Classifier(nn.Cell):

    def __init__(self):
        super(Classifier, self).__init__()
        ...
        self.reshape = P.Reshape(input_shape=(1, 1280, 1, 1),
                                 output_shape=(1, 1280))
        ...

    def construct(self, x):
        ...
        # Suppose input of `reshape` is x.
        reshape_output = self.reshape(x, (1, 1280))
        ...

```

> 其中`--output`与`--report`参数可省略，若省略，该命令将在当前工作目录（Working directory）下自动创建`output`目录，将生成的脚本、转换报告输出至该目录。

#### TensorFlow模型脚本生成示例

使用TensorFlow模型脚本迁移，需要先将TensorFlow模型导出为pb格式，并且获取模型输入节点、输出节点名称。TensorFlow pb模型导出可参考[TensorFlow Pb模型导出](#tensorflow-pb模型导出)
。

假设输入节点名称为`input_1:0`、输出节点名称为`predictions/Softmax:0`，模型输入样本尺寸为`1,224,224,3`，则可使用如下命令进行脚本生成：

```bash
mindconverter --model_file /home/user/xxx/frozen_model.pb --shape 1,224,224,3 \
              --input_nodes input_1:0 \
              --output_nodes predictions/Softmax:0 \
              --output /home/user/output \
              --report /home/user/output/report
```

执行该命令，MindSpore代码文件、转换报告生成至相应目录。

由于基于图结构方案属于生成式方法，转换过程中未参考原TensorFlow脚本，因此生成的转换报告中涉及的代码行、列号均指生成后脚本。

另外，对于未成功转换的算子，在代码中会相应的标识该节点输入、输出Tensor的shape（以`input_shape`、`output_shape`标识），便于用户手动修改，示例见**PyTorch模型脚本生成示例**。

## 注意事项

1. PyTorch、TensorFlow不作为MindInsight明确声明的依赖库。若想使用基于图结构的脚本生成工具，需要用户手动安装与生成PyTorch模型版本一致的PyTorch库（MindConverter推荐使用PyTorch 1.4.0进行脚本生成），或TensorFlow；
2. 脚本转换工具本质上为算子驱动，对于MindConverter未维护的PyTorch或ONNX算子与MindSpore算子映射，将会出现相应的算子无法转换的问题，对于该类算子，用户可手动修改，或基于MindConverter实现映射关系，向MindInsight仓库贡献。
3. MindConverter仅保证转换后模型脚本在输入数据尺寸与`--shape`一致的情况下，可达到无需人工修改或少量修改（`--shape`中batch size维度不受限）。

## AST方案不支持场景

### 场景1

部分类和方法目前无法转换：

1. 使用`torch.Tensor`的`shape`，`ndim`和`dtype`成员；
2. `torch.nn.AdaptiveXXXPoolXd`和`torch.nn.functional.adaptive_XXX_poolXd()`；
3. `torch.nn.functional.Dropout`；
4. `torch.unsqueeze()`和`torch.Tensor.unsqueeze()`；
5. `torch.chunk()`和`torch.Tensor.chunk()`。

### 场景2

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

## 三方库依赖

用户在使用MindConverter时，下列三方库未在MindInsight依赖列表（requirements.txt）中声明。用户除安装可满足导出的Pb模型加载、训练、推理的TensorFlow版本外，还需要安装（pip
install）如下依赖库（PyTorch模型脚本转MindSpore的用户无需安装tf2onnx）：

```text
onnx>=1.8.0
tf2onnx>=1.7.1
onnxruntime>=1.5.2
```

## 常见问题

Q1. `terminate called after throwing an instance of 'std::system_error', what(): Resource temporarily unavailable, Aborted (core dumped)`:

> 答: 该问题由TensorFlow导致。脚本转换时，需要通过TensorFlow库加载TensorFlow的模型文件，此时TensorFlow会申请相关资源进行初始化，若申请资源失败（可能由于系统进程数超过Linux最大进程数限制），TensorFlow C/C++层会出现Core Dumped问题。详细信息请参考TensorFlow官方ISSUE，如下ISSUE仅供参考：[TF ISSUE 14885](https://github.com/tensorflow/tensorflow/issues/14885), [TF ISSUE 37449](https://github.com/tensorflow/tensorflow/issues/37449)

Q2. MindConverter是否可以在ARM平台运行？

> 答：MindConverter同时支持X86、ARM平台，若在ARM平台运行需要用户自行安装模型所需的依赖包和运行环境。

Q3. PyTorch模型转换时为什么提示`Error detail: [NodeInputMissing] ...`?

> 答：对于PyTorch模型，若网络中存在`torch.nn.functional.xxx`, `torch.xxx`, `torch.Tensor.xxx`层算子，可能存在节点解析失败的情况，需要用户手动替换为torch.nn层算子。

## 附录

### TensorFlow Pb模型导出

使用Keras构建模型的用户，可尝试如下方法进行导出。

对于TensorFlow 1.15.x版本：

```python
import tensorflow as tf
from tensorflow.python.framework import graph_io
from tensorflow.python.keras.applications.inception_v3 import InceptionV3


def freeze_graph(graph, session, output_nodes, output_folder: str):
    """
    Freeze graph for tf 1.x.x.

    Args:
        graph (tf.Graph): Graph instance.
        session (tf.Session): Session instance.
        output_nodes (list): Output nodes name.
        output_folder (str): Output folder path for frozen model.

    """
    with graph.as_default():
        graphdef_inf = tf.graph_util.remove_training_nodes(graph.as_graph_def())
        graphdef_frozen = tf.graph_util.convert_variables_to_constants(session, graphdef_inf, output_nodes)
        graph_io.write_graph(graphdef_frozen, output_folder, "frozen_model.pb", as_text=False)


tf.keras.backend.set_learning_phase(0)

keras_model = InceptionV3()
session = tf.keras.backend.get_session()

INPUT_NODES = [ipt.op.name for ipt in keras_model.inputs]
OUTPUT_NODES = [opt.op.name for opt in keras_model.outputs]
freeze_graph(session.graph, session, OUTPUT_NODES, "/home/user/xxx")
print(f"Input nodes name: {INPUT_NODES}, output nodes name: {OUTPUT_NODES}")
```

对于TensorFlow 2.x.x版本：

```python
import tensorflow as tf
from tensorflow.python.framework.convert_to_constants import convert_variables_to_constants_v2


def convert_to_froze_graph(keras_model: tf.python.keras.models.Model, model_name: str,
                           output_folder: str):
    """
    Export keras model to frozen model.

    Args:
        keras_model (tensorflow.python.keras.models.Model):
        model_name (str): Model name for the file name.
        output_folder (str): Output folder for saving model.

    """
    full_model = tf.function(lambda x: keras_model(x))
    full_model = full_model.get_concrete_function(
        tf.TensorSpec(keras_model.inputs[0].shape, keras_model.inputs[0].dtype)
    )

    frozen_func = convert_variables_to_constants_v2(full_model)
    frozen_func.graph.as_graph_def()

    print(f"Model inputs: {frozen_func.inputs}")
    print(f"Model outputs: {frozen_func.outputs}")

    tf.io.write_graph(graph_or_graph_def=frozen_func.graph,
                      logdir=output_folder,
                      name=model_name,
                      as_text=False)
```

### MindConverter错误码速查表

|       异常声明       | 异常描述                       | 异常代码 | 常见原因                                                     |
| :----------------------------: | :------: | :----------------------------------------------------------- | ----------------------- |
| MindConverterException | MindConverter异常基类          |   NAN    | MindConverter异常基类。                                      |
|    BaseConverterError    | 未知错误引起的转换失败         | 0000000  | 程序运行中出现未知错误，请打开MindInsight log文件（默认位于`~/mindinsight/log/mindconverter/`目录下）查看具体错误原因。 |
|       UnKnownModelError       | 识别网络模型对应的框架失败     | 0000001  | 通常为用户给定模型文件不符合TensorFlow或PyTorch标准。        |
| ParamMissingError | 缺少转换所需参数 | 0000002 | 通常为`--shape`, `--input_nodes` , `--output_nodes`缺失导致 |
|      GraphInitFailError      | 依据网络模型构建计算图失败     | 1000000  | 由1000001，1000002，1000003导致的计算图无法解析。                                                           |
|     ModelNotSupportError     | 解析.pth/.pb文件失败           | 1000001  | 给定的`--input_nodes`, `--output_nodes`与实际模型不符；或模型文件存在问题导致模型无法加载。 |
|     TfRuntimeError     | TensorFlow库执行出错           | 1000002  | TensorFlow启动申请所需资源失败导致无法正常启动，请检查系统资源（进程数、内存、显存占用、CPU占用）是否充足。 |
| ModelLoadingError | 模型加载失败                   | 1000003  | 可能由于用户给定网络输入尺寸错误导致模型无法加载。           |
| RuntimeIntegrityError | 三方依赖库不完整 | 1000004 | MindConverter运行时所需的三方依赖库未安装。 |
| TreeCreateFailError | 依据计算图构建模型树失败       | 2000000  | Tree用于生成最终代码结构，通常由于PyTorch网络中存在`torch.nn.functional.xxx`, `torch.xxx`, `torch.Tensor.xxx`算子导致。 |
| NodeInputMissingError | 网络节点输入信息丢失           | 2000001  | 节点的输入信息丢失。                                                            |
| TreeNodeInsertError | 树节点构建失败                 | 2000002  | 由于scope name错误，无法找到该节点的父节点。                                                             |
|   SourceFilesSaveError   | 生成和保存转换后的脚本文件失败 | 3000000  | 由3000001，3000002，3000003导致的脚本生成保存失败。                                                             |
| NodeInputTypeNotSupportError | 网络节点输入类型未知           | 3000001  | 映射关系中设置节点输入类型错误。                                                             |
| ScriptGenerationError | 转换脚本生成失败               | 3000002  | 空间不足；生成的脚本不符合PEP-8规范；`--output`目录下已有同名文件存在                                   |
| ReportGenerationError | 转换报告生成失败               | 3000003  | 空间不足；脚本中没有需要转换的算子；`--report`目录下已有同名文件存在。              |
|      GeneratorError      | 代码生成失败                   | 4000000  |由4000001至4000004引发的代码生成模块错误                                                |
| NodeLoadingError | 节点读取失败                   | 4000001  |转换后的节点缺少必要参数                                                                |
| NodeArgsTranslationError | 节点参数转换失败          | 4000002  |转换后的节点参数信息不正确                                                              |
| ModuleBuildError | 模块搭建失败                   | 4000003  |转换后的节点信息不正确，与模块信息冲突，导致模块生成失败                                   |
| CodeGenerationError | 代码生成失败                   | 4000004  |转换后的节点信息前后矛盾，生成过程产生冲突                                               |
|  SubGraphSearchingError  | 子图模式挖掘失败               | 5000000  | 通常由于模型生成对应的拓扑序错误导致。                       |

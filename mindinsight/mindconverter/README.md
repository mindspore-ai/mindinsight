# MindConverter tutorial

[查看中文](./README_CN.md)

<!-- TOC -->

- [MindConverter tutorial](#mindconverter-tutorial)
    - [Overview](#overview)
    - [Installation](#installation)
    - [Usage](#usage)
        - [PyTorch Model Scripts Migration](#pytorch-model-scripts-migration)
        - [TensorFlow Model Scripts Migration](#tensorflow-model-scripts-migration)
    - [Scenario](#scenario)
    - [Example](#example)
        - [AST-Based Conversion](#ast-based-conversion)
        - [Graph-Based Conversion](#graph-based-conversion)
            - [PyTorch Model Scripts Conversion](#pytorch-model-scripts-conversion)
            - [TensorFlow Model Scripts Conversion](#tensorflow-model-scripts-conversion)
    - [Caution](#caution)
    - [Unsupported situation of AST mode](#unsupported-situation-of-ast-mode)
        - [Situation1](#situation1)
        - [Situation2](#situation2)
    - [Requirements](#requirements)
    - [Frequently asked questions](#frequently-asked-questions)
    - [Appendix](#appendix)
        - [Tensorflow Pb Model Exporting](#tensorflow-pb-model-exporting)
        - [MindConverter Error Code Definition](#mindconverter-error-code-definition)

<!-- /TOC -->

## Overview

MindConverter is a migration tool to transform the model scripts from PyTorch or TensorFlow to MindSpore. Users can migrate their PyTorch or TensorFlow models to MindSpore rapidly with minor changes according to the conversion report.

## Installation

MindConverter is a submodule in MindInsight. Please follow the [Guide](https://www.mindspore.cn/install/en) here to install MindInsight.

## Usage

MindConverter currently only provides command-line interface. Here is the manual page.

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

### PyTorch Model Scripts Migration

#### MindConverter Provides Two Modes for PyTorch：

1. **Abstract Syntax Tree (AST) based conversion**: Use the argument `--in_file` will enable the AST mode.
2. **Computational Graph based conversion**: Use `--model_file` and `--shape` arguments will enable the Graph mode.

> The AST mode will be enabled, if both `--in_file` and `--model_file` are specified.

For the Graph mode, `--shape` is mandatory.

For the AST mode, `--shape` is ignored.

`--output` and `--report` is optional. MindConverter creates an `output` folder under the current working directory, and outputs generated scripts and conversion reports to it.  

Please note that your original PyTorch project is included in the module search path (PYTHONPATH). Use the python interpreter and test your module can be successfully loaded by `import` command. Use `--project_path` instead if your project is not in the PYTHONPATH to ensure MindConverter can load it.

> Assume the project is located at `/home/user/project/model_training`, users can use this command to add the project to `PYTHONPATH` : `export PYTHONPATH=/home/user/project/model_training:$PYTHONPATH`  
> MindConverter needs the original PyTorch scripts because of the reverse serialization.

### TensorFlow Model Scripts Migration

**MindConverter provides computational graph based conversion for TensorFlow**: Transformation will be done given `--model_file`, `--shape`, `--input_nodes` and `--output_nodes`.

> AST mode is not supported for TensorFlow, only computational graph based mode is available.

## Scenario

MindConverter provides two modes for different migration demands.

1. Keep original scripts' structures, including variables, functions, and libraries.
2. Keep extra modifications as few as possible, or no modifications are required after conversion.

The AST mode is recommended for the first demand (AST mode is only supported for PyTorch). It parses and analyzes PyTorch scripts, then replace them with the MindSpore AST to generate codes. Theoretically, The AST mode supports any model script. However, the conversion may differ due to the coding style of original scripts.

For the second demand, the Graph mode is recommended. As the computational graph is a standard descriptive language, it is not affected by user's coding style. This mode may have more operators converted as long as these operators are supported by MindConverter.

Some typical image classification networks have been tested for the Graph mode. Note that:

> 1. Currently, the Graph mode does not support models with multiple inputs. Only models with a single input and single output are supported.
> 2. The Dropout operator will be lost after conversion because the inference mode is used to load the PyTorch or TensorFlow model. Manually re-implement is necessary.
> 3. The Graph-based mode will be continuously developed and optimized with further updates.

Supported models list (Models in below table have been tested based on PyTorch 1.4.0(TorchVision 0.5.0) and TensorFlow 1.15.0, X86 Ubuntu released version):

|  Supported Model | PyTorch Script | TensorFlow Script | Comment |
| :----: | :----: | :----: | :----: |
| ResNet18 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | / |  |
| ResNet34 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | / |  |
| ResNet50 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet.py) |  |
| ResNet50V2 | / | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet_v2.py) |  |
| ResNet101 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet.py) |  |
| ResNet101V2 | / | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet_v2.py) |  |
| ResNet152 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet.py) |  |
| ResNet152V2 | / | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet_v2.py) |  |
| Wide ResNet50 2 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | / | |
| Wide ResNet101 2 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | / | |
| VGG11/11BN | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | / |  |
| VGG13/13BN | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | / |  |
| VGG16 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/vgg16.py) |  |
| VGG16BN | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | / |  |
| VGG19 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/vgg19.py) |  |
| VGG19BN | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | / |  |
| AlexNet | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/alexnet.py) | / |  |
| GoogLeNet | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/googlenet.py) | / |  |
| Xception | / | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/xception.py) |  |
| InceptionV3 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/inception.py) | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/inception_v3.py) |  |
| InceptionResNetV2 | / | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/inception_resnet_v2.py) |  |
| MobileNetV1 | / | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/mobilenet.py) |  |
| MobileNetV2 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/mobilenet.py) | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/mobilenet_v2.py) |  |
| MNASNet | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/mnasnet.py) | / | |
| SqueezeNet | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/squeezenet.py) | / | |
| DenseNet121/169/201 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/densenet.py) | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/densenet.py) |  |
| DenseNet161 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/densenet.py) | / | |
| NASNetMobile/Large | / | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/nasnet.py) |  |
| EfficientNetB0~B7 | [Link](https://github.com/lukemelas/EfficientNet-PyTorch) | [TF1.5Link](https://github.com/tensorflow/tpu/tree/master/models/official/efficientnet) [TF2.3Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/efficientnet.py) |  |
| Unet | [Link](https://github.com/milesial/Pytorch-UNet) | [Link](https://github.com/zhixuhao/unet) | Due to Operator `mindspore.ops.ResizeBilinear` is not implemented on GPU device for now, operator `mindspore.ops.ResizeBilinear` should be replaced by operator `mindspore.ops.ResizeNearestNeighbor`, while running in GPU device |

## Example

### AST-Based Conversion

Assume the PyTorch script is located at `/home/user/model.py`, and outputs the transformed MindSpore script to `/home/user/output`, with the conversion report to `/home/user/output/report`. Use the following command:

```bash
mindconverter --in_file /home/user/model.py \
              --output /home/user/output \
              --report /home/user/output/report
```

In the conversion report, non-transformed code is listed as follows:

```text
line <row>:<col> [UnConvert] 'operator' didn't convert. ...
```

For non-transformed operators, the original code keeps. Please manually migrate them. [Click here](https://www.mindspore.cn/doc/note/en/master/index.html#operator_api) for more information about operator mapping.

Here is an example of the conversion report:

```text
 [Start Convert]
 [Insert] 'import mindspore.ops.operations as P' is inserted to the converted file.
 line 1:0: [Convert] 'import torch' is converted to 'import mindspore'.
 ...
 line 157:23: [UnConvert] 'nn.AdaptiveAvgPool2d' didn't convert. Maybe could convert to mindspore.ops.operations.ReduceMean.
 ...
 [Convert Over]
```

For non-transformed operators, suggestions are provided in the report. For instance, MindConverter suggests that replace `torch.nn.AdaptiveAvgPool2d` with `mindspore.ops.operations.ReduceMean`.

### Graph-Based Conversion

#### PyTorch Model Scripts Conversion

Assume the PyTorch model (.pth file) is located at `/home/user/model.pth`, with input shape (1, 3, 224, 224) and the original PyTorch script is at `/home/user/project/model_training`. Output the transformed MindSpore script to `/home/user/output`, with the conversion report to `/home/user/output/report`. Use the following command:

```bash
mindconverter --model_file /home/user/model.pth --shape 1,3,224,224 \
              --output /home/user/output \
              --report /home/user/output/report \
              --project_path /home/user/project/model_training
```

The Graph mode has the same conversion report as the AST mode. However, the line number and column number refer to the transformed scripts since no original scripts are used in the process.

In addition, input and output Tensor shape of unconverted operators shows explicitly (`input_shape` and `output_shape`) as comments in converted scripts to help further manual modifications. Here is an example of the `Reshape` operator (Not supported in current version):

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

It is convenient to replace the operators according to the `input_shape` and `output_shape` parameters. The replacement is like this:

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

> `--output` and `--report` are optional. MindConverter creates an `output` folder under the current working directory, and outputs generated scripts and conversion reports to it.

#### TensorFlow Model Scripts Conversion

To use TensorFlow model script migration, users need to export TensorFlow model to Pb format first, and obtain the model input node and output node name. For exporting pb model, please refer to [TensorFlow Pb model exporting](#tensorflow-pb-model-exporting).

Suppose the model is saved to `/home/user/xxx/frozen_model.pb`, corresponding input node name is `input_1:0`, output node name is `predictions/Softmax:0`, the input shape of model is `1,224,224,3`, the following command can be used to generate the script:

```bash
mindconverter --model_file /home/user/xxx/frozen_model.pb --shape 1,224,224,3 \
              --input_nodes input_1:0 \
              --output_nodes predictions/Softmax:0 \
              --output /home/user/output \
              --report /home/user/output/report
```

After executed MindSpore script, and report file can be found in corresponding directory.

Since the graph based scheme is a generative method, the original TensorFlow script is not referenced in the conversion process. Therefore, the code line and column numbers involved in the generated conversion report refer to the generated script.

In addition, for operators that are not converted successfully, the input and output shape of tensor of the node will be identified in the code by `input_shape` and `output_shape`. For example, please refer to the example in **PyTorch Model Scripts Conversion** section.

## Caution

1. PyTorch, TensorFlow are not an explicitly stated dependency libraries in MindInsight. The Graph conversion requires the consistent PyTorch or TensorFlow version as the model is trained. (MindConverter recommends PyTorch 1.4.0)
2. This script conversion tool relies on operators which supported by MindConverter and MindSpore. Unsupported operators may not be successfully mapped to MindSpore operators. You can manually edit, or implement the mapping based on MindConverter, and contribute to our MindInsight repository. We appreciate your support for the MindSpore community.
3. MindConverter can only guarantee that the converted model scripts require a minor revision or no revision when the inputs' shape fed to the generated model script are equal to the value of `--shape` (The batch size dimension is not limited).

## Unsupported situation of AST mode

### Situation1

Classes and functions that can't be converted:

1. The use of `.shape`, `.ndim` and `.dtype` member of `torch.Tensor`.
2. `torch.nn.AdaptiveXXXPoolXd` and `torch.nn.functional.adaptive_XXX_poolXd()`.
3. `torch.nn.functional.Dropout`.
4. `torch.unsqueeze()` and `torch.Tensor.unsqueeze()`.
5. `torch.chunk()` and `torch.Tensor.chunk()`.

### Situation2

Subclassing from the subclasses of nn.Module

e.g. (code snip from torchvision.models.mobilenet)

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

## Requirements

For users using MindConverter, in addition to install the TensorFlow that can satisfy the model loading, inference and training requirements, users also need to pip install the following third party package (tf2onnx is not required for users that convert PyTorch model definition script to MindSpore):

```text
onnx>=1.8.0
tf2onnx>=1.7.1
onnxruntime>=1.5.2
```

## Frequently asked questions

Q1. `terminate called after throwing an instance of 'std::system_error', what(): Resource temporarily unavailable, Aborted (core dumped)`:
> Answer: This problem is caused by TensorFlow. First step of conversion process is loading TensorFlow model into memory using TensorFlow module, and TensorFlow starts to apply for needed resource. When required resource is unavailable, such as exceeding max process number of Linux system limit, etc., TensorFlow will raise an error from its C/C++ layer. For more detail, please refer to TensorFlow official repository. There are some known issue for reference only:
[TF ISSUE 14885](https://github.com/tensorflow/tensorflow/issues/14885), [TF ISSUE 37449](https://github.com/tensorflow/tensorflow/issues/37449)

Q2. Can MindConverter run on ARM platform?
> Answer: MindConverter supports both x86 and ARM platform. Please ensure all required dependencies and environments installed in the ARM platform.

Q3. Why did I get message of `Error detail: [NodeInputMissing] ...` when converting PyTorch model?
> Answer: For PyTorch model, if operations in `torch.nn.functional.xxx`, `torch.xxx`, `torch.Tensor.xxx` were used, node parsing could be failed. It's better to replace those operations with `torch.nn.xxx`.

## Appendix

### TensorFlow Pb model exporting

If build model with Keras API, user can try the following methods.

For TensorFlow 1.15.x version:

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

For TensorFlow 2.x.x version:

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

### MindConverter Error Code Definition

|    Exception definition    |          Error description       | Error code |  Common causes                                                    |
| :--------------------------: | :----------------------------------------------------: | :------- | ------------------------------------------------------------ |
|    MindConverterException    |                MindConverter base error                | NAN      | MindConverter base error                                     |
|      BaseConverterError      |        Fail to convert because of unknown error        | 0000000  | Unknown error occurred during runtime, please see the detail in MindInsight log file (default path is `~/mindinsight/log/mindconverter/`) |
|      UnKnownModelError       |             Fail to recognize model format             | 0000001  | Generally, the given TensorFlow model or PyTorch model doesn't observe the standard |
| ParamMissingError | Fail to get required conversion params | 0000002 | Mainly caused by missing `--shape`, `--input_nodes`, `--output_nodes` |
|      GraphInitFailError      |         Fail to trace the computational graph          | 1000000  | Exception caused by 1000001~1000003                          |
|     ModelNotSupportError     |              Fail to parse .pth/.pb file               | 1000001  | Given `--input_nodes`, `--output_nodes don't  match the input model; Meanwhile, the model file can not be loaded also can cause this error. |
|        TfRuntimeError        |           Fail to initialize the TF runtime            | 1000002  | Resources required by TensorFlow are not available           |
|    ModelLoadingError     |                 Fail to load the model                 | 1000003  | Maybe cause by the wrong `--input_shape` value               |
|    RuntimeIntegrityError     |     Fail to locate required third party dependency     | 1000004  | Caused by required third party packages are not installed    |
|     TreeCreateFailError      |         Fail to create code hierarchical tree          | 2000000  | Mainly caused by usage of `torch.nn.functional.xxx`, `torch.xxx`, `torch.Tensor.xxx` in PyTorch |
|    NodeInputMissingError     |            Fail to get the input node info             | 2000001  | Fail to get input node info                                  |
|     TreeNodeInsertError      |                Fail to insert tree node                | 2000002  | Mainly caused by wrong scope name                            |
|     SourceFilesSaveError     |       Fail to generate or save converted script        | 3000000  | Exception caused by 3000001~3000003                          |
| NodeInputTypeNotSupportError | Fail to recognize the input type of converted operator | 3000001  | Wrong input type set in mapper                               |
|    ScriptGenerationError     |           Fail to generate converted script            | 3000002  | No left space on hard disk; Converted code is not legal; A file with the same name already exists in `--output` |
|    ReportGenerationError     |           Fail to generate converted script            | 3000003  | No left space on hard disk; No available operator to be converted;A file with the same name already exists in  `--report` |
|        GeneratorError        |                 Fail to generate code                  | 4000000  | Exception caused by 4000001~4000004                          |
|       NodeLoadingError       |             Fail to load node information              | 4000001  | Essential parameters are missing after conversion of a node  |
|   NodeArgsTranslationError   |         Fail to translate the node's argument          | 4000002  | Converted nodes have incorrect and conflicted information    |
|       ModuleBuildError       |             Fail to build module instance              | 4000003  | Converted nodes have incorrect and conflicted information with module |
|     CodeGenerationError      |          Fail to generate the code statement           | 4000004  | Converted nodes have inconsistent information                |
|    SubGraphSearchingError    |            Fail to find frequent sub-graph             | 5000000  | Generally, caused by IR graph topological order error      |

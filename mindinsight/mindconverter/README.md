# MindConverter tutorial

[查看中文](./README_CN.md)

<!-- TOC -->

- [MindConverter tutorial](#mindconverter-tutorial)
    - [Overview](#overview)
    - [Installation](#installation)
    - [Usage](#usage)
        - [PyTorch Model Scripts Migration](#pytorch-model-scripts-migration)
        - [TensorFlow Model Scripts Migration](#tensorflow-model-scripts-migration)
        - [ONNX Model File Migration](#onnx-model-file-migration)
    - [Scenario](#scenario)
    - [Example](#example)
        - [AST-Based Conversion](#ast-based-conversion)
        - [Graph-Based Conversion](#graph-based-conversion)
            - [TensorFlow Model Scripts Conversion](#tensorflow-model-scripts-conversion)
            - [ONNX Model File Conversion](#onnx-model-file-conversion)
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

MindConverter is a migration tool to transform the model scripts and weights from PyTorch, TensorFlow or ONNX to MindSpore. Users can migrate their PyTorch, TensorFlow or ONNX models to MindSpore rapidly with minor changes according to the conversion report.

## Installation

MindConverter is a submodule in MindInsight. Please follow the [Guide](https://www.mindspore.cn/install/en) here to install MindInsight.

## Usage

MindConverter currently only provides command-line interface. Here is the manual page.

```bash
usage: mindconverter [-h] [--version] [--in_file IN_FILE]
                     [--model_file MODEL_FILE] [--shape SHAPE [SHAPE ...]]
                     [--input_nodes INPUT_NODES [INPUT_NODES ...]]
                     [--output_nodes OUTPUT_NODES [OUTPUT_NODES ...]]
                     [--output OUTPUT] [--report REPORT]

optional arguments:
  -h, --help            show this help message and exit
  --version             show program version number and exit
  --in_file IN_FILE     Specify path for script file to use AST schema to do
                        script conversation.
  --model_file MODEL_FILE
                        Tensorflow(.pb) or ONNX(.onnx) model file path is
                        expected to do script generation based on graph
                        schema. When `--in_file` and `--model_file` are both
                        provided, use AST schema as default.
  --shape SHAPE [SHAPE ...]
                        Optional, expected input tensor shape of
                        `--model_file`. It is required when use graph based
                        schema. Both order and number should be consistent
                        with `--input_nodes`. Usage: --shape 1,512 1,512
  --input_nodes INPUT_NODES [INPUT_NODES ...]
                        Optional, input node(s) name of `--model_file`. It is
                        required when use graph based schema. Both order and
                        number should be consistent with `--shape`. Usage:
                        --input_nodes input_1:0 input_2:0
  --output_nodes OUTPUT_NODES [OUTPUT_NODES ...]
                        Optional, output node(s) name of `--model_file`. It is
                        required when use graph based schema. Usage:
                        --output_nodes output_1:0 output_2:0
  --output OUTPUT       Optional, specify path for converted script file
                        directory. Default output directory is `output` folder
                        in the current working directory.
  --report REPORT       Optional, specify report directory. Default is
                        converted script directory.
```

### PyTorch Model Scripts Migration

#### MindConverter Provides AST for PyTorch：

**Abstract Syntax Tree (AST) based conversion**: Use the argument `--in_file` will enable the AST mode.

> The AST mode will be enabled, if both `--in_file` and `--model_file` are specified.

`--output` and `--report` is optional. MindConverter creates an `output` folder under the current working directory, and outputs generated scripts to it.

> While computational graph based conversion is required, it is recommended to use ONNX file after converting PyTorch model scripts to ONNX file， and the tutorial is [PyTorch instruction](https://pytorch.org/docs/stable/onnx.html).

### TensorFlow Model Scripts Migration

**MindConverter provides computational graph based conversion for TensorFlow**: Transformation will be done given `--model_file`, `--shape`, `--input_nodes` and `--output_nodes`.

> AST mode is not supported for TensorFlow, only computational graph based mode is available.

If both `output` and `report` are not set, mindConverter creates an `output` folder under the current working directory, and outputs generated scripts, converted checkpoint file, weight map file and conversion reports to it.

### ONNX Model File Migration

**MindConverter provides computational graph based conversion for ONNX**: Transformation will be done given `--model_file`, `--shape`, `--input_nodes` and `--output_nodes`.

> AST mode is not supported for ONNX, only computational graph based mode is available.

If both `output` and `report` are not set, mindConverter creates an `output` folder under the current working directory, and outputs generated scripts, converted checkpoint file, weight map file and conversion reports to it.

## Scenario

MindConverter provides two modes for different migration demands.

1. Keep original scripts' structures, including variables, functions, and libraries.
2. Keep extra modifications as few as possible, or no modifications are required after conversion.

The AST mode is recommended for the first demand (AST mode is only supported for PyTorch). It parses and analyzes PyTorch scripts, then replace them with the MindSpore AST to generate codes. Theoretically, The AST mode supports any model script. However, the conversion may differ due to the coding style of original scripts.

For the second demand, the Graph mode is recommended. As the computational graph is a standard descriptive language, it is not affected by user's coding style. This mode may have more operators converted as long as these operators are supported by MindConverter.

Some typical image classification networks have been tested for the Graph mode. Note that:

> 1. The Dropout operator will be lost after conversion because the inference mode is used to load the ONNX or TensorFlow model. Manually re-implement is necessary.
> 2. The Graph-based mode will be continuously developed and optimized with further updates.

[Supported models list (Models in below table have been tested based on PyTorch 1.5.0 and TensorFlow 1.15.0, X86 Ubuntu released version)](./docs/supported_model_list.md).

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

#### TensorFlow Model Scripts Conversion

To use TensorFlow model script migration, users need to export TensorFlow model to Pb format first, and obtain the model input node and output node name. For exporting pb model, please refer to [TensorFlow Pb model exporting](#tensorflow-pb-model-exporting).

Suppose the input node name is `input_1:0`, output node name is `predictions/Softmax:0`, the input shape of model is `1,224,224,3` and the original TensorFlow model is at `/home/user/xxx/frozen_model.pb`. Output the transformed MindSpore script and MindSpore checkpoint file to `/home/user/output`, with the conversion report and weight map file to `/home/user/output/report`. Use the following command:

```bash
mindconverter --model_file /home/user/xxx/frozen_model.pb --shape 1,224,224,3 \
              --input_nodes input_1:0 \
              --output_nodes predictions/Softmax:0 \
              --output /home/user/output \
              --report /home/user/output/report
```

After executed, MindSpore script, MindSpore checkpoint file, weight map file and report file can be found in corresponding directory.

Since the graph based scheme is a generative method, the original TensorFlow script is not referenced in the conversion process. Therefore, the code line and column numbers involved in the generated conversion report refer to the generated script.

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

> `--output` and `--report` are optional. MindConverter creates an `output` folder under the current working directory, and outputs generated scripts, MindSpore checkpoint file, weight map file and conversion reports to it.

Here is an example of the weight map:

```json
{
    "resnet50": [
        {
            "converted_weight": {
                "name": "conv2d_0.weight",
                "shape": [
                    64,
                    3,
                    7,
                    7
                ],
                "data_type": "Float32"
            },
            "source_weight": {
                "name": "conv1.weight",
                "shape": [
                    64,
                    3,
                    7,
                    7
                ],
                "data_type": "float32"
            }
        }
    ]
}
```

Weight information in MindSpore (`converted_weight`) and that in source framework(`source_weight`) are saved in weight map separately.

#### ONNX Model File Conversion

To use ONNX model file migration, user needs to obtain the model input node and output node name from ONNX model. To get input node and output node name, [Netron](https://github.com/lutzroeder/netron) is recommended.

Suppose the model is saved to `/home/user/xxx/model.onnx`, corresponding input node name is `input_1:0`, output node name is `predictions/Softmax:0`, the input shape of model is `1,3,224,224`, the following command can be used to generate the script:

```bash
mindconverter --model_file /home/user/xxx/model.onnx --shape 1,3,224,224 \
              --input_nodes input_1:0 \
              --output_nodes predictions/Softmax:0 \
              --output /home/user/output \
              --report /home/user/output/report
```

After executed, MindSpore script, MindSpore checkpoint file, weight map file and report file can be found in corresponding directory.

Since the graph based scheme is a generative method, the original ONNX model is not referenced in the conversion process. Therefore, the code line and column numbers involved in the generated conversion report refer to the generated script.

In addition, for operators that are not converted successfully, the input and output shape of tensor of the node will be identified in the code by `input_shape` and `output_shape`. For example, please refer to the example in **TensorFlow Model Scripts Conversion** section.

## Caution

1. TensorFlow are not an explicitly stated dependency libraries in MindInsight. The Graph conversion requires the consistent TensorFlow version as the model is trained.
2. This script conversion tool relies on operators which supported by ONNX and MindSpore. Unsupported operators may not be successfully mapped to MindSpore operators. You can manually edit, or implement the mapping based on MindConverter, and contribute to our MindInsight repository. We appreciate your support for the MindSpore community.
3. MindConverter converts dynamic input shape to constant one based on `--shape` while using graph based scheme, as a result, it is required that inputs shape used to retrain or inference in MindSpore are the same as that used to convert using MindConverter. If inputs shape has changed, rerunning MindConverter with new `--shape` or fixing shape related parameters in old script manually is necessary.
4. MindSpore script and MindSpore checkpoint file are saved in the same file folder path, while report file and weight map are saved in the same one.
5. The security and consistency of the model file should be guaranteed by the user.

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

For users using MindConverter, in addition to install the TensorFlow that can satisfy the model loading, inference and training requirements, users also need to pip install the following third party package (tf2onnx is not required for users that convert ONNX model definition file to MindSpore):

```text
onnx>=1.8.0
tf2onnx>=1.7.1
onnxruntime>=1.5.2
onnxoptimizer>=0.1.2
```

For some models, if the onnx or tf2onnx error message appears during the conversion process, please try to upgrade the onnx, tf2onnx or onnxoptimizer in the environment to the latest version.

## Frequently asked questions

Q1. `terminate called after throwing an instance of 'std::system_error', what(): Resource temporarily unavailable, Aborted (core dumped)`:
> Answer: This problem is caused by TsorFlow. First step of conversion process is loading TensorFlow model into memory using TensorFlow module, and TensorFlow starts to apply for needed resource. When required resource is unavailable, such as exceeding max process number of Linux system limit, etc., TensorFlow will raise an error from its C/C++ layer. For more detail, please refer to TensorFlow official repository. There are some known issue for reference only:
[TF ISSUE 14885](https://github.com/tensorflow/tensorflow/issues/14885), [TF ISSUE 37449](https://github.com/tensorflow/tensorflow/issues/37449)

Q2. Can MindConverter run on ARM platform?
> Answer: MindConverter supports both x86 and ARM platform. Please ensure all required dependencies and environments installed in the ARM platform.

Q3. Why does the conversion process take a lot of time (more than 10 minutes), but the model is not so large?
> Answer: When converting, MindConverter needs to use protobuf to deserialize the model file. Please make sure that the protobuf installed in Python environment is implemented by C++ backend. The validation method is as follows. If the output is "python", you need to install Python protobuf implemented by C++ (download the protobuf source code, enter the "python" subdirectory in the source code, and use `python setup.py install --cpp_implementation` to install). If the output is "cpp" and the conversion process still takes a long time, please add environment variable `export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=cpp` before conversion.

```python
from google.protobuf.internal import api_implementation
print(api_implementation.Type())
```

## Appendix

### TensorFlow Pb model exporting

If build model with Keras API, user can refer to this [tutorial](./docs/tensorflow_model_exporting.md).

### MindConverter Error Code Definition

Error code defined in MindConverter, please refer to [LINK](./docs/error_code_definition.md).

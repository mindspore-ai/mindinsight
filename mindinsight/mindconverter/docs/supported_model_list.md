# Verified model list of MindConverter

[查看中文](./supported_model_list_cn.md)

Supported models list (Models in below table have been tested based on PyTorch 1.5.0 and TensorFlow 1.15.0, X86 Ubuntu
released version):

|  Supported Model | PyTorch Script | TensorFlow Script | Comment | PyTorch Weights Converted | TensorFlow Weights Converted |
| :----: | :----: | :----: | :----: | :----: | :----: |
| ResNet18 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | / |  | TESTED | / |
| ResNet34 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | / |  | TESTED | / |
| ResNet50 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet.py) |  | TESTED | TESTED |
| ResNet50V2 | / | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet_v2.py) |  | / | TESTED |
| ResNet101 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet.py) |  | UNTESTED | TESTED |
| ResNet101V2 | / | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet_v2.py) |  | / | TESTED |
| ResNet152 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet.py) |  | TESTED | TESTED |
| ResNet152V2 | / | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet_v2.py) |  | / | TESTED |
| Wide ResNet50 2 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | / | | TESTED | / |
| Wide ResNet101 2 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | / | | TESTED | / |
| VGG11/11BN | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | / |  | TESTED | / |
| VGG13/13BN | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | / |  | TESTED | / |
| VGG16 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/vgg16.py) |  | TESTED | TESTED |
| VGG16BN | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | / |  | TESTED | / |
| VGG19 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/vgg19.py) |  | TESTED | TESTED |
| VGG19BN | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | / |  | TESTED | / |
| AlexNet | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/alexnet.py) | / |  | TESTED | / |
| GoogLeNet | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/googlenet.py) | / |  | TESTED | / |
| Xception | / | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/xception.py) |  | / | TESTED |
| InceptionV3 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/inception.py) | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/inception_v3.py) |  | TESTED | TESTED |
| InceptionResNetV2 | / | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/inception_resnet_v2.py) |  | / | TESTED |
| MobileNetV1 | / | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/mobilenet.py) |  | / | TESTED |
| MobileNetV2 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/mobilenet.py) | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/mobilenet_v2.py) |  | TESTED | TESTED |
| MNASNet | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/mnasnet.py) | / | | mnasnet0_5:TESTED mnasnet0_75:UNTESTED mnasnet1_0:TESTED mnasnet1_3:UNTESTED | / |
| SqueezeNet | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/squeezenet.py) | / | | TESTED | / |
| DenseNet121/169/201 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/densenet.py) | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/densenet.py) |  | TESTED | TESTED |
| DenseNet161 | [Link](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/densenet.py) | / | | TESTED | / |
| NASNetMobile/Large | / | [Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/nasnet.py) |  | / | TESTED |
| EfficientNetB0~B7 | [Link](https://github.com/lukemelas/EfficientNet-PyTorch) | [TF1.15Link](https://github.com/tensorflow/tpu/tree/master/models/official/efficientnet) [TF2.3Link](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/efficientnet.py) |  | TESTED | TESTED(TF1.15) TESTED(TF2.3) |
| Unet | [Link](https://github.com/milesial/Pytorch-UNet) | [Link](https://github.com/zhixuhao/unet) | Due to Operator `mindspore.ops.ResizeBilinear` is not implemented on GPU device for now, operator `mindspore.ops.ResizeBilinear` should be replaced by operator `mindspore.ops.ResizeNearestNeighbor`, while running in GPU device | TESTED | TESTED |
| Bert | [Link](https://huggingface.co/bert-base-uncased) | [Link](https://github.com/google-research/bert) |  | TESTED | TESTED |

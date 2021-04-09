# MindConverter已验证的模型列表

[Switch to English version](./supported_model_list.md)

支持的模型列表（如下模型已基于x86 Ubuntu发行版，PyTorch 1.5.0以及TensorFlow 1.15.0测试通过）:

|  模型  | PyTorch脚本 | TensorFlow脚本 | 备注 | PyTorch权重迁移 | TensorFlow权重迁移 |
| :----: | :-----: | :----: | :----: | :----: | :----: |
| ResNet18 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | / |  | 已测试 | / |
| ResNet34 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | / |  | 已测试 | / |
| ResNet50 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet.py) |  | 已测试 | 已测试 |
| ResNet50V2 | / | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet_v2.py) |  | / | 已测试 |
| ResNet101 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet.py) |  | 未测试 | 已测试 |
| ResNet101V2 | / | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet_v2.py) |  | / | 已测试 |
| ResNet152 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet.py) |  | 已测试 | 已测试 |
| ResNet152V2 | / | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/resnet_v2.py) |  | / | 已测试 |
| Wide ResNet50 2 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | / | | 已测试 | / |
| Wide ResNet101 2 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/resnet.py) | / | | 已测试 | / |
| VGG11/11BN | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | / |  | 已测试 | / |
| VGG13/13BN | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | / |  | 已测试 | / |
| VGG16 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/vgg16.py) |  | 已测试 | 已测试 |
| VGG16BN | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | / |  | 已测试 | / |
| VGG19 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/vgg19.py) |  | 已测试 | 已测试 |
| VGG19BN | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/vgg.py) | / |  | 已测试 | / |
| AlexNet | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/alexnet.py) | / |  | 已测试 | / |
| GoogLeNet | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/googlenet.py) | / |  | 已测试 | / |
| Xception | / | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/xception.py) |  | / | 已测试 |
| InceptionV3 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/inception.py) | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/inception_v3.py) |  | 已测试 | 已测试 |
| InceptionResNetV2 | / | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/inception_resnet_v2.py) |  | / | 已测试 |
| MobileNetV1 | / | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/mobilenet.py) |  | / | 已测试 |
| MobileNetV2 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/mobilenet.py) | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/mobilenet_v2.py) |  | 已测试 | 已测试 |
| MNASNet | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/mnasnet.py) | / | | mnasnet0_5：已测试 mnasnet0_75：未测试 mnasnet1_0：已测试 mnasnet1_3：未测试  | / |
| SqueezeNet | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/squeezenet.py) | / | | 已测试 | / |
| DenseNet121/169/201 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/densenet.py) | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/densenet.py) |  | 已测试 | 已测试 |
| DenseNet161 | [脚本链接](https://github.com/pytorch/vision/blob/v0.5.0/torchvision/models/densenet.py) | / | | 已测试 | / |
| NASNetMobile/Large | / | [脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/nasnet.py) |  | / | 已测试 |
| EfficientNetB0~B7 | [脚本链接](https://github.com/lukemelas/EfficientNet-PyTorch) | [TF1.15<br />脚本链接](https://github.com/tensorflow/tpu/tree/master/models/official/efficientnet) <br />[TF2.3<br />脚本链接](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/keras/applications/efficientnet.py) |  | 已测试 | 已测试（TF1.15） 已测试（TF2.3）|
| Unet | [脚本链接](https://github.com/milesial/Pytorch-UNet) | [脚本链接](https://github.com/zhixuhao/unet) | 由于算子`mindspore.ops.ResizeBilinear`在GPU上暂未实现，所以当运行在GPU设备上时，算子`mindspore.ops.ResizeBilinear`需要被替换为算子`mindspore.ops.ResizeNearestNeighbor` | 已测试 | 已测试 |
| Bert | [脚本链接](https://huggingface.co/bert-base-uncased) | [脚本链接](https://github.com/google-research/bert) |  | 已测试 | 已测试 |

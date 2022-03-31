mindconverter
=============

.. py:function:: mindconverter.pytorch2mindspore(model, dummy_inputs, output_dir=None)

    实现PyTorch模型到MindSpore模型的快速等价迁移。

    该方法可以将已经加载预训练权重信息的PyTorch模型实例，转换为等价的MindSpore模型脚本以及可加载的权重文件。

    **参数：**

    - **model** (torch.nn.Module)：加载权重的PyTorch模型实例。
    - **dummy_inputs** (tuple<torch.tensor>)：由PyTorch模型的输入张量组成的元组。该元组中的张量数量，以及每个张量的Shape信息和DType信息和PyTorch模型所需的输入保持一致。
    - **output_dir** (str)：生成的文件和转换报告的保存路径。如果没有设置，则默认使用 `./output` 目录进行保存。默认值：None。

    **异常：**

    - **BaseConverterError：** 由于不明确异常导致的转换异常。具体信息可在 `mindconverter.log` 中查看。
    - **GraphInitFailError：** 生成PyTorch计算图时发生异常。
    - **FileSaveError：** 保存转换生成的文件时发生异常。
    - **GeneratorError：** 生成MindSpore网络脚本代码时发生异常。
    - **SubGraphSearchingError：** 搜索重复子图时发生异常。
# MindConverter错误码速查表

[Switch to English version](./error_code_definition.md)

|       异常声明       | 异常描述                       | 异常代码 | 常见原因                   |
| :----------------------------: | :------: | :--------------- | ----------------------- |
| MindConverterException | MindConverter异常基类          | NAN    | MindConverter异常基类                                      |
|    BaseConverterError    | 未知错误引起的转换失败         | 0000000    | 程序运行中出现未知错误，请打开MindInsight log文件（默认位于`~/mindinsight/log/mindconverter/`目录下）查看具体错误原因 |
|       UnKnownModelError       | 识别网络模型对应的框架失败     | 0000001   | 通常为用户给定模型文件不符合TensorFlow或PyTorch标准        |
| ParamMissingError | 缺少转换所需参数 | 0000002 | 通常为`--shape`, `--input_nodes` , `--output_nodes`缺失导致 |
|      GraphInitFailError      | 依据网络模型构建计算图失败     | 1000000  | 由1000001，1000002，1000003导致的计算图无法解析                                                           |
|     ModelLoadingError     | 模型加载失败           | 1000001  | 给定的`--input_nodes`, `--output_nodes`, `--shape`与实际模型不符；<br />或模型文件存在问题导致模型无法加载 |
|     TfRuntimeError     | TensorFlow库执行出错           | 1000002  | TensorFlow启动申请所需资源失败导致无法正常启动，<br />请检查系统资源（进程数、内存、显存占用、CPU占用）是否充足 |
| RuntimeIntegrityError | 三方依赖库不完整 | 1000003 | MindConverter运行时所需的三方依赖库未安装 |
| TreeCreateFailError | 依据计算图构建模型树失败       | 2000000  | Tree用于生成最终代码结构，<br />通常由于PyTorch网络中存在`torch.nn.functional.xxx`, `torch.xxx`, `torch.Tensor.xxx`算子导致 |
| NodeInputMissingError | 网络节点输入信息丢失           | 2000001  | 节点的输入信息丢失                                                            |
| TreeNodeInsertError | 树节点构建失败                 | 2000002  | 由于scope name错误，无法找到该节点的父节点                                                            |
|   SourceFilesSaveError   | 生成和保存转换后的脚本文件失败 | 3000000  | 由300000至3000005导致的脚本生成保存失败            |
| NodeInputTypeNotSupportError | 网络节点输入类型未知           | 3000001  | 映射关系中设置节点输入类型错误                                                           |
| ScriptGenerationError | 转换脚本生成失败               | 3000002  | 空间不足；生成的脚本不符合PEP-8规范；`--output`目录下已有同名文件存在                                   |
| ReportGenerationError | 转换报告生成失败               | 3000003  | 空间不足；脚本中没有需要转换的算子；`--report`目录下已有同名文件存在              |
| CheckPointGenerationError | 转换权重生成失败 | 3000004 | 空间不足；`--output`目录下已有同名文件存在 |
| WeightMapGenerationError | 权重映射表生成失败 | 3000005 | 空间不足；`--output`目录下已有同名文件存在 |
|      GeneratorError      | 代码生成失败                   | 4000000  |由4000001至4000004引发的代码生成模块错误                                                |
| NodeLoadingError | 节点读取失败                   | 4000001  |转换后的节点缺少必要参数                                                                |
| NodeArgsTranslationError | 节点参数转换失败          | 4000002  |转换后的节点参数信息不正确                                                              |
| ModuleBuildError | 模块搭建失败                   | 4000003  |转换后的节点信息不正确，与模块信息冲突，导致模块生成失败                                   |
| CodeGenerationError | 代码生成失败                   | 4000004  |转换后的节点信息前后矛盾，生成过程产生冲突                                               |
|  SubGraphSearchingError  | 子图模式挖掘失败               | 5000000  | 通常由于模型生成对应的拓扑序错误导致                       |

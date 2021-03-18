# MindConverter Error Code Definition

[查看中文](./error_code_definition_cn.md)

|    Exception definition    |          Error description       | Error code |  Common causes                                                    |
| :--------------------------: | :----------------------------------------------------: | :------- | ------------------------------------------------------------ |
|    MindConverterException    |                MindConverter base error                | NAN      | MindConverter base error                                     |
|      BaseConverterError      |        Fail to convert because of unknown error        | 0000000  | Unknown error occurred during runtime, please see the detail in MindInsight log file (default path is `~/mindinsight/log/mindconverter/`) |
|      UnKnownModelError       |             Fail to recognize model format             | 0000001  | Generally, the given TensorFlow model or PyTorch model doesn't observe the standard |
| ParamMissingError | Fail to get required conversion params | 0000002 | Mainly caused by missing `--shape`, `--input_nodes`, `--output_nodes` |
|      GraphInitFailError      |         Fail to trace the computational graph          | 1000000  | Exception caused by 1000001~1000003                          |
|     ModelLoadingError     |              Fail to load the model              | 1000001  | Given `--input_nodes`, `--output_nodes`, `--shape` don't  match the input model; Meanwhile, the model file can not be loaded also can cause this error |
|        TfRuntimeError        |           Fail to initialize the TF runtime            | 1000002  | Resources required by TensorFlow are not available           |
|    RuntimeIntegrityError     |     Fail to locate required third party dependency     | 1000003  | Caused by required third party packages are not installed    |
|     TreeCreateFailError      |         Fail to create code hierarchical tree          | 2000000  | Mainly caused by usage of `torch.nn.functional.xxx`, `torch.xxx`, `torch.Tensor.xxx` in PyTorch |
|    NodeInputMissingError     |            Fail to get the input node info             | 2000001  | Fail to get input node info                                  |
|     TreeNodeInsertError      |                Fail to insert tree node                | 2000002  | Mainly caused by wrong scope name                            |
|     SourceFilesSaveError     |       Fail to generate or save converted script        | 3000000  | Exception caused by 3000001~3000005                         |
| NodeInputTypeNotSupportError | Fail to recognize the input type of converted operator | 3000001  | Wrong input type set in mapper                               |
|    ScriptGenerationError     |           Fail to generate converted script            | 3000002  | No left space on hard disk; Converted code is not legal; A file with the same name already exists in `--output` |
|    ReportGenerationError     |           Fail to generate converted script            | 3000003  | No left space on hard disk; No available operator to be converted;A file with the same name already exists in  `--report` |
|   CheckPointGenerationError  |         Fail to generate converted weight file         | 3000004  | No left space on hard dist; A file with the same name already exists in `--output` |
|    WeightMapGenerationError  |            Fail to generate weight map file            | 3000005  | No left space on hard dist; A file with the same name already exists in `--output` |
|        GeneratorError        |                 Fail to generate code                  | 4000000  | Exception caused by 4000001~4000004                          |
|       NodeLoadingError       |             Fail to load node information              | 4000001  | Essential parameters are missing after conversion of a node  |
|   NodeArgsTranslationError   |         Fail to translate the node's argument          | 4000002  | Converted nodes have incorrect and conflicted information    |
|       ModuleBuildError       |             Fail to build module instance              | 4000003  | Converted nodes have incorrect and conflicted information with module |
|     CodeGenerationError      |          Fail to generate the code statement           | 4000004  | Converted nodes have inconsistent information                |
|    SubGraphSearchingError    |            Fail to find frequent sub-graph             | 5000000  | Generally, caused by IR graph topological order error      |

# MindConverter Error Code Definition

[查看中文](./error_code_definition_cn.md)

|    Exception definition    |          Error description       | Error code |  Common causes                                                    |
| :--------------------------: | :----------------------------------------------------: | :------- | ------------------------------------------------------------ |
|    MindConverterException    |                MindConverter base error                | NAN      | MindConverter base error                                     |
|      BaseConverterError      |        Fail to convert because of unknown error        | 0000000  | Unknown error occurred during runtime, please see the detail in MindInsight log file (default path is `~/mindinsight/log/mindconverter/`) |
|      UnKnownModelError       |             Fail to recognize model format             | 0000001  | Generally, the given TensorFlow model or PyTorch model doesn't observe the standard |
| ParamMissingError | Fail to get required conversion params | 0000002 | Mainly caused by missing `--shape`, `--input_nodes`, `--output_nodes` |
| BadParamError | Fail to get correct conversion params | 0000003 | Mainly caused by error `--shape`, `--input_nodes`, `--output_nodes` |
|      GraphInitFailError      |         Fail to trace the computational graph          | 1000000  | Exception caused by 1000001~1000003                          |
|     ModelLoadingError     |              Fail to load the model              | 1000001  | Given `--input_nodes`, `--output_nodes`, `--shape` don't  match the input model; Meanwhile, the model file can not be loaded also can cause this error |
|        TfRuntimeError        |           Fail to initialize the TF runtime            | 1000002  | Resources required by TensorFlow are not available           |
|    RuntimeIntegrityError     |     Fail to locate required third party dependency     | 1000003  | Caused by required third party packages are not installed    |
|     FileSaveError     |       Fail to generate or save converted script        | 2000000  | Exception caused by 2000001~2000005                         |
| NodeInputTypeNotSupportError | Fail to recognize the input type of converted operator | 2000001  | Wrong input type set in mapper                               |
|    ScriptGenerationError     |           Fail to generate converted script            | 2000002  | No left space on hard disk; Converted code is not legal; A file with the same name already exists in `--output` |
|    ReportGenerationError     |           Fail to generate converted script            | 2000003  | No left space on hard disk; No available operator to be converted;A file with the same name already exists in  `--report` |
|   CheckPointGenerationError  |         Fail to generate converted weight file         | 2000004  | No left space on hard disk; A file with the same name already exists in `--output` |
|    WeightMapGenerationError  |            Fail to generate weight map file            | 2000005  | No left space on hard disk; A file with the same name already exists in `--output` |
|    OnnxModelSaveError  |            Fail to save model            | 2000006  | No left space on hard disk; No permission |
|        GeneratorError        |                 Fail to generate code                  | 3000000  | Exception caused by 3000001~3000004                          |
|       NodeLoadingError       |             Fail to load node information              | 3000001  | Essential parameters are missing after conversion of a node  |
|   NodeArgsTranslationError   |         Fail to translate the node's argument          | 3000002  | Converted nodes have incorrect and conflicted information    |
|       ModuleBuildError       |             Fail to build module instance              | 3000003  | Converted nodes have incorrect and conflicted information with module |
|     CodeGenerationError      |          Fail to generate the code statement           | 3000004  | Converted nodes have inconsistent information                |
|    SubGraphSearchingError    |            Fail to find frequent sub-graph             | 4000000  | Generally, caused by IR graph topological order error      |
| PatternConflictError | Sub-graph pattern register conflict error | 4000001 | Sub-graph pattern name has already been registered |
| PatternInvalidError | Sub-graph pattern or name is invalid | 4000002 | Sub-graph pattern or name is invalid |
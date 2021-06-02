# DumpParser介绍

[View English](./README.md)

## 接口定义

### mindinsight.parser.dump.DumpParser

Dump数据解析器。

参数:

- dump_dir (str) - Dump数据目录路径。

#### convert_all_data_to_host()

批量转换异步dump数据为host侧格式。

返回值:

- list, 转换失败的tensor文件信息。

#### get_tensor_files(qs, use_regex=False, rank_ids=None, iterations=None)

查询tensor文件信息。

参数:

- qs (str): 查询关键字。
- use_regex (bool): 标识查询关键字是否为正则表达式。
- rank_ids (list): 选择指定的rank_ids。
- iterations (list): 选择指定的迭代。

返回值:

- dict, tensor文件路径信息, 结构为: `{[op_full_name]: OpPathManager}`. 调用`OpPathManager.to_dict()`, 返回结果结构如下:

```json
{'rank_[rank_id]':
    {[iteration_id]:
        {
            'input': list[file_path],
            'output': list[file_path]
        }
    }
}
```

### export_xlsx(output_dir=None)

导出excel文件。

参数:

- output_dir (str): excel文件的输出目录路径。默认值为None。

返回值:

- str, excel文件路径。

## 使用举例

```python
from mindinsight.parser.dump import DumpParser

# 实例化DumpParser
dump_dir = '/path/to/dump/dir'
parser = DumpParser(dump_dir)

# 批量转换异步dump数据为host侧格式
parser.convert_all_data_to_host()

# 根据关键词信息匹配算子节点，并返回算子的关联tensor文件信息
qs = 'BatchNorm'
rank_ids = [1, 2]
tensor_mapping = parser.get_tensor_files(qs, rank_ids=rank_ids)

# 导出计算图节点的汇总报告
output_dir = '/path/to/output/dir'
parser.export_xlsx(output_dir=output_dir)
```

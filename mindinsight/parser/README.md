# DumpParser Introduction

[查看中文](./README_CN.md)

## API

### mindinsight.parser.dump.DumpParser

Dump Parser.

Args:

- dump_dir (str) - Dump directory path.

#### convert_all_data_to_host()

Convert all data to host format.

Returns:

- list, failed tensors.

#### get_tensor_files(qs, use_regex=False, rank_ids=None, iterations=None)

Get tensor files.

Args:

- qs (str): Query string.
- use_regex (bool): Indicates if query is regex.
- rank_ids (list): Selected rank IDs.
- iterations (list): Selected iterations.

Returns:

- dict, paths of tensor files. The format is like: `{[op_full_name]: OpPathManager}`. Call `OpPathManager.to_dict()`, the result is format like:

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

Export to excel file.

Args:

- output_dir (str): Output directory to save the excel file. Default is None.

Returns:

- str, excel file path.

## Usage

```python
from mindinsight.parser.dump import DumpParser

# initialize DumpParser
dump_dir = '/path/to/dump/dir'
parser = DumpParser(dump_dir)

# convert async dump files into host format
parser.convert_all_data_to_host()

# filter operator nodes with keywords and return related tensor files info
qs = 'BatchNorm'
rank_ids = [1, 2]
tensor_mapping = parser.get_tensor_files(qs, rank_ids=rank_ids)

# export graph node info to report file with excel format
output_dir = '/path/to/output/dir'
parser.export_xlsx(output_dir=output_dir)
```

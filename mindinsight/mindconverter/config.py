# Copyright 2020 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless REQUIRED by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""API config"""
import ast
from collections import OrderedDict
from importlib import import_module
import json
import os

import pasta

from mindinsight.mindconverter.common.log import logger
from mindinsight.mindconverter.common.exceptions import CodeSyntaxError

REQUIRED = 'REQUIRED'
UNREQUIRED = 'UNREQUIRED'
FUNC_MODULE = 'mindinsight.mindconverter.funcs'


class APIPt:
    """Base API for args parse, and API for one frame."""

    def __init__(self, name: str, params: dict):
        self.name = name
        self.params = OrderedDict()

        for k, value in params.items():
            self.params[k] = self.to_str(value)

    @staticmethod
    def to_str(value):
        """
        Trans value to str.

        Args:
            value (Union[str,Number,int]): The value to convert.

        Returns:
            str, str type of value.
        """
        if value is REQUIRED:
            return value
        if isinstance(value, str):
            return "'{}'".format(value)
        return str(value)

    def parse_args(self, call_name: str, args_str: str):
        """
        Parse call_name and args_str.

        Args:
            call_name (str): str of the call function, etc.
            args_str (str): str of args for function, which starts with '(' and end with ')'.

        Returns:
            OrderedDict, all args parsed.

        Raises:
            ValueError: If can not use ast to parse or the required parse node not type of ast.Call,
            or the given args_str not valid.
        """
        # expr is REQUIRED to meet (**) format
        if not (len(args_str) >= 2 and args_str[0] == "(" and args_str.strip()[-1] == ")"):
            raise ValueError('"{}" is think as args string, it should start with "(" and end with ")" without '
                             'considering spaces'.format(args_str))
        try:
            ast_node = ast.parse("whatever_call_name" + args_str)
            call_node = ast_node.body[0].value
        except SyntaxError as parse_error:
            raise CodeSyntaxError("can't parse code:\n{}".format(args_str)) from parse_error

        # regard all actual parameter as one parameter
        if len(self.params) == 1:
            k = list(self.params.keys())[0]
            if k.startswith('*'):
                value = args_str[1:-1]
                return OrderedDict([(k, value), ("call_name", call_name)])

        args = OrderedDict()

        # param which name not assigned
        param_iter = iter(self.params.keys())
        if len(call_node.args) > len(self.params):
            raise ValueError('Parse args of torch in {}, but there is problems with params'.format(call_name))
        for arg in call_node.args:
            if isinstance(arg, ast.Starred):
                logger.debug("Find *%s", arg.value.id)
                args['*'] = arg.value.id
            else:
                # remove \n
                args[next(param_iter)] = pasta.dump(arg).strip()

        # params which name is assigned
        for keyword in call_node.keywords:
            if keyword.arg is None:
                logger.info("Find **%s", keyword.value.id)
                args['**'] = keyword.value.id
            else:
                # remove \n
                args[keyword.arg] = pasta.dump(keyword.value).strip()

        args["call_name"] = call_name
        return args


class APIMs(APIPt):
    """API for MindSpore"""

    def __init__(self, name: str, params: dict, p_attrs=None):
        self.is_primitive = name.startswith('P.')
        if self.is_primitive:
            self.p_attrs = p_attrs if p_attrs else set()
        super(APIMs, self).__init__(name, params)

    def create_args(self, params_pt, args_pt, ms2pt_map, explicit_map):
        """
        Create args for MindSpore according to other frame op info.

        Args:
            params_pt (OrderedDict): Params used for initialize function of APIPt.
            args_pt (OrderedDict): Args parsed from APIPt.
            ms2pt_map (dict): Dict of params mapping relation for ops between frames.
            explicit_map（func): Function to generate mapping relation for ops between frames.

        Returns:
            OrderedDict, args for MindSpore.
        """
        args = OrderedDict()

        # traverse MindSpore's params
        for k in self.params.keys():
            # has relevant param? yes
            if k in ms2pt_map:
                if ms2pt_map[k] in args_pt:
                    # user assigned value
                    args[k] = args_pt[ms2pt_map[k]]
                elif self.params[k] != params_pt[ms2pt_map[k]]:
                    # user didn't assigned value, but initial value different between 2 frames
                    args[k] = params_pt[ms2pt_map[k]]
            # has relevant param? no
            else:
                # params forced to display
                if k in explicit_map:
                    args[k] = explicit_map[k]
                elif self.params[k] is REQUIRED:
                    args[k] = "<REQUIRED>"

        # find * or ** in frame actual parameters
        for star in ('*', '**'):
            if star in args_pt:
                args[star] = args_pt[star]

        return args


class MappingHelper:
    """Mapping from one frame to another frame"""

    def __init__(self, ms_api: APIMs, pt_api: APIPt, **kwargs):
        ms2pt_mapping = kwargs.get('ms2pt_mapping')
        gen_explicit_map = kwargs.get('gen_explicit_map')
        export_key = kwargs.get('export_key')

        if ms2pt_mapping is None:
            ms2pt_mapping = {}
        if gen_explicit_map is None:
            gen_explicit_map = lambda params_pt, args_pt: {}
        self.ms_api = ms_api
        self.pt_api = pt_api
        self.ms2pt_mapping = ms2pt_mapping
        self.gen_explicit_map = gen_explicit_map
        if export_key is not None:
            self.export_key = export_key
        else:
            self.export_key = not ms_api.is_primitive

    def gen_args_expr(self, args):
        """
        Generate str assignment statement from given dict.

        Args:
            args (OrderedDict): Key, value pairs for assignment source.

        Returns:
            str, generated str.
        """
        expr = ''
        for key, value in args.items():
            if expr:
                expr += ', '
            sym = '' if key in ('*', '**') else '='
            if self.export_key:
                expr += key + sym
            expr += value
        return expr

    def gen_args_expr_for_p(self, args, p_attrs):
        """
        Generate str assignment statement from given dict for primitive and not primitive.

        Args:
            args (OrderedDict): Key, value pairs for assignment source.
            p_attrs (set): Exclusive params for operator.

        Returns:
            tuple, generated str for primitive, generated str for not primitive.
        """
        args_attrs = OrderedDict([(k, v) for k, v in args.items() if k in p_attrs])
        args_ios = OrderedDict([(k, v) for k, v in args.items() if k not in p_attrs])
        return self.gen_args_expr(args_attrs), self.gen_args_expr(args_ios)

    def convert(self, call_name_pt: str, args_str_pt: str):
        """
        Convert code sentence to MindSpore code sentence.

        Args:
            call_name_pt (str): str of the call function, etc.
            args_str_pt (str): str of args for function, which starts with '(' and end with ')'.

        Returns:
            str, converted code sentence for MindSpore.
        """
        # all value for args_pt is str
        args_pt = self.pt_api.parse_args(call_name_pt, args_str_pt)

        # all value for args_ms is str
        explicit_map = self.gen_explicit_map(self.pt_api.params, args_pt)
        args_ms = self.ms_api.create_args(self.pt_api.params, args_pt, self.ms2pt_mapping, explicit_map)

        if self.ms_api.is_primitive:
            if self.pt_api.name == '.size' and 'idx' in args_pt:
                args_expr = self.gen_args_expr(args_ms)
                expr_ms = "%s()(%s)[%s]" % (self.ms_api.name, args_expr, args_pt['idx'])
            else:
                expr_attrs, expr_ios = self.gen_args_expr_for_p(args_ms, self.ms_api.p_attrs)
                expr_ms = "%s(%s)(%s)" % (self.ms_api.name, expr_attrs, expr_ios)
        else:
            ms_expr = self.gen_args_expr(args_ms)
            expr_ms = "%s(%s)" % (self.ms_api.name, ms_expr)
        return expr_ms


def get_ms_api(ms_api_info):
    """
    Get APIMs instance from ms_api_info.

    Args:
        ms_api_info (list): info for create an APIMs instance, the first value in list is name for APIMs, the second(if
        provided) is params for APIMs, the third(if provided) is p_attrs for APIMs.

    Returns:
        APIMs, instance of APIMs parsed from given info.
    """
    ms_name = ms_api_info[0]
    ms_params = ms_api_info[1] if len(ms_api_info) >= 2 else None
    ms_p_attrs = set(ms_api_info[2]) if len(ms_api_info) >= 3 else None
    ms_api = APIMs(name=ms_name, params=ms_params, p_attrs=ms_p_attrs)
    return ms_api


def get_pt_api(pt_api_info):
    """
    Get APIPt instance from pt_api_info.

    Args:
        pt_api_info (list): info for create an APIMs instance, the first value in list is name for APIPt, the second(if
        provided) is params for APIPt.

    Returns:
        APIMs, instance of APIMs parsed from given info.
    """
    pt_name = pt_api_info[0]
    pt_params = pt_api_info[1] if len(pt_api_info) >= 2 else None
    pt_api = APIPt(name=pt_name, params=pt_params)
    return pt_api


def get_mapping_from_file(path):
    """
    Parse mapping info from given file.

    Args:
        path (str): The file path.

    Returns:
        dict, key is op name, value is a relevant instance of MappingHelper.
    """
    mapping_info_d = load_json_file(path)
    parse_mapping_dict = {}
    for key, value in mapping_info_d.items():
        ms_api_info = value.pop('ms_api')
        ms_api = get_ms_api(ms_api_info)
        pt_api_info = value.pop('pt_api')
        pt_api = get_pt_api(pt_api_info)
        gen_explicit_map = value.get('gen_explicit_map')
        if gen_explicit_map:
            module_name = import_module(FUNC_MODULE)
            value['gen_explicit_map'] = getattr(module_name, gen_explicit_map)

        parse_mapping_dict.update({key: MappingHelper(**dict(ms_api=ms_api, pt_api=pt_api), **value)})
    return parse_mapping_dict


def load_json_file(file_path):
    """
    Load data from given json file path.

    Args:
        file_path (str): The file to load json data from.

    Returns:
        list(str), the list data stored in file_path.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        info = json.loads(file.read())
    return info


def get_corresponding_ms_name(pt_name):
    """
    Get corresponding MindSpore op name for PyTorch name according to the mappings in mindconverter.

    Args:
        pt_name: PyTorch op name, whether shortened form or full name is available.

    Returns:
        str, full MindSpore op name, None if the op is not supported in mindconverter.

    Raises:
        ValueError， if get shortened form of MindSpore name not starts with `P` or 'nn', which means it is wrong in
        the mappings file.
    """
    helper = ALL_MAPPING.get(pt_name)
    if helper is None:
        return None
    ms_name = helper.ms_api.name
    if ms_name.startswith('nn.'):
        full_ms_name = 'mindspore.' + ms_name
    elif ms_name.startswith('P.'):
        full_ms_name = 'mindspore.ops.operations.' + ms_name[len('P.'):]
    else:
        raise ValueError('check your mapping infos, the corresponding mindspore op name may wrong for torch op : '
                         '{}'.format(pt_name))
    return full_ms_name


def get_prompt_info(pt_name):
    """
    Get prompt info for PyTorch op name.

    Args:
        pt_name: PyTorch op name, whether shortened form or full name is available.

    Returns:
        str, prompt info on the op, None if no prompt info for the op.
    """
    prompt_dict = {**UNSUPPORTED_WARN_INFOS, **SUPPORTED_WARN_INFOS}
    return prompt_dict.get(pt_name)


# ---------------------------- mappings ----------------------------
NN_MAPPING_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), 'mappings/nn_mappings.json'))
NN_MAPPING = get_mapping_from_file(NN_MAPPING_PATH)
# update to add key with full api_name, which starts with 'torch.nn.'
NN_MAPPING.update({"torch." + k: v for k, v in NN_MAPPING.items()})

F_MAPPING_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), 'mappings/f_mappings.json'))
F_MAPPING = get_mapping_from_file(F_MAPPING_PATH)
# update to add key starts with 'nn.functional.'
NN_FUNCTIONAL_D = {"nn.functional." + k[len('F.'):]: v for k, v in F_MAPPING.items()}
# update to add key starts with 'torch.nn.functional.'
TORCH_NN_FUNCTIONAL_D = {"torch.nn.functional." + k[len('F.'):]: v for k, v in F_MAPPING.items()}
F_MAPPING.update(NN_FUNCTIONAL_D)
F_MAPPING.update(TORCH_NN_FUNCTIONAL_D)

TORCH_DOT_MAPPING_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), 'mappings/torch_dot_mappings.json'))
TORCH_DOT_MAPPING = get_mapping_from_file(TORCH_DOT_MAPPING_PATH)

TENSOR_DOT_MAPPING_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), 'mappings/tensor_dot_mappings.json'))
TENSOR_DOT_MAPPING = get_mapping_from_file(TENSOR_DOT_MAPPING_PATH)

ALL_MAPPING = {**NN_MAPPING, **F_MAPPING, **TORCH_DOT_MAPPING, **TENSOR_DOT_MAPPING}

# ---------------------------- api list support or not support ----------------------------
NN_LIST_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), 'ops', 'nn_list.json'))
NN_LIST = load_json_file(NN_LIST_PATH)
NN_LIST += ["torch." + name for name in NN_LIST]
NN_SUPPORTED = [x for x in NN_LIST if x in ALL_MAPPING]
NN_UNSUPPORTED = [x for x in NN_LIST if x not in ALL_MAPPING]

F_LIST_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), 'ops', 'f_list.json'))
F_LIST = load_json_file(F_LIST_PATH)
F_LIST += ["F." + name[len("torch.nn.functional."):] for name in F_LIST] + \
          [name[len("torch."):] for name in F_LIST]
F_SUPPORTED = [x for x in F_LIST if x in ALL_MAPPING]
F_UNSUPPORTED = [x for x in F_LIST if x not in ALL_MAPPING]

TORCH_DOT_LIST_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), 'ops', 'torch_dot_list.json'))
TORCH_DOT_LIST = load_json_file(TORCH_DOT_LIST_PATH)

TORCH_DOT_SUPPORTED = [x for x in TORCH_DOT_LIST if x in ALL_MAPPING]
TORCH_DOT_UNSUPPORTED = [x for x in TORCH_DOT_LIST if x not in ALL_MAPPING]

TENSOR_DOT_LIST_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), 'ops', 'tensor_dot_list.json'))
TENSOR_DOT_LIST = load_json_file(TENSOR_DOT_LIST_PATH)

TENSOR_DOT_SUPPORTED = [x for x in TENSOR_DOT_LIST if x in ALL_MAPPING]
TENSOR_DOT_UNSUPPORTED = [x for x in TENSOR_DOT_LIST if x not in ALL_MAPPING]

ALL_2P_LIST = F_LIST + TORCH_DOT_LIST + TENSOR_DOT_LIST
ALL_TORCH_APIS = NN_LIST + F_LIST + TORCH_DOT_LIST + TENSOR_DOT_LIST
ALL_SUPPORTED = NN_SUPPORTED + F_SUPPORTED + TORCH_DOT_SUPPORTED + TENSOR_DOT_SUPPORTED
ALL_UNSUPPORTED = NN_UNSUPPORTED + F_UNSUPPORTED + TORCH_DOT_UNSUPPORTED + TENSOR_DOT_UNSUPPORTED

UNSUPPORTED_WARN_INFOS = {
    "nn.AdaptiveAvgPool2d": "Maybe could convert to mindspore.ops.operations.ReduceMean.",
    "nn.AvgPool1d": "Maybe could convert to mindspore.nn.AvgPool1d.",
    "nn.ConvTranspose2d": "Maybe could convert to mindspore.nn.Conv2dTranspose.",
    "nn.CrossEntropyLoss": "Maybe could convert to mindspore.nn.SoftmaxCrossEntropyWithLogits.",
    "nn.Embedding": "Maybe could convert to mindspore.nn.Embedding.",
    "nn.GroupNorm": "Maybe could convert to mindspore.nn.GroupNorm.",
    "nn.MSELoss": "Maybe could convert to mindspore.nn.MSELoss.",
    "nn.LSTM": "Maybe could convert to mindspore.nn.LSTM.",
    "nn.LSTMCell": "Maybe could convert to mindspore.nn.LSTMCell.",
    "nn.ModuleList": "Maybe could convert to mindspore.nn.CellList.",
    "nn.SmoothL1Loss": "Maybe could convert to mindspore.nn.SmoothL1Loss.",
    "nn.Tanh": "Maybe could convert to mindspore.nn.Tanh.",
    "nn.Upsample": "Maybe could convert to mindspore.ops.operations.ResizeBilinear.",
    "nn.L1Loss": "Maybe could convert to mindspore.nn.L1Loss.",
    "nn.Parameter": "Maybe could convert to mindspore.Parameter.",
    "nn.ParameterList": "Maybe could convert to mindspore.ParameterTuple.",
    "nn.Unfold": "Maybe could convert to mindspore.nn.Unfold.",
    "nn.PixelShuffle": "Maybe could convert to mindspore.ops.operations.DepthToSpace.",
    "F.adaptive_avg_pool2d": "Maybe could convert to mindspore.ops.operations.ReduceMean.",
    "F.conv2d": "Maybe could convert to mindspore.ops.operations.Conv2D.",
    "F.dropout": "please use mindspore.nn.Dropout in __init__().",
    "F.interpolate": "Maybe could convert to mindspore.ops.operations.ResizeBilinear.",
    "F.one_hot": "Maybe could convert to mindspore.ops.operations.OneHot.",
    "torch.bmm": "Maybe could convert to mindspore.ops.operations.BatchMatMul.",
    "torch.cumsum": "Maybe could convert to mindspore.ops.operations.CumSum.",
    "F.pad": "Maybe could convert to mindspore.ops.operations.Pad.",
    "F.softmax": "Maybe could convert to mindspore.ops.operations.Softmax.",
    "torch.clamp": "Maybe could convert to mindspore.ops.composite.clip_by_value.",
    "torch.eq": "Maybe could convert to mindspore.ops.operations.Equal.",
    "torch.load": "Maybe could convert to mindspore.train.serialization.load_checkpoint.",
    "torch.matmul": "Maybe could convert to mindspore.ops.operations.MatMul.",
    "torch.max": "try to use P.ArgMaxWithValue, notice that two values are returned by mindspore.ops.operations."
                 "ArgMaxWithValue.",
    "torch.mean": "Maybe could convert to mindspore.ops.operations.ReduceMean.",
    "torch.min": "try to use P.ArgMinWithValue, notice that two values are returned by mindspore.ops.operations."
                 "ArgMinWithValue.",
    "torch.mm": "Maybe could convert to mindspore.ops.operations.MatMul.",
    "torch.mul": "Maybe could convert to mindspore.ops.operations.Mul.",
    "torch.norm": "Maybe could convert to mindspore.nn.Norm.",
    "torch.numel": "Maybe could convert to mindspore.ops.operations.Size.",
    "torch.ones_like": "Maybe could convert to mindspore.ops.operations.OnesLike.",
    "torch.randn": "Maybe could convert to mindspore.ops.operations.TruncatedNormal.",
    "torch.round": "Maybe could convert to mindspore.ops.operations.Round.",
    "torch.save": "Maybe could convert to mindspore.train.serialization.save_checkpoint.",
    "torch.sigmoid": "Maybe could convert to mindspore.ops.operations.Sigmoid.",
    "torch.split": "Maybe could convert to mindspore.ops.operations.Split.",
    "torch.squeeze": "Maybe could convert to mindspore.ops.operations.Squeeze.",
    "torch.stack": "Maybe could convert to mindspore.ops.operations.Pack.",
    "torch.sum": "Maybe could convert to mindspore.ops.operations.ReduceSum.",
    "torch.tanh": "Maybe could convert to mindspore.ops.operations.Tanh.",
    "torch.tensor": "Maybe could convert to mindspore.Tensor.",
    "torch.transpose": "Maybe could convert to mindspore.ops.operations.Transpose.",
    "torch.unsqueeze": "Maybe could convert to mindspore.ops.operations.ExpandDims.",
    "torch.zeros_like": "Maybe could convert to mindspore.ops.operations.ZerosLike.",
    ".chunk": "Maybe could convert to mindspore.ops.operations.Split.",
    ".fill_": "Maybe could convert to mindspore.ops.operations.Fill.",
    ".float": "Maybe could convert to mindspore.ops.operations.Cast.",
    ".mm": "Maybe could convert to mindspore.ops.operations.MatMul.",
    ".mul": "Maybe could convert to mindspore.ops.operations.Mul.",
    ".pow": "Maybe could convert to mindspore.ops.operations.Pow.",
    ".round": "Maybe could convert to mindspore.ops.operations.Round.",
    ".scatter": "Maybe could convert to mindspore.ops.operations.ScatterNd.",
    ".sigmoid": "Maybe could convert to mindspore.nn.Sigmoid.",
    ".sign": "Maybe could convert to mindspore.ops.operations.Sign.",
    ".sqrt": "Maybe could convert to mindspore.ops.operations.Sqrt.",
    ".sub": "Maybe could convert to mindspore.ops.operations.Sub.",
    ".transpose": "Maybe could convert to mindspore.ops.operations.Transpose.",
    ".unsqueeze": "Maybe could convert to mindspore.ops.operations.ExpandDims.",
    ".zero_": "Maybe could convert to mindspore.ops.operations.ZerosLike.",
}

NN_UNSUPPORTED_INFOS = {k: v for k, v in UNSUPPORTED_WARN_INFOS.items() if k.startswith('nn.')}
TORCH_NN_UNSUPPORTED_INFOS = {('torch.' + k): v for k, v in NN_UNSUPPORTED_INFOS.items()}

F_UNSUPPORTED_INFOS = {k: v for k, v in UNSUPPORTED_WARN_INFOS.items() if k.startswith('F.')}
NN_FUNCTIONAL_UNSUPPORTED_INFOS = {'nn.functional.' + k[len('F.'):]: v for k, v in F_UNSUPPORTED_INFOS.items()}
TORCH_NN_FUNCTIONAL_UNSUPPORTED_INFOS = {'torch.nn.functional.' + k[len('F.'):]: v for k, v in
                                         F_UNSUPPORTED_INFOS.items()}

UNSUPPORTED_WARN_INFOS.update(TORCH_NN_UNSUPPORTED_INFOS)
UNSUPPORTED_WARN_INFOS.update(NN_FUNCTIONAL_UNSUPPORTED_INFOS)
UNSUPPORTED_WARN_INFOS.update(TORCH_NN_FUNCTIONAL_UNSUPPORTED_INFOS)

SUPPORTED_WARN_INFOS = {
    "torch.eye": "Pay attention to use right mindspore data type.",
    "nn.Linear": "Pay attention to reshape the input to 2 dims if it is 3 dims before, because MindSpore.nn.Dense only "
                 "support 2-dim input.",
    ".view": "Only float Tensor is supported in mindspore.ops.operations.Reshape.",
    ".reshape": "Only float Tensor is supported in mindspore.ops.operations.Reshape."
}

NN_SUPPORTED_INFOS = {k: v for k, v in SUPPORTED_WARN_INFOS.items() if k.startswith('nn.')}
TORCH_NN_SUPPORTED_INFOS = {('torch.' + k): v for k, v in NN_SUPPORTED_INFOS.items()}
SUPPORTED_WARN_INFOS.update(TORCH_NN_SUPPORTED_INFOS)

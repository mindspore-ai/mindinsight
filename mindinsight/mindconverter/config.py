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
from functools import partial
import json
import os

import pasta

from mindinsight.mindconverter.enums import RequriedType
from mindinsight.mindconverter.common.log import logger

REQUIRED = RequriedType.REQUIRED.name
UNREQUIRED = RequriedType.UNREQUIRED.name


class APIPt:
    """Base API for args parse, and API for one frame."""
    def __init__(self, name: str, params: OrderedDict):
        self.name = name
        self.params = OrderedDict()

        for k, value in params.items():
            self.params[k] = self.to_str(value)

    @staticmethod
    def to_str(value):
        """
        Trans value to str.

        Args:
            value (Union[str,Number,int]): Each value for params of OrderedDict.

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
        if not (len(args_str) >= 2 and args_str[0] == "(" and args_str[-1] == ")"):
            raise ValueError('[{}] is think as args str, it should start with "(" and end with ")"'.format(args_str))

        try:
            ast_node = ast.parse("whatever_call_name" + args_str)
            call_node = ast_node.body[0].value
            if not isinstance(call_node, ast.Call):
                raise ValueError('call name with args str [{}] not instance of ast.Call'.format(args_str))
        except:
            raise ValueError("can't parse code:\n{}".format(args_str))

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
    def __init__(self, name: str, params: OrderedDict, p_attrs=None):
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


def gen_explicit_map_nn_sequential(_, args_pt):
    """
    Generate explicit_map for nn.Sequential.

    Args:
        args_pt (dict): Args for APIPt.

    Returns:
        dict, map between frames.
    """
    args = args_pt['*args']
    return {"*args": "[{}]".format(args)}


def gen_explicit_map_nn_maxpool2d(params_pt, args_pt):
    """
    Generate explicit_map for nn.MaxPool2d.

    Args:
        params_pt (dict): Params for APIPt.
        args_pt (dict): Args for APIPt.

    Returns:
        dict, map between frames.
    """
    if 'padding' in args_pt:
        padding = args_pt['padding']
    else:
        padding = params_pt['padding']
    if padding.strip() in ("0", "(0,0)", "(0, 0)"):
        pad_mode = "'valid'"
    else:
        pad_mode = "'same'"
    return {"pad_mode": pad_mode}


def gen_explicit_map_f_max_pool2d(params_pt, args_pt):
    """
    Generate explicit_map for F.MaxPool2d.

    Args:
        params_pt (dict): Params for APIPt.
        args_pt (dict): Args for APIPt.

    Returns:
        dict, map between frames.
    """
    if 'padding' in args_pt:
        padding = args_pt['padding']
    else:
        padding = params_pt['padding']
    if padding.strip() in ("0", "(0,0)", "(0, 0)"):
        padding = "'valid'"
    else:
        padding = "'same'"
    return {"padding": padding}


def gen_explicit_map_one_delta(params_pt, args_pt, k_ms, k_pt):
    """
    Generate explicit_map for which include mapping relationship is `1 - k_ms = k_pt`.

    Args:
        params_pt (dict): Params for APIPt.
        args_pt (dict): Args for APIPt.

    Returns:
        dict, map between frames.
    """
    value = args_pt[k_pt] if k_pt in args_pt else params_pt[k_pt]
    value = value.strip()

    def is_number(string):
        try:
            float(string)
            return True
        except ValueError:
            return False

    if is_number(value):
        return {k_ms: str(1 - float(value))}
    return {k_ms: "1.0 - " + value}


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


# ---------------------------- mappings ----------------------------
NN_MAPPING = {
    'nn.Sequential': MappingHelper(**{"ms_api": APIMs('nn.SequentialCell', OrderedDict([('*args', REQUIRED)])),
                                      "pt_api": APIPt('nn.Sequential', OrderedDict([('*args', REQUIRED)])),
                                      "gen_explicit_map": gen_explicit_map_nn_sequential,
                                      "export_key": False
                                      }),
    'nn.Conv2d': MappingHelper(**{"ms_api": APIMs('nn.Conv2d', OrderedDict(in_channels=REQUIRED,
                                                                           out_channels=REQUIRED,
                                                                           kernel_size=REQUIRED,
                                                                           stride=1,
                                                                           pad_mode='same',
                                                                           padding=0,
                                                                           dilation=1,
                                                                           group=1,
                                                                           has_bias=False,
                                                                           weight_init='normal',
                                                                           bias_init='zeros')),
                                  "pt_api": APIPt('nn.Conv2d', OrderedDict(in_channels=REQUIRED,
                                                                           out_channels=REQUIRED,
                                                                           kernel_size=REQUIRED,
                                                                           stride=1,
                                                                           padding=0,
                                                                           dilation=1,
                                                                           groups=1,
                                                                           bias=True,
                                                                           padding_mode='zeros')),
                                  "ms2pt_mapping": {'in_channels': 'in_channels',
                                                    'out_channels': 'out_channels',
                                                    'kernel_size': 'kernel_size',
                                                    'stride': 'stride',
                                                    'padding': 'padding',
                                                    'dilation': 'dilation',
                                                    'group': 'groups',
                                                    'has_bias': 'bias'},
                                  "gen_explicit_map": (lambda params_pt, args_pt: {"pad_mode": "'pad'"})
                                  }),
    'nn.BatchNorm2d': MappingHelper(**{"ms_api": APIMs('nn.BatchNorm2d', OrderedDict(num_features=REQUIRED,
                                                                                     eps=1e-5,
                                                                                     momentum=0.9,
                                                                                     affine=True,
                                                                                     gamma_init='ones',
                                                                                     beta_init='zeros',
                                                                                     moving_mean_init='zeros',
                                                                                     moving_var_init='ones',
                                                                                     use_batch_statistics=True)),
                                       "pt_api": APIPt('nn.BatchNorm2d', OrderedDict(num_features=REQUIRED,
                                                                                     eps=1e-5,
                                                                                     momentum=0.1,
                                                                                     affine=True,
                                                                                     track_running_stats=True)),
                                       "ms2pt_mapping": {"num_features": "num_features",
                                                         "eps": "eps",
                                                         "affine": "affine",
                                                         "use_batch_statistics": "track_running_stats"},
                                       "gen_explicit_map": partial(gen_explicit_map_one_delta,
                                                                   k_ms="momentum", k_pt="momentum")
                                       }),
    'nn.ReLU': MappingHelper(**{"ms_api": APIMs('nn.ReLU', OrderedDict()),
                                "pt_api": APIPt('nn.ReLU', OrderedDict(inplace=False)),
                                "ms2pt_mapping": {}}),
    'nn.ReLU6': MappingHelper(**{"ms_api": APIMs('nn.ReLU6', OrderedDict()),
                                 "pt_api": APIPt('nn.ReLU6', OrderedDict(inplace=False)),
                                 "ms2pt_mapping": {}}),
    'nn.Linear': MappingHelper(**{"ms_api": APIMs('nn.Dense', OrderedDict(in_channels=REQUIRED,
                                                                          out_channels=REQUIRED,
                                                                          weight_init='normal',
                                                                          bias_init='zeros',
                                                                          has_bias=True,
                                                                          activation=None)),
                                  "pt_api": APIPt('nn.Linear', OrderedDict(in_features=REQUIRED,
                                                                           out_features=REQUIRED,
                                                                           bias=True)),
                                  "ms2pt_mapping": {"in_channels": "in_features",
                                                    "out_channels": "out_features",
                                                    "has_bias": "bias"}
                                  }),
    'nn.MaxPool2d': MappingHelper(**{"ms_api": APIMs('nn.MaxPool2d', OrderedDict(kernel_size=1,
                                                                                 stride=1,
                                                                                 pad_mode="valid")),
                                     "pt_api": APIPt('nn.MaxPool2d', OrderedDict(kernel_size=REQUIRED,
                                                                                 stride=None,
                                                                                 padding=0,
                                                                                 dilation=1,
                                                                                 return_indices=False,
                                                                                 ceil_mode="False")),
                                     "ms2pt_mapping": {"kernel_size": "kernel_size",
                                                       "stride": "stride"},
                                     "gen_explicit_map": gen_explicit_map_nn_maxpool2d
                                     }),
    'nn.AvgPool2d': MappingHelper(**{"ms_api": APIMs('nn.AvgPool2d', OrderedDict(kernel_size=1,
                                                                                 stride=1,
                                                                                 pad_mode="valid")),
                                     "pt_api": APIPt('nn.AvgPool2d', OrderedDict(kernel_size=REQUIRED,
                                                                                 stride=None,
                                                                                 padding=0,
                                                                                 dilation=1,
                                                                                 return_indices=False,
                                                                                 ceil_mode="False")),
                                     "ms2pt_mapping": {"kernel_size": "kernel_size",
                                                       "stride": "stride"},
                                     "gen_explicit_map": gen_explicit_map_nn_maxpool2d
                                     }),
    'nn.Dropout': MappingHelper(**{"ms_api": APIMs('nn.Dropout', OrderedDict(keep_prob=0.5,
                                                                             seed0=0,
                                                                             seed1=0,
                                                                             dtype="mstype.float32")),
                                   "pt_api": APIPt('nn.Dropout', OrderedDict(p=0.5,
                                                                             inplace=False)),
                                   "ms2pt_mapping": {"keep_prob": "p"},
                                   "gen_explicit_map": partial(gen_explicit_map_one_delta,
                                                               k_ms="keep_prob", k_pt="p")
                                   })
}
# set alias nn. = torch.nn.
NN_MAPPING.update({"torch." + k: v for k, v in NN_MAPPING.items()})


F_MAPPING = {
    'F.relu': MappingHelper(**{"ms_api": APIMs('P.ReLU', OrderedDict(input=REQUIRED)),
                               "pt_api": APIPt('F.relu', OrderedDict(input=REQUIRED, inplace=False)),
                               "ms2pt_mapping": {"input": "input"},
                               }),
    'F.relu6': MappingHelper(**{"ms_api": APIMs('P.ReLU6', OrderedDict(input=REQUIRED)),
                                "pt_api": APIPt('F.relu6', OrderedDict(input=REQUIRED, inplace=False)),
                                "ms2pt_mapping": {"input": "input"},
                                }),
    'F.max_pool2d': MappingHelper(**{"ms_api": APIMs('P.MaxPool', OrderedDict(ksize=1,
                                                                              strides=1,
                                                                              padding="valid",
                                                                              input=REQUIRED),
                                                     p_attrs={"ksize", "strides", "padding"}),
                                     "pt_api": APIPt('F.max_pool2d', OrderedDict(input=REQUIRED,
                                                                                 kernel_size=REQUIRED,
                                                                                 stride=None,
                                                                                 padding=0,
                                                                                 dilation=1,
                                                                                 ceil_mode=False,
                                                                                 return_indices=False)),
                                     "ms2pt_mapping": {"ksize": "kernel_size",
                                                       "strides": "stride",
                                                       "input": "input",
                                                       },
                                     "gen_explicit_map": gen_explicit_map_f_max_pool2d
                                     }),
    'F.avg_pool2d': MappingHelper(**{"ms_api": APIMs('P.AvgPool', OrderedDict(ksize=1,
                                                                              strides=1,
                                                                              padding="valid",
                                                                              input=REQUIRED),
                                                     p_attrs={"ksize", "strides", "padding"}),
                                     "pt_api": APIPt('F.avg_pool2d', OrderedDict(input=REQUIRED,
                                                                                 kernel_size=REQUIRED,
                                                                                 stride=None,
                                                                                 padding=0,
                                                                                 dilation=1,
                                                                                 ceil_mode=False,
                                                                                 return_indices=False)),
                                     "ms2pt_mapping": {"ksize": "kernel_size",
                                                       "strides": "stride",
                                                       "input": "input",
                                                       },
                                     "gen_explicit_map": gen_explicit_map_f_max_pool2d
                                     }),
}
# set alias F = nn.functional = torch.nn.functional
nn_functional_d = {"nn.functional." + k[2:]: v for k, v in F_MAPPING.items()}
torch_nn_functional_d = {"torch.nn.functional." + k[2:]: v for k, v in F_MAPPING.items()}
F_MAPPING.update(nn_functional_d)
F_MAPPING.update(torch_nn_functional_d)


TORCH_DOT_MAPPING = {
    'torch.flatten': MappingHelper(**{"ms_api": APIMs('P.Flatten', OrderedDict(input=REQUIRED)),
                                      "pt_api": APIPt('torch.flatten', OrderedDict(input=REQUIRED,
                                                                                   start_dim=0,
                                                                                   end_dim=-1)),
                                      "ms2pt_mapping": {"input": "input"}
                                      }),
    'torch.cat': MappingHelper(**{"ms_api": APIMs('P.Concat',
                                                  OrderedDict(axis=0, input=REQUIRED),
                                                  p_attrs={"axis"}),
                                  "pt_api": APIPt('torch.flatten', OrderedDict(tensors=REQUIRED, dim=0, out=None)),
                                  "ms2pt_mapping": {"input": "tensors",
                                                    "axis": "dim"}
                                  }),
}


TENSOR_DOT_MAPPING = {
    '.view': MappingHelper(**{"ms_api": APIMs('P.Reshape', OrderedDict(x=REQUIRED, shape=REQUIRED)),
                              "pt_api": APIPt('.view', OrderedDict([('*shape', REQUIRED)])),
                              "ms2pt_mapping": {"x": "call_name"},
                              "gen_explicit_map": (lambda params_pt, args_pt: {"shape": "(" + args_pt["*shape"] + ",)"})
                              }),
    '.size': MappingHelper(**{"ms_api": APIMs('P.Shape', OrderedDict(x=REQUIRED)),
                              "pt_api": APIPt('.size', OrderedDict([('idx', REQUIRED)])),
                              "ms2pt_mapping": {"x": "call_name"}
                              }),
    '.flatten': MappingHelper(**{"ms_api": APIMs('P.Flatten', OrderedDict(input=REQUIRED)),
                                 "pt_api": APIPt('.flatten', OrderedDict(start_dim=0,
                                                                         end_dim=-1)),
                                 "ms2pt_mapping": {"input": "call_name"}
                                 }),
    '.reshape': MappingHelper(**{"ms_api": APIMs('P.Reshape', OrderedDict(x=REQUIRED, shape=REQUIRED)),
                                 "pt_api": APIPt('.reshape', OrderedDict([('*shape', REQUIRED)])),
                                 "ms2pt_mapping": {"x": "call_name"},
                                 "gen_explicit_map": (
                                     lambda params_pt, args_pt: {"shape": "(" + args_pt["*shape"] + ",)"})
                                 }),
    '.mean': MappingHelper(**{"ms_api": APIMs('P.ReduceMean', OrderedDict(keep_dims=False,
                                                                          input=REQUIRED,
                                                                          axis=()),
                                              p_attrs={"keep_dims"}),
                              "pt_api": APIPt('.mean', OrderedDict(dim=None,
                                                                   keepdim=False)),
                              "ms2pt_mapping": {"keep_dims": "keepdim",
                                                "axis": "dim",
                                                "input": "call_name"},
                              }),
    '.squeeze': MappingHelper(**{"ms_api": APIMs('P.ReduceMean', OrderedDict(input=REQUIRED,
                                                                             axis=()),
                                                 p_attrs={"axis"}),
                                 "pt_api": APIPt('.squeeze', OrderedDict(dim=None)),
                                 "ms2pt_mapping": {"axis": "dim",
                                                   "input": "call_name"},
                                 }),
}


ALL_MAPPING = {**NN_MAPPING, **F_MAPPING, **TORCH_DOT_MAPPING, **TENSOR_DOT_MAPPING}


# ---------------------------- api list support or not support ----------------------------
NN_LIST_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), 'nn_list.json'))
NN_LIST = load_json_file(NN_LIST_PATH)
# set alias nn. = torch.nn.
NN_LIST += ["torch." + name for name in NN_LIST]
NN_SUPPORTED = [x for x in NN_LIST if x in ALL_MAPPING]
NN_UNSUPPORTED = [x for x in NN_LIST if x not in ALL_MAPPING]


F_LIST_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), 'f_list.json'))
F_LIST = load_json_file(F_LIST_PATH)
# set alias F = nn.functional = torch.nn.functional
F_LIST += ["F." + name[len("torch.nn.functional."):] for name in F_LIST] + \
          [name[len("torch."):] for name in F_LIST]
F_SUPPORTED = [x for x in F_LIST if x in ALL_MAPPING]
F_UNSUPPORTED = [x for x in F_LIST if x not in ALL_MAPPING]


TORCH_DOT_LIST_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), 'torch_dot_list.json'))
TORCH_DOT_LIST = load_json_file(TORCH_DOT_LIST_PATH)


TORCH_DOT_SUPPORTED = [x for x in TORCH_DOT_LIST if x in ALL_MAPPING]
TORCH_DOT_UNSUPPORTED = [x for x in TORCH_DOT_LIST if x not in ALL_MAPPING]


TENSOR_DOT_LIST_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), 'tensor_dot_list.json'))
TENSOR_DOT_LIST = load_json_file(TENSOR_DOT_LIST_PATH)


TENSOR_DOT_SUPPORTED = [x for x in TENSOR_DOT_LIST if x in ALL_MAPPING]
TENSOR_DOT_UNSUPPORTED = [x for x in TENSOR_DOT_LIST if x not in ALL_MAPPING]


ALL_2P_LIST = F_LIST + TORCH_DOT_LIST + TENSOR_DOT_LIST
ALL_TORCH_APIS = NN_LIST + F_LIST + TORCH_DOT_LIST + TENSOR_DOT_LIST
ALL_SUPPORTED = NN_SUPPORTED + F_SUPPORTED + TORCH_DOT_SUPPORTED + TENSOR_DOT_SUPPORTED
ALL_UNSUPPORTED = NN_UNSUPPORTED + F_UNSUPPORTED + TORCH_DOT_UNSUPPORTED + TENSOR_DOT_UNSUPPORTED


UNSUPPORTED_WARN_INFOS = {
    "nn.AdaptiveAvgPool2d": "maybe could convert to P.ReduceMean",
    "F.adaptive_avg_pool2d": "maybe could convert to P.ReduceMean",
    "F.dropout": "please use nn.Dropout in __init__()",
}

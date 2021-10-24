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
"""funcs for gen_explicit_map"""
from functools import partial


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

    if 'stride' in args_pt:
        strides = args_pt['stride']
    else:
        strides = args_pt['kernel_size']

    return {"padding": padding,
            "strides": strides}


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

    if 'stride' in args_pt:
        stride = args_pt['stride']
    else:
        stride = args_pt['kernel_size']

    return {"pad_mode": pad_mode,
            "stride": stride}


def torch_dot_eye_gen_explicit_map(_, args_pt):
    """
    Generate explicit_map for torch.eye.

    Args:
        args_pt (dict): Args for APIPt.

    Returns:
        dict, map between frames.
    """
    explicit_map = {'t': 'mindspore.int32'}
    if args_pt.get('m'):
        explicit_map.update({'m': args_pt.get('m')})
    else:
        explicit_map.update({'m': args_pt.get('n')})
    return explicit_map

tensor_dot_permute_gen_explicit_map = lambda params_pt, args_pt: {"input_perm": "(" + args_pt["*dIms"] + ",)"}
tensor_dot_repeat_gen_explicit_map = lambda params_pt, args_pt: {"multiples": "(" + args_pt["*sizes"] + ",)"}
tensor_dot_reshape_gen_explicit_map = lambda params_pt, args_pt: {"shape": "(" + args_pt["*shape"] + ",)"}
tensor_dot_view_gen_explicit_map = lambda params_pt, args_pt: {"shape": "(" + args_pt["*shape"] + ",)"}
nn_conv2d_gen_explicit_map = lambda params_pt, args_pt: {"pad_mode": "'pad'"}
nn_batchnorm2d_gen_explicit_map = partial(gen_explicit_map_one_delta, k_ms="momentum", k_pt="momentum")
nn_batchnorm1d_gen_explicit_map = nn_batchnorm2d_gen_explicit_map
nn_dropout_gen_explicit_map = partial(gen_explicit_map_one_delta, k_ms="keep_prob", k_pt="p")
torch_dot_add_gen_explicit_map = lambda params_pt, args_pt:\
    {"input_y": (args_pt['value'] + '*' + args_pt["alpha"]) if args_pt.get("alpha") else args_pt['value']}

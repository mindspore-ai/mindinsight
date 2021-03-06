# Copyright 2020 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""Utils for optimizer."""
import string

import numpy as np

_DEFAULT_HISTOGRAM_BINS = 5


def calc_histogram(np_value: np.ndarray, bins=_DEFAULT_HISTOGRAM_BINS):
    """
    Calculates histogram.

    This is a simple wrapper around the error-prone np.histogram() to improve robustness.
    """
    ma_value = np.ma.masked_invalid(np_value)

    valid_cnt = ma_value.count()
    if not valid_cnt:
        max_val = 0
        min_val = 0
    else:
        # Note that max of a masked array with dtype np.float16 returns inf (numpy issue#15077).
        if np.issubdtype(np_value.dtype, np.floating):
            max_val = ma_value.max(fill_value=np.NINF)
            min_val = ma_value.min(fill_value=np.PINF)
        else:
            max_val = ma_value.max()
            min_val = ma_value.min()

    range_left = min_val
    range_right = max_val

    default_half_range = 0.5
    if range_left >= range_right:
        range_left -= default_half_range
        range_right += default_half_range

    with np.errstate(invalid='ignore'):
        # if don't ignore state above, when np.nan exists,
        # it will occur RuntimeWarning: invalid value encountered in less_equal
        counts, edges = np.histogram(np_value, bins=bins, range=(range_left, range_right))

    histogram_bins = [None] * len(counts)
    for ind, count in enumerate(counts):
        histogram_bins[ind] = [float(edges[ind]), float(edges[ind + 1] - edges[ind]), float(count)]

    return histogram_bins


def is_simple_numpy_number(dtype):
    """Verify if it is simple number."""
    if np.issubdtype(dtype, np.integer):
        return True

    if np.issubdtype(dtype, np.floating):
        return True

    return False


def get_nested_message(info: dict, out_err_msg=""):
    """Get error message from the error dict generated by schema validation."""
    if not isinstance(info, dict):
        if isinstance(info, list):
            info = info[0]
        return f'Error in {out_err_msg}: {info}'
    for key in info:
        if isinstance(key, str) and key != '_schema':
            if out_err_msg:
                out_err_msg = f'{out_err_msg}.{key}'
            else:
                out_err_msg = key
        return get_nested_message(info[key], out_err_msg)


def is_number(uchar):
    """If it is a number, return True."""
    if uchar in string.digits:
        return True
    return False


def is_alphabet(uchar):
    """If it is an alphabet, return True."""
    if uchar in string.ascii_letters:
        return True
    return False


def is_allowed_symbols(uchar):
    """If it is an allowed symbol, return True."""
    if uchar in ['_']:
        return True
    return False


def is_param_name_valid(param_name: str):
    """If parameter name only contains underscore, number or alphabet, return True."""
    for uchar in param_name:
        if not is_number(uchar) and not is_alphabet(uchar) and not is_allowed_symbols(uchar):
            return False
    return True

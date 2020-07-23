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
"""The npu collector."""

import inspect
from collections import defaultdict
from ctypes import CDLL, Structure, byref, c_char, c_int, c_uint, c_ulong, c_ushort
from functools import lru_cache, wraps
from threading import Lock, Thread

from mindinsight.sysmetric.common.exceptions import DsmiQueryingException
from mindinsight.sysmetric.common.log import logger


def _timeout(seconds, default):
    """
    The timeout decorator wait for specified seconds or return the default value.

    Args:
        seconds (float): The specified seconds.
        default (Any): The default value.
    """

    def outer(fn):
        cached, lockdict = {}, defaultdict(Lock)

        def target(*args):
            lock = lockdict[args]
            if lock.acquire(blocking=False):
                try:
                    cached[args] = fn(*args)
                finally:
                    lock.release()
            else:
                logger.debug('%s%r skipped.', fn.__name__, args)

        @wraps(fn)
        def inner(*args):
            thread = Thread(target=target, args=args, daemon=True)
            thread.start()
            thread.join(seconds)
            if thread.is_alive():
                logger.debug('%s%r timeouted.', fn.__name__, args)
            return cached.get(args, default)

        return inner

    return outer


def _fallback_to_prev_result(fn):
    """Fallback to previous successful result when failing."""
    prev_result = None

    @wraps(fn)
    def wrap(*args):
        nonlocal prev_result
        sucess, result = fn(*args)
        if sucess:
            prev_result = result
            return sucess, result
        if prev_result is not None:
            return sucess, prev_result
        raise RuntimeError(f'{fn.__name__} querying failed and no previous successful result.')

    return wrap


def _libsmicall(*args):
    """
    Call the lib function to querying NPU metrics.

    Returns:
        bool, True when success of querying, False otherwise.
    """
    if not libsmi:
        logger.error('Trying to call the libdrvdsmi_host which is not loaded.')
        raise ValueError('Trying to call the libdrvdsmi_host which is not loaded.')
    fname = inspect.stack()[1].function
    error_code = getattr(libsmi, fname)(*args)
    if error_code != 0:
        logger.error(f'{fname} querying failed with error code {error_code}.')
    return error_code == 0


@lru_cache(maxsize=4)
def dsmi_get_device_count():
    """
    Get device count.

    Returns:
        int, the device count.

    Raises:
        RuntimeError, when querying dsmi returning non-zero.
    """
    device_count = c_int()

    if _libsmicall(byref(device_count)):
        return device_count.value
    raise RuntimeError('Querying device count failed.')


@lru_cache(maxsize=4)
def dsmi_list_device(count):
    """
    List the device IDs.

    Args:
        count (int): The device count.

    Returns:
        List[int], the device IDs.

    Raises:
        RuntimeError, when querying dsmi returning non-zero.
    """
    device_id_array = c_int * count
    device_id_list = device_id_array()
    count = c_int(count)

    if _libsmicall(device_id_list, count):
        return list(device_id_list)
    raise RuntimeError('Querying device id list failed.')


@lru_cache(maxsize=8)
@_fallback_to_prev_result
def dsmi_get_chip_info(device_id):
    """
    Get chip info.

    Args:
        device_id (int): The specific device id.

    Returns:
        dict, the chip info:
            - chip_type (str): The chip type.
            - chip_name (str): The chip name.
            - chip_ver (str): The chip name.

    Raises:
        RuntimeError, when querying dsmi returning non-zero.
    """

    class ChipInfoStruct(Structure):
        _fields_ = [('chip_type', c_char * 32), ('chip_name', c_char * 32), ('chip_ver', c_char * 32)]

    device_id = c_int(device_id)
    chip_info = ChipInfoStruct()
    success = _libsmicall(device_id, byref(chip_info))
    return success, {
        'chip_type': chip_info.chip_type.decode('utf-8'),
        'chip_name': chip_info.chip_name.decode('utf-8'),
        'chip_ver': chip_info.chip_ver.decode('utf-8')
    }


@_fallback_to_prev_result
def dsmi_get_device_health(device_id):
    """
    Get device health.

    Args:
        device_id (int): The specific device id.

    Returns:
        int, 0 indicats normal, 1 minor alarm, 2 major alarm, 3 critical alarm, 0xffffffff device not found.

    Raises:
        RuntimeError, when querying dsmi returning non-zero.
    """
    device_id = c_int(device_id)
    health = c_uint()

    success = _libsmicall(device_id, byref(health))

    return success, health.value


@lru_cache(maxsize=8)
@_fallback_to_prev_result
def dsmi_get_device_ip_address(device_id):
    """
    Get device IP address.

    Args:
        device_id (int): The specific device ID.
    Returns:
        dict, the device IP address:
            - ip_address (str): the IP address.
            - mask_address (str): the mask address.

    Raises:
        RuntimeError, when querying dsmi returning non-zero.
    """
    is_ipv6, port_type, port_id = False, 1, 0

    class Ipaddrstruct(Structure):
        _fields_ = [('u_addr', c_char * (16 if is_ipv6 else 4)), ('ip_type', c_int)]

    ip_type = c_int(1 if is_ipv6 else 0)

    device_id = c_int(device_id)
    ip_address = Ipaddrstruct(b'', ip_type)
    mask_address = Ipaddrstruct(b'', ip_type)

    success = _libsmicall(device_id, port_type, port_id, byref(ip_address), byref(mask_address))

    def pad(u_addr):
        for i in range(4):
            if i < len(u_addr):
                yield u_addr[i]
            else:
                yield 0

    return success, {
        'ip_address': '.'.join(str(c) for c in pad(ip_address.u_addr)),
        'mask_address': '.'.join(str(c) for c in pad(mask_address.u_addr))
    }


@_fallback_to_prev_result
def dsmi_get_hbm_info(device_id):
    """
    Get the HBM info.

    Args:
        device_id (int): The specific device id.

    Returns:
        dict, the HBM info:
            memory_size (int), The total HBM memory, in KB.
            frep (int), The HBM frequency, in MHZ.
            memory_usage (int), The used HBM memory, in KB.
            temp (int), The HBM temperature, in °C.
            bandwith_util_rate (int): The bandwith util rate, in %.

    Raises:
        RuntimeError, when querying dsmi returning non-zero.
    """

    class HbmInfoStruct(Structure):
        _fields_ = [('memory_size', c_ulong), ('freq', c_uint), ('memory_usage', c_ulong), ('temp', c_int),
                    ('bandwith_util_rate', c_uint)]

    device_id = c_int(device_id)
    hbm_info = HbmInfoStruct()

    success = _libsmicall(device_id, byref(hbm_info))

    return success, {
        'memory_size': hbm_info.memory_size,
        'freq': hbm_info.freq,
        'memory_usage': hbm_info.memory_usage,
        'temp': hbm_info.temp,
        'bandwith_util_rate': hbm_info.bandwith_util_rate
    }


@_timeout(0.2, 0)
@_fallback_to_prev_result
def dsmi_get_device_utilization_rate(device_id, device_type):
    """
    Get device utilization rate, %.

    Note: Query AI Core when profiling turns on will return failure.

    Args:
        device_id (int): The specific device id
        device_type (int): The device type, 1 for memory, 2 AI Core, 5 memory bandwidth, 6 HBM, 10 HBM bandwidth.
    Returns:
        int, the utilization rate.
    """
    device_id = c_int(device_id)
    device_type = c_int(device_type)
    utilization_rate = c_uint()
    success = _libsmicall(device_id, device_type, byref(utilization_rate))
    return success, utilization_rate.value


@_fallback_to_prev_result
def dsmi_get_device_power_info(device_id):
    """
    Get the device power.

    Args:
        device_id (int): The specific device id.

    Returns:
        dict, the device power info.
            - power, the device power, in Watt.

    Raises:
        RuntimeError, when querying dsmi returning non-zero.
    """

    class PowerInfoStruct(Structure):
        _fields_ = [('power', c_ushort)]

    power_info = PowerInfoStruct()
    device_id = c_int(device_id)

    success = _libsmicall(device_id, byref(power_info))
    return success, {'power': round(power_info.power * 0.1, 2)}


@_fallback_to_prev_result
def dsmi_get_device_temperature(device_id):
    """
    Get the device temperature.

    Args:
        device_id (int): The specific device id.

    Returns:
        int, the device temperature, in °C.

    Raises:
        RuntimeError, when querying dsmi returning non-zero.
    """
    device_id = c_int(device_id)
    temperature = c_uint()

    success = _libsmicall(device_id, byref(temperature))

    return success, temperature.value


def collect_npu():
    """Collect the metrics for each NPUs.

    Returns:
        List[dict], the metrics of each NPUs.

    Raises:
        DsmiQueryingException, when querying dsmi returning non-zero.
    """
    try:
        return _collect_npus()
    except RuntimeError as e:
        logger.warning(e.args[0])
        raise DsmiQueryingException(e.args[0])


def _collect_npus():
    """Collect the metrics for each NPUs.

    Returns:
        List[dict], the metrics of each NPUs.

    Raises:
        RuntimeError, when querying dsmi returning non-zero.
    """
    if not libsmi:
        return None
    count = dsmi_get_device_count()
    device_ids = dsmi_list_device(count)
    npus = []
    for device_id in device_ids:
        npu = _collect_one(device_id)
        npus.append(npu)
    return npus


def _collect_one(device_id):
    """
    Collect NPU info by the device_id.

    Args:
        device_id (int): The specific device id.

    Returns:
        dict, the NPU info.

    Raises:
        RuntimeError, when querying dsmi returning non-zero.
    """
    kb_to_mb, memory_threshold, success = 1024, 4, [True] * 7
    success[0], health = dsmi_get_device_health(device_id)
    success[1], hbm_info = dsmi_get_hbm_info(device_id)
    success[2], chip_info = dsmi_get_chip_info(device_id)
    success[3], ip_addr = dsmi_get_device_ip_address(device_id)
    success[4], aicore_rate = dsmi_get_device_utilization_rate(device_id, 2)
    success[5], power_info = dsmi_get_device_power_info(device_id)
    success[6], temperature = dsmi_get_device_temperature(device_id)
    return {
        'chip_name': chip_info.get('chip_name'),
        'device_id': device_id,
        'available': all(success) and health == 0 and hbm_info.get('memory_usage', 0) // kb_to_mb < memory_threshold,
        'health': health,
        'ip_address': ip_addr.get('ip_address'),
        'aicore_rate': aicore_rate,
        'hbm_info': {
            'memory_size': hbm_info.get('memory_size') // kb_to_mb,
            'memory_usage': hbm_info.get('memory_usage') // kb_to_mb
        },
        'power': power_info.get('power'),
        'temperature': temperature,
        'success': all(success)
    }


try:
    libsmi = CDLL('libdrvdsmi_host.so')
except OSError:
    logger.info('Failed to load libdrvdsmi_host.so.')
    libsmi = None

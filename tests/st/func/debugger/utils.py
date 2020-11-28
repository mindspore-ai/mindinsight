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
"""Test debugger server utils."""
import json
import os
import time

from tests.st.func.debugger.conftest import DEBUGGER_EXPECTED_RESULTS, DEBUGGER_BASE_URL
from tests.utils.tools import compare_result_with_file, get_url


def check_state(app_client, server_state='waiting'):
    """Check if the Server is ready."""
    url = 'retrieve'
    body_data = {'mode': 'all'}
    max_try_times = 30
    count = 0
    flag = False
    while count < max_try_times:
        res = get_request_result(app_client, url, body_data)
        state = res.get('metadata', {}).get('state')
        if state == server_state:
            flag = True
            break
        count += 1
        time.sleep(0.1)
    assert flag is True


def get_request_result(app_client, url, body_data, method='post', expect_code=200, full_url=False):
    """Get request result."""
    if not full_url:
        real_url = os.path.join(DEBUGGER_BASE_URL, url)
    else:
        real_url = url
    if method == 'post':
        response = app_client.post(real_url, data=json.dumps(body_data))
    else:
        real_url = get_url(real_url, body_data)
        response = app_client.get(real_url)
    assert response.status_code == expect_code
    res = response.get_json()
    return res


def send_and_compare_result(app_client, url, body_data, expect_file=None, method='post', full_url=False):
    """Send and compare result."""
    res = get_request_result(app_client, url, body_data, method=method, full_url=full_url)
    delete_random_items(res)
    if expect_file:
        real_path = os.path.join(DEBUGGER_EXPECTED_RESULTS, 'restful_results', expect_file)
        compare_result_with_file(res, real_path)


def send_and_save_result(app_client, url, body_data, file_path, method='post'):
    """Send and save result."""
    res = get_request_result(app_client, url, body_data, method=method)
    delete_random_items(res)
    real_path = os.path.join(DEBUGGER_EXPECTED_RESULTS, 'restful_results', file_path)
    json.dump(res, open(real_path, 'w'))


def delete_random_items(res):
    """delete the random items in metadata."""
    if res.get('metadata'):
        if res['metadata'].get('ip'):
            res['metadata'].pop('ip')
        if res['metadata'].get('pos'):
            res['metadata'].pop('pos')
        if res['metadata'].get('debugger_version') and res['metadata']['debugger_version'].get('mi'):
            res['metadata']['debugger_version'].pop('mi')

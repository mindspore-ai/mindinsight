#!/bin/bash
# Copyright 2020 Huawei Technologies Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -e

SCRIPT_BASEDIR=$(realpath "$(dirname "$0")")

build_ui() {
    cd "$(realpath "$SCRIPT_BASEDIR/../../mindinsight/ui")" || exit

    if ! command -v npm; then
        command npm
    fi

    rm -rf dist
    mkdir -p patches
    PATCH_PATH=$(realpath "$SCRIPT_BASEDIR/../../third_party/patch/axios+0.19.2.patch")
    cp $PATCH_PATH patches/

    npm config set strict-ssl false
    npm config set unsafe-perm true
    npm config set user 0

    npm install --loglevel=error
    npm run build

    if [ ! -f "dist/index.html" ]; then
        echo "dist does not have file index.html, build failed"
        exit 1
    fi

    cp node_modules/@hpcc-js/wasm/dist/graphvizlib.wasm dist/static/js
}

build_ui

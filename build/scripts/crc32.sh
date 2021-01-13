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

THIRD_PARTY_DIR=$(realpath "$SCRIPT_BASEDIR/../../third_party")
MINDINSIGHT_DIR=$(realpath "$SCRIPT_BASEDIR/../../mindinsight")
BUILDDIR="$(dirname "$SCRIPT_BASEDIR")/build_securec"

build_securec() {
    [ -n "$BUILDDIR" ] && rm -rf "$BUILDDIR"
    mkdir "$BUILDDIR"
    cd "$BUILDDIR" || exit
    if ! command -v cmake; then
        command cmake
    fi
    cmake ../..
    make
}

clean_securec() {
    [ -n "$BUILDDIR" ] && rm -rf "$BUILDDIR"
}

build_crc32() {
    DATAVISUAL_DIR=$(realpath "$SCRIPT_BASEDIR/../../mindinsight/datavisual")
    CRC32_SOURCE_DIR="$DATAVISUAL_DIR/utils/crc32"
    CRC32_OUTPUT_DIR="$DATAVISUAL_DIR/utils"
    CRC32_SO_FILE="crc32$(python3-config --extension-suffix)"

    cd "$CRC32_SOURCE_DIR" || exit

    if ! command -v c++; then
        command c++
    fi

    if command -v python3; then
        PYTHON=python3
    elif command -v python; then
        PYTHON=python
    else
        command python3
    fi

    if ! "$PYTHON" -c 'import sys; assert sys.version_info >= (3, 7)' &>/dev/null; then
        echo "Python 3.7 or higher is required. You are running $("$PYTHON" -V)"
        exit 1
    fi

    rm -f "$CRC32_SOURCE_DIR/$CRC32_SO_FILE"
    rm -f "$CRC32_OUTPUT_DIR/$CRC32_SO_FILE"

    read -ra PYBIND11_INCLUDES <<< "$($PYTHON -m pybind11 --includes)"
    if [ ! -n "${PYBIND11_INCLUDES[0]}" ]; then
        echo "pybind11 is required"
        exit 1
    fi

    c++ -O2 -O3 -shared -std=c++11 -fPIC -fstack-protector-all -D_FORTIFY_SOURCE=2 \
        -Wno-maybe-uninitialized -Wno-unused-parameter -Wall -Wl,-z,relro,-z,now,-z,noexecstack \
        -I"$MINDINSIGHT_DIR" -I"$THIRD_PARTY_DIR" "${PYBIND11_INCLUDES[0]}" "${PYBIND11_INCLUDES[1]}" \
        -o "$CRC32_SO_FILE" crc32.cc "$BUILDDIR/libsecurec.a"

    if [ ! -f "$CRC32_SO_FILE" ]; then
        echo "$CRC32_SO_FILE file does not exist, build failed"
        exit 1
    fi

    mv "$CRC32_SO_FILE" "$CRC32_OUTPUT_DIR"
}

build_securec

build_crc32

clean_securec

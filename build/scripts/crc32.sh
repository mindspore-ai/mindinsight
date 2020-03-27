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

SCRIPT_BASEDIR=$(cd "$(dirname "$0")" || exit; pwd)

THIRD_PARTY_DIR=$(realpath "${SCRIPT_BASEDIR}/../../third_party")
SECUREC_SOURCE_DIR="${THIRD_PARTY_DIR}/securec"

build_securec() {
    CMAKE=$(command -v cmake)
    if [ -z "${CMAKE}" ]; then
        echo "Could not find cmake command"
        exit 1
    fi

    cd "${SECUREC_SOURCE_DIR}" || exit
    rm -rf build
    mkdir build
    cd build || exit
    ${CMAKE} ..
    make
    cd - >/dev/null 2>&1 || exit
}

build_crc32() {
    CPP=$(command -v c++)
    if [ -z "${CPP}" ]; then
        echo "Could not find c++ command"
        exit 1
    fi

    PYTHON=$(command -v python3 || command -v python)
    if [ -z "${PYTHON}" ]; then
        echo "Could not find python3 or python command"
        exit 1
    fi
    PYTHON_VERSION=$(${PYTHON} -c "import platform; print(platform.python_version())" | grep '^3.*')
    if [ -z "${PYTHON_VERSION}" ]; then
        echo "Could not find Python 3"
        exit 1
    fi

    DATAVISUAL_DIR=$(realpath "${SCRIPT_BASEDIR}/../../mindinsight/datavisual")
    CRC32_SOURCE_DIR="${DATAVISUAL_DIR}/utils/crc32"
    CRC32_OUTPUT_DIR="${DATAVISUAL_DIR}/utils"
    CRC32_SO_FILE="crc32$(python3-config --extension-suffix)"

    rm -f "${CRC32_SOURCE_DIR}/${CRC32_SO_FILE}"
    rm -f "${CRC32_OUTPUT_DIR}/${CRC32_SO_FILE}"
    cd "${CRC32_SOURCE_DIR}" || exit
    PYBIND11_INCLUDES=$(${PYTHON} -m pybind11 --includes)
    if [ -z "${PYBIND11_INCLUDES}" ]; then
        echo "Could not find pybind11 module"
        exit 1
    fi

    PYTHON_INCLUDE=$(echo "${PYBIND11_INCLUDES}" | awk '{print $1}' | sed "s/^-I//g")
    PYTHON_HEADERS=$(echo "${PYBIND11_INCLUDES}" | awk '{print $2}' | sed "s/^-I//g")
    ${CPP} -O2 -O3 -shared -std=c++11 -fPIC -fstack-protector-all -D_FORTIFY_SOURCE=2 \
      -Wno-maybe-uninitialized -Wno-unused-parameter -Wall -Wl,-z,relro,-z,now,-z,noexecstack \
      -I"${THIRD_PARTY_DIR}" -I"${DATAVISUAL_DIR}/utils" -I"${PYTHON_INCLUDE}" -I"${PYTHON_HEADERS}" \
      -o "${CRC32_SO_FILE}" crc32.cc "${SECUREC_SOURCE_DIR}/build/src/libsecurec.a"

    if [ ! -f "${CRC32_SO_FILE}" ]; then
        echo "crc so file does not exist, build failed"
        exit 1
    fi
    mv "${CRC32_SO_FILE}" "${CRC32_OUTPUT_DIR}"
}

cd "${SCRIPT_BASEDIR}" || exit
build_securec

cd "${SCRIPT_BASEDIR}" || exit
build_crc32

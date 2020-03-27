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

SCRIPT_BASEDIR=$(
    cd "$(dirname "$0")" || exit
    pwd
)

rename_wheel() {
    VERSION="$1"
    PACKAGE_LIST=$(ls mindinsight-*-any.whl) || exit
    for PACKAGE_ORIG in ${PACKAGE_LIST}; do
        MINDINSIGHT_VERSION=$(echo "${PACKAGE_ORIG}" | awk -F"-" '{print $2}')
        PYTHON_VERSION_NUM=$(echo "${VERSION}" | awk -F"." '{print $1$2}')
        PYTHON_VERSION_TAG="cp${PYTHON_VERSION_NUM}"
        PYTHON_ABI_TAG="cp${PYTHON_VERSION_NUM}m"
        OS_NAME=$(uname | tr '[:upper:]' '[:lower:]')
        MACHINE_TAG="${OS_NAME}_$(uname -i)"
        PACKAGE_NEW="mindinsight-${MINDINSIGHT_VERSION}-${PYTHON_VERSION_TAG}-${PYTHON_ABI_TAG}-${MACHINE_TAG}.whl"
        mv "${PACKAGE_ORIG}" "${PACKAGE_NEW}"
    done
}

build_wheel() {
    PROJECT_BASEDIR=$(cd "$(dirname "$SCRIPT_BASEDIR")" || exit; pwd)
    cd "${PROJECT_BASEDIR}" || exit

    if [ $# -gt 0 ]; then
        if [ "$1" = "clean" ]; then
            echo "start cleaning mindinsight"
            clean_files
            echo "clean mindinsight done"
        else
            echo "unknown command: $1"
        fi
        exit
    fi

    echo "start building mindinsight"
    clean_files

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

    rm -f output
    mkdir output

    ${PYTHON} setup.py bdist_wheel
    if [ ! -x "dist" ]; then
        echo "Build failed"
        exit 1
    fi

    mv dist/mindinsight-*-any.whl output/

    cd output || exit
    rename_wheel "${PYTHON_VERSION}"
    cd - >/dev/null 2>&1 || exit

    clean_files

    echo "Build success, output directory is: ${PROJECT_BASEDIR}/output"
}

clean_files() {
    rm -rf third_party/build
    rm -rf build/lib
    rm -rf build/bdist.*
    rm -rf mindinsight.egg-info
    rm -rf dist
}

show_usage() {
    echo "Build mindinsight"
    echo ""
    echo "usage: build.sh [-h] [clean]"
    echo ""
    echo "options:"
    echo "  -h          show usage info"
    echo "  clean       clean build files"
}

check_opts() {
    while getopts ':h' OPT; do
        case "$OPT" in
        h)
            show_usage
            exit 0
            ;;
        \?)
            show_usage
            exit 1
            ;;
        esac
    done
}

check_opts "$@"

cd "${SCRIPT_BASEDIR}" || exit
build_wheel "$@"

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

PROJECT_BASEDIR=$(dirname "$SCRIPT_BASEDIR")

write_checksum() {
    cd "$PROJECT_BASEDIR/output" || exit
    PACKAGE_LIST=$(ls mindinsight-*.whl) || exit
    for PACKAGE_NAME in $PACKAGE_LIST; do
        sha256sum -b "$PACKAGE_NAME" >"$PACKAGE_NAME.sha256"
    done
}

build_wheel() {

    cd "$PROJECT_BASEDIR" || exit

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

    if command -v python3 > /dev/null; then
        PYTHON=python3
    elif command -v python > /dev/null; then
        PYTHON=python
    else
        command python3
    fi

    if ! "$PYTHON" -c 'import sys; assert sys.version_info >= (3, 7)' > /dev/null; then
        echo "Python 3.7 or higher is required. You are running $("$PYTHON" -V)"
        exit 1
    fi

    rm -rf output

    "$PYTHON" setup.py bdist_wheel
    if [ ! -x "dist" ]; then
        echo "Build failed"
        exit 1
    fi

    mv dist output

    write_checksum
    clean_files

    echo "Build success, output directory is: $PROJECT_BASEDIR/output"
}

clean_files() {
    cd "$PROJECT_BASEDIR" || exit
    rm -rf build/lib
    rm -rf build/bdist.*
    rm -rf mindinsight.egg-info
}

show_usage() {
    echo "Build mindinsight"
    echo ""
    echo "usage: build.sh [-h] [clean]"
    echo ""
    echo "options:"
    echo "  -h          show this help message and exit"
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

build_wheel "$@"

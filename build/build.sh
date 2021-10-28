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
    cd output || exit
    WHEEL_LIST=$(ls *.whl) || exit
    for WHEEL_NAME in $WHEEL_LIST; do
        sha256sum -b "$WHEEL_NAME" >"$WHEEL_NAME.sha256"
    done
    cd .. || exit
}

build_wheel() {
    echo "start building"
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
}

build_mindinsight() {
    cd $PROJECT_BASEDIR || exit
    build_wheel
}

build_mindconverter() {
    cd $PROJECT_BASEDIR/ecosystem_tools/mindconverter || exit
    build_wheel
    mkdir -p $PROJECT_BASEDIR/output
    cp output/*.whl $PROJECT_BASEDIR/output
    cp output/*.whl.sha256 $PROJECT_BASEDIR/output
    cd $PROJECT_BASEDIR || exit
}

build_entry() {
    if [ $# -eq 0 ]; then
        build_mindinsight
        build_mindconverter
        exit
    fi

    if [ "$1" = "clean" ]; then
        echo "Cleaning starts"
        cd $PROJECT_BASEDIR || exit
        clean_files
        cd $PROJECT_BASEDIR/ecosystem_tools/mindconverter || exit
        clean_files
        echo "Cleaning done"
        exit
    fi

    if [ "$1" = "mindinsight" ]; then
        build_mindinsight
    elif [ "$1" = "mindconverter" ]; then
        build_mindconverter
    else
        echo "unknown command: $1"
        exit
    fi

    echo "Build success, output directory is: $PROJECT_BASEDIR/output"
}

clean_files() {
    rm -rf *.egg-info

    if [ -d build ];then
        rm -rf build/lib
        rm -rf build/bdist.*
        if [ "$(ls -A build)" = "" ]; then
            rm -rf build
        fi
    fi
}

show_usage() {
    echo "Build mindinsight"
    echo ""
    echo "usage: build.sh [-h] [clean]"
    echo ""
    echo "options:"
    echo "  -h              show this help message and exit"
    echo "  clean           clean build files"
    echo "  mindinsight     build mindinsight"
    echo "  mindconverter   build mindconverter"
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
build_entry "$@"

#!/bin/bash
# Copyright 2020-2024 Huawei Technologies Co., Ltd.
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

PROJECT_DIR=$(realpath "$SCRIPT_BASEDIR/../../")
ST_PATH="$PROJECT_DIR/tests/st"

PYTEST_MARK=""

show_usage() {
    echo "Run test cases for st."
    echo ""
    echo "usage: runtest.sh [-h] [-m <PYTEST MARK>]"
    echo ""
    echo "options:"
    echo "  -h          show usage info"
    echo "  -m <PYTEST MARK>       mark of pytest."

}

check_opts() {
    while getopts ":hm:" opt; do
        case $opt in
        h)
            show_usage
            exit 0
            ;;
        m)
            PYTEST_MARK="$OPTARG"
            ;;
        \?)
            show_usage
            exit 1
            ;;
        esac
    done
}

before_run_test() {
    echo "Before run tests."
    export PYTHONPATH=$PROJECT_DIR:$PYTHONPATH
}

after_run_test() {
    echo "After run tests."
    echo "End to run tests."
}

run_mindinsight_test() {
    for dir in "$ST_PATH"/*; do
        if [ ! -d "$dir" ] || [ "$dir" = "$ST_PATH/__pycache__" ]; then
            continue
        fi

        for sub_dir in "$dir"/*; do
            if [ ! -d "$sub_dir" ] || [ "$sub_dir" = "$dir/__pycache__" ]; then
                continue
            fi
            echo "Run test for path: $sub_dir"
            python -m pytest "$sub_dir" --disable-pytest-warnings -m "$PYTEST_MARK"
        done
    done

    echo "Test mindinsight all use cases success."
}


run_test() {
    echo "Start to run test."
    cd "$PROJECT_DIR" || exit

    if [ $# -eq 0 ]; then
        run_mindinsight_test
    else
        if  [ $1 == "mindinsight" ]; then
            run_mindinsight_test
        fi
    fi
}

check_opts "$@"
before_run_test
run_test "$@"
after_run_test

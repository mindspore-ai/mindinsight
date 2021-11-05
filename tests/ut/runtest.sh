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

PROJECT_DIR=$(realpath "$SCRIPT_BASEDIR/../../")
UT_PATH="$PROJECT_DIR/tests/ut"

before_run_test() {
    echo "Before run tests."
    export PYTHONPATH=$PROJECT_DIR:$PYTHONPATH
}

after_run_test() {
    echo "After run tests."
    echo "End to run test."
}

run_mindinsight_test() {
    pytest "$UT_PATH"
    echo "Test mindinsight all use cases success."
}

run_mindconverter_test() {
    cd "$PROJECT_DIR/tests/ecosystem_tools/mindconverter" || exit
    bash tests/ut/runtest.sh
    echo "Test mindconverter all use cases success."
}

run_test() {
    echo "Start to run test."
    cd "$PROJECT_DIR" || exit

    if [ $# -eq 0 ]; then
        run_mindinsight_test
        run_mindconverter_test
    else
        if  [ $1 == "mindinsight" ]; then
            run_mindinsight_test
        elif [ $1 == "mindconverter" ]; then
            run_mindconverter_test
        fi
    fi
}

before_run_test
run_test "$@"
after_run_test

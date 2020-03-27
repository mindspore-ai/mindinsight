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

SCRIPT_BASEDIR=$(cd "$(dirname "$0")" || exit; pwd)
PROJECT_DIR=$(realpath "${SCRIPT_BASEDIR}/../../")
CRC32_SCRIPT_PATH="${PROJECT_DIR}/build/scripts/crc32.sh"
CRC32_OUTPUT_DIR="${PROJECT_DIR}/mindinsight/datavisual/utils/"
ST_PATH="${PROJECT_DIR}/tests/st"
IS_BUILD_CRC=""

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
    while getopts ":hm:" opt
    do
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

build_crc32() {
    echo "Start to check crc32."
    if [ -d $CRC32_OUTPUT_DIR ];then
      cd $CRC32_OUTPUT_DIR
      result=$(find . -maxdepth 1 -name "crc32*.so")
      if [ -z $result ];then
        echo "Start to build crc32."
        IS_BUILD_CRC="true"
        bash $CRC32_SCRIPT_PATH
      fi
    fi

}

clean_crc32() {
  echo "Start to clean crc32."
  if [ ! -z $IS_BUILD_CRC ];then
    rm $CRC32_OUTPUT_DIR/crc32*.so -f
  fi
}

before_run_test() {
    echo "Before run tests."
    export PYTHONPATH=$PROJECT_DIR:$PYTHONPATH
    build_crc32
}

after_run_test() {
    echo "After run tests."
    clean_crc32

    echo "End to run tests."
}

run_test() {
    echo "Start to run test."
    cd $PROJECT_DIR

    for dir in $(ls -l $ST_PATH |awk '/^d/ {print $NF}')
    do
        if [ $dir = "__pycache__" ];then
          continue
        fi

        for sub_dir in $(ls -l $ST_PATH/$dir |awk '/^d/ {print $NF}')
        do
            if [ $sub_dir = "__pycache__"  ];then
              continue
            fi
            echo "Run test for path: $ST_PATH/$dir/$sub_dir"
            pytest $ST_PATH/$dir/$sub_dir --disable-pytest-warnings -m "$PYTEST_MARK"
        done
    done

    echo "Test all use cases success."
}

check_opts "$@"
before_run_test
run_test
after_run_test

#!/bin/bash
# Copyright 2021 Huawei Technologies Co., Ltd.
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

start_dir=$(pwd)
cd "$(dirname "$0")"/../../ecosystem_tools/VulkanVision

if [[ ! -d  "SPIRV-Tools" ]]
then
    echo "Cloning SPIRV-Tools"
    git clone https://github.com/KhronosGroup/SPIRV-Tools
    cp st-patches/*.patch SPIRV-Tools
    cd SPIRV-Tools
    git checkout 17ffa89097b26efeb323e6963220326b5ffb2baf
    # These are the current stable changes and can be updated with new releases
    git apply 0001-spirv-opt-Add-auto-inst-passes.patch
    rm *.patch
    cd ..
fi

if [[ ! -d  "Vulkan-ValidationLayers" ]] 
then
    echo "Cloning Vulkan-ValidationLayers"
    git clone https://github.com/KhronosGroup/Vulkan-ValidationLayers
    cp vv-patches/*.patch Vulkan-ValidationLayers
    cd Vulkan-ValidationLayers
    git checkout aa076dae88e282d7b6cada4f900b2fa7dac8ed08
    # These are the current stable changes and can be updated with new releases
    git apply 0001-layers-Added-auto-inst-layers.patch
    rm *.patch
    cd ..
fi


build_dir=$(pwd)

echo "Building SPIRV-Tools"
cd SPIRV-Tools
git clone https://github.com/KhronosGroup/SPIRV-Headers.git external/spirv-headers
cd external/spirv-headers
git checkout f027d53ded7e230e008d37c8b47ede7cd308e19d
cd ../..
git clone https://github.com/google/effcee.git external/effcee
git clone https://github.com/google/re2.git external/re2
mkdir build
cd build
mkdir install
cmake -DCMAKE_BUILD_TYPE=release -DCMAKE_INSTALL_PREFIX=install ..
cmake --build . --target install --config Release -- -j 4
cd $build_dir

echo "Building Vulkan-ValidationLayers"
cd Vulkan-ValidationLayers
mkdir build 
cd build
mkdir install
python ../scripts/update_deps.py --config release
cmake -DCMAKE_BUILD_TYPE=release -DCMAKE_INSTALL_PREFIX=install -DSPIRV_TOOLS_INSTALL_DIR=$build_dir/SPIRV-Tools/build/install -C helper.cmake ..
cmake --build . --target install --config Release -- -j 4

echo "Build completed at $build_dir"!

cd $start_dir
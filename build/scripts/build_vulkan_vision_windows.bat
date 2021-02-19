REM Copyright 2021 Huawei Technologies Co., Ltd.
REM
REM Licensed under the Apache License, Version 2.0 (the "License");
REM you may not use this file except in compliance with the License.
REM You may obtain a copy of the License at
REM
REM     http://www.apache.org/licenses/LICENSE-2.0
REM
REM Unless required by applicable law or agreed to in writing, software
REM distributed under the License is distributed on an "AS IS" BASIS,
REM WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
REM See the License for the specific language governing permissions and
REM limitations under the License.

@echo off

set start_dir=%cd%
cd %~dp0..\..\ecosystem_tools\VulkanVision

IF NOT EXIST SPIRV-Tools (
    echo Cloning SPIRV-Tools
    git clone https://github.com/KhronosGroup/SPIRV-Tools --branch v2020.6
    copy st-patches\*.patch SPIRV-Tools
    cd SPIRV-Tools
    REM These are the current stable changes and can be updated with new releases
    git apply 0001-spirv-opt-Add-auto-inst-passes.patch
    del *.patch
    git clone https://github.com/KhronosGroup/SPIRV-Headers.git external\spirv-headers --branch 1.5.4.raytracing.fixed
    git clone https://github.com/google/effcee.git external\effcee --branch v2019.1
    git clone https://github.com/google/re2.git external\re2 --branch 2020-11-01
    cd ..
)

IF NOT EXIST Vulkan-ValidationLayers (
    echo Cloning Vulkan-ValidationLayers
    git clone https://github.com/KhronosGroup/Vulkan-ValidationLayers --branch sdk-1.2.162
    copy vv-patches\*.patch Vulkan-ValidationLayers
    cd Vulkan-ValidationLayers
    REM These are the current stable changes and can be updated with new releases
    git apply 0001-layers-Added-auto-inst-layers.patch
    del *.patch
    cd ..
)

set build_dir=%cd%

echo Building SPIRV-Tools
cd SPIRV-Tools
mkdir build
cd build
mkdir install
cmake -DCMAKE_BUILD_TYPE=release -DCMAKE_INSTALL_PREFIX=install ..
cmake --build . --target install --config Release
cd %build_dir%

echo Building Vulkan-ValidationLayers
cd Vulkan-ValidationLayers
mkdir build 
cd build
mkdir install
python ../scripts/update_deps.py --config release
cmake -DCMAKE_BUILD_TYPE=release -DCMAKE_INSTALL_PREFIX=install -DSPIRV_TOOLS_INSTALL_DIR=%cd%/../../SPIRV-Tools/build/install -C helper.cmake ..
cmake --build . --target install --config Release

echo Build completed at %build_dir%!

cd %start_dir%
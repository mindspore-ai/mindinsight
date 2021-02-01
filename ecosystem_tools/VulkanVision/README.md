# Vulkan Vision

If Vulkan Vision is useful to you, please cite "Vulkan Vision: Ray Tracing Workload Characterization using Automatic Graphics Instrumentation".

Vulkan Vision is released as patches on the Khronos Group [Vulkan-ValidationLayers](https://github.com/KhronosGroup/Vulkan-ValidationLayers) and [SPIRV-Tools](https://github.com/KhronosGroup/SPIRV-Tools) repositories.

To generate a vvision build:

## Windows

```bat
..\..\build\scripts\build_vulkan_vision_windows.bat
```

## Linux

```bash
../../build/scripts/build_vulkan_vision_linux.sh
```

The completed build will be at `mindinsight/ecosystem_tools/VulkanVision/Vulkan-ValidationLayers/build/install`

V-Vision Documentation will be at `mindinsight/ecosystem_tools/VulkanVision/Vulkan-ValidationLayers/docs/auto_instrument.md`

Documentation for enabling and using Vulkan Validation layers can be found [here](https://vulkan.lunarg.com/doc/sdk/1.2.162.0/windows/layer_configuration.html)
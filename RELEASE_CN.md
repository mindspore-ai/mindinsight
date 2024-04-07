# MindSpore Insight Release Notes

[View English](./RELEASE.md)

## MindInsight 2.3.0-rc1 Release Notes

### 主要特性和增强

#### Profiler

- [BETA] 动态启停profiling，用户可以根据训练情况实时采集profiling 数据，减少采集数据量。
- [BETA] Profiling通信算子耗时矩阵，用户通过分析通信算子耗时矩阵，找出集群通信性能瓶颈。
- [BETA] 提高昇腾环境解析Profiling数据的性能。
- [BETA] 支持离线解析Profiling生成的数据，用户可以先采集数据，然后根据需要再解析数据。
- [BETA] 支持采集HBM、PCIe、l2_cache性能数据，丰富性能分析指标。

#### Dump

- [BETA] Dump保存的统计信息记录MD5值，用户可以通过MD5值确定张量值的微小差异。
- [BETA] Dump支持bfloat16数据类型，支撑用户定位bfloat16类型的算子精度问题。

### 贡献者

感谢以下人员做出的贡献:

Ning Ma, Jiaxing Zhu, Jiarong Ji, Yanming Miao, Nan Wang, XiaoXian Jin, Qingxiang Zang, DaWei Fan, XinYu Shi, KaiDa Qiu, Wei Zhang, XianQi Zhou, Chen Mao, XiHan Peng.

欢迎以任何形式对项目提供贡献！

## MindSpore Insight 2.2.1 Release Notes

### Bug fixes

- [I88AN5] MindSpore Insight适配Numpy高于1.20.0版本。

### 贡献者

感谢以下人员做出的贡献:

Ning Ma, Jiaxing Zhu, Jiarong Ji, Yanming Miao, Nan Wang, XiaoXian Jin, Qingxiang Zang, Yang Luo, TianCi Xiao, DaWei Fan.

欢迎以任何形式对项目提供贡献！

## MindSpore Insight 2.2.0 Release Notes

### 主要特性和增强

#### Profiler

- [STABLE] Profiler支持收集自定义AICPU 算子耗时。
- [Beta] 支持多卡的timeline数据合并能力。

#### Dump

- [Beta] 提供溢出算子的统计能力。

### Bug fixes

- [I7J1LF] 修复Profiler解析数据报IndexError问题。
- [I82CGQ] 修复溢出检测报core dump问题。

### 贡献者

感谢以下人员做出的贡献:

Ning Ma, Jiaxing Zhu, Jiarong Ji, Yanming Miao, Nan Wang, XiaoXian Jin, Qingxiang Zang, Yang Luo, TianCi Xiao, DaWei Fan.

欢迎以任何形式对项目提供贡献！

## MindSpore Insight 2.1.0 Release Notes

### 主要特性和增强

#### Profiler

- [STABLE] Profiler支持收集Host侧各个阶段耗时数据。
- [Beta] Profiler支持收集Host侧各个阶段内存数据。
- [Beta] Profiler支持收集数据处理算子的执行耗时。

### 贡献者

感谢以下人员做出的贡献:

Ning Ma, Jiaxing Zhu, Jiarong Ji, Yanming Miao, Nan Wang, XiaoXian Jin, Qingxiang Zang, Yang Luo, TianCi Xiao, DaWei Fan.

欢迎以任何形式对项目提供贡献！

## MindSpore Insight 2.0.0 Release Notes

### Bug fixes

- [I7BIKO] 修复cube和vector混合场景下Flops不准问题

### 贡献者

感谢以下人员做出的贡献:

Ning Ma, Jiaxing Zhu, Jiarong Ji, Yanming Miao, Nan Wang, XiaoXian Jin, Chuting Liu, Han Gao, Qingxiang Zang.

欢迎以任何形式对项目提供贡献！

## MindSpore Insight 2.0.0-rc1 Release Notes

### 主要特性和增强

#### MindSpore Insight

- [STABLE] MindSpore Insight与Mindspore版本匹配校验。

#### Debugger

- [STABLE] 调试器展示计算图节点数上限可配置。

#### Profiler

- [STABLE] Profiler算子耗时占比使用total time计算。

### Bug fixes

- 修复若干页面展示问题。

### 贡献者

感谢以下人员做出的贡献:

Ning Ma, Chuting Liu, Jiaxing Zhu, Qingxiang Zang, Yaomin Mao.

欢迎以任何形式对项目提供贡献！

## MindInsight 2.0.0-alpha Release Notes

### 主要特性和增强

#### Profiling

- [STABLE] Profiler支持通过环境变量使能
- [STABLE] 提供生成PMU性能数据的接口（Ascend）
- [BETA] PyNative模式下，Profiler算子性能数据准确性优化（Ascend）
- [BETA] Profiler支持PyNative模式基础功能（GPU）
- [STABLE] 支持Msprof二进制工具拉起Mindspore Profiling（Ascend）
- [BETA] Profiling支持动态shape网络（GPU）

#### Dump

- [STABLE] Dump支持动态shape

### 贡献者

感谢以下人员做出的贡献:

Ning Ma, Chuting Liu, Jiaxing Zhu, Qingxiang Zang, Yaomin Mao.

欢迎以任何形式对项目提供贡献！

## MindInsight 1.9.0 Release Notes

### 主要特性和增强

#### Profiling

- [BETA] 并行执行训练性能分析（Ascend）
- [BETA] 性能小助手专家系统 （Ascend）

#### Summary

- [STABLE] 自动识别降精度算子，Ascend场景下，有部分算子最高精度只支持float16，这会导致该类型算子的精度自动下降，该功能用于帮助用户识别出此类降精度算子

#### 兼容性变更

##### 新增API

### 贡献者

感谢以下人员做出的贡献:

Kai Wen, Yue Wang, Ximiao Yu, Ning Ma, Haitao Yang, Han Gao, Chuting Liu, Jiaxing Zhu, Qingxiang Zang.

Special thanks to Zhongwei Wang, Rongchen Zhu, Jiaying Lu, Zhiyong Wang, Yating Wei, Yong Dai, Luoxuan Weng, etc., from State Key Lab of CAD&CG, Zhejiang University led by Prof. Wei Chen, for their contributions of innovative frontend and interaction technology to support parallel training execution analysis module, collective communication analysis module, etc.

欢迎以任何形式对项目提供贡献！

## MindInsight 1.8.0 Release Notes

### 主要特性和增强

#### Profiling

- [STABLE] Profiler支持动态shape算子（Ascend）
- [STABLE] Profiler样例代码按import规范调整

#### Debugger

- [STABLE] dump、固定随机性文档优化

#### 兼容性变更

##### 新增API

- [STABLE] profiler新增算子性能查询接口

### 贡献者

感谢以下人员做出的贡献：

Congli Gao, Longfei Li, Yongxiong Liang, Chongming Liu, Pengting Luo, Yanming Miao, Gongchang Ou, Kai Wen, Yue Wang, Lihua Ye, Ximiao Yu, Yunshu Zhang, Ning Ma, Yihui Zhang, Hong Sheng, Ran Mo, Zhaohong Guo, Tianshu Liang, Shuqiang Jiang, Yanjun Peng, Haitao Yang, Jiabin Liu, Han Gao, Xiaohui Li, Ngaifai Ng, Hui Pan, Weifeng Huang, Yifan Xia, Xuefeng Feng, Yanxi Wei, Yufeng Lv, Maohua He, Chuting Liu, Jiaxing Zhu, Yuanwei Song.

Special thanks to Zhiyong Wang, Zhongwei Wang, Rusheng Pan, Yating Wei, Luoxuan Weng, Rongchen Zhu, Jingli Xu, Qinxian Liu, Haozhe Feng, Tong Xu, etc., from State Key Lab of CAD&CG, Zhejiang University led by Prof. Wei Chen, for their contributions of innovative frontend and interaction technology to support strategy perception including Computational Graph Exploration module, Parallel Strategy Analysis module, etc.

欢迎以任何形式对项目提供贡献！

## MindInsight 1.7.0 Release Notes

### 主要特性及改进

#### Profiling

- [STABLE] GPU上性能调优支持集群迭代轨迹分析 (GPU)
- [BETA] 性能调优支持动态图模式 (Ascend)

#### Debugger

- [STABLE] 调试器监测点检查速度提升

#### Summary

- [STABLE] Summary提供中文API文档
- [STABLE] 官网提供Summary样例代码

### 贡献者

鸣谢：

Congli Gao, Longfei Li, Yongxiong Liang, Chongming Liu, Pengting Luo, Yanming Miao, Gongchang Ou, Kai Wen, Yue Wang, Lihua Ye, Ximiao Yu, Yunshu Zhang, Ning Ma, Yihui Zhang, Hong Sheng, Ran Mo, Zhaohong Guo, Tianshu Liang, Shuqiang Jiang, Yanjun Peng, Haitao Yang, Jiabin Liu, Han Gao, Xiaohui Li, Ngaifai Ng, Hui Pan, Weifeng Huang, Yifan Xia, Xuefeng Feng, Yanxi Wei, Yufeng Lv, Maohua He, Chuting Liu, Jiaxing Zhu, Yuanwei Song.

特别鸣谢：

Zhiyong Wang, Zhongwei Wang, Rusheng Pan, Yating Wei, Luoxuan Weng, Rongchen Zhu, Jingli Xu, Qinxian Liu, Haozhe Feng, Tong Xu, etc., from State Key Lab of CAD&CG, Zhejiang University led by Prof. Wei Chen, for their contributions of innovative frontend and interaction technology to support strategy perception including Computational Graph Exploration module, Parallel Strategy Analysis module, etc.

欢迎以任何形式贡献代码及建议！

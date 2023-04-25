# MindInsight Release Notes

[View English](./RELEASE.md)

## MindInsight 2.0.0 Release Notes

### 主要特性和增强

#### MindInsight

- [STABLE] MindInsight与Mindspore版本匹配校验。

#### Debugger

- [STABLE] 调试器展示计算图节点数上限可配置。

#### Profiler

- [STABLE] Profiler算子耗时占比使用total time计算。

#### Bug fixes

- 修复若干页面展示问题。

### Contributors

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

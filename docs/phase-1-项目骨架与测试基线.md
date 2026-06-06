# Phase 1: 项目骨架与测试基线

## 1. 阶段目标

先把项目的工程骨架、运行入口、模块边界和测试基线搭起来，为后续每个核心子系统提供稳定落点。

这一阶段不追求功能多，而追求以下三件事：

- 项目目录结构合理
- 核心接口先定义清楚
- 测试框架和第一批回归测试先落地

## 2. 范围

本阶段包含：

- Python 包结构
- 配置对象与常量定义
- 统一错误模型
- 基础日志与调试开关
- 测试目录结构与执行方式

本阶段不包含：

- 真正的文件写入逻辑
- 真正的进程调度
- 真正的 Shell 命令执行

## 3. 建议目录

```text
src/tinyos/
  __init__.py
  config.py
  errors.py
  kernel/
  storage/
  vfs/
  shell/
  observability/

tests/
  unit/
  integration/
  e2e/
```

## 4. 功能需求

### 4.1 配置系统

需要一个统一配置对象，至少包含：

- 磁盘初始大小
- 磁盘扩容步长
- 磁盘最大上限
- 块大小
- 页大小
- 是否启用调试日志

### 4.2 错误模型

定义统一异常类型，例如：

- `TinyOSError`
- `PathNotFoundError`
- `AlreadyExistsError`
- `DiskFullError`
- `PermissionDeniedError`
- `InvalidCommandError`

### 4.3 可测试接口基线

需要先定义但可以暂时留空或最小实现的接口：

- `ExpandableVirtualDisk`
- `VirtualFileSystem`
- `KernelScheduler`
- `Shell`
- `KernelStats`

## 5. TDD 要求

本阶段必须先建立测试约束，而不是等功能写多了再补。

至少要有以下测试：

- 配置默认值测试
- 非法配置拒绝测试
- 错误类型层级测试
- 核心对象可构造测试
- 统一模块导入测试

## 6. 验收标准

- 项目存在清晰的 `src/` 与 `tests/` 结构
- 测试命令可运行
- 至少有一批基础测试先失败后转绿
- 后续 Phase 的关键类名和职责已经固定

## 7. 风险

- 如果 Phase 1 省略，后续很容易一边写功能一边改接口，导致测试和实现同时失控
- 如果错误模型不统一，后续 Shell 很难稳定映射成用户可理解的错误输出

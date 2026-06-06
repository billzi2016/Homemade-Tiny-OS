# Doc Tree

## 1. 文档总览

```text
docs/
├── tiny-os-prd.md
├── doc-tree.md
├── git-workflow.md
├── tasks.md
├── phase-1-项目骨架与测试基线.md
├── phase-2-可扩展虚拟磁盘与块设备.md
├── phase-3-虚拟文件系统与元数据索引.md
├── phase-4-进程调度-shell与系统内省.md
└── phase-5-可靠性权限与可扩展能力.md
```

## 2. 各文档用途

- `tiny-os-prd.md`
  - 总体产品需求文档
  - 定义目标、边界、实现粒度、测试纪律和阶段划分

- `doc-tree.md`
  - 文档导航入口
  - 用于说明各文档职责，避免后续扩展时文档体系混乱

- `git-workflow.md`
  - Git 提交与里程碑管理规则
  - 定义按 Phase、按测试点提交的节奏

- `tasks.md`
  - 项目任务清单
  - 使用 Markdown checkbox 追踪进度
  - 默认按 TDD 顺序组织任务

- `phase-1-项目骨架与测试基线.md`
  - 工程骨架、统一错误模型、配置、测试基线

- `phase-2-可扩展虚拟磁盘与块设备.md`
  - 可扩展虚拟磁盘、块读写、块分配、容量上限

- `phase-3-虚拟文件系统与元数据索引.md`
  - VFS、路径解析、inode、目录项、索引模块、文件数据映射

- `phase-4-进程调度-shell与系统内省.md`
  - 调度器、Shell、`top`、`sysstat`、`dmesg`

- `phase-5-可靠性权限与可扩展能力.md`
  - 空间保护、恢复、一致性、权限、插件式扩展与替换能力

## 3. 使用方式

- 想理解全局目标时，先看 `tiny-os-prd.md`
- 想按阶段推进开发时，按 `phase-1` 到 `phase-5` 顺序阅读
- 想直接进入执行时，优先看 `tasks.md`

## 4. 维护规则

- 新增设计文档时，先更新本文件
- 新增任务或完成任务时，同步更新 `tasks.md`
- 如果 Phase 内容发生明显变化，应同时回写 `tiny-os-prd.md`

# Project Tree

## 1. 文档目的

本文档用于定义 `Homemade-Tiny-OS` 的**整体项目目录树**，而不是只描述文档目录。

需要明确两件事：

- 当前仓库里已经存在什么
- 后续 Tiny OS 完整实现时，推荐长成什么样

因此本文档分为：

- 当前目录树
- 目标目录树

## 2. 当前目录树

当前仓库中，已经存在的主要内容如下：

```text
Homemade-Tiny-OS/
└── docs/
    ├── docs-tree.md
    ├── git-workflow.md
    ├── phase-1-项目骨架与测试基线.md
    ├── phase-2-可扩展虚拟磁盘与块设备.md
    ├── phase-3-虚拟文件系统与元数据索引.md
    ├── phase-4-进程调度-shell与系统内省.md
    ├── phase-5-可靠性权限与可扩展能力.md
    ├── project-tree.md
    ├── tasks.md
    └── tiny-os-prd.md
```

## 3. 目标目录树

下面是推荐的 Tiny OS 完整项目结构。

```text
Homemade-Tiny-OS/
├── docs/
│   ├── docs-tree.md
│   ├── git-workflow.md
│   ├── phase-1-项目骨架与测试基线.md
│   ├── phase-2-可扩展虚拟磁盘与块设备.md
│   ├── phase-3-虚拟文件系统与元数据索引.md
│   ├── phase-4-进程调度-shell与系统内省.md
│   ├── phase-5-可靠性权限与可扩展能力.md
│   ├── project-tree.md
│   ├── tasks.md
│   └── tiny-os-prd.md
├── src/
│   └── tinyos/
│       ├── __init__.py
│       ├── config.py
│       ├── errors.py
│       ├── constants.py
│       ├── boot.py
│       ├── kernel/
│       │   ├── __init__.py
│       │   ├── scheduler.py
│       │   ├── process.py
│       │   ├── signals.py
│       │   └── syscalls.py
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── disk.py
│       │   ├── block_allocator.py
│       │   ├── superblock.py
│       │   └── checkpoint.py
│       ├── vfs/
│       │   ├── __init__.py
│       │   ├── filesystem.py
│       │   ├── inode.py
│       │   ├── directory_entry.py
│       │   ├── path.py
│       │   ├── permissions.py
│       │   └── index/
│       │       ├── __init__.py
│       │       ├── interface.py
│       │       └── bplustree_adapter.py
│       ├── memory/
│       │   ├── __init__.py
│       │   ├── manager.py
│       │   ├── page_table.py
│       │   └── replacement.py
│       ├── shell/
│       │   ├── __init__.py
│       │   ├── repl.py
│       │   ├── parser.py
│       │   ├── commands/
│       │   │   ├── __init__.py
│       │   │   ├── fs_commands.py
│       │   │   ├── process_commands.py
│       │   │   └── monitor_commands.py
│       │   └── registry.py
│       └── observability/
│           ├── __init__.py
│           ├── stats.py
│           ├── dmesg.py
│           └── formatters.py
├── tests/
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_errors.py
│   │   ├── test_disk.py
│   │   ├── test_block_allocator.py
│   │   ├── test_path.py
│   │   ├── test_inode.py
│   │   ├── test_directory_index.py
│   │   ├── test_scheduler.py
│   │   └── test_shell_parser.py
│   ├── integration/
│   │   ├── test_disk_recovery.py
│   │   ├── test_vfs_read_write.py
│   │   ├── test_vfs_persistence.py
│   │   ├── test_scheduler_and_shell.py
│   │   └── test_permissions.py
│   └── e2e/
│       ├── test_shell_basic_flow.py
│       ├── test_monitor_commands.py
│       └── test_disk_full_flow.py
├── scripts/
│   ├── run_tinyos.py
│   └── inspect_disk.py
├── assets/
│   └── sample_disk_images/
├── .gitignore
├── README.md
├── pyproject.toml
└── tinyos.disk
```

## 4. 目录职责说明

### 4.1 `docs/`

负责保存产品需求、阶段规划、任务清单、Git 规则和项目结构说明。

### 4.2 `src/tinyos/`

负责保存 Tiny OS 的实际实现代码。

### 4.3 `src/tinyos/kernel/`

负责：

- 进程模型
- 调度逻辑
- syscall 分发
- 内核级状态变更

### 4.4 `src/tinyos/storage/`

负责：

- 可扩展虚拟磁盘
- 块分配
- 超级块
- 持久化恢复
- 检查点或简化一致性机制

### 4.5 `src/tinyos/vfs/`

负责：

- 路径解析
- inode 与目录项
- 文件系统接口
- 权限检查
- 目录索引适配

### 4.6 `src/tinyos/vfs/index/`

这是目录索引模块层。

要求：

- 对上暴露统一接口
- 对下可接成熟库实现
- 不让上层直接耦合具体 B+ 树库

### 4.7 `src/tinyos/memory/`

负责：

- 页面管理
- 页表映射
- 页面置换策略

### 4.8 `src/tinyos/shell/`

负责：

- REPL 循环
- 命令解析
- 命令注册与分发
- 文件系统命令、进程命令、监控命令接入

### 4.9 `src/tinyos/observability/`

负责：

- 系统指标
- `dmesg`
- `top`
- `sysstat` 所需格式化输出

### 4.10 `tests/`

按 TDD 原则分层：

- `unit/`：小粒度逻辑和数据结构
- `integration/`：模块协作
- `e2e/`：面向用户命令流的完整验证

### 4.11 `scripts/`

负责一些工程辅助入口，但不能替代系统核心逻辑。

例如：

- 本地启动 Tiny OS
- 检查磁盘镜像内容

## 5. 结构约束

后续实现时，应遵守以下约束：

- `Shell` 不直接操作磁盘文件
- `VFS` 不直接依赖具体索引库对象
- `Kernel` 不越层篡改底层持久化格式
- `tests/` 必须随着功能增加同步增长
- `docs/` 中的规划与真实目录结构发生偏离时，要及时更新

## 6. 使用建议

开发推进时，可以把这份文档当成“目录落地蓝图”：

1. 先按 `Phase 1` 建最小项目骨架
2. 每完成一个模块，再逐步把目标目录树中的节点落地
3. 若实际实现需要调整结构，应先更新文档再改代码

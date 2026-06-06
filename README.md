# Homemade Tiny OS

`Homemade Tiny OS` 是一个运行在宿主机用户态的 Tiny OS 仿真项目。  
它的目标不是做一个只能截图演示的“假系统”，而是做一个**有真实内部状态、有清晰模块边界、有持久化能力、有测试约束、能持续扩展**的微型操作系统工程。

这个项目不追求裸机启动，也不伪装成真实内核；它更关注以下问题：

- 虚拟磁盘如何初始化、扩容、持久化
- 文件系统如何组织路径、目录项和 inode
- 进程和调度器如何建模
- Shell 如何把用户输入落到内部系统调用接口
- 错误、权限、观测和恢复能力如何逐步建立

## 项目定位

这是一个**教学型 + 工程型**项目。

它既要保留足够强的操作系统学习价值，也要避免掉进“什么都自己造轮子”的陷阱。

因此项目的基本原则是：

- 操作系统核心抽象必须自己实现
- 通用但不构成教学重点的底层能力，可以使用成熟库
- 任何第三方库都不能直接吞掉整个文件系统、调度器或 Shell

例如：

- `B+ Tree` 这类索引结构可以使用成熟库
- 但目录索引接口、VFS、路径解析、块映射和持久化策略必须由项目自己定义和控制

## 当前阶段

当前项目进度：

- `Phase 1`：项目骨架与测试基线，已完成
- `Phase 2`：可扩展虚拟磁盘与块设备，进行中
- `Phase 3` 及以后：见 `docs/`

详细路线请看：

- [总 PRD](docs/tiny-os-prd.md)
- [任务清单](docs/tasks.md)
- [项目目录树](docs/project-tree.md)
- [Git 工作流](docs/git-workflow.md)

## 设计原则

### 1. TDD 优先

项目默认按测试驱动开发推进：

1. 先写测试
2. 再写最小实现
3. 测试转绿后再重构

没有对应测试的功能，不应视为稳定完成。

### 2. 用户态仿真，但内部状态必须真实

Shell 命令不能通过调用宿主机命令伪装成功能。  
例如：

- 不能用 `os.system("ls")` 假装自己实现了 `ls`
- 不能把宿主机文件系统直接当成 Tiny OS 的文件系统

所有用户可见行为都应该落到 Tiny OS 自己的内部对象和 API。

### 3. 小步扩展，避免写爆宿主机磁盘

虚拟磁盘采用：

- 小初始容量
- 固定步长扩容
- 明确硬上限
- 只在需要时扩容

这样既能保留“磁盘会增长”的真实感，也能避免无节制写宿主 SSD。

## 推荐目录结构

当前目标结构请看 [project-tree.md](docs/project-tree.md)。

核心部分大致如下：

```text
Homemade-Tiny-OS/
├── docs/
├── src/
│   └── tinyos/
│       ├── kernel/
│       ├── storage/
│       ├── vfs/
│       ├── memory/
│       ├── shell/
│       └── observability/
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

## 阶段路线

### Phase 1: 项目骨架与测试基线

目标：

- 固定包结构
- 固定配置对象
- 固定统一错误模型
- 建立最小测试基线

### Phase 2: 可扩展虚拟磁盘与块设备

目标：

- 创建磁盘镜像
- 支持重复打开
- 提供固定块读写
- 支持按步长扩容
- 支持硬上限拒绝

### Phase 3: 虚拟文件系统与元数据索引

目标：

- 路径解析
- inode 与目录项
- 文件读写
- 目录索引接入
- 持久化恢复

### Phase 4: 进程调度、Shell 与系统内省

目标：

- 协作式调度器
- Shell REPL
- `ps`、`kill`、`top`、`sysstat`、`dmesg`

### Phase 5: 可靠性、权限与可扩展能力

目标：

- 权限模型
- 空间不足保护
- 一致性与恢复
- 插件式命令扩展

## 开发方式

### 环境要求

- Python `3.13+`

### 本地测试

当前项目默认使用标准库 `unittest` 作为最稳的测试入口：

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py'
```

后续如果需要，也可以补充 `pytest` 作为更丰富的开发体验，但主线测试不应依赖复杂外部环境才能运行。

### Git 提交节奏

建议按以下粒度提交：

- 一个 Phase 完成后提交
- 一组关键测试转绿后提交
- 一个关键接口定型后提交

不要把大量不相关改动混在一个 commit 里。

更详细的规则见 [git-workflow.md](docs/git-workflow.md)。

## 当前已实现内容

截至目前，项目已经完成：

- 基础 `src` 布局
- `TinyOSConfig`
- 统一错误层级
- `ExpandableVirtualDisk` 骨架和 `Phase 2` 开发入口
- `VirtualFileSystem` / `KernelScheduler` / `Shell` / `KernelStats` 骨架
- `Phase 1` 单元测试基线

## 后续重点

接下来最关键的是把 `storage/disk.py` 做成稳定的块设备基础层。  
如果这层不稳，后续 VFS、持久化和恢复都会一起失稳。

## 文档索引

- [Tiny OS PRD](docs/tiny-os-prd.md)
- [项目目录树](docs/project-tree.md)
- [任务清单](docs/tasks.md)
- [Git 工作流](docs/git-workflow.md)
- [Phase 1](docs/phase-1-项目骨架与测试基线.md)
- [Phase 2](docs/phase-2-可扩展虚拟磁盘与块设备.md)
- [Phase 3](docs/phase-3-虚拟文件系统与元数据索引.md)
- [Phase 4](docs/phase-4-进程调度-shell与系统内省.md)
- [Phase 5](docs/phase-5-可靠性权限与可扩展能力.md)

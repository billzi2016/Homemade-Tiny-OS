# QUICKSTART

这份文档只做一件事：让你尽快把当前的 Tiny OS 跑起来，并知道怎么做基础操作、多任务测试、联调测试和实际运行测试。

如果你想看完整背景、架构和阶段规划，请回到 [README.md](README.md) 和 `docs/`。

## 1. 环境要求

- Python `3.13+`
- 当前环境里已经可用的依赖：
  - `sortedcontainers`

## 2. 当前项目的“启动”是什么意思

这个项目目前不是一个裸机镜像，也不是已经做成真正的交互式终端程序。  
现在的“启动 Tiny OS”含义是：

- 创建 `VirtualFileSystem`
- 创建 `KernelScheduler`
- 创建 `Shell`
- 通过 `Shell.execute(...)` 连续执行命令

也就是说，当前最真实的使用方式是：

1. 在 Python 里实例化一个 Shell
2. 让它挂着自己的磁盘、文件系统、调度器
3. 然后像操作系统一样执行命令

## 3. 最快启动方式

在项目根目录执行：

```bash
python3
```

然后输入下面这段：

```python
from tinyos.config import TinyOSConfig
from tinyos.kernel import KernelScheduler
from tinyos.shell import Shell
from tinyos.storage import ExpandableVirtualDisk
from tinyos.vfs import VirtualFileSystem

config = TinyOSConfig()
disk = ExpandableVirtualDisk("tinyos.disk", config=config)
vfs = VirtualFileSystem(config=config, disk=disk)
scheduler = KernelScheduler(config=config)
shell = Shell(config=config, vfs=vfs, scheduler=scheduler, stats=scheduler.stats, uid=0)
```

现在你就有了一个当前可用的 Tiny OS 会话对象：

```python
shell
```

## 4. 基础命令使用

下面这些命令已经可以通过：

```python
shell.execute("...")
```

来运行。

### 4.1 查看当前目录

```python
shell.execute("pwd")
```

### 4.2 创建目录

```python
shell.execute("mkdir /docs")
shell.execute("mkdir /workspace")
```

### 4.3 切换目录

```python
shell.execute("cd /workspace")
shell.execute("pwd")
```

### 4.4 创建文件

```python
shell.execute("touch notes.txt")
```

### 4.5 写文件

```python
shell.execute('echo "hello tiny os" > notes.txt')
```

### 4.6 读文件

```python
shell.execute("cat notes.txt")
```

### 4.7 列目录

```python
shell.execute("ls")
shell.execute("ls /workspace")
```

### 4.8 删除文件

```python
shell.execute("rm notes.txt")
```

## 5. 多任务测试

当前调度器采用协作式生成器任务。  
也就是说，一个任务要通过 `yield` 主动交出控制权。

### 5.1 创建一个最小任务

```python
def worker():
    print("step-1")
    yield
    print("step-2")
    yield
    print("step-3")
    yield
```

### 5.2 注册到调度器

```python
pcb = shell.scheduler.create_process(
    name="worker",
    task=worker(),
    cwd=shell.cwd,
)
```

### 5.3 推进调度

```python
shell.scheduler.schedule_once()
shell.scheduler.schedule_once()
shell.scheduler.schedule_once()
shell.scheduler.schedule_once()
```

运行过程中你可以查看：

```python
shell.execute("ps")
```

如果任务执行完，会进入 `ZOMBIE`。

### 5.4 多任务轮转示例

```python
def task_a():
    print("A-1")
    yield
    print("A-2")
    yield

def task_b():
    print("B-1")
    yield
    print("B-2")
    yield

shell.scheduler.create_process(name="task-a", task=task_a(), cwd=shell.cwd)
shell.scheduler.create_process(name="task-b", task=task_b(), cwd=shell.cwd)

shell.scheduler.schedule_once()
shell.scheduler.schedule_once()
shell.scheduler.schedule_once()
shell.scheduler.schedule_once()
```

你会看到轮转顺序类似：

```text
A-1
B-1
A-2
B-2
```

## 6. 系统观测命令

### 6.1 `ps`

查看当前进程：

```python
shell.execute("ps")
```

### 6.2 `kill`

杀死一个进程：

```python
shell.execute(f"kill {pcb.pid}")
```

### 6.3 `top`

查看当前调度与基础运行状态：

```python
shell.execute("top")
```

输出会包含：

- 总 tick 数
- 调度切换次数
- 当前运行进程
- 就绪队列
- 当前工作目录

### 6.4 `sysstat`

查看磁盘和核心计数器：

```python
shell.execute("sysstat")
```

输出会包含：

- 当前磁盘大小
- 最大磁盘大小
- 当前块数量
- 页错误计数
- 索引/调度相关计数

### 6.5 `dmesg`

查看内核日志缓冲区：

```python
shell.execute("dmesg")
```

这里能看到例如：

- 调度切换
- 文件写入
- 目录创建
- kill 操作

## 7. 权限测试

当前支持最基础的 `uid` 区分。

### 7.1 root 用户

```python
root_shell = Shell(config=config, vfs=vfs, scheduler=scheduler, stats=scheduler.stats, uid=0)
```

### 7.2 普通用户

```python
user_shell = Shell(config=config, vfs=vfs, scheduler=scheduler, stats=scheduler.stats, uid=1000)
```

普通用户尝试直接在根目录写文件时，会得到：

```python
user_shell.execute("touch /blocked.txt")
```

返回：

```text
Permission denied
```

## 8. 自定义命令扩展

当前 Shell 已经支持注册自定义命令。

```python
shell.register_command("hello", lambda args: f"hello {' '.join(args)}".strip())
shell.execute("hello tiny os")
```

## 9. 关闭系统

当你结束当前会话时，建议显式关闭：

```python
shell.close()
```

这样会把底层 VFS 和磁盘句柄正确关掉。

## 10. 跑测试

### 10.1 全量测试

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py'
```

### 10.2 只跑联调测试

```bash
python3 -B -m unittest tests.integration.test_runtime_integration -v
```

### 10.3 只跑实际运行测试

```bash
python3 -B -m unittest tests.e2e.test_actual_run_flow -v
```

### 10.4 只跑 Shell 联动测试

```bash
python3 -B -m unittest tests.integration.test_shell_commands -v
```

## 11. 推荐演示顺序

如果你要向别人演示当前 Tiny OS，建议按这个顺序：

1. 启动 `Shell`
2. `mkdir /workspace`
3. `cd /workspace`
4. `touch notes.txt`
5. `echo "hello tiny os" > notes.txt`
6. `cat notes.txt`
7. 创建两个生成器任务并调度几次
8. `ps`
9. `top`
10. `sysstat`
11. `dmesg`
12. `shell.close()`
13. 重新创建一个 `Shell`
14. 再次 `cat /workspace/notes.txt`，证明状态恢复

## 12. 当前限制

当前 QUICKSTART 所描述的是**当前仓库已实现的真实能力**，不是未来规划。

因此你需要知道这些限制：

- 目前还没有真正的交互式命令循环入口脚本
- 当前“启动 OS”主要通过 Python 对象实例化实现
- 多任务是协作式生成器，不是抢占式
- 内存管理层还没有作为独立可操作模块暴露

但对于当前版本来说，这已经足够支撑：

- 文件系统演示
- 多任务调度演示
- 观测命令演示
- 权限/恢复/错误路径演示

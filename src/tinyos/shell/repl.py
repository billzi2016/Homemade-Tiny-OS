"""Phase 4 的 Shell 实现。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from tinyos.config import TinyOSConfig
from tinyos.errors import DiskFullError, InvalidCommandError, PermissionDeniedError
from tinyos.kernel import KernelScheduler
from tinyos.observability.stats import KernelStats
from tinyos.shell.parser import parse_command
from tinyos.vfs import VirtualFileSystem


@dataclass(slots=True)
class Shell:
    """Shell 对象。

    这里先提供“执行单条命令”的核心能力，
    真实 REPL 循环后续如果需要可以再套一层。
    """

    config: TinyOSConfig = field(default_factory=TinyOSConfig)
    vfs: VirtualFileSystem | None = None
    scheduler: KernelScheduler | None = None
    stats: KernelStats | None = None
    prompt: str = "tinyos$ "
    cwd: str = "/"
    uid: int = 0
    command_registry: dict[str, Callable[[list[str]], str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """补齐默认依赖对象。"""

        if self.vfs is None:
            self.vfs = VirtualFileSystem(config=self.config)
        if self.scheduler is None:
            self.scheduler = KernelScheduler(config=self.config)
        if self.stats is None:
            self.stats = self.scheduler.stats

    def execute(self, command_line: str) -> str:
        """执行一条命令并返回输出文本。"""
        try:
            parsed = parse_command(command_line)
            command_name = parsed.name
            args = parsed.args

            if command_name in self.command_registry:
                return self.command_registry[command_name](args)

            if command_name == "ls":
                path = args[0] if args else self.cwd
                entries = self.vfs.list_dir(path, cwd=self.cwd, acting_uid=self.uid)
                return "\n".join(entry.name for entry in entries)

            if command_name == "cd":
                path = args[0] if args else "/"
                self.vfs.stat(path, cwd=self.cwd, acting_uid=self.uid)
                self.cwd = self.vfs._normalize(path, self.cwd)
                current_process = self.scheduler.get_current_process()
                if current_process is not None:
                    current_process.cwd = self.cwd
                return self.cwd

            if command_name == "pwd":
                return self.cwd

            if command_name == "mkdir":
                if not args:
                    raise InvalidCommandError("mkdir requires a path")
                self.vfs.mkdir(args[0], cwd=self.cwd, acting_uid=self.uid)
                self.stats.log(f"[SHELL] mkdir {args[0]}")
                return ""

            if command_name == "touch":
                if not args:
                    raise InvalidCommandError("touch requires a path")
                self.vfs.create_file(args[0], cwd=self.cwd, acting_uid=self.uid)
                self.stats.log(f"[SHELL] touch {args[0]}")
                return ""

            if command_name == "cat":
                if not args:
                    raise InvalidCommandError("cat requires a path")
                return self.vfs.read_file(args[0], cwd=self.cwd, acting_uid=self.uid).decode("utf-8")

            if command_name == "echo":
                if parsed.output_redirect is None:
                    return " ".join(args)
                content = " ".join(args).encode("utf-8")
                target = parsed.output_redirect
                try:
                    self.vfs.stat(target, cwd=self.cwd, acting_uid=self.uid)
                except Exception:
                    self.vfs.create_file(target, cwd=self.cwd, acting_uid=self.uid)
                self.vfs.write_file(target, content, cwd=self.cwd, acting_uid=self.uid)
                self.stats.log(f"[SHELL] echo > {target}")
                return ""

            if command_name == "rm":
                if not args:
                    raise InvalidCommandError("rm requires a path")
                self.vfs.delete_file(args[0], cwd=self.cwd, acting_uid=self.uid)
                self.stats.log(f"[SHELL] rm {args[0]}")
                return ""

            if command_name == "ps":
                return "\n".join(
                    f"{pcb.pid} {pcb.name} {pcb.status} {pcb.cwd}"
                    for pcb in self.scheduler.list_processes()
                )

            if command_name == "kill":
                if not args:
                    raise InvalidCommandError("kill requires a pid")
                self.scheduler.kill_process(int(args[0]))
                return ""

            if command_name in {"top", "mon"}:
                current = self.scheduler.get_current_process()
                current_text = "none" if current is None else f"{current.pid}:{current.name}:{current.status}"
                queue_text = " ".join(str(pid) for pid in self.scheduler.queue_snapshot()) or "empty"
                return "\n".join(
                    [
                        f"ticks={self.stats.total_ticks}",
                        f"switches={self.stats.scheduler_switches}",
                        f"current={current_text}",
                        f"queue={queue_text}",
                        f"cwd={self.cwd}",
                    ]
                )

            if command_name == "sysstat":
                disk = self.vfs.disk
                assert disk is not None
                return "\n".join(
                    [
                        f"disk_current={disk.current_size_bytes}",
                        f"disk_max={disk.config.disk_max_size_bytes}",
                        f"blocks={disk.current_block_count}",
                        f"page_faults={self.stats.page_faults}",
                        f"tree_splits={self.stats.tree_splits}",
                        f"scheduler_switches={self.stats.scheduler_switches}",
                    ]
                )

            if command_name == "dmesg":
                return "\n".join(self.stats.dmesg_lines())

            raise InvalidCommandError(f"unknown command: {command_name}")
        except DiskFullError:
            return "No space left on device"
        except PermissionDeniedError:
            return "Permission denied"

    def close(self) -> None:
        """关闭 Shell 依赖的底层资源。

        当前最重要的是把 VFS 和底层磁盘关闭，
        避免测试或后续真实运行时残留文件句柄。
        """

        if self.vfs is not None:
            self.vfs.close()

    def register_command(self, name: str, handler: Callable[[list[str]], str]) -> None:
        """注册一个自定义命令。

        这为后续插件式命令扩展提供最小稳定入口。
        """

        self.command_registry[name] = handler

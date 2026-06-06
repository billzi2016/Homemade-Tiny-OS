"""Phase 4 Shell 集成测试。"""

from __future__ import annotations

import shutil
import unittest
from pathlib import Path

from tinyos.config import TinyOSConfig
from tinyos.kernel import KernelScheduler
from tinyos.shell import Shell
from tinyos.vfs import VirtualFileSystem
from tinyos.storage import ExpandableVirtualDisk


def _simple_task():
    """最小可调度任务。"""

    yield "step-1"
    yield "step-2"


class ShellIntegrationTests(unittest.TestCase):
    """验证 Shell 与 VFS / scheduler 的联动。"""

    def setUp(self) -> None:
        """准备独立测试目录。"""

        self.artifacts_root = Path("tests/.artifacts")
        self.artifacts_root.mkdir(parents=True, exist_ok=True)
        self.test_dir = self.artifacts_root / self.id().replace(".", "_")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        """清理测试目录。"""

        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_shell_supports_basic_filesystem_commands(self) -> None:
        """应能通过 Shell 操作目录与文件。"""

        shell = self._create_shell("fs.disk")
        shell.execute("mkdir /docs")
        shell.execute("touch /docs/readme.txt")
        shell.execute('echo "hello os" > /docs/readme.txt')

        self.assertEqual(shell.execute("cat /docs/readme.txt"), "hello os")
        self.assertEqual(shell.execute("ls /docs"), "readme.txt")

    def test_shell_supports_cd_and_pwd(self) -> None:
        """cd 后 pwd 应反映当前目录。"""

        shell = self._create_shell("cwd.disk")
        shell.execute("mkdir /work")
        shell.execute("cd /work")

        self.assertEqual(shell.execute("pwd"), "/work")

    def test_shell_supports_ps_and_kill(self) -> None:
        """应能查看并杀死进程。"""

        shell = self._create_shell("proc.disk")
        pcb = shell.scheduler.create_process(name="worker", task=_simple_task())
        process_view = shell.execute("ps")
        self.assertIn(str(pcb.pid), process_view)

        shell.execute(f"kill {pcb.pid}")
        self.assertEqual(shell.scheduler.processes[pcb.pid].status, "ZOMBIE")

    def test_shell_supports_top_sysstat_and_dmesg(self) -> None:
        """系统内省命令应返回稳定文本快照。"""

        shell = self._create_shell("obs.disk")
        shell.scheduler.create_process(name="worker", task=_simple_task())
        shell.scheduler.schedule_once()

        top_output = shell.execute("top")
        sysstat_output = shell.execute("sysstat")
        dmesg_output = shell.execute("dmesg")

        self.assertIn("ticks=", top_output)
        self.assertIn("disk_current=", sysstat_output)
        self.assertIn("[SCHED] switch", dmesg_output)

    def _create_shell(self, file_name: str) -> Shell:
        """创建测试用 Shell。"""

        config = TinyOSConfig(
            disk_initial_size_bytes=8 * 4096,
            disk_growth_step_bytes=4 * 4096,
            disk_max_size_bytes=32 * 4096,
            block_size_bytes=4096,
            page_size_bytes=4096,
        )
        disk = ExpandableVirtualDisk(self.test_dir / file_name, config=config)
        vfs = VirtualFileSystem(config=config, disk=disk)
        scheduler = KernelScheduler(config=config)
        shell = Shell(config=config, vfs=vfs, scheduler=scheduler, stats=scheduler.stats)
        self.addCleanup(shell.close)
        return shell

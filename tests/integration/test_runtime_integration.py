"""补充联调测试。

这组测试不再只验证单个命令或单个模块，而是覆盖：
- Shell + VFS + Disk 的连续命令流
- Scheduler + Shell 的交互
- 关闭后重开系统的恢复路径
"""

from __future__ import annotations

import shutil
import unittest
from pathlib import Path

from tinyos.config import TinyOSConfig
from tinyos.kernel import KernelScheduler
from tinyos.shell import Shell
from tinyos.storage import ExpandableVirtualDisk
from tinyos.vfs import VirtualFileSystem


def _counting_task():
    """测试用协作任务。"""

    yield "tick-1"
    yield "tick-2"
    yield "tick-3"


class RuntimeIntegrationTests(unittest.TestCase):
    """覆盖跨模块联调场景。"""

    def setUp(self) -> None:
        self.artifacts_root = Path("tests/.artifacts")
        self.artifacts_root.mkdir(parents=True, exist_ok=True)
        self.test_dir = self.artifacts_root / self.id().replace(".", "_")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_shell_scheduler_and_restart_work_together(self) -> None:
        """联调验证：命令流、调度、重启恢复应串得起来。"""

        shell = self._create_shell("integration.disk")
        self.addCleanup(shell.close)

        shell.execute("mkdir /workspace")
        shell.execute("cd /workspace")
        shell.execute("touch notes.txt")
        shell.execute('echo "alpha" > notes.txt')
        shell.execute('echo "beta" > journal.txt')

        worker = shell.scheduler.create_process(name="worker", task=_counting_task(), cwd=shell.cwd)
        shell.scheduler.schedule_once()
        shell.scheduler.schedule_once()

        self.assertIn("notes.txt", shell.execute("ls"))
        self.assertEqual(shell.execute("cat notes.txt"), "alpha")
        self.assertIn(str(worker.pid), shell.execute("ps"))
        self.assertIn("ticks=", shell.execute("top"))
        self.assertIn("disk_current=", shell.execute("sysstat"))

        shell.close()

        reopened = self._create_shell("integration.disk")
        self.addCleanup(reopened.close)
        reopened.execute("cd /workspace")

        self.assertEqual(reopened.execute("cat notes.txt"), "alpha")
        self.assertEqual(reopened.execute("cat journal.txt"), "beta")

    def _create_shell(self, file_name: str) -> Shell:
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
        return Shell(config=config, vfs=vfs, scheduler=scheduler, stats=scheduler.stats, uid=0)

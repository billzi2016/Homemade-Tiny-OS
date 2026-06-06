"""实际运行测试。

这里的目标不是做 UI 自动化，而是尽量用接近真实使用的方式，
跑通一个 Tiny OS 会话：
- 启动
- 执行连续命令
- 调度进程
- 查看监控信息
- 关闭
- 重启后验证状态仍在
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


def _writer_task(shell: Shell):
    """模拟一个会交出控制权的用户任务。"""

    shell.execute("cd /app")
    shell.execute('echo "task-step-1" > task.log')
    yield "step-1"
    shell.execute('echo "task-step-1task-step-2" > task.log')
    yield "step-2"


class ActualRunFlowTests(unittest.TestCase):
    """验证接近真实运行路径的端到端行为。"""

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

    def test_actual_run_flow_survives_restart(self) -> None:
        """应能从启动一路跑到关闭重开，并保留核心状态。"""

        shell = self._create_shell("actual.disk")
        self.addCleanup(shell.close)

        shell.execute("mkdir /app")
        shell.execute("cd /app")
        shell.execute("touch readme.txt")
        shell.execute('echo "tiny os runtime" > readme.txt')

        worker = shell.scheduler.create_process(
            name="writer",
            task=_writer_task(shell),
            cwd=shell.cwd,
        )
        shell.scheduler.schedule_once()
        shell.scheduler.schedule_once()
        shell.scheduler.schedule_once()

        self.assertIn("readme.txt", shell.execute("ls"))
        self.assertEqual(shell.execute("cat readme.txt"), "tiny os runtime")
        self.assertEqual(shell.execute("cat task.log"), "task-step-1task-step-2")
        self.assertIn(str(worker.pid), shell.execute("dmesg"))

        shell.close()

        reopened = self._create_shell("actual.disk")
        self.addCleanup(reopened.close)
        reopened.execute("cd /app")

        self.assertEqual(reopened.execute("cat readme.txt"), "tiny os runtime")
        self.assertEqual(reopened.execute("cat task.log"), "task-step-1task-step-2")
        self.assertIn("disk_current=", reopened.execute("sysstat"))

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

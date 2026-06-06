"""Phase 5 Shell 行为测试。"""

from __future__ import annotations

import shutil
import unittest
from pathlib import Path

from tinyos.config import TinyOSConfig
from tinyos.kernel import KernelScheduler
from tinyos.shell import Shell
from tinyos.storage import ExpandableVirtualDisk
from tinyos.vfs import VirtualFileSystem


class PhaseFiveShellTests(unittest.TestCase):
    """验证 Shell 层的权限、空间不足和命令扩展行为。"""

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

    def test_non_root_user_gets_permission_denied_in_root_directory(self) -> None:
        """普通用户不应能直接在根目录下创建文件。"""

        shell = self._create_shell("perm.disk", uid=1000)
        self.addCleanup(shell.close)
        self.assertEqual(shell.execute("touch /user.txt"), "Permission denied")

    def test_root_user_can_bypass_basic_write_restrictions(self) -> None:
        """root 用户应能在根目录写文件。"""

        shell = self._create_shell("root.disk", uid=0)
        self.addCleanup(shell.close)
        self.assertEqual(shell.execute("touch /root.txt"), "")
        self.assertEqual(shell.execute('echo "ok" > /root.txt'), "")
        self.assertEqual(shell.execute("cat /root.txt"), "ok")

    def test_shell_returns_no_space_left_on_device_when_disk_is_full(self) -> None:
        """写满磁盘时，Shell 应返回稳定错误文本。"""

        shell = self._create_shell(
            "full.disk",
            uid=0,
            initial_size_bytes=4 * 4096,
            growth_step_bytes=4096,
            max_size_bytes=4 * 4096,
        )
        self.addCleanup(shell.close)
        shell.execute("touch /big.bin")
        result = shell.execute(f'echo "{"A" * 9000}" > /big.bin')
        self.assertEqual(result, "No space left on device")

    def test_shell_supports_registering_custom_commands_without_breaking_builtins(self) -> None:
        """注册自定义命令后，内建命令仍应正常工作。"""

        shell = self._create_shell("registry.disk", uid=0)
        self.addCleanup(shell.close)
        shell.register_command("hello", lambda args: f"hello {' '.join(args)}".strip())

        self.assertEqual(shell.execute("hello tiny os"), "hello tiny os")
        self.assertEqual(shell.execute("pwd"), "/")

    def _create_shell(
        self,
        file_name: str,
        *,
        uid: int,
        initial_size_bytes: int = 8 * 4096,
        growth_step_bytes: int = 4 * 4096,
        max_size_bytes: int = 32 * 4096,
    ) -> Shell:
        config = TinyOSConfig(
            disk_initial_size_bytes=initial_size_bytes,
            disk_growth_step_bytes=growth_step_bytes,
            disk_max_size_bytes=max_size_bytes,
            block_size_bytes=4096,
            page_size_bytes=4096,
        )
        disk = ExpandableVirtualDisk(self.test_dir / file_name, config=config)
        vfs = VirtualFileSystem(config=config, disk=disk)
        scheduler = KernelScheduler(config=config)
        return Shell(config=config, vfs=vfs, scheduler=scheduler, stats=scheduler.stats, uid=uid)

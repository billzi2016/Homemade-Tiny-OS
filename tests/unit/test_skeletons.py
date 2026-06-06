"""Phase 1 骨架对象测试。"""

import unittest

from tinyos import TinyOSConfig
from tinyos.kernel import KernelScheduler
from tinyos.observability import KernelStats
from tinyos.shell import Shell
from tinyos.storage import ExpandableVirtualDisk
from tinyos.vfs import VirtualFileSystem


class PhaseOneSkeletonTests(unittest.TestCase):
    """验证核心骨架对象已经具备最小可构造状态。"""

    def test_core_objects_can_be_constructed(self) -> None:
        """Phase 1 至少要保证后续核心对象都能实例化。"""
        config = TinyOSConfig()

        disk = ExpandableVirtualDisk(config=config)
        vfs = VirtualFileSystem(config=config)
        scheduler = KernelScheduler(config=config)
        shell = Shell(config=config)
        stats = KernelStats()

        self.assertEqual(disk.current_size_bytes, config.disk_initial_size_bytes)
        self.assertEqual(vfs.root_path, "/")
        self.assertEqual(scheduler.ready_queue, [])
        self.assertEqual(shell.prompt, "tinyos$ ")
        self.assertEqual(stats.total_ticks, 0)

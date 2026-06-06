"""Phase 1 导入契约测试。"""

import unittest


class ImportContractTests(unittest.TestCase):
    """验证顶层和分层导入入口已经稳定存在。"""

    def test_phase_one_modules_are_importable(self) -> None:
        """后续模块应能通过固定导入路径访问基础对象。"""
        from tinyos import TinyOSConfig, TinyOSError
        from tinyos.kernel import KernelScheduler
        from tinyos.observability import KernelStats
        from tinyos.shell import Shell
        from tinyos.storage import ExpandableVirtualDisk
        from tinyos.vfs import VirtualFileSystem

        self.assertIsNotNone(TinyOSConfig)
        self.assertIsNotNone(TinyOSError)
        self.assertIsNotNone(ExpandableVirtualDisk)
        self.assertIsNotNone(VirtualFileSystem)
        self.assertIsNotNone(KernelScheduler)
        self.assertIsNotNone(Shell)
        self.assertIsNotNone(KernelStats)

"""Phase 3 虚拟文件系统测试。"""

from __future__ import annotations

import shutil
import unittest
from pathlib import Path

from tinyos.config import TinyOSConfig
from tinyos.errors import AlreadyExistsError, PathNotFoundError
from tinyos.storage import ExpandableVirtualDisk
from tinyos.vfs import VirtualFileSystem


class VirtualFileSystemTests(unittest.TestCase):
    """验证 VFS 的目录、文件、持久化和块回收行为。"""

    def setUp(self) -> None:
        """为每个测试准备独立磁盘镜像目录。"""

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

    def test_root_directory_is_initialized(self) -> None:
        """首次启动时应自动建立根目录。"""

        vfs = self._create_vfs("root.disk")
        root_entries = vfs.list_dir("/")
        root_inode = vfs.stat("/")

        self.assertEqual(root_entries, [])
        self.assertEqual(root_inode.kind, "directory")

    def test_mkdir_supports_nested_paths(self) -> None:
        """应支持多级目录创建。"""

        vfs = self._create_vfs("mkdir.disk")
        vfs.mkdir("/home")
        vfs.mkdir("/home/user")

        names = [entry.name for entry in vfs.list_dir("/home")]
        self.assertEqual(names, ["user"])

    def test_create_and_read_file(self) -> None:
        """应能创建空文件并读取内容。"""

        vfs = self._create_vfs("read.disk")
        vfs.mkdir("/docs")
        vfs.create_file("/docs/readme.txt")
        vfs.write_file("/docs/readme.txt", b"hello tiny os")

        self.assertEqual(vfs.read_file("/docs/readme.txt"), b"hello tiny os")

    def test_write_file_supports_overwrite_and_append(self) -> None:
        """覆盖写与追加写都应可用。"""

        vfs = self._create_vfs("append.disk")
        vfs.create_file("/log.txt")
        vfs.write_file("/log.txt", b"abc")
        vfs.write_file("/log.txt", b"XYZ")
        self.assertEqual(vfs.read_file("/log.txt"), b"XYZ")

        vfs.write_file("/log.txt", b"123", append=True)
        self.assertEqual(vfs.read_file("/log.txt"), b"XYZ123")

    def test_large_file_spans_multiple_blocks(self) -> None:
        """大文件应能跨多个块保存并读回。"""

        vfs = self._create_vfs("large.disk", max_size_bytes=64 * 4096)
        vfs.create_file("/big.bin")
        payload = b"A" * 9000
        vfs.write_file("/big.bin", payload)

        inode = vfs.stat("/big.bin")
        self.assertGreaterEqual(len(inode.data_blocks), 3)
        self.assertEqual(vfs.read_file("/big.bin"), payload)

    def test_delete_file_reclaims_blocks(self) -> None:
        """删除文件后，其数据块应可被后续文件复用。"""

        vfs = self._create_vfs("delete.disk")
        vfs.create_file("/a.bin")
        vfs.write_file("/a.bin", b"A" * 5000)
        old_blocks = list(vfs.stat("/a.bin").data_blocks)

        vfs.delete_file("/a.bin")
        vfs.create_file("/b.bin")
        vfs.write_file("/b.bin", b"B" * 5000)
        new_blocks = list(vfs.stat("/b.bin").data_blocks)

        self.assertEqual(new_blocks, old_blocks)

    def test_reopen_restores_directories_and_files(self) -> None:
        """重启后应恢复目录结构和文件内容。"""

        vfs = self._create_vfs("reopen.disk")
        vfs.mkdir("/etc")
        vfs.create_file("/etc/hosts")
        vfs.write_file("/etc/hosts", b"127.0.0.1 localhost")
        vfs.close()

        reopened = self._create_vfs("reopen.disk")
        self.assertEqual(reopened.read_file("/etc/hosts"), b"127.0.0.1 localhost")
        self.assertEqual([entry.name for entry in reopened.list_dir("/etc")], ["hosts"])

    def test_invalid_paths_and_name_conflicts_are_rejected(self) -> None:
        """非法路径和重名冲突必须报错。"""

        vfs = self._create_vfs("errors.disk")
        with self.assertRaises(PathNotFoundError):
            vfs.create_file("/missing/path.txt")

        vfs.mkdir("/data")
        with self.assertRaises(AlreadyExistsError):
            vfs.mkdir("/data")

    def test_directory_pressure_keeps_listing_order_stable(self) -> None:
        """较多目录项时，列出顺序仍应稳定。"""

        vfs = self._create_vfs("pressure.disk", max_size_bytes=64 * 4096)
        vfs.mkdir("/dir")
        for index in range(50):
            vfs.create_file(f"/dir/file-{49 - index:02d}.txt")

        names = [entry.name for entry in vfs.list_dir("/dir")]
        self.assertEqual(names, sorted(names))

    def _create_vfs(
        self,
        file_name: str,
        *,
        initial_size_bytes: int = 8 * 4096,
        growth_step_bytes: int = 4 * 4096,
        max_size_bytes: int = 32 * 4096,
    ) -> VirtualFileSystem:
        """创建测试用 VFS。"""

        config = TinyOSConfig(
            disk_initial_size_bytes=initial_size_bytes,
            disk_growth_step_bytes=growth_step_bytes,
            disk_max_size_bytes=max_size_bytes,
            block_size_bytes=4096,
            page_size_bytes=4096,
        )
        disk = ExpandableVirtualDisk(self.test_dir / file_name, config=config)
        self.addCleanup(disk.close)
        vfs = VirtualFileSystem(config=config, disk=disk)
        self.addCleanup(vfs.close)
        return vfs

"""Phase 5 可靠性与扩展性测试。"""

from __future__ import annotations

import shutil
import unittest
from pathlib import Path

from tinyos.config import TinyOSConfig
from tinyos.storage import ExpandableVirtualDisk
from tinyos.vfs import VirtualFileSystem
from tinyos.vfs.directory_entry import DirectoryEntry
from tinyos.vfs.index.interface import DirectoryIndex


class AlternateDirectoryIndex(DirectoryIndex):
    """测试用目录索引实现。

    这个实现不依赖项目默认的 `MemoryDirectoryIndex`，用来验证
    VFS 的目录索引后端确实可替换。
    """

    def __init__(self) -> None:
        self._mapping: dict[str, int] = {}

    def get(self, name: str) -> int:
        return self._mapping[name]

    def set(self, name: str, inode_id: int) -> None:
        self._mapping[name] = inode_id

    def delete(self, name: str) -> None:
        del self._mapping[name]

    def contains(self, name: str) -> bool:
        return name in self._mapping

    def list_entries(self) -> list[DirectoryEntry]:
        return [DirectoryEntry(name=name, inode_id=self._mapping[name]) for name in sorted(self._mapping)]

    def to_mapping(self) -> dict[str, int]:
        return dict(self._mapping)


class PhaseFiveReliabilityTests(unittest.TestCase):
    """验证恢复能力与索引替换能力。"""

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

    def test_corrupted_primary_superblock_recovers_from_backup_copy(self) -> None:
        """主超级块损坏时，应能从备份副本恢复。"""

        config = self._config()
        disk_path = self.test_dir / "recover.disk"
        vfs = VirtualFileSystem(config=config, disk=ExpandableVirtualDisk(disk_path, config=config))
        self.addCleanup(vfs.close)
        vfs.create_file("/note.txt")
        vfs.write_file("/note.txt", b"recover me")
        vfs.close()

        disk = ExpandableVirtualDisk(disk_path, config=config)
        self.addCleanup(disk.close)
        disk.open()
        disk.write_block(0, b"X" * config.block_size_bytes)
        disk.close()

        reopened = VirtualFileSystem(config=config, disk=ExpandableVirtualDisk(disk_path, config=config))
        self.addCleanup(reopened.close)
        self.assertEqual(reopened.read_file("/note.txt"), b"recover me")

    def test_corrupted_both_superblocks_raise_error(self) -> None:
        """主备超级块都损坏时，应显式报错。"""

        config = self._config()
        disk_path = self.test_dir / "corrupt.disk"
        vfs = VirtualFileSystem(config=config, disk=ExpandableVirtualDisk(disk_path, config=config))
        self.addCleanup(vfs.close)
        vfs.create_file("/note.txt")
        vfs.close()

        disk = ExpandableVirtualDisk(disk_path, config=config)
        self.addCleanup(disk.close)
        disk.open()
        garbage = b"X" * config.block_size_bytes
        disk.write_block(0, garbage)
        disk.write_block(1, garbage)
        disk.close()

        reopened = VirtualFileSystem(config=config, disk=ExpandableVirtualDisk(disk_path, config=config))
        self.addCleanup(reopened.close)
        with self.assertRaises(ValueError):
            reopened.list_dir("/")

    def test_vfs_supports_replacing_directory_index_backend(self) -> None:
        """目录索引后端应可替换而不影响基本文件系统行为。"""

        config = self._config()
        disk_path = self.test_dir / "index.disk"
        vfs = VirtualFileSystem(
            config=config,
            disk=ExpandableVirtualDisk(disk_path, config=config),
            index_factory=AlternateDirectoryIndex,
        )
        self.addCleanup(vfs.close)

        vfs.mkdir("/docs")
        vfs.create_file("/docs/a.txt")
        names = [entry.name for entry in vfs.list_dir("/docs")]
        self.assertEqual(names, ["a.txt"])

    def _config(self) -> TinyOSConfig:
        return TinyOSConfig(
            disk_initial_size_bytes=8 * 4096,
            disk_growth_step_bytes=4 * 4096,
            disk_max_size_bytes=32 * 4096,
            block_size_bytes=4096,
            page_size_bytes=4096,
        )

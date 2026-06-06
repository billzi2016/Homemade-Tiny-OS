"""Phase 2 虚拟磁盘测试。

这些测试覆盖：
- 首次创建磁盘镜像
- 重启后重新打开镜像
- 固定大小块读写
- 按需扩容
- 超上限拒绝
- 块回收与复用
"""

from __future__ import annotations

import shutil
import unittest
from pathlib import Path

from tinyos.config import TinyOSConfig
from tinyos.errors import DiskFullError
from tinyos.storage import ExpandableVirtualDisk


class ExpandableVirtualDiskTests(unittest.TestCase):
    """验证 Phase 2 虚拟磁盘的核心行为。"""

    def setUp(self) -> None:
        """为每个测试准备独立的磁盘镜像目录。

        这里不使用系统临时目录，而是把测试产物放在仓库内的
        `tests/.artifacts` 下，避免依赖宿主机的 `/tmp`。
        """

        self.artifacts_root = Path("tests/.artifacts")
        self.artifacts_root.mkdir(parents=True, exist_ok=True)
        test_dir_name = self.id().replace(".", "_")
        self.test_dir = self.artifacts_root / test_dir_name
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        """清理当前测试产生的镜像文件和目录。"""

        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_open_creates_new_disk_image_with_expected_capacity(self) -> None:
        """首次打开时应创建新镜像并写入初始容量。"""

        disk = self._create_disk("create.disk")
        disk.open()

        self.assertTrue(disk.image_path.exists())
        self.assertEqual(disk.current_size_bytes, 2 * 4096)
        self.assertEqual(disk.current_block_count, 2)
        self.assertFalse(disk.is_open is False)

    def test_existing_disk_reopens_and_restores_written_data(self) -> None:
        """重新打开已有镜像时，应恢复容量与块内容。"""

        disk = self._create_disk("reopen.disk")
        disk.open()
        payload = b"A" * disk.config.block_size_bytes
        disk.write_block(1, payload)
        disk.flush()
        disk.close()

        reopened_disk = self._create_disk("reopen.disk")
        reopened_disk.open()

        self.assertEqual(reopened_disk.current_size_bytes, disk.current_size_bytes)
        self.assertEqual(reopened_disk.read_block(1), payload)

    def test_block_read_write_round_trip(self) -> None:
        """写入一个块后，应能完整读回相同内容。"""

        disk = self._create_disk("roundtrip.disk")
        disk.open()

        payload = bytes([7]) * disk.config.block_size_bytes
        disk.write_block(0, payload)

        self.assertEqual(disk.read_block(0), payload)

    def test_allocate_blocks_can_trigger_single_growth_step(self) -> None:
        """分配数量超过当前容量时，应按步长扩容一次。"""

        disk = self._create_disk(
            "single-growth.disk",
            initial_size_bytes=4096,
            growth_step_bytes=4096,
            max_size_bytes=3 * 4096,
        )
        disk.open()

        allocated = disk.allocate_blocks(2)

        self.assertEqual(allocated, [0, 1])
        self.assertEqual(disk.current_size_bytes, 2 * 4096)
        self.assertEqual(disk.current_block_count, 2)

    def test_allocate_blocks_can_trigger_multiple_growth_steps(self) -> None:
        """需要更多容量时，应重复扩容直到满足需求。"""

        disk = self._create_disk(
            "multi-growth.disk",
            initial_size_bytes=4096,
            growth_step_bytes=4096,
            max_size_bytes=4 * 4096,
        )
        disk.open()

        allocated = disk.allocate_blocks(4)

        self.assertEqual(allocated, [0, 1, 2, 3])
        self.assertEqual(disk.current_size_bytes, 4 * 4096)
        self.assertEqual(disk.current_block_count, 4)

    def test_allocate_blocks_rejects_requests_beyond_maximum_size(self) -> None:
        """当扩容会超过硬上限时，必须拒绝请求。"""

        disk = self._create_disk(
            "full.disk",
            initial_size_bytes=4096,
            growth_step_bytes=4096,
            max_size_bytes=2 * 4096,
        )
        disk.open()

        with self.assertRaises(DiskFullError):
            disk.allocate_blocks(3)

    def test_free_blocks_can_be_reused(self) -> None:
        """释放后的块应能再次被分配。"""

        disk = self._create_disk("reuse.disk")
        disk.open()

        allocated = disk.allocate_blocks(2)
        disk.free_blocks([allocated[0]])
        reused = disk.allocate_blocks(1)

        self.assertEqual(reused, [allocated[0]])

    def test_invalid_block_ids_are_rejected(self) -> None:
        """非法块号不能被读取或写入。"""

        disk = self._create_disk("invalid-block.disk")
        disk.open()

        with self.assertRaises(ValueError):
            disk.read_block(-1)

        with self.assertRaises(ValueError):
            disk.read_block(disk.current_block_count)

    def _create_disk(
        self,
        file_name: str,
        initial_size_bytes: int = 2 * 4096,
        growth_step_bytes: int = 4096,
        max_size_bytes: int = 4 * 4096,
    ) -> ExpandableVirtualDisk:
        """创建测试用磁盘对象。

        这里统一使用较小容量配置，保证测试快速，同时仍然遵守
        “按块对齐”的真实约束。
        """

        config = TinyOSConfig(
            disk_initial_size_bytes=initial_size_bytes,
            disk_growth_step_bytes=growth_step_bytes,
            disk_max_size_bytes=max_size_bytes,
            block_size_bytes=4096,
            page_size_bytes=4096,
        )
        disk = ExpandableVirtualDisk(
            image_path=self.test_dir / file_name,
            config=config,
        )
        # 测试结束时无论是否显式调用过 `close()`，都统一尝试关闭，
        # 避免镜像文件句柄遗留到解释器回收阶段。
        self.addCleanup(disk.close)
        return disk

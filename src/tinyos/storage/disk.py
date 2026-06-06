"""Phase 2 的虚拟磁盘实现。

本模块实现一个最小但完整的块设备闭环：
- 使用单个镜像文件保存状态
- 第一个块保存元数据
- 后续块保存真实数据
- 支持首次创建、重复打开、块读写、按需扩容、块分配和释放

当前实现的设计重点不是“模拟真实磁盘的所有复杂性”，而是先把
Phase 2 必需的持久化边界、容量约束和块接口稳定下来。
"""

from __future__ import annotations

import math
import os
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO

from tinyos.config import TinyOSConfig
from tinyos.errors import DiskFullError

# 8 字节魔数，用于识别 Tiny OS 自己创建的磁盘镜像。
_MAGIC = b"TNYOSD01"
# 元数据版本号。后续如果磁盘格式升级，可以据此做兼容分支。
_VERSION = 1
# 头部保存固定长度元信息，位图数据紧随其后。
_HEADER_STRUCT = struct.Struct(">8sIIIIII")


@dataclass(slots=True)
class ExpandableVirtualDisk:
    """可扩展虚拟磁盘对象。

    对外职责：
    - 管理镜像文件的生命周期
    - 对外提供固定块大小的读写接口
    - 维护当前容量与最大容量边界
    - 维护块分配位图

    当前阶段不负责文件系统语义，只负责“可靠块设备”这一层。
    """

    image_path: Path | str = Path("tinyos.disk")
    config: TinyOSConfig = field(default_factory=TinyOSConfig)
    current_size_bytes: int = field(init=False)
    is_open: bool = field(init=False, default=False)
    _allocated_bitmap: bytearray = field(init=False, repr=False)
    _file_handle: BinaryIO | None = field(init=False, default=None, repr=False)

    def __post_init__(self) -> None:
        """初始化内存态的默认状态，但不立即触碰磁盘文件。

        这样做的意图是：
        - 保持构造函数轻量
        - 让 Phase 1 的“对象可构造”测试继续成立
        - 把所有真实 I/O 行为收敛到 `open()` 里
        """

        self.image_path = Path(self.image_path)
        self.current_size_bytes = self.config.disk_initial_size_bytes
        self._allocated_bitmap = bytearray(self._bitmap_size_bytes)
        self._validate_metadata_capacity()

    @property
    def current_block_count(self) -> int:
        """返回当前容量下可用的数据块总数。"""

        return self.current_size_bytes // self.config.block_size_bytes

    @property
    def max_block_count(self) -> int:
        """返回最大容量下允许的数据块总数。"""

        return self.config.disk_max_size_bytes // self.config.block_size_bytes

    @property
    def _bitmap_size_bytes(self) -> int:
        """返回位图所需字节数。

        位图长度按“最大块数”一次性确定，这样磁盘扩容时不需要变更
        元数据布局，只需要更新当前容量和位图内容。
        """

        return math.ceil(self.max_block_count / 8)

    @property
    def _metadata_size_bytes(self) -> int:
        """返回元数据区域大小。

        当前实现直接复用“一个块大小”作为元数据区。
        这样逻辑简单，且对于当前默认最大容量，位图也能放得下。
        """

        return self.config.block_size_bytes

    @property
    def _data_offset_bytes(self) -> int:
        """返回数据区起始偏移。

        所有逻辑块都从这个偏移后开始编号。
        """

        return self._metadata_size_bytes

    def open(self) -> None:
        """打开或创建磁盘镜像。

        行为分两种：
        - 镜像不存在：创建新镜像并写入初始元数据
        - 镜像已存在：读取元数据并恢复容量与块分配状态
        """

        if self.is_open:
            return

        self.image_path.parent.mkdir(parents=True, exist_ok=True)
        if self.image_path.exists():
            self._open_existing_image()
        else:
            self._create_new_image()

        self.is_open = True

    def close(self) -> None:
        """关闭镜像文件。

        关闭前会先刷新元数据和文件内容，确保重新打开时能恢复。
        """

        if not self.is_open:
            return

        self.flush()
        assert self._file_handle is not None
        self._file_handle.close()
        self._file_handle = None
        self.is_open = False

    def flush(self) -> None:
        """把当前元数据和文件内容刷到磁盘。"""

        self._ensure_open()
        self._write_metadata_block()
        assert self._file_handle is not None
        self._file_handle.flush()
        os.fsync(self._file_handle.fileno())

    def read_block(self, block_id: int) -> bytes:
        """读取指定块号的数据。

        输入约束：
        - 块号必须在当前容量范围内
        - 磁盘必须已经打开
        """

        self._ensure_open()
        self._validate_block_id(block_id)
        assert self._file_handle is not None
        self._file_handle.seek(self._block_offset(block_id))
        payload = self._file_handle.read(self.config.block_size_bytes)
        if len(payload) < self.config.block_size_bytes:
            # 稀疏文件在未实际写入的区域可能读出较短内容，
            # 这里统一补零，保持块设备视角下的固定块长度。
            payload += b"\x00" * (self.config.block_size_bytes - len(payload))
        return payload

    def write_block(self, block_id: int, data: bytes) -> None:
        """向指定块写入一个完整块的数据。

        当前实现要求一次必须写满一个块。
        这样可以保持块接口语义简单，后续文件系统层再决定如何切片。
        """

        self._ensure_open()
        if len(data) != self.config.block_size_bytes:
            raise ValueError("data length must equal block_size_bytes")

        self._ensure_capacity_for_block(block_id)
        self._validate_block_id(block_id)

        assert self._file_handle is not None
        self._file_handle.seek(self._block_offset(block_id))
        self._file_handle.write(data)
        self._set_allocated(block_id, True)
        self._write_metadata_block()

    def allocate_blocks(self, count: int) -> list[int]:
        """分配指定数量的空闲块。

        如果当前容量不足，会按扩容步长逐步扩容，直到满足请求或到达上限。
        """

        self._ensure_open()
        if count <= 0:
            raise ValueError("count must be greater than zero")

        while self._count_free_blocks() < count:
            self._grow_once()

        allocated: list[int] = []
        for block_id in range(self.current_block_count):
            if not self._is_allocated(block_id):
                self._set_allocated(block_id, True)
                allocated.append(block_id)
                if len(allocated) == count:
                    break

        self._write_metadata_block()
        return allocated

    def free_blocks(self, block_ids: list[int]) -> None:
        """释放一组块。

        当前实现释放时会同步把块内容清零，目的是让后续测试和调试时
        行为更可预期，也减少“脏数据看起来像有效内容”的混淆。
        """

        self._ensure_open()
        assert self._file_handle is not None

        for block_id in block_ids:
            self._validate_block_id(block_id)

        zero_block = b"\x00" * self.config.block_size_bytes
        for block_id in block_ids:
            self._set_allocated(block_id, False)
            self._file_handle.seek(self._block_offset(block_id))
            self._file_handle.write(zero_block)

        self._write_metadata_block()

    def _create_new_image(self) -> None:
        """创建新的磁盘镜像并写入初始元数据。"""

        self.current_size_bytes = self.config.disk_initial_size_bytes
        self._allocated_bitmap = bytearray(self._bitmap_size_bytes)
        self._file_handle = self.image_path.open("w+b")
        self._file_handle.truncate(self._total_file_size_bytes())
        self._write_metadata_block()

    def _open_existing_image(self) -> None:
        """打开已有磁盘镜像并恢复内存态状态。"""

        self._file_handle = self.image_path.open("r+b")
        metadata_block = self._file_handle.read(self._metadata_size_bytes)
        if len(metadata_block) != self._metadata_size_bytes:
            raise ValueError("disk metadata block is incomplete")

        (
            magic,
            version,
            stored_initial_size,
            stored_growth_step,
            stored_max_size,
            stored_block_size,
            stored_current_size,
        ) = _HEADER_STRUCT.unpack_from(metadata_block, 0)

        if magic != _MAGIC:
            raise ValueError("disk image magic mismatch")
        if version != _VERSION:
            raise ValueError("unsupported disk image version")

        self._validate_stored_config(
            stored_initial_size=stored_initial_size,
            stored_growth_step=stored_growth_step,
            stored_max_size=stored_max_size,
            stored_block_size=stored_block_size,
        )

        bitmap_start = _HEADER_STRUCT.size
        bitmap_end = bitmap_start + self._bitmap_size_bytes
        self._allocated_bitmap = bytearray(metadata_block[bitmap_start:bitmap_end])
        self.current_size_bytes = stored_current_size

        expected_file_size = self._total_file_size_bytes()
        actual_file_size = self.image_path.stat().st_size
        if actual_file_size < expected_file_size:
            raise ValueError("disk image is smaller than recorded capacity")

    def _write_metadata_block(self) -> None:
        """把当前容量与位图状态写回元数据块。"""

        assert self._file_handle is not None
        metadata = bytearray(self._metadata_size_bytes)
        _HEADER_STRUCT.pack_into(
            metadata,
            0,
            _MAGIC,
            _VERSION,
            self.config.disk_initial_size_bytes,
            self.config.disk_growth_step_bytes,
            self.config.disk_max_size_bytes,
            self.config.block_size_bytes,
            self.current_size_bytes,
        )
        bitmap_start = _HEADER_STRUCT.size
        metadata[bitmap_start : bitmap_start + len(self._allocated_bitmap)] = self._allocated_bitmap
        self._file_handle.seek(0)
        self._file_handle.write(metadata)

    def _validate_metadata_capacity(self) -> None:
        """确认一个元数据块足够容纳头部和位图。"""

        required_bytes = _HEADER_STRUCT.size + self._bitmap_size_bytes
        if required_bytes > self._metadata_size_bytes:
            raise ValueError("metadata does not fit into a single block")

    def _validate_stored_config(
        self,
        *,
        stored_initial_size: int,
        stored_growth_step: int,
        stored_max_size: int,
        stored_block_size: int,
    ) -> None:
        """校验镜像中的配置是否与当前对象配置兼容。"""

        expected = (
            self.config.disk_initial_size_bytes,
            self.config.disk_growth_step_bytes,
            self.config.disk_max_size_bytes,
            self.config.block_size_bytes,
        )
        stored = (
            stored_initial_size,
            stored_growth_step,
            stored_max_size,
            stored_block_size,
        )
        if stored != expected:
            raise ValueError("disk image configuration does not match requested config")

    def _count_free_blocks(self) -> int:
        """统计当前容量范围内的空闲块数。"""

        free_count = 0
        for block_id in range(self.current_block_count):
            if not self._is_allocated(block_id):
                free_count += 1
        return free_count

    def _is_allocated(self, block_id: int) -> bool:
        """判断指定块是否已被标记为已分配。"""

        byte_index, bit_index = divmod(block_id, 8)
        return bool(self._allocated_bitmap[byte_index] & (1 << bit_index))

    def _set_allocated(self, block_id: int, allocated: bool) -> None:
        """更新位图中的分配标记。"""

        byte_index, bit_index = divmod(block_id, 8)
        if allocated:
            self._allocated_bitmap[byte_index] |= 1 << bit_index
        else:
            self._allocated_bitmap[byte_index] &= ~(1 << bit_index)

    def _ensure_capacity_for_block(self, block_id: int) -> None:
        """确保指定块号在当前容量范围内。

        如果块号超过当前容量，会按扩容步长持续扩容到足够容纳它。
        """

        if block_id < 0:
            raise ValueError("block_id must be non-negative")

        while block_id >= self.current_block_count:
            self._grow_once()

    def _grow_once(self) -> None:
        """按一个扩容步长增长当前容量。

        如果再增长会超过上限，则直接抛出 `DiskFullError`。
        """

        next_size_bytes = min(
            self.current_size_bytes + self.config.disk_growth_step_bytes,
            self.config.disk_max_size_bytes,
        )
        if next_size_bytes == self.current_size_bytes:
            raise DiskFullError("virtual disk reached maximum size")

        self.current_size_bytes = next_size_bytes
        assert self._file_handle is not None
        self._file_handle.truncate(self._total_file_size_bytes())
        self._write_metadata_block()

    def _validate_block_id(self, block_id: int) -> None:
        """校验块号是否位于当前容量范围内。"""

        if block_id < 0 or block_id >= self.current_block_count:
            raise ValueError("block_id is out of range")

    def _block_offset(self, block_id: int) -> int:
        """计算指定块在镜像文件中的实际字节偏移。"""

        return self._data_offset_bytes + (block_id * self.config.block_size_bytes)

    def _total_file_size_bytes(self) -> int:
        """返回镜像文件的总大小。

        这里的总大小 = 元数据块 + 当前容量。
        """

        return self._metadata_size_bytes + self.current_size_bytes

    def _ensure_open(self) -> None:
        """确保磁盘已经打开。"""

        if not self.is_open or self._file_handle is None:
            raise RuntimeError("disk image is not open")

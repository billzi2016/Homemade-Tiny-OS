"""Phase 3 的虚拟文件系统实现。

这版实现目标是先把“可用闭环”做出来：
- 路径解析
- 目录创建
- 文件创建、读取、覆盖写、追加写
- 删除与块回收
- 元数据持久化与重启恢复

当前重点是稳定性和可测试性，不追求复杂文件系统格式。
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Callable

from tinyos.config import TinyOSConfig
from tinyos.errors import AlreadyExistsError, PathNotFoundError, PermissionDeniedError
from tinyos.storage import ExpandableVirtualDisk
from tinyos.vfs.directory_entry import DirectoryEntry
from tinyos.vfs.index import DirectoryIndex, MemoryDirectoryIndex, SortedContainersDirectoryIndex
from tinyos.vfs.inode import Inode
from tinyos.vfs.path import normalize_path, split_parent

_SUPERBLOCK_MAGIC = "TNYOSFS1"
_SUPERBLOCK_VERSION = 1
_PRIMARY_SUPERBLOCK_BLOCK_ID = 0
_BACKUP_SUPERBLOCK_BLOCK_ID = 1


@dataclass(slots=True)
class VirtualFileSystem:
    """虚拟文件系统对象。

    当前阶段它直接依赖 `ExpandableVirtualDisk`，并把整个元数据状态
    序列化后写入一组保留块里。这个设计足够支持 Phase 3 的教学目标：
    - 目录与文件的基本抽象
    - 数据块映射
    - 冷启动恢复
    """

    config: TinyOSConfig = field(default_factory=TinyOSConfig)
    disk: ExpandableVirtualDisk | None = None
    index_factory: Callable[[], DirectoryIndex] = SortedContainersDirectoryIndex
    root_path: str = "/"
    current_working_directory: str = "/"
    _loaded: bool = field(init=False, default=False, repr=False)
    _next_inode_id: int = field(init=False, default=1, repr=False)
    _root_inode_id: int = field(init=False, default=1, repr=False)
    _metadata_blocks: list[int] = field(init=False, default_factory=list, repr=False)
    _inodes: dict[int, Inode] = field(init=False, default_factory=dict, repr=False)
    _directories: dict[int, DirectoryIndex] = field(init=False, default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        """初始化对象，但推迟实际磁盘加载。"""

        if self.disk is None:
            self.disk = ExpandableVirtualDisk(config=self.config)

    def mkdir(self, path: str, cwd: str | None = None, acting_uid: int = 0) -> None:
        """创建目录。"""

        self._ensure_loaded()
        absolute_path = self._normalize(path, cwd)
        parent_inode_id, name = self._resolve_parent(absolute_path)
        parent_inode = self._inodes[parent_inode_id]
        self._require_permission(parent_inode, acting_uid=acting_uid, permission="write")
        parent_directory = self._directories[parent_inode_id]
        if parent_directory.contains(name):
            raise AlreadyExistsError(f"path already exists: {absolute_path}")

        inode = self._create_inode(kind="directory", permissions=0o755, owner_uid=acting_uid)
        self._directories[inode.inode_id] = self.index_factory()
        parent_directory.set(name, inode.inode_id)
        self._touch_inode(parent_inode_id)
        self._persist()

    def create_file(self, path: str, cwd: str | None = None, acting_uid: int = 0) -> None:
        """创建空文件。"""

        self._ensure_loaded()
        absolute_path = self._normalize(path, cwd)
        parent_inode_id, name = self._resolve_parent(absolute_path)
        parent_inode = self._inodes[parent_inode_id]
        self._require_permission(parent_inode, acting_uid=acting_uid, permission="write")
        parent_directory = self._directories[parent_inode_id]
        if parent_directory.contains(name):
            raise AlreadyExistsError(f"path already exists: {absolute_path}")

        inode = self._create_inode(kind="file", permissions=0o644, owner_uid=acting_uid)
        parent_directory.set(name, inode.inode_id)
        self._touch_inode(parent_inode_id)
        self._persist()

    def read_file(self, path: str, cwd: str | None = None, acting_uid: int = 0) -> bytes:
        """读取文件内容。"""

        self._ensure_loaded()
        inode = self._resolve_inode(self._normalize(path, cwd))
        if inode.kind != "file":
            raise ValueError("path does not reference a file")
        self._require_permission(inode, acting_uid=acting_uid, permission="read")

        payload = bytearray()
        for block_id in inode.data_blocks:
            payload.extend(self.disk.read_block(block_id))
        return bytes(payload[: inode.size])

    def write_file(
        self,
        path: str,
        data: bytes,
        cwd: str | None = None,
        append: bool = False,
        acting_uid: int = 0,
    ) -> None:
        """写入文件内容。

        当前版本支持：
        - 覆盖写
        - 追加写
        """

        self._ensure_loaded()
        absolute_path = self._normalize(path, cwd)
        inode = self._resolve_inode(absolute_path)
        if inode.kind != "file":
            raise ValueError("path does not reference a file")
        self._require_permission(inode, acting_uid=acting_uid, permission="write")

        existing = self.read_file(absolute_path, acting_uid=acting_uid) if append else b""
        payload = existing + data

        if inode.data_blocks:
            self.disk.free_blocks(inode.data_blocks)
            inode.data_blocks = []

        block_size = self.config.block_size_bytes
        required_blocks = math.ceil(len(payload) / block_size) if payload else 0
        if required_blocks:
            inode.data_blocks = self.disk.allocate_blocks(required_blocks)
            for offset, block_id in enumerate(inode.data_blocks):
                chunk = payload[offset * block_size : (offset + 1) * block_size]
                padded_chunk = chunk.ljust(block_size, b"\x00")
                self.disk.write_block(block_id, padded_chunk)

        inode.size = len(payload)
        inode.touch()
        self._persist()

    def delete_file(self, path: str, cwd: str | None = None, acting_uid: int = 0) -> None:
        """删除文件或空目录。"""

        self._ensure_loaded()
        absolute_path = self._normalize(path, cwd)
        if absolute_path == "/":
            raise ValueError("root directory cannot be deleted")

        parent_inode_id, name = self._resolve_parent(absolute_path)
        parent_inode = self._inodes[parent_inode_id]
        self._require_permission(parent_inode, acting_uid=acting_uid, permission="write")
        parent_directory = self._directories[parent_inode_id]
        inode_id = parent_directory.get(name)
        inode = self._inodes[inode_id]

        if inode.kind == "directory" and self._directories[inode_id].list_entries():
            raise ValueError("directory is not empty")

        if inode.kind == "file" and inode.data_blocks:
            self.disk.free_blocks(inode.data_blocks)

        if inode.kind == "directory":
            del self._directories[inode_id]

        del self._inodes[inode_id]
        parent_directory.delete(name)
        self._touch_inode(parent_inode_id)
        self._persist()

    def list_dir(self, path: str = "/", cwd: str | None = None, acting_uid: int = 0) -> list[DirectoryEntry]:
        """列出目录项。"""

        self._ensure_loaded()
        inode = self._resolve_inode(self._normalize(path, cwd))
        if inode.kind != "directory":
            raise ValueError("path does not reference a directory")
        self._require_permission(inode, acting_uid=acting_uid, permission="read")
        return self._directories[inode.inode_id].list_entries()

    def stat(self, path: str, cwd: str | None = None, acting_uid: int = 0) -> Inode:
        """返回 inode 元数据。"""

        self._ensure_loaded()
        inode = self._resolve_inode(self._normalize(path, cwd))
        self._require_permission(inode, acting_uid=acting_uid, permission="read")
        return inode

    def close(self) -> None:
        """关闭底层磁盘。"""

        if self.disk is not None:
            self.disk.close()
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """确保 VFS 已经完成初始化或恢复。"""

        if self._loaded:
            return

        assert self.disk is not None
        self.disk.open()
        primary_superblock, primary_error = self._try_read_superblock(_PRIMARY_SUPERBLOCK_BLOCK_ID)
        backup_superblock, backup_error = self._try_read_superblock(_BACKUP_SUPERBLOCK_BLOCK_ID)

        if primary_superblock is None and backup_superblock is None:
            if primary_error is not None or backup_error is not None:
                raise ValueError("filesystem metadata corrupted")
            self._format_new_filesystem()
            return

        if primary_superblock is not None:
            self._load_from_superblock(primary_superblock)
        elif backup_superblock is not None:
            self._load_from_superblock(backup_superblock)
        else:
            raise ValueError("filesystem metadata corrupted")
        self._loaded = True

    def _format_new_filesystem(self) -> None:
        """格式化一个新的文件系统。"""

        root_inode = Inode(
            inode_id=1,
            kind="directory",
            permissions=0o755,
            owner_uid=0,
        )
        self._root_inode_id = 1
        self._next_inode_id = 2
        self._metadata_blocks = []
        self._inodes = {root_inode.inode_id: root_inode}
        self._directories = {root_inode.inode_id: self.index_factory()}
        self._loaded = True
        self._persist()

    def _load_from_superblock(self, superblock: dict[str, object]) -> None:
        """根据超级块恢复文件系统状态。"""

        self._root_inode_id = int(superblock["root_inode_id"])
        self._next_inode_id = int(superblock["next_inode_id"])
        self._metadata_blocks = [int(block_id) for block_id in superblock["metadata_blocks"]]
        payload_size = int(superblock["payload_size"])

        metadata_payload = bytearray()
        for block_id in self._metadata_blocks:
            metadata_payload.extend(self.disk.read_block(block_id))
        state = json.loads(metadata_payload[:payload_size].decode("utf-8"))

        self._inodes = {
            int(inode_id): Inode(
                inode_id=int(serialized["inode_id"]),
                kind=str(serialized["kind"]),
                size=int(serialized["size"]),
                created_at=float(serialized["created_at"]),
                modified_at=float(serialized["modified_at"]),
                permissions=int(serialized["permissions"]),
                owner_uid=int(serialized["owner_uid"]),
                data_blocks=[int(block_id) for block_id in serialized["data_blocks"]],
            )
            for inode_id, serialized in state["inodes"].items()
        }
        self._directories = {
            int(inode_id): self.index_factory()
            for inode_id, mapping in state["directories"].items()
        }
        for inode_id, mapping in state["directories"].items():
            directory = self._directories[int(inode_id)]
            for name, target in mapping.items():
                directory.set(name, int(target))

    def _persist(self) -> None:
        """把当前文件系统状态写入磁盘。

        持久化格式分两层：
        - 块 0：固定位置的超级块
        - 其他保留块：文件系统状态 JSON
        """

        state_payload = json.dumps(
            {
                "inodes": {
                    str(inode_id): {
                        "inode_id": inode.inode_id,
                        "kind": inode.kind,
                        "size": inode.size,
                        "created_at": inode.created_at,
                        "modified_at": inode.modified_at,
                        "permissions": inode.permissions,
                        "owner_uid": inode.owner_uid,
                        "data_blocks": inode.data_blocks,
                    }
                    for inode_id, inode in self._inodes.items()
                },
                "directories": {
                    str(inode_id): directory.to_mapping()
                    for inode_id, directory in self._directories.items()
                },
            },
            sort_keys=True,
        ).encode("utf-8")

        placeholder = self._encode_json_block(
            {
                "magic": _SUPERBLOCK_MAGIC,
                "version": _SUPERBLOCK_VERSION,
                "root_inode_id": self._root_inode_id,
                "next_inode_id": self._next_inode_id,
                "payload_size": 0,
                "metadata_blocks": [],
            }
        )
        self.disk.write_block(_PRIMARY_SUPERBLOCK_BLOCK_ID, placeholder)
        self.disk.write_block(_BACKUP_SUPERBLOCK_BLOCK_ID, placeholder)

        block_size = self.config.block_size_bytes
        required_blocks = max(1, math.ceil(len(state_payload) / block_size))

        if len(self._metadata_blocks) < required_blocks:
            self._metadata_blocks.extend(self.disk.allocate_blocks(required_blocks - len(self._metadata_blocks)))
        elif len(self._metadata_blocks) > required_blocks:
            redundant_blocks = self._metadata_blocks[required_blocks:]
            self.disk.free_blocks(redundant_blocks)
            self._metadata_blocks = self._metadata_blocks[:required_blocks]

        for offset, block_id in enumerate(self._metadata_blocks):
            chunk = state_payload[offset * block_size : (offset + 1) * block_size]
            self.disk.write_block(block_id, chunk.ljust(block_size, b"\x00"))

        superblock = self._encode_json_block(
            {
                "magic": _SUPERBLOCK_MAGIC,
                "version": _SUPERBLOCK_VERSION,
                "root_inode_id": self._root_inode_id,
                "next_inode_id": self._next_inode_id,
                "payload_size": len(state_payload),
                "metadata_blocks": self._metadata_blocks,
            }
        )
        self.disk.write_block(_PRIMARY_SUPERBLOCK_BLOCK_ID, superblock)
        self.disk.write_block(_BACKUP_SUPERBLOCK_BLOCK_ID, superblock)
        self.disk.flush()

    def _resolve_inode(self, absolute_path: str) -> Inode:
        """把绝对路径解析成 inode。"""

        if absolute_path == "/":
            return self._inodes[self._root_inode_id]

        current_inode = self._inodes[self._root_inode_id]
        current_directory = self._directories[current_inode.inode_id]
        for part in absolute_path.strip("/").split("/"):
            if current_inode.kind != "directory":
                raise PathNotFoundError(f"path not found: {absolute_path}")
            inode_id = current_directory.get(part)
            current_inode = self._inodes[inode_id]
            if current_inode.kind == "directory":
                current_directory = self._directories[current_inode.inode_id]
        return current_inode

    def _resolve_parent(self, absolute_path: str) -> tuple[int, str]:
        """解析父目录 inode 和当前名字。"""

        parent_path, name = split_parent(absolute_path)
        parent_inode = self._resolve_inode(parent_path)
        if parent_inode.kind != "directory":
            raise PathNotFoundError(f"parent path is not a directory: {parent_path}")
        return parent_inode.inode_id, name

    def _create_inode(self, kind: str, permissions: int, owner_uid: int) -> Inode:
        """创建一个新的 inode 并注册到 inode 表。"""

        inode = Inode(
            inode_id=self._next_inode_id,
            kind=kind,
            permissions=permissions,
            owner_uid=owner_uid,
        )
        self._next_inode_id += 1
        self._inodes[inode.inode_id] = inode
        return inode

    def _touch_inode(self, inode_id: int) -> None:
        """更新指定 inode 的修改时间。"""

        self._inodes[inode_id].touch()

    def _normalize(self, path: str, cwd: str | None) -> str:
        """统一入口：把外部路径转成绝对路径。"""

        return normalize_path(path, cwd or self.current_working_directory)

    def _encode_json_block(self, payload: dict[str, object]) -> bytes:
        """把 JSON 对象编码成一个固定大小块。"""

        raw = json.dumps(payload, sort_keys=True).encode("utf-8")
        if len(raw) > self.config.block_size_bytes:
            raise ValueError("superblock payload exceeds block size")
        return raw.ljust(self.config.block_size_bytes, b"\x00")

    def _decode_json_block(self, payload: bytes) -> dict[str, object]:
        """从固定大小块中解出 JSON 对象。"""

        stripped = payload.rstrip(b"\x00")
        if not stripped:
            return {}
        try:
            return json.loads(stripped.decode("utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError("filesystem metadata corrupted") from error

    def _read_superblock(self, block_id: int) -> dict[str, object] | None:
        """读取一个超级块副本。

        返回值语义：
        - `None`：这个块还是空白块
        - `dict`：解析成功且是合法超级块
        - 抛异常：内容存在但已损坏
        """

        payload = self.disk.read_block(block_id)
        if payload.rstrip(b"\x00") == b"":
            return None
        decoded = self._decode_json_block(payload)
        if decoded.get("magic") != _SUPERBLOCK_MAGIC:
            return None
        if int(decoded.get("version", -1)) != _SUPERBLOCK_VERSION:
            raise ValueError("unsupported filesystem metadata version")
        return decoded

    def _try_read_superblock(self, block_id: int) -> tuple[dict[str, object] | None, ValueError | None]:
        """安全读取超级块副本。

        返回值中：
        - 第一个元素是成功解析出的超级块或 `None`
        - 第二个元素是解析失败时的 `ValueError`
        """

        try:
            return self._read_superblock(block_id), None
        except ValueError as error:
            return None, error

    def _require_permission(self, inode: Inode, *, acting_uid: int, permission: str) -> None:
        """验证当前用户是否有权限访问 inode。"""

        if acting_uid == 0:
            return

        permission_bit = {
            "read": 0o4,
            "write": 0o2,
            "execute": 0o1,
        }[permission]
        mode = inode.permissions
        owner_bits = (mode >> 6) & 0o7
        other_bits = mode & 0o7
        active_bits = owner_bits if acting_uid == inode.owner_uid else other_bits
        if not (active_bits & permission_bit):
            raise PermissionDeniedError("permission denied")

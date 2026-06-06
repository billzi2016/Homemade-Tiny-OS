"""目录索引抽象接口。

这层的目的不是规定底层必须怎么存，而是固定 VFS 能依赖的最小能力。
后续如果要切到真正的 B+ 树库，只需要替换适配层实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from tinyos.vfs.directory_entry import DirectoryEntry


class DirectoryIndex(ABC):
    """目录索引抽象基类。"""

    @abstractmethod
    def get(self, name: str) -> int:
        """按名字获取 inode 编号。"""

    @abstractmethod
    def set(self, name: str, inode_id: int) -> None:
        """写入或覆盖一个目录项。"""

    @abstractmethod
    def delete(self, name: str) -> None:
        """删除一个目录项。"""

    @abstractmethod
    def contains(self, name: str) -> bool:
        """判断目录项是否存在。"""

    @abstractmethod
    def list_entries(self) -> list[DirectoryEntry]:
        """返回稳定有序的目录项列表。"""

    @abstractmethod
    def to_mapping(self) -> dict[str, int]:
        """导出为可序列化映射。"""

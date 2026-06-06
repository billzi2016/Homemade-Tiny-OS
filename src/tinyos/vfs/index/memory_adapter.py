"""基于内存映射的目录索引适配器。

这不是最终性能方案，但它满足 Phase 3 的几个关键要求：
- 输出顺序稳定
- 不泄露底层容器细节
- 可被后续真正的 B+ 树适配器替换
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tinyos.errors import PathNotFoundError
from tinyos.vfs.directory_entry import DirectoryEntry
from tinyos.vfs.index.interface import DirectoryIndex


@dataclass(slots=True)
class MemoryDirectoryIndex(DirectoryIndex):
    """使用内置字典保存目录项，再在输出时排序。"""

    entries: dict[str, int] = field(default_factory=dict)

    def get(self, name: str) -> int:
        """获取目录项对应的 inode 编号。"""

        if name not in self.entries:
            raise PathNotFoundError(f"entry not found: {name}")
        return self.entries[name]

    def set(self, name: str, inode_id: int) -> None:
        """写入目录项。"""

        self.entries[name] = inode_id

    def delete(self, name: str) -> None:
        """删除目录项。"""

        if name not in self.entries:
            raise PathNotFoundError(f"entry not found: {name}")
        del self.entries[name]

    def contains(self, name: str) -> bool:
        """判断目录项是否存在。"""

        return name in self.entries

    def list_entries(self) -> list[DirectoryEntry]:
        """按名字稳定排序输出目录项。"""

        return [
            DirectoryEntry(name=name, inode_id=self.entries[name])
            for name in sorted(self.entries.keys())
        ]

    def to_mapping(self) -> dict[str, int]:
        """导出普通字典，供持久化使用。"""

        return dict(self.entries)

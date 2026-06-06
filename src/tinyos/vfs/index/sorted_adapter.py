"""基于 `sortedcontainers` 的目录索引适配器。

这个适配器的目的不是把 VFS 绑死在第三方库上，而是把一个成熟的、
可维护的有序映射实现接到项目自己的 `DirectoryIndex` 抽象后面。

这样做有几个好处：
- VFS 仍只依赖项目自己的接口
- 目录项天然保持有序
- 后续若切换到真正的 B+ 树库，替换点仍然清晰
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sortedcontainers import SortedDict

from tinyos.errors import PathNotFoundError
from tinyos.vfs.directory_entry import DirectoryEntry
from tinyos.vfs.index.interface import DirectoryIndex


@dataclass(slots=True)
class SortedContainersDirectoryIndex(DirectoryIndex):
    """使用 `sortedcontainers.SortedDict` 的目录索引适配器。"""

    entries: SortedDict[str, int] = field(default_factory=SortedDict)

    def get(self, name: str) -> int:
        """按名字获取 inode 编号。"""

        if name not in self.entries:
            raise PathNotFoundError(f"entry not found: {name}")
        return self.entries[name]

    def set(self, name: str, inode_id: int) -> None:
        """写入或覆盖目录项。"""

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
        """按有序键输出目录项。"""

        return [
            DirectoryEntry(name=name, inode_id=inode_id)
            for name, inode_id in self.entries.items()
        ]

    def to_mapping(self) -> dict[str, int]:
        """导出普通字典，供持久化使用。"""

        return dict(self.entries)

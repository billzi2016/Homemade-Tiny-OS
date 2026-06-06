"""目录项定义。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DirectoryEntry:
    """目录中的一个名字到 inode 的映射。"""

    name: str
    inode_id: int

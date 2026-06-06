"""inode 元数据模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time


@dataclass(slots=True)
class Inode:
    """Tiny OS 中的 inode 对象。

    当前阶段先保留文件系统最核心的元数据字段：
    - inode 编号
    - 类型
    - 文件大小
    - 创建/修改时间
    - 权限位
    - 所属用户
    - 数据块列表
    """

    inode_id: int
    kind: str
    size: int = 0
    created_at: float = field(default_factory=time)
    modified_at: float = field(default_factory=time)
    permissions: int = 0o755
    owner_uid: int = 0
    data_blocks: list[int] = field(default_factory=list)

    def touch(self) -> None:
        """更新 inode 的修改时间。"""

        self.modified_at = time()

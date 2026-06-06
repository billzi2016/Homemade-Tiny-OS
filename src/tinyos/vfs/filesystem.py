"""Phase 1 的文件系统骨架。

当前阶段先固定 VFS 对象本身，而不是实现真实目录和文件操作。
这样后续 Phase 3 可以围绕这个对象继续补 inode、路径解析和目录索引。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tinyos.config import TinyOSConfig


@dataclass(slots=True)
class VirtualFileSystem:
    """虚拟文件系统骨架对象。

    这里先只保留配置和根目录标识，确认对象边界已经存在。
    """

    config: TinyOSConfig = field(default_factory=TinyOSConfig)
    root_path: str = "/"

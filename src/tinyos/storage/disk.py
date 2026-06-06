"""Phase 1 的虚拟磁盘骨架。

这一阶段只保证：
- 有统一的磁盘对象
- 能携带配置
- 能反映当前容量基线

不保证：
- 真正的块读写
- 真正的扩容
- 真正的镜像文件持久化
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tinyos.config import TinyOSConfig


@dataclass(slots=True)
class ExpandableVirtualDisk:
    """可扩展虚拟磁盘骨架对象。

    当前只保存配置和“当前容量”这两个最基础状态。
    这样 Phase 2 实现块分配和扩容时，可以直接在这个类上演进，
    不需要推翻接口入口。
    """

    config: TinyOSConfig = field(default_factory=TinyOSConfig)
    current_size_bytes: int = field(init=False)

    def __post_init__(self) -> None:
        """用配置里的初始容量建立最小可验证状态。"""
        self.current_size_bytes = self.config.disk_initial_size_bytes

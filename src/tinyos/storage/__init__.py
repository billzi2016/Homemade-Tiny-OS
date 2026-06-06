"""存储层包入口。

当前 Phase 1 只暴露虚拟磁盘骨架类，先把导入路径固定下来，
Phase 2 再逐步填充真实磁盘逻辑。
"""

from tinyos.storage.disk import ExpandableVirtualDisk

__all__ = ["ExpandableVirtualDisk"]

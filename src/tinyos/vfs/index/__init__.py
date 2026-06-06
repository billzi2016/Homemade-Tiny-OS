"""目录索引模块入口。"""

from tinyos.vfs.index.interface import DirectoryIndex
from tinyos.vfs.index.memory_adapter import MemoryDirectoryIndex

__all__ = ["DirectoryIndex", "MemoryDirectoryIndex"]

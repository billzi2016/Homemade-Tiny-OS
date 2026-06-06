"""Phase 3 目录索引测试。"""

import unittest

from tinyos.errors import PathNotFoundError
from tinyos.vfs.index import MemoryDirectoryIndex


class DirectoryIndexTests(unittest.TestCase):
    """验证目录索引接口与顺序稳定性。"""

    def test_directory_index_supports_basic_crud(self) -> None:
        """目录索引应支持增删查改。"""

        index = MemoryDirectoryIndex()
        index.set("b.txt", 2)
        index.set("a.txt", 1)

        self.assertTrue(index.contains("a.txt"))
        self.assertEqual(index.get("b.txt"), 2)

        index.delete("a.txt")
        self.assertFalse(index.contains("a.txt"))

        with self.assertRaises(PathNotFoundError):
            index.get("a.txt")

    def test_directory_index_output_order_is_stable(self) -> None:
        """目录项输出顺序必须稳定。"""

        index = MemoryDirectoryIndex(entries={"z": 3, "a": 1, "m": 2})
        names = [entry.name for entry in index.list_entries()]
        self.assertEqual(names, ["a", "m", "z"])

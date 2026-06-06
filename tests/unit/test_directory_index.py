"""Phase 3 目录索引测试。"""

import unittest

from tinyos.errors import PathNotFoundError
from tinyos.vfs.index import MemoryDirectoryIndex, SortedContainersDirectoryIndex


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

    def test_sortedcontainers_adapter_supports_same_contract(self) -> None:
        """成熟第三方索引适配器应满足同样的目录索引契约。"""

        index = SortedContainersDirectoryIndex()
        index.set("z.txt", 3)
        index.set("a.txt", 1)
        index.set("m.txt", 2)

        self.assertTrue(index.contains("a.txt"))
        self.assertEqual(index.get("m.txt"), 2)
        self.assertEqual(
            [entry.name for entry in index.list_entries()],
            ["a.txt", "m.txt", "z.txt"],
        )

        index.delete("m.txt")
        with self.assertRaises(PathNotFoundError):
            index.get("m.txt")

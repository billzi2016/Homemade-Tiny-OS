"""Phase 3 路径规范化测试。"""

import unittest

from tinyos.vfs.path import normalize_path, split_parent


class PathNormalizationTests(unittest.TestCase):
    """验证路径规范化行为。"""

    def test_normalize_absolute_and_relative_paths(self) -> None:
        """绝对路径和相对路径都应转成稳定绝对路径。"""

        self.assertEqual(normalize_path("/a//b/./c"), "/a/b/c")
        self.assertEqual(normalize_path("notes.txt", "/home/user"), "/home/user/notes.txt")

    def test_normalize_parent_segments(self) -> None:
        """`..` 应正确回退父目录。"""

        self.assertEqual(normalize_path("../tmp", "/home/user"), "/home/tmp")
        self.assertEqual(normalize_path("../../etc", "/home/user/docs"), "/home/etc")

    def test_split_parent_returns_parent_and_name(self) -> None:
        """父目录和当前节点名应正确拆分。"""

        self.assertEqual(split_parent("/a/b/file.txt"), ("/a/b", "file.txt"))
        self.assertEqual(split_parent("/file.txt"), ("/", "file.txt"))

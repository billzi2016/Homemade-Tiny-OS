"""Phase 3 inode 与目录项模型测试。"""

import unittest

from tinyos.vfs.directory_entry import DirectoryEntry
from tinyos.vfs.inode import Inode


class InodeModelTests(unittest.TestCase):
    """验证核心元数据模型。"""

    def test_inode_and_directory_entry_fields_are_constructible(self) -> None:
        """inode 和目录项应具备基础字段。"""

        inode = Inode(inode_id=7, kind="file", permissions=0o644, owner_uid=1000)
        entry = DirectoryEntry(name="hello.txt", inode_id=7)

        self.assertEqual(inode.inode_id, 7)
        self.assertEqual(inode.kind, "file")
        self.assertEqual(entry.name, "hello.txt")
        self.assertEqual(entry.inode_id, 7)

    def test_inode_touch_updates_modified_time(self) -> None:
        """touch 应推进修改时间。"""

        inode = Inode(inode_id=1, kind="directory")
        original_modified_at = inode.modified_at
        inode.touch()
        self.assertGreaterEqual(inode.modified_at, original_modified_at)

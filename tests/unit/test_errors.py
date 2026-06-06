"""Phase 1 错误层级测试。"""

import unittest

from tinyos.errors import (
    AlreadyExistsError,
    DiskFullError,
    InvalidCommandError,
    PathNotFoundError,
    PermissionDeniedError,
    TinyOSError,
)


class TinyOSErrorHierarchyTests(unittest.TestCase):
    """验证所有领域错误都挂在统一基类下。"""

    def test_domain_errors_inherit_from_base_type(self) -> None:
        """后续各层错误必须能被 `TinyOSError` 统一兜住。"""
        for error_cls in (
            PathNotFoundError,
            AlreadyExistsError,
            DiskFullError,
            PermissionDeniedError,
            InvalidCommandError,
        ):
            self.assertTrue(issubclass(error_cls, TinyOSError))

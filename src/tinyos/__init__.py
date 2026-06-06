"""Tiny OS 顶层包。

当前 Phase 1 只暴露最基础的配置对象和统一错误类型，
目的是先把后续阶段都会依赖的公共入口固定下来。
"""

from tinyos.config import TinyOSConfig
from tinyos.errors import (
    AlreadyExistsError,
    DiskFullError,
    InvalidCommandError,
    PathNotFoundError,
    PermissionDeniedError,
    TinyOSError,
)

__all__ = [
    "AlreadyExistsError",
    "DiskFullError",
    "InvalidCommandError",
    "PathNotFoundError",
    "PermissionDeniedError",
    "TinyOSConfig",
    "TinyOSError",
]

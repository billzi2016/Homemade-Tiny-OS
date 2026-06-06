"""Tiny OS 统一错误层级。

Phase 1 先把错误类型固定下来，后续 Shell、VFS、调度器和磁盘层
都应该尽量抛出这里定义的领域错误，而不是散落的裸 `ValueError`
或 `RuntimeError`。
"""


class TinyOSError(Exception):
    """所有 Tiny OS 领域错误的基类。

    后续如果需要统一做错误映射、日志记录或 Shell 输出转换，
    可以优先捕获这个基类。
    """


class PathNotFoundError(TinyOSError):
    """路径无法解析时抛出。

    主要用于 VFS、路径解析器和 Shell 的文件路径相关命令。
    """


class AlreadyExistsError(TinyOSError):
    """创建已存在节点时抛出。

    例如目录已存在、文件名冲突等情况。
    """


class DiskFullError(TinyOSError):
    """虚拟磁盘无法继续分配空间时抛出。

    这个错误会在 Phase 2/5 里进一步映射到更接近真实系统的
    “No space left on device” 之类输出。
    """


class PermissionDeniedError(TinyOSError):
    """权限不足时抛出。

    后续用于普通用户访问受保护节点、命令无权执行等场景。
    """


class InvalidCommandError(TinyOSError):
    """Shell 输入无法解析或不合法时抛出。"""

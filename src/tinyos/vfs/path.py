"""路径处理工具。

Phase 3 的路径系统先解决最核心的 Unix 风格规则：
- 绝对路径
- 相对路径
- `.`
- `..`
- 根目录 `/`

这里不做符号链接、挂载点或复杂路径语义，只把后续 VFS 依赖的
“规范化绝对路径”固定下来。
"""

from __future__ import annotations


def normalize_path(path: str, cwd: str = "/") -> str:
    """把输入路径规范化为绝对路径。

    参数说明：
    - `path`：用户传入的路径，可以是绝对或相对路径
    - `cwd`：当前工作目录，用于解析相对路径

    返回值始终是：
    - 以 `/` 开头
    - 不包含重复 `/`
    - 不包含 `.` 和可消去的 `..`
    """

    if not path:
        raise ValueError("path must not be empty")
    if not cwd.startswith("/"):
        raise ValueError("cwd must be an absolute path")

    if path.startswith("/"):
        raw_parts = path.split("/")
    else:
        raw_parts = (cwd.rstrip("/") + "/" + path).split("/")

    normalized_parts: list[str] = []
    for part in raw_parts:
        if part in ("", "."):
            continue
        if part == "..":
            if normalized_parts:
                normalized_parts.pop()
            continue
        normalized_parts.append(part)

    return "/" + "/".join(normalized_parts)


def split_parent(path: str) -> tuple[str, str]:
    """把绝对路径拆成父目录路径和当前节点名。"""

    normalized = normalize_path(path)
    if normalized == "/":
        raise ValueError("root path does not have a parent entry name")

    parent, _, name = normalized.rpartition("/")
    if not name:
        raise ValueError("path entry name must not be empty")
    return (parent or "/"), name

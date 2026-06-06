"""单元测试包。

这里在包初始化时把 `src/` 加入 `sys.path`，
目的是让 `python -m unittest discover` 在不安装项目的情况下，
也能直接导入 `tinyos` 包。
"""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_src_on_sys_path() -> None:
    """把项目的 `src/` 目录加入导入路径。

    当前项目采用 `src` 布局，测试在本地直接运行时，
    需要手动把 `src/` 注入到 `sys.path`。
    """

    project_root = Path(__file__).resolve().parents[2]
    src_path = project_root / "src"
    src_path_str = str(src_path)
    if src_path_str not in sys.path:
        sys.path.insert(0, src_path_str)


_ensure_src_on_sys_path()

"""集成测试包。

这里和 `tests/unit` 一样，在包初始化时把 `src/` 加入导入路径，
确保 `unittest discover` 能直接导入项目代码。
"""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_src_on_sys_path() -> None:
    """把项目的 `src/` 目录加入导入路径。"""

    project_root = Path(__file__).resolve().parents[2]
    src_path = project_root / "src"
    src_path_str = str(src_path)
    if src_path_str not in sys.path:
        sys.path.insert(0, src_path_str)


_ensure_src_on_sys_path()

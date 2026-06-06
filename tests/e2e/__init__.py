"""端到端测试包。

当前虽然还没有 e2e 用例，但先把 `src/` 导入路径注入规则补齐，
避免后续新增测试时再重复踩相同问题。
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

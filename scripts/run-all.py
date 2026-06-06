"""顺序运行全部编号脚本。

这个总入口适合两类用途：
- 一键演示当前 Tiny OS 的核心能力
- 一键回归检查当前编号脚本是否全部通过
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from _common import OUTPUT_ROOT, close_logging, emit, setup_script_logging


SCRIPT_ORDER = [
    "01-basic-filesystem.py",
    "02-persistence-recovery.py",
    "03-scheduler-and-shell.py",
    "04-observability.py",
    "05-permissions-and-reliability.py",
    "06-full-demo.py",
]


def main() -> None:
    """顺序执行全部脚本，任何一步失败都立即退出。"""

    scripts_dir = Path(__file__).resolve().parent
    setup_script_logging("run-all.log")
    emit("=" * 78)
    emit("Tiny OS 全量编号脚本运行器")
    emit("=" * 78)

    for script_name in SCRIPT_ORDER:
        script_path = scripts_dir / script_name
        emit("")
        emit("-" * 78)
        emit(f"开始运行: {script_name}")
        emit("-" * 78)
        subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        child_log_path = OUTPUT_ROOT / script_name.replace(".py", ".log")
        if child_log_path.exists():
            for line in child_log_path.read_text(encoding="utf-8").splitlines():
                emit(line)

    emit("")
    emit("=" * 78)
    emit("全部编号脚本运行完成。")
    emit("=" * 78)
    close_logging()


if __name__ == "__main__":
    main()

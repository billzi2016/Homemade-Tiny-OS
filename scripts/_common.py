"""编号演示脚本的公共工具。

这一层的目标不是隐藏逻辑，而是把脚本里重复的初始化、打印和断言整理出来，
让每个 `01`、`02`、`03` 脚本都能更清晰地表达“自己到底在验证什么”。
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import TextIO


def ensure_src_on_sys_path() -> None:
    """把项目的 `src/` 目录加入导入路径。

    这些脚本会从项目根目录直接运行，因此需要显式把 `src/` 放进 `sys.path`，
    否则 Python 找不到 `tinyos` 包。
    """

    project_root = Path(__file__).resolve().parents[1]
    src_path = project_root / "src"
    src_path_str = str(src_path)
    if src_path_str not in sys.path:
        sys.path.insert(0, src_path_str)


ensure_src_on_sys_path()

from tinyos.config import TinyOSConfig
from tinyos.kernel import KernelScheduler
from tinyos.shell import Shell
from tinyos.storage import ExpandableVirtualDisk
from tinyos.vfs import VirtualFileSystem


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = PROJECT_ROOT / "scripts" / ".artifacts"
OUTPUT_ROOT = PROJECT_ROOT / "scripts" / "output"
_LOG_FILE_HANDLE: TextIO | None = None


def banner(title: str) -> None:
    """打印大标题，让脚本输出一眼可读。"""

    emit("")
    emit("=" * 78)
    emit(title)
    emit("=" * 78)


def step(title: str) -> None:
    """打印步骤标题。"""

    emit("")
    emit(f"[STEP] {title}")


def info(message: str) -> None:
    """打印说明信息。"""

    emit(f"  - {message}")


def show_command(command: str) -> None:
    """打印即将执行的 Shell 命令。"""

    if len(command) > 160:
        compact_command = f"{command[:140]} ... [已截断，共 {len(command)} 个字符]"
    else:
        compact_command = command
    emit(f"  $ {compact_command}")


def show_output(output: str) -> None:
    """打印命令输出。

    这里对空输出做显式展示，避免运行者误以为脚本没执行。
    """

    if output == "":
        emit("    -> <空输出，表示命令执行成功但没有返回文本>")
        return
    for line in output.splitlines():
        emit(f"    -> {line}")


def expect_equal(actual: object, expected: object, context: str) -> None:
    """做严格相等断言，并打印中文上下文。"""

    if actual != expected:
        raise AssertionError(f"{context}，期望 {expected!r}，实际得到 {actual!r}")
    emit(f"    [OK] {context}")


def expect_contains(text: str, expected_substring: str, context: str) -> None:
    """做包含断言。"""

    if expected_substring not in text:
        raise AssertionError(f"{context}，期望包含 {expected_substring!r}，实际得到 {text!r}")
    emit(f"    [OK] {context}")


def emit(message: str) -> None:
    """同时写到终端和日志文件。

    这是所有编号脚本统一的输出通道。
    这样运行者在终端能看清楚，事后也能在 `scripts/output/` 里回看完整日志。
    """

    print(message, flush=True)
    if _LOG_FILE_HANDLE is not None:
        _LOG_FILE_HANDLE.write(message + "\n")
        _LOG_FILE_HANDLE.flush()


def clean_artifacts(name: str) -> Path:
    """为单个脚本准备独立产物目录。"""

    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    target_dir = ARTIFACT_ROOT / name
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def setup_script_logging(log_file_name: str) -> Path:
    """初始化当前脚本的日志文件。

    每个脚本在启动时都应该先调用它，这样后续所有 `emit()` 输出
    都会自动双写到终端和日志文件。
    """

    global _LOG_FILE_HANDLE
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    log_path = OUTPUT_ROOT / log_file_name
    if _LOG_FILE_HANDLE is not None:
        _LOG_FILE_HANDLE.close()
    _LOG_FILE_HANDLE = log_path.open("w", encoding="utf-8")
    return log_path


def build_config(
    *,
    initial_size_bytes: int = 8 * 4096,
    growth_step_bytes: int = 4 * 4096,
    max_size_bytes: int = 32 * 4096,
) -> TinyOSConfig:
    """构造脚本默认使用的配置。"""

    return TinyOSConfig(
        disk_initial_size_bytes=initial_size_bytes,
        disk_growth_step_bytes=growth_step_bytes,
        disk_max_size_bytes=max_size_bytes,
        block_size_bytes=4096,
        page_size_bytes=4096,
    )


def boot_shell(
    artifact_dir: Path,
    *,
    disk_name: str,
    uid: int = 0,
    initial_size_bytes: int = 8 * 4096,
    growth_step_bytes: int = 4 * 4096,
    max_size_bytes: int = 32 * 4096,
) -> Shell:
    """启动一个可用的 Tiny OS 会话。

    这里统一完成：
    - 配置创建
    - 磁盘镜像定位
    - VFS 初始化
    - 调度器初始化
    - Shell 初始化
    """

    config = build_config(
        initial_size_bytes=initial_size_bytes,
        growth_step_bytes=growth_step_bytes,
        max_size_bytes=max_size_bytes,
    )
    disk = ExpandableVirtualDisk(artifact_dir / disk_name, config=config)
    vfs = VirtualFileSystem(config=config, disk=disk)
    scheduler = KernelScheduler(config=config)
    return Shell(config=config, vfs=vfs, scheduler=scheduler, stats=scheduler.stats, uid=uid)


def run_shell_command(shell: Shell, command: str) -> str:
    """执行一条 Shell 命令，并把命令和输出清晰打印出来。"""

    show_command(command)
    output = shell.execute(command)
    show_output(output)
    return output


def close_shell(shell: Shell) -> None:
    """安全关闭 Shell。

    编号脚本在结束前都会调用它，确保磁盘句柄正常关闭。
    """

    shell.close()


def close_logging() -> None:
    """关闭当前脚本的日志文件句柄。"""

    global _LOG_FILE_HANDLE
    if _LOG_FILE_HANDLE is not None:
        _LOG_FILE_HANDLE.close()
        _LOG_FILE_HANDLE = None

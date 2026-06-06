"""02 持久化与恢复演示。"""

from __future__ import annotations

from _common import (
    banner,
    boot_shell,
    clean_artifacts,
    close_logging,
    close_shell,
    emit,
    expect_contains,
    expect_equal,
    run_shell_command,
    setup_script_logging,
    step,
)


def main() -> None:
    """验证关闭后重开，文件系统状态仍然保留。"""

    setup_script_logging("02-persistence-recovery.log")
    banner("02 持久化与恢复演示")
    artifact_dir = clean_artifacts("02-persistence-recovery")

    step("第一次启动：创建目录和文件")
    shell = boot_shell(artifact_dir, disk_name="persist.disk")
    try:
        run_shell_command(shell, "mkdir /data")
        run_shell_command(shell, "cd /data")
        run_shell_command(shell, "touch state.txt")
        run_shell_command(shell, 'echo "persistent-state" > state.txt')
        expect_equal(run_shell_command(shell, "cat state.txt"), "persistent-state", "首次启动写入内容应正确")
    finally:
        close_shell(shell)

    step("第二次启动：重新打开同一磁盘，验证状态恢复")
    reopened = boot_shell(artifact_dir, disk_name="persist.disk")
    try:
        run_shell_command(reopened, "cd /data")
        expect_equal(run_shell_command(reopened, "cat state.txt"), "persistent-state", "重启后文件内容应恢复")
        expect_contains(run_shell_command(reopened, "ls"), "state.txt", "重启后目录项应恢复")
    finally:
        close_shell(reopened)

    emit("")
    emit("[DONE] 02 持久化与恢复演示完成。")
    close_logging()


if __name__ == "__main__":
    main()

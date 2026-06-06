"""01 基础文件系统演示。

目标：
- 启动一个 Tiny OS 会话
- 演示最基础的目录、文件、读写、删除命令
- 明确当前系统已经具备的最小“可用文件系统”能力
"""

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
    """运行基础文件系统演示。"""

    setup_script_logging("01-basic-filesystem.log")
    banner("01 基础文件系统演示")
    artifact_dir = clean_artifacts("01-basic-filesystem")
    shell = boot_shell(artifact_dir, disk_name="basic.disk")

    try:
        step("创建目录并检查当前工作目录")
        expect_equal(run_shell_command(shell, "pwd"), "/", "初始工作目录应为根目录")
        run_shell_command(shell, "mkdir /workspace")
        expect_equal(run_shell_command(shell, "cd /workspace"), "/workspace", "切换目录后应进入 /workspace")
        expect_equal(run_shell_command(shell, "pwd"), "/workspace", "pwd 应返回当前目录")

        step("创建文件、写入内容、再读取回来")
        run_shell_command(shell, "touch notes.txt")
        run_shell_command(shell, 'echo "hello tiny os" > notes.txt')
        expect_equal(run_shell_command(shell, "cat notes.txt"), "hello tiny os", "文件内容应与写入内容一致")

        step("列出目录内容")
        ls_output = run_shell_command(shell, "ls")
        expect_contains(ls_output, "notes.txt", "ls 输出应包含新创建的文件")

        step("删除文件并确认目录已清空")
        run_shell_command(shell, "rm notes.txt")
        expect_equal(run_shell_command(shell, "ls"), "", "删除文件后目录应为空")
    finally:
        close_shell(shell)

    emit("")
    emit("[DONE] 01 基础文件系统演示完成。")
    close_logging()


if __name__ == "__main__":
    main()

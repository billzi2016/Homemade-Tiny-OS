"""05 权限与可靠性演示。"""

from __future__ import annotations

from _common import (
    banner,
    boot_shell,
    clean_artifacts,
    close_logging,
    close_shell,
    emit,
    expect_equal,
    run_shell_command,
    setup_script_logging,
    step,
)


def main() -> None:
    """验证普通用户权限拒绝、root 放行和磁盘写满错误。"""

    setup_script_logging("05-permissions-and-reliability.log")
    banner("05 权限与可靠性演示")
    artifact_dir = clean_artifacts("05-permissions-and-reliability")

    step("普通用户尝试在根目录创建文件，应被拒绝")
    user_shell = boot_shell(artifact_dir, disk_name="permissions.disk", uid=1000)
    try:
        result = run_shell_command(user_shell, "touch /blocked.txt")
        expect_equal(result, "Permission denied", "普通用户在根目录写文件应被拒绝")
    finally:
        close_shell(user_shell)

    step("root 用户应可以完成相同操作")
    root_shell = boot_shell(artifact_dir, disk_name="permissions.disk", uid=0)
    try:
        expect_equal(run_shell_command(root_shell, "touch /root.txt"), "", "root 创建文件应成功")
        expect_equal(run_shell_command(root_shell, 'echo "root-ok" > /root.txt'), "", "root 写文件应成功")
        expect_equal(run_shell_command(root_shell, "cat /root.txt"), "root-ok", "root 写入内容应可读回")
    finally:
        close_shell(root_shell)

    step("构造一个很小的磁盘，验证写满后的错误提示")
    tiny_shell = boot_shell(
        artifact_dir,
        disk_name="disk-full.disk",
        uid=0,
        initial_size_bytes=4 * 4096,
        growth_step_bytes=4096,
        max_size_bytes=4 * 4096,
    )
    try:
        run_shell_command(tiny_shell, "touch /big.bin")
        full_result = run_shell_command(tiny_shell, f'echo "{"A" * 9000}" > /big.bin')
        expect_equal(full_result, "No space left on device", "磁盘写满后应返回稳定错误文本")
    finally:
        close_shell(tiny_shell)

    emit("")
    emit("[DONE] 05 权限与可靠性演示完成。")
    close_logging()


if __name__ == "__main__":
    main()

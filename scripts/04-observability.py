"""04 系统观测演示。"""

from __future__ import annotations

from _common import (
    banner,
    boot_shell,
    clean_artifacts,
    close_logging,
    close_shell,
    emit,
    expect_contains,
    run_shell_command,
    setup_script_logging,
    step,
)


def observer_task():
    """最小观测任务。"""

    yield "tick-1"
    yield "tick-2"


def main() -> None:
    """演示 `top`、`sysstat`、`dmesg`。"""

    setup_script_logging("04-observability.log")
    banner("04 系统观测演示")
    artifact_dir = clean_artifacts("04-observability")
    shell = boot_shell(artifact_dir, disk_name="observability.disk")

    try:
        step("准备一些运行状态，确保观测命令有内容可看")
        shell.scheduler.create_process(name="observer", task=observer_task(), cwd=shell.cwd)
        shell.scheduler.schedule_once()
        run_shell_command(shell, "mkdir /obs")
        run_shell_command(shell, "cd /obs")
        run_shell_command(shell, "touch a.txt")
        run_shell_command(shell, 'echo "observe" > a.txt')

        step("查看 top 输出")
        top_output = run_shell_command(shell, "top")
        expect_contains(top_output, "ticks=", "top 应显示总 tick 数")
        expect_contains(top_output, "queue=", "top 应显示就绪队列")

        step("查看 sysstat 输出")
        sysstat_output = run_shell_command(shell, "sysstat")
        expect_contains(sysstat_output, "disk_current=", "sysstat 应显示当前磁盘大小")
        expect_contains(sysstat_output, "scheduler_switches=", "sysstat 应显示调度切换次数")

        step("查看 dmesg 输出")
        dmesg_output = run_shell_command(shell, "dmesg")
        expect_contains(dmesg_output, "[SCHED]", "dmesg 应包含调度日志")
        expect_contains(dmesg_output, "[SHELL]", "dmesg 应包含 Shell 操作日志")
    finally:
        close_shell(shell)

    emit("")
    emit("[DONE] 04 系统观测演示完成。")
    close_logging()


if __name__ == "__main__":
    main()

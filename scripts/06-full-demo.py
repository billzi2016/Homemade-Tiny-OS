"""06 完整系统演示。

这个脚本把前面几个编号脚本的关键路径串起来，适合：
- 自己回归检查
- 给别人演示
- 快速判断当前 Tiny OS 是否处于“基本可用”状态
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
    info,
    run_shell_command,
    setup_script_logging,
    step,
)


def worker(shell):
    """示例任务：在调度过程中写日志。"""

    shell.execute("cd /app")
    shell.execute('echo "task-step-1" > task.log')
    yield "step-1"
    shell.execute('echo "task-step-1task-step-2" > task.log')
    yield "step-2"


def main() -> None:
    """运行完整系统演示。"""

    setup_script_logging("06-full-demo.log")
    banner("06 完整系统演示")
    artifact_dir = clean_artifacts("06-full-demo")
    shell = boot_shell(artifact_dir, disk_name="full-demo.disk", uid=0)

    try:
        step("启动系统并创建工作目录")
        run_shell_command(shell, "mkdir /app")
        run_shell_command(shell, "cd /app")
        expect_equal(run_shell_command(shell, "pwd"), "/app", "完整演示中应能切换到 /app")

        step("创建基础文件")
        run_shell_command(shell, "touch readme.txt")
        run_shell_command(shell, 'echo "tiny os runtime" > readme.txt')
        expect_equal(run_shell_command(shell, "cat readme.txt"), "tiny os runtime", "readme.txt 内容应正确")

        step("创建并推进协作式任务")
        pcb = shell.scheduler.create_process(name="writer", task=worker(shell), cwd=shell.cwd)
        info(f"writer 任务 PID = {pcb.pid}")
        shell.scheduler.schedule_once()
        shell.scheduler.schedule_once()
        shell.scheduler.schedule_once()

        expect_equal(run_shell_command(shell, "cat task.log"), "task-step-1task-step-2", "任务日志应完整落盘")

        step("查看进程表和监控信息")
        expect_contains(run_shell_command(shell, "ps"), str(pcb.pid), "ps 应包含 writer 任务")
        expect_contains(run_shell_command(shell, "top"), "ticks=", "top 应输出 tick 统计")
        expect_contains(run_shell_command(shell, "sysstat"), "disk_current=", "sysstat 应输出磁盘状态")
        expect_contains(run_shell_command(shell, "dmesg"), "[SCHED]", "dmesg 应记录调度行为")
    finally:
        close_shell(shell)

    step("关闭后重新启动，验证状态恢复")
    reopened = boot_shell(artifact_dir, disk_name="full-demo.disk", uid=0)
    try:
        run_shell_command(reopened, "cd /app")
        expect_equal(run_shell_command(reopened, "cat readme.txt"), "tiny os runtime", "重启后 readme.txt 应恢复")
        expect_equal(run_shell_command(reopened, "cat task.log"), "task-step-1task-step-2", "重启后任务日志应恢复")
    finally:
        close_shell(reopened)

    emit("")
    emit("[DONE] 06 完整系统演示完成。")
    close_logging()


if __name__ == "__main__":
    main()

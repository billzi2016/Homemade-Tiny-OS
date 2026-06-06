"""03 调度器与 Shell 多任务演示。"""

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


def task_a():
    """测试用任务 A。"""

    emit("    [TASK-A] 第 1 步")
    yield "A-1"
    emit("    [TASK-A] 第 2 步")
    yield "A-2"


def task_b():
    """测试用任务 B。"""

    emit("    [TASK-B] 第 1 步")
    yield "B-1"
    emit("    [TASK-B] 第 2 步")
    yield "B-2"


def main() -> None:
    """验证协作式调度器与 Shell 的进程命令。"""

    setup_script_logging("03-scheduler-and-shell.log")
    banner("03 调度器与 Shell 多任务演示")
    artifact_dir = clean_artifacts("03-scheduler-and-shell")
    shell = boot_shell(artifact_dir, disk_name="scheduler.disk")

    try:
        step("创建两个协作式任务")
        pcb_a = shell.scheduler.create_process(name="task-a", task=task_a(), cwd=shell.cwd)
        pcb_b = shell.scheduler.create_process(name="task-b", task=task_b(), cwd=shell.cwd)
        info(f"创建进程 task-a，PID={pcb_a.pid}")
        info(f"创建进程 task-b，PID={pcb_b.pid}")

        step("轮转执行 4 次，观察任务交替运行")
        shell.scheduler.schedule_once()
        shell.scheduler.schedule_once()
        shell.scheduler.schedule_once()
        shell.scheduler.schedule_once()
        expect_equal(pcb_a.cpu_ticks, 2, "task-a 应被推进 2 次")
        expect_equal(pcb_b.cpu_ticks, 2, "task-b 应被推进 2 次")

        step("查看当前进程表")
        ps_output = run_shell_command(shell, "ps")
        expect_contains(ps_output, str(pcb_a.pid), "ps 输出应包含 task-a")
        expect_contains(ps_output, str(pcb_b.pid), "ps 输出应包含 task-b")

        step("继续调度直到进程退出")
        shell.scheduler.schedule_once()
        shell.scheduler.schedule_once()
        expect_equal(pcb_a.status, "ZOMBIE", "task-a 应在执行完成后进入 ZOMBIE")
        expect_equal(pcb_b.status, "ZOMBIE", "task-b 应在执行完成后进入 ZOMBIE")

        step("演示 kill 命令")
        killed = shell.scheduler.create_process(name="task-kill", task=task_a(), cwd=shell.cwd)
        run_shell_command(shell, f"kill {killed.pid}")
        expect_equal(killed.status, "ZOMBIE", "kill 后进程应进入 ZOMBIE")
    finally:
        close_shell(shell)

    emit("")
    emit("[DONE] 03 调度器与 Shell 多任务演示完成。")
    close_logging()


if __name__ == "__main__":
    main()

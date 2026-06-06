"""Phase 4 调度器测试。"""

from __future__ import annotations

import unittest

from tinyos.kernel import KernelScheduler
from tinyos.observability import KernelStats


def _task(log: list[str], name: str):
    """测试用协作任务。"""

    log.append(f"{name}-1")
    yield
    log.append(f"{name}-2")
    yield


class SchedulerTests(unittest.TestCase):
    """验证 PCB 状态流转与轮转调度。"""

    def test_round_robin_scheduler_interleaves_tasks(self) -> None:
        """两个任务应按轮转顺序交替推进。"""

        log: list[str] = []
        scheduler = KernelScheduler()
        scheduler.create_process(name="task-a", task=_task(log, "a"))
        scheduler.create_process(name="task-b", task=_task(log, "b"))

        scheduler.schedule_once()
        scheduler.schedule_once()
        scheduler.schedule_once()
        scheduler.schedule_once()

        self.assertEqual(log, ["a-1", "b-1", "a-2", "b-2"])

    def test_process_eventually_becomes_zombie_after_exit(self) -> None:
        """生成器结束后应进入 ZOMBIE。"""

        log: list[str] = []
        scheduler = KernelScheduler()
        pcb = scheduler.create_process(name="task-a", task=_task(log, "a"))

        scheduler.schedule_once()
        scheduler.schedule_once()
        scheduler.schedule_once()

        self.assertEqual(pcb.status, "ZOMBIE")

    def test_kill_marks_process_as_zombie(self) -> None:
        """kill 应立即把进程置为 ZOMBIE。"""

        scheduler = KernelScheduler()
        pcb = scheduler.create_process(name="task-a", task=_task([], "a"))
        scheduler.kill_process(pcb.pid)

        self.assertEqual(pcb.status, "ZOMBIE")


"""Phase 4 的协作式调度器实现。"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from types import GeneratorType

from tinyos.config import TinyOSConfig
from tinyos.kernel.process import ProcessControlBlock
from tinyos.observability.stats import KernelStats


@dataclass(slots=True)
class KernelScheduler:
    """Round-Robin 调度器。

    调度规则很简单：
    - 就绪队列按 FIFO 轮转
    - 每次只推进一个生成器步长
    - 正常 `yield` 后回到 `READY`
    - `StopIteration` 进入 `ZOMBIE`
    """

    config: TinyOSConfig = field(default_factory=TinyOSConfig)
    stats: KernelStats = field(default_factory=KernelStats)
    ready_queue: list[int] = field(default_factory=list)
    processes: dict[int, ProcessControlBlock] = field(default_factory=dict)
    current_pid: int | None = None
    _next_pid: int = field(default=100, repr=False)

    def create_process(
        self,
        *,
        name: str,
        task: GeneratorType,
        ppid: int = 0,
        cwd: str = "/",
        uid: int = 0,
        time_slice: int = 1,
    ) -> ProcessControlBlock:
        """创建进程并加入就绪队列。"""

        pcb = ProcessControlBlock(
            pid=self._next_pid,
            name=name,
            task=task,
            ppid=ppid,
            cwd=cwd,
            uid=uid,
            time_slice=time_slice,
        )
        self._next_pid += 1
        self.processes[pcb.pid] = pcb
        self.ready_queue.append(pcb.pid)
        self.stats.log(f"[SCHED] created pid={pcb.pid} name={pcb.name}")
        return pcb

    def schedule_once(self) -> ProcessControlBlock | None:
        """执行一次最小调度步长。"""

        if not self.ready_queue:
            return None

        pid = self.ready_queue.pop(0)
        pcb = self.processes[pid]
        self.current_pid = pid
        pcb.status = "RUNNING"
        self.stats.total_ticks += 1
        self.stats.scheduler_switches += 1
        self.stats.log(f"[SCHED] switch -> pid={pid}")

        try:
            pcb.last_result = next(pcb.task)
            pcb.cpu_ticks += 1
            if pcb.status != "BLOCKED":
                pcb.status = "READY"
                self.ready_queue.append(pid)
        except StopIteration:
            pcb.status = "ZOMBIE"
            self.stats.log(f"[SCHED] exit pid={pid}")

        return pcb

    def kill_process(self, pid: int) -> None:
        """把指定进程标记为 ZOMBIE 并移出就绪队列。"""

        if pid not in self.processes:
            raise ValueError(f"unknown pid: {pid}")

        pcb = self.processes[pid]
        pcb.status = "ZOMBIE"
        self.ready_queue = [queued_pid for queued_pid in self.ready_queue if queued_pid != pid]
        self.stats.log(f"[SCHED] kill pid={pid}")

    def list_processes(self) -> list[ProcessControlBlock]:
        """按 PID 排序返回当前进程列表。"""

        return [self.processes[pid] for pid in sorted(self.processes.keys())]

    def get_current_process(self) -> ProcessControlBlock | None:
        """返回当前运行进程。"""

        if self.current_pid is None:
            return None
        return self.processes.get(self.current_pid)

    def queue_snapshot(self) -> list[int]:
        """返回当前就绪队列快照。"""

        return list(self.ready_queue)

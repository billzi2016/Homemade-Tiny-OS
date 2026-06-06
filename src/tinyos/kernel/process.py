"""Phase 4 进程模型定义。"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import GeneratorType


@dataclass(slots=True)
class ProcessControlBlock:
    """进程控制块。

    当前实现采用协作式调度，因此 `task` 是一个生成器对象。
    调度器每次只推进它一个 `next()` 步长。
    """

    pid: int
    name: str
    task: GeneratorType
    ppid: int = 0
    status: str = "READY"
    cwd: str = "/"
    uid: int = 0
    time_slice: int = 1
    cpu_ticks: int = 0
    last_result: object | None = field(default=None, repr=False)

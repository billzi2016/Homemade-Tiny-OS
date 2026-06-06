"""Phase 1 的调度器骨架。

当前阶段只建立调度器对象和就绪队列容器，
真正的进程状态切换和轮转逻辑留到 Phase 4。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tinyos.config import TinyOSConfig


@dataclass(slots=True)
class KernelScheduler:
    """内核调度器骨架对象。

    先通过 `ready_queue` 固定一个最小可验证状态，
    这样测试可以确认后续调度逻辑的宿主对象已经存在。
    """

    config: TinyOSConfig = field(default_factory=TinyOSConfig)
    ready_queue: list[object] = field(default_factory=list)

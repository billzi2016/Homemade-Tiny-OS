"""Phase 1 的系统指标骨架。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class KernelStats:
    """内核指标骨架对象。

    这些计数器现在还不会被真正驱动，
    但先把字段固定下来，方便后续调度、内存和日志模块接入。
    """

    total_ticks: int = 0
    page_faults: int = 0
    scheduler_switches: int = 0

"""Phase 4 的系统指标与内核日志。"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass(slots=True)
class KernelStats:
    """内核指标对象。

    除了基础计数器外，这里维护一个固定容量的日志缓冲区，
    作为 `dmesg` 的数据来源。
    """

    total_ticks: int = 0
    page_faults: int = 0
    scheduler_switches: int = 0
    tree_splits: int = 0
    max_log_entries: int = 100
    _messages: deque[str] = field(default_factory=deque, repr=False)

    def log(self, message: str) -> None:
        """追加一条内核日志。

        超过上限时，自动丢弃最旧的消息。
        """

        if len(self._messages) >= self.max_log_entries:
            self._messages.popleft()
        self._messages.append(message)

    def dmesg_lines(self) -> list[str]:
        """返回当前日志缓冲区内容。"""

        return list(self._messages)

"""Phase 4 系统观测测试。"""

import unittest

from tinyos.observability import KernelStats


class KernelStatsTests(unittest.TestCase):
    """验证日志缓冲区与覆盖行为。"""

    def test_dmesg_keeps_fixed_capacity(self) -> None:
        """超过上限时应丢弃最旧消息。"""

        stats = KernelStats(max_log_entries=3)
        stats.log("one")
        stats.log("two")
        stats.log("three")
        stats.log("four")

        self.assertEqual(stats.dmesg_lines(), ["two", "three", "four"])


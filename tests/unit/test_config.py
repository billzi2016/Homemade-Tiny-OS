"""Phase 1 配置对象测试。"""

import unittest

from tinyos.config import TinyOSConfig


class TinyOSConfigTests(unittest.TestCase):
    """验证配置默认值和基础约束是否固定。"""

    def test_default_values_match_phase_one_contract(self) -> None:
        """默认配置必须与 PRD 的 Phase 1 约定一致。"""
        config = TinyOSConfig()

        self.assertEqual(config.disk_initial_size_bytes, 4 * 1024 * 1024)
        self.assertEqual(config.disk_growth_step_bytes, 1 * 1024 * 1024)
        self.assertEqual(config.disk_max_size_bytes, 64 * 1024 * 1024)
        self.assertEqual(config.block_size_bytes, 4 * 1024)
        self.assertEqual(config.page_size_bytes, 4 * 1024)
        self.assertFalse(config.debug_enabled)

    def test_invalid_configuration_is_rejected(self) -> None:
        """明显非法的配置必须在对象创建时被拦截。"""
        with self.assertRaises(ValueError):
            TinyOSConfig(disk_initial_size_bytes=0)

        with self.assertRaises(ValueError):
            TinyOSConfig(disk_initial_size_bytes=8, disk_max_size_bytes=4)

        with self.assertRaises(ValueError):
            TinyOSConfig(disk_growth_step_bytes=3, block_size_bytes=4)

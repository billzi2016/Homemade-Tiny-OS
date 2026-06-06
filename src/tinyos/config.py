"""项目级配置定义。

Phase 1 的目标不是把系统功能做完，而是先把“全局默认参数”和
“参数约束”固定下来，避免后续每个模块各自定义一套配置。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class TinyOSConfig:
    """Tiny OS 运行期配置对象。

    这里保存的是所有核心子系统都会共享的基础参数：
    - 虚拟磁盘初始大小、扩容步长、最大上限
    - 块大小
    - 页大小
    - 调试开关

    当前阶段把它设计成不可变对象，目的是减少后续模块在运行中
    随意改配置导致的状态漂移。
    """

    disk_initial_size_bytes: int = 4 * 1024 * 1024
    disk_growth_step_bytes: int = 1 * 1024 * 1024
    disk_max_size_bytes: int = 64 * 1024 * 1024
    block_size_bytes: int = 4 * 1024
    page_size_bytes: int = 4 * 1024
    debug_enabled: bool = False

    def __post_init__(self) -> None:
        """在对象创建后立即校验配置合法性。

        这里的校验意图不是追求“配置体系完美”，而是先挡住
        Phase 1 最容易出问题的几类非法输入：
        - 容量或大小为 0 / 负数
        - 初始容量大于最大容量
        - 与块大小不对齐，导致后续块设备实现边界不清
        """
        positive_values = {
            "disk_initial_size_bytes": self.disk_initial_size_bytes,
            "disk_growth_step_bytes": self.disk_growth_step_bytes,
            "disk_max_size_bytes": self.disk_max_size_bytes,
            "block_size_bytes": self.block_size_bytes,
            "page_size_bytes": self.page_size_bytes,
        }
        for field_name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{field_name} must be greater than zero")

        if self.disk_initial_size_bytes > self.disk_max_size_bytes:
            raise ValueError("disk_initial_size_bytes must not exceed disk_max_size_bytes")

        # 这里强制容量参数和块大小对齐，后续 Phase 2 做块分配时
        # 就不需要额外处理“半块容量”这种无意义状态。
        if self.disk_initial_size_bytes % self.block_size_bytes != 0:
            raise ValueError("disk_initial_size_bytes must be a multiple of block_size_bytes")

        if self.disk_growth_step_bytes % self.block_size_bytes != 0:
            raise ValueError("disk_growth_step_bytes must be a multiple of block_size_bytes")

        if self.disk_max_size_bytes % self.block_size_bytes != 0:
            raise ValueError("disk_max_size_bytes must be a multiple of block_size_bytes")

"""Phase 1 的 Shell 骨架。

当前只固定命令行对象和默认提示符。
真正的 REPL 循环、命令解析和分发留到 Phase 4。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tinyos.config import TinyOSConfig


@dataclass(slots=True)
class Shell:
    """Shell 骨架对象。

    通过保留 `prompt` 字段，先把后续交互层最基础的外观边界定下来。
    """

    config: TinyOSConfig = field(default_factory=TinyOSConfig)
    prompt: str = "tinyos$ "

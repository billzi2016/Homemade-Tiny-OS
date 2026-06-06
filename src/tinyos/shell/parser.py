"""Shell 命令解析器。"""

from __future__ import annotations

import shlex
from dataclasses import dataclass


@dataclass(slots=True)
class ParsedCommand:
    """解析后的命令表示。"""

    name: str
    args: list[str]
    output_redirect: str | None = None


def parse_command(command_line: str) -> ParsedCommand:
    """把命令行文本解析成结构化命令。

    当前支持：
    - 空格分隔参数
    - 引号
    - 一个输出重定向 `>`
    """

    parts = shlex.split(command_line)
    if not parts:
        raise ValueError("command line is empty")

    if ">" in parts:
        redirect_index = parts.index(">")
        if redirect_index == len(parts) - 1:
            raise ValueError("redirect target is missing")
        if redirect_index == 0:
            raise ValueError("command is missing before redirect")
        name = parts[0]
        args = parts[1:redirect_index]
        return ParsedCommand(name=name, args=args, output_redirect=parts[redirect_index + 1])

    return ParsedCommand(name=parts[0], args=parts[1:])

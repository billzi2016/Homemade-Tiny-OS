"""Phase 4 Shell 解析测试。"""

import unittest

from tinyos.shell import parse_command


class ShellParserTests(unittest.TestCase):
    """验证命令解析器。"""

    def test_parser_supports_quotes(self) -> None:
        """引号包裹的文本应保留为空间参数。"""

        parsed = parse_command('echo "hello tiny os"')
        self.assertEqual(parsed.name, "echo")
        self.assertEqual(parsed.args, ["hello tiny os"])

    def test_parser_supports_output_redirect(self) -> None:
        """应识别基础重定向语法。"""

        parsed = parse_command('echo "abc" > note.txt')
        self.assertEqual(parsed.name, "echo")
        self.assertEqual(parsed.args, ["abc"])
        self.assertEqual(parsed.output_redirect, "note.txt")


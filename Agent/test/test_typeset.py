"""Typesetting tool: the agent renders its own paper."""

import tempfile
import unittest
from pathlib import Path

from ht_moonshine.typeset import choose_python, typeset


class TestTypeset(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _draft(self) -> Path:
        path = self.dir / "paper.md"
        path.write_text(
            "# 一个测试标题\n\n"
            "作者: Tester\n"
            "单位: Unit\n"
            "日期: 2026-10-23\n"
            "关键词: alpha; beta\n"
            "MSC 2020: 62D05\n\n"
            "## 摘要\n\n这是一段摘要，包含公式 $N = 2^m$ 与下标 $\\pi_i$。\n\n"
            "## Abstract\n\nAn English abstract paragraph.\n\n"
            "## 1 问题\n\n正文一段，引用 claim_id 与 ht_verify_bundle 不应被改写。\n\n"
            "| 检查项 | 结果 |\n| --- | --- |\n| A | 1 |\n| B | 2 |\n\n"
            "## 参考文献\n\n- [1] Someone. A paper. 2026.\n",
            encoding="utf-8",
        )
        return path

    def test_renders_a_pdf_with_pages(self):
        source = self._draft()
        out = self.dir / "paper.pdf"
        result = typeset(source, out)
        self.assertTrue(result.get("ok"), msg=result.get("error") or result.get("stderr_tail"))
        self.assertGreaterEqual(int(result.get("pages") or 0), 1)
        self.assertTrue(out.exists())
        self.assertGreater(out.stat().st_size, 10_000)

    def test_missing_source_returns_error_not_exception(self):
        result = typeset(self.dir / "nope.md", self.dir / "nope.pdf")
        self.assertFalse(result.get("ok"))
        self.assertIn("not found", str(result.get("error")))

    def test_interpreter_can_be_chosen(self):
        choice = choose_python()
        self.assertTrue(Path(choice["python"]).exists())


if __name__ == "__main__":
    unittest.main()

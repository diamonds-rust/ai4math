"""Streaming output: deltas must become paragraphs, not one word per line."""

import io
import unittest
from contextlib import redirect_stdout

import run_ht_agent


class TestStreamPrinter(unittest.TestCase):
    def _run(self, chunks):
        printer = run_ht_agent.StreamPrinter("[text]", width=80)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            for chunk in chunks:
                printer.feed(chunk)
            printer.close()
        return buffer.getvalue()

    def test_sentence_is_flushed_once(self):
        out = self._run(["这是", "一句", "完整的", "话。"])
        self.assertEqual(out.strip(), "[text] 这是一句完整的话。")
        self.assertEqual(len(out.strip().splitlines()), 1)

    def test_newline_flushes_a_paragraph(self):
        out = self._run(["第一段。\n", "第二段。"])
        lines = [line for line in out.splitlines() if line.strip()]
        self.assertEqual(lines[0].strip(), "[text] 第一段。")
        self.assertIn("第二段。", " ".join(lines))

    def test_long_run_without_punctuation_still_flushes(self):
        printer = run_ht_agent.StreamPrinter("[text]", width=80, max_chars=60)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            printer.feed("x" * 120)
            printer.close()
        self.assertGreaterEqual(len(buffer.getvalue()), 2)

    def test_reasoning_disabled_prints_nothing(self):
        printer = run_ht_agent.StreamPrinter("[reasoning]", enabled=False)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            printer.feed("hidden reasoning。")
            printer.close()
        self.assertEqual(buffer.getvalue(), "")


if __name__ == "__main__":
    unittest.main()

"""LaTeX compilation tool."""

import os
import tempfile
import unittest
from pathlib import Path

from ht_moonshine.latex import compile_tex, find_engine

HAS_ENGINE = find_engine() is not None
HAS_SIMSUN = Path(r"C:\Windows\Fonts\simsun.ttc").exists()


class TestLatex(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_missing_source_returns_error(self):
        result = compile_tex(self.dir / "nope.tex")
        self.assertFalse(result.get("ok"))
        self.assertIn("not found", str(result.get("error")))

    @unittest.skipUnless(HAS_ENGINE, "no LaTeX engine on PATH")
    def test_compiles_plain_document(self):
        tex = self.dir / "plain.tex"
        tex.write_text(
            "\\documentclass{article}\n"
            "\\usepackage{amsmath}\n"
            "\\begin{document}\n"
            "Hello $x^2=1$.\n"
            "\\end{document}\n",
            encoding="utf-8",
        )
        out = self.dir / "plain.pdf"
        result = compile_tex(tex, out, runs=1)
        self.assertTrue(result.get("ok"), msg=str(result.get("error"))[:400])
        self.assertGreaterEqual(int(result.get("pages") or 0), 1)
        self.assertTrue(out.exists())

    @unittest.skipUnless(HAS_ENGINE and HAS_SIMSUN, "needs xelatex and SimSun")
    def test_compiles_chinese_with_xecjk(self):
        tex = self.dir / "zh.tex"
        tex.write_text(
            "\\documentclass{article}\n"
            "\\usepackage{xeCJK}\n"
            "\\setCJKmainfont[Path=C:/Windows/Fonts/,FontIndex=0]{simsun.ttc}\n"
            "\\begin{document}\n"
            "你好，世界。$N=2^m$。\n"
            "\\end{document}\n",
            encoding="utf-8",
        )
        result = compile_tex(tex, self.dir / "zh.pdf", runs=1)
        self.assertTrue(result.get("ok"), msg=str(result.get("error"))[:400])

    @unittest.skipUnless(HAS_ENGINE, "no LaTeX engine on PATH")
    def test_broken_source_reports_a_log_error(self):
        tex = self.dir / "broken.tex"
        tex.write_text(
            "\\documentclass{article}\n\\begin{document}\n\\undefinedcommand\n\\end{document}\n",
            encoding="utf-8",
        )
        result = compile_tex(tex, runs=1)
        self.assertFalse(result.get("ok"))
        self.assertTrue(str(result.get("error") or "").strip())


if __name__ == "__main__":
    unittest.main()

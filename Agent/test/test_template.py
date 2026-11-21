"""Paper templates: seeding from 期中报告-style and journal-style sources."""

import tempfile
import unittest
from pathlib import Path

from ht_moonshine.tools_impl import ht_template


class TestTemplate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_midterm_template_is_copied(self):
        out = self.dir / "paper.tex"
        result = ht_template(template="midterm", out=str(out), force=True)
        self.assertEqual(result["status"], "ok")
        self.assertTrue(out.exists())
        text = out.read_text(encoding="utf-8")
        self.assertIn("ctex", text)
        self.assertIn("Times New Roman", text)
        self.assertIn("top=2.5cm", text)
        self.assertIn("newtheorem{Thm}", text)
        self.assertNotIn("数据思维与价值", text)  # no cover page

    def test_journal_template_is_available(self):
        out = self.dir / "journal.tex"
        result = ht_template(template="journal", out=str(out), force=True)
        self.assertEqual(result["status"], "ok")
        self.assertIn("xeCJK", out.read_text(encoding="utf-8"))

    def test_existing_draft_is_not_overwritten(self):
        out = self.dir / "paper.tex"
        out.write_text("% my draft\n", encoding="utf-8")
        result = ht_template(template="midterm", out=str(out))
        self.assertEqual(result["status"], "exists")
        self.assertEqual(out.read_text(encoding="utf-8"), "% my draft\n")

    def test_unknown_template_raises(self):
        with self.assertRaises(ValueError):
            ht_template(template="nonexistent", out=str(self.dir / "x.tex"))


if __name__ == "__main__":
    unittest.main()

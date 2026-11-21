"""The launcher: doctor must resolve the real agent, skills, tools and project."""

import argparse
import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import run_ht_agent

REPO = Path(__file__).resolve().parent.parent
ROOT = REPO / "runtime" / "moonshine-src"
HOME = ROOT / "home"


class TestReasoningPrinter(unittest.TestCase):
    def test_disabled_prints_nothing(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            printer = run_ht_agent.ReasoningPrinter(False)
            for word in ("alpha ", "beta ", "gamma"):
                printer.feed(word)
            printer.close()
        self.assertEqual(buffer.getvalue(), "")

    def test_enabled_prints_one_wrapped_paragraph(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            printer = run_ht_agent.ReasoningPrinter(True, width=60, flush_at=200)
            for index in range(80):
                printer.feed("token%d " % index)
            printer.close()
        output = buffer.getvalue()
        self.assertEqual(output.count("[reasoning]"), 1)
        self.assertEqual(output.count("[/reasoning]"), 1)
        body = output.split("[reasoning]")[1].split("[/reasoning]")[0]
        lines = [line for line in body.strip().splitlines() if line.strip()]
        self.assertGreater(len(lines), 1)
        self.assertLessEqual(max(len(line) for line in lines), 60)
        self.assertIn("token0", body)

    def test_quiet_overrides_show_reasoning(self):
        args = run_ht_agent.build_parser().parse_args(["run", "--quiet", "--show-reasoning"])
        self.assertFalse(run_ht_agent.reasoning_enabled(args))
        args2 = run_ht_agent.build_parser().parse_args(["run", "--show-reasoning"])
        self.assertTrue(run_ht_agent.reasoning_enabled(args2))
        args3 = run_ht_agent.build_parser().parse_args(["run"])
        self.assertFalse(run_ht_agent.reasoning_enabled(args3))


class TestDoctor(unittest.TestCase):
    def setUp(self):
        if not (ROOT / "moonshine" / "app.py").exists():
            self.skipTest("run integration/install_into_moonshine.py first")

    def _doctor(self):
        args = argparse.Namespace(
            root=str(ROOT),
            home=str(HOME),
            project=run_ht_agent.DEFAULT_PROJECT,
            agent=run_ht_agent.DEFAULT_AGENT,
            json=True,
        )
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = run_ht_agent.cmd_doctor(args)
        return code, json.loads(buffer.getvalue())

    def test_doctor_resolves_agent_skills_tools_project(self):
        code, report = self._doctor()
        self.assertTrue(report["agent"]["found"])
        self.assertGreaterEqual(len(report["skills"]["ht"]), 3)
        self.assertGreaterEqual(len(report["tools"]["ht"]), 12)
        self.assertTrue(report["checks"]["agent_profile_found"])
        self.assertTrue(report["checks"]["ht_skills_present"])
        self.assertTrue(report["checks"]["ht_tools_present"])
        self.assertTrue(report["checks"]["project_seeded"])
        # no provider configured on this machine, so doctor reports not-ready but still exits 1
        self.assertFalse(report["checks"]["provider_configured"])
        self.assertEqual(code, 1)

    def test_problem_brief_has_the_essentials(self):
        workspace = HOME / "projects" / run_ht_agent.DEFAULT_PROJECT / "workspace"
        brief = (workspace / "problem.md").read_text(encoding="utf-8")
        for needle in ("Conjecture under test", "5-tuple", "Method portfolio", "Failure record schema", "ht_verify_bundle"):
            self.assertIn(needle, brief)
        # the agent can only read inside the project, so the paper templates must be seeded there
        self.assertTrue((workspace / "template.tex").exists())
        self.assertTrue((workspace / "template.md").exists())

    def test_agent_prompt_carries_method_freedom(self):
        text = (REPO / "assets" / "agents" / "builtin" / "ht-researcher" / "AGENT.md").read_text(encoding="utf-8")
        self.assertIn("Method freedom", text)
        self.assertIn("run_python_script", text)
        self.assertIn("ht-method-portfolio", text)


if __name__ == "__main__":
    unittest.main()

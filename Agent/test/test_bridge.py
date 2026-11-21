"""Moonshine integration: registry subclass, dispatch, tool definitions."""

import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

from ht_moonshine.tools_impl import HT_HANDLERS  # noqa: E402


class TestRegistryBridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from ht_moonshine.moonshine_bridge import build_registry, ht_tool_names

        cls.registry = build_registry()
        cls.names = ht_tool_names(cls.registry)

    def test_all_ht_tools_registered(self):
        self.assertEqual(len(self.names), len(HT_HANDLERS))
        for name in (
            "ht_build_design",
            "ht_inclusion_probs",
            "ht_order3_witness",
            "ht_solve_population",
            "ht_check_srswor_clt",
            "ht_sample_total_law",
            "ht_hajek_decay",
            "ht_verify_bundle",
            "ht_design_search",
            "ht_weight_search",
            "ht_permutation_search",
            "ht_simulate_design",
        ):
            self.assertIn(name, self.names)

    def test_stock_tools_still_present(self):
        schemas = {item["name"] for item in self.registry.schemas(mode="research")}
        for name in ("verify_overall", "query_memory", "run_python_script", "assess_problem_quality"):
            self.assertIn(name, schemas)

    def test_dispatch_build_design(self):
        result = self.registry.dispatch(
            "ht_build_design",
            {"family": "hadamard3", "m": 4, "t": 3},
            {"mode": "research", "exposure": {"tools_include": [], "tools_exclude": []}},
        )
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["is_design"])
        self.assertEqual(result["design"]["v"], 16)

    def test_dispatch_verify_bundle_pass_and_fail(self):
        runtime = {"mode": "research", "exposure": {"tools_include": [], "tools_exclude": []}}
        ok = self.registry.dispatch(
            "ht_verify_bundle",
            {
                "bundle": {
                    "claim": "realizability_obstruction",
                    "r": 3,
                    "design": {"family": "hadamard3", "params": {"m": 4}},
                    "population": {"denominator": 1000},
                    "options": {},
                }
            },
            runtime,
        )
        self.assertEqual(ok["overall"], "PASS")
        bad = self.registry.dispatch(
            "ht_verify_bundle",
            {
                "bundle": {
                    "claim": "order_agreement",
                    "r": 3,
                    "design": {"family": "projective_plane", "params": {"q": 7}},
                    "population": {"denominator": 1000},
                    "options": {},
                }
            },
            runtime,
        )
        self.assertEqual(bad["overall"], "FAIL")

    def test_schema_validation_rejects_bad_enum(self):
        from moonshine.json_schema import JsonSchemaValidationError

        with self.assertRaises(JsonSchemaValidationError):
            self.registry.dispatch("ht_build_design", {"family": "nope"}, {"mode": "research"})

    def test_tool_definitions_are_valid_json(self):
        from ht_moonshine.moonshine_bridge import DEFINITIONS_DIR

        files = sorted(DEFINITIONS_DIR.glob("*.md"))
        self.assertEqual(len(files), len(HT_HANDLERS))
        for path in files:
            text = path.read_text(encoding="utf-8")
            start = text.index("<!--") + 4
            end = text.index("-->")
            metadata = json.loads(text[start:end])
            self.assertTrue(metadata["name"].startswith("ht_"))
            self.assertIn("Usage Hint", text)
            self.assertEqual(metadata["name"], metadata["handler"])

    def test_skills_and_agent_ship_with_frontmatter(self):
        skill = REPO / "assets" / "skills" / "builtin" / "ht-counterexample-protocol" / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---"))
        self.assertIn("allowed-tools:", text)
        agent = REPO / "assets" / "agents" / "builtin" / "ht-researcher" / "AGENT.md"
        agent_text = agent.read_text(encoding="utf-8")
        self.assertIn('"slug": "ht-researcher"', agent_text)


class TestPatchedTree(unittest.TestCase):
    """Exercises the patched copy produced by the installer, if it exists."""

    def setUp(self):
        self.root = REPO / "runtime" / "moonshine-src"
        if not (self.root / "moonshine" / "tools" / "registry.py").exists():
            self.skipTest("run integration/install_into_moonshine.py first")

    def test_patched_tree_registers_and_dispatches(self):
        from ht_moonshine.moonshine_bridge import verify_patched_tree

        report = verify_patched_tree(self.root, self.root / "home")
        self.assertEqual(len(report["ht_tools"]), len(HT_HANDLERS))
        self.assertTrue(report["dispatch_ok"])
        self.assertGreaterEqual(report["tool_count"], 32)

    def test_patches_are_idempotent(self):
        from ht_moonshine.moonshine_bridge import patch_source

        first = patch_source(self.root)
        second = patch_source(self.root)
        self.assertTrue(all(item["status"] in ("applied", "already_patched") for item in first["patches"]))
        self.assertTrue(all(item["status"] == "already_patched" for item in second["patches"]))

    def test_patched_workflow_knows_the_new_activities(self):
        import sys

        if str(self.root) not in sys.path:
            sys.path.insert(0, str(self.root))
        for name in list(sys.modules):
            if name == "moonshine" or name.startswith("moonshine."):
                del sys.modules[name]
        from moonshine.agent_runtime import research_workflow as workflow

        for activity in ("design_synthesis", "population_backsolve", "limit_law_check"):
            self.assertIn(activity, workflow.PROBLEM_SOLVING_ACTIVITIES)
            self.assertIn(activity, workflow.ACTIVITY_SPECS)
            self.assertIn(activity, workflow.RESEARCH_ACTIVITY_ENUM)


if __name__ == "__main__":
    unittest.main()

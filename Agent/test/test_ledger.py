"""The statement ledger backing the paper draft."""

import json
import tempfile
import unittest
from pathlib import Path

from ht_moonshine.ledger import StatementLedger


class TestLedger(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "statements.jsonl"
        self.ledger = StatementLedger(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_and_list(self):
        self.ledger.add(
            "The affine-hyperplane design is strength 3.",
            kind="proposition",
            status="gated",
            evidence={"claim_id": "abc123", "tool": "ht_population_first"},
        )
        result = self.ledger.list()
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["statements"][0]["status"], "gated")

    def test_check_ok_when_gated_has_evidence_and_cited_has_reference(self):
        self.ledger.add("strength 3", status="gated", evidence={"claim_id": "c1"})
        self.ledger.add("bent functions exist", status="cited", evidence={"reference": "Rothaus 1976"})
        report = self.ledger.check()
        self.assertTrue(report["ok"])
        self.assertEqual(report["by_status"]["gated"], 1)
        self.assertEqual(report["by_status"]["cited"], 1)

    def test_check_flags_gated_without_evidence(self):
        self.ledger.add("claim without evidence", status="gated")
        report = self.ledger.check()
        self.assertFalse(report["ok"])
        self.assertTrue(report["gated_without_evidence"])

    def test_check_flags_cited_without_reference(self):
        self.ledger.add("borrowed theorem", status="cited")
        report = self.ledger.check()
        self.assertFalse(report["ok"])
        self.assertTrue(report["cited_without_reference"])

    def test_unproved_are_reported_but_do_not_fail(self):
        self.ledger.add("general m statement", status="unproved", notes="needs the counting proof")
        report = self.ledger.check()
        self.assertTrue(report["ok"])
        self.assertEqual(report["unproved"], ["stmt-general-m-statement-001"])

    def test_duplicate_identifier_rejected(self):
        self.ledger.add("one", identifier="stmt-1")
        with self.assertRaises(ValueError):
            self.ledger.add("two", identifier="stmt-1")

    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError):
            self.ledger.add("x", status="true")

    def test_render_table(self):
        self.ledger.add("statement one", kind="lemma", status="derived", depends_on=["stmt-0"])
        text = self.ledger.render()
        self.assertIn("附录 A 陈述账本", text)
        self.assertIn("| stmt-statement-one-001 |", text)

    def test_jsonl_is_append_only(self):
        self.ledger.add("first")
        self.ledger.add("second")
        lines = self.path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[1])["statement"], "second")


    def test_update_status_and_evidence(self):
        self.ledger.add("P1", identifier="P1", status="unproved")
        updated = self.ledger.update("P1", status="derived", evidence={"claim_id": "c9"})
        self.assertEqual(updated["status"], "derived")
        self.assertEqual(updated["evidence"]["claim_id"], "c9")
        rows = self.ledger.list()["statements"]
        self.assertEqual(rows[0]["status"], "derived")

    def test_update_unknown_id_raises(self):
        with self.assertRaises(KeyError):
            self.ledger.update("nope", status="derived")

    def test_update_rejects_bad_status(self):
        self.ledger.add("P1", identifier="P1")
        with self.assertRaises(ValueError):
            self.ledger.update("P1", status="true")


class TestLedgerTool(unittest.TestCase):
    def test_dispatch_through_registry(self):
        from ht_moonshine.moonshine_bridge import build_registry

        registry = build_registry()
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "statements.jsonl")
            runtime = {"mode": "research", "exposure": {"tools_include": [], "tools_exclude": []}}
            added = registry.dispatch(
                "ht_statement_ledger",
                {"action": "add", "path": path, "statement": "gate check", "status": "gated",
                 "evidence": {"claim_id": "c1"}},
                runtime,
            )
            self.assertEqual(added["status"], "ok")
            checked = registry.dispatch("ht_statement_ledger", {"action": "check", "path": path}, runtime)
            self.assertTrue(checked["ok"])


if __name__ == "__main__":
    unittest.main()

"""End-to-end: the shipped self-test must pass as a whole."""

import unittest

from ht_moonshine.selftest import run_selftest


class TestSelftest(unittest.TestCase):
    def test_all_checks_pass(self):
        report = run_selftest()
        failed = [item for item in report["checks"] if not item["ok"]]
        self.assertEqual(failed, [], "failing checks: %r" % (failed,))
        self.assertEqual(report["overall"], "PASS")
        self.assertGreaterEqual(report["total"], 15)


if __name__ == "__main__":
    unittest.main()

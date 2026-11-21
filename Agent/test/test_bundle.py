"""The deterministic gate: bundle verification, including negative cases."""

import unittest

from ht_moonshine.bundle import (
    bundle_hash,
    r2_reference_bundle,
    r3_obstruction_bundle,
    verify_bundle,
)


class TestR2Counterexample(unittest.TestCase):
    def test_passes_every_check(self):
        verdict = verify_bundle(r2_reference_bundle(13))
        self.assertEqual(verdict["overall"], "PASS")
        self.assertEqual(verdict["failed_checks"], [])
        names = [item["name"] for item in verdict["checks"]]
        self.assertEqual(
            names,
            [
                "design_is_strength_r",
                "pis_match_srswor_through_r",
                "block_totals_realizable",
                "srswor_clt_evidence",
                "same_first_two_moments",
                "limit_law_differs",
            ],
        )

    def test_moment_identity_detail(self):
        verdict = verify_bundle(r2_reference_bundle(13))
        moment_check = [item for item in verdict["checks"] if item["name"] == "same_first_two_moments"][0]
        self.assertTrue(moment_check["detail"]["variance_identity_equal"])
        self.assertEqual(
            moment_check["detail"]["variance_closed_form"],
            moment_check["detail"]["variance_block_law"],
        )

    def test_claim_id_is_stable(self):
        self.assertEqual(bundle_hash(r2_reference_bundle(13)), bundle_hash(r2_reference_bundle(13)))
        self.assertNotEqual(bundle_hash(r2_reference_bundle(13)), bundle_hash(r2_reference_bundle(7)))


class TestR3Obstruction(unittest.TestCase):
    def test_obstruction_is_confirmed(self):
        verdict = verify_bundle(r3_obstruction_bundle(4))
        self.assertEqual(verdict["overall"], "PASS")
        detail = [item for item in verdict["checks"] if item["name"] == "block_totals_realizable"][0]
        self.assertFalse(detail["detail"]["solvable"])
        self.assertLess(detail["detail"]["rank"], detail["detail"]["augmented_rank"])

    def test_ag_planes_obstruction_too(self):
        bundle = {
            "id": "r3_ag4",
            "claim": "realizability_obstruction",
            "r": 3,
            "design": {"family": "ag_planes", "params": {"m": 4}},
            "population": {"denominator": 1000},
            "options": {},
        }
        verdict = verify_bundle(bundle)
        self.assertEqual(verdict["overall"], "PASS")


class TestGateRejectsFalseClaims(unittest.TestCase):
    def test_r3_counterexample_claim_fails(self):
        bundle = dict(r3_obstruction_bundle(4))
        bundle["claim"] = "counterexample"
        bundle["options"] = {"srswor_reps": 200, "seed": 1}
        verdict = verify_bundle(bundle)
        self.assertEqual(verdict["overall"], "FAIL")
        self.assertIn("block_totals_realizable", verdict["failed_checks"])

    def test_order_three_on_projective_plane_fails(self):
        bundle = {
            "id": "pg_order3",
            "claim": "order_agreement",
            "r": 3,
            "design": {"family": "projective_plane", "params": {"q": 7}},
            "population": {"denominator": 1000},
            "options": {},
        }
        verdict = verify_bundle(bundle)
        self.assertEqual(verdict["overall"], "FAIL")
        self.assertIn("design_is_strength_r", verdict["failed_checks"])
        self.assertIn("pis_match_srswor_through_r", verdict["failed_checks"])

    def test_unknown_claim_is_rejected(self):
        bundle = dict(r2_reference_bundle(7))
        bundle["claim"] = "hand_waving"
        with self.assertRaises(ValueError):
            verify_bundle(bundle)

    def test_unknown_family_is_rejected(self):
        bundle = dict(r2_reference_bundle(7))
        bundle["design"] = {"family": "chebyshev", "params": {}}
        with self.assertRaises(ValueError):
            verify_bundle(bundle)


if __name__ == "__main__":
    unittest.main()

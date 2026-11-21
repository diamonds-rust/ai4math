"""Exact inclusion probabilities and the SRSWOR comparison."""

import unittest
from fractions import Fraction

from ht_moonshine.designs import hadamard3, projective_plane
from ht_moonshine.exact import falling, srswor_inclusion_prob
from ht_moonshine.inclusion import compare_to_srswor, inclusion_probs, order3_collinear_witness


class TestExactBasics(unittest.TestCase):
    def test_falling_factorial(self):
        self.assertEqual(falling(8, 2), 56)
        self.assertEqual(falling(8, 0), 1)
        self.assertEqual(falling(5, 5), 120)

    def test_srswor_values(self):
        self.assertEqual(srswor_inclusion_prob(4, 2, 2), Fraction(1, 6))
        self.assertEqual(srswor_inclusion_prob(57, 8, 1), Fraction(8, 57))
        self.assertEqual(srswor_inclusion_prob(57, 8, 2), Fraction(1, 57))

    def test_srswor_rejects_bad_bounds(self):
        with self.assertRaises(ValueError):
            srswor_inclusion_prob(5, 8, 1)


class TestOrderTwoAgreement(unittest.TestCase):
    def test_projective_plane_matches(self):
        report = compare_to_srswor(projective_plane(7), 2)
        self.assertTrue(report["match"])
        self.assertEqual(report["orders"]["1"]["mismatch_count"], 0)
        self.assertEqual(report["orders"]["2"]["mismatch_count"], 0)
        self.assertEqual(report["orders"]["2"]["expected"], "1/57")

    def test_hadamard3_matches_through_three(self):
        report = compare_to_srswor(hadamard3(4), 3)
        self.assertTrue(report["match"])
        self.assertEqual({key: value["mismatch_count"] for key, value in report["orders"].items()}, {"1": 0, "2": 0, "3": 0})


class TestOrderThreeFailure(unittest.TestCase):
    def test_projective_plane_fails_order_three(self):
        report = compare_to_srswor(projective_plane(7), 3)
        self.assertFalse(report["match"])
        self.assertGreater(report["orders"]["3"]["mismatch_count"], 0)
        self.assertEqual(len(report["orders"]["3"]["mismatch_examples"]), 5)

    def test_collinear_witness_fractions(self):
        witness = order3_collinear_witness(7, True)
        self.assertEqual(witness["collinear_prob"], "1/57")
        self.assertEqual(witness["scattered_prob"], "0")
        self.assertEqual(witness["srswor_order3"], "2/1045")
        self.assertFalse(witness["agree"])

    def test_inclusion_probs_are_exact_fractions(self):
        probs = inclusion_probs(projective_plane(5), 2)
        for value in probs[2].values():
            self.assertIsInstance(value, Fraction)
        self.assertTrue(all(value == Fraction(1, 31) for value in probs[2].values()))


if __name__ == "__main__":
    unittest.main()

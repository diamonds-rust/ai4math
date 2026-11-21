"""Route B: affine-hyperplane design plus bent-function population."""

import unittest
from fractions import Fraction

from ht_moonshine.bundle import bundle_hash, verify_bundle
from ht_moonshine.designs import verify_strength
from ht_moonshine.hyperplane import (
    bent_population,
    check_population_first,
    d1_ht_law,
    d2_ht_law,
    hyperplane_design,
    is_bent,
    ks_to_normal,
    population_first_bundle,
    population_stats,
    sample_hyperplane_containment,
    strength_profile_by_affine_dimension,
)


class TestHyperplaneDesign(unittest.TestCase):
    def test_parameters_and_strength(self):
        design = hyperplane_design(4)
        self.assertEqual((design.v, design.b, design.block_size), (16, 30, 8))
        self.assertTrue(verify_strength(design, 3)["is_design"])
        self.assertFalse(verify_strength(design, 4)["is_design"])

    def test_rejects_odd_m(self):
        with self.assertRaises(ValueError):
            hyperplane_design(5)

    def test_lambda_three_formula(self):
        for m in (4, 6):
            design = hyperplane_design(m)
            report = verify_strength(design, 3)
            self.assertEqual(report["orders"]["3"]["lambda_values"], [design.v // 4 - 1])


class TestBentPopulation(unittest.TestCase):
    def test_walsh_magnitudes(self):
        for m in (4, 6):
            self.assertTrue(is_bent(m)["bent"])
            self.assertEqual(is_bent(m)["magnitudes"], [1 << (m // 2)])

    def test_population_is_two_valued_and_centered(self):
        stats = population_stats(4)
        self.assertEqual(stats["centered_sum"], "0")
        self.assertEqual(stats["sum_squares"], "15")
        self.assertTrue(stats["two_valued"])

    def test_population_values_are_exact(self):
        y = bent_population(4)
        self.assertIsInstance(y[0], Fraction)
        # y = f - 1/sqrt(N) with f = +-1 and sqrt(N) = 4
        self.assertEqual(sorted({str(value) for value in y}), ["-5/4", "3/4"])


class TestLaws(unittest.TestCase):
    def test_d1_is_two_point_rademacher(self):
        law = d1_ht_law(4)
        self.assertEqual(law["support"], 2)
        self.assertEqual(law["variance"], Fraction(16))
        probs = sorted(law["law"].values())
        self.assertEqual(probs, [Fraction(1, 2), Fraction(1, 2)])

    def test_d2_variance_identity(self):
        for m in (4, 6, 8):
            self.assertEqual(d2_ht_law(m)["variance"], Fraction(1 << m))

    def test_d2_ks_shrinks(self):
        distances = [ks_to_normal(d2_ht_law(m)["law"]) for m in (4, 6, 8)]
        self.assertGreater(distances[0], distances[1])
        self.assertGreater(distances[1], distances[2])
        self.assertLess(distances[2], 0.06)


class TestExactStrengthProfile(unittest.TestCase):
    def test_two_lambda_values_at_order_four(self):
        for m in (4, 6):
            profile = strength_profile_by_affine_dimension(m)
            self.assertTrue(profile["is_strength_exactly_3"])
            self.assertTrue(profile["consistent"])
            self.assertEqual(profile["lambda_4_values"], [1 << (m - 3) if False else (1 << (m - 3)) - 1,
                                                         (1 << (m - 2)) - 1])

    def test_containment_formula_matches_blocks(self):
        for m in (4, 6):
            result = sample_hyperplane_containment(m, trials=120)
            self.assertEqual(result["mismatches"], 0)
            self.assertEqual(result["checked"], 120)

    def test_m6_profile_is_consistent(self):
        profile = strength_profile_by_affine_dimension(6)
        self.assertEqual(profile["total_from_formula"], profile["total_from_blocks"])


class TestRouteBGate(unittest.TestCase):
    def test_passes_at_m4(self):
        result = check_population_first(4, 3)
        self.assertEqual(result["overall"], "PASS")
        self.assertEqual(result["failed_checks"], [])
        self.assertEqual(len(result["checks"]), 8)

    def test_fails_when_design_lacks_the_required_strength(self):
        result = check_population_first(4, 4)  # the design is strength 3 only
        self.assertEqual(result["overall"], "FAIL")
        self.assertIn("design_is_strength_r", result["failed_checks"])

    def test_rejects_m_below_four(self):
        with self.assertRaises(ValueError):
            check_population_first(2, 3)

    def test_bundle_entry_point(self):
        verdict = verify_bundle(population_first_bundle(4))
        self.assertEqual(verdict["overall"], "PASS")
        self.assertEqual(verdict["claim"], "counterexample_population_first")
        self.assertEqual(verdict["claim_id"], bundle_hash(population_first_bundle(4)))
        self.assertEqual(verdict["r"], 3)

    def test_bundle_requires_even_m(self):
        with self.assertRaises(ValueError):
            verify_bundle(population_first_bundle(5))


if __name__ == "__main__":
    unittest.main()

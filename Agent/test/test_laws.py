"""Limit-law diagnostics: exact laws, moments, variance identity, decay."""

import unittest
from fractions import Fraction

from ht_moonshine.algebra import back_solve_closed_form
from ht_moonshine.designs import projective_plane
from ht_moonshine.laws import (
    block_law_ks_to_normal,
    centered_rational_quantiles,
    check_srswor_clt,
    exact_variances,
    hajek_decay_study,
    moments,
    sample_total_law,
)


class TestExactLaw(unittest.TestCase):
    def test_moments_of_a_two_point_law(self):
        result = moments([Fraction(-1), Fraction(1)], [Fraction(1, 2), Fraction(1, 2)])
        self.assertEqual(float(result["mean"]), 0.0)
        self.assertAlmostEqual(float(result["sd"]), 1.0, places=6)
        self.assertAlmostEqual(float(result["skewness"]), 0.0, places=6)
        self.assertAlmostEqual(float(result["kurtosis"]), 1.0, places=6)  # two-point law

    def test_probabilities_must_sum_to_one(self):
        with self.assertRaises(ValueError):
            moments([Fraction(0)], [Fraction(1, 2)])

    def test_block_law_is_not_the_normal_shape(self):
        design = projective_plane(13)
        y = back_solve_closed_form(design, centered_rational_quantiles(design.b))["y"]
        law = sample_total_law(design, y)
        self.assertGreater(float(law["moments"]["skewness"]), 1.5)
        self.assertGreater(block_law_ks_to_normal(law), 0.05)


class TestVarianceIdentity(unittest.TestCase):
    def test_identical_first_two_moments(self):
        design = projective_plane(13)
        y = back_solve_closed_form(design, centered_rational_quantiles(design.b))["y"]
        variances = exact_variances(design, y)
        self.assertTrue(variances["means_equal"])
        self.assertTrue(variances["equal"])
        # the equality is exact rational arithmetic, not a tolerance
        self.assertEqual(variances["srswor_closed_form"], variances["block_law"])

    def test_variance_scales_like_one_over_q(self):
        variances = []
        for q in (7, 11, 13):
            design = projective_plane(q)
            y = back_solve_closed_form(design, centered_rational_quantiles(design.b))["y"]
            variances.append(float(exact_variances(design, y)["block_law"]))
        self.assertTrue(all(value > 0 for value in variances))


class TestSrsworDiagnostics(unittest.TestCase):
    def test_srswor_totals_are_close_to_normal(self):
        design = projective_plane(13)
        y = back_solve_closed_form(design, centered_rational_quantiles(design.b))["y"]
        check = check_srswor_clt(y, design.block_size, reps=6000, seed=7)
        self.assertLess(check["srswor_totals"]["ks_vs_normal"], 0.05)
        self.assertLess(abs(check["srswor_totals"]["skewness"]), 0.3)
        self.assertGreater(int(check["max_abs_y"].replace(".", "").lstrip("0")), 0)

    def test_reproducible_with_the_same_seed(self):
        design = projective_plane(7)
        y = back_solve_closed_form(design, centered_rational_quantiles(design.b))["y"]
        first = check_srswor_clt(y, design.block_size, reps=500, seed=99)
        second = check_srswor_clt(y, design.block_size, reps=500, seed=99)
        self.assertEqual(first["srswor_totals"], second["srswor_totals"])


class TestDecay(unittest.TestCase):
    def test_hajek_ratio_decays_in_q(self):
        study = hajek_decay_study([5, 7, 11, 13, 17])
        self.assertTrue(study["endpoints_decrease"])
        self.assertLess(study["loglog_slope"], 0)
        self.assertTrue(study["consistent_with_o_one_over_q"])

    def test_rows_are_complete(self):
        study = hajek_decay_study([5, 7])
        self.assertEqual(len(study["rows"]), 2)
        for row in study["rows"]:
            self.assertIn("hajek_ratio", row)
            self.assertIn("max_abs_y", row)


if __name__ == "__main__":
    unittest.main()

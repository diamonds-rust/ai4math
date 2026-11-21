"""Exact linear algebra: the block-total inverse problem."""

import unittest
from fractions import Fraction

from ht_moonshine.algebra import (
    back_solve_closed_form,
    block_sums,
    centered,
    check_symmetric_identity,
    hajek_ratio,
    incidence,
    matmul,
    population_variance,
    solve_linear,
    transpose,
)
from ht_moonshine.designs import hadamard3, projective_plane
from ht_moonshine.laws import centered_rational_quantiles


class TestSymmetricInverse(unittest.TestCase):
    def test_residual_is_exactly_zero(self):
        design = projective_plane(7)
        w = centered_rational_quantiles(design.b)
        result = back_solve_closed_form(design, w)
        self.assertTrue(result["solvable"])
        self.assertEqual(str(result["residual_max_abs"]), "0")
        self.assertEqual(result["method"], "closed_form_symmetric")

    def test_reconstruction_is_independent_of_the_algebra(self):
        design = projective_plane(5)
        w = centered_rational_quantiles(design.b)
        y = back_solve_closed_form(design, w)["y"]
        self.assertEqual(block_sums(design, y), w)

    def test_non_centered_totals_are_not_realisable(self):
        design = projective_plane(5)
        w = [Fraction(1)] * design.b  # sum != 0, so J w != 0
        result = back_solve_closed_form(design, w)
        self.assertFalse(result["solvable"])


class TestOverDetermined(unittest.TestCase):
    def test_hadamard3_system_is_inconsistent(self):
        design = hadamard3(4)
        w = centered_rational_quantiles(design.b)
        A = incidence(design)
        result = solve_linear(A, w)
        self.assertFalse(result["solvable"])
        self.assertLess(result["rank"], result["augmented_rank"])
        self.assertEqual(result["rank"], 16)

    def test_rank_numerics(self):
        A = [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)], [Fraction(1), Fraction(1)]]
        consistent = solve_linear(A, [Fraction(1), Fraction(2), Fraction(3)])
        self.assertTrue(consistent["solvable"])
        self.assertEqual(consistent["solution"], [Fraction(1), Fraction(2)])
        inconsistent = solve_linear(A, [Fraction(1), Fraction(2), Fraction(4)])
        self.assertFalse(inconsistent["solvable"])


class TestMatrixHelpers(unittest.TestCase):
    def test_transpose_and_product(self):
        A = [[Fraction(1), Fraction(2)], [Fraction(3), Fraction(4)]]
        self.assertEqual(transpose(A), [[Fraction(1), Fraction(3)], [Fraction(2), Fraction(4)]])
        self.assertEqual(matmul(A, A), [[Fraction(7), Fraction(10)], [Fraction(15), Fraction(22)]])

    def test_symmetric_identity_limited_to_square(self):
        report = check_symmetric_identity(hadamard3(4))
        self.assertFalse(report["applicable"])

    def test_centered_and_variance(self):
        values = [Fraction(1), Fraction(2), Fraction(3)]
        self.assertEqual(sum(centered(values), Fraction(0)), 0)
        self.assertEqual(population_variance(values), 1)

    def test_hajek_ratio_is_finite(self):
        design = projective_plane(7)
        y = back_solve_closed_form(design, centered_rational_quantiles(design.b))["y"]
        ratio = hajek_ratio(y, design.block_size)
        self.assertGreater(float(ratio), 0.0)
        self.assertLess(float(ratio), 1.0)


if __name__ == "__main__":
    unittest.main()

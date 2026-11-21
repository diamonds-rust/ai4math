"""Broader method space: design search, weighted designs, permutations, simulation."""

import unittest
from fractions import Fraction

from ht_moonshine.designs import hadamard3, projective_plane
from ht_moonshine.explore import (
    design_search,
    permutation_search,
    simulate_design,
    weight_search,
)
from ht_moonshine.algebra import back_solve_closed_form
from ht_moonshine.laws import centered_rational_quantiles


class TestDesignSearch(unittest.TestCase):
    def test_finds_the_3_design(self):
        result = design_search(8, 4, 3, 1, max_nodes=200000, time_limit=15)
        self.assertEqual(result["status"], "satisfied")
        self.assertEqual(result["block_count"], 14)
        self.assertTrue(result["verified_strength"])
        self.assertEqual(result["lambda_profile"]["3"], [1])

    def test_reports_infeasible_when_counts_forbid(self):
        # C(5,2) = 10 pairs, each block of size 3 covers 3 pairs: no exact cover exists
        result = design_search(5, 3, 2, 1, max_nodes=5000, time_limit=5)
        self.assertEqual(result["status"], "infeasible")

    def test_budget_exhaustion_is_not_infeasibility(self):
        result = design_search(16, 8, 3, 3, max_nodes=5, time_limit=1)
        self.assertIn(result["status"], ("budget_exhausted", "satisfied"))
        if result["status"] == "budget_exhausted":
            self.assertIn("not a proof", result["note"])


class TestWeightSearch(unittest.TestCase):
    def test_unique_weighting_for_hadamard3(self):
        result = weight_search(hadamard3(4), order=3)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["constraints"], 696)
        self.assertEqual(result["rank"], 30)
        self.assertEqual(result["nullity"], 0)
        self.assertTrue(result["uniform_weights_feasible"])

    def test_refuses_oversized_system(self):
        result = weight_search(projective_plane(7), order=2)
        self.assertEqual(result["status"], "too_large")
        self.assertIn("rows", result)


class TestPermutationSearch(unittest.TestCase):
    def test_search_is_deterministic_and_improves_nothing_worse(self):
        design = projective_plane(7)
        first = permutation_search(design, trials=6, seed=11)
        second = permutation_search(design, trials=6, seed=11)
        self.assertEqual(first["status"], "ok")
        self.assertEqual(first["best"]["permutation"], second["best"]["permutation"])
        self.assertEqual(first["best"]["max_abs_y"], second["best"]["max_abs_y"])

    def test_blocks_when_inverse_is_unsolvable(self):
        result = permutation_search(hadamard3(4), trials=3, seed=5)
        self.assertEqual(result["status"], "blocked")


class TestSimulateDesign(unittest.TestCase):
    def test_reproducible_and_shape_sane(self):
        design = projective_plane(7)
        y = back_solve_closed_form(design, centered_rational_quantiles(design.b))["y"]
        first = simulate_design([list(b) for b in design.blocks], [float(v) for v in y], reps=500, seed=42)
        second = simulate_design([list(b) for b in design.blocks], [float(v) for v in y], reps=500, seed=42)
        self.assertEqual(first["moments"], second["moments"])
        self.assertGreater(first["moments"]["skewness"], 1.0)

    def test_rejects_bad_weights(self):
        with self.assertRaises(ValueError):
            simulate_design([[0, 1], [2, 3]], [0.0, 0.0, 0.0, 0.0], weights=[0.3, 0.3])

    def test_rejects_bad_blocks(self):
        with self.assertRaises(ValueError):
            simulate_design([[0, 1], [2, 9]], [0.0, 0.0, 0.0, 0.0])


if __name__ == "__main__":
    unittest.main()

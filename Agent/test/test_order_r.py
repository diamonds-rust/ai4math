"""General order-r strength profile of the affine-hyperplane design."""

import unittest

from ht_moonshine.hyperplane import order_r_obstruction


class TestOrderRObstruction(unittest.TestCase):
    def test_r2_pairs_form_a_design(self):
        result = order_r_obstruction(4, 2)
        self.assertTrue(result["is_design"])
        self.assertEqual(result["lambda_values"], [7])

    def test_r3_triples_form_a_design(self):
        result = order_r_obstruction(6, 3)
        self.assertTrue(result["is_design"])
        self.assertEqual(result["lambda_values"], [15])
        self.assertEqual(result["feasible_affine_dimensions"], [2])

    def test_r4_has_two_lambda_values(self):
        result = order_r_obstruction(6, 4)
        self.assertFalse(result["is_design"])
        self.assertEqual(result["lambda_values"], [7, 15])
        self.assertEqual(result["verdict"], "not_a_design_at_order_r")
        self.assertEqual(result["feasible_affine_dimensions"], [2, 3])

    def test_r5_fails_as_well(self):
        result = order_r_obstruction(8, 5)
        self.assertFalse(result["is_design"])
        self.assertGreaterEqual(len(result["lambda_values"]), 2)

    def test_hyperplane_design_strength_is_exactly_three(self):
        for r in (4, 5, 6):
            self.assertFalse(order_r_obstruction(8, r)["is_design"], msg="r=%d" % r)

    def test_bad_parameters_raise(self):
        with self.assertRaises(ValueError):
            order_r_obstruction(4, 1)
        with self.assertRaises(ValueError):
            order_r_obstruction(4, 17)


if __name__ == "__main__":
    unittest.main()

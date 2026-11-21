"""Design construction and strength verification."""

import unittest

from ht_moonshine.designs import (
    ag_planes,
    block_sizes,
    difference_set_ok,
    hadamard3,
    projective_plane,
    sylvester_hadamard,
    verify_strength,
)


class TestProjectivePlane(unittest.TestCase):
    def test_parameters_and_strength(self):
        design = projective_plane(7)
        self.assertEqual((design.v, design.b, design.block_size), (57, 57, 8))
        self.assertTrue(verify_strength(design, 2)["is_design"])
        self.assertEqual(block_sizes(design), {8: 57})

    def test_singer_difference_set(self):
        design = projective_plane(7)
        self.assertTrue(difference_set_ok(design))
        # every non-zero difference occurs exactly once among ordered pairs
        N = design.v
        D = design.params["difference_set"]
        seen = {(d1 - d2) % N for d1 in D for d2 in D if d1 != d2}
        self.assertEqual(len(seen), N - 1)

    def test_symmetric_identity(self):
        """A A^T = (n-1)I + J is what makes the block-total inverse work."""
        from ht_moonshine.algebra import check_symmetric_identity

        report = check_symmetric_identity(projective_plane(5))
        self.assertTrue(report["applicable"])
        self.assertTrue(report["ok"])

    def test_not_strength_three(self):
        design = projective_plane(7)
        self.assertFalse(verify_strength(design, 3)["is_design"])


class TestHadamard3(unittest.TestCase):
    def test_strength_three_small(self):
        design = hadamard3(3)
        self.assertEqual((design.v, design.b, design.block_size), (8, 14, 4))
        report = verify_strength(design, 3)
        self.assertTrue(report["is_design"])
        self.assertEqual(report["orders"]["3"]["lambda_values"], [1])

    def test_strength_three_16(self):
        design = hadamard3(4)
        self.assertEqual((design.v, design.b, design.block_size), (16, 30, 8))
        report = verify_strength(design, 3)
        self.assertTrue(report["is_design"])
        self.assertEqual(report["orders"]["3"]["lambda_values"], [3])

    def test_sylvester_orthogonality(self):
        H = sylvester_hadamard(8)
        for i in range(8):
            for j in range(8):
                dot = sum(H[i][k] * H[j][k] for k in range(8))
                self.assertEqual(dot, 8 if i == j else 0)


class TestAgPlanes(unittest.TestCase):
    def test_strength_three(self):
        design = ag_planes(4)
        self.assertEqual((design.v, design.block_size), (16, 4))
        report = verify_strength(design, 3)
        self.assertTrue(report["is_design"])
        self.assertEqual(report["orders"]["3"]["lambda_values"], [1])
        # every block is a coset of a 2-dimensional subspace: the XOR of its points is 0
        for block in design.blocks:
            self.assertEqual(len(block), 4)
            xor = 0
            for point in block:
                xor ^= point
            self.assertEqual(xor, 0)

    def test_rejects_bad_parameters(self):
        with self.assertRaises(ValueError):
            hadamard3(1)
        with self.assertRaises(ValueError):
            projective_plane(1)


if __name__ == "__main__":
    unittest.main()

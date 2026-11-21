"""Exact linear algebra for the block-total inverse problem.

Two operations matter for the HT counterexample programme:

* verifying the symmetric-design identity ``A A^T = (n-1) I + J`` (which is what
  makes arbitrary centered block totals realisable for r = 2), and
* actually producing a population ``y`` with ``A y = w`` for a prescribed block
  total vector ``w``, or proving that no such ``y`` exists (the r >= 3 case).

Everything is exact: entries are ints, vectors and matrices of Fractions.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from .designs import Design


def zero_vector(size: int) -> List[Fraction]:
    return [Fraction(0) for _ in range(size)]


def matvec(matrix: Sequence[Sequence[Fraction]], vector: Sequence[Fraction]) -> List[Fraction]:
    """Return matrix @ vector."""
    out: List[Fraction] = []
    for row in matrix:
        total = Fraction(0)
        for a, b in zip(row, vector):
            total += a * b
        out.append(total)
    return out


def matmul(A: Sequence[Sequence[Fraction]], B: Sequence[Sequence[Fraction]]) -> List[List[Fraction]]:
    """Return A @ B (both dense)."""
    if not A:
        return []
    rows = len(A)
    cols = len(B[0]) if B else 0
    inner = len(B)
    out = [[Fraction(0) for _ in range(cols)] for _ in range(rows)]
    for i in range(rows):
        Ai = A[i]
        for k in range(inner):
            a = Ai[k]
            if a:
                Bk = B[k]
                for j in range(cols):
                    if Bk[j]:
                        out[i][j] += a * Bk[j]
    return out


def transpose(A: Sequence[Sequence[Fraction]]) -> List[List[Fraction]]:
    if not A:
        return []
    return [[A[i][j] for i in range(len(A))] for j in range(len(A[0]))]


def incidence(design: Design) -> List[List[Fraction]]:
    """Return the B-by-v 0/1 incidence matrix of the design."""
    A = [[Fraction(0) for _ in range(design.v)] for _ in range(design.b)]
    for row, block in enumerate(design.blocks):
        for point in block:
            A[row][point] = Fraction(1)
    return A


def block_sums(design: Design, y: Sequence[Fraction]) -> List[Fraction]:
    """Return A @ y, i.e. the sample total of every block, without building A."""
    return [sum((y[point] for point in block), Fraction(0)) for block in design.blocks]


def check_symmetric_identity(design: Design, limit: int = 120) -> Dict[str, object]:
    """Verify A A^T = (n-1) I + J exactly, for square symmetric designs."""
    if design.b != design.v:
        return {"applicable": False, "reason": "not square (b != v)"}
    if design.v > limit:
        return {"applicable": False, "reason": "v=%d exceeds exact-check limit %d" % (design.v, limit)}
    A = incidence(design)
    AAT = matmul(A, transpose(A))
    n = design.block_size
    ok = True
    first_bad: Optional[Tuple[int, int]] = None
    for i in range(design.v):
        for j in range(design.v):
            # (A A^T)_ij = |B_i ∩ B_j| = n on the diagonal, lambda = 1 off it
            expected = Fraction(n if i == j else 1)
            if AAT[i][j] != expected:
                ok = False
                if first_bad is None:
                    first_bad = (i, j)
    return {
        "applicable": True,
        "ok": ok,
        "identity": "A A^T = (n-1) I + J with n = %d" % n,
        "first_mismatch": list(first_bad) if first_bad else None,
    }


def back_solve_closed_form(design: Design, w: Sequence[Fraction]) -> Dict[str, object]:
    """Solve A y = w through the symmetric identity: y = A^T w / (n-1).

    Only valid when b == v and the design is a symmetric 2-design (projective
    plane). The returned ``residual`` is computed by an independent forward
    application of A to y, not by trusting the algebra.
    """
    if design.b != design.v:
        return {"solvable": False, "reason": "not square (b=%d, v=%d)" % (design.b, design.v)}
    if len(w) != design.b:
        return {"solvable": False, "reason": "w has length %d, expected %d" % (len(w), design.b)}
    n = design.block_size
    scale = Fraction(n - 1)
    # y_i = (1/(n-1)) * sum of w over the blocks containing point i
    y = [Fraction(0) for _ in range(design.v)]
    for block, weight in zip(design.blocks, w):
        if not weight:
            continue
        for point in block:
            y[point] += weight
    y = [value / scale for value in y]
    reconstructed = block_sums(design, y)
    residual = [reconstructed[j] - w[j] for j in range(len(w))]
    return {
        "solvable": all(item == 0 for item in residual),
        "method": "closed_form_symmetric",
        "scale": str(scale),
        "y": y,
        "residual_max_abs": str(max((abs(item) for item in residual), default=Fraction(0))),
        "residual": residual,
    }


def solve_linear(A: Sequence[Sequence[Fraction]], b: Sequence[Fraction]) -> Dict[str, object]:
    """Exact Gauss-Jordan solve of A x = b.

    Returns solvable/rank/augmented-rank and one solution when it exists. Size
    is not artificially capped, but callers should stay at v <= 80 for speed.
    """
    m = len(A)
    if m == 0:
        return {"solvable": False, "reason": "empty system"}
    n = len(A[0])
    # augmented copy
    aug = [[Fraction(A[i][j]) for j in range(n)] + [Fraction(b[i])] for i in range(m)]
    pivot_row = 0
    pivot_cols: List[int] = []
    for col in range(n):
        pivot = None
        for row in range(pivot_row, m):
            if aug[row][col] != 0:
                pivot = row
                break
        if pivot is None:
            continue
        aug[pivot_row], aug[pivot] = aug[pivot], aug[pivot_row]
        pivot_value = aug[pivot_row][col]
        aug[pivot_row] = [item / pivot_value for item in aug[pivot_row]]
        for row in range(m):
            if row == pivot_row:
                continue
            factor = aug[row][col]
            if factor:
                aug[row] = [a - factor * bb for a, bb in zip(aug[row], aug[pivot_row])]
        pivot_cols.append(col)
        pivot_row += 1
        if pivot_row == m:
            break
    rank = pivot_row
    # consistency: a row with all-zero coefficients but nonzero rhs
    inconsistent = False
    for row in range(rank, m):
        if all(item == 0 for item in aug[row][:n]) and aug[row][n] != 0:
            inconsistent = True
            break
    solution = [Fraction(0) for _ in range(n)]
    for index, col in enumerate(pivot_cols):
        solution[col] = aug[index][n]
    return {
        "solvable": not inconsistent,
        "rank": rank,
        "augmented_rank": rank if not inconsistent else rank + 1,
        "solution": solution if not inconsistent else None,
        "pivot_columns": pivot_cols,
        "degrees_of_freedom": n - rank,
    }


def solve_block_totals(design: Design, w: Sequence[Fraction]) -> Dict[str, object]:
    """Solve A y = w exactly, preferring the closed form for symmetric designs."""
    closed = back_solve_closed_form(design, w)
    if closed.get("solvable"):
        return closed
    if design.v > 80:
        return {
            "solvable": False,
            "reason": "not square and v=%d exceeds the exact elimination limit 80" % design.v,
        }
    A = incidence(design)
    result = solve_linear(A, [Fraction(item) for item in w])
    if not result.get("solvable"):
        return {
            "solvable": False,
            "method": "gauss_jordan",
            "rank": result.get("rank"),
            "augmented_rank": result.get("augmented_rank"),
            "reason": "A y = w is inconsistent: rank(A) < rank([A|w])",
        }
    y = result["solution"]
    residual = [a - bb for a, bb in zip(block_sums(design, y), w)]
    return {
        "solvable": True,
        "method": "gauss_jordan",
        "y": y,
        "residual_max_abs": str(max((abs(item) for item in residual), default=Fraction(0))),
        "degrees_of_freedom": result["degrees_of_freedom"],
    }


def max_abs(values: Sequence[Fraction]) -> Fraction:
    return max((abs(item) for item in values), default=Fraction(0))


def mean(values: Sequence[Fraction]) -> Fraction:
    if not values:
        raise ValueError("empty vector")
    return sum(values, Fraction(0)) / len(values)


def centered(values: Sequence[Fraction]) -> List[Fraction]:
    mu = mean(values)
    return [item - mu for item in values]


def population_variance(values: Sequence[Fraction]) -> Fraction:
    """Unbiased finite-population variance S^2 = sum (y-ybar)^2 / (N-1)."""
    if len(values) < 2:
        raise ValueError("need at least two units")
    mu = mean(values)
    return sum(((item - mu) ** 2 for item in values), Fraction(0)) / (len(values) - 1)


def hajek_ratio(values: Sequence[Fraction], n: int) -> Fraction:
    """Finite-population Lindeberg/Hajek ratio.

    ratio = max_i (y_i - ybar)^2 / ((n-1) S^2); the finite-population CLT
    sufficient condition is ratio -> 0. Note this is a finite-N diagnostic here:
    for a fixed N it is a number, not a proof of an asymptotic statement.
    """
    mu = mean(values)
    s2 = population_variance(values)
    numerator = max(((item - mu) ** 2 for item in values), default=Fraction(0))
    denominator = Fraction(n - 1) * s2
    if denominator == 0:
        return Fraction(0)
    return numerator / denominator

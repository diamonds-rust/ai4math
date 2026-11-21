"""Broader method space: design search, weighted designs, permutation freedom, simulation.

The r = 2 proof used one design family and one construction. Nothing says a
counterexample for r >= 3 must come that way, so the agent needs more than the
three built-in families. This module opens four extra routes:

* ``design_search``       -- exact-cover backtracking for an arbitrary
                             t-(v, k, lambda) design, so families nobody
                             hard-coded can still be found and used;
* ``weight_search``       -- "a design" generalised to "a probability
                             distribution over candidate blocks": exact rank /
                             nullity of the inclusion-probability constraints,
                             plus an explicit alternative weight vector when one
                             exists;
* ``permutation_search``  -- the paper's own degree of freedom: permute the
                             prescribed block totals to shrink max |y_i|;
* ``simulate_design``     -- Monte-Carlo HT law for an arbitrary block list and
                             weight vector, for quick screening before exact
                             work.
"""

from __future__ import annotations

import math
import random
import time
from fractions import Fraction
from itertools import combinations
from typing import Dict, List, Optional, Sequence, Tuple

from .algebra import block_sums, hajek_ratio, incidence, max_abs, mean, solve_linear
from .designs import Design, verify_strength
from .exact import srswor_inclusion_prob
from .laws import (
    centered_rational_quantiles,
    ks_distance_empirical_to_normal,
    normal_cdf,
    sample_moments,
)


# --------------------------------------------------------------- design search


def design_search(
    v: int,
    k: int,
    t: int,
    lam: int = 1,
    max_nodes: int = 200000,
    time_limit: float = 20.0,
    max_solutions: int = 1,
) -> Dict[str, object]:
    """Search for a t-(v, k, lam) design by exact-cover backtracking.

    Returns ``satisfied`` with block lists, ``infeasible`` when the covering
    count can be exhausted, or ``budget_exhausted`` when the search stopped
    first (which is not evidence of non-existence).
    """
    if not (1 <= t <= k <= v):
        raise ValueError("need 1 <= t <= k <= v")
    if lam < 1:
        raise ValueError("lambda must be positive")

    targets = list(combinations(range(v), t))
    target_index = {subset: index for index, subset in enumerate(targets)}
    if len(targets) > 4000:
        raise ValueError("too many t-subsets (%d); keep v small for an exact search" % len(targets))

    # divisibility precheck: every block covers C(k,t) t-subsets, so b must be integral
    import math

    triples_per_block = math.comb(k, t)
    total_needed = lam * math.comb(v, t)
    if total_needed % triples_per_block != 0:
        return {
            "status": "infeasible",
            "v": v,
            "k": k,
            "t": t,
            "lambda": lam,
            "nodes": 0,
            "reason": "count divisibility: lambda*C(v,t) is not a multiple of C(k,t)",
            "note": "infeasible by the standard counting identity, before any search",
        }

    candidates: List[Tuple[Tuple[int, ...], Tuple[int, ...]]] = []
    blocks_by_subset: List[List[int]] = [[] for _ in targets]
    for block in combinations(range(v), k):
        covered = tuple(target_index[subset] for subset in combinations(block, t))
        index = len(candidates)
        candidates.append((block, covered))
        for subset_index in covered:
            blocks_by_subset[subset_index].append(index)

    cover = [0] * len(targets)
    solutions: List[List[Tuple[int, ...]]] = []
    nodes = [0]
    start = time.time()
    budget_exhausted = [False]

    def recurse() -> None:
        if len(solutions) >= max_solutions:
            return
        nodes[0] += 1
        if nodes[0] > max_nodes or time.time() - start > time_limit:
            budget_exhausted[0] = True
            return
        unmet = [index for index, count in enumerate(cover) if count < lam]
        if not unmet:
            solutions.append([block for block, _ in current])
            return
        # static heuristic: branch on the unmet t-subset with the fewest candidate blocks
        branch = min(unmet, key=lambda item: len(blocks_by_subset[item]))
        options = [
            index
            for index in blocks_by_subset[branch]
            if all(cover[item] < lam for item in candidates[index][1])
        ]
        if not options:
            return
        for index in options:
            block, covered = candidates[index]
            for item in covered:
                cover[item] += 1
            current.append((block, covered))
            recurse()
            current.pop()
            for item in covered:
                cover[item] -= 1
            if budget_exhausted[0] or len(solutions) >= max_solutions:
                return

    current: List[Tuple[Tuple[int, ...], Tuple[int, ...]]] = []
    recurse()

    if solutions:
        blocks = [sorted(block) for block in solutions[0]]
        design = Design(family="custom", v=v, blocks=[tuple(block) for block in blocks], params={"k": k, "t": t})
        strength = verify_strength(design, t)
        return {
            "status": "satisfied",
            "v": v,
            "k": k,
            "t": t,
            "lambda": lam,
            "blocks": [list(block) for block in blocks],
            "block_count": len(blocks),
            "verified_strength": strength["is_design"],
            "lambda_profile": {order: entry["lambda_values"] for order, entry in strength["orders"].items()},
            "nodes": nodes[0],
            "elapsed_seconds": round(time.time() - start, 3),
        }
    return {
        "status": "budget_exhausted" if budget_exhausted[0] else "infeasible",
        "v": v,
        "k": k,
        "t": t,
        "lambda": lam,
        "nodes": nodes[0],
        "elapsed_seconds": round(time.time() - start, 3),
        "note": (
            "budget_exhausted is not a proof of non-existence; raise max_nodes/time_limit "
            "or change parameters before concluding anything."
        ),
    }


# --------------------------------------------------------------- weighted designs


def constraint_matrix(design: Design, order: int) -> Dict[str, object]:
    """Rows of the inclusion-probability constraint system over block weights.

    Row for subset S: coefficient 1 on block j iff S is contained in block j.
    Target: sum_j p_j 1[S subset B_j] = C(n, |S|)/C(N, |S|).
    """
    n = design.block_size
    N = design.v
    rows: List[List[Fraction]] = []
    targets: List[Fraction] = []
    labels: List[List[int]] = []
    for s in range(1, order + 1):
        for subset in combinations(range(N), s):
            row = [Fraction(0)] * design.b
            hit = False
            for j, block in enumerate(design.blocks):
                if set(subset).issubset(block):
                    row[j] = Fraction(1)
                    hit = True
            if not hit:
                continue  # a subset in no block forces target 0; handled by caller
            rows.append(row)
            targets.append(srswor_inclusion_prob(N, n, s))
            labels.append(list(subset))
    return {"rows": rows, "targets": targets, "labels": labels}


def _rref(matrix: List[List[Fraction]]) -> Tuple[List[List[Fraction]], List[int], int]:
    """Reduced row echelon form over the rationals (returns also pivots and rank)."""
    if not matrix:
        return [], [], 0
    rows = [list(row) for row in matrix]
    n_cols = len(rows[0])
    pivot_row = 0
    pivots: List[int] = []
    for col in range(n_cols):
        pivot = None
        for index in range(pivot_row, len(rows)):
            if rows[index][col] != 0:
                pivot = index
                break
        if pivot is None:
            continue
        rows[pivot_row], rows[pivot] = rows[pivot], rows[pivot_row]
        value = rows[pivot_row][col]
        rows[pivot_row] = [item / value for item in rows[pivot_row]]
        for index in range(len(rows)):
            if index != pivot_row and rows[index][col] != 0:
                factor = rows[index][col]
                rows[index] = [a - factor * b for a, b in zip(rows[index], rows[pivot_row])]
        pivots.append(col)
        pivot_row += 1
        if pivot_row == len(rows):
            break
    return rows, pivots, pivot_row


def weight_search(design: Design, order: int = 3, max_rows: int = 1200) -> Dict[str, object]:
    """Rank/nullity of the inclusion-probability constraints over block weights.

    With uniform weights 1/B (a genuine design) the weight vector sits in the
    relative interior, so the feasible set has local dimension nullity = B - rank.
    A positive nullity means the *design* can be generalised to a distribution
    over blocks without changing inclusion probabilities through ``order``.
    """
    system = constraint_matrix(design, order)
    rows = system["rows"]
    targets = system["targets"]
    if len(rows) > max_rows:
        return {
            "status": "too_large",
            "rows": len(rows),
            "note": "reduce v or order; the exact rank computation is quadratic in the row count",
        }
    uniform = [Fraction(1, design.b)] * design.b
    uniform_ok = all(
        sum((p for p, coefficient in zip(uniform, row) if coefficient), Fraction(0)) == target
        for row, target in zip(rows, targets)
    )
    # rank of B equals rank of B^T; eliminate the small side for speed
    transposed = [[rows[i][j] for i in range(len(rows))] for j in range(design.b)]
    _, pivots, rank = _rref(transposed)
    nullity = design.b - rank
    payload: Dict[str, object] = {
        "status": "ok",
        "family": design.family,
        "v": design.v,
        "b": design.b,
        "n": design.block_size,
        "order": order,
        "constraints": len(rows),
        "rank": rank,
        "nullity": nullity,
        "face_dimension": nullity,
        "uniform_weights_feasible": uniform_ok,
        "uniform_weight": str(Fraction(1, design.b)),
        "note": (
            "nullity > 0 means a family of block-weightings matches every inclusion "
            "probability through this order; that is the natural next search space "
            "when no symmetric design exists."
        ),
    }
    if nullity > 0:
        # find one null vector by putting the last free column at 1 and solving B d = 0
        free = None
        for col in range(design.b - 1, -1, -1):
            if col not in pivots:
                free = col
                break
        if free is not None:
            rhs = [Fraction(0) for _ in rows]
            reduced = [list(row) for row in rows]
            for row in reduced:
                row[free] = Fraction(0)
            # solve B_rest d_rest = -B_free * 1 for the pivot columns
            sub_rows = [[row[col] for col in pivots] for row in reduced]
            sub_targets = [-row[free] for row in reduced]
            solution = solve_linear(sub_rows, sub_targets)
            if solution.get("solvable"):
                direction = [Fraction(0)] * design.b
                direction[free] = Fraction(1)
                for col, value in zip(pivots, solution["solution"]):
                    direction[col] = value
                payload["null_direction"] = [str(item) for item in direction]
                payload["alternative_weight_vector"] = _perturb(uniform, direction)
    return payload


def _perturb(uniform: Sequence[Fraction], direction: Sequence[Fraction]) -> List[str]:
    """Return uniform + eps * direction with eps small enough to stay non-negative."""
    best = None
    for p, d in zip(uniform, direction):
        if d < 0:
            candidate = -p / d
            best = candidate if best is None else min(best, candidate)
    if best is None:
        best = Fraction(1, 100)
    eps = best / 2
    perturbed = [p + eps * d for p, d in zip(uniform, direction)]
    total = sum(perturbed, Fraction(0))
    return [str(item / total) for item in perturbed]


# ---------------------------------------------------------- permutation freedom


def permutation_search(
    design: Design,
    trials: int = 40,
    seed: int = 20261023,
    denominator: int = 1000,
) -> Dict[str, object]:
    """Search random permutations of the prescribed block totals for a small max |y|.

    This is the paper's own degree of freedom: permuting w leaves the block-law
    unchanged while changing the population coordinates.
    """
    from .algebra import back_solve_closed_form, solve_block_totals

    w = centered_rational_quantiles(design.b, denominator)
    rng = random.Random(seed)
    best = None
    evaluated = 0
    for trial in range(max(1, trials)):
        permutation = list(range(design.b))
        rng.shuffle(permutation)
        permuted = [w[permutation[index]] for index in range(design.b)]
        result = solve_block_totals(design, permuted)
        if not result.get("solvable"):
            return {
                "status": "blocked",
                "reason": result.get("reason", ""),
                "trials": trial,
                "note": "the inverse problem must be solvable before permutation search is meaningful",
            }
        y = result["y"]
        score = max_abs(y)
        evaluated += 1
        if best is None or score < best["max_abs_y"]:
            best = {
                "trial": trial,
                "max_abs_y": score,
                "hajek_ratio": hajek_ratio(y, design.block_size),
                "permutation": permutation,
            }
    return {
        "status": "ok",
        "family": design.family,
        "N": design.v,
        "trials": evaluated,
        "seed": seed,
        "best": {
            "trial": best["trial"],
            "max_abs_y": "%.8f" % float(best["max_abs_y"]),
            "hajek_ratio": "%.6f" % float(best["hajek_ratio"]),
            "permutation": best["permutation"],
        },
        "note": "permutation does not change the block law, only the population; it is a free variable.",
    }


# ----------------------------------------------------------------- simulation


def simulate_design(
    blocks: Sequence[Sequence[int]],
    y: Sequence[float],
    weights: Optional[Sequence[float]] = None,
    reps: int = 5000,
    seed: int = 20261023,
) -> Dict[str, object]:
    """Monte-Carlo HT law for an arbitrary fixed-size block list and weights.

    Screening only: exact tools are preferred once a candidate looks promising.
    """
    if not blocks:
        raise ValueError("blocks must not be empty")
    N = len(y)
    for block in blocks:
        if len(block) != len(blocks[0]):
            raise ValueError("design is not fixed-size")
        if any(index < 0 or index >= N for index in block):
            raise ValueError("block index out of range")
    if weights is None:
        weights = [1.0 / len(blocks)] * len(blocks)
    if len(weights) != len(blocks):
        raise ValueError("weights length mismatch")
    total = sum(weights)
    if abs(total - 1.0) > 1e-9:
        raise ValueError("weights must sum to 1, got %r" % total)
    rng = random.Random(seed)
    sampling = []
    cumulative = 0.0
    for weight in weights:
        cumulative += weight
        sampling.append(cumulative)
    values = [float(item) for item in y]
    sums = [sum(values[index] for index in block) for block in blocks]
    totals: List[float] = []
    for _ in range(max(1, reps)):
        draw = rng.random()
        chosen = 0
        while chosen < len(sampling) - 1 and draw > sampling[chosen]:
            chosen += 1
        totals.append(sums[chosen])
    shape = sample_moments(totals)
    normal = ks_distance_empirical_to_normal(totals)
    return {
        "status": "ok",
        "blocks": len(blocks),
        "block_size": len(blocks[0]),
        "N": N,
        "reps": reps,
        "seed": seed,
        "moments": {key: round(value, 6) for key, value in shape.items()},
        "ks_vs_normal": round(normal["ks"], 6),
        "note": "screening only; use the exact tools for any claim that will be recorded.",
    }

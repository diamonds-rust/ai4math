"""Route B candidate: affine-hyperplane design plus a bent-function population.

This is the construction the research agent found for r = 3. It deliberately
goes the other way round from the r = 2 recipe:

* the design is D1 = uniform over all affine hyperplanes of F_2^m,
  H_{S,eps} = {x : parity(S.x) = eps}, S != 0, eps in {0,1};
  block size k = N/2, number of blocks b = 2(N-1), and the design is a
  3-(N, N/2, N/4 - 1) design (strength exactly 3: at order 4 parallelograms and
  independent 4-sets fall into different numbers of hyperplanes);
* the population is chosen first: y_x = f(x) - 1/sqrt(N), with f(x) = (-1)^{g(x)}
  a bent quadratic form g(x) = sum_i x_{2i-1} x_{2i} (m even). Then y is
  two-valued, centered, sum y^2 = N - 1, and max|y| / sqrt(sum y^2) -> 0.

Why it works: for a hyperplane H, the indicator is (1/2)(1 + (-1)^{S.x+eps}), so
the block sum of the *centered* y is (1/2)(-1)^eps times the Walsh coefficient
y_hat(S) = f_hat(S) (S != 0). Bentness makes every |f_hat(S)| = sqrt(N), hence
every block sum is +-sqrt(N)/2 and the HT total under D1 (weight N/k = 2) is
exactly +-sqrt(N): the D1 limit law is Rademacher, for every even m, with no
approximation at all. The SRSWOR side is a two-valued population, so its HT total
is an affine function of a hypergeometric variable and is asymptotically normal
with the same mean 0 and variance N.

For even m, sqrt(N) = 2^(m/2) is an integer, so every quantity here is exact
rational arithmetic -- no floating point except for the KS distance.
"""

from __future__ import annotations

import math
from fractions import Fraction
from itertools import combinations
from typing import Dict, List, Optional, Sequence, Tuple

from .designs import Design, block_sizes, verify_strength


def require_even(m: int) -> int:
    m = int(m)
    if m < 2 or m % 2:
        raise ValueError("ag_hyperplanes needs an even m >= 2 (sqrt(N) must be an integer)")
    return m


def hyperplane_design(m: int) -> Design:
    """All affine hyperplanes of F_2^m, one block per (S, eps)."""
    m = require_even(m)
    N = 1 << m
    blocks: List[Tuple[int, ...]] = []
    for S in range(1, N):
        for eps in (0, 1):
            blocks.append(tuple(x for x in range(N) if ((bin(S & x).count("1")) & 1) == eps))
    return Design(
        family="ag_hyperplanes",
        v=N,
        blocks=blocks,
        params={
            "m": m,
            "N": N,
            "n": N // 2,
            "B": 2 * (N - 1),
            "lambda_3": N // 4 - 1,
            "note": "3-(N, N/2, N/4-1); strength exactly 3, not 4",
        },
    )


def bent_quadratic_signs(m: int) -> List[int]:
    """f(x) = (-1)^{sum_i x_{2i-1} x_{2i}} on F_2^m, as a list of +-1."""
    m = require_even(m)
    N = 1 << m
    signs = []
    for x in range(N):
        g = 0
        for i in range(m // 2):
            g ^= ((x >> (2 * i)) & 1) & ((x >> (2 * i + 1)) & 1)
        signs.append(-1 if g else 1)
    return signs


def walsh(signs: Sequence[int]) -> List[int]:
    """Unnormalised Walsh transform f_hat(S) = sum_x f(x) (-1)^{S.x}, exactly."""
    N = len(signs)
    out = []
    for S in range(N):
        total = 0
        for x, value in enumerate(signs):
            if value == 1:
                total += 1 if ((bin(S & x).count("1")) & 1) == 0 else -1
            else:
                total += -1 if ((bin(S & x).count("1")) & 1) == 0 else 1
        out.append(total)
    return out


def is_bent(m: int) -> Dict[str, object]:
    """Check |f_hat(S)| = sqrt(N) for every S; return the coefficient profile."""
    m = require_even(m)
    N = 1 << m
    root = 1 << (m // 2)
    coefficients = walsh(bent_quadratic_signs(m))
    magnitudes = sorted({abs(value) for value in coefficients})
    return {
        "m": m,
        "N": N,
        "sqrt_N": root,
        "magnitudes": magnitudes,
        "bent": magnitudes == [root],
        "f_hat_0": coefficients[0],
    }


def bent_population(m: int) -> List[Fraction]:
    """y_x = f(x) - 1/sqrt(N), exact because sqrt(N) is an integer for even m."""
    m = require_even(m)
    root = 1 << (m // 2)
    shift = Fraction(1, root)
    return [Fraction(sign) - shift for sign in bent_quadratic_signs(m)]


def population_stats(m: int) -> Dict[str, object]:
    m = require_even(m)
    N = 1 << m
    y = bent_population(m)
    total = sum(y, Fraction(0))
    sum_sq = sum((value * value for value in y), Fraction(0))
    max_abs = max(abs(value) for value in y)
    return {
        "m": m,
        "N": N,
        "mean": str(total / N),
        "centered_sum": str(total),
        "sum_squares": str(sum_sq),
        "expected_sum_squares": str(N - 1),
        "max_abs": str(max_abs),
        "hajek_shape": "%.6f" % float(max_abs / math.sqrt(float(max_abs * max_abs + 0))),
        "two_valued": len({value for value in y}) == 2,
    }


def d1_ht_law(m: int) -> Dict[str, object]:
    """Exact law of the HT total under D1 (uniform hyperplane), as Fractions."""
    m = require_even(m)
    N = 1 << m
    design = hyperplane_design(m)
    y = bent_population(m)
    weight = Fraction(N, design.block_size)  # N/k = 2
    law: Dict[Fraction, Fraction] = {}
    for block in design.blocks:
        total = sum((y[point] for point in block), Fraction(0)) * weight
        law[total] = law.get(total, Fraction(0)) + Fraction(1, design.b)
    return {"law": law, "support": len(law), "variance": _variance(law), "mean": _mean(law)}


def d2_ht_law(m: int) -> Dict[str, object]:
    """Exact law of the HT total under SRSWOR(n = N/2), hypergeometric by construction."""
    m = require_even(m)
    N = 1 << m
    n = N // 2
    root = 1 << (m // 2)
    positives = (N + root) // 2
    shift = Fraction(1, root)
    weight = Fraction(N, n)  # 2
    total_samples = math.comb(N, n)
    law: Dict[Fraction, Fraction] = {}
    for k in range(max(0, n - (N - positives)), min(n, positives) + 1):
        count = math.comb(positives, k) * math.comb(N - positives, n - k)
        if count == 0:
            continue
        sample_total = Fraction(2 * k - n) - Fraction(n, root)
        ht_total = sample_total * weight
        law[ht_total] = law.get(ht_total, Fraction(0)) + Fraction(count, total_samples)
    return {"law": law, "support": len(law), "variance": _variance(law), "mean": _mean(law)}


def _mean(law: Dict[Fraction, Fraction]) -> Fraction:
    return sum((value * prob for value, prob in law.items()), Fraction(0))


def _variance(law: Dict[Fraction, Fraction]) -> Fraction:
    mean = _mean(law)
    return sum(((value - mean) ** 2) * prob for value, prob in law.items())


def _skewness(law: Dict[Fraction, Fraction]) -> float:
    mean = _mean(law)
    variance = _variance(law)
    sd = math.sqrt(float(variance))
    m3 = sum(((value - mean) ** 3) * prob for value, prob in law.items())
    return float(m3) / sd ** 3


def _kurtosis(law: Dict[Fraction, Fraction]) -> float:
    mean = _mean(law)
    variance = _variance(law)
    m4 = sum(((value - mean) ** 4) * prob for value, prob in law.items())
    return float(m4) / float(variance) ** 2


def _normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def ks_to_normal(law: Dict[Fraction, Fraction]) -> float:
    """KS distance of an exact finite law (standardised by its own moments) to N(0,1)."""
    mean = _mean(law)
    sd = math.sqrt(float(_variance(law)))
    cumulative = 0.0
    distance = 0.0
    for value in sorted(law):
        cumulative += float(law[value])
        z = float(value - mean) / sd
        distance = max(distance, abs(cumulative - _normal_cdf(z)))
    return distance


def strength_profile_by_affine_dimension(m: int) -> Dict[str, object]:
    """Count, for every 4-set, how many hyperplanes contain it, via affine dimension.

    A 4-set S spans an affine subspace of dimension d in {2, 3}; an affine
    subspace of dimension d lies in exactly 2^(m-d) - 1 hyperplanes. For F_2,
    d = 2 exactly for parallelograms (a+b+c+d = 0) and d = 3 otherwise, so the
    order-4 lambda profile has two values and the design is strength exactly 3.
    The total is cross-checked against the block incidences sum_blocks C(k,4).
    """
    m = require_even(m)
    N = 1 << m
    k = N // 2
    counts = {2: 0, 3: 0}
    lambda_by_dim = {2: (1 << (m - 2)) - 1, 3: (1 << (m - 3)) - 1}
    for quadruple in combinations(range(N), 4):
        a, b, c, d = quadruple
        # affine span of the four points: rank over F_2 of the three differences
        vectors = [a ^ b, a ^ c, a ^ d]
        rank = 0
        basis: List[int] = []
        for vector in vectors:
            for pivot in basis:
                vector = min(vector, vector ^ pivot)
            if vector:
                basis.append(vector)
                basis.sort(reverse=True)
                rank += 1
        counts[rank] += 1
    total_from_formula = sum(count * lambda_by_dim[dim] for dim, count in counts.items())
    total_from_blocks = len(hyperplane_design(m).blocks) * math.comb(k, 4)
    return {
        "m": m,
        "four_sets_by_affine_dim": {str(dim): count for dim, count in counts.items()},
        "lambda_4_by_dim": {str(dim): value for dim, value in lambda_by_dim.items()},
        "lambda_4_values": sorted(lambda_by_dim.values()),
        "total_from_formula": total_from_formula,
        "total_from_blocks": total_from_blocks,
        "consistent": total_from_formula == total_from_blocks,
        "is_strength_exactly_3": len(set(lambda_by_dim.values())) > 1,
    }


def sample_hyperplane_containment(m: int, trials: int = 300, seed: int = 20261023) -> Dict[str, object]:
    """Spot-check the containment formula on random 4-sets (independent of the count)."""
    import random

    m = require_even(m)
    N = 1 << m
    design = hyperplane_design(m)
    block_sets = [set(block) for block in design.blocks]
    rng = random.Random(seed)
    checked = 0
    mismatches = 0
    for _ in range(trials):
        sample = tuple(sorted(rng.sample(range(N), 4)))
        a, b, c, d = sample
        vectors = [a ^ b, a ^ c, a ^ d]
        rank = 0
        basis: List[int] = []
        for vector in vectors:
            for pivot in basis:
                vector = min(vector, vector ^ pivot)
            if vector:
                basis.append(vector)
                basis.sort(reverse=True)
                rank += 1
        expected = (1 << (m - rank)) - 1
        actual = sum(1 for block in block_sets if set(sample) <= block)
        checked += 1
        if actual != expected:
            mismatches += 1
    return {"m": m, "checked": checked, "mismatches": mismatches, "formula": "2^(m-rank)-1"}


def check_population_first(
    m: int = 4,
    r: int = 3,
    clt_ks_threshold: float = 0.12,
    check_subsets: bool = True,
) -> Dict[str, object]:
    """Run every check needed to certify the Route B counterexample at one m.

    The asymptotic statement is supported by computing the same quantities at
    ``m + 2`` and requiring the KS distance to shrink; a single finite-m value is
    never treated as a CLT proof.
    """
    m = require_even(m)
    if m < 4:
        raise ValueError("the Route B check needs m >= 4: order-3 agreement requires k >= 3")
    N = 1 << m
    design = hyperplane_design(m)
    strength = verify_strength(design, r)

    checks: List[Dict[str, object]] = []

    def add(name: str, ok: bool, detail: Dict[str, object]) -> None:
        checks.append({"name": name, "status": "pass" if ok else "fail", "detail": detail})

    # exact strength, and the order-4 break that shows strength is exactly 3
    if N <= 64:
        profile = strength_profile_by_affine_dimension(m)
        exactly_three = bool(profile["is_strength_exactly_3"] and profile["consistent"])
        order4_detail = {
            "method": "affine-dimension count over all 4-sets",
            "four_sets_by_affine_dim": profile["four_sets_by_affine_dim"],
            "lambda_4_values": profile["lambda_4_values"],
            "formula_total": profile["total_from_formula"],
            "block_incidence_total": profile["total_from_blocks"],
            "consistent": profile["consistent"],
        }
    else:
        exactly_three = True
        order4_detail = {
            "method": "analytic only (N too large for the exact count)",
            "lambda_4_by_dim": {"2": (1 << (m - 2)) - 1, "3": (1 << (m - 3)) - 1},
        }
    add(
        "design_is_strength_r",
        bool(strength["is_design"]),
        {
            "family": design.family,
            "N": design.v,
            "B": design.b,
            "k": design.block_size,
            "lambda_profile": {order: entry["lambda_values"] for order, entry in strength["orders"].items()},
        },
    )
    add(
        "design_strength_is_exactly_r",
        exactly_three,
        dict(order4_detail, note="two distinct order-4 lambda values mean the design is strength exactly 3"),
    )

    # subset-by-subset inclusion check (exhaustive only when N is small)
    subset_report: Dict[str, object]
    if check_subsets and N <= 16:
        from .inclusion import compare_to_srswor

        comparison = compare_to_srswor(design, r)
        subset_report = {
            "exhaustive": True,
            "match": bool(comparison["match"]),
            "mismatch_counts": {order: entry["mismatch_count"] for order, entry in comparison["orders"].items()},
            "expected": {order: entry["expected"] for order, entry in comparison["orders"].items()},
        }
        subset_ok = bool(comparison["match"])
    else:
        subset_report = {
            "exhaustive": False,
            "match": None,
            "counting_argument": (
                "every triple spans an affine 2-space, which lies in 2^(m-2)-1 = N/4-1 hyperplanes; "
                "this equals C(k,3)/C(N,3) with k = N/2, so all order-3 probabilities are C(k,s)/C(N,s)"
            ),
        }
        subset_ok = True
    add("pis_match_srswor_through_r", subset_ok, subset_report)

    bent = is_bent(m)
    stats = population_stats(m)
    add(
        "bent_population_construction",
        bool(bent["bent"])
        and stats["centered_sum"] == "0"
        and stats["sum_squares"] == str(N - 1)
        and stats["two_valued"],
        {
            "walsh_magnitudes": bent["magnitudes"],
            "expected_magnitude": bent["sqrt_N"],
            "centered_sum": stats["centered_sum"],
            "sum_squares": stats["sum_squares"],
            "max_abs": stats["max_abs"],
        },
    )

    d1 = d1_ht_law(m)
    d2 = d2_ht_law(m)
    add(
        "d1_law_is_two_point",
        d1["support"] == 2 and abs(float(d1["mean"])) < 1e-12 and d1["variance"] == N,
        {
            "support": d1["support"],
            "atoms": {str(value): str(prob) for value, prob in sorted(d1["law"].items())},
            "variance": str(d1["variance"]),
        },
    )
    add(
        "same_first_two_moments",
        d2["variance"] == N and abs(float(d2["mean"])) < 1e-12,
        {"d1_variance": str(d1["variance"]), "d2_variance": str(d2["variance"]), "N": N},
    )

    # the CLT is supported by the next instance, not by one finite-m number
    d2_next = d2_ht_law(m + 2)
    ks_now = ks_to_normal(d2["law"])
    ks_next = ks_to_normal(d2_next["law"])
    add(
        "d2_law_is_asymptotically_normal",
        ks_next < clt_ks_threshold and ks_next < 0.7 * ks_now and abs(_kurtosis(d2_next["law"]) - 3.0) < 0.1,
        {
            "ks_at_m": round(ks_now, 6),
            "ks_at_m_plus_2": round(ks_next, 6),
            "skewness_at_m_plus_2": round(_skewness(d2_next["law"]), 6),
            "kurtosis_at_m_plus_2": round(_kurtosis(d2_next["law"]), 4),
            "threshold": clt_ks_threshold,
            "note": "finite-m KS is a diagnostic; the shrinking sequence is the evidence for the limit",
        },
    )
    add(
        "limit_law_differs",
        ks_to_normal(d1["law"]) > 0.05 and d1["support"] == 2,
        {
            "d1_ks_to_normal": round(ks_to_normal(d1["law"]), 6),
            "d1_support": d1["support"],
            "d2_ks_to_normal": round(ks_now, 6),
            "d1_limit": "Rademacher on {+-sqrt(N)}",
            "d2_limit": "standard normal",
        },
    )
    return {
        "claim": "counterexample_population_first",
        "m": m,
        "r": r,
        "N": N,
        "design": {
            "family": "ag_hyperplanes",
            "v": N,
            "b": design.b,
            "block_size": design.block_size,
            "params": dict(design.params),
        },
        "overall": "PASS" if all(item["status"] == "pass" for item in checks) else "FAIL",
        "checks": checks,
        "failed_checks": [item["name"] for item in checks if item["status"] == "fail"],
    }


def population_first_bundle(m: int = 4) -> Dict[str, object]:
    """Bundle spec accepted by ``ht_verify_bundle`` for the Route B construction."""
    return {
        "id": "r3_hyperplane_bent_m%d" % m,
        "claim": "counterexample_population_first",
        "r": 3,
        "design": {"family": "ag_hyperplanes", "params": {"m": m}},
        "population": {"method": "bent_quadratic", "m": m},
        "options": {},
    }


def order_r_obstruction(m: int, r: int) -> Dict[str, object]:
    """Exact strength profile of the affine-hyperplane design at order ``r``.

    For a non-empty ``T`` with affine dimension ``d(T)``, the number of blocks
    containing it is ``2^(m-d) - 1``. An ``r``-subset can have affine dimension
    ``d`` exactly when ``r <= 2^d`` and ``d <= r-1`` (and ``d <= m``), and every
    such ``d`` is realised. Order-``r`` agreement with SRSWOR therefore holds iff
    ``2^(m-d) - 1`` is the same for all feasible ``d``.

    This is the r >= 3 generalisation of ``ht_order3_witness``: it shows in one
    call that the hyperplane family is a design exactly for r <= 3 and fails for
    every r >= 4, so an r >= 4 counterexample needs a genuine strength-4 design.
    """
    m = int(m)
    r = int(r)
    if m < 2:
        raise ValueError("m must be at least 2")
    if r < 2:
        raise ValueError("r must be at least 2")
    N = 1 << m
    if r > N:
        raise ValueError("r must not exceed N = 2^m")

    low = 0
    while (1 << low) < r:
        low += 1
    high = min(r - 1, m)
    dims = list(range(low, high + 1)) if low <= high else []
    rows = [
        {
            "affine_dim": d,
            "points_per_flat": 1 << d,
            "lambda_r": (1 << (m - d)) - 1,
            "blocks_containing": (1 << (m - d)) - 1,
        }
        for d in dims
    ]
    values = sorted({row["lambda_r"] for row in rows})
    is_design = len(values) == 1
    b = 2 * (N - 1)
    required = Fraction(1 << (m - 1), b) if r == 1 else None
    return {
        "tool": "ht_order_r_obstruction",
        "design": "ag_hyperplanes",
        "m": m,
        "r": r,
        "N": N,
        "blocks": b,
        "block_size": N // 2,
        "feasible_affine_dimensions": dims,
        "rows": rows,
        "lambda_values": values,
        "is_design": is_design,
        "verdict": "strength_r_design" if is_design else "not_a_design_at_order_r",
        "note": (
            "lambda(T) = 2^(m-d(T)) - 1; every feasible affine dimension occurs, "
            "so the design has strength exactly 3 and no strength r >= 4."
            if not is_design
            else "a single lambda value at this order; check the exact fractions with ht_inclusion_probs."
        ),
        "required_pair_probability_example": required,
    }

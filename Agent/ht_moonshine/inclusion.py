"""Exact inclusion probabilities and their comparison against SRSWOR.

The comparison is the admission ticket for every counterexample attempt:
agreement through order r must be verified subset by subset in exact rational
arithmetic, never inferred from "it is a t-design, therefore ...".
"""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations
from typing import Dict, List, Sequence, Tuple

from .designs import Design
from .exact import fraction_to_str, srswor_inclusion_prob


def inclusion_probs(design: Design, order: int) -> Dict[int, Dict[Tuple[int, ...], Fraction]]:
    """Return pi_S for every |S| <= order, as exact Fractions.

    Missing subsets have probability zero under the design; callers should use
    ``get(S, Fraction(0))``.
    """
    if order < 1:
        raise ValueError("order must be at least 1")
    B = design.b
    out: Dict[int, Dict[Tuple[int, ...], Fraction]] = {}
    for s in range(1, order + 1):
        counts: Dict[Tuple[int, ...], int] = {}
        for block in design.blocks:
            for subset in combinations(block, s):
                counts[subset] = counts.get(subset, 0) + 1
        out[s] = {subset: Fraction(count, B) for subset, count in counts.items()}
    return out


def compare_to_srswor(
    design: Design,
    order: int,
    max_report: int = 5,
) -> Dict[str, object]:
    """Verify that inclusion probabilities through ``order`` equal SRSWOR's.

    SRSWOR benchmark: pi_S = C(n, s) / C(N, s) for every s-subset S, where
    n = block size and N = number of points.
    """
    n = design.block_size
    N = design.v
    probs = inclusion_probs(design, order)
    report: Dict[str, object] = {
        "family": design.family,
        "N": N,
        "n": n,
        "order": order,
        "match": True,
        "orders": {},
    }
    for s in range(1, order + 1):
        expected = srswor_inclusion_prob(N, n, s)
        mismatches: List[Dict[str, object]] = []
        missing = 0
        for subset in combinations(range(N), s):
            actual = probs[s].get(subset, Fraction(0))
            if actual != expected:
                if len(mismatches) < max_report:
                    mismatches.append(
                        {
                            "subset": list(subset),
                            "actual": fraction_to_str(actual),
                            "expected": fraction_to_str(expected),
                        }
                    )
                missing += 1
        entry = {
            "order": s,
            "expected": fraction_to_str(expected),
            "mismatch_count": missing,
            "mismatch_examples": mismatches,
            "match": missing == 0,
        }
        report["orders"][str(s)] = entry
        if missing:
            report["match"] = False
    return report


def order3_collinear_witness(q: int, collinear: bool) -> Dict[str, object]:
    """Expose why the r = 2 construction cannot be reused for r = 3.

    In PG(2, q) a collinear triple lies on exactly one line (a block), while a
    non-collinear triple lies on none. Both probabilities must equal
    C(n,3)/C(N,3) to agree with SRSWOR through order 3, so they cannot agree
    with each other. This function returns the two exact probabilities.
    """
    from .designs import projective_plane

    design = projective_plane(q)
    probs3 = inclusion_probs(design, 3)[3]
    N = design.v
    n = design.block_size
    expected = srswor_inclusion_prob(N, n, 3)

    collinear_triple = None
    scattered_triple = None
    for subset, value in probs3.items():
        if collinear_triple is None and value == Fraction(1, design.b):
            collinear_triple = subset
        if scattered_triple is None and subset not in probs3:
            scattered_triple = subset
    if collinear_triple is None:
        # every triple in the design's blocks appears; take one explicitly
        collinear_triple = design.blocks[0][:3]
    if scattered_triple is None:
        all_triples = set(combinations(range(N), 3))
        scattered_triple = sorted(all_triples - set(probs3))[0]

    inside = probs3.get(collinear_triple, Fraction(0))
    outside = probs3.get(scattered_triple, Fraction(0))
    return {
        "q": q,
        "N": N,
        "n": n,
        "srswor_order3": fraction_to_str(expected),
        "collinear_triple": list(collinear_triple),
        "collinear_prob": fraction_to_str(inside),
        "scattered_triple": list(scattered_triple),
        "scattered_prob": fraction_to_str(outside),
        "agree": inside == outside == expected,
        "note": (
            "A strength-2 design fixes order <= 2 only. Order 3 already splits into "
            "collinear (1/B) and non-collinear (0) cases, so the r = 2 construction "
            "does not transfer to r = 3."
        ),
    }

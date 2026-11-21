"""Block-design constructors and exact strength verification.

Families implemented (all constructible from scratch, no data files):

* ``projective_plane(q)``  -- PG(2,q) BIBD via the Singer difference set,
  parameters (N, n, B, R, lambda) = (q^2+q+1, q+1, N, q+1, 1). This is the
  family used by Chen (2026) for the r = 2 counterexample. By Theorem 2.1 of
  that paper it reproduces SRSWOR inclusion probabilities through order 2.

* ``hadamard3(m)`` -- the Hadamard 3-design obtained from the Sylvester
  Hadamard matrix of order 4u = 2^m, giving a 3-(4u, 2u, u-1) design. Blocks are
  the sign classes of the non-trivial rows. This is a genuine strength-3 block
  design, i.e. the natural r = 3 analogue of the r = 2 starting point.

* ``ag_planes(m)`` -- the 2-flats of AG(m, 2): a 3-(2^m, 4, 1) design with
  block size 4. Useful as a second, differently-shaped strength-3 family
  (small block size, tiny sampling fraction).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Dict, List, Sequence, Tuple

from .fields import GFp3


@dataclass
class Design:
    """A fixed-size block design, blocks as sorted tuples of point labels."""

    family: str
    v: int
    blocks: List[Tuple[int, ...]]
    params: Dict[str, object] = field(default_factory=dict)

    @property
    def b(self) -> int:
        return len(self.blocks)

    @property
    def block_size(self) -> int:
        sizes = {len(block) for block in self.blocks}
        if len(sizes) != 1:
            raise ValueError("design is not fixed-size: block sizes %r" % (sizes,))
        return sizes.pop()

    def as_dict(self) -> Dict[str, object]:
        payload = {
            "family": self.family,
            "v": self.v,
            "b": self.b,
            "block_size": self.block_size,
            "params": dict(self.params),
        }
        payload.update(dict(self.params))
        return payload


def projective_plane(q: int) -> Design:
    """Build the PG(2, q) BIBD from a Singer difference set.

    Points are the projective points of F_{q^3} / F_q^*, labelled 0..N-1 by
    powers of a primitive element theta; the block D is the set of exponents i
    with Tr(theta^i) = 0, and all blocks are the cyclic translates D + j.
    """
    if q < 2:
        raise ValueError("q must be at least 2")
    N = q * q + q + 1
    field = GFp3(q)
    theta = field.primitive_element()

    difference_set: List[int] = []
    power = field.one
    for i in range(N):
        if field.trace(power) == 0:
            difference_set.append(i)
        power = field.mul(power, theta)
    if len(difference_set) != q + 1:
        raise ArithmeticError(
            "Singer difference set has size %d, expected %d" % (len(difference_set), q + 1)
        )

    blocks = [tuple(sorted((d + j) % N for d in difference_set)) for j in range(N)]
    design = Design(
        family="projective_plane",
        v=N,
        blocks=blocks,
        params={
            "q": q,
            "N": N,
            "n": q + 1,
            "B": N,
            "R": q + 1,
            "lambda": 1,
            "difference_set": list(difference_set),
        },
    )
    return design


def sylvester_hadamard(order: int) -> List[List[int]]:
    """Return the Sylvester Hadamard matrix of the given power-of-two order."""
    if order & (order - 1) or order < 1:
        raise ValueError("order must be a power of two")
    return [[1 - 2 * ((bin(i & j).count("1")) & 1) for j in range(order)] for i in range(order)]


def hadamard3(m: int) -> Design:
    """Hadamard 3-design 3-(4u, 2u, u-1) with 4u = 2^m.

    Blocks are, for each non-trivial row i and each sign eps, the set of
    columns j with H[i][j] = eps. Every row after the first has exactly half
    +1 and half -1 entries, so all blocks have size 4u/2 = 2u.
    """
    if m < 2:
        raise ValueError("m must be at least 2 (4u = 2^m, u >= 2 for a non-degenerate design)")
    order = 1 << m
    H = sylvester_hadamard(order)
    blocks: List[Tuple[int, ...]] = []
    for i in range(1, order):
        for eps in (1, -1):
            block = tuple(j for j in range(order) if H[i][j] == eps)
            blocks.append(block)
    u = order // 4
    return Design(
        family="hadamard3",
        v=order,
        blocks=blocks,
        params={
            "m": m,
            "u": u,
            "v": order,
            "n": order // 2,
            "B": 2 * (order - 1),
            "lambda_3": u - 1,
        },
    )


def ag_planes(m: int) -> Design:
    """The 2-flats of AG(m, 2): a 3-(2^m, 4, 1) design."""
    if m < 2:
        raise ValueError("m must be at least 2")
    v = 1 << m
    points = list(range(v))

    # all 2-dimensional linear subspaces of F_2^m, as frozensets
    subspaces = set()
    for u in points:
        if u == 0:
            continue
        for w in points:
            if w == 0 or w == u:
                continue
            subspaces.add(frozenset({0, u, w, u ^ w}))

    blocks = set()
    for sub in subspaces:
        for a in points:
            blocks.add(tuple(sorted(a ^ x for x in sub)))
    ordered = sorted(blocks)
    return Design(
        family="ag_planes",
        v=v,
        blocks=ordered,
        params={"m": m, "v": v, "n": 4, "B": len(ordered), "lambda_3": 1},
    )


def block_sizes(design: Design) -> Dict[int, int]:
    """Return the histogram of block sizes."""
    hist: Dict[int, int] = {}
    for block in design.blocks:
        hist[len(block)] = hist.get(len(block), 0) + 1
    return hist


def _subset_counts(design: Design, order: int) -> Dict[Tuple[int, ...], int]:
    counts: Dict[Tuple[int, ...], int] = {}
    for block in design.blocks:
        for subset in combinations(block, order):
            counts[subset] = counts.get(subset, 0) + 1
    return counts


def verify_strength(design: Design, t: int) -> Dict[str, object]:
    """Verify exactly that the design is a t-(v, k, lambda_t) design.

    Returns the observed lambda profile, whether it is constant, and the number
    of t-subsets that violate uniformity. This is the check that must pass
    before any inclusion-probability claim is allowed.
    """
    if t < 1:
        raise ValueError("t must be at least 1")
    report: Dict[str, object] = {
        "family": design.family,
        "v": design.v,
        "b": design.b,
        "strength": t,
        "sizes": {str(k): c for k, c in block_sizes(design).items()},
        "orders": {},
        "is_design": True,
    }
    for order in range(1, t + 1):
        counts = _subset_counts(design, order)
        observed = sorted(set(counts.values()))
        expected_subsets = _num_subsets(design.v, order)
        covered = len(counts)
        uniform = len(observed) == 1 and covered == expected_subsets
        report["orders"][str(order)] = {
            "lambda_values": observed,
            "lambda": observed[0] if uniform else None,
            "subsets_total": expected_subsets,
            "subsets_covered": covered,
            "uniform": uniform,
        }
        if not uniform:
            report["is_design"] = False
    return report


def _num_subsets(v: int, s: int) -> int:
    from math import comb

    return comb(v, s)


def difference_set_ok(design: Design) -> bool:
    """Check the cyclic difference-set property of the r = 2 construction."""
    if design.family != "projective_plane":
        raise ValueError("difference_set_ok only applies to projective_plane")
    D = list(design.params["difference_set"])  # type: ignore[index]
    N = design.v
    seen = set()
    for d1 in D:
        for d2 in D:
            if d1 == d2:
                continue
            seen.add((d1 - d2) % N)
    return len(seen) == N - 1

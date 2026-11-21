"""ht_moonshine -- a deterministic HT counterexample toolkit for Moonshine.

Built for the problem: does agreement of inclusion probabilities through a
fixed order r force a common limit law for the Horvitz-Thompson estimator?
Chen (2026, arXiv:2610.09168) settles r = 2 and leaves r >= 3 open.

Design rule of this package: the model may propose, but only exact arithmetic
may decide. Every numeric statement a research agent makes about inclusion
probabilities, sample totals, maxima or limit laws is expected to come from
one of the tools exposed here.

Public entry points are re-exported below; ``python -m ht_moonshine selftest``
runs the full deterministic check suite.
"""

from __future__ import annotations

__version__ = "0.1.0"

from .designs import Design, ag_planes, hadamard3, projective_plane, verify_strength
from .exact import falling, srswor_inclusion_prob
from .inclusion import compare_to_srswor, inclusion_probs, order3_collinear_witness

__all__ = [
    "__version__",
    "Design",
    "ag_planes",
    "hadamard3",
    "projective_plane",
    "verify_strength",
    "falling",
    "srswor_inclusion_prob",
    "compare_to_srswor",
    "inclusion_probs",
    "order3_collinear_witness",
]

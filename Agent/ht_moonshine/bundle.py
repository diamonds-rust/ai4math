"""The deterministic verification gate: verify_counterexample_bundle.

A bundle is a self-contained claim:

    {
      "id": "r2_pg13",
      "claim": "counterexample" | "order_agreement" | "realizability_obstruction",
      "r": 2,
      "design": {"family": "projective_plane", "params": {"q": 13}},
      "population": {"method": "centered_exponential_quantiles", "denominator": 1000},
      "options": {"srswor_reps": 20000, "seed": 20261023, "decay_qs": [5, 7, 11, 13, 17]}
    }

The verifier rebuilds everything from the spec and decides each check with
exact arithmetic (or, for the SRSWOR side, a seeded simulation whose seed and
repetition count are part of the hashed claim). No claim may be accepted on the
model's word: this function is the only place a bundle becomes PASS.
"""

from __future__ import annotations

import hashlib
import json
from typing import Dict, List, Optional

from .algebra import back_solve_closed_form, max_abs, solve_block_totals
from .designs import Design, ag_planes, hadamard3, projective_plane, verify_strength
from .inclusion import compare_to_srswor
from .laws import (
    block_law_ks_to_normal,
    centered_rational_quantiles,
    check_srswor_clt,
    exact_variances,
    hajek_decay_study,
    sample_total_law,
)

CLAIM_TYPES = (
    "counterexample",
    "order_agreement",
    "realizability_obstruction",
    "counterexample_population_first",
)


def build_design(spec: Dict[str, object]) -> Design:
    """Instantiate a design from its JSON spec."""
    family = str(spec.get("family") or "").strip()
    params = dict(spec.get("params") or {})
    if family == "projective_plane":
        return projective_plane(int(params.get("q", 0)))
    if family == "hadamard3":
        return hadamard3(int(params.get("m", 0)))
    if family == "ag_planes":
        return ag_planes(int(params.get("m", 0)))
    if family == "ag_hyperplanes":
        from .hyperplane import hyperplane_design

        return hyperplane_design(int(params.get("m", 0)))
    raise ValueError("unknown design family: %r" % (family,))


def _check(name: str, status: str, detail: Dict[str, object]) -> Dict[str, object]:
    return {"name": name, "status": status, "detail": detail}


def bundle_hash(bundle: Dict[str, object]) -> str:
    """Stable hash of the claim specification (the claim_id)."""
    payload = json.dumps(bundle, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def verify_bundle(bundle: Dict[str, object]) -> Dict[str, object]:
    """Run every check a bundle must survive and return a verdict."""
    claim = str(bundle.get("claim") or "").strip()
    if claim not in CLAIM_TYPES:
        raise ValueError("claim must be one of %r" % (CLAIM_TYPES,))
    r = int(bundle.get("r") or 2)
    if r < 1:
        raise ValueError("r must be >= 1")

    design = build_design(dict(bundle.get("design") or {}))
    options = dict(bundle.get("options") or {})
    pop_spec = dict(bundle.get("population") or {})
    denominator = int(pop_spec.get("denominator", 1000))

    if claim == "counterexample_population_first":
        from .hyperplane import check_population_first

        params = dict(dict(bundle.get("design") or {}).get("params") or {})
        result = check_population_first(
            int(params.get("m", 0)),
            r=r,
            check_subsets=bool(options.get("check_subsets", True)),
        )
        result["claim_id"] = bundle_hash(bundle)
        result["claim"] = claim
        result["bundle_id"] = bundle.get("id", "")
        return result

    checks: List[Dict[str, object]] = []

    # 1. the design really is a strength-r design
    strength = verify_strength(design, r)
    checks.append(
        _check(
            "design_is_strength_r",
            "pass" if strength["is_design"] else "fail",
            {
                "family": design.family,
                "v": design.v,
                "b": design.b,
                "block_size": design.block_size,
                "lambda_profile": {
                    order: entry["lambda_values"] for order, entry in strength["orders"].items()
                },
            },
        )
    )

    # 2. inclusion probabilities through order r equal SRSWOR's, subset by subset
    comparison = compare_to_srswor(design, r)
    checks.append(
        _check(
            "pis_match_srswor_through_r",
            "pass" if comparison["match"] else "fail",
            {
                "r": r,
                "N": design.v,
                "n": design.block_size,
                "expected": {order: entry["expected"] for order, entry in comparison["orders"].items()},
                "mismatch_counts": {
                    order: entry["mismatch_count"] for order, entry in comparison["orders"].items()
                },
                "examples": comparison["orders"].get(str(r), {}).get("mismatch_examples", []),
            },
        )
    )

    # 3. can the prescribed block totals be realised by an actual population?
    w = centered_rational_quantiles(design.b, denominator)
    realization = solve_block_totals(design, w)
    if claim == "realizability_obstruction":
        checks.append(
            _check(
                "block_totals_realizable",
                "pass" if not realization.get("solvable") else "fail",
                {
                    "solvable": bool(realization.get("solvable")),
                    "reason": realization.get("reason", ""),
                    "rank": realization.get("rank"),
                    "augmented_rank": realization.get("augmented_rank"),
                    "note": (
                        "For claim=realizability_obstruction a pass means the obstruction "
                        "is confirmed: A y = w has no solution for the prescribed totals."
                    ),
                },
            )
        )
        overall = "PASS" if all(item["status"] != "fail" for item in checks) else "FAIL"
        return _finish(bundle, design, checks, overall, claim)

    checks.append(
        _check(
            "block_totals_realizable",
            "pass" if realization.get("solvable") else "fail",
            {
                "solvable": bool(realization.get("solvable")),
                "method": realization.get("method", ""),
                "residual_max_abs": str(realization.get("residual_max_abs", "n/a")),
                "degrees_of_freedom": realization.get("degrees_of_freedom"),
                "reason": realization.get("reason", ""),
            },
        )
    )
    if not realization.get("solvable"):
        overall = "FAIL"
        return _finish(bundle, design, checks, overall, claim)

    y = realization["y"]

    if claim == "order_agreement":
        overall = "PASS" if all(item["status"] != "fail" for item in checks) else "FAIL"
        return _finish(bundle, design, checks, overall, claim)

    # 4. SRSWOR-side CLT conditions (finite-N diagnostics + decay evidence)
    n = design.block_size
    reps = int(options.get("srswor_reps", 20000))
    seed = int(options.get("seed", 20261023))
    clt = check_srswor_clt(y, n, reps=reps, seed=seed)
    decay = hajek_decay_study(list(options.get("decay_qs") or [5, 7, 11, 13, 17]))
    srswor_ok = (
        clt["srswor_totals"]["ks_vs_normal"] < 0.05
        and abs(clt["srswor_totals"]["skewness"]) < 0.3
        and decay["consistent_with_o_one_over_q"]
    )
    checks.append(
        _check(
            "srswor_clt_evidence",
            "pass" if srswor_ok else "fail",
            {
                "hajek_ratio_at_bundle_q": clt["hajek_ratio"],
                "max_abs_y": clt["max_abs_y"],
                "srswor_simulation": clt["srswor_totals"],
                "hajek_loglog_slope": round(decay["loglog_slope"] or 0.0, 4),
                "hajek_endpoints_decrease": decay["endpoints_decrease"],
                "decay_rows": decay["rows"],
                "note": (
                    "The Hajek ratio is a finite-N diagnostic here; the asymptotic "
                    "claim is supported by simulated SRSWOR normality plus the fitted "
                    "O(1/q) decay of the ratio, not asserted."
                ),
            },
        )
    )

    # 5. identical first two moments, different limit law
    law = sample_total_law(design, y)
    variances = exact_variances(design, y)
    block_ks = block_law_ks_to_normal(law)
    same_moments = variances["equal"] and variances["means_equal"]
    checks.append(
        _check(
            "same_first_two_moments",
            "pass" if same_moments else "fail",
            {
                "mean_identity_equal": variances["means_equal"],
                "variance_identity_equal": variances["equal"],
                "variance_closed_form": str(variances["srswor_closed_form"]),
                "variance_block_law": str(variances["block_law"]),
            },
        )
    )
    different_law = float(law["moments"]["skewness"]) > 1.0 and block_ks > 0.05
    checks.append(
        _check(
            "limit_law_differs",
            "pass" if different_law else "fail",
            {
                "block_law_moments": law["moments"],
                "block_law_ks_to_normal": round(block_ks, 6),
                "target": "centered exponential (skewness ~2)",
                "note": "Same mean and variance as the SRSWOR side by check 5; different shape.",
            },
        )
    )

    overall = "PASS" if all(item["status"] != "fail" for item in checks) else "FAIL"
    return _finish(bundle, design, checks, overall, claim)


def _finish(bundle, design, checks, overall, claim) -> Dict[str, object]:
    return {
        "claim_id": bundle_hash(bundle),
        "claim": claim,
        "r": int(bundle.get("r") or 0),
        "design": design.as_dict(),
        "overall": overall,
        "checks": checks,
        "failed_checks": [item["name"] for item in checks if item["status"] == "fail"],
    }


def validate_block_totals(design: Design, w) -> Dict[str, object]:
    """Thin wrapper kept for the tool layer."""
    return solve_block_totals(design, w)


def r2_reference_bundle(q: int = 13) -> Dict[str, object]:
    """The canonical r = 2 regression bundle (Chen 2026, Theorem 4.1 mechanism)."""
    return {
        "id": "r2_projective_plane_q%d" % q,
        "claim": "counterexample",
        "r": 2,
        "design": {"family": "projective_plane", "params": {"q": q}},
        "population": {"method": "centered_exponential_quantiles", "denominator": 1000},
        "options": {"srswor_reps": 20000, "seed": 20261023, "decay_qs": [5, 7, 11, 13, 17]},
    }


def r3_obstruction_bundle(m: int = 4) -> Dict[str, object]:
    """The r = 3 probe: a genuine strength-3 design whose block totals are over-determined."""
    return {
        "id": "r3_hadamard3_m%d" % m,
        "claim": "realizability_obstruction",
        "r": 3,
        "design": {"family": "hadamard3", "params": {"m": m}},
        "population": {"method": "centered_exponential_quantiles", "denominator": 1000},
        "options": {"seed": 20261023},
    }

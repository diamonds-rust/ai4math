"""Deterministic self-test: the evidence the package ships with.

Every entry returns a real computed value, not a restatement of intent. The CLI
``selftest`` command and the unittest suite both drive this module, so the claim
"the toolkit works" always has one implementation behind it.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List

from .algebra import back_solve_closed_form, max_abs, solve_block_totals
from .bundle import r2_reference_bundle, r3_obstruction_bundle, verify_bundle
from .designs import ag_planes, hadamard3, projective_plane, verify_strength
from .exact import srswor_inclusion_prob
from .inclusion import compare_to_srswor, order3_collinear_witness
from .laws import (
    block_law_ks_to_normal,
    centered_rational_quantiles,
    check_srswor_clt,
    exact_variances,
    sample_total_law,
)


def _entry(name: str, ok: bool, detail) -> Dict[str, object]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def run_selftest() -> Dict[str, object]:
    checks: List[Dict[str, object]] = []

    # --- exact arithmetic baseline -----------------------------------------
    checks.append(
        _entry(
            "exact_srswor_probabilities",
            srswor_inclusion_prob(4, 2, 2) == Fraction(1, 6)
            and srswor_inclusion_prob(57, 8, 1) == Fraction(8, 57)
            and srswor_inclusion_prob(57, 8, 2) == Fraction(1, 57)
            and srswor_inclusion_prob(183, 14, 2) == Fraction(1, 183),
            {
                "order2_N57": str(srswor_inclusion_prob(57, 8, 2)),
                "order2_N183": str(srswor_inclusion_prob(183, 14, 2)),
            },
        )
    )

    # --- design families ----------------------------------------------------
    pg = projective_plane(7)
    pg_strength = verify_strength(pg, 2)
    checks.append(
        _entry(
            "projective_plane_is_strength_2",
            pg.v == 57 and pg.b == 57 and pg.block_size == 8 and pg_strength["is_design"],
            {"v": pg.v, "b": pg.b, "k": pg.block_size},
        )
    )
    h3 = hadamard3(4)
    h3_strength = verify_strength(h3, 3)
    checks.append(
        _entry(
            "hadamard3_is_strength_3",
            h3.v == 16 and h3.b == 30 and h3_strength["is_design"]
            and h3_strength["orders"]["3"]["lambda_values"] == [3],
            {"v": h3.v, "b": h3.b, "lambda3": h3_strength["orders"]["3"]["lambda_values"]},
        )
    )
    ag = ag_planes(4)
    ag_strength = verify_strength(ag, 3)
    checks.append(
        _entry(
            "ag_planes_is_strength_3",
            ag.v == 16 and ag_strength["is_design"] and ag_strength["orders"]["3"]["lambda_values"] == [1],
            {"v": ag.v, "b": ag.b, "k": ag.block_size},
        )
    )

    # --- exact order-2 agreement / order-3 failure -------------------------
    order2 = compare_to_srswor(pg, 2)
    checks.append(
        _entry(
            "pg_order2_matches_srswor_exactly",
            order2["match"] and order2["orders"]["2"]["mismatch_count"] == 0,
            {"expected_order2": order2["orders"]["2"]["expected"]},
        )
    )
    witness = order3_collinear_witness(7, True)
    checks.append(
        _entry(
            "pg_order3_fails_exactly",
            witness["agree"] is False
            and witness["collinear_prob"] == "1/57"
            and witness["scattered_prob"] == "0",
            {
                "collinear": witness["collinear_prob"],
                "scattered": witness["scattered_prob"],
                "required": witness["srswor_order3"],
            },
        )
    )
    h3_order3 = compare_to_srswor(h3, 3)
    checks.append(
        _entry(
            "hadamard3_order3_matches_srswor",
            h3_order3["match"],
            {"mismatch_counts": {k: v["mismatch_count"] for k, v in h3_order3["orders"].items()}},
        )
    )

    # --- inverse problem: works for r=2, blocked for r=3 -------------------
    w_pg = centered_rational_quantiles(pg.b, 1000)
    pg_inverse = solve_block_totals(pg, w_pg)
    checks.append(
        _entry(
            "pg_block_totals_invertible",
            bool(pg_inverse["solvable"]) and str(pg_inverse["residual_max_abs"]) == "0",
            {"method": pg_inverse["method"], "residual": pg_inverse["residual_max_abs"]},
        )
    )
    w_h3 = centered_rational_quantiles(h3.b, 1000)
    h3_inverse = solve_block_totals(h3, w_h3)
    checks.append(
        _entry(
            "hadamard3_block_totals_over_determined",
            h3_inverse["solvable"] is False and h3_inverse["rank"] < h3_inverse["augmented_rank"],
            {
                "rank": h3_inverse.get("rank"),
                "augmented_rank": h3_inverse.get("augmented_rank"),
            },
        )
    )

    # --- the r = 2 punchline: identical moments, different law -------------
    q = 13
    pg13 = projective_plane(q)
    y13 = back_solve_closed_form(pg13, centered_rational_quantiles(pg13.b, 1000))["y"]
    variances = exact_variances(pg13, y13)
    law = sample_total_law(pg13, y13)
    checks.append(
        _entry(
            "variance_identity_is_exact",
            variables_equal(variances),
            {"closed_form": str(variances["srswor_closed_form"]), "block_law": str(variances["block_law"])},
        )
    )
    checks.append(
        _entry(
            "block_law_is_non_normal",
            float(law["moments"]["skewness"]) > 1.5 and block_law_ks_to_normal(law) > 0.05,
            {
                "skewness": law["moments"]["skewness"],
                "ks_to_normal": round(block_law_ks_to_normal(law), 6),
            },
        )
    )
    srswor = check_srswor_clt(y13, pg13.block_size, reps=20000)
    checks.append(
        _entry(
            "srswor_side_is_normal",
            srswor["srswor_totals"]["ks_vs_normal"] < 0.05
            and abs(srswor["srswor_totals"]["skewness"]) < 0.3,
            srswor["srswor_totals"],
        )
    )

    # --- the gate must reject false claims ---------------------------------
    false_bundle = {
        "id": "false_r3_counterexample",
        "claim": "counterexample",
        "r": 3,
        "design": {"family": "hadamard3", "params": {"m": 4}},
        "population": {"denominator": 1000},
        "options": {"srswor_reps": 200, "seed": 1},
    }
    verdict = verify_bundle(false_bundle)
    checks.append(
        _entry(
            "gate_rejects_false_r3_counterexample",
            verdict["overall"] == "FAIL" and "block_totals_realizable" in verdict["failed_checks"],
            {"failed": verdict["failed_checks"]},
        )
    )
    wrong_order = {
        "id": "pg_claimed_order3",
        "claim": "order_agreement",
        "r": 3,
        "design": {"family": "projective_plane", "params": {"q": 7}},
        "population": {"denominator": 1000},
        "options": {},
    }
    verdict2 = verify_bundle(wrong_order)
    checks.append(
        _entry(
            "gate_rejects_pg_as_order3_agreement",
            verdict2["overall"] == "FAIL",
            {"failed": verdict2["failed_checks"]},
        )
    )

    # --- the two canonical bundles -----------------------------------------
    r2 = verify_bundle(r2_reference_bundle(13))
    checks.append(
        _entry(
            "r2_bundle_passes",
            r2["overall"] == "PASS" and not r2["failed_checks"],
            {"claim_id": r2["claim_id"], "checks": [(c["name"], c["status"]) for c in r2["checks"]]},
        )
    )
    r3 = verify_bundle(r3_obstruction_bundle(4))
    checks.append(
        _entry(
            "r3_obstruction_bundle_passes",
            r3["overall"] == "PASS",
            {"claim_id": r3["claim_id"], "checks": [(c["name"], c["status"]) for c in r3["checks"]]},
        )
    )

    # --- broader method space ----------------------------------------------
    from .explore import design_search, permutation_search, simulate_design, weight_search

    found = design_search(8, 4, 3, 1)
    checks.append(
        _entry(
            "design_search_finds_3_design",
            found["status"] == "satisfied" and found["block_count"] == 14 and found["verified_strength"],
            {"blocks": found["block_count"], "nodes": found["nodes"]},
        )
    )
    weights = weight_search(hadamard3(4), order=3)
    checks.append(
        _entry(
            "weight_search_rank_nullity",
            weights["status"] == "ok" and weights["rank"] == 30 and weights["nullity"] == 0,
            {"rank": weights.get("rank"), "nullity": weights.get("nullity")},
        )
    )
    permuted = permutation_search(projective_plane(7), trials=4, seed=7)
    checks.append(
        _entry(
            "permutation_search_runs",
            permuted["status"] == "ok" and float(permuted["best"]["max_abs_y"]) > 0,
            {"best_max_abs_y": permuted["best"]["max_abs_y"]},
        )
    )

    # --- route B: affine hyperplanes + bent population ----------------------
    from .bundle import bundle_hash
    from .hyperplane import check_population_first, hyperplane_design, population_first_bundle

    hyper = hyperplane_design(4)
    hyper3 = verify_strength(hyper, 3)
    hyper4 = verify_strength(hyper, 4)
    checks.append(
        _entry(
            "hyperplane_family_is_strength_3_not_4",
            hyper3["is_design"] and not hyper4["is_design"],
            {
                "v": hyper.v,
                "b": hyper.b,
                "k": hyper.block_size,
                "lambda3": hyper3["orders"]["3"]["lambda_values"],
                "order4_uniform": hyper4["is_design"],
            },
        )
    )
    route_b = check_population_first(4, 3)
    checks.append(
        _entry(
            "route_b_gate_passes",
            route_b["overall"] == "PASS",
            {
                "claim_id": bundle_hash(population_first_bundle(4)),
                "checks": [(item["name"], item["status"]) for item in route_b["checks"]],
            },
        )
    )

    # --- Moonshine bridge ---------------------------------------------------
    try:
        from .moonshine_bridge import build_registry, ht_tool_names
        from .tools_impl import HT_HANDLERS

        registry = build_registry()
        names = ht_tool_names(registry)
        dispatched = registry.dispatch(
            "ht_build_design",
            {"family": "projective_plane", "q": 7, "t": 2},
            {"mode": "research", "exposure": {"tools_include": [], "tools_exclude": []}},
        )
        checks.append(
            _entry(
                "moonshine_registry_exposes_ht_tools",
                len(names) == len(HT_HANDLERS) and dispatched.get("is_design") is True,
                {"ht_tools": len(names), "total": len(registry.schemas(mode="research"))},
            )
        )
    except Exception as exc:  # pragma: no cover - depends on the Moonshine checkout
        checks.append(_entry("moonshine_registry_exposes_ht_tools", False, {"error": str(exc)[:160]}))

    passed = sum(1 for item in checks if item["ok"])
    return {
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "overall": "PASS" if passed == len(checks) else "FAIL",
    }


def variables_equal(variances) -> bool:
    return bool(variances["equal"]) and bool(variances["means_equal"])

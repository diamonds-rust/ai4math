"""Provider-callable tool handlers (Moonshine signature: handler(runtime, **kwargs)).

These are the functions Moonshine dispatches to via its tool registry. They are
deliberately thin: all mathematics lives in the sibling modules, so the same
code path is exercised by the CLI, the unit tests and the agent tools.

Every return value is JSON-serialisable (Fractions become strings).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, Optional

from .algebra import back_solve_closed_form, max_abs, mean, solve_block_totals
from .bundle import build_design, verify_bundle
from .designs import ag_planes, hadamard3, projective_plane, verify_strength
from .inclusion import compare_to_srswor, order3_collinear_witness
from .laws import (
    block_law_ks_to_normal,
    centered_rational_quantiles,
    check_srswor_clt,
    exact_variances,
    hajek_decay_study,
    sample_total_law,
)

FAMILIES = ["projective_plane", "hadamard3", "ag_planes", "ag_hyperplanes"]


def _jsonable(value):
    """Recursively convert Fractions/tuples into JSON-friendly objects."""
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _make_design(family: str, q: int, m: int):
    family = str(family or "").strip()
    if family == "projective_plane":
        if q < 2:
            raise ValueError("projective_plane needs q >= 2 (use a prime q for the Singer construction)")
        return projective_plane(int(q))
    if family == "hadamard3":
        if m < 2:
            raise ValueError("hadamard3 needs m >= 2 (v = 2^m, block size v/2)")
        return hadamard3(int(m))
    if family == "ag_planes":
        if m < 2:
            raise ValueError("ag_planes needs m >= 2 (v = 2^m, block size 4)")
        return ag_planes(int(m))
    if family == "ag_hyperplanes":
        from .hyperplane import hyperplane_design

        return hyperplane_design(int(m))
    raise ValueError("family must be one of %r" % (FAMILIES,))


def _population(design, denominator: int):
    """Build the exact centered exponential-quantile block totals and invert them."""
    w = centered_rational_quantiles(design.b, int(denominator))
    return solve_block_totals(design, w)


def ht_build_design(runtime=None, family: str = "", q: int = 0, m: int = 0, t: int = 0) -> Dict[str, object]:
    """Tool: construct a design family and verify its strength exactly."""
    design = _make_design(family, q, m)
    strength_order = int(t) if t else (3 if design.family != "projective_plane" else 2)
    report = verify_strength(design, strength_order)
    return _jsonable(
        {
            "tool": "ht_build_design",
            "status": "ok",
            "design": design.as_dict(),
            "verified_strength": strength_order,
            "is_design": report["is_design"],
            "lambda_profile": {order: entry["lambda_values"] for order, entry in report["orders"].items()},
            "note": (
                "A strength-t design reproduces SRSWOR inclusion probabilities through "
                "order t (Chen 2026, Thm 2.1); order t+1 is where the r = 2 route breaks."
            ),
        }
    )


def ht_inclusion_probs(runtime=None, family: str = "", q: int = 0, m: int = 0, order: int = 2) -> Dict[str, object]:
    """Tool: compute inclusion probabilities and compare them with SRSWOR exactly."""
    design = _make_design(family, q, m)
    order = int(order)
    if order < 1:
        raise ValueError("order must be >= 1")
    report = compare_to_srswor(design, order)
    return _jsonable(
        {
            "tool": "ht_inclusion_probs",
            "status": "ok",
            "match": report["match"],
            "N": design.v,
            "n": design.block_size,
            "B": design.b,
            "order": order,
            "mismatch_counts": {key: entry["mismatch_count"] for key, entry in report["orders"].items()},
            "expected": {key: entry["expected"] for key, entry in report["orders"].items()},
            "examples": report["orders"].get(str(order), {}).get("mismatch_examples", []),
        }
    )


def ht_order3_witness(runtime=None, q: int = 7) -> Dict[str, object]:
    """Tool: exhibit the exact order-3 failure of the r = 2 projective-plane design."""
    witness = order3_collinear_witness(int(q), True)
    witness["tool"] = "ht_order3_witness"
    witness["status"] = "ok"
    return _jsonable(witness)


def ht_solve_population(runtime=None, family: str = "", q: int = 0, m: int = 0, denominator: int = 1000) -> Dict[str, object]:
    """Tool: solve A y = w for a prescribed block-total vector, exactly."""
    design = _make_design(family, q, m)
    result = _population(design, denominator)
    payload: Dict[str, object] = {
        "tool": "ht_solve_population",
        "status": "ok",
        "family": design.family,
        "N": design.v,
        "B": design.b,
        "n": design.block_size,
        "solvable": bool(result.get("solvable")),
        "method": result.get("method", ""),
        "reason": result.get("reason", ""),
        "rank": result.get("rank"),
        "augmented_rank": result.get("augmented_rank"),
        "degrees_of_freedom": result.get("degrees_of_freedom"),
        "residual_max_abs": result.get("residual_max_abs"),
    }
    if result.get("solvable"):
        y = result["y"]
        payload.update(
            {
                "max_abs_y": "%.8f" % float(max_abs(y)),
                "l2_y_squared": str(sum((item * item for item in y), Fraction(0))),
                "mean_y": "%.10f" % float(mean(y)),
            }
        )
    else:
        payload["note"] = (
            "The prescribed block totals are not realisable: rank(A) < rank([A|w]). "
            "For r >= 3 this is the expected structural obstruction, not a tool failure."
        )
    return _jsonable(payload)


def ht_check_srswor_clt(
    runtime=None,
    family: str = "projective_plane",
    q: int = 13,
    m: int = 0,
    reps: int = 20000,
    seed: int = 20261023,
    denominator: int = 1000,
) -> Dict[str, object]:
    """Tool: finite-N SRSWOR CLT diagnostics on the constructed population."""
    design = _make_design(family, q, m)
    result = _population(design, denominator)
    if not result.get("solvable"):
        return _jsonable(
            {
                "tool": "ht_check_srswor_clt",
                "status": "blocked",
                "reason": result.get("reason", ""),
                "solvable": False,
            }
        )
    y = result["y"]
    check = check_srswor_clt(y, design.block_size, reps=int(reps), seed=int(seed))
    check["tool"] = "ht_check_srswor_clt"
    check["status"] = "ok"
    return _jsonable(check)


def ht_sample_total_law(
    runtime=None, family: str = "projective_plane", q: int = 13, m: int = 0, denominator: int = 1000
) -> Dict[str, object]:
    """Tool: exact law of the sample total under block sampling, plus variance identity."""
    design = _make_design(family, q, m)
    result = _population(design, denominator)
    if not result.get("solvable"):
        return _jsonable(
            {
                "tool": "ht_sample_total_law",
                "status": "blocked",
                "solvable": False,
                "reason": result.get("reason", ""),
            }
        )
    y = result["y"]
    law = sample_total_law(design, y)
    variances = exact_variances(design, y)
    return _jsonable(
        {
            "tool": "ht_sample_total_law",
            "status": "ok",
            "family": design.family,
            "N": design.v,
            "B": design.b,
            "moments": law["moments"],
            "ks_to_normal": round(block_law_ks_to_normal(law), 6),
            "same_first_two_moments": variances["equal"] and variances["means_equal"],
            "variance_closed_form": str(variances["srswor_closed_form"]),
            "variance_block_law": str(variances["block_law"]),
            "note": (
                "The block law is computed exactly from the design, never simulated. "
                "Identical mean/variance with a different shape is the r = 2 counterexample."
            ),
        }
    )


def ht_hajek_decay(runtime=None, qs: Optional[list] = None) -> Dict[str, object]:
    """Tool: measure the O(1/q) decay of the finite-N Hajek ratio."""
    qs = [int(item) for item in (qs or [5, 7, 11, 13, 17])]
    study = hajek_decay_study(qs)
    study["tool"] = "ht_hajek_decay"
    study["status"] = "ok"
    return _jsonable(study)


def ht_verify_bundle(runtime=None, bundle: Optional[dict] = None) -> Dict[str, object]:
    """Tool: the deterministic gate. Accepts a bundle dict and returns a verdict."""
    if not isinstance(bundle, dict):
        raise ValueError("bundle must be an object")
    verdict = verify_bundle(bundle)
    verdict["tool"] = "ht_verify_bundle"
    verdict["status"] = "ok"
    return _jsonable(verdict)


def ht_design_search(
    runtime=None,
    v: int = 8,
    k: int = 4,
    t: int = 3,
    lam: int = 1,
    max_nodes: int = 200000,
    time_limit: float = 20.0,
    **extra,
) -> Dict[str, object]:
    """Tool: exact-cover search for an arbitrary t-(v,k,lambda) design.

    The JSON schema names the parameter `lambda`; Python cannot bind that as a
    keyword, so it arrives in `extra` and is mapped onto `lam` here.
    """
    from .explore import design_search

    request = extra.pop("lambda", None)
    if request is not None:
        lam = int(request)
    if extra:
        raise TypeError("unexpected keyword arguments: %s" % ", ".join(sorted(extra)))
    result = design_search(int(v), int(k), int(t), int(lam), int(max_nodes), float(time_limit))
    result["tool"] = "ht_design_search"
    return _jsonable(result)


def ht_weight_search(runtime=None, family: str = "", q: int = 0, m: int = 0, t: int = 3) -> Dict[str, object]:
    """Tool: rank/nullity of inclusion constraints over block weights."""
    design = _make_design(family, q, m)
    from .explore import weight_search

    result = weight_search(design, int(t))
    result["tool"] = "ht_weight_search"
    return _jsonable(result)


def ht_permutation_search(
    runtime=None, family: str = "", q: int = 0, m: int = 0, trials: int = 40, seed: int = 20261023
) -> Dict[str, object]:
    """Tool: search permutations of the prescribed block totals for small max|y|."""
    design = _make_design(family, q, m)
    from .explore import permutation_search

    result = permutation_search(design, int(trials), int(seed))
    result["tool"] = "ht_permutation_search"
    return _jsonable(result)


def ht_simulate_design(
    runtime=None,
    blocks: Optional[list] = None,
    y: Optional[list] = None,
    weights: Optional[list] = None,
    reps: int = 5000,
    seed: int = 20261023,
) -> Dict[str, object]:
    """Tool: Monte-Carlo HT law for an arbitrary block list and weight vector."""
    from .explore import simulate_design

    if not isinstance(blocks, list) or not blocks:
        raise ValueError("blocks must be a non-empty array of integer arrays")
    if not isinstance(y, list) or not y:
        raise ValueError("y must be a non-empty array of numbers")
    result = simulate_design(blocks, y, weights, int(reps), int(seed))
    result["tool"] = "ht_simulate_design"
    return _jsonable(result)


def ht_population_first(runtime=None, m: int = 4, r: int = 3, check_subsets: bool = True) -> Dict[str, object]:
    """Tool: Route B -- affine hyperplanes plus a bent population, then gate the claim."""
    from .bundle import bundle_hash
    from .hyperplane import check_population_first, population_first_bundle

    result = check_population_first(int(m), int(r), check_subsets=bool(check_subsets))
    result["claim_id"] = bundle_hash(population_first_bundle(int(m)))
    result["bundle"] = population_first_bundle(int(m))
    result["tool"] = "ht_population_first"
    result["status"] = "ok"
    return _jsonable(result)


def ht_statement_ledger(
    runtime=None,
    action: str = "list",
    path: str = "",
    statement: str = "",
    kind: str = "proposition",
    status: str = "",
    evidence: Optional[dict] = None,
    depends_on: Optional[list] = None,
    notes: str = "",
    identifier: str = "",
) -> Dict[str, object]:
    """Tool: keep the paper's statements and their provenance in one append-only ledger."""
    from pathlib import Path

    from .ledger import StatementLedger

    resolved = str(path or "").strip()
    if not resolved:
        runtime = runtime or {}
        paths = runtime.get("paths")
        slug = str(runtime.get("project_slug") or "").strip()
        if paths is not None and slug:
            resolved = str(Path(paths.project_workspace_dir(slug)) / "statements.jsonl")
    if not resolved:
        raise ValueError("path is required when there is no active project")

    ledger = StatementLedger(Path(resolved))
    action = str(action or "list").strip().lower()
    if action == "add":
        if not str(statement or "").strip():
            raise ValueError("statement is required for action=add")
        entry = ledger.add(
            statement,
            kind=kind,
            status=status or "unproved",
            evidence=dict(evidence or {}),
            depends_on=list(depends_on or []),
            notes=notes,
            identifier=identifier,
        )
        return _jsonable({"tool": "ht_statement_ledger", "status": "ok", "action": "add", "entry": entry})
    if action == "update":
        if not str(identifier or "").strip():
            raise ValueError("identifier is required for action=update")
        updated = ledger.update(
            identifier,
            status=status or None,
            evidence=dict(evidence or {}) or None,
            notes=notes or None,
            statement=statement or None,
            kind=kind if kind != "proposition" else None,
            depends_on=list(depends_on or []) or None,
        )
        return _jsonable({"tool": "ht_statement_ledger", "status": "ok", "action": "update", "entry": updated})
    if action == "list":
        return _jsonable({"tool": "ht_statement_ledger", "status": "ok", "action": "list", **ledger.list()})
    if action == "check":
        return _jsonable({"tool": "ht_statement_ledger", "status": "ok", "action": "check", **ledger.check()})
    if action == "render":
        return _jsonable({"tool": "ht_statement_ledger", "status": "ok", "action": "render", "markdown": ledger.render()})
    raise ValueError("action must be add / list / check / render")


def ht_typeset_paper(runtime=None, report: str = "", out: str = "", title: str = "", timeout: int = 180) -> Dict[str, object]:
    """Tool: render the Markdown draft as a journal-style PDF."""
    from pathlib import Path

    from .typeset import default_paths, typeset

    resolved = default_paths(runtime)
    report_path = Path(report or resolved["report"])
    out_path = Path(out or resolved["out"])
    if not str(report_path).strip() or str(report_path) == ".":
        raise ValueError("report path is required when there is no active project")
    if not str(out_path).strip():
        out_path = report_path.with_suffix(".pdf")
    result = typeset(report_path, out_path, title=title, timeout=int(timeout))
    result["tool"] = "ht_typeset_paper"
    result["status"] = "ok" if result.get("ok") else "error"
    return _jsonable(result)


def ht_compile_latex(runtime=None, tex: str = "", out: str = "", engine: str = "", runs: int = 2, timeout: int = 300) -> Dict[str, object]:
    """Tool: compile workspace/paper.tex with XeLaTeX and report pages or the first error."""
    from pathlib import Path

    from .latex import compile_tex, default_paths

    resolved = default_paths(runtime)
    tex_path = Path(tex or resolved["tex"])
    out_path = Path(out or resolved["out"])
    if not str(tex_path).strip() or str(tex_path) == ".":
        raise ValueError("tex path is required when there is no active project")
    result = compile_tex(tex_path, out_path, engine=engine, runs=int(runs), timeout=int(timeout))
    result["tool"] = "ht_compile_latex"
    result["status"] = "ok" if result.get("ok") else "error"
    return _jsonable(result)


def ht_order_r_obstruction(runtime=None, m: int = 4, r: int = 4) -> Dict[str, object]:
    """Tool: exact order-r obstruction of the affine-hyperplane design (any r >= 2)."""
    from .hyperplane import order_r_obstruction

    result = order_r_obstruction(int(m), int(r))
    result["tool"] = "ht_order_r_obstruction"
    result["status"] = "ok"
    return _jsonable(result)


def ht_template(runtime=None, template: str = "midterm", out: str = "", force: bool = False) -> Dict[str, object]:
    """Tool: copy a shipped paper template into the project workspace."""
    import shutil
    from pathlib import Path

    repo = Path(__file__).resolve().parent.parent
    choices = {
        "midterm": (repo / "paper" / "template-midterm.tex", "paper.tex"),
        "journal": (repo / "paper" / "template.tex", "paper.tex"),
        "markdown": (repo / "paper" / "template.md", "paper.md"),
    }
    key = str(template or "midterm").strip().lower()
    if key not in choices:
        raise ValueError("template must be one of %s" % ", ".join(sorted(choices)))
    source, default_name = choices[key]
    if not source.exists():
        raise FileNotFoundError("shipped template missing: %s" % source)
    target = Path(out) if out else None
    if target is None:
        runtime = runtime or {}
        paths = runtime.get("paths")
        slug = str(runtime.get("project_slug") or "").strip()
        if paths is None or not slug:
            raise ValueError("out is required when there is no active project")
        target = Path(paths.project_workspace_dir(slug)) / default_name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not force:
        return _jsonable({
            "tool": "ht_template",
            "status": "exists",
            "template": key,
            "out": str(target),
            "bytes": target.stat().st_size,
            "note": "pass force=true to overwrite the existing draft",
        })
    shutil.copy2(source, target)
    return _jsonable({
        "tool": "ht_template",
        "status": "ok",
        "template": key,
        "source": str(source),
        "out": str(target),
        "bytes": target.stat().st_size,
    })


HT_HANDLERS = {
    "ht_build_design": ht_build_design,
    "ht_inclusion_probs": ht_inclusion_probs,
    "ht_order3_witness": ht_order3_witness,
    "ht_order_r_obstruction": ht_order_r_obstruction,
    "ht_solve_population": ht_solve_population,
    "ht_check_srswor_clt": ht_check_srswor_clt,
    "ht_sample_total_law": ht_sample_total_law,
    "ht_hajek_decay": ht_hajek_decay,
    "ht_verify_bundle": ht_verify_bundle,
    "ht_design_search": ht_design_search,
    "ht_weight_search": ht_weight_search,
    "ht_permutation_search": ht_permutation_search,
    "ht_simulate_design": ht_simulate_design,
    "ht_population_first": ht_population_first,
    "ht_statement_ledger": ht_statement_ledger,
    "ht_typeset_paper": ht_typeset_paper,
    "ht_compile_latex": ht_compile_latex,
    "ht_template": ht_template,
}

"""Command line interface: selftest, demos, bundle verification, installation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .algebra import back_solve_closed_form, max_abs, solve_block_totals
from .bundle import r2_reference_bundle, r3_obstruction_bundle, verify_bundle
from .designs import ag_planes, hadamard3, projective_plane, verify_strength
from .inclusion import compare_to_srswor, order3_collinear_witness
from .laws import centered_rational_quantiles, check_srswor_clt, exact_variances, sample_total_law


def _print(title: str, payload) -> None:
    print("\n== %s ==" % title)
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def cmd_designs(args) -> int:
    for family, builder in (
        ("projective_plane q=7", lambda: projective_plane(7)),
        ("hadamard3 m=4", lambda: hadamard3(4)),
        ("ag_planes m=4", lambda: ag_planes(4)),
    ):
        design = builder()
        strength = verify_strength(design, 2 if design.family == "projective_plane" else 3)
        print(
            "%-22s v=%-4d b=%-4d k=%-3d strength=%-2d lambda=%s is_design=%s"
            % (
                family,
                design.v,
                design.b,
                design.block_size,
                strength["strength"],
                {order: entry["lambda_values"] for order, entry in strength["orders"].items()},
                strength["is_design"],
            )
        )
    return 0


def cmd_witness(args) -> int:
    _print("order-3 witness for PG(2,%d)" % args.q, order3_collinear_witness(args.q, True))
    return 0


def cmd_r2(args) -> int:
    bundle = r2_reference_bundle(args.q)
    verdict = verify_bundle(bundle)
    _print("r = 2 counterexample bundle (q=%d)" % args.q, verdict)
    return 0 if verdict["overall"] == "PASS" else 1


def cmd_r3(args) -> int:
    bundle = r3_obstruction_bundle(args.m)
    verdict = verify_bundle(bundle)
    _print("r = 3 obstruction bundle (hadamard3 m=%d)" % args.m, verdict)
    design = hadamard3(args.m)
    w = centered_rational_quantiles(design.b, 1000)
    inversion = solve_block_totals(design, w)
    print(
        "\nInterpretation: the design agrees with SRSWOR through order 3 exactly, but "
        "A y = w has rank %s vs augmented rank %s, so the r = 2 prescription trick does "
        "not transfer. This is the open problem, not a solved case."
        % (inversion.get("rank"), inversion.get("augmented_rank"))
    )
    return 0 if verdict["overall"] == "PASS" else 1


def cmd_law(args) -> int:
    design = projective_plane(args.q)
    w = centered_rational_quantiles(design.b, 1000)
    y = back_solve_closed_form(design, w)["y"]
    law = sample_total_law(design, y)
    variances = exact_variances(design, y)
    clt = check_srswor_clt(y, design.block_size, reps=args.reps, seed=args.seed)
    _print(
        "sample-total law, PG(2,%d)" % args.q,
        {
            "block_law_moments": law["moments"],
            "variance_closed_form_srswor": str(variances["srswor_closed_form"]),
            "variance_block_law": str(variances["block_law"]),
            "variance_identity_holds": variances["equal"],
            "srswor_side": clt["srswor_totals"],
            "hajek_ratio": clt["hajek_ratio"],
            "max_abs_y": clt["max_abs_y"],
        },
    )
    return 0


def cmd_verify(args) -> int:
    if args.file:
        bundle = json.loads(Path(args.file).read_text(encoding="utf-8"))
    elif args.json:
        bundle = json.loads(args.json)
    else:
        print("provide --file or --json", file=sys.stderr)
        return 2
    verdict = verify_bundle(bundle)
    _print("bundle verdict", verdict)
    return 0 if verdict["overall"] == "PASS" else 1


def cmd_tools(args) -> int:
    from .moonshine_bridge import build_registry, ht_tool_names

    registry = build_registry()
    names = [item["name"] for item in registry.schemas(mode="research")]
    print("total tools visible in research mode: %d" % len(names))
    print("ht tools: %s" % ", ".join(ht_tool_names(registry)))
    return 0


def cmd_install(args) -> int:
    from .moonshine_bridge import install_assets

    result = install_assets(Path(args.home))
    _print("assets installed", result)
    return 0


def cmd_patch(args) -> int:
    from .moonshine_bridge import patch_source, verify_patched_tree

    result = patch_source(Path(args.root))
    _print("source patches", result)
    if args.verify:
        check = verify_patched_tree(Path(args.root))
        _print("patched tree verification", check)
        return 0 if check["dispatch_ok"] and len(check["ht_tools"]) == 8 else 1
    return 0


def cmd_selftest(args) -> int:
    from .selftest import run_selftest

    report = run_selftest()
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    else:
        for item in report["checks"]:
            print("[%s] %-34s %s" % ("PASS" if item["ok"] else "FAIL", item["name"], item["detail"]))
        print("\n%d/%d checks passed" % (report["passed"], report["total"]))
        print("overall: %s" % report["overall"])
    return 0 if report["overall"] == "PASS" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ht_moonshine",
        description="Deterministic HT counterexample toolkit for Moonshine (Chen 2026, r >= 3).",
    )
    parser.add_argument("--version", action="version", version="ht_moonshine %s" % __version__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("selftest", help="run the full deterministic check suite")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_selftest)

    p = sub.add_parser("designs", help="build and verify every implemented design family")
    p.set_defaults(func=cmd_designs)

    p = sub.add_parser("witness", help="exact order-3 failure of the r = 2 construction")
    p.add_argument("--q", type=int, default=7)
    p.set_defaults(func=cmd_witness)

    p = sub.add_parser("r2", help="verify the r = 2 counterexample bundle")
    p.add_argument("--q", type=int, default=13)
    p.set_defaults(func=cmd_r2)

    p = sub.add_parser("r3", help="verify the r = 3 obstruction bundle")
    p.add_argument("--m", type=int, default=4)
    p.set_defaults(func=cmd_r3)

    p = sub.add_parser("law", help="exact block law, variance identity and SRSWOR check")
    p.add_argument("--q", type=int, default=13)
    p.add_argument("--reps", type=int, default=20000)
    p.add_argument("--seed", type=int, default=20261023)
    p.set_defaults(func=cmd_law)

    p = sub.add_parser("verify", help="verify a bundle from a JSON file or string")
    p.add_argument("--file")
    p.add_argument("--json")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("tools", help="list the HT tools registered into Moonshine")
    p.set_defaults(func=cmd_tools)

    p = sub.add_parser("install", help="copy HT assets into a Moonshine home directory")
    p.add_argument("--home", required=True)
    p.set_defaults(func=cmd_install)

    p = sub.add_parser("patch", help="patch a Moonshine source tree (idempotent)")
    p.add_argument("--root", required=True)
    p.add_argument("--verify", action="store_true")
    p.set_defaults(func=cmd_patch)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

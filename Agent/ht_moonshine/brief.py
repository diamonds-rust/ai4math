"""The research brief and project rules seeded into a Moonshine home.

Kept as a standalone module so the installer (which seeds the project for the
user's own ``python -m moonshine`` command) and the launcher (which seeds before
running) write exactly the same brief.
"""

from __future__ import annotations

PROBLEM_BRIEF = """# Active problem: HT limit law under fixed-order inclusion-probability agreement

## Conjecture under test

For every fixed integer r, agreement of all inclusion probabilities through order r is
*not* sufficient to force a common limit law for the Horvitz-Thompson estimator.

- Proved for r = 2 by Chen (2026, arXiv:2610.09168), Theorem 4.1, using a
  projective-plane BIBD (strength 2) and a prescribed centered-exponential block law.
- Open for r >= 3. This project attacks r = 3 first.

## Quantifier discipline

r is fixed; N -> infinity with n -> infinity. Attempts where r grows with N, or where
r = N (all inclusion probabilities then determine the design), are not progress.

## What a counterexample must exhibit (5-tuple)

(r; design D1; design D2; population sequence P_N; target law) such that

1. every pi_S with |S| <= r is identical under D1 and D2, verified subset by subset;
2. the D1 sample total has a non-normal limit;
3. the D2 sample total is asymptotically normal;
4. both have the same mean and variance at every N (this is the punchline);
5. all of it holds along one sequence of populations.

## Known structural facts (established in this project, do not re-derive from memory)

- Theorem 2.1 of the paper: a strength-t block design reproduces SRSWOR inclusion
  probabilities through order t. So "order-r agreement" is easy to arrange; the hard part
  is the limit law.
- The r = 2 mechanism needs four things: (i) order-2 agreement, (ii) a square incidence
  matrix with A A^T = (n-1)I + J so that every centered block-total vector w is realisable
  via y = A^T w / (n-1), (iii) the free choice of w (its empirical distribution *is* the
  block sample-total law), (iv) a permutation making max|y_i| = o(1) for the SRSWOR CLT.
- The projective plane is strength 2 only: collinear triples have probability 1/B,
  non-collinear 0, while SRSWOR needs C(n,3)/C(N,3). `ht_order3_witness` returns these
  exact fractions. Do not try to reuse PG(2,q) for r = 3.
- A concrete r = 3 obstruction observed here: the Hadamard 3-(16,8,3) design agrees with
  SRSWOR through order 3 exactly, but its incidence matrix is 30x16, so rank(A) = 16 while
  rank([A|w]) = 17 for generic w: prescribed block totals are not realisable. This is the
  mathematical content of the r = 3 gap, not a tool error.

## Method portfolio (full detail in the ht-method-portfolio skill)

A. Symmetric strength-3 transplant (needs v = b and a closed-form inverse).
B. Non-symmetric inverse: accept B > v, characterise admissible w, choose inside col(A).
C. Weighted designs: replace "one block" by a distribution p over blocks; inclusion
   probabilities constrain sum_j p_j 1[S in B_j] only (`ht_weight_search`).
D. Design search outside the catalogue (`ht_design_search`).
E. Permutation freedom (`ht_permutation_search`).
F. Prove impossibility for a family - a legitimate result.
G. Change the sampling scheme (multistage/rejective/stratified), then re-establish
   order-r agreement and the laws explicitly.

You may also write and run your own Python (run_python_script) for any of these.

## Tool map

| Question | Tool |
|---|---|
| Build and verify a design | ht_build_design / ht_design_search |
| Do inclusion probabilities through r agree? | ht_inclusion_probs |
| Why can PG(2,q) not serve r = 3? | ht_order3_witness |
| Can the prescribed block totals be realised? | ht_solve_population |
| Is the design the only weighting? | ht_weight_search |
| Can a permutation shrink max(abs(y))? | ht_permutation_search |
| What is the exact block-side law? | ht_sample_total_law |
| Is the SRSWOR side normal, and does the Hajek ratio decay? | ht_check_srswor_clt / ht_hajek_decay |
| Screen an arbitrary block list | ht_simulate_design |
| Gate a claim | ht_verify_bundle |

## Success criteria

Either a `ht_verify_bundle` PASS with a `claim_id` (counterexample), or a precisely
recorded obstruction: parameter set, rank deficit, breaking subset family, and which route
might escape. A negative result about a family is a deliverable, not a failure.

## Failure record schema (write into failed_path)

r; design family and parameters (v, b, k, lambda_r, group action); symmetry and rank;
failed_at in {strength_check, pis_match, realizability, srswor_clt, law_target};
witness (first mismatching subset / rank vs augmented rank / ratio); obstruction_class;
next_action.
"""

RULES = """# Project rules: Horvitz-Thompson r >= 3

## Working target

Decide whether agreement of inclusion probabilities through order r = 3 forces a common
HT limit law. Counterexample first; a clean obstruction theorem is the fallback.

## Local conventions

- Exact arithmetic for anything recorded; floats only for diagnostics, always with seed
  and repetition count.
- r is fixed and N -> infinity; never let r grow with N.
- The 5-tuple (r, D1, D2, population, target law) is the unit of progress.
- Route switches must be recorded with the blocker that forced them.

## Priorities

1. Close a 5-tuple or write an obstruction.
2. Keep the design space open: symmetric, non-symmetric, weighted, searched.
3. Never promote a claim without `ht_verify_bundle` (or a script-only label).

## Blocking: read the rank correctly

`rank(A) = 16` for the 30x16 Hadamard design is a **design-level** fact; it does not depend
on which w you chose. The realisable block-total vectors are exactly `col(A)`. Therefore
"the inverse failed" is a statement about `w not in col(A)` only, and it does **not** by
itself kill the counterexample route. The question that matters is: inside `col(A)`, can the
block law still be made non-normal while the population side keeps its CLT? Answer that with
`ht_weight_search` (which weightings are admissible) and `ht_sample_total_law` (what law they
induce), not by re-running the same inverse with a different w.
"""


def seed(home, project_slug: str, force: bool = False) -> dict:
    """Write problem.md, rules.md and the paper templates under <home>/projects/<slug>."""
    import shutil
    from pathlib import Path

    home = Path(home)
    workspace = home / "projects" / project_slug / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    brief = workspace / "problem.md"
    rules = home / "projects" / project_slug / "rules.md"
    rules.parent.mkdir(parents=True, exist_ok=True)
    written = []
    if force or not brief.exists():
        brief.write_text(PROBLEM_BRIEF, encoding="utf-8")
        written.append(str(brief))
    if force or not rules.exists():
        rules.write_text(RULES, encoding="utf-8")
        written.append(str(rules))
    # the agent can only read inside the project, so ship the paper templates here
    repo = Path(__file__).resolve().parent.parent
    for source_name, target_name in (
        ("paper/template.tex", "template.tex"),
        ("paper/template-midterm.tex", "template-midterm.tex"),
        ("paper/template.md", "template.md"),
    ):
        source = repo / source_name
        target = workspace / target_name
        if source.exists() and (force or not target.exists()):
            shutil.copy2(source, target)
            written.append(str(target))
    return {"problem": str(brief), "rules": str(rules), "written": written}

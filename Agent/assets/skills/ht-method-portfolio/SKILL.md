---
name: ht-method-portfolio
description: Seven independent routes to an r >= 3 counterexample, with the signal that each route is blocked.
compatibility: Works in Agent Skills-compatible research runtimes.
allowed-tools: ht_build_design ht_design_search ht_weight_search ht_solve_population ht_permutation_search ht_simulate_design ht_inclusion_probs ht_order3_witness ht_sample_total_law ht_hajek_decay ht_verify_bundle run_python_script
metadata:
  title: HT Method Portfolio
  category: builtin
  tags: research,statistics,sampling,strategy
  skill-standard: agentskills.io/v1
---

# HT Method Portfolio

## Usage Hint
- Use this skill when the default symmetric-design route is blocked, or when you notice you have been trying the same idea repeatedly.
- Pick a route explicitly, state why the others are worse right now, and record the choice as a `big_decisions` note; do not drift between routes silently.

## Summary
- There is no requirement that the r = 3 counterexample look like the r = 2 one. The r = 2 proof needed four ingredients, and each can be replaced independently: (i) order-r agreement, (ii) an inverse that prescribes block totals, (iii) a free choice of population, (iv) a population-side CLT.
- Each route below replaces a different ingredient. A route is "blocked" only with a specific, recorded witness.

## Execution Steps

### Route A — symmetric strength-3 transplant
Replace the r = 2 design by a symmetric strength-3 design (v = b) so that A is square.
- Check: `ht_build_design`, then `ht_solve_population`; a square family gives `closed_form_symmetric` with residual 0.
- Blocked when: no symmetric strength-3 design exists at usable parameters, or the identity `A A^T = (k-lambda)I + lambda J` fails. Record the rank deficit if squareness fails.

### Route B — non-symmetric inverse with consistency constraints
Accept B > v and ask which prescribed block totals are *admissible* (w in col(A)), then choose w inside col(A) that still yields a non-normal law.
- Check: `ht_solve_population` (rank vs augmented rank) then solve for w = A y with chosen y; you are now choosing y first and reading off the law.
- Blocked when: every admissible w produces a law close to normal; quantify with `ht_sample_total_law` + `ht_simulate_design`.

### Route C — weighted designs (generalise "one block")
Replace "select one block uniformly" by "select block j with probability p_j". Inclusion probabilities only constrain the linear system sum_j p_j 1[S subset B_j] = target.
- Check: `ht_weight_search` gives rank, nullity and an explicit alternative weight vector.
- Blocked when: nullity = 0 (unique weighting) *and* the uniform design fails to give a non-normal law — then weights add nothing at this order.

### Route D — design search outside the catalogue
Ask for a t-(v,k,lambda) design directly instead of picking a known family.
- Check: `ht_design_search`; a found design is re-verified by strength profile.
- Blocked when: search returns `infeasible` (real evidence) or `budget_exhausted` (no evidence — raise the budget or change parameters before concluding).

### Route E — exploit the permutation freedom
Keep the design and the block law, move the population by permuting w.
- Check: `ht_permutation_search` reports the best max|y| and Hajek ratio among trials.
- Blocked when: the best ratio stays bounded away from 0 across trials (that is a finite-size symptom, not proof); then the population-side CLT needs a different scaling argument.

### Route F — prove impossibility for a family
Instead of a counterexample, prove that for a class of designs every admissible population forces normality (or that order-r agreement forces the whole design).
- Check: use `ht_weight_search` nullity as a structural invariant, and `ht_build_design` to delimit the class you are proving over.
- Use this when Routes A–E keep producing the same obstruction; a negative result about a family is a real deliverable.

### Route G — change the sampling scheme, not the design
Move away from "one uniform block": multistage, rejective, or stratified schemes whose inclusion probabilities through order r are fixed by construction.
- Check: build the scheme explicitly, then measure with `ht_simulate_design` and only promote via `ht_verify_bundle` if the exact machinery can be extended to it (currently it cannot — say so instead of pretending).

## Tool Calls
- `ht_build_design`, `ht_design_search`: obtain a design and its strength certificate.
- `ht_solve_population`, `ht_permutation_search`: the inverse problem and the free permutation.
- `ht_weight_search`: the weighted-design relaxation (Route C).
- `ht_simulate_design`: screening for schemes outside the exact machinery.
- `run_python_script`: allowed and encouraged for exploration (custom constructions, larger instances, ILP/SAT formulations); a conclusion still needs `ht_*` evidence or an explicit record that it is a script-only result.

## File References
- `projects/<project_slug>/memory/by_type/big_decisions.md`
- `projects/<project_slug>/memory/by_type/failed_path.md`

## Output Contract
- State the chosen route, the ingredient it replaces, the concrete check that decided it, and the witness if blocked.
- When switching routes, write one sentence naming the earlier route and its recorded blocker; never restart from memory.

## Notes
- Route F is legitimate and often the most publishable outcome of a hard attempt; do not treat "no counterexample" as failure if the obstruction is written down precisely.
- `run_python_script` runs inside the active project; keep scripts small, deterministic, and seeded, and save them so the run is reproducible.

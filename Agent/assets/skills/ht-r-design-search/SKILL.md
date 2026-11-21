---
name: ht-r-design-search
description: Enumerate and screening-test strength-r block designs (r >= 3) that could carry a counterexample at fixed order r.
compatibility: Works in Agent Skills-compatible research runtimes.
allowed-tools: ht_order_r_obstruction ht_build_design ht_inclusion_probs ht_solve_population query_memory search_knowledge
metadata:
  title: HT r>=3 Design Search
  category: builtin
  tags: research,designs,statistics,combinatorics
  skill-standard: agentskills.io/v1
---

# HT r >= 3 Design Search

## Usage Hint
- Use this skill inside `design_synthesis` when the question is "which strength-r design should carry the counterexample at order r >= 3".
- Decide with `ht_order_r_obstruction` (does the family even have strength r?) and `ht_solve_population` (can the block totals be prescribed?); never argue for a family from memory.

## Summary
- The r = 2 proof used a symmetric 2-design: `A A^T = (n-1) I + J` makes every centered block-total vector realisable, so the block law can be prescribed.
- For general r the same trick needs a *symmetric* strength-r design (v = b). If no such design exists at the needed size, the inverse problem becomes over-determined and the construction must change.
- The affine-hyperplane family is the worked r = 3 case; it is strength exactly 3 and provably fails for every r >= 4 (use `ht_order_r_obstruction` to see the two different lambda values).

## Execution Steps
1. **Screen strength first.** Call `ht_order_r_obstruction(m=..., r=...)` for the hyperplane family: a single `lambda_values` entry means order-r agreement is possible; two or more means the family cannot carry order r, whatever the population. Record the values as the witness.
2. **Catalogue the candidates** by these properties, in this priority order:
   - strength r (mandatory): known families are 2-designs (projective planes), 3-designs (Hadamard 3-(4u,2u,u-1), affine hyperplanes of F_2^m); for r >= 4 no infinite family is shipped, so a search is required.
   - square incidence matrix (v = b) with a closed-form inverse, because that is what lets you prescribe the block totals.
   - block size large relative to v, so that the population-side Lindeberg condition can hold.
3. **Build it.** `ht_build_design` with the right family/parameters; require `is_design: true` and read the `lambda_profile`.
4. **Confirm order-r agreement exactly.** `ht_inclusion_probs(order=r)`; a t-design certificate is not a substitute for the subset check when the instance is small enough to enumerate.
5. **Measure the inverse problem.** `ht_solve_population`. If `solvable: false`, record `rank` vs `augmented_rank`: that ratio is the quantitative content of the obstruction and the thing to report.
6. **Compare candidate families** on (a) whether order-r agreement holds exactly, (b) the dimension deficit `b - rank(A)`, (c) the block size / sampling fraction. Store the comparison as a `big_decisions` record.
7. **Escalate deliberately.** If every symmetric candidate is over-determined, state the three available escapes and pick one explicitly: drop symmetry and handle consistency constraints; relax "one uniform block" to a probability distribution over candidate blocks; or prove the blocking is unavoidable for this family.

## Tool Calls
- `ht_order_r_obstruction`: exact order-r strength profile of the hyperplane family (the r >= 4 screen).
- `ht_build_design`: construct and verify strength.
- `ht_inclusion_probs`: confirm order-r agreement before spending effort on the population side.
- `ht_solve_population`: the inverse problem; produces either a population or the obstruction.
- `query_memory`, `search_knowledge`: check whether a family has already been tried and how it failed.

## File References
- `projects/<project_slug>/memory/by_type/big_decisions.md`
- `projects/<project_slug>/memory/by_type/failed_path.md`
- `projects/<project_slug>/references/index.jsonl`

## Output Contract
- A candidate table: family, parameters (v, b, k, lambda_r), square or not, `rank(A)`, dimension deficit, order-r agreement (exact), verdict.

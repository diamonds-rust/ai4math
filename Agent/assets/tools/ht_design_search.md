<!--
{
  "name": "ht_design_search",
  "handler": "ht_design_search",
  "description": "Exact-cover backtracking search for an arbitrary t-(v,k,lambda) design, so designs outside the built-in families can still be found and verified.",
  "parameters": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "v": {"type": "integer"},
      "k": {"type": "integer"},
      "t": {"type": "integer"},
      "lambda": {"type": "integer"},
      "max_nodes": {"type": "integer"},
      "time_limit": {"type": "number"}
    },
    "required": ["v", "k", "t"]
  }
}
-->

# Tool: ht_design_search

## Usage Hint
- Use this tool when the counterexample needs a strength-t design that no built-in family provides; do not assume a parameter set is realisable without a found block list.
- ALWAYS report the returned `status`: `infeasible` and `budget_exhausted` are different claims.

## Parameters
- `v`, `k`, `t`, `lambda`: the t-(v,k,lambda) target (keep v small; exact cover is exponential).
- `max_nodes`, `time_limit`: search budget.

## Output
`status` (satisfied / infeasible / budget_exhausted), the `blocks` when found, `verified_strength` and `lambda_profile` from an independent check, plus `nodes` and elapsed time.

## Notes
- `budget_exhausted` is not a proof of non-existence.
- The returned blocks are re-verified with `verify_strength`, so a "found" design cannot be a search artefact.

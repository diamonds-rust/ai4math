<!--
{
  "name": "ht_solve_population",
  "handler": "ht_solve_population",
  "description": "Solve A y = w exactly for a prescribed centered block-total vector, or report the exact obstruction (rank vs augmented rank).",
  "parameters": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "family": {"type": "string", "enum": ["projective_plane", "hadamard3", "ag_planes"]},
      "q": {"type": "integer"},
      "m": {"type": "integer"},
      "denominator": {"type": "integer"}
    },
    "required": ["family"]
  }
}
-->

# Tool: ht_solve_population

## Usage Hint
- ALWAYS use this tool for the "prescribe the block totals, then recover a population" step; never claim a population vector was constructed without its output.
- Use it to distinguish "the totals can be realised" from "the system is over-determined"; the second case is the r >= 3 obstruction and must be recorded as such.

## Parameters
- `family`, `q`, `m`: design spec.
- `denominator`: rational grid for the centered exponential-quantile vector w (default 1000). The grid keeps A y = w checkable in exact arithmetic.

## Output
When solvable: `solvable: true`, `method` (`closed_form_symmetric` when `A A^T = (n-1)I + J` applies, else `gauss_jordan`), `residual_max_abs` (must be 0), `max_abs_y`, `l2_y_squared`, `mean_y`, and `degrees_of_freedom`.
When not: `solvable: false` with `rank`, `augmented_rank` and the reason.

## Notes
- For a symmetric 2-design the closed form is y = A^T w / (n-1); it is verified by a forward application of A, not by trusting the algebra.

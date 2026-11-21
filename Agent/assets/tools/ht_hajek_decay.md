<!--
{
  "name": "ht_hajek_decay",
  "handler": "ht_hajek_decay",
  "description": "Measure the log-log decay of the finite-N Hajek ratio across PG(2,q) designs to test whether the CLT sufficient condition tends to zero.",
  "parameters": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "qs": {"type": "array", "items": {"type": "integer"}}
    },
    "required": ["qs"]
  }
}
-->

# Tool: ht_hajek_decay

## Usage Hint
- Use this tool when the SRSWOR normality claim needs an asymptotic argument rather than a single finite-N number.
- Report the fitted slope and the per-q rows; do not round a slope of -0.4 into "O(1/q)".

## Parameters
- `qs`: list of prime orders (default [5, 7, 11, 13, 17]).

## Output
`rows` with (q, N, n, max_abs_y, hajek_ratio), `loglog_slope`, `endpoints_decrease`, `consistent_with_o_one_over_q`.

## Notes
- `consistent_with_o_one_over_q` means slope <= -0.25 and both endpoints decreasing; it is numerical evidence, not a theorem.
- This is the tool that keeps the r = 2 regression honest at small q, where the finite-N ratio is still far from zero.

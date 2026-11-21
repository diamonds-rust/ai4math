<!--
{
  "name": "ht_check_srswor_clt",
  "handler": "ht_check_srswor_clt",
  "description": "Finite-N SRSWOR CLT diagnostics on the constructed population: exact Hajek ratio, exact max|y|, and a seeded normality check on simulated SRSWOR totals.",
  "parameters": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "family": {"type": "string", "enum": ["projective_plane", "hadamard3", "ag_planes"]},
      "q": {"type": "integer"},
      "m": {"type": "integer"},
      "reps": {"type": "integer"},
      "seed": {"type": "integer"},
      "denominator": {"type": "integer"}
    },
    "required": ["family"]
  }
}
-->

# Tool: ht_check_srswor_clt

## Usage Hint
- ALWAYS use this tool before claiming the SRSWOR side is asymptotically normal; a simulation whose seed and repetition count are not reported here does not count as evidence.
- Use it to read off `hajek_ratio` and `max_abs_y`: the finite-N numbers are diagnostics, not a proof of an asymptotic statement.

## Parameters
- `family`, `q`, `m`: design spec (the population is built from the prescribed block totals).
- `reps`, `seed`: simulation settings, part of the evidence record.
- `denominator`: rational grid for w.

## Output
`max_abs_y`, `hajek_ratio`, `passes_finite_n` (ratio below threshold at this N), `srswor_totals` (reps, seed, skewness, kurtosis, KS distance to normal), and the population mean/variance.

## Notes
- The asymptotic claim needs `ht_hajek_decay`, which measures the O(1/q) decay across design sizes.
- If `solvable` is false upstream, this tool returns `status: blocked` instead of guessing.

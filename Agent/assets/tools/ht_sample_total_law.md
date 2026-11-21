<!--
{
  "name": "ht_sample_total_law",
  "handler": "ht_sample_total_law",
  "description": "Exact law of the HT sample total under block sampling: moments, KS distance to normal, and the exact variance identity against the SRSWOR closed form.",
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

# Tool: ht_sample_total_law

## Usage Hint
- ALWAYS take the block-side distribution from this tool; it is computed exactly from the design, never simulated.
- Use it to prove the punchline: identical first two moments with the SRSWOR estimator, different shape.

## Parameters
- `family`, `q`, `m`: design spec.
- `denominator`: rational grid for w.

## Output
`moments` (mean, sd, skewness, kurtosis), `ks_to_normal`, `same_first_two_moments`, and both exact variances (`variance_closed_form` for SRSWOR, `variance_block_law` for the block design).

## Notes
- For the r = 2 construction the two variances are exactly equal as rationals while the skewness is near 2 (exponential) instead of 0 (normal). That numerical pair is the counterexample, not a narrative about it.

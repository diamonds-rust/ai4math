<!--
{
  "name": "ht_simulate_design",
  "handler": "ht_simulate_design",
  "description": "Monte-Carlo HT law for an arbitrary fixed-size block list and weight vector: screening for designs that are not built in.",
  "parameters": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "blocks": {"type": "array", "items": {"type": "array", "items": {"type": "integer"}}},
      "y": {"type": "array", "items": {"type": "number"}},
      "weights": {"type": "array", "items": {"type": "number"}},
      "reps": {"type": "integer"},
      "seed": {"type": "integer"}
    },
    "required": ["blocks", "y"]
  }
}
-->

# Tool: ht_simulate_design

## Usage Hint
- Use this tool to screen a block list produced by `ht_design_search` (or written by hand) before spending exact arithmetic on it.
- Screening only: any claim that enters the research record must be re-established by the exact tools or by `ht_verify_bundle`.

## Parameters
- `blocks`: array of equal-size arrays of unit indices.
- `y`: the population vector.
- `weights`: optional block-selection probabilities (default uniform; must sum to 1).
- `reps`, `seed`: simulation settings, part of the evidence.

## Output
`moments` (mean, sd, skewness, kurtosis), `ks_vs_normal`, and the run settings.

## Notes
- Useful when the candidate design is not one of the built-in families, so no exact law is available yet.
- Reports a seed; results are reproducible exactly with the same inputs.

<!--
{
  "name": "ht_permutation_search",
  "handler": "ht_permutation_search",
  "description": "Search random permutations of the prescribed block totals for a population with small max|y_i| (the paper's own degree of freedom).",
  "parameters": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "family": {"type": "string", "enum": ["projective_plane", "hadamard3", "ag_planes"]},
      "q": {"type": "integer"},
      "m": {"type": "integer"},
      "trials": {"type": "integer"},
      "seed": {"type": "integer"}
    },
    "required": ["family", "trials"]
  }
}
-->

# Tool: ht_permutation_search

## Usage Hint
- Use this tool when the SRSWOR side needs a smaller max|y_i|: permuting the block totals leaves the block law unchanged and only moves the population.
- Report the best `max_abs_y` and `hajek_ratio` with its trial index and seed; never present a hand-chosen permutation as searched.

## Parameters
- `family`, `q`, `m`: design spec.
- `trials`, `seed`: search budget and seed (both go into the evidence record).

## Output
`status`, the best `{trial, max_abs_y, hajek_ratio, permutation}`, and the number of evaluated trials.

## Notes
- Blocked when the inverse problem itself is unsolvable (non-square design): permutation cannot rescue an over-determined system.
- This is not a simulation: every candidate is evaluated exactly.

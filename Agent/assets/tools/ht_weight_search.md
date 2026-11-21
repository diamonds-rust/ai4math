<!--
{
  "name": "ht_weight_search",
  "handler": "ht_weight_search",
  "description": "Generalise a block design to a probability distribution over candidate blocks: exact rank, nullity and an explicit alternative weight vector for the inclusion-probability constraints through order t.",
  "parameters": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "family": {"type": "string", "enum": ["projective_plane", "hadamard3", "ag_planes"]},
      "q": {"type": "integer"},
      "m": {"type": "integer"},
      "t": {"type": "integer"}
    },
    "required": ["family", "t"]
  }
}
-->

# Tool: ht_weight_search

## Usage Hint
- Use this tool when no symmetric design exists and you want to know whether the design can still be varied: a positive `nullity` means many block-weightings match every inclusion probability through order t.
- Report `rank`, `nullity` and `uniform_weights_feasible`; never claim uniqueness of a design outside a real rank computation.

## Parameters
- `family`, `q`, `m`: a built-in design whose block list defines the constraint columns.
- `t`: order of the inclusion probabilities to constrain (default 3).

## Output
`constraints` (row count), `rank`, `nullity` (= face dimension around the uniform weighting), `uniform_weights_feasible`, and — when nullity > 0 — a `null_direction` and a normalised `alternative_weight_vector` that still matches all constrained inclusion probabilities.

## Notes
- Rows are the exact constraint set sum_j p_j 1[S subset B_j] = C(n,|S|)/C(N,|S|) for every |S| <= t.
- Large v makes the exact rank expensive; the tool refuses above its row cap rather than approximating.

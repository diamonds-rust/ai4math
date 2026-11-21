<!--
{
  "name": "ht_inclusion_probs",
  "handler": "ht_inclusion_probs",
  "description": "Compute exact s-th order inclusion probabilities under block sampling and compare them subset by subset with SRSWOR's C(n,s)/C(N,s).",
  "parameters": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "family": {"type": "string", "enum": ["projective_plane", "hadamard3", "ag_planes"]},
      "q": {"type": "integer"},
      "m": {"type": "integer"},
      "order": {"type": "integer"}
    },
    "required": ["family", "order"]
  }
}
-->

# Tool: ht_inclusion_probs

## Usage Hint
- ALWAYS use this tool to establish that inclusion probabilities through order r agree with SRSWOR; never infer agreement from "it is a t-design, therefore the theorem applies".
- Use it on every candidate: the answer is a mismatch count, and the first few exact mismatching subsets.

## Parameters
- `family`, `q`, `m`: design spec, as in `ht_build_design`.
- `order`: the r in the conjecture (1, 2, 3, ...).

## Output
`match` (all orders pass), `mismatch_counts` per order, `expected` values as exact fractions, and up to five `examples` of mismatching subsets with their exact actual/expected probabilities. Missing subsets are treated as probability zero.

## Notes
- Cost grows like C(N, r); keep N modest or use `ht_build_design` plus the strength certificate for larger designs.

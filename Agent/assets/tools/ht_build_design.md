<!--
{
  "name": "ht_build_design",
  "handler": "ht_build_design",
  "description": "Construct a fixed-size block design (projective plane, Hadamard 3-design, or AG(m,2) planes) and verify exactly that it is a strength-t design.",
  "parameters": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "family": {"type": "string", "enum": ["projective_plane", "hadamard3", "ag_planes", "ag_hyperplanes"]},
      "q": {"type": "integer"},
      "m": {"type": "integer"},
      "t": {"type": "integer"}
    },
    "required": ["family"]
  }
}
-->

# Tool: ht_build_design

## Usage Hint
- ALWAYS build candidate designs with this tool instead of describing them in prose; a design that was not built and strength-checked here does not exist for this project.
- Use it before any inclusion-probability claim: strength t is the precondition, never the conclusion.

## Parameters
- `family`: `projective_plane` (v = q^2+q+1, block size q+1, strength 2), `hadamard3` (v = 2^m, block size v/2, strength 3), `ag_planes` (v = 2^m, block size 4, strength 3), `ag_hyperplanes` (v = 2^m, block size 2^(m-1), strength exactly 3; m even).
- `q`: prime for `projective_plane` (the Singer construction needs GF(q^3)).
- `m`: exponent for `hadamard3` / `ag_planes` / `ag_hyperplanes` (even for the last one).
- `t`: strength to verify; defaults to 2 for `projective_plane` and 3 otherwise.

## Output
`design` (v, b, block size, parameters), `is_design`, and the observed `lambda_profile` per order. A non-uniform profile means the candidate is not a strength-t design and cannot be used.

## Notes
- `projective_plane(q)` is the r = 2 family of Chen (2026). Its strength is 2 only.
- Exact arithmetic throughout; no floating point.

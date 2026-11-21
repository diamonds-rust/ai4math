<!--
{
  "name": "ht_order_r_obstruction",
  "handler": "ht_order_r_obstruction",
  "description": "Exact order-r strength profile of the affine-hyperplane design: which affine dimensions an r-subset can have, the resulting lambda values, and whether order-r inclusion probabilities are constant. Use it to decide whether a candidate family can serve r=4,5,... at all.",
  "parameters": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "m": {"type": "integer"},
      "r": {"type": "integer"}
    },
    "required": ["m", "r"]
  }
}
-->

# Tool: ht_order_r_obstruction

## Usage Hint
- Before spending effort on an r >= 4 counterexample with the hyperplane family, call this with the target `r`: it decides in one exact computation whether that family is a strength-r design at all.
- If `verdict` is `not_a_design_at_order_r`, the family cannot carry an r-order construction; record the `lambda_values` as the witness and switch to a genuine strength-r design (`ht_design_search`).

## Parameters
- `m`: dimension of the ambient space, `N = 2^m` (even m for the bent population, but the counting works for any m >= 2).
- `r`: order of agreement being tested, `2 <= r <= N`.

## Output
- `feasible_affine_dimensions`: every affine dimension `d` an r-subset can realise.
- `rows`: `{affine_dim, points_per_flat, lambda_r}` for each feasible `d`, where `lambda_r = 2^(m-d) - 1`.
- `lambda_values`, `is_design`, `verdict`: order-r agreement requires a single `lambda` value.
- `note`: the interpretation, including that the hyperplane family has strength exactly 3.

## Notes
- `r = 2` gives `d = 1` only; `r = 3` gives `d = 2` only (no three collinear points in `F_2^m`); every `r >= 4` admits at least two dimensions, so the family fails.
- This is a counting certificate, not a sampling experiment; pair it with `ht_inclusion_probs` when a design is available.

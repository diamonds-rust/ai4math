<!--
{
  "name": "ht_population_first",
  "handler": "ht_population_first",
  "description": "Route B (population first): affine-hyperplane design of AG(m,2) plus a bent-function population, with the exact two-point D1 law, the exact D2 hypergeometric law, the variance identity, and a gate verdict.",
  "parameters": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "m": {"type": "integer"},
      "r": {"type": "integer"},
      "check_subsets": {"type": "boolean"}
    },
    "required": ["m"]
  }
}
-->

# Tool: ht_population_first

## Usage Hint
- Use this tool when the design-side order agreement is settled but the r = 2 "prescribe block totals then invert" step is blocked; it constructs the population first and lets the block totals follow.
- ALWAYS report its `overall` and `claim_id`; a PASS here is the only way this construction may enter `verified_conclusion`.

## Parameters
- `m`: even integer, N = 2^m. Requires m >= 4 for the asymptotic evidence (the tool also evaluates m + 2).
- `r`: order under test; use 3.
- `check_subsets`: run the exhaustive subset-by-subset inclusion comparison when N <= 16 (default true).

## Output
- `design`: AG(m,2) affine hyperplanes, v = N, b = 2(N-1), k = N/2, lambda_3 = N/4 - 1.
- `bent_population_construction`: Walsh magnitudes all equal sqrt(N), centered sum 0, sum y^2 = N-1, two-valued y.
- `d1_law_is_two_point`: the D1 HT total is exactly +-sqrt(N) with probability 1/2 each; variance N.
- `same_first_two_moments`: D2 (SRSWOR) variance equals N exactly.
- `d2_law_is_asymptotically_normal`: KS at m and at m+2, requiring the distance to shrink and m+2 below threshold.
- `limit_law_differs`: Rademacher versus normal, with the KS values.
- `claim_id`: the bundle hash, citable.

## Notes
- For even m, sqrt(N) is an integer, so every number is exact rational arithmetic; only the KS distance uses floats.
- The order-4 break (parallelograms vs independent 4-sets) is verified when N <= 16 and stated analytically otherwise; it is what makes the design strength exactly 3.
- This is a *candidate* counterexample for r = 3 built along Route B. A PASS certifies the listed finite-m checks and the two-instance CLT evidence, not a hand-written proof for all m.

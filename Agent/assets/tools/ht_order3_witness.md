<!--
{
  "name": "ht_order3_witness",
  "handler": "ht_order3_witness",
  "description": "Show the exact order-3 failure of the r = 2 projective-plane design: collinear triples have probability 1/B, non-collinear triples 0, SRSWOR needs C(n,3)/C(N,3).",
  "parameters": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "q": {"type": "integer"}
    },
    "required": ["q"]
  }
}
-->

# Tool: ht_order3_witness

## Usage Hint
- Use this tool whenever someone (including you) tries to reuse the projective-plane BIBD for r = 3; it returns the exact witness numbers that kill that route.
- Do not restate this argument from memory: report the fractions the tool returns.

## Parameters
- `q`: prime order of PG(2, q).

## Output
`srswor_order3` (the required value C(n,3)/C(N,3)), `collinear_prob` (1/B), `scattered_prob` (0), the witness triples, and `agree: false`.

## Notes
- This is the concrete reason the r = 2 construction does not transfer to r = 3: a strength-2 design fixes orders <= 2 only.

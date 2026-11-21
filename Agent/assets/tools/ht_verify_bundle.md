<!--
{
  "name": "ht_verify_bundle",
  "handler": "ht_verify_bundle",
  "description": "Deterministic verification gate for a counterexample claim bundle: re-runs design strength, inclusion-probability agreement, block-total realizability, SRSWOR CLT evidence, moment identity and law separation.",
  "parameters": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "bundle": {"type": "object"}
    },
    "required": ["bundle"]
  }
}
-->

# Tool: ht_verify_bundle

## Usage Hint
- ALWAYS route a final or intermediate counterexample claim through this tool; a claim without a PASS verdict from here is a conjecture, not a result.
- Use it before `verify_overall`: `verify_overall` audits the prose, this tool audits the mathematics.

## Parameters
- `bundle`: claim specification with `claim` (`counterexample` | `order_agreement` | `realizability_obstruction`), `r`, `design` {family, params}, `population` {denominator}, and `options` {srswor_reps, seed, decay_qs}.

## Output
`claim_id` (stable hash of the claim), `overall` (PASS/FAIL), and one entry per check with `status` and exact details: `design_is_strength_r`, `pis_match_srswor_through_r`, `block_totals_realizable`, `srswor_clt_evidence`, `same_first_two_moments`, `limit_law_differs`.

## Notes
- For `claim: realizability_obstruction` the `block_totals_realizable` check passes when the obstruction is *confirmed* (no solution), which is the honest r >= 3 outcome.
- Verification is pure replay: no model output is trusted, and the hash makes the claim citable.

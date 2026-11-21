<!--
{
  "name": "ht_statement_ledger",
  "handler": "ht_statement_ledger",
  "description": "Append, list, check or render the statement ledger: every claim in the paper with status gated/derived/cited/unproved, its evidence and its dependencies.",
  "parameters": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "action": {"type": "string", "enum": ["add", "update", "list", "check", "render"]},
      "path": {"type": "string"},
      "statement": {"type": "string"},
      "kind": {"type": "string", "enum": ["definition", "conjecture", "lemma", "proposition", "theorem", "corollary", "remark"]},
      "status": {"type": "string", "enum": ["gated", "derived", "cited", "unproved"]},
      "evidence": {"type": "object"},
      "depends_on": {"type": "array", "items": {"type": "string"}},
      "notes": {"type": "string"},
      "identifier": {"type": "string"}
    },
    "required": ["action"]
  }
}
-->

# Tool: ht_statement_ledger

## Usage Hint
- ALWAYS record a statement in this ledger before writing it into the paper draft; the ledger, not the prose, is the authority on what is proved.
- Use it when drafting, revising, or checking a paper: `check` must return `ok: true` before typesetting.

## Parameters
- `action`: `add` | `update` | `list` | `check` | `render`.
- `path`: ledger file; defaults to `<active project>/workspace/statements.jsonl`.
- `add`: `statement`, `kind`, `status`, `evidence` (e.g. `{"claim_id": "...", "tool": "..."}` or `{"reference": "..."}`), `depends_on`, `notes`, optional `identifier`.
- `update`: `identifier` plus any of `status`, `evidence` (merged), `kind`, `statements`, `notes`, `depends_on`. Use it when a statement was mislabelled, or when a proof turns `unproved` into `derived`.
- `render`: returns the Markdown appendix (table) for the paper.

## Output
- `add`: the stored entry.
- `list`: every entry.
- `check`: counts per status, plus `gated_without_evidence`, `cited_without_reference`, `unproved`, and `ok`.
- `render`: Markdown appendix text.

## Notes
- `gated` without evidence, or `cited` without a reference, makes `check` fail by design; that is the guard against "wrote a result that was never computed".
- `unproved` entries are allowed to stay in the ledger (they become the limitations section), but must not be described as results.

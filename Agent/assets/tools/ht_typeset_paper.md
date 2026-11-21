<!--
{
  "name": "ht_typeset_paper",
  "handler": "ht_typeset_paper",
  "description": "Render the paper draft (workspace/paper.md) into a statistics-journal style PDF and return the page count, byte size and any render error.",
  "parameters": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "report": {"type": "string"},
      "out": {"type": "string"},
      "title": {"type": "string"},
      "timeout": {"type": "integer"}
    },
    "required": []
  }
}
-->

# Tool: ht_typeset_paper

## Usage Hint
- ALWAYS typeset through this tool instead of describing the PDF; it returns `ok`, `pages`, `bytes` and, on failure, the builder's `error` or `stderr_tail`.
- Use it after `ht_statement_ledger(action=check)` returns `ok: true`; if it fails, fix the **markdown**, not the renderer.

## Parameters
- `report`: path to the Markdown draft; defaults to `<active project>/workspace/paper.md`.
- `out`: output PDF path; defaults to `<active project>/workspace/paper.pdf`.
- `title`: optional running head; defaults to the draft's `# ` heading.
- `timeout`: render timeout in seconds (default 180).

## Output
- Success: `ok: true`, `pages`, `bytes`, `out`, `source`, `title`, `python` (which interpreter rendered it), `elapsed_seconds`.
- Failure: `ok: false` plus `error`, or `stderr_tail` when the renderer itself raised.

## Notes
- The renderer is `paper/build_paper.py`; it needs reportlab. When the agent's interpreter lacks it, the tool automatically uses a venv that has it (or `HT_TYPESET_PYTHON`).
- Layout fixes belong in the markdown: use `表 1` lines as table captions, four-space indentation for display formulae, front-matter lines for authors/keywords/MSC.
- A page count that jumps by more than one between nearly identical drafts usually means a table is overflowing; shorten the caption or split the table.

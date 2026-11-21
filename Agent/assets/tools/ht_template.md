<!--
{
  "name": "ht_template",
  "handler": "ht_template",
  "description": "Copy a shipped paper template into the project workspace: midterm (course-report style from 期中报告.tex), journal (statistics-journal style), or markdown.",
  "parameters": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "template": {"type": "string", "enum": ["midterm", "journal", "markdown"]},
      "out": {"type": "string"},
      "force": {"type": "boolean"}
    },
    "required": []
  }
}
-->

# Tool: ht_template

## Usage Hint
- Start a draft with this tool instead of writing a preamble from memory: `template="midterm"` for a course report in the style of `期中报告.tex` (ctex + Times New Roman, 2.5cm margins, Chinese theorem environments, no cover page), `template="journal"` for the statistics-journal style, `template="markdown"` when no LaTeX engine is available.
- It never overwrites an existing draft unless `force=true`.

## Parameters
- `template`: `midterm` (default) | `journal` | `markdown`.
- `out`: destination; defaults to `<active project>/workspace/paper.tex` (or `paper.md` for markdown).
- `force`: overwrite an existing file.

## Output
- `ok`/`exists`, `template`, `source`, `out`, `bytes`; `status="exists"` means the draft was left untouched.

## Notes
- The midterm template deliberately has **no cover page**: centred title, one author/course/date line, then abstract and sections.
- After filling it, compile with `ht_compile_latex`; do not hand-write a new preamble.

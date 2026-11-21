<!--
{
  "name": "ht_compile_latex",
  "handler": "ht_compile_latex",
  "description": "Compile the LaTeX paper draft with XeLaTeX (two passes) and return pages, bytes, engine and the first LaTeX error.",
  "parameters": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "tex": {"type": "string"},
      "out": {"type": "string"},
      "engine": {"type": "string"},
      "runs": {"type": "integer"},
      "timeout": {"type": "integer"}
    },
    "required": []
  }
}
-->

# Tool: ht_compile_latex

## Usage Hint
- Use this tool when a LaTeX engine is available and the draft is `workspace/paper.tex`; it compiles twice and returns `ok`, `pages`, `engine`, and the first `error` from the log.
- On failure, fix the `.tex` at the reported line; do not fall back to hand-waving about the PDF.

## Parameters
- `tex`: source path; defaults to `<active project>/workspace/paper.tex`.
- `out`: PDF path; defaults to `<active project>/workspace/paper.pdf`.
- `engine`: `xelatex` (default), `lualatex`, or `pdflatex`.
- `runs`: compilation passes (default 2, needed for cross-references).
- `timeout`: per-pass timeout in seconds.

## Output
- Success: `ok: true`, `pages`, `bytes`, `out`, `engine`, `log`, `elapsed_seconds`.
- Failure: `ok: false` plus `error` (first `!` block from the log) or the stdout tail.

## Notes
- XeLaTeX is required by the shipped template (xeCJK + fontspec). Do not switch the template to `pdflatex` without replacing those packages.
- Keep the file name free of underscores when compiling by hand (`paper.tex`, not `paper_v1.tex`).
- Cite with `\cite{key}` and list keys in `thebibliography`; every key used must appear there, and every listed work must be one you actually read or verified.

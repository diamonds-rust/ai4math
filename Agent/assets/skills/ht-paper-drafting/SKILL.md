---
name: ht-paper-drafting
description: Turn verified HT findings into a formal paper draft, with a statement ledger that keeps proved, derived, cited and unproved claims separate.
compatibility: Works in Agent Skills-compatible research runtimes.
allowed-tools: ht_statement_ledger ht_template ht_compile_latex ht_typeset_paper ht_verify_bundle ht_population_first ht_build_design ht_inclusion_probs ht_sample_total_law ht_check_srswor_clt ht_hajek_decay verify_overall load_skill_definition lemma-prover direct-proving proof-constructor
metadata:
  title: HT Paper Drafting
  category: builtin
  tags: research,writing,paper,proof
  skill-standard: agentskills.io/v1
---

# HT Paper Drafting

## Usage Hint
- Use this skill when the task is no longer "compute one more number" but "write this up as a paper": it fixes the statement ledger first, then the proofs, then the prose.
- Every statement in the draft must appear in the ledger with a status; a draft whose ledger has `gated` entries without evidence, or `unproved` entries described as results, is rejected before typesetting.

## Summary
- The paper is assembled from four kinds of statements: gated (tool-verified), derived (proved from the above), cited (published), unproved (open). Mixtures are fine; confusion between them is not.
- Proof work is prose work, but each proof must name the statements it consumes, so a reader can audit the chain down to a tool output or a reference.

## Execution Steps

1. **Enumerate statements before writing.** List definitions, the conjecture, then every lemma/proposition you intend to use. For each, call `ht_statement_ledger` with `action=add`:
   - `status=gated` + `evidence={"claim_id": ..., "tool": ...}` when a tool PASS or exact run backs it;
   - `status=cited` + `evidence={"reference": "Author, title, venue, year"}` when it comes from the literature;
   - `status=derived` when it is proved in the paper from earlier entries (list `depends_on`);
   - `status=unproved` when it is only conjectured. Never silently upgrade.
2. **Write the proofs for the `derived` ones.** Use `$lemma-prover` / `$direct-proving` for the hard steps, `$proof-constructor` to order dependencies. Each proof states: assumptions, the statements it consumes (ledger ids), the argument, and the exact statement proved.
3. **Keep the general-m arguments explicit.** For a family result, prove it for the parameter (e.g. all even m), then confirm the finite instances separately; do not let "verified at m = 4, 6" stand in for the family statement.
4. **Assemble the draft** in `workspace/paper.md`, following `paper/template.md`: title, abstract (what is proved, what is candidate), one section per ledger statement with its proof, a limitations section that names the unproved entries, and the ledger appendix produced by `ht_statement_ledger(action=render)`.
5. **Gate before promoting.** Any statement that a reader would call "a result" must be `gated` or `derived`; run `verify_overall` on the prose of the main theorem's proof, and `ht_verify_bundle` on the bundle behind every gated claim.
6. **Run the paper check.** `ht_statement_ledger(action=check)` must return `ok: true`; fix `gated_without_evidence` and `cited_without_reference` before typesetting.
7. **Typeset it yourself.** If a LaTeX engine is present (`xelatex --version` works), start the draft with `ht_template(template="midterm")` for a course report in the style of `期中报告.tex` (ctex + Times New Roman, 2.5cm margins, Chinese theorem environments, no cover page) or `ht_template(template="journal")` for the journal style; fill the sections and the `thebibliography`, then call `ht_compile_latex` and report `ok`, `pages`, and the first `error` on failure. Otherwise call `ht_typeset_paper` on `workspace/paper.md`. Fix layout by editing the source, never the renderer.

## Tool Calls
- `ht_statement_ledger`: add / list / check / render the statement ledger.
- `ht_template`: seed `workspace/paper.tex` from the shipped midterm/journal template.
- `ht_compile_latex`: compile `workspace/paper.tex` with XeLaTeX (two passes) and return pages/errors.
- `ht_typeset_paper`: Markdown → journal-style PDF, used when no LaTeX engine is available.
- `ht_verify_bundle`, `ht_population_first`, `ht_build_design`, `ht_inclusion_probs`, `ht_sample_total_law`, `ht_check_srswor_clt`, `ht_hajek_decay`: produce the evidence behind `gated` entries.
- `verify_overall`: audit a proof's prose (assumption use, computation, logic); it does not create evidence on its own.
- `$lemma-prover`, `$direct-proving`, `$proof-constructor`: the proof machinery for `derived` entries.

## File References
- `workspace/statements.jsonl` — the ledger (append-only).
- `workspace/paper.md` — the draft assembled from the template.
- `memory/by_type/verified_conclusion.md` — the gated claims already promoted.
- `memory/by_type/failed_path.md` — routes that must appear in the limitations section.

## Output Contract
- A draft whose every numeric claim cites a ledger id, and whose every "result" is gated or derived.
- An explicit limitations section listing the `unproved` entries by id, with the missing argument named.
- A ledger `check` that returns `ok: true`, quoted in the reply.

## Notes
- Do not invent references. If a citation is needed but not verified in this session, mark it `cited` with `reference: "TO VERIFY: <what is needed>"`; the check will flag it, and the draft keeps the gap visible.
- The paper may legitimately report a negative/structural result (an obstruction, a family that cannot work). That is a result; write it up with the same rigor.
- Do not claim the conjecture is settled: the abstract must state which instances are gated and which family-level statements are still unproved.

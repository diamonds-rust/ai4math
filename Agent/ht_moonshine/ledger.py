"""Statement ledger: every claim in the paper with its provenance.

The point is to make "what is actually established" a machine-readable object
instead of a matter of prose. Each entry is one statement with a status:

* ``gated``   -- backed by a PASS verdict (claim_id from ht_verify_bundle /
                 ht_population_first) or an exact tool run;
* ``derived`` -- proved in the paper from gated/derived statements, no external
                 input needed;
* ``cited``   -- taken from a published result, with the reference given;
* ``unproved``-- stated, not yet proved; must not be presented as a result.

``check`` refuses to bless a ledger that has a ``gated`` entry without evidence,
and reports the unproved ones so the paper cannot quietly absorb them.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

STATUSES = ("gated", "derived", "cited", "unproved")
KINDS = ("definition", "conjecture", "lemma", "proposition", "theorem", "corollary", "remark")


def _slug(text: str, length: int = 24) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")
    return (cleaned[:length] or "stmt").strip("-")


class StatementLedger(object):
    """Append-only JSONL ledger of statements and their status."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def _read(self) -> List[Dict[str, object]]:
        if not self.path.exists():
            return []
        rows = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
        return rows

    def add(
        self,
        statement: str,
        *,
        kind: str = "proposition",
        status: str = "unproved",
        evidence: Optional[Dict[str, object]] = None,
        depends_on: Optional[List[str]] = None,
        notes: str = "",
        identifier: str = "",
    ) -> Dict[str, object]:
        kind = str(kind).strip().lower()
        status = str(status).strip().lower()
        if kind not in KINDS:
            raise ValueError("kind must be one of %r" % (KINDS,))
        if status not in STATUSES:
            raise ValueError("status must be one of %r" % (STATUSES,))
        rows = self._read()
        identifier = str(identifier or "").strip() or "stmt-%s-%03d" % (_slug(statement), len(rows) + 1)
        if any(row.get("id") == identifier for row in rows):
            raise ValueError("duplicate statement id: %s" % identifier)
        entry = {
            "id": identifier,
            "kind": kind,
            "statement": str(statement).strip(),
            "status": status,
            "evidence": dict(evidence or {}),
            "depends_on": [str(item) for item in list(depends_on or [])],
            "notes": str(notes),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def update(
        self,
        identifier: str,
        *,
        status: Optional[str] = None,
        evidence: Optional[Dict[str, object]] = None,
        notes: Optional[str] = None,
        statement: Optional[str] = None,
        kind: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
    ) -> Dict[str, object]:
        """Revise one entry in place (append-only history stays in git/backups)."""
        rows = self._read()
        target = None
        for row in rows:
            if str(row.get("id")) == str(identifier):
                target = row
                break
        if target is None:
            raise KeyError("unknown statement id: %s" % identifier)
        if status is not None:
            normalized = str(status).strip().lower()
            if normalized not in STATUSES:
                raise ValueError("status must be one of %r" % (STATUSES,))
            target["status"] = normalized
        if kind is not None:
            normalized_kind = str(kind).strip().lower()
            if normalized_kind not in KINDS:
                raise ValueError("kind must be one of %r" % (KINDS,))
            target["kind"] = normalized_kind
        if evidence is not None:
            merged = dict(target.get("evidence") or {})
            merged.update(dict(evidence))
            target["evidence"] = merged
        if notes is not None:
            target["notes"] = str(notes)
        if statement is not None:
            target["statement"] = str(statement)
        if depends_on is not None:
            target["depends_on"] = [str(item) for item in depends_on]
        self.path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
            encoding="utf-8",
        )
        return target

    def list(self) -> Dict[str, object]:
        rows = self._read()
        return {"path": str(self.path), "count": len(rows), "statements": rows}

    def check(self) -> Dict[str, object]:
        rows = self._read()
        by_status: Dict[str, int] = {status: 0 for status in STATUSES}
        gated_without_evidence: List[str] = []
        unproved: List[str] = []
        cited_without_reference: List[str] = []
        for row in rows:
            status = str(row.get("status") or "").strip()
            if status in by_status:
                by_status[status] += 1
            evidence = dict(row.get("evidence") or {})
            if status == "gated" and not evidence:
                gated_without_evidence.append(str(row.get("id")))
            if status == "unproved":
                unproved.append(str(row.get("id")))
            if status == "cited" and not str(evidence.get("reference") or row.get("notes") or "").strip():
                cited_without_reference.append(str(row.get("id")))
        ok = not gated_without_evidence and not cited_without_reference
        return {
            "path": str(self.path),
            "count": len(rows),
            "by_status": by_status,
            "gated_without_evidence": gated_without_evidence,
            "cited_without_reference": cited_without_reference,
            "unproved": unproved,
            "ok": ok,
            "rule": (
                "a gated statement needs evidence (claim_id or exact tool record); "
                "a cited statement needs a reference; unproved statements may stay but "
                "must not be reported as results"
            ),
        }

    def render(self) -> str:
        """Render the ledger as a Markdown appendix for the paper."""
        rows = self._read()
        lines = ["## 附录 A 陈述账本", "", "| id | 类型 | 状态 | 证据 | 陈述 |", "| --- | --- | --- | --- | --- |"]
        for row in rows:
            evidence = dict(row.get("evidence") or {})
            label = str(evidence.get("claim_id") or evidence.get("reference") or evidence.get("tool") or "")
            statement = str(row.get("statement") or "").replace("|", "\\|")
            lines.append(
                "| %s | %s | %s | %s | %s |"
                % (row.get("id"), row.get("kind"), row.get("status"), label, statement)
            )
        return "\n".join(lines) + "\n"

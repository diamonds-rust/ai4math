"""Typeset a Markdown paper draft into a journal-style PDF, from inside the agent.

The renderer lives in ``paper/build_paper.py`` and needs reportlab. The agent's
interpreter may not have it, so this module picks a working interpreter:

1. the current interpreter, if ``reportlab`` imports there;
2. ``$HT_TYPESET_PYTHON``;
3. the DSH office runtime venv (present on this machine);
4. common venv locations under the user profile.

It then runs the builder as a subprocess and returns its JSON report, so a tool
caller sees ``ok``, ``pages``, ``bytes`` and ``error`` instead of a traceback.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
BUILDER = REPO_ROOT / "paper" / "build_paper.py"

OFFICE_VENVS = [
    Path.home() / ".dsh" / "office" / "runtime" / "venv" / "Scripts" / "python.exe",
    Path.home() / ".dsh" / "office" / "runtime" / "venv" / "bin" / "python",
]


def _has_reportlab(python: str) -> bool:
    try:
        result = subprocess.run(
            [python, "-c", "import reportlab, pypdf"],
            capture_output=True, timeout=30,
        )
        return result.returncode == 0
    except Exception:
        return False


def choose_python() -> Dict[str, object]:
    """Return the interpreter that can run the builder, with a reason."""
    candidates: List[str] = []
    if importlib.util.find_spec("reportlab"):
        candidates.append(sys.executable)
    env_python = os.environ.get("HT_TYPESET_PYTHON", "").strip()
    if env_python:
        candidates.append(env_python)
    candidates.extend(str(path) for path in OFFICE_VENVS if path.exists())
    seen = set()
    for python in candidates:
        if python in seen or not Path(python).exists():
            continue
        seen.add(python)
        if _has_reportlab(python):
            return {"python": python, "reason": "reportlab available"}
    raise RuntimeError(
        "no interpreter with reportlab found; install it (python -m pip install reportlab pypdf) "
        "or set HT_TYPESET_PYTHON to one that has it"
    )


def typeset(
    report: Path,
    out: Path,
    title: str = "",
    timeout: int = 180,
) -> Dict[str, object]:
    """Run the builder and return its report; never raises for a render failure."""
    report = Path(report)
    out = Path(out)
    if not report.exists():
        return {"ok": False, "error": "markdown source not found: %s" % report}
    if not BUILDER.exists():
        return {"ok": False, "error": "builder not found: %s" % BUILDER}
    try:
        choice = choose_python()
    except RuntimeError as exc:
        return {"ok": False, "error": str(exc)}
    command = [choice["python"], str(BUILDER), "--report", str(report), "--out", str(out), "--json"]
    if title:
        command.extend(["--title", title])
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    started = time.time()
    try:
        completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", timeout=int(timeout), env=env)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "typesetting timed out after %s s" % timeout, "python": choice["python"]}
    elapsed = round(time.time() - started, 2)
    payload: Optional[Dict[str, object]] = None
    for line in reversed((completed.stdout or "").splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                payload = json.loads(line)
                break
            except json.JSONDecodeError:
                continue
    if payload is None:
        return {
            "ok": False,
            "error": "builder produced no JSON report",
            "returncode": completed.returncode,
            "stderr_tail": (completed.stderr or "")[-800:],
            "python": choice["python"],
        }
    payload.setdefault("python", choice["python"])
    payload["elapsed_seconds"] = elapsed
    # trust our own output path: the child's reported path may be re-encoded
    payload["out"] = str(out)
    payload["ok"] = bool(payload.get("ok")) and out.exists() and out.stat().st_size > 1000
    if not payload["ok"]:
        payload["stderr_tail"] = (completed.stderr or "")[-800:]
    return payload

def default_paths(runtime: Optional[Dict[str, object]]) -> Dict[str, str]:
    """Resolve <project>/workspace/paper.md and paper.pdf when the caller passes nothing."""
    runtime = runtime or {}
    paths = runtime.get("paths")
    slug = str(runtime.get("project_slug") or "").strip()
    if paths is None or not slug:
        return {"report": "", "out": ""}
    workspace = Path(paths.project_workspace_dir(slug))
    return {"report": str(workspace / "paper.md"), "out": str(workspace / "paper.pdf")}

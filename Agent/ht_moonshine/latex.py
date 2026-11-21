"""Compile a LaTeX paper from inside the agent.

The agent writes ``workspace/paper.tex`` from ``paper/template.tex`` (xeCJK +
booktabs + amsthm), then calls this module. We run XeLaTeX twice (cross-refs and
bibliography), read the ``.log`` for the first real error, and report pages.

The engine is discovered with ``shutil.which``; XeLaTeX is required because the
template uses xeCJK and fontspec.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional

ENGINES = ["xelatex", "lualatex", "pdflatex"]


def find_engine(preferred: str = "") -> Optional[str]:
    for name in ([preferred] if preferred else []) + ENGINES:
        path = shutil.which(name)
        if path:
            return path
    return None


def _log_error(log_path: Path) -> str:
    if not log_path.exists():
        return ""
    text = log_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("!") or "Undefined control sequence" in line:
            return "\n".join(lines[index:index + 12]).strip()
    return ""


def _pages_from_log(log_path: Path) -> int:
    """Read "Output written on x.pdf (N pages" from the TeX log."""
    if not log_path.exists():
        return 0
    text = log_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"Output written on .*?\((\d+)\s+page", text)
    return int(match.group(1)) if match else 0


def _page_count(pdf: Path) -> int:
    try:
        from pypdf import PdfReader

        return len(PdfReader(str(pdf)).pages)
    except Exception:
        pass
    try:
        data = pdf.read_bytes()
        objects = data.count(b"/Type /Page") - data.count(b"/Type /Pages")
        return max(0, objects)
    except Exception:
        return 0


def compile_tex(
    tex_path: Path,
    out_pdf: Optional[Path] = None,
    engine: str = "",
    runs: int = 2,
    timeout: int = 300,
) -> Dict[str, object]:
    tex_path = Path(tex_path).expanduser().resolve()
    if not tex_path.exists():
        return {"ok": False, "error": "tex source not found: %s" % tex_path}
    engine_path = find_engine(engine)
    if not engine_path:
        return {"ok": False, "error": "no LaTeX engine found on PATH (xelatex/lualatex/pdflatex)"}
    workdir = tex_path.parent
    produced = tex_path.with_suffix(".pdf")
    log_path = tex_path.with_suffix(".log")
    stdout_tail = ""
    started = time.time()
    for _ in range(max(1, int(runs))):
        try:
            completed = subprocess.run(
                [engine_path, "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", tex_path.name],
                cwd=str(workdir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=int(timeout),
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "latex timed out after %s s" % timeout, "engine": Path(engine_path).name}
        stdout_tail = (completed.stdout or "")[-2000:]
        if completed.returncode != 0:
            break
    pages = _page_count(produced) if produced.exists() else 0
    if not pages:
        pages = _pages_from_log(log_path)
    ok = produced.exists() and pages > 0
    result: Dict[str, object] = {
        "ok": ok,
        "tex": str(tex_path),
        "engine": Path(engine_path).name,
        "pages": pages,
        "elapsed_seconds": round(time.time() - started, 2),
        "log": str(log_path),
    }
    if ok:
        if out_pdf is not None:
            export = Path(out_pdf).expanduser().resolve()
            export.parent.mkdir(parents=True, exist_ok=True)
            if export != produced.resolve():
                shutil.copy2(produced, export)
            result["out"] = str(export)
            result["bytes"] = export.stat().st_size
        else:
            result["out"] = str(produced)
            result["bytes"] = produced.stat().st_size
    else:
        result["error"] = _log_error(log_path) or stdout_tail or "compilation failed"
    return result


def default_paths(runtime: Optional[Dict[str, object]]) -> Dict[str, str]:
    runtime = runtime or {}
    paths = runtime.get("paths")
    slug = str(runtime.get("project_slug") or "").strip()
    if paths is None or not slug:
        return {"tex": "", "out": ""}
    workspace = Path(paths.project_workspace_dir(slug))
    return {"tex": str(workspace / "paper.tex"), "out": str(workspace / "paper.pdf")}

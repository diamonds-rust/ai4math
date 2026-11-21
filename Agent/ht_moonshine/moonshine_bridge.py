"""Moonshine integration: registry subclass, asset install, source patching.

Two integration modes, both exercised by the test-suite:

1. **Subclass mode** (reversible, no source edits): :func:`build_registry`
   returns a ``ToolRegistry`` subclass that loads the HT tool definitions and
   registers the HT handlers. Use it when you want the tools without changing
   Moonshine's own loop.

2. **Patch mode** (what "a modified Moonshine" means): :func:`patch_source`
   edits a *copy* of the Moonshine source tree so that the stock agent gains
   the eight HT tools, three counterexample-pipeline activities, the failure
   hook, and the final-report whitelist entries. Every patch is idempotent and
   validated with ``ast.parse`` afterwards.
"""

from __future__ import annotations

import ast
import importlib
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = REPO_ROOT / "assets"
DEFINITIONS_DIR = ASSETS_DIR / "tools" / "definitions"
SKILLS_DIR = ASSETS_DIR / "skills" / "builtin"
AGENTS_DIR = ASSETS_DIR / "agents" / "builtin"

MARKER = "# --- ht_moonshine patch (idempotent) ---"
END_MARKER = "# --- end ht_moonshine patch ---"

CANDIDATE_ROOTS = [
    REPO_ROOT / "runtime",
    REPO_ROOT / "integration",
]


# --------------------------------------------------------------------- import


def ensure_moonshine_importable(extra_root: Optional[Path] = None) -> Path:
    """Make ``import moonshine`` work and return the directory that provides it."""
    try:
        module = importlib.import_module("moonshine")
        return Path(module.__file__).resolve().parent.parent
    except Exception:
        pass
    candidates = ([Path(extra_root)] if extra_root else []) + CANDIDATE_ROOTS
    for candidate in candidates:
        if candidate and (candidate / "moonshine" / "__init__.py").exists():
            sys.path.insert(0, str(candidate))
            importlib.import_module("moonshine")
            return Path(candidate).resolve()
    raise RuntimeError(
        "moonshine is not importable. Either install it (pip install moonshine) or run the "
        "installer: python integration/install_into_moonshine.py"
    )


def _tool_registry_base():
    ensure_moonshine_importable()
    from moonshine.tools.registry import ToolRegistry  # local import: optional dependency

    return ToolRegistry


def _ht_registry_class():
    base = _tool_registry_base()

    class HTToolRegistry(base):
        """A Moonshine ToolRegistry that also exposes the HT tool family."""

        def _definition_directories(self):
            directories = list(super()._definition_directories())
            if DEFINITIONS_DIR not in directories:
                directories.append(DEFINITIONS_DIR)
            return [path for path in directories if Path(path).exists()]

        def _register_from_markdown(self):
            from .tools_impl import HT_HANDLERS

            self._handler_map.update(HT_HANDLERS)
            return super()._register_from_markdown()

    HTToolRegistry.__name__ = "HTToolRegistry"
    HTToolRegistry.__qualname__ = "HTToolRegistry"
    return HTToolRegistry


def build_registry(home: Optional[Path] = None):
    """Return a registry with the stock tools plus the eight HT tools."""
    registry_class = _ht_registry_class()
    paths = None
    if home is not None:
        from moonshine.moonshine_constants import MoonshinePaths

        paths = MoonshinePaths(Path(home))
    return registry_class(paths)


def ht_tool_names(registry) -> List[str]:
    return sorted(item["name"] for item in registry.schemas(mode="research") if item["name"].startswith("ht_"))


# --------------------------------------------------------------------- assets


def install_assets(home: Path) -> Dict[str, object]:
    """Copy tool definitions, skills and the agent bundle into a Moonshine home."""
    home = Path(home)
    copied: List[str] = []

    target_defs = home / "tools" / "definitions"
    target_defs.mkdir(parents=True, exist_ok=True)
    for source in sorted(DEFINITIONS_DIR.glob("*.md")):
        destination = target_defs / source.name
        shutil.copy2(source, destination)
        copied.append(str(destination.relative_to(home)))

    target_skills = home / "skills" / "installed"
    target_skills.mkdir(parents=True, exist_ok=True)
    # stale slugs from earlier versions: drop them so the agent does not list both
    for stale in ("ht-r3-design-search",):
        stale_dir = target_skills / stale
        if stale_dir.exists():
            shutil.rmtree(stale_dir)
    for skill_dir in sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir()):
        destination = target_skills / skill_dir.name
        destination.mkdir(parents=True, exist_ok=True)
        for source in skill_dir.rglob("*"):
            if source.is_file():
                target = destination / source.relative_to(skill_dir)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                copied.append(str(target.relative_to(home)))

    target_agents = home / "agents" / "installed"
    target_agents.mkdir(parents=True, exist_ok=True)
    for agent_dir in sorted(path for path in AGENTS_DIR.iterdir() if path.is_dir()):
        destination = target_agents / agent_dir.name
        destination.mkdir(parents=True, exist_ok=True)
        for source in agent_dir.rglob("*"):
            if source.is_file():
                target = destination / source.relative_to(agent_dir)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                copied.append(str(target.relative_to(home)))

    return {"home": str(home), "copied": copied, "count": len(copied)}


# -------------------------------------------------------------------- patches


def _apply(path: Path, transform) -> Dict[str, object]:
    """Apply a text transform idempotently, back up once, verify the result still parses."""
    original = path.read_text(encoding="utf-8")
    updated, status = transform(original)
    if status == "applied":
        ast.parse(updated)  # fail loudly rather than leave a broken tree
        backup = path.with_suffix(path.suffix + ".ht-backup")
        if not backup.exists():
            backup.write_text(original, encoding="utf-8")
        path.write_text(updated, encoding="utf-8")
    return {"file": str(path), "status": status}


def _patch_registry_handlers(text: str):
    if "from ht_moonshine.tools_impl import HT_HANDLERS" in text:
        return text, "already_patched"
    anchor = "        self._register_from_markdown()"
    if text.count(anchor) != 1:
        raise RuntimeError("registry.py anchor for handler injection not found exactly once")
    injection = (
        "        %s\n"
        "        try:\n"
        "            from ht_moonshine.tools_impl import HT_HANDLERS as _HT_HANDLERS\n"
        "        except Exception as _exc:  # pragma: no cover\n"
        "            raise RuntimeError(\n"
        "                \"ht_moonshine is not importable; add the Stastistics directory to PYTHONPATH\"\n"
        "            ) from _exc\n"
        "        self._handler_map.update(_HT_HANDLERS)\n"
        "        %s\n"
    ) % (MARKER + " handlers", END_MARKER)
    return text.replace(anchor, injection + anchor, 1), "applied"


def _patch_unhide_failed_path(text: str):
    if '"record_failed_path",\n            "store_conclusion"' not in text and text.count('"record_failed_path",') == 1:
        # already unhidden
        return text, "already_patched"
    anchor = (
        '            "record_solve_attempt",\n'
        '            "record_failed_path",\n'
        '            "store_conclusion",'
    )
    if text.count(anchor) != 1:
        return text, "anchor_missing"
    replacement = (
        '            "record_solve_attempt",\n'
        '            # ht_moonshine: record_failed_path stays visible in research mode so\n'
        '            # structured failure records are written deliberately, not only auto-captured.\n'
        '            "store_conclusion",'
    )
    return text.replace(anchor, replacement, 1), "applied"


HT_ACTIVITY_BLOCK = '''

%s
HT_ACTIVITIES = ["design_synthesis", "population_backsolve", "limit_law_check"]
for _ht_activity in HT_ACTIVITIES:
    if _ht_activity not in PROBLEM_SOLVING_ACTIVITIES:
        PROBLEM_SOLVING_ACTIVITIES.append(_ht_activity)
ACTIVITIES_BY_STAGE["problem_solving"] = PROBLEM_SOLVING_ACTIVITIES
RESEARCH_ACTIVITY_ORDER = PROBLEM_DESIGN_ACTIVITIES + PROBLEM_SOLVING_ACTIVITIES
RESEARCH_ACTIVITY_ENUM = RESEARCH_ACTIVITY_ORDER + ["stay"]
try:
    RESEARCH_WORKFLOW_UPDATE_SCHEMA["properties"]["recommended_next_activity"]["enum"] = RESEARCH_ACTIVITY_ENUM
except Exception:
    pass
ACTIVITY_SPECS.update({
    "design_synthesis": {
        "stage": "problem_solving",
        "label": "DesignSynthesis",
        "goal": "Build and strength-verify candidate block designs whose inclusion probabilities through order r match SRSWOR.",
        "skills": ["ht-counterexample-protocol", "ht-r-design-search"],
        "tools": ["ht_build_design", "ht_inclusion_probs", "ht_order3_witness"],
        "good_outputs": ["verified design (v, b, k, lambda profile)", "exact inclusion-probability report"],
    },
    "population_backsolve": {
        "stage": "problem_solving",
        "label": "PopulationBacksolve",
        "goal": "Prescribe block totals and solve A y = w exactly, or record the exact rank obstruction.",
        "skills": ["ht-counterexample-protocol"],
        "tools": ["ht_solve_population"],
        "good_outputs": ["population vector with residual 0", "or rank/augmented-rank obstruction"],
    },
    "limit_law_check": {
        "stage": "problem_solving",
        "label": "LimitLawCheck",
        "goal": "Compare the exact block-sample-total law with the SRSWOR side and verify the first-two-moment identity.",
        "skills": ["ht-counterexample-protocol"],
        "tools": ["ht_sample_total_law", "ht_check_srswor_clt", "ht_hajek_decay", "ht_verify_bundle"],
        "good_outputs": ["exact law moments", "variance identity", "Hajek decay evidence", "bundle verdict"],
    },
})
NODE_SPECS = ACTIVITY_SPECS
SKILL_ACTIVITY_HINTS.update({
    "ht-counterexample-protocol": "solver_branching",
    "ht-r-design-search": "design_synthesis",
})
%s
''' % (MARKER + " activities", END_MARKER)


def _patch_activities(text: str):
    if "HT_ACTIVITIES" in text and MARKER in text:
        return text, "already_patched"
    return text + HT_ACTIVITY_BLOCK, "applied"


def _patch_report_whitelist(text: str):
    if '"ht_verify_bundle",' in text:
        return text, "already_patched"
    anchor = '        important_tools = {\n            "assess_problem_quality",'
    if text.count(anchor) != 1:
        return text, "anchor_missing"
    replacement = (
        '        important_tools = {\n'
        '            # ht_moonshine: keep HT tool evidence in the final report\n'
        '            "ht_build_design",\n'
        '            "ht_inclusion_probs",\n'
        '            "ht_order3_witness",\n'
        '            "ht_solve_population",\n'
        '            "ht_check_srswor_clt",\n'
        '            "ht_sample_total_law",\n'
        '            "ht_hajek_decay",\n'
        '            "ht_verify_bundle",\n'
        '            "assess_problem_quality",'
    )
    return text.replace(anchor, replacement, 1), "applied"


def package_root_of(root: Path) -> Path:
    """Return the directory that holds ``tools/`` and ``agent_runtime/``.

    Handles both layouts: ``<root>/moonshine/...`` (copy) and ``<root>/...``
    where ``root`` itself is the package (editable install).
    """
    root = Path(root)
    nested = root / "moonshine"
    return nested if (nested / "tools" / "registry.py").exists() else root


def patch_source(root: Path) -> Dict[str, object]:
    """Patch a Moonshine source tree (copy layout or editable-install layout)."""
    root = Path(root)
    package = package_root_of(root)
    registry = package / "tools" / "registry.py"
    workflow = package / "agent_runtime" / "research_workflow.py"
    for path in (registry, workflow):
        if not path.exists():
            raise FileNotFoundError("not a Moonshine source tree: %s" % path)
    results = [
        _apply(registry, _patch_registry_handlers),
        _apply(registry, _patch_unhide_failed_path),
        _apply(workflow, _patch_activities),
        _apply(workflow, _patch_report_whitelist),
    ]
    return {"root": str(root), "package_root": str(package), "patches": results}


def import_moonshine_from(package_dir: Path):
    """Import the package ``moonshine`` and require it to resolve to ``package_dir``.

    The import name is always ``moonshine``; ``package_dir`` is the directory that
    holds ``__init__.py`` -- either ``<root>/moonshine`` (copy layout) or the
    editable-install source root (whose folder may be named anything, e.g.
    ``Moonshine-main``). A stray ``moonshine`` directory on sys.path (such as the
    helper junction under ``integration/``) can shadow the intended installation,
    so conflicting entries are dropped and the result is verified.
    """
    package_dir = Path(package_dir).resolve()
    for name in list(sys.modules):
        if name == "moonshine" or name.startswith("moonshine."):
            del sys.modules[name]
    for entry in list(sys.path):
        if not entry:
            continue
        candidate = Path(entry) / "moonshine"
        try:
            if candidate.exists() and candidate.resolve() != package_dir:
                sys.path.remove(entry)
        except OSError:
            continue
    if package_dir.name == "moonshine":
        parent = str(package_dir.parent)
        if parent not in sys.path:
            sys.path.insert(0, parent)
    module = importlib.import_module("moonshine")
    found = Path(module.__file__).resolve().parent
    if found != package_dir:
        raise RuntimeError(
            "imported moonshine from %s, expected %s; install the toolkit/environment so that "
            "the package resolves to that tree (editable install or patched copy)" % (found, package_dir)
        )
    return module


def verify_patched_tree(root: Path, home: Optional[Path] = None) -> Dict[str, object]:
    """Import a patched tree and prove the HT tools are registered and callable.

    Supports both layouts Moonshine ships with:

    * ``root/moonshine/...``  (the copy produced by the installer),
    * ``root/...`` with ``app.py`` at the top level (an editable install, where
      setuptools maps the package name ``moonshine`` onto ``root`` itself).

    Pass ``home`` to load the tool definitions installed via
    :func:`install_assets`; without it only the packaged definitions exist and no
    HT tool can be visible.
    """
    root = Path(root)
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    package_dir = package_root_of(root)
    copy_layout = (root / "moonshine" / "app.py").exists()
    module = import_moonshine_from(package_dir)
    from moonshine.tools.registry import ToolRegistry

    module_path = Path(module.__file__).resolve().parent
    paths = None
    if home is not None:
        from moonshine.moonshine_constants import MoonshinePaths

        paths = MoonshinePaths(Path(home))
    registry = ToolRegistry(paths)
    names = [item["name"] for item in registry.schemas(mode="research")]
    ht_names = sorted(name for name in names if name.startswith("ht_"))
    result = registry.dispatch(
        "ht_build_design",
        {"family": "projective_plane", "q": 7, "t": 2},
        {"mode": "research", "exposure": {"tools_include": [], "tools_exclude": []}},
    )
    return {
        "root": str(root),
        "layout": "copy" if copy_layout else "installed-package",
        "moonshine_module": str(module_path),
        "home": str(home) if home is not None else "",
        "tool_count": len(names),
        "ht_tools": ht_names,
        "dispatch_ok": result.get("status") == "ok" and result.get("is_design") is True,
        "dispatch_design": result.get("design"),
    }


RECOMMENDED_OVERRIDES = {
    "agent": {
        "max_tool_rounds": 14,
        "max_tool_calls_per_round": 24,
        "verification_dimension_review_count": 2,
        "research_max_iterations": 120,
    },
    "context": {
        "compression_threshold_tokens": 220000,
        "history_compression_token_budget": 110000,
    },
}


def write_settings(home: Path, default_mode: Optional[str] = None) -> Dict[str, object]:
    """Merge HT-friendly agent/context settings into a Moonshine home.

    Non-destructive by design: an existing settings.json keeps every section it
    already has (provider, credentials env, exposure, ...). Only the keys listed
    in :data:`RECOMMENDED_OVERRIDES` are updated, plus ``default_mode`` when the
    caller asks for it.
    """
    import json

    home = Path(home)
    ensure_moonshine_importable()
    from moonshine.moonshine_constants import default_config

    config = default_config()
    for section, values in RECOMMENDED_OVERRIDES.items():
        target = config.setdefault(section, {})
        target.update(values)
    config_dir = home / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    path = config_dir / "settings.json"
    preserved_provider = None
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        preserved_provider = dict(existing.get("provider") or {})
        for section, values in RECOMMENDED_OVERRIDES.items():
            existing.setdefault(section, {}).update(values)
        config = existing
    if default_mode:
        config["default_mode"] = str(default_mode)
    path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "path": str(path),
        "overrides": RECOMMENDED_OVERRIDES,
        "default_mode": config.get("default_mode"),
        "provider_preserved": preserved_provider is not None,
        "provider_model": (config.get("provider") or {}).get("model", ""),
    }

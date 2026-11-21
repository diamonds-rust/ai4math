#!/usr/bin/env python
"""Run the HT research agent: patched Moonshine, your provider, your iterations.

Works against either layout:

* a portable copy produced by ``integration/install_into_moonshine.py``
  (``--root .../runtime/moonshine-src``), or
* an editable install you already use, after ``--inplace`` patching
  (``--root "C:\\Users\\<you>\\Desktop\\Moonshine-main"``).

Commands: ``doctor`` / ``config`` / ``run`` / ``ask`` / ``shell``.

Typical use against an existing installation::

    python run_ht_agent.py --root "C:\\Users\\<you>\\Desktop\\Moonshine-main" ^
        --home "C:\\Users\\<you>\\Desktop\\moonshine-data" doctor
    python run_ht_agent.py --root ... --home ... run --iterations 40

Environment variables: ``HT_AGENT_ROOT``, ``HT_AGENT_HOME``, ``HT_AGENT_BASE_URL``,
``HT_AGENT_MODEL``, ``HT_AGENT_API_KEY_ENV``.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from ht_moonshine.brief import seed as seed_brief  # noqa: E402

DEFAULT_ROOT = HERE / "runtime" / "moonshine-src"
DEFAULT_HOME = DEFAULT_ROOT / "home"
DEFAULT_PROJECT = "ht_r3"
DEFAULT_AGENT = "ht-researcher"


# --------------------------------------------------------------------- bootstrap


def bootstrap(root: Path) -> str:
    """Put the patched Moonshine on sys.path (or confirm the editable install)."""
    root = Path(root)
    if (root / "moonshine" / "app.py").exists():
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        return "copy"
    if (root / "app.py").exists():
        from ht_moonshine.moonshine_bridge import import_moonshine_from

        try:
            import_moonshine_from(root)
        except Exception as exc:  # editable install missing from this interpreter
            raise SystemExit(
                "cannot import moonshine from %s in this interpreter (%s).\n"
                "activate the environment where Moonshine is installed, or use --root <patched copy>."
                % (root, exc)
            )
        return "installed"
    raise SystemExit(
        "not a Moonshine source tree: %s\n"
        "expected <root>/moonshine/app.py (copy) or <root>/app.py (editable install)" % root
    )


def load_app(root: Path, home: Path):
    bootstrap(root)
    from moonshine.app import MoonshineApp

    return MoonshineApp(str(home))


def seed_project(app, project_slug: str, force: bool = False) -> dict:
    """Write the problem brief and project rules if absent (or when forced)."""
    seeded = seed_brief(app.paths.home, project_slug, force=force)
    app.ensure_project(project_slug)
    return seeded


def _provider_state(app) -> dict:
    provider = app.config.provider
    api_key_env = str(getattr(provider, "api_key_env", "") or "")
    return {
        "type": getattr(provider, "type", ""),
        "model": getattr(provider, "model", ""),
        "base_url": getattr(provider, "base_url", ""),
        "api_key_env": api_key_env,
        "api_key_present": bool(api_key_env and os.environ.get(api_key_env)),
        "verification_inherits_main": bool(getattr(app.config.verification_provider, "inherit_from_main", True)),
    }


# ------------------------------------------------------------------------ commands


def cmd_doctor(args) -> int:
    layout = bootstrap(Path(args.root))
    app = load_app(Path(args.root), Path(args.home))
    seeding = seed_project(app, args.project)
    provider = _provider_state(app)

    agent = app.agent_manager.get_agent(args.agent)
    skills = app.skill_manager.list_skills()
    skill_slugs = [item["slug"] for section in skills.values() for item in section]
    ht_skills = sorted(slug for slug in skill_slugs if slug.startswith("ht-"))

    schemas = app.tool_registry.schemas(mode="research")
    names = [item["name"] for item in schemas]
    ht_tools = sorted(name for name in names if name.startswith("ht_"))

    state = app.start_shell_state(mode="research", project_slug=args.project, agent_slug=args.agent)

    checks = {
        "agent_profile_found": agent is not None,
        "ht_skills_present": len(ht_skills) >= 3,
        "ht_tools_present": len(ht_tools) >= 12,
        "provider_configured": provider["type"] != "offline",
        "api_key_visible": provider["api_key_present"] or not provider["api_key_env"],
        "project_seeded": Path(seeding["problem"]).exists(),
    }

    module = importlib.import_module("moonshine")
    report = {
        "layout": layout,
        "moonshine_module": str(Path(module.__file__).resolve().parent),
        "root": str(Path(args.root)),
        "home": str(app.paths.home),
        "provider": provider,
        "agent": {
            "slug": args.agent,
            "found": agent is not None,
            "title": agent.title if agent else "",
            "path": agent.path if agent else "",
            "prompt_chars": len(agent.runtime_body()) if agent else 0,
        },
        "skills": {"count": len(skill_slugs), "ht": ht_skills},
        "tools": {"count": len(names), "ht": ht_tools},
        "project": {
            "slug": state.project_slug,
            "session_id": state.session_id,
            "agent_slug": state.agent_slug,
            "problem_file": seeding["problem"],
        },
        "checks": checks,
        "ready": all(checks.values()),
    }
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("layout    : %s (%s)" % (layout, report["moonshine_module"]))
        print("home      : %s" % report["home"])
        print("provider  : %s / %s (key env %s, present=%s)" % (
            provider["type"], provider["model"], provider["api_key_env"], provider["api_key_present"]))
        print("agent     : %s found=%s prompt_chars=%s" % (
            args.agent, report["agent"]["found"], report["agent"]["prompt_chars"]))
        print("skills    : %d total, ht=%s" % (len(skill_slugs), ", ".join(ht_skills) or "(none)"))
        print("tools     : %d total, ht=%d" % (len(names), len(ht_tools)))
        print("project   : %s (session %s, agent %s)" % (state.project_slug, state.session_id, state.agent_slug))
        print("brief     : %s" % seeding["problem"])
        for name, ok in checks.items():
            print("check     : [%s] %s" % ("ok" if ok else "MISSING", name))
        print("ready     : %s" % ("yes" if report["ready"] else "no"))
        if not provider["api_key_present"] and provider["api_key_env"]:
            print("\nnote      : %s is not in this process's environment; Moonshine loads its"
                  " credentials file at startup, so check `provider --show` in the same shell."
                  % provider["api_key_env"])
    return 0 if report["ready"] else 1


def cmd_config(args) -> int:
    app = load_app(Path(args.root), Path(args.home))
    result = app.configure_openai_compatible(
        base_url=args.base_url,
        model=args.model,
        api_key=args.api_key or "",
        api_key_env=args.api_key_env,
        stream=not args.no_stream,
        temperature=args.temperature,
        structured_output_format=args.structured_output_format,
        timeout_seconds=args.timeout,
        target="main",
    )
    app.set_verification_provider_inherit_main(True)
    if args.api_key:
        os.environ[args.api_key_env] = args.api_key
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("\nprovider configured; verification inherits the main provider.")
    print("next: python %s --root %s --home %s doctor" % (Path(sys.argv[0]).name, args.root, args.home))
    return 0


class StreamPrinter(object):
    """Turn token-by-token deltas into whole paragraphs.

    Moonshine emits one delta per token chunk; printing each on its own line is the
    "one word per line" flood. Both ``text_delta`` and ``reasoning_delta`` are
    buffered here and emitted as wrapped paragraphs at sentence, line or size
    boundaries. Reasoning output can be switched off entirely.
    """

    PUNCT = "。！？；：.!?;:"

    def __init__(self, prefix: str, enabled: bool = True, width: int = 100,
                 max_chars: int = 700):
        self.prefix = prefix
        self.enabled = bool(enabled)
        self.width = max(40, int(width))
        self.max_chars = max(200, int(max_chars))
        self.buffer = ""
        self.opened = False

    def feed(self, text: str) -> None:
        if not self.enabled or not text:
            return
        self.buffer += text
        if self._should_flush():
            self.flush()

    def _should_flush(self) -> bool:
        stripped = self.buffer.rstrip()
        if not stripped:
            return False
        if "\n" in self.buffer:
            return True
        if stripped[-1] in self.PUNCT:
            return True
        return len(self.buffer) >= self.max_chars

    def flush(self) -> None:
        if not self.enabled:
            self.buffer = ""
            return
        text = " ".join(self.buffer.split())
        self.buffer = ""
        if not text:
            return
        import textwrap

        body = textwrap.fill(text, width=self.width - len(self.prefix) - 1)
        lines = body.splitlines() or [""]
        print("%s %s" % (self.prefix, lines[0]), flush=True)
        for line in lines[1:]:
            print(" " * (len(self.prefix) + 1) + line, flush=True)

    def close(self) -> None:
        self.flush()


class ReasoningPrinter(StreamPrinter):
    """Backward-compatible reasoning printer: one header, wrapped paragraphs, opt-in."""

    def __init__(self, enabled: bool, width: int = 100, flush_at: int = 900):
        super(ReasoningPrinter, self).__init__(
            "[reasoning]", enabled=enabled, width=width, max_chars=flush_at)
        self.opened = False

    def flush(self) -> None:
        if not self.enabled:
            self.buffer = ""
            return
        text = " ".join(self.buffer.split())
        self.buffer = ""
        if not text:
            return
        import textwrap

        if not self.opened:
            print("[reasoning]", flush=True)
            self.opened = True
        print(textwrap.fill(text, width=self.width), flush=True)

    def close(self) -> None:
        self.flush()
        if self.opened:
            print("[/reasoning]", flush=True)
            self.opened = False


def reasoning_enabled(args) -> bool:
    """Reasoning is opt-in, and ``--quiet`` always wins over ``--show-reasoning``."""
    return bool(getattr(args, "show_reasoning", False)) and not bool(getattr(args, "quiet", False))


def cmd_run(args) -> int:
    app = load_app(Path(args.root), Path(args.home))
    seed_project(app, args.project)
    state = app.start_shell_state(mode="research", project_slug=args.project, agent_slug=args.agent)
    prompt = args.prompt or ""
    if getattr(args, "prompt_file", ""):
        prompt_path = Path(args.prompt_file).expanduser()
        if not prompt_path.exists():
            raise SystemExit("prompt file not found: %s" % prompt_path)
        # utf-8-sig tolerates the BOM that Windows PowerShell 5.1 writes with -Encoding utf8
        prompt = prompt_path.read_text(encoding="utf-8-sig")
    if not prompt:
        prompt = (
            "Begin the research programme on the conjecture in workspace/problem.md. "
            "Work autonomously: build and strength-verify a design, check order-r inclusion "
            "probabilities exactly, attempt the block-total inverse, and either close a "
            "counterexample 5-tuple or record the precise obstruction. Gate every claim with "
            "ht_verify_bundle; write failed_path records with exact witnesses."
        )
    tool_calls = 0
    finals = 0
    reasoning_chunks = 0
    reasoning_chars = 0
    printer = ReasoningPrinter(reasoning_enabled(args))
    text_printer = StreamPrinter("[text]", enabled=True, width=args.width)
    for event in app.run_research_autopilot_events(prompt, state, max_iterations=args.iterations):
        raw_text = str(getattr(event, "text", "") or "")
        text = raw_text.strip().replace("\n", " ")
        kind = str(getattr(event, "type", ""))
        if kind in {"reasoning_delta", "reasoning"}:
            reasoning_chunks += 1
            reasoning_chars += len(raw_text)
            printer.feed(raw_text)
            continue
        if kind == "text_delta":
            printer.close()
            text_printer.feed(raw_text)
            continue
        printer.close()
        text_printer.close()
        if kind == "tool_result":
            tool_calls += 1
        if kind == "final":
            finals += 1
        if args.quiet and kind in {"status", "tool_result"}:
            continue
        print("[%s] %s" % (kind, text[: args.width]))
    printer.close()
    text_printer.close()
    project = app.paths.project_dir(state.project_slug)
    print("\n--- run finished ---")
    print("project     : %s" % project)
    print("tool calls  : %d" % tool_calls)
    print("turns       : %d" % finals)
    print("reasoning   : %d chunks, %d chars %s" % (
        reasoning_chunks, reasoning_chars,
        "(paragraphs shown)" if reasoning_enabled(args) else "(hidden)"))
    for name in ("research_log.jsonl", "blueprint.md"):
        candidate = (project / "memory" / name) if name.endswith(".jsonl") else (project / "workspace" / name)
        if candidate.exists():
            print("%-12s: %s (%d bytes)" % (name, candidate, candidate.stat().st_size))
    return 0


def cmd_ask(args) -> int:
    app = load_app(Path(args.root), Path(args.home))
    seed_project(app, args.project)
    state = app.start_shell_state(mode="research", project_slug=args.project, agent_slug=args.agent)
    print(app.ask(args.prompt, state))
    return 0


def cmd_shell(args) -> int:
    bootstrap(Path(args.root))
    from moonshine.moonshine_cli.main import main as cli_main

    argv = ["--home", args.home, "shell", "--mode", "research",
            "--project", args.project, "--agent", args.agent]
    if args.iterations:
        argv += ["--max-iterations", str(args.iterations)]
    return int(cli_main(argv))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HT research agent (patched Moonshine).")
    parser.add_argument("--root", default=os.environ.get("HT_AGENT_ROOT", str(DEFAULT_ROOT)))
    parser.add_argument("--home", default=os.environ.get("HT_AGENT_HOME", str(DEFAULT_HOME)))
    parser.add_argument("--project", default=DEFAULT_PROJECT)
    parser.add_argument("--agent", default=DEFAULT_AGENT)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("doctor", help="verify agent, skills, tools, provider and project wiring")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("config", help="configure an OpenAI-compatible provider")
    p.add_argument("--base-url", default=os.environ.get("HT_AGENT_BASE_URL", "https://api.openai.com/v1"))
    p.add_argument("--model", default=os.environ.get("HT_AGENT_MODEL", "gpt-4o"))
    p.add_argument("--api-key-env", default=os.environ.get("HT_AGENT_API_KEY_ENV", "OPENAI_API_KEY"))
    p.add_argument("--api-key", default="")
    p.add_argument("--no-stream", action="store_true")
    p.add_argument("--temperature", type=float, default=None)
    p.add_argument("--timeout", type=int, default=None)
    p.add_argument("--structured-output-format", default="json_schema")
    p.set_defaults(func=cmd_config)

    p = sub.add_parser("run", help="run the autonomous research loop")
    p.add_argument("--iterations", type=int, default=40)
    p.add_argument("--prompt", default="")
    p.add_argument("--prompt-file", default="", help="read the prompt from a UTF-8 text file")
    p.add_argument("--quiet", action="store_true",
                   help="only the model's final text plus the run summary (hides status, tool lines and reasoning)")
    p.add_argument("--show-reasoning", action="store_true",
                   help="print the model's reasoning as wrapped paragraphs between [reasoning] markers")
    p.add_argument("--width", type=int, default=220)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("ask", help="one research turn")
    p.add_argument("prompt")
    p.set_defaults(func=cmd_ask)

    p = sub.add_parser("shell", help="interactive research shell")
    p.add_argument("--iterations", type=int, default=0)
    p.set_defaults(func=cmd_shell)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

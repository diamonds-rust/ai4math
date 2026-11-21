"""Install the HT modification into a Moonshine setup.

Two modes
---------
``--copy`` (default): copy the source into ``--target``, patch the copy, write a
launcher, seed a portable home. The pristine checkout is untouched.

``--inplace``: patch the source you already use (an editable install such as
``C:\\Users\\<you>\\Desktop\\Moonshine-main``), install the assets into your
existing runtime home, and leave your provider configuration alone. This is the
mode for "moonshine is already installed and working".

Usage
-----
    # simulate / first-time portable setup
    python integration/install_into_moonshine.py

    # patch the real installation, keep its provider and settings
    python integration/install_into_moonshine.py --inplace ^
        --source "C:\\Users\\<you>\\Desktop\\Moonshine-main" ^
        --home   "C:\\Users\\<you>\\Desktop\\moonshine-data" ^
        --no-settings --seed-project --project ht_r3

Verification (both modes): imports the patched registry, counts the HT tools and
dispatches a real HT tool.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ht_moonshine.brief import seed as seed_project  # noqa: E402
from ht_moonshine.tools_impl import HT_HANDLERS  # noqa: E402
from ht_moonshine.moonshine_bridge import (  # noqa: E402
    install_assets,
    patch_source,
    verify_patched_tree,
    write_settings,
)

IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".git", "*.egg-info", ".pytest_cache")

LAUNCHER = '''"""Launcher for the patched HT Moonshine tree (portable copy mode).

Adds the Moonshine package root and the toolkit to sys.path, then hands over to
Moonshine's own CLI.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLKIT = HERE.parent.parent  # the Stastistics directory

for path in (str(HERE), str(TOOLKIT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from moonshine.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
'''


def _copy_source(source: Path, target: Path, force: bool) -> Path:
    package = target / "moonshine"
    if package.exists() and not force:
        print("target already exists, reuse it (--force to recopy): %s" % package)
        return package
    package.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, package, dirs_exist_ok=True, ignore=IGNORE)
    return package


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Install the HT Moonshine modification.")
    parser.add_argument("--inplace", action="store_true", help="patch an existing editable install instead of copying")
    parser.add_argument("--source", default=str(REPO_ROOT.parent / "Moonshine-main"))
    parser.add_argument("--target", default=str(REPO_ROOT / "runtime" / "moonshine-src"))
    parser.add_argument("--home", default="")
    parser.add_argument("--skip-copy", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-settings", action="store_true", help="do not touch <home>/config/settings.json")
    parser.add_argument("--no-seed", action="store_true", help="do not write the project brief")
    parser.add_argument("--seed-project", action="store_true", help="write <home>/projects/<slug>/workspace/problem.md")
    parser.add_argument("--force-seed", action="store_true", help="overwrite an existing problem.md")
    parser.add_argument("--project", default="ht_r3")
    parser.add_argument("--agent", default="ht-researcher")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    source = Path(args.source).resolve()
    target = Path(args.target).resolve()
    home = Path(args.home).resolve() if args.home else (source / "home" if args.inplace else target / "home")

    if not (source / "app.py").exists() and not (source / "tools" / "registry.py").exists():
        print("not a Moonshine source tree: %s" % source, file=sys.stderr)
        return 2

    if args.inplace:
        patched_root = source
        layout = "installed-package"
    else:
        if args.skip_copy:
            patched_root = target
        else:
            _copy_source(source, target, args.force)
            patched_root = target
        (target / "run_ht.py").write_text(LAUNCHER, encoding="utf-8")
        layout = "copy"

    patches = patch_source(patched_root)
    assets = install_assets(home)
    settings = None
    if not args.no_settings:
        settings = write_settings(home)
    seeded = None
    if args.seed_project or args.inplace:
        if not args.no_seed:
            seeded = seed_project(home, args.project, force=args.force_seed)
    verification = verify_patched_tree(patched_root, home)

    report = {
        "mode": layout,
        "source": str(source),
        "patched_root": str(patched_root),
        "home": str(home),
        "patches": patches["patches"],
        "assets": assets["count"],
        "settings": settings,
        "seeded": seeded,
        "verification": verification,
        "ok": bool(
            verification["dispatch_ok"]
            and len(verification["ht_tools"]) == len(HT_HANDLERS)
        ),
    }
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    else:
        print("mode   : %s" % layout)
        print("root   : %s" % report["patched_root"])
        print("home   : %s" % report["home"])
        for item in report["patches"]:
            print("patch  : %-22s %s" % (item["status"], Path(item["file"]).relative_to(patched_root)))
        print("assets : %d files" % report["assets"])
        if settings:
            print("setting: %s (provider preserved=%s, model=%s)" % (
                settings["path"], settings["provider_preserved"], settings["provider_model"]))
        if seeded:
            print("brief  : %s" % seeded["problem"])
        print("tools  : %d registered, %d HT tools (%s layout)" % (
            verification["tool_count"], len(verification["ht_tools"]), verification["layout"]))
        print("module : %s" % verification["moonshine_module"])
        print("dispatch ht_build_design -> %s" % ("ok" if verification["dispatch_ok"] else "FAILED"))
        print("overall: %s" % ("OK" if report["ok"] else "FAILED"))
        if report["ok"]:
            print("\nnext   : conda activate moonshine")
            print("        python -m moonshine --home \"%s\" shell --mode research --project %s --agent %s"
                  % (home, args.project, args.agent))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

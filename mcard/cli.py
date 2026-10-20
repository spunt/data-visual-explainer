"""mcard CLI: lint, build, new."""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

from .lint import lint
from .model import Card, CardError
from .render import render_card, render_index


def _prog() -> str:
    # bin/mcard sets MCARD_PROG, so hints show a command the user can actually run from anywhere.
    if os.environ.get("MCARD_PROG"):
        return os.environ["MCARD_PROG"]
    return "python -m mcard" if Path(sys.argv[0]).name == "__main__.py" else "mcard"


def _cards(paths: list[str]) -> list[Path]:
    out: list[Path] = []
    for p in map(Path, paths):
        out += sorted(p.glob("*.yaml")) if p.is_dir() else [p]
    return out


def cmd_lint(args) -> int:
    worst = 0
    for path in _cards(args.paths):
        card = Card.load(path)
        findings = lint(card)
        shown = [f for f in findings if args.verbose or f.level != "info"]
        n_err = sum(f.level == "error" for f in findings)
        n_warn = sum(f.level == "warn" for f in findings)
        print(f"{path}: {n_err} error(s), {n_warn} warning(s)")
        for f in shown:
            print(f"  {f}")
        worst = max(worst, 2 if n_err else (1 if n_warn and args.strict else 0))
    return worst


def cmd_build(args) -> int:
    out = Path(args.out)
    cards = []
    status = 0
    for path in _cards(args.paths):
        card = Card.load(path)
        if card.errors:
            print(f"{path}: schema errors, skipped")
            for e in card.errors:
                print(f"  {e}")
            status = 2
            continue
        paths = render_card(card, out)
        cards.append(card)
        errs = sum(f.level == "error" for f in lint(card))
        flag = f"  ({errs} lint error(s); shown in level 4)" if errs else ""
        print(f"{path} -> {paths['explorer']}{flag}")
    if cards:
        print(f"index -> {render_index(cards, out)}")
    return status


def cmd_new(args) -> int:
    template = Path(__file__).resolve().parent.parent / "schema" / "card_template.yaml"
    dest = Path(args.dir) / f"{args.id}.yaml"
    if dest.exists():
        print(f"{dest} exists", file=sys.stderr)
        return 1
    text = template.read_text().replace("REPLACE_ID", args.id)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text)
    print(f"created {dest}; fill it in following SKILL.md, then run: {_prog()} lint {dest}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog=_prog(), description="Metric cards: lint and render.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("lint", help="check cards")
    a.add_argument("paths", nargs="+")
    a.add_argument("-v", "--verbose", action="store_true", help="include info findings")
    a.add_argument("--strict", action="store_true", help="non-zero exit on warnings")
    a.set_defaults(fn=cmd_lint)
    b = sub.add_parser("build", help="render explorer, label, methods and index")
    b.add_argument("paths", nargs="+")
    b.add_argument("-o", "--out", default="site")
    b.set_defaults(fn=cmd_build)
    n = sub.add_parser("new", help="start a card from the template")
    n.add_argument("id")
    n.add_argument("--dir", default="cards")
    n.set_defaults(fn=cmd_new)
    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except CardError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

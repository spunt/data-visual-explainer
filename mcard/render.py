"""Render cards to self-contained HTML (explorer, label), Markdown (methods) and an index."""
from __future__ import annotations

import base64
import re
from html import escape
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from . import svg
from .lint import lint
from .model import CLAIM_STRENGTH, EFFECTS, TARGETS, Card, fmt, lc_first, window_phrase, window_range

HERE = Path(__file__).resolve().parent
GIST_W, STAGE_W, FULL_W = 520, 540, 1000


class Glosser:
    """Wraps the first mention of each glossary term per section in an accessible toggletip trigger."""

    def __init__(self, glossary: list[dict]):
        self.entries = []
        for i, item in enumerate(glossary):
            for t in [item["term"], *item.get("aliases", [])]:
                self.entries.append((t, f"g{i}"))
        self.entries.sort(key=lambda e: -len(e[0]))
        self.seen: set[str] = set()
        self.pattern = None
        if self.entries:
            alts = "|".join(re.escape(t) for t, _ in self.entries)
            self.pattern = re.compile(rf"(?<![\w-])({alts})(?![\w-])", re.I)
        self.lookup = {t.lower(): (gid, t) for t, gid in self.entries}

    def section(self, _name: str = "") -> str:
        self.seen = set()
        return ""

    def __call__(self, text, link: bool = True) -> Markup:
        if text is None:
            return Markup("")
        html = inline(str(text))
        if not (link and self.pattern):
            return Markup(html)
        out, pos = [], 0
        # only match outside tags
        for chunk in re.split(r"(<[^>]+>)", html):
            if chunk.startswith("<"):
                out.append(chunk)
                continue
            def repl(m):
                hit = self.lookup.get(m.group(1).lower())
                if not hit:
                    return m.group(0)
                gid, canon = hit
                case_sensitive = any(ch.isupper() for ch in canon[1:]) or (canon.isupper() and len(canon) <= 4)
                if gid in self.seen or (case_sensitive and m.group(1) != canon):
                    return m.group(0)
                self.seen.add(gid)
                return (f'<button type="button" class="term" data-tip="{gid}" '
                        f'aria-describedby="tip-{gid}">{m.group(0)}</button>')
            out.append(self.pattern.sub(repl, chunk))
        return Markup("".join(out))


def inline(text: str) -> str:
    s = escape(text)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    return s


def build_steps(card: Card) -> list[dict]:
    g = card.g
    unit = g["unit"]
    steps = []
    flow = []
    for rule in g["population"]:
        flow.append({"text": rule["plain"], "exact": rule.get("exact"), "n": rule.get("n_after"), "src": card.src_list(rule.get("src"))})
    steps.append({
        "id": "who", "kicker": "Who is counted", "title": f"Start with {unit['plural']}, then apply each rule",
        "plain": unit.get("plain", ""), "exact": unit.get("exact"), "src": card.src_list(unit.get("src")),
        "figure": {"kind": "flow", "items": flow, "unit": unit},
    })
    anchor = g["anchor"]
    steps.append({
        "id": "clock", "kicker": "When the clock starts", "title": f"Time zero: {lc_first(anchor.get('label', 'the start'))}",
        "plain": anchor["plain"], "exact": anchor.get("exact"), "src": card.src_list(anchor.get("src")),
        "windows": [dict(w, phrase=window_phrase(w, anchor.get("label", "time zero"))) for w in g["windows"]],
        "figure": {"kind": "svg", "svg": svg.timeline(card, with_example=False, highlight="all", w=STAGE_W)},
    })
    pm = card.primary_measure
    steps.append({
        "id": "counts", "kicker": "What counts", "title": pm["label"],
        "plain": pm["plain"], "exact": pm.get("exact"), "src": card.src_list(pm.get("src")),
        "measures": [m for m in g["measures"] if m is not pm],
        "figure": {"kind": "svg", "svg": svg.timeline(card, with_example=bool(card.get("example")), highlight=pm["window"], w=STAGE_W)},
    })
    agg = g["aggregate"]
    frac = None
    cells = card.cells
    focal = (card.group_by_role("treated", "focal") or [None])[-1]
    if agg["kind"] == "proportion" and cells:
        gid = focal["id"] if focal and focal["id"] in cells else list(cells)[-1]
        c = cells[gid]
        unit_r = card.result_unit
        if c.get("n") and unit_r in ("percent", "share"):
            share = c["value"] / (100 if unit_r == "percent" else 1)
            frac = {"num": round(share * c["n"]), "den": c["n"], "value": fmt(c["value"], unit_r),
                    "group": card.groups.get(gid, {}).get("label", "")}
    elif agg["kind"] == "mean" and cells:
        gid = focal["id"] if focal and focal["id"] in cells else list(cells)[-1]
        c = cells[gid]
        frac = {"num": None, "den": c.get("n"), "value": fmt(c["value"], card.result_unit),
                "group": card.groups.get(gid, {}).get("label", "")}
    steps.append({
        "id": "combine", "kicker": "Combine", "title": {"proportion": "Turn yes/no answers into a share", "mean": "Average across people",
                                                          "sum": "Add up across people", "ratio_of_sums": "Divide one total by another"}[agg["kind"]],
        "plain": agg["plain"], "exact": agg.get("exact"), "src": card.src_list(agg.get("src")),
        "figure": {"kind": "fraction", "agg": agg, "frac": frac},
    })
    comp = g.get("comparison")
    if comp:
        val, formula = card.recompute()
        steps.append({
            "id": "compare", "kicker": "Compare", "title": {"difference_in_differences": "Subtract the usual change",
                                                            "difference": "Take the difference", "ratio": "Take the ratio",
                                                            "adjusted_difference": "Compare with a matched group"}[comp["kind"]],
            "plain": comp["plain"], "exact": comp.get("exact"), "src": card.src_list(comp.get("src")),
            "formula": comp.get("formula"), "worked": formula, "target": comp.get("target"),
            "figure": {"kind": "svg", "svg": svg.comparison_chart(card, STAGE_W)},
        })
    adj = g.get("adjustment")
    if adj:
        steps.append({
            "id": "adjust", "kicker": "Make it fair", "title": "Reweight the comparison group",
            "plain": adj["plain"], "exact": adj.get("exact"), "src": card.src_list(adj.get("src")),
            "figure": {"kind": "adjust", "adj": adj, "svg": svg.bars_chart(card, STAGE_W)},
        })
    unc = g.get("uncertainty")
    if unc and card.measured:
        h = card["gist"]["headline"]
        steps.append({
            "id": "sure", "kicker": "How sure", "title": "Show the range of plausible values",
            "plain": unc["plain"], "exact": unc.get("exact"), "src": card.src_list(unc.get("src")),
            "gaps": unc.get("known_gaps"),
            "figure": {"kind": "svg", "svg": svg.dotplot(h["value"], h.get("low"), h.get("high"), h["unit"], label=h["label"], w=STAGE_W),
                       "caption": "Each dot is one of 20 equally likely values, given sampling noise alone (normal approximation to the interval)."},
        })
    for i, s in enumerate(steps, 1):
        s["n"] = i
    return steps


def data_uri(text: str, mime="text/yaml") -> str:
    return f"data:{mime};base64," + base64.b64encode(text.encode()).decode()


def env() -> Environment:
    e = Environment(loader=FileSystemLoader(HERE / "templates"), autoescape=select_autoescape(["html", "j2"]),
                    trim_blocks=True, lstrip_blocks=True)
    e.filters["fmt"] = fmt
    e.filters["inline"] = lambda t: Markup(inline(str(t))) if t else ""
    e.filters["lc_first"] = lc_first
    e.filters["wrange"] = window_range
    return e


def static(name: str) -> Markup:
    return Markup((HERE / "static" / name).read_text())


def context(card: Card) -> dict:
    h = card["gist"].get("headline") or {"value": 0, "unit": "other", "label": ""}
    findings = lint(card)
    return {
        "c": card.raw, "card": card, "g": card.g,
        "gl": Glosser(card.get("glossary", [])),
        "steps": build_steps(card),
        "headline": card.headline_text(), "headline_range": card.headline_range(),
        "unit_words": {"pp": "percentage points", "percent": "", "share": "", "days": "", "count": ""}.get(h["unit"], ""),
        "claim": CLAIM_STRENGTH.get(card["gist"].get("claim_strength", ""), None),
        "effects": EFFECTS, "targets": TARGETS,
        "chart": Markup((svg.comparison_chart(card, GIST_W) if card.measured else "") or svg.timeline(card, with_example=False, highlight="all", w=GIST_W)),
        "measured": card.measured,
        "sens": Markup(svg.sensitivity(card, FULL_W)),
        "example_tl": Markup(svg.timeline(card, with_example=True, w=FULL_W)) if card.get("example") else "",
        "literal": card.literal_reading(),
        "maturity": card.maturity() if card.measured else {"status": "n/a", "text": "No result yet, so completeness does not apply. When the metric is run, record data_complete_through and latest_anchor."},
        "caveats_sorted": sorted(card["fine_print"].get("caveats", []), key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.get("severity"), 1)),
        "teachback": card.teachback(),
        "recompute": card.recompute(),
        "lint": findings,
        "lint_counts": {k: sum(1 for x in findings if x.level == k) for k in ("error", "warn", "info")},
        "yaml_uri": data_uri(card.yaml_text),
        "yaml_name": card.path.name,
        "minutes": {k: card.reading_minutes(k) for k in ("gist", "build", "mind", "reproduce")},
        "css": static("style.css"), "js": static("app.js"),
        "Markup": Markup,
    }


def render_card(card: Card, out_dir: Path) -> dict[str, Path]:
    e = env()
    ctx = context(card)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for kind, tpl, ext in (("explorer", "explorer.html.j2", ".html"), ("label", "label.html.j2", ".label.html"),
                           ("methods", "methods.md.j2", ".methods.md")):
        ctx["gl"] = Glosser(card.get("glossary", []))
        text = e.get_template(tpl).render(**ctx)
        p = out_dir / f"{card['id']}{ext}"
        p.write_text(text)
        paths[kind] = p
    paths["methods_html"] = methods_html(card, paths["methods"], ctx["css"])
    return paths


def methods_html(card: Card, md_path: Path, css: str) -> Path:
    text = md_path.read_text()
    try:
        import markdown
        body = markdown.markdown(text, extensions=["tables", "fenced_code"])
    except ImportError:
        body = f"<pre>{escape(text)}</pre>"
    out = md_path.with_name(f"{card['id']}.methods.html")
    out.write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(card['title'])}: methods</title>
<style>{css} .doc{{max-width:900px;margin:0 auto;padding:28px 28px 80px}} .doc h1{{font:600 1.8rem/1.2 var(--serif)}}</style></head>
<body><div class="doc"><p class="crumbs"><a href="{card['id']}.html">← Explorer</a> · <a href="{md_path.name}" download>Download Markdown</a></p>{body}</div></body></html>""")
    return out


def render_index(cards: list[Card], out_dir: Path) -> Path:
    e = env()
    rows = []
    for c in cards:
        rows.append({"c": c.raw, "measured": c.measured, "headline": c.headline_text(), "range": c.headline_range(),
                     "claim": CLAIM_STRENGTH.get(c["gist"].get("claim_strength", ""), None),
                     "lint": lint(c)})
    p = out_dir / "index.html"
    p.write_text(e.get_template("index.html.j2").render(rows=rows, css=static("style.css"), js=static("app.js")))
    return p

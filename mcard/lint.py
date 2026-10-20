"""Quality checks beyond the schema: integrity, arithmetic, plain language, completeness."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .model import Card, jargon_in


@dataclass
class Finding:
    level: str  # error | warn | info
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.level.upper():5} {self.code:22} {self.message}"


def syllables(word: str) -> int:
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    groups = re.findall(r"[aeiouy]+", w)
    n = len(groups)
    if w.endswith("e") and not w.endswith(("le", "ee")) and n > 1:
        n -= 1
    return max(1, n)


def fk_grade(text: str) -> float:
    sentences = max(1, len(re.findall(r"[.!?]+(\s|$)", text)))
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", text)
    if not words:
        return 0.0
    syl = sum(syllables(w) for w in words)
    return 0.39 * len(words) / sentences + 11.8 * syl / len(words) - 15.59


def plain_texts(card: Card) -> list[tuple[str, str]]:
    out = []
    gist = card["gist"]
    for k in ("sentence", "frequency", "key_caveat"):
        if gist.get(k):
            out.append((f"gist.{k}", gist[k]))
    out.append(("gist.reading.say", gist["reading"]["say"]))
    g = card.g
    for key in ("unit", "anchor", "aggregate", "comparison", "adjustment", "uncertainty"):
        if g.get(key, {}).get("plain"):
            out.append((f"grammar.{key}", g[key]["plain"]))
    for key in ("population", "windows", "measures", "groups"):
        for i, item in enumerate(g.get(key, [])):
            out.append((f"grammar.{key}[{i}]", item["plain"]))
    ex = card.get("example") or {}
    for k in ("intro", "outcome"):
        if ex.get(k):
            out.append((f"example.{k}", ex[k]))
    for i, c in enumerate(card["fine_print"].get("caveats", [])):
        out.append((f"caveats[{i}]", c["text"]))
    return out


def lint(card: Card) -> list[Finding]:
    f: list[Finding] = []
    todo = []

    def find_todo(node, path=""):
        if isinstance(node, str) and ("TODO" in node or "YYYY" in node or "REPLACE_ID" in node):
            todo.append(path)
        elif isinstance(node, dict):
            for k, v in node.items():
                find_todo(v, f"{path}.{k}" if path else k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                find_todo(v, f"{path}[{i}]")
    find_todo(card.raw)
    if todo:
        f.append(Finding("error", "unfinished", f"{len(todo)} placeholder field(s) remain, e.g. {', '.join(todo[:4])}"))
    for e in card.errors:
        f.append(Finding("error", "schema", e))
    if card.errors:
        return f

    g = card.g
    windows, measures, groups, sources = card.windows, card.measures, card.groups, card.sources

    # --- referential integrity
    for w in g["windows"]:
        if w["end"] <= w["start"]:
            f.append(Finding("error", "window-order", f"window {w['id']}: end must be greater than start (end is exclusive)"))
    for m in g["measures"]:
        if m["window"] not in windows:
            f.append(Finding("error", "ref-window", f"measure {m['id']} uses unknown window {m['window']}"))
    if g["aggregate"]["measure"] not in measures:
        f.append(Finding("error", "ref-measure", f"aggregate uses unknown measure {g['aggregate']['measure']}"))
    for c in card["results"].get("cells", []):
        if groups and c["group"] not in groups:
            f.append(Finding("error", "ref-group", f"results cell refers to unknown group {c['group']}"))
    for om in card["results"].get("other_measures", []):
        if om["measure"] not in measures:
            f.append(Finding("warn", "ref-measure", f"other_measures refers to {om['measure']}, not defined in grammar.measures"))

    def walk(node, path=""):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "src":
                    for sid in ([v] if isinstance(v, str) else v):
                        if sid not in sources:
                            f.append(Finding("error", "ref-source", f"{path}: unknown source id {sid}"))
                else:
                    walk(v, f"{path}.{k}" if path else k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
    walk(card.raw)

    for i, q in enumerate(card.get("quiz", [])):
        if not 0 <= q["answer"] < len(q["options"]):
            f.append(Finding("error", "quiz-answer", f"quiz[{i}] answer index out of range"))

    # --- arithmetic
    est = card["results"].get("estimate")
    head = card["gist"].get("headline")
    if not head:
        if card["results"].get("status") != "not_run":
            f.append(Finding("error", "headline", "no gist.headline: add one, or set results.status: not_run for a definition-only card"))
        else:
            f.append(Finding("info", "not-run", "definition-only card: no number yet"))
            stray = [k for k in ("data_complete_through", "latest_anchor", "cells", "estimate", "sensitivity", "other_measures")
                     if card["results"].get(k)]
            if stray:
                f.append(Finding("warn", "not-run-results", f"definition-only card has result fields ({', '.join(stray)}); move planned values to spec.parameters"))
        head = {"value": 0, "unit": "other"}
        est = None
    val, formula = card.recompute()
    if val is not None and est:
        tol = 0.006 + 0.01 * abs(est["value"])
        if abs(val - est["value"]) > tol:
            f.append(Finding("error", "recompute", f"cells give {formula}, but results.estimate is {est['value']}"))
        else:
            f.append(Finding("info", "recompute", f"estimate reproduced from cells: {formula}"))
    from .model import DEFAULT_DECIMALS
    half_step = 0.5 * 10 ** -head.get("decimals", DEFAULT_DECIMALS.get(head["unit"], 2)) + 1e-9
    if est and abs(head["value"] - est["value"]) > half_step:
        f.append(Finding("error", "headline-mismatch", f"headline {head['value']} ≠ results.estimate {est['value']}"))
    if est and ("low" in est) != ("low" in head):
        f.append(Finding("warn", "headline-interval", "results.estimate and gist.headline disagree on whether an interval exists"))
    if not g.get("comparison") and card.measured:
        cells = card["results"].get("cells", [])
        if len(cells) == 1 and abs(cells[0]["value"] - head["value"]) > half_step:
            f.append(Finding("error", "headline-mismatch", f"headline {head['value']} ≠ single cell {cells[0]['value']}"))

    # --- plain language
    sent = card["gist"]["sentence"]
    n_words = len(sent.split())
    if n_words > 50:
        f.append(Finding("warn", "gist-length", f"gist.sentence is {n_words} words; aim for 45 or fewer"))
    grade = fk_grade(sent)
    if grade > 12:
        f.append(Finding("warn", "readability", f"gist.sentence reads at grade {grade:.0f}; aim for 10 or below"))
    glossed = {t.lower() for item in card.get("glossary", []) for t in [item["term"], *item.get("aliases", [])]}

    def covered(j: str) -> bool:
        jl = j.lower()
        return any(jl in t or t in jl for t in glossed)

    missing: dict[str, list[str]] = {}
    for where, text in plain_texts(card):
        for j in jargon_in(text):
            if not covered(j):
                missing.setdefault(j, []).append(where)
    for j, wheres in missing.items():
        f.append(Finding("warn", "jargon", f"'{j}' appears in plain text ({', '.join(wheres[:3])}) without a glossary entry"))

    # --- completeness
    if not card["gist"].get("claim_strength"):
        f.append(Finding("warn", "claim-strength", "gist.claim_strength not set"))
    comp = g.get("comparison")
    if comp and not comp.get("target"):
        f.append(Finding("warn", "target", "comparison.target (ATT/ATE/descriptive) not set"))
    if card["gist"].get("claim_strength") in ("quasi-causal", "causal", "associational") and not g.get("uncertainty"):
        f.append(Finding("warn", "uncertainty", "comparative claim without grammar.uncertainty"))
    if g.get("uncertainty") and not g["uncertainty"].get("known_gaps"):
        f.append(Finding("warn", "uncertainty-gaps", "say what the interval does not cover (uncertainty.known_gaps)"))
    kinds = {q.get("kind") for q in card.get("quiz", [])}
    for k in ("gist", "verbatim", "transfer"):
        if k not in kinds:
            f.append(Finding("warn", "quiz-coverage", f"no {k} question in quiz"))
    if len(card["fine_print"].get("misreadings", [])) < 2:
        f.append(Finding("warn", "misreadings", "list at least two likely misreadings"))
    if not card.get("example"):
        f.append(Finding("warn", "example", "no worked example; concrete cases aid understanding"))
    if not card["gist"].get("frequency"):
        f.append(Finding("info", "frequency", "no natural-frequency restatement"))
    unsourced = 0
    for key in ("population", "windows", "measures"):
        unsourced += sum(1 for x in g.get(key, []) if x.get("exact") and not x.get("src"))
    if unsourced:
        f.append(Finding("warn", "provenance", f"{unsourced} exact rule(s) in population/windows/measures have no src"))
    m = card.maturity() if card.measured else {"status": "n/a"}
    if m["status"] == "immature":
        f.append(Finding("error", "maturity", m["text"]))
    elif m["status"] == "unknown":
        f.append(Finding("warn", "maturity", m["text"]))
    if not card["fine_print"].get("discrepancies"):
        f.append(Finding("info", "discrepancies", "no description-vs-code discrepancies recorded (state if checked and none found)"))
    return f

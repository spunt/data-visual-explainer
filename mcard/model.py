"""Load, validate and derive a renderable view of a Metric Card."""
from __future__ import annotations

import calendar
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schema" / "metric_card.schema.yaml"

UNIT_WORDS = {
    "pp": "percentage points",
    "percent": "percent",
    "share": "percent",
    "count": "",
    "days": "days",
    "ratio": "×",
    "currency": "USD",
    "other": "",
}
DEFAULT_DECIMALS = {"pp": 2, "percent": 1, "share": 1, "count": 0, "days": 2, "ratio": 2, "currency": 0, "other": 2}

CLAIM_STRENGTH = {
    "descriptive": ("Describes a level", "This number describes what happened in one group. It does not compare groups or explain why."),
    "associational": ("Shows a link", "Groups are compared, but nothing rules out other differences between them. Treat it as a link, not a cause."),
    "quasi-causal": ("Points toward a cause, with assumptions", "The design removes some alternative explanations, not all. Read it as a cause only if its assumptions hold."),
    "causal": ("Supports a cause", "Groups were assigned at random, so differences can be read as effects of the exposure."),
}

EFFECTS = {
    "overstates": ("↑", "May make the number look bigger than it really is"),
    "understates": ("↓", "May make the number look smaller than it really is"),
    "wider_uncertainty": ("±", "The true uncertainty is larger than shown"),
    "unknown_direction": ("↕", "Could push the number either way"),
    "limits_scope": ("◎", "Limits what the number can be used to conclude"),
}

TARGETS = {
    "ATT": "Effect among those who actually did it (not everyone)",
    "ATE": "Average effect if everyone did it",
    "ATC": "Effect among those who did not do it, had they done it",
    "descriptive": "No causal target; a comparison of observed numbers",
}


def load_schema() -> dict:
    return yaml.safe_load(SCHEMA_PATH.read_text())


def schema_errors(raw: dict) -> list[str]:
    validator = jsonschema.Draft202012Validator(load_schema())
    return [f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}" for e in validator.iter_errors(raw)]


def fmt(value, unit: str, signed: bool = False, decimals: int | None = None, words: bool = False) -> str:
    if value is None:
        return "–"
    d = DEFAULT_DECIMALS.get(unit, 2) if decimals is None else decimals
    v = value * 100 if unit == "share" else value
    sign = "+" if signed and v > 0 else ("−" if v < 0 else "")
    body = f"{abs(v):,.{d}f}"
    if unit in ("percent", "share"):
        return f"{sign}{body}%"
    if unit == "pp":
        return f"{sign}{body}{' percentage points' if words else ' pp'}"
    if unit == "days":
        return f"{sign}{body} day{'' if abs(v) == 1 else 's'}"
    if unit == "ratio":
        return f"{sign}{body}×"
    if unit == "currency":
        return f"{sign}${body}"
    return f"{sign}{body}"


def to_days(offset: int, unit: str) -> float:
    return offset * {"day": 1, "week": 7, "month": 30.44}[unit]


def add_months(d: date, months: int) -> date:
    idx = d.year * 12 + d.month - 1 + months
    y, m = divmod(idx, 12)
    return date(y, m + 1, min(d.day, calendar.monthrange(y, m + 1)[1]))


def window_range(w: dict) -> str:
    """Human range for a window. Day/week ends are shown inclusive; month windows keep the exclusive end."""
    unit, s, e = w["unit"], w["start"], w["end"]
    if unit == "month":
        return f"from {s} to {e} months (up to, not including, {e})"
    def n(x):
        return f"−{abs(x)}" if x < 0 else str(x)
    if e - 1 == s:
        return f"{unit} {n(s)}"
    return f"{unit}s {n(s)}{' to ' if s < 0 else '–'}{n(e - 1)}"


def window_phrase(w: dict, anchor_label: str) -> str:
    unit = w["unit"]
    if unit == "month":
        return f"from {w['start']} months after the {lc_first(anchor_label)} up to, but not including, {w['end']} months after"
    s, e = w["start"], w["end"] - 1
    plural = unit + ("s" if e != s else "")
    a = anchor_label.lower()
    if s == e:
        where = f"{unit} {s}" if s else f"{unit} 0, the {a} itself"
        return where
    if e <= 0:
        n = e - s + 1
        return f"the {n} {unit}s up to {'and including' if e == 0 else 'before'} the {a} ({plural} {s} to {e})"
    if s < 0 < e:
        return f"{plural} {s} to {e} around the {a}"
    return f"{plural} {s}–{e} after the {a}" if s > 0 else f"{plural} {s}–{e}, counting the {a} as {unit} 0"


class CardError(ValueError):
    pass


def _strip(node):
    if isinstance(node, str):
        return node.strip()
    if isinstance(node, dict):
        return {k: _strip(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_strip(v) for v in node]
    return node


def lc_first(text: str) -> str:
    return text[:1].lower() + text[1:] if text[:2] != text[:2].upper() else text


@dataclass
class Card:
    raw: dict
    path: Path
    errors: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: str | Path) -> "Card":
        p = Path(path)
        try:
            raw = _strip(yaml.safe_load(p.read_text()))
        except yaml.YAMLError as e:
            mark = getattr(e, "problem_mark", None)
            where = f"line {mark.line + 1}, column {mark.column + 1}" if mark else "unknown position"
            hint = ("Wrap text that contains ': ', '#', or starts with a quote, '-', '[' or '{' in double quotes, "
                    "or use a block scalar (key: >).")
            raise CardError(f"{p}: YAML could not be parsed at {where}: {getattr(e, 'problem', e)}. {hint}") from None
        if not isinstance(raw, dict):
            raise CardError(f"{p}: expected a mapping at the top level")
        return cls(raw=raw, path=p, errors=schema_errors(raw))

    def __getitem__(self, key):
        return self.raw[key]

    def get(self, key, default=None):
        return self.raw.get(key, default)

    @property
    def g(self) -> dict:
        return self.raw["grammar"]

    @property
    def yaml_text(self) -> str:
        return self.path.read_text()

    def by_id(self, items: list | None) -> dict:
        return {i["id"]: i for i in (items or []) if "id" in i}

    @property
    def windows(self) -> dict:
        return self.by_id(self.g.get("windows"))

    @property
    def measures(self) -> dict:
        return self.by_id(self.g.get("measures"))

    @property
    def groups(self) -> dict:
        return self.by_id(self.g.get("groups"))

    @property
    def sources(self) -> dict:
        return self.by_id(self.raw.get("sources"))

    @property
    def primary_measure(self) -> dict:
        ms = self.g["measures"]
        return next((m for m in ms if m.get("primary")), ms[0])

    @property
    def measured(self) -> bool:
        return bool(self.raw["gist"].get("headline")) and self.raw["results"].get("status") != "not_run"

    @property
    def result_unit(self) -> str:
        return self.raw["results"].get("unit") or (self.raw["gist"].get("headline") or {}).get("unit", "other")

    @property
    def cells(self) -> dict:
        return {c["group"]: c for c in self.raw["results"].get("cells", [])}

    def group_by_role(self, *roles: str) -> list[dict]:
        return [g for g in self.g.get("groups", []) if g.get("role") in roles]

    def did_series(self) -> tuple[str, str]:
        """Names of the baseline and focal lines in a difference-in-differences chart: `series`, else `year`."""
        def name(role: str, default: str) -> str:
            g = next((g for g in self.g.get("groups", []) if g.get("role") == role), {})
            return g.get("series") or g.get("year") or default
        return name("baseline", "baseline"), name("focal", "focal")

    def src_list(self, src) -> list[dict]:
        if not src:
            return []
        ids = [src] if isinstance(src, str) else src
        return [self.sources.get(i, {"id": i, "path": "(unknown source)"}) for i in ids]

    # ---------- derived content ----------

    def headline_text(self) -> str:
        h = self.raw["gist"].get("headline")
        if not h:
            return "Not measured yet"
        signed = self.g.get("comparison") is not None
        return fmt(h["value"], h["unit"], signed=signed, decimals=h.get("decimals"))

    def headline_range(self) -> str | None:
        h = self.raw["gist"].get("headline")
        if not h or "low" not in h or "high" not in h:
            return None
        signed = self.g.get("comparison") is not None
        d = h.get("decimals")
        return f"{fmt(h['low'], h['unit'], signed, d)} to {fmt(h['high'], h['unit'], signed, d)}"

    def literal_reading(self) -> list[str]:
        """The metric re-assembled mechanically from the grammar, one sentence per stage."""
        g = self.g
        unit = g["unit"]
        anchor = g["anchor"]
        out = [f"The unit is one {unit['singular']}." + (f" {unit['plain']}" if unit.get("plain") else "")]
        rules = "; ".join(lc_first(p["plain"].rstrip(".")) for p in g["population"])
        out.append(f"Keep {unit['plural']} that meet every rule, in order: {rules}.")
        out.append(f"Time zero is the {lc_first(anchor.get('label', 'start'))}: {anchor['plain']}")
        for w in g["windows"]:
            out.append(f"{w['label']} ({w['role']}): {window_phrase(w, anchor.get('label', 'time zero'))}.")
        for m in g["measures"]:
            w = self.windows.get(m["window"], {})
            tag = " (headline)" if m is self.primary_measure else ""
            kind = {"indicator": "yes/no", "count": "a count", "value": "a value"}[m["kind"]]
            out.append(f"For each {unit['singular']}, record {m['label'].lower()}{tag} as {kind} within the {w.get('label', m['window']).lower()}: {m['plain']}")
        agg = g["aggregate"]
        out.append(agg["plain"] if agg["plain"].endswith(".") else agg["plain"] + ".")
        if g.get("groups"):
            out.append("Do this separately for each group: " + ", ".join(x["label"] for x in g["groups"]) + ".")
        for key in ("comparison", "adjustment", "uncertainty"):
            if g.get(key):
                out.append(g[key]["plain"].strip())
        return out

    def recompute(self) -> tuple[float | None, str]:
        """Recompute the comparison from `results.cells`. Returns (value, formula-with-numbers)."""
        comp = self.g.get("comparison")
        cells = self.cells
        if not comp:
            return None, ""
        kind = comp["kind"]
        try:
            if kind == "difference_in_differences":
                v = {}
                for g in self.g["groups"]:
                    v[(g.get("role"), g.get("period"))] = cells[g["id"]]["value"]
                fp, fq = v[("focal", "post")], v[("focal", "pre")]
                bp, bq = v[("baseline", "post")], v[("baseline", "pre")]
                val = (fp - fq) - (bp - bq)
                return val, f"({fp:g} − {fq:g}) − ({bp:g} − {bq:g}) = {val:.3f}"
            treated = (self.group_by_role("treated", "focal") or [None])[0]
            other = (self.group_by_role("adjusted_control") or self.group_by_role("control", "comparison", "baseline") or [None])[0]
            if treated and other:
                a, b = cells[treated["id"]]["value"], cells[other["id"]]["value"]
                if kind == "ratio":
                    return a / b, f"{a:g} ÷ {b:g} = {a / b:.3f}"
                return a - b, f"{a:g} − {b:g} = {a - b:.3f}"
        except (KeyError, ZeroDivisionError):
            return None, ""
        return None, ""

    def maturity(self) -> dict:
        r = self.raw["results"]
        through, latest = r.get("data_complete_through"), r.get("latest_anchor")
        outcome = [w for w in self.g["windows"] if w["role"] in ("outcome", "observation", "exposure")]
        if not outcome:
            return {"status": "n/a", "text": "No forward-looking window."}
        last = max(outcome, key=lambda w: to_days(w["end"], w["unit"]))
        if not (through and latest):
            return {"status": "unknown", "text": "The card does not state when the data were complete, so we cannot confirm every window was fully observed."}
        try:
            a = date.fromisoformat(latest[:10])
            t = date.fromisoformat(through[:10])
        except ValueError:
            return {"status": "unknown", "text": "Dates could not be read."}
        if last["unit"] == "month":
            needed = add_months(a, last["end"]) - timedelta(days=1)
        else:
            needed = a + timedelta(days=int(to_days(last["end"], last["unit"])) - 1)
        ok = needed <= t
        return {
            "status": "ok" if ok else "immature",
            "text": (f"The latest {lc_first(self.g['anchor'].get('label', 'start'))} is {a:%d %b %Y}; its {lc_first(last['label'])} ends {needed:%d %b %Y}. "
                     f"Data are complete through {t:%d %b %Y}, so "
                     + ("every window is fully observed. This number should not move as more data arrive." if ok
                        else "some windows are not yet complete. Expect this number to change.")),
        }

    def teachback(self) -> list[tuple[str, str]]:
        g = self.g
        items = [("Who is counted", "; ".join(lc_first(p["plain"].rstrip(".")) for p in g["population"][:3]))]
        out_w = [w for w in g["windows"] if w["role"] == "outcome"]
        if out_w:
            items.append(("Over what time", f"{out_w[0]['label']}: {window_phrase(out_w[0], g['anchor'].get('label', 'time zero'))}"))
        items.append(("What counts", self.primary_measure["plain"]))
        if g.get("comparison"):
            items.append(("Compared with what", g["comparison"]["plain"]))
        items.append(("The main limitation", self.raw["gist"]["key_caveat"]))
        return items

    def reading_minutes(self, section: str) -> int:
        def words(x) -> int:
            if isinstance(x, str):
                return len(x.split())
            if isinstance(x, dict):
                return sum(words(v) for v in x.values())
            if isinstance(x, list):
                return sum(words(v) for v in x)
            return 0
        parts = {
            "gist": [self.raw["gist"]],
            "build": [self.g, self.raw.get("example", {})],
            "mind": [self.raw["fine_print"]],
            "reproduce": [self.raw["spec"]],
        }[section]
        return max(1, round(words(parts) / 200))


JARGON = [
    "DiD", "difference-in-differences", "IPTW", "IPW", "ATT", "ATE", "propensity", "bootstrap", "SMD",
    "cohort", "confidence interval", "CI", "p-value", "pp", "percentage point", "parallel trends",
    "estimand", "covariate", "counterfactual", "regression", "winsoris", "MAU", "WAU", "fiscal",
    "correlation", "Pearson", "phi", "censor", "denominator", "numerator", "median", "quantile",
    "standard deviation", "significan", "treatment", "control group", "matched", "weighted",
]


STEMS = {"winsoris", "significan", "censor"}


COMMON_CAPS = {"US", "UK", "EU", "OK", "AM", "PM", "ID", "FAQ", "PDF", "USD", "AND", "OR", "NOT"}


def jargon_in(text: str) -> list[str]:
    text = re.sub(r"`[^`]*`", "", text)
    hits = [a for a in dict.fromkeys(re.findall(r"\b[A-Z][A-Z0-9]{1,}\b", text)) if a not in COMMON_CAPS]
    for j in JARGON:
        pat = r"\b" + re.escape(j) + ("" if j in STEMS else r"\b")
        case_sensitive = any(ch.isupper() for ch in j) or j in ("pp", "phi")
        if j not in hits and re.search(pat, text, flags=0 if case_sensitive else re.I):
            hits.append(j)
    return hits

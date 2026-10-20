"""Static SVG figures generated from a card's grammar. No external libraries; styled by CSS classes."""
from __future__ import annotations

import math
from html import escape
from statistics import NormalDist

from .model import Card, fmt, to_days, window_range

W = 760
CHAR = 6.6  # approx px per char at 12px system-ui


def _t(x, y, text, cls="v-label", anchor="start", extra=""):
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="{anchor}" {extra}>{escape(str(text))}</text>'


def _svg(h, body, label, w=None):
    w = w or W
    return (f'<svg viewBox="0 0 {w} {h:.0f}" role="img" aria-label="{escape(label)}" '
            f'xmlns="http://www.w3.org/2000/svg" class="fig">{body}</svg>')


def nice_ticks(lo, hi, n=5):
    if hi == lo:
        hi = lo + 1
    span = hi - lo
    step = 10 ** math.floor(math.log10(span / n))
    for m in (1, 2, 2.5, 5, 10):
        if span / (step * m) <= n:
            step *= m
            break
    start = math.floor(lo / step) * step
    ticks, v = [], start
    while v <= hi + step * 1e-9:
        if v >= lo - step * 1e-9:
            ticks.append(round(v, 10))
        v += step
    return ticks


# ---------------------------------------------------------------- timeline

def _segments(intervals, min_gap=20):
    ivs = sorted(intervals)
    clusters = [list(ivs[0])]
    for a, b in ivs[1:]:
        cur = clusters[-1]
        if a - cur[1] <= max(min_gap, 0.25 * (cur[1] - cur[0]) + 8):
            cur[1] = max(cur[1], b)
        else:
            clusters.append([a, b])
    return clusters


def timeline(card: Card, with_example: bool = True, highlight: str | None = None, w: int = W) -> str:
    g = card.g
    wins = [dict(w, s=to_days(w["start"], w["unit"]), e=to_days(w["end"], w["unit"])) for w in g["windows"]]
    events = (card.get("example") or {}).get("events", []) if with_example else []
    ivs = [(w["s"], w["e"]) for w in wins] + [(0, 1)] + [(e["at"], e["at"] + 1) for e in events]
    clusters = _segments(ivs)
    for c in clusters:
        pad = max(1.5, 0.06 * (c[1] - c[0]))
        c[0] -= pad
        c[1] += pad
    left, right, brk = 20, w - 20, 26
    usable = right - left - brk * (len(clusters) - 1)
    lens = [c[1] - c[0] for c in clusters]
    # each cluster gets width proportional to sqrt of its length, so short windows stay legible
    weights = [max(math.sqrt(L), 4) for L in lens]
    widths = [usable * w / sum(weights) for w in weights]
    xs, x = [], left
    for wd in widths:
        xs.append(x)
        x += wd + brk

    def X(d):
        for (a, b), x0, wd in zip(clusters, xs, widths):
            if a <= d <= b:
                return x0 + (d - a) / (b - a) * wd
        best = min(range(len(clusters)), key=lambda i: min(abs(d - clusters[i][0]), abs(d - clusters[i][1])))
        a, b = clusters[best]
        return xs[best] + (min(max(d, a), b) - a) / (b - a) * widths[best]

    parts = []
    top = 34 if events else 14
    lane_h, lane_gap = 30, 10
    axis_y = top + len(wins) * (lane_h + lane_gap) + 6
    # axis
    for (a, b), x0, wd in zip(clusters, xs, widths):
        parts.append(f'<line x1="{x0:.1f}" x2="{x0 + wd:.1f}" y1="{axis_y}" y2="{axis_y}" class="v-axis"/>')
    for i in range(len(clusters) - 1):
        bx = xs[i] + widths[i] + brk / 2
        parts.append(f'<path d="M{bx - 7:.1f},{axis_y + 6} l5,-12 M{bx + 1:.1f},{axis_y + 6} l5,-12" class="v-break"/>')
    # windows
    role_cls = {"outcome": "v-win-outcome", "exposure": "v-win-exposure", "eligibility": "v-win-look",
                "lookback": "v-win-look", "observation": "v-win-outcome"}
    ticks, starts, ends, month_ticks = set(), set(), set(), {}
    for i, win in enumerate(wins):
        y = top + i * (lane_h + lane_gap)
        x0, x1 = X(win["s"]), X(win["e"])
        dim = " v-dim" if highlight and win["id"] != highlight and highlight != "all" else ""
        parts.append(f'<rect x="{x0:.1f}" y="{y}" width="{max(x1 - x0, 3):.1f}" height="{lane_h}" rx="5" class="{role_cls.get(win["role"], "v-win-look")}{dim}"/>')
        rng = window_range(win) if win["unit"] != "month" else f"months {win['start']}–{win['end']}"
        label = f"{win['label']} · {rng}"
        tw = len(label) * CHAR
        if tw + 12 < x1 - x0:
            parts.append(_t(x0 + 8, y + lane_h / 2 + 4, label, "v-label v-on-band" + dim))
        elif x1 + 6 + tw < right:
            parts.append(_t(x1 + 6, y + lane_h / 2 + 4, label, "v-label" + dim))
        else:
            parts.append(_t(x0 - 6, y + lane_h / 2 + 4, label, "v-label" + dim, "end"))
        ticks.update([win["s"], win["e"]]); starts.add(win["s"]); ends.add(win["e"])
        if win["unit"] == "month":
            month_ticks[win["s"]] = f"month {win['start']}"
            month_ticks[win["e"]] = f"month {win['end']}"
    # anchor line
    ax = X(0)
    anchor_label = g["anchor"].get("label", "Time zero")
    parts.append(f'<line x1="{ax:.1f}" x2="{ax:.1f}" y1="{top - (22 if events else 6)}" y2="{axis_y + 4}" class="v-anchor"/>')
    alab = f"{anchor_label} (day 0)"
    aw = len(alab) * CHAR
    if ax - aw / 2 < 4:
        x0 = max(ax - 10, 2)
        parts.append(_t(x0, axis_y + 20, alab, "v-label v-strong", "start"))
        occupied = [(x0, x0 + aw)]
    elif ax + aw / 2 > w - 4:
        x1 = min(ax + 10, w - 2)
        parts.append(_t(x1, axis_y + 20, alab, "v-label v-strong", "end"))
        occupied = [(x1 - aw, x1)]
    else:
        parts.append(_t(ax, axis_y + 20, alab, "v-label v-strong", "middle"))
        occupied = [(ax - aw / 2, ax + aw / 2)]
    # event markers
    for k, e in enumerate(events, 1):
        ex = X(e["at"] + 0.5)
        cls = "v-event-on" if e.get("counts") else "v-event"
        parts.append(f'<circle cx="{ex:.1f}" cy="{top - 14}" r="9" class="{cls}"/>')
        parts.append(_t(ex, top - 10, k, "v-event-num", "middle"))
        parts.append(f'<line x1="{ex:.1f}" x2="{ex:.1f}" y1="{top - 5}" y2="{axis_y}" class="v-event-stem"/>')
    # tick labels at window edges, skipping collisions
    for d in sorted(ticks):
        if d == 0:
            continue
        tx = X(d)
        day = int(round(d)) - (1 if d in ends and d not in starts else 0)
        if day == 0 and d not in month_ticks:
            continue
        text = month_ticks.get(d, f"day {day}")
        tw = len(text) * 6 + 10
        span = (tx - tw / 2, tx + tw / 2)
        if all(span[1] < a or span[0] > b for a, b in occupied) and span[0] > 0 and span[1] < w:
            parts.append(f'<line x1="{tx:.1f}" x2="{tx:.1f}" y1="{axis_y}" y2="{axis_y + 4}" class="v-axis"/>')
            parts.append(_t(tx, axis_y + 20, text, "v-tick", "middle"))
            occupied.append(span)
    h = axis_y + 30
    return _svg(h, "".join(parts), f"Timeline of windows relative to {anchor_label}", w)


# ---------------------------------------------------------------- comparisons

def _label_for(card, gid):
    return card.groups.get(gid, {}).get("label", gid)


def did_chart(card: Card, w: int = W) -> str:
    cells, unit = card.cells, card.result_unit
    roles = {(g.get("role"), g.get("period")): g for g in card.g["groups"]}
    bq, bp = roles[("baseline", "pre")], roles[("baseline", "post")]
    fq, fp = roles[("focal", "pre")], roles[("focal", "post")]
    v = {k: cells[g["id"]]["value"] for k, g in {"bq": bq, "bp": bp, "fq": fq, "fp": fp}.items()}
    cf = v["fq"] + (v["bp"] - v["bq"])
    d = 2 if unit in ("percent", "share") else None
    lo, hi = min(list(v.values()) + [cf]), max(list(v.values()) + [cf])
    pad = (hi - lo) * 0.12
    lo, hi = lo - pad, hi + pad
    H, top, bot = 290, 16, 246
    x_pre, x_post = 78, int(w * 0.50)
    x_lab = x_post + 12
    x_brk = x_post + 150
    year_b, year_f = card.did_series()

    def Y(val):
        return bot - (val - lo) / (hi - lo) * (bot - top)

    p = [f'<line x1="{x_pre}" x2="{x_pre}" y1="{top}" y2="{bot}" class="v-grid"/>',
         f'<line x1="{x_post}" x2="{x_post}" y1="{top}" y2="{bot}" class="v-grid"/>']
    p.append(_t(x_pre, bot + 22, "Before", "v-label v-strong", "middle"))
    p.append(_t(x_post, bot + 22, "After", "v-label v-strong", "middle"))
    for x, a, b in ((x_pre, bq, fq), (x_post, bp, fp)):
        sub = f"{a['label']} · {b['label']}"
        if len(sub) <= 30:  # longer pairs collide with the other column; the legend labels carry the names
            p.append(_t(x, bot + 38, sub, "v-tick", "middle"))
    p.append(f'<line x1="{x_pre}" y1="{Y(v["bq"]):.1f}" x2="{x_post}" y2="{Y(v["bp"]):.1f}" class="v-line-base"/>')
    p.append(f'<line x1="{x_pre}" y1="{Y(v["fq"]):.1f}" x2="{x_post}" y2="{Y(cf):.1f}" class="v-line-cf"/>')
    p.append(f'<line x1="{x_pre}" y1="{Y(v["fq"]):.1f}" x2="{x_post}" y2="{Y(v["fp"]):.1f}" class="v-line-focal"/>')
    for key, x, cls in (("bq", x_pre, "v-dot-base"), ("bp", x_post, "v-dot-base"), ("fq", x_pre, "v-dot-focal"), ("fp", x_post, "v-dot-focal")):
        p.append(f'<circle cx="{x}" cy="{Y(v[key]):.1f}" r="5.5" class="{cls}"/>')
    p.append(f'<circle cx="{x_post}" cy="{Y(cf):.1f}" r="5" class="v-dot-cf"/>')
    p.append(_t(x_pre - 10, Y(v["bq"]) + 4, fmt(v["bq"], unit, decimals=d), "v-label v-base-text", "end"))
    p.append(_t(x_pre - 10, Y(v["fq"]) + 4, fmt(v["fq"], unit, decimals=d), "v-label v-focal-text", "end"))
    # right-hand labels, nudged apart if they collide
    labs = sorted([(Y(v["fp"]), f"{fmt(v['fp'], unit, decimals=d)} {year_f} actual", "v-label v-focal-text v-strong"),
                   (Y(cf), f"{fmt(cf, unit, decimals=d)} {year_f} expected", "v-label v-cf-text"),
                   (Y(v["bp"]), f"{fmt(v['bp'], unit, decimals=d)} {year_b}", "v-label v-base-text")])
    last = -99
    for y, text, cls in labs:
        y = max(y, last + 15)
        p.append(_t(x_lab, y + 4, text, cls))
        last = y
    y1, y2 = Y(cf), Y(v["fp"])
    p.append(f'<path d="M{x_brk - 6},{y1:.1f} H{x_brk} V{y2:.1f} H{x_brk - 6}" class="v-bracket"/>')
    diff = v["fp"] - cf
    du = "pp" if unit in ("percent", "share") else unit
    p.append(_t(x_brk + 8, (y1 + y2) / 2 + 1, fmt(diff, du, signed=True), "v-label v-accent-text v-strong"))
    p.append(_t(x_brk + 8, (y1 + y2) / 2 + 15, "more than expected", "v-tick v-accent-text"))
    return _svg(H, "".join(p), f"Difference-in-differences: change in {year_f} compared with change in {year_b}", w)


def bars_chart(card: Card, w: int = W) -> str:
    cells, unit = card.cells, card.result_unit
    order = [g for g in card.g["groups"] if g["id"] in cells and g.get("role") != "excluded"]
    if not order:
        return ""
    rank = {"treated": 0, "focal": 0, "control": 1, "comparison": 1, "baseline": 1, "adjusted_control": 2}
    order.sort(key=lambda g: rank.get(g.get("role"), 3))
    vals = [cells[g["id"]]["value"] for g in order]
    hi = max(vals) * 1.12 or 1
    left, right = min(230, int(w * 0.3)), w - 130
    row, top = 46, 14
    p = []
    for t in nice_ticks(0, hi, 5):
        if t > hi:
            continue
        x = left + t / hi * (right - left)
        p.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top - 4}" y2="{top + row * len(order)}" class="v-grid"/>')
        p.append(_t(x, top + row * len(order) + 16, fmt(t, unit, decimals=0 if t == int(t) else 1), "v-tick", "middle"))
    ys = {}
    for i, g in enumerate(order):
        y = top + i * row
        v = cells[g["id"]]["value"]
        cls = {"treated": "v-bar-focal", "focal": "v-bar-focal", "adjusted_control": "v-bar-adj"}.get(g.get("role"), "v-bar-base")
        if g.get("role") == "control" and any(o.get("role") == "adjusted_control" for o in order):
            cls = "v-bar-raw"
        wd = v / hi * (right - left)
        p.append(f'<rect x="{left}" y="{y + 8}" width="{wd:.1f}" height="26" rx="4" class="{cls}"/>')
        p.append(_t(left - 10, y + 25, g["label"], "v-label", "end"))
        n = cells[g["id"]].get("n")
        p.append(_t(left + wd + 8, y + 25, fmt(v, unit) + (f"  ·  n={n:,}" if n else ""), "v-label v-strong" if cls == "v-bar-focal" else "v-label"))
        ys[g.get("role")] = (y + 21, left + wd, g["label"])
    h = top + row * len(order) + 26
    val, _ = card.recompute()
    comp = card.g.get("comparison")
    if val is not None and comp and comp["kind"] != "difference_in_differences":
        other = ys.get("adjusted_control") or ys.get("control") or ys.get("comparison") or ys.get("baseline")
        if other:
            unit_d = "pp" if unit in ("percent", "share") else unit
            word = "ratio" if comp["kind"] == "ratio" else "difference"
            txt = (f"{word.capitalize()} vs {other[2]}: "
                   + (f"{val:.2f}×" if comp["kind"] == "ratio" else fmt(val, unit_d, signed=True)))
            p.append(_t(left, h + 14, txt, "v-label v-accent-text v-strong"))
            h += 26
    return _svg(h, "".join(p), "Comparison of groups", w)


def part_of_whole(card: Card, w: int = W) -> str:
    cells, unit = card.cells, card.result_unit
    if len(cells) != 1 or unit not in ("percent", "share"):
        return ""
    c = next(iter(cells.values()))
    share = c["value"] / (100 if unit == "percent" else 1)
    m = card.primary_measure
    left, right, y = 4, w - 4, 30
    wd = (right - left) * share
    n = c.get("n")
    p = [f'<rect x="{left}" y="{y}" width="{right - left}" height="34" rx="6" class="v-bar-rest"/>',
         f'<rect x="{left}" y="{y}" width="{wd:.1f}" height="34" rx="6" class="v-bar-focal"/>',
         _t(left, y - 10, f"{fmt(c['value'], unit)} {m['label'].lower()}" + (f" (about {round(share * n):,} of {n:,})" if n else ""), "v-label v-strong"),
         _t(right, y - 10, f"{fmt(100 - c['value'] if unit == 'percent' else 1 - c['value'], unit)} did not", "v-label", "end")]
    return _svg(y + 50, "".join(p), "Share of the group meeting the rule", w)


def comparison_chart(card: Card, w: int = W) -> str:
    comp = card.g.get("comparison")
    if comp and comp["kind"] == "difference_in_differences":
        try:
            return did_chart(card, w)
        except KeyError:
            return bars_chart(card, w)
    if comp:
        return bars_chart(card, w)
    return part_of_whole(card, w) or bars_chart(card, w)


# ---------------------------------------------------------------- uncertainty

def dotplot(value, low, high, unit, n_dots=20, label="estimate", w: int = W) -> str:
    """Quantile dotplot from a normal approximation to the interval."""
    if low is None or high is None or high <= low:
        return ""
    sd = (high - low) / (2 * 1.959964)
    nd = NormalDist(value, sd)
    qs = [nd.inv_cdf((i + 0.5) / n_dots) for i in range(n_dots)]
    span = high - low
    lo_ax, hi_ax = value - span * 1.1, value + span * 1.1
    if 0 < lo_ax and lo_ax < span * 1.6:
        lo_ax = 0
    if hi_ax < 0 and -hi_ax < span * 1.6:
        hi_ax = 0
    left, right = 30, w - 30
    r = 9

    def X(v):
        return left + (v - lo_ax) / (hi_ax - lo_ax) * (right - left)

    bins: dict[int, int] = {}
    p = []
    base = 120
    for q in qs:
        b = round((X(q) - left) / (2 * r + 1))
        k = bins.get(b, 0)
        bins[b] = k + 1
        cx = left + b * (2 * r + 1)
        p.append(f'<circle cx="{cx:.1f}" cy="{base - r - k * (2 * r + 1):.1f}" r="{r}" class="v-qdot"/>')
    p.append(f'<line x1="{left}" x2="{right}" y1="{base + 4}" y2="{base + 4}" class="v-axis"/>')
    for t in nice_ticks(lo_ax, hi_ax, 6):
        x = X(t)
        if left - 1 <= x <= right + 1:
            p.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{base + 4}" y2="{base + 9}" class="v-axis"/>')
            p.append(_t(x, base + 24, fmt(t, unit, signed=True, decimals=2 if abs(hi_ax - lo_ax) < 2 else 1), "v-tick", "middle"))
    if lo_ax <= 0 <= hi_ax:
        p.append(f'<line x1="{X(0):.1f}" x2="{X(0):.1f}" y1="{base - 80}" y2="{base + 4}" class="v-zero"/>')
        p.append(_t(X(0), base - 84, "no difference", "v-tick", "middle"))
    return _svg(base + 34, "".join(p), f"Twenty equally likely values for the {label}", w)


def sensitivity(card: Card, w: int = W) -> str:
    rows = card["results"].get("sensitivity", [])
    if not rows:
        return ""
    unit = (card["gist"].get("headline") or {}).get("unit") or card.result_unit
    vals = [x for r in rows for x in (r["value"], r.get("low", r["value"]), r.get("high", r["value"]))]
    lo, hi = min(vals + [0]), max(vals + [0])
    if hi == lo:
        lo, hi = lo - 1, hi + 1
    pad = (hi - lo) * 0.08
    lo, hi = lo - pad, hi + pad
    left, right, row, top = 280, w - 30, 38, 12

    def X(v):
        return left + (v - lo) / (hi - lo) * (right - left)

    p = []
    for t in nice_ticks(lo, hi, 5):
        x = X(t)
        p.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top - 4}" y2="{top + row * len(rows)}" class="v-grid"/>')
        p.append(_t(x, top + row * len(rows) + 16, fmt(t, unit, signed=True, decimals=1 if hi - lo > 1 else 2), "v-tick", "middle"))
    if lo < 0 < hi:
        p.append(f'<line x1="{X(0):.1f}" x2="{X(0):.1f}" y1="{top - 6}" y2="{top + row * len(rows)}" class="v-zero"/>')
    for i, r in enumerate(rows):
        y = top + i * row + row / 2
        cls = "v-dot-focal" if r.get("primary") else "v-dot-base"
        if "low" in r and "high" in r:
            p.append(f'<line x1="{X(r["low"]):.1f}" x2="{X(r["high"]):.1f}" y1="{y:.1f}" y2="{y:.1f}" class="v-whisker{" v-whisker-focal" if r.get("primary") else ""}"/>')
        p.append(f'<circle cx="{X(r["value"]):.1f}" cy="{y:.1f}" r="{7 if r.get("primary") else 6}" class="{cls}"/>')
        label = r["label"] if len(r["label"]) * CHAR < left - 20 else r["label"][: int((left - 30) / CHAR)] + "…"
        p.append(_t(left - 14, y + 4, label, "v-label v-strong" if r.get("primary") else "v-label", "end"))
    return _svg(top + row * len(rows) + 26, "".join(p), "Estimate under alternative reasonable choices", w)

---
name: data-visual-explainer
description: >
  Explain one metric, KPI or reported estimate (a rate, a count, an A/B-test lift, a causal
  effect) so non-specialists read it correctly and specialists can reproduce it. Reads the
  analysis (readout, SQL, notebook, results table), traces the number to the code that produced
  it, records every place where the written definition and the code disagree, and writes a
  Metric Card: a plain-language gist, caveats, likely misreadings and a reproducible spec,
  rendered as an HTML explainer, a one-page label and a Markdown methods section. Use when people
  misquote or misread a number, when asked what a metric actually measures (who is counted, over
  what time window, what counts), to define or document a KPI, to check a metric's documented
  definition against its SQL or code, or to write the methods behind a reported number. Not for
  building charts or dashboards, or for persuasive slides and narratives.
---

# Metric Card

A Metric Card answers two needs with one source file:

- **Literacy.** A motivated non-specialist can say what the number means, what it does not
  mean, and how much to trust it.
- **Reproducibility.** A specialist can rebuild the number from the card alone and can see
  where the description and the code disagree.

The YAML card (`cards/<id>.yaml`, schema `schema/metric_card.schema.yaml`) is the single source
of truth. `python -m mcard build` renders every view from it. Never hand-edit rendered output.

## Procedure

Work in this order. The order is deliberate: plain-language text is written **last**, after the
facts are pinned to code, so the friendly words cannot drift from the real rule.

0. **Set up once.** `<skill>` below means the folder that holds this SKILL.md. Run
   `<skill>/bin/mcard --help`. If it reports a missing package, install the three dependencies
   with `python3 -m pip install pyyaml jinja2 jsonschema` and run it again. You write the card
   yourself from the user's files; do not ask the user to fill in the YAML.
1. **Pick the number.** Find the headline number a reader actually sees: the message that was
   sent, not a later or earlier draft. One card per headline metric. If a result has several
   outcomes, pick the one leadership will repeat and list the others under
   `results.other_measures`. If the metric has never been run, write a **definition-only card**:
   omit `gist.headline`, set `results.status: not_run`, and never invent numbers.
2. **Register sources.** Give every file you rely on an id (`S1`, `S2`…), with line ranges for
   code. Every `exact`, caveat and discrepancy should carry a `src`.
3. **Trace the number to code.** Read the SQL/notebook that produced it. Do not describe the
   metric from a README or readout alone; those are claims to be checked.
4. **Fill `grammar` in order.**
   - `unit`: what one row stands for (person, subscription, session).
   - `population`: eligibility rules in the order applied; add `n_after` where known.
   - `anchor`: time zero. Calendar date (fixed snapshot) or per-unit event (first use).
   - `windows`: integer offsets from time zero, `end` exclusive. Include look-back and exposure
     windows, not just the outcome window.
   - `measures`: what is computed per unit; mark the headline one `primary: true`.
   - `aggregate`: how units become one number per group, with numerator and denominator.
   - `groups`, `comparison`, `adjustment`, `uncertainty` as applicable. Set `comparison.target`
     (ATT, ATE, descriptive). For difference-in-differences, give each group a `role`
     (focal/baseline), a `period` (pre/post) and a `series` naming its line (a place or a year).
5. **Recompute.** Re-derive the headline from the saved outputs (CSV, results table) and record
   it in `spec.reproduce.receipts`. The linter recomputes difference and DiD from `results.cells`
   and fails on a mismatch.
6. **Hunt discrepancies in both directions.**
   - *Description → code:* for every claim in a description (README, readout, comments, spec
     YAML, data dictionary), check the code.
   - *Code → description:* list every filter, join, dedup (`MIN`/first-ever), date boundary and
     exclusion in the code, and check that some description mentions it. A rule that changes
     who is counted but appears in no description is a discrepancy (`described: "Not
     mentioned in any description"`).
   Record each under `fine_print.discrepancies` with `described`, `implemented`, `impact`.
   State unknown impact as unknown; do not guess a size.
7. **Write the fine print.**
   - `caveats` with `effect` (overstates, understates, wider_uncertainty, unknown_direction,
     limits_scope) and `severity`.
   - `misreadings`: at least the ones that apply from: percent vs percentage points; rate vs
     count; who is in the denominator; association vs cause; whose effect (ATT vs ATE);
     immature or still-moving numbers; what an "event" includes.
   - `judgment_calls`: choices a reasonable analyst could have made differently, and what they
     would change.
   - `results.sensitivity`: the same estimand under alternative reasonable choices, if run.
8. **Write the plain layers last.**
   - `gist.sentence`: at most ~45 words, readable at about grade 10, no unexplained jargon. It
     must name who is counted, over what time, and what counts. Give the window as the code
     computes it, with its real boundaries ("on days 0–14 after the trial started", not "within
     14 days" when the end is inclusive).
   - `gist.headline`: value, interval, unit, and a `context` line that gives scale.
   - `gist.frequency`: restate in counts ("about 4 in every 1,000").
   - `gist.reading.say` / `dont_say`: a sentence safe to repeat in a meeting, and the tempting
     wrong one.
   - `gist.key_caveat`: the one limitation a reader of only the first screen must not miss.
   - `gist.claim_strength`: descriptive (one group's level), associational (groups compared,
     no adjustment), quasi-causal (DiD, matching, weighting on observational data), causal
     (randomised).
   - `example`: one concrete person walked through the rules, with events at day offsets. Pick
     a case that teaches a boundary (an event just outside a window, a save that still counts).
9. **Glossary.** Every technical term that appears in plain fields gets an entry with `aliases`.
   The linter flags known jargon in plain text that has no glossary entry.
10. **Quiz.** At least one `gist`, one `verbatim` and one `transfer` question, each aimed at a
    listed misreading.
11. **Lint, render, look.** From any directory, with `<skill>` = the folder holding this SKILL.md
    and `<dir>` = the folder you are working in:
    `<skill>/bin/mcard lint <dir>/cards/<id>.yaml`, then
    `<skill>/bin/mcard build <dir>/cards -o <dir>/site`, then open `<dir>/site/<id>.html` and read
    it as the target reader would. If you cannot open a browser, read the page's text instead; do
    not install browsers or screenshot tools for this step. Fix the card, not the HTML. Start a new
    card with `<skill>/bin/mcard new <id> --dir <dir>/cards`; the linter fails until every TODO is
    replaced.

## Traps seen in practice

Each of these happened in a real authoring run. The linter catches some, not all.

- **Never expand an acronym or name from memory.** Take the expansion from a source file and
  cite it. If no source expands it, leave it unexpanded and say so. (One draft card expanded a
  product acronym from memory, and the expansion did not match the project's own glossary.)
- **Windows are offsets from each unit's own time zero.** A calendar entry period ("first use
  4–10 Jan 2025") is a population rule, not a window.
- **Calendar-month windows use `unit: month`** (e.g. `start: 12, end: 13`). Do not approximate
  them with day counts.
- **`example.events[].counts: true` only for events that count toward the headline measure.**
  Events that put someone in a group (an exposure, a treatment action) are explained in the
  label, not flagged as counting.
- **One caveat per issue, and its `effect` must match its text.** Do not list the same issue
  twice with different directions. If the analysts call an estimate an upper bound, the
  caveat's effect is `overstates`.
- **Claim strength comes from the design as implemented,** not from the readout's wording. A
  readout that says "drives" or "causes" is a claim to check, and often a misreading to list.
- **Unverifiable comparisons** (a number quoted in a readout with no source in the files) are
  stated as unverifiable, not repeated as fact. They belong in `misreadings` or `caveats`, not
  in `results.other_measures`, which is only for measures defined in `grammar.measures`.
- **Definition-only cards carry no result fields.** Planned dates or frontiers go in
  `spec.parameters`, not `results.data_complete_through`.
- **Glossary aliases must not be ordinary words** ("points", "default", "did"); they would be
  linked everywhere.

## Writing rules

- `plain` fields: short sentences, everyday words, no field names. `exact` fields: field names,
  boundaries, inclusive/exclusive, as implemented.
- Always give units. Use "percentage points" for differences between percentages. Co-present
  absolute and relative changes.
- Uncertainty is always shown when it exists. Say what it does not cover (`known_gaps`).
- Never upgrade claim strength in prose beyond `claim_strength`.
- If a fact is unknown, say so in the card. Do not fill gaps with plausible guesses.

## Files

| Path | Role |
|---|---|
| `schema/metric_card.schema.yaml` | Field definitions (JSON Schema in YAML) |
| `cards/*.yaml` | One card per metric |
| `mcard/` | Loader, linter, SVG generators, renderer |
| `docs/content-model.md` | Why each layer and field exists, with evidence |
| `docs/evaluation.md` | How to test a card with real readers |

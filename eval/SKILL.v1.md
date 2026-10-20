---
name: metric-card
description: >
  Turn an analysis (readout, spec, SQL, notebook, results table) into a Metric Card: one metric
  explained at four depths, from a plain-language gist to a reproducible specification, rendered
  as a self-contained HTML explainer, a printable label and a Markdown methods section. Use when
  asked to define, document, explain or "make legible" a metric for a general audience, or to
  write the methods behind a reported number.
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

1. **Pick the number.** Find the headline number a reader actually sees (Slack post, readout,
   dashboard tile). One card per headline metric. If a result has several outcomes, pick the
   one leadership will repeat and list the others under `results.other_measures`.
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
     (ATT, ATE, descriptive).
5. **Recompute.** Re-derive the headline from the saved outputs (CSV, results table) and record
   it in `spec.reproduce.receipts`. The linter recomputes difference and DiD from `results.cells`
   and fails on a mismatch.
6. **Hunt discrepancies.** For every description of the metric (README, readout, comments, spec
   YAML, data dictionary), compare against the code. Record each disagreement under
   `fine_print.discrepancies` with `described`, `implemented`, `impact`. State unknown impact as
   unknown; do not guess a size.
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
     must name who is counted, over what time, and what counts.
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
11. **Lint, render, look.** `python -m mcard lint cards/<id>.yaml`, then
    `python -m mcard build cards -o site`, then open `site/<id>.html` and read it as the target
    reader would. Fix the card, not the HTML.

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

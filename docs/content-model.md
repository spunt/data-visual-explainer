# Content model: why each layer and field exists

A metric card has to do two jobs that usually pull apart. **Literacy:** a motivated
non-specialist should be able to repeat what the number means and what it does not.
**Reproducibility:** a specialist should be able to rebuild the number and see where the
documentation and the code disagree. The design handles both by writing the metric down once,
as structured data, and generating every view from it.

## 1. One grammar for every metric

Most reported metrics are built from the same stages. Writing them as typed stages, instead
of free prose, is what lets the tool draw the right picture for any metric. It also lets the
tool restate the definition mechanically, so the friendly wording can be checked against it.

| Stage | Field | Question it answers | Prior art |
|---|---|---|---|
| Unit | `grammar.unit` | What does one row stand for? | MetricFlow entities |
| Eligibility | `grammar.population[]` (+`n_after`) | Who is in the denominator, rule by rule? | STROBE/CONSORT flow diagrams with counts at each stage |
| Time zero | `grammar.anchor` | When does each unit's clock start? | Target-trial emulation; misaligned time zero causes immortal-time bias (Hernán & Robins) |
| Windows | `grammar.windows[]` | Which days or months, relative to time zero? Start inclusive, end exclusive. | Cohort-retention specs; estimand "variable" |
| Per-unit measure | `grammar.measures[]` | What is recorded for each unit? | ICH E9(R1) "variable" |
| Aggregate | `grammar.aggregate` | How do units become one number? Numerator and denominator. | MetricFlow ratio/simple metrics |
| Groups | `grammar.groups[]` | Which cohorts, periods or arms? | |
| Comparison | `grammar.comparison` (+`target`) | Difference, ratio, DiD, adjusted difference; whose effect (ATT/ATE)? | ICH E9(R1) summary measure; ATT vs ATE confusion |
| Adjustment | `grammar.adjustment` | What was made comparable, and with what diagnostics? | Propensity-weighting reporting |
| Uncertainty | `grammar.uncertainty` (+`known_gaps`) | How sure, and what the interval does not cover? | |

Three checks fall out of the grammar for free, with no hand-written explanation:

- **Recompute.** The linter recomputes difference, ratio and difference-in-differences from
  `results.cells` and fails if the headline disagrees.
- **Maturity.** From `latest_anchor`, the outcome window and `data_complete_through`, the tool
  says whether every window was fully observed, so readers know whether the number can still move.
- **Literal reading.** The definition is re-assembled sentence by sentence from the grammar.
  If it disagrees with the author's summary, the summary is wrong.

## 2. Four depths, each self-sufficient

| Depth | Reader | Contains | Design rule and evidence |
|---|---|---|---|
| 1 · The gist | Everyone | Question; headline with range; one-sentence definition; scale context; natural-frequency restatement; strength of the claim; "safe to say / not this"; the one caveat; one chart | **The first layer must stand alone and not mislead.** Most readers never expand further (NN/g on accordions; Cochrane plain-language summaries use claim → what was measured → limits). The key caveat and claim strength are on screen, not behind a click: buried caveats are poorly retained, and charts alone do not stop readers inferring cause (Xiong et al. 2019; Kale, Wu & Hullman 2021). |
| 2 · How it's built | The curious | A worked example (one person through the rules) **before** the general rules; then step-by-step stages with the visual changing beside them; the literal reading | Worked examples reduce cognitive load for novices (worked-example effect; Krieglstein et al. 2022 meta-analysis). Temporal definitions get a timeline. Each step keeps the precise rule one click away ("Exactly"), with source chips. |
| 3 · Keep in mind | Decision makers | Completeness check; caveats tagged by **direction of bias** (overstates, understates, wider uncertainty, either way, limits scope) and severity; misreadings (wrong → right); judgment calls; sensitivity across reasonable choices; related results | Direction of bias tells the reader which way to discount the number. Misreadings are written as wrong/right pairs so readers see the tempting sentence before they say it. Sensitivity is shown as a plain dot-and-range list, not a specification-curve grid: lay readers have not been shown to read the full grid (evidence gap). |
| 4 · Reproduce it | Specialists | Estimand table (ICH E9(R1) attributes plus time zero and target); **where the description and the code disagree**; every rule as implemented with sources; numbers per group with the recompute check; parameters; lineage; code excerpts with paths; rebuild checklist; receipts; change log; downloadable spec | A methods section for a general reader. Recording disagreements between documentation and code is the most valuable output: in all three pilot cards it surfaced gaps the readouts did not mention. |

## 3. Presentation choices, with the evidence behind them

| Choice | Why | Strength of evidence |
|---|---|---|
| Plain numbers and simple bars by default; **no icon arrays** | Icon arrays show no general comprehension advantage and add effort for numerate readers (Scalia et al. 2021; Tiede & Gaissmaier 2023). Pictograms raise trust more than understanding (Machida et al. 2022). | Moderate |
| Absolute and relative change shown together; "percentage points" spelled out | Relative changes alone are over-read; pp vs % is a common confusion. | Strong |
| Uncertainty always shown, with what it does not cover | Showing numeric uncertainty costs little trust in the number and none in the source (van der Bles et al. 2020, PNAS). | Strong |
| Quantile dotplot ("20 equally likely values") for the headline interval | Supports better-calibrated judgments than bare intervals for lay readers (Kay, Hullman et al.). Static, so it works offline and in print. | Moderate |
| Claim-strength badge (describes / link / points toward cause / supports cause) in layer 1 | Readers over-infer causality from aggregated charts; explicit scaffolding is needed. | Strong (bias); moderate (fix) |
| Glossary as toggletips: keyboard-focusable, dismiss with Escape, hoverable; never `title` attributes | WCAG 2.2 SC 1.4.13; W3C APG tooltip pattern. | Strong |
| Single self-contained HTML file, no network | Shareable by email, Slack or SharePoint; prints; opens years later. | Design choice |
| One-page label view | Printable summary for appendices and decks (Data Nutrition Project label as a pattern). | Design choice |
| Methods view in Markdown | Paste into a readout, Confluence page or paper. | Design choice |

## 4. What the linter enforces

Errors: schema violations; broken references (windows, measures, groups, sources); quiz
answers out of range; headline that disagrees with the recomputed comparison; an immature
outcome window. Warnings: definition over 50 words or above grade 12; jargon or ALL-CAPS
acronyms in plain text without a glossary entry; missing claim strength, ATT/ATE target or
uncertainty gaps; quiz without gist, detail and transfer questions; fewer than two
misreadings; no worked example; unsourced exact rules; unknown completeness.

## 5. Known limits of this design

- Visuals are generated for the comparison kinds in the grammar (none, difference, ratio,
  DiD, adjusted difference). A new kind, such as a regression slope or a survival curve, needs a
  new chart in `mcard/svg.py`.
- The dotplot uses a normal approximation to the reported interval. It is labelled as such.
- Readability is checked with Flesch-Kincaid, which is a weak proxy. Real comprehension needs
  testing with readers; see `evaluation.md`.
- The card is only as accurate as its author's reading of the code. The procedure in
  `SKILL.md` and the linter reduce this risk but cannot remove it.

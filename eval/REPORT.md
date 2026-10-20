# Evaluation report: metric-card skill

Run on 2026-10-04 with a skill-evaluation harness. Acceptance criteria were frozen in
`evaluation-contract.json` **before** any run.

**What you can check from this repository.** The two synthetic cases (`syn-a`, `syn-b`) are
complete: fixtures, answer keys, every run's card, and the grades. The training pilots and the
real holdout were analyses of internal product data and are **withheld**; their rows below are
reported as run but cannot be independently checked. The public worked examples in
`examples/` were added later (2026-10-07) and are not part of this evaluation. After the
evaluation, the fictional product in `syn-b` was renamed because its first name belonged to a real
company; nothing else in the fixtures or keys changed.

## Bottom line

| Question | Answer | Evidence |
|---|---|---|
| Is the output accurate? | **Yes.** Across all 5 skill runs on new analyses: 0 fabrications, correct headline, 8/8 implemented rules, and every planted doc-vs-code gap except one subtle one (fixed in v3, then 5/5). On the withheld real analysis, 23 of 25 audited claims verified, 1 wrong, 0 invented numbers. | `grades/*.json` |
| Does it beat not using the skill? | **On what a skimming reader takes away, clearly. On deep-document accuracy, no: a strong model given the full brief ties it.** After reading only the first layer, readers got 6/6 key answers right with the skill vs 3.5/6 without. The baseline's first layer left a reader believing an A/B result covered "all assigned users" when it did not. | `grades/reader-answers.md` |
| Is it easy to use? | **Yes.** 5 of 5 evaluation runs finished from a one-line request with no questions, lint 0 errors, rendered output. Each friction point they reported was fixed and given a test. | Run replies below |
| Can the checks be trusted? | **Yes, in both directions.** The grader failed both fault-injected cards (wrong headline, wrong window, causal over-claim) and passed the answer key restated as a document. | `grades/grades-syn-a.json` (K, T), `grades-syn-b.json` (A) |

## What was tested

| Split | Case | Why it's hard |
|---|---|---|
| Train | 2 pilot cards on internal product analyses (withheld) | Real, messy analyses; author = v1 skill via agents |
| Selection (dev) | `fixtures/syn-a`: trial conversion | 5 planted doc-vs-code gaps (30 vs 14 days; cohort end; test accounts; refunds; an undocumented first-ever-trial rule) + a causal-claim bait in the readout |
| Final holdout | `fixtures/syn-b`: randomized A/B test | README claims intent-to-treat; code filters after randomization (exposure, ≥1 active day), uses UTC, drops a country. Readout says "causes … for all new users" |
| Final holdout | Real internal analysis (withheld) | Queries never executed, so a correct card has **no number**; several denominators |

Conditions: **no-skill**: same folder and permissions, prompted with the full original brief
(layered, visual, reproducible, for a general audience). That is a strong baseline. **v1**:
the skill as first written. **v2**: revised from the training failures. **v3**: revised once
more from dev evidence, then frozen before the holdout.

## Results

### Accuracy (blind grader with answer key; A1 headline, A2 rules, A3 gaps, A4 no fabrication, A5 no over-claim)

| Case | Condition | A1 | A2 rules | A3 gaps | A4 | A5 |
|---|---|---|---|---|---|---|
| syn-a | no-skill | ✓ | 8/8 | 4/5 | ✓ | ✓ |
| syn-a | v1 | ✓ | 8/8 | 4/5 | ✓ | ✓ |
| syn-a | v2 | ✓ | 8/8 | 4/5 | ✓ | ✓ |
| syn-a | **v3** | ✓ | 8/8 | **5/5** | ✓ | ✓ |
| syn-b (holdout) | no-skill | ✓ | 8/8 | 4/4 | ✓ | ✓ |
| syn-b (holdout) | **v3** | ✓ | 8/8 | 4/4 | ✓ | ✓ (rated "Shows a link", stated the restricted population) |
| control | fault-injected syn-a | ✗ | 7/8 | — | ✗ (8 errors listed) | ✓ |
| control | fault-injected syn-b | ✗ | 8/8 | 4/4 | ✗ (3 errors listed) | ✗ |
| control | answer key as a doc | ✓ | 8/8 | 5/5 | ✓ | ✓ |

Real holdout, withheld (independent auditor with source access, 25 claims each):

| Condition | Verified | Wrong | Unverifiable | Invented numbers | Real gaps found |
|---|---|---|---|---|---|
| no-skill | 23 | 1 (grain omits error-code qualifiers) | 1 | 0 | 3/3 real |
| **v3** | 23 | 1 (put a planned date in a result field) | 1 | 0 | 3/3 real |

The v3 error is now caught by a new lint rule (`not-run-results`, verified against that exact
card). That fix came after the holdout, so the holdout score above does not include it.

### Comprehension (naive reader, first layer only, about 200 words in every condition)

| Case | Key question | no-skill | v3 |
|---|---|---|---|
| syn-a | Exact payment window as computed | "Can't tell" | "Days 0–14, a 15-day inclusive window" |
| syn-b | Who is in the averages | ✗ "all assigned users" | ✓ exposed, non-CN, ≥1 active day |
| syn-b | Can we say it causes +0.21 days for all users? | ½ (right answer, wrong reason) | ✓ "a link, not causation; not pure intent-to-treat" |

Total on gist, detail and claim questions across both synthetic cases: **v3 6/6, no-skill 3.5/6.**
The baseline's long document is accurate, but its opening does not carry the facts that
change the meaning. The skill's first layer is built to (`SKILL.md` step 8, linted).

### Learning without regressions (v1 → v3)

| Failure seen | Where | Fix | Verified |
|---|---|---|---|
| Product acronym expanded from memory | train (pilot) | SKILL v2 trap list | No later run invented an expansion |
| Calendar entry period modelled as a window; months approximated as days | train (retention pilot) | SKILL v2; `unit: month` used | syn-b/real cards model windows correctly |
| `counts` flag on exposure events; contradictory caveats | train | SKILL v2 | Not repeated |
| Undocumented code rule missed (D5) by **every** condition | dev | SKILL v3: hunt code → description too | syn-a v3: 5/5 |
| First layer said "14 days" for an inclusive days 0–14 window | dev | SKILL v3: state real boundaries | syn-a v3 reader: "15-day inclusive" |
| YAML colon broke parsing with a traceback | dev (v1 run) | Friendly line/column error + test | `test_yaml_error_is_friendly` |
| Renderer crashed on a definition-only card with sensitivity rows | holdout (real) | Fixed + regression test | `test_definition_only_card` |
| Planned date in a result field on a definition-only card | holdout (real) | New lint warning + test | `test_not_run_with_result_fields_warns` |

## Ease of use

Every skill run started from: *"Make a metric card for the headline number in `<folder>`.
Follow `<SKILL.md>`."* All 5 evaluation runs completed without asking anything, in 88–113 s (no-skill:
41–93 s). Friction they reported, all fixed: YAML quoting (now a friendly error);
`python -m mcard` needing the project directory (now `bin/mcard` from anywhere); where
readout-only numbers belong (now in the skill); the definition-only crash (fixed).

## Not shown by this evaluation

- **Real human comprehension.** Naive readers here are AI personas, a pre-screen only (persona
  fidelity is poor; see `docs/evaluation.md`). Before a card is marked `validated`, run the
  5-reader teach-back protocol in that file.
- **Automatic routing.** Runs named the skill explicitly. Whether an agent picks it unprompted
  needs an installed skill and a fresh-session trace.
- **Second host or model.** All runs used this host's default model.
- **Cost.** About 25 subagent runs. Dollar cost is unknown.
- **Sample size.** 2 synthetic + 1 real holdout cases. This is enough to show behaviour, not to
  estimate rates.

## Reproduce

```bash
python -m pytest tests -q
bin/mcard lint eval/runs/syn-a-v3/cards eval/runs/syn-b-v3/cards
# Authoring/grading prompts are in evaluation-contract.json; artifacts in runs/, grades in grades/.
# Runs before v3 were linted with the tool as it was then; later lint rules may flag them.
```

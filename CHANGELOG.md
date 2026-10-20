# Changelog

## 0.1.0 (2026-10-20)

First public release.

- **Examples.** Four cards. Two are the skill's unedited output from a blind evaluation on
  synthetic product analyses (an A/B test and a trial-conversion rate). Two are built on public
  data and reproduced from the authors' files with a checksum-pinned download script: Card &
  Krueger (1994) difference-in-differences, and Hernán & Robins' NHEFS inverse-probability
  weighting. All four are rendered in `site/` and published as the live demo.
- **Routing.** The skill description now uses the words people actually say ("what does this
  metric actually measure", people misquoting a number, checking a definition against its SQL),
  covers A/B lifts and causal estimates, and says what it is not for (charts, dashboards,
  persuasive slides).
- **Setup.** A missing Python package now prints the one-line install command instead of a
  traceback, and `SKILL.md` starts with a setup check. `mcard new` prints the exact command to run
  next.
- **Charts.** Difference-in-differences lines are named by the optional `groups[].series` field
  (falling back to `year`), so comparisons between places as well as between years read
  correctly; the y-axis always includes the counterfactual point.
- **Fixes.** `mcard new` creates the target directory if it does not exist; `tools/shoot.py`
  accepts a relative site path.
- **Packaging.** Claude Code plugin and marketplace manifests; tests on Linux in CI.
- **Evaluation.** `eval/` is published for its synthetic cases; rows from internal analyses are
  marked as withheld. The fictional product in one fixture was renamed after the evaluation
  because its first name belonged to a real company.

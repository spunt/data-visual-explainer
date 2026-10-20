# Weight gain from quitting smoking: methods

*Generated from `smoking-cessation-ipw.yaml`. Status: provisional. Owner: data-visual-explainer worked example (public data). Updated 2026-10-07.*

**Question.** If every smoker in this study had quit, how much more weight would they have gained over about ten years than if none had quit?

**Definition.** We followed 1,566 adult smokers from a health check in 1971–75 to a second visit in 1982. We compare weight change in people who quit with people who did not, after reweighting so the two groups match on nine traits.

**Result.** Kg more weight gain from quitting, averaged over everyone in the study: **+3.44** (plausible range +2.41 to +4.47). Without the reweighting the gap is 2.54 kg. Non-quitters gained about 2 kg on their own.
## Population

The unit of analysis is the person (One row per seqn in nhefs.csv (1,629 rows).). Eligibility rules, in the order applied:

1. Adults aged 25–74 who smoked at the first health check and had the basic facts recorded (sex, age, race, weight, height, education, alcohol use, smoking intensity). *Implementation:* Margin note to §12.1. Applied before distribution: nhefs.csv already holds only these 1,629 people, and no code restricts on these fields. (n = 1,629) [S1, S3]
2. Had their weight measured at the 1982 visit. *Implementation:* nhefs.nmv <- nhefs[which(!is.na(nhefs$wt82)),] (chapter12.R line 12). Drops 63 people. (n = 1,566) [S2, S1]

## Time zero and windows

Time zero is the first health check: Each person's first health check, held some time between 1971 and 1975. *Implementation:* Baseline visit 1971–75 (§12.1 margin note). Visit dates are not in nhefs.csv.

| Window | Role | Offsets (start inclusive, end exclusive) | Definition |
|---|---|---|---|
| Time to quit | exposure | [1, 73) months | qsmk = 1 if the person reported in 1982 having quit (§12.1). The quit date is not used; the authors note it is really a time-varying treatment they ignore (Fine Point 12.1). The window shown is the shortest possible gap (1975 → 1982). |
| 1982 visit | observation | [73, 144) months | Follow-up visit in 1982 (§12.1); per-person gap between 73 and 143 months, not recorded in the file. |

## Measures

- **Weight change** (headline) (value, followup): Body weight at the 1982 visit minus body weight at the first health check, in kilograms. *Implementation:* wt82_71 = wt82 − wt71 (kg); matches the difference of the two columns to 1e-14.
- **Quit smoking** (indicator, quit_period): Reported in 1982 having quit smoking. *Implementation:* qsmk (0/1); 403 of 1,566 = 1.

## Aggregation and comparison

Average weight change in each group, with each person counted according to their weight. `Weighted least squares of wt82_71 on qsmk; the intercept is the weighted mean for non-quitters and intercept + slope the weighted mean for quitters.`

| Group | Definition | Value (other) | n |
|---|---|---|---|
| Quitters, reweighted | qsmk = 1, stabilized weights Pr[A=1] / Pr[A=1 \| L]. | 5.221 | 403 |
| Non-quitters, reweighted | qsmk = 0, stabilized weights (1 − Pr[A=1]) / (1 − Pr[A=1 \| L]). | 1.78 | 1,163 |


Compare the two reweighted groups. Because both are made to resemble the whole study, the gap estimates what quitting would do on average across all of these smokers. `θ₁ in E[Y | A] = θ₀ + θ₁A fitted to the pseudo-population (§12.2–12.3).` Target: ATE (average effect if everyone did it).

Recomputed from the group values: `5.221 − 1.78 = 3.441`.

## Adjustment

People who were more likely to quit, given their traits, count for less; people unlikely to quit who did quit count for more. This balances the nine traits across the two groups. Method: Inverse-probability weighting with stabilized weights, average treatment effect. Balances on: sex, race, age (linear and squared), education (5 levels), cigarettes per day (linear and squared), years smoking (linear and squared), exercise (3 levels), how active day to day (3 levels), baseline weight (linear and squared). Logistic model for qsmk on the nine confounders, with squared terms for age, intensity, duration and weight, no interactions (Program 12.3, lines 93–97). Numerator: intercept-only logistic model (403/1566). Diagnostics: Stabilized weights range 0.33 to 4.30 with mean 1.00 (book: 0.33 to 4.30, mean 1.00). Nonstabilized weights range 1.05 to 16.7 with mean 2.00. Program 12.2 tabulates one stratum (white women, by age) as a positivity check; the book recommends checking that stabilized weights average 1.

## Uncertainty

The range 2.4 to 4.5 kg uses a standard formula that allows for the weighting. The authors describe it as slightly wider than necessary. geeglm(wt82_71 ~ qsmk, weights = sw, id = seqn, corstr = "independence"); β ± 1.96 SE. Reproduced with weighted least squares and HC0 standard errors: SE 0.525. **Not covered:** Treats the propensity model as correct and the weights as known. It does not cover unmeasured confounding, the selection of people who survived to 1982, or the 63 people with no 1982 weight.

## Estimand

| Attribute | Specification |
|---|---|
| Population | NHEFS participants aged 25–74 who smoked at the 1971–75 baseline visit, met the book's completeness restrictions, and had weight measured at the 1982 follow-up. |
| Exposure | Reported having quit smoking by the 1982 follow-up (qsmk = 1) vs not. |
| Time zero | Baseline visit, 1971–75. |
| Variable | Weight at follow-up minus weight at baseline, kg (wt82_71). |
| Intercurrent events | Death or loss to follow-up before 1982 excludes the person from treatment classification (Fine Point 12.1); 63 eligible people lack a 1982 weight and are excluded from the headline. |
| Summary | Difference in IP-weighted means, E[Y^{a=1}] − E[Y^{a=0}], kg; robust 95% interval. |

## Sensitivity

| Specification | Estimate | Interval | Note |
|---|---|---|---|
| No adjustment (raw difference) | 2.54 | [1.66, 3.43] | Program 12.1: quitters 4.53 kg, non-quitters 1.98 kg. |
| Stabilized weights (headline) (headline) | 3.44 | [2.41, 4.47] |  |
| Nonstabilized weights | 3.44 | [2.41, 4.47] | Program 12.2; same estimate here. |
| Also weighting for missing 1982 weights | 3.5 | [2.47, 4.53] | Program 12.7; book: 3.5 (2.5, 4.5). |

## Limitations

- **Only as good as the nine traits** (could push the number either way; high). Reweighting removes differences in the nine measured traits. If something else, such as health worries, made people both quit and gain weight, it is still mixed into the number.
- **Survivors only** (could push the number either way; medium). Only people who lived to 1982 and came back could report quitting. If quitting affects survival, the groups are selected after the fact. The authors flag this and leave it unfixed.
- **Quitting happened at different times** (limits what the number can be used to conclude; medium). Someone who quit in 1972 and someone who quit just before 1982 both count as quitters. The number averages over very different amounts of time without smoking.
- **The interval is wider than it needs to be** (limits what the number can be used to conclude; low). The robust formula behind 2.4 to 4.5 kg covers the true value more than 95% of the time, according to the authors. It still assumes the model for quitting is right.

## Description vs implementation

- **Who is in the study.** Described: Book margin note: restricted to people with known sex, age, race, weight, height, education, alcohol use and smoking intensity, who answered the medical history questionnaire. Implemented: No code applies these rules. The downloadable nhefs.csv already contains only the 1,629 eligible people; the code's only restriction is a non-missing 1982 weight. Impact: The eligibility rules cannot be checked or varied from the distributed files.
- **Treatment model in the censoring analysis.** Described: §12.6 says the model for being measured in 1982 was fit to all 1,629 people. It does not say the model for quitting was refit. Implemented: Program 12.7 refits the quitting model on all 1,629 people (data = nhefs), not the 1,566 used for the headline. Impact: Small. The censoring-weighted estimate is 3.50 vs 3.44.
- **Input file.** Described: The book's site provides nhefs.csv, NHEFS.xls and nhefs.dta. Implemented: chapter12.R reads "XXXX/nhefs.xls" with readxl; other chapters point to a contributor's local Windows path. Impact: None for the numbers; reproducers must edit the path.
- **Year labels.** Described: Baseline visits ran 1971–75 (§12.1). Implemented: Columns are named wt71 and wt82_71, and chapter15.R labels groups "Quit Smoking 1971-1982". Impact: Cosmetic, but readers of the code may assume a fixed 11-year gap.

## Reproduction

1. python examples/fetch_data.py nhefs-ipw (downloads and checks the data, R code and book).
2. python examples/nhefs-ipw/analysis.py (writes results/estimates.csv and results/weights.csv).

- Receipt: 2026-10-07: stabilized IPW 3.441 (2.411, 4.470); book 3.4 (2.4, 4.5). Weights 0.331–4.298, mean 0.999.
- Receipt: 2026-10-07: unadjusted 2.541 (1.656, 3.425), book 2.5 (1.7, 3.4); Program 12.7 3.496 (2.466, 4.527), book 3.5 (2.5, 4.5).

**Completeness.** The card does not state when the data were complete, so we cannot confirm every window was fully observed.

## Sources

- [S1] `examples/nhefs-ipw/data/hernanrobins_WhatIf_19aug26.pdf`. Hernán & Robins, Causal Inference: What If, chapter 12 (§12.1–12.3, 12.6, Fine Point 12.1)
- [S2] `examples/nhefs-ipw/data/chapter12.R`, lines 9-16, 51-76, 92-122, 231-292
- [S3] `examples/nhefs-ipw/data/nhefs.csv`. 1,629 rows; downloaded from miguelhernan.org/whatifbook
- [S4] `examples/nhefs-ipw/analysis.py`, lines 22-77. Outputs in examples/nhefs-ipw/results/
- [S5] `examples/nhefs-ipw/data/chapter15.R`, lines 11, 82-83

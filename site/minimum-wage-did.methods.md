# Fast-food jobs after New Jersey's 1992 minimum-wage rise: methods

*Generated from `minimum-wage-did.yaml`. Status: provisional. Owner: data-visual-explainer worked example (public data). Updated 2026-10-07.*

**Question.** When New Jersey raised its minimum wage in April 1992, did fast-food restaurants there cut jobs compared with similar restaurants just across the border in Pennsylvania, where the wage did not change?

**Definition.** We counted staff at fast-food restaurants in early 1992 and again late in the year. New Jersey raised its minimum wage on 1 April; nearby Pennsylvania did not. We compare how the average staff per restaurant changed in each state.

**Result.** More full-time-equivalent workers per new jersey restaurant than the pennsylvania trend predicts: **+2.75** (plausible range +0.09 to +5.42). New Jersey restaurants averaged 20.4 full-time-equivalent workers before the rise, so this is about 13% of a typical store.
## Population

The unit of analysis is the restaurant (One row per store in public.dat (410 rows); CHAIN 1 = Burger King, 2 = KFC, 3 = Roy Rogers, 4 = Wendy's. SHEET is documented as the unique store id, but sheet 407 is used by two different stores; rows, not SHEET values, are the unit.). Eligibility rules, in the order applied:

1. Fast-food restaurants in New Jersey and eastern Pennsylvania from four chains that took part in the first telephone survey. *Implementation:* public.dat: 410 stores, STATE = 1 (NJ, 331) or 0 (PA, 79). (n = 410) [S1, S3]
2. Reported staff numbers in that survey round. Each round's average uses every restaurant with a count for that round, so the two rounds are not exactly the same restaurants. *Implementation:* Wave-1 mean over stores with non-missing fte1 (PA 77, NJ 321); wave-2 mean over stores with non-missing fte2 (PA 77, NJ 319). "All available observations" (Table 3 rows 1–2). [S1, S5]
3. Restaurants that closed for good by the second round count as having zero staff. The four that were closed only temporarily are left out of the second round. *Implementation:* STATUS2 = 3 (6 stores): wave-2 employment fields are already 0 in public.dat. STATUS2 in (2, 4, 5) (4 stores, all NJ): wave-2 fields missing, so excluded from the wave-2 mean. [S1, S3, S6]

## Time zero and windows

Time zero is the wage rise: New Jersey's minimum wage went from $4.25 to $5.05 an hour on 1 April 1992. *Implementation:* 1992-04-01 (paper, introduction and section I). Pennsylvania stayed at the federal $4.25.

| Window | Role | Offsets (start inclusive, end exclusive) | Definition |
|---|---|---|---|
| First survey round | observation | [-46, -27) days | Wave 1: February 15 – March 4, 1992 (Table 1). |
| Second survey round | outcome | [218, 275) days | Wave 2: November 5 – December 31, 1992 (Table 1); DATE2 in the file spans 110592–123192. |

## Measures

- **Staff before** (value, wave1): Full-time workers, including managers, plus half the number of part-time workers. *Implementation:* EMPTOT = EMPPT*.5 + EMPFT + NMGRS (check.sas line 54).
- **Staff after** (headline) (value, wave2): The same count, taken in the second survey round. *Implementation:* EMPTOT2 = EMPPT2*.5 + EMPFT2 + NMGRS2 (check.sas line 55).

## Aggregation and comparison

Average the staff count over restaurants in each state and survey round. `PROC MEANS of EMPTOT and EMPTOT2 BY NJ (check.sas lines 128–131, 'PART OF TABLE 3').`

| Group | Definition | Value (other) | n |
|---|---|---|---|
| Pennsylvania, Feb–Mar | STATE = 0, non-missing EMPTOT (n = 77). | 23.3312 | 77 |
| Pennsylvania, Nov–Dec | STATE = 0, non-missing EMPTOT2 (n = 77). | 21.1656 | 77 |
| New Jersey, Feb–Mar | STATE = 1, non-missing EMPTOT (n = 321). | 20.4394 | 321 |
| New Jersey, Nov–Dec | STATE = 1, non-missing EMPTOT2 (n = 319). | 21.0274 | 319 |


Take New Jersey's change in average staff between the two rounds. Subtract Pennsylvania's change over the same months. What is left is the change Pennsylvania's path does not explain. `(NJ wave 2 − NJ wave 1) − (PA wave 2 − PA wave 1), FTE per store (Table 3, row 3, column iii).` Target: ATT (effect among those who actually did it (not everyone)).

Recomputed from the group values: `(21.0274 − 20.4394) − (21.1656 − 23.3312) = 2.754`.

## Uncertainty

The paper reports a t statistic of 2.03 for this number. We turned that into a 95% range of 0.09 to 5.42 workers. The paper does not say how it computed the spread. SE = 2.76 / 2.03 ≈ 1.36 (paper, section III.A); interval = 2.754 ± 1.96 × 1.36. Treating the four state-by-round means as independent gives SE 1.80 (interval −0.78 to 6.28). The balanced-sample change (row 4) gives SE 1.34. **Not covered:** The calculation behind the published spread is not stated, and check.sas does not compute it. Restaurants appear in both rounds, so the four averages are not independent; the simplest formula that ignores this gives a range that includes zero. Nothing here covers the assumption that both states would have moved alike.

## Estimand

| Attribute | Specification |
|---|---|
| Population | Burger King, KFC, Wendy's and Roy Rogers restaurants in New Jersey and eastern Pennsylvania in the 1992 sample frame that responded in wave 1 and reported employment in the given wave. |
| Exposure | Being in New Jersey when its minimum wage rose from $4.25 to $5.05 on 1992-04-01. |
| Time zero | 1992-04-01. |
| Variable | FTE employment per store = full-time + managers + 0.5 × part-time, in wave 2 (Nov 5 – Dec 31, 1992) minus wave 1 (Feb 15 – Mar 4, 1992). |
| Intercurrent events | Permanent closures count as zero employment; temporary closures (4) are missing in wave 2. |
| Summary | Difference in state mean changes (unbalanced means), FTE workers per store; interval from the published t statistic. |

## Sensitivity

| Specification | Estimate | Interval | Note |
|---|---|---|---|
| Same restaurants in both rounds (row 4) | 2.75 | [0.12, 5.38] | 384 restaurants with a count in both rounds; SE 1.34. |
| All restaurants with a count (row 3, headline) (headline) | 2.75 | [0.09, 5.42] |  |
| Temporarily closed counted as zero (row 5) | 2.51 | [-0.13, 5.15] | Paper: 'only slightly smaller'. |
| Regression, Table 4 sample | 2.33 | [0.0, 4.66] | 357 restaurants with wage data in both rounds; coefficient 2.33 (SE 1.19). |

## Limitations

- **Pennsylvania fell more than New Jersey rose** (limits what the number can be used to conclude; high). New Jersey's average went up by 0.59 workers while Pennsylvania's fell by 2.17. Most of the gap is Pennsylvania shrinking. The paper attributes this to a worsening regional economy, which the design assumes hit both states equally.
- **The spread depends on an unstated calculation** (the true uncertainty is larger than shown; medium). The published t statistic implies a 95% range of about 0.1 to 5.4 workers. A simple calculation that treats the two rounds as separate samples gives −0.8 to 6.3, which includes no effect. Counting only restaurants seen in both rounds gives 0.1 to 5.4 again.
- **Self-reported counts from a phone survey** (the true uncertainty is larger than shown; medium). Managers reported staff numbers by phone. The paper estimates the reliability of this measure at 0.70 by reinterviewing a subset of stores, so some changes are noise.
- **One region, one industry, one rise** (limits what the number can be used to conclude; medium). This is four fast-food chains in New Jersey and eastern Pennsylvania in 1992, after an 80-cent rise. It says nothing directly about other industries, larger rises or other places.

## Description vs implementation

- **Store identifier.** Described: Codebook: SHEET is the 'sheet number (unique store id)'. Implemented: Sheet 407 appears twice in public.dat: a Pennsylvania KFC and a New Jersey Wendy's. Impact: Anyone deduplicating or joining on SHEET loses or mixes one store. The paper's averages, which treat rows as stores, are unaffected.
- **Where closed stores become zero.** Described: Table 3 note: 'Employment at six closed stores is set to zero.' Implemented: check.sas never sets anything to zero; the six STATUS2 = 3 rows already carry 0 in the wave-2 employment fields of public.dat. Impact: None for the published numbers. A re-analysis that recodes STATUS2 itself, or treats 0 as missing, will silently change the headline.
- **Headline value.** Described: Text: 'The relative gain … is 2.76 FTE employees (or 13 percent), with a t statistic of 2.03.' Implemented: The public data give 2.754, which rounds to 2.75. Rows 4 and 5 and Table 4 reproduce to the published decimals. Impact: Rounding only. It is likely the text was computed from rounded table entries.
- **How the headline's uncertainty was computed.** Described: A t statistic of 2.03; no method given. Implemented: check.sas computes only per-state means (PROC MEANS), not the standard error of the difference. The independent-samples formula gives t = 1.53; the balanced-sample formula gives t = 2.05. Impact: Unknown. It decides whether the headline is distinguishable from zero.
- **Restaurants without a starting wage.** Described: Table 3 notes give New Jersey wage-group counts of 101, 140 and 73. Implemented: Those sum to 314 of 331 New Jersey stores. The 17 with no wave-1 starting wage go to check.sas's 'NJ STORE, BAD WAGE' group and are not mentioned in the text. Impact: Affects only the within-New Jersey columns (iv)–(viii), not the headline.

## Reproduction

1. python examples/fetch_data.py minimum-wage (downloads and checks the data and paper).
2. python examples/minimum-wage/analysis.py (writes results/table3.csv and results/checks.csv).

- Receipt: 2026-10-07: PA 23.33 → 21.17, NJ 20.44 → 21.03; DiD 2.754. Row 4 2.750 (SE 1.342), row 5 2.509.
- Receipt: 2026-10-07: Table 4 column (i) 2.326 (SE 1.192), n = 357, mean change −0.238, SD 8.825; the paper prints 2.33 (1.19), −0.237, 8.825.

**Completeness.** The latest wage rise is 01 Apr 1992; its second survey round ends 31 Dec 1992. Data are complete through 31 Dec 1992, so every window is fully observed. This number should not move as more data arrive.

## Sources

- [S1] `examples/minimum-wage/data/njmin-aer.pdf`. Card & Krueger (1994), AER 84(4): intro, section I, Table 1, section III.A, Tables 3–4 notes
- [S2] `examples/minimum-wage/data/check.sas`, lines 54-59, 128-139, 150-163
- [S3] `examples/minimum-wage/data/codebook`. Column definitions; STATUS2 codes
- [S4] `examples/minimum-wage/data/read.me`. Says the files support Myth and Measurement, chapter 2
- [S5] `examples/minimum-wage/analysis.py`, lines 30-103. Outputs in examples/minimum-wage/results/
- [S6] `examples/minimum-wage/data/public.dat`. 410 rows; downloaded from davidcard.berkeley.edu/data_sets.html

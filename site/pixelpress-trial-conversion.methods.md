# PixelPress Pro mobile trial conversion: methods

*Generated from `pixelpress-trial-conversion.yaml`. Status: provisional. Owner: Growth analytics. Updated 2026-10-04.*

**Question.** What share of people who start a PixelPress Pro free trial become paying subscribers?

**Definition.** Among PixelPress Pro mobile users whose first recorded trial started from 2 through 9 March 2026, 14.3% had a positive charge on days 0-14 after trial start.

**Result.** Mobile trial conversion rate: **14.3%**. 6,894 of 48,210 trial users had a positive charge in the implemented window.
## Population

The unit of analysis is the user (One distinct user_id from app.trial_events after taking MIN(trial_start_date) per user for product = 'PIXELPRESS_PRO' and platform IN ('ios', 'android').). Eligibility rules, in the order applied:

1. Users with at least one PixelPress Pro trial event on iOS or Android. *Implementation:* app.trial_events rows where product = 'PIXELPRESS_PRO' and platform IN ('ios', 'android'). [S3]
2. Each user is assigned their first recorded PixelPress Pro mobile trial date. *Implementation:* The trials CTE groups by user_id and sets trial_start_date to MIN(t.trial_start_date). [S3]
3. The first recorded trial date is from 2 through 9 March 2026. *Implementation:* cohort keeps rows where trial_start_date BETWEEN DATE '2026-03-02' AND DATE '2026-03-09', inclusive. (n = 48,210) [S3, S4]

## Time zero and windows

Time zero is the first recorded trial start: Each user's clock starts on their first recorded PixelPress Pro mobile trial date. *Implementation:* trial_start_date is MIN(t.trial_start_date) per user_id from the trials CTE.

| Window | Role | Offsets (start inclusive, end exclusive) | Definition |
|---|---|---|---|
| Positive-charge window | outcome | [0, 15) days | b.charge_date BETWEEN c.trial_start_date AND DATE_ADD(c.trial_start_date, p.conversion_days), with conversion_days = 14. Because BETWEEN is inclusive, this is day offsets 0 through 14. |

## Measures

- **Had a positive charge** (headline) (indicator, charge_days_0_14): Counts a user if they had at least one charge above zero dollars in the window. *Implementation:* first_charge joins billing.charges where b.user_id = c.user_id, b.amount_usd > 0, and b.charge_date falls in the inclusive charge window, then groups to MIN(b.charge_date). The final summary counts DISTINCT f.user_id.

## Aggregation

Divide users with a positive charge by all users in the implemented cohort. `ROUND(100.0 * COUNT(DISTINCT f.user_id) / COUNT(DISTINCT c.user_id), 2) AS conversion_rate_pct.`

| Group | Definition | Value (percent) | n |
|---|---|---|---|
| March 2026 first-trial mobile cohort | product = 'PIXELPRESS_PRO', platform IN ('ios', 'android'), MIN(trial_start_date) BETWEEN DATE '2026-03-02' AND DATE '2026-03-09'. | 14.3 | 48,210 |


## Uncertainty

No confidence interval or standard error was reported for the 14.3% headline. conversion_summary.csv reports trial_users, converted_users, conversion_rate_pct, run_date, and data_complete_through only. **Not covered:** Random uncertainty, data-quality uncertainty, and uncertainty from the definition discrepancies are not quantified.

## Estimand

| Attribute | Specification |
|---|---|
| Population | Users whose earliest recorded PixelPress Pro iOS or Android trial started from 2026-03-02 through 2026-03-09, inclusive. |
| Exposure | None. This is a single-cohort descriptive rate. |
| Time zero | Each user's earliest recorded PixelPress Pro mobile trial_start_date. |
| Variable | Indicator for at least one billing.charges row with amount_usd > 0 and charge_date on day offsets 0 through 14 after time zero. |
| Intercurrent events | Refunds, internal/test status, and later trial starts are not handled in the saved SQL except that later trial starts do not change time zero. |
| Summary | Proportion of implemented-cohort users with converted_to_paid = 1, reported as a percent rounded to two decimals. |

## Limitations

- **The saved SQL is not a 30-day metric** (may make the number look smaller than it really is; high). The README and readout define conversion as payment within 30 days, but the SQL parameter is 14 and the inclusive date comparison counts days 0-14.
- **The cohort end date differs** (could push the number either way; high). The README says the cohort runs through 8 March, while the SQL includes first recorded trial starts through 9 March.
- **Described exclusions are not visible in SQL** (could push the number either way; high). The README says internal, test, and refunded accounts are excluded, but the SQL shown here only requires amount_usd > 0 and does not filter internal users, test users, or refunds.
- **The February comparison is not reproducible from these files** (limits what the number can be used to conclude; medium). The readout quotes a 12.9% February rate and a 1.4-point lift, but the fixture includes no February result, comparison SQL, or uncertainty.
- **No uncertainty interval saved** (the true uncertainty is larger than shown; low). The saved output reports a point estimate only. It does not include a confidence interval, standard error, or sensitivity run.

## Description vs implementation

- **Outcome window length.** Described: README and readout define conversion as paying within 30 days of trial start. Implemented: params sets conversion_days = 14, and first_charge keeps charge_date BETWEEN trial_start_date AND DATE_ADD(trial_start_date, 14), inclusive. Impact: A shorter window likely understates the 30-day conversion rate. The size is unknown from the saved files.
- **Cohort date range.** Described: README says trials started 2026-03-02 through 2026-03-08. Implemented: SQL sets cohort_end to DATE '2026-03-09' and uses BETWEEN, so 9 March starts are included. Impact: The implemented denominator can include an extra start date. Direction and size are unknown.
- **Internal and test account exclusions.** Described: README says internal and test accounts are excluded. Implemented: No internal-account or test-account filter appears in the saved SQL. Impact: If such accounts exist in app.trial_events, they remain in the result. Direction and size are unknown.
- **Refund exclusion.** Described: README says refunded charges do not count. Implemented: SQL joins billing.charges with b.amount_usd > 0, but shows no refund, reversal, or net-paid filter. Impact: Refunded positive charges could overstate net-paid conversion. The size is unknown.
- **First trial versus any trial.** Described: Descriptions say users who started a trial in the cohort week. Implemented: SQL first takes MIN(trial_start_date) per user across PixelPress Pro mobile trial events, then filters that first recorded trial into the cohort. Impact: Users with an earlier PixelPress Pro mobile trial and another trial in March are excluded. Direction and size are unknown.
- **Onboarding lift claim.** Described: The readout says the new onboarding is driving a 1.4-point lift and recommends rolling it out to web. Implemented: The saved SQL computes a single March cohort rate only. No February cohort SQL, web cohort, counterfactual, adjustment, or uncertainty is included. Impact: The fixture supports a descriptive March rate, not a causal onboarding claim or web rollout inference.

## Reproduction

1. Run sql/trial_conversion.sql against the app.trial_events and billing.charges tables.
2. Save the one-row summary to results/conversion_summary.csv.
3. Recompute converted_users / trial_users * 100 from the saved CSV.

- Receipt: conversion_summary.csv reports 48,210 trial users, 6,894 converted users, and 14.30%.
- Receipt: Independent arithmetic: 6,894 / 48,210 * 100 = 14.2999%, which rounds to 14.30%.

**Completeness.** The latest first recorded trial start is 09 Mar 2026; its positive-charge window ends 23 Mar 2026. Data are complete through 17 Apr 2026, so every window is fully observed. This number should not move as more data arrive.

## Sources

- [S1] `eval/fixtures/syn-a/README.md`, lines 1-21. Question, prose definition, cohort dates, exclusions, and file list
- [S2] `eval/fixtures/syn-a/readout.md`, lines 1-9. Headline, February comparison, onboarding claim, and 30-day definition
- [S3] `eval/fixtures/syn-a/sql/trial_conversion.sql`, lines 1-43. Implemented cohort, charge window, and aggregation
- [S4] `eval/fixtures/syn-a/results/conversion_summary.csv`, lines 1-2. Saved result row

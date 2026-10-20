# PixelPress Pro mobile trial conversion rate: methods

*Generated from `pixelpress-mobile-trial-conversion.yaml`. Status: provisional. Owner: Growth analytics. Updated 2026-10-04.*

**Question.** What share of people who started a PixelPress Pro mobile free trial in the March cohort became paying users?

**Definition.** Among users whose first PixelPress Pro mobile trial started from 2 to 9 March 2026, 14.3% had a positive first charge from trial day 0 through day 14.

**Result.** Mobile trial users who converted to paid: **14.3%**. 6,894 of 48,210 users in the implemented March cohort had a qualifying charge.
## Population

The unit of analysis is the user (One DISTINCT t.user_id from app.trial_events after grouping all PIXELPRESS_PRO iOS or Android trial events to that user's MIN(trial_start_date).). Eligibility rules, in the order applied:

1. Users with a PixelPress Pro trial on iOS or Android. *Implementation:* app.trial_events rows where product = 'PIXELPRESS_PRO' and platform IN ('ios', 'android'), grouped to one row per user_id. [S3]
2. Keep users whose first recorded qualifying trial started from 2 to 9 March 2026. *Implementation:* MIN(t.trial_start_date) AS trial_start_date per user_id, then trial_start_date BETWEEN DATE '2026-03-02' AND DATE '2026-03-09', inclusive. (n = 48,210) [S3, S4]

## Time zero and windows

Time zero is the trial start: Each user's clock starts on the date their first qualifying mobile trial began. *Implementation:* trial_start_date = MIN(t.trial_start_date) over PIXELPRESS_PRO iOS or Android trial events for that user_id.

| Window | Role | Offsets (start inclusive, end exclusive) | Definition |
|---|---|---|---|
| Implemented charge window | outcome | [0, 15) days | b.charge_date BETWEEN c.trial_start_date AND DATE_ADD(c.trial_start_date, p.conversion_days), where p.conversion_days = 14. The SQL BETWEEN is inclusive, so this covers offsets 0 through 14. |

## Measures

- **Converted to paid** (headline) (indicator, conversion_window): Counts a user if they had at least one positive first charge inside the implemented charge window. *Implementation:* first_charge groups the cohort by user_id and keeps MIN(b.charge_date) where billing.charges.amount_usd > 0 and the charge_date falls in the implemented charge window. The final SELECT counts DISTINCT f.user_id.

## Aggregation

Divide users with a qualifying charge by all users in the implemented trial cohort. `ROUND(100.0 * COUNT(DISTINCT f.user_id) / COUNT(DISTINCT c.user_id), 2) AS conversion_rate_pct after LEFT JOIN first_charge f ON f.user_id = c.user_id.`

| Group | Definition | Value (percent) | n |
|---|---|---|---|
| March mobile trial cohort | Users whose earliest PIXELPRESS_PRO iOS or Android trial_start_date is between 2026-03-02 and 2026-03-09, inclusive. | 14.3 | 48,210 |


## Uncertainty

No confidence interval or error bar was reported for the 14.3% headline. conversion_summary.csv contains trial_users, converted_users, conversion_rate_pct, run_date, and data_complete_through, but no standard error, confidence interval, or test result. **Not covered:** The missing interval covers only random variation. It would not cover the larger definition gaps between the README/readout and SQL.

## Estimand

| Attribute | Specification |
|---|---|
| Population | Users whose earliest supplied PixelPress Pro iOS or Android trial_start_date is 2026-03-02 through 2026-03-09, inclusive. |
| Exposure | None. This card reports one descriptive cohort rate. The new onboarding claim is not identified by the supplied SQL or CSV. |
| Time zero | Each user's first qualifying mobile trial_start_date. |
| Variable | Indicator for at least one billing.charges row for the same user_id with amount_usd > 0 and charge_date from trial_start_date through trial_start_date + 14 days, inclusive. |
| Intercurrent events | Refunds, test-account status, internal-account status, and web rollout eligibility are not handled in the supplied SQL. |
| Summary | COUNT(DISTINCT converted user_id) divided by COUNT(DISTINCT cohort user_id), reported as a percentage rounded to two decimals. |

## Limitations

- **Prose definition does not match the SQL** (limits what the number can be used to conclude; high). The README and readout call this a 30-day conversion rate, but the SQL parameter is 14 and the implemented inclusive window is trial day 0 through day 14.
- **Exclusions are claimed but not implemented in this SQL** (could push the number either way; high). The README says internal and test accounts are excluded and refunded charges do not count. The SQL shown here has no internal/test-account filter and counts charges with amount_usd greater than zero.
- **Onboarding lift is not supported by the supplied code** (limits what the number can be used to conclude; high). The readout says conversion rose from 12.9% in February and attributes a 1.4-point lift to onboarding. The supplied SQL and CSV only show the March conversion rate.
- **Cohort end date differs** (could push the number either way; medium). The README says the cohort runs through 8 March, while the SQL includes trial starts through 9 March.
- **No uncertainty interval saved** (the true uncertainty is larger than shown; low). The saved output does not include a confidence interval or statistical test, so the card cannot show sampling uncertainty.

## Description vs implementation

- **Conversion window.** Described: README and readout define conversion as paying within 30 days of trial start. Implemented: SQL sets conversion_days = 14 and uses charge_date BETWEEN trial_start_date and DATE_ADD(trial_start_date, 14), inclusive. Impact: The implemented metric likely understates a true 30-day conversion rate. The size is unknown from the supplied output.
- **Cohort end date.** Described: README says trials started 2026-03-02 through 2026-03-08. Implemented: SQL sets cohort_end = DATE '2026-03-09' and uses BETWEEN, so 9 March is included. Impact: Adds one extra start date relative to the README. Direction and size are unknown because no daily breakdown is supplied.
- **Internal and test account exclusions.** Described: README says internal and test accounts are excluded. Implemented: The supplied SQL filters product and platform only in app.trial_events; no internal or test account exclusion appears. Impact: If internal/test users exist in the source tables, they remain in the implemented denominator and may affect the rate. Direction and size are unknown.
- **Refunded charges.** Described: README says paying means a net-paid first charge and refunded charges do not count. Implemented: The supplied SQL joins billing.charges with amount_usd > 0 and does not show refund or net-payment logic. Impact: Refunded positive charges could be counted as conversions. Direction would overstate net-paid conversion if refunds are present; size is unknown.
- **February comparison and onboarding claim.** Described: Readout says 14.3% is up from 12.9% for February and that new onboarding is driving a 1.4-point lift. Implemented: The supplied SQL and CSV contain only the March cohort summary and no February cohort, experiment assignment, adjustment, or causal design. Impact: The supplied evidence supports the March descriptive rate, not the lift estimate or the onboarding causal claim.

## Reproduction

1. Run sql/trial_conversion.sql against the app.trial_events and billing.charges sources.
2. Save the one-row summary with trial_users, converted_users, conversion_rate_pct, run_date, and data_complete_through.
3. Recompute 100 * converted_users / trial_users from results/conversion_summary.csv.

- Receipt: conversion_summary.csv reports trial_users = 48,210, converted_users = 6,894, and conversion_rate_pct = 14.30.
- Receipt: Independent arithmetic from the CSV: 100 * 6,894 / 48,210 = 14.30% when rounded to two decimals.

**Completeness.** The latest trial start is 09 Mar 2026; its implemented charge window ends 23 Mar 2026. Data are complete through 17 Apr 2026, so every window is fully observed. This number should not move as more data arrive.

## Sources

- [S1] `eval/fixtures/syn-a/README.md`, lines 1-21. Question, prose definition, claimed exclusions, result pointer
- [S2] `eval/fixtures/syn-a/readout.md`, lines 1-9. Headline 14.3%, February comparison, onboarding claim, 30-day definition
- [S3] `eval/fixtures/syn-a/sql/trial_conversion.sql`, lines 1-43. Implemented cohort, charge window, numerator, denominator, rate
- [S4] `eval/fixtures/syn-a/results/conversion_summary.csv`, lines 1-2. Saved aggregate output

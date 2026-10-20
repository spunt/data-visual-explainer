# PixelPress Pro mobile trial conversion, March cohort: methods

*Generated from `pixelpress-trial-conversion.yaml`. Status: provisional. Owner: Growth analytics. Updated 2026-04-20.*

**Question.** What share of people who start a PixelPress Pro free trial become paying subscribers?

**Definition.** In the saved March mobile trial group, 14.3% of PixelPress Pro trial users had a positive charge by day 14.

**Result.** Trial users converted to paid: **14.3%**. 6,894 of 48,210 trial users converted in the saved summary.
## Population

The unit of analysis is the trial user (One distinct t.user_id after taking MIN(t.trial_start_date) from app.trial_events where product = 'PIXELPRESS_PRO' and platform IN ('ios', 'android').). Eligibility rules, in the order applied:

1. People who started a PixelPress Pro trial on iOS or Android. *Implementation:* app.trial_events rows where product = 'PIXELPRESS_PRO' and platform IN ('ios', 'android'), grouped to each user's earliest trial_start_date. [S3]
2. Users whose earliest trial start falls in the SQL's March cohort window. *Implementation:* tr.trial_start_date BETWEEN DATE '2026-03-02' AND DATE '2026-03-09'. In SQL, BETWEEN is inclusive, so the implemented cohort includes 2026-03-09. (n = 48,210) [S3, S4]

## Time zero and windows

Time zero is the first trial start: Each user's clock starts on the day they first started a PixelPress Pro mobile trial. *Implementation:* trial_start_date = MIN(t.trial_start_date) per user_id in the trials CTE.

| Window | Role | Offsets (start inclusive, end exclusive) | Definition |
|---|---|---|---|
| March cohort entry | eligibility | [0, 1) days | tr.trial_start_date BETWEEN p.cohort_start AND p.cohort_end. |
| SQL conversion watch window | outcome | [0, 15) days | b.charge_date BETWEEN c.trial_start_date AND DATE_ADD(c.trial_start_date, p.conversion_days), where p.conversion_days = 14. Because BETWEEN is inclusive, this covers offsets 0 through 14. |

## Measures

- **Converted to paid** (headline) (indicator, conversion_window_sql): Counts a trial user if they had at least one positive charge in the SQL outcome window. *Implementation:* first_charge has one row for users with MIN(b.charge_date) after joining billing.charges on user_id with b.amount_usd > 0 inside the conversion window; converted users are COUNT(DISTINCT f.user_id).

## Aggregation

Divide converted trial users by all trial users in the cohort and report it as a percent. `ROUND(100.0 * COUNT(DISTINCT f.user_id) / COUNT(DISTINCT c.user_id), 2) AS conversion_rate_pct.`

| Group | Definition | Value (percent) | n |
|---|---|---|---|
| March 2026 mobile SQL cohort | The SQL parameterizes cohort_start as 2026-03-02 and cohort_end as 2026-03-09, then uses an inclusive BETWEEN filter. | 14.3 | 48,210 |


## Uncertainty

No confidence interval or standard error was reported with the 14.3% headline. conversion_summary.csv reports trial_users, converted_users, conversion_rate_pct, run_date, and data_complete_through only. **Not covered:** Sampling uncertainty, data latency, and the effects of the documented prose-versus-SQL discrepancies are not quantified.

## Estimand

| Attribute | Specification |
|---|---|
| Population | PixelPress Pro iOS and Android users whose earliest trial_start_date falls in the SQL cohort window, 2026-03-02 through 2026-03-09 inclusive. |
| Exposure | None. This is a single-group descriptive conversion rate. |
| Time zero | Each user's earliest PixelPress Pro mobile trial_start_date. |
| Variable | Indicator for at least one billing.charges row with amount_usd > 0 from trial_start_date through DATE_ADD(trial_start_date, 14), inclusive. |
| Intercurrent events | Refunds, internal accounts, and test accounts are not handled in the visible SQL; if they are handled upstream, that handling is not documented in the provided code. |
| Summary | Converted users divided by all SQL-cohort trial users, multiplied by 100 and rounded to two decimal places. |

## Limitations

- **Prose and SQL use different conversion windows** (may make the number look smaller than it really is; high). The project note and readout call the metric 30-day conversion, but the query parameter is 14 days. If a 30-day rerun were made, the rate could be higher.
- **Exclusion and refund rules are not visible in the SQL** (could push the number either way; high). The project note says internal and test accounts are excluded and refunded charges do not count. The query shown filters only product, platform, and positive charge amount.
- **Cohort end date differs by one day** (could push the number either way; medium). The project note says the cohort is 2026-03-02 through 2026-03-08, but the query uses an inclusive date filter ending on 2026-03-09.
- **The February comparison is not reproducible from the saved files** (limits what the number can be used to conclude; medium). The readout says March is up from 12.9% in February, but the saved query and results table only contain the March cohort summary.

## Description vs implementation

- **Conversion window.** Described: The project note and readout define conversion as paying within 30 days of trial start. Implemented: The query sets conversion_days = 14 and filters b.charge_date through DATE_ADD(trial_start_date, 14). Impact: A longer 30-day window would include later converters, so the saved 14.3% may understate the intended 30-day conversion rate. The size is unknown.
- **Cohort end date.** Described: The project note says trials started 2026-03-02 through 2026-03-08. Implemented: The query sets cohort_end to DATE '2026-03-09' and uses an inclusive date filter. Impact: The SQL appears to include one extra trial-start date. Direction and size are unknown.
- **Internal and test account exclusions.** Described: The project note says internal and test accounts are excluded. Implemented: The provided SQL does not show an internal-account or test-account exclusion. Impact: If those accounts exist in app.trial_events, they may affect the denominator and numerator. Direction and size are unknown.
- **Refunded charges.** Described: The project note says refunded charges do not count as paying. Implemented: The provided SQL requires b.amount_usd > 0 but does not show a refund or net-paid filter. Impact: Refunded positive charges could overstate paid conversion if the billing table does not already remove or net them out. Size is unknown.
- **Onboarding lift claim.** Described: Readout says the new onboarding flow is driving a 1.4-point lift versus February. Implemented: The saved query and results table provide one March cohort rate and no causal comparison or February cohort computation. Impact: The 14.3% March level is reproducible from the saved output; the 1.4-point causal lift is not reproducible from the provided files.

## Reproduction

1. Use the saved SQL metric definition: PixelPress Pro iOS and Android first trial starts in the implemented March cohort window.
2. Count trial users and users with at least one positive charge in the inclusive 14-day SQL outcome window.
3. Divide converted_users by trial_users and multiply by 100.

- Receipt: Saved CSV: trial_users = 48,210; converted_users = 6,894; conversion_rate_pct = 14.30.
- Receipt: Recomputed from saved counts: 6,894 / 48,210 * 100 = 14.2999%, which rounds to 14.30%.

**Completeness.** The latest first trial start is 09 Mar 2026; its SQL conversion watch window ends 23 Mar 2026. Data are complete through 17 Apr 2026, so every window is fully observed. This number should not move as more data arrive.

## Sources

- [S1] `eval/fixtures/syn-a/README.md`, lines 1-21. Question, intended definition, cohort dates, exclusions, refund statement, result file list
- [S2] `eval/fixtures/syn-a/readout.md`, lines 1-9. Leadership-facing headline, February comparison, onboarding claim, and 30-day definition
- [S3] `eval/fixtures/syn-a/sql/trial_conversion.sql`, lines 1-43. Implemented cohort, conversion window, charge filter, and aggregate formula
- [S4] `eval/fixtures/syn-a/results/conversion_summary.csv`, lines 1-2. Saved headline output and run metadata

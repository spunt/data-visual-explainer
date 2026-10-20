# Home v2 active-days lift: methods

*Generated from `home-v2-active-days.yaml`. Status: provisional. Owner: Product analytics. Updated 2026-10-04.*

**Question.** Did users assigned to Home v2 have more active app days after assignment than users assigned to control?

**Definition.** Among users kept by the saved analysis, Home v2 users had 0.21 more active days than control users in days 1-28 after they were assigned.

**Result.** More active days per treatment user: **+0.21 days** (plausible range +0.05 days to +0.37 days). Control users averaged 6.42 active days; treatment users averaged 6.63.
## Population

The unit of analysis is the user (One user_id from exp.assignments for experiment_id = 'home_v2', after joining to exp.exposures with saw_variant_screen = 1, excluding country_code = 'CN', and requiring at least one joined app.events activity_date in the outcome window.). Eligibility rules, in the order applied:

1. Assigned to the Home v2 experiment from 4 May through 17 May 2026. *Implementation:* a.experiment_id = 'home_v2' and assigned_at >= TIMESTAMP '2026-05-04 00:00:00' and assigned_at < TIMESTAMP '2026-05-18 00:00:00'. [S3]
2. Saw the variant screen and was not in China. *Implementation:* INNER JOIN exp.exposures on user_id and experiment_id with saw_variant_screen = 1; country_code <> 'CN'. [S3]
3. Had at least one recorded activity day in days 1-28 after assignment. *Implementation:* per_user is built with an INNER JOIN from assigned to activity on act.activity_date > assigned_date and act.activity_date <= DATE_ADD(assigned_date, 28), so users with no activity_date in that interval are not in the final COUNT(*). (n = 83,482) [S3, S4]

## Time zero and windows

Time zero is the assignment date: Each user's clock starts on their assignment date. *Implementation:* assigned_date = CAST(a.assigned_at AS DATE).

| Window | Role | Offsets (start inclusive, end exclusive) | Definition |
|---|---|---|---|
| Assignment window | eligibility | [0, 14) days | assigned_at >= 2026-05-04 00:00:00 and assigned_at < 2026-05-18 00:00:00. |
| Days 1-28 after assignment | outcome | [1, 29) days | act.activity_date > assigned_date AND act.activity_date <= DATE_ADD(assigned_date, 28). |

## Measures

- **Active days** (headline) (count, active_days_1_28): Counts how many different dates had any app activity in the outcome window. *Implementation:* COUNT(DISTINCT act.activity_date), where activity_date is DATE(e.event_ts) from app.events grouped by user_id and UTC-derived activity_date.

## Aggregation and comparison

Average the active-day counts within each experiment arm. `AVG(active_days) grouped by arm; denominator is COUNT(*) from per_user.`

| Group | Definition | Value (days) | n |
|---|---|---|---|
| Control | arm = 'control' in the per_user export. | 6.42 | 41,880 |
| Home v2 | arm = 'treatment' in the per_user export. | 6.63 | 41,602 |


Subtract the control average from the treatment average. `diff = treatment.mean() - control.mean(); from the summary table, 6.63 - 6.42 = 0.21 days.` Target: descriptive (no causal target; a comparison of observed numbers).

Recomputed from the group values: `6.63 − 6.42 = 0.210`.

## Uncertainty

The saved interval uses the spread of per-user active days in each arm to estimate sampling uncertainty around the treatment-control difference. se = sqrt(var_treatment / n_treatment + var_control / n_control); interval = diff +/- 1.96 * se. p comes from scipy.stats.ttest_ind(..., equal_var=False). **Not covered:** The interval does not cover bias from post-assignment filtering, UTC-vs-local date mismatch, missing events, or whether zero-activity assigned users were dropped.

## Estimand

| Attribute | Specification |
|---|---|
| Population | Users assigned to home_v2 from 2026-05-04 through 2026-05-17, excluding China, joined to a saw_variant_screen exposure row, and present in app.events on at least one date in days 1-28. |
| Exposure | Home v2 treatment assignment versus control assignment, as labeled by arm. |
| Time zero | CAST(assigned_at AS DATE) for each user. |
| Variable | Count of distinct UTC-derived app activity dates greater than assigned_date and less than or equal to assigned_date plus 28 days. |
| Intercurrent events | The saved SQL does not specify special handling for uninstall, churn, travel, or missing events. Users with no activity in the window are excluded by the inner join rather than retained with zero. |
| Summary | Difference in arm-level means, treatment minus control, with a Welch t-test confidence interval. |

## Limitations

- **Not pure intent-to-treat** (limits what the number can be used to conclude; high). The readout says every assigned user is analyzed in their assigned arm, but the query keeps only users with a matching exposure row and at least one post-assignment activity day. If Home v2 changes exposure or whether a user has any activity at all, the reported mean is conditional on a post-randomization outcome.
- **Zero-activity users are not in the denominator** (could push the number either way; high). Because per_user uses an inner join to activity, users with no recorded active days in days 1-28 are absent rather than counted as zero active days. This likely overstates each arm's average active days; the direction for the treatment-control difference is unknown.
- **Time zone mismatch** (could push the number either way; medium). The readout says activity is counted in each user's local time zone. The query turns UTC event times into dates before counting active days.
- **Scope is narrower than all new users** (limits what the number can be used to conclude; medium). The implemented population excludes China and requires seeing the variant screen. The saved result should not be generalized to all new users without checking those exclusions.

## Description vs implementation

- **Intent-to-treat denominator.** Described: README says every assigned user is analyzed in the arm they were assigned to. Implemented: assigned joins to exposures with saw_variant_screen = 1, then per_user inner joins to activity, excluding assigned users without a matching exposure row or without activity in days 1-28. Impact: Narrows the denominator from all assigned users to exposed active users. The impact on the +0.21-day difference is unknown from saved outputs.
- **Geographic scope.** Described: The readouts describe randomized users or all new users without a country exclusion. Implemented: The SQL filters a.country_code <> 'CN'. Impact: Results do not cover China. Direction and size of any difference are unknown.
- **Time zone for active dates.** Described: README says active days use the user's local time zone. Implemented: activity_date is DATE(e.event_ts), and the SQL comment says event_ts is stored in UTC. Impact: Activity near local midnight can land on a different date. The effect on distinct active-day counts is unknown.
- **Breadth of causal claim.** Described: Readout says Home v2 causes users to be active 0.21 more days a month and applies to all new users. Implemented: The code estimates a treatment-control difference over days 1-28 among exposed, non-CN users who had at least one activity day in the outcome window. Impact: The implemented result is narrower than the readout claim. A true all-assigned ITT estimate could be smaller or larger.

## Reproduction

1. Run sql/experiment_metric.sql to produce arm-level users, mean_active_days, and sd_active_days.
2. Export or summarize per-user active_days by arm and run src/analysis.py's summarize(control, treatment).
3. Compare the resulting arm summaries with results/ab_summary.csv.

- Receipt: CSV arithmetic check: treatment mean 6.63 - control mean 6.42 = +0.21 active days.
- Receipt: Saved rows report n = 41,880 control and 41,602 treatment, total n = 83,482.
- Receipt: Saved interval is 0.05 to 0.37 with p = 0.011 and data_complete_through = 2026-06-20.

**Completeness.** The latest assignment date is 17 May 2026; its days 1-28 after assignment ends 14 Jun 2026. Data are complete through 20 Jun 2026, so every window is fully observed. This number should not move as more data arrive.

## Sources

- [S1] `eval/fixtures/syn-b/README.md`, lines 1-15. Experiment design, stated ITT, primary metric definition, and reported result
- [S2] `eval/fixtures/syn-b/readout.md`, lines 1-4. Headline leadership readout
- [S3] `eval/fixtures/syn-b/sql/experiment_metric.sql`, lines 1-30. Implemented population, activity-date derivation, outcome window, and aggregation
- [S4] `eval/fixtures/syn-b/results/ab_summary.csv`, lines 1-8. Saved group means, sample sizes, interval, p-value, and data completeness date
- [S5] `eval/fixtures/syn-b/src/analysis.py`, lines 1-9. Welch t-test calculation

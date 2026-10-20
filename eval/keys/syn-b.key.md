# Answer key: syn-b (RepRoom home_v2 experiment). NOT visible to authoring agents.

## Headline
- +0.21 active days (treatment 6.63 vs control 6.42), 95% CI 0.05 to 0.37; relative ≈ +3.3%.

## Key implemented rules (8)
R1 experiment_id = 'home_v2'; assigned_at in [2026-05-04, 2026-05-18) (i.e., through 05-17)
R2 ONLY users with an exposure row saw_variant_screen = 1 (inner join to exp.exposures)
R3 country_code <> 'CN'
R4 time zero = assignment date (CAST(assigned_at AS DATE))
R5 window: activity_date > assigned_date AND <= assigned_date + 28 (days 1–28)
R6 activity dates computed from event_ts in UTC
R7 per-user active days = distinct activity dates; users with ZERO active days are dropped (inner join), so the mean is over users active ≥1 day
R8 comparison = difference in means (treatment − control), Welch t-test, normal-approx CI

## Planted discrepancies (4)
D1 ITT described; implementation keeps only exposed users (saw_variant_screen = 1) → per-protocol, can break randomization balance
D2 Local time described; implementation uses UTC dates
D3 "Average per user" described; implementation averages only users with ≥1 active day (zeros excluded; conditional mean)
D4 Undocumented exclusion of country_code 'CN'

## Claim-strength trap
- Readout: "causes … applies to all new users." Correct handling: randomized design, but the analysed groups are filtered post-assignment (exposure, ≥1 active day), so the comparison is no longer a clean randomized contrast; claim strength should be below "causal" (or causal with explicit, prominent caveat), and it does not generalize to "all new users" (only exposed, active, non-CN users in the window). Stating it is a clean causal effect for all new users = fail.

## Non-specialist comprehension questions
Q1 (gist) What does +0.21 measure?  Correct: difference in average active days in the 4 weeks after assignment between new-home and old-home users (among those counted).
Q2 (verbatim) Who is included in the averages?  Correct: only users who saw the variant screen AND were active at least one day (non-CN, assigned May 4–17). Partial: mentions one of the two filters. Wrong: "all assigned users".
Q3 (claim) Can we say Home v2 causes 0.21 more active days for all new users?  Correct: No — filtering after randomization and the restricted population mean it is not a clean causal estimate for all users.

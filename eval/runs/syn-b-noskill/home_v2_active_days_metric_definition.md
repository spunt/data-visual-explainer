# Metric definition: Home v2 active-days lift

**Headline number:** users assigned to **Home v2** were active **0.21 more days** during the first 28 days after assignment than users assigned to the current home experience.

In plain language, this metric asks: **after someone enters the experiment, on how many different days do they come back and do anything in the app?** The headline compares that average count between the randomized treatment and control groups.

```text
Average active days in the 28-day follow-up window

Control     6.42 days  |█████████████████████████
Home v2     6.63 days  |██████████████████████████
Difference +0.21 days  |█

Interpretation: about one extra active day for every 5 treatment users
over their first 28 days after assignment.
```

## One-sentence definition

**Active days per user** is the number of distinct calendar days on which a user has at least one app activity event during days 1 through 28 after experiment assignment, averaged across users in an experiment arm.

The experiment's reported treatment effect is:

```text
average active days in treatment - average active days in control
= 6.63 - 6.42
= +0.21 active days per user
```

The reported relative lift is approximately:

```text
0.21 / 6.42 = 3.3%
```

## How to interpret the number

An increase of **0.21 active days per user** does **not** mean each individual user became active for exactly 0.21 more days. It means that, across a large randomized group, the treatment group's average was higher by 0.21 days over the 28-day measurement window.

A useful intuition is:

```text
0.21 extra days/user x 100 users = 21 extra active-user-days
```

So, for every 100 comparable users assigned to Home v2, the experiment estimates about **21 additional days with app activity** during the first 28 days after assignment.

Because users were randomized 50/50, the treatment-control difference is intended to estimate the causal effect of Home v2 for the analyzed population, assuming the experiment assignment and data processing are correct.

## What counts as an active day?

A user gets credit for **at most one active day per calendar date**. Multiple events on the same date still count as one active day.

Example:

| Day after assignment | User activity | Active-day credit |
|---:|---|---:|
| 1 | Opens app once | 1 |
| 2 | No activity | 0 |
| 3 | Opens app, views feed, sends message | 1 |
| 4 | No activity | 0 |
| ... | ... | ... |
| 28 | Opens app once | 1 |

In this example, the user has 3 active days, not 5 events.

## Measurement window

The intended measurement window is **days 1-28 after assignment**:

```text
assignment day       day 1                              day 28
      |                |-----------------------------------|
      |                included measurement window         |
      |
      not counted
```

The assignment day itself is excluded. Activity is counted only when the activity date is:

```text
activity_date > assigned_date
activity_date <= assigned_date + 28 days
```

This means the metric is a short-term engagement measure: it captures whether users return on distinct days in the first four weeks after they enter the experiment.

## Experiment population

Based on the analysis files, the experiment was:

- **Experiment:** `home_v2`
- **Assignment window:** 2026-05-04 through 2026-05-17
- **Randomization:** 50/50 at first app open after 2026-05-04
- **Analysis style described in the readout:** intent-to-treat, meaning users are analyzed in the arm they were assigned to
- **Observed sample in the result table:** 41,880 control users and 41,602 treatment users
- **Data complete through:** 2026-06-20

The SQL implementation additionally filters to:

- assignments with `experiment_id = 'home_v2'`
- `assigned_at >= 2026-05-04 00:00:00`
- `assigned_at < 2026-05-18 00:00:00`
- `country_code <> 'CN'`
- users with a matching exposure row where `saw_variant_screen = 1`

## Statistical result

The result file reports:

| Quantity | Value |
|---|---:|
| Control users | 41,880 |
| Treatment users | 41,602 |
| Control mean active days | 6.42 |
| Treatment mean active days | 6.63 |
| Difference | +0.21 |
| 95% confidence interval | +0.05 to +0.37 |
| p-value | 0.011 |

The confidence interval means that, under the statistical model used, the estimated treatment effect is reasonably compatible with values from **+0.05 to +0.37 active days per user**. Since this interval is above zero, the result is statistically distinguishable from no difference at the conventional 5% level.

The p-value of **0.011** means that, if Home v2 truly had no effect and the model assumptions held, a difference at least this extreme would occur by random assignment noise about 1.1% of the time.

## Exact reproducible specification

This section defines the implemented metric logic as directly as possible from the analysis files.

### 1. Select assigned users

Start from `exp.assignments` as `a`.

Join to `exp.exposures` as `x` on:

```sql
x.user_id = a.user_id
AND x.experiment_id = a.experiment_id
AND x.saw_variant_screen = 1
```

Keep rows where:

```sql
a.experiment_id = 'home_v2'
AND a.assigned_at >= TIMESTAMP '2026-05-04 00:00:00'
AND a.assigned_at <  TIMESTAMP '2026-05-18 00:00:00'
AND a.country_code <> 'CN'
```

For each kept row, define:

```sql
assigned_date = CAST(a.assigned_at AS DATE)
```

Retain:

```sql
user_id, arm, assigned_date
```

### 2. Create user-day activity records

Start from `app.events`.

For every event, define:

```sql
activity_date = DATE(event_ts)
```

The SQL comment says `event_ts` is stored in UTC. The query groups by:

```sql
user_id, DATE(event_ts)
```

This produces one record per user per UTC-derived activity date.

### 3. Count active days per analyzed user

Join assigned users to activity records on:

```sql
act.user_id = assigned.user_id
AND act.activity_date > assigned.assigned_date
AND act.activity_date <= DATE_ADD(assigned.assigned_date, 28)
```

Then compute:

```sql
active_days = COUNT(DISTINCT act.activity_date)
```

grouped by:

```sql
user_id, arm
```

### 4. Summarize by experiment arm

For each arm:

```sql
users = COUNT(*)
mean_active_days = AVG(active_days)
sd_active_days = STDDEV(active_days)
```

### 5. Estimate treatment effect and uncertainty

The Python analysis computes:

```python
diff = treatment.mean() - control.mean()
se = sqrt(treatment.var(ddof=1) / len(treatment)
          + control.var(ddof=1) / len(control))
ci_low = diff - 1.96 * se
ci_high = diff + 1.96 * se
p = Welch two-sample t-test p-value
```

So the reported effect is an absolute difference in arm means, with a normal-approximation 95% confidence interval and a Welch unequal-variance t-test.

## Important implementation caveats

These caveats matter for exact interpretation:

1. **Local time zone vs UTC:** the readout defines active days using the user's local time zone, but the SQL derives `activity_date` as `DATE(event_ts)` and notes that `event_ts` is stored in UTC. Unless the execution environment converts `event_ts` to local dates elsewhere, the implemented logic appears to count UTC dates rather than user-local dates.
2. **Intent-to-treat vs exposed-user filter:** the readout says the analysis is intent-to-treat, but the SQL joins to exposures and requires `saw_variant_screen = 1`. That makes the implemented population look like assigned users who also saw the variant screen, not all assigned users.
3. **Zero-active-day users:** the SQL uses an inner join from assigned users to activity. Users with no activity during days 1-28 would not appear in `per_user`, so they would not contribute zero active days to the average. The plain-language metric definition implies they should be included as zeroes if they were in the analyzed population.
4. **Country exclusion:** the README says the causal effect applies to all new users, but the SQL excludes `country_code = 'CN'`. The safest population statement is therefore the analyzed non-CN, exposed experiment population unless clarified elsewhere.

## Recommended short wording

> Home v2 increased 28-day engagement by **0.21 active days per user**: treatment users averaged **6.63** distinct active days in the first 28 days after assignment versus **6.42** for control users. This is a **3.3% lift** over control, with a 95% confidence interval of **+0.05 to +0.37 days**.


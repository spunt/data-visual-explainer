# Metric definition: PixelPress Pro mobile trial conversion

**Headline number:** **14.3% of PixelPress Pro mobile trial users converted to paid** for the March cohort.

In plain language, this is the share of people who started a PixelPress Pro free trial on iOS or Android during the March cohort window and then had a first positive-dollar charge soon enough to count as a conversion.

```
March mobile trial starters
48,210 users
        |
        | first paid charge within the measured conversion window
        v
Converted to paid
6,894 users

Conversion rate = 6,894 / 48,210 = 14.30%
```

## How to interpret it

A conversion rate of **14.3%** means that about **14 out of every 100** users who entered the measured free-trial cohort became paying subscribers under the implemented counting rules.

This is a cohort metric, not a same-day sales metric. Users enter the denominator when they start a trial. They enter the numerator only if a qualifying first paid charge is observed within the conversion window after their own trial start date.

## What is being measured

The metric answers:

> Among users who started a PixelPress Pro mobile free trial in the cohort period, what percentage had a qualifying first paid charge within the allowed conversion window?

The implemented summary is:

| Quantity | Value | Meaning |
|---|---:|---|
| Trial users | 48,210 | Distinct users in the trial-start cohort |
| Converted users | 6,894 | Distinct cohort users with a qualifying paid charge |
| Conversion rate | 14.30% | Converted users divided by trial users |
| Run date | 2026-04-18 | Date associated with the output |
| Data complete through | 2026-04-17 | Latest complete data date reported in the output |

## Progressive drill-down

### 1. Population

The measured population is users of **PixelPress Pro** on mobile platforms:

- Product: `PIXELPRESS_PRO`
- Platforms: `ios`, `android`
- Unit of analysis: distinct `user_id`

Each user contributes at most one trial start date: their earliest recorded PixelPress Pro mobile trial start.

### 2. Cohort entry

A user enters the cohort if their earliest PixelPress Pro mobile trial start date falls inside the configured cohort period.

The SQL sets:

- `cohort_start = DATE '2026-03-02'`
- `cohort_end = DATE '2026-03-09'`

The implemented filter uses `BETWEEN p.cohort_start AND p.cohort_end`, which is inclusive in standard SQL. Therefore, the reproducible SQL logic includes trial starts dated **2026-03-02 through 2026-03-09**, inclusive.

### 3. Conversion event

A cohort user is counted as converted if they have at least one billing charge that meets all implemented criteria:

- Same `user_id` as the trial user
- `amount_usd > 0`
- `charge_date` is on or after the user's trial start date
- `charge_date` is on or before `DATE_ADD(trial_start_date, conversion_days)`

Only the user's first qualifying charge date is retained, but the summary only needs whether the user has any qualifying charge.

### 4. Conversion window

The SQL sets:

- `conversion_days = 14`

So the reproducible implementation counts a user as converted if their first positive-dollar charge occurs from the trial start date through **14 days after** the trial start date, inclusive.

### 5. Formula

Let:

- `N_trial` = number of distinct cohort users
- `N_converted` = number of distinct cohort users with a qualifying charge in the conversion window

Then:

```text
conversion_rate_pct = round(100 * N_converted / N_trial, 2)
```

For this run:

```text
conversion_rate_pct = round(100 * 6,894 / 48,210, 2)
                    = round(14.2999..., 2)
                    = 14.30%
```

## Exact reproducible specification

This is the implemented logic expressed as a methods-style algorithm.

1. Set parameters:
   - `cohort_start = 2026-03-02`
   - `cohort_end = 2026-03-09`
   - `conversion_days = 14`
2. From `app.trial_events`, select trial events where:
   - `product = 'PIXELPRESS_PRO'`
   - `platform IN ('ios', 'android')`
3. Collapse trial events to one row per user:
   - `trial_start_date = MIN(trial_start_date)` by `user_id`
4. Keep cohort users whose `trial_start_date` is between `cohort_start` and `cohort_end`, inclusive.
5. From `billing.charges`, find each cohort user's earliest qualifying charge where:
   - `billing.charges.user_id = cohort.user_id`
   - `amount_usd > 0`
   - `charge_date BETWEEN trial_start_date AND DATE_ADD(trial_start_date, conversion_days)`
6. Count:
   - `trial_users = COUNT(DISTINCT cohort.user_id)`
   - `converted_users = COUNT(DISTINCT first_charge.user_id)`
7. Report:
   - `conversion_rate_pct = ROUND(100.0 * converted_users / trial_users, 2)`

Equivalent SQL shape:

```sql
WITH params AS (
  SELECT DATE '2026-03-02' AS cohort_start,
         DATE '2026-03-09' AS cohort_end,
         14                AS conversion_days
),

trials AS (
  SELECT t.user_id,
         MIN(t.trial_start_date) AS trial_start_date
  FROM app.trial_events t
  WHERE t.product = 'PIXELPRESS_PRO'
    AND t.platform IN ('ios', 'android')
  GROUP BY t.user_id
),

cohort AS (
  SELECT tr.user_id, tr.trial_start_date
  FROM trials tr
  CROSS JOIN params p
  WHERE tr.trial_start_date BETWEEN p.cohort_start AND p.cohort_end
),

first_charge AS (
  SELECT c.user_id, MIN(b.charge_date) AS first_charge_date
  FROM cohort c
  JOIN billing.charges b
    ON b.user_id = c.user_id
   AND b.amount_usd > 0
  CROSS JOIN params p
  WHERE b.charge_date BETWEEN c.trial_start_date
                          AND DATE_ADD(c.trial_start_date, p.conversion_days)
  GROUP BY c.user_id
)

SELECT
  COUNT(DISTINCT c.user_id) AS trial_users,
  COUNT(DISTINCT f.user_id) AS converted_users,
  ROUND(
    100.0 * COUNT(DISTINCT f.user_id) / COUNT(DISTINCT c.user_id),
    2
  ) AS conversion_rate_pct
FROM cohort c
LEFT JOIN first_charge f ON f.user_id = c.user_id;
```

## Important caveats and source discrepancies

The analysis folder contains inconsistent descriptions of the metric. The headline result file and SQL support the 14.30% result, but the prose definition does not perfectly match the SQL.

| Topic | Prose says | SQL implements | Why it matters |
|---|---|---|---|
| Conversion window | Paid within **30 days** | Paid within **14 days** | A 30-day window would usually produce an equal or higher conversion rate than a 14-day window. |
| Cohort end | 2026-03-02 through **2026-03-08** | `BETWEEN 2026-03-02 AND 2026-03-09`, inclusive | The SQL may include one extra day, depending on date semantics and source data. |
| Internal/test accounts | Excluded | No exclusion appears in the SQL | The reported metric may include such accounts unless excluded upstream. |
| Refunded charges | Refunded charges do not count | SQL only requires `amount_usd > 0`; no refund exclusion appears | Refunded paid charges may be counted unless already removed or netted upstream. |
| February comparison and onboarding lift | Readout says March is up from 12.9%, a 1.4-point lift | No February or causal-comparison logic is present | The headline conversion rate is reproducible; the lift claim is not reproducible from the provided files alone. |

For a strict metric definition document, the safest interpretation is:

> **14.30% is reproducibly defined by the SQL and result file as the share of distinct PixelPress Pro iOS/Android trial users in the implemented March cohort who had a positive-dollar charge within 14 days of trial start.**

The broader prose claim, "paid within 30 days," should be reconciled before using this metric as an official leadership definition.


# PixelPress mobile: trial conversion, March cohort

**Owner:** Growth analytics · **Status:** shared with leadership 2026-04-20

## Question
What share of people who start a PixelPress Pro free trial become paying subscribers?

## Definition
Trial conversion rate = the share of users who started a free trial during the cohort week
and became paying subscribers within **30 days** of starting the trial.

- Cohort: trials started **2026-03-02 through 2026-03-08** (one fiscal week).
- Internal and test accounts are excluded.
- "Paying" means a net-paid first charge (refunded charges do not count).

## Result
See `results/conversion_summary.csv` and `readout.md`.

## Files
- `sql/trial_conversion.sql` — builds the user-level table and the summary.
- `results/conversion_summary.csv` — output.

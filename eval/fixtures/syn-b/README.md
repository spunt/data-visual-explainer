# RepRoom app: "Home v2" experiment — engagement readout

**Owner:** Product analytics · **Experiment:** `home_v2` · **Status:** final

## Design
Randomized 50/50 at first app open after 2026-05-04 (assignment window 2026-05-04 to 2026-05-17).
Analysis is **intent-to-treat**: every assigned user is analysed in the arm they were assigned to.

## Primary metric
**Active days per user**: the average number of distinct days with any app activity in the
28 days after assignment (days 1–28), using the user's **local time zone**.

## Result
Treatment users were active **0.21 more days** (95% CI 0.05 to 0.37, p = 0.011).
See `results/ab_summary.csv`, `sql/experiment_metric.sql`, `src/analysis.py`.

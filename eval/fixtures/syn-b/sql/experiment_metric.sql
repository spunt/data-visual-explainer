-- home_v2 primary metric: per-user active days, days 1-28 after assignment
WITH assigned AS (
  SELECT a.user_id, a.arm, CAST(a.assigned_at AS DATE) AS assigned_date
  FROM exp.assignments a
  JOIN exp.exposures x
    ON x.user_id = a.user_id
   AND x.experiment_id = a.experiment_id
   AND x.saw_variant_screen = 1
  WHERE a.experiment_id = 'home_v2'
    AND a.assigned_at >= TIMESTAMP '2026-05-04 00:00:00'
    AND a.assigned_at <  TIMESTAMP '2026-05-18 00:00:00'
    AND a.country_code <> 'CN'
),
activity AS (
  SELECT e.user_id, DATE(e.event_ts) AS activity_date      -- event_ts is stored in UTC
  FROM app.events e
  GROUP BY e.user_id, DATE(e.event_ts)
),
per_user AS (
  SELECT s.user_id, s.arm, COUNT(DISTINCT act.activity_date) AS active_days
  FROM assigned s
  JOIN activity act
    ON act.user_id = s.user_id
   AND act.activity_date >  s.assigned_date
   AND act.activity_date <= DATE_ADD(s.assigned_date, 28)
  GROUP BY s.user_id, s.arm
)
SELECT arm, COUNT(*) AS users, AVG(active_days) AS mean_active_days, STDDEV(active_days) AS sd_active_days
FROM per_user
GROUP BY arm;

-- PixelPress trial conversion, user-level then summary
-- Author: growth analytics. Last edited 2026-04-18.

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
  COUNT(DISTINCT c.user_id)                                   AS trial_users,
  COUNT(DISTINCT f.user_id)                                   AS converted_users,
  ROUND(100.0 * COUNT(DISTINCT f.user_id) / COUNT(DISTINCT c.user_id), 2) AS conversion_rate_pct
FROM cohort c
LEFT JOIN first_charge f ON f.user_id = c.user_id;

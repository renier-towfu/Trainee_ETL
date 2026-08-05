-- =============================================================================
-- Trainee Portal - Sample Athena Queries
-- Run these in the Athena console against the trainee_portal_dev database
-- =============================================================================

-- Trainees by cohort
SELECT cohort, COUNT(*) as trainee_count
FROM trainee_profiles
GROUP BY cohort
ORDER BY cohort;

-- Overall attendance rate
SELECT
  COUNT(CASE WHEN attended = true THEN 1 END) as attended_count,
  COUNT(*) as total_records,
  ROUND(CAST(COUNT(CASE WHEN attended = true THEN 1 END) AS DOUBLE) / COUNT(*) * 100, 2) as attendance_rate_pct
FROM trainee_activities;

-- Late submissions summary
SELECT
  COUNT(*) as total_submissions,
  COUNT(CASE WHEN is_late = true THEN 1 END) as late_count,
  ROUND(CAST(COUNT(CASE WHEN is_late = true THEN 1 END) AS DOUBLE) / COUNT(*) * 100, 2) as late_rate_pct
FROM weekly_report_submissions;

-- Average performance score
SELECT
  ROUND(AVG(score), 2) as avg_score,
  MIN(score) as min_score,
  MAX(score) as max_score,
  COUNT(*) as total_reviews
FROM performance_reviews;

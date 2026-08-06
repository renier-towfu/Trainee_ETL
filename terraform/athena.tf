# =============================================================================
# Amazon Athena - Workgroup + Named Queries
# =============================================================================

resource "aws_athena_workgroup" "main" {
  name        = "${var.project_name}-${var.environment}"
  description = "Trainee Portal analytics workgroup"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.datalake.id}/athena-results/"
    }

    engine_version {
      selected_engine_version = "Athena engine version 3"
    }
  }
}

# --- Named Queries ---

resource "aws_athena_named_query" "trainees_by_cohort" {
  name        = "trainees-by-cohort"
  description = "Trainee count and status breakdown per cohort"
  workgroup   = aws_athena_workgroup.main.name
  database    = aws_glue_catalog_database.trainee_portal.name
  query       = <<-EOQ
    SELECT
      CAST(cohort AS INTEGER) as cohort,
      COUNT(*) as trainee_count,
      COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
      COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
      COUNT(CASE WHEN status = 'on-leave' THEN 1 END) as on_leave
    FROM trainee_profiles
    GROUP BY cohort
    ORDER BY cohort;
  EOQ
}

resource "aws_athena_named_query" "attendance_rate" {
  name        = "attendance-rate"
  description = "Overall activity attendance rate"
  workgroup   = aws_athena_workgroup.main.name
  database    = aws_glue_catalog_database.trainee_portal.name
  query       = <<-EOQ
    SELECT
      COUNT(CASE WHEN attended = true THEN 1 END) as attended,
      COUNT(*) as total,
      ROUND(CAST(COUNT(CASE WHEN attended = true THEN 1 END) AS DOUBLE) / COUNT(*) * 100, 2) as rate_pct
    FROM trainee_activities;
  EOQ
}

resource "aws_athena_named_query" "submission_summary" {
  name        = "submission-summary"
  description = "Weekly report submission and late rates"
  workgroup   = aws_athena_workgroup.main.name
  database    = aws_glue_catalog_database.trainee_portal.name
  query       = <<-EOQ
    SELECT
      COUNT(*) as total_submissions,
      COUNT(CASE WHEN islate = true THEN 1 END) as late_count,
      ROUND(CAST(COUNT(CASE WHEN islate = true THEN 1 END) AS DOUBLE) / COUNT(*) * 100, 2) as late_rate_pct
    FROM weekly_report_submissions;
  EOQ
}

resource "aws_athena_named_query" "performance_scores" {
  name        = "performance-scores"
  description = "Performance review score statistics"
  workgroup   = aws_athena_workgroup.main.name
  database    = aws_glue_catalog_database.trainee_portal.name
  query       = <<-EOQ
    SELECT
      ROUND(AVG(score), 2) as avg_score,
      MIN(score) as min_score,
      MAX(score) as max_score,
      COUNT(*) as total_reviews
    FROM performance_reviews;
  EOQ
}

resource "aws_athena_named_query" "top_performers" {
  name        = "top-performers"
  description = "Top 10 trainees by average review score"
  workgroup   = aws_athena_workgroup.main.name
  database    = aws_glue_catalog_database.trainee_portal.name
  query       = <<-EOQ
    SELECT
      tp.fullname,
      tp.school,
      CAST(tp.cohort AS INTEGER) as cohort,
      ROUND(AVG(pr.score), 2) as avg_score,
      COUNT(pr.score) as review_count
    FROM performance_reviews pr
    JOIN trainee_profiles tp ON pr.traineeid = tp.cognitosub
    GROUP BY tp.fullname, tp.school, tp.cohort
    HAVING COUNT(pr.score) >= 3
    ORDER BY avg_score DESC
    LIMIT 10;
  EOQ
}

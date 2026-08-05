# =============================================================================
# AWS Glue - Data Catalog + ETL Job + Crawler
#
# Flow: s3://bucket/raw/ → Glue ETL → s3://bucket/curated/ → Crawler → Catalog
# =============================================================================

# --- Glue Data Catalog Database ---
resource "aws_glue_catalog_database" "trainee_portal" {
  name        = "${replace(var.project_name, "-", "_")}_${var.environment}"
  description = "Trainee Portal - curated analytics datasets"
}

# --- Glue ETL Job ---
resource "aws_glue_job" "etl_pipeline" {
  name         = "${var.project_name}-${var.environment}-etl"
  role_arn     = var.glue_role_arn
  description  = "ETL: JSON validation, cleansing, transformation, KPI generation, Parquet conversion"
  glue_version = "4.0"

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.datalake.id}/scripts/etl_pipeline.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                    = "python"
    "--job-bookmark-option"             = "job-bookmark-enable"
    "--enable-metrics"                  = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--TempDir"                         = "s3://${aws_s3_bucket.datalake.id}/temp/"
    "--BUCKET"                          = aws_s3_bucket.datalake.id
    "--DATABASE_NAME"                   = aws_glue_catalog_database.trainee_portal.name
  }

  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 60

  execution_property {
    max_concurrent_runs = 1
  }
}

# --- Glue Crawler (catalogs Parquet from curated/) ---
resource "aws_glue_crawler" "curated" {
  name          = "${var.project_name}-${var.environment}-crawler"
  database_name = aws_glue_catalog_database.trainee_portal.name
  role          = var.glue_role_arn
  description   = "Discovers schema from curated Parquet and registers tables in Data Catalog"

  s3_target {
    path = "s3://${aws_s3_bucket.datalake.id}/curated/"
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "LOG"
  }

  configuration = jsonencode({
    Version = 1.0
    Grouping = {
      TableLevelConfiguration = 2
    }
  })
}

# --- Glue Trigger (on-demand) ---
resource "aws_glue_trigger" "etl_on_demand" {
  name = "${var.project_name}-${var.environment}-etl-trigger"
  type = "ON_DEMAND"

  actions {
    job_name = aws_glue_job.etl_pipeline.name
  }
}

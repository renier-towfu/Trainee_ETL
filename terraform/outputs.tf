# =============================================================================
# Outputs
# =============================================================================

output "bucket_name" {
  description = "S3 data lake bucket"
  value       = aws_s3_bucket.datalake.id
}

output "glue_database_name" {
  description = "Glue Data Catalog database"
  value       = aws_glue_catalog_database.trainee_portal.name
}

output "glue_job_name" {
  description = "Glue ETL job name"
  value       = aws_glue_job.etl_pipeline.name
}

output "glue_crawler_name" {
  description = "Glue Crawler name"
  value       = aws_glue_crawler.curated.name
}

# --- Workflow Commands ---
output "step_1_upload_script" {
  description = "Step 1: Upload ETL script"
  value       = "aws s3 cp terraform/scripts/etl_pipeline.py s3://${aws_s3_bucket.datalake.id}/scripts/etl_pipeline.py"
}

output "step_2_upload_data" {
  description = "Step 2: Upload JSON to raw/"
  value       = "aws s3 cp . s3://${aws_s3_bucket.datalake.id}/raw/ --recursive --exclude \"*\" --include \"*.json\""
}

output "step_3_run_etl" {
  description = "Step 3: Run Glue ETL job"
  value       = "aws glue start-job-run --job-name ${aws_glue_job.etl_pipeline.name}"
}

output "step_4_run_crawler" {
  description = "Step 4: Run Crawler to catalog Parquet"
  value       = "aws glue start-crawler --name ${aws_glue_crawler.curated.name}"
}

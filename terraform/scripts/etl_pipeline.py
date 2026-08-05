"""
Trainee Portal - AWS Glue ETL Pipeline
Single bucket layout:
  s3://bucket/raw/          ← Source JSON
  s3://bucket/curated/      ← Output Parquet
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

# --- Initialize ---
args = getResolvedOptions(sys.argv, ["JOB_NAME", "BUCKET", "DATABASE_NAME"])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

BUCKET = args["BUCKET"]
DATABASE_NAME = args["DATABASE_NAME"]


# =============================================================================
# Datasets
# =============================================================================

DATASETS = {
    "trainee-profiles": "trainee_profiles",
    "programs": "programs",
    "enrollments": "enrollments",
    "activities": "activities",
    "trainee-activities": "trainee_activities",
    "attendance-logs": "attendance_logs",
    "weekly-report-bins": "weekly_report_bins",
    "weekly-report-submissions": "weekly_report_submissions",
    "performance-reviews": "performance_reviews",
}


# =============================================================================
# Helper Functions
# =============================================================================

def flatten_dynamodb_json(df):
    """Flatten DynamoDB JSON format ({"S": "val"}, {"N": "123"}, {"BOOL": true})."""
    select_exprs = []
    for field in df.schema.fields:
        col_name = field.name
        dtype = field.dataType
        if hasattr(dtype, "fieldNames"):
            field_names = dtype.fieldNames()
            if "S" in field_names:
                select_exprs.append(F.col(f"`{col_name}`.S").alias(col_name))
            elif "N" in field_names:
                select_exprs.append(F.col(f"`{col_name}`.N").cast("double").alias(col_name))
            elif "BOOL" in field_names:
                select_exprs.append(F.col(f"`{col_name}`.BOOL").alias(col_name))
            elif "L" in field_names:
                select_exprs.append(F.to_json(F.col(f"`{col_name}`.L")).alias(col_name))
            else:
                select_exprs.append(F.to_json(F.col(col_name)).alias(col_name))
        else:
            select_exprs.append(F.col(f"`{col_name}`"))
    return df.select(*select_exprs)


def cleanse_strings(df):
    """Trim whitespace from all string columns."""
    for field in df.schema.fields:
        if isinstance(field.dataType, StringType):
            df = df.withColumn(field.name, F.trim(F.col(field.name)))
    return df


# =============================================================================
# ETL Processing
# =============================================================================

def process_dataset(file_name, table_name):
    """Full ETL: read JSON → flatten → cleanse → deduplicate → write Parquet."""
    source = f"s3://{BUCKET}/raw/{file_name}.json"
    target = f"s3://{BUCKET}/curated/{table_name}/"

    print(f"\n{'='*60}")
    print(f"[ETL] {file_name} → {table_name}")
    print(f"{'='*60}")

    try:
        # Read
        df = spark.read.option("multiLine", "true").json(source)
        if df.rdd.isEmpty():
            print(f"  [SKIP] Empty dataset")
            return
        count = df.count()
        print(f"  [READ] {count} records")

        # Flatten DynamoDB format
        df = flatten_dynamodb_json(df)
        print(f"  [FLATTEN] Done")

        # Cleanse
        df = cleanse_strings(df)

        # Deduplicate
        key_col = df.columns[0]
        before = df.count()
        df = df.dropDuplicates([key_col])
        after = df.count()
        dupes = before - after
        if dupes > 0:
            print(f"  [DEDUP] Removed {dupes} duplicates")

        # Quality check
        for col_name in df.columns:
            nulls = df.filter(F.col(col_name).isNull()).count()
            if nulls > 0:
                print(f"  [QUALITY] {col_name}: {nulls} nulls ({round(nulls/after*100,1)}%)")

        # Write Parquet
        df.write.mode("overwrite").parquet(target)
        print(f"  [WRITE] {after} records → Parquet")

    except Exception as e:
        print(f"  [ERROR] {file_name}: {str(e)}")


# --- Main ---
print("\n" + "=" * 60)
print("TRAINEE PORTAL ETL PIPELINE")
print(f"Bucket: s3://{BUCKET}/")
print(f"Database: {DATABASE_NAME}")
print("=" * 60)

for file_name, table_name in DATASETS.items():
    process_dataset(file_name, table_name)

print("\n" + "=" * 60)
print("ETL COMPLETE")
print("=" * 60)

job.commit()

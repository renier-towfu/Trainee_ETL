"""
Trainee Portal - AWS Glue ETL Pipeline
Single bucket layout:
  s3://bucket/raw/          ← Source JSON (DynamoDB format)
  s3://bucket/curated/      ← Output Parquet (clean, readable dates)
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, DoubleType

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
# Dataset Configuration
# key_column: used for deduplication (primary key)
# timestamp_columns: converted from Unix epoch to readable datetime
# =============================================================================

DATASETS = {
    "trainee-profiles": {
        "table": "trainee_profiles",
        "key_column": "cognitosub",
        "timestamp_columns": ["createdat", "startdate"],
    },
    "programs": {
        "table": "programs",
        "key_column": "id",
        "timestamp_columns": ["createdat", "startdate", "enddate"],
    },
    "enrollments": {
        "table": "enrollments",
        "key_column": "id",
        "timestamp_columns": ["enrolledat"],
    },
    "activities": {
        "table": "activities",
        "key_column": "id",
        "timestamp_columns": ["createdat", "date"],
    },
    "trainee-activities": {
        "table": "trainee_activities",
        "key_column": None,  # composite key (traineeId + activityId)
        "timestamp_columns": ["updatedat"],
    },
    "attendance-logs": {
        "table": "attendance_logs",
        "key_column": "id",
        "timestamp_columns": ["date", "clockintime", "clockouttime", "timelogged"],
    },
    "weekly-report-bins": {
        "table": "weekly_report_bins",
        "key_column": "id",
        "timestamp_columns": ["createdat", "closedate"],
    },
    "weekly-report-submissions": {
        "table": "weekly_report_submissions",
        "key_column": "id",
        "timestamp_columns": ["createdat", "submittedat", "lastmodified"],
    },
    "performance-reviews": {
        "table": "performance_reviews",
        "key_column": "id",
        "timestamp_columns": ["reviewedat"],
    },
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


def convert_timestamps(df, timestamp_cols):
    """Convert Unix epoch (seconds) columns to readable timestamp strings."""
    # Build a case-insensitive lookup of actual column names
    actual_cols = {c.lower(): c for c in df.columns}

    for col_name in timestamp_cols:
        actual_name = actual_cols.get(col_name.lower())
        if actual_name:
            df = df.withColumn(
                actual_name,
                F.from_unixtime(
                    F.col(f"`{actual_name}`").cast("double").cast("long"),
                    "yyyy-MM-dd HH:mm:ss"
                )
            )
    return df


# =============================================================================
# ETL Processing
# =============================================================================

def process_dataset(file_name, config):
    """Full ETL: read → flatten → cleanse → convert dates → deduplicate → write."""
    table_name = config["table"]
    key_column = config["key_column"]
    timestamp_cols = config["timestamp_columns"]

    source = f"s3://{BUCKET}/raw/{file_name}.json"
    target = f"s3://{BUCKET}/curated/{table_name}/"

    print(f"\n{'='*60}")
    print(f"[ETL] {file_name} → {table_name}")
    print(f"{'='*60}")

    try:
        # 1. Read JSON
        df = spark.read.option("multiLine", "true").json(source)
        if df.rdd.isEmpty():
            print(f"  [SKIP] Empty dataset")
            return
        count = df.count()
        print(f"  [READ] {count} records")

        # 2. Flatten DynamoDB format
        df = flatten_dynamodb_json(df)
        print(f"  [FLATTEN] Columns: {df.columns}")

        # 3. Cleanse strings
        df = cleanse_strings(df)

        # 4. Convert Unix timestamps to readable dates
        df = convert_timestamps(df, timestamp_cols)
        if timestamp_cols:
            print(f"  [DATES] Converted: {timestamp_cols}")

        # 5. Deduplicate
        if key_column and key_column in df.columns:
            before = df.count()
            df = df.dropDuplicates([key_column])
            after = df.count()
            dupes = before - after
            if dupes > 0:
                print(f"  [DEDUP] Removed {dupes} duplicates (key: {key_column})")
            else:
                print(f"  [DEDUP] No duplicates (key: {key_column})")
        elif key_column is None:
            # Composite key - deduplicate on all columns
            before = df.count()
            df = df.dropDuplicates()
            after = df.count()
            dupes = before - after
            if dupes > 0:
                print(f"  [DEDUP] Removed {dupes} exact duplicates")
        else:
            print(f"  [DEDUP] Key column '{key_column}' not found, skipping")

        # 6. Data quality
        final_count = df.count()
        for col_name in df.columns:
            nulls = df.filter(F.col(col_name).isNull()).count()
            if nulls > 0:
                print(f"  [QUALITY] {col_name}: {nulls} nulls ({round(nulls/final_count*100,1)}%)")

        # 7. Write Parquet
        df.write.mode("overwrite").parquet(target)
        print(f"  [WRITE] {final_count} records → Parquet")

    except Exception as e:
        print(f"  [ERROR] {file_name}: {str(e)}")


# --- Main ---
print("\n" + "=" * 60)
print("TRAINEE PORTAL ETL PIPELINE")
print(f"Bucket: s3://{BUCKET}/")
print(f"Database: {DATABASE_NAME}")
print("=" * 60)

for file_name, config in DATASETS.items():
    process_dataset(file_name, config)

print("\n" + "=" * 60)
print("ETL COMPLETE")
print("=" * 60)

job.commit()

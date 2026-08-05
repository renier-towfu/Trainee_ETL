# Trainee Portal - Serverless Data Analytics Platform

## What This Is

A serverless ETL pipeline on AWS that takes trainee program JSON data, validates and transforms it into Parquet, and makes it queryable for executive dashboards. Built with Terraform so the entire infrastructure can be created or destroyed in one command.

---

## Architecture

```
Manual JSON Upload
       │
       ▼
Amazon S3 (raw/)
       │
       ▼
AWS Glue ETL Job
  • Read JSON
  • Schema Validation
  • Data Cleansing
  • Missing Value Handling
  • Data Type Conversion
  • Duplicate Detection
  • Error Logging
  • JSON → Parquet
       │
       ▼
Amazon S3 (curated/)
       │
       ▼
AWS Glue Crawler
       │
       ▼
AWS Glue Data Catalog
       │
       ▼
Amazon Athena (pending permissions)
       │
       ▼
Amazon QuickSight (pending permissions)
```

---

## Current State

### What is deployed and working

| Resource | Name | Status |
|----------|------|--------|
| S3 Bucket | `trainee-portal-dev-956304645529` | ✅ Live |
| Glue ETL Job | `trainee-portal-dev-etl` | ✅ Tested, SUCCEEDED |
| Glue Crawler | `trainee-portal-dev-crawler` | ✅ Tested, 9 tables created |
| Glue Data Catalog | `trainee_portal_dev` | ✅ 9 tables registered |
| IAM Role | `trainee-portal-dev-glue-role` | ✅ Exists (created outside Terraform) |
| Athena | — | ❌ Blocked (no `athena:*` permission) |
| QuickSight | — | ❌ Blocked (no `quicksight:*` permission) |

### S3 Bucket Structure

```
s3://trainee-portal-dev-956304645529/
├── raw/                         ← Original JSON files (8.2 MB)
│   ├── trainee-profiles.json
│   ├── programs.json
│   ├── enrollments.json
│   ├── activities.json
│   ├── trainee-activities.json
│   ├── attendance-logs.json
│   ├── weekly-report-bins.json
│   ├── weekly-report-submissions.json
│   └── performance-reviews.json
├── curated/                     ← Transformed Parquet (222 KB, 97% compression)
│   ├── trainee_profiles/
│   ├── programs/
│   ├── enrollments/
│   ├── activities/
│   ├── trainee_activities/
│   ├── attendance_logs/
│   ├── weekly_report_bins/
│   ├── weekly_report_submissions/
│   └── performance_reviews/
├── scripts/                     ← Glue ETL Python code
│   └── etl_pipeline.py
└── temp/                        ← Glue temporary files (auto-deleted after 7 days)
```

### Data Catalog Tables

Database: `trainee_portal_dev`

| Table | Source File | Records |
|-------|-------------|---------|
| `trainee_profiles` | trainee-profiles.json | 120 |
| `programs` | programs.json | 96 |
| `enrollments` | enrollments.json | 1,200 |
| `activities` | activities.json | 672 |
| `trainee_activities` | trainee-activities.json | 6,240 |
| `attendance_logs` | attendance-logs.json | 8,352 |
| `weekly_report_bins` | weekly-report-bins.json | 96 |
| `weekly_report_submissions` | weekly-report-submissions.json | 952 |
| `performance_reviews` | performance-reviews.json | 476 |

---

## Terraform

All infrastructure is managed by Terraform in the `terraform/` directory.

### Files

```
terraform/
├── main.tf              ← Provider, backend, locals
├── variables.tf         ← Input variables
├── s3.tf                ← Single S3 bucket + lifecycle + security
├── glue.tf              ← Catalog DB, ETL Job, Crawler, Trigger
├── outputs.tf           ← Bucket name, job names, workflow commands
├── terraform.tfvars     ← Actual variable values (not committed)
├── terraform.tfvars.example
├── .gitignore
└── scripts/
    ├── etl_pipeline.py  ← Glue ETL script (PySpark)
    └── sample_queries.sql ← Athena SQL queries for later
```

### Commands

```bash
cd terraform

# Create everything
terraform apply

# Destroy everything
terraform destroy

# See what exists
terraform state list
```

### Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `aws_region` | `ap-southeast-1` | Singapore region |
| `environment` | `dev` | Environment tag |
| `project_name` | `trainee-portal` | Used in all resource names |
| `glue_role_arn` | `arn:aws:iam::956304645529:role/trainee-portal-dev-glue-role` | Existing IAM role for Glue |

---

## ETL Pipeline Details

### What the ETL job does

1. Reads each JSON file from `s3://bucket/raw/`
2. Parses DynamoDB JSON format (`{"S": "value"}`, `{"N": "123"}`, `{"BOOL": true}`)
3. Flattens into plain columnar format
4. Trims whitespace from string columns
5. Removes duplicate records
6. Logs data quality metrics (null counts per column)
7. Writes as Snappy-compressed Parquet to `s3://bucket/curated/`

### DynamoDB JSON → Flat Column Example

Input (raw):
```json
{
  "fullName": {"S": "Maria Santos"},
  "cohort": {"N": "1"},
  "attended": {"BOOL": true}
}
```

Output (curated Parquet):
```
fullName = "Maria Santos"  (string)
cohort = 1.0               (double)
attended = true            (boolean)
```

### Error Handling

- Empty datasets: skipped with log message
- Malformed records: logged, pipeline continues
- Duplicates: removed based on first column as key
- Null values: preserved (not dropped), logged as quality metric

---

## Workflow (How to Run)

### Full pipeline execution

```bash
# 1. Upload ETL script
aws s3 cp terraform/scripts/etl_pipeline.py s3://trainee-portal-dev-956304645529/scripts/etl_pipeline.py

# 2. Upload JSON data to raw/
aws s3 cp data/ s3://trainee-portal-dev-956304645529/raw/ --recursive --exclude "*" --include "*.json"

# 3. Run ETL (takes ~2 min)
aws glue start-job-run --job-name trainee-portal-dev-etl

# 4. Check ETL status
aws glue get-job-runs --job-name trainee-portal-dev-etl --query "JobRuns[0].{Status:JobRunState,Duration:ExecutionTime}" --output table

# 5. Run Crawler (takes ~1 min)
aws glue start-crawler --name trainee-portal-dev-crawler

# 6. Verify tables in catalog
aws glue get-tables --database-name trainee_portal_dev --query "TableList[].Name" --output table
```

---

## Data Overview

120 trainees across 6 cohorts (20 per cohort), each going through a 4-month training program spanning January 2025 – December 2026.

### Training Structure

```
Month 1-2: Cloud Training (8 weeks, mandatory)
Month 3:   Specialization (choose 1 of 4)
Month 4:   Capstone Project
```

### Specializations (30 trainees each)

- Data Engineering
- Freshworks Administration
- QA Engineering
- App Development

### Key Metrics in the Data

- 75% activity attendance rate
- 80% daily presence rate
- 85% weekly report submission rate
- 50% review rate (476 of 952 submissions reviewed)
- Score range: 6-10 (average ~8.3)

### Data Relationships

```
Trainee Profile (120)
├── Enrollments (1,200)
│   └── Programs (96)
│       ├── Activities (672)
│       │   └── Trainee Activities (6,240)
│       ├── Weekly Report Bins (96)
│       │   └── Weekly Report Submissions (952)
│       │       └── Performance Reviews (476)
└── Attendance Logs (8,352)
```

For detailed field definitions and samples, see [docs/DATA-DICTIONARY.md](docs/DATA-DICTIONARY.md).

---

## What's Next (Blocked by Permissions)

### Phase 1 completion (needs `athena:*`)

- Create Athena workgroup
- Run SQL queries against the 9 curated tables
- Create views for KPIs and aggregations

### Phase 2 (needs `quicksight:*`)

- Connect QuickSight to Athena
- Build 4 dashboard pages:
  - Executive Overview (totals, success rates, trends)
  - Operations (processing duration, errors, uploads)
  - Business Analytics (cohort performance, specialization breakdown)
  - Future AI (reserved for ML predictions)

### Phase 3 (future)

- Machine Learning with SageMaker
- Prediction datasets written back to curated/
- Combined historical + predictive dashboards

---

## AWS Account Details

| Item | Value |
|------|-------|
| Account ID | `956304645529` |
| Region | `ap-southeast-1` (Singapore) |
| IAM User | `renier` |
| Glue Role | `trainee-portal-dev-glue-role` |

### IAM User Permissions (what works)

- ✅ S3 (full)
- ✅ Glue (full)
- ✅ IAM: list-roles, get-role, create-role, attach-role-policy
- ❌ IAM: PutRolePolicy, GetRolePolicy (inline policies)
- ❌ Athena (all actions)
- ❌ QuickSight (all actions)
- ❌ KMS: CreateKey, TagResource

### Permissions needed from admin

```json
{
  "Effect": "Allow",
  "Action": ["athena:*", "quicksight:*"],
  "Resource": "*"
}
```

---

## Cost

Current monthly cost: **~$0.00** (data at rest is negligible)

Per ETL run: **~$0.07** (2 workers × ~2 minutes × $0.44/DPU-hour)

The architecture is fully serverless — zero cost when idle.

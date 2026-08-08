# Dashboard Data Sources & Calculated Fields

This document explains every Athena view (dataset) available for the QuickSight dashboard, what fields they contain, and how calculated metrics are derived.

---

## Available Datasets (Athena Views)

| View | Purpose | Use for |
|------|---------|---------|
| `v_executive_dashboard` | Full trainee metrics (1 row per trainee) | KPIs, bar charts, tables |
| `v_trainee_detail` | Enhanced trainee data with risk_status and review_status as strings | Intervention table, scatter plots, filters |
| `v_cohort_health` | Aggregated per cohort (1 row per cohort) | Cohort Health Matrix table |
| `v_daily_trend` | Daily attendance aggregates | Time-series line charts |
| `v_enrollment_monthly` | Monthly enrollment counts | Enrollment trend bar/line |
| `v_trainee_intake` | Monthly new trainee intake | Growth chart |
| `v_submissions_detail` | Individual submission records with scores | Submission drill-down |
| `v_attendance_metrics` | Per-trainee attendance rate (helper) | Used by other views |
| `v_submission_metrics` | Per-trainee submission rate (helper) | Used by other views |
| `v_score_metrics` | Per-trainee avg score (helper) | Used by other views |
| `v_daily_presence` | Per-trainee daily log summary (helper) | Used by other views |
| `v_risk_dashboard` | Original risk-only view | Legacy, replaced by v_executive_dashboard |

---

## Primary Dataset: `v_trainee_detail`

**Use this as your main QuickSight dataset.** It has everything needed for the full dashboard.

### Fields

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `trainee_id` | String | trainee-profiles.json → `cognitoSub` | Unique trainee identifier |
| `fullname` | String | trainee-profiles.json → `fullName` | Trainee's full name |
| `email` | String | trainee-profiles.json → `email` | Email address |
| `school` | String | trainee-profiles.json → `school` | University |
| `cohort` | Integer | trainee-profiles.json → `cohort` | Cohort number (1-6) |
| `status` | String | trainee-profiles.json → `status` | active / completed / on-leave |
| `data_coverage` | String | **Calculated** | Established / Partial / Upcoming |
| `activity_participation` | Double | **Calculated** from trainee-activities.json | % of activities attended (0-1) |
| `days_logged` | Integer | **Calculated** from attendance-logs.json | Number of days with clock-in |
| `total_hours_logged` | Double | **Calculated** from attendance-logs.json | Sum of all hours worked |
| `total_submissions` | Integer | **Calculated** from weekly-report-submissions.json | Reports submitted |
| `ontime_submissions` | Integer | **Calculated** | total_submissions - late_submissions |
| `late_submissions` | Integer | **Calculated** from weekly-report-submissions.json | Reports submitted late |
| `avg_score` | Double | **Calculated** from performance-reviews.json | Average review score (6-10), NULL if no reviews |
| `review_count` | Integer | **Calculated** from performance-reviews.json | How many reviews received |
| `review_status` | String | **Calculated** | "Reviewed" or "Not Reviewed" |
| `engagement_score` | Double | **Calculated** | Composite metric (0-1) |
| `risk_status` | String | **Calculated** | "At Risk" or "On Track" |

---

## Cohort Health Dataset: `v_cohort_health`

**1 row per cohort.** Use for the Cohort Health Matrix table.

| Field | Description |
|-------|-------------|
| `cohort` | Cohort number (1-6) |
| `cohort_status` | Established / Partial / Upcoming |
| `total_trainees` | Count of trainees in cohort |
| `active_trainees` | Count with status = active |
| `onleave_trainees` | Count with status = on-leave |
| `completed_trainees` | Count with status = completed |
| `avg_attendance_pct` | Average attendance rate as percentage |
| `total_submissions` | Total reports submitted by cohort |
| `late_submissions` | Late reports in cohort |
| `ontime_submissions` | On-time reports in cohort |
| `ontime_rate_pct` | On-time as % of total submissions |
| `avg_reviewed_score` | Average score (reviewed submissions only) |
| `total_reviews` | Number of reviews in cohort |
| `review_coverage_pct` | Reviews / submissions as % |
| `at_risk_count` | Trainees flagged at-risk |

---

## How Calculated Fields Are Derived

### Activity Participation (attendance_rate)

```
Source: trainee-activities.json
Formula: COUNT(attended = true) / COUNT(*) per trainee
Range: 0 to 1
Note: Measures activity attendance (standups, code reviews), NOT daily presence
```

### Submission Rate

```
Source: weekly-report-submissions.json + enrollments.json + weekly-report-bins.json
Formula: COUNT(submissions) / COUNT(applicable bins for trainee's enrolled programs)
Range: 0 to 1
Note: Denominator varies per trainee based on their enrolled programs
```

### On-Time Submission Rate

```
Formula: (total_submissions - late_submissions) / total_submissions
Range: 0 to 1
Note: Only considers submitted reports. Missing submissions are not counted as late.
```

### Review Coverage

```
Formula: total_reviews / total_submissions
Approx value: ~50%
Note: Resource constraint — not all submissions get reviewed
```

### Average Score

```
Source: performance-reviews.json
Formula: AVG(score) per trainee WHERE reviews exist
Range: 6 to 10
CRITICAL: Only includes reviewed submissions. NULL if trainee has no reviews.
Do NOT treat NULL as 0.
```

### Normalized Score

```
Formula: (avg_score - 6) / 4
Range: 0 to 1
Purpose: Maps 6-10 scale to 0-1 for engagement composite
```

### Engagement Score

```
If trainee has reviews:
  0.4 × activity_participation + 0.4 × submission_rate + 0.2 × normalized_score

If trainee has NO reviews:
  0.5 × activity_participation + 0.5 × submission_rate

Range: 0 to 1
Note: Formula changes based on review availability. Scores are NOT directly comparable between reviewed and non-reviewed trainees.
```

### Risk Status

```
Formula: "At Risk" IF activity_participation < 0.6 OR submission_rate < 0.6
Otherwise: "On Track"
Note: Uses OR logic — either metric below 60% triggers the flag
```

### Data Coverage Status

```
Cohort 1-4: "Established" (complete 4-month cycle data)
Cohort 5: "Partial" (started May 2026, still in progress)
Cohort 6: "Upcoming" (starts Sep 2026, no submissions/scores)
```

---

## Data Caveats for Dashboard

| Issue | Impact | How to handle |
|-------|--------|---------------|
| Review coverage ~50% | Score metrics only represent reviewed trainees | Label as "Reviewed Score", show review coverage KPI |
| Cohort 6 not started | 0% submissions, flagged at-risk incorrectly | Exclude via filter or show as "Upcoming" |
| Cohort 5 partial data | Fewer submissions/reviews than established cohorts | Label as "Partial", compare cautiously |
| On-leave trainees | Metrics frozen at time of departure | Filter to active-only for operational views |
| Engagement score weights | 40/40/20 is arbitrary, not validated | Don't use as primary executive metric |
| Dummy data timestamps | Synthetic patterns, not real trends | Don't draw trend conclusions |

---

## QuickSight Dataset Connection

In QuickSight:
1. Datasets → Create dataset → Athena
2. Data source: `trainee-portal-athena`
3. Database: `trainee_portal_dev`
4. Select view name (e.g., `v_trainee_detail`)
5. Choose "Directly query your data" (SPICE has S3 permission issues)
6. Visualize

### Recommended datasets to add:

| Priority | View | Used for |
|----------|------|----------|
| 1 | `v_trainee_detail` | Main dashboard (all visuals) |
| 2 | `v_cohort_health` | Cohort Health Matrix table |
| 3 | `v_submissions_detail` | Drill-down into individual submissions |

---

## Dashboard Layout (from dashboard.md)

```
┌──────────────────────────────────────────────────────────────┐
│              TRAINEE PROGRAM EXECUTIVE DASHBOARD             │
├──────────────────────────────────────────────────────────────┤
│  Filters: Cohort | Status | Risk | Review Status            │
├──────────────────────────────────────────────────────────────┤
│  DATA COVERAGE: 50% Reviewed | C5 Partial | C6 Upcoming     │
├──────────────────────────────────────────────────────────────┤
│  KPIs: Total | Active | At-Risk | Risk% | Avg Score | Participation │
├──────────────────────────────────────────────────────────────┤
│  COHORT HEALTH MATRIX (table with conditional formatting)    │
├─────────────────────────────┬────────────────────────────────┤
│ Score by Cohort (bar)       │ Score Distribution (histogram) │
├─────────────────────────────┼────────────────────────────────┤
│ Participation by Cohort     │ On-Time vs Late (stacked bar)  │
├─────────────────────────────┼────────────────────────────────┤
│ Attendance vs Score         │ Late Subs vs Score             │
│ (scatter)                   │ (scatter)                      │
├─────────────────────────────┴────────────────────────────────┤
│  RISK: Risk by Cohort (bar) │ Risk vs Performance (scatter)  │
├──────────────────────────────────────────────────────────────┤
│  TRAINEES REQUIRING ATTENTION (filtered table)               │
├──────────────────────────────────────────────────────────────┤
│  DATA METHODOLOGY (text box with caveats)                    │
└──────────────────────────────────────────────────────────────┘
```

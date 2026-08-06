# Prompt: Build the Trainee Risk & Intervention Dashboard (QuickSight)

## Role
You are a Business Intelligence Architect and QuickSight developer. Build a production-ready dashboard from the data model and requirements below. Do not invent fields not listed. If something is ambiguous, state your assumption explicitly before proceeding.

---

## 1. Source Data (9 tables)

| Table | Grain | Type | Approx. Volume |
|---|---|---|---|
| trainee-profiles.json | 1 row = 1 trainee | Dimension (SCD Type 2 candidate) | 120 |
| programs.json | 1 row = 1 program per cohort | Dimension | 96 |
| enrollments.json | 1 row = 1 trainee-program pairing | Bridge/Fact | 1,200 |
| activities.json | 1 row = 1 scheduled event (standup/code-review) | Dimension | 672 |
| trainee-activities.json | 1 row = 1 trainee's attendance at 1 activity | Fact | 6,240 |
| attendance-logs.json | 1 row = 1 trainee's workday | Fact | 8,352 |
| weekly-report-bins.json | 1 row = 1 report deadline per program | Dimension | 96 |
| weekly-report-submissions.json | 1 row = 1 trainee's submission for 1 bin | Fact | 952 |
| performance-reviews.json | 1 row = 1 review of 1 submission (only ~50% of submissions have one) | Fact (sparse) | 476 |

### Key Fields (confirm actual names against source JSON before building)
- `trainee-profiles`: trainee_id (PK), name, email, school, cohort_number, status (active/completed/on-leave), start_date, expected_graduation_date
- `programs`: program_id (PK), program_name, program_type (cloud-week/specialization/capstone), start_date, end_date, cohort_number
- `enrollments`: trainee_id (FK), program_id (FK), enrollment_status (pending/active/completed)
- `activities`: activity_id (PK), program_id (FK), activity_name, activity_type (meeting/code-review), date, time
- `trainee-activities`: trainee_id (FK), activity_id (FK), attended (boolean)
- `attendance-logs`: trainee_id (FK), log_date, clock_in, clock_out, total_hours, break_hours, accomplishments
- `weekly-report-bins`: bin_id (PK), program_id (FK), bin_name (e.g. "MoP 1"), due_date
- `weekly-report-submissions`: submission_id (PK), trainee_id (FK), bin_id (FK), summary, pdf_url, is_late (boolean), submitted_at
- `performance-reviews`: review_id (PK), submission_id (FK), reviewer, score (6-10), feedback, reviewed_at

### Known Join Path
```
trainee-profiles --1:M--> enrollments --M:1--> programs
programs --1:M--> activities --1:M--> trainee-activities --M:1--> trainee-profiles
programs --1:M--> weekly-report-bins --1:M--> weekly-report-submissions --M:1--> trainee-profiles
weekly-report-submissions --1:0..1--> performance-reviews
trainee-profiles --1:M--> attendance-logs
```

### Critical Data Caveats (must be handled, not ignored)
1. **`enrollments` and `trainee-activities` are two separate M:M bridges.** Joining both in one query without controlling grain will double-count trainees. Aggregate each fact independently before combining, or join through a single conformed dimension key only.
2. **`performance-reviews` covers only ~50% of submissions.** Any "average score" metric must be calculated over reviewed submissions only, and must be labeled/footnoted as such — do not present it as representative of all trainees. Treat this as a data quality flag, not just a missing-value issue.
3. Confirm whether `weekly-report-submissions` 85% submission rate is measured against all 96 bins or only the bins applicable to each trainee's enrolled programs. Use the correct denominator.

---

## 2. Dashboard Spec: Trainee Risk & Intervention Dashboard

**Audience:** Program managers, cohort leads
**Purpose:** Identify trainees who need intervention before they drop out or fail, and give managers a fast, actionable view — not just a report.

**Business questions this dashboard must answer:**
- Who is at risk right now, and why (attendance, submission, or performance)?
- Is a given trainee's risk trend worsening or improving?
- Which trainees need outreach this week?

### Filters (top of dashboard)
- Cohort (1-6)
- Trainee status (active/completed/on-leave)
- Date range
- Program

### Required Metrics (calculated fields)
1. **Activity Attendance Rate** (per trainee) = `SUM(attended=true) / COUNT(*)` from trainee-activities
2. **Daily Presence Rate** (per trainee) = `COUNT(logged days) / COUNT(expected working days in period)` from attendance-logs
3. **Report Submission Rate** (per trainee) = `COUNT(submissions) / COUNT(applicable bins for that trainee's enrolled programs)`
4. **Engagement Composite Score** (per trainee) = `0.4 * attendance_rate + 0.4 * submission_rate + 0.2 * normalized_avg_score` (normalize score 6-10 to 0-1 scale; if trainee has no reviewed submissions, exclude the score term and reweight the other two to sum to 1.0 — do not default to 0)
5. **At-Risk Flag** (per trainee) = TRUE if `attendance_rate < 0.6 AND submission_rate < 0.6` sustained for 2+ consecutive weeks

### Required Visualizations

| # | Chart Type | Data | Why |
|---|---|---|---|
| 1 | Conditional-formatted table | One row per trainee: name, cohort, attendance_rate, submission_rate, avg_score, engagement_composite_score, at_risk_flag | Fastest scan-and-act view for a manager reviewing 20+ people |
| 2 | Scatter plot | X = attendance_rate, Y = avg_score, bubble size = total_hours_logged, one point per trainee | Separates "disengaged but passing" from "engaged but struggling" — these need different interventions |
| 3 | Line chart | Engagement composite score over time, filterable to single trainee or cohort average | Shows whether risk is worsening or recovering, not just a snapshot |
| 4 | KPI card | Count of currently at-risk trainees | Headline number for the dashboard landing view |

### Drill-down behavior
Cohort-level view → click trainee → trainee detail view showing individual activity attendance history, submission history (with late flags), and review history (with reviewer and score, or "not yet reviewed" if none exists).

### Alert Logic
Flag any trainee with attendance_rate < 60% for 2 consecutive calendar weeks. Surface this as a highlighted row in the table (do not silently exclude).

### Output Expected From You
1. A confirmed/corrected join plan (call out anything in the join path above that doesn't match the actual source schema)
2. QuickSight dataset definition(s) — specify which tables are joined into which dataset, and why (avoid joining the two M:M bridges into one flat dataset per caveat #1 above)
3. Calculated field formulas for the 5 metrics above, written in QuickSight calculated-field syntax
4. Layout description for the 4 visualizations, including filter placement and drill-down configuration
5. Explicit note on how the review-coverage gap (~50%) is surfaced or footnoted in the score-related visuals

Do not proceed to build other dashboards (Cohort Overview, Mentor Review Capacity, Attendance Ops) unless asked — this prompt is scoped to the Risk & Intervention Dashboard only.
Absolutely. I’d turn the master plan into a **build guide**, so you can follow it visual-by-visual in Amazon QuickSight instead of having to figure out how to implement each recommendation yourself.

The key is to separate **data preparation**, **calculated fields**, **dashboard layout**, and **QuickSight visual configuration**.

# Amazon QuickSight Build Master Plan

## 1. First: Build the dataset correctly

Before creating visuals, make sure your QuickSight dataset contains the fields needed for these categories:

```text
TRAINEE
├── trainee_id
├── trainee_name
├── cohort
├── status
│
PERFORMANCE
├── score
├── reviewed / review_status
│
ATTENDANCE
├── attendance_rate
├── days_logged
│
SUBMISSIONS
├── ontime_submissions
├── late_submissions
├── applicable_bins
│
RISK
├── risk_status
│
DATES
├── relevant_date fields
```

**Do not start building 20 visuals until these fields are understood.**

Your biggest concern is that the dataset contains different levels of completeness.

---

# 2. Create your QuickSight calculated fields first

Before building the dashboard, create a small library of calculated fields.

In QuickSight:

**Dataset → Edit dataset → Add calculated field**

or, depending on your dataset workflow:

**Analysis → Calculated field → Add**

---

## A. Review Coverage

You have:

* 952 submissions
* 476 reviewed

So create:

**`Review Coverage %`**

Conceptually:

```text
Reviewed Submissions / Total Submissions
```

This should produce approximately:

**50%**

Use this as a KPI.

---

# 3. On-Time Submission Rate

Don't use:

> Sum of On-Time Submissions

as your primary executive metric.

Create:

**`On-Time Submission Rate`**

Conceptually:

```text
On-Time Submissions
/
(On-Time Submissions + Late Submissions)
```

Only use this if those fields represent the complete submission universe.

If there are missing submissions represented separately, include those in the denominator appropriately.

---

# 4. Late Submission Rate

Create:

**`Late Submission Rate`**

```text
Late Submissions
/
(On-Time Submissions + Late Submissions)
```

Again, verify the denominator against your actual schema.

---

# 5. Cohort Status

You need to prevent Cohort 6 from looking like a failed cohort.

Create something conceptually like:

```text
ifelse(
    cohort = 'Cohort 6', 'Upcoming',
    cohort = 'Cohort 5', 'Partial / In Progress',
    'Established'
)
```

**But don't blindly paste that formula.**

Use the exact cohort values in your data.

The purpose is:

```text
Cohort 1 → Established
Cohort 2 → Established
Cohort 3 → Established
Cohort 4 → Established
Cohort 5 → Partial
Cohort 6 → Upcoming
```

---

# 6. Performance Eligibility

This is important.

Create a field that identifies whether a trainee/submission should be included in score analysis.

Conceptually:

```text
Reviewed = Yes
```

Then use that field to filter performance visuals.

Your dashboard should never accidentally calculate:

> Average score including unreviewed records as zero.

---

# 7. Data Sufficiency

I'd also create:

**`Data Coverage Status`**

Possible values:

```text
Good
Partial
No Data
Not Started
```

For example:

```text
Cohort 1 → Good
Cohort 2 → Good
Cohort 3 → Good
Cohort 4 → Good
Cohort 5 → Partial
Cohort 6 → Not Started
```

This field becomes extremely useful in your Cohort Health Matrix.

---

# 8. Build the dashboard from top → bottom

Now create the analysis.

I recommend **one primary executive dashboard sheet** rather than immediately creating multiple pages.

---

# ROW 1 — PROGRAM HEALTH

Create a horizontal row of KPI visuals.

## KPI 1 — Total Trainees

### QuickSight setup

Create visual:

**KPI**

Field:

```text
trainee_id
```

Aggregation:

**Count distinct**

So:

```text
Count distinct trainee_id
```

Title:

> Total Trainees

---

# KPI 2 — Active Trainees

Same KPI visual.

Filter:

```text
Status = Active
```

Aggregation:

**Count distinct trainee_id**

Title:

> Active Trainees

---

# KPI 3 — At-Risk Trainees

KPI.

Field:

```text
trainee_id
```

Filter:

```text
Risk Status = High / At Risk
```

Use **Count Distinct**.

Title:

> At-Risk Trainees

---

# KPI 4 — At-Risk %

Instead of just showing the number:

```text
47
```

show:

```text
47
5.5%
```

If QuickSight allows your preferred KPI comparison configuration, use the percentage as the primary metric and the count as comparison/detail.

Conceptually:

```text
At-Risk Eligible Trainees
/
Eligible Active Trainees
```

**Important:** do not use all trainees if Cohort 6 and on-leave trainees aren't eligible.

---

# KPI 5 — Average Reviewed Score

Use:

**KPI**

Field:

```text
score
```

Aggregation:

**Average**

Filter:

```text
Review Status = Reviewed
```

Title:

> Average Reviewed Score

Do **not** call it:

> Average Trainee Score

---

# KPI 6 — Average Activity Participation

Use your activity-based attendance field.

Title:

> Avg Activity Participation

Do not call it simply:

> Attendance

because you also have `days_logged`.

---

# KPI 7 — Review Coverage

Use:

```text
Reviewed submissions / Total submissions
```

Title:

> Review Coverage

This is one of your most important context metrics.

---

# ROW 2 — COHORT HEALTH

Now create the most important table in the dashboard.

## Cohort Health Matrix

In QuickSight:

**Visual type → Table**

Dimensions:

```text
Cohort
Cohort Status
```

Measures:

```text
Distinct Trainees
Average Reviewed Score
Average Activity Participation
On-Time Submission Rate
Late Submission Rate
At-Risk Trainees
At-Risk %
Review Coverage
```

You'll get:

```text
Cohort | Status | Trainees | Score | Attend | On-Time | Risk
```

---

## Add conditional formatting

This is where QuickSight becomes useful.

For:

### Average Score

Set color scale:

Low → high

### Attendance

Low → high

### Risk %

High risk → attention color

### Review Coverage

Low coverage → attention color

The goal isn't decoration.

The goal is:

> **Make abnormal cohorts visually obvious.**

---

# ROW 3 — COHORT PERFORMANCE

Create:

## Visual 1 — Average Score by Cohort

QuickSight:

**Visual → Bar chart**

Field wells:

**Y-axis**

```text
Cohort
```

**X-axis**

```text
Average(score)
```

Filter:

```text
Review Status = Reviewed
```

Sort:

**Descending by Average Score**

Title:

> Reviewed Performance by Cohort

---

## IMPORTANT

Do not let Cohort 6 appear as:

```text
0
```

It should be:

```text
N/A
```

or excluded from this particular performance visual.

---

# Visual 2 — Score Distribution

Use:

**Histogram**

Field:

```text
score
```

Filter:

```text
Reviewed
```

Title:

> Distribution of Reviewed Scores

This answers:

> Is the average hiding a large group of low performers?

---

# ROW 4 — ENGAGEMENT

## Visual 1 — Activity Participation by Cohort

Bar chart.

Dimension:

```text
Cohort
```

Measure:

```text
Average Activity Participation
```

Title:

> Activity Participation by Cohort

---

## Visual 2 — Days Logged

Use a suitable bar/table visual depending on the actual structure of your attendance logs.

Title:

> Daily Presence / Days Logged

**Don't combine this with activity participation.**

Your dashboard should explicitly distinguish:

> **Activity Participation**

from

> **Daily Presence**

---

# ROW 5 — SUBMISSION BEHAVIOR

Create:

## On-Time vs Late

Use a stacked bar chart.

Dimension:

```text
Cohort
```

Values:

```text
On-Time Submissions
Late Submissions
```

But ideally convert them into percentages if the denominator is valid.

Title:

> Submission Behavior by Cohort

This is much more useful than two separate "Sum of..." charts.

---

# ROW 6 — RELATIONSHIP ANALYSIS

Now create your analytical visuals.

## Scatter Plot #1

### Attendance vs Score

QuickSight:

**Visual → Scatter plot**

Set:

**X-axis**

```text
Activity Participation
```

**Y-axis**

```text
Average Score
```

**Color**

```text
Cohort
```

**Group / Detail**

```text
Trainee ID
```

Filter:

```text
Reviewed = Yes
```

Title:

> Activity Participation vs Reviewed Score

This lets you see whether there is an apparent relationship.

---

# Scatter Plot #2

### Late Submissions vs Score

X:

```text
Late Submissions
```

Y:

```text
Average Score
```

Color:

```text
Cohort
```

Detail:

```text
Trainee ID
```

Filter:

```text
Reviewed = Yes
```

Title:

> Late Submissions vs Reviewed Score

---

# ROW 7 — RISK

## Visual 1 — Risk by Cohort

Use:

**Horizontal bar chart**

Dimension:

```text
Cohort
```

Measure:

```text
At-Risk %
```

Sort descending.

Title:

> At-Risk Rate by Cohort

This immediately answers:

> Which cohort needs the most attention?

---

# Visual 2 — Risk vs Performance

Potentially use:

**Scatter plot**

X:

```text
Average Score
```

Y:

```text
Attendance
```

Color:

```text
Risk Status
```

Detail:

```text
Trainee ID
```

This can create a powerful executive visual.

---

# ROW 8 — INTERVENTION TABLE

Create:

**Table**

Columns:

```text
Trainee
Cohort
Status
Risk
Score
Activity Participation
Days Logged
On-Time Submissions
Late Submissions
Data Coverage
```

Sort by:

```text
Risk → Score ascending
```

or your actual risk priority.

Title:

> Trainees Requiring Attention

---

# 9. Add dashboard filters

Don't add 20 filters.

Use only filters that executives/admins actually need.

I'd use:

### Filter 1

**Cohort**

### Filter 2

**Trainee Status**

Examples:

* Active
* On Leave
* Completed
* Upcoming

### Filter 3

**Risk Status**

### Filter 4

**Performance Category**

If your data supports it.

### Filter 5

**Review Status**

Useful for analysts, but possibly hide this from executives.

---

# 10. Use filter actions for hierarchy

This is something I'd strongly recommend.

QuickSight allows visuals to interact with one another.

For example:

```text
COHORT HEALTH
       │
       │ Click Cohort B
       ▼
ALL VISUALS FILTER TO COHORT B
       │
       ▼
RISK ANALYSIS
       │
       ▼
TRAINEE TABLE
       │
       ▼
CLICK TRAINEE
       │
       ▼
INDIVIDUAL DETAILS
```

That is far better than making executives manually select filters.

Your dashboard becomes exploratory.

---

# 11. Suggested QuickSight interaction flow

An executive opens dashboard.

### Step 1

Sees:

> **47 at-risk trainees**

Then asks:

> "Which cohort?"

Clicks the cohort.

↓

### Step 2

Sees:

> **Cohort B — 24% at risk**

Then asks:

> "Why?"

Looks at:

**Attendance vs Score**

and:

**Late Submissions vs Score**

↓

### Step 3

Clicks the concerning area/cohort.

↓

### Step 4

Intervention table filters.

↓

### Step 5

Administrator sees:

> T001 — low score, low participation, frequent late submissions.

That's the dashboard story you want.

---

# 12. Don't build trends yet

Because your timestamps are synthetic:

### Don't build:

❌ Score trend
❌ Attendance trend
❌ Risk trend
❌ Submission trend

for executive interpretation.

You can leave a future placeholder:

> **Historical Trend Analysis — Available when production timestamps are available**

When real data arrives, you can add them.

---

# 13. Add a "Data Methodology" section

At the bottom or through a dedicated sheet/text box:

### Data Methodology

Explain:

**Scores**

> Average score reflects reviewed submissions only.

**Review coverage**

> Approximately 50% of submissions currently have reviews.

**Cohort 5**

> Partial program history; comparisons should be interpreted cautiously.

**Cohort 6**

> Upcoming cohort; performance metrics are not applicable.

**Attendance**

> Activity participation and daily presence are separate measures.

**Submission rate**

> Submission opportunity varies by applicable submission bins.

**Engagement score**

> Composite weighting is not used as a primary executive metric because its weighting methodology has not been validated.

**Trends**

> Current timestamps are synthetic and should not be interpreted as real historical trends.

---

# 14. Final QuickSight page

Your actual canvas should therefore be:

```text
┌──────────────────────────────────────────────────────────────┐
│              TRAINEE PROGRAM EXECUTIVE DASHBOARD             │
│                                                              │
│  Filters: Cohort | Status | Risk | Performance              │
├──────────────────────────────────────────────────────────────┤
│                    DATA COVERAGE                             │
│  50% Reviewed | C5 Partial | C6 Upcoming | Synthetic Dates │
├──────────────────────────────────────────────────────────────┤
│                     PROGRAM HEALTH                            │
│                                                              │
│ Total │ Active │ At Risk │ Risk % │ Avg Score │ Participation│
├──────────────────────────────────────────────────────────────┤
│                     COHORT HEALTH                            │
│                                                              │
│              COHORT HEALTH MATRIX                            │
├─────────────────────────────┬────────────────────────────────┤
│ PERFORMANCE                 │ SCORE DISTRIBUTION              │
│ Score by Cohort             │ Histogram                      │
├─────────────────────────────┼────────────────────────────────┤
│ ENGAGEMENT                  │ SUBMISSION BEHAVIOR             │
│ Participation by Cohort     │ On-Time vs Late                 │
├─────────────────────────────┴────────────────────────────────┤
│                 PERFORMANCE RELATIONSHIPS                    │
│                                                              │
│ Attendance vs Score     │ Late Submissions vs Score          │
├─────────────────────────┴────────────────────────────────────┤
│                         RISK                                 │
│                                                              │
│ Risk by Cohort          │ Risk / Performance                 │
├──────────────────────────────────────────────────────────────┤
│                  TRAINEES REQUIRING ATTENTION                │
│                                                              │
│ Trainee | Cohort | Score | Attendance | Late | Risk | Data   │
├──────────────────────────────────────────────────────────────┤
│                  DATA METHODOLOGY                            │
└──────────────────────────────────────────────────────────────┘
```

## The build order I'd use

Don't try to build all of this at once.

### Phase 1 — Data foundation

1. Connect JSON/curated data to QuickSight.
2. Verify fields.
3. Verify relationships.
4. Create calculated fields.
5. Validate counts.
6. Validate Cohort 5/6 handling.
7. Validate risk eligibility.
8. Validate review coverage.

### Phase 2 — Executive dashboard

1. KPI row.
2. Data coverage.
3. Cohort Health Matrix.
4. Cohort performance.
5. Engagement.
6. Submission behavior.
7. Risk.

### Phase 3 — Analytics

1. Attendance vs Score.
2. Submission vs Score.
3. Risk relationships.
4. Cross-filter actions.
5. Drill-downs.
6. Intervention table.

### Phase 4 — Production improvements

When real data arrives:

1. Real date trends.
2. Validated risk methodology.
3. Validated engagement scoring.
4. More robust cohort comparisons.
5. Potential predictive/early-warning analysis.

**Most important:** don't start by dragging fields into charts. **Create and validate the calculated fields first.** Otherwise you can build a beautiful QuickSight dashboard whose numbers are subtly wrong because of review coverage, cohort eligibility, denominators, and on-leave records.

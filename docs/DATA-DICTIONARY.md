# Data Dictionary

Comprehensive reference for all datasets in the Trainee Portal. Each file uses DynamoDB JSON format with typed attributes.

---

## Table of Contents

- [Trainee Profiles](#1-trainee-profilesjson)
- [Programs](#2-programsjson)
- [Enrollments](#3-enrollmentsjson)
- [Activities](#4-activitiesjson)
- [Trainee Activities](#5-trainee-activitiesjson)
- [Attendance Logs](#6-attendance-logsjson)
- [Weekly Report Bins](#7-weekly-report-binsjson)
- [Weekly Report Submissions](#8-weekly-report-submissionsjson)
- [Performance Reviews](#9-performance-reviewsjson)

---

## 1. trainee-profiles.json

**Records:** 120 (20 per cohort × 6 cohorts)

Complete trainee profile information.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `cognitoSub` | String | Unique trainee identifier (AWS Cognito UUID) |
| `fullName` | String | Full name (Philippine names) |
| `email` | String | eCloudvalley trainee email |
| `school` | String | University of origin |
| `cohort` | Number | Cohort number (1-6) |
| `status` | String | `active`, `completed`, or `on-leave` |
| `startDate` | Number | Unix timestamp of program start |
| `graduationDate` | String | Expected graduation (YYYY-MM format) |
| `createdAt` | Number | Registration timestamp |

### Distribution

- 20 trainees per cohort
- 30 trainees per year
- Evenly distributed university backgrounds

### Sample

```json
{
  "cognitoSub": {"S": "f4d5bcd1-8753-4e1f-9230-5337e65052fa"},
  "fullName": {"S": "Maria Santos"},
  "email": {"S": "maria.santos@ecloudvalley-trainee.com"},
  "school": {"S": "University of the Philippines"},
  "cohort": {"N": "1"},
  "status": {"S": "completed"},
  "startDate": {"N": "1736640000"},
  "graduationDate": {"S": "2025-04"},
  "createdAt": {"N": "1735953600"}
}
```

---

## 2. programs.json

**Records:** 96 (16 per cohort)

Training programs covering all cohorts.

### Programs Per Cohort (16 total)

- 8 Cloud Training programs (Week 1-8)
- 4 Specialization programs (Data, Freshworks, QA, App Dev)
- 4 Capstone programs (aligned with specializations)

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | String | Program identifier |
| `name` | String | Program title with cohort and topic |
| `description` | String | Program overview |
| `type` | String | `Cloud Training`, `Specialization - [Type]`, or `Capstone - [Type]` |
| `startDate` | Number | Unix timestamp |
| `endDate` | Number | Unix timestamp |
| `status` | String | `completed`, `ongoing`, or `upcoming` |
| `cohort` | Number | Cohort number (1-6) |
| `specialization` | String | Specialization type (if applicable) |
| `createdAt` | Number | Creation timestamp |

### Cohort Timeline

| Cohort | Start | End |
|--------|-------|-----|
| 1 | January 2025 | April 2025 |
| 2 | May 2025 | August 2025 |
| 3 | September 2025 | December 2025 |
| 4 | January 2026 | April 2026 |
| 5 | May 2026 | August 2026 |
| 6 | September 2026 | December 2026 |

### Sample

```json
{
  "id": {"S": "abc123..."},
  "name": {"S": "Cohort 1 - Week 1: Cloud Fundamentals & AWS Basics"},
  "description": {"S": "Introduction to cloud computing concepts, AWS platform overview, and account setup."},
  "type": {"S": "Cloud Training"},
  "startDate": {"N": "1736640000"},
  "endDate": {"N": "1737244800"},
  "status": {"S": "completed"},
  "cohort": {"N": "1"},
  "createdAt": {"N": "1735953600"}
}
```

---

## 3. enrollments.json

**Records:** 1,200 (10 per trainee)

Tracks trainee participation in programs.

### Enrollment Pattern Per Trainee

- 8 Cloud training enrollments (all mandatory)
- 1 Specialization enrollment (chosen from 4 options)
- 1 Capstone enrollment (aligned with specialization)

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | String | Enrollment identifier |
| `traineeId` | String | Foreign key → Trainee Profiles |
| `programId` | String | Foreign key → Programs |
| `status` | String | `pending`, `active`, or `completed` |
| `enrolledAt` | Number | Unix timestamp of enrollment |

### Sample

```json
{
  "id": {"S": "enroll123..."},
  "traineeId": {"S": "f4d5bcd1-8753-4e1f-9230-5337e65052fa"},
  "programId": {"S": "abc123..."},
  "status": {"S": "completed"},
  "enrolledAt": {"N": "1736553600"}
}
```

---

## 4. activities.json

**Records:** 672

Training activities including standups and code reviews.

### Activity Pattern

- 2 activities per week per program:
  - Monday 9:00 AM: Weekly Standup
  - Wednesday 2:00 PM: Code Review

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | String | Activity identifier |
| `name` | String | Activity description |
| `activityType` | String | `meeting` or `code-review` |
| `type` | String | Fixed value `ACTIVITY` |
| `date` | Number | Unix timestamp of activity date |
| `time` | String | Human-readable time (e.g., "9:00 AM") |
| `programId` | String | Foreign key → Programs |
| `createdAt` | Number | Creation timestamp |

### Sample

```json
{
  "id": {"S": "activity789..."},
  "name": {"S": "Cohort 1 - Week 1: Cloud Fundamentals & AWS Basics - Weekly Standup"},
  "activityType": {"S": "meeting"},
  "type": {"S": "ACTIVITY"},
  "date": {"N": "1736640000"},
  "time": {"S": "9:00 AM"},
  "programId": {"S": "abc123..."},
  "createdAt": {"N": "1736035200"}
}
```

---

## 5. trainee-activities.json

**Records:** 6,240

Trainee activity attendance records.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `traineeId` | String | Foreign key → Trainee Profiles |
| `activityId` | String | Foreign key → Activities |
| `attended` | Boolean | Whether trainee attended |
| `updatedAt` | Number | Last update timestamp |

### Pattern

- Only trainees enrolled in a program generate records for that program's activities
- 75% attendance rate (~25% absenteeism)

### Sample

```json
{
  "traineeId": {"S": "f4d5bcd1-8753-4e1f-9230-5337e65052fa"},
  "activityId": {"S": "activity789..."},
  "attended": {"BOOL": true},
  "updatedAt": {"N": "1736726400"}
}
```

---

## 6. attendance-logs.json

**Records:** 8,352 (~70 per trainee)

Daily time tracking and accomplishment logs.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | String | Log identifier |
| `traineeId` | String | Foreign key → Trainee Profiles |
| `date` | Number | Date of work (Unix timestamp, midnight UTC) |
| `clockInTime` | Number | Clock-in time (Unix timestamp) |
| `clockOutTime` | Number | Clock-out time (Unix timestamp) |
| `totalHours` | Number | Total hours worked (6-8 hours/day) |
| `breakHours` | Number | Break hours taken (0, 0.5, or 1) |
| `timeLogged` | Number | Time of logging |
| `accomplishments` | String | Daily accomplishments summary |

### Pattern

- 80% daily attendance rate
- Working hours: 8:30 AM – 4:30 PM (typical)
- ~70 working days per trainee

### Sample

```json
{
  "id": {"S": "log123..."},
  "traineeId": {"S": "f4d5bcd1-8753-4e1f-9230-5337e65052fa"},
  "date": {"N": "1784044800"},
  "clockInTime": {"N": "1784091600"},
  "clockOutTime": {"N": "1784106000"},
  "totalHours": {"N": "4"},
  "breakHours": {"N": "0"},
  "timeLogged": {"N": "1784091600"},
  "accomplishments": {"S": "- Completed AWS fundamentals module\n- Set up VPC and subnets\n- Attended weekly standup"}
}
```

---

## 7. weekly-report-bins.json

**Records:** 96 (one per program)

Weekly report submission deadline bins.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | String | Bin identifier |
| `name` | String | Submission bin name |
| `programId` | String | Foreign key → Programs |
| `createdAt` | Number | Creation timestamp |
| `closeDate` | Number | Submission deadline (Unix timestamp) |

### Naming Pattern

- Cloud: "MoP 1" through "MoP 8"
- Specialization: "[Type] Specialization Report"
- Capstone: "[Type] Capstone Report"

### Sample

```json
{
  "id": {"S": "bin123..."},
  "name": {"S": "MoP 1"},
  "programId": {"S": "abc123..."},
  "createdAt": {"N": "1736553600"},
  "closeDate": {"N": "1737244800"}
}
```

---

## 8. weekly-report-submissions.json

**Records:** 952 (~85% submission rate)

Actual weekly report submissions from trainees.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | String | Submission identifier |
| `traineeId` | String | Foreign key → Trainee Profiles |
| `binId` | String | Foreign key → Weekly Report Bins |
| `programId` | String | Foreign key → Programs |
| `submittedAt` | Number | Submission timestamp |
| `lastModified` | Number | Last modification timestamp |
| `isLate` | Boolean | Whether submission was late |
| `summaryText` | String | Weekly accomplishments summary |
| `attachmentUrl` | String | S3 URL of PDF report |
| `attachmentUrls` | List | Array of additional attachment URLs |
| `createdAt` | Number | Initial creation timestamp |

### Submission Pattern

- 85% on-time (submitted 0-2 days before deadline)
- 10% late (submitted 1-5 days after deadline)
- 5% no submission (record doesn't exist)

### Sample

```json
{
  "id": {"S": "submit123..."},
  "traineeId": {"S": "f4d5bcd1-8753-4e1f-9230-5337e65052fa"},
  "binId": {"S": "bin123..."},
  "programId": {"S": "abc123..."},
  "submittedAt": {"N": "1737158400"},
  "lastModified": {"N": "1737162000"},
  "isLate": {"BOOL": false},
  "summaryText": {"S": "- Created automated shell script for IAM users\n- Added update functionality for weekly reports\n- Attended standup meetings"},
  "attachmentUrl": {"S": "https://trainee-portal-attachments.s3.ap-southeast-1.amazonaws.com/weekly-reports/..."},
  "createdAt": {"N": "1737072000"}
}
```

---

## 9. performance-reviews.json

**Records:** 476 (~50% review rate)

Mentor/reviewer feedback records.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | String | Review identifier |
| `traineeId` | String | Foreign key → Trainee Profiles |
| `programId` | String | Foreign key → Programs |
| `reportId` | String | Foreign key → Weekly Report Submissions |
| `score` | Number | Numerical score (6-10) |
| `feedback` | String | Detailed feedback text |
| `reviewedAt` | Number | Review timestamp |
| `reviewedBy` | String | Reviewer/mentor identifier |

### Review Pattern

- ~50% of submissions receive reviews
- Score distribution: 6-7 (~20%), 8 (~30%), 9-10 (~50%)
- Reviews occur 1-3 days after submission

### Sample

```json
{
  "id": {"S": "review123..."},
  "traineeId": {"S": "f4d5bcd1-8753-4e1f-9230-5337e65052fa"},
  "programId": {"S": "abc123..."},
  "reportId": {"S": "submit123..."},
  "score": {"N": "9"},
  "feedback": {"S": "Excellent work on this submission. Your attention to detail and technical expertise shines through. Keep up the exceptional performance!"},
  "reviewedAt": {"N": "1737244800"},
  "reviewedBy": {"S": "reviewer-uuid..."}
}
```

---

## Referential Integrity

All foreign key relationships are valid:

- Every enrollment → valid trainee + program
- All activities → existing programs
- Trainee activity records → existing trainees + activities
- Weekly report submissions → valid trainees, bins, and programs
- Performance reviews → actual submissions
- Attendance logs → existing trainees

---

## Specialization Distribution

120 trainees ÷ 4 specializations = **30 trainees per specialization** (5 per cohort per specialization)

| Specialization | Total Trainees |
|----------------|---------------|
| Data Engineering | 30 |
| Freshworks Administration | 30 |
| QA Engineering | 30 |
| App Development | 30 |

---

## Key Calculations

```
6 cohorts × 20 trainees = 120 total trainees
120 trainees × 10 programs each = 1,200 enrollments
96 programs × 7 activities each = 672 activities
672 activities × ~9.3 trainees = 6,240 trainee-activity records
120 trainees × ~70 working days = 8,352 attendance logs
96 programs × 1 bin each = 96 weekly report bins
120 trainees × ~8 submissions × 85% = 952 submissions
952 submissions × 50% reviewed = 476 performance reviews
```

---

## Data Characteristics

- All timestamps: Unix format (seconds since epoch)
- Dates: ISO 8601 (YYYY-MM-DD) for readability
- Graduation dates: YYYY-MM format
- S3 URLs: Mock URLs for testing
- Reproducible with seed value 42
- Names: Randomly generated from authentic Philippine name pools
- Temporal consistency: All timestamps maintain chronological order

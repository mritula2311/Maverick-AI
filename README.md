# MaverickAI — AI-Powered Fresher Onboarding & Training Platform

MaverickAI is a full-stack enterprise platform that automates the complete fresher onboarding lifecycle using a multi-agent AI architecture. Freshers follow structured training curricula, take AI-evaluated quizzes and assignments, earn badges, and receive PDF progress reports. Managers get real-time analytics on their cohort. Admins control the entire platform.

Built for the **Hexaware Hackathon 2026**.

---

## Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [System Architecture](#system-architecture)
4. [Prerequisites](#prerequisites)
5. [Quick Start](#quick-start)
6. [Manual Setup](#manual-setup)
7. [Default Credentials](#default-credentials)
8. [Role Capabilities](#role-capabilities)
9. [AI Agent Details](#ai-agent-details)
10. [Ollama Integration](#ollama-integration)
11. [API Reference](#api-reference)
12. [Project Structure](#project-structure)
13. [Environment Variables](#environment-variables)
14. [Known Limitations](#known-limitations)

---

## Features

- **AI Quiz Evaluation** — LLM-powered grading that returns a competency level, strengths, development areas, recommended actions, and HR notes for every quiz submission
- **AI Assignment Evaluation** — Rubric-based scoring with depth-of-understanding analysis, professional quality rating, and business readiness assessment
- **Automated Onboarding** — Agent-driven curriculum assignment and schedule generation personalised to each fresher's department
- **Performance Analytics** — Real-time score tracking, progress trends, and batch-level comparisons for managers
- **PDF Report Generation** — Downloadable individual progress reports and assessment result exports
- **Badge & Certification System** — Badges awarded automatically when score thresholds are crossed; certification records maintained per curriculum
- **Role-Based Access Control** — Three completely separate dashboards (fresher / manager / admin) with JWT-enforced permissions
- **Mock AI Fallback** — Every flow works without Ollama installed; evaluations return deterministic mock responses with the correct schema

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Backend framework | FastAPI | 0.104.1 |
| ASGI server | Uvicorn | 0.24.0 |
| ORM | SQLAlchemy | 2.0.23 |
| Database | SQLite (local) | — |
| Auth | python-jose (JWT) + passlib/bcrypt | 3.3.0 / 4.1.2 |
| LLM runtime | Ollama HTTP API | latest |
| PDF (reports) | fpdf2 | 2.7.6 |
| PDF (premium) | reportlab | 4.0.7 |
| Frontend framework | Next.js | 14 |
| Language | TypeScript | 5 |
| Styling | Tailwind CSS | 3 |

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      Next.js 14 Frontend                         │
│          http://localhost:3000                                    │
│                                                                  │
│   ┌─────────────────┐  ┌──────────────────┐  ┌──────────────┐   │
│   │ Fresher Dashboard│  │Manager Dashboard │  │ Admin Panel  │   │
│   │ • Overview       │  │ • Team Overview  │  │ • User Mgmt  │   │
│   │ • Learning       │  │ • Fresher Detail │  │ • Curricula  │   │
│   │ • Schedule       │  │ • Analytics      │  │ • Stats      │   │
│   │ • Assessments    │  │ • Reports        │  │              │   │
│   │ • Profile/Badges │  │ • Schedules      │  │              │   │
│   └─────────────────┘  └──────────────────┘  └──────────────┘   │
└───────────────────────────────┬──────────────────────────────────┘
                                │ REST API (Bearer JWT)
┌───────────────────────────────▼──────────────────────────────────┐
│                     FastAPI Backend                               │
│                  http://localhost:8000                            │
│                                                                  │
│  Route Groups:                                                   │
│  /api/v1/auth          /api/v1/assessments    /api/v1/admin      │
│  /api/v1/freshers      /api/v1/analytics      /api/v1/premium    │
│  /api/v1/schedules     /api/v1/reports        /api/v1/certifs    │
│  /api/v1/curricula     /api/v1/agents         /api/v1/workflows  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                      AI Agent Layer                        │  │
│  │                                                            │  │
│  │  QuizEvaluatorAgent        AssignmentEvaluatorAgent        │  │
│  │  AssessmentAgent           ProfileAgent (badges)           │  │
│  │  OnboardingAgent           AnalyticsAgent                  │  │
│  │  ReportingAgent                                            │  │
│  └───────────────────────────┬────────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────▼────────────────────────────────┐  │
│  │          SQLAlchemy 2.0  ←→  SQLite (maverickai.db)        │  │
│  └────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬──────────────────────────────────┘
                                │ HTTP
┌───────────────────────────────▼──────────────────────────────────┐
│                    Ollama LLM Server                              │
│                 http://localhost:11434                            │
│            Models: neural-chat  |  mistral                       │
└──────────────────────────────────────────────────────────────────┘
```

### Request Flow — Quiz Submission

```
Fresher submits quiz answers
        │
        ▼
POST /api/v1/assessments/{id}/submit
        │
        ▼
AssessmentAgent.evaluate()
        │
        ▼
QuizEvaluatorAgent.evaluate(questions, answers)
        │
        ├── LLMClient.generate(prompt)
        │         │
        │         ├── Ollama online  →  neural-chat model response
        │         └── Ollama offline →  _mock_response() (same schema)
        │
        ▼
Score + HR feedback JSON saved to Submission record
        │
        ▼
ProfileAgent.check_badges(fresher_id)   ← awards badges if threshold crossed
        │
        ▼
AnalyticsAgent.update(fresher_id)       ← recalculates running stats
        │
        ▼
Response returned to frontend with score, competency_level, feedback
```

---

## Prerequisites

| Requirement | Minimum Version | Install |
|---|---|---|
| Python | 3.11 | https://python.org |
| Node.js | 18 | https://nodejs.org |
| npm | bundled with Node | — |
| Ollama | latest | https://ollama.ai (optional) |

Ollama is optional. The platform runs in **mock mode** without it — all AI evaluations return structured demo responses and every feature remains usable.

---

## Quick Start

### Windows — PowerShell

```powershell
cd HEXAWARE-HACKATHON-
.\start.ps1
```

### Linux / macOS / Git Bash

```bash
cd HEXAWARE-HACKATHON-
chmod +x start.sh
./start.sh
```

Both scripts do the following automatically:

1. Verify Python, Node.js, and Ollama are installed
2. Start the Ollama server and pull the `mistral` model (if Ollama is present)
3. Create a Python virtual environment inside `backend/.venv`
4. Install all backend dependencies from `requirements.txt`
5. Create `backend/.env` from the example file if it does not exist
6. Start the FastAPI backend on **port 8000** and wait for `/health` to return 200
7. Install frontend npm dependencies if `node_modules` is absent
8. Create `frontend/.env.local` with the backend URL if it does not exist
9. Start Next.js on **port 3000**
10. Print all URLs, credentials, and log paths
11. Clean up every process on Ctrl+C

**Runtime logs** are written to `logs/` in the project root:

```
logs/
  backend.log        backend stdout
  backend_err.log    backend stderr
  frontend.log       frontend stdout
  frontend_err.log   frontend stderr
  ollama.log         Ollama stdout + pull progress
  ollama_err.log     Ollama stderr
```

---

## Manual Setup

If you need to start services individually:

### 1. Ollama (optional)

```bash
# Start Ollama server
ollama serve

# Pull models (in a separate terminal)
ollama pull neural-chat
ollama pull mistral
```

### 2. Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env          # or create manually — see Environment Variables section

# Start
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The SQLite database (`maverickai.db`) is created automatically on first startup along with all seed data.

### 3. Frontend

```bash
cd frontend

# Install dependencies
npm install --legacy-peer-deps

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local

# Start
npm run dev
```

---

## Default Credentials

Seed data is inserted automatically when the database is empty:

| Role | Email | Password |
|---|---|---|
| Fresher | alice@maverick.ai | password123 |
| Fresher | john@maverick.ai | password123 |
| Fresher | bob@maverick.ai | password123 |
| Fresher | emily@maverick.ai | password123 |
| Manager | manager@maverick.ai | password123 |
| Admin | admin@maverick.ai | **admin123** |

> The admin password is intentionally different. Never use these credentials in a production environment.

---

## Role Capabilities

### Fresher

The primary learner interface.

| Section | What it does |
|---|---|
| **Overview** | Shows training progress percentage, current score, upcoming assessments, and badges earned |
| **Learning** | Browse and read curriculum modules assigned by the manager; content is organised by topic and difficulty |
| **Schedule** | Weekly training calendar showing module sessions and assessment due dates |
| **Assessments** | Take quizzes (multiple-choice), submit written assignments, or complete code challenges |
| **Assessment Results** | Detailed AI feedback: competency level, strengths, development areas, recommended actions, and HR notes |
| **Profile** | Earned badges with criteria, certification progress, overall score history |

Assessment workflow:

1. Fresher opens an assessment and clicks Start
2. For a quiz: answers multiple-choice questions and submits
3. For an assignment: writes a free-text response and submits
4. The AI evaluator runs immediately; results are shown on the results page
5. Score is added to the fresher's running average; badges are checked and awarded

### Manager

Team oversight and reporting.

| Section | What it does |
|---|---|
| **Team Overview** | Table of all freshers with progress %, scores, active status, and at-risk flags |
| **Fresher Detail** | Full individual profile: quiz history, assignment scores, AI-generated summary, schedule adherence |
| **Analytics** | Batch score distributions, completion rates, top performers, at-risk cohort |
| **Schedule Management** | Create training schedules; assign assessments to time slots |
| **Reports** | Generate and download PDF progress reports for individuals or the whole batch |

### Admin

Full platform control.

| Section | What it does |
|---|---|
| **Dashboard** | Platform-wide stats: total users by role, assessment completion rates, system health |
| **User Management** | Create accounts, activate/deactivate users across all roles |
| **Curriculum Management** | Create learning modules, organise by department, assign to fresher batches |
| **Assessment Configuration** | Build quiz question banks, set passing thresholds, configure AI evaluator parameters |
| **Badge Management** | Define badge names, icons, score thresholds, and award criteria |
| **Demo Data Reset** | Re-seed the database with fresh demo data without restarting the server |

---

## AI Agent Details

All agents inherit from `BaseAgent` in `backend/app/agents/base.py` and interact with Ollama through `LLMClient`.

### QuizEvaluatorAgent

**File:** `backend/app/agents/quiz_evaluator_agent.py`

Evaluates multiple-choice quiz submissions. Sends the question bank and fresher's answers to the LLM using a corporate HR learning prompt. Returns:

```json
{
  "overall_assessment": "Narrative summary of the attempt",
  "competency_level": "Exceeds Expectations | Meets Expectations | Below Expectations",
  "strengths": ["..."],
  "development_areas": ["..."],
  "recommended_actions": ["..."],
  "hr_notes": "HR-facing commentary"
}
```

The numeric score is computed separately as percentage of correct answers × 100.

### AssignmentEvaluatorAgent

**File:** `backend/app/agents/assignment_evaluator_agent.py`

Evaluates free-text assignment submissions against a rubric. Returns:

```json
{
  "score": 75,
  "overall_assessment": "...",
  "competency_rating": "Adequate | Proficient | Exemplary",
  "strengths": ["..."],
  "areas_for_improvement": ["..."],
  "content_analysis": {
    "depth_of_understanding": "...",
    "clarity_of_communication": "...",
    "professional_quality": "..."
  },
  "developmental_recommendations": ["..."],
  "business_readiness_notes": "...",
  "hr_recommendation": "..."
}
```

### AssessmentAgent

**File:** `backend/app/agents/assessment_agent.py`

Orchestrates the full assessment lifecycle:
1. Creates the submission record
2. Routes to `QuizEvaluatorAgent` or `AssignmentEvaluatorAgent` based on assessment type
3. Persists score and feedback
4. Calls `ProfileAgent` to check badge eligibility
5. Calls `AnalyticsAgent` to update running stats

### ProfileAgent

**File:** `backend/app/agents/profile_agent.py`

Manages fresher profiles and the badge system. After every evaluated assessment:
1. Recalculates the fresher's overall average score
2. Queries all badge definitions for thresholds the fresher now meets
3. Awards new badges and writes audit records to the database

### OnboardingAgent

**File:** `backend/app/agents/onboarding_agent.py`

Generates personalised onboarding plans when a new fresher is registered:
1. Reads the fresher's department
2. Selects appropriate curricula
3. Creates an initial weekly training schedule
4. Generates an LLM-written welcome summary stored on the fresher's profile

### AnalyticsAgent

**File:** `backend/app/agents/analytics_agent.py`

Aggregates performance data across all submissions:
- Recalculates running average score
- Updates quiz vs. assignment breakdown
- Writes to the `PerformanceAnalytics` table used by manager and admin dashboards

### ReportingAgent

**File:** `backend/app/agents/reporting_agent.py`

Generates structured report data consumed by two PDF generators:
- `pdf_generator.py` (fpdf2) — individual fresher progress reports via `/api/v1/reports`
- `pdf_generator_v2.py` (reportlab) — richer premium exports via the premium routes

---

## Ollama Integration

**File:** `backend/app/core/llm_client.py`

`LLMClient` wraps all Ollama HTTP calls. On startup it checks whether the Ollama server is reachable at `OLLAMA_BASE_URL`.

**Default models:**

| Purpose | Model |
|---|---|
| General evaluation and feedback | `neural-chat` |
| Code assessment | `mistral` |

**Switching models:**

Set the environment variable before running the startup script:

```bash
# Linux/Mac
OLLAMA_MODEL=llama3 ./start.sh

# Windows
$env:OLLAMA_MODEL = "llama3"; .\start.ps1
```

Or edit `backend/.env`:

```
OLLAMA_MODEL=neural-chat
OLLAMA_CODE_MODEL=mistral
```

**Mock fallback:**

When Ollama is offline or not installed, `LLMClient._mock_response()` is called instead. It inspects the prompt and returns a structurally valid JSON object matching whichever agent schema was requested. Every platform feature — quiz submission, assignment evaluation, badge award, report generation — works in mock mode. Scores use deterministic logic; feedback uses templated responses.

---

## API Reference

Interactive Swagger documentation is served at:

```
http://localhost:8000/docs
```

ReDoc is at:

```
http://localhost:8000/redoc
```

### Authentication

```
POST /api/v1/auth/login
POST /api/v1/auth/register
GET  /api/v1/auth/me
```

Login response includes:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": 1,
    "email": "alice@maverick.ai",
    "first_name": "Alice",
    "last_name": "Smith",
    "role": "fresher",
    "department": "Engineering",
    "is_active": true,
    "fresher_id": 1
  }
}
```

All protected endpoints require the header:

```
Authorization: Bearer <access_token>
```

Report PDF downloads additionally accept `?token=<jwt>` as a query parameter so browsers can trigger a direct download without a custom header.

### Fresher Routes

```
GET  /api/v1/freshers/me                         Current fresher profile
GET  /api/v1/freshers/user/{user_id}             Profile by user ID
GET  /api/v1/freshers                            All freshers (manager/admin)
GET  /api/v1/freshers/{fresher_id}               Fresher detail (manager/admin)
GET  /api/v1/freshers/{fresher_id}/dashboard     Dashboard data
GET  /api/v1/freshers/{fresher_id}/analytics     Performance analytics
```

### Assessment Routes

```
GET  /api/v1/assessments                         List all assessments
GET  /api/v1/assessments/{id}                    Assessment detail
POST /api/v1/assessments/{id}/start              Begin attempt
POST /api/v1/assessments/{id}/submit             Submit answers → triggers AI evaluation
GET  /api/v1/assessments/{id}/results            Latest evaluation results
GET  /api/v1/assessments/{id}/history            Submission history
```

### Schedule Routes

```
GET  /api/v1/schedules/today                     Today's schedule items
GET  /api/v1/schedules/week                      This week's schedule
POST /api/v1/schedules/{id}/start                Mark item as started
POST /api/v1/schedules/{id}/complete             Mark item as completed
```

### Analytics Routes

```
GET  /api/v1/analytics/manager/dashboard         Manager team summary
GET  /api/v1/analytics/manager/alerts            At-risk fresher alerts
GET  /api/v1/analytics/manager/cohort            Cohort comparison data
GET  /api/v1/analytics/admin/dashboard           Platform-wide stats
```

### Report Routes

```
GET  /api/v1/reports/{fresher_id}                Generate report (JSON)
GET  /api/v1/reports/{fresher_id}/download       Download PDF (auth via header or ?token=)
```

### Admin Routes

```
GET  /api/v1/admin/stats                         Platform statistics
POST /api/v1/admin/users                         Create user
PUT  /api/v1/admin/users/{id}                    Update user
POST /api/v1/admin/seed                          Re-seed demo data
```

### Premium Routes

```
GET  /api/v1/badges                              List available badges
GET  /api/v1/badges/fresher/{id}                 Fresher's earned badges
GET  /api/v1/analytics/premium/{fresher_id}      Premium analytics
GET  /api/v1/reports/pdf/{fresher_id}            Premium PDF export
GET  /api/v1/schedules/premium/{fresher_id}      Enhanced schedule view
```

### Health

```
GET  /health                                     Backend liveness check
GET  /api/v1/health/db                           Database connectivity check
```

---

## Project Structure

```
HEXAWARE-HACKATHON-/
│
├── start.ps1                      Windows PowerShell startup script
├── start.sh                       Linux / macOS / Git Bash startup script
├── docker-compose.yml             Docker Compose (optional alternative)
├── .gitignore
├── README.md
│
├── logs/                          Created at runtime by start scripts
│
├── backend/
│   ├── .env.example               Template for environment variables
│   ├── requirements.txt           Python dependencies
│   ├── Dockerfile
│   │
│   └── app/
│       ├── main.py                App factory, router registration, startup hook
│       ├── config.py              Settings loaded from .env via pydantic-settings
│       ├── database.py            SQLAlchemy engine, session factory, auto-migration
│       ├── seed.py                Initial data seeding (users, curricula, badges)
│       │
│       ├── agents/                AI agent layer
│       │   ├── base.py            BaseAgent with shared LLMClient access
│       │   ├── quiz_evaluator_agent.py
│       │   ├── assignment_evaluator_agent.py
│       │   ├── assessment_agent.py
│       │   ├── profile_agent.py
│       │   ├── onboarding_agent.py
│       │   ├── analytics_agent.py
│       │   └── reporting_agent.py
│       │
│       ├── api/
│       │   ├── deps.py            Shared dependencies: get_current_user, get_db
│       │   └── routes/
│       │       ├── auth.py        Login, register, /me
│       │       ├── freshers.py    Fresher profiles, dashboard
│       │       ├── assessments.py Quiz / assignment lifecycle
│       │       ├── schedules.py   Training schedule management
│       │       ├── analytics.py   Manager and admin analytics
│       │       ├── agents.py      Direct agent invocation endpoints
│       │       ├── workflows.py   Automated onboarding workflows
│       │       ├── reports.py     Report generation and PDF download
│       │       ├── curricula.py   Curriculum CRUD
│       │       ├── admin.py       Admin-only operations
│       │       ├── premium.py     Badge, premium analytics, premium PDF
│       │       ├── certifications.py  Certification records
│       │       └── quiz_config.py     Quiz evaluator configuration (admin)
│       │
│       ├── core/
│       │   ├── llm_client.py      Ollama HTTP wrapper + mock fallback
│       │   └── security.py        JWT encode/decode, password hashing
│       │
│       ├── models/                SQLAlchemy ORM models
│       │   ├── user.py            User (all roles)
│       │   ├── fresher.py         Fresher profile, skills, achievements
│       │   ├── assessment.py      Assessment, Submission
│       │   ├── curriculum.py      Curriculum, Module
│       │   ├── schedule.py        Schedule, ScheduleItem
│       │   ├── analytics.py       PerformanceAnalytics, Alert
│       │   ├── badge.py           Badge, FresherBadge
│       │   ├── certification.py   Certification, FresherCertification
│       │   ├── report.py          Report records
│       │   └── schedule_assessment.py  Assessment-to-schedule mapping
│       │
│       ├── schemas/               Pydantic request/response models
│       │   ├── auth.py
│       │   └── __init__.py
│       │
│       └── utils/
│           ├── pdf_generator.py       fpdf2 — standard progress reports
│           ├── pdf_generator_v2.py    reportlab — premium exports
│           └── feedback_generator.py  Deterministic fallback feedback
│
└── frontend/
    ├── package.json
    ├── next.config.js
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── Dockerfile
    │
    └── src/
        ├── app/
        │   ├── layout.tsx             Root layout, AuthProvider
        │   ├── globals.css
        │   ├── page.tsx               Landing → redirect to login
        │   ├── login/page.tsx         Login form
        │   ├── signup/page.tsx        Registration form
        │   └── dashboard/
        │       ├── fresher/
        │       │   ├── layout.tsx                  Sidebar + auth guard
        │       │   ├── page.tsx                    Overview / home
        │       │   ├── learning/[id]/page.tsx       Curriculum reader
        │       │   ├── schedule/page.tsx            Training calendar
        │       │   ├── profile/page.tsx             Badges and stats
        │       │   └── assessments/
        │       │       ├── page.tsx                Assessment list
        │       │       └── [id]/
        │       │           ├── quiz/page.tsx        MCQ quiz interface
        │       │           ├── assignment/page.tsx  Free-text submission
        │       │           ├── code/page.tsx        Code challenge
        │       │           └── results/page.tsx     AI evaluation results
        │       ├── manager/
        │       │   ├── layout.tsx                  Sidebar + auth guard
        │       │   ├── page.tsx                    Team dashboard
        │       │   └── fresher/[id]/page.tsx        Individual fresher detail
        │       └── admin/
        │           └── page.tsx                    Admin control panel
        │
        ├── components/ui/
        │   ├── badge.tsx
        │   ├── button.tsx
        │   ├── card.tsx
        │   └── progress.tsx
        │
        ├── hooks/
        │   └── useApi.ts              Generic data-fetching hook with auth header
        │
        └── lib/
            ├── api-service.ts         All backend API calls, typed responses
            └── auth-context.tsx       JWT auth state provider (decode + store)
```

---

## Environment Variables

### Backend — `backend/.env`

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./maverickai.db` | SQLAlchemy database URL |
| `SECRET_KEY` | *(change in production)* | JWT signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token lifetime (24 hours) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `neural-chat` | Primary LLM for evaluations |
| `OLLAMA_CODE_MODEL` | `mistral` | Model for code assessments |

### Frontend — `frontend/.env.local`

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | Backend API base URL |

---

## Application URLs

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Backend health | http://localhost:8000/health |
| DB health | http://localhost:8000/api/v1/health/db |
| Ollama | http://localhost:11434 |

---

## Known Limitations

- **CORS** is currently set to `allow_origins=["*"]` for local development. Restrict this to your frontend domain before deploying.
- **Secret key** defaults are placeholders. Generate a strong random secret for any non-local environment.
- **Profile page edits** (extended fields like bio and skills) are saved to local React state only and are not persisted to the backend — the backend API for these extended fields does not exist yet.
- **Manager action modals** (Warn / Appreciate / Fired) are UI-only and do not call any backend endpoint.
- **Skill stats** on the profile page display demo data from the seed, not computed from real assessment history.
- **Synchronous LLM calls** — evaluations run synchronously in the request. Under heavier concurrent load, consider moving to a background task queue (Celery, ARQ).
- The `(trapped) error reading bcrypt version` warning on backend startup is harmless — it is a known passlib cosmetic issue and does not affect password hashing.

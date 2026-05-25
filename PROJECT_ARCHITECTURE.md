# MaverickAI Project Architecture and Workflow Guide

This document explains the structure, runtime workflow, and architecture of the MaverickAI codebase for LLM-driven code understanding (e.g., Claude Code). It is based on the current repository contents and focuses on verified behavior.

## 1) High-Level Architecture

MaverickAI is a two-tier web application with an AI-assisted evaluation layer:

- Frontend: Next.js 14 (React 18) with the App Router, TypeScript, Tailwind CSS.
- Backend: FastAPI (Python) with SQLAlchemy ORM and Pydantic models.
- LLM Layer: Ollama HTTP API, with mock fallback when Ollama is unavailable.
- Data: SQLite by default for local runs; PostgreSQL via Docker Compose.

### Runtime Topology (Local)

- Browser -> Next.js dev server (port 3000)
- Next.js -> FastAPI API (port 8000)
- FastAPI -> SQLite file database (backend/maverickai.db)
- FastAPI -> Ollama HTTP API (optional, http://localhost:11434)

### Runtime Topology (Docker Compose)

- Next.js container -> FastAPI container
- FastAPI container -> PostgreSQL container
- FastAPI container -> Ollama container
- MongoDB container exists but is not used by verified backend flows

See [docker-compose.yml](docker-compose.yml) for wiring.

## 2) Repository Structure

Top-level layout:

- backend/  (FastAPI + SQLAlchemy + LLM agents)
- frontend/ (Next.js App Router UI)
- docker-compose.yml (multi-service local stack)
- PROJECT_ENGINEERING_AND_DEPLOYMENT_GUIDE.md (project overview)

Backend layout highlights:

- backend/app/main.py  -> FastAPI app creation and router registration
- backend/app/config.py -> Settings (DB URL, JWT, Ollama, CORS)
- backend/app/database.py -> SQLAlchemy engine/session + create_tables
- backend/app/models/ -> SQLAlchemy models for users, assessments, schedules, etc.
- backend/app/api/routes/ -> FastAPI routers (auth, assessments, workflows, reports, etc.)
- backend/app/agents/ -> LLM-backed or rules-based business logic
- backend/app/utils/ -> PDF generation and other helpers
- backend/app/seed.py -> Demo data seeding on startup

Frontend layout highlights:

- frontend/src/app/ -> Next.js App Router pages and layouts
- frontend/src/lib/api-service.ts -> API wrapper and endpoint map
- frontend/src/lib/auth-context.tsx -> Auth context and token persistence
- frontend/src/components/ -> UI primitives

## 3) Backend Architecture

### 3.1 FastAPI App and Routing

Entry point: backend/app/main.py

- Creates FastAPI app with CORS enabled.
- Health endpoints:
  - GET /health
  - GET /api/v1/health/db
- Root redirects to /docs (Swagger UI).
- Registers routers under /api/v1/*, including:
  - auth, freshers, schedules, assessments, analytics, agents, workflows,
    reports, curricula, admin, premium, certifications, quiz-config

### 3.2 Configuration

Source: backend/app/config.py

Key settings:

- DATABASE_URL (default: sqlite:///./maverickai.db)
- JWT secret and token lifetime
- OLLAMA_BASE_URL and model names
- CORS origins

### 3.3 Database Layer

Source: backend/app/database.py

- SQLAlchemy engine + SessionLocal.
- SQLite uses check_same_thread=False for FastAPI.
- create_tables() imports models and runs Base.metadata.create_all().
- get_db() yields DB sessions for request handlers.

### 3.4 Models

Core models are in backend/app/models/. Examples:

- User: role, department, auth fields.
- Assessment: quiz/assignment/code metadata, JSON fields for questions/rubric.
- Submission: user submissions, grading results, feedback JSON.

Relationships are simple; explicit foreign keys exist in relevant tables
(e.g., Submission -> User and Assessment).

### 3.5 Authentication and Authorization

- JWT-based auth in backend/app/api/routes/auth.py
- /auth/login, /auth/register, /auth/me, /auth/refresh
- Authorization uses HTTP Bearer tokens (backend/app/api/deps.py).
- `require_role()` helpers enforce role-based access where needed.

### 3.6 Workflows and Evaluations

Source: backend/app/api/routes/workflows.py

Key flow: POST /api/v1/workflows/submit

1) Request contains assessment_id, submission_type, answers/code.
2) Submission created with status=grading.
3) Grading happens synchronously:
   - quiz -> QuizEvaluatorAgent
   - assignment -> AssignmentEvaluatorAgent
   - fallback -> AssessmentAgent
4) Results are stored in the Submission (score, feedback, status).
5) Optional fresher profile updates via ProfileAgent.

Workflow status endpoint:

- GET /api/v1/workflows/status/{trace_id}
- Returns normalized feedback and safe JSON for UI rendering.

### 3.7 LLM Integration (Ollama)

Source: backend/app/core/llm_client.py

- OllamaClient calls /api/generate on Ollama.
- If Ollama is unavailable, it falls back to mock JSON payloads.
- Agents call Ollama via BaseAgent.call_llm().

### 3.8 Reporting

Source: backend/app/api/routes/reports.py

- POST /api/v1/reports/generate/{report_type}
- ReportingAgent generates report content and stores it.
- /reports/{id}/download supports PDF or JSON downloads.

### 3.9 Seeding and Demo Data

Source: backend/app/seed.py

- On startup, seed_database() populates demo users, freshers, schedules,
  assessments, and other data if the DB is empty.

## 4) Frontend Architecture

### 4.1 Next.js App Router

Entry: frontend/src/app/layout.tsx

- Root layout applies global styles and wraps the app in AuthProvider.

Landing page: frontend/src/app/page.tsx

- Public marketing-style landing.

### 4.2 Auth Context

Source: frontend/src/lib/auth-context.tsx

- Stores token in localStorage (maverick_token + legacy key).
- Fetches /auth/me for current user during app init.
- Exposes login/register/logout methods for UI.

### 4.3 API Wrapper

Source: frontend/src/lib/api-service.ts

- Base URL from NEXT_PUBLIC_API_URL (default http://localhost:8000/api/v1).
- Centralized API calls for assessments, workflows, admin, reports, etc.
- All calls return { success, data, error } wrapper.

### 4.4 Pages and Roles

The frontend uses role-based screens for:

- Fresher: dashboard, schedules, assessments, profile
- Manager: analytics and cohort overview
- Admin: stats and user management

Pages are in frontend/src/app/dashboard/... with nested layouts.

## 5) Key End-to-End Flows

### 5.1 Login and Session

1) UI submits email/password to /auth/login.
2) Backend returns access_token and user info.
3) Token is stored in localStorage.
4) AuthProvider sets user context for UI.

### 5.2 Assessment List and Detail

1) UI calls GET /assessments.
2) Backend returns { items: [...], total, page }.
3) UI renders list and links to details.

### 5.3 Assessment Submission and Grading

1) User submits quiz/assignment data to /workflows/submit.
2) Submission is created, evaluated, and updated.
3) UI polls /workflows/status/{trace_id} to retrieve feedback.

### 5.4 Report Generation and Download

1) UI calls /reports/generate/{type}.
2) Backend stores report content.
3) UI calls /reports/{id}/download?token=... to fetch a PDF or JSON report.

## 6) Environment Variables

Backend (defaults in backend/app/config.py):

- DATABASE_URL
- SECRET_KEY
- OLLAMA_BASE_URL
- OLLAMA_MODEL / OLLAMA_CODE_MODEL / OLLAMA_FAST_MODEL

Frontend:

- NEXT_PUBLIC_API_URL

## 7) Local Run (Without Docker)

Backend:

- cd backend
- .\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload

Frontend:

- cd frontend
- npm run dev

## 8) Notes and Known Behaviors

- Some analytics and agent outputs are demo or mock-like.
- Ollama is optional; mock responses are used when it is unavailable.
- MongoDB is provisioned in docker-compose.yml but not actively used
  by verified backend code paths.

## 9) Files to Read First (Claude Code)

If a model needs a quick map, start with:

- backend/app/main.py
- backend/app/config.py
- backend/app/database.py
- backend/app/api/routes/workflows.py
- backend/app/api/routes/assessments.py
- backend/app/api/routes/auth.py
- backend/app/core/llm_client.py
- backend/app/agents/
- frontend/src/lib/api-service.ts
- frontend/src/lib/auth-context.tsx
- frontend/src/app/layout.tsx
- docker-compose.yml

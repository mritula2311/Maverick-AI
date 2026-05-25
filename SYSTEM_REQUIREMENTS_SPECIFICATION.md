# System Requirements Specification: MaverickAI

## Front Matter

| Field | Value |
|---|---|
| Project Name | MaverickAI |
| Repository | HEXAWARE-HACKATHON- |
| Document Type | System Requirements Specification (SRS) |
| Version | 1.0 |
| Revision Date | 2026-05-03 |
| Prepared For | Hexaware Hackathon project stakeholders |
| Prepared By | Project engineering documentation team |
| System Status Reflected | Current repository implementation and QA evidence as of 2026-05-03 |

### Template Instructions

This document is intended to be used as the baseline system requirements document for MaverickAI, a role-based onboarding and training management platform for enterprise freshers.

Use this document as follows:

- Treat statements marked as implemented or verified as requirements supported by the current repository, README, engineering guide, route structure, dependency files, Docker Compose file, and QA report.
- Treat statements marked as production requirement, future requirement, or acceptance caveat as requirements that are needed for a production-grade deployment but are not fully complete in the current repository.
- Update the revision history whenever a requirement, acceptance condition, architecture decision, dependency, interface, security rule, or known limitation changes.
- Obtain stakeholder approval before using this document as a delivery baseline.
- Do not use demo credentials, demo seed data, permissive CORS, or default secrets in a real production environment.

### Template Revision History

| Template Version | Date | Author/Owner | Description |
|---|---|---|---|
| 1.0 | 2026-05-03 | Project documentation team | Initial project-specific SRS created from repository documentation, source structure, configuration, and QA report. |

### Approval Section

| Stakeholder Role | Name | Signature | Date | Approval Status |
|---|---|---|---|---|
| Product Owner / Business Sponsor | TBD | TBD | TBD | Pending |
| Training / Onboarding Representative | TBD | TBD | TBD | Pending |
| Engineering Lead | TBD | TBD | TBD | Pending |
| QA Lead | TBD | TBD | TBD | Pending |
| Security Reviewer | TBD | TBD | TBD | Pending |
| Deployment / Operations Owner | TBD | TBD | TBD | Pending |

## 1. Purpose

### 1.1 Objective

The objective of this System Requirements Specification is to define the required capabilities, constraints, interfaces, security expectations, training needs, capacity assumptions, architecture baseline, acceptance criteria, current-state analysis, and supporting references for MaverickAI.

MaverickAI is implemented as a web-based platform for enterprise fresher onboarding and training management. It supports role-specific workflows for freshers, managers, and administrators, including dashboards, learning schedules, assessments, analytics, reports, certifications, badges, and AI-assisted assessment or feedback functions.

### 1.2 Scope of System Development

The current system scope includes:

- A Next.js frontend for fresher, manager, and admin users.
- A FastAPI backend exposing REST-style APIs under `/api/v1`.
- JWT-based authentication and role-aware access checks.
- Relational persistence through SQLAlchemy, using SQLite by default locally and PostgreSQL through Docker Compose.
- Seeded demo data for repeatable hackathon or MVP demonstration.
- Fresher progress, skills, achievements, training status, schedules, assessments, and dashboard data.
- Manager analytics, alerts, cohort views, department views, report generation, and AI assessment generation.
- Admin user creation, system statistics, fresher detail retrieval, warnings, overall reporting, and seed-data reset.
- Certifications, assignment history, badges, assessment schedules, and premium analytics routes.
- PDF report generation and downloadable report endpoints.
- Ollama-backed AI features with mock fallback behavior when the model service is unavailable.
- Basic health and database health endpoints.

The current system scope does not fully include:

- Verified enterprise SSO integration.
- Production-grade audit logging.
- Confirmed active MongoDB persistence in backend application flows.
- Message queue or asynchronous job processing for grading/reporting.
- Verified CI/CD pipelines.
- Production-level security hardening, rate limiting, monitoring, backup, and disaster recovery.

## 2. General System Requirements

### 2.1 Major System Capabilities

The system shall provide the following major capabilities:

| ID | Capability | Requirement |
|---|---|---|
| MSC-01 | Authentication | The system shall allow users to register, log in, refresh tokens, and retrieve current-user information using JWT-based authentication. |
| MSC-02 | Role-Based Experience | The system shall support fresher, manager, and admin roles with role-aware dashboards and protected backend routes where required. |
| MSC-03 | Fresher Dashboard | The system shall display fresher progress, current training week, skills, achievements, schedules, assessment history, badges, and training status. |
| MSC-04 | Schedule Management | The system shall allow retrieval of daily, weekly, and date-specific fresher schedules and allow schedule items to be started or completed. |
| MSC-05 | Assessment Management | The system shall list assessments, start assessments, accept submissions or answers, return latest results, and support quiz, assignment, and code-style assessment flows. |
| MSC-06 | Workflow Submission | The system shall process assessment submissions and expose status by workflow trace ID. Current QA evidence shows this flow requires defect resolution before final acceptance. |
| MSC-07 | AI Assessment Generation | The system shall generate quiz, assignment, or code-style assessment content through an Ollama-backed AI client, with fallback behavior when Ollama is unavailable. |
| MSC-08 | Manager Analytics | The system shall provide manager-facing dashboard summaries, alerts, cohort analytics, trends, department views, and recent activity summaries. |
| MSC-09 | Reporting | The system shall generate individual, department, cohort, and general reports and support PDF download where implemented. |
| MSC-10 | Admin Operations | The system shall provide admin operations for user creation, user listing, mentor assignment, statistics, fresher details, warnings, seed-data actions, and overall reporting. |
| MSC-11 | Certifications | The system shall allow certification retrieval, creation, update, deletion, and assignment-history tracking for freshers and submissions. |
| MSC-12 | Badges and Premium Analytics | The system shall expose badge listing, fresher badge assignment, assessment scheduling, performance analytics, cohort comparison, AI feedback, and AI insights routes. |
| MSC-13 | System Health | The system shall provide service health and database health endpoints for local and containerized operation checks. |

### 2.2 Major System Conditions

#### Constraints

- The backend is a modular monolith implemented in Python using FastAPI.
- The frontend is implemented with Next.js 14, React 18, TypeScript, and Tailwind CSS.
- The default local database is SQLite at `backend/maverickai.db`.
- Docker Compose uses PostgreSQL 15 as the relational database.
- Docker Compose provisions MongoDB 7, but active application persistence through MongoDB was not verified in current backend route logic.
- Docker Compose provisions Ollama for AI features.
- The backend currently allows all CORS origins in `app.main`, which is acceptable for local/demo use but not for production.
- The default `SECRET_KEY` and demo credentials are not acceptable for production.
- Some dashboard and analytics values are still demo/static in the current implementation.
- Some frontend widgets appear to be locally editable without full backend persistence.
- Synchronous grading may limit throughput under heavier concurrent usage.

#### Assumptions

- Users will access the application through a modern web browser.
- The frontend will call the backend through `NEXT_PUBLIC_API_URL`, defaulting to `http://localhost:8000/api/v1`.
- A production deployment will replace demo secrets, demo credentials, and permissive CORS values.
- A production deployment will intentionally choose PostgreSQL or another managed relational database instead of local SQLite.
- AI-dependent features may return fallback/mock-style outputs when Ollama is unavailable.
- Stakeholders accept the current system as an MVP/hackathon baseline unless the listed acceptance caveats are resolved.

### 2.3 System Interfaces

#### User Interfaces

- Landing page.
- Login page.
- Signup page.
- Fresher dashboard.
- Fresher profile page.
- Fresher schedule page.
- Fresher learning page.
- Fresher assessment pages for quiz, code, assignment, and results.
- Manager dashboard.
- Manager fresher-detail view.
- Admin dashboard.

#### Backend API Interfaces

The backend exposes the following route groups:

- `/api/v1/auth`
- `/api/v1/freshers`
- `/api/v1/schedules`
- `/api/v1/assessments`
- `/api/v1/analytics`
- `/api/v1/agents`
- `/api/v1/workflows`
- `/api/v1/reports`
- `/api/v1/curricula`
- `/api/v1/admin`
- `/api/v1/certifications`
- `/api/v1/quiz-evaluator`
- Premium routes mounted under `/api/v1`

Health interfaces:

- `GET /`
- `GET /health`
- `GET /api/v1/health/db`
- Swagger documentation at `/docs`

#### Data Interfaces

- SQLAlchemy ORM models define the relational persistence layer.
- SQLite is used by default for local development.
- PostgreSQL is configured through Docker Compose using `DATABASE_URL`.
- MongoDB is provisioned for possible agent memory/log use but was not verified as active persistence in the inspected backend code.

#### External Service Interfaces

- Ollama API through `OLLAMA_BASE_URL`, defaulting locally to `http://localhost:11434`.
- Ollama model settings through `OLLAMA_MODEL`, `OLLAMA_CODE_MODEL`, and `OLLAMA_FAST_MODEL`.
- A configured `N8N_WEBHOOK_URL` exists in backend settings, but active workflow usage was not verified in the current implementation.

### 2.4 System User Characteristics

| User Type | Characteristics | Primary Needs |
|---|---|---|
| Fresher | New employee or trainee participating in onboarding. May have limited technical or organizational knowledge. | View schedules, complete learning tasks, take assessments, track progress, view feedback, certifications, and badges. |
| Manager | Training manager, team lead, or onboarding owner responsible for monitoring multiple freshers. | Track cohorts, identify risks, generate reports, view alerts, inspect fresher progress, and create assessments. |
| Admin | System administrator or operations owner. | Create users, inspect system stats, reseed demo data, view warnings, manage platform-level data. |
| HR / Reporting Stakeholder | Consumer of onboarding status and report outputs. May not operate daily workflows directly. | Reliable reports, progress summaries, risk visibility, and completion evidence. |
| Engineering / Operations Team | Maintains, deploys, and troubleshoots the platform. | Clear configuration, health checks, logs, database setup, dependency management, and deployment repeatability. |

## 3. Policy and Regulation Requirements

### 3.1 Policy Requirements

The following policy requirements should govern use of MaverickAI:

- The system shall enforce role-based access for fresher, manager, and admin operations.
- The system shall require authenticated access for protected dashboard, assessment, reporting, certification, analytics, and admin functions.
- Demo credentials shall be used only for local demonstration and testing.
- Production deployments shall require unique user accounts, non-default passwords, and non-default JWT secrets.
- Training records, assessment submissions, scores, certifications, and generated reports shall be treated as confidential internal business data.
- AI-generated assessment content and feedback shall be reviewed under organizational quality and fairness expectations before high-stakes use.
- Seed-data reset functionality shall be restricted to authorized admin users and disabled or heavily controlled in production.
- Report downloads shall be available only to authorized users whose role requires access to that report scope.

### 3.2 Regulation Requirements

No project-specific legal compliance target is explicitly implemented in the repository. For production usage, the following regulatory and governance requirements should be evaluated based on deployment region and enterprise policy:

- Data privacy requirements for employee or trainee records, such as applicable local privacy laws and organizational HR data policies.
- Access logging and retention requirements for training and assessment records.
- Secure password handling and credential lifecycle policies.
- Records retention requirements for reports, certifications, and assessment submissions.
- AI governance requirements for generated evaluations, scoring assistance, and feedback.
- Accessibility expectations for web applications used in enterprise training environments.

Production acceptance shall require a security and compliance review before handling real employee data.

## 4. Security Requirements

| ID | Security Requirement | Current Status |
|---|---|---|
| SEC-01 | The system shall authenticate users using email/password login and JWT access tokens. | Implemented. |
| SEC-02 | Passwords shall be hashed before storage. | Implemented using passlib/bcrypt. |
| SEC-03 | JWT tokens shall include expiration. | Implemented with a default 24-hour access token expiry. |
| SEC-04 | The backend shall validate bearer tokens for protected operations. | Implemented through FastAPI HTTPBearer dependencies. |
| SEC-05 | The backend shall enforce role authorization for admin, manager, and fresher-only routes. | Partially implemented; production review required for all route groups. |
| SEC-06 | CORS shall be restricted to approved frontend origins in production. | Not production-ready; current backend permits all origins. |
| SEC-07 | Default `SECRET_KEY` values shall be replaced in deployed environments. | Required for production. |
| SEC-08 | Demo accounts shall be removed, disabled, or password-rotated before production use. | Required for production. |
| SEC-09 | Sensitive configuration shall be provided through environment variables and not committed as live secrets. | Partially supported through `.env` and Docker Compose variables. |
| SEC-10 | APIs shall avoid exposing stack traces, internal debug logs, or sensitive token details in production logs. | Production hardening required; current code includes verbose auth/JWT logging. |
| SEC-11 | Report and PDF endpoints shall verify user authorization before returning content. | Required for production verification. |
| SEC-12 | Admin seed-data and user-management endpoints shall be admin-only. | Implemented or intended by route design; full route audit recommended. |
| SEC-13 | AI-generated outputs shall be handled as untrusted content and sanitized before frontend rendering. | Some sanitization patterns are present; full review required. |

## 5. Training Requirements

### 5.1 Fresher Training

Freshers shall receive basic training on:

- Logging in and navigating the fresher dashboard.
- Reading daily and weekly schedules.
- Starting and completing schedule items.
- Taking quiz, assignment, and code-style assessments.
- Viewing assessment results, feedback, badges, certifications, and progress.
- Reporting incorrect profile, schedule, or assessment information.

### 5.2 Manager Training

Managers shall receive training on:

- Using the manager dashboard and analytics panels.
- Interpreting risk alerts, cohort data, department summaries, and trend views.
- Generating individual, department, and cohort reports.
- Downloading and sharing reports according to internal policy.
- Reviewing AI-generated assessments before assigning or relying on them.
- Understanding which values are live, computed, seeded, or demo-oriented in the MVP.

### 5.3 Admin Training

Admins shall receive training on:

- Creating users and assigning roles.
- Reviewing system statistics and warnings.
- Running or avoiding seed-data operations.
- Understanding database startup and automatic seed behavior.
- Managing environment variables, deployment settings, and secrets.
- Verifying backend health, database health, and Docker Compose service readiness.

### 5.4 Operations and Engineering Training

Engineering and operations users shall receive training on:

- Local setup with Python, Node.js, npm, and Docker.
- Backend dependency installation through `backend/requirements.txt`.
- Frontend dependency installation through `frontend/package-lock.json` and `npm ci`.
- Running `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`.
- Running `npm run dev`, `npm run build`, and `npm run lint`.
- Running `docker compose up --build`.
- Inspecting health endpoints and QA output.
- Replacing demo configuration before production deployment.

## 6. Initial Capacity Requirements

The repository does not define formal production load targets. The following initial capacity requirements are therefore stated as MVP baseline requirements and production planning assumptions.

### 6.1 Expected Users

| Environment | Expected Usage |
|---|---|
| Local development | 1 developer or tester using frontend and backend locally. |
| Hackathon/demo | Small demo group, typically fewer than 20 simultaneous users. |
| MVP pilot | One or more onboarding cohorts with tens to low hundreds of users, subject to performance testing. |
| Production | Requires separate load testing, infrastructure sizing, database tuning, monitoring, and async processing review. |

### 6.2 Transactions and Workloads

The system shall support the following transaction types:

- User login, registration, token refresh, and current-user lookup.
- Dashboard data retrieval.
- Schedule retrieval and item status updates.
- Assessment start, answer submission, grading, and result retrieval.
- Workflow submission and status polling.
- Analytics dashboard, alert, trend, department, and cohort retrieval.
- Report generation and PDF download.
- Certification and badge operations.
- Admin user creation and system statistics retrieval.

### 6.3 Storage

The system shall store:

- Users and roles.
- Fresher profiles and onboarding progress.
- Skills and achievements.
- Schedules and schedule items.
- Assessments and submissions.
- Curricula.
- Reports and alerts.
- Badges and fresher badge assignments.
- Certifications and assignment history.
- Performance analytics.

SQLite is acceptable for local development. PostgreSQL or another managed relational database is required for production-like use.

### 6.4 Performance

Initial performance requirements:

- Health endpoints should respond quickly under normal local or containerized conditions.
- Dashboard and list endpoints should return within acceptable web interaction latency for MVP demonstration.
- Report generation should complete without blocking other critical user interactions in pilot use.
- Assessment grading currently occurs synchronously in relevant workflows and may become a bottleneck; production use should move grading and heavy AI calls to background processing or job queues.
- AI response times depend on Ollama availability, model size, host resources, and fallback behavior.

## 7. Initial System Architecture

### 7.1 Architecture Overview

MaverickAI is currently a layered modular monolith:

- Browser-based frontend built with Next.js.
- REST-style backend built with FastAPI.
- Relational data layer through SQLAlchemy.
- Optional containerized infrastructure through Docker Compose.
- AI integration through an Ollama client with fallback behavior.
- PDF/report utilities for downloadable outputs.

### 7.2 Hardware Requirements

#### Local Development

- Developer workstation capable of running Python 3.11+, Node.js 18+, npm, and a browser.
- Recommended: 8 GB RAM minimum; 16 GB RAM preferred for running frontend, backend, database, and Docker services together.
- Disk space for `node_modules`, Python virtual environment, Docker images, database files, and generated reports.

#### Docker Compose / AI-Enabled Demo

- Docker-compatible host.
- Additional memory for PostgreSQL, MongoDB, Ollama, backend, and frontend containers.
- GPU-capable host is beneficial for Ollama because the Compose file reserves GPU device capability, but CPU-only behavior depends on the host and Ollama image support.

#### Production

- Production sizing shall be determined through load testing.
- Dedicated managed database storage, backup, monitoring, and network security are required before handling real employee data.

### 7.3 Software Requirements

#### Backend

- Python 3.11+.
- FastAPI 0.104.1.
- Uvicorn 0.24.0.
- SQLAlchemy 2.0.23.
- Pydantic 2.5.2.
- Pydantic Settings 2.1.0.
- python-jose 3.3.0.
- passlib 1.7.4.
- bcrypt 4.1.2.
- psycopg2-binary 2.9.9.
- requests 2.31.0.
- aiofiles 23.2.1.
- Jinja2 3.1.2.
- fpdf2 2.7.6.
- ReportLab 4.0.7.

#### Frontend

- Node.js 18+.
- npm.
- Next.js 14.0.4.
- React 18.
- TypeScript 5.
- Tailwind CSS 3.3.
- Recharts 2.10.4.
- Lucide React 0.309.0.
- Radix UI packages used by UI components.
- Monaco Editor React package for code assessment experience.

#### Infrastructure

- Docker and Docker Compose for containerized setup.
- PostgreSQL 15 container.
- MongoDB 7 container.
- Ollama container.

### 7.4 Programming Languages and Tools

- Python for backend APIs, agents, data access, grading workflows, reporting, and utilities.
- TypeScript for frontend pages, UI components, hooks, and API interactions.
- SQLAlchemy ORM for relational database modeling.
- Tailwind CSS for frontend styling.
- Dockerfiles for backend and frontend containers.
- Docker Compose for multi-service local/container setup.
- Swagger/OpenAPI documentation generated by FastAPI.

### 7.5 Network and Operating System Requirements

Default local ports:

- Frontend: `3000`
- Backend: `8000`
- PostgreSQL: `5432`
- MongoDB: `27017`
- Ollama: `11434`

Supported operating systems:

- Windows development is supported by the current repository usage and PowerShell commands.
- Linux-based containers are used for Docker services.
- macOS/Linux local development should be possible if Python, Node.js, npm, and Docker prerequisites are met, but should be verified separately.

## 8. System Acceptance Criteria

The system shall be accepted when the following conditions are met:

| ID | Acceptance Criterion |
|---|---|
| AC-01 | Backend starts successfully and exposes `/health`, `/api/v1/health/db`, and `/docs`. |
| AC-02 | Frontend starts successfully and reaches the configured backend API. |
| AC-03 | Seeded demo users or created users can log in according to assigned roles. |
| AC-04 | Fresher dashboard loads profile, progress, schedule, assessment, badge, and training status data. |
| AC-05 | Manager dashboard loads analytics, alerts, cohorts, departments, reports, and relevant fresher details. |
| AC-06 | Admin dashboard supports stats, user creation, fresher details, warnings, and seed-data operation according to role permissions. |
| AC-07 | Schedules can be retrieved and schedule items can be started and completed. |
| AC-08 | Assessments can be listed, started, submitted, and results can be retrieved. |
| AC-09 | Workflow submission and workflow status shall return successful graded states for valid submissions. Current QA on 2026-05-03 shows failures that must be resolved before full acceptance. |
| AC-10 | Reports can be generated and downloaded in supported formats, including PDF where implemented. |
| AC-11 | Certification and badge operations work for valid users and authorized roles. |
| AC-12 | AI-dependent flows behave predictably when Ollama is available and degrade clearly through fallback behavior when unavailable. |
| AC-13 | Frontend TypeScript compilation succeeds. Current QA on 2026-05-03 reported a TypeScript compile failure in `tsconfig.json` for `ignoreDeprecations`. |
| AC-14 | Security review confirms secrets, CORS, demo accounts, logging, role enforcement, and report access are acceptable for the target environment. |
| AC-15 | Stakeholders approve that remaining demo/static values are acceptable for demo use or are replaced before production use. |

### QA Baseline

The QA report dated 2026-05-03 recorded:

- Total test cases: 50.
- Passed: 47.
- Failed: 3.
- Pass rate: 94.00%.

Failed high-severity cases:

- `ASM-04`: Workflow submission grades quiz answers synchronously.
- `ASM-05`: Workflow status returns graded state.
- `FE-02`: Frontend TypeScript compile check succeeds.

These failures are acceptance blockers for a production or final delivery baseline unless formally waived by stakeholders.

## 9. Current System Analysis

### 9.1 Existing System Overview

The current system is a working MVP/hackathon-grade web application named MaverickAI. It combines role-based onboarding dashboards, schedule tracking, assessments, analytics, reporting, certifications, badges, and AI-assisted evaluator/generator functionality.

The project is organized as:

- `backend/app/api/routes`: FastAPI route modules.
- `backend/app/agents`: agent-style modules for onboarding, assessment, analytics, profile, reporting, quiz evaluation, and assignment evaluation.
- `backend/app/models`: SQLAlchemy data models.
- `backend/app/schemas`: Pydantic schemas.
- `backend/app/utils`: PDF and feedback utilities.
- `frontend/src/app`: Next.js pages and route segments.
- `frontend/src/components`: reusable UI components.
- `frontend/src/hooks`: frontend API hooks.
- `docker-compose.yml`: PostgreSQL, MongoDB, Ollama, FastAPI backend, and Next.js frontend services.

### 9.2 Current Data Flow

Typical login flow:

1. User enters email and password in frontend.
2. Frontend sends credentials to `/api/v1/auth/login`.
3. Backend verifies password hash using passlib/bcrypt.
4. Backend returns JWT token and user information.
5. Frontend stores/uses token for subsequent API calls.
6. Protected backend routes validate the bearer token and identify the current user.

Typical fresher dashboard flow:

1. Fresher logs in.
2. Frontend requests profile, dashboard, schedule, assessment, badge, and certification data.
3. Backend queries SQLAlchemy models and returns JSON responses.
4. Frontend renders progress, tasks, schedules, results, and achievements.

Typical assessment flow:

1. Fresher starts an assessment through the assessment API.
2. Backend creates or retrieves a submission.
3. Fresher submits answers or assignment/code content.
4. Backend processes grading through assessment/workflow routes and evaluator agents.
5. Result, score, feedback, and status are returned or retrievable.
6. Current QA shows synchronous workflow grading/status failures requiring correction.

Typical manager reporting flow:

1. Manager logs in.
2. Frontend requests analytics, alerts, cohort, department, and report data.
3. Backend produces summaries from database and demo/static sources where still present.
4. Manager generates reports.
5. Backend returns report records and downloadable output such as PDF.

### 9.3 Current Interfaces

Current verified interfaces include:

- Browser UI to Next.js application.
- Next.js frontend to FastAPI backend through REST APIs.
- FastAPI backend to relational database through SQLAlchemy.
- FastAPI backend to Ollama through configured HTTP base URL.
- Report endpoints to PDF generation utilities.
- Docker Compose service networking among frontend, backend, PostgreSQL, MongoDB, and Ollama.

### 9.4 Current Limitations

Known limitations include:

- Some analytics, trends, timestamps, workflow activity, and metrics are demo/static in backend responses.
- Some frontend editable widgets are not fully persisted to the backend.
- Workflow grading/status has high-severity QA failures as of 2026-05-03.
- Frontend TypeScript compile check has a high-severity QA failure as of 2026-05-03.
- MongoDB is provisioned but active backend persistence usage was not verified.
- CORS is currently permissive.
- Default secrets and demo credentials are present for local/demo use.
- Auth/JWT debug logging is verbose and should be reduced for production.
- Synchronous grading and AI calls may block request/response cycles.
- Production monitoring, audit logging, backup, and CI/CD are not verified in the current repository.

### 9.5 Migration and Conversion Requirements

For moving from demo/local use to production-like use:

- Migrate from SQLite to PostgreSQL or another managed relational database.
- Replace seeded demo accounts with real identity-managed users.
- Disable or restrict seed-data reset operations.
- Replace default `SECRET_KEY`, database password, and AI endpoint configuration.
- Restrict CORS origins to approved frontend domains.
- Confirm all role-based access rules for every route group.
- Move synchronous grading and heavy AI processing to background jobs if load testing shows bottlenecks.
- Convert demo/static metrics to computed, persisted, or clearly labeled values.
- Add database migration tooling such as Alembic if schema evolution becomes part of ongoing delivery.
- Establish backup, restore, log retention, and data archival procedures.

## 10. References

The following project artifacts were used to prepare this SRS:

- `README.md`
- `PROJECT_ENGINEERING_AND_DEPLOYMENT_GUIDE.md`
- `QA_TEST_REPORT.txt`
- `docker-compose.yml`
- `backend/requirements.txt`
- `frontend/package.json`
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/api/deps.py`
- `backend/app/core/security.py`
- `backend/app/api/routes/*`
- `backend/app/models/*`
- `frontend/src/app/*`
- `frontend/src/components/*`

External standards and practices referenced conceptually:

- ISO/IEC/IEEE 29148-style requirements documentation practices.
- OWASP-style web security review expectations for authentication, authorization, CORS, secrets, and input/output handling.

## 11. Glossary

| Term | Definition |
|---|---|
| Admin | User role responsible for system-level management, user creation, statistics, warnings, seed data, and overall reporting. |
| AI | Artificial Intelligence; in this project, mainly Ollama-backed generation, grading, feedback, and insight support. |
| API | Application Programming Interface exposed by the FastAPI backend. |
| Assessment | Quiz, assignment, or code-style evaluation assigned to a fresher. |
| Badge | Recognition artifact assigned to a fresher through premium/badge routes. |
| CORS | Cross-Origin Resource Sharing, browser security policy controlling frontend-backend cross-origin calls. |
| Docker Compose | Tool used to run PostgreSQL, MongoDB, Ollama, backend, and frontend services together. |
| FastAPI | Python web framework used by the backend. |
| Fresher | New employee or trainee user participating in onboarding. |
| JWT | JSON Web Token used for authenticated API access. |
| Manager | User role responsible for monitoring fresher cohorts, analytics, alerts, and reports. |
| MongoDB | NoSQL database provisioned by Docker Compose; active backend persistence usage was not verified. |
| MVP | Minimum Viable Product. |
| Ollama | Local/containerized LLM service used for AI-assisted features. |
| PostgreSQL | Relational database used in Docker Compose. |
| SRS | System Requirements Specification. |
| SQLite | Local file-based relational database used by default. |
| SQLAlchemy | Python ORM used for database modeling and queries. |
| Workflow | Backend submission and grading flow that tracks assessment processing state by trace ID. |

## 12. Document Revision History

| Version | Date | Author/Owner | Change Description |
|---|---|---|---|
| 1.0 | 2026-05-03 | Project documentation team | Initial SRS for MaverickAI based on current repository implementation and QA report. |

## 13. Appendices

### Appendix A: Demo Credentials

The current seed logic creates the following demo users when the database is empty:

| Email | Password | Role |
|---|---|---|
| `alice@maverick.ai` | `password123` | fresher |
| `john@maverick.ai` | `password123` | fresher |
| `bob@maverick.ai` | `password123` | fresher |
| `emily@maverick.ai` | `password123` | fresher |
| `manager@maverick.ai` | `password123` | manager |
| `admin@maverick.ai` | `admin123` | admin |

These credentials are for demo use only and shall not be used in production.

### Appendix B: Main Backend Route Groups

| Route Group | Purpose |
|---|---|
| `/api/v1/auth` | Login, registration, token refresh, current-user lookup. |
| `/api/v1/freshers` | Fresher profile, dashboard, skills, training status, workflow status, evaluations, updates. |
| `/api/v1/schedules` | Schedule retrieval, item details, start/complete actions, schedule generation. |
| `/api/v1/assessments` | AI generation, assessment listing, pending/completed views, start, submit answers, results. |
| `/api/v1/analytics` | Manager dashboard, alerts, acknowledgment, cohorts, trends, departments. |
| `/api/v1/agents` | Agent operations for schedule generation, grading, risk prediction, profile update, metrics, status. |
| `/api/v1/workflows` | Assessment workflow submission, workflow status, fresher dashboard, manager dashboard. |
| `/api/v1/reports` | Report generation, individual/department/cohort reports, report listing, download. |
| `/api/v1/curricula` | Curriculum listing and fresher curriculum retrieval. |
| `/api/v1/admin` | Users, mentor assignment, stats, fresher details, seed data, warnings, overall report. |
| `/api/v1/certifications` | Certification CRUD and assignment history. |
| `/api/v1/quiz-evaluator` | Quiz evaluator configuration, thresholds, templates, prompt, presets, reset. |
| `/api/v1` premium routes | Badges, assessment schedules, performance analytics, PDF exports, AI feedback, AI insights. |

### Appendix C: Core Data Model Areas

The backend model layer includes:

- `User`
- `Fresher`
- `Skill`
- `Achievement`
- `Schedule`
- `ScheduleItem`
- `Assessment`
- `Submission`
- `Curriculum`
- `Report`
- `Alert`
- `Badge`
- `FresherBadge`
- `AssessmentSchedule`
- `PerformanceAnalytics`
- `Certification`
- `AssignmentHistory`

### Appendix D: Environment Variables

| Variable | Default / Example | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./maverickai.db` | Backend database connection string. |
| `SECRET_KEY` | `maverickai-super-secret-key-change-in-production` | JWT signing secret; must be replaced in production. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | JWT access-token lifetime. |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama service URL. |
| `OLLAMA_MODEL` | `gpt-oss:120b-cloud` | Default LLM model setting. |
| `OLLAMA_CODE_MODEL` | `gpt-oss:120b-cloud` | Code-oriented LLM model setting. |
| `OLLAMA_FAST_MODEL` | `gpt-oss:120b-cloud` | Fast LLM model setting. |
| `N8N_WEBHOOK_URL` | `http://localhost:5678/webhook` | Configured webhook URL; active use not verified. |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:3001,http://localhost:8000` | Intended allowed origins configuration, though current middleware allows all origins. |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | Frontend API base URL. |

### Appendix E: Local Run Commands

Backend:

```powershell
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend:

```powershell
cd frontend
npm ci
npm run dev
```

Docker Compose:

```powershell
docker compose up --build
```

### Appendix F: Production Readiness Checklist

- Replace all default secrets and passwords.
- Disable or tightly restrict demo seed accounts.
- Restrict CORS origins.
- Complete route-level authorization audit.
- Fix workflow grading/status QA defects.
- Fix frontend TypeScript compile defect.
- Add migration tooling for schema changes.
- Add automated backend and frontend tests.
- Add monitoring, structured logging, and alerting.
- Add database backup and restore process.
- Add deployment-specific environment documentation.
- Confirm AI model availability, governance, and fallback behavior.
- Validate report access and PDF download authorization.
- Remove or reduce sensitive debug logs.

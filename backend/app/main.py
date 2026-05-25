from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import create_tables, SessionLocal

# Import routers
from app.api.routes import auth, freshers, schedules, assessments, analytics, agents, workflows, reports, curricula, admin, premium, certifications, quiz_config

app = FastAPI(
    title="MaverickAI API",
    description="Multi-Agent Platform for Enterprise Fresher Onboarding and Training Management",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Type", "Content-Length"],
)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "MaverickAI API", "version": "1.0.0"}


@app.get("/api/v1/health/db")
async def health_db():
    """Database health check endpoint"""
    try:
        db = SessionLocal()
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


# Mount routers
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(freshers.router, prefix="/api/v1/freshers")
app.include_router(schedules.router, prefix="/api/v1/schedules")
app.include_router(assessments.router, prefix="/api/v1/assessments")
app.include_router(analytics.router, prefix="/api/v1/analytics")
app.include_router(agents.router, prefix="/api/v1/agents")
app.include_router(workflows.router, prefix="/api/v1/workflows")
app.include_router(reports.router, prefix="/api/v1/reports")
app.include_router(curricula.router, prefix="/api/v1/curricula")
app.include_router(admin.router, prefix="/api/v1/admin")
app.include_router(premium.router)  # Premium routes use their own /api/v1 prefix
app.include_router(certifications.router, prefix="/api/v1/certifications")
app.include_router(quiz_config.router, prefix="/api/v1/quiz-evaluator")


@app.on_event("startup")
async def startup():
    print("[START] MaverickAI Backend starting...")
    create_tables()
    print("[OK] Database tables created")

    # Auto-seed on first run
    db = SessionLocal()
    try:
        from app.seed import seed_database
        seed_database(db)
    finally:
        db.close()

    print("[READY] MaverickAI API ready at http://localhost:8000")
    print("[DOCS] Swagger docs at http://localhost:8000/docs")

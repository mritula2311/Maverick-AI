from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# SQLite needs check_same_thread=False for FastAPI
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    from app.models import (
        User, Fresher, Skill, Achievement,
        Schedule, ScheduleItem,
        Assessment, Submission,
        Curriculum, Report, Alert,
    )
    from app.models.badge import Badge, FresherBadge
    from app.models.schedule_assessment import AssessmentSchedule
    from app.models.analytics import PerformanceAnalytics
    from app.models.certification import Certification, AssignmentHistory
    Base.metadata.create_all(bind=engine)
    _migrate_missing_columns()


def _migrate_missing_columns():
    """Add any columns that exist in models but not in the DB (SQLite-safe ALTER TABLE)."""
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.connect() as conn:
        for table_name, table in Base.metadata.tables.items():
            if table_name not in existing_tables:
                continue
            db_cols = {col["name"] for col in inspector.get_columns(table_name)}
            for col in table.columns:
                if col.name not in db_cols:
                    col_type = col.type.compile(engine.dialect)
                    nullable = "NULL" if col.nullable else "NOT NULL DEFAULT ''"
                    try:
                        conn.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN "{col.name}" {col_type}'))
                        conn.commit()
                        print(f"[MIGRATE] Added column {table_name}.{col.name}")
                    except Exception as e:
                        print(f"[MIGRATE] Skip {table_name}.{col.name}: {e}")

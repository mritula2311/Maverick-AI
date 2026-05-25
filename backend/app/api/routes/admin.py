from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.core.security import get_password_hash


def _build_fresher_details(db: Session, fresher):
    from app.models.fresher import Skill
    from app.models.assessment import Submission, Assessment
    from app.models.certification import Certification

    user = db.query(User).filter(User.id == fresher.user_id).first()
    if not user:
        return None

    skills = db.query(Skill).filter(Skill.fresher_id == fresher.id).all()
    submissions = db.query(Submission).filter(Submission.user_id == user.id).order_by(Submission.submitted_at.desc()).all()
    certifications = db.query(Certification).filter(Certification.fresher_id == fresher.id).order_by(Certification.updated_at.desc()).all()

    latest_quiz = next((s for s in submissions if s.submission_type == "quiz"), None)
    latest_assignment = next((s for s in submissions if s.submission_type == "assignment"), None)

    quiz_obj = db.query(Assessment).filter(
        Assessment.is_active == True,
        Assessment.assessment_type == "quiz"
    ).order_by(Assessment.id.asc()).first()

    assignment_obj = db.query(Assessment).filter(
        Assessment.is_active == True,
        Assessment.assessment_type == "assignment"
    ).order_by(Assessment.id.asc()).first()

    latest_cert = certifications[0] if certifications else None

    return {
        "id": str(fresher.id),
        "user_id": str(user.id),
        "name": f"{user.first_name} {user.last_name}".strip(),
        "email": user.email,
        "department": user.department,
        "employee_id": fresher.employee_id,
        "join_date": fresher.join_date,
        "current_week": fresher.current_week,
        "overall_progress": fresher.overall_progress,
        "risk_level": fresher.risk_level,
        "risk_score": fresher.risk_score,
        "profile": {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "department": user.department,
            "employee_id": fresher.employee_id,
            "join_date": fresher.join_date,
            "current_week": fresher.current_week,
            "overall_progress": fresher.overall_progress,
            "risk_level": fresher.risk_level,
            "risk_score": fresher.risk_score,
        },
        "training": {
            "quiz": {
                "status": latest_quiz.status if latest_quiz else "not_started",
                "score": latest_quiz.score if latest_quiz else None,
                "title": quiz_obj.title if quiz_obj else "Python Quiz",
            },
            "assignment": {
                "status": latest_assignment.status if latest_assignment else "not_started",
                "score": latest_assignment.score if latest_assignment else None,
                "title": assignment_obj.title if assignment_obj else "Software Assignment",
            },
            "certification": {
                "status": latest_cert.status if latest_cert else "not_started",
                "progress": latest_cert.progress if latest_cert else 0,
                "name": latest_cert.name if latest_cert else "AWS Cloud Practitioner",
                "linkedin_url": latest_cert.certificate_url if latest_cert else None,
            },
        },
        "workflow": {
            "profile": True,
            "quiz": bool(latest_quiz and latest_quiz.status in ["completed", "graded"]),
            "assignment": bool(latest_assignment and latest_assignment.status in ["submitted", "completed", "graded"]),
            "certification": bool(latest_cert and latest_cert.progress >= 100),
        },
        "skills": [
            {
                "name": s.name,
                "level": s.level,
                "category": s.category,
                "trend": s.trend,
                "assessments_count": s.assessments_count,
            }
            for s in skills
        ],
        "certifications": [
            {
                "id": str(c.id),
                "name": c.name,
                "provider": c.provider,
                "status": c.status,
                "progress": c.progress,
                "linkedin_url": c.certificate_url,
                "resource_url": c.certification_url,
                "updated_at": str(c.updated_at) if c.updated_at else "",
            }
            for c in certifications
        ],
        "submissions": [
            {
                "id": str(s.id),
                "assessment_id": str(s.assessment_id),
                "submission_type": s.submission_type,
                "status": s.status,
                "score": s.score,
                "pass_status": s.pass_status,
                "submitted_at": str(s.submitted_at) if s.submitted_at else "",
                "graded_at": str(s.graded_at) if s.graded_at else "",
            }
            for s in submissions
        ],
    }

router = APIRouter(tags=["Admin"])


def _require_admin(current_user: User = Depends(get_current_user)):
    """Enforce admin role requirement"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/users")
def get_users(db: Session = Depends(get_db), admin_user: User = Depends(_require_admin)):
    users = db.query(User).all()
    return {
        "items": [
            {
                "id": str(u.id),
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "role": u.role,
                "department": u.department,
                "is_active": u.is_active,
                "created_at": str(u.created_at) if u.created_at else "",
                "updated_at": str(u.updated_at) if u.updated_at else "",
            }
            for u in users
        ],
        "total": len(users),
        "page": 1,
    }


@router.post("/users")
def create_user(data: dict, db: Session = Depends(get_db), admin_user: User = Depends(_require_admin)):
    existing = db.query(User).filter(User.email == data.get("email")).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=data.get("email"),
        first_name=data.get("first_name", ""),
        last_name=data.get("last_name", ""),
        hashed_password=get_password_hash(data.get("password", "password123")),
        role=data.get("role", "fresher"),
        department=data.get("department"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
    }


@router.post("/bulk/assign-mentor")
def bulk_assign(data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.fresher import Fresher
    fresher_ids = data.get("fresher_ids", [])
    mentor_id = data.get("mentor_id")
    count = 0
    for fid in fresher_ids:
        fresher = db.query(Fresher).filter(Fresher.id == int(fid)).first()
        if fresher:
            fresher.mentor_id = int(mentor_id)
            count += 1
    db.commit()
    return {"updated": count}


@router.get("/stats")
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.fresher import Fresher
    from app.models.assessment import Assessment, Submission
    return {
        "total_users": db.query(User).count(),
        "total_freshers": db.query(Fresher).count(),
        "total_assessments": db.query(Assessment).count(),
        "total_submissions": db.query(Submission).count(),
        "system_status": "healthy",
    }


@router.get("/freshers/details")
def get_all_fresher_details(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.fresher import Fresher

    freshers = db.query(Fresher).order_by(Fresher.id.asc()).all()
    details = []
    for fresher in freshers:
        detail = _build_fresher_details(db, fresher)
        if detail:
            details.append(detail)
    return {"freshers": details}


@router.get("/freshers/{fresher_id}/details")
def get_fresher_full_details(fresher_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.fresher import Fresher

    fresher = db.query(Fresher).filter(Fresher.id == int(fresher_id)).first()
    if not fresher:
        raise HTTPException(status_code=404, detail="Fresher not found")

    detail = _build_fresher_details(db, fresher)
    if not detail:
        raise HTTPException(status_code=404, detail="Fresher user profile not found")

    return detail


@router.post("/seed-data")
def seed_data(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.seed import seed_database
    seed_database(db)
    return {"status": "success", "message": "Test data seeded successfully"}


@router.get("/warnings")
def get_performance_warnings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get all performance warnings for freshers who have failed assessments 2-3+ times.
    Returns professional HR warnings with recommendations.
    """
    from app.agents.reporting_agent import ReportingAgent
    agent = ReportingAgent()
    return agent.generate_warnings_report(db)


@router.get("/overall-report")
def get_overall_performance_report(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Generate comprehensive overall performance report for entire cohort.
    Includes warnings, top performers, struggling performers, and HR recommendations.
    """
    from app.agents.reporting_agent import ReportingAgent
    agent = ReportingAgent()
    return agent.generate_overall_performance_report(db)


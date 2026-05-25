import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.fresher import Fresher, Skill, Achievement
from app.models.badge import Badge, FresherBadge
from app.models.schedule import Schedule, ScheduleItem
from app.models.assessment import Assessment, Submission

router = APIRouter(tags=["Freshers"])


@router.get("/me")
def get_my_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    fresher = db.query(Fresher).filter(Fresher.user_id == current_user.id).first()
    if not fresher:
        raise HTTPException(status_code=404, detail="Fresher profile not found")
    try:
        return _build_dashboard(db, fresher, current_user)
    except Exception as e:
        print(f"[ERROR] Dashboard build failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")


@router.get("/user/{user_id}")
def get_by_user_id(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    fresher = db.query(Fresher).filter(Fresher.user_id == int(user_id)).first()
    if not fresher:
        raise HTTPException(status_code=404, detail="Fresher not found")
    return _fresher_dict(fresher, db)


@router.get("", response_model=None)
def list_freshers(
    department: str = None,
    status: str = None,
    skill: str = None,
    search: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Fresher)
    freshers = query.all()
    result = []
    for f in freshers:
        user = db.query(User).filter(User.id == f.user_id).first()
        if search and user:
            full_name = f"{user.first_name} {user.last_name}".lower()
            if search.lower() not in full_name:
                continue
        if department and user and user.department != department:
            continue
        result.append(_fresher_dict(f, db))
    return result


@router.get("/{fresher_id}")
def get_fresher(fresher_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    fresher = db.query(Fresher).filter(Fresher.id == int(fresher_id)).first()
    if not fresher:
        raise HTTPException(status_code=404, detail="Fresher not found")
    return _fresher_dict(fresher, db)


@router.get("/{fresher_id}/dashboard")
def get_fresher_dashboard(fresher_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    fresher = db.query(Fresher).filter(Fresher.id == int(fresher_id)).first()
    if not fresher:
        raise HTTPException(status_code=404, detail="Fresher not found")
    user = db.query(User).filter(User.id == fresher.user_id).first()
    return _build_dashboard(db, fresher, user)


@router.get("/{fresher_id}/skills")
def get_skills(fresher_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    skills = db.query(Skill).filter(Skill.fresher_id == int(fresher_id)).all()
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "category": s.category,
            "level": s.level,
            "trend": s.trend,
            "assessments_count": s.assessments_count,
        }
        for s in skills
    ]


@router.get("/{fresher_id}/training-status")
def get_training_status(fresher_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    fresher = db.query(Fresher).filter(Fresher.id == int(fresher_id)).first()
    if not fresher:
        raise HTTPException(status_code=404, detail="Fresher not found")
    subs = db.query(Submission).filter(Submission.user_id == fresher.user_id).all()
    quiz_done = any(s.submission_type == "quiz" and s.status == "completed" for s in subs)
    assign_done = any(s.submission_type == "assignment" and s.status == "completed" for s in subs)
    return {
        "quiz_status": "completed" if quiz_done else "not_started",
        "quiz_score": next((s.score for s in subs if s.submission_type == "quiz" and s.score), None),
        "assignment_status": "completed" if assign_done else "not_started",
        "assignment_score": next((s.score for s in subs if s.submission_type == "assignment" and s.score), None),
        "certification_status": "not_started",
        "certification_name": None,
    }


@router.get("/{fresher_id}/workflow-status")
def get_workflow_status(fresher_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {
        "profile_updated": True,
        "daily_quiz_completed": False,
        "assignment_submitted": False,
        "certification_completed": False,
        "last_updated": "2026-02-14T10:00:00Z",
    }


@router.get("/{fresher_id}/assessment-evaluations")
def get_assessment_evaluations(fresher_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get recent AI-powered assessment evaluations with detailed feedback - ONLY for attempted/completed assessments"""
    fresher = db.query(Fresher).filter(Fresher.id == int(fresher_id)).first()
    if not fresher:
        raise HTTPException(status_code=404, detail="Fresher not found")
    
    # Get ONLY completed/graded submissions with valid scores (attempted assessments)
    # Exclude "submitted" status as it means submitted but not yet graded
    submissions = db.query(Submission).filter(
        Submission.user_id == fresher.user_id,
        Submission.status.in_(["completed", "graded"]),  # Only completed or graded
        Submission.score != None,  # Must have a score
        Submission.score >= 0  # Score must be valid (>= 0)
    ).order_by(Submission.submitted_at.desc()).all()
    
    print(f"[DEBUG] Fetching evaluations for fresher_id={fresher_id}, user_id={fresher.user_id}")
    print(f"[DEBUG] Found {len(submissions)} attempted submissions")
    
    evaluations = []
    for sub in submissions:
        assessment = db.query(Assessment).filter(Assessment.id == sub.assessment_id).first()
        if not assessment:
            print(f"[DEBUG] No assessment found for submission {sub.id}")
            continue
            
        # Parse feedback
        feedback_obj = {}
        if sub.feedback:
            try:
                feedback_obj = json.loads(sub.feedback)
            except Exception as e:
                print(f"[DEBUG] Error parsing feedback for submission {sub.id}: {e}")
                pass
        
        # Sanitize lists to ensure all items are strings (LLM may return objects)
        def clean_list(l):
            if not isinstance(l, list): return []
            return [str(v) if isinstance(v, (dict, list)) else str(v) for v in l]
        
        # Calculate time ago
        from datetime import datetime, timezone
        now_utc = datetime.now(timezone.utc)
        submitted = sub.submitted_at if sub.submitted_at.tzinfo else sub.submitted_at.replace(tzinfo=timezone.utc)
        time_diff = now_utc - submitted
        if time_diff.days > 0:
            time_ago = f"{time_diff.days}d ago"
        elif time_diff.seconds // 3600 > 0:
            time_ago = f"{time_diff.seconds // 3600}h ago"
        else:
            time_ago = f"{time_diff.seconds // 60}m ago"
        
        eval_obj = {
            "id": str(sub.id),
            "assessment_title": assessment.title,
            "assessment_type": assessment.assessment_type,
            "score": sub.score,
            "pass_status": sub.pass_status,
            "status": sub.status,
            "time_ago": time_ago,
            "feedback": {
                "overall": str(feedback_obj.get("overall_comment", feedback_obj.get("overall_assessment", "Assessment evaluated successfully"))),
                "strengths": clean_list(feedback_obj.get("strengths", [])),
                "weaknesses": clean_list(feedback_obj.get("weaknesses", feedback_obj.get("areas_for_improvement", []))),
                "suggestions": clean_list(feedback_obj.get("suggestions", feedback_obj.get("developmental_recommendations", []))),
                "risk_level": str(feedback_obj.get("risk_level", "low")),
                "test_score": feedback_obj.get("test_score"),
                "style_score": feedback_obj.get("style_score"),
            }
        }
        evaluations.append(eval_obj)
        print(f"[DEBUG] Added evaluation: {assessment.title} - Score: {sub.score}")
    
    print(f"[DEBUG] Returning {len(evaluations)} attempted evaluations (filtered)")
    return evaluations


@router.get("/schedule-items/{item_id}")
def get_schedule_item(item_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(ScheduleItem).filter(ScheduleItem.id == int(item_id)).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {
        "id": str(item.id),
        "title": item.title,
        "description": item.description,
        "item_type": item.item_type,
        "duration_minutes": item.duration_minutes,
        "status": item.status,
        "topic": item.topic,
        "content": item.content,
        "external_url": item.external_url,
        "assessment_id": item.assessment_id,
    }


@router.put("/{fresher_id}")
def update_profile(fresher_id: str, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    fresher = db.query(Fresher).filter(Fresher.id == int(fresher_id)).first()
    if not fresher:
        raise HTTPException(status_code=404, detail="Fresher not found")
    for key, val in data.items():
        if hasattr(fresher, key):
            setattr(fresher, key, val)
    db.commit()
    db.refresh(fresher)
    return _fresher_dict(fresher, db)


def _fresher_dict(fresher: Fresher, db: Session) -> dict:
    user = db.query(User).filter(User.id == fresher.user_id).first()
    return {
        "id": str(fresher.id),
        "user_id": str(fresher.user_id),
        "employee_id": fresher.employee_id,
        "mentor_id": str(fresher.mentor_id) if fresher.mentor_id else None,
        "manager_id": str(fresher.manager_id) if fresher.manager_id else None,
        "join_date": fresher.join_date,
        "onboarding_end_date": fresher.onboarding_end_date,
        "current_week": fresher.current_week,
        "overall_progress": fresher.overall_progress,
        "risk_level": fresher.risk_level,
        "risk_score": fresher.risk_score,
        "created_at": str(fresher.created_at) if fresher.created_at else "",
        "updated_at": str(fresher.updated_at) if fresher.updated_at else "",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "department": user.department,
            "is_active": user.is_active,
            "created_at": str(user.created_at) if user.created_at else "",
            "updated_at": str(user.updated_at) if user.updated_at else "",
        } if user else None,
    }


def _build_dashboard(db: Session, fresher: Fresher, user: User) -> dict:
    from datetime import date
    skills = db.query(Skill).filter(Skill.fresher_id == fresher.id).all()
    achievements = db.query(Achievement).filter(Achievement.fresher_id == fresher.id).all()
    fresher_badges = db.query(FresherBadge).filter(FresherBadge.fresher_id == fresher.id).all()
    today = date.today().isoformat()
    schedule = db.query(Schedule).filter(Schedule.fresher_id == fresher.id, Schedule.schedule_date == today).first()
    items = []
    if schedule:
        raw_items = db.query(ScheduleItem).filter(ScheduleItem.schedule_id == schedule.id).all()
        items = [
            {
                "id": str(si.id),
                "title": si.title,
                "description": si.description,
                "item_type": si.item_type,
                "duration_minutes": si.duration_minutes,
                "status": si.status,
                "topic": si.topic,
                "start_time": si.start_time,
                "end_time": si.end_time,
                "content": si.content,
                "external_url": si.external_url,
            }
            for si in raw_items
        ]
    # ONLY quiz and assignment assessments (code challenges removed)
    raw_assessments = db.query(Assessment).filter(
        Assessment.is_active == True,
        Assessment.assessment_type.in_(["quiz", "assignment"])
    ).all()
    upcoming = [
        {
            "id": str(a.id),
            "title": a.title,
            "description": a.description,
            "assessment_type": a.assessment_type,
            "max_score": a.max_score,
            "passing_score": a.passing_score,
            "due_date": a.available_until,
            "created_at": str(a.created_at) if a.created_at else "",
        }
        for a in raw_assessments[:5]
    ]
    subs = db.query(Submission).filter(Submission.user_id == user.id).order_by(Submission.submitted_at.desc()).all()
    passed = sum(1 for s in subs if s.pass_status == "pass")

    # Dynamic training status - ONLY quiz and assignment (code removed)
    quiz_sub = next((s for s in subs if s.submission_type == "quiz"), None)
    assign_sub = next((s for s in subs if s.submission_type == "assignment"), None)

    # Direct DB queries to ensure correct assessment types (Python quiz, Software assignment)
    quiz_obj = db.query(Assessment).filter(
        Assessment.is_active == True,
        Assessment.assessment_type == "quiz",
        Assessment.title.ilike("%python%")
    ).order_by(Assessment.id.asc()).first()
    if not quiz_obj:
        quiz_obj = db.query(Assessment).filter(
            Assessment.is_active == True,
            Assessment.assessment_type == "quiz"
        ).order_by(Assessment.id.asc()).first()
    
    assign_obj = db.query(Assessment).filter(
        Assessment.is_active == True,
        Assessment.assessment_type == "assignment",
        Assessment.title.ilike("%software%")
    ).order_by(Assessment.id.asc()).first()
    if not assign_obj:
        assign_obj = db.query(Assessment).filter(
            Assessment.is_active == True,
            Assessment.assessment_type == "assignment"
        ).order_by(Assessment.id.asc()).first()

    # Certification progress (first certification record if exists)
    from app.models.certification import Certification
    cert_obj = db.query(Certification).filter(Certification.fresher_id == fresher.id).order_by(Certification.id.asc()).first()

    training_status = {
        "quiz_status": str(quiz_sub.status) if quiz_sub else "not_started",
        "quiz_score": quiz_sub.score if quiz_sub else None,
        "quiz_id": str(quiz_obj.id) if quiz_obj else "",
        "quiz_title": quiz_obj.title if quiz_obj else "Python Quiz",
        "assignment_status": "submitted" if assign_sub else "pending",
        "assignment_score": assign_sub.score if assign_sub else None,
        "assignment_id": str(assign_obj.id) if assign_obj else "",
        "assignment_title": assign_obj.title if assign_obj else "Software Assignment",
        "certification_status": cert_obj.status if cert_obj else "not_started",
        "certification_name": cert_obj.name if cert_obj else "AWS Cloud Practitioner",
        "certification_progress": cert_obj.progress if cert_obj else 0.0,
    }

    return {
        "fresher": _fresher_dict(fresher, db),
        "user": {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "department": user.department,
            "is_active": user.is_active,
            "created_at": str(user.created_at) if user.created_at else "",
            "updated_at": str(user.updated_at) if user.updated_at else "",
        },
        "progress": {
            "overall": fresher.overall_progress,
            "current_week": fresher.current_week,
            "topics_completed": int(fresher.overall_progress / 10),
            "topics_total": 10,
            "assessments_passed": passed,
            "assessments_total": len(subs) or 5,
            "learning_hours_today": 2.5,
            "learning_hours_week": 18.0,
            "streak": 5,
        },
        "today_schedule": items,
        "upcoming_assessments": upcoming,
        "training_status": training_status,
        "recent_achievements": [
            {
                "id": str(a.id),
                "title": a.title,
                "icon": a.icon,
                "description": a.description,
                "earned_at": str(a.earned_at) if a.earned_at else "",
            }
            for a in achievements
        ],
        "badges": [
            {
                "id": str(fb.badge.id),
                "name": fb.badge.name,
                "description": fb.badge.description,
                "skill_name": fb.badge.skill_name,
                "color": fb.badge.color,
                "icon_url": fb.badge.icon_url,
                "score_achieved": fb.score_achieved,
                "earned_at": str(fb.earned_at) if fb.earned_at else "",
            }
            for fb in fresher_badges
        ],
        "agent_activity": [
            {"id": "1", "agent": "Onboarding Agent", "task": "Generating personalized schedule", "status": "idle", "last_run": "10 mins ago"},
            {"id": "2", "agent": "Assessment Agent", "task": "Grading Python Quiz", "status": "idle", "last_run": "2 hours ago"},
            {"id": "3", "agent": "Analytics Agent", "task": "Calculating performance risk", "status": "active", "last_run": "Just now"},
            {"id": "4", "agent": "Reporting Agent", "task": "Synthesizing weekly report", "status": "scheduled", "last_run": "5 hours ago"},
        ],
        "multi_agent_workflow": {
            "title": "Continuous Learning Loop",
            "steps": [
                {"name": "Discovery", "desc": "Onboarding Agent analyzes curriculum vs trainee profile", "completed": True},
                {"name": "Execution", "desc": "Trainee completes tasks; Assessment Agent evaluates in real-time", "completed": True},
                {"name": "Analysis", "desc": "Analytics Agent predicts risk & identifies skill gaps", "completed": False},
                {"name": "Optimization", "desc": "Agents collaborate to refine tomorrow's schedule", "completed": False},
            ]
        },
        "skills": [
            {
                "id": str(s.id),
                "name": s.name,
                "category": s.category,
                "level": s.level,
                "trend": s.trend,
                "assessments_count": s.assessments_count,
            }
            for s in skills
        ],
        "workflow_status": {
            "profile_updated": True,
            "daily_quiz_completed": quiz_sub is not None,
            "assignment_submitted": assign_sub is not None,
            "certification_completed": False,
            "last_updated": "2026-02-14T10:00:00Z",
        },
    }

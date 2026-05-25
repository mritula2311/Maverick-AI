"""API routes for badges, scheduling, analytics, and reports."""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.badge import Badge, FresherBadge
from app.models.schedule_assessment import AssessmentSchedule
from app.models.analytics import PerformanceAnalytics
from app.models.fresher import Fresher
from app.models.assessment import Submission, Assessment
from app.utils.feedback_generator import feedback_generator
from app.utils.pdf_generator_v2 import pdf_generator
from datetime import datetime, timedelta
import json

from app.models.user import User
router = APIRouter(prefix="/api/v1", tags=["premium"], dependencies=[Depends(get_current_user)])


# ============= BADGE ROUTES =============

@router.get("/badges")
def list_badges(db: Session = Depends(get_db)):
    """Get all available badges."""
    badges = db.query(Badge).all()
    return {
        "total": len(badges),
        "badges": [
            {
                "id": b.id,
                "name": b.name,
                "description": b.description,
                "skill_name": b.skill_name,
                "min_score": b.min_score,
                "color": b.color,
                "icon_url": b.icon_url,
            }
            for b in badges
        ]
    }


@router.get("/freshers/{fresher_id}/badges")
def get_fresher_badges(fresher_id: int, db: Session = Depends(get_db)):
    """Get badges earned by a fresher."""
    fresher = db.get(Fresher, fresher_id)
    if not fresher:
        raise HTTPException(status_code=404, detail="Fresher not found")
    
    badges = db.query(FresherBadge).filter(FresherBadge.fresher_id == fresher_id).all()
    return {
        "fresher_id": fresher_id,
        "total_badges": len(badges),
        "badges": [
            {
                "id": fb.badge.id,
                "name": fb.badge.name,
                "description": fb.badge.description,
                "earned_at": fb.earned_at.isoformat(),
                "score_achieved": fb.score_achieved,
                "skill_name": fb.badge.skill_name,
            }
            for fb in badges
        ]
    }


@router.post("/freshers/{fresher_id}/badges/{badge_id}")
def assign_badge(fresher_id: int, badge_id: int, score: float, assessment_id: int = None, db: Session = Depends(get_db)):
    """Manually assign a badge to a fresher."""
    fresher = db.get(Fresher, fresher_id)
    badge = db.get(Badge, badge_id)
    
    if not fresher or not badge:
        raise HTTPException(status_code=404, detail="Fresher or badge not found")
    
    # Check if already earned
    existing = db.query(FresherBadge).filter(
        FresherBadge.fresher_id == fresher_id,
        FresherBadge.badge_id == badge_id
    ).first()
    
    if existing:
        return {"status": "already_earned", "badge_id": badge_id}
    
    # Create new badge record
    fresher_badge = FresherBadge(
        fresher_id=fresher_id,
        badge_id=badge_id,
        assessment_id=assessment_id,
        score_achieved=score,
        earned_at=datetime.utcnow()
    )
    db.add(fresher_badge)
    db.commit()
    
    return {
        "status": "badge_assigned",
        "fresher_id": fresher_id,
        "badge_id": badge_id,
        "badge_name": badge.name
    }


# ============= SCHEDULING ROUTES =============

@router.get("/assessments/{assessment_id}/schedules")
def get_assessment_schedules(assessment_id: int, db: Session = Depends(get_db)):
    """Get all schedules for an assessment."""
    schedules = db.query(AssessmentSchedule).filter(
        AssessmentSchedule.assessment_id == assessment_id
    ).all()
    
    return {
        "assessment_id": assessment_id,
        "total_schedules": len(schedules),
        "schedules": [
            {
                "id": s.id,
                "scheduled_date": s.scheduled_date.isoformat(),
                "deadline": s.deadline.isoformat(),
                "duration_minutes": s.duration_minutes,
                "is_mandatory": s.is_mandatory,
                "description": s.description,
                "fresher_id": s.fresher_id,
            }
            for s in schedules
        ]
    }


@router.post("/assessments/{assessment_id}/schedule")
def create_assessment_schedule(
    assessment_id: int,
    scheduled_date: str,
    deadline: str,
    duration_minutes: int,
    fresher_id: int = None,
    is_mandatory: bool = True,
    description: str = "",
    db: Session = Depends(get_db)
):
    """Create a new assessment schedule."""
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    schedule = AssessmentSchedule(
        assessment_id=assessment_id,
        fresher_id=fresher_id,
        scheduled_date=datetime.fromisoformat(scheduled_date),
        deadline=datetime.fromisoformat(deadline),
        duration_minutes=duration_minutes,
        is_mandatory=is_mandatory,
        description=description,
        is_active=True
    )
    db.add(schedule)
    db.commit()
    
    return {
        "status": "schedule_created",
        "schedule_id": schedule.id,
        "assessment_id": assessment_id
    }


@router.get("/freshers/{fresher_id}/schedules")
def get_fresher_schedules(fresher_id: int, db: Session = Depends(get_db)):
    """Get upcoming assessment schedules for a fresher."""
    fresher = db.get(Fresher, fresher_id)
    if not fresher:
        raise HTTPException(status_code=404, detail="Fresher not found")
    
    # Get both fresher-specific and general schedules
    now = datetime.utcnow()
    schedules = db.query(AssessmentSchedule).filter(
        (AssessmentSchedule.fresher_id == fresher_id) | (AssessmentSchedule.fresher_id == None),
        AssessmentSchedule.scheduled_date >= now - timedelta(days=1),
        AssessmentSchedule.is_active == True
    ).order_by(AssessmentSchedule.scheduled_date).all()
    
    return {
        "fresher_id": fresher_id,
        "total_upcoming": len(schedules),
        "schedules": [
            {
                "id": s.id,
                "assessment_id": s.assessment_id,
                "assessment_title": s.assessment.title,
                "scheduled_date": s.scheduled_date.isoformat(),
                "deadline": s.deadline.isoformat(),
                "duration_minutes": s.duration_minutes,
                "is_mandatory": s.is_mandatory,
                "days_remaining": (s.deadline - now).days,
                "description": s.description,
            }
            for s in schedules
        ]
    }


# ============= ANALYTICS ROUTES =============

@router.get("/freshers/{fresher_id}/analytics")
def get_fresher_analytics(fresher_id: int, db: Session = Depends(get_db)):
    """Get performance analytics for a fresher."""
    fresher = db.get(Fresher, fresher_id)
    if not fresher:
        raise HTTPException(status_code=404, detail="Fresher not found")
    
    analytics = db.query(PerformanceAnalytics).filter(
        PerformanceAnalytics.fresher_id == fresher_id
    ).first()
    
    if not analytics:
        # Create default analytics if not exists
        analytics = PerformanceAnalytics(fresher_id=fresher_id)
        db.add(analytics)
        db.commit()
    
    return {
        "fresher_id": fresher_id,
        "overall_score": analytics.overall_score,
        "quiz_average": analytics.quiz_average,
        "assessment_count": analytics.assessment_count,
        "pass_rate": analytics.pass_rate,
        "skills_breakdown": analytics.skills_breakdown or {},
        "risk_level": analytics.risk_level,
        "risk_score": analytics.risk_score,
        "engagement_score": analytics.engagement_score,
        "cohort_percentile": analytics.cohort_percentile,
        "improvement_rate": analytics.improvement_rate,
        "last_updated": analytics.updated_at.isoformat(),
    }


@router.get("/analytics/cohort-comparison")
def get_cohort_comparison(db: Session = Depends(get_db)):
    """Get fresher comparison dashboard data."""
    analytics_list = db.query(PerformanceAnalytics).all()
    
    freshers_data = []
    for analytics in analytics_list:
        fresher = db.get(Fresher, analytics.fresher_id)
        if fresher and fresher.user_id:
            user = fresher.user_id  # Simplified for brevity
            freshers_data.append({
                "fresher_id": analytics.fresher_id,
                "fresher_name": f"Fresher {analytics.fresher_id}",
                "overall_score": analytics.overall_score,
                "pass_rate": analytics.pass_rate,
                "engagement_score": analytics.engagement_score,
                "risk_level": analytics.risk_level,
                "assessments_completed": analytics.assessment_count,
                "cohort_percentile": analytics.cohort_percentile,
            })
    
    # Sort by overall score
    freshers_data.sort(key=lambda x: x['overall_score'], reverse=True)
    
    # Add rank
    for idx, fresher in enumerate(freshers_data, 1):
        fresher['cohort_rank'] = idx
    
    cohort_avg = sum(f['overall_score'] for f in freshers_data) / len(freshers_data) if freshers_data else 0
    
    return {
        "total_freshers": len(freshers_data),
        "cohort_average_score": cohort_avg,
        "freshers": freshers_data
    }


@router.post("/analytics/update/{fresher_id}")
def update_fresher_analytics(fresher_id: int, db: Session = Depends(get_db)):
    """Recalculate analytics for a fresher based on submissions."""
    fresher = db.get(Fresher, fresher_id)
    if not fresher:
        raise HTTPException(status_code=404, detail="Fresher not found")
    
    # Get all submissions for this fresher
    submissions = db.query(Submission).filter(Submission.user_id == fresher.user_id).all()
    
    if not submissions:
        return {"status": "no_submissions"}
    
    # Calculate metrics (guard against None scores)
    scored = [s for s in submissions if s.score is not None]
    total_score = sum(s.score for s in scored)
    avg_score = total_score / len(scored) if scored else 0

    quiz_subs = [s for s in scored if s.submission_type == 'quiz']
    quiz_avg = sum(s.score for s in quiz_subs) / len(quiz_subs) if quiz_subs else 0
    
    passed = sum(1 for s in submissions if s.pass_status == 'pass')
    pass_rate = (passed / len(submissions) * 100) if submissions else 0
    
    # Update or create analytics
    analytics = db.query(PerformanceAnalytics).filter(
        PerformanceAnalytics.fresher_id == fresher_id
    ).first()
    
    if not analytics:
        analytics = PerformanceAnalytics(fresher_id=fresher_id)
    
    analytics.overall_score = avg_score
    analytics.quiz_average = quiz_avg
    analytics.assessment_count = len(submissions)
    analytics.passed_count = passed
    analytics.failed_count = len(submissions) - passed
    analytics.pass_rate = pass_rate
    analytics.updated_at = datetime.utcnow()
    
    db.add(analytics)
    db.commit()
    
    return {
        "status": "analytics_updated",
        "fresher_id": fresher_id,
        "overall_score": avg_score,
        "pass_rate": pass_rate,
    }


# ============= REPORT/PDF ROUTES =============

@router.get("/submissions/{submission_id}/pdf")
def export_submission_pdf(submission_id: int, db: Session = Depends(get_db)):
    """Export individual submission as PDF."""
    submission = db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    assessment = db.get(Assessment, submission.assessment_id)
    fresher = db.query(Fresher).filter(Fresher.user_id == submission.user_id).first()
    
    if not assessment or not fresher:
        raise HTTPException(status_code=404, detail="Related data not found")
    
    submission_data = {
        "score": submission.score,
        "max_score": submission.max_score,
        "passing_score": submission.passing_score,
        "type": submission.submission_type,
        "feedback": submission.feedback,
    }
    
    pdf_buffer = pdf_generator.generate_submission_pdf(
        submission_data,
        fresher_name=f"Fresher {fresher.id}",
        assessment_title=assessment.title
    )
    
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=submission_report.pdf"}
    )


@router.get("/freshers/{fresher_id}/performance-report/pdf")
def export_performance_report_pdf(fresher_id: int, db: Session = Depends(get_db)):
    """Export comprehensive performance report as PDF."""
    fresher = db.get(Fresher, fresher_id)
    if not fresher:
        raise HTTPException(status_code=404, detail="Fresher not found")
    
    analytics = db.query(PerformanceAnalytics).filter(
        PerformanceAnalytics.fresher_id == fresher_id
    ).first()
    
    if not analytics:
        raise HTTPException(status_code=404, detail="Analytics not found")
    
    fresher_data = {
        "name": f"Fresher {fresher_id}",
        "employee_id": fresher.employee_id,
    }
    
    analytics_data = {
        "overall_score": analytics.overall_score,
        "quiz_average": analytics.quiz_average,
        "pass_rate": analytics.pass_rate,
        "assessment_count": analytics.assessment_count,
        "risk_level": analytics.risk_level,
        "engagement_score": analytics.engagement_score,
        "cohort_percentile": analytics.cohort_percentile,
        "skills_breakdown": analytics.skills_breakdown or {},
    }
    
    pdf_buffer = pdf_generator.generate_performance_report_pdf(fresher_data, analytics_data)
    
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=performance_report.pdf"}
    )


# ============= FEEDBACK ROUTES =============

@router.post("/submissions/{submission_id}/ai-feedback")
def generate_ai_feedback(submission_id: int, db: Session = Depends(get_db)):
    """Generate AI-powered personalized feedback for a submission."""
    submission = db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    assessment = db.get(Assessment, submission.assessment_id)
    fresher = db.query(Fresher).filter(Fresher.user_id == submission.user_id).first()
    
    submission_data = {
        "assessment_type": submission.submission_type,
        "score": submission.score,
        "max_score": submission.max_score,
        "passing_score": submission.passing_score,
        "title": assessment.title if assessment else "Assessment",
        "fresher_name": f"Fresher {fresher.id}" if fresher else "User",
        "topics": assessment.instructions if assessment else "General",
    }
    
    feedback = feedback_generator.generate_submission_feedback(submission_data)
    
    # Save feedback to submission
    submission.feedback = json.dumps(feedback)
    db.commit()
    
    return {
        "submission_id": submission_id,
        "feedback": feedback
    }


@router.get("/freshers/{fresher_id}/ai-insights")
def get_ai_performance_insights(fresher_id: int, db: Session = Depends(get_db)):
    """Get AI-powered performance insights and recommendations."""
    fresher = db.get(Fresher, fresher_id)
    if not fresher:
        raise HTTPException(status_code=404, detail="Fresher not found")
    
    analytics = db.query(PerformanceAnalytics).filter(
        PerformanceAnalytics.fresher_id == fresher_id
    ).first()
    
    if not analytics:
        raise HTTPException(status_code=404, detail="Analytics not found")
    
    insights = feedback_generator.generate_performance_insights({
        "overall_score": analytics.overall_score,
        "quiz_average": analytics.quiz_average,
        "pass_rate": analytics.pass_rate,
        "assessment_count": analytics.assessment_count,
        "risk_level": analytics.risk_level,
        "risk_score": analytics.risk_score,
        "improvement_rate": analytics.improvement_rate,
        "cohort_percentile": analytics.cohort_percentile or 0,
        "skills_breakdown": analytics.skills_breakdown or {},
        "score_trend": analytics.score_trend or {},
    })
    
    return {
        "fresher_id": fresher_id,
        "insights": insights
    }

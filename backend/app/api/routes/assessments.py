import json
import random
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.assessment import Assessment, Submission
from app.core.llm_client import OllamaClient

router = APIRouter(tags=["Assessments"])


class AiGenerateRequest(BaseModel):
    topic: str
    assessment_type: Optional[str] = "quiz"
    max_score: Optional[int] = 100
    passing_score: Optional[int] = 60
    time_limit_minutes: Optional[int] = 15


@router.post("/ai-generate")
def ai_generate_assessment(payload: AiGenerateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Use LLM to generate a new assessment (quiz/code/assignment) on a given topic."""
    llm = OllamaClient()

    if payload.assessment_type == "quiz":
        prompt = f"""Generate a quiz on the topic: "{payload.topic}".
Create exactly 5 multiple-choice questions. Return ONLY a JSON array where each element has:
- "question": the question text
- "options": array of 4 option strings
- "correct_answer": index (0-3) of the correct option
- "explanation": brief explanation of the answer

Return ONLY the JSON array, no markdown, no extra text. Start with [ and end with ]."""
    elif payload.assessment_type == "code":
        prompt = f"""Generate a coding challenge on the topic: "{payload.topic}".
Return ONLY a JSON object with:
- "title": challenge title
- "description": detailed problem description (2-3 paragraphs)
- "starter_code": starter code template in Python
- "test_cases": array of objects with "input", "expected_output", "description"
- "language": "python"

Return ONLY the JSON object. Start with {{ and end with }}."""
    else:
        prompt = f"""Generate a written assignment on the topic: "{payload.topic}".
Return ONLY a JSON object with:
- "title": assignment title
- "description": detailed instructions (2-3 paragraphs)
- "rubric": array of objects with "criterion", "weight", "description"

Return ONLY the JSON object. Start with {{ and end with }}."""

    try:
        response = llm.generate(prompt, system="You are an expert assessment creator. Return only valid JSON, no markdown.")
        cleaned = response.strip()
        if "```" in cleaned:
            import re
            match = re.search(r"```(?:json)?\s*([\[\{].*?[\]\}])\s*```", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1)
        if cleaned.startswith("["):
            start = cleaned.find("[")
            end = cleaned.rfind("]") + 1
            cleaned = cleaned[start:end]
        elif cleaned.startswith("{"):
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            cleaned = cleaned[start:end]

        generated = json.loads(cleaned)
    except Exception as e:
        print(f"[AI-Generate] LLM error: {e}")
        # Fallback: create a simple default assessment
        if payload.assessment_type == "quiz":
            generated = [
                {"question": f"What is a key concept in {payload.topic}?", "options": ["Option A", "Option B", "Option C", "Option D"], "correct_answer": 0, "explanation": "This is a fundamental concept."},
                {"question": f"Which best describes {payload.topic}?", "options": ["Definition A", "Definition B", "Definition C", "Definition D"], "correct_answer": 1, "explanation": "Based on standard definitions."},
                {"question": f"What is an advantage of {payload.topic}?", "options": ["Speed", "Simplicity", "Scalability", "All of the above"], "correct_answer": 3, "explanation": "Multiple benefits apply."},
                {"question": f"In {payload.topic}, what is most important?", "options": ["Accuracy", "Performance", "Readability", "Depends on context"], "correct_answer": 3, "explanation": "Context matters."},
                {"question": f"How would you apply {payload.topic} in practice?", "options": ["Approach A", "Approach B", "Approach C", "Approach D"], "correct_answer": 0, "explanation": "Standard practical approach."},
            ]
        else:
            generated = {"title": f"{payload.topic} Assessment", "description": f"Complete this assessment on {payload.topic}.", "rubric": []}

    # Create Assessment in DB
    title = f"{payload.topic} - AI Generated {payload.assessment_type.title()}"
    if payload.assessment_type == "quiz":
        questions_json = json.dumps(generated)
        assessment = Assessment(
            title=title,
            description=f"AI-generated {payload.assessment_type} on {payload.topic}",
            assessment_type=payload.assessment_type,
            time_limit_minutes=payload.time_limit_minutes,
            max_score=payload.max_score,
            passing_score=payload.passing_score,
            questions=questions_json,
            is_active=True,
            is_published=True,
        )
    elif payload.assessment_type == "code":
        assessment = Assessment(
            title=generated.get("title", title),
            description=generated.get("description", f"Coding challenge on {payload.topic}"),
            assessment_type="code",
            time_limit_minutes=payload.time_limit_minutes,
            max_score=payload.max_score,
            passing_score=payload.passing_score,
            starter_code=generated.get("starter_code", ""),
            test_cases=json.dumps(generated.get("test_cases", [])),
            language=generated.get("language", "python"),
            is_active=True,
            is_published=True,
        )
    else:
        assessment = Assessment(
            title=generated.get("title", title),
            description=generated.get("description", f"Assignment on {payload.topic}"),
            assessment_type="assignment",
            time_limit_minutes=payload.time_limit_minutes,
            max_score=payload.max_score,
            passing_score=payload.passing_score,
            rubric=json.dumps(generated.get("rubric", [])),
            is_active=True,
            is_published=True,
        )

    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return {
        "id": assessment.id,
        "title": assessment.title,
        "assessment_type": assessment.assessment_type,
        "message": "Assessment created successfully",
        "generated": generated,
    }


@router.get("/")
def list_assessments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    assessments = db.query(Assessment).filter(Assessment.is_active == True).all()
    return [_assessment_detail(a) for a in assessments]


@router.get("/my/pending")
def get_pending(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    submitted_ids = [
        s.assessment_id
        for s in db.query(Submission).filter(Submission.user_id == current_user.id).all()
    ]
    assessments = db.query(Assessment).filter(
        Assessment.is_active == True,
        ~Assessment.id.in_(submitted_ids) if submitted_ids else True,
    ).all()
    return [_assessment_detail(a) for a in assessments]


@router.get("/my/completed")
def get_completed(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    subs = db.query(Submission).filter(
        Submission.user_id == current_user.id,
        Submission.status.in_(["graded", "completed"]),
    ).all()
    result = []
    for s in subs:
        a = db.query(Assessment).filter(Assessment.id == s.assessment_id).first()
        if a:
            result.append({
                "id": str(a.id),
                "title": a.title,
                "description": a.description,
                "assessment_type": a.assessment_type,
                "fresher_id": None,
                "status": "graded",
                "score": s.score,
                "max_score": a.max_score,
                "passing_score": a.passing_score,
                "submitted_at": str(s.submitted_at) if s.submitted_at else None,
                "graded_at": str(s.graded_at) if s.graded_at else None,
                "feedback": s.feedback,
                "created_at": str(a.created_at) if a.created_at else "",
            })
    return result


@router.get("/{assessment_id}")
def get_assessment(assessment_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    a = db.query(Assessment).filter(Assessment.id == int(assessment_id)).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return _assessment_detail(a)


@router.post("/{assessment_id}/start")
def start_assessment(assessment_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    a = db.query(Assessment).filter(Assessment.id == int(assessment_id)).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")

    sub = Submission(
        assessment_id=a.id,
        user_id=current_user.id,
        submission_type=a.assessment_type,  # Keep original type (quiz, code, or assignment)
        status="in_progress",
        max_score=a.max_score,
        passing_score=a.passing_score,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return {"submission_id": str(sub.id), "status": "in_progress"}


@router.post("/submissions/{submission_id}/answers")
def submit_answers(submission_id: str, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sub = db.query(Submission).filter(Submission.id == int(submission_id)).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    sub.answers = json.dumps(data.get("answers", {}))
    sub.status = "submitted"
    db.commit()
    return {"status": "submitted", "submission_id": str(sub.id)}


def _sanitize_feedback(raw_feedback: dict) -> dict:
    """Sanitize feedback to ensure all list items are strings (not objects)."""
    def clean_list(l):
        if not isinstance(l, list): return []
        return [str(v) if isinstance(v, (dict, list)) else str(v) for v in l]

    return {
        "overall_comment": str(raw_feedback.get("overall_comment", raw_feedback.get("overall_assessment", raw_feedback.get("overall", raw_feedback.get("feedback", ""))))),
        "strengths": clean_list(raw_feedback.get("strengths", [])),
        "weaknesses": clean_list(raw_feedback.get("weaknesses", raw_feedback.get("areas_for_improvement", []))),
        "suggestions": clean_list(raw_feedback.get("suggestions", raw_feedback.get("developmental_recommendations", []))),
        "missing_points": clean_list(raw_feedback.get("missing_points", [])),
        "errors": clean_list(raw_feedback.get("errors", [])),
        "improvements": clean_list(raw_feedback.get("improvements", [])),
        "risk_level": str(raw_feedback.get("risk_level", "low")),
        "risk_factors": clean_list(raw_feedback.get("risk_factors", [])),
        "accuracy_score": raw_feedback.get("accuracy_score") if raw_feedback.get("accuracy_score") not in [None, ""] else None,
        "test_score": raw_feedback.get("test_score") if raw_feedback.get("test_score") not in [None, ""] else None,
        "style_score": raw_feedback.get("style_score") if raw_feedback.get("style_score") not in [None, ""] else None,
        "rubric_scores": {
            str(k): (v if isinstance(v, (int, float)) else 0)
            for k, v in (raw_feedback.get("rubric_scores", {}) if isinstance(raw_feedback.get("rubric_scores"), dict) else {}).items()
        }
    }


@router.get("/submissions/{submission_id}/results")
def get_results(submission_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sub = db.query(Submission).filter(Submission.id == int(submission_id)).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    feedback = {}
    if sub.feedback:
        try:
            raw = json.loads(sub.feedback)
            feedback = _sanitize_feedback(raw) if isinstance(raw, dict) else {"overall_comment": str(raw)}
        except Exception:
            feedback = {"overall_comment": str(sub.feedback)}
    test_results = []
    if sub.test_results:
        try:
            test_results = json.loads(sub.test_results)
        except Exception:
            pass
    return {
        "submission_id": str(sub.id),
        "assessment_id": str(sub.assessment_id),
        "score": sub.score,
        "max_score": sub.max_score,
        "pass_status": sub.pass_status,
        "status": sub.status,
        "feedback": feedback,
        "test_results": test_results,
        "submitted_at": str(sub.submitted_at) if sub.submitted_at else None,
        "graded_at": str(sub.graded_at) if sub.graded_at else None,
    }


@router.get("/{assessment_id}/latest-result")
def get_latest_result(assessment_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get the latest completed submission result for a specific assessment."""
    sub = db.query(Submission).filter(
        Submission.user_id == current_user.id,
        Submission.assessment_id == int(assessment_id),
        Submission.status.in_(["completed", "graded"])
    ).order_by(Submission.submitted_at.desc()).first()

    if not sub:
        raise HTTPException(status_code=404, detail="No completed submission found for this assessment")

    feedback = {}
    if sub.feedback:
        try:
            raw = json.loads(sub.feedback)
            feedback = _sanitize_feedback(raw) if isinstance(raw, dict) else {"overall_comment": str(raw)}
        except Exception:
            feedback = {"overall_comment": str(sub.feedback)}
            
    test_results = []
    if sub.test_results:
        try:
            test_results = json.loads(sub.test_results)
        except Exception:
            pass

    return {
        "submission_id": str(sub.id),
        "assessment_id": str(sub.assessment_id),
        "score": sub.score,
        "max_score": sub.max_score,
        "pass_status": sub.pass_status,
        "status": sub.status,
        "feedback": feedback,
        "test_results": test_results,
        "submitted_at": str(sub.submitted_at) if sub.submitted_at else None,
        "graded_at": str(sub.graded_at) if sub.graded_at else None,
    }


def _assessment_detail(a: Assessment) -> dict:
    def _parse_json(val):
        if not val:
            return []
        try:
            return json.loads(val)
        except Exception:
            return []

    def _select_daily_questions(questions: list, count: int, assessment_id: int):
        if not questions:
            return []
        if len(questions) <= count:
            return questions
        day_seed = int(date.today().strftime("%Y%m%d")) + int(assessment_id)
        rng = random.Random(day_seed)
        return rng.sample(questions, count)

    questions = _parse_json(a.questions)
    if a.assessment_type == "quiz":
        questions = _select_daily_questions(questions, 5, a.id)

    return {
        "id": a.id,
        "title": a.title,
        "description": a.description or "",
        "assessment_type": a.assessment_type,
        "time_limit_minutes": a.time_limit_minutes,
        "max_score": a.max_score,
        "passing_score": a.passing_score,
        "max_attempts": a.max_attempts,
        "instructions": a.instructions,
        "module_id": a.module_id,
        "weight": a.weight,
        "rubric": _parse_json(a.rubric) if a.rubric else {},
        "starter_code": a.starter_code,
        "test_cases": _parse_json(a.test_cases),
        "questions": questions,
        "skills_assessed": _parse_json(a.skills_assessed),
        "language": a.language,
        "is_active": a.is_active,
        "is_published": a.is_published,
        "available_from": a.available_from,
        "available_until": a.available_until,
        "created_at": str(a.created_at) if a.created_at else "",
    }

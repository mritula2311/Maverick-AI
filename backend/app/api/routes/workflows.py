import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.assessment import Assessment, Submission

router = APIRouter(tags=["Workflows"])


@router.post("/submit")
def submit_workflow(data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    assessment_id = data.get("assessment_id")
    submission_type = data.get("submission_type", "quiz") 
    code = data.get("code") or data.get("submission_text") or data.get("content")
    language = data.get("language", "python")
    answers = data.get("answers")

    print(f"[SUBMIT] User {current_user.email} (ID: {current_user.id}) submitting {submission_type} for assessment {assessment_id}")

    assessment = db.query(Assessment).filter(Assessment.id == int(assessment_id)).first()
    if not assessment:
        print(f"[SUBMIT ERROR] Assessment {assessment_id} not found")
        raise HTTPException(status_code=404, detail="Assessment not found")

    trace_id = str(uuid.uuid4())
    print(f"[SUBMIT] Generated trace_id: {trace_id}")

    sub = Submission(
        assessment_id=int(assessment_id),
        user_id=current_user.id,
        submission_type=submission_type,
        code=code,
        language=language,
        answers=json.dumps(answers) if answers else None,
        status="grading",
        trace_id=trace_id,
        max_score=assessment.max_score,
        passing_score=assessment.passing_score,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    print(f"[SUBMIT] Created submission ID: {sub.id}, trace_id: {trace_id}, initial status: {sub.status}")

    # Run grading synchronously with specialized HR-focused evaluators
    # Only quiz and assignment types supported (code challenges removed)
    try:
        # Select appropriate evaluator based on assessment type
        if assessment.assessment_type == "quiz":
            from app.agents.quiz_evaluator_agent import QuizEvaluatorAgent
            agent = QuizEvaluatorAgent()
            print(f"[SUBMIT] Starting QUIZ evaluation for submission {sub.id} with HR assessment framework...")
        elif assessment.assessment_type == "assignment":
            from app.agents.assignment_evaluator_agent import AssignmentEvaluatorAgent
            agent = AssignmentEvaluatorAgent()
            print(f"[SUBMIT] Starting ASSIGNMENT evaluation for submission {sub.id} with professional document assessment...")
        else:
            # Fallback to generic agent for unknown types
            from app.agents.assessment_agent import AssessmentAgent
            agent = AssessmentAgent()
            print(f"[SUBMIT] Starting grading for submission {sub.id} with generic agent (type: {assessment.assessment_type})...")
        
        result = agent.evaluate(db, sub, assessment)
        
        # Refresh submission to get updated status
        db.refresh(sub)
        
        print(f"[SUBMIT] ✅ Grading complete!")
        print(f"[SUBMIT]   - Score: {sub.score}/{sub.max_score}")
        print(f"[SUBMIT]   - Pass Status: {sub.pass_status}")
        print(f"[SUBMIT]   - Status: {sub.status}")
        print(f"[SUBMIT]   - Feedback length: {len(sub.feedback) if sub.feedback else 0} chars")

        # Automatically update Fresher Profile
        try:
            from app.models.fresher import Fresher
            from app.agents.profile_agent import ProfileAgent
            
            fresher = db.query(Fresher).filter(Fresher.user_id == current_user.id).first()
            if fresher and sub.status == "completed":
                print(f"[SUBMIT] Updating profile for fresher strategy...")
                profile_agent = ProfileAgent()
                profile_agent.update_after_assessment(db, fresher, sub)
                print(f"[SUBMIT] ✅ Profile updated successfully (Skills & Progress)")
        except Exception as pe:
            print(f"[SUBMIT WARNING] Profile update failed: {pe}")
            # Don't fail the whole request just because profile update failed

    except Exception as e:
        print(f"[SUBMIT ERROR] Grading failed: {e}")
        import traceback
        traceback.print_exc()
        sub.status = "failed"
        sub.feedback = json.dumps({"error": str(e)})
        db.commit()
        db.refresh(sub)

    response = {
        "submission_id": str(sub.id),
        "trace_id": trace_id,
        "status": sub.status,  # Return actual status (completed/graded)
    }
    print(f"[SUBMIT] Returning response: {response}")
    return response


@router.get("/status/{trace_id}")
def get_workflow_status(trace_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    print(f"[STATUS] Checking status for trace_id: {trace_id}, user: {current_user.email}")
    
    try:
        sub = db.query(Submission).filter(Submission.trace_id == trace_id).first()
        if not sub:
            print(f"[STATUS ERROR] Workflow not found for trace_id: {trace_id}")
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        print(f"[STATUS] Found submission {sub.id}, status: {sub.status}, score: {sub.score}")

        feedback = {}
        if sub.feedback:
            try:
                raw_feedback = json.loads(sub.feedback)
                if isinstance(raw_feedback, dict):
                    # Ensure no nested objects for keys that React renders as children
                    def clean_val(v):
                        if isinstance(v, (dict, list)): return str(v)
                        return v

                    def clean_list(l):
                        if not isinstance(l, list): return []
                        return [str(v) if isinstance(v, (dict, list)) else v for v in l]

                    feedback = {
                        "overall_comment": str(raw_feedback.get("overall_comment", raw_feedback.get("overall_assessment", raw_feedback.get("overall", raw_feedback.get("feedback", ""))))),
                        "strengths": clean_list(raw_feedback.get("strengths", [])),
                        "weaknesses": clean_list(raw_feedback.get("weaknesses", [])),
                        "suggestions": clean_list(raw_feedback.get("suggestions", [])),
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
                else:
                    feedback = {"overall_comment": str(raw_feedback)}
            except Exception:
                feedback = {"overall_comment": str(sub.feedback)}

        test_results = []
        if sub.test_results:
            try:
                test_results = json.loads(sub.test_results)
            except Exception:
                pass

        # Deep Recursive Sanitizer to prevent "Object as React Child"
        def make_safe(obj):
            if obj is None: return ""
            if isinstance(obj, (int, float, bool)): return obj
            if isinstance(obj, str): return obj
            if isinstance(obj, list): return [make_safe(item) for item in obj]
            if isinstance(obj, dict):
                return {str(k): make_safe(v) for k, v in obj.items()}
            return str(obj)

        # Safe float conversion
        score_val = float(sub.score) if sub.score is not None else 0.0
        max_score_val = float(sub.max_score) if sub.max_score is not None else 100.0
        percentage_val = (score_val / max_score_val * 100) if max_score_val > 0 else 0.0
        
        pass_status_val = str(sub.pass_status) if sub.pass_status in ["pass", "fail"] else None

        state = {
            "submission_id": str(sub.id),
            "assessment_id": str(sub.assessment_id),
            "score": score_val,
            "max_score": max_score_val,
            "percentage": percentage_val,
            "pass_status": pass_status_val,
            "passed": pass_status_val == "pass",
            "feedback": make_safe(feedback),
            "test_results": make_safe(test_results),
            "rubric_scores": make_safe(feedback.get("rubric_scores", {
                "correctness": float(feedback.get("accuracy_score") or 0) if isinstance(feedback.get("accuracy_score"), (int, float)) else 0,
                "quality": 0,
            })),
            "risk_level": str(feedback.get("risk_level", "low")),
            "risk_factors": make_safe(feedback.get("risk_factors", [])),
        }

        print(f"[STATUS] Returning response with status={sub.status}")
        return {
            "trace_id": trace_id,
            "status": sub.status,
            "state": state,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[STATUS ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing status: {str(e)}")


@router.get("/fresher-dashboard")
def fresher_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.api.routes.freshers import _build_dashboard
    from app.models.fresher import Fresher
    fresher = db.query(Fresher).filter(Fresher.user_id == current_user.id).first()
    if not fresher:
        return {"error": "No fresher profile found"}
    return _build_dashboard(db, fresher, current_user)


@router.get("/manager-dashboard")
def manager_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.api.routes.analytics import get_dashboard
    return get_dashboard(db=db, current_user=current_user)

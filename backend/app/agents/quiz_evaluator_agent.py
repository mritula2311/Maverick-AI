"""
Quiz Evaluation Agent - Corporate HR Style
Evaluates quiz submissions with professional, constructive feedback
Focuses on knowledge assessment and learning guidance
"""

import json
import random
from datetime import datetime, timezone, date
from typing import Dict, List, Optional, Any
from app.agents.base import BaseAgent
from app.models.assessment import Assessment, Submission
from app.config import settings


class QuizEvaluatorAgent(BaseAgent):
    """
    Specialized agent for evaluating quiz submissions.
    Evaluates with the mindset of a corporate HR professional:
    - Professional and constructive
    - Focuses on knowledge gaps and development areas
    - Provides actionable learning recommendations
    - Fully configurable and updatable parameters
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(model_name=settings.OLLAMA_CODE_MODEL)
        self.config = self._load_default_config()
        if config:
            self.config.update(config)
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration parameters"""
        return {
            "daily_question_count": 5,
            "default_question_points": 10,
            "default_passing_score": 70,
            "competency_thresholds": {
                "exceeds": 90,
                "meets": 70,
                "developing": 50,
                "needs_improvement": 0
            },
            "feedback_templates": {
                "exceeds": "Outstanding performance demonstrating exceptional technical knowledge and comprehension.",
                "meets": "Solid performance demonstrating good understanding of core concepts with minor areas for improvement.",
                "developing": "Developing competency with foundational knowledge present but requiring focused skill development.",
                "needs_improvement": "Performance indicates significant knowledge gaps requiring immediate training and development intervention."
            },
            "max_incorrect_details": 5,
            "max_feedback_errors": 4,
            "enable_llm_feedback": True,
            "fallback_on_llm_error": True
        }
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update agent configuration parameters"""
        self.config.update(new_config)
        print(f"[QuizEvaluatorAgent] [OK] Configuration updated: {list(new_config.keys())}")
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.config.copy()

    def execute(self, db, submission: Submission, assessment: Assessment):
        return self.evaluate(db, submission, assessment)

    def evaluate(self, db, submission: Submission, assessment: Assessment):
        """Main evaluation method for quiz submissions"""

        def normalize_answer(value):
            text = str(value or "").strip().lower()
            if text in ["true", "t", "yes", "1"]:
                return "true"
            if text in ["false", "f", "no", "0"]:
                return "false"
            return text

        def select_daily_questions(question_list, count, assessment_id):
            if not question_list or len(question_list) <= count:
                return question_list
            day_seed = int(date.today().strftime("%Y%m%d")) + int(assessment_id)
            rng = random.Random(day_seed)
            return rng.sample(question_list, count)
        
        # Parse answers
        answers = {}
        if submission.answers:
            try:
                answers = json.loads(submission.answers)
            except Exception:
                pass

        # Parse questions for correct answers
        questions = []
        if assessment.questions:
            try:
                questions = json.loads(assessment.questions)
            except Exception:
                pass

        if assessment.assessment_type == "quiz":
            daily_count = self.config.get("daily_question_count", 5)
            questions = select_daily_questions(questions, daily_count, assessment.id)

        # Auto-grade against correct answers
        total_points = 0
        earned_points = 0
        incorrect_questions = []
        
        for q_index, q in enumerate(questions):
            q_id_raw = q.get("id", "")
            q_id = str(q_id_raw).strip()
            points = q.get("points", self.config.get("default_question_points", 10))
            total_points += points
            correct = q.get("correct_answer", "")

            candidate_keys = [
                q_id_raw,
                q_id,
                f"q{q_index + 1}",
                str(q_index),
                str(q_index + 1),
            ]

            user_answer = ""
            matched_key = None
            for key in candidate_keys:
                if key in answers:
                    user_answer = answers.get(key, "")
                    matched_key = key
                    break

            print(
                f"[QuizEvaluatorAgent] Q{q_index + 1} id={q_id} key={matched_key} "
                f"user={normalize_answer(user_answer)!r} correct={normalize_answer(correct)!r}"
            )
            
            if normalize_answer(user_answer) == normalize_answer(correct):
                earned_points += points
            else:
                # Store incorrect question with details for HR feedback
                incorrect_questions.append({
                    "question": q.get("question", "N/A"),
                    "correct_answer": correct,
                    "user_answer": user_answer,
                    "topic": q.get("topic", "General"),
                    "points": points
                })

        # Calculate score
        score = (earned_points / total_points * 100) if total_points > 0 else 0
        passing_threshold = assessment.passing_score or self.config.get("default_passing_score", 70)
        pass_status = "pass" if score >= passing_threshold else "fail"

        # Generate HR-style feedback using LLM (if enabled)
        if self.config.get("enable_llm_feedback", True):
            hr_feedback = self._generate_hr_feedback(
                assessment_title=assessment.title,
                score=score,
                total_questions=len(questions),
                incorrect_count=len(incorrect_questions),
                incorrect_details=incorrect_questions[:self.config.get("max_incorrect_details", 5)],
                passing_score=passing_threshold
            )
        else:
            hr_feedback = self._get_fallback_feedback(score, len(incorrect_questions), len(questions))

        # Normalize to the frontend's expected feedback schema
        feedback = {
            "overall_comment": hr_feedback.get("overall_assessment") or hr_feedback.get("overall_comment") or "Assessment evaluated successfully.",
            "strengths": hr_feedback.get("strengths", []),
            "weaknesses": hr_feedback.get("development_areas", hr_feedback.get("weaknesses", [])),
            "suggestions": hr_feedback.get("recommended_actions", hr_feedback.get("suggestions", [])),
            "missing_points": [q.get("question", "") for q in incorrect_questions[:self.config.get("max_feedback_errors", 4)]],
            "errors": [
                f"For '{q.get('question', 'question')}', expected '{q.get('correct_answer', '')}' but got '{q.get('user_answer', '')}'."
                for q in incorrect_questions[:self.config.get("max_feedback_errors", 4)]
            ],
            "improvements": hr_feedback.get("recommended_actions", hr_feedback.get("improvements", [])),
            "accuracy_score": round(score, 2),
            "risk_level": hr_feedback.get("risk_level", "low" if score >= passing_threshold else "medium"),
        }

        # Update submission
        submission.score = round(score, 2)
        submission.pass_status = pass_status
        submission.status = "completed"
        submission.feedback = json.dumps(feedback)
        submission.graded_at = datetime.now(timezone.utc)
        db.commit()

        print(f"[QuizEvaluatorAgent] [OK] Evaluated quiz: {score:.1f}% ({pass_status})")

        return {
            "score": round(score, 2),
            "pass_status": pass_status,
            "feedback": feedback
        }

    def _generate_hr_feedback(self, assessment_title, score, total_questions, incorrect_count, incorrect_details, passing_score):
        """Generate professional HR-style feedback using LLM"""
        
        # Construct HR evaluation prompt
        prompt = f"""You are a Corporate HR Learning & Development Specialist evaluating a technical assessment.

Assessment: {assessment_title}
Score Achieved: {score:.1f}%
Passing Threshold: {passing_score}%
Questions Answered Correctly: {total_questions - incorrect_count}/{total_questions}

EVALUATION GUIDELINES:
- Be professional, constructive, and supportive
- Focus on competency development and growth potential
- Identify specific knowledge gaps with actionable recommendations
- Balance recognition of strengths with constructive improvement areas
- Use corporate HR terminology (competencies, development areas, growth opportunities)

"""

        # Add incorrect question context if any
        if incorrect_details:
            prompt += "\nAREAS REQUIRING ATTENTION:\n"
            for i, q in enumerate(incorrect_details, 1):
                prompt += f"\n{i}. Topic: {q['topic']}"
                prompt += f"\n   Question: {q['question'][:100]}..."
                prompt += f"\n   Expected: {q['correct_answer']}"
                prompt += f"\n   Response: {q['user_answer']}\n"

        prompt += """
Provide your evaluation as a JSON object with this structure:
{
  "overall_assessment": "2-3 sentence professional summary of performance",
  "competency_level": "Exceeds Expectations | Meets Expectations | Developing | Needs Improvement",
  "strengths": ["strength 1 (if score > 60)", "strength 2"],
  "development_areas": ["area 1 with specific topic", "area 2"],
  "recommended_actions": ["specific resource or training recommendation 1", "recommendation 2", "recommendation 3"],
  "hr_notes": "Brief note for HR record about candidate's technical readiness"
}

IMPORTANT: Return ONLY valid JSON, no additional text or markdown."""

        try:
            response = self.call_llm(prompt)
            feedback = self._extract_json_from_llm_response(response)
            
            # Validate required fields
            required_fields = ["overall_assessment", "competency_level", "development_areas", "recommended_actions"]
            if all(field in feedback for field in required_fields):
                return feedback
            else:
                print(f"[QuizEvaluatorAgent] [WARN] LLM response missing required fields")
                if self.config.get("fallback_on_llm_error", True):
                    return self._get_fallback_feedback(score, incorrect_count, total_questions)
                else:
                    raise ValueError("LLM feedback validation failed")
                
        except Exception as e:
            print(f"[QuizEvaluatorAgent] [ERR] LLM feedback error: {e}")
            if self.config.get("fallback_on_llm_error", True):
                return self._get_fallback_feedback(score, incorrect_count, total_questions)
            else:
                raise e

    def _extract_json_from_llm_response(self, llm_response: str) -> dict:
        """Extract JSON from LLM response, handling markdown code blocks"""
        try:
            response_text = llm_response.strip()
            
            # Remove markdown code blocks
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                if end > start:
                    response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                if end > start:
                    response_text = response_text[start:end].strip()
            
            # Extract JSON object
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                response_text = response_text[json_start:json_end]
            
            parsed = json.loads(response_text)
            return parsed
        except Exception as e:
            print(f"[QuizEvaluatorAgent] [ERR] JSON parse error: {e}")
            return {}

    def _get_fallback_feedback(self, score, incorrect_count, total_questions):
        """Generate fallback feedback if LLM fails"""
        thresholds = self.config.get("competency_thresholds", {})
        templates = self.config.get("feedback_templates", {})
        
        if score >= thresholds.get("exceeds", 90):
            competency = "Exceeds Expectations"
            assessment = templates.get("exceeds", "Outstanding performance demonstrating exceptional technical knowledge and comprehension.")
        elif score >= thresholds.get("meets", 70):
            competency = "Meets Expectations"
            assessment = templates.get("meets", "Solid performance demonstrating good understanding of core concepts with minor areas for improvement.")
        elif score >= thresholds.get("developing", 50):
            competency = "Developing"
            assessment = templates.get("developing", "Developing competency with foundational knowledge present but requiring focused skill development.")
        else:
            competency = "Needs Improvement"
            assessment = templates.get("needs_improvement", "Performance indicates significant knowledge gaps requiring immediate training and development intervention.")

        passing_threshold = self.config.get("default_passing_score", 70)
        
        return {
            "overall_assessment": assessment,
            "competency_level": competency,
            "strengths": ["Completed assessment within time limit"] if score > thresholds.get("developing", 50) else [],
            "development_areas": [f"Review material for {incorrect_count} questions answered incorrectly"],
            "recommended_actions": [
                "Schedule 1:1 with technical mentor",
                "Complete targeted learning modules",
                "Review core concepts before proceeding"
            ],
            "hr_notes": f"Candidate achieved {score:.1f}% on technical assessment. {'Recommended for next stage.' if score >= passing_threshold else 'Additional training required before advancement.'}"
        }
    
    def update_feedback_templates(self, templates: Dict[str, str]) -> None:
        """Update feedback templates for different competency levels"""
        if "feedback_templates" not in self.config:
            self.config["feedback_templates"] = {}
        self.config["feedback_templates"].update(templates)
        print(f"[QuizEvaluatorAgent] [OK] Updated feedback templates: {list(templates.keys())}")
    
    def update_competency_thresholds(self, thresholds: Dict[str, float]) -> None:
        """Update scoring thresholds for competency levels"""
        if "competency_thresholds" not in self.config:
            self.config["competency_thresholds"] = {}
        self.config["competency_thresholds"].update(thresholds)
        print(f"[QuizEvaluatorAgent] [OK] Updated competency thresholds: {thresholds}")
    
    def update_llm_prompt_template(self, prompt_template: str) -> None:
        """Update the LLM prompt template for generating feedback"""
        self.config["custom_llm_prompt"] = prompt_template
        print(f"[QuizEvaluatorAgent] [OK] Updated LLM prompt template")
    
    def get_evaluation_stats(self) -> Dict[str, Any]:
        """Get current evaluation statistics and configuration"""
        return {
            "config": self.config,
            "model_name": self.model_name,
            "version": "2.0-updatable",
            "features": [
                "Dynamic configuration",
                "Updatable feedback templates",
                "Configurable scoring thresholds",
                "Custom LLM prompts",
                "Fallback evaluation system"
            ]
        }

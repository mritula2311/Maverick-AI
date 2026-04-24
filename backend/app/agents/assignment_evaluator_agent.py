"""
Assignment Evaluation Agent - Corporate HR Document/Project Assessment Style
Evaluates written assignments and project submissions
Focuses on communication skills, depth of analysis, and professional presentation
"""

import json
from datetime import datetime, timezone
from app.agents.base import BaseAgent
from app.models.assessment import Assessment, Submission
from app.config import settings


class AssignmentEvaluatorAgent(BaseAgent):
    """
    Specialized agent for evaluating written assignments and project submissions.
    Evaluates with the mindset of a corporate HR evaluator:
    - Assesses communication and documentation skills
    - Evaluates depth of technical understanding
    - Reviews professional presentation and structure
    - Provides comprehensive developmental feedback
    """

    def __init__(self):
        super().__init__(model_name=settings.OLLAMA_CODE_MODEL)

    def execute(self, db, submission: Submission, assessment: Assessment):
        return self.evaluate(db, submission, assessment)

    def evaluate(self, db, submission: Submission, assessment: Assessment):
        """Main evaluation method for assignment submissions"""
        
        submission_text = submission.code or ""
        
        # Parse rubric if available
        rubric = {}
        if assessment.rubric:
            try:
                rubric = json.loads(assessment.rubric)
            except Exception:
                pass

        # Generate comprehensive HR-style feedback using LLM
        feedback = self._generate_hr_assignment_feedback(
            assessment_title=assessment.title,
            description=assessment.description or "",
            submission_text=submission_text,
            rubric=rubric,
            max_score=assessment.max_score or 100,
            passing_score=assessment.passing_score or 70
        )

        # Extract score from feedback
        score = feedback.get("score", 75)  # Default to 75 if not provided
        pass_status = "pass" if score >= (assessment.passing_score or 70) else "fail"

        # Update submission
        submission.score = round(score, 2)
        submission.pass_status = pass_status
        submission.status = "completed"
        submission.feedback = json.dumps(feedback)
        submission.graded_at = datetime.now(timezone.utc)

        # Record assignment history so the fresher history view has versioned attempts.
        try:
            from app.models.certification import AssignmentHistory
            from app.models.fresher import Fresher

            fresher_obj = db.query(Fresher).filter(Fresher.user_id == submission.user_id).first()
            fresher_id = fresher_obj.id if fresher_obj else None

            latest = db.query(AssignmentHistory).filter(
                AssignmentHistory.submission_id == submission.id
            ).order_by(AssignmentHistory.version.desc()).first()
            next_version = (latest.version + 1) if latest else 1

            history = AssignmentHistory(
                submission_id=submission.id,
                fresher_id=fresher_id,
                assessment_id=submission.assessment_id,
                version=next_version,
                content=submission_text,
                status=submission.status,
                score=submission.score,
                feedback=submission.feedback,
                submitted_at=submission.submitted_at,
                graded_at=submission.graded_at,
            )
            if fresher_id:
                db.add(history)
        except Exception as e:
            print(f"[AssignmentEvaluatorAgent] assignment history record failed: {e}")
        db.commit()

        print(f"[AssignmentEvaluatorAgent] ✓ Evaluated assignment: {score:.1f}% ({pass_status})")

        return {
            "score": round(score, 2),
            "pass_status": pass_status,
            "feedback": feedback
        }

    def _generate_hr_assignment_feedback(self, assessment_title, description, submission_text, rubric, max_score, passing_score):
        """Generate professional HR-style assignment feedback using LLM"""
        
        # Construct HR evaluation prompt
        prompt = f"""You are a Corporate HR Learning & Development Specialist evaluating a written assignment for professional communication, technical understanding, and documentation skills.

ASSIGNMENT DETAILS:
Title: {assessment_title}
Requirement: {description[:500]}
Maximum Score: {max_score}
Passing Threshold: {passing_score}

CANDIDATE'S SUBMISSION:
{submission_text[:2000]}  # First 2000 chars

EVALUATION CRITERIA:
"""

        if rubric:
            prompt += "Assessment Rubric:\n"
            for criterion, details in rubric.items():
                prompt += f"- {criterion}: {details}\n"
        else:
            prompt += """Standard Professional Assessment Criteria:
- Content Quality & Depth (30%): Technical accuracy, depth of analysis, completeness
- Communication & Clarity (25%): Writing quality, organization, clarity of expression
- Professional Presentation (20%): Structure, formatting, professionalism
- Critical Thinking (15%): Analysis, insights, problem-solving approach
- Practical Application (10%): Real-world relevance, actionable recommendations
"""

        prompt += """

HR EVALUATION FRAMEWORK:
Evaluate this submission as an HR professional assessing:
1. Professional Communication Skills - Can this individual document work effectively?
2. Technical Comprehension - Does the candidate understand the subject matter?
3. Attention to Detail - Is the work thorough and well-organized?
4. Business Readiness - Would this quality of work meet corporate standards?

Provide your evaluation as a JSON object:
{{
  "score": <number between 0-100>,
  "overall_assessment": "Professional 2-3 sentence summary of submission quality and competency demonstrated",
  "competency_rating": "Exceptional | Proficient | Adequate | Developing | Insufficient",
  "strengths": [
    "Specific strength in content or presentation 1",
    "strength 2",
    "strength 3"
  ],
  "areas_for_improvement": [
    "Specific area needing development 1 with actionable guidance",
    "area 2",
    "area 3"
  ],
  "content_analysis": {{
    "depth_of_understanding": "Assessment of technical depth, 1-2 sentences",
    "clarity_of_communication": "Assessment of writing and organization, 1-2 sentences",
    "professional_quality": "Assessment of presentation standards, 1-2 sentences"
  }},
  "developmental_recommendations": [
    "Specific training or resource recommendation 1",
    "recommendation 2",
    "recommendation 3"
  ],
  "business_readiness_notes": "Assessment of whether work meets professional corporate standards",
  "hr_recommendation": "Brief recommendation regarding candidate's documentation and communication competency"
}}

SCORING GUIDANCE:
- 90-100: Exceptional work exceeding professional standards
- 80-89: Proficient work meeting all requirements professionally
- 70-79: Adequate work meeting minimum standards with some gaps
- 60-69: Developing work with significant improvement needed
- Below 60: Insufficient quality requiring comprehensive revision

Be constructive, specific, and professional. Return ONLY valid JSON."""

        try:
            response = self.call_llm(prompt)
            feedback = self._extract_json_from_llm_response(response)
            
            # Validate required fields
            required_fields = ["score", "overall_assessment", "competency_rating", "areas_for_improvement"]
            if all(field in feedback for field in required_fields):
                # Ensure score is within bounds
                feedback["score"] = max(0, min(100, feedback.get("score", 75)))
                return feedback
            else:
                print(f"[AssignmentEvaluatorAgent] ⚠ LLM response missing required fields")
                return self._get_fallback_feedback(submission_text)
                
        except Exception as e:
            print(f"[AssignmentEvaluatorAgent] ✗ LLM feedback error: {e}")
            return self._get_fallback_feedback(submission_text)

    def _extract_json_from_llm_response(self, llm_response: str) -> dict:
        """Extract JSON from LLM response"""
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
            
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                response_text = response_text[json_start:json_end]
            
            return json.loads(response_text)
        except Exception as e:
            print(f"[AssignmentEvaluatorAgent] ✗ JSON parse error: {e}")
            return {}

    def _get_fallback_feedback(self, submission_text):
        """Generate fallback feedback if LLM fails"""
        
        # Basic heuristic assessment
        word_count = len(submission_text.split())
        
        if word_count > 500:
            score = 85
            rating = "Proficient"
            assessment = "Submission demonstrates good effort with comprehensive content. Professional presentation meets corporate documentation standards."
        elif word_count > 200:
            score = 75
            rating = "Adequate"
            assessment = "Submission meets basic requirements with adequate content coverage. Some areas could benefit from more depth and detail."
        elif word_count > 50:
            score = 60
            rating = "Developing"
            assessment = "Submission shows basic understanding but lacks sufficient depth and detail. Significant expansion and refinement needed."
        else:
            score = 45
            rating = "Insufficient"
            assessment = "Submission is incomplete and does not meet minimum requirements. Substantial additional work required."

        return {
            "score": score,
            "overall_assessment": assessment,
            "competency_rating": rating,
            "strengths": [
                "Submission completed within deadline",
                "Basic structure present"
            ] if word_count > 100 else ["Attempted the assignment"],
            "areas_for_improvement": [
                "Provide more detailed analysis and depth",
                "Improve professional presentation and formatting",
                "Include specific examples and evidence",
                "Enhance clarity and organization of content"
            ],
            "content_analysis": {
                "depth_of_understanding": "Basic concepts present but requires deeper technical analysis and comprehension.",
                "clarity_of_communication": "Communication is functional but would benefit from improved structure and clarity.",
                "professional_quality": "Presentation meets basic standards but should be enhanced for corporate environment."
            },
            "developmental_recommendations": [
                "Complete business writing and technical documentation course",
                "Review examples of professional technical reports",
                "Practice structured writing with clear sections and flow",
                "Seek feedback from mentor on documentation quality"
            ],
            "business_readiness_notes": f"{'Work demonstrates adequate documentation skills for entry-level role with mentorship.' if score >= 70 else 'Documentation skills require significant development before meeting corporate standards.'}",
            "hr_recommendation": f"Candidate scored {score}% on written assignment. {'Acceptable for role with standard training.' if score >= 70 else 'Recommend professional communication training program.'}"
        }

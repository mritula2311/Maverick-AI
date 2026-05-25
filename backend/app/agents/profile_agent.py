import json
from app.agents.base import BaseAgent
from app.models.fresher import Fresher, Skill
from app.models.assessment import Submission, Assessment


class ProfileAgent(BaseAgent):
    """The Librarian — maintains fresher skill profiles and tracks progress."""

    def __init__(self):
        super().__init__()

    def execute(self, db, fresher: Fresher, **kwargs):
        return self.get_profile_summary(db, fresher)

    def update_after_assessment(self, db, fresher: Fresher, submission: Submission):
        """Update skills after an assessment is graded."""
        assessment = db.query(Assessment).filter(Assessment.id == submission.assessment_id).first()
        if not assessment:
            return

        # Get skills assessed
        skills_assessed = []
        if assessment.skills_assessed:
            try:
                skills_assessed = json.loads(assessment.skills_assessed)
            except Exception:
                pass

        if not skills_assessed:
            skills_assessed = [assessment.title.split()[0] if assessment.title else "General"]

        # Update or create skill records
        for skill_name in skills_assessed:
            skill = db.query(Skill).filter(
                Skill.fresher_id == fresher.id,
                Skill.name == skill_name,
            ).first()

            if skill:
                # Weighted average with new score
                old_level = skill.level
                new_score = submission.score or 0
                skill.level = round((old_level * skill.assessments_count + new_score) / (skill.assessments_count + 1), 1)
                skill.assessments_count += 1
                skill.trend = "up" if skill.level > old_level else ("down" if skill.level < old_level else "stable")
            else:
                skill = Skill(
                    fresher_id=fresher.id,
                    name=skill_name,
                    category="Technical",
                    level=submission.score or 0,
                    trend="stable",
                    assessments_count=1,
                )
                db.add(skill)

        # Award achievement for excellence
        if submission.score and submission.score >= 90:
            from app.models.fresher import Achievement
            # skill_name is defined in the loop above, but we only award once per graded event
            achievement_title = f"High Scorer: {assessment.title}"
            existing_ach = db.query(Achievement).filter(
                Achievement.fresher_id == fresher.id,
                Achievement.title == achievement_title
            ).first()
            if not existing_ach:
                new_ach = Achievement(
                    fresher_id=fresher.id,
                    title=achievement_title,
                    icon="⭐",
                    description=f"Scored {submission.score}% on {assessment.title}"
                )
                db.add(new_ach)

        # Award badges based on skill performance
        self._check_and_award_badges(db, fresher, skills_assessed)

        # Update overall progress
        all_subs = db.query(Submission).filter(
            Submission.user_id == fresher.user_id,
            Submission.status == "completed",
        ).all()
        if all_subs:
            avg_score = sum(s.score or 0 for s in all_subs) / len(all_subs)
            fresher.overall_progress = min(round(avg_score, 1), 100)

        db.commit()

    def update_profile(self, db, fresher: Fresher, data: dict):
        """Manual profile update via agent."""
        for key, val in data.items():
            if key != "fresher_id" and hasattr(fresher, key):
                setattr(fresher, key, val)
        db.commit()
        return {"status": "updated", "agent": "ProfileAgent"}

    def get_profile_summary(self, db, fresher: Fresher):
        skills = db.query(Skill).filter(Skill.fresher_id == fresher.id).all()
        
        # Add a generative summary if enough data exists
        ai_summary = fresher.summary
        if not ai_summary and len(skills) >= 2:
            ai_summary = self.generate_fresher_summary(fresher, skills)
            fresher.summary = ai_summary
            db.commit()

        return {
            "fresher_id": str(fresher.id),
            "overall_progress": fresher.overall_progress,
            "risk_level": fresher.risk_level,
            "skills": [
                {"name": s.name, "level": s.level, "trend": s.trend}
                for s in skills
            ],
            "ai_summary": ai_summary or "Initializing skill analysis...",
            "agent": "ProfileAgent",
        }

    def _check_and_award_badges(self, db, fresher: Fresher, skills_assessed: list):
        """Check and award badges based on skill performance."""
        from app.models.badge import Badge, FresherBadge
        from datetime import datetime
        
        # Get all submissions for this fresher
        all_subs = db.query(Submission).filter(
            Submission.user_id == fresher.user_id,
            Submission.status == "completed",
        ).all()
        
        if not all_subs:
            return
        
        # Group submissions by skill
        skill_scores = {}
        for sub in all_subs:
            assessment = db.query(Assessment).filter(Assessment.id == sub.assessment_id).first()
            if assessment and assessment.skills_assessed:
                try:
                    skills = json.loads(assessment.skills_assessed) if isinstance(assessment.skills_assessed, str) else assessment.skills_assessed
                except Exception:
                    skills = []
                    
                for skill in skills:
                    if skill not in skill_scores:
                        skill_scores[skill] = []
                    if sub.score is not None:
                        skill_scores[skill].append(sub.score)
        
        # Get all available badges
        all_badges = db.query(Badge).all()
        
        # Check badge eligibility for each badge
        for badge in all_badges:
            should_award = False
            score_achieved = 0
            
            if badge.skill_name in skill_scores:
                # Skill-specific badge
                avg_skill_score = sum(skill_scores[badge.skill_name]) / len(skill_scores[badge.skill_name])
                if avg_skill_score >= badge.min_score:
                    should_award = True
                    score_achieved = avg_skill_score
            elif badge.skill_name == "General":
                # General badges based on overall scores
                all_scores = [sub.score for sub in all_subs if sub.score is not None]
                if all_scores:
                    avg_score = sum(all_scores) / len(all_scores)
                    if avg_score >= badge.min_score:
                        should_award = True
                        score_achieved = avg_score
            
            if should_award:
                # Check if badge already assigned
                existing = db.query(FresherBadge).filter(
                    FresherBadge.fresher_id == fresher.id,
                    FresherBadge.badge_id == badge.id
                ).first()
                
                if not existing:
                    fresher_badge = FresherBadge(
                        fresher_id=fresher.id,
                        badge_id=badge.id,
                        assessment_id=None,
                        score_achieved=round(score_achieved, 1),
                        earned_at=datetime.utcnow()
                    )
                    db.add(fresher_badge)
                    print(f"[ProfileAgent] [BADGE] Awarded badge '{badge.name}' to fresher {fresher.id} (score: {score_achieved:.1f})")

    def generate_fresher_summary(self, fresher: Fresher, skills: list):
        """Use LLM to generate a personalized skill portrait."""
        skill_data = [{"name": s.name, "level": s.level} for s in skills]
        prompt = f"""
        Analyze this fresher's technical profile and write a professional 2-sentence 'Skill Portrait'.
        Progress: {fresher.overall_progress}%
        Skills: {json.dumps(skill_data)}
        
        Focus on their strongest area and potential career trajectory within the company.
        """
        response = self.call_llm(prompt, system="You are an expert technical career coach.")
        return response.strip()

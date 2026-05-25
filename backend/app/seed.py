import json
from app.models.user import User
from app.models.fresher import Fresher, Skill, Achievement
from app.models.schedule import Schedule, ScheduleItem
from app.models.assessment import Assessment
from app.models.curriculum import Curriculum
from app.models.report import Alert
from app.core.security import get_password_hash


def seed_database(db):
    """Seed the database with test data for demo purposes."""
    # Check if already seeded
    if db.query(User).count() > 0:
        print("[Seed] Database already has data, skipping...")
        return
    print("[Seed] Seeding database with fresh data...")
    
    # Clear existing data for fresh seed
    try:
        from app.models.report import Alert
        from app.models.assessment import Submission
        from app.models.badge import FresherBadge, Badge
        from app.models.schedule_assessment import AssessmentSchedule
        from app.models.analytics import PerformanceAnalytics
        
        db.query(Alert).delete()
        db.query(Submission).delete()
        db.query(FresherBadge).delete()
        db.query(Badge).delete()
        db.query(AssessmentSchedule).delete()
        db.query(PerformanceAnalytics).delete()
        db.query(Achievement).delete()
        db.query(Skill).delete()
        db.query(ScheduleItem).delete()
        db.query(Schedule).delete()
        db.query(Assessment).delete()
        db.query(Curriculum).delete()
        db.query(Fresher).delete()
        db.query(User).delete()
        db.commit()
        print("[Seed] Cleared existing data")
    except Exception as e:
        print(f"[Seed] Warning during cleanup: {e}")
        db.rollback()

    # ========== USERS ==========
    users_data = [
        {"email": "alice@maverick.ai", "first_name": "Alice", "last_name": "Thompson", "role": "fresher", "department": "Engineering", "password": "password123"},
        {"email": "john@maverick.ai", "first_name": "John", "last_name": "Smith", "role": "fresher", "department": "Data Science", "password": "password123"},
        {"email": "bob@maverick.ai", "first_name": "Bob", "last_name": "Martinez", "role": "fresher", "department": "Engineering", "password": "password123"},
        {"email": "emily@maverick.ai", "first_name": "Emily", "last_name": "Davis", "role": "fresher", "department": "Engineering", "password": "password123"},
        {"email": "admin@maverick.ai", "first_name": "Admin", "last_name": "User", "role": "admin", "department": "IT", "password": "admin123"},
        {"email": "manager@maverick.ai", "first_name": "James", "last_name": "Manager", "role": "manager", "department": "Engineering", "password": "password123"},
    ]
    users = []
    for u in users_data:
        user = User(
            email=u["email"],
            first_name=u["first_name"],
            last_name=u["last_name"],
            hashed_password=get_password_hash(u.get("password", "password123")),
            role=u["role"],
            department=u["department"],
        )
        db.add(user)
        users.append(user)
    db.flush()

    # ========== FRESHERS ==========
    freshers_data = [
        {"user_idx": 0, "employee_id": "MAV-2026-001", "week": 4, "progress": 78, "risk": "low", "risk_score": 12},      # Alice Thompson
        {"user_idx": 1, "employee_id": "MAV-2026-002", "week": 2, "progress": 35, "risk": "critical", "risk_score": 85},  # John Smith
        {"user_idx": 2, "employee_id": "MAV-2026-003", "week": 3, "progress": 75, "risk": "low", "risk_score": 15},      # Bob Martinez
        {"user_idx": 3, "employee_id": "MAV-2026-004", "week": 2, "progress": 48, "risk": "medium", "risk_score": 52},   # Emily Davis
    ]
    freshers = []
    for fd in freshers_data:
        fresher = Fresher(
            user_id=users[fd["user_idx"]].id,
            employee_id=fd["employee_id"],
            mentor_id=None,
            manager_id=None,
            join_date="2026-01-20",
            current_week=fd["week"],
            overall_progress=fd["progress"],
            risk_level=fd["risk"],
            risk_score=fd["risk_score"],
        )
        db.add(fresher)
        freshers.append(fresher)
    db.flush()

    # ========== SKILLS ==========
    skill_data = [
        ("React", "Programming", [78, 35, 75, 48]),
        ("Node.js", "Programming", [75, 30, 72, 45]),
        ("Python", "Programming", [80, 25, 78, 42]),
        ("Docker", "DevOps", [72, 35, 70, 50]),
        ("JavaScript", "Programming", [76, 28, 75, 50]),
        ("Communication", "Soft Skills", [85, 60, 82, 70]),
    ]
    for skill_name, category, levels in skill_data:
        for i, fresher in enumerate(freshers):
            skill = Skill(
                fresher_id=fresher.id,
                name=skill_name,
                category=category,
                level=levels[i],
                trend="up" if levels[i] > 50 else "down",
                assessments_count=3,
            )
            db.add(skill)

    # ========== ACHIEVEMENTS ==========
    achievements = [
        (0, "First Login", "🎯", "Completed first platform login"),              # Alice
        (0, "React Master", "⚛️", "Mastered React fundamentals"),
        (0, "3-Day Streak", "🔥", "3 consecutive days of learning"),
        (1, "First Login", "🎯", "Completed first platform login"),              # John
        (2, "Quick Learner", "⚡", "Completed module ahead of schedule"),         # Bob
        (3, "On Track", "✅", "Consistent learning progress"),                    # Emily
    ]
    for fidx, title, icon, desc in achievements:
        db.add(Achievement(fresher_id=freshers[fidx].id, title=title, icon=icon, description=desc))

    # ========== SCHEDULES (today) ==========
    from datetime import date
    today = date.today().isoformat()
    for i, fresher in enumerate(freshers):
        sched = Schedule(fresher_id=fresher.id, schedule_date=today, status="in_progress")
        db.add(sched)
        db.flush()
        items = [
            ("Python Fundamentals - Variables & Types", "reading", 60, "09:00", "Python", 
             "# Python Fundamentals\n\nPython is a versatile language... [Detailed Guide]", None, None),
            ("Quiz: Python Basics", "quiz", 30, "11:00", "Python",
             "Test your knowledge of Python basics.", None, 1),
            ("Video: Control Flow", "video", 45, "11:30", "Python",
             "Watch this video on if-statements and loops.", "https://www.youtube.com/embed/Zp5MuPOxlM0", None),
            ("Data Structures - Lists", "reading", 60, "14:00", "Data Structures",
             "# Python Lists\n\nLists are ordered collections...", None, None),
            ("Project: Contact Manager", "project", 90, "15:00", "Python",
             "Build a command-line contact manager.", None, None),
        ]
        for title, itype, dur, time, topic, content, url, aid in items:
            db.add(ScheduleItem(
                schedule_id=sched.id, title=title, description=f"Week {fresher.current_week} task",
                item_type=itype, duration_minutes=dur, status="pending", topic=topic, start_time=time,
                content=content, external_url=url, assessment_id=aid
            ))

    # ========== ASSESSMENTS ==========
    assessments_data = [
        {
            "title": "Python Basics Quiz",
            "description": "Test your knowledge of Python fundamentals including variables, data types, and basic operations.",
            "type": "quiz",
            "time_limit": 15,
            "max_score": 100,
            "passing_score": 60,
            "language": "python",
            "skills": ["Python", "Programming"],
            "questions": [
                {"id": "q1", "question": "What is the output of print(type(42))?", "type": "multiple_choice", "options": ["<class 'int'>", "<class 'str'>", "<class 'float'>", "<class 'number'>"], "correct_answer": "<class 'int'>", "points": 10},
                {"id": "q2", "question": "Python is a dynamically typed language.", "type": "true_false", "options": ["True", "False"], "correct_answer": "True", "points": 10},
                {"id": "q3", "question": "Which keyword is used to define a function in Python?", "type": "multiple_choice", "options": ["function", "def", "func", "define"], "correct_answer": "def", "points": 10},
                {"id": "q4", "question": "What does len([1, 2, 3]) return?", "type": "multiple_choice", "options": ["2", "3", "4", "1"], "correct_answer": "3", "points": 10},
                {"id": "q5", "question": "Python supports multiple inheritance.", "type": "true_false", "options": ["True", "False"], "correct_answer": "True", "points": 10},
                {"id": "q6", "question": "Which of the following data types is immutable in Python?", "type": "multiple_choice", "options": ["list", "dict", "set", "tuple"], "correct_answer": "tuple", "points": 10},
                {"id": "q7", "question": "What is the output of 3 * 'ab'?", "type": "multiple_choice", "options": ["ababab", "ab3", "aabbb", "ab ab ab"], "correct_answer": "ababab", "points": 10},
                {"id": "q8", "question": "Which keyword is used to handle exceptions in Python?", "type": "multiple_choice", "options": ["catch", "except", "error", "handle"], "correct_answer": "except", "points": 10},
                {"id": "q9", "question": "What does dict.get('key') return if 'key' does not exist in the dictionary?", "type": "multiple_choice", "options": ["KeyError", "None", "0", "False"], "correct_answer": "None", "points": 10},
                {"id": "q10", "question": "Which loop is best suited for iterating over elements of a list?", "type": "multiple_choice", "options": ["for", "while", "do-while", "loop"], "correct_answer": "for", "points": 10},
            ],
        },
        {
            "title": "SQL Fundamentals Quiz",
            "description": "Test your understanding of SQL queries, joins, and database concepts.",
            "type": "quiz",
            "time_limit": 15,
            "max_score": 100,
            "passing_score": 60,
            "language": None,
            "skills": ["SQL", "Database"],
            "questions": [
                {"id": "q1", "question": "Which SQL statement is used to retrieve data from a database?", "type": "multiple_choice", "options": ["GET", "SELECT", "FETCH", "RETRIEVE"], "correct_answer": "SELECT", "points": 20},
                {"id": "q2", "question": "In SQL, NULL represents an unknown or missing value, not zero.", "type": "true_false", "options": ["True", "False"], "correct_answer": "True", "points": 20},
                {"id": "q3", "question": "Which clause is used to filter results after GROUP BY?", "type": "multiple_choice", "options": ["WHERE", "HAVING", "FILTER", "GROUP FILTER"], "correct_answer": "HAVING", "points": 20},
                {"id": "q4", "question": "A PRIMARY KEY column can contain NULL values.", "type": "true_false", "options": ["True", "False"], "correct_answer": "False", "points": 20},
                {"id": "q5", "question": "Which JOIN returns all matching and non-matching rows from both tables?", "type": "multiple_choice", "options": ["INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL OUTER JOIN"], "correct_answer": "FULL OUTER JOIN", "points": 20},
            ],
        },
        {
            "title": "Software Architecture Report",
            "description": "Write a detailed report on software architecture principles including design patterns, scalability, and best practices. Explain how you would architect a real-world web application.",
            "type": "assignment",
            "time_limit": 60,
            "max_score": 100,
            "passing_score": 60,
            "language": None,
            "skills": ["Software Design", "Architecture", "Technical Writing"],
            "questions": [],
        },

    ]
    assessments = []
    for ad in assessments_data:
        a = Assessment(
            title=ad["title"],
            description=ad["description"],
            assessment_type=ad["type"],
            time_limit_minutes=ad["time_limit"],
            max_score=ad["max_score"],
            passing_score=ad["passing_score"],
            max_attempts=3,
            language=ad.get("language"),
            skills_assessed=json.dumps(ad.get("skills", [])),
            questions=json.dumps(ad.get("questions", [])),
            test_cases=json.dumps(ad.get("test_cases", [])),
            starter_code=ad.get("starter_code"),
            rubric=json.dumps(ad.get("rubric", {})),
            instructions=ad["description"],
        )
        db.add(a)
        assessments.append(a)

    # ========== CURRICULUM ==========
    curriculum = Curriculum(
        name="Software Engineering Foundation",
        description="12-week comprehensive training program for software engineering freshers.",
        duration_weeks=12,
        modules=json.dumps([
            {"id": "1", "name": "Python Fundamentals", "week_number": 1, "topics": ["Variables", "Data Types", "Control Flow", "Functions"], "learning_objectives": ["Write basic Python programs", "Understand data types"]},
            {"id": "2", "name": "Data Structures", "week_number": 2, "topics": ["Lists", "Tuples", "Dictionaries", "Sets"], "learning_objectives": ["Implement common data structures", "Choose appropriate structures"]},
            {"id": "3", "name": "OOP & Design Patterns", "week_number": 3, "topics": ["Classes", "Inheritance", "Polymorphism", "Design Patterns"], "learning_objectives": ["Design OOP solutions", "Apply design patterns"]},
            {"id": "4", "name": "Database & SQL", "week_number": 4, "topics": ["SQL Basics", "Joins", "Indexes", "ORM"], "learning_objectives": ["Write complex SQL queries", "Design database schemas"]},
            {"id": "5", "name": "Web Development", "week_number": 5, "topics": ["HTML/CSS", "JavaScript", "React Basics", "APIs"], "learning_objectives": ["Build responsive web pages", "Consume REST APIs"]},
            {"id": "6", "name": "Backend Development", "week_number": 6, "topics": ["FastAPI", "REST APIs", "Authentication", "Testing"], "learning_objectives": ["Build REST APIs", "Implement auth"]},
            {"id": "7", "name": "Git & DevOps", "week_number": 7, "topics": ["Git Workflow", "CI/CD", "Docker", "Deployment"], "learning_objectives": ["Manage code with Git", "Deploy applications"]},
            {"id": "8", "name": "System Design", "week_number": 8, "topics": ["Architecture", "Scalability", "Caching", "Load Balancing"], "learning_objectives": ["Design scalable systems"]},
            {"id": "9", "name": "Testing & QA", "week_number": 9, "topics": ["Unit Tests", "Integration Tests", "TDD", "Code Review"], "learning_objectives": ["Write comprehensive tests"]},
            {"id": "10", "name": "AI & ML Basics", "week_number": 10, "topics": ["ML Concepts", "Pandas", "Scikit-learn", "Model Evaluation"], "learning_objectives": ["Build basic ML models"]},
            {"id": "11", "name": "Capstone Project", "week_number": 11, "topics": ["Project Planning", "Implementation", "Demo"], "learning_objectives": ["Build end-to-end application"]},
            {"id": "12", "name": "Review & Certification", "week_number": 12, "topics": ["Final Assessment", "Portfolio", "Presentation"], "learning_objectives": ["Demonstrate readiness"]},
        ]),
    )
    db.add(curriculum)

    # Flush to ensure assessments and freshers have IDs
    db.flush()

    # ========== SUBMISSIONS (Assessment Attempts) ==========
    from app.models.assessment import Submission
    
    # Create submissions for each fresher on various assessments with realistic scores
    submission_data = [
        # Assessment 1: Python Basics Quiz
        {"assessment_idx": 0, "fresher_idx": 0, "score": 92, "status": "completed"},  # Alice
        {"assessment_idx": 0, "fresher_idx": 1, "score": 35, "status": "completed"},  # John
        {"assessment_idx": 0, "fresher_idx": 2, "score": 88, "status": "completed"},  # Bob
        {"assessment_idx": 0, "fresher_idx": 3, "score": 65, "status": "completed"},  # Emily

        # Assessment 2: SQL Fundamentals Quiz
        {"assessment_idx": 1, "fresher_idx": 0, "score": 90, "status": "completed"},  # Alice
        {"assessment_idx": 1, "fresher_idx": 1, "score": 50, "status": "completed"},  # John
        {"assessment_idx": 1, "fresher_idx": 2, "score": 82, "status": "completed"},  # Bob
        {"assessment_idx": 1, "fresher_idx": 3, "score": 72, "status": "completed"},  # Emily
    ]
    
    submissions = []
    for sub_data in submission_data:
        assessment = assessments[sub_data["assessment_idx"]]
        fresher = freshers[sub_data["fresher_idx"]]
        
        # Generate AI feedback via LLM agent
        score = sub_data["score"]
        from app.core.llm_client import llm_client

        prompt = f"""You are the MaverickAI Assessment Agent. Generate feedback JSON.

Assessment: {assessment.title}
Type: {assessment.assessment_type}
Score: {score}/100
Context: Seed data for demo; provide professional feedback.

Return JSON with:
- overall_comment (string)
- strengths (list)
- weaknesses (list)
- suggestions (list)
- missing_points (list)
- errors (list)
- improvements (list)
- risk_level (low/medium/high)
"""

        try:
            llm_response = llm_client.generate(prompt=prompt)
            feedback = json.loads(llm_response)
        except Exception:
            feedback = {
                "overall_comment": "Assessment completed with AI review.",
                "strengths": ["Submission recorded"],
                "weaknesses": ["Limited detail in seed data"],
                "suggestions": ["Review core concepts", "Practice similar problems"],
                "missing_points": ["Edge cases", "Input validation"],
                "errors": [],
                "improvements": ["Add clarity to approach", "Include explanations"],
                "risk_level": "low" if score >= 80 else ("medium" if score >= 60 else "high"),
            }
        
        submission = Submission(
            assessment_id=assessment.id,
            user_id=fresher.user_id,
            submission_type=assessment.assessment_type,
            score=sub_data["score"],
            max_score=assessment.max_score,
            passing_score=assessment.passing_score,
            pass_status="pass" if sub_data["score"] >= assessment.passing_score else "fail",
            status=sub_data["status"],
            feedback=json.dumps(feedback)
        )
        db.add(submission)
        submissions.append(submission)
    
    db.flush()

    # ========== ALERTS ==========
    alerts = [
        Alert(fresher_id=freshers[1].id, fresher_name="John Smith", risk_level="critical", risk_score=85, reason="Failed multiple assessments; Critical performance concerns", status="new"),
        Alert(fresher_id=freshers[3].id, fresher_name="Emily Davis", risk_level="medium", risk_score=52, reason="Below average engagement; 48% progress in weeks 1-2", status="new"),
    ]
    for a in alerts:
        db.add(a)

    db.commit()
    print("[Seed] Database seeded successfully!")
    print(f"  - {len(users_data)} users")
    print(f"  - {len(freshers_data)} freshers")
    print(f"  - {len(assessments_data)} assessments")
    print(f"  - {len(submission_data)} submissions")
    print(f"  - 1 curriculum")
    print(f"  - {len(alerts)} alerts")
    
    # ========== BADGES ==========
    from app.models.badge import Badge
    badges_data = [
        {"name": "Python Master", "description": "Scored 90+ on Python assessments", "skill_name": "Python", "min_score": 90, "color": "blue"},
        {"name": "Python Expert", "description": "Consistent excellence in Python", "skill_name": "Python", "min_score": 85, "color": "indigo"},
        {"name": "SQL Champion", "description": "Mastery of SQL fundamentals", "skill_name": "SQL", "min_score": 90, "color": "purple"},
        {"name": "SQL Pro", "description": "Advanced SQL skills demonstrated", "skill_name": "SQL", "min_score": 85, "color": "violet"},
        {"name": "Quick Learner", "description": "Fast improvement across assessments", "skill_name": "General", "min_score": 70, "color": "green"},
        {"name": "Consistent Performer", "description": "Reliable and steady performance", "skill_name": "General", "min_score": 75, "color": "teal"},
    ]
    
    for bd in badges_data:
        badge = Badge(
            name=bd["name"],
            description=bd["description"],
            skill_name=bd["skill_name"],
            min_score=bd["min_score"],
            color=bd["color"],
            icon_url=f"https://api.dicebear.com/7.x/badges/svg?seed={bd['name']}"
        )
        db.add(badge)
    
    db.commit()
    db.flush()
    print(f"  - {len(badges_data)} badges created")
    
    # ========== AUTO-ASSIGN BADGES BASED ON SCORES ==========
    from app.models.badge import FresherBadge
    from datetime import datetime
    
    # Get all badges
    all_badges = db.query(Badge).all()
    badge_assignments = 0
    
    for fresher in freshers:
        # Get submissions for this fresher
        fresher_submissions = [sub for sub in submissions if sub.user_id == fresher.user_id]
        
        # Group submissions by skill
        skill_scores = {}
        for sub in fresher_submissions:
            assessment = next((a for a in assessments if a.id == sub.assessment_id), None)
            if assessment and assessment.skills_assessed:
                skills = json.loads(assessment.skills_assessed) if isinstance(assessment.skills_assessed, str) else assessment.skills_assessed
                for skill in skills:
                    if skill not in skill_scores:
                        skill_scores[skill] = []
                    skill_scores[skill].append(sub.score)
        
        # Check badge eligibility for each badge
        for badge in all_badges:
            if badge.skill_name in skill_scores:
                avg_skill_score = sum(skill_scores[badge.skill_name]) / len(skill_scores[badge.skill_name])
                
                # Check if fresher qualifies for this badge
                if avg_skill_score >= badge.min_score:
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
                            score_achieved=avg_skill_score,
                            earned_at=datetime.utcnow()
                        )
                        db.add(fresher_badge)
                        badge_assignments += 1
            elif badge.skill_name == "General":
                # General badges based on overall scores
                all_scores = [sub.score for sub in fresher_submissions]
                if all_scores:
                    avg_score = sum(all_scores) / len(all_scores)
                    if avg_score >= badge.min_score:
                        existing = db.query(FresherBadge).filter(
                            FresherBadge.fresher_id == fresher.id,
                            FresherBadge.badge_id == badge.id
                        ).first()
                        
                        if not existing:
                            fresher_badge = FresherBadge(
                                fresher_id=fresher.id,
                                badge_id=badge.id,
                                assessment_id=None,
                                score_achieved=avg_score,
                                earned_at=datetime.utcnow()
                            )
                            db.add(fresher_badge)
                            badge_assignments += 1
    
    db.commit()
    db.flush()
    print(f"  - {badge_assignments} badges assigned to freshers")
    
    # ========== INITIALIZE ANALYTICS ==========
    from app.models.analytics import PerformanceAnalytics
    
    for fresher in freshers:
        # Get submissions for this fresher
        fresher_submissions = [sub for sub in submissions if sub.user_id == fresher.user_id]
        
        if fresher_submissions:
            total_score = sum(s.score for s in fresher_submissions)
            avg_score = total_score / len(fresher_submissions)
            
            quiz_subs = [s for s in fresher_submissions if s.submission_type == 'quiz']
            quiz_avg = sum(s.score for s in quiz_subs) / len(quiz_subs) if quiz_subs else 0
            
            passed = sum(1 for s in fresher_submissions if s.pass_status == 'pass')
            pass_rate = (passed / len(fresher_submissions) * 100)
            
            # Build skills breakdown
            skills_breakdown = {}
            for sub in fresher_submissions:
                assessment = next((a for a in assessments if a.id == sub.assessment_id), None)
                if assessment and assessment.skills_assessed:
                    skills = json.loads(assessment.skills_assessed) if isinstance(assessment.skills_assessed, str) else assessment.skills_assessed
                    for skill in skills:
                        skills_breakdown[skill] = skills_breakdown.get(skill, 0) + sub.score
            
            # Average skills
            for skill in skills_breakdown:
                skills_breakdown[skill] = skills_breakdown[skill] / len(quiz_subs) if quiz_subs else 0
            
            analytics = PerformanceAnalytics(
                fresher_id=fresher.id,
                overall_score=avg_score,
                quiz_average=quiz_avg,
                assessment_count=len(fresher_submissions),
                passed_count=passed,
                failed_count=len(fresher_submissions) - passed,
                pass_rate=pass_rate,
                skills_breakdown=skills_breakdown,
                risk_level=fresher.risk_level,
                risk_score=fresher.risk_score,
                engagement_score=75 + (avg_score / 100 * 25),  # Score-based engagement
            )
            db.add(analytics)
    
    db.commit()
    print(f"  - {len(freshers_data)} analytics initialized")

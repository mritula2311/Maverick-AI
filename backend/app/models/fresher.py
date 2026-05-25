from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Fresher(Base):
    __tablename__ = "freshers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    employee_id = Column(String, unique=True, nullable=False)
    mentor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    join_date = Column(String, nullable=False)
    onboarding_end_date = Column(String, nullable=True)
    current_week = Column(Integer, default=1)
    overall_progress = Column(Float, default=0.0)
    risk_level = Column(String, default="low")  # low, medium, high, critical
    risk_score = Column(Float, default=0.0)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    badges = relationship("FresherBadge", back_populates="fresher", cascade="all, delete-orphan")
    assessment_schedules = relationship("AssessmentSchedule", back_populates="fresher", cascade="all, delete-orphan")
    performance_analytics = relationship("PerformanceAnalytics", back_populates="fresher", uselist=False, cascade="all, delete-orphan")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fresher_id = Column(Integer, ForeignKey("freshers.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    level = Column(Float, default=0.0)
    trend = Column(String, default="stable")  # up, down, stable
    assessments_count = Column(Integer, default=0)


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fresher_id = Column(Integer, ForeignKey("freshers.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    icon = Column(String, default="🏆")
    description = Column(String, nullable=True)
    earned_at = Column(DateTime(timezone=True), server_default=func.now())

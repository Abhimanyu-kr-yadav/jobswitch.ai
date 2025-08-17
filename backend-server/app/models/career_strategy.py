"""
Career Strategy Models
Data models for career roadmaps, goals, milestones, and progress tracking
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum

from .base import Base



class GoalStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"


class MilestoneType(str, Enum):
    SKILL_DEVELOPMENT = "skill_development"
    EXPERIENCE_GAIN = "experience_gain"
    CERTIFICATION = "certification"
    NETWORKING = "networking"
    ROLE_TRANSITION = "role_transition"
    EDUCATION = "education"


class CareerRoadmap(Base):
    """Career roadmap database model"""
    __tablename__ = "career_roadmaps"
    
    id = Column(Integer, primary_key=True, index=True)
    roadmap_id = Column(String, unique=True, index=True)
    user_id = Column(String, ForeignKey("user_profiles.user_id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    current_role = Column(String, nullable=False)
    target_role = Column(String, nullable=False)
    target_industry = Column(String)
    target_company = Column(String)
    timeline_months = Column(Integer, nullable=False)
    progress_percentage = Column(Float, default=0.0)
    status = Column(String, default=GoalStatus.NOT_STARTED)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    target_date = Column(DateTime)
    
    # Relationships
    milestones = relationship("CareerMilestone", back_populates="roadmap", cascade="all, delete-orphan")
    goals = relationship("CareerGoal", back_populates="roadmap", cascade="all, delete-orphan")


class CareerGoal(Base):
    """Career goal database model"""
    __tablename__ = "career_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(String, unique=True, index=True)
    roadmap_id = Column(String, ForeignKey("career_roadmaps.roadmap_id"), nullable=False)
    user_id = Column(String, ForeignKey("user_profiles.user_id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String, nullable=False)  # skill, experience, networking, etc.
    priority = Column(Integer, default=1)  # 1=high, 2=medium, 3=low
    status = Column(String, default=GoalStatus.NOT_STARTED)
    progress_percentage = Column(Float, default=0.0)
    target_date = Column(DateTime)
    completion_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional metadata
    success_criteria = Column(JSON)  # List of criteria for goal completion
    resources_needed = Column(JSON)  # Resources required to achieve goal
    dependencies = Column(JSON)  # Other goals this depends on
    
    # Relationships
    roadmap = relationship("CareerRoadmap", back_populates="goals")
    milestones = relationship("CareerMilestone", back_populates="goal", cascade="all, delete-orphan")


class CareerMilestone(Base):
    """Career milestone database model"""
    __tablename__ = "career_milestones"
    
    id = Column(Integer, primary_key=True, index=True)
    milestone_id = Column(String, unique=True, index=True)
    roadmap_id = Column(String, ForeignKey("career_roadmaps.roadmap_id"), nullable=False)
    goal_id = Column(String, ForeignKey("career_goals.goal_id"))
    user_id = Column(String, ForeignKey("user_profiles.user_id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    milestone_type = Column(String, nullable=False)
    status = Column(String, default=GoalStatus.NOT_STARTED)
    progress_percentage = Column(Float, default=0.0)
    target_date = Column(DateTime)
    completion_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Milestone-specific data
    requirements = Column(JSON)  # What needs to be done
    success_metrics = Column(JSON)  # How to measure success
    resources = Column(JSON)  # Resources needed
    
    # Relationships
    roadmap = relationship("CareerRoadmap", back_populates="milestones")
    goal = relationship("CareerGoal", back_populates="milestones")


class ProgressTracking(Base):
    """Progress tracking database model"""
    __tablename__ = "progress_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    tracking_id = Column(String, unique=True, index=True)
    user_id = Column(String, ForeignKey("user_profiles.user_id"), nullable=False)
    roadmap_id = Column(String, ForeignKey("career_roadmaps.roadmap_id"))
    goal_id = Column(String, ForeignKey("career_goals.goal_id"))
    milestone_id = Column(String, ForeignKey("career_milestones.milestone_id"))
    
    # Progress data
    progress_percentage = Column(Float, nullable=False)
    notes = Column(Text)
    achievements = Column(JSON)  # List of achievements
    challenges = Column(JSON)  # List of challenges faced
    next_steps = Column(JSON)  # Planned next steps
    
    # Timestamps
    recorded_at = Column(DateTime, default=datetime.utcnow)
    period_start = Column(DateTime)
    period_end = Column(DateTime)


# Pydantic models for API requests/responses

class CareerGoalCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: str = Field(..., min_length=1)
    priority: int = Field(default=1, ge=1, le=3)
    target_date: Optional[datetime] = None
    success_criteria: Optional[List[str]] = []
    resources_needed: Optional[List[str]] = []
    dependencies: Optional[List[str]] = []


class CareerGoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=3)
    status: Optional[GoalStatus] = None
    progress_percentage: Optional[float] = Field(None, ge=0, le=100)
    target_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    success_criteria: Optional[List[str]] = None
    resources_needed: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None


class CareerMilestoneCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    milestone_type: MilestoneType
    goal_id: Optional[str] = None
    target_date: Optional[datetime] = None
    requirements: Optional[List[str]] = []
    success_metrics: Optional[List[str]] = []
    resources: Optional[List[str]] = []


class CareerMilestoneUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    milestone_type: Optional[MilestoneType] = None
    status: Optional[GoalStatus] = None
    progress_percentage: Optional[float] = Field(None, ge=0, le=100)
    target_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    requirements: Optional[List[str]] = None
    success_metrics: Optional[List[str]] = None
    resources: Optional[List[str]] = None


class CareerRoadmapCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    current_role: str = Field(..., min_length=1)
    target_role: str = Field(..., min_length=1)
    target_industry: Optional[str] = None
    target_company: Optional[str] = None
    timeline_months: int = Field(..., ge=1, le=120)  # 1 month to 10 years
    target_date: Optional[datetime] = None


class CareerRoadmapUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    current_role: Optional[str] = None
    target_role: Optional[str] = None
    target_industry: Optional[str] = None
    target_company: Optional[str] = None
    timeline_months: Optional[int] = Field(None, ge=1, le=120)
    status: Optional[GoalStatus] = None
    progress_percentage: Optional[float] = Field(None, ge=0, le=100)
    target_date: Optional[datetime] = None


class ProgressUpdate(BaseModel):
    progress_percentage: float = Field(..., ge=0, le=100)
    notes: Optional[str] = None
    achievements: Optional[List[str]] = []
    challenges: Optional[List[str]] = []
    next_steps: Optional[List[str]] = []
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class CareerRoadmapResponse(BaseModel):
    roadmap_id: str
    user_id: str
    title: str
    description: Optional[str]
    current_role: str
    target_role: str
    target_industry: Optional[str]
    target_company: Optional[str]
    timeline_months: int
    progress_percentage: float
    status: str
    created_at: datetime
    updated_at: datetime
    target_date: Optional[datetime]
    
    class Config:
        from_attributes = True


class CareerGoalResponse(BaseModel):
    goal_id: str
    roadmap_id: str
    user_id: str
    title: str
    description: Optional[str]
    category: str
    priority: int
    status: str
    progress_percentage: float
    target_date: Optional[datetime]
    completion_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    success_criteria: Optional[List[str]]
    resources_needed: Optional[List[str]]
    dependencies: Optional[List[str]]
    
    class Config:
        from_attributes = True


class CareerMilestoneResponse(BaseModel):
    milestone_id: str
    roadmap_id: str
    goal_id: Optional[str]
    user_id: str
    title: str
    description: Optional[str]
    milestone_type: str
    status: str
    progress_percentage: float
    target_date: Optional[datetime]
    completion_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    requirements: Optional[List[str]]
    success_metrics: Optional[List[str]]
    resources: Optional[List[str]]
    
    class Config:
        from_attributes = True


class ProgressTrackingResponse(BaseModel):
    tracking_id: str
    user_id: str
    roadmap_id: Optional[str]
    goal_id: Optional[str]
    milestone_id: Optional[str]
    progress_percentage: float
    notes: Optional[str]
    achievements: Optional[List[str]]
    challenges: Optional[List[str]]
    next_steps: Optional[List[str]]
    recorded_at: datetime
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    
    class Config:
        from_attributes = True
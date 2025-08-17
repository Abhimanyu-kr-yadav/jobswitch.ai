"""
User Profile Database Models
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Dict, Any
from app.models.encrypted_fields import EncryptedString, EncryptedText, HashedField

from .base import Base


class UserProfile(Base):
    """User profile model with career information"""
    __tablename__ = "user_profiles"
    
    user_id = Column(String(50), primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # Hashed password
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(EncryptedString(20))  # Encrypted phone number
    location = Column(String(255))
    
    # Sensitive personal information (encrypted)
    ssn_last_four = Column(EncryptedString(10))  # Last 4 digits of SSN for verification
    date_of_birth = Column(EncryptedString(20))  # Encrypted date of birth
    emergency_contact = Column(EncryptedText())  # Encrypted emergency contact info
    
    # Career information
    current_title = Column(String(255))
    current_company = Column(String(255))
    years_experience = Column(Integer, default=0)
    industry = Column(String(100))
    
    # Profile data stored as JSON
    skills = Column(JSON)  # List of skills with proficiency levels
    experience = Column(JSON)  # Work experience history
    education = Column(JSON)  # Education background
    certifications = Column(JSON)  # Professional certifications
    
    # Career goals and preferences
    career_goals = Column(JSON)  # Career objectives and target roles
    job_preferences = Column(JSON)  # Salary, location, company size preferences
    
    # Profile metadata
    profile_completion = Column(Float, default=0.0)  # Percentage complete
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    activities = relationship("UserActivity", back_populates="user")
    job_search_metrics = relationship("JobSearchMetrics", back_populates="user")
    ab_test_participations = relationship("ABTestParticipant", back_populates="user")
    reports = relationship("UserReport", back_populates="user")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user profile to dictionary"""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "location": self.location,
            "current_title": self.current_title,
            "current_company": self.current_company,
            "years_experience": self.years_experience,
            "industry": self.industry,
            "skills": self.skills,
            "experience": self.experience,
            "education": self.education,
            "certifications": self.certifications,
            "career_goals": self.career_goals,
            "job_preferences": self.job_preferences,
            "profile_completion": self.profile_completion,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class UserSession(Base):
    """User session tracking for agent interactions"""
    __tablename__ = "user_sessions"
    
    session_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False)
    session_data = Column(JSON)  # Session context and state
    agent_interactions = Column(JSON)  # History of agent interactions
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)


class UserPreferences(Base):
    """User preferences for AI agent behavior"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False)
    preference_type = Column(String(50), nullable=False)  # 'notification', 'agent_behavior', etc.
    preference_data = Column(JSON)  # Preference settings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
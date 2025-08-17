"""
Resume Database Models
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, Boolean
from datetime import datetime
from typing import Dict, Any, List

from .base import Base



class Resume(Base):
    """Resume model with versioning and optimization tracking"""
    __tablename__ = "resumes"
    
    resume_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    
    # Resume content
    title = Column(String(255))  # Resume title/target role
    content = Column(JSON, nullable=False)  # Structured resume content
    raw_text = Column(Text)  # Plain text version for parsing
    
    # Optimization details
    target_job_id = Column(String(50))  # Job this resume was optimized for
    ats_score = Column(Float)  # ATS compatibility score (0.0 to 1.0)
    keyword_density = Column(JSON)  # Keyword analysis results
    optimization_suggestions = Column(JSON)  # List of improvement suggestions
    
    # Resume metadata
    template_id = Column(String(50))  # Template used
    format_type = Column(String(20), default="pdf")  # 'pdf', 'docx', 'html'
    file_path = Column(String(500))  # Path to generated file
    
    # Status and tracking
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)  # Primary resume for user
    usage_count = Column(Integer, default=0)  # How many times used for applications
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert resume to dictionary"""
        return {
            "resume_id": self.resume_id,
            "user_id": self.user_id,
            "version": self.version,
            "title": self.title,
            "content": self.content,
            "target_job_id": self.target_job_id,
            "ats_score": self.ats_score,
            "keyword_density": self.keyword_density,
            "optimization_suggestions": self.optimization_suggestions,
            "template_id": self.template_id,
            "format_type": self.format_type,
            "file_path": self.file_path,
            "is_active": self.is_active,
            "is_primary": self.is_primary,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class ResumeTemplate(Base):
    """Resume templates for different industries and roles"""
    __tablename__ = "resume_templates"
    
    template_id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Template details
    industry = Column(String(100))  # Target industry
    role_type = Column(String(100))  # Target role type
    experience_level = Column(String(50))  # 'entry', 'mid', 'senior'
    
    # Template structure
    sections = Column(JSON, nullable=False)  # Template sections and order
    styling = Column(JSON)  # CSS/styling information
    layout_type = Column(String(50))  # 'traditional', 'modern', 'creative'
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    rating = Column(Float)  # User rating average
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ResumeAnalysis(Base):
    """Detailed analysis results for resumes"""
    __tablename__ = "resume_analyses"
    
    analysis_id = Column(String(50), primary_key=True)
    resume_id = Column(String(50), nullable=False)
    job_id = Column(String(50))  # Job analyzed against (optional)
    
    # Analysis results
    ats_score = Column(Float, nullable=False)
    keyword_analysis = Column(JSON)  # Keyword matching results
    section_analysis = Column(JSON)  # Analysis of each resume section
    formatting_analysis = Column(JSON)  # Formatting and structure analysis
    
    # Recommendations
    improvement_suggestions = Column(JSON)  # Specific improvement recommendations
    missing_keywords = Column(JSON)  # Keywords that should be added
    optimization_priority = Column(JSON)  # Priority order for improvements
    
    # Scoring breakdown
    content_score = Column(Float)  # Content quality score
    format_score = Column(Float)  # Format/structure score
    keyword_score = Column(Float)  # Keyword optimization score
    readability_score = Column(Float)  # Readability score
    
    # Analysis metadata
    analysis_type = Column(String(50))  # 'general', 'job_specific', 'ats_check'
    agent_version = Column(String(20))  # Version of analysis agent
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis to dictionary"""
        return {
            "analysis_id": self.analysis_id,
            "resume_id": self.resume_id,
            "job_id": self.job_id,
            "ats_score": self.ats_score,
            "keyword_analysis": self.keyword_analysis,
            "section_analysis": self.section_analysis,
            "formatting_analysis": self.formatting_analysis,
            "improvement_suggestions": self.improvement_suggestions,
            "missing_keywords": self.missing_keywords,
            "optimization_priority": self.optimization_priority,
            "content_score": self.content_score,
            "format_score": self.format_score,
            "keyword_score": self.keyword_score,
            "readability_score": self.readability_score,
            "analysis_type": self.analysis_type,
            "agent_version": self.agent_version,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ResumeOptimization(Base):
    """Track resume optimization history and changes"""
    __tablename__ = "resume_optimizations"
    
    optimization_id = Column(String(50), primary_key=True)
    original_resume_id = Column(String(50), nullable=False)
    optimized_resume_id = Column(String(50), nullable=False)
    job_id = Column(String(50))  # Job optimized for
    
    # Optimization details
    optimization_type = Column(String(50))  # 'ats', 'keyword', 'job_specific'
    changes_made = Column(JSON)  # List of changes applied
    improvement_metrics = Column(JSON)  # Before/after metrics
    
    # Results
    score_improvement = Column(Float)  # ATS score improvement
    keyword_improvement = Column(JSON)  # Keyword matching improvement
    success_probability = Column(Float)  # Estimated success probability
    
    created_at = Column(DateTime, default=datetime.utcnow)


class ResumeVersion(Base):
    """Track resume version history and relationships"""
    __tablename__ = "resume_versions"
    
    version_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False)
    base_resume_id = Column(String(50))  # Original resume this is based on
    resume_id = Column(String(50), nullable=False)  # Current resume ID
    
    # Version details
    version_number = Column(Integer, nullable=False)
    version_name = Column(String(255))  # Custom name for version
    description = Column(Text)  # Description of changes
    
    # Version type
    version_type = Column(String(50))  # 'original', 'optimization', 'manual_edit', 'copy'
    parent_version_id = Column(String(50))  # Parent version if applicable
    
    # Change tracking
    changes_summary = Column(JSON)  # Summary of changes from parent
    diff_data = Column(JSON)  # Detailed diff information
    
    # Metadata
    is_active = Column(Boolean, default=True)
    is_archived = Column(Boolean, default=False)
    tags = Column(JSON)  # Tags for organization
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert version to dictionary"""
        return {
            "version_id": self.version_id,
            "user_id": self.user_id,
            "base_resume_id": self.base_resume_id,
            "resume_id": self.resume_id,
            "version_number": self.version_number,
            "version_name": self.version_name,
            "description": self.description,
            "version_type": self.version_type,
            "parent_version_id": self.parent_version_id,
            "changes_summary": self.changes_summary,
            "is_active": self.is_active,
            "is_archived": self.is_archived,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
"""
Analytics and reporting data models
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid

from .base import Base

class UserActivity(Base):
    """Track user activities and interactions"""
    __tablename__ = "user_activities"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("user_profiles.user_id"), nullable=False)
    activity_type = Column(String, nullable=False)  # job_search, resume_optimization, interview_prep, etc.
    activity_subtype = Column(String)  # specific action within activity type
    session_id = Column(String)  # group related activities
    activity_metadata = Column(JSON)  # additional activity-specific data
    timestamp = Column(DateTime, default=datetime.utcnow)
    duration_seconds = Column(Integer)  # time spent on activity
    success = Column(Boolean, default=True)  # whether activity completed successfully
    
    # Relationships
    user = relationship("UserProfile", back_populates="activities")

class JobSearchMetrics(Base):
    """Track job search progress and success metrics"""
    __tablename__ = "job_search_metrics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("user_profiles.user_id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    
    # Search metrics
    jobs_viewed = Column(Integer, default=0)
    jobs_saved = Column(Integer, default=0)
    jobs_applied = Column(Integer, default=0)
    searches_performed = Column(Integer, default=0)
    
    # Application metrics
    applications_sent = Column(Integer, default=0)
    interviews_scheduled = Column(Integer, default=0)
    interviews_completed = Column(Integer, default=0)
    offers_received = Column(Integer, default=0)
    
    # Engagement metrics
    time_spent_minutes = Column(Integer, default=0)
    pages_visited = Column(Integer, default=0)
    features_used = Column(JSON)  # list of features used
    
    # Success metrics
    response_rate = Column(Float, default=0.0)  # percentage of applications that got responses
    interview_rate = Column(Float, default=0.0)  # percentage of applications that led to interviews
    offer_rate = Column(Float, default=0.0)  # percentage of interviews that led to offers
    
    # Relationships
    user = relationship("UserProfile", back_populates="job_search_metrics")

class AgentPerformanceMetrics(Base):
    """Track AI agent performance and effectiveness"""
    __tablename__ = "agent_performance_metrics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_name = Column(String, nullable=False)  # job_discovery, resume_optimization, etc.
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Performance metrics
    response_time_ms = Column(Integer)
    success_rate = Column(Float)
    error_count = Column(Integer, default=0)
    total_requests = Column(Integer, default=0)
    
    # Quality metrics
    user_satisfaction_score = Column(Float)  # 1-5 rating from users
    recommendation_accuracy = Column(Float)  # how accurate were recommendations
    task_completion_rate = Column(Float)  # percentage of tasks completed successfully
    
    # Resource usage
    cpu_usage_percent = Column(Float)
    memory_usage_mb = Column(Float)
    api_calls_made = Column(Integer, default=0)
    
    # Additional metadata
    performance_metadata = Column(JSON)

class ABTestExperiment(Base):
    """A/B testing experiments for algorithm optimization"""
    __tablename__ = "ab_test_experiments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    feature_name = Column(String, nullable=False)  # which feature is being tested
    
    # Experiment configuration
    control_algorithm = Column(String)  # name/version of control algorithm
    test_algorithm = Column(String)  # name/version of test algorithm
    traffic_split = Column(Float, default=0.5)  # percentage of users in test group
    
    # Experiment status
    status = Column(String, default="draft")  # draft, running, paused, completed
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # Success metrics to track
    primary_metric = Column(String)  # main metric to optimize
    secondary_metrics = Column(JSON)  # additional metrics to monitor
    
    # Results
    control_conversion_rate = Column(Float)
    test_conversion_rate = Column(Float)
    statistical_significance = Column(Float)
    confidence_interval = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ABTestParticipant(Base):
    """Track which users are in which A/B test groups"""
    __tablename__ = "ab_test_participants"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id = Column(String, ForeignKey("ab_test_experiments.id"), nullable=False)
    user_id = Column(String, ForeignKey("user_profiles.user_id"), nullable=False)
    group = Column(String, nullable=False)  # control or test
    assigned_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    experiment = relationship("ABTestExperiment")
    user = relationship("UserProfile", back_populates="ab_test_participations")

class SystemPerformanceMetrics(Base):
    """Track overall system performance and health"""
    __tablename__ = "system_performance_metrics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # System metrics
    cpu_usage_percent = Column(Float)
    memory_usage_percent = Column(Float)
    disk_usage_percent = Column(Float)
    active_users = Column(Integer)
    concurrent_sessions = Column(Integer)
    
    # API metrics
    total_requests = Column(Integer)
    successful_requests = Column(Integer)
    failed_requests = Column(Integer)
    average_response_time_ms = Column(Float)
    
    # Database metrics
    db_connections_active = Column(Integer)
    db_query_time_avg_ms = Column(Float)
    db_slow_queries = Column(Integer)
    
    # External API metrics
    external_api_calls = Column(Integer)
    external_api_failures = Column(Integer)
    external_api_avg_response_time_ms = Column(Float)
    
    # Cache metrics
    cache_hit_rate = Column(Float)
    cache_memory_usage_mb = Column(Float)

class ReportTemplate(Base):
    """Predefined report templates for analytics dashboard"""
    __tablename__ = "report_templates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)  # user_progress, system_health, agent_performance, etc.
    
    # Report configuration
    metrics = Column(JSON)  # list of metrics to include
    filters = Column(JSON)  # default filters to apply
    visualization_config = Column(JSON)  # chart types, colors, etc.
    
    # Access control
    is_public = Column(Boolean, default=False)
    created_by = Column(String, ForeignKey("user_profiles.user_id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserReport(Base):
    """Generated reports for users"""
    __tablename__ = "user_reports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("user_profiles.user_id"), nullable=False)
    template_id = Column(String, ForeignKey("report_templates.id"))
    
    # Report details
    title = Column(String, nullable=False)
    report_type = Column(String)  # weekly_progress, monthly_summary, etc.
    date_range_start = Column(DateTime)
    date_range_end = Column(DateTime)
    
    # Report data
    data = Column(JSON)  # the actual report data
    insights = Column(JSON)  # AI-generated insights
    recommendations = Column(JSON)  # AI-generated recommendations
    
    # Status
    status = Column(String, default="generated")  # generated, viewed, archived
    generated_at = Column(DateTime, default=datetime.utcnow)
    viewed_at = Column(DateTime)
    
    # Relationships
    user = relationship("UserProfile", back_populates="reports")
    template = relationship("ReportTemplate")
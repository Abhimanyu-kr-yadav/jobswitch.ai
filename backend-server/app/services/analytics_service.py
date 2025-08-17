"""
Analytics service for tracking user activities and generating insights
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import json
import asyncio
from collections import defaultdict

from app.models.analytics import (
    UserActivity, JobSearchMetrics, AgentPerformanceMetrics,
    ABTestExperiment, ABTestParticipant, SystemPerformanceMetrics,
    ReportTemplate, UserReport
)
from app.core.database import get_database
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class AnalyticsService:
    """Service for handling analytics tracking and reporting"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def track_user_activity(
        self,
        user_id: str,
        activity_type: str,
        activity_subtype: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        duration_seconds: Optional[int] = None,
        success: bool = True
    ) -> str:
        """Track a user activity"""
        try:
            activity = UserActivity(
                user_id=user_id,
                activity_type=activity_type,
                activity_subtype=activity_subtype,
                session_id=session_id,
                activity_metadata=metadata or {},
                duration_seconds=duration_seconds,
                success=success
            )
            
            self.db.add(activity)
            self.db.commit()
            
            logger.info(f"Tracked activity {activity_type} for user {user_id}")
            return activity.id
            
        except Exception as e:
            logger.error(f"Error tracking user activity: {str(e)}")
            self.db.rollback()
            raise
    
    async def update_job_search_metrics(
        self,
        user_id: str,
        metrics_update: Dict[str, Any]
    ) -> None:
        """Update job search metrics for a user"""
        try:
            # Get today's metrics or create new
            today = datetime.utcnow().date()
            metrics = self.db.query(JobSearchMetrics).filter(
                and_(
                    JobSearchMetrics.user_id == user_id,
                    func.date(JobSearchMetrics.date) == today
                )
            ).first()
            
            if not metrics:
                metrics = JobSearchMetrics(user_id=user_id)
                self.db.add(metrics)
            
            # Update metrics
            for key, value in metrics_update.items():
                if hasattr(metrics, key):
                    if isinstance(value, (int, float)) and key not in ['response_rate', 'interview_rate', 'offer_rate']:
                        # Increment counters
                        current_value = getattr(metrics, key) or 0
                        setattr(metrics, key, current_value + value)
                    else:
                        # Set direct values for rates
                        setattr(metrics, key, value)
            
            # Calculate rates
            if metrics.applications_sent > 0:
                metrics.response_rate = (metrics.interviews_scheduled / metrics.applications_sent) * 100
                metrics.interview_rate = (metrics.interviews_completed / metrics.applications_sent) * 100
            
            if metrics.interviews_completed > 0:
                metrics.offer_rate = (metrics.offers_received / metrics.interviews_completed) * 100
            
            self.db.commit()
            logger.info(f"Updated job search metrics for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating job search metrics: {str(e)}")
            self.db.rollback()
            raise
    
    async def track_agent_performance(
        self,
        agent_name: str,
        response_time_ms: int,
        success: bool = True,
        user_satisfaction_score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track AI agent performance metrics"""
        try:
            # Get or create today's metrics for this agent
            today = datetime.utcnow().date()
            metrics = self.db.query(AgentPerformanceMetrics).filter(
                and_(
                    AgentPerformanceMetrics.agent_name == agent_name,
                    func.date(AgentPerformanceMetrics.timestamp) == today
                )
            ).first()
            
            if not metrics:
                metrics = AgentPerformanceMetrics(agent_name=agent_name)
                self.db.add(metrics)
            
            # Update metrics
            metrics.total_requests = (metrics.total_requests or 0) + 1
            if not success:
                metrics.error_count = (metrics.error_count or 0) + 1
            
            # Calculate success rate
            metrics.success_rate = ((metrics.total_requests - metrics.error_count) / metrics.total_requests) * 100
            
            # Update response time (moving average)
            if metrics.response_time_ms:
                metrics.response_time_ms = int((metrics.response_time_ms + response_time_ms) / 2)
            else:
                metrics.response_time_ms = response_time_ms
            
            # Update satisfaction score if provided
            if user_satisfaction_score:
                if metrics.user_satisfaction_score:
                    metrics.user_satisfaction_score = (metrics.user_satisfaction_score + user_satisfaction_score) / 2
                else:
                    metrics.user_satisfaction_score = user_satisfaction_score
            
            if metadata:
                current_metadata = metrics.performance_metadata or {}
                current_metadata.update(metadata)
                metrics.performance_metadata = current_metadata
            
            self.db.commit()
            logger.info(f"Tracked performance for agent {agent_name}")
            
        except Exception as e:
            logger.error(f"Error tracking agent performance: {str(e)}")
            self.db.rollback()
            raise
    
    async def get_user_analytics_summary(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics summary for a user"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get user activities
            activities = self.db.query(UserActivity).filter(
                and_(
                    UserActivity.user_id == user_id,
                    UserActivity.timestamp >= start_date
                )
            ).all()
            
            # Get job search metrics
            job_metrics = self.db.query(JobSearchMetrics).filter(
                and_(
                    JobSearchMetrics.user_id == user_id,
                    JobSearchMetrics.date >= start_date
                )
            ).all()
            
            # Aggregate data
            activity_summary = defaultdict(int)
            for activity in activities:
                activity_summary[activity.activity_type] += 1
            
            total_jobs_viewed = sum(m.jobs_viewed for m in job_metrics)
            total_applications = sum(m.applications_sent for m in job_metrics)
            total_interviews = sum(m.interviews_completed for m in job_metrics)
            total_offers = sum(m.offers_received for m in job_metrics)
            
            # Calculate overall rates
            response_rate = 0
            interview_rate = 0
            offer_rate = 0
            
            if total_applications > 0:
                response_rate = (total_interviews / total_applications) * 100
                interview_rate = response_rate  # Simplified for now
            
            if total_interviews > 0:
                offer_rate = (total_offers / total_interviews) * 100
            
            return {
                "period_days": days,
                "activity_summary": dict(activity_summary),
                "job_search_summary": {
                    "jobs_viewed": total_jobs_viewed,
                    "applications_sent": total_applications,
                    "interviews_completed": total_interviews,
                    "offers_received": total_offers,
                    "response_rate": round(response_rate, 2),
                    "interview_rate": round(interview_rate, 2),
                    "offer_rate": round(offer_rate, 2)
                },
                "engagement_metrics": {
                    "total_activities": len(activities),
                    "active_days": len(set(a.timestamp.date() for a in activities)),
                    "most_used_feature": max(activity_summary.items(), key=lambda x: x[1])[0] if activity_summary else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting user analytics summary: {str(e)}")
            raise
    
    async def get_system_performance_summary(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get system performance summary"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Get system metrics
            system_metrics = self.db.query(SystemPerformanceMetrics).filter(
                SystemPerformanceMetrics.timestamp >= start_time
            ).all()
            
            # Get agent performance
            agent_metrics = self.db.query(AgentPerformanceMetrics).filter(
                AgentPerformanceMetrics.timestamp >= start_time
            ).all()
            
            if not system_metrics:
                return {"error": "No system metrics available"}
            
            # Calculate averages
            avg_cpu = sum(m.cpu_usage_percent for m in system_metrics if m.cpu_usage_percent) / len(system_metrics)
            avg_memory = sum(m.memory_usage_percent for m in system_metrics if m.memory_usage_percent) / len(system_metrics)
            avg_response_time = sum(m.average_response_time_ms for m in system_metrics if m.average_response_time_ms) / len(system_metrics)
            
            # Agent performance summary
            agent_summary = {}
            for metric in agent_metrics:
                if metric.agent_name not in agent_summary:
                    agent_summary[metric.agent_name] = {
                        "success_rate": metric.success_rate,
                        "avg_response_time": metric.response_time_ms,
                        "total_requests": metric.total_requests,
                        "error_count": metric.error_count
                    }
            
            return {
                "period_hours": hours,
                "system_health": {
                    "avg_cpu_usage": round(avg_cpu, 2),
                    "avg_memory_usage": round(avg_memory, 2),
                    "avg_response_time_ms": round(avg_response_time, 2),
                    "status": "healthy" if avg_cpu < 80 and avg_memory < 80 else "warning"
                },
                "agent_performance": agent_summary,
                "total_requests": sum(m.total_requests for m in system_metrics if m.total_requests),
                "error_rate": sum(m.failed_requests for m in system_metrics if m.failed_requests) / max(sum(m.total_requests for m in system_metrics if m.total_requests), 1) * 100
            }
            
        except Exception as e:
            logger.error(f"Error getting system performance summary: {str(e)}")
            raise
    
    async def create_user_report(
        self,
        user_id: str,
        report_type: str = "weekly_progress",
        template_id: Optional[str] = None
    ) -> str:
        """Generate a user report"""
        try:
            # Determine date range based on report type
            if report_type == "weekly_progress":
                start_date = datetime.utcnow() - timedelta(days=7)
                title = "Weekly Progress Report"
            elif report_type == "monthly_summary":
                start_date = datetime.utcnow() - timedelta(days=30)
                title = "Monthly Summary Report"
            else:
                start_date = datetime.utcnow() - timedelta(days=7)
                title = "Progress Report"
            
            end_date = datetime.utcnow()
            
            # Get analytics data
            analytics_data = await self.get_user_analytics_summary(
                user_id, 
                days=(end_date - start_date).days
            )
            
            # Generate insights (simplified AI insights)
            insights = await self._generate_insights(analytics_data)
            recommendations = await self._generate_recommendations(analytics_data)
            
            # Create report
            report = UserReport(
                user_id=user_id,
                template_id=template_id,
                title=title,
                report_type=report_type,
                date_range_start=start_date,
                date_range_end=end_date,
                data=analytics_data,
                insights=insights,
                recommendations=recommendations
            )
            
            self.db.add(report)
            self.db.commit()
            
            logger.info(f"Created report {report.id} for user {user_id}")
            return report.id
            
        except Exception as e:
            logger.error(f"Error creating user report: {str(e)}")
            self.db.rollback()
            raise
    
    async def _generate_insights(self, analytics_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate AI insights from analytics data"""
        insights = []
        
        job_summary = analytics_data.get("job_search_summary", {})
        engagement = analytics_data.get("engagement_metrics", {})
        
        # Job search insights
        if job_summary.get("applications_sent", 0) > 0:
            response_rate = job_summary.get("response_rate", 0)
            if response_rate > 20:
                insights.append({
                    "type": "positive",
                    "title": "Strong Response Rate",
                    "description": f"Your {response_rate}% response rate is above average, indicating your applications are well-targeted."
                })
            elif response_rate < 5:
                insights.append({
                    "type": "improvement",
                    "title": "Low Response Rate",
                    "description": f"Your {response_rate}% response rate suggests room for improvement in application targeting or resume optimization."
                })
        
        # Engagement insights
        active_days = engagement.get("active_days", 0)
        period_days = analytics_data.get("period_days", 7)
        
        if active_days / period_days > 0.7:
            insights.append({
                "type": "positive",
                "title": "Consistent Engagement",
                "description": f"You've been active {active_days} out of {period_days} days, showing great consistency."
            })
        elif active_days / period_days < 0.3:
            insights.append({
                "type": "improvement",
                "title": "Increase Activity",
                "description": f"Consider increasing your job search activity. You were active only {active_days} out of {period_days} days."
            })
        
        return insights
    
    async def _generate_recommendations(self, analytics_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate AI recommendations from analytics data"""
        recommendations = []
        
        job_summary = analytics_data.get("job_search_summary", {})
        activity_summary = analytics_data.get("activity_summary", {})
        
        # Job search recommendations
        if job_summary.get("jobs_viewed", 0) > job_summary.get("applications_sent", 0) * 10:
            recommendations.append({
                "type": "action",
                "title": "Apply to More Jobs",
                "description": "You're viewing many jobs but applying to few. Consider applying to more positions that match your criteria.",
                "priority": "high"
            })
        
        # Feature usage recommendations
        if "resume_optimization" not in activity_summary:
            recommendations.append({
                "type": "feature",
                "title": "Try Resume Optimization",
                "description": "Use our AI resume optimizer to improve your application success rate.",
                "priority": "medium"
            })
        
        if "interview_preparation" not in activity_summary and job_summary.get("interviews_completed", 0) > 0:
            recommendations.append({
                "type": "feature",
                "title": "Practice Interview Skills",
                "description": "Use our mock interview feature to improve your interview performance.",
                "priority": "medium"
            })
        
        return recommendations

# Utility functions for analytics
async def track_activity(
    user_id: str,
    activity_type: str,
    activity_subtype: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    db: Session = None
):
    """Convenience function to track user activity"""
    if not db:
        db = next(get_database())
    
    service = AnalyticsService(db)
    return await service.track_user_activity(
        user_id=user_id,
        activity_type=activity_type,
        activity_subtype=activity_subtype,
        metadata=metadata
    )

async def update_job_metrics(
    user_id: str,
    metrics_update: Dict[str, Any],
    db: Session = None
):
    """Convenience function to update job search metrics"""
    if not db:
        db = next(get_database())
    
    service = AnalyticsService(db)
    return await service.update_job_search_metrics(user_id, metrics_update)
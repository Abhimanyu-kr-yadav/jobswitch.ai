"""
Analytics API endpoints for reporting and metrics
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.core.database import get_database
from app.core.auth import get_current_user
from app.models.user import UserProfile
from app.services.analytics_service import AnalyticsService
from app.models.analytics import UserReport, ReportTemplate, ABTestExperiment, UserActivity, JobSearchMetrics, AgentPerformanceMetrics
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/user/summary")
async def get_user_analytics_summary(
    days: int = Query(30, ge=1, le=365),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """Get analytics summary for the current user"""
    try:
        service = AnalyticsService(db)
        summary = await service.get_user_analytics_summary(current_user.id, days)
        return {
            "success": True,
            "data": summary
        }
    except Exception as e:
        logger.error(f"Error getting user analytics summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get analytics summary")

@router.get("/user/job-search-progress")
async def get_job_search_progress(
    days: int = Query(30, ge=1, le=365),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """Get detailed job search progress metrics"""
    try:
        service = AnalyticsService(db)
        
        # Get basic summary
        summary = await service.get_user_analytics_summary(current_user.id, days)
        
        # Get daily breakdown
        start_date = datetime.utcnow() - timedelta(days=days)
        daily_metrics = db.query(
            func.date(JobSearchMetrics.date).label('date'),
            func.sum(JobSearchMetrics.jobs_viewed).label('jobs_viewed'),
            func.sum(JobSearchMetrics.applications_sent).label('applications_sent'),
            func.sum(JobSearchMetrics.interviews_completed).label('interviews_completed')
        ).filter(
            and_(
                JobSearchMetrics.user_id == current_user.id,
                JobSearchMetrics.date >= start_date
            )
        ).group_by(func.date(JobSearchMetrics.date)).all()
        
        # Format daily data
        daily_data = []
        for metric in daily_metrics:
            daily_data.append({
                "date": metric.date.isoformat(),
                "jobs_viewed": metric.jobs_viewed or 0,
                "applications_sent": metric.applications_sent or 0,
                "interviews_completed": metric.interviews_completed or 0
            })
        
        return {
            "success": True,
            "data": {
                "summary": summary["job_search_summary"],
                "daily_breakdown": daily_data,
                "trends": {
                    "applications_trend": "increasing" if len(daily_data) > 1 and daily_data[-1]["applications_sent"] > daily_data[0]["applications_sent"] else "stable",
                    "interview_trend": "increasing" if len(daily_data) > 1 and daily_data[-1]["interviews_completed"] > daily_data[0]["interviews_completed"] else "stable"
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting job search progress: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get job search progress")

@router.get("/user/activity-timeline")
async def get_user_activity_timeline(
    days: int = Query(7, ge=1, le=90),
    activity_type: Optional[str] = Query(None),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """Get user activity timeline"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(UserActivity).filter(
            and_(
                UserActivity.user_id == current_user.id,
                UserActivity.timestamp >= start_date
            )
        )
        
        if activity_type:
            query = query.filter(UserActivity.activity_type == activity_type)
        
        activities = query.order_by(UserActivity.timestamp.desc()).limit(100).all()
        
        # Format activities
        timeline = []
        for activity in activities:
            timeline.append({
                "id": activity.id,
                "activity_type": activity.activity_type,
                "activity_subtype": activity.activity_subtype,
                "timestamp": activity.timestamp.isoformat(),
                "duration_seconds": activity.duration_seconds,
                "success": activity.success,
                "metadata": activity.metadata
            })
        
        return {
            "success": True,
            "data": {
                "timeline": timeline,
                "total_activities": len(timeline),
                "period_days": days
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting activity timeline: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get activity timeline")

@router.post("/user/track-activity")
async def track_user_activity(
    activity_data: Dict[str, Any],
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """Track a user activity"""
    try:
        service = AnalyticsService(db)
        
        activity_id = await service.track_user_activity(
            user_id=current_user.id,
            activity_type=activity_data.get("activity_type"),
            activity_subtype=activity_data.get("activity_subtype"),
            session_id=activity_data.get("session_id"),
            metadata=activity_data.get("metadata"),
            duration_seconds=activity_data.get("duration_seconds"),
            success=activity_data.get("success", True)
        )
        
        return {
            "success": True,
            "data": {"activity_id": activity_id}
        }
        
    except Exception as e:
        logger.error(f"Error tracking user activity: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to track activity")

@router.post("/user/update-job-metrics")
async def update_user_job_metrics(
    metrics_data: Dict[str, Any],
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """Update job search metrics for user"""
    try:
        service = AnalyticsService(db)
        
        await service.update_job_search_metrics(
            user_id=current_user.id,
            metrics_update=metrics_data
        )
        
        return {
            "success": True,
            "message": "Job metrics updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error updating job metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update job metrics")

@router.get("/user/reports")
async def get_user_reports(
    limit: int = Query(10, ge=1, le=50),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """Get user reports"""
    try:
        reports = db.query(UserReport).filter(
            UserReport.user_id == current_user.id
        ).order_by(UserReport.generated_at.desc()).limit(limit).all()
        
        reports_data = []
        for report in reports:
            reports_data.append({
                "id": report.id,
                "title": report.title,
                "report_type": report.report_type,
                "date_range_start": report.date_range_start.isoformat() if report.date_range_start else None,
                "date_range_end": report.date_range_end.isoformat() if report.date_range_end else None,
                "status": report.status,
                "generated_at": report.generated_at.isoformat(),
                "viewed_at": report.viewed_at.isoformat() if report.viewed_at else None
            })
        
        return {
            "success": True,
            "data": {
                "reports": reports_data,
                "total": len(reports_data)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user reports: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get reports")

@router.get("/user/reports/{report_id}")
async def get_user_report_details(
    report_id: str,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """Get detailed user report"""
    try:
        report = db.query(UserReport).filter(
            and_(
                UserReport.id == report_id,
                UserReport.user_id == current_user.id
            )
        ).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Mark as viewed if not already
        if not report.viewed_at:
            report.viewed_at = datetime.utcnow()
            report.status = "viewed"
            db.commit()
        
        return {
            "success": True,
            "data": {
                "id": report.id,
                "title": report.title,
                "report_type": report.report_type,
                "date_range_start": report.date_range_start.isoformat() if report.date_range_start else None,
                "date_range_end": report.date_range_end.isoformat() if report.date_range_end else None,
                "data": report.data,
                "insights": report.insights,
                "recommendations": report.recommendations,
                "status": report.status,
                "generated_at": report.generated_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report details: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get report details")

@router.post("/user/generate-report")
async def generate_user_report(
    report_config: Dict[str, Any],
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """Generate a new user report"""
    try:
        service = AnalyticsService(db)
        
        report_id = await service.create_user_report(
            user_id=current_user.id,
            report_type=report_config.get("report_type", "weekly_progress"),
            template_id=report_config.get("template_id")
        )
        
        return {
            "success": True,
            "data": {"report_id": report_id}
        }
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate report")

# Admin endpoints for system analytics
@router.get("/system/performance")
async def get_system_performance(
    hours: int = Query(24, ge=1, le=168),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """Get system performance metrics (admin only)"""
    try:
        # Check if user is admin (simplified check)
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        service = AnalyticsService(db)
        performance_data = await service.get_system_performance_summary(hours)
        
        return {
            "success": True,
            "data": performance_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system performance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get system performance")

@router.get("/system/real-time-metrics")
async def get_real_time_metrics(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """Get real-time system and agent metrics (admin only)"""
    try:
        # Check if user is admin
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        from app.services.performance_monitoring_service import get_performance_monitor
        
        monitor = get_performance_monitor()
        if not monitor:
            raise HTTPException(status_code=503, detail="Performance monitoring not available")
        
        metrics = await monitor.get_real_time_metrics()
        
        return {
            "success": True,
            "data": metrics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting real-time metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get real-time metrics")

@router.get("/system/performance-alerts")
async def get_performance_alerts(
    hours: int = Query(24, ge=1, le=168),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """Get performance alerts (admin only)"""
    try:
        # Check if user is admin
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        from app.services.performance_monitoring_service import get_performance_monitor
        
        monitor = get_performance_monitor()
        if not monitor:
            raise HTTPException(status_code=503, detail="Performance monitoring not available")
        
        alerts = await monitor.get_performance_alerts(hours)
        
        # Group alerts by severity
        alert_summary = {
            'high': [a for a in alerts if a.get('severity') == 'high'],
            'medium': [a for a in alerts if a.get('severity') == 'medium'],
            'low': [a for a in alerts if a.get('severity') == 'low']
        }
        
        return {
            "success": True,
            "data": {
                "alerts": alerts,
                "summary": {
                    "total": len(alerts),
                    "high_severity": len(alert_summary['high']),
                    "medium_severity": len(alert_summary['medium']),
                    "low_severity": len(alert_summary['low'])
                },
                "by_severity": alert_summary
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance alerts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get performance alerts")

@router.get("/system/health-check")
async def system_health_check(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """Get overall system health status"""
    try:
        from app.services.performance_monitoring_service import get_performance_monitor
        
        monitor = get_performance_monitor()
        health_status = {
            "overall_status": "healthy",
            "components": {
                "database": "healthy",
                "cache": "healthy",
                "performance_monitor": "healthy" if monitor else "unavailable"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check database connectivity
        try:
            db.execute("SELECT 1")
            health_status["components"]["database"] = "healthy"
        except:
            health_status["components"]["database"] = "unhealthy"
            health_status["overall_status"] = "degraded"
        
        # Check cache connectivity
        try:
            from app.core.cache import get_redis_client
            redis_client = get_redis_client()
            await redis_client.ping()
            health_status["components"]["cache"] = "healthy"
        except:
            health_status["components"]["cache"] = "unhealthy"
            health_status["overall_status"] = "degraded"
        
        # Get real-time metrics if available
        if monitor:
            try:
                metrics = await monitor.get_real_time_metrics()
                if metrics.get('system'):
                    system_status = metrics['system'].get('status', 'unknown')
                    health_status["components"]["system_performance"] = system_status
                    
                    if system_status == 'critical':
                        health_status["overall_status"] = "critical"
                    elif system_status == 'warning' and health_status["overall_status"] == "healthy":
                        health_status["overall_status"] = "warning"
            except:
                pass
        
        return {
            "success": True,
            "data": health_status
        }
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return {
            "success": False,
            "data": {
                "overall_status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        }

@router.get("/system/agent-performance")
async def get_agent_performance_metrics(
    agent_name: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=168),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """Get AI agent performance metrics (admin only)"""
    try:
        # Check if user is admin
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = db.query(AgentPerformanceMetrics).filter(
            AgentPerformanceMetrics.timestamp >= start_time
        )
        
        if agent_name:
            query = query.filter(AgentPerformanceMetrics.agent_name == agent_name)
        
        metrics = query.all()
        
        # Aggregate metrics by agent
        agent_data = {}
        for metric in metrics:
            if metric.agent_name not in agent_data:
                agent_data[metric.agent_name] = {
                    "total_requests": 0,
                    "total_errors": 0,
                    "avg_response_time": 0,
                    "avg_satisfaction": 0,
                    "success_rate": 0
                }
            
            data = agent_data[metric.agent_name]
            data["total_requests"] += metric.total_requests or 0
            data["total_errors"] += metric.error_count or 0
            data["avg_response_time"] = (data["avg_response_time"] + (metric.response_time_ms or 0)) / 2
            if metric.user_satisfaction_score:
                data["avg_satisfaction"] = (data["avg_satisfaction"] + metric.user_satisfaction_score) / 2
            if metric.success_rate:
                data["success_rate"] = (data["success_rate"] + metric.success_rate) / 2
        
        return {
            "success": True,
            "data": {
                "period_hours": hours,
                "agents": agent_data
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent performance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get agent performance")

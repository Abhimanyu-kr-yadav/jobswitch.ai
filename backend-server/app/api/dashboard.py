"""
Dashboard API Endpoints
Provides unified dashboard data and statistics
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_database
from app.core.auth import get_current_active_user
from app.models.user import UserProfile
from app.core.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    current_user: UserProfile = Depends(get_current_active_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get dashboard statistics for the current user
    
    Returns:
        Dashboard statistics including agent activities and counts
    """
    try:
        user_id = current_user.user_id
        
        # Initialize stats
        stats = {
            "job_recommendations": 0,
            "skill_gaps": 0,
            "resume_optimizations": 0,
            "interview_sessions": 0,
            "networking_contacts": 0,
            "career_milestones": 0,
            "total_activities": 0,
            "active_agents": 0
        }
        
        # Get job discovery stats
        try:
            job_count = db.execute(
                "SELECT COUNT(*) FROM saved_jobs WHERE user_id = ?", 
                (user_id,)
            ).fetchone()
            if job_count:
                stats["job_recommendations"] = job_count[0]
        except Exception as e:
            logger.warning(f"Could not get job stats: {str(e)}")
        
        # Get skills analysis stats
        try:
            skills_count = db.execute(
                "SELECT COUNT(*) FROM skill_analyses WHERE user_id = ?", 
                (user_id,)
            ).fetchone()
            if skills_count:
                stats["skill_gaps"] = skills_count[0]
        except Exception as e:
            logger.warning(f"Could not get skills stats: {str(e)}")
        
        # Get resume optimization stats
        try:
            resume_count = db.execute(
                "SELECT COUNT(*) FROM resume_versions WHERE user_id = ?", 
                (user_id,)
            ).fetchone()
            if resume_count:
                stats["resume_optimizations"] = resume_count[0]
        except Exception as e:
            logger.warning(f"Could not get resume stats: {str(e)}")
        
        # Get interview preparation stats
        try:
            interview_count = db.execute(
                "SELECT COUNT(*) FROM interview_sessions WHERE user_id = ?", 
                (user_id,)
            ).fetchone()
            if interview_count:
                stats["interview_sessions"] = interview_count[0]
        except Exception as e:
            logger.warning(f"Could not get interview stats: {str(e)}")
        
        # Get networking stats
        try:
            networking_count = db.execute(
                "SELECT COUNT(*) FROM networking_contacts WHERE user_id = ?", 
                (user_id,)
            ).fetchone()
            if networking_count:
                stats["networking_contacts"] = networking_count[0]
        except Exception as e:
            logger.warning(f"Could not get networking stats: {str(e)}")
        
        # Get career strategy stats
        try:
            career_count = db.execute(
                "SELECT COUNT(*) FROM career_roadmaps WHERE user_id = ?", 
                (user_id,)
            ).fetchone()
            if career_count:
                stats["career_milestones"] = career_count[0]
        except Exception as e:
            logger.warning(f"Could not get career stats: {str(e)}")
        
        # Calculate totals
        stats["total_activities"] = sum([
            stats["job_recommendations"],
            stats["skill_gaps"],
            stats["resume_optimizations"],
            stats["interview_sessions"],
            stats["networking_contacts"],
            stats["career_milestones"]
        ])
        
        # Get WebSocket connection stats
        ws_stats = websocket_manager.get_connection_stats()
        stats["websocket_connections"] = ws_stats.get("total_connections", 0)
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent-activities")
async def get_recent_activities(
    limit: int = 10,
    current_user: UserProfile = Depends(get_current_active_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get recent activities for the current user
    
    Args:
        limit: Maximum number of activities to return
        
    Returns:
        List of recent activities
    """
    try:
        user_id = current_user.user_id
        activities = []
        
        # Get recent job discoveries
        try:
            job_activities = db.execute("""
                SELECT 'job_discovery' as agent, 'Job saved' as message, 
                       created_at as timestamp, job_title as details
                FROM saved_jobs 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (user_id, limit // 6)).fetchall()
            
            for activity in job_activities:
                activities.append({
                    "agent": activity[0],
                    "message": f"{activity[1]}: {activity[3]}",
                    "timestamp": activity[2],
                    "type": "job_discovery"
                })
        except Exception as e:
            logger.warning(f"Could not get job activities: {str(e)}")
        
        # Get recent skill analyses
        try:
            skill_activities = db.execute("""
                SELECT 'skills_analysis' as agent, 'Skills analyzed' as message, 
                       created_at as timestamp, analysis_type as details
                FROM skill_analyses 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (user_id, limit // 6)).fetchall()
            
            for activity in skill_activities:
                activities.append({
                    "agent": activity[0],
                    "message": f"{activity[1]}: {activity[3]}",
                    "timestamp": activity[2],
                    "type": "skills_analysis"
                })
        except Exception as e:
            logger.warning(f"Could not get skill activities: {str(e)}")
        
        # Get recent resume optimizations
        try:
            resume_activities = db.execute("""
                SELECT 'resume_optimization' as agent, 'Resume optimized' as message, 
                       created_at as timestamp, version_name as details
                FROM resume_versions 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (user_id, limit // 6)).fetchall()
            
            for activity in resume_activities:
                activities.append({
                    "agent": activity[0],
                    "message": f"{activity[1]}: {activity[3]}",
                    "timestamp": activity[2],
                    "type": "resume_optimization"
                })
        except Exception as e:
            logger.warning(f"Could not get resume activities: {str(e)}")
        
        # Get recent interview sessions
        try:
            interview_activities = db.execute("""
                SELECT 'interview_preparation' as agent, 'Interview session completed' as message, 
                       created_at as timestamp, session_type as details
                FROM interview_sessions 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (user_id, limit // 6)).fetchall()
            
            for activity in interview_activities:
                activities.append({
                    "agent": activity[0],
                    "message": f"{activity[1]}: {activity[3]}",
                    "timestamp": activity[2],
                    "type": "interview_preparation"
                })
        except Exception as e:
            logger.warning(f"Could not get interview activities: {str(e)}")
        
        # Sort activities by timestamp and limit
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        activities = activities[:limit]
        
        return {
            "success": True,
            "data": {
                "activities": activities,
                "total": len(activities)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting recent activities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications")
async def get_notifications(
    limit: int = 20,
    unread_only: bool = False,
    current_user: UserProfile = Depends(get_current_active_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get notifications for the current user
    
    Args:
        limit: Maximum number of notifications to return
        unread_only: Whether to return only unread notifications
        
    Returns:
        List of notifications
    """
    try:
        user_id = current_user.user_id
        
        # For now, return mock notifications since we don't have a notifications table
        # In a real implementation, you'd query a notifications table
        notifications = [
            {
                "id": "notif_1",
                "title": "New Job Recommendations Available",
                "message": "Found 5 new job opportunities matching your profile",
                "type": "job_recommendation",
                "agent": "job_discovery",
                "priority": "medium",
                "read": False,
                "timestamp": "2025-01-08T10:00:00Z",
                "data": {"count": 5}
            },
            {
                "id": "notif_2",
                "title": "Skills Analysis Complete",
                "message": "Your skills analysis has been updated with new recommendations",
                "type": "skill_gap",
                "agent": "skills_analysis",
                "priority": "low",
                "read": True,
                "timestamp": "2025-01-08T09:30:00Z",
                "data": {"gaps": 3}
            },
            {
                "id": "notif_3",
                "title": "Resume Optimization Suggestion",
                "message": "Your resume can be improved for better ATS compatibility",
                "type": "resume_optimization",
                "agent": "resume_optimization",
                "priority": "high",
                "read": False,
                "timestamp": "2025-01-08T09:00:00Z",
                "data": {"score": 75}
            }
        ]
        
        if unread_only:
            notifications = [n for n in notifications if not n["read"]]
        
        notifications = notifications[:limit]
        
        return {
            "success": True,
            "data": {
                "notifications": notifications,
                "total": len(notifications),
                "unread_count": len([n for n in notifications if not n["read"]])
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: UserProfile = Depends(get_current_active_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """
    Mark a notification as read
    
    Args:
        notification_id: ID of the notification to mark as read
        
    Returns:
        Success status
    """
    try:
        # In a real implementation, you'd update the notification in the database
        # For now, we'll just return success
        
        return {
            "success": True,
            "message": f"Notification {notification_id} marked as read"
        }
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/read-all")
async def mark_all_notifications_read(
    current_user: UserProfile = Depends(get_current_active_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """
    Mark all notifications as read for the current user
    
    Returns:
        Success status
    """
    try:
        # In a real implementation, you'd update all notifications in the database
        # For now, we'll just return success
        
        return {
            "success": True,
            "message": "All notifications marked as read"
        }
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
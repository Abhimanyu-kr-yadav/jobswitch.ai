"""
Job Discovery API endpoints
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from app.core.database import get_database
from app.core.auth import get_current_user
from app.models.user import UserProfile
from app.models.job import Job, JobRecommendation, JobApplication, SavedJob
from app.agents.job_discovery import JobDiscoveryAgent
from app.integrations.watsonx import WatsonXClient
from app.integrations.job_connectors import job_connector_manager
from app.core.orchestrator import orchestrator
from app.core.exceptions import AgentException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/discover")
async def discover_jobs(
    search_params: Dict[str, Any] = None,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Discover new job opportunities for the current user
    
    Args:
        search_params: Optional search parameters to override user preferences
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Job discovery results
    """
    try:
        # Create job discovery task
        task_data = {
            "user_id": current_user.user_id,
            "search_params": search_params or {}
        }
        
        # Submit task to orchestrator
        task_id = await orchestrator.create_task(
            agent_id="job_discovery_agent",
            task_type="discover_jobs",
            payload=task_data
        )
        
        return {
            "success": True,
            "message": "Job discovery task submitted",
            "task_id": task_id,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error submitting job discovery task: {str(e)}")
        
        # Check if this is an agent not registered error
        if "not registered" in str(e).lower():
            # Provide fallback response for missing agent
            return await _handle_missing_job_discovery_agent(current_user, db, search_params)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start job discovery"
        )


@router.get("/recommendations")
async def get_job_recommendations(
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    min_score: float = Query(0.0, ge=0.0, le=1.0, description="Minimum compatibility score"),
    feedback_filter: Optional[str] = Query(None, description="Filter by user feedback"),
    sort_by: str = Query("compatibility_score", description="Sort field"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Get personalized job recommendations for the current user with enhanced filtering
    
    Args:
        limit: Number of recommendations to return
        offset: Offset for pagination
        min_score: Minimum compatibility score filter
        feedback_filter: Filter by user feedback (interested, not_interested, applied)
        sort_by: Sort field (compatibility_score, created_at, skill_match_score)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Job recommendations with compatibility scores
    """
    try:
        # Build query with filters
        recommendations_query = db.query(JobRecommendation).filter(
            JobRecommendation.user_id == current_user.user_id,
            JobRecommendation.compatibility_score >= min_score
        )
        
        # Apply feedback filter
        if feedback_filter:
            if feedback_filter == "no_feedback":
                recommendations_query = recommendations_query.filter(JobRecommendation.user_feedback.is_(None))
            else:
                recommendations_query = recommendations_query.filter(JobRecommendation.user_feedback == feedback_filter)
        
        # Apply sorting
        if sort_by == "created_at":
            recommendations_query = recommendations_query.order_by(desc(JobRecommendation.created_at))
        elif sort_by == "skill_match_score":
            recommendations_query = recommendations_query.order_by(desc(JobRecommendation.skill_match_score))
        else:  # Default to compatibility_score
            recommendations_query = recommendations_query.order_by(desc(JobRecommendation.compatibility_score))
        
        total_count = recommendations_query.count()
        recommendations = recommendations_query.offset(offset).limit(limit).all()
        
        # Get job details for each recommendation
        recommendation_data = []
        for rec in recommendations:
            job = db.query(Job).filter(Job.job_id == rec.job_id).first()
            if job and job.is_active:
                # Parse recommendation context for enhanced data
                context = rec.recommendation_context or {}
                
                recommendation_data.append({
                    "recommendation_id": rec.id,
                    "job": job.to_dict(),
                    "compatibility_score": rec.compatibility_score,
                    "reasoning": rec.reasoning,
                    "detailed_scores": {
                        "skill_match": rec.skill_match_score,
                        "experience_match": rec.experience_match_score,
                        "location_match": rec.location_match_score,
                        "salary_match": rec.salary_match_score,
                        "career_growth": context.get("career_growth_score", 0.0)
                    },
                    "strengths": context.get("strengths", []),
                    "concerns": context.get("concerns", []),
                    "ai_recommendation": context.get("recommendation", ""),
                    "created_at": rec.created_at.isoformat(),
                    "user_feedback": rec.user_feedback
                })
        
        # If we don't have enough recommendations, generate new ones
        if len(recommendation_data) < limit and offset == 0:
            await _generate_new_recommendations(current_user, db)
        
        return {
            "success": True,
            "recommendations": recommendation_data,
            "total_count": total_count,
            "has_more": offset + len(recommendation_data) < total_count,
            "filters": {
                "min_score": min_score,
                "feedback_filter": feedback_filter,
                "sort_by": sort_by
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting job recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job recommendations"
        )


@router.post("/recommendations/generate")
async def generate_job_recommendations(
    limit: int = Query(10, ge=1, le=50),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Generate new job recommendations for the current user
    
    Args:
        limit: Number of recommendations to generate
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Generated recommendations
    """
    try:
        # Create recommendation generation task
        task_data = {
            "user_id": current_user.user_id,
            "limit": limit
        }
        
        # Submit task to orchestrator
        task_id = await orchestrator.create_task(
            agent_id="job_discovery_agent",
            task_type="recommend_jobs",
            payload=task_data
        )
        
        return {
            "success": True,
            "message": "Job recommendation task submitted",
            "task_id": task_id,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error generating job recommendations: {str(e)}")
        
        # Check if this is an agent not registered error
        if "not registered" in str(e).lower():
            # Provide fallback response for missing agent
            return await _handle_missing_job_recommendation_agent(current_user, db, limit)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate job recommendations"
        )


@router.get("/search")
async def search_jobs(
    q: str = Query(..., description="Search query"),
    location: Optional[str] = Query(None, description="Job location"),
    remote_type: Optional[str] = Query(None, description="Remote work type"),
    experience_level: Optional[str] = Query(None, description="Experience level"),
    employment_type: Optional[str] = Query(None, description="Employment type"),
    salary_min: Optional[int] = Query(None, description="Minimum salary"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Search jobs with filters
    
    Args:
        q: Search query
        location: Job location filter
        remote_type: Remote work type filter
        experience_level: Experience level filter
        employment_type: Employment type filter
        salary_min: Minimum salary filter
        limit: Number of results to return
        offset: Offset for pagination
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Search results
    """
    try:
        # Build search query
        query = db.query(Job).filter(Job.is_active == True)
        
        # Apply text search
        if q:
            query = query.filter(
                or_(
                    Job.title.ilike(f"%{q}%"),
                    Job.description.ilike(f"%{q}%"),
                    Job.company.ilike(f"%{q}%")
                )
            )
        
        # Apply filters
        if location:
            query = query.filter(Job.location.ilike(f"%{location}%"))
        
        if remote_type:
            query = query.filter(Job.remote_type == remote_type)
        
        if experience_level:
            query = query.filter(Job.experience_level == experience_level)
        
        if employment_type:
            query = query.filter(Job.employment_type == employment_type)
        
        if salary_min:
            query = query.filter(
                or_(
                    Job.salary_min >= salary_min,
                    Job.salary_max >= salary_min
                )
            )
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        jobs = query.order_by(desc(Job.scraped_at)).offset(offset).limit(limit).all()
        
        # Convert to dict format
        job_data = [job.to_dict() for job in jobs]
        
        return {
            "success": True,
            "jobs": job_data,
            "total_count": total_count,
            "has_more": offset + len(job_data) < total_count,
            "search_params": {
                "query": q,
                "location": location,
                "remote_type": remote_type,
                "experience_level": experience_level,
                "employment_type": employment_type,
                "salary_min": salary_min
            }
        }
        
    except Exception as e:
        logger.error(f"Error searching jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search jobs"
        )


@router.get("/{job_id}")
async def get_job_details(
    job_id: str,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Get detailed information for a specific job
    
    Args:
        job_id: Job identifier
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Detailed job information
    """
    try:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check if user has saved this job
        saved_job = db.query(SavedJob).filter(
            SavedJob.user_id == current_user.user_id,
            SavedJob.job_id == job_id,
            SavedJob.is_active == True
        ).first()
        
        # Check if user has applied to this job
        application = db.query(JobApplication).filter(
            JobApplication.user_id == current_user.user_id,
            JobApplication.job_id == job_id
        ).first()
        
        # Get recommendation if exists
        recommendation = db.query(JobRecommendation).filter(
            JobRecommendation.user_id == current_user.user_id,
            JobRecommendation.job_id == job_id
        ).first()
        
        job_data = job.to_dict()
        
        # Add compatibility data if recommendation exists
        if recommendation:
            context = recommendation.recommendation_context or {}
            job_data.update({
                "compatibility_analysis": {
                    "overall_score": recommendation.compatibility_score,
                    "detailed_scores": {
                        "skill_match": recommendation.skill_match_score,
                        "experience_match": recommendation.experience_match_score,
                        "location_match": recommendation.location_match_score,
                        "salary_match": recommendation.salary_match_score,
                        "career_growth": context.get("career_growth_score", 0.0)
                    },
                    "reasoning": recommendation.reasoning,
                    "strengths": context.get("strengths", []),
                    "concerns": context.get("concerns", []),
                    "ai_recommendation": context.get("recommendation", "")
                }
            })
        
        job_data.update({
            "is_saved": saved_job is not None,
            "is_applied": application is not None,
            "application_status": application.status if application else None,
            "saved_notes": saved_job.notes if saved_job else None,
            "saved_priority": saved_job.priority if saved_job else None
        })
        
        return {
            "success": True,
            "job": job_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job details"
        )


@router.post("/{job_id}/compatibility")
async def calculate_job_compatibility(
    job_id: str,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Calculate compatibility score for a specific job
    
    Args:
        job_id: Job identifier
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Compatibility analysis
    """
    try:
        # Create compatibility scoring task
        task_data = {
            "user_id": current_user.user_id,
            "job_id": job_id
        }
        
        # Submit task to orchestrator
        task_id = await orchestrator.create_task(
            agent_id="job_discovery_agent",
            task_type="score_job_compatibility",
            payload=task_data
        )
        
        return {
            "success": True,
            "message": "Compatibility analysis started",
            "task_id": task_id,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error calculating job compatibility: {str(e)}")
        
        # Check if this is an agent not registered error
        if "not registered" in str(e).lower():
            # Provide fallback response for missing agent
            return await _handle_missing_job_compatibility_agent(current_user, db, job_id)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate job compatibility"
        )


@router.post("/{job_id}/save")
async def save_job(
    job_id: str,
    notes: Optional[str] = None,
    priority: str = "medium",
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Save a job for later review
    
    Args:
        job_id: Job identifier
        notes: Optional notes about the job
        priority: Job priority (low, medium, high)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Save confirmation
    """
    try:
        # Check if job exists
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check if already saved
        existing_save = db.query(SavedJob).filter(
            SavedJob.user_id == current_user.user_id,
            SavedJob.job_id == job_id,
            SavedJob.is_active == True
        ).first()
        
        if existing_save:
            # Update existing save
            existing_save.notes = notes
            existing_save.priority = priority
            db.commit()
            
            return {
                "success": True,
                "message": "Job save updated",
                "already_saved": True
            }
        else:
            # Create new save
            saved_job = SavedJob(
                user_id=current_user.user_id,
                job_id=job_id,
                notes=notes,
                priority=priority
            )
            
            db.add(saved_job)
            db.commit()
            
            return {
                "success": True,
                "message": "Job saved successfully",
                "already_saved": False
            }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save job"
        )


@router.delete("/{job_id}/save")
async def unsave_job(
    job_id: str,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Remove a job from saved jobs
    
    Args:
        job_id: Job identifier
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Unsave confirmation
    """
    try:
        saved_job = db.query(SavedJob).filter(
            SavedJob.user_id == current_user.user_id,
            SavedJob.job_id == job_id,
            SavedJob.is_active == True
        ).first()
        
        if not saved_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved job not found"
            )
        
        saved_job.is_active = False
        db.commit()
        
        return {
            "success": True,
            "message": "Job removed from saved jobs"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error unsaving job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unsave job"
        )


@router.get("/saved/list")
async def get_saved_jobs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Get user's saved jobs
    
    Args:
        limit: Number of results to return
        offset: Offset for pagination
        priority: Priority filter
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of saved jobs
    """
    try:
        query = db.query(SavedJob).filter(
            SavedJob.user_id == current_user.user_id,
            SavedJob.is_active == True
        )
        
        if priority:
            query = query.filter(SavedJob.priority == priority)
        
        total_count = query.count()
        saved_jobs = query.order_by(desc(SavedJob.saved_at)).offset(offset).limit(limit).all()
        
        # Get job details for each saved job
        saved_jobs_data = []
        for saved_job in saved_jobs:
            job = db.query(Job).filter(Job.job_id == saved_job.job_id).first()
            if job:
                job_data = job.to_dict()
                job_data.update({
                    "saved_at": saved_job.saved_at.isoformat(),
                    "notes": saved_job.notes,
                    "priority": saved_job.priority,
                    "applied": saved_job.applied
                })
                saved_jobs_data.append(job_data)
        
        return {
            "success": True,
            "saved_jobs": saved_jobs_data,
            "total_count": total_count,
            "has_more": offset + len(saved_jobs_data) < total_count
        }
        
    except Exception as e:
        logger.error(f"Error getting saved jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get saved jobs"
        )


@router.post("/recommendations/{recommendation_id}/feedback")
async def provide_recommendation_feedback(
    recommendation_id: int,
    feedback: str,  # 'interested', 'not_interested', 'applied'
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Provide feedback on a job recommendation
    
    Args:
        recommendation_id: Recommendation identifier
        feedback: User feedback
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Feedback confirmation
    """
    try:
        recommendation = db.query(JobRecommendation).filter(
            JobRecommendation.id == recommendation_id,
            JobRecommendation.user_id == current_user.user_id
        ).first()
        
        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommendation not found"
            )
        
        if feedback not in ['interested', 'not_interested', 'applied']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid feedback value"
            )
        
        recommendation.user_feedback = feedback
        recommendation.feedback_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "message": "Feedback recorded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error providing recommendation feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record feedback"
        )


async def _generate_new_recommendations(user_profile: UserProfile, db: Session):
    """
    Helper function to generate new recommendations for a user
    """
    try:
        task_data = {
            "user_id": user_profile.user_id,
            "limit": 10
        }
        
        await orchestrator.create_task(
            agent_id="job_discovery_agent",
            task_type="recommend_jobs",
            payload=task_data
        )
        
    except Exception as e:
        logger.error(f"Error generating new recommendations: {str(e)}")


async def _handle_missing_job_discovery_agent(
    current_user: UserProfile, 
    db: Session, 
    search_params: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Handle job discovery when the agent is not available
    
    Args:
        current_user: Current authenticated user
        db: Database session
        search_params: Search parameters
        
    Returns:
        Fallback response with meaningful error message
    """
    logger.warning(f"Job discovery agent not available for user {current_user.user_id}")
    
    # Try to provide basic job search from database as fallback
    try:
        # Get basic job search results from database
        query = db.query(Job).filter(Job.is_active == True)
        
        # Apply basic filtering if search params provided
        if search_params:
            if search_params.get("location"):
                query = query.filter(Job.location.ilike(f"%{search_params['location']}%"))
            if search_params.get("title"):
                query = query.filter(Job.title.ilike(f"%{search_params['title']}%"))
        
        # Get recent jobs as fallback
        jobs = query.order_by(desc(Job.scraped_at)).limit(20).all()
        job_data = [job.to_dict() for job in jobs]
        
        return {
            "success": True,
            "message": "Job discovery service is temporarily unavailable. Showing recent job postings instead.",
            "task_id": None,
            "status": "completed_with_fallback",
            "fallback_used": True,
            "jobs": job_data,
            "total_count": len(job_data),
            "user_message": "Our AI-powered job discovery is temporarily unavailable, but we've found some recent job postings that might interest you. Please try again later for personalized recommendations."
        }
        
    except Exception as e:
        logger.error(f"Fallback job discovery also failed: {str(e)}")
        
        return {
            "success": False,
            "message": "Job discovery service is temporarily unavailable and fallback failed.",
            "task_id": None,
            "status": "failed",
            "fallback_used": True,
            "jobs": [],
            "total_count": 0,
            "user_message": "Our job discovery service is temporarily unavailable. Please try again in a few minutes. You can still browse saved jobs and use the search function."
        }


async def _handle_missing_job_recommendation_agent(
    current_user: UserProfile, 
    db: Session, 
    limit: int = 10
) -> Dict[str, Any]:
    """
    Handle job recommendations when the agent is not available
    
    Args:
        current_user: Current authenticated user
        db: Database session
        limit: Number of recommendations requested
        
    Returns:
        Fallback response with meaningful error message
    """
    logger.warning(f"Job recommendation agent not available for user {current_user.user_id}")
    
    # Try to provide existing recommendations or basic job suggestions as fallback
    try:
        # First, try to get existing recommendations from database
        existing_recommendations = db.query(JobRecommendation).filter(
            JobRecommendation.user_id == current_user.user_id
        ).order_by(desc(JobRecommendation.created_at)).limit(limit).all()
        
        if existing_recommendations:
            # Return existing recommendations
            recommendation_data = []
            for rec in existing_recommendations:
                job = db.query(Job).filter(Job.job_id == rec.job_id).first()
                if job and job.is_active:
                    recommendation_data.append({
                        "recommendation_id": rec.id,
                        "job": job.to_dict(),
                        "compatibility_score": rec.compatibility_score,
                        "reasoning": rec.reasoning,
                        "created_at": rec.created_at.isoformat(),
                        "user_feedback": rec.user_feedback
                    })
            
            return {
                "success": True,
                "message": "Job recommendation service is temporarily unavailable. Showing your previous recommendations.",
                "task_id": None,
                "status": "completed_with_fallback",
                "fallback_used": True,
                "recommendations": recommendation_data,
                "user_message": "Our AI recommendation engine is temporarily unavailable, but here are your previous personalized recommendations. Please try again later for new recommendations."
            }
        else:
            # No existing recommendations, provide general popular jobs
            popular_jobs = db.query(Job).filter(Job.is_active == True).order_by(
                desc(Job.scraped_at)
            ).limit(limit).all()
            
            fallback_recommendations = []
            for job in popular_jobs:
                fallback_recommendations.append({
                    "recommendation_id": None,
                    "job": job.to_dict(),
                    "compatibility_score": 0.5,  # Neutral score
                    "reasoning": "This is a recent job posting that might interest you.",
                    "created_at": datetime.utcnow().isoformat(),
                    "user_feedback": None
                })
            
            return {
                "success": True,
                "message": "Job recommendation service is temporarily unavailable. Showing recent job postings.",
                "task_id": None,
                "status": "completed_with_fallback",
                "fallback_used": True,
                "recommendations": fallback_recommendations,
                "user_message": "Our AI recommendation engine is temporarily unavailable. Here are some recent job postings that might interest you. Please try again later for personalized recommendations."
            }
        
    except Exception as e:
        logger.error(f"Fallback job recommendations also failed: {str(e)}")
        
        return {
            "success": False,
            "message": "Job recommendation service is temporarily unavailable and fallback failed.",
            "task_id": None,
            "status": "failed",
            "fallback_used": True,
            "recommendations": [],
            "user_message": "Our job recommendation service is temporarily unavailable. Please try again in a few minutes. You can still browse and search for jobs manually."
        }


async def _handle_missing_job_compatibility_agent(
    current_user: UserProfile, 
    db: Session, 
    job_id: str
) -> Dict[str, Any]:
    """
    Handle job compatibility analysis when the agent is not available
    
    Args:
        current_user: Current authenticated user
        db: Database session
        job_id: Job identifier
        
    Returns:
        Fallback response with meaningful error message
    """
    logger.warning(f"Job compatibility agent not available for user {current_user.user_id}, job {job_id}")
    
    # Try to provide existing compatibility analysis or basic response
    try:
        # Check if we have existing compatibility analysis for this job
        existing_recommendation = db.query(JobRecommendation).filter(
            JobRecommendation.user_id == current_user.user_id,
            JobRecommendation.job_id == job_id
        ).first()
        
        if existing_recommendation:
            # Return existing compatibility analysis
            context = existing_recommendation.recommendation_context or {}
            
            return {
                "success": True,
                "message": "Job compatibility service is temporarily unavailable. Showing previous analysis.",
                "task_id": None,
                "status": "completed_with_fallback",
                "fallback_used": True,
                "compatibility_analysis": {
                    "overall_score": existing_recommendation.compatibility_score,
                    "detailed_scores": {
                        "skill_match": existing_recommendation.skill_match_score,
                        "experience_match": existing_recommendation.experience_match_score,
                        "location_match": existing_recommendation.location_match_score,
                        "salary_match": existing_recommendation.salary_match_score,
                        "career_growth": context.get("career_growth_score", 0.0)
                    },
                    "reasoning": existing_recommendation.reasoning,
                    "strengths": context.get("strengths", []),
                    "concerns": context.get("concerns", []),
                    "ai_recommendation": context.get("recommendation", "")
                },
                "user_message": "Our AI compatibility analysis is temporarily unavailable, but here's your previous analysis for this job. Please try again later for updated analysis."
            }
        else:
            # No existing analysis, provide basic response
            return {
                "success": True,
                "message": "Job compatibility service is temporarily unavailable.",
                "task_id": None,
                "status": "completed_with_fallback",
                "fallback_used": True,
                "compatibility_analysis": {
                    "overall_score": 0.0,
                    "detailed_scores": {
                        "skill_match": 0.0,
                        "experience_match": 0.0,
                        "location_match": 0.0,
                        "salary_match": 0.0,
                        "career_growth": 0.0
                    },
                    "reasoning": "Compatibility analysis is temporarily unavailable.",
                    "strengths": [],
                    "concerns": [],
                    "ai_recommendation": "Please try again later for AI-powered compatibility analysis."
                },
                "user_message": "Our AI compatibility analysis is temporarily unavailable. Please try again in a few minutes to get detailed compatibility scores and recommendations for this job."
            }
        
    except Exception as e:
        logger.error(f"Fallback job compatibility also failed: {str(e)}")
        
        return {
            "success": False,
            "message": "Job compatibility service is temporarily unavailable and fallback failed.",
            "task_id": None,
            "status": "failed",
            "fallback_used": True,
            "user_message": "Our job compatibility service is temporarily unavailable. Please try again in a few minutes."
        }
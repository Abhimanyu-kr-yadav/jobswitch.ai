"""
Skills Analysis API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import logging

from app.core.database import get_database
from app.core.auth import get_current_user
from app.models.user import UserProfile
from app.agents.skills_analysis import SkillsAnalysisAgent
from app.integrations.watsonx import WatsonXClient
from app.integrations.langchain_utils import langchain_manager
from app.core.config import get_settings
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/agents/skills-analysis", tags=["Skills Analysis"])

# Pydantic models for request/response
class SkillExtractionRequest(BaseModel):
    resume_text: str
    update_profile: bool = True

class JobSkillExtractionRequest(BaseModel):
    job_description: str
    job_title: str = ""

class SkillGapAnalysisRequest(BaseModel):
    target_job_id: Optional[str] = None
    target_role: Optional[str] = None
    job_description: Optional[str] = None
    job_title: Optional[str] = None
    job_requirements: Optional[List[Dict[str, Any]]] = None

class LearningPathRequest(BaseModel):
    target_skills: Optional[List[str]] = None
    target_role: Optional[str] = None

class SkillsAnalysisResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# Initialize WatsonX client
settings = get_settings()
watsonx_client = WatsonXClient(
    api_key=settings.watsonx_api_key,
    base_url=settings.watsonx_base_url
)

# Initialize Skills Analysis Agent
skills_agent = SkillsAnalysisAgent(watsonx_client, langchain_manager)


@router.post("/extract-resume-skills", response_model=SkillsAnalysisResponse)
async def extract_skills_from_resume(
    request: SkillExtractionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Extract skills from resume text using NLP
    """
    try:
        user_id = current_user["user_id"]
        
        task_data = {
            "task_type": "extract_skills_from_resume",
            "user_id": user_id,
            "resume_text": request.resume_text,
            "update_profile": request.update_profile
        }
        
        result = await skills_agent.process_task(task_data)
        
        return SkillsAnalysisResponse(
            success=result.get("success", False),
            data=result.get("data"),
            recommendations=result.get("recommendations", []),
            error=result.get("error"),
            metadata=result.get("metadata")
        )
        
    except Exception as e:
        logger.error(f"Error extracting skills from resume: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract skills: {str(e)}"
        )


@router.post("/extract-job-skills", response_model=SkillsAnalysisResponse)
async def extract_skills_from_job(
    request: JobSkillExtractionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Extract required skills from job description
    """
    try:
        task_data = {
            "task_type": "extract_skills_from_job",
            "job_description": request.job_description,
            "job_title": request.job_title
        }
        
        result = await skills_agent.process_task(task_data)
        
        return SkillsAnalysisResponse(
            success=result.get("success", False),
            data=result.get("data"),
            recommendations=result.get("recommendations", []),
            error=result.get("error"),
            metadata=result.get("metadata")
        )
        
    except Exception as e:
        logger.error(f"Error extracting skills from job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract job skills: {str(e)}"
        )


@router.post("/analyze-skill-gaps", response_model=SkillsAnalysisResponse)
async def analyze_skill_gaps(
    request: SkillGapAnalysisRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Analyze skill gaps between user profile and target job/role
    """
    try:
        user_id = current_user["user_id"]
        
        task_data = {
            "task_type": "analyze_skill_gaps",
            "user_id": user_id,
            "target_job_id": request.target_job_id,
            "target_role": request.target_role,
            "job_description": request.job_description,
            "job_title": request.job_title,
            "job_requirements": request.job_requirements
        }
        
        result = await skills_agent.process_task(task_data)
        
        return SkillsAnalysisResponse(
            success=result.get("success", False),
            data=result.get("data"),
            recommendations=result.get("recommendations", []),
            error=result.get("error"),
            metadata=result.get("metadata")
        )
        
    except Exception as e:
        logger.error(f"Error analyzing skill gaps: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze skill gaps: {str(e)}"
        )


@router.post("/recommend-learning-paths", response_model=SkillsAnalysisResponse)
async def recommend_learning_paths(
    request: LearningPathRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Generate personalized learning path recommendations
    """
    try:
        user_id = current_user["user_id"]
        
        task_data = {
            "task_type": "recommend_learning_paths",
            "user_id": user_id,
            "target_skills": request.target_skills,
            "target_role": request.target_role
        }
        
        result = await skills_agent.process_task(task_data)
        
        return SkillsAnalysisResponse(
            success=result.get("success", False),
            data=result.get("data"),
            recommendations=result.get("recommendations", []),
            error=result.get("error"),
            metadata=result.get("metadata")
        )
        
    except Exception as e:
        logger.error(f"Error generating learning paths: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate learning paths: {str(e)}"
        )


@router.get("/analyze-user-skills", response_model=SkillsAnalysisResponse)
async def analyze_user_skills(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Comprehensive analysis of user's current skills
    """
    try:
        user_id = current_user["user_id"]
        
        task_data = {
            "task_type": "analyze_skills",
            "user_id": user_id
        }
        
        result = await skills_agent.process_task(task_data)
        
        return SkillsAnalysisResponse(
            success=result.get("success", False),
            data=result.get("data"),
            recommendations=result.get("recommendations", []),
            error=result.get("error"),
            metadata=result.get("metadata")
        )
        
    except Exception as e:
        logger.error(f"Error analyzing user skills: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze user skills: {str(e)}"
        )


@router.get("/recommendations", response_model=List[Dict[str, Any]])
async def get_skills_recommendations(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Get personalized skills development recommendations
    """
    try:
        user_id = current_user["user_id"]
        
        # Get user profile
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        recommendations = await skills_agent.get_recommendations(user_profile.to_dict())
        
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skills recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )


@router.get("/skills-categories")
async def get_skills_categories():
    """
    Get available skill categories for organization
    """
    try:
        return {
            "categories": skills_agent.skill_categories,
            "total_categories": len(skills_agent.skill_categories)
        }
        
    except Exception as e:
        logger.error(f"Error getting skill categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get skill categories: {str(e)}"
        )


@router.get("/agent-status")
async def get_agent_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Get Skills Analysis Agent status and health information
    """
    try:
        status_info = await skills_agent.get_status()
        
        return {
            "agent_status": status_info,
            "watsonx_available": bool(watsonx_client),
            "langchain_available": langchain_manager.available if langchain_manager else False
        }
        
    except Exception as e:
        logger.error(f"Error getting agent status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent status: {str(e)}"
        )
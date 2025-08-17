"""
Resume Optimization API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import logging
import json
import uuid

from app.core.database import get_database
from app.core.auth import get_current_user
from app.agents.resume_optimization import ResumeOptimizationAgent
from app.integrations.watsonx import WatsonXClient
from app.models.resume import Resume, ResumeAnalysis, ResumeOptimization
from app.models.user import UserProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents/resume-optimization", tags=["resume-optimization"])


def get_resume_agent(request: Request):
    """Get Resume Optimization Agent instance"""
    watsonx_client = request.app.state.watsonx_client
    return ResumeOptimizationAgent(watsonx_client)


@router.post("/parse")
async def parse_resume(
    resume_content: str = None,
    resume_file: UploadFile = File(None),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database),
    agent: ResumeOptimizationAgent = Depends(get_resume_agent)
):
    """
    Parse resume content and extract structured information
    """
    try:
        if not resume_content and not resume_file:
            raise HTTPException(status_code=400, detail="Either resume_content or resume_file is required")
        
        # Handle file upload
        file_content = None
        if resume_file:
            content = await resume_file.read()
            file_content = {
                "filename": resume_file.filename,
                "content": content.decode('utf-8') if resume_file.content_type.startswith('text') else str(content)
            }
        
        task_data = {
            "task_type": "parse_resume",
            "user_id": current_user.user_id,
            "resume_content": resume_content,
            "resume_file": file_content
        }
        
        result = await agent.process_task(task_data)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to parse resume"))
        
        return {
            "success": True,
            "data": result.get("data"),
            "message": "Resume parsed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error in parse_resume endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize")
async def optimize_resume(
    resume_id: str,
    job_id: str = None,
    optimization_type: str = "ats",
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database),
    agent: ResumeOptimizationAgent = Depends(get_resume_agent)
):
    """
    Optimize resume for specific job or general ATS compatibility
    """
    try:
        # Verify resume belongs to user
        resume = db.query(Resume).filter(
            Resume.resume_id == resume_id,
            Resume.user_id == current_user.user_id
        ).first()
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        task_data = {
            "task_type": "optimize_resume",
            "user_id": current_user.user_id,
            "resume_id": resume_id,
            "job_id": job_id,
            "optimization_type": optimization_type
        }
        
        result = await agent.process_task(task_data)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to optimize resume"))
        
        return {
            "success": True,
            "data": result.get("data"),
            "recommendations": result.get("recommendations", []),
            "message": "Resume optimized successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in optimize_resume endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-ats")
async def analyze_ats_compatibility(
    resume_id: str,
    job_id: str = None,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database),
    agent: ResumeOptimizationAgent = Depends(get_resume_agent)
):
    """
    Analyze resume for ATS compatibility and scoring
    """
    try:
        # Verify resume belongs to user
        resume = db.query(Resume).filter(
            Resume.resume_id == resume_id,
            Resume.user_id == current_user.user_id
        ).first()
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        task_data = {
            "task_type": "analyze_ats_compatibility",
            "user_id": current_user.user_id,
            "resume_id": resume_id,
            "job_id": job_id
        }
        
        result = await agent.process_task(task_data)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to analyze ATS compatibility"))
        
        return {
            "success": True,
            "data": result.get("data"),
            "recommendations": result.get("recommendations", []),
            "message": "ATS analysis completed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze_ats_compatibility endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_resume(
    job_id: str = None,
    template_id: str = None,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database),
    agent: ResumeOptimizationAgent = Depends(get_resume_agent)
):
    """
    Generate new resume from user profile and job requirements
    """
    try:
        task_data = {
            "task_type": "generate_resume",
            "user_id": current_user.user_id,
            "job_id": job_id,
            "template_id": template_id
        }
        
        result = await agent.process_task(task_data)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to generate resume"))
        
        return {
            "success": True,
            "data": result.get("data"),
            "message": "Resume generated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error in generate_resume endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations")
async def get_resume_recommendations(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database),
    agent: ResumeOptimizationAgent = Depends(get_resume_agent)
):
    """
    Get resume optimization recommendations for user
    """
    try:
        task_data = {
            "task_type": "get_resume_recommendations",
            "user_id": current_user.user_id
        }
        
        result = await agent.process_task(task_data)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to get recommendations"))
        
        return {
            "success": True,
            "recommendations": result.get("recommendations", []),
            "data": result.get("data"),
            "message": "Recommendations retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error in get_resume_recommendations endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/score")
async def score_resume(
    resume_id: str,
    job_id: str = None,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database),
    agent: ResumeOptimizationAgent = Depends(get_resume_agent)
):
    """
    Score resume against job requirements
    """
    try:
        # Verify resume belongs to user
        resume = db.query(Resume).filter(
            Resume.resume_id == resume_id,
            Resume.user_id == current_user.user_id
        ).first()
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        task_data = {
            "task_type": "score_resume",
            "user_id": current_user.user_id,
            "resume_id": resume_id,
            "job_id": job_id
        }
        
        result = await agent.process_task(task_data)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to score resume"))
        
        return {
            "success": True,
            "data": result.get("data"),
            "message": "Resume scored successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in score_resume endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resumes")
async def get_user_resumes(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Get all resumes for the current user
    """
    try:
        resumes = db.query(Resume).filter(
            Resume.user_id == current_user.user_id,
            Resume.is_active == True
        ).order_by(Resume.updated_at.desc()).all()
        
        resume_data = []
        for resume in resumes:
            resume_dict = resume.to_dict()
            
            # Get latest analysis if available
            latest_analysis = db.query(ResumeAnalysis).filter(
                ResumeAnalysis.resume_id == resume.resume_id
            ).order_by(ResumeAnalysis.created_at.desc()).first()
            
            if latest_analysis:
                resume_dict["latest_analysis"] = {
                    "ats_score": latest_analysis.ats_score,
                    "analysis_date": latest_analysis.created_at.isoformat()
                }
            
            resume_data.append(resume_dict)
        
        return {
            "success": True,
            "data": resume_data,
            "total": len(resume_data),
            "message": "Resumes retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error in get_user_resumes endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resumes/{resume_id}")
async def get_resume(
    resume_id: str,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Get specific resume by ID
    """
    try:
        resume = db.query(Resume).filter(
            Resume.resume_id == resume_id,
            Resume.user_id == current_user.user_id
        ).first()
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        resume_data = resume.to_dict()
        
        # Get all analyses for this resume
        analyses = db.query(ResumeAnalysis).filter(
            ResumeAnalysis.resume_id == resume_id
        ).order_by(ResumeAnalysis.created_at.desc()).all()
        
        resume_data["analyses"] = [analysis.to_dict() for analysis in analyses]
        
        # Get optimization history
        optimizations = db.query(ResumeOptimization).filter(
            ResumeOptimization.original_resume_id == resume_id
        ).all()
        
        resume_data["optimizations"] = [
            {
                "optimization_id": opt.optimization_id,
                "optimized_resume_id": opt.optimized_resume_id,
                "job_id": opt.job_id,
                "optimization_type": opt.optimization_type,
                "score_improvement": opt.score_improvement,
                "created_at": opt.created_at.isoformat()
            }
            for opt in optimizations
        ]
        
        return {
            "success": True,
            "data": resume_data,
            "message": "Resume retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_resume endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/resumes/{resume_id}")
async def delete_resume(
    resume_id: str,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Delete resume (soft delete)
    """
    try:
        resume = db.query(Resume).filter(
            Resume.resume_id == resume_id,
            Resume.user_id == current_user.user_id
        ).first()
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        resume.is_active = False
        db.commit()
        
        return {
            "success": True,
            "message": "Resume deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_resume endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/resumes/{resume_id}/primary")
async def set_primary_resume(
    resume_id: str,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Set resume as primary resume for user
    """
    try:
        # Verify resume belongs to user
        resume = db.query(Resume).filter(
            Resume.resume_id == resume_id,
            Resume.user_id == current_user.user_id
        ).first()
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Unset all other primary resumes for this user
        db.query(Resume).filter(
            Resume.user_id == current_user.user_id
        ).update({"is_primary": False})
        
        # Set this resume as primary
        resume.is_primary = True
        db.commit()
        
        return {
            "success": True,
            "message": "Primary resume updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in set_primary_resume endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resumes/{resume_id}/versions")
async def get_resume_versions(
    resume_id: str,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Get all versions of a resume
    """
    try:
        # Get base resume to verify ownership
        base_resume = db.query(Resume).filter(
            Resume.resume_id == resume_id,
            Resume.user_id == current_user.user_id
        ).first()
        
        if not base_resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Get all versions (including optimizations)
        versions = []
        
        # Add original resume
        versions.append({
            "resume_id": base_resume.resume_id,
            "version": base_resume.version,
            "title": base_resume.title,
            "created_at": base_resume.created_at.isoformat(),
            "is_original": True,
            "target_job_id": base_resume.target_job_id,
            "ats_score": base_resume.ats_score
        })
        
        # Get optimized versions
        optimizations = db.query(ResumeOptimization).filter(
            ResumeOptimization.original_resume_id == resume_id
        ).all()
        
        for opt in optimizations:
            optimized_resume = db.query(Resume).filter(
                Resume.resume_id == opt.optimized_resume_id
            ).first()
            
            if optimized_resume:
                versions.append({
                    "resume_id": optimized_resume.resume_id,
                    "version": optimized_resume.version,
                    "title": optimized_resume.title,
                    "created_at": optimized_resume.created_at.isoformat(),
                    "is_original": False,
                    "optimization_type": opt.optimization_type,
                    "target_job_id": optimized_resume.target_job_id,
                    "ats_score": optimized_resume.ats_score,
                    "score_improvement": opt.score_improvement
                })
        
        # Sort by creation date
        versions.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "success": True,
            "data": versions,
            "total": len(versions),
            "message": "Resume versions retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_resume_versions endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resumes/compare")
async def compare_resumes(
    resume_id_1: str,
    resume_id_2: str,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database),
    agent: ResumeOptimizationAgent = Depends(get_resume_agent)
):
    """
    Compare two resume versions and show differences
    """
    try:
        # Verify both resumes belong to user
        resume1 = db.query(Resume).filter(
            Resume.resume_id == resume_id_1,
            Resume.user_id == current_user.user_id
        ).first()
        
        resume2 = db.query(Resume).filter(
            Resume.resume_id == resume_id_2,
            Resume.user_id == current_user.user_id
        ).first()
        
        if not resume1 or not resume2:
            raise HTTPException(status_code=404, detail="One or both resumes not found")
        
        task_data = {
            "task_type": "compare_resumes",
            "user_id": current_user.user_id,
            "resume_id_1": resume_id_1,
            "resume_id_2": resume_id_2
        }
        
        result = await agent.process_task(task_data)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to compare resumes"))
        
        return {
            "success": True,
            "data": result.get("data"),
            "message": "Resume comparison completed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in compare_resumes endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resumes/{resume_id}/acceptance-probability")
async def calculate_acceptance_probability(
    resume_id: str,
    job_id: str,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database),
    agent: ResumeOptimizationAgent = Depends(get_resume_agent)
):
    """
    Calculate acceptance probability for resume-job matching
    """
    try:
        # Verify resume belongs to user
        resume = db.query(Resume).filter(
            Resume.resume_id == resume_id,
            Resume.user_id == current_user.user_id
        ).first()
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        task_data = {
            "task_type": "calculate_acceptance_probability",
            "user_id": current_user.user_id,
            "resume_id": resume_id,
            "job_id": job_id
        }
        
        result = await agent.process_task(task_data)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to calculate acceptance probability"))
        
        return {
            "success": True,
            "data": result.get("data"),
            "message": "Acceptance probability calculated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in calculate_acceptance_probability endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resumes/{resume_id}/create-version")
async def create_resume_version(
    resume_id: str,
    content: Dict[str, Any],
    title: str = None,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Create a new version of an existing resume
    """
    try:
        # Verify original resume belongs to user
        original_resume = db.query(Resume).filter(
            Resume.resume_id == resume_id,
            Resume.user_id == current_user.user_id
        ).first()
        
        if not original_resume:
            raise HTTPException(status_code=404, detail="Original resume not found")
        
        # Get next version number
        max_version = db.query(Resume).filter(
            Resume.user_id == current_user.user_id
        ).order_by(Resume.version.desc()).first()
        
        next_version = (max_version.version + 1) if max_version else 1
        
        # Create new resume version
        new_resume_id = str(uuid.uuid4())
        new_resume = Resume(
            resume_id=new_resume_id,
            user_id=current_user.user_id,
            version=next_version,
            title=title or f"{original_resume.title} - v{next_version}",
            content=content,
            template_id=original_resume.template_id,
            target_job_id=original_resume.target_job_id
        )
        
        db.add(new_resume)
        db.commit()
        
        return {
            "success": True,
            "data": new_resume.to_dict(),
            "message": "Resume version created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_resume_version endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

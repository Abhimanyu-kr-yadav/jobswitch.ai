"""
User profile management API endpoints
"""
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_database
from app.core.auth import get_current_user
from app.models.user import UserProfile
from app.models.auth_schemas import (
    UserProfileUpdate,
    UserProfileData,
    UserProfileResponse,
    SkillData,
    ExperienceData,
    EducationData,
    CertificationData,
    CareerGoalsData,
    JobPreferencesData,
    ApiResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["user profile"])


def calculate_profile_completion(user: UserProfile) -> float:
    """
    Calculate profile completion percentage
    
    Args:
        user: User profile
        
    Returns:
        Completion percentage (0.0 to 1.0)
    """
    completion_score = 0.0
    
    # Basic info (30%)
    basic_fields = [user.first_name, user.last_name, user.email]
    if all(basic_fields):
        completion_score += 0.3
    
    # Contact info (10%)
    if user.phone and user.location:
        completion_score += 0.1
    
    # Career info (20%)
    career_fields = [user.current_title, user.current_company, user.industry]
    if all(career_fields) and user.years_experience is not None:
        completion_score += 0.2
    
    # Skills (15%)
    if user.skills and len(user.skills) >= 5:
        completion_score += 0.15
    
    # Experience (15%)
    if user.experience and len(user.experience) >= 1:
        completion_score += 0.15
    
    # Education (5%)
    if user.education and len(user.education) >= 1:
        completion_score += 0.05
    
    # Career goals (5%)
    if user.career_goals:
        completion_score += 0.05
    
    return min(completion_score, 1.0)


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Get complete user profile with career data
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Complete user profile data
    """
    return UserProfileResponse.from_orm(current_user)


@router.put("/profile", response_model=ApiResponse)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Update user profile basic information
    
    Args:
        profile_data: Profile update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Update success response
    """
    try:
        # Update fields if provided
        update_data = profile_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(current_user, field):
                setattr(current_user, field, value)
        
        # Recalculate profile completion
        current_user.profile_completion = calculate_profile_completion(current_user)
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"Profile updated for user: {current_user.email}")
        
        return ApiResponse(
            success=True,
            message="Profile updated successfully",
            data={"profile_completion": current_user.profile_completion}
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Profile update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.put("/profile/skills", response_model=ApiResponse)
async def update_user_skills(
    skills: List[SkillData],
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Update user skills
    
    Args:
        skills: List of user skills
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Update success response
    """
    try:
        # Convert skills to dict format
        skills_data = [skill.dict() for skill in skills]
        current_user.skills = skills_data
        
        # Recalculate profile completion
        current_user.profile_completion = calculate_profile_completion(current_user)
        
        db.commit()
        
        logger.info(f"Skills updated for user: {current_user.email}")
        
        return ApiResponse(
            success=True,
            message="Skills updated successfully",
            data={"skills_count": len(skills_data)}
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Skills update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Skills update failed"
        )


@router.put("/profile/experience", response_model=ApiResponse)
async def update_user_experience(
    experience: List[ExperienceData],
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Update user work experience
    
    Args:
        experience: List of work experience
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Update success response
    """
    try:
        # Convert experience to dict format
        experience_data = [exp.dict() for exp in experience]
        current_user.experience = experience_data
        
        # Recalculate profile completion
        current_user.profile_completion = calculate_profile_completion(current_user)
        
        db.commit()
        
        logger.info(f"Experience updated for user: {current_user.email}")
        
        return ApiResponse(
            success=True,
            message="Experience updated successfully",
            data={"experience_count": len(experience_data)}
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Experience update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Experience update failed"
        )


@router.put("/profile/education", response_model=ApiResponse)
async def update_user_education(
    education: List[EducationData],
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Update user education
    
    Args:
        education: List of education records
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Update success response
    """
    try:
        # Convert education to dict format
        education_data = [edu.dict() for edu in education]
        current_user.education = education_data
        
        # Recalculate profile completion
        current_user.profile_completion = calculate_profile_completion(current_user)
        
        db.commit()
        
        logger.info(f"Education updated for user: {current_user.email}")
        
        return ApiResponse(
            success=True,
            message="Education updated successfully",
            data={"education_count": len(education_data)}
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Education update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Education update failed"
        )


@router.put("/profile/certifications", response_model=ApiResponse)
async def update_user_certifications(
    certifications: List[CertificationData],
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Update user certifications
    
    Args:
        certifications: List of certifications
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Update success response
    """
    try:
        # Convert certifications to dict format
        certifications_data = [cert.dict() for cert in certifications]
        current_user.certifications = certifications_data
        
        # Recalculate profile completion
        current_user.profile_completion = calculate_profile_completion(current_user)
        
        db.commit()
        
        logger.info(f"Certifications updated for user: {current_user.email}")
        
        return ApiResponse(
            success=True,
            message="Certifications updated successfully",
            data={"certifications_count": len(certifications_data)}
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Certifications update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Certifications update failed"
        )


@router.put("/profile/career-goals", response_model=ApiResponse)
async def update_career_goals(
    career_goals: CareerGoalsData,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Update user career goals
    
    Args:
        career_goals: Career goals data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Update success response
    """
    try:
        current_user.career_goals = career_goals.dict()
        
        # Recalculate profile completion
        current_user.profile_completion = calculate_profile_completion(current_user)
        
        db.commit()
        
        logger.info(f"Career goals updated for user: {current_user.email}")
        
        return ApiResponse(
            success=True,
            message="Career goals updated successfully"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Career goals update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Career goals update failed"
        )


@router.put("/profile/job-preferences", response_model=ApiResponse)
async def update_job_preferences(
    job_preferences: JobPreferencesData,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Update user job preferences
    
    Args:
        job_preferences: Job preferences data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Update success response
    """
    try:
        current_user.job_preferences = job_preferences.dict()
        
        # Recalculate profile completion
        current_user.profile_completion = calculate_profile_completion(current_user)
        
        db.commit()
        
        logger.info(f"Job preferences updated for user: {current_user.email}")
        
        return ApiResponse(
            success=True,
            message="Job preferences updated successfully"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Job preferences update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Job preferences update failed"
        )


@router.delete("/profile", response_model=ApiResponse)
async def delete_user_account(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Delete user account (soft delete by deactivating)
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Deletion success response
    """
    try:
        # Soft delete by deactivating account
        current_user.is_active = False
        db.commit()
        
        logger.info(f"User account deactivated: {current_user.email}")
        
        return ApiResponse(
            success=True,
            message="Account deactivated successfully"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Account deletion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Account deletion failed"
        )
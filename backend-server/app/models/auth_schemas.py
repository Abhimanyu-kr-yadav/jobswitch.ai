"""
Pydantic schemas for authentication and user management
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re


class UserRegistrationRequest(BaseModel):
    """User registration request schema"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=255)
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format"""
        if v and not re.match(r'^\+?[\d\s\-\(\)]+$', v):
            raise ValueError('Invalid phone number format')
        return v


class UserLoginRequest(BaseModel):
    """User login request schema"""
    email: EmailStr
    password: str


class UserProfileUpdate(BaseModel):
    """User profile update schema"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=255)
    current_title: Optional[str] = Field(None, max_length=255)
    current_company: Optional[str] = Field(None, max_length=255)
    years_experience: Optional[int] = Field(None, ge=0, le=50)
    industry: Optional[str] = Field(None, max_length=100)
    
    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format"""
        if v and not re.match(r'^\+?[\d\s\-\(\)]+$', v):
            raise ValueError('Invalid phone number format')
        return v


class SkillData(BaseModel):
    """Skill data schema"""
    name: str
    proficiency: int = Field(..., ge=1, le=5, description="Proficiency level from 1-5")
    category: Optional[str] = None
    years_experience: Optional[int] = Field(None, ge=0)


class ExperienceData(BaseModel):
    """Work experience data schema"""
    title: str
    company: str
    location: Optional[str] = None
    start_date: str  # ISO date string
    end_date: Optional[str] = None  # ISO date string, None if current
    description: Optional[str] = None
    skills_used: Optional[List[str]] = []


class EducationData(BaseModel):
    """Education data schema"""
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    start_date: str  # ISO date string
    end_date: Optional[str] = None  # ISO date string
    gpa: Optional[float] = Field(None, ge=0.0, le=4.0)
    description: Optional[str] = None


class CertificationData(BaseModel):
    """Certification data schema"""
    name: str
    issuing_organization: str
    issue_date: str  # ISO date string
    expiration_date: Optional[str] = None  # ISO date string
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None


class CareerGoalsData(BaseModel):
    """Career goals data schema"""
    target_roles: List[str] = []
    target_companies: Optional[List[str]] = []
    target_industries: Optional[List[str]] = []
    career_level: Optional[str] = Field(None, pattern="^(entry|mid|senior|executive)$")
    timeline: Optional[str] = None  # e.g., "6 months", "1 year"
    salary_expectations: Optional[Dict[str, Any]] = None
    location_preferences: Optional[List[str]] = []
    remote_preference: Optional[str] = Field(None, pattern="^(remote|hybrid|onsite|flexible)$")


class JobPreferencesData(BaseModel):
    """Job preferences data schema"""
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    currency: Optional[str] = Field("USD", max_length=3)
    employment_type: Optional[List[str]] = []  # full-time, part-time, contract, etc.
    company_size: Optional[List[str]] = []  # startup, small, medium, large, enterprise
    work_arrangement: Optional[str] = Field(None, pattern="^(remote|hybrid|onsite|flexible)$")
    travel_willingness: Optional[str] = Field(None, pattern="^(none|minimal|moderate|extensive)$")
    visa_sponsorship_needed: Optional[bool] = False


class UserProfileData(BaseModel):
    """Complete user profile data schema"""
    skills: Optional[List[SkillData]] = []
    experience: Optional[List[ExperienceData]] = []
    education: Optional[List[EducationData]] = []
    certifications: Optional[List[CertificationData]] = []
    career_goals: Optional[CareerGoalsData] = None
    job_preferences: Optional[JobPreferencesData] = None


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    """User profile response schema"""
    user_id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    location: Optional[str] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    years_experience: Optional[int] = None
    industry: Optional[str] = None
    profile_completion: float
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserProfileResponse(UserResponse):
    """Extended user profile response with career data"""
    skills: Optional[List[Dict[str, Any]]] = None
    experience: Optional[List[Dict[str, Any]]] = None
    education: Optional[List[Dict[str, Any]]] = None
    certifications: Optional[List[Dict[str, Any]]] = None
    career_goals: Optional[Dict[str, Any]] = None
    job_preferences: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class PasswordChangeRequest(BaseModel):
    """Password change request schema"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str


class ApiResponse(BaseModel):
    """Generic API response schema"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
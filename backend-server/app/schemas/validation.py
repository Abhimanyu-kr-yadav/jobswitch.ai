"""
Pydantic schemas for input validation across all API endpoints.
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from app.core.security import InputValidator

class BaseValidatedModel(BaseModel):
    """Base model with common validation"""
    
    @validator('*', pre=True)
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            return InputValidator.sanitize_string(v)
        return v

# Auth validation schemas
class LoginRequest(BaseValidatedModel):
    email: str = Field(..., max_length=254)
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator('email')
    def validate_email(cls, v):
        return InputValidator.validate_email(v)

class RegisterRequest(BaseValidatedModel):
    email: str = Field(..., max_length=254)
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    
    @validator('email')
    def validate_email(cls, v):
        return InputValidator.validate_email(v)
    
    @validator('password')
    def validate_password(cls, v):
        return InputValidator.validate_password(v)

class PasswordChangeRequest(BaseValidatedModel):
    current_password: str = Field(..., min_length=8, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        return InputValidator.validate_password(v)

# User profile validation schemas
class UserProfileUpdate(BaseValidatedModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=200)
    bio: Optional[str] = Field(None, max_length=1000)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    github_url: Optional[str] = Field(None, max_length=500)
    portfolio_url: Optional[str] = Field(None, max_length=500)

class SkillCreate(BaseValidatedModel):
    name: str = Field(..., max_length=100)
    level: int = Field(..., ge=1, le=5)
    category: str = Field(..., max_length=50)

class ExperienceCreate(BaseValidatedModel):
    company: str = Field(..., max_length=200)
    position: str = Field(..., max_length=200)
    description: str = Field(..., max_length=2000)
    start_date: datetime
    end_date: Optional[datetime] = None
    is_current: bool = False

class EducationCreate(BaseValidatedModel):
    institution: str = Field(..., max_length=200)
    degree: str = Field(..., max_length=200)
    field_of_study: str = Field(..., max_length=200)
    start_date: datetime
    end_date: Optional[datetime] = None
    gpa: Optional[float] = Field(None, ge=0.0, le=4.0)

# Job-related validation schemas
class JobSearchRequest(BaseValidatedModel):
    query: str = Field(..., max_length=500)
    location: Optional[str] = Field(None, max_length=200)
    job_type: Optional[str] = Field(None, max_length=50)
    experience_level: Optional[str] = Field(None, max_length=50)
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    remote_ok: Optional[bool] = False
    limit: Optional[int] = Field(10, ge=1, le=100)
    offset: Optional[int] = Field(0, ge=0)

class JobSaveRequest(BaseValidatedModel):
    job_id: str = Field(..., max_length=100)
    notes: Optional[str] = Field(None, max_length=1000)

# Resume validation schemas
class ResumeOptimizationRequest(BaseValidatedModel):
    resume_content: str = Field(..., max_length=50000)
    job_description: str = Field(..., max_length=20000)
    target_role: str = Field(..., max_length=200)

class ResumeCreateRequest(BaseValidatedModel):
    title: str = Field(..., max_length=200)
    content: str = Field(..., max_length=50000)
    template_id: Optional[str] = Field(None, max_length=50)

# Interview validation schemas
class MockInterviewRequest(BaseValidatedModel):
    job_role: str = Field(..., max_length=200)
    company: Optional[str] = Field(None, max_length=200)
    interview_type: str = Field(..., max_length=50)
    difficulty_level: str = Field(..., max_length=20)
    duration_minutes: int = Field(..., ge=5, le=120)

class InterviewResponseSubmission(BaseValidatedModel):
    session_id: str = Field(..., max_length=100)
    question_id: str = Field(..., max_length=100)
    response_text: str = Field(..., max_length=5000)
    response_duration: int = Field(..., ge=0)

# Skills analysis validation schemas
class SkillsAnalysisRequest(BaseValidatedModel):
    resume_text: Optional[str] = Field(None, max_length=50000)
    job_description: str = Field(..., max_length=20000)
    target_role: str = Field(..., max_length=200)

class LearningPathRequest(BaseValidatedModel):
    current_skills: List[str] = Field(..., max_items=50)
    target_skills: List[str] = Field(..., max_items=50)
    learning_style: Optional[str] = Field(None, max_length=50)
    time_commitment: Optional[int] = Field(None, ge=1, le=40)  # hours per week

# Networking validation schemas
class ContactSearchRequest(BaseValidatedModel):
    company: str = Field(..., max_length=200)
    role_keywords: List[str] = Field(..., max_items=10)
    seniority_level: Optional[str] = Field(None, max_length=50)
    department: Optional[str] = Field(None, max_length=100)

class EmailCampaignRequest(BaseValidatedModel):
    campaign_name: str = Field(..., max_length=200)
    target_company: str = Field(..., max_length=200)
    email_template: str = Field(..., max_length=5000)
    contact_ids: List[str] = Field(..., max_items=100)

class EmailTemplateRequest(BaseValidatedModel):
    template_name: str = Field(..., max_length=200)
    subject: str = Field(..., max_length=200)
    body: str = Field(..., max_length=5000)
    template_type: str = Field(..., max_length=50)

# Career strategy validation schemas
class CareerGoalRequest(BaseValidatedModel):
    target_role: str = Field(..., max_length=200)
    target_company: Optional[str] = Field(None, max_length=200)
    target_salary: Optional[int] = Field(None, ge=0)
    timeline_months: int = Field(..., ge=1, le=120)
    priority: str = Field(..., max_length=20)

class RoadmapGenerationRequest(BaseValidatedModel):
    current_role: str = Field(..., max_length=200)
    target_role: str = Field(..., max_length=200)
    current_skills: List[str] = Field(..., max_items=50)
    industry: Optional[str] = Field(None, max_length=100)
    experience_years: int = Field(..., ge=0, le=50)

# Technical interview validation schemas
class CodingChallengeRequest(BaseValidatedModel):
    difficulty: str = Field(..., max_length=20)
    topic: str = Field(..., max_length=100)
    language: str = Field(..., max_length=50)

class CodeSubmissionRequest(BaseValidatedModel):
    challenge_id: str = Field(..., max_length=100)
    code: str = Field(..., max_length=10000)
    language: str = Field(..., max_length=50)
    test_cases: Optional[List[Dict[str, Any]]] = Field(None, max_items=20)

# File upload validation schemas
class FileUploadRequest(BaseValidatedModel):
    filename: str = Field(..., max_length=255)
    file_size: int = Field(..., ge=1)
    file_type: str = Field(..., max_length=50)
    
    @validator('filename')
    def validate_filename(cls, v, values):
        file_size = values.get('file_size', 0)
        return InputValidator.validate_file_upload(v, file_size)

# Data export validation schemas
class DataExportRequest(BaseValidatedModel):
    data_types: List[str] = Field(..., max_items=20)
    format: str = Field(..., max_length=10)
    include_deleted: bool = False

class DataDeletionRequest(BaseValidatedModel):
    data_types: List[str] = Field(..., max_items=20)
    confirm_deletion: bool = Field(..., description="Must be True to confirm deletion")
    
    @validator('confirm_deletion')
    def must_confirm_deletion(cls, v):
        if not v:
            raise ValueError("Deletion must be explicitly confirmed")
        return v

# Generic validation schemas
class PaginationParams(BaseValidatedModel):
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)

class SearchParams(BaseValidatedModel):
    query: str = Field(..., max_length=500)
    filters: Optional[Dict[str, Any]] = None
    sort_by: Optional[str] = Field(None, max_length=50)
    sort_order: Optional[str] = Field("asc", pattern="^(asc|desc)$")

class BulkOperationRequest(BaseValidatedModel):
    item_ids: List[str] = Field(..., max_items=1000)
    operation: str = Field(..., max_length=50)
    parameters: Optional[Dict[str, Any]] = None

# Security-specific validation schemas
class SecurityEventRequest(BaseValidatedModel):
    event_type: str = Field(..., max_length=50)
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    description: str = Field(..., max_length=1000)
    metadata: Optional[Dict[str, Any]] = None

class IPWhitelistRequest(BaseValidatedModel):
    ip_addresses: List[str] = Field(..., max_items=100)
    action: str = Field(..., pattern="^(add|remove)$")
    reason: str = Field(..., max_length=500)

class RateLimitConfigRequest(BaseValidatedModel):
    endpoint_pattern: str = Field(..., max_length=200)
    requests_per_minute: int = Field(..., ge=1, le=10000)
    requests_per_hour: int = Field(..., ge=1, le=100000)
    burst_limit: Optional[int] = Field(None, ge=1, le=1000)

# Enhanced validation with security checks
class SecureFileUploadRequest(BaseValidatedModel):
    filename: str = Field(..., max_length=255)
    file_size: int = Field(..., ge=1, le=10*1024*1024)  # Max 10MB
    file_type: str = Field(..., max_length=50)
    checksum: str = Field(..., max_length=64)  # SHA-256 checksum
    
    @validator('filename')
    def validate_secure_filename(cls, v):
        # Additional security checks for filename
        import os
        import re
        
        # Remove path traversal attempts
        v = os.path.basename(v)
        
        # Check for dangerous characters
        if re.search(r'[<>:"|?*\x00-\x1f]', v):
            raise ValueError("Filename contains invalid characters")
        
        # Check for reserved names (Windows)
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL'] + [f'COM{i}' for i in range(1, 10)] + [f'LPT{i}' for i in range(1, 10)]
        if v.upper().split('.')[0] in reserved_names:
            raise ValueError("Filename uses reserved name")
        
        return InputValidator.validate_file_upload(v, 0)  # Size validated separately
    
    @validator('checksum')
    def validate_checksum(cls, v):
        import re
        if not re.match(r'^[a-fA-F0-9]{64}$', v):
            raise ValueError("Invalid SHA-256 checksum format")
        return v

class APIKeyRequest(BaseValidatedModel):
    name: str = Field(..., max_length=100)
    permissions: List[str] = Field(..., max_items=20)
    expires_at: Optional[datetime] = None
    ip_restrictions: Optional[List[str]] = Field(None, max_items=10)

class TwoFactorAuthRequest(BaseValidatedModel):
    method: str = Field(..., pattern="^(totp|sms|email)$")
    code: str = Field(..., min_length=6, max_length=8)
    
    @validator('code')
    def validate_2fa_code(cls, v):
        import re
        if not re.match(r'^\d{6,8}$', v):
            raise ValueError("2FA code must be 6-8 digits")
        return v

class PasswordResetRequest(BaseValidatedModel):
    email: str = Field(..., max_length=254)
    
    @validator('email')
    def validate_email(cls, v):
        return InputValidator.validate_email(v)

class PasswordResetConfirmRequest(BaseValidatedModel):
    token: str = Field(..., min_length=32, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_password(cls, v):
        return InputValidator.validate_password(v)
    
    @validator('token')
    def validate_token(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Invalid token format")
        return v

# Advanced input validation decorators
def validate_json_depth(max_depth: int = 10):
    """Decorator to validate JSON depth"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would be implemented in the actual endpoint
            return func(*args, **kwargs)
        return wrapper
    return decorator

def sanitize_html_input(allowed_tags: List[str] = None):
    """Decorator to sanitize HTML input"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would be implemented in the actual endpoint
            return func(*args, **kwargs)
        return wrapper
    return decorator

def validate_csrf_token(func):
    """Decorator to validate CSRF token"""
    def wrapper(*args, **kwargs):
        # This would be implemented in the actual endpoint
        return func(*args, **kwargs)
    return wrapper

# Custom validators for specific use cases
class SQLInjectionValidator:
    """Validator to detect SQL injection attempts"""
    
    @staticmethod
    def validate_query_param(value: str) -> str:
        """Validate query parameter for SQL injection"""
        import re
        
        # Common SQL injection patterns
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(--|#|/\*|\*/)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
            r"(;|\|\||&&)"
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValueError("Potentially malicious input detected")
        
        return value

class XSSValidator:
    """Validator to detect XSS attempts"""
    
    @staticmethod
    def validate_user_input(value: str) -> str:
        """Validate user input for XSS"""
        import re
        
        # Common XSS patterns
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<link[^>]*>",
            r"<meta[^>]*>"
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValueError("Potentially malicious script detected")
        
        return InputValidator.sanitize_html(value)

class PathTraversalValidator:
    """Validator to detect path traversal attempts"""
    
    @staticmethod
    def validate_file_path(value: str) -> str:
        """Validate file path for traversal attempts"""
        import os
        import re
        
        # Check for path traversal patterns
        if re.search(r'\.\.[/\\]', value):
            raise ValueError("Path traversal attempt detected")
        
        # Check for absolute paths
        if os.path.isabs(value):
            raise ValueError("Absolute paths not allowed")
        
        # Normalize path
        normalized = os.path.normpath(value)
        
        # Ensure normalized path doesn't escape
        if normalized.startswith('..'):
            raise ValueError("Path traversal attempt detected")
        
        return normalized

# Global validation utilities
def validate_request_signature(request_body: str, signature: str, secret: str) -> bool:
    """Validate request signature for webhook security"""
    import hmac
    import hashlib
    
    expected_signature = hmac.new(
        secret.encode(),
        request_body.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

def validate_jwt_token(token: str) -> Dict[str, Any]:
    """Validate JWT token structure and signature"""
    import jwt
    from app.core.config import settings
    
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"]
        )
        return payload
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid JWT token: {str(e)}")

def validate_api_key_format(api_key: str) -> bool:
    """Validate API key format"""
    import re
    
    # API key should be 32-64 characters, alphanumeric with dashes/underscores
    pattern = r'^[a-zA-Z0-9_-]{32,64}$'
    return bool(re.match(pattern, api_key))

# Rate limiting validation
class RateLimitValidator:
    """Validator for rate limiting parameters"""
    
    @staticmethod
    def validate_rate_limit_config(requests: int, window: int) -> tuple[int, int]:
        """Validate rate limit configuration"""
        if requests <= 0:
            raise ValueError("Requests must be positive")
        
        if window <= 0:
            raise ValueError("Window must be positive")
        
        if requests > 10000:
            raise ValueError("Requests limit too high")
        
        if window > 86400:  # 24 hours
            raise ValueError("Window too large")
        
        return requests, window
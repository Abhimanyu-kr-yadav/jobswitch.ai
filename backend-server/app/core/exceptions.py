"""
Custom Exception Classes for JobSwitch.ai Platform
"""
from typing import Any, Dict, Optional, List
from enum import Enum
import traceback
from datetime import datetime


class ErrorCode(Enum):
    """
    Standardized error codes for the platform
    """
    # General errors
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND_ERROR = "NOT_FOUND_ERROR"
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"
    
    # Agent errors
    AGENT_INITIALIZATION_ERROR = "AGENT_INITIALIZATION_ERROR"
    AGENT_PROCESSING_ERROR = "AGENT_PROCESSING_ERROR"
    AGENT_TIMEOUT_ERROR = "AGENT_TIMEOUT_ERROR"
    AGENT_COMMUNICATION_ERROR = "AGENT_COMMUNICATION_ERROR"
    AGENT_FALLBACK_ERROR = "AGENT_FALLBACK_ERROR"
    
    # AI/ML errors
    WATSONX_API_ERROR = "WATSONX_API_ERROR"
    WATSONX_ORCHESTRATE_ERROR = "WATSONX_ORCHESTRATE_ERROR"
    LANGCHAIN_ERROR = "LANGCHAIN_ERROR"
    MODEL_INFERENCE_ERROR = "MODEL_INFERENCE_ERROR"
    
    # External API errors
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"
    LINKEDIN_API_ERROR = "LINKEDIN_API_ERROR"
    INDEED_API_ERROR = "INDEED_API_ERROR"
    GLASSDOOR_API_ERROR = "GLASSDOOR_API_ERROR"
    ANGELLIST_API_ERROR = "ANGELLIST_API_ERROR"
    
    # Database errors
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    DATABASE_QUERY_ERROR = "DATABASE_QUERY_ERROR"
    DATABASE_CONSTRAINT_ERROR = "DATABASE_CONSTRAINT_ERROR"
    
    # Cache errors
    CACHE_CONNECTION_ERROR = "CACHE_CONNECTION_ERROR"
    CACHE_OPERATION_ERROR = "CACHE_OPERATION_ERROR"
    
    # File/Data errors
    FILE_NOT_FOUND_ERROR = "FILE_NOT_FOUND_ERROR"
    FILE_PROCESSING_ERROR = "FILE_PROCESSING_ERROR"
    DATA_EXPORT_ERROR = "DATA_EXPORT_ERROR"
    DATA_IMPORT_ERROR = "DATA_IMPORT_ERROR"
    
    # Email errors
    EMAIL_SEND_ERROR = "EMAIL_SEND_ERROR"
    EMAIL_TEMPLATE_ERROR = "EMAIL_TEMPLATE_ERROR"
    
    # Resume processing errors
    RESUME_PARSING_ERROR = "RESUME_PARSING_ERROR"
    RESUME_OPTIMIZATION_ERROR = "RESUME_OPTIMIZATION_ERROR"
    ATS_ANALYSIS_ERROR = "ATS_ANALYSIS_ERROR"
    
    # Interview errors
    INTERVIEW_SESSION_ERROR = "INTERVIEW_SESSION_ERROR"
    INTERVIEW_RECORDING_ERROR = "INTERVIEW_RECORDING_ERROR"
    INTERVIEW_FEEDBACK_ERROR = "INTERVIEW_FEEDBACK_ERROR"
    
    # Job discovery errors
    JOB_SEARCH_ERROR = "JOB_SEARCH_ERROR"
    JOB_RECOMMENDATION_ERROR = "JOB_RECOMMENDATION_ERROR"
    JOB_COMPATIBILITY_ERROR = "JOB_COMPATIBILITY_ERROR"
    
    # Skills analysis errors
    SKILLS_EXTRACTION_ERROR = "SKILLS_EXTRACTION_ERROR"
    SKILLS_GAP_ANALYSIS_ERROR = "SKILLS_GAP_ANALYSIS_ERROR"
    LEARNING_PATH_ERROR = "LEARNING_PATH_ERROR"
    
    # Networking errors
    CONTACT_DISCOVERY_ERROR = "CONTACT_DISCOVERY_ERROR"
    EMAIL_GENERATION_ERROR = "EMAIL_GENERATION_ERROR"
    CAMPAIGN_MANAGEMENT_ERROR = "CAMPAIGN_MANAGEMENT_ERROR"
    
    # Career strategy errors
    ROADMAP_GENERATION_ERROR = "ROADMAP_GENERATION_ERROR"
    GOAL_TRACKING_ERROR = "GOAL_TRACKING_ERROR"
    PROGRESS_ANALYSIS_ERROR = "PROGRESS_ANALYSIS_ERROR"


class JobSwitchException(Exception):
    """
    Base exception class for JobSwitch.ai platform
    """
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        retry_after: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.user_message = user_message or message
        self.retry_after = retry_after
        self.context = context or {}
        self.timestamp = datetime.utcnow()
        self.traceback = traceback.format_exc()
        
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary for API responses
        """
        return {
            "error": {
                "code": self.error_code.value,
                "message": self.user_message,
                "details": self.details,
                "timestamp": self.timestamp.isoformat(),
                "retry_after": self.retry_after,
                "context": self.context
            }
        }
    
    def to_log_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary for logging
        """
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "user_message": self.user_message,
            "details": self.details,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "traceback": self.traceback
        }


class ValidationException(JobSwitchException):
    """
    Exception for validation errors
    """
    
    def __init__(
        self,
        message: str,
        field_errors: Optional[Dict[str, List[str]]] = None,
        **kwargs
    ):
        self.field_errors = field_errors or {}
        details = kwargs.get('details', {})
        details['field_errors'] = self.field_errors
        kwargs['details'] = details
        
        super().__init__(
            message,
            error_code=ErrorCode.VALIDATION_ERROR,
            **kwargs
        )


class AuthenticationException(JobSwitchException):
    """
    Exception for authentication errors
    """
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            message,
            error_code=ErrorCode.AUTHENTICATION_ERROR,
            user_message="Authentication required. Please log in.",
            **kwargs
        )


class AuthorizationException(JobSwitchException):
    """
    Exception for authorization errors
    """
    
    def __init__(self, message: str = "Access denied", **kwargs):
        super().__init__(
            message,
            error_code=ErrorCode.AUTHORIZATION_ERROR,
            user_message="You don't have permission to access this resource.",
            **kwargs
        )


class NotFoundException(JobSwitchException):
    """
    Exception for resource not found errors
    """
    
    def __init__(self, resource: str, identifier: str = "", **kwargs):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        
        super().__init__(
            message,
            error_code=ErrorCode.NOT_FOUND_ERROR,
            user_message=f"The requested {resource.lower()} was not found.",
            **kwargs
        )


class RateLimitException(JobSwitchException):
    """
    Exception for rate limiting errors
    """
    
    def __init__(self, retry_after: int = 60, **kwargs):
        super().__init__(
            "Rate limit exceeded",
            error_code=ErrorCode.RATE_LIMIT_ERROR,
            user_message="Too many requests. Please try again later.",
            retry_after=retry_after,
            **kwargs
        )


class AgentException(JobSwitchException):
    """
    Base exception for agent-related errors
    """
    
    def __init__(
        self,
        message: str,
        agent_name: str,
        error_code: ErrorCode = ErrorCode.AGENT_PROCESSING_ERROR,
        **kwargs
    ):
        self.agent_name = agent_name
        context = kwargs.get('context', {})
        context['agent_name'] = agent_name
        kwargs['context'] = context
        
        super().__init__(message, error_code=error_code, **kwargs)


class AgentTimeoutException(AgentException):
    """
    Exception for agent timeout errors
    """
    
    def __init__(self, agent_name: str, timeout_seconds: int, **kwargs):
        message = f"Agent {agent_name} timed out after {timeout_seconds} seconds"
        super().__init__(
            message,
            agent_name=agent_name,
            error_code=ErrorCode.AGENT_TIMEOUT_ERROR,
            user_message="The operation is taking longer than expected. Please try again.",
            **kwargs
        )


class ExternalAPIException(JobSwitchException):
    """
    Exception for external API errors
    """
    
    def __init__(
        self,
        message: str,
        api_name: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        self.api_name = api_name
        self.status_code = status_code
        self.response_data = response_data or {}
        
        details = kwargs.get('details', {})
        details.update({
            'api_name': api_name,
            'status_code': status_code,
            'response_data': response_data
        })
        kwargs['details'] = details
        
        super().__init__(
            message,
            error_code=ErrorCode.EXTERNAL_API_ERROR,
            user_message="External service is temporarily unavailable. Please try again later.",
            **kwargs
        )


class DatabaseException(JobSwitchException):
    """
    Exception for database errors
    """
    
    def __init__(
        self,
        message: str,
        operation: str,
        error_code: ErrorCode = ErrorCode.DATABASE_QUERY_ERROR,
        **kwargs
    ):
        self.operation = operation
        context = kwargs.get('context', {})
        context['operation'] = operation
        kwargs['context'] = context
        
        super().__init__(
            message,
            error_code=error_code,
            user_message="A database error occurred. Please try again.",
            **kwargs
        )


class CacheException(JobSwitchException):
    """
    Exception for cache errors
    """
    
    def __init__(
        self,
        message: str,
        operation: str,
        error_code: ErrorCode = ErrorCode.CACHE_OPERATION_ERROR,
        **kwargs
    ):
        self.operation = operation
        context = kwargs.get('context', {})
        context['operation'] = operation
        kwargs['context'] = context
        
        super().__init__(
            message,
            error_code=error_code,
            user_message="Cache operation failed. The system will continue without caching.",
            **kwargs
        )


class WatsonXException(JobSwitchException):
    """
    Exception for WatsonX.ai errors
    """
    
    def __init__(
        self,
        message: str,
        model_id: Optional[str] = None,
        **kwargs
    ):
        self.model_id = model_id
        context = kwargs.get('context', {})
        if model_id:
            context['model_id'] = model_id
        kwargs['context'] = context
        
        super().__init__(
            message,
            error_code=ErrorCode.WATSONX_API_ERROR,
            user_message="AI service is temporarily unavailable. Please try again later.",
            **kwargs
        )


class LangChainException(JobSwitchException):
    """
    Exception for LangChain errors
    """
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code=ErrorCode.LANGCHAIN_ERROR,
            user_message="AI processing failed. Please try again.",
            **kwargs
        )


class FileProcessingException(JobSwitchException):
    """
    Exception for file processing errors
    """
    
    def __init__(
        self,
        message: str,
        filename: str,
        operation: str,
        **kwargs
    ):
        self.filename = filename
        self.operation = operation
        
        context = kwargs.get('context', {})
        context.update({
            'filename': filename,
            'operation': operation
        })
        kwargs['context'] = context
        
        super().__init__(
            message,
            error_code=ErrorCode.FILE_PROCESSING_ERROR,
            user_message=f"Failed to process file: {filename}",
            **kwargs
        )


class EmailException(JobSwitchException):
    """
    Exception for email-related errors
    """
    
    def __init__(
        self,
        message: str,
        recipient: Optional[str] = None,
        **kwargs
    ):
        self.recipient = recipient
        context = kwargs.get('context', {})
        if recipient:
            context['recipient'] = recipient
        kwargs['context'] = context
        
        super().__init__(
            message,
            error_code=ErrorCode.EMAIL_SEND_ERROR,
            user_message="Failed to send email. Please try again later.",
            **kwargs
        )
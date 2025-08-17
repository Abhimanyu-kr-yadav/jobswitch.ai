"""
Comprehensive Error Handler for FastAPI Application
"""
import uuid
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from .exceptions import (
    JobSwitchException, 
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    RateLimitException,
    AgentException,
    ExternalAPIException,
    DatabaseException,
    CacheException,
    WatsonXException,
    ErrorCode
)
from .logging_config import logging_manager, get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle all exceptions and provide consistent error responses
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and handle any exceptions
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Set request context for logging
        logging_manager.set_request_context(
            request_id=request_id,
            endpoint=str(request.url.path),
            method=request.method,
            user_id=getattr(request.state, 'user_id', None)
        )
        
        try:
            # Add request ID to request state
            request.state.request_id = request_id
            
            # Process request
            response = await call_next(request)
            
            return response
            
        except Exception as exc:
            # Log the error with full context
            logging_manager.log_error(
                exc,
                context={
                    "request_id": request_id,
                    "endpoint": str(request.url.path),
                    "method": request.method,
                    "user_agent": request.headers.get("user-agent"),
                    "client_ip": request.client.host if request.client else None
                },
                user_id=getattr(request.state, 'user_id', None)
            )
            
            # Handle the exception and return appropriate response
            return await self._handle_exception(exc, request_id)
        
        finally:
            # Clear logging context
            logging_manager.clear_context()
    
    async def _handle_exception(self, exc: Exception, request_id: str) -> JSONResponse:
        """
        Handle different types of exceptions and return appropriate responses
        """
        if isinstance(exc, JobSwitchException):
            return await self._handle_jobswitch_exception(exc, request_id)
        elif isinstance(exc, RequestValidationError):
            return await self._handle_validation_error(exc, request_id)
        elif isinstance(exc, HTTPException):
            return await self._handle_http_exception(exc, request_id)
        elif isinstance(exc, StarletteHTTPException):
            return await self._handle_starlette_exception(exc, request_id)
        else:
            return await self._handle_unhandled_exception(exc, request_id)
    
    async def _handle_jobswitch_exception(
        self, 
        exc: JobSwitchException, 
        request_id: str
    ) -> JSONResponse:
        """
        Handle JobSwitch custom exceptions
        """
        status_code = self._get_status_code_for_error(exc.error_code)
        
        error_response = exc.to_dict()
        error_response["error"]["request_id"] = request_id
        
        # Add retry_after header if specified
        headers = {}
        if exc.retry_after:
            headers["Retry-After"] = str(exc.retry_after)
        
        return JSONResponse(
            status_code=status_code,
            content=error_response,
            headers=headers
        )
    
    async def _handle_validation_error(
        self, 
        exc: RequestValidationError, 
        request_id: str
    ) -> JSONResponse:
        """
        Handle FastAPI validation errors
        """
        field_errors = {}
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            if field_path not in field_errors:
                field_errors[field_path] = []
            field_errors[field_path].append(error["msg"])
        
        error_response = {
            "error": {
                "code": ErrorCode.VALIDATION_ERROR.value,
                "message": "Validation failed",
                "details": {
                    "field_errors": field_errors,
                    "raw_errors": exc.errors()
                },
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id
            }
        }
        
        return JSONResponse(
            status_code=422,
            content=error_response
        )
    
    async def _handle_http_exception(
        self, 
        exc: HTTPException, 
        request_id: str
    ) -> JSONResponse:
        """
        Handle FastAPI HTTP exceptions
        """
        error_response = {
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "details": {},
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id
            }
        }
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response
        )
    
    async def _handle_starlette_exception(
        self, 
        exc: StarletteHTTPException, 
        request_id: str
    ) -> JSONResponse:
        """
        Handle Starlette HTTP exceptions
        """
        error_response = {
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "details": {},
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id
            }
        }
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response
        )
    
    async def _handle_unhandled_exception(
        self, 
        exc: Exception, 
        request_id: str
    ) -> JSONResponse:
        """
        Handle unexpected exceptions
        """
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        
        error_response = {
            "error": {
                "code": ErrorCode.INTERNAL_SERVER_ERROR.value,
                "message": "An unexpected error occurred",
                "details": {
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc)
                },
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id
            }
        }
        
        return JSONResponse(
            status_code=500,
            content=error_response
        )
    
    def _get_status_code_for_error(self, error_code: ErrorCode) -> int:
        """
        Map error codes to HTTP status codes
        """
        status_code_mapping = {
            ErrorCode.VALIDATION_ERROR: 422,
            ErrorCode.AUTHENTICATION_ERROR: 401,
            ErrorCode.AUTHORIZATION_ERROR: 403,
            ErrorCode.NOT_FOUND_ERROR: 404,
            ErrorCode.RATE_LIMIT_ERROR: 429,
            ErrorCode.AGENT_TIMEOUT_ERROR: 408,
            ErrorCode.EXTERNAL_API_ERROR: 502,
            ErrorCode.DATABASE_CONNECTION_ERROR: 503,
            ErrorCode.CACHE_CONNECTION_ERROR: 503,
            ErrorCode.WATSONX_API_ERROR: 502,
            ErrorCode.WATSONX_ORCHESTRATE_ERROR: 502,
            ErrorCode.LANGCHAIN_ERROR: 502,
            ErrorCode.FILE_PROCESSING_ERROR: 422,
            ErrorCode.EMAIL_SEND_ERROR: 502,
        }
        
        return status_code_mapping.get(error_code, 500)


# Exception handlers for specific FastAPI exception types
async def jobswitch_exception_handler(request: Request, exc: JobSwitchException):
    """
    Handler for JobSwitch custom exceptions
    """
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    status_code = ErrorHandlerMiddleware()._get_status_code_for_error(exc.error_code)
    
    error_response = exc.to_dict()
    error_response["error"]["request_id"] = request_id
    
    headers = {}
    if exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)
    
    return JSONResponse(
        status_code=status_code,
        content=error_response,
        headers=headers
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler for validation errors
    """
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    field_errors = {}
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        if field_path not in field_errors:
            field_errors[field_path] = []
        field_errors[field_path].append(error["msg"])
    
    error_response = {
        "error": {
            "code": ErrorCode.VALIDATION_ERROR.value,
            "message": "Validation failed",
            "details": {
                "field_errors": field_errors
            },
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }
    }
    
    return JSONResponse(
        status_code=422,
        content=error_response
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handler for HTTP exceptions
    """
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    error_response = {
        "error": {
            "code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "details": {},
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }
    }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


async def general_exception_handler(request: Request, exc: Exception):
    """
    Handler for general exceptions
    """
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    # Log the unhandled exception
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    error_response = {
        "error": {
            "code": ErrorCode.INTERNAL_SERVER_ERROR.value,
            "message": "An unexpected error occurred",
            "details": {},
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }
    }
    
    return JSONResponse(
        status_code=500,
        content=error_response
    )


# Health check for error handling system
class ErrorHandlingHealthCheck:
    """
    Health check for error handling system
    """
    
    def __init__(self):
        self.start_time = datetime.utcnow()
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of error handling system
        """
        error_stats = logging_manager.get_error_stats()
        
        return {
            "status": "healthy",
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "error_tracking": {
                "total_errors": error_stats.get("total_errors", 0),
                "error_counts": error_stats.get("error_counts", {}),
                "recent_errors_count": error_stats.get("recent_errors_count", 0)
            },
            "logging": {
                "handlers_configured": True,
                "log_level": logging.getLogger().level,
                "context_tracking": True
            }
        }


# Global health check instance
error_handling_health = ErrorHandlingHealthCheck()


def setup_error_handling(app):
    """
    Setup error handling for FastAPI application
    """
    # Add error handler middleware
    app.add_middleware(ErrorHandlerMiddleware)
    
    # Add exception handlers
    app.add_exception_handler(JobSwitchException, jobswitch_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Error handling configured for FastAPI application")


# Utility functions for raising common exceptions
def raise_not_found(resource: str, identifier: str = ""):
    """
    Raise a not found exception
    """
    raise NotFoundException(resource, identifier)


def raise_validation_error(message: str, field_errors: Optional[Dict[str, list]] = None):
    """
    Raise a validation exception
    """
    raise ValidationException(message, field_errors)


def raise_authentication_error(message: str = "Authentication required"):
    """
    Raise an authentication exception
    """
    raise AuthenticationException(message)


def raise_authorization_error(message: str = "Access denied"):
    """
    Raise an authorization exception
    """
    raise AuthorizationException(message)


def raise_rate_limit_error(retry_after: int = 60):
    """
    Raise a rate limit exception
    """
    raise RateLimitException(retry_after)


def raise_agent_error(agent_name: str, message: str):
    """
    Raise an agent exception
    """
    raise AgentException(message, agent_name)


def raise_external_api_error(api_name: str, message: str, status_code: Optional[int] = None):
    """
    Raise an external API exception
    """
    raise ExternalAPIException(message, api_name, status_code)


def raise_database_error(operation: str, message: str):
    """
    Raise a database exception
    """
    raise DatabaseException(message, operation)


def raise_watsonx_error(message: str, model_id: Optional[str] = None):
    """
    Raise a WatsonX exception
    """
    raise WatsonXException(message, model_id)
"""
Base Agent Interface for JobSwitch.ai AI Agents
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import time
import traceback

from app.core.logging_config import get_logger, log_agent_activity, log_error
from app.core.exceptions import (
    AgentException, 
    AgentTimeoutException, 
    WatsonXException,
    ErrorCode
)
from app.core.retry import retry, RetryConfig
from app.core.fallback import with_fallback
# from app.core.monitoring import monitoring_manager  # Temporarily disabled

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents in the JobSwitch.ai platform.
    Provides common functionality and interface for agent communication.
    """
    
    def __init__(self, agent_id: str, watsonx_client=None, langchain_config=None):
        self.agent_id = agent_id
        self.watsonx = watsonx_client
        self.langchain = langchain_config
        self.context = {}
        self.status = "initialized"
        self.created_at = datetime.utcnow()
        self.last_activity = None
        self.error_count = 0
        self.success_count = 0
        self.total_processing_time = 0.0
        
        # Configure retry settings for this agent
        self.retry_config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True
        )
        
    @abstractmethod
    async def _process_request_impl(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implementation of request processing - to be overridden by subclasses
        
        Args:
            user_input: User request data
            context: Current conversation/session context
            
        Returns:
            Structured response with recommendations and data
        """
        pass
    
    @with_fallback(
        operation="agent_process_request",
        service_type="agent",
        queueable=True
    )
    @retry(config="agent")
    async def process_request(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user request with comprehensive error handling and monitoring
        
        Args:
            user_input: User request data
            context: Current conversation/session context
            
        Returns:
            Structured response with recommendations and data
        """
        start_time = time.time()
        self.last_activity = datetime.utcnow()
        
        try:
            # Validate input
            if not self._validate_input(user_input):
                raise AgentException(
                    "Invalid input format",
                    agent_name=self.agent_id,
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Set agent context for logging
            from app.core.logging_config import logging_manager
            logging_manager.set_agent_context(
                agent_name=self.agent_id,
                user_id=context.get('user_id')
            )
            
            # Log activity start
            log_agent_activity(
                self.agent_id,
                "process_request",
                "started",
                {"input_keys": list(user_input.keys())}
            )
            
            # Update status
            self.status = "processing"
            
            # Process the request
            result = await self._process_request_impl(user_input, context)
            
            # Update success metrics
            self.success_count += 1
            processing_time = (time.time() - start_time) * 1000
            self.total_processing_time += processing_time
            
            # Record metrics (temporarily disabled)
            # monitoring_manager.record_agent_activity(
            #     self.agent_id,
            #     "process_request",
            #     processing_time,
            #     True
            # )
            
            # Log successful completion
            log_agent_activity(
                self.agent_id,
                "process_request",
                "completed",
                {
                    "processing_time_ms": processing_time,
                    "result_keys": list(result.keys()) if isinstance(result, dict) else None
                }
            )
            
            self.status = "ready"
            return result
            
        except Exception as e:
            # Update error metrics
            self.error_count += 1
            processing_time = (time.time() - start_time) * 1000
            
            # Record error metrics (temporarily disabled)
            # monitoring_manager.record_agent_activity(
            #     self.agent_id,
            #     "process_request",
            #     processing_time,
            #     False
            # )
            
            # Log error
            log_error(
                e,
                {
                    "agent_id": self.agent_id,
                    "operation": "process_request",
                    "processing_time_ms": processing_time,
                    "input_keys": list(user_input.keys()) if isinstance(user_input, dict) else None
                },
                user_id=context.get('user_id')
            )
            
            # Log agent activity failure
            log_agent_activity(
                self.agent_id,
                "process_request",
                "failed",
                {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "processing_time_ms": processing_time
                }
            )
            
            self.status = "error"
            
            # Re-raise as AgentException if not already
            if not isinstance(e, AgentException):
                raise AgentException(
                    f"Agent processing failed: {str(e)}",
                    agent_name=self.agent_id,
                    error_code=ErrorCode.AGENT_PROCESSING_ERROR
                ) from e
            else:
                raise
        
        finally:
            # Clear logging context
            from app.core.logging_config import logging_manager
            logging_manager.clear_context()
    
    @abstractmethod
    async def _get_recommendations_impl(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Implementation of recommendation generation - to be overridden by subclasses
        
        Args:
            user_profile: User profile data
            
        Returns:
            List of personalized recommendations
        """
        pass
    
    @with_fallback(
        operation="agent_get_recommendations",
        service_type="agent",
        queueable=False
    )
    @retry(config="agent")
    async def get_recommendations(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate personalized recommendations with error handling and monitoring
        
        Args:
            user_profile: User profile data
            
        Returns:
            List of personalized recommendations
        """
        start_time = time.time()
        self.last_activity = datetime.utcnow()
        
        try:
            # Validate input
            if not isinstance(user_profile, dict):
                raise AgentException(
                    "Invalid user profile format",
                    agent_name=self.agent_id,
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Set agent context for logging
            from app.core.logging_config import logging_manager
            logging_manager.set_agent_context(
                agent_name=self.agent_id,
                user_id=user_profile.get('user_id')
            )
            
            # Log activity start
            log_agent_activity(
                self.agent_id,
                "get_recommendations",
                "started",
                {"profile_keys": list(user_profile.keys())}
            )
            
            # Update status
            self.status = "generating_recommendations"
            
            # Generate recommendations
            recommendations = await self._get_recommendations_impl(user_profile)
            
            # Update success metrics
            processing_time = (time.time() - start_time) * 1000
            
            # Record metrics (temporarily disabled)
            # monitoring_manager.record_agent_activity(
            #     self.agent_id,
            #     "get_recommendations",
            #     processing_time,
            #     True
            # )
            
            # Log successful completion
            log_agent_activity(
                self.agent_id,
                "get_recommendations",
                "completed",
                {
                    "processing_time_ms": processing_time,
                    "recommendations_count": len(recommendations) if recommendations else 0
                }
            )
            
            self.status = "ready"
            return recommendations or []
            
        except Exception as e:
            # Update error metrics
            self.error_count += 1
            processing_time = (time.time() - start_time) * 1000
            
            # Record error metrics (temporarily disabled)
            # monitoring_manager.record_agent_activity(
            #     self.agent_id,
            #     "get_recommendations",
            #     processing_time,
            #     False
            # )
            
            # Log error
            log_error(
                e,
                {
                    "agent_id": self.agent_id,
                    "operation": "get_recommendations",
                    "processing_time_ms": processing_time
                },
                user_id=user_profile.get('user_id')
            )
            
            # Log agent activity failure
            log_agent_activity(
                self.agent_id,
                "get_recommendations",
                "failed",
                {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "processing_time_ms": processing_time
                }
            )
            
            self.status = "error"
            
            # Re-raise as AgentException if not already
            if not isinstance(e, AgentException):
                raise AgentException(
                    f"Recommendation generation failed: {str(e)}",
                    agent_name=self.agent_id,
                    error_code=ErrorCode.AGENT_PROCESSING_ERROR
                ) from e
            else:
                raise
        
        finally:
            # Clear logging context
            from app.core.logging_config import logging_manager
            logging_manager.clear_context()
    
    async def update_context(self, new_context: Dict[str, Any]) -> None:
        """
        Update agent context with new information
        
        Args:
            new_context: New context data to merge
        """
        self.context.update(new_context)
        logger.info(f"Agent {self.agent_id} context updated")
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status and health information
        
        Returns:
            Comprehensive agent status information
        """
        uptime_seconds = (datetime.utcnow() - self.created_at).total_seconds()
        avg_processing_time = (
            self.total_processing_time / max(self.success_count, 1)
            if self.success_count > 0 else 0
        )
        
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "uptime_seconds": uptime_seconds,
            "context_size": len(self.context),
            "metrics": {
                "success_count": self.success_count,
                "error_count": self.error_count,
                "total_requests": self.success_count + self.error_count,
                "success_rate": self.success_count / max(self.success_count + self.error_count, 1),
                "avg_processing_time_ms": avg_processing_time,
                "total_processing_time_ms": self.total_processing_time
            },
            "health": self._get_health_status()
        }
    
    def _get_health_status(self) -> str:
        """
        Determine agent health status based on metrics
        
        Returns:
            Health status string
        """
        total_requests = self.success_count + self.error_count
        
        if total_requests == 0:
            return "healthy"  # No requests yet
        
        success_rate = self.success_count / total_requests
        
        if success_rate >= 0.95:
            return "healthy"
        elif success_rate >= 0.80:
            return "degraded"
        elif success_rate >= 0.50:
            return "unhealthy"
        else:
            return "critical"
    
    async def reset_context(self) -> None:
        """Reset agent context to initial state"""
        self.context = {}
        logger.info(f"Agent {self.agent_id} context reset")
    
    def _validate_input(self, user_input: Dict[str, Any]) -> bool:
        """
        Validate user input format and required fields
        
        Args:
            user_input: Input to validate
            
        Returns:
            True if valid, False otherwise
        """
        return isinstance(user_input, dict) and len(user_input) > 0
    
    async def handle_timeout(self, timeout_seconds: int) -> None:
        """
        Handle agent timeout scenarios
        
        Args:
            timeout_seconds: Timeout duration that was exceeded
        """
        self.status = "timeout"
        self.error_count += 1
        
        log_agent_activity(
            self.agent_id,
            "timeout",
            "occurred",
            {"timeout_seconds": timeout_seconds}
        )
        
        raise AgentTimeoutException(
            self.agent_id,
            timeout_seconds
        )
    
    async def handle_external_api_error(self, api_name: str, error: Exception) -> None:
        """
        Handle external API errors with appropriate logging and fallback
        
        Args:
            api_name: Name of the external API that failed
            error: The original error
        """
        self.error_count += 1
        
        log_agent_activity(
            self.agent_id,
            "external_api_error",
            "occurred",
            {
                "api_name": api_name,
                "error": str(error),
                "error_type": type(error).__name__
            }
        )
        
        # This will be caught by the retry and fallback decorators
        from app.core.exceptions import ExternalAPIException
        raise ExternalAPIException(
            f"External API {api_name} failed: {str(error)}",
            api_name=api_name
        ) from error
    
    async def handle_watsonx_error(self, error: Exception, model_id: Optional[str] = None) -> None:
        """
        Handle WatsonX.ai API errors
        
        Args:
            error: The original error
            model_id: Optional model ID that failed
        """
        self.error_count += 1
        
        log_agent_activity(
            self.agent_id,
            "watsonx_error",
            "occurred",
            {
                "error": str(error),
                "error_type": type(error).__name__,
                "model_id": model_id
            }
        )
        
        raise WatsonXException(
            f"WatsonX.ai API failed: {str(error)}",
            model_id=model_id
        ) from error


class AgentResponse:
    """Standardized response format for all agents"""
    
    def __init__(self, success: bool, data: Any = None, error: str = None, 
                 recommendations: List[Dict] = None, metadata: Dict = None):
        self.success = success
        self.data = data
        self.error = error
        self.recommendations = recommendations or []
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary format"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "recommendations": self.recommendations,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class AgentError(Exception):
    """Custom exception for agent-related errors - deprecated, use AgentException instead"""
    
    def __init__(self, message: str, agent_id: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.agent_id = agent_id
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


# Utility functions for agent error handling
def handle_agent_exception(func):
    """
    Decorator to handle common agent exceptions
    """
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except asyncio.TimeoutError:
            await self.handle_timeout(30)  # Default 30 second timeout
        except Exception as e:
            if "watsonx" in str(e).lower() or "watson" in str(e).lower():
                await self.handle_watsonx_error(e)
            else:
                # Re-raise as AgentException
                raise AgentException(
                    f"Agent operation failed: {str(e)}",
                    agent_name=self.agent_id,
                    error_code=ErrorCode.AGENT_PROCESSING_ERROR
                ) from e
    
    return wrapper
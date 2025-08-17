"""
Fallback Mechanisms for JobSwitch.ai Platform
"""
import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar, Generic
from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime, timedelta
import json

from .exceptions import (
    JobSwitchException, 
    AgentException, 
    ExternalAPIException,
    WatsonXException,
    ErrorCode
)
from .logging_config import get_logger, log_error

logger = get_logger(__name__)

T = TypeVar('T')


class FallbackStrategy(Enum):
    """
    Available fallback strategies
    """
    ALTERNATIVE_SERVICE = "alternative_service"
    CACHED_RESPONSE = "cached_response"
    DEFAULT_RESPONSE = "default_response"
    DEGRADED_FUNCTIONALITY = "degraded_functionality"
    QUEUE_FOR_LATER = "queue_for_later"
    MANUAL_INTERVENTION = "manual_intervention"


class FallbackResult(Generic[T]):
    """
    Result of a fallback operation
    """
    
    def __init__(
        self,
        success: bool,
        data: Optional[T] = None,
        strategy_used: Optional[FallbackStrategy] = None,
        message: Optional[str] = None,
        degraded: bool = False
    ):
        self.success = success
        self.data = data
        self.strategy_used = strategy_used
        self.message = message
        self.degraded = degraded
        self.timestamp = datetime.utcnow()


class FallbackHandler(ABC, Generic[T]):
    """
    Abstract base class for fallback handlers
    """
    
    @abstractmethod
    async def can_handle(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """
        Check if this handler can handle the given exception
        """
        pass
    
    @abstractmethod
    async def handle(self, exception: Exception, context: Dict[str, Any]) -> FallbackResult[T]:
        """
        Handle the fallback
        """
        pass
    
    @property
    @abstractmethod
    def strategy(self) -> FallbackStrategy:
        """
        The fallback strategy this handler implements
        """
        pass


class CachedResponseHandler(FallbackHandler[T]):
    """
    Fallback to cached responses
    """
    
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
    
    @property
    def strategy(self) -> FallbackStrategy:
        return FallbackStrategy.CACHED_RESPONSE
    
    async def can_handle(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """
        Check if we have cached data for this request
        """
        cache_key = context.get('cache_key')
        if not cache_key:
            return False
        
        try:
            cached_data = await self.cache_manager.get(cache_key)
            return cached_data is not None
        except Exception:
            return False
    
    async def handle(self, exception: Exception, context: Dict[str, Any]) -> FallbackResult[T]:
        """
        Return cached response
        """
        cache_key = context.get('cache_key')
        try:
            cached_data = await self.cache_manager.get(cache_key)
            if cached_data:
                logger.info(f"Using cached response for fallback: {cache_key}")
                return FallbackResult(
                    success=True,
                    data=cached_data,
                    strategy_used=self.strategy,
                    message="Using cached response due to service unavailability",
                    degraded=True
                )
        except Exception as e:
            logger.error(f"Failed to retrieve cached response: {str(e)}")
        
        return FallbackResult(
            success=False,
            message="No cached response available"
        )


class DefaultResponseHandler(FallbackHandler[T]):
    """
    Fallback to default responses
    """
    
    def __init__(self, default_responses: Dict[str, Any]):
        self.default_responses = default_responses
    
    @property
    def strategy(self) -> FallbackStrategy:
        return FallbackStrategy.DEFAULT_RESPONSE
    
    async def can_handle(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """
        Check if we have a default response for this operation
        """
        operation = context.get('operation')
        return operation in self.default_responses
    
    async def handle(self, exception: Exception, context: Dict[str, Any]) -> FallbackResult[T]:
        """
        Return default response
        """
        operation = context.get('operation')
        default_data = self.default_responses.get(operation)
        
        if default_data:
            logger.info(f"Using default response for fallback: {operation}")
            return FallbackResult(
                success=True,
                data=default_data,
                strategy_used=self.strategy,
                message="Using default response due to service unavailability",
                degraded=True
            )
        
        return FallbackResult(
            success=False,
            message="No default response available"
        )


class AlternativeServiceHandler(FallbackHandler[T]):
    """
    Fallback to alternative services
    """
    
    def __init__(self, alternative_services: Dict[str, Callable]):
        self.alternative_services = alternative_services
    
    @property
    def strategy(self) -> FallbackStrategy:
        return FallbackStrategy.ALTERNATIVE_SERVICE
    
    async def can_handle(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """
        Check if we have an alternative service for this operation
        """
        service_type = context.get('service_type')
        return service_type in self.alternative_services
    
    async def handle(self, exception: Exception, context: Dict[str, Any]) -> FallbackResult[T]:
        """
        Use alternative service
        """
        service_type = context.get('service_type')
        alternative_service = self.alternative_services.get(service_type)
        
        if alternative_service:
            try:
                logger.info(f"Using alternative service for fallback: {service_type}")
                
                # Call alternative service with original parameters
                args = context.get('args', ())
                kwargs = context.get('kwargs', {})
                
                if asyncio.iscoroutinefunction(alternative_service):
                    result = await alternative_service(*args, **kwargs)
                else:
                    result = alternative_service(*args, **kwargs)
                
                return FallbackResult(
                    success=True,
                    data=result,
                    strategy_used=self.strategy,
                    message=f"Used alternative service: {service_type}",
                    degraded=True
                )
            except Exception as e:
                logger.error(f"Alternative service failed: {str(e)}")
                log_error(e, {"service_type": service_type, "fallback": True})
        
        return FallbackResult(
            success=False,
            message="Alternative service failed or unavailable"
        )


class DegradedFunctionalityHandler(FallbackHandler[T]):
    """
    Fallback to degraded functionality
    """
    
    def __init__(self, degraded_handlers: Dict[str, Callable]):
        self.degraded_handlers = degraded_handlers
    
    @property
    def strategy(self) -> FallbackStrategy:
        return FallbackStrategy.DEGRADED_FUNCTIONALITY
    
    async def can_handle(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """
        Check if we have a degraded handler for this operation
        """
        operation = context.get('operation')
        return operation in self.degraded_handlers
    
    async def handle(self, exception: Exception, context: Dict[str, Any]) -> FallbackResult[T]:
        """
        Use degraded functionality
        """
        operation = context.get('operation')
        degraded_handler = self.degraded_handlers.get(operation)
        
        if degraded_handler:
            try:
                logger.info(f"Using degraded functionality for fallback: {operation}")
                
                args = context.get('args', ())
                kwargs = context.get('kwargs', {})
                
                if asyncio.iscoroutinefunction(degraded_handler):
                    result = await degraded_handler(*args, **kwargs)
                else:
                    result = degraded_handler(*args, **kwargs)
                
                return FallbackResult(
                    success=True,
                    data=result,
                    strategy_used=self.strategy,
                    message=f"Used degraded functionality: {operation}",
                    degraded=True
                )
            except Exception as e:
                logger.error(f"Degraded functionality failed: {str(e)}")
                log_error(e, {"operation": operation, "fallback": True})
        
        return FallbackResult(
            success=False,
            message="Degraded functionality failed or unavailable"
        )


class QueueForLaterHandler(FallbackHandler[T]):
    """
    Queue requests for later processing
    """
    
    def __init__(self, queue_manager):
        self.queue_manager = queue_manager
    
    @property
    def strategy(self) -> FallbackStrategy:
        return FallbackStrategy.QUEUE_FOR_LATER
    
    async def can_handle(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """
        Check if this operation can be queued
        """
        return context.get('queueable', False)
    
    async def handle(self, exception: Exception, context: Dict[str, Any]) -> FallbackResult[T]:
        """
        Queue the request for later processing
        """
        try:
            task_data = {
                'operation': context.get('operation'),
                'args': context.get('args', ()),
                'kwargs': context.get('kwargs', {}),
                'user_id': context.get('user_id'),
                'timestamp': datetime.utcnow().isoformat(),
                'retry_count': context.get('retry_count', 0)
            }
            
            await self.queue_manager.enqueue(task_data)
            
            logger.info(f"Queued request for later processing: {context.get('operation')}")
            
            return FallbackResult(
                success=True,
                data={"queued": True, "message": "Request queued for processing"},
                strategy_used=self.strategy,
                message="Request queued for later processing",
                degraded=True
            )
        except Exception as e:
            logger.error(f"Failed to queue request: {str(e)}")
            log_error(e, {"operation": context.get('operation'), "fallback": True})
        
        return FallbackResult(
            success=False,
            message="Failed to queue request"
        )


class FallbackManager:
    """
    Manages fallback strategies and handlers
    """
    
    def __init__(self):
        self.handlers: List[FallbackHandler] = []
        self.fallback_stats = {
            "total_fallbacks": 0,
            "successful_fallbacks": 0,
            "failed_fallbacks": 0,
            "fallbacks_by_strategy": {},
            "fallbacks_by_exception": {}
        }
    
    def register_handler(self, handler: FallbackHandler):
        """
        Register a fallback handler
        """
        self.handlers.append(handler)
        logger.info(f"Registered fallback handler: {handler.strategy.value}")
    
    async def handle_failure(
        self,
        exception: Exception,
        context: Dict[str, Any]
    ) -> FallbackResult:
        """
        Handle a failure using available fallback strategies
        """
        self.fallback_stats["total_fallbacks"] += 1
        
        # Track exception type
        exception_type = type(exception).__name__
        if exception_type not in self.fallback_stats["fallbacks_by_exception"]:
            self.fallback_stats["fallbacks_by_exception"][exception_type] = 0
        self.fallback_stats["fallbacks_by_exception"][exception_type] += 1
        
        logger.warning(f"Attempting fallback for exception: {str(exception)}")
        
        # Try each handler in order
        for handler in self.handlers:
            try:
                if await handler.can_handle(exception, context):
                    result = await handler.handle(exception, context)
                    
                    if result.success:
                        self.fallback_stats["successful_fallbacks"] += 1
                        
                        # Track by strategy
                        strategy = result.strategy_used.value
                        if strategy not in self.fallback_stats["fallbacks_by_strategy"]:
                            self.fallback_stats["fallbacks_by_strategy"][strategy] = 0
                        self.fallback_stats["fallbacks_by_strategy"][strategy] += 1
                        
                        logger.info(f"Fallback successful using strategy: {strategy}")
                        return result
                    else:
                        logger.debug(f"Fallback handler failed: {result.message}")
            except Exception as handler_exception:
                logger.error(f"Fallback handler error: {str(handler_exception)}")
                log_error(handler_exception, {"handler": handler.__class__.__name__})
        
        # No fallback succeeded
        self.fallback_stats["failed_fallbacks"] += 1
        logger.error("All fallback strategies failed")
        
        return FallbackResult(
            success=False,
            message="All fallback strategies failed"
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get fallback statistics
        """
        return self.fallback_stats.copy()


# Global fallback manager
fallback_manager = FallbackManager()


def with_fallback(
    operation: str,
    cache_key: Optional[str] = None,
    service_type: Optional[str] = None,
    queueable: bool = False,
    **context_kwargs
):
    """
    Decorator to add fallback handling to functions
    """
    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs):
            context = {
                'operation': operation,
                'cache_key': cache_key,
                'service_type': service_type,
                'queueable': queueable,
                'args': args,
                'kwargs': kwargs,
                **context_kwargs
            }
            
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Primary operation failed: {str(e)}")
                
                fallback_result = await fallback_manager.handle_failure(e, context)
                
                if fallback_result.success:
                    return fallback_result.data
                else:
                    # Re-raise original exception if no fallback worked
                    raise e
        
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we can't use async fallbacks
            # Just execute the original function
            return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Default fallback responses for common operations
DEFAULT_FALLBACK_RESPONSES = {
    "job_search": {
        "jobs": [],
        "total": 0,
        "message": "Job search service is temporarily unavailable. Please try again later."
    },
    "job_recommendations": {
        "recommendations": [],
        "message": "Job recommendation service is temporarily unavailable. Please try again later."
    },
    "skills_analysis": {
        "skills": [],
        "gaps": [],
        "message": "Skills analysis service is temporarily unavailable. Please try again later."
    },
    "resume_optimization": {
        "optimized_resume": None,
        "suggestions": [],
        "ats_score": 0,
        "message": "Resume optimization service is temporarily unavailable. Please try again later."
    },
    "interview_questions": {
        "questions": [],
        "message": "Interview preparation service is temporarily unavailable. Please try again later."
    },
    "networking_contacts": {
        "contacts": [],
        "message": "Contact discovery service is temporarily unavailable. Please try again later."
    },
    "career_roadmap": {
        "roadmap": None,
        "milestones": [],
        "message": "Career strategy service is temporarily unavailable. Please try again later."
    }
}


def setup_default_fallbacks(cache_manager=None, queue_manager=None):
    """
    Setup default fallback handlers
    """
    # Default response handler
    default_handler = DefaultResponseHandler(DEFAULT_FALLBACK_RESPONSES)
    fallback_manager.register_handler(default_handler)
    
    # Cached response handler (if cache manager provided)
    if cache_manager:
        cache_handler = CachedResponseHandler(cache_manager)
        fallback_manager.register_handler(cache_handler)
    
    # Queue handler (if queue manager provided)
    if queue_manager:
        queue_handler = QueueForLaterHandler(queue_manager)
        fallback_manager.register_handler(queue_handler)
    
    logger.info("Default fallback handlers configured")


def get_fallback_stats() -> Dict[str, Any]:
    """
    Get fallback statistics
    """
    return fallback_manager.get_stats()
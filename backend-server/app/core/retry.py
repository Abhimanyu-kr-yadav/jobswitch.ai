"""
Retry Logic with Exponential Backoff for JobSwitch.ai Platform
"""
import asyncio
import time
import random
from typing import Any, Callable, Optional, Type, Union, List, Tuple
from functools import wraps
import logging
from datetime import datetime, timedelta

from .exceptions import (
    JobSwitchException, 
    ExternalAPIException, 
    AgentTimeoutException,
    DatabaseException,
    CacheException,
    WatsonXException,
    ErrorCode
)
from .logging_config import get_logger, log_error

logger = get_logger(__name__)


class RetryConfig:
    """
    Configuration for retry behavior
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        backoff_factor: float = 1.0
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.backoff_factor = backoff_factor
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for the given attempt
        """
        delay = self.base_delay * (self.exponential_base ** (attempt - 1)) * self.backoff_factor
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            # Add random jitter to prevent thundering herd
            jitter_range = delay * 0.1
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)


class RetryableException(Exception):
    """
    Base class for exceptions that should trigger retries
    """
    pass


class NonRetryableException(Exception):
    """
    Base class for exceptions that should not trigger retries
    """
    pass


# Default retry configurations for different scenarios
DEFAULT_RETRY_CONFIGS = {
    "external_api": RetryConfig(
        max_attempts=3,
        base_delay=1.0,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=True
    ),
    "database": RetryConfig(
        max_attempts=3,
        base_delay=0.5,
        max_delay=10.0,
        exponential_base=2.0,
        jitter=True
    ),
    "cache": RetryConfig(
        max_attempts=2,
        base_delay=0.1,
        max_delay=1.0,
        exponential_base=2.0,
        jitter=False
    ),
    "agent": RetryConfig(
        max_attempts=2,
        base_delay=2.0,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=True
    ),
    "watsonx": RetryConfig(
        max_attempts=3,
        base_delay=2.0,
        max_delay=60.0,
        exponential_base=2.0,
        jitter=True
    ),
    "file_processing": RetryConfig(
        max_attempts=2,
        base_delay=1.0,
        max_delay=5.0,
        exponential_base=2.0,
        jitter=False
    )
}


def is_retryable_exception(exception: Exception) -> bool:
    """
    Determine if an exception should trigger a retry
    """
    # Always retry these exception types
    if isinstance(exception, RetryableException):
        return True
    
    # Never retry these exception types
    if isinstance(exception, NonRetryableException):
        return False
    
    # JobSwitch exceptions - check specific error codes
    if isinstance(exception, JobSwitchException):
        non_retryable_codes = {
            ErrorCode.VALIDATION_ERROR,
            ErrorCode.AUTHENTICATION_ERROR,
            ErrorCode.AUTHORIZATION_ERROR,
            ErrorCode.NOT_FOUND_ERROR,
            ErrorCode.RATE_LIMIT_ERROR
        }
        return exception.error_code not in non_retryable_codes
    
    # External API exceptions - retry on server errors
    if isinstance(exception, ExternalAPIException):
        if exception.status_code:
            # Retry on 5xx errors and some 4xx errors
            return exception.status_code >= 500 or exception.status_code in [408, 429]
        return True
    
    # Database exceptions - retry on connection issues
    if isinstance(exception, DatabaseException):
        return "connection" in str(exception).lower()
    
    # Cache exceptions - always retry
    if isinstance(exception, CacheException):
        return True
    
    # WatsonX exceptions - retry on service errors
    if isinstance(exception, WatsonXException):
        return True
    
    # Timeout exceptions - retry
    if isinstance(exception, (asyncio.TimeoutError, AgentTimeoutException)):
        return True
    
    # Connection errors - retry
    if isinstance(exception, (ConnectionError, OSError)):
        return True
    
    # Default: don't retry unknown exceptions
    return False


class RetryStats:
    """
    Track retry statistics
    """
    
    def __init__(self):
        self.total_attempts = 0
        self.successful_retries = 0
        self.failed_retries = 0
        self.retry_by_exception = {}
        self.retry_by_operation = {}
    
    def record_attempt(self, operation: str, exception_type: str, success: bool):
        """
        Record a retry attempt
        """
        self.total_attempts += 1
        
        if success:
            self.successful_retries += 1
        else:
            self.failed_retries += 1
        
        # Track by exception type
        if exception_type not in self.retry_by_exception:
            self.retry_by_exception[exception_type] = {"attempts": 0, "successes": 0}
        
        self.retry_by_exception[exception_type]["attempts"] += 1
        if success:
            self.retry_by_exception[exception_type]["successes"] += 1
        
        # Track by operation
        if operation not in self.retry_by_operation:
            self.retry_by_operation[operation] = {"attempts": 0, "successes": 0}
        
        self.retry_by_operation[operation]["attempts"] += 1
        if success:
            self.retry_by_operation[operation]["successes"] += 1
    
    def get_stats(self) -> dict:
        """
        Get retry statistics
        """
        return {
            "total_attempts": self.total_attempts,
            "successful_retries": self.successful_retries,
            "failed_retries": self.failed_retries,
            "success_rate": self.successful_retries / max(self.total_attempts, 1),
            "retry_by_exception": self.retry_by_exception,
            "retry_by_operation": self.retry_by_operation
        }


# Global retry statistics
retry_stats = RetryStats()


def retry(
    config: Optional[Union[str, RetryConfig]] = None,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    non_retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    operation_name: Optional[str] = None
):
    """
    Decorator for adding retry logic to functions
    
    Args:
        config: Retry configuration (string key or RetryConfig object)
        retryable_exceptions: Tuple of exception types that should trigger retries
        non_retryable_exceptions: Tuple of exception types that should not trigger retries
        operation_name: Name of the operation for logging
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await _retry_async(
                func, args, kwargs, config, retryable_exceptions, 
                non_retryable_exceptions, operation_name
            )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return _retry_sync(
                func, args, kwargs, config, retryable_exceptions,
                non_retryable_exceptions, operation_name
            )
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


async def _retry_async(
    func: Callable,
    args: tuple,
    kwargs: dict,
    config: Optional[Union[str, RetryConfig]],
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]],
    non_retryable_exceptions: Optional[Tuple[Type[Exception], ...]],
    operation_name: Optional[str]
) -> Any:
    """
    Async retry implementation
    """
    # Get retry configuration
    if isinstance(config, str):
        retry_config = DEFAULT_RETRY_CONFIGS.get(config, DEFAULT_RETRY_CONFIGS["external_api"])
    elif isinstance(config, RetryConfig):
        retry_config = config
    else:
        retry_config = DEFAULT_RETRY_CONFIGS["external_api"]
    
    operation = operation_name or func.__name__
    last_exception = None
    
    for attempt in range(1, retry_config.max_attempts + 1):
        try:
            logger.debug(f"Attempting {operation} (attempt {attempt}/{retry_config.max_attempts})")
            result = await func(*args, **kwargs)
            
            if attempt > 1:
                logger.info(f"Operation {operation} succeeded on attempt {attempt}")
                retry_stats.record_attempt(operation, "success", True)
            
            return result
            
        except Exception as e:
            last_exception = e
            exception_type = type(e).__name__
            
            # Check if we should retry this exception
            should_retry = _should_retry_exception(
                e, retryable_exceptions, non_retryable_exceptions
            )
            
            if not should_retry or attempt == retry_config.max_attempts:
                logger.error(
                    f"Operation {operation} failed permanently on attempt {attempt}: {str(e)}"
                )
                retry_stats.record_attempt(operation, exception_type, False)
                log_error(e, {"operation": operation, "attempt": attempt})
                raise e
            
            delay = retry_config.calculate_delay(attempt)
            logger.warning(
                f"Operation {operation} failed on attempt {attempt}: {str(e)}. "
                f"Retrying in {delay:.2f} seconds..."
            )
            
            await asyncio.sleep(delay)
    
    # This should never be reached, but just in case
    if last_exception:
        raise last_exception


def _retry_sync(
    func: Callable,
    args: tuple,
    kwargs: dict,
    config: Optional[Union[str, RetryConfig]],
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]],
    non_retryable_exceptions: Optional[Tuple[Type[Exception], ...]],
    operation_name: Optional[str]
) -> Any:
    """
    Sync retry implementation
    """
    # Get retry configuration
    if isinstance(config, str):
        retry_config = DEFAULT_RETRY_CONFIGS.get(config, DEFAULT_RETRY_CONFIGS["external_api"])
    elif isinstance(config, RetryConfig):
        retry_config = config
    else:
        retry_config = DEFAULT_RETRY_CONFIGS["external_api"]
    
    operation = operation_name or func.__name__
    last_exception = None
    
    for attempt in range(1, retry_config.max_attempts + 1):
        try:
            logger.debug(f"Attempting {operation} (attempt {attempt}/{retry_config.max_attempts})")
            result = func(*args, **kwargs)
            
            if attempt > 1:
                logger.info(f"Operation {operation} succeeded on attempt {attempt}")
                retry_stats.record_attempt(operation, "success", True)
            
            return result
            
        except Exception as e:
            last_exception = e
            exception_type = type(e).__name__
            
            # Check if we should retry this exception
            should_retry = _should_retry_exception(
                e, retryable_exceptions, non_retryable_exceptions
            )
            
            if not should_retry or attempt == retry_config.max_attempts:
                logger.error(
                    f"Operation {operation} failed permanently on attempt {attempt}: {str(e)}"
                )
                retry_stats.record_attempt(operation, exception_type, False)
                log_error(e, {"operation": operation, "attempt": attempt})
                raise e
            
            delay = retry_config.calculate_delay(attempt)
            logger.warning(
                f"Operation {operation} failed on attempt {attempt}: {str(e)}. "
                f"Retrying in {delay:.2f} seconds..."
            )
            
            time.sleep(delay)
    
    # This should never be reached, but just in case
    if last_exception:
        raise last_exception


def _should_retry_exception(
    exception: Exception,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]],
    non_retryable_exceptions: Optional[Tuple[Type[Exception], ...]]
) -> bool:
    """
    Determine if an exception should trigger a retry
    """
    # Check explicit non-retryable exceptions first
    if non_retryable_exceptions and isinstance(exception, non_retryable_exceptions):
        return False
    
    # Check explicit retryable exceptions
    if retryable_exceptions and isinstance(exception, retryable_exceptions):
        return True
    
    # Use default logic
    return is_retryable_exception(exception)


async def retry_async(
    func: Callable,
    *args,
    config: Optional[Union[str, RetryConfig]] = None,
    operation_name: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Async function to retry a coroutine
    """
    return await _retry_async(
        func, args, kwargs, config, None, None, operation_name
    )


def retry_sync(
    func: Callable,
    *args,
    config: Optional[Union[str, RetryConfig]] = None,
    operation_name: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Function to retry a synchronous function
    """
    return _retry_sync(
        func, args, kwargs, config, None, None, operation_name
    )


def get_retry_stats() -> dict:
    """
    Get global retry statistics
    """
    return retry_stats.get_stats()


# Circuit breaker pattern for external services
class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await self._call_async(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return self._call_sync(func, *args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    async def _call_async(self, func: Callable, *args, **kwargs):
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise JobSwitchException(
                    "Circuit breaker is OPEN",
                    error_code=ErrorCode.EXTERNAL_API_ERROR,
                    user_message="Service is temporarily unavailable"
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _call_sync(self, func: Callable, *args, **kwargs):
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise JobSwitchException(
                    "Circuit breaker is OPEN",
                    error_code=ErrorCode.EXTERNAL_API_ERROR,
                    user_message="Service is temporarily unavailable"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
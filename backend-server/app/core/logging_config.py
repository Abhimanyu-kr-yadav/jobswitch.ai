"""
Centralized Logging Configuration for JobSwitch.ai Platform
"""
import logging
import logging.handlers
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import traceback
from contextlib import contextmanager

from .config import settings
from .exceptions import JobSwitchException, ErrorCode


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON
        """
        # Get the formatted message safely
        try:
            message = record.getMessage()
        except Exception:
            message = str(record.msg)
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
            "process": record.process,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields from the record (safely)
        excluded_fields = {
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
            'filename', 'module', 'lineno', 'funcName', 'created',
            'msecs', 'relativeCreated', 'thread', 'threadName',
            'processName', 'process', 'getMessage', 'exc_info',
            'exc_text', 'stack_info', 'message'
        }
        
        for key, value in record.__dict__.items():
            if key not in excluded_fields and key not in log_entry:
                try:
                    log_entry[key] = value
                except Exception:
                    # Skip fields that can't be serialized
                    pass
        
        return json.dumps(log_entry, default=str)


class ContextFilter(logging.Filter):
    """
    Filter to add contextual information to log records
    """
    
    def __init__(self):
        super().__init__()
        self.context = {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add context to log record
        """
        for key, value in self.context.items():
            setattr(record, key, value)
        return True
    
    def set_context(self, **kwargs):
        """
        Set context variables
        """
        self.context.update(kwargs)
    
    def clear_context(self):
        """
        Clear all context variables
        """
        self.context.clear()


class ErrorTracker:
    """
    Track and aggregate errors for monitoring
    """
    
    def __init__(self):
        self.error_counts = {}
        self.recent_errors = []
        self.max_recent_errors = 1000
    
    def track_error(self, error_code: str, details: Dict[str, Any]):
        """
        Track an error occurrence
        """
        # Increment error count
        self.error_counts[error_code] = self.error_counts.get(error_code, 0) + 1
        
        # Add to recent errors
        error_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_code": error_code,
            "details": details
        }
        
        self.recent_errors.append(error_entry)
        
        # Keep only recent errors
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors = self.recent_errors[-self.max_recent_errors:]
    
    def get_error_stats(self) -> Dict[str, Any]:
        """
        Get error statistics
        """
        return {
            "error_counts": self.error_counts,
            "total_errors": sum(self.error_counts.values()),
            "recent_errors_count": len(self.recent_errors),
            "recent_errors": self.recent_errors[-10:]  # Last 10 errors
        }


class LoggingManager:
    """
    Centralized logging manager
    """
    
    def __init__(self):
        self.context_filter = ContextFilter()
        self.error_tracker = ErrorTracker()
        self._setup_logging()
    
    def _setup_logging(self):
        """
        Setup logging configuration
        """
        # Create logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, settings.log_level.upper()))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        if settings.environment == "development":
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        else:
            console_formatter = JSONFormatter()
        
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(self.context_filter)
        root_logger.addHandler(console_handler)
        
        # File handler for general logs
        file_handler = logging.handlers.RotatingFileHandler(
            logs_dir / "jobswitch.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(JSONFormatter())
        file_handler.addFilter(self.context_filter)
        root_logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            logs_dir / "errors.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        error_handler.addFilter(self.context_filter)
        root_logger.addHandler(error_handler)
        
        # Agent-specific handler
        agent_handler = logging.handlers.RotatingFileHandler(
            logs_dir / "agents.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        agent_handler.setFormatter(JSONFormatter())
        agent_handler.addFilter(self.context_filter)
        
        # Add agent handler to agent loggers
        agent_logger = logging.getLogger("app.agents")
        agent_logger.addHandler(agent_handler)
        
        # External API handler
        api_handler = logging.handlers.RotatingFileHandler(
            logs_dir / "external_apis.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        api_handler.setFormatter(JSONFormatter())
        api_handler.addFilter(self.context_filter)
        
        # Add API handler to integration loggers
        api_logger = logging.getLogger("app.integrations")
        api_logger.addHandler(api_handler)
        
        # Performance handler
        perf_handler = logging.handlers.RotatingFileHandler(
            logs_dir / "performance.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        perf_handler.setFormatter(JSONFormatter())
        perf_handler.addFilter(self.context_filter)
        
        # Add performance handler to performance logger
        perf_logger = logging.getLogger("app.performance")
        perf_logger.addHandler(perf_handler)
    
    def set_request_context(
        self,
        request_id: str,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None
    ):
        """
        Set request context for logging
        """
        context = {
            "request_id": request_id,
            "user_id": user_id,
            "endpoint": endpoint,
            "method": method
        }
        self.context_filter.set_context(**context)
    
    def set_agent_context(
        self,
        agent_name: str,
        task_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """
        Set agent context for logging
        """
        context = {
            "agent_name": agent_name,
            "task_id": task_id,
            "user_id": user_id
        }
        self.context_filter.set_context(**context)
    
    def clear_context(self):
        """
        Clear logging context
        """
        self.context_filter.clear_context()
    
    def log_error(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ):
        """
        Log an error with full context
        """
        logger = logging.getLogger(__name__)
        
        if isinstance(exception, JobSwitchException):
            error_data = exception.to_log_dict()
            self.error_tracker.track_error(
                exception.error_code.value,
                error_data
            )
        else:
            error_data = {
                "error_type": type(exception).__name__,
                "message": str(exception),
                "traceback": traceback.format_exc()
            }
            self.error_tracker.track_error(
                "UNHANDLED_EXCEPTION",
                error_data
            )
        
        # Add context
        if context:
            error_data.update(context)
        if user_id:
            error_data["user_id"] = user_id
        
        # Remove 'message' from error_data to avoid conflict with LogRecord
        log_message = error_data.pop('message', str(exception))
        
        logger.error(
            f"Error occurred: {log_message}",
            extra=error_data,
            exc_info=True
        )
    
    def log_performance(
        self,
        operation: str,
        duration: float,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log performance metrics
        """
        perf_logger = logging.getLogger("app.performance")
        
        perf_data = {
            "operation": operation,
            "duration_seconds": duration,
            "details": details or {}
        }
        
        perf_logger.info(
            f"Performance: {operation} took {duration:.3f}s",
            extra=perf_data
        )
    
    def log_agent_activity(
        self,
        agent_name: str,
        activity: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log agent activity
        """
        agent_logger = logging.getLogger("app.agents")
        
        activity_data = {
            "agent_name": agent_name,
            "activity": activity,
            "status": status,
            "details": details or {}
        }
        
        agent_logger.info(
            f"Agent {agent_name}: {activity} - {status}",
            extra=activity_data
        )
    
    def log_external_api_call(
        self,
        api_name: str,
        endpoint: str,
        method: str,
        status_code: int,
        duration: float,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log external API calls
        """
        api_logger = logging.getLogger("app.integrations")
        
        api_data = {
            "api_name": api_name,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "duration_seconds": duration,
            "details": details or {}
        }
        
        level = logging.INFO if 200 <= status_code < 400 else logging.WARNING
        api_logger.log(
            level,
            f"API Call: {api_name} {method} {endpoint} - {status_code} ({duration:.3f}s)",
            extra=api_data
        )
    
    def get_error_stats(self) -> Dict[str, Any]:
        """
        Get error statistics
        """
        return self.error_tracker.get_error_stats()


# Global logging manager instance
logging_manager = LoggingManager()


@contextmanager
def log_context(**kwargs):
    """
    Context manager for setting logging context
    """
    logging_manager.context_filter.set_context(**kwargs)
    try:
        yield
    finally:
        logging_manager.context_filter.clear_context()


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name
    """
    return logging.getLogger(name)


def log_error(
    exception: Exception,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None
):
    """
    Convenience function to log errors
    """
    logging_manager.log_error(exception, context, user_id)


def log_performance(
    operation: str,
    duration: float,
    details: Optional[Dict[str, Any]] = None
):
    """
    Convenience function to log performance metrics
    """
    logging_manager.log_performance(operation, duration, details)


def log_agent_activity(
    agent_name: str,
    activity: str,
    status: str,
    details: Optional[Dict[str, Any]] = None
):
    """
    Convenience function to log agent activity
    """
    logging_manager.log_agent_activity(agent_name, activity, status, details)


def log_external_api_call(
    api_name: str,
    endpoint: str,
    method: str,
    status_code: int,
    duration: float,
    details: Optional[Dict[str, Any]] = None
):
    """
    Convenience function to log external API calls
    """
    logging_manager.log_external_api_call(
        api_name, endpoint, method, status_code, duration, details
    )
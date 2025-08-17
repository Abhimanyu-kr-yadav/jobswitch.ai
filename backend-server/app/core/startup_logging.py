"""
Startup Logging and Performance Tracking Module
Provides comprehensive logging and error reporting for application startup
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from .logging_config import get_logger, log_performance, logging_manager

logger = get_logger(__name__)


class StartupPhase(Enum):
    """Enumeration of startup phases"""
    CORE_INFRASTRUCTURE = "core_infrastructure"
    MONITORING_OPTIMIZATION = "monitoring_optimization"
    AI_SERVICES = "ai_services"
    ORCHESTRATOR = "orchestrator"
    AGENT_REGISTRATION = "agent_registration"
    VALIDATION = "validation"
    COMPLETE = "complete"


@dataclass
class PhaseMetrics:
    """Metrics for a startup phase"""
    phase: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    success: bool = False
    errors: List[str] = None
    warnings: List[str] = None
    sub_steps: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.sub_steps is None:
            self.sub_steps = {}
    
    def complete(self, success: bool = True):
        """Mark phase as complete"""
        self.end_time = datetime.utcnow()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.success = success
    
    def add_error(self, error: str):
        """Add error to phase"""
        self.errors.append(error)
    
    def add_warning(self, warning: str):
        """Add warning to phase"""
        self.warnings.append(warning)
    
    def add_sub_step(self, step_name: str, data: Any):
        """Add sub-step data"""
        self.sub_steps[step_name] = data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "phase": self.phase,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "success": self.success,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
            "sub_steps": self.sub_steps
        }


class StartupLogger:
    """
    Comprehensive startup logging and performance tracking
    """
    
    def __init__(self):
        self.startup_start_time = datetime.utcnow()
        self.phase_metrics: Dict[str, PhaseMetrics] = {}
        self.current_phase: Optional[str] = None
        self.global_errors: List[str] = []
        self.global_warnings: List[str] = []
        self.dependency_checks: Dict[str, bool] = {}
        self.performance_metrics: Dict[str, float] = {}
        
    def start_phase(self, phase: StartupPhase, description: str = None) -> PhaseMetrics:
        """Start tracking a startup phase"""
        phase_name = phase.value
        
        # Complete previous phase if exists
        if self.current_phase and self.current_phase in self.phase_metrics:
            if not self.phase_metrics[self.current_phase].end_time:
                self.phase_metrics[self.current_phase].complete(success=True)
        
        # Start new phase
        self.current_phase = phase_name
        metrics = PhaseMetrics(phase=phase_name, start_time=datetime.utcnow())
        self.phase_metrics[phase_name] = metrics
        
        logger.info(
            f"Starting startup phase: {phase_name}",
            extra={
                "startup_event": "phase_start",
                "phase": phase_name,
                "phase_description": description,
                "phase_start_time": metrics.start_time.isoformat(),
                "total_elapsed": (metrics.start_time - self.startup_start_time).total_seconds()
            }
        )
        
        return metrics
    
    def complete_phase(self, phase: StartupPhase, success: bool = True, summary: str = None):
        """Complete a startup phase"""
        phase_name = phase.value
        
        if phase_name not in self.phase_metrics:
            logger.warning(f"Attempting to complete phase {phase_name} that was not started")
            return
        
        metrics = self.phase_metrics[phase_name]
        metrics.complete(success=success)
        
        # Log performance metric
        log_performance(f"startup_phase_{phase_name}", metrics.duration)
        
        logger.info(
            f"Completed startup phase: {phase_name}",
            extra={
                "startup_event": "phase_complete",
                "phase": phase_name,
                "phase_duration": metrics.duration,
                "phase_success": success,
                "phase_summary": summary,
                "error_count": len(metrics.errors),
                "warning_count": len(metrics.warnings),
                "total_elapsed": (metrics.end_time - self.startup_start_time).total_seconds()
            }
        )
        
        if not success:
            logger.error(
                f"Phase {phase_name} failed",
                extra={
                    "startup_event": "phase_failed",
                    "phase": phase_name,
                    "errors": metrics.errors,
                    "warnings": metrics.warnings
                }
            )
    
    def log_dependency_check(self, dependency: str, available: bool, details: Dict[str, Any] = None):
        """Log dependency check result"""
        self.dependency_checks[dependency] = available
        
        logger.debug(
            f"Dependency check: {dependency}",
            extra={
                "startup_event": "dependency_check",
                "dependency": dependency,
                "available": available,
                "details": details or {}
            }
        )
        
        if not available:
            warning = f"Dependency {dependency} not available"
            self.add_warning(warning)
    
    def log_component_initialization(self, component: str, duration: float, success: bool, details: Dict[str, Any] = None):
        """Log component initialization"""
        self.performance_metrics[f"init_{component}"] = duration
        
        logger.info(
            f"Component initialization: {component}",
            extra={
                "startup_event": "component_init",
                "component": component,
                "duration": duration,
                "success": success,
                "details": details or {}
            }
        )
        
        # Add to current phase if exists
        if self.current_phase and self.current_phase in self.phase_metrics:
            self.phase_metrics[self.current_phase].add_sub_step(
                f"init_{component}",
                {
                    "duration": duration,
                    "success": success,
                    "details": details
                }
            )
    
    def add_error(self, error: str, phase: StartupPhase = None):
        """Add error to startup tracking"""
        self.global_errors.append(error)
        
        if phase and phase.value in self.phase_metrics:
            self.phase_metrics[phase.value].add_error(error)
        elif self.current_phase and self.current_phase in self.phase_metrics:
            self.phase_metrics[self.current_phase].add_error(error)
        
        logger.error(
            f"Startup error: {error}",
            extra={
                "startup_event": "error",
                "error_message": error,
                "phase": phase.value if phase else self.current_phase
            }
        )
    
    def add_warning(self, warning: str, phase: StartupPhase = None):
        """Add warning to startup tracking"""
        self.global_warnings.append(warning)
        
        if phase and phase.value in self.phase_metrics:
            self.phase_metrics[phase.value].add_warning(warning)
        elif self.current_phase and self.current_phase in self.phase_metrics:
            self.phase_metrics[self.current_phase].add_warning(warning)
        
        logger.warning(
            f"Startup warning: {warning}",
            extra={
                "startup_event": "warning",
                "warning_message": warning,
                "phase": phase.value if phase else self.current_phase
            }
        )
    
    def log_startup_complete(self, success: bool = True):
        """Log startup completion with comprehensive summary"""
        startup_end_time = datetime.utcnow()
        total_duration = (startup_end_time - self.startup_start_time).total_seconds()
        
        # Complete current phase if exists
        if self.current_phase and self.current_phase in self.phase_metrics:
            if not self.phase_metrics[self.current_phase].end_time:
                self.phase_metrics[self.current_phase].complete(success=success)
        
        # Calculate statistics
        successful_phases = sum(1 for metrics in self.phase_metrics.values() if metrics.success)
        total_phases = len(self.phase_metrics)
        total_errors = len(self.global_errors)
        total_warnings = len(self.global_warnings)
        
        # Create comprehensive summary
        startup_summary = {
            "startup_success": success,
            "total_duration": total_duration,
            "startup_start_time": self.startup_start_time.isoformat(),
            "startup_end_time": startup_end_time.isoformat(),
            "phases_completed": successful_phases,
            "total_phases": total_phases,
            "phase_success_rate": (successful_phases / total_phases * 100) if total_phases > 0 else 0,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "dependency_checks": self.dependency_checks,
            "performance_metrics": self.performance_metrics,
            "phase_durations": {
                phase: metrics.duration for phase, metrics in self.phase_metrics.items() 
                if metrics.duration is not None
            }
        }
        
        # Log performance metric for total startup
        log_performance("application_startup", total_duration, startup_summary)
        
        if success:
            logger.info(
                f"Application startup completed successfully in {total_duration:.2f} seconds",
                extra={
                    "startup_event": "startup_complete",
                    "startup_summary": startup_summary
                }
            )
        else:
            logger.error(
                f"Application startup failed after {total_duration:.2f} seconds",
                extra={
                    "startup_event": "startup_failed",
                    "startup_summary": startup_summary,
                    "global_errors": self.global_errors,
                    "global_warnings": self.global_warnings
                }
            )
        
        # Log detailed phase breakdown
        logger.info("Startup phase breakdown:")
        for phase_name, metrics in self.phase_metrics.items():
            status = "✓" if metrics.success else "✗"
            duration_str = f"{metrics.duration:.2f}s" if metrics.duration else "incomplete"
            logger.info(f"  {status} {phase_name}: {duration_str}")
            
            if metrics.errors:
                for error in metrics.errors:
                    logger.info(f"    Error: {error}")
            
            if metrics.warnings:
                for warning in metrics.warnings:
                    logger.info(f"    Warning: {warning}")
        
        return startup_summary
    
    def get_startup_report(self) -> Dict[str, Any]:
        """Get comprehensive startup report"""
        current_time = datetime.utcnow()
        elapsed_time = (current_time - self.startup_start_time).total_seconds()
        
        return {
            "startup_start_time": self.startup_start_time.isoformat(),
            "current_time": current_time.isoformat(),
            "elapsed_time": elapsed_time,
            "current_phase": self.current_phase,
            "phases": {name: metrics.to_dict() for name, metrics in self.phase_metrics.items()},
            "global_errors": self.global_errors,
            "global_warnings": self.global_warnings,
            "dependency_checks": self.dependency_checks,
            "performance_metrics": self.performance_metrics
        }
    
    def export_startup_log(self, file_path: str = None):
        """Export startup log to file"""
        if file_path is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_path = f"logs/startup_log_{timestamp}.json"
        
        try:
            report = self.get_startup_report()
            with open(file_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Startup log exported to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to export startup log: {str(e)}")
            return None


# Global startup logger instance
startup_logger = StartupLogger()


def get_startup_logger() -> StartupLogger:
    """Get the global startup logger instance"""
    return startup_logger


def log_startup_error(error: str, phase: StartupPhase = None):
    """Convenience function to log startup error"""
    startup_logger.add_error(error, phase)


def log_startup_warning(warning: str, phase: StartupPhase = None):
    """Convenience function to log startup warning"""
    startup_logger.add_warning(warning, phase)


def log_component_init(component: str, duration: float, success: bool, details: Dict[str, Any] = None):
    """Convenience function to log component initialization"""
    startup_logger.log_component_initialization(component, duration, success, details)


def log_dependency_check(dependency: str, available: bool, details: Dict[str, Any] = None):
    """Convenience function to log dependency check"""
    startup_logger.log_dependency_check(dependency, available, details)
"""
Agent Orchestration Framework for JobSwitch.ai
Manages coordination between multiple AI agents using WatsonX Orchestrate
"""
import asyncio
import logging
import json
import uuid
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
from contextlib import asynccontextmanager

# Optional Redis import
try:
    import aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None

from app.agents.base import BaseAgent, AgentResponse, AgentError
from app.integrations.watsonx import WatsonXOrchestrate
from app.core.config import settings
from app.core.retry import retry, RetryConfig, retry_async
from app.core.exceptions import AgentException, ErrorCode

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class AgentStatus(Enum):
    HEALTHY = "healthy"
    BUSY = "busy"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


class MessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    CONTEXT_UPDATE = "context_update"
    HEALTH_CHECK = "health_check"


class AgentMessage:
    """Represents a message between agents"""
    
    def __init__(self, message_id: str, sender_id: str, recipient_id: str,
                 message_type: MessageType, payload: Dict[str, Any],
                 correlation_id: str = None):
        self.message_id = message_id
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.message_type = message_type
        self.payload = payload
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow()
        self.delivered = False
        self.response_received = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format"""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "message_type": self.message_type.value,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
            "delivered": self.delivered,
            "response_received": self.response_received
        }


class AgentTask:
    """Represents a task to be executed by an agent"""
    
    def __init__(self, task_id: str, agent_id: str, task_type: str, 
                 payload: Dict[str, Any], priority: TaskPriority = TaskPriority.MEDIUM,
                 retry_count: int = 0, max_retries: int = 3, timeout_seconds: int = 300):
        self.task_id = task_id
        self.agent_id = agent_id
        self.task_type = task_type
        self.payload = payload
        self.priority = priority
        self.status = TaskStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.error = None
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.dependencies = []  # List of task IDs this task depends on
        self.dependents = []    # List of task IDs that depend on this task
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary format"""
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "task_type": self.task_type,
            "payload": self.payload,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "dependencies": self.dependencies,
            "dependents": self.dependents
        }


class AgentRegistrationStatus:
    """Represents registration status of an agent"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.is_registered = False
        self.registration_time = None
        self.last_health_check = None
        self.error_message = None
        self.retry_count = 0
        self.registration_attempts = []  # List of registration attempt timestamps
        self.validation_passed = False
        
    def record_attempt(self, success: bool, error_message: str = None):
        """Record a registration attempt"""
        self.registration_attempts.append({
            'timestamp': datetime.utcnow(),
            'success': success,
            'error_message': error_message
        })
        
        if success:
            self.is_registered = True
            self.registration_time = datetime.utcnow()
            self.error_message = None
            self.validation_passed = True
        else:
            self.retry_count += 1
            self.error_message = error_message
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert registration status to dictionary format"""
        return {
            "agent_id": self.agent_id,
            "is_registered": self.is_registered,
            "registration_time": self.registration_time.isoformat() if self.registration_time else None,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "validation_passed": self.validation_passed,
            "total_attempts": len(self.registration_attempts),
            "registration_attempts": [
                {
                    'timestamp': attempt['timestamp'].isoformat(),
                    'success': attempt['success'],
                    'error_message': attempt['error_message']
                }
                for attempt in self.registration_attempts
            ]
        }


class AgentHealthStatus:
    """Represents health status of an agent"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.status = AgentStatus.HEALTHY
        self.last_heartbeat = datetime.utcnow()
        self.response_times = deque(maxlen=100)  # Keep last 100 response times
        self.error_count = 0
        self.success_count = 0
        self.current_load = 0  # Number of active tasks
        self.max_load = 10     # Maximum concurrent tasks
        self.metadata = {}
    
    def update_heartbeat(self):
        """Update last heartbeat timestamp"""
        self.last_heartbeat = datetime.utcnow()
    
    def add_response_time(self, response_time: float):
        """Add response time measurement"""
        self.response_times.append(response_time)
    
    def get_average_response_time(self) -> float:
        """Get average response time"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    def increment_error(self):
        """Increment error count"""
        self.error_count += 1
    
    def increment_success(self):
        """Increment success count"""
        self.success_count += 1
    
    def get_success_rate(self) -> float:
        """Get success rate as percentage"""
        total = self.error_count + self.success_count
        if total == 0:
            return 100.0
        return (self.success_count / total) * 100.0
    
    def is_healthy(self) -> bool:
        """Check if agent is healthy based on various metrics"""
        # Check heartbeat (should be within last 60 seconds)
        heartbeat_threshold = datetime.utcnow() - timedelta(seconds=60)
        if self.last_heartbeat < heartbeat_threshold:
            return False
        
        # Check success rate (should be above 80%)
        if self.get_success_rate() < 80.0 and (self.error_count + self.success_count) > 10:
            return False
        
        # Check load (should not exceed max load)
        if self.current_load > self.max_load:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert health status to dictionary format"""
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "average_response_time": self.get_average_response_time(),
            "error_count": self.error_count,
            "success_count": self.success_count,
            "success_rate": self.get_success_rate(),
            "current_load": self.current_load,
            "max_load": self.max_load,
            "is_healthy": self.is_healthy(),
            "metadata": self.metadata
        }


class AgentOrchestrator:
    """
    Central orchestrator for managing AI agents and coordinating their activities
    Integrates with WatsonX Orchestrate for advanced workflow management
    """
    
    def __init__(self, watsonx_orchestrate_config: Dict[str, Any] = None):
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_health: Dict[str, AgentHealthStatus] = {}
        self.agent_registration_status: Dict[str, AgentRegistrationStatus] = {}
        self.task_queue: List[AgentTask] = []
        self.active_tasks: Dict[str, AgentTask] = {}
        self.completed_tasks: Dict[str, AgentTask] = {}
        self.failed_tasks: Dict[str, AgentTask] = {}
        self.message_queue: List[AgentMessage] = []
        self.message_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.watsonx_orchestrate = None
        self.shared_context: Dict[str, Any] = {}
        self.context_subscribers: Dict[str, List[str]] = defaultdict(list)  # context_key -> [agent_ids]
        self.is_running = False
        self.redis_client = None
        self.health_check_interval = 30  # seconds
        self.max_queue_size = settings.task_queue_size
        self.max_concurrent_tasks = settings.max_concurrent_agents
        
        # Readiness tracking properties
        self._is_ready = False
        self._initialization_phase = "not_started"  # not_started, initializing, ready, failed
        self._initialization_start_time = None
        self._initialization_complete_time = None
        self._readiness_waiters = []  # List of futures waiting for readiness
        
        # Agent registration retry configuration
        self._registration_retry_config = RetryConfig(
            max_attempts=3,
            base_delay=2.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True
        )
        
        # Initialize WatsonX Orchestrate if config provided
        if watsonx_orchestrate_config:
            # Store config for later async initialization
            self._watsonx_config = watsonx_orchestrate_config
    
    async def _init_watsonx_orchestrate(self, config: Dict[str, Any]):
        """Initialize WatsonX Orchestrate client"""
        try:
            self.watsonx_orchestrate = WatsonXOrchestrate(
                api_key=config.get("api_key"),
                base_url=config.get("base_url")
            )
            logger.info("WatsonX Orchestrate initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WatsonX Orchestrate: {str(e)}")
    
    @property
    def is_ready(self) -> bool:
        """
        Check if orchestrator is ready to accept agent registrations and tasks
        
        Returns:
            True if orchestrator is fully initialized and ready
        """
        return self._is_ready
    
    async def wait_for_ready(self, timeout: float = 30.0) -> bool:
        """
        Wait for orchestrator to be ready
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if orchestrator became ready, False if timeout
        """
        if self._is_ready:
            return True
        
        # Create a future to wait for readiness
        future = asyncio.Future()
        self._readiness_waiters.append(future)
        
        try:
            # Wait for readiness with timeout
            await asyncio.wait_for(future, timeout=timeout)
            return True
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for orchestrator readiness after {timeout} seconds")
            return False
        finally:
            # Remove future from waiters list
            if future in self._readiness_waiters:
                self._readiness_waiters.remove(future)
    
    def _notify_readiness_waiters(self):
        """Notify all waiters that orchestrator is ready"""
        for future in self._readiness_waiters:
            if not future.done():
                future.set_result(True)
        self._readiness_waiters.clear()
    
    async def _init_redis(self):
        """Initialize Redis connection for distributed messaging"""
        try:
            if settings.redis_enabled and REDIS_AVAILABLE:
                self.redis_client = await aioredis.from_url(settings.redis_url)
                logger.info("Redis connection established for distributed messaging")
            elif settings.redis_enabled and not REDIS_AVAILABLE:
                logger.warning("Redis requested but aioredis not available. Using in-memory messaging.")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {str(e)}. Using in-memory messaging.")
    
    async def start(self):
        """Start the orchestrator and background tasks"""
        logger.info("Starting agent orchestrator initialization...")
        
        try:
            # Set initialization phase
            self._initialization_phase = "initializing"
            self._initialization_start_time = datetime.utcnow()
            
            # Initialize Redis connection
            logger.info("Initializing Redis connection...")
            await self._init_redis()
            
            # Initialize WatsonX Orchestrate if config was provided
            if hasattr(self, '_watsonx_config'):
                logger.info("Initializing WatsonX Orchestrate...")
                await self._init_watsonx_orchestrate(self._watsonx_config)
            
            # Set running state
            self.is_running = True
            
            # Start background tasks
            logger.info("Starting background tasks...")
            asyncio.create_task(self._process_task_queue())
            asyncio.create_task(self._process_message_queue())
            asyncio.create_task(self._health_check_loop())
            asyncio.create_task(self._cleanup_completed_tasks())
            
            # Mark as ready
            self._is_ready = True
            self._initialization_phase = "ready"
            self._initialization_complete_time = datetime.utcnow()
            
            # Notify any waiters
            self._notify_readiness_waiters()
            
            initialization_time = (self._initialization_complete_time - self._initialization_start_time).total_seconds()
            logger.info(f"Agent orchestrator started successfully in {initialization_time:.2f} seconds")
            
        except Exception as e:
            self._initialization_phase = "failed"
            self._is_ready = False
            logger.error(f"Failed to start agent orchestrator: {str(e)}")
            
            # Notify waiters of failure
            for future in self._readiness_waiters:
                if not future.done():
                    future.set_exception(e)
            self._readiness_waiters.clear()
            
            raise
    
    async def stop(self):
        """Stop the orchestrator and cleanup resources"""
        logger.info("Stopping agent orchestrator...")
        
        # Mark as not ready and not running
        self._is_ready = False
        self.is_running = False
        self._initialization_phase = "stopped"
        
        # Cancel any pending readiness waiters
        for future in self._readiness_waiters:
            if not future.done():
                future.cancel()
        self._readiness_waiters.clear()
        
        try:
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
                logger.info("Redis connection closed")
            
            # Close WatsonX Orchestrate connection
            if self.watsonx_orchestrate:
                await self.watsonx_orchestrate.__aexit__(None, None, None)
                logger.info("WatsonX Orchestrate connection closed")
            
            logger.info("Agent orchestrator stopped successfully")
            
        except Exception as e:
            logger.error(f"Error during orchestrator shutdown: {str(e)}")
            raise
        
    async def register_agent(self, agent: BaseAgent) -> None:
        """
        Register an AI agent with the orchestrator with validation and retry logic
        
        Args:
            agent: Agent instance to register
            
        Raises:
            AgentError: If orchestrator is not ready or registration fails after retries
        """
        agent_id = getattr(agent, 'agent_id', 'unknown')
        registration_start_time = datetime.utcnow()
        
        # Initialize registration status tracking
        if agent_id not in self.agent_registration_status:
            self.agent_registration_status[agent_id] = AgentRegistrationStatus(agent_id)
        
        registration_status = self.agent_registration_status[agent_id]
        
        # Enhanced logging with structured data
        from app.core.logging_config import log_agent_activity, logging_manager
        
        # Set agent context for logging
        logging_manager.set_agent_context(agent_id)
        
        logger.info(
            f"Starting agent registration for {agent_id}",
            extra={
                "agent_id": agent_id,
                "registration_attempt": registration_status.retry_count + 1,
                "total_previous_attempts": len(registration_status.registration_attempts),
                "orchestrator_ready": self._is_ready,
                "orchestrator_phase": self._initialization_phase,
                "registered_agents_count": len(self.agents),
                "start_time": registration_start_time.isoformat()
            }
        )
        
        # Log agent details for troubleshooting
        agent_details = {
            "agent_type": type(agent).__name__,
            "agent_module": type(agent).__module__,
            "has_agent_id": hasattr(agent, 'agent_id'),
            "has_process_request": hasattr(agent, 'process_request'),
            "has_get_status": hasattr(agent, 'get_status'),
            "agent_status": getattr(agent, 'status', 'unknown')
        }
        
        logger.debug(
            f"Agent registration details for {agent_id}",
            extra={
                "agent_id": agent_id,
                "agent_details": agent_details
            }
        )
        
        try:
            # Use retry logic for the registration process
            await self._register_agent_with_retry(agent, registration_status)
            
            # Calculate registration time
            registration_duration = (datetime.utcnow() - registration_start_time).total_seconds()
            
            # Log successful registration with performance metrics
            log_agent_activity(
                agent_id,
                "registration",
                "completed",
                {
                    "duration_seconds": registration_duration,
                    "total_attempts": registration_status.retry_count + 1,
                    "validation_passed": registration_status.validation_passed,
                    "registered_agents_count": len(self.agents)
                }
            )
            
            logger.info(
                f"Agent registration completed successfully for {agent_id}",
                extra={
                    "agent_id": agent_id,
                    "registration_duration": registration_duration,
                    "total_attempts": registration_status.retry_count + 1,
                    "registered_agents_count": len(self.agents),
                    "orchestrator_ready": self._is_ready
                }
            )
            
        except Exception as e:
            # Calculate failed registration time
            registration_duration = (datetime.utcnow() - registration_start_time).total_seconds()
            
            # Record failed attempt
            registration_status.record_attempt(False, str(e))
            
            # Log detailed error information
            error_details = {
                "agent_id": agent_id,
                "error_message": str(e),
                "error_type": type(e).__name__,
                "registration_duration": registration_duration,
                "total_attempts": registration_status.retry_count,
                "orchestrator_ready": self._is_ready,
                "orchestrator_phase": self._initialization_phase,
                "registered_agents": list(self.agents.keys()),
                "agent_details": agent_details
            }
            
            log_agent_activity(
                agent_id,
                "registration",
                "failed",
                error_details
            )
            
            logger.error(
                f"Agent registration failed for {agent_id} after all retry attempts",
                extra=error_details,
                exc_info=True
            )
            
            raise AgentError(f"Agent registration failed: {str(e)}", agent_id)
        
        finally:
            # Clear agent context
            logging_manager.clear_context()
    
    async def _register_agent_with_retry(self, agent: BaseAgent, registration_status: AgentRegistrationStatus) -> None:
        """
        Internal method to register agent with retry logic
        
        Args:
            agent: Agent instance to register
            registration_status: Registration status tracker
        """
        agent_id = agent.agent_id
        
        from app.core.logging_config import log_agent_activity, log_performance
        
        for attempt in range(1, self._registration_retry_config.max_attempts + 1):
            attempt_start_time = datetime.utcnow()
            
            try:
                logger.debug(
                    f"Agent registration attempt {attempt}/{self._registration_retry_config.max_attempts} for {agent_id}",
                    extra={
                        "agent_id": agent_id,
                        "attempt_number": attempt,
                        "max_attempts": self._registration_retry_config.max_attempts,
                        "orchestrator_ready": self._is_ready,
                        "registered_agents_count": len(self.agents)
                    }
                )
                
                # Perform the actual registration
                await self._perform_agent_registration(agent)
                
                # Calculate attempt duration
                attempt_duration = (datetime.utcnow() - attempt_start_time).total_seconds()
                
                # Record successful attempt
                registration_status.record_attempt(True)
                
                # Log successful attempt with performance data
                log_performance(
                    f"agent_registration_{agent_id}",
                    attempt_duration,
                    {
                        "agent_id": agent_id,
                        "attempt_number": attempt,
                        "success": True
                    }
                )
                
                logger.info(
                    f"Agent {agent_id} registered successfully on attempt {attempt}",
                    extra={
                        "agent_id": agent_id,
                        "attempt_number": attempt,
                        "attempt_duration": attempt_duration,
                        "total_attempts": attempt,
                        "registered_agents_count": len(self.agents)
                    }
                )
                return
                
            except Exception as e:
                # Calculate failed attempt duration
                attempt_duration = (datetime.utcnow() - attempt_start_time).total_seconds()
                
                # Log detailed failure information
                failure_details = {
                    "agent_id": agent_id,
                    "attempt_number": attempt,
                    "max_attempts": self._registration_retry_config.max_attempts,
                    "error_message": str(e),
                    "error_type": type(e).__name__,
                    "attempt_duration": attempt_duration,
                    "orchestrator_ready": self._is_ready,
                    "orchestrator_phase": self._initialization_phase
                }
                
                log_performance(
                    f"agent_registration_{agent_id}",
                    attempt_duration,
                    {
                        "agent_id": agent_id,
                        "attempt_number": attempt,
                        "success": False,
                        "error": str(e)
                    }
                )
                
                if attempt < self._registration_retry_config.max_attempts:
                    # Calculate delay for next attempt
                    delay = self._registration_retry_config.calculate_delay(attempt)
                    
                    logger.warning(
                        f"Agent registration attempt {attempt} failed for {agent_id}: {str(e)}",
                        extra=failure_details
                    )
                    
                    logger.info(
                        f"Retrying agent registration for {agent_id} in {delay:.2f} seconds...",
                        extra={
                            "agent_id": agent_id,
                            "retry_delay": delay,
                            "next_attempt": attempt + 1,
                            "max_attempts": self._registration_retry_config.max_attempts
                        }
                    )
                    
                    # Wait before retry
                    await asyncio.sleep(delay)
                else:
                    # Final attempt failed
                    logger.error(
                        f"Agent registration final attempt {attempt} failed for {agent_id}: {str(e)}",
                        extra=failure_details,
                        exc_info=True
                    )
                    
                    log_agent_activity(
                        agent_id,
                        "registration_retry",
                        "exhausted",
                        failure_details
                    )
                    
                    raise e
        
        # This should never be reached, but just in case
        raise AgentError(f"Agent registration failed after {self._registration_retry_config.max_attempts} attempts", agent_id)
    
    async def _perform_agent_registration(self, agent: BaseAgent) -> None:
        """
        Perform the actual agent registration with comprehensive validation
        
        Args:
            agent: Agent instance to register
            
        Raises:
            AgentError: If validation fails or registration cannot be completed
        """
        agent_id = agent.agent_id
        registration_step_start = datetime.utcnow()
        
        from app.core.logging_config import log_performance
        
        # Step 1: Validate orchestrator readiness
        step_start = datetime.utcnow()
        logger.debug(
            f"Step 1: Validating orchestrator readiness for agent {agent_id}",
            extra={
                "agent_id": agent_id,
                "orchestrator_ready": self._is_ready,
                "orchestrator_phase": self._initialization_phase,
                "step": "orchestrator_readiness_check"
            }
        )
        
        if not self._is_ready:
            logger.debug(
                f"Orchestrator not ready, waiting for readiness before registering agent {agent_id}",
                extra={
                    "agent_id": agent_id,
                    "orchestrator_phase": self._initialization_phase,
                    "step": "waiting_for_orchestrator_readiness"
                }
            )
            
            # Wait for orchestrator to be ready
            ready = await self.wait_for_ready(timeout=30.0)
            if not ready:
                error_msg = f"Orchestrator not ready for agent registration after timeout"
                logger.error(
                    error_msg,
                    extra={
                        "agent_id": agent_id,
                        "orchestrator_phase": self._initialization_phase,
                        "timeout_seconds": 30.0,
                        "step": "orchestrator_readiness_timeout"
                    }
                )
                raise AgentError(error_msg, agent_id)
        
        step_duration = (datetime.utcnow() - step_start).total_seconds()
        log_performance(f"agent_registration_step1_{agent_id}", step_duration)
        
        # Step 2: Validate agent instance
        step_start = datetime.utcnow()
        logger.debug(
            f"Step 2: Validating agent instance for {agent_id}",
            extra={
                "agent_id": agent_id,
                "step": "agent_validation"
            }
        )
        
        try:
            await self._validate_agent_for_registration(agent)
            step_duration = (datetime.utcnow() - step_start).total_seconds()
            log_performance(f"agent_registration_step2_{agent_id}", step_duration)
            
            logger.debug(
                f"Agent validation completed for {agent_id}",
                extra={
                    "agent_id": agent_id,
                    "validation_duration": step_duration,
                    "step": "agent_validation_complete"
                }
            )
        except Exception as e:
            step_duration = (datetime.utcnow() - step_start).total_seconds()
            logger.error(
                f"Agent validation failed for {agent_id}: {str(e)}",
                extra={
                    "agent_id": agent_id,
                    "validation_duration": step_duration,
                    "error_message": str(e),
                    "error_type": type(e).__name__,
                    "step": "agent_validation_failed"
                },
                exc_info=True
            )
            raise
        
        # Step 3: Handle existing registration
        step_start = datetime.utcnow()
        if agent_id in self.agents:
            logger.warning(
                f"Step 3: Agent {agent_id} is already registered, updating registration",
                extra={
                    "agent_id": agent_id,
                    "step": "existing_registration_cleanup",
                    "existing_agents_count": len(self.agents)
                }
            )
            # Clean up existing registration first
            await self._cleanup_existing_registration(agent_id)
            
            logger.debug(
                f"Existing registration cleanup completed for {agent_id}",
                extra={
                    "agent_id": agent_id,
                    "step": "existing_registration_cleanup_complete"
                }
            )
        else:
            logger.debug(
                f"Step 3: No existing registration found for {agent_id}",
                extra={
                    "agent_id": agent_id,
                    "step": "no_existing_registration"
                }
            )
        
        step_duration = (datetime.utcnow() - step_start).total_seconds()
        log_performance(f"agent_registration_step3_{agent_id}", step_duration)
        
        # Step 4: Perform registration
        step_start = datetime.utcnow()
        logger.debug(
            f"Step 4: Performing agent registration for {agent_id}",
            extra={
                "agent_id": agent_id,
                "step": "agent_registration"
            }
        )
        
        try:
            # Register the agent
            self.agents[agent_id] = agent
            logger.debug(f"Agent {agent_id} added to agents registry")
            
            # Create health status
            self.agent_health[agent_id] = AgentHealthStatus(agent_id)
            logger.debug(f"Health status created for agent {agent_id}")
            
            # Subscribe agent to context updates
            await self._subscribe_to_context_updates(agent_id)
            logger.debug(f"Context subscriptions set up for agent {agent_id}")
            
            step_duration = (datetime.utcnow() - step_start).total_seconds()
            log_performance(f"agent_registration_step4_{agent_id}", step_duration)
            
            logger.debug(
                f"Agent registration setup completed for {agent_id}",
                extra={
                    "agent_id": agent_id,
                    "setup_duration": step_duration,
                    "registered_agents_count": len(self.agents),
                    "step": "agent_registration_setup_complete"
                }
            )
            
        except Exception as e:
            step_duration = (datetime.utcnow() - step_start).total_seconds()
            logger.error(
                f"Agent registration setup failed for {agent_id}: {str(e)}",
                extra={
                    "agent_id": agent_id,
                    "setup_duration": step_duration,
                    "error_message": str(e),
                    "error_type": type(e).__name__,
                    "step": "agent_registration_setup_failed"
                },
                exc_info=True
            )
            
            # Clean up partial registration on failure
            await self._cleanup_failed_registration(agent_id)
            raise AgentError(f"Agent registration failed during setup: {str(e)}", agent_id)
        
        # Step 5: Validate successful registration
        step_start = datetime.utcnow()
        logger.debug(
            f"Step 5: Validating successful registration for {agent_id}",
            extra={
                "agent_id": agent_id,
                "step": "registration_validation"
            }
        )
        
        try:
            await self._validate_agent_registration(agent_id)
            step_duration = (datetime.utcnow() - step_start).total_seconds()
            log_performance(f"agent_registration_step5_{agent_id}", step_duration)
            
            # Calculate total registration time
            total_duration = (datetime.utcnow() - registration_step_start).total_seconds()
            
            logger.info(
                f"Agent {agent_id} registered and validated successfully",
                extra={
                    "agent_id": agent_id,
                    "validation_duration": step_duration,
                    "total_registration_duration": total_duration,
                    "registered_agents_count": len(self.agents),
                    "step": "registration_complete"
                }
            )
            
        except Exception as e:
            step_duration = (datetime.utcnow() - step_start).total_seconds()
            logger.error(
                f"Agent registration validation failed for {agent_id}: {str(e)}",
                extra={
                    "agent_id": agent_id,
                    "validation_duration": step_duration,
                    "error_message": str(e),
                    "error_type": type(e).__name__,
                    "step": "registration_validation_failed"
                },
                exc_info=True
            )
            
            # Clean up failed registration
            await self._cleanup_failed_registration(agent_id)
            raise AgentError(f"Agent registration validation failed: {str(e)}", agent_id)
    
    async def _validate_agent_for_registration(self, agent: BaseAgent) -> None:
        """
        Validate agent instance before registration
        
        Args:
            agent: Agent instance to validate
            
        Raises:
            AgentError: If validation fails
        """
        validation_start = datetime.utcnow()
        validation_results = {}
        
        # Check agent has required attributes
        logger.debug(f"Validating agent_id attribute for agent")
        
        if not hasattr(agent, 'agent_id'):
            validation_results['has_agent_id'] = False
            error_msg = "Agent must have an agent_id attribute"
            logger.error(
                error_msg,
                extra={
                    "validation_step": "agent_id_attribute_check",
                    "validation_results": validation_results
                }
            )
            raise AgentError(error_msg, 'unknown')
        
        validation_results['has_agent_id'] = True
        agent_id = agent.agent_id
        
        if not agent.agent_id:
            validation_results['agent_id_not_empty'] = False
            error_msg = "Agent must have a valid agent_id"
            logger.error(
                error_msg,
                extra={
                    "agent_id": agent_id,
                    "validation_step": "agent_id_value_check",
                    "validation_results": validation_results
                }
            )
            raise AgentError(error_msg, agent_id)
        
        validation_results['agent_id_not_empty'] = True
        
        if not isinstance(agent.agent_id, str) or len(agent.agent_id.strip()) == 0:
            validation_results['agent_id_valid_string'] = False
            error_msg = "Agent ID must be a non-empty string"
            logger.error(
                error_msg,
                extra={
                    "agent_id": agent_id,
                    "agent_id_type": type(agent.agent_id).__name__,
                    "agent_id_length": len(str(agent.agent_id).strip()) if agent.agent_id else 0,
                    "validation_step": "agent_id_format_check",
                    "validation_results": validation_results
                }
            )
            raise AgentError(error_msg, agent_id)
        
        validation_results['agent_id_valid_string'] = True
        
        # Check agent has required methods
        logger.debug(f"Validating required methods for agent {agent_id}")
        required_methods = ['process_request', 'get_status']
        method_validation = {}
        
        for method_name in required_methods:
            has_method = hasattr(agent, method_name)
            is_callable = callable(getattr(agent, method_name, None)) if has_method else False
            
            method_validation[method_name] = {
                'exists': has_method,
                'callable': is_callable,
                'valid': has_method and is_callable
            }
            
            if not has_method or not is_callable:
                validation_results['required_methods'] = method_validation
                error_msg = f"Agent must implement {method_name} method"
                logger.error(
                    error_msg,
                    extra={
                        "agent_id": agent_id,
                        "missing_method": method_name,
                        "method_exists": has_method,
                        "method_callable": is_callable,
                        "validation_step": "required_methods_check",
                        "validation_results": validation_results
                    }
                )
                raise AgentError(error_msg, agent_id)
        
        validation_results['required_methods'] = method_validation
        
        # Check agent is properly initialized
        logger.debug(f"Validating agent initialization status for {agent_id}")
        agent_status = getattr(agent, 'status', 'unknown')
        validation_results['agent_status'] = agent_status
        
        if not hasattr(agent, 'status') or agent.status != 'initialized':
            logger.warning(
                f"Agent {agent_id} status is not 'initialized'",
                extra={
                    "agent_id": agent_id,
                    "current_status": agent_status,
                    "expected_status": "initialized",
                    "validation_step": "initialization_status_check",
                    "validation_results": validation_results
                }
            )
        else:
            validation_results['properly_initialized'] = True
        
        # Additional validation checks
        validation_results['agent_type'] = type(agent).__name__
        validation_results['agent_module'] = type(agent).__module__
        
        # Calculate validation time
        validation_duration = (datetime.utcnow() - validation_start).total_seconds()
        validation_results['validation_duration'] = validation_duration
        
        logger.debug(
            f"Agent {agent_id} passed all validation checks",
            extra={
                "agent_id": agent_id,
                "validation_duration": validation_duration,
                "validation_results": validation_results,
                "validation_step": "validation_complete"
            }
        )
    
    async def _validate_agent_registration(self, agent_id: str) -> None:
        """
        Validate that agent registration was successful
        
        Args:
            agent_id: ID of agent to validate
            
        Raises:
            AgentError: If validation fails
        """
        validation_start = datetime.utcnow()
        validation_checks = {}
        
        logger.debug(
            f"Starting registration validation for agent {agent_id}",
            extra={
                "agent_id": agent_id,
                "validation_step": "registration_validation_start"
            }
        )
        
        # Check agent is in registry
        logger.debug(f"Checking if agent {agent_id} is in registry")
        agent_in_registry = agent_id in self.agents
        validation_checks['agent_in_registry'] = agent_in_registry
        
        if not agent_in_registry:
            error_msg = f"Agent registration verification failed: agent not in registry"
            logger.error(
                error_msg,
                extra={
                    "agent_id": agent_id,
                    "registered_agents": list(self.agents.keys()),
                    "registered_agents_count": len(self.agents),
                    "validation_checks": validation_checks,
                    "validation_step": "registry_check_failed"
                }
            )
            raise AgentError(error_msg, agent_id)
        
        # Check health status was created
        logger.debug(f"Checking if health status exists for agent {agent_id}")
        health_status_exists = agent_id in self.agent_health
        validation_checks['health_status_exists'] = health_status_exists
        
        if not health_status_exists:
            error_msg = f"Agent registration verification failed: health status not created"
            logger.error(
                error_msg,
                extra={
                    "agent_id": agent_id,
                    "health_statuses": list(self.agent_health.keys()),
                    "validation_checks": validation_checks,
                    "validation_step": "health_status_check_failed"
                }
            )
            raise AgentError(error_msg, agent_id)
        
        # Try to get agent status to ensure it's responsive
        logger.debug(f"Testing agent responsiveness for {agent_id}")
        status_check_start = datetime.utcnow()
        
        try:
            agent = self.agents[agent_id]
            status = await agent.get_status()
            status_check_duration = (datetime.utcnow() - status_check_start).total_seconds()
            
            validation_checks['status_check_duration'] = status_check_duration
            validation_checks['status_response_type'] = type(status).__name__
            validation_checks['status_is_dict'] = isinstance(status, dict)
            
            if not isinstance(status, dict):
                error_msg = f"Agent status check failed: invalid status format"
                logger.error(
                    error_msg,
                    extra={
                        "agent_id": agent_id,
                        "status_type": type(status).__name__,
                        "status_value": str(status)[:200],  # Truncate for logging
                        "validation_checks": validation_checks,
                        "validation_step": "status_format_check_failed"
                    }
                )
                raise AgentError(error_msg, agent_id)
            
            validation_checks['agent_responsive'] = True
            validation_checks['status_response'] = status
            
            logger.debug(
                f"Agent {agent_id} status check passed",
                extra={
                    "agent_id": agent_id,
                    "status_check_duration": status_check_duration,
                    "status_keys": list(status.keys()) if isinstance(status, dict) else None,
                    "validation_step": "status_check_passed"
                }
            )
            
        except Exception as e:
            status_check_duration = (datetime.utcnow() - status_check_start).total_seconds()
            validation_checks['status_check_duration'] = status_check_duration
            validation_checks['status_check_error'] = str(e)
            validation_checks['agent_responsive'] = False
            
            error_msg = f"Agent registration verification failed: status check error - {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "agent_id": agent_id,
                    "status_check_duration": status_check_duration,
                    "error_message": str(e),
                    "error_type": type(e).__name__,
                    "validation_checks": validation_checks,
                    "validation_step": "status_check_error"
                },
                exc_info=True
            )
            raise AgentError(error_msg, agent_id)
        
        # Calculate total validation time
        validation_duration = (datetime.utcnow() - validation_start).total_seconds()
        validation_checks['total_validation_duration'] = validation_duration
        
        logger.debug(
            f"Agent {agent_id} registration validation completed successfully",
            extra={
                "agent_id": agent_id,
                "validation_duration": validation_duration,
                "validation_checks": validation_checks,
                "validation_step": "registration_validation_complete"
            }
        )
    
    async def _cleanup_existing_registration(self, agent_id: str) -> None:
        """
        Clean up existing agent registration
        
        Args:
            agent_id: ID of agent to clean up
        """
        logger.debug(f"Cleaning up existing registration for agent {agent_id}")
        
        # Remove from agents registry
        if agent_id in self.agents:
            del self.agents[agent_id]
        
        # Remove health status
        if agent_id in self.agent_health:
            del self.agent_health[agent_id]
        
        # Remove from context subscriptions
        for context_key in list(self.context_subscribers.keys()):
            if agent_id in self.context_subscribers[context_key]:
                self.context_subscribers[context_key].remove(agent_id)
    
    async def _cleanup_failed_registration(self, agent_id: str) -> None:
        """
        Clean up failed agent registration
        
        Args:
            agent_id: ID of agent to clean up
        """
        logger.debug(f"Cleaning up failed registration for agent {agent_id}")
        
        # Remove from agents registry
        if agent_id in self.agents:
            del self.agents[agent_id]
        
        # Remove health status
        if agent_id in self.agent_health:
            del self.agent_health[agent_id]
        
        # Remove from context subscriptions
        for context_key in list(self.context_subscribers.keys()):
            if agent_id in self.context_subscribers[context_key]:
                self.context_subscribers[context_key].remove(agent_id)
    
    async def unregister_agent(self, agent_id: str) -> None:
        """
        Unregister an AI agent from the orchestrator
        
        Args:
            agent_id: ID of agent to unregister
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
            
        if agent_id in self.agent_health:
            del self.agent_health[agent_id]
        
        if agent_id in self.agent_registration_status:
            del self.agent_registration_status[agent_id]
        
        # Remove from context subscriptions
        for context_key in list(self.context_subscribers.keys()):
            if agent_id in self.context_subscribers[context_key]:
                self.context_subscribers[context_key].remove(agent_id)
        
        logger.info(f"Agent {agent_id} unregistered from orchestrator")
    
    async def _subscribe_to_context_updates(self, agent_id: str, context_keys: List[str] = None):
        """Subscribe agent to context updates"""
        if context_keys is None:
            context_keys = ["global"]  # Default to global context
        
        for key in context_keys:
            if agent_id not in self.context_subscribers[key]:
                self.context_subscribers[key].append(agent_id)
    
    async def submit_task(self, task: AgentTask) -> str:
        """
        Submit a task to the orchestrator queue
        
        Args:
            task: Task to submit
            
        Returns:
            Task ID for tracking
        """
        if task.agent_id not in self.agents:
            # Provide detailed error information for missing agents
            registered_agents = list(self.agents.keys())
            registration_status = self.agent_registration_status.get(task.agent_id)
            
            error_details = {
                "requested_agent": task.agent_id,
                "registered_agents": registered_agents,
                "total_registered": len(registered_agents),
                "orchestrator_ready": self._is_ready,
                "registration_status": registration_status.to_dict() if registration_status else None
            }
            
            logger.error(f"Agent {task.agent_id} not registered. Available agents: {registered_agents}")
            
            raise AgentError(
                f"Agent {task.agent_id} not registered. Available agents: {registered_agents}",
                task.agent_id,
                details=error_details
            )
        
        # Check queue size limit
        if len(self.task_queue) >= self.max_queue_size:
            raise AgentError("Task queue is full", task.agent_id)
        
        # Check agent health
        agent_health = self.agent_health.get(task.agent_id)
        if agent_health and not agent_health.is_healthy():
            logger.warning(f"Submitting task to unhealthy agent {task.agent_id}")
        
        # Note: Dependencies will be checked during queue processing, not at submission time
        
        # Insert task based on priority
        inserted = False
        for i, queued_task in enumerate(self.task_queue):
            if task.priority.value > queued_task.priority.value:
                self.task_queue.insert(i, task)
                inserted = True
                break
        
        if not inserted:
            self.task_queue.append(task)
        
        # Store in Redis if available for persistence
        if self.redis_client:
            await self._persist_task(task)
        
        logger.info(f"Task {task.task_id} submitted for agent {task.agent_id}")
        return task.task_id
    
    async def _check_task_dependencies(self, task: AgentTask) -> bool:
        """Check if task dependencies are satisfied"""
        if not task.dependencies:
            return True
            
        for dep_task_id in task.dependencies:
            # Check if dependency is completed
            if dep_task_id not in self.completed_tasks:
                return False
            
            # Check if dependency completed successfully
            dep_task = self.completed_tasks[dep_task_id]
            if dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    async def _persist_task(self, task: AgentTask):
        """Persist task to Redis for durability"""
        try:
            await self.redis_client.hset(
                f"task:{task.task_id}",
                mapping={
                    "data": json.dumps(task.to_dict()),
                    "status": task.status.value
                }
            )
            await self.redis_client.expire(f"task:{task.task_id}", 86400)  # 24 hours
        except Exception as e:
            logger.error(f"Failed to persist task {task.task_id}: {str(e)}")
    
    async def create_task(self, agent_id: str, task_type: str, payload: Dict[str, Any],
                         priority: TaskPriority = TaskPriority.MEDIUM,
                         dependencies: List[str] = None) -> str:
        """
        Create and submit a new task
        
        Args:
            agent_id: ID of agent to execute task
            task_type: Type of task
            payload: Task payload data
            priority: Task priority
            dependencies: List of task IDs this task depends on
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        task = AgentTask(
            task_id=task_id,
            agent_id=agent_id,
            task_type=task_type,
            payload=payload,
            priority=priority
        )
        
        if dependencies:
            task.dependencies = dependencies
        
        return await self.submit_task(task)
    
    async def execute_task(self, task: AgentTask) -> AgentResponse:
        """
        Execute a single task using the appropriate agent
        
        Args:
            task: Task to execute
            
        Returns:
            Agent response
        """
        if task.agent_id not in self.agents:
            raise AgentError(f"Agent {task.agent_id} not found", task.agent_id)
        
        agent = self.agents[task.agent_id]
        agent_health = self.agent_health.get(task.agent_id)
        
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.utcnow()
        
        # Update agent load
        if agent_health:
            agent_health.current_load += 1
        
        try:
            # Update agent context with shared context
            await agent.update_context(self.shared_context)
            
            # Execute the task with timeout
            start_time = datetime.utcnow()
            result = await asyncio.wait_for(
                agent.process_request(task.payload, agent.context),
                timeout=task.timeout_seconds
            )
            end_time = datetime.utcnow()
            
            # Calculate response time
            response_time = (end_time - start_time).total_seconds()
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = end_time
            task.result = result
            
            # Update agent health metrics
            if agent_health:
                agent_health.increment_success()
                agent_health.add_response_time(response_time)
                agent_health.current_load -= 1
                agent_health.update_heartbeat()
            
            # Update shared context with results if applicable
            if isinstance(result, dict) and "context_updates" in result:
                await self.broadcast_context_update(result["context_updates"])
            
            # Notify dependent tasks
            await self._notify_dependent_tasks(task.task_id)
            
            # Persist task completion
            if self.redis_client:
                await self._persist_task(task)
            
            return AgentResponse(success=True, data=result)
            
        except asyncio.TimeoutError:
            task.status = TaskStatus.FAILED
            task.error = f"Task timed out after {task.timeout_seconds} seconds"
            task.completed_at = datetime.utcnow()
            
            if agent_health:
                agent_health.increment_error()
                agent_health.current_load -= 1
            
            logger.error(f"Task {task.task_id} timed out")
            return AgentResponse(success=False, error=task.error)
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.utcnow()
            
            if agent_health:
                agent_health.increment_error()
                agent_health.current_load -= 1
            
            logger.error(f"Task {task.task_id} failed: {str(e)}")
            
            # Check if task should be retried
            if task.retry_count < task.max_retries:
                await self._retry_task(task)
                return AgentResponse(success=False, error=f"Task failed, retrying ({task.retry_count}/{task.max_retries})")
            
            return AgentResponse(success=False, error=str(e))
    
    async def _retry_task(self, task: AgentTask):
        """Retry a failed task"""
        task.retry_count += 1
        task.status = TaskStatus.RETRYING
        task.started_at = None
        task.completed_at = None
        task.error = None
        
        # Add exponential backoff delay
        delay = min(2 ** task.retry_count, 60)  # Max 60 seconds
        await asyncio.sleep(delay)
        
        # Re-queue the task
        await self.submit_task(task)
        logger.info(f"Task {task.task_id} queued for retry ({task.retry_count}/{task.max_retries})")
    
    async def _notify_dependent_tasks(self, completed_task_id: str):
        """Notify tasks that depend on the completed task"""
        for task in self.task_queue:
            if completed_task_id in task.dependencies:
                # Check if all dependencies are now satisfied
                if await self._check_task_dependencies(task):
                    logger.info(f"Task {task.task_id} dependencies satisfied, ready for execution")
    
    async def send_message(self, sender_id: str, recipient_id: str, 
                          message_type: MessageType, payload: Dict[str, Any],
                          correlation_id: str = None) -> str:
        """
        Send a message between agents
        
        Args:
            sender_id: ID of sending agent
            recipient_id: ID of receiving agent
            message_type: Type of message
            payload: Message payload
            correlation_id: Optional correlation ID for request/response tracking
            
        Returns:
            Message ID
        """
        message_id = str(uuid.uuid4())
        message = AgentMessage(
            message_id=message_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=message_type,
            payload=payload,
            correlation_id=correlation_id
        )
        
        self.message_queue.append(message)
        
        # If using Redis, publish message for distributed systems
        if self.redis_client:
            await self.redis_client.publish(
                f"agent_messages:{recipient_id}",
                json.dumps(message.to_dict())
            )
        
        logger.debug(f"Message {message_id} sent from {sender_id} to {recipient_id}")
        return message_id
    
    async def broadcast_message(self, sender_id: str, message_type: MessageType, 
                              payload: Dict[str, Any]) -> List[str]:
        """
        Broadcast a message to all registered agents
        
        Args:
            sender_id: ID of sending agent
            message_type: Type of message
            payload: Message payload
            
        Returns:
            List of message IDs
        """
        message_ids = []
        
        for agent_id in self.agents.keys():
            if agent_id != sender_id:  # Don't send to self
                message_id = await self.send_message(
                    sender_id, agent_id, message_type, payload
                )
                message_ids.append(message_id)
        
        return message_ids
    
    async def register_message_handler(self, agent_id: str, handler: Callable):
        """
        Register a message handler for an agent
        
        Args:
            agent_id: ID of agent
            handler: Message handler function
        """
        self.message_handlers[agent_id].append(handler)
    
    async def _process_message_queue(self):
        """Process messages in the message queue"""
        while self.is_running:
            if not self.message_queue:
                await asyncio.sleep(0.1)
                continue
            
            message = self.message_queue.pop(0)
            
            try:
                await self._deliver_message(message)
            except Exception as e:
                logger.error(f"Error delivering message {message.message_id}: {str(e)}")
    
    async def _deliver_message(self, message: AgentMessage):
        """Deliver a message to the recipient agent"""
        recipient_id = message.recipient_id
        
        # Check if recipient exists
        if recipient_id not in self.agents:
            logger.warning(f"Message recipient {recipient_id} not found")
            return
        
        # Call registered message handlers
        for handler in self.message_handlers.get(recipient_id, []):
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"Message handler error for agent {recipient_id}: {str(e)}")
        
        # Handle specific message types
        if message.message_type == MessageType.CONTEXT_UPDATE:
            agent = self.agents[recipient_id]
            await agent.update_context(message.payload)
        
        message.delivered = True
        logger.debug(f"Message {message.message_id} delivered to {recipient_id}")
    
    async def _process_task_queue(self):
        """Process tasks in the queue continuously"""
        logger.info("Task queue processor started")
        
        while self.is_running:
            if not self.task_queue:
                await asyncio.sleep(1)
                continue
            
            # Check if we can process more tasks
            if len(self.active_tasks) >= self.max_concurrent_tasks:
                await asyncio.sleep(1)
                continue
            
            # Get next ready task (dependencies satisfied)
            task = None
            for i, queued_task in enumerate(self.task_queue):
                if await self._check_task_dependencies(queued_task):
                    task = self.task_queue.pop(i)
                    break
            
            if not task:
                await asyncio.sleep(1)
                continue
            
            # Check agent availability
            agent_health = self.agent_health.get(task.agent_id)
            if agent_health and agent_health.current_load >= agent_health.max_load:
                # Re-queue task and try later
                self.task_queue.append(task)
                await asyncio.sleep(1)
                continue
            
            self.active_tasks[task.task_id] = task
            
            # Execute task asynchronously
            asyncio.create_task(self._execute_task_async(task))
    
    async def _execute_task_async(self, task: AgentTask):
        """Execute a task asynchronously"""
        try:
            response = await self.execute_task(task)
            
            # Move to appropriate collection based on result
            if response.success:
                self.completed_tasks[task.task_id] = task
            else:
                self.failed_tasks[task.task_id] = task
            
            # Remove from active tasks
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
                
        except Exception as e:
            logger.error(f"Error executing task {task.task_id}: {str(e)}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self.failed_tasks[task.task_id] = task
            
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
    
    async def _health_check_loop(self):
        """Continuously monitor agent health"""
        logger.info("Health check loop started")
        
        while self.is_running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Error in health check loop: {str(e)}")
                await asyncio.sleep(5)
    
    async def _perform_health_checks(self):
        """Perform health checks on all registered agents"""
        for agent_id, agent in self.agents.items():
            try:
                # Send health check message
                await self.send_message(
                    "orchestrator", agent_id, MessageType.HEALTH_CHECK, {}
                )
                
                # Update health status
                health = self.agent_health.get(agent_id)
                if health:
                    # Check if agent is responsive
                    if health.is_healthy():
                        health.status = AgentStatus.HEALTHY
                    else:
                        health.status = AgentStatus.UNHEALTHY
                        logger.warning(f"Agent {agent_id} is unhealthy")
                
            except Exception as e:
                logger.error(f"Health check failed for agent {agent_id}: {str(e)}")
                if agent_id in self.agent_health:
                    self.agent_health[agent_id].status = AgentStatus.OFFLINE
    
    async def _cleanup_completed_tasks(self):
        """Clean up old completed and failed tasks"""
        while self.is_running:
            try:
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                
                # Clean up completed tasks older than 24 hours
                completed_to_remove = [
                    task_id for task_id, task in self.completed_tasks.items()
                    if task.completed_at and task.completed_at < cutoff_time
                ]
                
                for task_id in completed_to_remove:
                    del self.completed_tasks[task_id]
                
                # Clean up failed tasks older than 24 hours
                failed_to_remove = [
                    task_id for task_id, task in self.failed_tasks.items()
                    if task.completed_at and task.completed_at < cutoff_time
                ]
                
                for task_id in failed_to_remove:
                    del self.failed_tasks[task_id]
                
                if completed_to_remove or failed_to_remove:
                    logger.info(f"Cleaned up {len(completed_to_remove)} completed and {len(failed_to_remove)} failed tasks")
                
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific task
        
        Args:
            task_id: ID of task to check
            
        Returns:
            Task status information or None if not found
        """
        # Check active tasks
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
        # Check completed tasks
        elif task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
        # Check failed tasks
        elif task_id in self.failed_tasks:
            task = self.failed_tasks[task_id]
        # Check queued tasks
        else:
            task = next((t for t in self.task_queue if t.task_id == task_id), None)
        
        if not task:
            return None
        
        return task.to_dict()
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific agent
        
        Args:
            agent_id: ID of agent to check
            
        Returns:
            Agent status information or None if not found
        """
        if agent_id not in self.agents:
            return None
        
        # Get basic agent status
        agent = self.agents[agent_id]
        basic_status = await agent.get_status()
        
        # Get health information
        health_status = self.agent_health.get(agent_id)
        if health_status:
            basic_status.update(health_status.to_dict())
        
        return basic_status
    
    async def get_orchestrator_status(self) -> Dict[str, Any]:
        """
        Get overall orchestrator status
        
        Returns:
            Orchestrator status information
        """
        status = {
            "is_running": self.is_running,
            "is_ready": self._is_ready,
            "initialization_phase": self._initialization_phase,
            "registered_agents": len(self.agents),
            "queued_tasks": len(self.task_queue),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "pending_messages": len(self.message_queue),
            "shared_context_keys": len(self.shared_context),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "max_queue_size": self.max_queue_size,
            "watsonx_orchestrate_enabled": self.watsonx_orchestrate is not None,
            "redis_enabled": self.redis_client is not None
        }
        
        # Add initialization timing information
        if self._initialization_start_time:
            status["initialization_start_time"] = self._initialization_start_time.isoformat()
        
        if self._initialization_complete_time:
            status["initialization_complete_time"] = self._initialization_complete_time.isoformat()
            initialization_duration = (self._initialization_complete_time - self._initialization_start_time).total_seconds()
            status["initialization_duration_seconds"] = initialization_duration
        
        # Add agent registry details
        if self.agents:
            status["agent_registry"] = {
                agent_id: {
                    "agent_type": type(agent).__name__,
                    "is_healthy": self.agent_health.get(agent_id, {}).is_healthy() if agent_id in self.agent_health else False,
                    "is_registered": self.agent_registration_status.get(agent_id, {}).is_registered if agent_id in self.agent_registration_status else False,
                    "registration_retry_count": self.agent_registration_status.get(agent_id, {}).retry_count if agent_id in self.agent_registration_status else 0
                }
                for agent_id, agent in self.agents.items()
            }
        
        # Add registration status summary
        status["registration_summary"] = {
            "total_agents_tracked": len(self.agent_registration_status),
            "successfully_registered": len([s for s in self.agent_registration_status.values() if s.is_registered]),
            "failed_registrations": len([s for s in self.agent_registration_status.values() if not s.is_registered and s.retry_count > 0]),
            "agents_with_retries": len([s for s in self.agent_registration_status.values() if s.retry_count > 0])
        }
        
        return status
    
    def get_registered_agents(self) -> Dict[str, Dict[str, Any]]:
        """
        Get list of registered agents with their status
        
        Returns:
            Dictionary of agent information
        """
        agents_info = {}
        
        for agent_id, agent in self.agents.items():
            health_status = self.agent_health.get(agent_id)
            registration_status = self.agent_registration_status.get(agent_id)
            
            agents_info[agent_id] = {
                "agent_type": type(agent).__name__,
                "registration_time": registration_status.registration_time.isoformat() if registration_status and registration_status.registration_time else None,
                "is_registered": registration_status.is_registered if registration_status else False,
                "is_healthy": health_status.is_healthy() if health_status else False,
                "current_load": health_status.current_load if health_status else 0,
                "success_rate": health_status.get_success_rate() if health_status else 0.0,
                "average_response_time": health_status.get_average_response_time() if health_status else 0.0,
                "registration_retry_count": registration_status.retry_count if registration_status else 0,
                "registration_error": registration_status.error_message if registration_status else None
            }
        
        return agents_info
    
    def get_agent_registration_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed registration status for a specific agent
        
        Args:
            agent_id: ID of agent to check
            
        Returns:
            Agent registration status information or None if not found
        """
        registration_status = self.agent_registration_status.get(agent_id)
        if not registration_status:
            return None
        
        return registration_status.to_dict()
    
    def get_all_agent_registration_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get registration status for all agents
        
        Returns:
            Dictionary of agent registration status information
        """
        return {
            agent_id: status.to_dict()
            for agent_id, status in self.agent_registration_status.items()
        }
    
    async def broadcast_context_update(self, context_update: Dict[str, Any], 
                                     context_key: str = "global") -> None:
        """
        Broadcast context update to subscribed agents
        
        Args:
            context_update: Context data to broadcast
            context_key: Context key for targeted updates
        """
        # Update shared context
        if context_key not in self.shared_context:
            self.shared_context[context_key] = {}
        self.shared_context[context_key].update(context_update)
        
        # Send context update messages to subscribed agents
        subscribers = self.context_subscribers.get(context_key, [])
        for agent_id in subscribers:
            await self.send_message(
                "orchestrator", agent_id, MessageType.CONTEXT_UPDATE,
                {"context_key": context_key, "update": context_update}
            )
        
        logger.info(f"Context update broadcasted to {len(subscribers)} agents for key '{context_key}'")
    
    async def get_shared_context(self, context_key: str = None) -> Dict[str, Any]:
        """
        Get shared context data
        
        Args:
            context_key: Specific context key to retrieve
            
        Returns:
            Context data
        """
        if context_key:
            return self.shared_context.get(context_key, {})
        return self.shared_context
    
    async def coordinate_agents(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Coordinate multiple agents for complex workflows
        
        Args:
            workflow: Workflow definition with agent tasks and dependencies
            
        Returns:
            Workflow execution results
        """
        workflow_id = workflow.get("workflow_id", str(uuid.uuid4()))
        
        # Use WatsonX Orchestrate if available
        if self.watsonx_orchestrate:
            return await self._execute_watsonx_workflow(workflow)
        
        # Fallback to local workflow execution
        return await self._execute_local_workflow(workflow)
    
    async def _execute_watsonx_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow using WatsonX Orchestrate"""
        try:
            # Create workflow in WatsonX Orchestrate
            creation_result = await self.watsonx_orchestrate.create_workflow(workflow)
            
            if not creation_result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to create workflow: {creation_result['error']}"
                }
            
            workflow_id = creation_result["workflow_id"]
            
            # Execute workflow
            execution_result = await self.watsonx_orchestrate.execute_workflow(
                workflow_id, workflow.get("input_data", {})
            )
            
            return execution_result
            
        except Exception as e:
            logger.error(f"WatsonX Orchestrate workflow execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_local_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow locally with dependency management"""
        workflow_id = workflow.get("workflow_id", str(uuid.uuid4()))
        steps = workflow.get("steps", [])
        results = {}
        
        # Create tasks with dependencies
        task_ids = {}
        for step in steps:
            step_id = step.get("step_id")
            agent_id = step.get("agent_id")
            task_data = step.get("task_data", {})
            dependencies = step.get("dependencies", [])
            
            if agent_id not in self.agents:
                results[step_id] = {
                    "success": False,
                    "error": f"Agent {agent_id} not found"
                }
                continue
            
            # Map step dependencies to task IDs
            task_dependencies = [task_ids.get(dep) for dep in dependencies if dep in task_ids]
            
            # Create task
            task_id = await self.create_task(
                agent_id=agent_id,
                task_type=step.get("task_type", "workflow_step"),
                payload={
                    "workflow_id": workflow_id,
                    "step_id": step_id,
                    "data": task_data
                },
                priority=TaskPriority.HIGH,
                dependencies=task_dependencies
            )
            
            task_ids[step_id] = task_id
        
        # Wait for all tasks to complete
        completed_count = 0
        total_tasks = len(task_ids)
        timeout = workflow.get("timeout", 300)  # 5 minutes default
        start_time = datetime.utcnow()
        
        while completed_count < total_tasks:
            if (datetime.utcnow() - start_time).total_seconds() > timeout:
                return {
                    "success": False,
                    "error": "Workflow execution timed out",
                    "partial_results": results
                }
            
            for step_id, task_id in task_ids.items():
                if step_id not in results:
                    task_status = await self.get_task_status(task_id)
                    if task_status and task_status["status"] in ["completed", "failed"]:
                        results[step_id] = {
                            "success": task_status["status"] == "completed",
                            "result": task_status.get("result"),
                            "error": task_status.get("error")
                        }
                        completed_count += 1
            
            await asyncio.sleep(1)
        
        # Determine overall workflow success
        workflow_success = all(result.get("success", False) for result in results.values())
        
        return {
            "success": workflow_success,
            "workflow_id": workflow_id,
            "results": results,
            "execution_time": (datetime.utcnow() - start_time).total_seconds()
        }
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending or active task
        
        Args:
            task_id: ID of task to cancel
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        # Check if task is in queue
        for i, task in enumerate(self.task_queue):
            if task.task_id == task_id:
                task.status = TaskStatus.CANCELLED
                self.task_queue.pop(i)
                self.failed_tasks[task_id] = task
                logger.info(f"Task {task_id} cancelled from queue")
                return True
        
        # Check if task is active (harder to cancel)
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = TaskStatus.CANCELLED
            # Note: We can't easily cancel a running task, but we mark it as cancelled
            logger.warning(f"Task {task_id} marked as cancelled but may still be running")
            return True
        
        return False
    
    def get_registered_agents(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all registered agents
        
        Returns:
            Dictionary with agent information including health and registration status
        """
        agent_info = {}
        
        for agent_id in self.agents.keys():
            health_status = self.agent_health.get(agent_id)
            registration_status = self.agent_registration_status.get(agent_id)
            
            agent_info[agent_id] = {
                "is_registered": True,
                "health_status": health_status.to_dict() if health_status else None,
                "registration_status": registration_status.to_dict() if registration_status else None
            }
        
        # Also include agents that attempted registration but failed
        for agent_id, registration_status in self.agent_registration_status.items():
            if agent_id not in agent_info and not registration_status.is_registered:
                agent_info[agent_id] = {
                    "is_registered": False,
                    "health_status": None,
                    "registration_status": registration_status.to_dict()
                }
        
        return agent_info
    
    def get_agent_availability_status(self) -> Dict[str, Any]:
        """
        Get overall agent availability status for system health checks
        
        Returns:
            Dictionary with availability information
        """
        registered_agents = list(self.agents.keys())
        failed_registrations = [
            agent_id for agent_id, status in self.agent_registration_status.items()
            if not status.is_registered
        ]
        
        healthy_agents = [
            agent_id for agent_id, health in self.agent_health.items()
            if health.is_healthy()
        ]
        
        return {
            "total_registered": len(registered_agents),
            "registered_agents": registered_agents,
            "healthy_agents": healthy_agents,
            "unhealthy_agents": [
                agent_id for agent_id in registered_agents
                if agent_id not in healthy_agents
            ],
            "failed_registrations": failed_registrations,
            "orchestrator_ready": self._is_ready,
            "initialization_phase": self._initialization_phase,
            "initialization_time": (
                self._initialization_complete_time - self._initialization_start_time
            ).total_seconds() if self._initialization_complete_time and self._initialization_start_time else None
        }


# Global orchestrator instance (initialized later)
orchestrator = None

# Convenience functions for easy access
async def get_orchestrator() -> AgentOrchestrator:
    """Get the global orchestrator instance"""
    if orchestrator is None:
        raise Exception("Orchestrator not initialized. Call initialize_orchestrator() first.")
    return orchestrator

async def initialize_orchestrator():
    """Initialize the global orchestrator with configuration and proper error handling"""
    try:
        logger.info("Initializing global orchestrator...")
        
        # Prepare WatsonX Orchestrate configuration
        watsonx_orchestrate_config = None
        if settings.watsonx_orchestrate_api_key:
            watsonx_orchestrate_config = {
                "api_key": settings.watsonx_orchestrate_api_key,
                "base_url": settings.watsonx_orchestrate_base_url
            }
            logger.info("WatsonX Orchestrate configuration prepared")
        else:
            logger.warning("WatsonX Orchestrate API key not configured - using basic orchestrator")
        
        # Initialize orchestrator with configuration
        global orchestrator
        
        # Shutdown existing orchestrator if it exists
        if orchestrator is not None:
            logger.info("Shutting down existing orchestrator...")
            await orchestrator.stop()
        
        # Create new orchestrator instance
        orchestrator = AgentOrchestrator(watsonx_orchestrate_config)
        
        # Start orchestrator with proper error handling
        await orchestrator.start()
        
        # Verify orchestrator is ready
        if not orchestrator.is_ready:
            raise Exception("Orchestrator failed to reach ready state")
        
        logger.info("Global orchestrator initialized and ready")
        
    except Exception as e:
        logger.error(f"Failed to initialize global orchestrator: {str(e)}")
        raise Exception(f"Orchestrator initialization failed: {str(e)}")

async def shutdown_orchestrator():
    """Shutdown the global orchestrator"""
    global orchestrator
    if orchestrator is not None:
        await orchestrator.stop()
        orchestrator = None
        logger.info("Global orchestrator shutdown")
    else:
        logger.warning("No orchestrator to shutdown")
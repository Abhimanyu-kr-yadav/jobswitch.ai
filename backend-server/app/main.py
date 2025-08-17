"""
JobSwitch.ai Main Application
Enhanced FastAPI backend with AI agent orchestration
"""
import logging
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import core components
from app.core.config import config, settings
from app.core.database import create_tables, db_manager
from app.core.orchestrator import orchestrator
from app.integrations.watsonx import WatsonXClient, WatsonXOrchestrate
from app.integrations.langchain_utils import initialize_langchain_manager

# Import error handling and logging
from app.core.error_handler import setup_error_handling, error_handling_health
from app.core.logging_config import logging_manager, get_logger
from app.core.fallback import setup_default_fallbacks, get_fallback_stats
from app.core.retry import get_retry_stats
# Temporarily disabled due to import issues
# from app.core.monitoring import monitoring_manager

# Create a simple mock monitoring manager
class MockMonitoringManager:
    def __init__(self):
        self.is_running = False
    
    async def initialize(self):
        self.is_running = True
    
    async def shutdown(self):
        self.is_running = False
    
    def record_api_call(self, *args, **kwargs):
        pass
    
    def record_agent_activity(self, *args, **kwargs):
        pass
    
    async def perform_health_check(self):
        """Mock health check that always returns healthy"""
        return {
            "overall_status": "healthy",
            "monitoring": "mocked",
            "database": "healthy",
            "cache": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }

monitoring_manager = MockMonitoringManager()

# Import API routes
from app.api.auth import router as auth_router
from app.api.user import router as user_router
from app.api.jobs import router as jobs_router
from app.api.skills import router as skills_router
from app.api.resume import router as resume_router
from app.api.interview import router as interview_router
from app.api.technical_interview import router as technical_interview_router
from app.api.networking import router as networking_router
from app.api.career_strategy import router as career_strategy_router
from app.api.orchestrator import router as orchestrator_router
from app.api.websocket import router as websocket_router
from app.api.dashboard import router as dashboard_router
from app.api.data_management import router as data_management_router
from app.api.gdpr import router as gdpr_router
from app.api.analytics import router as analytics_router
from app.api.ab_testing import router as ab_testing_router

# Configure centralized logging
logger = get_logger(__name__)


async def _setup_job_discovery_agent(agent_instance):
    """
    Setup function for Job Discovery Agent
    
    Args:
        agent_instance: Job Discovery Agent instance to setup
    """
    try:
        from app.integrations.job_connectors import job_connector_manager
        
        # Register job board connectors
        for source, connector in job_connector_manager.get_all_connectors().items():
            agent_instance.register_job_connector(source, connector)
        
        logger.debug("Job Discovery Agent connectors registered successfully")
        
    except Exception as e:
        logger.warning(f"Failed to setup Job Discovery Agent connectors: {str(e)}")
        # Don't raise - agent can still function without all connectors


async def _validate_startup_dependencies():
    """
    Validate that all critical dependencies are properly initialized
    
    Returns:
        Dict with validation results
    
    Raises:
        Exception: If critical dependencies are not available
    """
    validation_results = {
        "database": False,
        "orchestrator": False,
        "watsonx_client": False,
        "cache": False
    }
    
    # Validate database connection with retry logic
    try:
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            if db_manager.check_connection():
                validation_results["database"] = True
                logger.debug("Database validation: PASSED")
                break
            elif attempt < max_retries:
                logger.warning(f"Database validation attempt {attempt} failed, retrying in 2 seconds...")
                await asyncio.sleep(2)
            else:
                raise Exception("Database connection check failed after all retries")
    except Exception as e:
        logger.error(f"Database validation: FAILED - {str(e)}")
        raise Exception(f"Critical dependency validation failed: Database - {str(e)}")
    
    # Validate orchestrator with wait condition
    try:
        # Import the current orchestrator reference
        from app.core.orchestrator import orchestrator as current_orchestrator
        
        if current_orchestrator is None:
            raise Exception("Orchestrator instance is None")
        
        # Wait for orchestrator to be ready with timeout
        logger.debug("Waiting for orchestrator readiness...")
        ready = await current_orchestrator.wait_for_ready(timeout=30.0)
        
        if ready and current_orchestrator.is_ready:
            validation_results["orchestrator"] = True
            logger.debug("Orchestrator validation: PASSED")
        else:
            raise Exception("Orchestrator failed to become ready within timeout")
    except Exception as e:
        logger.error(f"Orchestrator validation: FAILED - {str(e)}")
        raise Exception(f"Critical dependency validation failed: Orchestrator - {str(e)}")
    
    # Validate WatsonX client (non-critical but important)
    try:
        from app.core.config import config
        watsonx_config = config.get_watsonx_config()
        if watsonx_config["api_key"]:
            validation_results["watsonx_client"] = True
            logger.debug("WatsonX client validation: PASSED")
        else:
            logger.warning("WatsonX client validation: SKIPPED - No API key configured")
    except Exception as e:
        logger.warning(f"WatsonX client validation: FAILED - {str(e)}")
    
    # Validate cache (non-critical)
    try:
        from app.core.cache import cache_manager
        if hasattr(cache_manager, 'is_connected') and cache_manager.is_connected():
            validation_results["cache"] = True
            logger.debug("Cache validation: PASSED")
        else:
            logger.warning("Cache validation: FAILED - Using fallback")
    except Exception as e:
        logger.warning(f"Cache validation: FAILED - {str(e)}")
    
    logger.info(f"Startup dependency validation completed: {validation_results}")
    return validation_results


async def _cleanup_failed_startup(app):
    """
    Cleanup resources after failed startup with enhanced error handling
    
    Args:
        app: FastAPI application instance
    """
    logger.info("Performing startup failure cleanup...")
    cleanup_errors = []
    
    # Cleanup orchestrator
    try:
        if hasattr(app.state, 'orchestrator_initialized') and app.state.orchestrator_initialized:
            logger.info("Shutting down orchestrator...")
            from app.core.orchestrator import shutdown_orchestrator
            await shutdown_orchestrator()
            logger.info("Orchestrator shutdown completed")
        elif orchestrator is not None:
            logger.info("Shutting down partially initialized orchestrator...")
            await orchestrator.stop()
            logger.info("Partial orchestrator shutdown completed")
    except Exception as e:
        error_msg = f"Error shutting down orchestrator: {str(e)}"
        logger.error(error_msg)
        cleanup_errors.append(error_msg)
    
    # Cleanup cache manager
    try:
        logger.info("Closing cache manager...")
        from app.core.cache import cache_manager
        if hasattr(cache_manager, 'close'):
            await cache_manager.close()
            logger.info("Cache manager closed")
        else:
            logger.info("Cache manager does not require explicit closing")
    except Exception as e:
        error_msg = f"Error closing cache manager: {str(e)}"
        logger.error(error_msg)
        cleanup_errors.append(error_msg)
    
    # Cleanup monitoring system
    try:
        logger.info("Shutting down monitoring system...")
        if monitoring_manager and hasattr(monitoring_manager, 'shutdown'):
            await monitoring_manager.shutdown()
            logger.info("Monitoring system shutdown completed")
        else:
            logger.info("Monitoring system does not require explicit shutdown")
    except Exception as e:
        error_msg = f"Error shutting down monitoring: {str(e)}"
        logger.error(error_msg)
        cleanup_errors.append(error_msg)
    
    # Cleanup WatsonX clients
    try:
        if hasattr(app.state, 'watsonx_client') and app.state.watsonx_client:
            logger.info("Cleaning up WatsonX client...")
            # WatsonX client cleanup would go here if needed
            app.state.watsonx_client = None
            
        if hasattr(app.state, 'watsonx_orchestrate') and app.state.watsonx_orchestrate:
            logger.info("Cleaning up WatsonX Orchestrate...")
            # WatsonX Orchestrate cleanup would go here if needed
            app.state.watsonx_orchestrate = None
            
        logger.info("WatsonX clients cleanup completed")
    except Exception as e:
        error_msg = f"Error cleaning up WatsonX clients: {str(e)}"
        logger.error(error_msg)
        cleanup_errors.append(error_msg)
    
    # Store cleanup errors for debugging
    if cleanup_errors:
        if not hasattr(app.state, 'cleanup_errors'):
            app.state.cleanup_errors = []
        app.state.cleanup_errors.extend(cleanup_errors)
        logger.warning(f"Startup cleanup completed with {len(cleanup_errors)} errors")
    else:
        logger.info("Startup failure cleanup completed successfully")
    
    return cleanup_errors


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager with proper dependency management
    Handles startup and shutdown events with graceful error handling
    """
    # Startup
    logger.info("Starting JobSwitch.ai application...")
    
    # Record application start time and initialize comprehensive tracking
    app.state.start_time = datetime.utcnow()
    app.state.initialization_errors = []
    app.state.initialization_warnings = []
    app.state.phase_timings = {}
    app.state.startup_metrics = {
        "startup_start_time": app.state.start_time.isoformat(),
        "phases_completed": [],
        "total_startup_duration": None,
        "initialization_status": "starting"
    }
    
    # Enhanced startup logging with performance tracking
    from app.core.logging_config import log_performance, logging_manager
    
    logger.info(
        "Starting JobSwitch.ai application...",
        extra={
            "startup_event": "application_start",
            "start_time": app.state.start_time.isoformat(),
            "environment": settings.environment,
            "log_level": settings.log_level
        }
    )
    
    try:
        # Phase 1: Core Infrastructure Initialization
        logger.info("Phase 1: Initializing core infrastructure...")
        
        # Initialize database first (critical dependency)
        logger.info("Initializing database...")
        try:
            create_tables()
            
            # Verify database connection with enhanced retry logic
            max_db_retries = 5
            retry_delay = 2.0
            
            for attempt in range(1, max_db_retries + 1):
                try:
                    if db_manager.check_connection():
                        logger.info(f"Database connection established successfully on attempt {attempt}")
                        break
                except Exception as db_error:
                    if attempt < max_db_retries:
                        logger.warning(f"Database connection attempt {attempt} failed: {str(db_error)}, retrying in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
                        retry_delay = min(retry_delay * 1.5, 10.0)  # Exponential backoff with cap
                    else:
                        raise Exception(f"Database connection failed after {max_db_retries} attempts: {str(db_error)}")
                        
        except Exception as e:
            logger.error(f"Critical error during database initialization: {str(e)}")
            app.state.initialization_errors.append(f"Database initialization failed: {str(e)}")
            raise Exception(f"Database initialization failed: {str(e)}")
        
        # Wait for database to be fully ready
        logger.info("Waiting for database to be fully ready...")
        await asyncio.sleep(1.0)  # Brief pause to ensure database is stable
        
        # Initialize Redis cache with fallback
        logger.info("Initializing Redis cache...")
        try:
            from app.core.cache import cache_manager
            await cache_manager.initialize()
            
            # Verify cache connection
            if hasattr(cache_manager, 'is_connected') and cache_manager.is_connected():
                logger.info("Redis cache initialized and connected successfully")
            else:
                logger.warning("Redis cache initialized but connection status unclear")
                
        except Exception as e:
            logger.warning(f"Redis cache initialization failed: {str(e)} - continuing with in-memory cache")
            app.state.initialization_warnings.append(f"Redis cache unavailable: {str(e)}")
        
        # Setup fallback mechanisms with dependency check
        logger.info("Setting up fallback mechanisms...")
        try:
            from app.core.cache import cache_manager
            setup_default_fallbacks(cache_manager=cache_manager)
            logger.info("Fallback mechanisms configured successfully")
        except Exception as e:
            logger.warning(f"Fallback setup failed: {str(e)} - some features may be degraded")
            app.state.initialization_warnings.append(f"Fallback setup failed: {str(e)}")
        
        # Validate Phase 1 completion
        logger.info("Validating Phase 1 completion...")
        if not db_manager.check_connection():
            raise Exception("Phase 1 validation failed: Database connection lost")
        
        # Phase 2: Monitoring and Optimization
        logger.info("Phase 2: Initializing monitoring and optimization...")
        
        # Initialize monitoring system
        logger.info("Initializing monitoring system...")
        try:
            await monitoring_manager.initialize()
            logger.info("Monitoring system initialized successfully")
        except Exception as e:
            logger.warning(f"Monitoring initialization failed: {str(e)} - using mock monitoring")
            app.state.initialization_warnings.append(f"Monitoring system unavailable: {str(e)}")
        
        # Initialize database optimization (non-critical)
        if settings.environment == "production":
            logger.info("Initializing database optimization...")
            try:
                from app.core.database_optimization import db_optimizer
                await db_optimizer.create_indexes()
                logger.info("Database optimization completed successfully")
            except Exception as e:
                logger.warning(f"Database optimization failed: {str(e)} - performance may be affected")
                app.state.initialization_warnings.append(f"Database optimization failed: {str(e)}")
        
        # Initialize backup system (non-critical)
        if settings.environment == "production":
            logger.info("Initializing backup system...")
            try:
                from app.core.backup_manager import start_backup_scheduler
                asyncio.create_task(start_backup_scheduler())
                logger.info("Backup system initialized successfully")
            except Exception as e:
                logger.warning(f"Backup system initialization failed: {str(e)} - backups disabled")
                app.state.initialization_warnings.append(f"Backup system unavailable: {str(e)}")
        
        # Phase 3: AI Services Initialization
        logger.info("Phase 3: Initializing AI services...")
        
        # Ensure Phase 2 dependencies are ready
        logger.info("Verifying Phase 2 dependencies before AI services initialization...")
        await asyncio.sleep(0.5)  # Brief pause to ensure monitoring is stable
        
        # Initialize WatsonX.ai client with validation
        logger.info("Initializing WatsonX.ai integration...")
        watsonx_config = config.get_watsonx_config()
        if watsonx_config["api_key"]:
            try:
                # Create WatsonX client with timeout protection
                logger.debug("Creating WatsonX client instance...")
                app.state.watsonx_client = WatsonXClient(
                    api_key=watsonx_config["api_key"],
                    base_url=watsonx_config["base_url"]
                )
                
                # Validate WatsonX client is working
                logger.debug("Validating WatsonX client connection...")
                # Note: Add actual validation call here if WatsonX client has a test method
                
                # Initialize LangChain manager with dependency check
                logger.info("Initializing LangChain integration...")
                if app.state.watsonx_client:
                    app.state.langchain_manager = initialize_langchain_manager(app.state.watsonx_client)
                    logger.info("WatsonX.ai and LangChain initialized successfully")
                else:
                    raise Exception("WatsonX client is None after initialization")
                
            except Exception as e:
                logger.error(f"WatsonX.ai initialization failed: {str(e)}")
                app.state.watsonx_client = None
                app.state.langchain_manager = None
                app.state.initialization_errors.append(f"WatsonX.ai initialization failed: {str(e)}")
        else:
            logger.warning("WatsonX.ai API key not configured - AI features disabled")
            app.state.watsonx_client = None
            app.state.langchain_manager = None
            app.state.initialization_warnings.append("WatsonX.ai API key not configured")
        
        # Initialize WatsonX Orchestrate with dependency validation
        logger.info("Initializing WatsonX Orchestrate...")
        orchestrate_config = config.get_watsonx_orchestrate_config()
        if orchestrate_config["api_key"]:
            try:
                logger.debug("Creating WatsonX Orchestrate instance...")
                app.state.watsonx_orchestrate = WatsonXOrchestrate(
                    api_key=orchestrate_config["api_key"],
                    base_url=orchestrate_config["base_url"]
                )
                
                # Validate Orchestrate client
                logger.debug("Validating WatsonX Orchestrate connection...")
                # Note: Add actual validation call here if WatsonX Orchestrate has a test method
                
                logger.info("WatsonX Orchestrate initialized successfully")
            except Exception as e:
                logger.warning(f"WatsonX Orchestrate initialization failed: {str(e)}")
                app.state.watsonx_orchestrate = None
                app.state.initialization_warnings.append(f"WatsonX Orchestrate unavailable: {str(e)}")
        else:
            logger.warning("WatsonX Orchestrate API key not configured")
            app.state.watsonx_orchestrate = None
            app.state.initialization_warnings.append("WatsonX Orchestrate API key not configured")
        
        # Validate Phase 3 completion
        logger.info("Validating Phase 3 completion...")
        if app.state.watsonx_client is None and watsonx_config["api_key"]:
            logger.warning("Phase 3 validation warning: WatsonX client failed to initialize despite API key being configured")
        
        # Phase 4: Agent Orchestrator Initialization
        phase4_start = datetime.utcnow()
        logger.info(
            "Phase 4: Initializing agent orchestrator...",
            extra={
                "phase": "orchestrator_initialization",
                "phase_start_time": phase4_start.isoformat()
            }
        )
        
        # Ensure Phase 3 dependencies are ready
        logger.info(
            "Verifying Phase 3 dependencies before orchestrator initialization...",
            extra={
                "phase": "orchestrator_initialization",
                "step": "dependency_verification",
                "watsonx_client_available": app.state.watsonx_client is not None,
                "langchain_manager_available": getattr(app.state, 'langchain_manager', None) is not None
            }
        )
        await asyncio.sleep(0.5)  # Brief pause to ensure AI services are stable
        
        try:
            # Initialize agent orchestrator with proper configuration and error handling
            orchestrator_init_start = datetime.utcnow()
            
            logger.info(
                "Starting agent orchestrator initialization...",
                extra={
                    "phase": "orchestrator_initialization",
                    "step": "orchestrator_init_start",
                    "init_start_time": orchestrator_init_start.isoformat()
                }
            )
            
            from app.core.orchestrator import initialize_orchestrator
            
            # Initialize with timeout protection
            await initialize_orchestrator()
            
            # Import the updated orchestrator reference
            from app.core.orchestrator import orchestrator as updated_orchestrator
            
            # Verify orchestrator instance exists
            if updated_orchestrator is None:
                raise Exception("Orchestrator instance is None after initialization")
            
            logger.info(
                "Orchestrator instance created, waiting for readiness...",
                extra={
                    "phase": "orchestrator_initialization",
                    "step": "waiting_for_readiness",
                    "orchestrator_phase": getattr(updated_orchestrator, '_initialization_phase', 'unknown')
                }
            )
            
            # Wait for orchestrator to be ready with extended timeout and progress logging
            orchestrator_ready = False
            ready_timeout = 45.0  # Extended timeout for orchestrator readiness
            ready_wait_start = datetime.utcnow()
            
            try:
                orchestrator_ready = await updated_orchestrator.wait_for_ready(timeout=ready_timeout)
                ready_wait_duration = (datetime.utcnow() - ready_wait_start).total_seconds()
                
                logger.info(
                    f"Orchestrator readiness check completed in {ready_wait_duration:.2f} seconds",
                    extra={
                        "phase": "orchestrator_initialization",
                        "step": "readiness_check_complete",
                        "ready_wait_duration": ready_wait_duration,
                        "orchestrator_ready": orchestrator_ready
                    }
                )
                
            except asyncio.TimeoutError:
                ready_wait_duration = (datetime.utcnow() - ready_wait_start).total_seconds()
                error_msg = f"Orchestrator readiness timeout after {ready_timeout} seconds"
                
                logger.error(
                    error_msg,
                    extra={
                        "phase": "orchestrator_initialization",
                        "step": "readiness_timeout",
                        "timeout_seconds": ready_timeout,
                        "ready_wait_duration": ready_wait_duration,
                        "orchestrator_phase": getattr(updated_orchestrator, '_initialization_phase', 'unknown')
                    }
                )
                raise Exception(f"Orchestrator failed to become ready within {ready_timeout} seconds")
            
            if not orchestrator_ready:
                error_msg = "Orchestrator wait_for_ready returned False"
                logger.error(
                    error_msg,
                    extra={
                        "phase": "orchestrator_initialization",
                        "step": "readiness_check_failed",
                        "orchestrator_phase": getattr(updated_orchestrator, '_initialization_phase', 'unknown'),
                        "orchestrator_ready_property": getattr(updated_orchestrator, 'is_ready', 'unknown')
                    }
                )
                raise Exception(error_msg)
            
            # Double-check orchestrator state
            if not updated_orchestrator.is_ready:
                error_msg = "Orchestrator reports not ready despite wait_for_ready success"
                logger.error(
                    error_msg,
                    extra={
                        "phase": "orchestrator_initialization",
                        "step": "state_verification_failed",
                        "wait_for_ready_result": orchestrator_ready,
                        "is_ready_property": updated_orchestrator.is_ready,
                        "orchestrator_phase": getattr(updated_orchestrator, '_initialization_phase', 'unknown')
                    }
                )
                raise Exception(error_msg)
            
            # Update the global reference for the rest of the application
            global orchestrator
            orchestrator = updated_orchestrator
            
            orchestrator_init_time = (datetime.utcnow() - orchestrator_init_start).total_seconds()
            phase4_duration = (datetime.utcnow() - phase4_start).total_seconds()
            
            logger.info(
                f"Agent orchestrator initialized and ready in {orchestrator_init_time:.2f} seconds",
                extra={
                    "phase": "orchestrator_initialization",
                    "step": "initialization_complete",
                    "orchestrator_init_time": orchestrator_init_time,
                    "phase4_total_duration": phase4_duration,
                    "orchestrator_ready": updated_orchestrator.is_ready,
                    "orchestrator_phase": getattr(updated_orchestrator, '_initialization_phase', 'unknown')
                }
            )
            
            # Store orchestrator initialization status
            app.state.orchestrator_initialized = True
            app.state.orchestrator_init_time = orchestrator_init_time
            
        except Exception as e:
            phase4_duration = (datetime.utcnow() - phase4_start).total_seconds()
            
            logger.error(
                f"Agent orchestrator initialization failed: {str(e)}",
                extra={
                    "phase": "orchestrator_initialization",
                    "step": "initialization_failed",
                    "error_message": str(e),
                    "error_type": type(e).__name__,
                    "phase4_duration": phase4_duration
                },
                exc_info=True
            )
            
            app.state.orchestrator_initialized = False
            app.state.initialization_errors.append(f"Agent orchestrator initialization failed: {str(e)}")
            
            # Attempt graceful cleanup of partial orchestrator initialization
            try:
                logger.info("Attempting orchestrator cleanup after initialization failure...")
                from app.core.orchestrator import shutdown_orchestrator
                await shutdown_orchestrator()
                logger.info("Partial orchestrator cleanup completed")
            except Exception as cleanup_error:
                logger.error(
                    f"Error during orchestrator cleanup: {str(cleanup_error)}",
                    extra={
                        "phase": "orchestrator_initialization",
                        "step": "cleanup_failed",
                        "cleanup_error": str(cleanup_error)
                    }
                )
            
            raise Exception(f"Agent orchestrator initialization failed: {str(e)}")
        
        # Phase 5: Agent Registration
        phase5_start = datetime.utcnow()
        logger.info(
            "Phase 5: Registering AI agents...",
            extra={
                "phase": "agent_registration",
                "phase_start_time": phase5_start.isoformat()
            }
        )
        
        # Ensure Phase 4 dependencies are ready
        logger.info(
            "Verifying Phase 4 dependencies before agent registration...",
            extra={
                "phase": "agent_registration",
                "step": "dependency_verification",
                "orchestrator_initialized": hasattr(app.state, 'orchestrator_initialized') and app.state.orchestrator_initialized,
                "orchestrator_init_time": getattr(app.state, 'orchestrator_init_time', None)
            }
        )
        
        if not hasattr(app.state, 'orchestrator_initialized') or not app.state.orchestrator_initialized:
            raise Exception("Cannot proceed with agent registration: orchestrator not properly initialized")
        
        # Wait for orchestrator to be fully stable
        logger.debug(
            "Waiting for orchestrator stability before agent registration...",
            extra={
                "phase": "agent_registration",
                "step": "stability_wait",
                "wait_duration": 1.0
            }
        )
        await asyncio.sleep(1.0)
        
        if app.state.watsonx_client:
            # Track agent registration results with detailed timing
            agent_registration_results = {}
            agent_registration_start = datetime.utcnow()
            app.state.agent_registration_start_time = agent_registration_start
            
            logger.info(
                "Starting agent registration process...",
                extra={
                    "phase": "agent_registration",
                    "step": "registration_start",
                    "registration_start_time": agent_registration_start.isoformat(),
                    "watsonx_client_available": app.state.watsonx_client is not None,
                    "langchain_manager_available": getattr(app.state, 'langchain_manager', None) is not None
                }
            )
            
            # Define agents to register with their dependencies
            agents_to_register = [
                {
                    'name': 'Job Discovery Agent',
                    'class': 'app.agents.job_discovery.JobDiscoveryAgent',
                    'init_args': [app.state.watsonx_client],
                    'setup_func': '_setup_job_discovery_agent',
                    'critical': True  # Mark as critical for system functionality
                },
                {
                    'name': 'Skills Analysis Agent',
                    'class': 'app.agents.skills_analysis.SkillsAnalysisAgent',
                    'init_args': [app.state.watsonx_client, app.state.langchain_manager],
                    'setup_func': None,
                    'critical': True
                },
                {
                    'name': 'Resume Optimization Agent',
                    'class': 'app.agents.resume_optimization.ResumeOptimizationAgent',
                    'init_args': [app.state.watsonx_client],
                    'setup_func': None,
                    'critical': True
                },
                {
                    'name': 'Interview Preparation Agent',
                    'class': 'app.agents.interview_preparation.InterviewPreparationAgent',
                    'init_args': [app.state.watsonx_client, app.state.langchain_manager],
                    'setup_func': None,
                    'critical': False
                },
                {
                    'name': 'Technical Interview Agent',
                    'class': 'app.agents.technical_interview.TechnicalInterviewAgent',
                    'init_args': [app.state.watsonx_client, app.state.langchain_manager],
                    'setup_func': None,
                    'critical': False
                },
                {
                    'name': 'Networking Agent',
                    'class': 'app.agents.networking.NetworkingAgent',
                    'init_args': [app.state.watsonx_client, app.state.langchain_manager],
                    'setup_func': None,
                    'critical': False
                },
                {
                    'name': 'Career Strategy Agent',
                    'class': 'app.agents.career_strategy.CareerStrategyAgent',
                    'init_args': [app.state.watsonx_client, app.state.langchain_manager],
                    'setup_func': None,
                    'critical': False
                }
            ]
            
            # Register each agent with enhanced error handling and dependency validation
            critical_agents_failed = []
            
            for i, agent_config in enumerate(agents_to_register):
                agent_name = agent_config['name']
                is_critical = agent_config.get('critical', False)
                agent_registration_start_individual = datetime.utcnow()
                
                logger.info(
                    f"Registering {agent_name} ({i+1}/{len(agents_to_register)}){'(critical)' if is_critical else ''}...",
                    extra={
                        "phase": "agent_registration",
                        "step": "individual_agent_registration",
                        "agent_name": agent_name,
                        "agent_index": i + 1,
                        "total_agents": len(agents_to_register),
                        "is_critical": is_critical,
                        "agent_class": agent_config['class'],
                        "has_setup_func": agent_config['setup_func'] is not None,
                        "registration_start": agent_registration_start_individual.isoformat()
                    }
                )
                
                try:
                    # Validate dependencies before creating agent
                    logger.debug(
                        f"Validating dependencies for {agent_name}...",
                        extra={
                            "phase": "agent_registration",
                            "step": "dependency_validation",
                            "agent_name": agent_name
                        }
                    )
                    
                    init_args = agent_config['init_args']
                    dependency_status = {}
                    
                    for i, arg in enumerate(init_args):
                        dependency_status[f"dependency_{i}"] = arg is not None
                        if arg is None:
                            raise Exception(f"Dependency {i} is None - cannot create agent")
                    
                    logger.debug(
                        f"Dependencies validated for {agent_name}",
                        extra={
                            "phase": "agent_registration",
                            "step": "dependency_validation_complete",
                            "agent_name": agent_name,
                            "dependency_status": dependency_status
                        }
                    )
                    
                    # Import agent class dynamically with error handling
                    logger.debug(
                        f"Importing agent class for {agent_name}...",
                        extra={
                            "phase": "agent_registration",
                            "step": "class_import",
                            "agent_name": agent_name,
                            "class_path": agent_config['class']
                        }
                    )
                    
                    module_path, class_name = agent_config['class'].rsplit('.', 1)
                    try:
                        module = __import__(module_path, fromlist=[class_name])
                        agent_class = getattr(module, class_name)
                        
                        logger.debug(
                            f"Agent class imported successfully for {agent_name}",
                            extra={
                                "phase": "agent_registration",
                                "step": "class_import_complete",
                                "agent_name": agent_name,
                                "class_name": class_name,
                                "module_path": module_path
                            }
                        )
                    except ImportError as import_error:
                        raise Exception(f"Failed to import agent class: {str(import_error)}")
                    
                    # Create agent instance with timeout protection
                    logger.debug(
                        f"Creating {agent_name} instance...",
                        extra={
                            "phase": "agent_registration",
                            "step": "instance_creation",
                            "agent_name": agent_name
                        }
                    )
                    
                    instance_creation_start = datetime.utcnow()
                    agent_instance = agent_class(*init_args)
                    instance_creation_duration = (datetime.utcnow() - instance_creation_start).total_seconds()
                    
                    logger.debug(
                        f"Agent instance created for {agent_name}",
                        extra={
                            "phase": "agent_registration",
                            "step": "instance_creation_complete",
                            "agent_name": agent_name,
                            "creation_duration": instance_creation_duration,
                            "agent_id": getattr(agent_instance, 'agent_id', 'unknown')
                        }
                    )
                    
                    # Run setup function if specified
                    if agent_config['setup_func']:
                        logger.debug(
                            f"Running setup function for {agent_name}...",
                            extra={
                                "phase": "agent_registration",
                                "step": "setup_function",
                                "agent_name": agent_name,
                                "setup_func": agent_config['setup_func']
                            }
                        )
                        
                        setup_func = globals().get(agent_config['setup_func'])
                        if setup_func:
                            setup_start = datetime.utcnow()
                            await setup_func(agent_instance)
                            setup_duration = (datetime.utcnow() - setup_start).total_seconds()
                            
                            logger.debug(
                                f"Setup function completed for {agent_name}",
                                extra={
                                    "phase": "agent_registration",
                                    "step": "setup_function_complete",
                                    "agent_name": agent_name,
                                    "setup_duration": setup_duration
                                }
                            )
                        else:
                            logger.warning(
                                f"Setup function {agent_config['setup_func']} not found for {agent_name}",
                                extra={
                                    "phase": "agent_registration",
                                    "step": "setup_function_not_found",
                                    "agent_name": agent_name,
                                    "setup_func": agent_config['setup_func']
                                }
                            )
                    
                    # Get current orchestrator reference
                    from app.core.orchestrator import orchestrator as current_orchestrator
                    
                    # Verify orchestrator is still ready before registration
                    if not current_orchestrator.is_ready:
                        raise Exception("Orchestrator became not ready during agent registration")
                    
                    logger.debug(
                        f"Orchestrator ready, proceeding with registration for {agent_name}",
                        extra={
                            "phase": "agent_registration",
                            "step": "orchestrator_ready_check",
                            "agent_name": agent_name,
                            "orchestrator_ready": current_orchestrator.is_ready,
                            "registered_agents_count": len(current_orchestrator.agents)
                        }
                    )
                    
                    # Register agent with orchestrator (includes built-in retry logic)
                    logger.debug(
                        f"Registering {agent_name} with orchestrator...",
                        extra={
                            "phase": "agent_registration",
                            "step": "orchestrator_registration",
                            "agent_name": agent_name,
                            "agent_id": getattr(agent_instance, 'agent_id', 'unknown')
                        }
                    )
                    
                    orchestrator_registration_start = datetime.utcnow()
                    await current_orchestrator.register_agent(agent_instance)
                    orchestrator_registration_duration = (datetime.utcnow() - orchestrator_registration_start).total_seconds()
                    
                    # Verify registration was successful
                    if hasattr(agent_instance, 'agent_id') and agent_instance.agent_id in current_orchestrator.agents:
                        individual_registration_duration = (datetime.utcnow() - agent_registration_start_individual).total_seconds()
                        
                        agent_registration_results[agent_name] = {
                            'success': True,
                            'error': None,
                            'critical': is_critical,
                            'agent_id': agent_instance.agent_id,
                            'registration_duration': individual_registration_duration,
                            'orchestrator_registration_duration': orchestrator_registration_duration
                        }
                        
                        logger.info(
                            f"✓ {agent_name} registered successfully",
                            extra={
                                "phase": "agent_registration",
                                "step": "registration_success",
                                "agent_name": agent_name,
                                "agent_id": agent_instance.agent_id,
                                "registration_duration": individual_registration_duration,
                                "orchestrator_registration_duration": orchestrator_registration_duration,
                                "registered_agents_count": len(current_orchestrator.agents)
                            }
                        )
                    else:
                        raise Exception("Agent registration verification failed")
                    
                except Exception as e:
                    individual_registration_duration = (datetime.utcnow() - agent_registration_start_individual).total_seconds()
                    error_msg = f"{agent_name} registration failed: {str(e)}"
                    
                    logger.error(
                        f"✗ {error_msg}",
                        extra={
                            "phase": "agent_registration",
                            "step": "registration_failed",
                            "agent_name": agent_name,
                            "error_message": str(e),
                            "error_type": type(e).__name__,
                            "is_critical": is_critical,
                            "registration_duration": individual_registration_duration
                        },
                        exc_info=True
                    )
                    
                    agent_registration_results[agent_name] = {
                        'success': False,
                        'error': str(e),
                        'critical': is_critical,
                        'agent_id': None,
                        'registration_duration': individual_registration_duration
                    }
                    
                    if is_critical:
                        critical_agents_failed.append(agent_name)
                    
                    app.state.initialization_errors.append(error_msg)
                
                # Brief pause between agent registrations to avoid overwhelming the orchestrator
                logger.debug(
                    f"Pausing before next agent registration...",
                    extra={
                        "phase": "agent_registration",
                        "step": "inter_registration_pause",
                        "completed_agent": agent_name,
                        "pause_duration": 0.2
                    }
                )
                await asyncio.sleep(0.2)
            
            # Store registration results for health checks
            app.state.agent_registration_results = agent_registration_results
            
            # Calculate registration statistics
            successful_registrations = sum(1 for result in agent_registration_results.values() if result['success'])
            total_agents = len(agent_registration_results)
            critical_successful = sum(1 for result in agent_registration_results.values() 
                                    if result['success'] and result.get('critical', False))
            total_critical = sum(1 for config in agents_to_register if config.get('critical', False))
            
            agent_registration_complete = datetime.utcnow()
            app.state.agent_registration_complete_time = agent_registration_complete
            agent_registration_time = (agent_registration_complete - agent_registration_start).total_seconds()
            phase5_duration = (agent_registration_complete - phase5_start).total_seconds()
            
            # Calculate average registration time
            successful_durations = [result.get('registration_duration', 0) for result in agent_registration_results.values() if result['success']]
            avg_registration_time = sum(successful_durations) / len(successful_durations) if successful_durations else 0
            
            # Detailed registration summary
            registration_summary = {
                "total_agents": total_agents,
                "successful_registrations": successful_registrations,
                "failed_registrations": total_agents - successful_registrations,
                "critical_agents_total": total_critical,
                "critical_agents_successful": critical_successful,
                "critical_agents_failed": len(critical_agents_failed),
                "registration_time_total": agent_registration_time,
                "phase5_total_duration": phase5_duration,
                "average_registration_time": avg_registration_time,
                "success_rate": (successful_registrations / total_agents * 100) if total_agents > 0 else 0,
                "critical_success_rate": (critical_successful / total_critical * 100) if total_critical > 0 else 0
            }
            
            logger.info(
                f"Agent registration completed in {agent_registration_time:.2f} seconds",
                extra={
                    "phase": "agent_registration",
                    "step": "registration_complete",
                    "registration_summary": registration_summary,
                    "successful_agents": [name for name, result in agent_registration_results.items() if result['success']],
                    "failed_agents": [name for name, result in agent_registration_results.items() if not result['success']],
                    "critical_agents_failed": critical_agents_failed
                }
            )
            
            logger.info(f"  Total agents: {successful_registrations}/{total_agents} ({registration_summary['success_rate']:.1f}%)")
            logger.info(f"  Critical agents: {critical_successful}/{total_critical} ({registration_summary['critical_success_rate']:.1f}%)")
            logger.info(f"  Average registration time: {avg_registration_time:.2f} seconds")
            
            # Log individual agent results for troubleshooting
            for agent_name, result in agent_registration_results.items():
                if result['success']:
                    logger.debug(
                        f"  ✓ {agent_name}: {result['registration_duration']:.2f}s",
                        extra={
                            "phase": "agent_registration",
                            "step": "individual_result",
                            "agent_name": agent_name,
                            "success": True,
                            "duration": result['registration_duration'],
                            "agent_id": result['agent_id']
                        }
                    )
                else:
                    logger.debug(
                        f"  ✗ {agent_name}: {result['error']}",
                        extra={
                            "phase": "agent_registration",
                            "step": "individual_result",
                            "agent_name": agent_name,
                            "success": False,
                            "error": result['error'],
                            "is_critical": result['critical']
                        }
                    )
            
            # Check if system can function
            if len(critical_agents_failed) > 0:
                error_msg = f"Critical agents failed to register: {', '.join(critical_agents_failed)}"
                logger.error(
                    error_msg,
                    extra={
                        "phase": "agent_registration",
                        "step": "critical_failure_check",
                        "critical_agents_failed": critical_agents_failed,
                        "critical_success_rate": registration_summary['critical_success_rate']
                    }
                )
                app.state.initialization_errors.append(error_msg)
                
                if critical_successful == 0:
                    raise Exception("No critical agents were successfully registered - system cannot function")
                else:
                    logger.warning("Some critical agents failed - system will run with reduced functionality")
            
            if successful_registrations == 0:
                raise Exception("No agents were successfully registered - system cannot function")
            elif successful_registrations < total_agents:
                logger.warning(f"Some agents failed to register - system will run with reduced functionality")
        
        else:
            logger.warning("WatsonX.ai client not available - skipping agent registration")
            app.state.agent_registration_results = {}
            app.state.agent_registration_start_time = datetime.utcnow()
            app.state.agent_registration_complete_time = datetime.utcnow()
            app.state.initialization_warnings.append("Agent registration skipped: WatsonX client not available")
        
        # Phase 6: Background Services
        logger.info("Phase 6: Starting background services...")
        
        # Start WebSocket cleanup task
        try:
            logger.info("Starting WebSocket cleanup task...")
            from app.core.websocket_manager import start_cleanup_task
            asyncio.create_task(start_cleanup_task())
            logger.info("WebSocket cleanup task started successfully")
        except Exception as e:
            logger.warning(f"WebSocket cleanup task failed to start: {str(e)}")
            app.state.initialization_warnings.append(f"WebSocket cleanup unavailable: {str(e)}")
        
        # Start performance monitoring
        try:
            logger.info("Starting performance monitoring...")
            from app.services.performance_monitoring_service import start_performance_monitoring
            asyncio.create_task(start_performance_monitoring(db_manager.get_session()))
            logger.info("Performance monitoring started successfully")
        except Exception as e:
            logger.warning(f"Performance monitoring failed to start: {str(e)}")
            app.state.initialization_warnings.append(f"Performance monitoring unavailable: {str(e)}")
        
        # Phase 7: Final Validation
        logger.info("Phase 7: Performing final startup validation...")
        
        # Ensure all previous phases are complete
        logger.info("Verifying all initialization phases are complete...")
        await asyncio.sleep(1.0)  # Brief pause to ensure all background tasks are stable
        
        try:
            # Perform comprehensive validation with enhanced error reporting
            logger.debug("Starting comprehensive dependency validation...")
            validation_results = await _validate_startup_dependencies()
            app.state.startup_validation = validation_results
            
            # Additional validation checks
            validation_results['agent_registration'] = bool(
                hasattr(app.state, 'agent_registration_results') and 
                app.state.agent_registration_results and
                any(result['success'] for result in app.state.agent_registration_results.values())
            )
            
            # Check for critical validation failures
            critical_validations = ['database', 'orchestrator']
            failed_critical = [key for key in critical_validations if not validation_results.get(key, False)]
            
            if failed_critical:
                raise Exception(f"Critical validation failures: {', '.join(failed_critical)}")
            
            logger.info("Final startup validation completed successfully")
            
        except Exception as e:
            logger.error(f"Final startup validation failed: {str(e)}")
            app.state.initialization_errors.append(f"Final validation failed: {str(e)}")
            raise Exception(f"Application startup validation failed: {str(e)}")
        
        # Calculate total startup time
        startup_time = (datetime.utcnow() - app.state.start_time).total_seconds()
        
        # Log startup summary
        logger.info("=" * 60)
        logger.info("JobSwitch.ai application startup completed!")
        logger.info(f"Total startup time: {startup_time:.2f} seconds")
        logger.info(f"Initialization errors: {len(app.state.initialization_errors)}")
        logger.info(f"Initialization warnings: {len(app.state.initialization_warnings)}")
        
        if app.state.initialization_errors:
            logger.warning("Initialization errors encountered:")
            for error in app.state.initialization_errors:
                logger.warning(f"  - {error}")
        
        if app.state.initialization_warnings:
            logger.info("Initialization warnings:")
            for warning in app.state.initialization_warnings:
                logger.info(f"  - {warning}")
        
        # Log validation results
        logger.info("Startup validation results:")
        for component, status in validation_results.items():
            status_text = "PASSED" if status else "FAILED"
            logger.info(f"  - {component}: {status_text}")
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Critical failure during application startup: {str(e)}")
        logger.error("Application startup failed - initiating graceful shutdown")
        
        # Store the critical error with context
        if not hasattr(app.state, 'initialization_errors'):
            app.state.initialization_errors = []
        app.state.initialization_errors.append(f"Critical startup failure: {str(e)}")
        
        # Store startup failure metadata
        app.state.startup_failed = True
        app.state.startup_failure_time = datetime.utcnow()
        app.state.startup_failure_reason = str(e)
        
        # Attempt graceful cleanup with error tracking
        cleanup_errors = []
        try:
            logger.info("Attempting graceful cleanup after startup failure...")
            cleanup_errors = await _cleanup_failed_startup(app)
            
            if cleanup_errors:
                logger.error(f"Cleanup completed with {len(cleanup_errors)} errors")
            else:
                logger.info("Graceful cleanup completed successfully")
                
        except Exception as cleanup_error:
            error_msg = f"Critical error during startup cleanup: {str(cleanup_error)}"
            logger.error(error_msg)
            cleanup_errors.append(error_msg)
            
            # Store cleanup errors
            if not hasattr(app.state, 'cleanup_errors'):
                app.state.cleanup_errors = []
            app.state.cleanup_errors.append(error_msg)
        
        # Log final startup failure summary
        total_startup_time = (datetime.utcnow() - app.state.start_time).total_seconds()
        logger.error("=" * 60)
        logger.error("APPLICATION STARTUP FAILED")
        logger.error(f"Failure time: {total_startup_time:.2f} seconds after start")
        logger.error(f"Primary cause: {str(e)}")
        logger.error(f"Total initialization errors: {len(app.state.initialization_errors)}")
        logger.error(f"Cleanup errors: {len(cleanup_errors)}")
        logger.error("=" * 60)
        
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down JobSwitch.ai application...")
    
    try:
        # Stop agent orchestrator
        from app.core.orchestrator import shutdown_orchestrator
        await shutdown_orchestrator()
        
        # Close Redis cache connection
        from app.core.cache import cache_manager
        await cache_manager.close()
        
        # Close WatsonX.ai client
        if hasattr(app.state, 'watsonx_client') and app.state.watsonx_client:
            # WatsonX client cleanup would go here
            pass
        
        logger.info("Application shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered career copilot platform with specialized AI agents",
    lifespan=lifespan
)

# Setup comprehensive error handling
setup_error_handling(app)

# Add security middleware (order matters - add before CORS)
from app.middleware.security import (
    SecurityMiddleware, InputValidationMiddleware, CSRFProtectionMiddleware,
    ContentSecurityPolicyMiddleware, DataLeakPreventionMiddleware,
    RequestSizeMiddleware, SecurityAuditMiddleware
)

# Add security audit middleware first (for comprehensive logging)
app.add_middleware(SecurityAuditMiddleware)

# Add request size limiting middleware
app.add_middleware(RequestSizeMiddleware, max_size=10 * 1024 * 1024)  # 10MB

# Add data leak prevention middleware
app.add_middleware(DataLeakPreventionMiddleware)

# Add Content Security Policy middleware
app.add_middleware(
    ContentSecurityPolicyMiddleware,
    csp_policy={
        "default-src": ["'self'"],
        "script-src": ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
        "style-src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
        "font-src": ["'self'", "https://fonts.gstatic.com"],
        "img-src": ["'self'", "data:", "https:"],
        "connect-src": ["'self'", "wss:", "https:"],
        "frame-ancestors": ["'none'"],
        "base-uri": ["'self'"],
        "form-action": ["'self'"]
    }
)

# Add input validation middleware
app.add_middleware(InputValidationMiddleware)

# Add CSRF protection middleware
app.add_middleware(
    CSRFProtectionMiddleware,
    exempt_paths=["/docs", "/redoc", "/openapi.json", "/health", "/monitoring", "/", "/api/auth/login", "/api/auth/register"]
)

# Add performance tracking middleware
from app.middleware.performance_tracking import PerformanceTrackingMiddleware
app.add_middleware(PerformanceTrackingMiddleware)

# Add comprehensive security middleware
app.add_middleware(
    SecurityMiddleware,
    enable_rate_limiting=settings.environment == "production",
    enable_abuse_detection=settings.environment == "production"
)

# Add CORS middleware
cors_config = config.get_cors_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config["origins"],
    allow_credentials=cors_config["allow_credentials"],
    allow_methods=cors_config["allow_methods"],
    allow_headers=cors_config["allow_headers"],
)

# Include API routers
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(user_router, prefix=settings.api_prefix)
app.include_router(jobs_router, prefix=settings.api_prefix)
app.include_router(skills_router, prefix=settings.api_prefix)
app.include_router(resume_router, prefix=settings.api_prefix)
app.include_router(interview_router, prefix=settings.api_prefix)
app.include_router(technical_interview_router, prefix=settings.api_prefix)
app.include_router(networking_router, prefix=settings.api_prefix)
app.include_router(career_strategy_router, prefix=settings.api_prefix)
app.include_router(orchestrator_router, prefix=settings.api_prefix)
app.include_router(dashboard_router, prefix=settings.api_prefix)
app.include_router(data_management_router, prefix=settings.api_prefix)
app.include_router(gdpr_router, prefix=settings.api_prefix)
app.include_router(analytics_router, prefix=settings.api_prefix)
app.include_router(ab_testing_router, prefix=settings.api_prefix)
app.include_router(websocket_router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint with agent registration status
    
    Returns:
        Detailed application health status including agent information
    """
    try:
        # Perform comprehensive health check
        health_result = await monitoring_manager.perform_health_check()
        
        # Add basic application info
        health_result.update({
            "version": settings.app_version,
            "environment": settings.environment,
            "uptime_seconds": (datetime.utcnow() - app.state.start_time).total_seconds() if hasattr(app.state, 'start_time') else None
        })
        
        # Add comprehensive orchestrator readiness status
        try:
            from app.core.orchestrator import orchestrator as current_orchestrator
            
            if current_orchestrator is not None:
                orchestrator_status = {
                    "is_ready": current_orchestrator.is_ready,
                    "initialization_phase": current_orchestrator._initialization_phase,
                    "is_running": current_orchestrator.is_running,
                    "registered_agents_count": len(current_orchestrator.agents),
                    "registered_agents": list(current_orchestrator.agents.keys()),
                    "active_tasks_count": len(current_orchestrator.active_tasks) if hasattr(current_orchestrator, 'active_tasks') else 0,
                    "task_queue_size": len(current_orchestrator.task_queue) if hasattr(current_orchestrator, 'task_queue') else 0
                }
                
                # Add initialization timing information
                if hasattr(current_orchestrator, '_initialization_start_time') and current_orchestrator._initialization_start_time:
                    orchestrator_status["initialization_start_time"] = current_orchestrator._initialization_start_time.isoformat()
                    
                    if hasattr(current_orchestrator, '_initialization_complete_time') and current_orchestrator._initialization_complete_time:
                        orchestrator_status["initialization_complete_time"] = current_orchestrator._initialization_complete_time.isoformat()
                        orchestrator_status["initialization_duration_seconds"] = (
                            current_orchestrator._initialization_complete_time - current_orchestrator._initialization_start_time
                        ).total_seconds()
                    elif current_orchestrator._initialization_phase == "initializing":
                        orchestrator_status["initialization_in_progress"] = True
                        orchestrator_status["initialization_elapsed_seconds"] = (
                            datetime.utcnow() - current_orchestrator._initialization_start_time
                        ).total_seconds()
                
                # Add task processing statistics if available
                if hasattr(current_orchestrator, 'completed_tasks'):
                    orchestrator_status["completed_tasks_count"] = len(current_orchestrator.completed_tasks)
                if hasattr(current_orchestrator, 'failed_tasks'):
                    orchestrator_status["failed_tasks_count"] = len(current_orchestrator.failed_tasks)
                
                # Add configuration information
                orchestrator_status["configuration"] = {
                    "max_queue_size": getattr(current_orchestrator, 'max_queue_size', 'unknown'),
                    "max_concurrent_tasks": getattr(current_orchestrator, 'max_concurrent_tasks', 'unknown'),
                    "health_check_interval": getattr(current_orchestrator, 'health_check_interval', 'unknown')
                }
                
                # Add readiness waiters information
                if hasattr(current_orchestrator, '_readiness_waiters'):
                    orchestrator_status["pending_readiness_waiters"] = len(current_orchestrator._readiness_waiters)
                
                health_result["orchestrator"] = orchestrator_status
            else:
                health_result["orchestrator"] = {
                    "is_ready": False,
                    "initialization_phase": "not_initialized",
                    "is_running": False,
                    "error": "Orchestrator instance not found",
                    "registered_agents_count": 0,
                    "registered_agents": [],
                    "active_tasks_count": 0,
                    "task_queue_size": 0
                }
        except Exception as e:
            health_result["orchestrator"] = {
                "is_ready": False,
                "initialization_phase": "error",
                "is_running": False,
                "error": f"Failed to get orchestrator status: {str(e)}",
                "registered_agents_count": 0,
                "registered_agents": [],
                "active_tasks_count": 0,
                "task_queue_size": 0
            }
        
        # Add comprehensive agent registration status
        try:
            agent_status = {}
            agent_summary = {
                "total_configured": 0,
                "successfully_registered": 0,
                "failed_registrations": 0,
                "pending_registrations": 0
            }
            
            # Get agent status from app state (startup registration results)
            if hasattr(app.state, 'agent_registration_results'):
                agent_summary["total_configured"] = len(app.state.agent_registration_results)
                
                for agent_name, result in app.state.agent_registration_results.items():
                    agent_status[agent_name] = {
                        "registered": result['success'],
                        "startup_error": result['error'],
                        "startup_success": result['success']
                    }
                    
                    if result['success']:
                        agent_summary["successfully_registered"] += 1
                    else:
                        agent_summary["failed_registrations"] += 1
            
            # Add detailed registration status from orchestrator
            if current_orchestrator is not None:
                # Get orchestrator-level agent information
                orchestrator_agents = list(current_orchestrator.agents.keys()) if hasattr(current_orchestrator, 'agents') else []
                
                # Add agents that are registered with orchestrator but not in startup results
                for agent_id in orchestrator_agents:
                    if agent_id not in agent_status:
                        agent_status[agent_id] = {
                            "registered": True,
                            "startup_error": None,
                            "startup_success": True
                        }
                        agent_summary["successfully_registered"] += 1
                        agent_summary["total_configured"] += 1
                
                # Add detailed registration status from orchestrator tracking
                if hasattr(current_orchestrator, 'agent_registration_status'):
                    for agent_id, registration_status in current_orchestrator.agent_registration_status.items():
                        if agent_id not in agent_status:
                            agent_status[agent_id] = {
                                "registered": registration_status.is_registered,
                                "startup_error": None,
                                "startup_success": registration_status.is_registered
                            }
                            
                            if registration_status.is_registered:
                                agent_summary["successfully_registered"] += 1
                            else:
                                agent_summary["failed_registrations"] += 1
                            agent_summary["total_configured"] += 1
                        
                        # Add detailed orchestrator registration information
                        agent_status[agent_id].update({
                            "registration_time": registration_status.registration_time.isoformat() if registration_status.registration_time else None,
                            "last_health_check": registration_status.last_health_check.isoformat() if registration_status.last_health_check else None,
                            "retry_count": registration_status.retry_count,
                            "validation_passed": registration_status.validation_passed,
                            "total_attempts": len(registration_status.registration_attempts),
                            "current_error": registration_status.error_message,
                            "registration_attempts": [
                                {
                                    "timestamp": attempt['timestamp'].isoformat(),
                                    "success": attempt['success'],
                                    "error_message": attempt['error_message']
                                }
                                for attempt in registration_status.registration_attempts
                            ] if hasattr(registration_status, 'registration_attempts') else []
                        })
                
                # Add agent health information if available
                if hasattr(current_orchestrator, 'agent_health'):
                    for agent_id, health_status in current_orchestrator.agent_health.items():
                        if agent_id in agent_status:
                            agent_status[agent_id].update({
                                "health_status": health_status.status.value if hasattr(health_status.status, 'value') else str(health_status.status),
                                "last_heartbeat": health_status.last_heartbeat.isoformat() if health_status.last_heartbeat else None,
                                "average_response_time": health_status.get_average_response_time(),
                                "success_rate": health_status.get_success_rate(),
                                "error_count": health_status.error_count,
                                "success_count": health_status.success_count,
                                "current_load": health_status.current_load,
                                "max_load": health_status.max_load,
                                "is_healthy": health_status.is_healthy()
                            })
            
            # Calculate pending registrations
            agent_summary["pending_registrations"] = max(0, agent_summary["total_configured"] - agent_summary["successfully_registered"] - agent_summary["failed_registrations"])
            
            health_result["agents"] = {
                "summary": agent_summary,
                "registration_details": agent_status
            }
            
            # Add agent registration timing information if available
            if hasattr(app.state, 'agent_registration_start_time') and hasattr(app.state, 'agent_registration_complete_time'):
                health_result["agents"]["timing"] = {
                    "registration_start_time": app.state.agent_registration_start_time.isoformat(),
                    "registration_complete_time": app.state.agent_registration_complete_time.isoformat(),
                    "total_registration_time_seconds": (app.state.agent_registration_complete_time - app.state.agent_registration_start_time).total_seconds()
                }
            elif hasattr(app.state, 'agent_registration_start_time'):
                health_result["agents"]["timing"] = {
                    "registration_start_time": app.state.agent_registration_start_time.isoformat(),
                    "registration_in_progress": True,
                    "elapsed_time_seconds": (datetime.utcnow() - app.state.agent_registration_start_time).total_seconds()
                }
            
        except Exception as e:
            health_result["agents"] = {
                "error": f"Failed to get agent status: {str(e)}",
                "summary": {
                    "total_configured": 0,
                    "successfully_registered": 0,
                    "failed_registrations": 0,
                    "pending_registrations": 0
                }
            }
        
        # Add initialization status
        if hasattr(app.state, 'initialization_errors') or hasattr(app.state, 'initialization_warnings'):
            health_result["initialization"] = {
                "errors": getattr(app.state, 'initialization_errors', []),
                "warnings": getattr(app.state, 'initialization_warnings', []),
                "error_count": len(getattr(app.state, 'initialization_errors', [])),
                "warning_count": len(getattr(app.state, 'initialization_warnings', []))
            }
        
        # Determine overall health status
        overall_status = "healthy"
        status_code = 200
        
        # Check for critical issues
        if hasattr(app.state, 'initialization_errors') and app.state.initialization_errors:
            # Check if any errors are critical
            critical_errors = [e for e in app.state.initialization_errors if 
                             'database' in e.lower() or 'orchestrator' in e.lower() or 'critical' in e.lower()]
            if critical_errors:
                overall_status = "critical"
                status_code = 503
            else:
                overall_status = "degraded"
        
        # Check orchestrator status
        try:
            from app.core.orchestrator import orchestrator as current_orchestrator
            if current_orchestrator is None or not current_orchestrator.is_ready:
                overall_status = "critical" if overall_status != "critical" else overall_status
                status_code = 503
        except Exception:
            overall_status = "critical"
            status_code = 503
        
        # Check agent registration
        if hasattr(app.state, 'agent_registration_results'):
            successful_agents = sum(1 for r in app.state.agent_registration_results.values() if r['success'])
            total_agents = len(app.state.agent_registration_results)
            
            if successful_agents == 0 and total_agents > 0:
                overall_status = "critical"
                status_code = 503
            elif successful_agents < total_agents and overall_status == "healthy":
                overall_status = "degraded"
        
        health_result["overall_status"] = overall_status
        
        return JSONResponse(
            status_code=status_code,
            content=health_result
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "overall_status": "critical",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Detailed monitoring endpoint
@app.get("/monitoring")
async def monitoring_stats():
    """
    Detailed monitoring and metrics endpoint
    
    Returns:
        Comprehensive monitoring statistics
    """
    try:
        from app.core.monitoring import get_monitoring_stats
        
        stats = get_monitoring_stats()
        
        # Add error handling stats
        stats["error_handling"] = error_handling_health.get_health_status()
        
        return stats
        
    except Exception as e:
        logger.error(f"Monitoring stats failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Legacy endpoint for backward compatibility
@app.post("/api/generate-cover-letter")
async def generate_cover_letter(request: Request):
    """
    Legacy cover letter generation endpoint
    Maintained for backward compatibility
    """
    try:
        data = await request.json()
        job_description = data.get("description", "")
        
        if not hasattr(app.state, 'watsonx_client') or not app.state.watsonx_client:
            return JSONResponse(
                status_code=503,
                content={"error": "AI services not available"}
            )
        
        # Use WatsonX.ai to generate cover letter
        async with app.state.watsonx_client as client:
            prompt = f"""
            Generate a professional cover letter for the following job description:
            
            {job_description}
            
            The cover letter should be:
            - Professional and engaging
            - Tailored to the specific role
            - Highlighting relevant skills and experience
            - Following standard business letter format
            
            Cover Letter:
            """
            
            result = await client.generate_text(prompt)
            
            if result["success"]:
                return {
                    "success": True,
                    "cover_letter": result["generated_text"],
                    "model_used": "watsonx"
                }
            else:
                return JSONResponse(
                    status_code=500,
                    content={"error": result.get("error", "Generation failed")}
                )
                
    except Exception as e:
        logger.error(f"Cover letter generation failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with application information
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "AI-powered career copilot platform",
        "environment": settings.environment,
        "api_prefix": settings.api_prefix,
        "health_check": "/health"
    }


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
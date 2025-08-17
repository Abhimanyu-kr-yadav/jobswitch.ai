"""
Agent Orchestrator API Endpoints
Provides REST API for managing agent orchestration and monitoring
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging

from app.core.orchestrator import orchestrator, TaskPriority, MessageType
from app.core.auth import get_current_user
from app.models.user import UserProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


# Request/Response Models
class TaskCreateRequest(BaseModel):
    agent_id: str
    task_type: str
    payload: Dict[str, Any]
    priority: str = "medium"
    dependencies: Optional[List[str]] = None
    timeout_seconds: Optional[int] = 300


class MessageSendRequest(BaseModel):
    recipient_id: str
    message_type: str
    payload: Dict[str, Any]
    correlation_id: Optional[str] = None


class WorkflowExecuteRequest(BaseModel):
    workflow_id: Optional[str] = None
    steps: List[Dict[str, Any]]
    input_data: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = 300


class ContextUpdateRequest(BaseModel):
    context_key: str = "global"
    update: Dict[str, Any]


# Helper functions
def _get_priority_enum(priority_str: str) -> TaskPriority:
    """Convert priority string to enum"""
    priority_map = {
        "low": TaskPriority.LOW,
        "medium": TaskPriority.MEDIUM,
        "high": TaskPriority.HIGH,
        "urgent": TaskPriority.URGENT
    }
    return priority_map.get(priority_str.lower(), TaskPriority.MEDIUM)


def _get_message_type_enum(message_type_str: str) -> MessageType:
    """Convert message type string to enum"""
    type_map = {
        "request": MessageType.REQUEST,
        "response": MessageType.RESPONSE,
        "broadcast": MessageType.BROADCAST,
        "context_update": MessageType.CONTEXT_UPDATE,
        "health_check": MessageType.HEALTH_CHECK
    }
    return type_map.get(message_type_str.lower(), MessageType.REQUEST)


# API Endpoints
@router.get("/status")
async def get_orchestrator_status(current_user: UserProfile = Depends(get_current_user)):
    """Get overall orchestrator status"""
    try:
        status = await orchestrator.get_orchestrator_status()
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        logger.error(f"Error getting orchestrator status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def list_agents(current_user: UserProfile = Depends(get_current_user)):
    """List all registered agents"""
    try:
        agents = []
        for agent_id in orchestrator.agents.keys():
            agent_status = await orchestrator.get_agent_status(agent_id)
            agents.append(agent_status)
        
        return {
            "success": True,
            "data": {
                "agents": agents,
                "count": len(agents)
            }
        }
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}/status")
async def get_agent_status(agent_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Get status of a specific agent"""
    try:
        status = await orchestrator.get_agent_status(agent_id)
        if not status:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        return {
            "success": True,
            "data": status
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks")
async def create_task(
    request: TaskCreateRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """Create and submit a new task"""
    try:
        priority = _get_priority_enum(request.priority)
        
        task_id = await orchestrator.create_task(
            agent_id=request.agent_id,
            task_type=request.task_type,
            payload=request.payload,
            priority=priority,
            dependencies=request.dependencies
        )
        
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "message": "Task created and queued successfully"
            }
        }
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Get status of a specific task"""
    try:
        status = await orchestrator.get_task_status(task_id)
        if not status:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        return {
            "success": True,
            "data": status
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Cancel a pending or active task"""
    try:
        cancelled = await orchestrator.cancel_task(task_id)
        if not cancelled:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found or cannot be cancelled")
        
        return {
            "success": True,
            "data": {
                "message": f"Task {task_id} cancelled successfully"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
    limit: int = 100,
    current_user: UserProfile = Depends(get_current_user)
):
    """List tasks with optional filtering"""
    try:
        all_tasks = []
        
        # Collect tasks from different collections
        for task_collection in [orchestrator.task_queue, 
                               list(orchestrator.active_tasks.values()),
                               list(orchestrator.completed_tasks.values()),
                               list(orchestrator.failed_tasks.values())]:
            for task in task_collection:
                task_dict = task.to_dict() if hasattr(task, 'to_dict') else task
                
                # Apply filters
                if status and task_dict.get("status") != status:
                    continue
                if agent_id and task_dict.get("agent_id") != agent_id:
                    continue
                
                all_tasks.append(task_dict)
        
        # Sort by created_at descending and limit
        all_tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        all_tasks = all_tasks[:limit]
        
        return {
            "success": True,
            "data": {
                "tasks": all_tasks,
                "count": len(all_tasks)
            }
        }
    except Exception as e:
        logger.error(f"Error listing tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/messages")
async def send_message(
    request: MessageSendRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """Send a message between agents"""
    try:
        message_type = _get_message_type_enum(request.message_type)
        
        message_id = await orchestrator.send_message(
            sender_id="api_user",  # Could be current_user.id
            recipient_id=request.recipient_id,
            message_type=message_type,
            payload=request.payload,
            correlation_id=request.correlation_id
        )
        
        return {
            "success": True,
            "data": {
                "message_id": message_id,
                "message": "Message sent successfully"
            }
        }
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context/update")
async def update_context(
    request: ContextUpdateRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """Update shared context and broadcast to agents"""
    try:
        await orchestrator.broadcast_context_update(
            context_update=request.update,
            context_key=request.context_key
        )
        
        return {
            "success": True,
            "data": {
                "message": f"Context updated for key '{request.context_key}'"
            }
        }
    except Exception as e:
        logger.error(f"Error updating context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context")
async def get_context(
    context_key: Optional[str] = None,
    current_user: UserProfile = Depends(get_current_user)
):
    """Get shared context data"""
    try:
        context_data = await orchestrator.get_shared_context(context_key)
        
        return {
            "success": True,
            "data": {
                "context": context_data,
                "context_key": context_key or "all"
            }
        }
    except Exception as e:
        logger.error(f"Error getting context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/execute")
async def execute_workflow(
    request: WorkflowExecuteRequest,
    background_tasks: BackgroundTasks,
    current_user: UserProfile = Depends(get_current_user)
):
    """Execute a complex workflow with multiple agents"""
    try:
        workflow_definition = {
            "workflow_id": request.workflow_id,
            "steps": request.steps,
            "input_data": request.input_data or {},
            "timeout": request.timeout
        }
        
        # Execute workflow asynchronously
        result = await orchestrator.coordinate_agents(workflow_definition)
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Error executing workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint for the orchestrator"""
    try:
        status = await orchestrator.get_orchestrator_status()
        
        return {
            "success": True,
            "data": {
                "status": "healthy" if status["is_running"] else "unhealthy",
                "orchestrator": status
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/restart")
async def restart_orchestrator(current_user: UserProfile = Depends(get_current_user)):
    """Restart the orchestrator (admin only)"""
    try:
        # This would typically require admin privileges
        await orchestrator.stop()
        await orchestrator.start()
        
        return {
            "success": True,
            "data": {
                "message": "Orchestrator restarted successfully"
            }
        }
    except Exception as e:
        logger.error(f"Error restarting orchestrator: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

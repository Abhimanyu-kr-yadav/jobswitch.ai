"""
A/B Testing API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.core.database import get_database
from app.core.auth import get_current_user
from app.models.user import UserProfile
from app.services.ab_testing_service import ABTestingService
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/ab-testing", tags=["ab-testing"])

class ExperimentCreate(BaseModel):
    name: str
    description: str
    feature_name: str
    control_algorithm: str
    test_algorithm: str
    traffic_split: float = 0.5
    primary_metric: str = "conversion_rate"
    secondary_metrics: List[str] = []

class EventRecord(BaseModel):
    event_type: str
    event_value: float = 1.0
    metadata: Optional[Dict[str, Any]] = None

@router.post("/experiments")
async def create_experiment(
    experiment_data: ExperimentCreate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """Create a new A/B test experiment (admin only)"""
    try:
        # Check if user is admin
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        service = ABTestingService(db)
        
        experiment_id = await service.create_experiment(
            name=experiment_data.name,
            description=experiment_data.description,
            feature_name=experiment_data.feature_name,
            control_algorithm=experiment_data.control_algorithm,
            test_algorithm=experiment_data.test_algorithm,
            traffic_split=experiment_data.traffic_split,
            primary_metric=experiment_data.primary_metric,
            secondary_metrics=experiment_data.secondary_metrics
        )
        
        return {
            "success": True,
            "data": {"experiment_id": experiment_id}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating experiment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create experiment")

@router.post("/experiments/{experiment_id}/start")
async def start_experiment(
    experiment_id: str,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """Start an A/B test experiment (admin only)"""
    try:
        # Check if user is admin
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        service = ABTestingService(db)
        success = await service.start_experiment(experiment_id)
        
        return {
            "success": success,
            "message": "Experiment started successfully"
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting experiment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start experiment")

@router.post("/experiments/{experiment_id}/stop")
async def stop_experiment(
    experiment_id: str,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """Stop an A/B test experiment (admin only)"""
    try:
        # Check if user is admin
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        service = ABTestingService(db)
        success = await service.stop_experiment(experiment_id)
        
        return {
            "success": success,
            "message": "Experiment stopped successfully"
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error stopping experiment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to stop experiment")

@router.get("/experiments")
async def get_experiments(
    status: Optional[str] = Query(None),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """Get A/B test experiments (admin only)"""
    try:
        # Check if user is admin
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        service = ABTestingService(db)
        
        if status == "active":
            experiments = await service.get_active_experiments()
        else:
            # Get all experiments (you'd implement this method)
            experiments = await service.get_active_experiments()  # Simplified for now
        
        return {
            "success": True,
            "data": {
                "experiments": experiments,
                "total": len(experiments)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting experiments: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get experiments")

@router.get("/experiments/{experiment_id}/results")
async def get_experiment_results(
    experiment_id: str,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """Get A/B test experiment results (admin only)"""
    try:
        # Check if user is admin
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        service = ABTestingService(db)
        results = await service.get_experiment_results(experiment_id)
        
        return {
            "success": True,
            "data": results
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting experiment results: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get experiment results")

@router.get("/user/assignment/{feature_name}")
async def get_user_assignment(
    feature_name: str,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """Get user's experiment assignment for a feature"""
    try:
        service = ABTestingService(db)
        group, experiment_id = await service.get_user_experiment_group(current_user.id, feature_name)
        
        return {
            "success": True,
            "data": {
                "feature_name": feature_name,
                "group": group,
                "experiment_id": experiment_id
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user assignment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user assignment")

@router.post("/experiments/{experiment_id}/events")
async def record_experiment_event(
    experiment_id: str,
    event_data: EventRecord,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """Record an event for experiment tracking"""
    try:
        service = ABTestingService(db)
        
        success = await service.record_experiment_event(
            user_id=current_user.id,
            experiment_id=experiment_id,
            event_type=event_data.event_type,
            event_value=event_data.event_value,
            metadata=event_data.metadata
        )
        
        return {
            "success": success,
            "message": "Event recorded successfully" if success else "Failed to record event"
        }
        
    except Exception as e:
        logger.error(f"Error recording experiment event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record event")

# Utility endpoint for testing A/B test assignments
@router.get("/debug/user-assignments")
async def debug_user_assignments(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """Debug endpoint to see all user's experiment assignments"""
    try:
        from app.models.analytics import ABTestParticipant, ABTestExperiment
        
        assignments = db.query(ABTestParticipant, ABTestExperiment).join(
            ABTestExperiment, ABTestParticipant.experiment_id == ABTestExperiment.id
        ).filter(ABTestParticipant.user_id == current_user.id).all()
        
        assignment_data = []
        for participant, experiment in assignments:
            assignment_data.append({
                "experiment_name": experiment.name,
                "feature_name": experiment.feature_name,
                "group": participant.group,
                "assigned_at": participant.assigned_at.isoformat(),
                "experiment_status": experiment.status
            })
        
        return {
            "success": True,
            "data": {
                "user_id": current_user.id,
                "assignments": assignment_data
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting debug assignments: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get assignments")

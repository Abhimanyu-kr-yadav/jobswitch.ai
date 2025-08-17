"""
A/B Testing service for optimizing recommendation algorithms
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import random
import hashlib
import json
from enum import Enum

from app.models.analytics import ABTestExperiment, ABTestParticipant
from app.core.database import get_database
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class ExperimentStatus(Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"

class ABTestingService:
    """Service for managing A/B testing experiments"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_experiment(
        self,
        name: str,
        description: str,
        feature_name: str,
        control_algorithm: str,
        test_algorithm: str,
        traffic_split: float = 0.5,
        primary_metric: str = "conversion_rate",
        secondary_metrics: List[str] = None
    ) -> str:
        """Create a new A/B test experiment"""
        try:
            experiment = ABTestExperiment(
                name=name,
                description=description,
                feature_name=feature_name,
                control_algorithm=control_algorithm,
                test_algorithm=test_algorithm,
                traffic_split=traffic_split,
                primary_metric=primary_metric,
                secondary_metrics=secondary_metrics or [],
                status=ExperimentStatus.DRAFT.value
            )
            
            self.db.add(experiment)
            self.db.commit()
            
            logger.info(f"Created A/B test experiment: {name}")
            return experiment.id
            
        except Exception as e:
            logger.error(f"Error creating experiment: {str(e)}")
            self.db.rollback()
            raise
    
    async def start_experiment(self, experiment_id: str) -> bool:
        """Start an A/B test experiment"""
        try:
            experiment = self.db.query(ABTestExperiment).filter(
                ABTestExperiment.id == experiment_id
            ).first()
            
            if not experiment:
                raise ValueError("Experiment not found")
            
            if experiment.status != ExperimentStatus.DRAFT.value:
                raise ValueError("Only draft experiments can be started")
            
            experiment.status = ExperimentStatus.RUNNING.value
            experiment.start_date = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Started experiment: {experiment.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting experiment: {str(e)}")
            self.db.rollback()
            raise
    
    async def stop_experiment(self, experiment_id: str) -> bool:
        """Stop an A/B test experiment"""
        try:
            experiment = self.db.query(ABTestExperiment).filter(
                ABTestExperiment.id == experiment_id
            ).first()
            
            if not experiment:
                raise ValueError("Experiment not found")
            
            experiment.status = ExperimentStatus.COMPLETED.value
            experiment.end_date = datetime.utcnow()
            
            # Calculate final results
            await self._calculate_experiment_results(experiment_id)
            
            self.db.commit()
            
            logger.info(f"Stopped experiment: {experiment.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping experiment: {str(e)}")
            self.db.rollback()
            raise
    
    async def assign_user_to_experiment(
        self,
        user_id: str,
        experiment_id: str
    ) -> str:
        """Assign a user to an experiment group (control or test)"""
        try:
            # Check if user is already assigned
            existing_assignment = self.db.query(ABTestParticipant).filter(
                and_(
                    ABTestParticipant.user_id == user_id,
                    ABTestParticipant.experiment_id == experiment_id
                )
            ).first()
            
            if existing_assignment:
                return existing_assignment.group
            
            # Get experiment details
            experiment = self.db.query(ABTestExperiment).filter(
                ABTestExperiment.id == experiment_id
            ).first()
            
            if not experiment or experiment.status != ExperimentStatus.RUNNING.value:
                return "control"  # Default to control if experiment not running
            
            # Deterministic assignment based on user ID hash
            user_hash = hashlib.md5(f"{user_id}_{experiment_id}".encode()).hexdigest()
            hash_value = int(user_hash[:8], 16) / (16**8)  # Convert to 0-1 range
            
            group = "test" if hash_value < experiment.traffic_split else "control"
            
            # Record assignment
            participant = ABTestParticipant(
                experiment_id=experiment_id,
                user_id=user_id,
                group=group
            )
            
            self.db.add(participant)
            self.db.commit()
            
            logger.info(f"Assigned user {user_id} to {group} group for experiment {experiment.name}")
            return group
            
        except Exception as e:
            logger.error(f"Error assigning user to experiment: {str(e)}")
            self.db.rollback()
            return "control"  # Default to control on error
    
    async def get_user_experiment_group(
        self,
        user_id: str,
        feature_name: str
    ) -> Tuple[str, Optional[str]]:
        """Get user's experiment group for a specific feature"""
        try:
            # Find active experiment for this feature
            experiment = self.db.query(ABTestExperiment).filter(
                and_(
                    ABTestExperiment.feature_name == feature_name,
                    ABTestExperiment.status == ExperimentStatus.RUNNING.value
                )
            ).first()
            
            if not experiment:
                return "control", None
            
            # Get or assign user to experiment
            group = await self.assign_user_to_experiment(user_id, experiment.id)
            
            return group, experiment.id
            
        except Exception as e:
            logger.error(f"Error getting user experiment group: {str(e)}")
            return "control", None
    
    async def record_experiment_event(
        self,
        user_id: str,
        experiment_id: str,
        event_type: str,
        event_value: float = 1.0,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Record an event for experiment tracking"""
        try:
            # Get user's group assignment
            participant = self.db.query(ABTestParticipant).filter(
                and_(
                    ABTestParticipant.user_id == user_id,
                    ABTestParticipant.experiment_id == experiment_id
                )
            ).first()
            
            if not participant:
                logger.warning(f"User {user_id} not found in experiment {experiment_id}")
                return False
            
            # Store event data (you might want a separate events table for detailed tracking)
            # For now, we'll update the experiment metrics directly
            await self._update_experiment_metrics(
                experiment_id,
                participant.group,
                event_type,
                event_value
            )
            
            logger.info(f"Recorded event {event_type} for user {user_id} in experiment {experiment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording experiment event: {str(e)}")
            return False
    
    async def get_experiment_results(self, experiment_id: str) -> Dict[str, Any]:
        """Get current results for an experiment"""
        try:
            experiment = self.db.query(ABTestExperiment).filter(
                ABTestExperiment.id == experiment_id
            ).first()
            
            if not experiment:
                raise ValueError("Experiment not found")
            
            # Get participant counts
            control_count = self.db.query(ABTestParticipant).filter(
                and_(
                    ABTestParticipant.experiment_id == experiment_id,
                    ABTestParticipant.group == "control"
                )
            ).count()
            
            test_count = self.db.query(ABTestParticipant).filter(
                and_(
                    ABTestParticipant.experiment_id == experiment_id,
                    ABTestParticipant.group == "test"
                )
            ).count()
            
            # Calculate statistical significance (simplified)
            significance = await self._calculate_statistical_significance(
                experiment.control_conversion_rate or 0,
                experiment.test_conversion_rate or 0,
                control_count,
                test_count
            )
            
            return {
                "experiment_id": experiment.id,
                "name": experiment.name,
                "status": experiment.status,
                "start_date": experiment.start_date.isoformat() if experiment.start_date else None,
                "end_date": experiment.end_date.isoformat() if experiment.end_date else None,
                "participants": {
                    "control": control_count,
                    "test": test_count,
                    "total": control_count + test_count
                },
                "metrics": {
                    "primary_metric": experiment.primary_metric,
                    "control_conversion_rate": experiment.control_conversion_rate or 0,
                    "test_conversion_rate": experiment.test_conversion_rate or 0,
                    "lift": self._calculate_lift(
                        experiment.control_conversion_rate or 0,
                        experiment.test_conversion_rate or 0
                    ),
                    "statistical_significance": significance
                },
                "algorithms": {
                    "control": experiment.control_algorithm,
                    "test": experiment.test_algorithm
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting experiment results: {str(e)}")
            raise
    
    async def get_active_experiments(self) -> List[Dict[str, Any]]:
        """Get all active experiments"""
        try:
            experiments = self.db.query(ABTestExperiment).filter(
                ABTestExperiment.status == ExperimentStatus.RUNNING.value
            ).all()
            
            results = []
            for experiment in experiments:
                result = await self.get_experiment_results(experiment.id)
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting active experiments: {str(e)}")
            raise
    
    async def _calculate_experiment_results(self, experiment_id: str) -> None:
        """Calculate final results for an experiment"""
        try:
            # This is a simplified calculation
            # In a real implementation, you'd calculate based on actual event data
            
            experiment = self.db.query(ABTestExperiment).filter(
                ABTestExperiment.id == experiment_id
            ).first()
            
            if not experiment:
                return
            
            # Get participant counts
            control_count = self.db.query(ABTestParticipant).filter(
                and_(
                    ABTestParticipant.experiment_id == experiment_id,
                    ABTestParticipant.group == "control"
                )
            ).count()
            
            test_count = self.db.query(ABTestParticipant).filter(
                and_(
                    ABTestParticipant.experiment_id == experiment_id,
                    ABTestParticipant.group == "test"
                )
            ).count()
            
            # Simulate conversion rates (replace with actual calculation)
            experiment.control_conversion_rate = random.uniform(0.05, 0.15)
            experiment.test_conversion_rate = random.uniform(0.08, 0.18)
            
            # Calculate statistical significance
            experiment.statistical_significance = await self._calculate_statistical_significance(
                experiment.control_conversion_rate,
                experiment.test_conversion_rate,
                control_count,
                test_count
            )
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error calculating experiment results: {str(e)}")
            self.db.rollback()
    
    async def _update_experiment_metrics(
        self,
        experiment_id: str,
        group: str,
        event_type: str,
        event_value: float
    ) -> None:
        """Update experiment metrics based on events"""
        # This would typically update a separate events table
        # For now, we'll just log the event
        logger.info(f"Event recorded: {event_type} = {event_value} for {group} group in experiment {experiment_id}")
    
    async def _calculate_statistical_significance(
        self,
        control_rate: float,
        test_rate: float,
        control_count: int,
        test_count: int
    ) -> float:
        """Calculate statistical significance (simplified z-test)"""
        if control_count == 0 or test_count == 0:
            return 0.0
        
        # Simplified z-test calculation
        pooled_rate = (control_rate * control_count + test_rate * test_count) / (control_count + test_count)
        
        if pooled_rate == 0 or pooled_rate == 1:
            return 0.0
        
        se = (pooled_rate * (1 - pooled_rate) * (1/control_count + 1/test_count)) ** 0.5
        
        if se == 0:
            return 0.0
        
        z_score = abs(test_rate - control_rate) / se
        
        # Convert z-score to confidence level (simplified)
        if z_score > 2.58:
            return 0.99  # 99% confidence
        elif z_score > 1.96:
            return 0.95  # 95% confidence
        elif z_score > 1.65:
            return 0.90  # 90% confidence
        else:
            return 0.0
    
    def _calculate_lift(self, control_rate: float, test_rate: float) -> float:
        """Calculate percentage lift"""
        if control_rate == 0:
            return 0.0
        return ((test_rate - control_rate) / control_rate) * 100

# Decorator for A/B testing
def ab_test(feature_name: str, control_algorithm: str, test_algorithm: str):
    """Decorator to enable A/B testing for a function"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user_id from kwargs or args
            user_id = kwargs.get('user_id') or (args[0] if args else None)
            
            if not user_id:
                # If no user_id, use control algorithm
                return await func(*args, algorithm=control_algorithm, **kwargs)
            
            try:
                db = next(get_database())
                service = ABTestingService(db)
                
                group, experiment_id = await service.get_user_experiment_group(user_id, feature_name)
                
                algorithm = test_algorithm if group == "test" else control_algorithm
                
                # Add experiment info to kwargs
                kwargs['algorithm'] = algorithm
                kwargs['experiment_group'] = group
                kwargs['experiment_id'] = experiment_id
                
                return await func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in A/B test decorator: {str(e)}")
                # Fallback to control algorithm
                return await func(*args, algorithm=control_algorithm, **kwargs)
        
        return wrapper
    return decorator
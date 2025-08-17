"""
Middleware for tracking API performance metrics
"""
import time
import asyncio
from datetime import datetime
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import json

from app.core.cache import get_redis_client
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class PerformanceTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to track API performance metrics"""
    
    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self.redis_client = redis_client or get_redis_client()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timing
        start_time = time.time()
        
        # Get request info
        method = request.method
        path = request.url.path
        user_agent = request.headers.get("user-agent", "")
        
        # Process request
        response = None
        error = None
        
        try:
            response = await call_next(request)
        except Exception as e:
            error = str(e)
            logger.error(f"Request error: {error}")
            # Re-raise the exception
            raise
        finally:
            # Calculate response time
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            # Track metrics asynchronously
            asyncio.create_task(self._track_metrics(
                method=method,
                path=path,
                response_time_ms=response_time_ms,
                status_code=response.status_code if response else 500,
                error=error,
                user_agent=user_agent
            ))
        
        return response
    
    async def _track_metrics(
        self,
        method: str,
        path: str,
        response_time_ms: float,
        status_code: int,
        error: str = None,
        user_agent: str = ""
    ):
        """Track API metrics in Redis"""
        try:
            # Create metrics key for current hour
            current_hour = datetime.utcnow().strftime('%Y%m%d%H')
            metrics_key = f"api_metrics:{current_hour}"
            
            # Determine if request was successful
            is_success = 200 <= status_code < 400 and error is None
            is_external_api = self._is_external_api_call(path)
            
            # Update metrics atomically (only if Redis is available)
            if not self.redis_client:
                return
                
            pipe = self.redis_client.pipeline()
            
            # Total requests
            pipe.hincrby(metrics_key, 'total_requests', 1)
            
            # Success/failure counts
            if is_success:
                pipe.hincrby(metrics_key, 'successful_requests', 1)
            else:
                pipe.hincrby(metrics_key, 'failed_requests', 1)
            
            # Response time (running average)
            current_avg = await self.redis_client.hget(metrics_key, 'avg_response_time')
            current_count = await self.redis_client.hget(metrics_key, 'total_requests')
            
            if current_avg and current_count:
                current_avg = float(current_avg)
                current_count = int(current_count)
                new_avg = ((current_avg * (current_count - 1)) + response_time_ms) / current_count
            else:
                new_avg = response_time_ms
            
            pipe.hset(metrics_key, 'avg_response_time', new_avg)
            
            # External API metrics
            if is_external_api:
                pipe.hincrby(metrics_key, 'external_api_calls', 1)
                if not is_success:
                    pipe.hincrby(metrics_key, 'external_api_failures', 1)
                
                # External API response time
                ext_avg = await self.redis_client.hget(metrics_key, 'external_avg_response_time')
                ext_count = await self.redis_client.hget(metrics_key, 'external_api_calls')
                
                if ext_avg and ext_count:
                    ext_avg = float(ext_avg)
                    ext_count = int(ext_count)
                    new_ext_avg = ((ext_avg * (ext_count - 1)) + response_time_ms) / ext_count
                else:
                    new_ext_avg = response_time_ms
                
                pipe.hset(metrics_key, 'external_avg_response_time', new_ext_avg)
            
            # Execute pipeline
            await pipe.execute()
            
            # Set expiration for metrics (keep for 7 days)
            await self.redis_client.expire(metrics_key, 7 * 24 * 60 * 60)
            
            # Track endpoint-specific metrics
            await self._track_endpoint_metrics(path, response_time_ms, is_success)
            
            # Track user agent metrics (for mobile vs desktop analysis)
            await self._track_user_agent_metrics(user_agent, response_time_ms, is_success)
            
        except Exception as e:
            logger.error(f"Error tracking API metrics: {str(e)}")
    
    async def _track_endpoint_metrics(self, path: str, response_time_ms: float, is_success: bool):
        """Track metrics for specific endpoints"""
        try:
            # Normalize path (remove IDs and query params)
            normalized_path = self._normalize_path(path)
            
            current_hour = datetime.utcnow().strftime('%Y%m%d%H')
            endpoint_key = f"endpoint_metrics:{normalized_path}:{current_hour}"
            
            pipe = self.redis_client.pipeline()
            pipe.hincrby(endpoint_key, 'requests', 1)
            pipe.hincrby(endpoint_key, 'successful_requests' if is_success else 'failed_requests', 1)
            
            # Response time for this endpoint
            current_avg = await self.redis_client.hget(endpoint_key, 'avg_response_time')
            current_count = await self.redis_client.hget(endpoint_key, 'requests')
            
            if current_avg and current_count:
                current_avg = float(current_avg)
                current_count = int(current_count)
                new_avg = ((current_avg * (current_count - 1)) + response_time_ms) / current_count
            else:
                new_avg = response_time_ms
            
            pipe.hset(endpoint_key, 'avg_response_time', new_avg)
            await pipe.execute()
            
            # Set expiration
            await self.redis_client.expire(endpoint_key, 7 * 24 * 60 * 60)
            
        except Exception as e:
            logger.error(f"Error tracking endpoint metrics: {str(e)}")
    
    async def _track_user_agent_metrics(self, user_agent: str, response_time_ms: float, is_success: bool):
        """Track metrics by user agent type"""
        try:
            # Determine device type
            device_type = self._get_device_type(user_agent)
            
            current_hour = datetime.utcnow().strftime('%Y%m%d%H')
            ua_key = f"user_agent_metrics:{device_type}:{current_hour}"
            
            pipe = self.redis_client.pipeline()
            pipe.hincrby(ua_key, 'requests', 1)
            pipe.hincrby(ua_key, 'successful_requests' if is_success else 'failed_requests', 1)
            
            # Response time by device type
            current_avg = await self.redis_client.hget(ua_key, 'avg_response_time')
            current_count = await self.redis_client.hget(ua_key, 'requests')
            
            if current_avg and current_count:
                current_avg = float(current_avg)
                current_count = int(current_count)
                new_avg = ((current_avg * (current_count - 1)) + response_time_ms) / current_count
            else:
                new_avg = response_time_ms
            
            pipe.hset(ua_key, 'avg_response_time', new_avg)
            await pipe.execute()
            
            # Set expiration
            await self.redis_client.expire(ua_key, 7 * 24 * 60 * 60)
            
        except Exception as e:
            logger.error(f"Error tracking user agent metrics: {str(e)}")
    
    def _is_external_api_call(self, path: str) -> bool:
        """Determine if this is an external API call"""
        external_patterns = [
            '/integrations/',
            '/jobs/search',
            '/networking/find-contacts',
            '/agents/'
        ]
        return any(pattern in path for pattern in external_patterns)
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path by removing IDs and query parameters"""
        # Remove query parameters
        path = path.split('?')[0]
        
        # Replace UUIDs and numeric IDs with placeholders
        import re
        
        # UUID pattern
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{id}', path)
        
        # Numeric ID pattern
        path = re.sub(r'/\d+', '/{id}', path)
        
        return path
    
    def _get_device_type(self, user_agent: str) -> str:
        """Determine device type from user agent"""
        user_agent_lower = user_agent.lower()
        
        if 'mobile' in user_agent_lower or 'android' in user_agent_lower or 'iphone' in user_agent_lower:
            return 'mobile'
        elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
            return 'tablet'
        else:
            return 'desktop'

class AgentPerformanceTracker:
    """Track AI agent performance metrics"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client or get_redis_client()
    
    async def track_agent_call(
        self,
        agent_name: str,
        response_time_ms: float,
        success: bool = True,
        user_satisfaction: float = None,
        metadata: dict = None
    ):
        """Track an AI agent call"""
        try:
            current_hour = datetime.utcnow().strftime('%Y%m%d%H')
            agent_key = f"agent_metrics:{agent_name}:{current_hour}"
            
            pipe = self.redis_client.pipeline()
            
            # Basic metrics
            pipe.hincrby(agent_key, 'total_requests', 1)
            if success:
                pipe.hincrby(agent_key, 'successful_requests', 1)
            else:
                pipe.hincrby(agent_key, 'error_count', 1)
            
            # Response time
            current_total_time = await self.redis_client.hget(agent_key, 'total_response_time')
            if current_total_time:
                new_total_time = float(current_total_time) + response_time_ms
            else:
                new_total_time = response_time_ms
            
            pipe.hset(agent_key, 'total_response_time', new_total_time)
            
            # API calls (if this agent made external calls)
            if metadata and metadata.get('api_calls'):
                pipe.hincrby(agent_key, 'api_calls', metadata['api_calls'])
            
            await pipe.execute()
            
            # Set expiration
            await self.redis_client.expire(agent_key, 7 * 24 * 60 * 60)
            
            # Track user satisfaction if provided
            if user_satisfaction is not None:
                await self._track_satisfaction(agent_name, user_satisfaction)
            
        except Exception as e:
            logger.error(f"Error tracking agent performance: {str(e)}")
    
    async def _track_satisfaction(self, agent_name: str, satisfaction_score: float):
        """Track user satisfaction scores"""
        try:
            current_date = datetime.utcnow().strftime('%Y%m%d')
            satisfaction_key = f"agent_satisfaction:{agent_name}:{current_date}"
            
            # Store satisfaction scores in a list
            await self.redis_client.lpush(satisfaction_key, satisfaction_score)
            
            # Keep only last 1000 scores
            await self.redis_client.ltrim(satisfaction_key, 0, 999)
            
            # Set expiration
            await self.redis_client.expire(satisfaction_key, 30 * 24 * 60 * 60)  # 30 days
            
        except Exception as e:
            logger.error(f"Error tracking satisfaction: {str(e)}")

# Global agent tracker instance
agent_tracker = AgentPerformanceTracker()

# Decorator for tracking agent performance
def track_agent_performance(agent_name: str):
    """Decorator to track agent performance"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                end_time = time.time()
                response_time_ms = (end_time - start_time) * 1000
                
                # Track performance asynchronously
                asyncio.create_task(agent_tracker.track_agent_call(
                    agent_name=agent_name,
                    response_time_ms=response_time_ms,
                    success=success,
                    metadata={'error': error} if error else None
                ))
        
        return wrapper
    return decorator
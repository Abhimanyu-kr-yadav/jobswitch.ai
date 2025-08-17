"""
Performance monitoring service for AI agents and system components
"""
import asyncio
import time
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
import redis
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import json
from collections import defaultdict, deque

from app.models.analytics import SystemPerformanceMetrics, AgentPerformanceMetrics
from app.core.database import get_database
from app.core.logging_config import get_logger
from app.core.cache import get_redis_client

logger = get_logger(__name__)

class PerformanceMonitor:
    """Real-time performance monitoring for system components"""
    
    def __init__(self, db: Session):
        self.db = db
        self.redis_client = get_redis_client()
        self.metrics_buffer = defaultdict(deque)
        self.alert_thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 85.0,
            'response_time': 5000,  # 5 seconds
            'error_rate': 10.0,  # 10%
            'agent_success_rate': 90.0
        }
        self.monitoring_active = False
    
    async def start_monitoring(self, interval_seconds: int = 60):
        """Start continuous performance monitoring"""
        self.monitoring_active = True
        logger.info("Starting performance monitoring")
        
        while self.monitoring_active:
            try:
                await self._collect_system_metrics()
                await self._collect_agent_metrics()
                await self._check_alerts()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in performance monitoring: {str(e)}")
                await asyncio.sleep(interval_seconds)
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        logger.info("Stopped performance monitoring")
    
    async def _collect_system_metrics(self):
        """Collect system-level performance metrics"""
        try:
            # Get system metrics
            if PSUTIL_AVAILABLE:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
            else:
                # Mock values when psutil is not available
                cpu_percent = 45.0
                memory = type('Memory', (), {'percent': 65.0})()
                disk = type('Disk', (), {'percent': 30.0})()
            
            # Get active connections (simplified)
            active_users = await self._get_active_users_count()
            concurrent_sessions = await self._get_concurrent_sessions_count()
            
            # Get API metrics from Redis cache
            api_metrics = await self._get_api_metrics()
            
            # Get database metrics
            db_metrics = await self._get_database_metrics()
            
            # Get cache metrics
            cache_metrics = await self._get_cache_metrics()
            
            # Create metrics record
            metrics = SystemPerformanceMetrics(
                cpu_usage_percent=cpu_percent,
                memory_usage_percent=memory.percent,
                disk_usage_percent=disk.percent,
                active_users=active_users,
                concurrent_sessions=concurrent_sessions,
                total_requests=api_metrics.get('total_requests', 0),
                successful_requests=api_metrics.get('successful_requests', 0),
                failed_requests=api_metrics.get('failed_requests', 0),
                average_response_time_ms=api_metrics.get('avg_response_time', 0),
                db_connections_active=db_metrics.get('active_connections', 0),
                db_query_time_avg_ms=db_metrics.get('avg_query_time', 0),
                db_slow_queries=db_metrics.get('slow_queries', 0),
                external_api_calls=api_metrics.get('external_api_calls', 0),
                external_api_failures=api_metrics.get('external_api_failures', 0),
                external_api_avg_response_time_ms=api_metrics.get('external_avg_response_time', 0),
                cache_hit_rate=cache_metrics.get('hit_rate', 0),
                cache_memory_usage_mb=cache_metrics.get('memory_usage_mb', 0)
            )
            
            self.db.add(metrics)
            self.db.commit()
            
            # Store in buffer for real-time monitoring
            self.metrics_buffer['system'].append({
                'timestamp': datetime.utcnow(),
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'response_time': api_metrics.get('avg_response_time', 0),
                'error_rate': self._calculate_error_rate(api_metrics)
            })
            
            # Keep only last 100 entries
            if len(self.metrics_buffer['system']) > 100:
                self.metrics_buffer['system'].popleft()
            
            logger.debug(f"Collected system metrics: CPU={cpu_percent}%, Memory={memory.percent}%")
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
    
    async def _collect_agent_metrics(self):
        """Collect AI agent performance metrics"""
        try:
            agents = ['job_discovery', 'skills_analysis', 'resume_optimization', 
                     'interview_preparation', 'networking', 'career_strategy']
            
            for agent_name in agents:
                # Get agent metrics from Redis
                agent_data = await self._get_agent_performance_data(agent_name)
                
                if agent_data:
                    # Calculate performance metrics
                    success_rate = self._calculate_success_rate(agent_data)
                    avg_response_time = self._calculate_avg_response_time(agent_data)
                    
                    # Get resource usage (simplified)
                    cpu_usage, memory_usage = await self._get_agent_resource_usage(agent_name)
                    
                    # Update or create agent metrics
                    await self._update_agent_metrics(
                        agent_name=agent_name,
                        response_time_ms=avg_response_time,
                        success_rate=success_rate,
                        cpu_usage=cpu_usage,
                        memory_usage=memory_usage,
                        total_requests=agent_data.get('total_requests', 0),
                        error_count=agent_data.get('error_count', 0)
                    )
                    
                    # Store in buffer
                    self.metrics_buffer[agent_name].append({
                        'timestamp': datetime.utcnow(),
                        'success_rate': success_rate,
                        'response_time': avg_response_time,
                        'cpu_usage': cpu_usage,
                        'memory_usage': memory_usage
                    })
                    
                    # Keep only last 100 entries
                    if len(self.metrics_buffer[agent_name]) > 100:
                        self.metrics_buffer[agent_name].popleft()
            
        except Exception as e:
            logger.error(f"Error collecting agent metrics: {str(e)}")
    
    async def _check_alerts(self):
        """Check for performance alerts and trigger notifications"""
        try:
            alerts = []
            
            # Check system alerts
            if self.metrics_buffer['system']:
                latest_system = self.metrics_buffer['system'][-1]
                
                if latest_system['cpu_usage'] > self.alert_thresholds['cpu_usage']:
                    alerts.append({
                        'type': 'system',
                        'severity': 'high',
                        'message': f"High CPU usage: {latest_system['cpu_usage']:.1f}%",
                        'metric': 'cpu_usage',
                        'value': latest_system['cpu_usage']
                    })
                
                if latest_system['memory_usage'] > self.alert_thresholds['memory_usage']:
                    alerts.append({
                        'type': 'system',
                        'severity': 'high',
                        'message': f"High memory usage: {latest_system['memory_usage']:.1f}%",
                        'metric': 'memory_usage',
                        'value': latest_system['memory_usage']
                    })
                
                if latest_system['response_time'] > self.alert_thresholds['response_time']:
                    alerts.append({
                        'type': 'system',
                        'severity': 'medium',
                        'message': f"High response time: {latest_system['response_time']:.0f}ms",
                        'metric': 'response_time',
                        'value': latest_system['response_time']
                    })
            
            # Check agent alerts
            for agent_name, metrics in self.metrics_buffer.items():
                if agent_name != 'system' and metrics:
                    latest_agent = metrics[-1]
                    
                    if latest_agent['success_rate'] < self.alert_thresholds['agent_success_rate']:
                        alerts.append({
                            'type': 'agent',
                            'agent': agent_name,
                            'severity': 'high',
                            'message': f"Low success rate for {agent_name}: {latest_agent['success_rate']:.1f}%",
                            'metric': 'success_rate',
                            'value': latest_agent['success_rate']
                        })
            
            # Process alerts
            if alerts:
                await self._process_alerts(alerts)
            
        except Exception as e:
            logger.error(f"Error checking alerts: {str(e)}")
    
    async def _process_alerts(self, alerts: List[Dict[str, Any]]):
        """Process and store alerts"""
        try:
            # Store alerts in Redis for real-time access (if Redis is available)
            if self.redis_client:
                alert_key = f"performance_alerts:{datetime.utcnow().strftime('%Y%m%d')}"
                
                for alert in alerts:
                    alert['timestamp'] = datetime.utcnow().isoformat()
                    await self.redis_client.lpush(alert_key, json.dumps(alert))
                
                # Keep only last 1000 alerts
                await self.redis_client.ltrim(alert_key, 0, 999)
            
            # Log critical alerts
            for alert in alerts:
                if alert['severity'] == 'high':
                    logger.warning(f"Performance Alert: {alert['message']}")
            
        except Exception as e:
            logger.error(f"Error processing alerts: {str(e)}")
    
    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time performance metrics"""
        try:
            result = {
                'timestamp': datetime.utcnow().isoformat(),
                'system': {},
                'agents': {}
            }
            
            # Get latest system metrics
            if self.metrics_buffer['system']:
                latest_system = self.metrics_buffer['system'][-1]
                result['system'] = {
                    'cpu_usage': latest_system['cpu_usage'],
                    'memory_usage': latest_system['memory_usage'],
                    'response_time': latest_system['response_time'],
                    'error_rate': latest_system['error_rate'],
                    'status': self._get_system_health_status(latest_system)
                }
            
            # Get latest agent metrics
            for agent_name, metrics in self.metrics_buffer.items():
                if agent_name != 'system' and metrics:
                    latest_agent = metrics[-1]
                    result['agents'][agent_name] = {
                        'success_rate': latest_agent['success_rate'],
                        'response_time': latest_agent['response_time'],
                        'cpu_usage': latest_agent['cpu_usage'],
                        'memory_usage': latest_agent['memory_usage'],
                        'status': self._get_agent_health_status(latest_agent)
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting real-time metrics: {str(e)}")
            return {}
    
    async def get_performance_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent performance alerts"""
        try:
            alerts = []
            
            # Get alerts from the last few days (if Redis is available)
            if not self.redis_client:
                return alerts
                
            for i in range(hours // 24 + 1):
                date = (datetime.utcnow() - timedelta(days=i)).strftime('%Y%m%d')
                alert_key = f"performance_alerts:{date}"
                
                alert_data = await self.redis_client.lrange(alert_key, 0, -1)
                for alert_json in alert_data:
                    try:
                        alert = json.loads(alert_json)
                        alert_time = datetime.fromisoformat(alert['timestamp'])
                        
                        # Filter by time range
                        if alert_time >= datetime.utcnow() - timedelta(hours=hours):
                            alerts.append(alert)
                    except (json.JSONDecodeError, KeyError):
                        continue
            
            # Sort by timestamp (newest first)
            alerts.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return alerts[:100]  # Return last 100 alerts
            
        except Exception as e:
            logger.error(f"Error getting performance alerts: {str(e)}")
            return []
    
    # Helper methods
    async def _get_active_users_count(self) -> int:
        """Get count of active users"""
        try:
            # Count unique users active in last hour
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            count = self.db.query(func.count(func.distinct(UserActivity.user_id))).filter(
                UserActivity.timestamp >= one_hour_ago
            ).scalar()
            return count or 0
        except:
            return 0
    
    async def _get_concurrent_sessions_count(self) -> int:
        """Get count of concurrent sessions"""
        try:
            # Get from Redis session store (if available)
            if not self.redis_client:
                return 0
            session_keys = await self.redis_client.keys("session:*")
            return len(session_keys)
        except:
            return 0
    
    async def _get_api_metrics(self) -> Dict[str, Any]:
        """Get API performance metrics from Redis"""
        try:
            if not self.redis_client:
                return {}
            metrics_key = f"api_metrics:{datetime.utcnow().strftime('%Y%m%d%H')}"
            metrics_data = await self.redis_client.hgetall(metrics_key)
            
            return {
                'total_requests': int(metrics_data.get('total_requests', 0)),
                'successful_requests': int(metrics_data.get('successful_requests', 0)),
                'failed_requests': int(metrics_data.get('failed_requests', 0)),
                'avg_response_time': float(metrics_data.get('avg_response_time', 0)),
                'external_api_calls': int(metrics_data.get('external_api_calls', 0)),
                'external_api_failures': int(metrics_data.get('external_api_failures', 0)),
                'external_avg_response_time': float(metrics_data.get('external_avg_response_time', 0))
            }
        except:
            return {}
    
    async def _get_database_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        try:
            # Simplified database metrics
            return {
                'active_connections': 5,  # Would get from actual DB pool
                'avg_query_time': 50,     # Would calculate from query logs
                'slow_queries': 0         # Would get from slow query log
            }
        except:
            return {}
    
    async def _get_cache_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics"""
        try:
            if not self.redis_client:
                return {}
            info = await self.redis_client.info()
            
            # Calculate hit rate (simplified)
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            hit_rate = (hits / (hits + misses)) * 100 if (hits + misses) > 0 else 0
            
            return {
                'hit_rate': hit_rate,
                'memory_usage_mb': info.get('used_memory', 0) / (1024 * 1024)
            }
        except:
            return {'hit_rate': 0, 'memory_usage_mb': 0}
    
    async def _get_agent_performance_data(self, agent_name: str) -> Dict[str, Any]:
        """Get agent performance data from Redis"""
        try:
            if not self.redis_client:
                return {}
            agent_key = f"agent_metrics:{agent_name}:{datetime.utcnow().strftime('%Y%m%d%H')}"
            data = await self.redis_client.hgetall(agent_key)
            
            return {
                'total_requests': int(data.get('total_requests', 0)),
                'successful_requests': int(data.get('successful_requests', 0)),
                'error_count': int(data.get('error_count', 0)),
                'total_response_time': float(data.get('total_response_time', 0)),
                'api_calls': int(data.get('api_calls', 0))
            }
        except:
            return {}
    
    async def _get_agent_resource_usage(self, agent_name: str) -> tuple:
        """Get agent resource usage (simplified)"""
        # In a real implementation, you'd track per-agent resource usage
        return 10.0, 50.0  # cpu_percent, memory_mb
    
    async def _update_agent_metrics(self, agent_name: str, **kwargs):
        """Update agent performance metrics in database"""
        try:
            # Get today's metrics or create new
            today = datetime.utcnow().date()
            metrics = self.db.query(AgentPerformanceMetrics).filter(
                and_(
                    AgentPerformanceMetrics.agent_name == agent_name,
                    func.date(AgentPerformanceMetrics.timestamp) == today
                )
            ).first()
            
            if not metrics:
                metrics = AgentPerformanceMetrics(agent_name=agent_name)
                self.db.add(metrics)
            
            # Update metrics
            for key, value in kwargs.items():
                if hasattr(metrics, key):
                    setattr(metrics, key, value)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating agent metrics: {str(e)}")
            self.db.rollback()
    
    def _calculate_error_rate(self, api_metrics: Dict[str, Any]) -> float:
        """Calculate error rate from API metrics"""
        total = api_metrics.get('total_requests', 0)
        failed = api_metrics.get('failed_requests', 0)
        return (failed / total) * 100 if total > 0 else 0
    
    def _calculate_success_rate(self, agent_data: Dict[str, Any]) -> float:
        """Calculate agent success rate"""
        total = agent_data.get('total_requests', 0)
        successful = agent_data.get('successful_requests', 0)
        return (successful / total) * 100 if total > 0 else 100
    
    def _calculate_avg_response_time(self, agent_data: Dict[str, Any]) -> float:
        """Calculate average response time"""
        total_time = agent_data.get('total_response_time', 0)
        total_requests = agent_data.get('total_requests', 0)
        return total_time / total_requests if total_requests > 0 else 0
    
    def _get_system_health_status(self, metrics: Dict[str, Any]) -> str:
        """Determine system health status"""
        if (metrics['cpu_usage'] > 80 or 
            metrics['memory_usage'] > 85 or 
            metrics['error_rate'] > 10):
            return 'critical'
        elif (metrics['cpu_usage'] > 60 or 
              metrics['memory_usage'] > 70 or 
              metrics['response_time'] > 2000):
            return 'warning'
        else:
            return 'healthy'
    
    def _get_agent_health_status(self, metrics: Dict[str, Any]) -> str:
        """Determine agent health status"""
        if metrics['success_rate'] < 90:
            return 'critical'
        elif metrics['response_time'] > 3000:
            return 'warning'
        else:
            return 'healthy'

# Global performance monitor instance
performance_monitor = None

async def start_performance_monitoring(db: Session):
    """Start the global performance monitor"""
    global performance_monitor
    if performance_monitor is None:
        performance_monitor = PerformanceMonitor(db)
        asyncio.create_task(performance_monitor.start_monitoring())

def get_performance_monitor() -> Optional[PerformanceMonitor]:
    """Get the global performance monitor instance"""
    return performance_monitor